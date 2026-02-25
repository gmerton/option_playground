"""
Tool implementations for the trade reviewer agent.

Two tools:
  - get_price_history: fetches ~300 days of OHLCV from Tradier around a trade date
  - get_trades: fetches the user's trades for a given symbol from MySQL
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from decimal import Decimal

import mysql.connector

from lib.tradier.get_daily_history import get_daily_history
from lib.tradier.tradier_client_wrapper import TradierClient

# ── Tool definitions for the Anthropic API ───────────────────────────────────

TOOL_DEFS = [
    {
        "name": "get_price_history",
        "description": (
            "Fetch daily OHLCV price and volume history for a stock ticker. "
            "Returns up to 300 trading days ending on or around the given date. "
            "Use this to compute moving averages, volume averages, and identify "
            "consolidation highs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. 'AAPL'",
                },
                "trade_date": {
                    "type": "string",
                    "description": "The date of the trade in YYYY-MM-DD format. "
                                   "History will cover ~300 days ending on this date.",
                },
            },
            "required": ["ticker", "trade_date"],
        },
    },
    {
        "name": "get_trades",
        "description": (
            "Fetch all trades for a given stock symbol from the user's trade history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker or option symbol to look up",
                },
            },
            "required": ["symbol"],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def _get_mysql_conn():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.environ["MYSQL_PASSWORD"],
        database="stocks",
    )


def run_get_price_history(ticker: str, trade_date: str) -> dict:
    """
    Fetch OHLCV history via Tradier, compute key indicators, and return a
    compact summary suitable for Stage 2 analysis.
    """
    import numpy as np

    end = date.fromisoformat(trade_date)
    start = end - timedelta(days=420)  # enough for 200d MA + look-back

    async def _fetch():
        api_key = os.environ["TRADIER_API_KEY"]
        async with TradierClient(api_key=api_key) as client:
            return await get_daily_history(ticker, start, end, client=client)

    df = asyncio.run(_fetch())

    if df is None or df.empty:
        return {"error": f"No price history found for {ticker}"}

    df = df.sort_index()
    close = df["close"]
    volume = df["volume"].astype(float)

    # Moving averages
    df["ma50"]  = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()
    df["vol50"] = volume.rolling(50).mean()

    # Most recent row = trade date (or last available)
    last = df.iloc[-1]
    ten_weeks_ago = df.iloc[-51] if len(df) >= 51 else None  # ~10 weeks back

    # Consolidation pivot: highest close in the 6–10 weeks before the last day
    # 6 weeks = 30 trading days, 10 weeks = 50 trading days
    lookback = df.iloc[-50:-30] if len(df) >= 50 else df.iloc[:-5]
    pivot_high = float(lookback["close"].max()) if not lookback.empty else None

    entry_price = float(last["close"])
    ma50_val    = float(last["ma50"])  if not np.isnan(last["ma50"])  else None
    ma200_val   = float(last["ma200"]) if not np.isnan(last["ma200"]) else None
    vol50_val   = float(last["vol50"]) if not np.isnan(last["vol50"]) else None
    ma200_10w   = float(ten_weeks_ago["ma200"]) if ten_weeks_ago is not None and not np.isnan(ten_weeks_ago["ma200"]) else None

    # Recent OHLCV: last 10 days for context
    recent = df.tail(10).reset_index()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    recent_records = recent[["date","open","high","low","close","volume"]].to_dict(orient="records")

    return {
        "ticker": ticker,
        "trade_date": trade_date,
        "entry_price": entry_price,
        "ma50": ma50_val,
        "ma200": ma200_val,
        "ma200_10_weeks_ago": ma200_10w,
        "vol_50d_avg": vol50_val,
        "entry_day_volume": float(last["volume"]),
        "consolidation_pivot_high_6_to_10wks_ago": pivot_high,
        "recent_10_days": recent_records,
        "note": (
            "Indicators computed over ~300 trading days ending on trade_date. "
            "ma200_10_weeks_ago is the 200d MA value ~50 trading days prior."
        ),
    }


def run_get_trades(symbol: str) -> dict:
    """Fetch trades for a symbol from MySQL."""
    conn = _get_mysql_conn()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, trade_date, asset_category, symbol, underlying,
                   expiry, strike, put_call, buy_sell, quantity,
                   price, amount, net_cash, commission
            FROM trades
            WHERE symbol = %s OR underlying = %s
            ORDER BY trade_date DESC
            """,
            (symbol, symbol),
        )
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()

    # Convert non-serialisable types
    for r in rows:
        for k, v in r.items():
            if isinstance(v, date):
                r[k] = v.isoformat()
            elif isinstance(v, Decimal):
                r[k] = float(v)

    return {"symbol": symbol, "count": len(rows), "trades": rows}


def dispatch_tool(name: str, inputs: dict) -> str:
    """Route a tool call to its implementation and return result as a string."""
    import json

    if name == "get_price_history":
        result = run_get_price_history(inputs["ticker"], inputs["trade_date"])
    elif name == "get_trades":
        result = run_get_trades(inputs["symbol"])
    else:
        result = {"error": f"Unknown tool: {name}"}

    return json.dumps(result, default=str)

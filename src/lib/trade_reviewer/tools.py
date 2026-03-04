"""
Tool implementations for the trade reviewer agent.

Tools:
  - get_price_history: fetches ~300 days of OHLCV from Tradier around a trade date
  - get_live_quote: fetches the current real-time quote for a ticker from Tradier
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
        "name": "get_live_quote",
        "description": (
            "Fetch the current real-time quote for a stock ticker, including the "
            "last price, today's open/high/low, today's volume so far, and the "
            "percentage change from yesterday's close. Use this when evaluating a "
            "prospective trade during market hours."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. 'AAPL'",
                },
            },
            "required": ["ticker"],
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
    close  = df["close"]
    high   = df["high"]
    low    = df["low"]
    volume = df["volume"].astype(float)

    # Simple moving averages
    df["ma50"]  = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()
    df["vol50"] = volume.rolling(50).mean()

    # Exponential moving averages (Luk's EMA stack: 9 > 21 > 50)
    df["ema9"]  = close.ewm(span=9,  adjust=False).mean()
    df["ema21"] = close.ewm(span=21, adjust=False).mean()
    df["ema50"] = close.ewm(span=50, adjust=False).mean()

    # Average Daily Range % (Luk: ADR > 5%)
    df["daily_range_pct"] = (high - low) / close * 100
    df["adr50"] = df["daily_range_pct"].rolling(50).mean()

    # Most recent row = trade date (or last available)
    last = df.iloc[-1]
    ten_weeks_ago = df.iloc[-51] if len(df) >= 51 else None  # ~10 weeks back

    # Explicit lookback closes for RS and extension checks — avoids LLM estimation
    def _lookback_close(n):
        """Close n trading days ago (1-indexed: -1 = yesterday, -21 = ~1 month ago)."""
        idx = -(n + 1)
        return _f(df["close"].iloc[idx]) if len(df) > n else None

    # Consolidation pivot: highest close in the 6–10 weeks before the last day
    # 6 weeks = 30 trading days, 10 weeks = 50 trading days
    lookback = df.iloc[-50:-30] if len(df) >= 50 else df.iloc[:-5]
    pivot_high = float(lookback["close"].max()) if not lookback.empty else None

    def _f(v):
        return float(v) if not np.isnan(v) else None

    close_now  = _f(last["close"])
    close_21d  = _lookback_close(21)   # ~1 month ago
    close_40d  = _lookback_close(40)   # ~2 months ago / C(40) for extension check
    close_63d  = _lookback_close(63)   # ~3 months ago

    def _pct(c_now, c_then):
        if c_now and c_then:
            return round((c_now - c_then) / c_then * 100, 1)
        return None

    # Recent OHLCV + indicators: last 10 days for context
    recent = df.tail(10).reset_index()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    recent_records = recent[
        ["date", "open", "high", "low", "close", "volume", "ema9", "ema21", "ema50"]
    ].to_dict(orient="records")

    return {
        "ticker": ticker,
        "trade_date": trade_date,
        # Price & MAs
        "entry_price":            close_now,
        "entry_day_low":          _f(last["low"]),   # for stop placement
        "ma50":                   _f(last["ma50"]),
        "ma200":                  _f(last["ma200"]),
        "ma200_10_weeks_ago":     _f(ten_weeks_ago["ma200"]) if ten_weeks_ago is not None else None,
        # Luk EMAs
        "ema9":                   _f(last["ema9"]),
        "ema21":                  _f(last["ema21"]),
        "ema50_ema":              _f(last["ema50"]),
        # Volume
        "vol_50d_avg":            _f(last["vol50"]),
        "entry_day_volume":       float(last["volume"]),
        # Luk ADR
        "adr_50d_pct":            _f(last["adr50"]),
        # Pivot
        "consolidation_pivot_high_6_to_10wks_ago": pivot_high,
        # Explicit lookback closes — use these directly, do NOT estimate from MAs
        "close_21d_ago":          close_21d,
        "close_40d_ago":          close_40d,
        "close_63d_ago":          close_63d,
        "pct_change_1m":          _pct(close_now, close_21d),   # ~1-month RS
        "pct_change_2m":          _pct(close_now, close_40d),   # ~2-month RS / C/C(40)
        "pct_change_3m":          _pct(close_now, close_63d),   # ~3-month RS
        # Recent bars with EMAs
        "recent_10_days": recent_records,
        "note": (
            "All indicators computed over ~300 trading days ending on trade_date. "
            "close_21d_ago/close_40d_ago/close_63d_ago are exact closes from the "
            "Tradier price history — use these (not MA estimates) when citing RS or "
            "extension figures. pct_change_* fields are pre-computed from those closes. "
            "adr_50d_pct is the 50-day avg of (high-low)/close as a percentage. "
            "entry_day_low is the low of the entry candle — use as the primary stop level."
        ),
    }


def run_get_live_quote(ticker: str) -> dict:
    """Fetch a real-time quote from Tradier's /markets/quotes endpoint."""
    import zoneinfo

    async def _fetch():
        api_key = os.environ["TRADIER_API_KEY"]
        async with TradierClient(api_key=api_key) as client:
            return await client.get_json(
                "/markets/quotes", params={"symbols": ticker, "greeks": "false"}
            )

    data = asyncio.run(_fetch())

    quotes = (data or {}).get("quotes") or {}
    quote = quotes.get("quote")
    if quote is None:
        return {"error": f"No quote found for {ticker}"}

    # Compute projected full-day volume so the LLM doesn't have to guess the time.
    # Market hours: 9:30–16:00 ET = 390 minutes total.
    from datetime import datetime
    et = zoneinfo.ZoneInfo("America/New_York")
    now_et = datetime.now(et)
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    minutes_elapsed = max(1, (now_et - market_open).total_seconds() / 60)
    minutes_elapsed = min(minutes_elapsed, 390)  # cap at full day
    current_volume = quote.get("volume") or 0
    projected_volume = int(current_volume / (minutes_elapsed / 390)) if minutes_elapsed > 0 else None

    return {
        "ticker": ticker,
        "last":                   quote.get("last"),
        "open":                   quote.get("open"),
        "high":                   quote.get("high"),
        "low":                    quote.get("low"),
        "close":                  quote.get("close"),       # previous close
        "change_pct":             quote.get("change_percentage"),
        "volume":                 current_volume,
        "current_time_et":        now_et.strftime("%H:%M ET"),
        "minutes_elapsed":        round(minutes_elapsed),
        "projected_full_day_vol": projected_volume,
        "note": (
            "projected_full_day_vol is today's volume scaled to a full session. "
            "To compute volume_buzz_pct, divide projected_full_day_vol by the "
            "vol_50d_avg from get_price_history — do NOT use any avg_volume from "
            "the quote API as it uses a different averaging period."
        ),
        "trade_date":             quote.get("trade_date"),
        "description":            quote.get("description"),
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
    elif name == "get_live_quote":
        result = run_get_live_quote(inputs["ticker"])
    elif name == "get_trades":
        result = run_get_trades(inputs["symbol"])
    else:
        result = {"error": f"Unknown tool: {name}"}

    return json.dumps(result, default=str)

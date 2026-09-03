from __future__ import annotations

from typing import Optional, List, Dict, Any
import aiohttp
from lib.commons.get_underlying_price import get_underlying_price
from datetime import date, timedelta
import pandas as pd
from dataclasses import dataclass
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.list_expirations import list_expirations
from lib.tradier.tradier_client_wrapper import TradierClient
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import math
import  asyncio
import os

async def get_daily_history(
    ticker: str,
    start: date,
    end: date,
    *,
    client: TradierClient,
) -> Optional[pd.DataFrame]:
    params = {
        "symbol": ticker,
        "interval": "daily",
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    data = await client.get_json("/markets/history", params=params)

    history = (data or {}).get("history") or {}
    day = history.get("day")

    if not day:
        return None

    if isinstance(day, dict):
        day = [day]

    df = pd.DataFrame(day)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df


async def get_intraday_bars(
    ticker: str,
    day: date,
    *,
    interval: str = "5min",
    client: TradierClient,
) -> Optional[pd.DataFrame]:
    """Intraday OHLC bars for one session via Tradier /markets/timesales.

    interval: '1min' / '5min' / '15min'. Works well for equities (real OHLC
    per bucket). For options this endpoint is trade-prints-only -- each bar's
    open/high/low/close collapse to the same value and coverage is sparse
    (confirmed empirically; see [[project_daily_trade_journal]]) -- don't rely
    on it for option premium charts, chart the underlying instead.

    Returns a DataFrame indexed by bar start time (naive, exchange-local /
    ET), columns open/high/low/close/volume/vwap, or None if no data (e.g.
    outside Tradier's intraday retention window, holiday, no trades).
    """
    params = {
        "symbol": ticker,
        "interval": interval,
        "start": f"{day.isoformat()} 09:30",
        "end": f"{day.isoformat()} 16:00",
        "session_filter": "open",
    }
    data = await client.get_json("/markets/timesales", params=params)
    series = (data or {}).get("series") or {}
    bars = series.get("data")
    if not bars:
        return None
    if isinstance(bars, dict):
        bars = [bars]
    df = pd.DataFrame(bars)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    return df

"""
On-disk + in-process cache for the daily/intraday price data behind the trade
journal review pages (run_trade_review_pages.py). A closed trading session's
data never changes, so once a symbol/day is cached it's trusted forever;
only sessions within REFRESH_WINDOW_DAYS of today are ever refetched.

This turns "regenerate everything" from N Tradier calls (roughly 1-2 per
review, previously ~90s for 500 reviews) into ~1 call per *symbol* the first
time it's ever needed, and zero calls on repeat runs for any symbol whose
data has fully aged out of the refresh window.

Cache layout:
    data/cache/journal_daily/<SYMBOL>.parquet             -- full daily OHLCV history
    data/cache/journal_intraday/<SYMBOL>_<YYYY-MM-DD>.parquet  -- one session's 5-min bars
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from lib.tradier.get_daily_history import get_daily_history, get_intraday_bars
from lib.tradier.tradier_client_wrapper import TradierClient

DAILY_CACHE_DIR = Path("data/cache/journal_daily")
INTRADAY_CACHE_DIR = Path("data/cache/journal_intraday")

# Sessions within this many days of today are never trusted from cache --
# same-week data can still be subject to late corrections, and an open
# position's "through today" window advances every day regardless.
REFRESH_WINDOW_DAYS = 2

_daily_mem: dict[str, pd.DataFrame] = {}
_intraday_mem: dict[tuple[str, date], pd.DataFrame | None] = {}


def _is_final(d: date) -> bool:
    return d < date.today() - timedelta(days=REFRESH_WINDOW_DAYS)


async def get_daily_history_cached(
    symbol: str, start: date, end: date, *, client: TradierClient
) -> pd.DataFrame | None:
    """Daily OHLCV for [start, end], cached per-symbol on disk. Zero API calls
    if the symbol is already cached, covers the requested range, and that
    range is old enough to be considered final."""
    cached = _daily_mem.get(symbol)
    if cached is None:
        path = DAILY_CACHE_DIR / f"{symbol}.parquet"
        if path.exists():
            cached = pd.read_parquet(path)
            _daily_mem[symbol] = cached

    if cached is not None and not cached.empty:
        covers = cached.index.min().date() <= start and cached.index.max().date() >= end
        if covers and _is_final(end):
            return cached.loc[str(start):str(end)]

    # Need a fetch. Pull the widest useful range in one call -- from the earliest
    # date anyone has asked for (this request or what's already cached) through
    # today -- so later requests for this symbol are more likely to be a pure
    # cache hit, even if their window differs from this one.
    fetch_start = min(start, cached.index.min().date()) if cached is not None and not cached.empty else start
    fetch_end = max(end, date.today())
    fresh = await get_daily_history(symbol, fetch_start, fetch_end, client=client)
    if fresh is None or fresh.empty:
        return cached.loc[str(start):str(end)] if cached is not None and not cached.empty else None

    DAILY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fresh.to_parquet(DAILY_CACHE_DIR / f"{symbol}.parquet")
    _daily_mem[symbol] = fresh
    return fresh.loc[str(start):str(end)]


async def get_intraday_bars_cached(
    symbol: str, day: date, *, client: TradierClient
) -> pd.DataFrame | None:
    """5-min bars for one session. Today's session is never cached (still
    developing); anything before that is cached permanently, including a
    cached "no data" result so a known-empty day isn't refetched forever."""
    if day >= date.today():
        return await get_intraday_bars(symbol, day, interval="5min", client=client)

    key = (symbol, day)
    if key in _intraday_mem:
        return _intraday_mem[key]

    path = INTRADAY_CACHE_DIR / f"{symbol}_{day.isoformat()}.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        result = None if df.empty else df
        _intraday_mem[key] = result
        return result

    df = await get_intraday_bars(symbol, day, interval="5min", client=client)
    INTRADAY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (df if df is not None else pd.DataFrame()).to_parquet(path)
    _intraday_mem[key] = df
    return df

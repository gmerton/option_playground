from __future__ import annotations
from lib.tradier.tradier_client_wrapper import TradierClient
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SmaTrendResult:
    symbol: str
    asof: str
    window: int                 # 200
    lookback_trading_days: int  # e.g. 21, 84, 105
    sma_now: Optional[float]
    sma_then: Optional[float]
    delta_abs: Optional[float]
    delta_pct: Optional[float]
    is_up: bool
    closes_used: int

def _rolling_sma(values: List[float], window: int) -> List[Optional[float]]:
    """
    Rolling SMA aligned so that sma[i] is the SMA ending at i (inclusive).
    Values before window-1 are None.
    O(n) time, O(n) memory.
    """
    out: List[Optional[float]] = [None] * len(values)
    if len(values) < window:
        return out

    s = sum(values[:window])
    out[window - 1] = s / window

    for i in range(window, len(values)):
        s += values[i] - values[i - window]
        out[i] = s / window

    return out

async def sma_trending_up_trading_days(
    tradier: "TradierClient",
    symbol: str,
    *,
    ma_window: int = 200,
    lookback_trading_days: int = 21,   # ~1 month default
    min_delta_pct: float = 0.0,        # e.g. 0.01 means SMA must be up >= 1%
    end: Optional[date] = None,
    lookback_calendar_days: int = 520, # enough to compute SMA200 + compare 4-5 months back
) -> SmaTrendResult:
    """
    Quantify: "MA line is trending up for at least N trading days"
    -> SMA(t) > SMA(t - N), optionally by min_delta_pct.

    This uses trading-day indexing by operating on the daily candle series returned by Tradier.
    """
    if not symbol or not symbol.strip():
        raise ValueError("symbol is required")

    end = end or date.today()
    start = end - timedelta(days=lookback_calendar_days)

    sym = symbol.strip().upper()
    payload: Dict[str, Any] = await tradier.get_json(
        "/markets/history",
        params={"symbol": sym, "start": start.isoformat(), "end": end.isoformat()},
    )

    history = (payload or {}).get("history") or {}
    days = history.get("day")

    if not days:
        return SmaTrendResult(
            symbol=sym,
            asof="",
            window=ma_window,
            lookback_trading_days=lookback_trading_days,
            sma_now=None,
            sma_then=None,
            delta_abs=None,
            delta_pct=None,
            is_up=False,
            closes_used=0,
        )

    # Single-day edge case
    if isinstance(days, dict):
        days = [days]

    # Ensure chronological
    days_sorted = sorted(days, key=lambda d: d.get("date", ""))

    closes: List[float] = []
    asof = ""
    for d in days_sorted:
        c = d.get("close")
        dt = d.get("date")
        if c is None or dt is None:
            continue
        closes.append(float(c))
        asof = str(dt)

    sma_series = _rolling_sma(closes, ma_window)

    # Find most recent valid SMA value
    i_now = len(sma_series) - 1
    while i_now >= 0 and sma_series[i_now] is None:
        i_now -= 1

    if i_now < 0:
        # Not enough data to compute MA at all
        return SmaTrendResult(
            symbol=sym,
            asof=asof,
            window=ma_window,
            lookback_trading_days=lookback_trading_days,
            sma_now=None,
            sma_then=None,
            delta_abs=None,
            delta_pct=None,
            is_up=False,
            closes_used=len(closes),
        )

    i_then = i_now - lookback_trading_days
    if i_then < 0 or sma_series[i_then] is None:
        # Not enough history to look back N trading days with a defined SMA
        return SmaTrendResult(
            symbol=sym,
            asof=asof,
            window=ma_window,
            lookback_trading_days=lookback_trading_days,
            sma_now=sma_series[i_now],
            sma_then=None,
            delta_abs=None,
            delta_pct=None,
            is_up=False,
            closes_used=len(closes),
        )

    now = sma_series[i_now]
    then = sma_series[i_then]
    assert now is not None and then is not None

    delta_abs = now - then
    delta_pct = (delta_abs / then) if then != 0 else None

    is_up = (delta_abs > 0) and (delta_pct is not None and delta_pct >= min_delta_pct)

    return SmaTrendResult(
        symbol=sym,
        asof=asof,
        window=ma_window,
        lookback_trading_days=lookback_trading_days,
        sma_now=now,
        sma_then=then,
        delta_abs=delta_abs,
        delta_pct=delta_pct,
        is_up=is_up,
        closes_used=len(closes),
    )

@dataclass(frozen=True)
class MovingAverages:
    symbol: str
    asof: str                 # last candle date in YYYY-MM-DD
    sma_50: Optional[float]
    sma_150: Optional[float]
    sma_200: Optional[float]
    closes_used: int


def _sma(values: List[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    w = values[-window:]
    return sum(w) / window


async def get_sma(
    tradier: TradierClient,
    symbol: str,
    *,
    end: Optional[date] = None,
    lookback_calendar_days: int = 320,  # usually enough to cover 200 trading days
) -> MovingAverages:
    """
    Fetch daily historical closes from Tradier and compute SMA(150) + SMA(200).

    Uses: GET /v1/markets/history?symbol=...&start=...&end=...
    """
    if not symbol or not symbol.strip():
        raise ValueError("symbol is required")

    end = end or date.today()
    start = end - timedelta(days=lookback_calendar_days)

    params = {
        "symbol": symbol.strip().upper(),
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    payload: Dict[str, Any] = await tradier.get_json("/markets/history", params=params)

    history = (payload or {}).get("history") or {}
    days = history.get("day")

    if not days:
        return MovingAverages(
            symbol=params["symbol"],
            asof="",
            sma_50=None,
            sma_150=None,
            sma_200=None,
            closes_used=0,
        )

    # Tradier sometimes returns a dict for a single day
    if isinstance(days, dict):
        days = [days]

    # Ensure chronological order
    days_sorted = sorted(days, key=lambda d: d.get("date", ""))

    closes: List[float] = []
    asof = ""
    for d in days_sorted:
        dt = d.get("date")
        c = d.get("close")
        if dt is None or c is None:
            continue
        closes.append(float(c))
        asof = str(dt)

    return MovingAverages(
        symbol=params["symbol"],
        asof=asof,
        sma_50 = _sma(closes, 50),
        sma_150=_sma(closes, 150),
        sma_200=_sma(closes, 200),
        closes_used=len(closes),
    )

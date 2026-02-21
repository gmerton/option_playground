from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from lib.tradier.tradier_client_wrapper import TradierClient


@dataclass(frozen=True)
class VolCompressionResult:
    symbol: str
    asof: str

    # ATR settings
    atr_period: int
    atr_slow_period: int
    atr_pct_lookback: int
    atr_pct_threshold: float
    atr_downtrend_lookback: int

    # Range contraction (Minervini)
    range_5: int
    range_20: int
    range_60: int

    # Volume dry-up (optional)
    require_volume_dry_up: bool
    vol_short: int
    vol_long: int

    # Computed metrics (most recent)
    atr: Optional[float]
    atr_slow: Optional[float]
    atr_pct: Optional[float]          # ATR / close
    atr_pct_rank: Optional[float]     # percentile of atr_pct within lookback window (0..1; lower=more compressed)

    avg_range_5: Optional[float]      # mean((H-L)/C) over last 5 days
    avg_range_20: Optional[float]
    avg_range_60: Optional[float]

    vol_ma_short: Optional[float]
    vol_ma_long: Optional[float]

    # Boolean sub-checks
    atr_rank_ok: bool
    atr_vs_slow_ok: bool
    atr_downtrend_ok: bool
    range_chain_ok: bool
    volume_dry_up_ok: bool

    # Final signal
    is_compressing: bool

    # Data sufficiency
    days_used: int


def _mean_last(values: List[float], window: int) -> Optional[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    w = values[-window:]
    return sum(w) / window


def _percentile_rank_of_last(values: List[float], lookback: int) -> Optional[float]:
    """
    Percentile rank of the last value within the last `lookback` values.
    Returns in [0..1], where 0.10 means last value is in the bottom 10%.
    """
    if lookback <= 1:
        raise ValueError("lookback must be > 1")
    if len(values) < min(lookback, 30):
        return None

    window = values[-lookback:] if len(values) >= lookback else values[:]
    last = window[-1]
    # <= gives bottom-heavy rank; fine for "is it among the lowest X%"
    return sum(1 for v in window if v <= last) / float(len(window))


def _wilder_rma(values: List[float], period: int) -> List[Optional[float]]:
    """
    Wilder's RMA (aka ATR smoothing in many charting packages).
    Output aligned with input; entries before first seed are None.

    Seed is the SMA of the first `period` values, then:
      rma[t] = (rma[t-1]*(period-1) + x[t]) / period
    """
    out: List[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return out

    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed

    for i in range(period, len(values)):
        prev = (prev * (period - 1) + values[i]) / period
        out[i] = prev

    return out


def _true_range_series(highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[float]]:
    """
    True Range for each day:
      TR = max(H-L, abs(H-prevC), abs(L-prevC))
    For first day, prevC unavailable => TR = H-L
    """
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    if n == 0:
        return out

    out[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        out[i] = max(hl, hc, lc)

    return out


async def volatility_compression_trading_days(
    tradier: "TradierClient",
    symbol: str,
    *,
    end: Optional[date] = None,
    lookback_calendar_days: int = 520,  # enough for ~252 trading days + buffers

    # ATR compression
    atr_period: int = 14,
    atr_slow_period: int = 50,
    atr_pct_lookback: int = 252,
    atr_pct_threshold: float = 0.20,      # bottom 20% of last year
    atr_downtrend_lookback: int = 20,     # ATR% today < ATR% 20 trading days ago

    # Minervini range contraction confirmation
    range_5: int = 5,
    range_20: int = 20,
    range_60: int = 60,

    # Optional volume dry-up
    require_volume_dry_up: bool = False,
    vol_short: int = 20,
    vol_long: int = 60,
) -> VolCompressionResult:
    """
    Identify Minervini-like volatility compression using Tradier daily candles.

    Signal is:
      1) ATR% (ATR/Close) is in the bottom `atr_pct_threshold` percentile over `atr_pct_lookback` days
      2) ATR(atr_period) < ATR(atr_slow_period)
      3) ATR% today < ATR% N trading days ago (downtrend)
      4) Range contraction: AvgRange(5) < AvgRange(20) < AvgRange(60), where AvgRange(k)=mean((H-L)/C)
      5) (optional) Volume dry-up: VolMA(short) < VolMA(long)

    Returns rich diagnostics so you can tune thresholds.
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
        return VolCompressionResult(
            symbol=sym,
            asof="",
            atr_period=atr_period,
            atr_slow_period=atr_slow_period,
            atr_pct_lookback=atr_pct_lookback,
            atr_pct_threshold=atr_pct_threshold,
            atr_downtrend_lookback=atr_downtrend_lookback,
            range_5=range_5,
            range_20=range_20,
            range_60=range_60,
            require_volume_dry_up=require_volume_dry_up,
            vol_short=vol_short,
            vol_long=vol_long,
            atr=None,
            atr_slow=None,
            atr_pct=None,
            atr_pct_rank=None,
            avg_range_5=None,
            avg_range_20=None,
            avg_range_60=None,
            vol_ma_short=None,
            vol_ma_long=None,
            atr_rank_ok=False,
            atr_vs_slow_ok=False,
            atr_downtrend_ok=False,
            range_chain_ok=False,
            volume_dry_up_ok=(not require_volume_dry_up),
            is_compressing=False,
            days_used=0,
        )

    if isinstance(days, dict):
        days = [days]

    days_sorted = sorted(days, key=lambda d: d.get("date", ""))

    highs: List[float] = []
    lows: List[float] = []
    closes: List[float] = []
    volumes: List[float] = []
    asof = ""

    for d in days_sorted:
        dt = d.get("date")
        h = d.get("high")
        l = d.get("low")
        c = d.get("close")
        v = d.get("volume")
        if dt is None or h is None or l is None or c is None or v is None:
            continue
        highs.append(float(h))
        lows.append(float(l))
        closes.append(float(c))
        volumes.append(float(v))
        asof = str(dt)

    n = len(closes)
    if n == 0:
        return VolCompressionResult(
            symbol=sym,
            asof="",
            atr_period=atr_period,
            atr_slow_period=atr_slow_period,
            atr_pct_lookback=atr_pct_lookback,
            atr_pct_threshold=atr_pct_threshold,
            atr_downtrend_lookback=atr_downtrend_lookback,
            range_5=range_5,
            range_20=range_20,
            range_60=range_60,
            require_volume_dry_up=require_volume_dry_up,
            vol_short=vol_short,
            vol_long=vol_long,
            atr=None,
            atr_slow=None,
            atr_pct=None,
            atr_pct_rank=None,
            avg_range_5=None,
            avg_range_20=None,
            avg_range_60=None,
            vol_ma_short=None,
            vol_ma_long=None,
            atr_rank_ok=False,
            atr_vs_slow_ok=False,
            atr_downtrend_ok=False,
            range_chain_ok=False,
            volume_dry_up_ok=(not require_volume_dry_up),
            is_compressing=False,
            days_used=0,
        )

    # --- ATR ---
    tr_opt = _true_range_series(highs, lows, closes)
    tr: List[float] = [t for t in tr_opt if t is not None]

    # Keep alignment: if we had missing, we'd be off; but we built lists only from complete rows.
    # So tr_opt has length n and no Nones except possibly none; we can safely cast.
    tr_full: List[float] = [float(t) for t in tr_opt if t is not None]
    if len(tr_full) != n:
        # Defensive: shouldn't happen given our data extraction
        tr_full = [highs[i] - lows[i] if i == 0 else max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        ) for i in range(n)]

    atr_series = _wilder_rma(tr_full, atr_period)
    atr_slow_series = _wilder_rma(tr_full, atr_slow_period)

    # Find last defined ATR values
    i_now = n - 1
    while i_now >= 0 and (atr_series[i_now] is None or atr_slow_series[i_now] is None):
        i_now -= 1

    if i_now < 0:
        # Not enough data to compute ATR series
        return VolCompressionResult(
            symbol=sym,
            asof=asof,
            atr_period=atr_period,
            atr_slow_period=atr_slow_period,
            atr_pct_lookback=atr_pct_lookback,
            atr_pct_threshold=atr_pct_threshold,
            atr_downtrend_lookback=atr_downtrend_lookback,
            range_5=range_5,
            range_20=range_20,
            range_60=range_60,
            require_volume_dry_up=require_volume_dry_up,
            vol_short=vol_short,
            vol_long=vol_long,
            atr=None,
            atr_slow=None,
            atr_pct=None,
            atr_pct_rank=None,
            avg_range_5=None,
            avg_range_20=None,
            avg_range_60=None,
            vol_ma_short=None,
            vol_ma_long=None,
            atr_rank_ok=False,
            atr_vs_slow_ok=False,
            atr_downtrend_ok=False,
            range_chain_ok=False,
            volume_dry_up_ok=(not require_volume_dry_up),
            is_compressing=False,
            days_used=n,
        )

    atr_now = atr_series[i_now]
    atr_slow_now = atr_slow_series[i_now]
    assert atr_now is not None and atr_slow_now is not None

    close_now = closes[i_now]
    atr_pct_now = (atr_now / close_now) if close_now != 0 else None

    # ATR% series for percentile + downtrend checks (only where ATR defined)
    atr_pct_series: List[float] = []
    atr_pct_index: List[int] = []
    for i in range(n):
        a = atr_series[i]
        c = closes[i]
        if a is None or c == 0:
            continue
        atr_pct_series.append(a / c)
        atr_pct_index.append(i)

    atr_pct_rank = _percentile_rank_of_last(atr_pct_series, atr_pct_lookback)

    # Downtrend: compare ATR% now vs ATR% N trading days ago (in ATR-defined space)
    atr_downtrend_ok = False
    if atr_pct_now is not None and len(atr_pct_series) > atr_downtrend_lookback:
        then_val = atr_pct_series[-1 - atr_downtrend_lookback]
        atr_downtrend_ok = atr_pct_now < then_val

    # ATR vs slow
    atr_vs_slow_ok = atr_now < atr_slow_now

    # ATR rank check
    atr_rank_ok = (atr_pct_rank is not None) and (atr_pct_rank <= atr_pct_threshold)

    # --- Range contraction ---
    daily_range_pct: List[float] = []
    for i in range(n):
        if closes[i] == 0:
            continue
        daily_range_pct.append((highs[i] - lows[i]) / closes[i])

    # Range averages should line up with last n days (we built daily_range_pct from all rows; close==0 unlikely)
    avg_r5 = _mean_last(daily_range_pct, range_5)
    avg_r20 = _mean_last(daily_range_pct, range_20)
    avg_r60 = _mean_last(daily_range_pct, range_60)

    range_chain_ok = False
    if avg_r5 is not None and avg_r20 is not None and avg_r60 is not None:
        range_chain_ok = (avg_r5 < avg_r20) and (avg_r20 < avg_r60)

    # --- Volume dry-up (optional) ---
    vol_ma_short_val = _mean_last(volumes, vol_short)
    vol_ma_long_val = _mean_last(volumes, vol_long)

    volume_dry_up_ok = True
    if require_volume_dry_up:
        volume_dry_up_ok = (
            vol_ma_short_val is not None
            and vol_ma_long_val is not None
            and vol_ma_short_val < vol_ma_long_val
        )

    is_compressing = (
        atr_rank_ok
        and atr_vs_slow_ok
        and atr_downtrend_ok
        and range_chain_ok
        and volume_dry_up_ok
    )

    return VolCompressionResult(
        symbol=sym,
        asof=asof,
        atr_period=atr_period,
        atr_slow_period=atr_slow_period,
        atr_pct_lookback=atr_pct_lookback,
        atr_pct_threshold=atr_pct_threshold,
        atr_downtrend_lookback=atr_downtrend_lookback,
        range_5=range_5,
        range_20=range_20,
        range_60=range_60,
        require_volume_dry_up=require_volume_dry_up,
        vol_short=vol_short,
        vol_long=vol_long,
        atr=float(atr_now),
        atr_slow=float(atr_slow_now),
        atr_pct=float(atr_pct_now) if atr_pct_now is not None else None,
        atr_pct_rank=float(atr_pct_rank) if atr_pct_rank is not None else None,
        avg_range_5=float(avg_r5) if avg_r5 is not None else None,
        avg_range_20=float(avg_r20) if avg_r20 is not None else None,
        avg_range_60=float(avg_r60) if avg_r60 is not None else None,
        vol_ma_short=float(vol_ma_short_val) if vol_ma_short_val is not None else None,
        vol_ma_long=float(vol_ma_long_val) if vol_ma_long_val is not None else None,
        atr_rank_ok=atr_rank_ok,
        atr_vs_slow_ok=atr_vs_slow_ok,
        atr_downtrend_ok=atr_downtrend_ok,
        range_chain_ok=range_chain_ok,
        volume_dry_up_ok=volume_dry_up_ok,
        is_compressing=is_compressing,
        days_used=n,
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from lib.tradier.tradier_client_wrapper import TradierClient



@dataclass(frozen=True)
class PivotSignal:
    symbol: str
    asof: str

    # Base / pivot settings
    base_lookback_days: int
    min_base_len_bars: int
    min_depth: float
    max_depth: float

    # Pivot breakout settings
    allow_high_breakout: bool
    pivot_wiggle: float                  # allow close to finish slightly below pivot (e.g. 0.005 = 0.5%)
    require_volume_confirm: bool
    avg_volume_lookback: int
    vol_mult: float

    # Risk / chasing guard
    max_extension: float
    fail_on_extended: bool

    # Computed metrics (most recent)
    pivot: Optional[float]
    close: Optional[float]
    high: Optional[float]
    volume: Optional[float]
    avg_volume: Optional[float]
    vol_ratio: Optional[float]

    base_start: Optional[str]
    base_end: Optional[str]
    base_high: Optional[float]
    base_low: Optional[float]
    base_depth: Optional[float]

    # Boolean sub-checks
    base_ok: bool
    breakout_ok: bool
    volume_ok: bool
    extended: bool

    # Aggregates
    setup: bool
    trigger: bool
    signal: bool

    # Diagnostics
    reasons: Tuple[str, ...]

    # Data sufficiency
    days_used: int


def _mean_last(values: List[float], window: int) -> Optional[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    w = values[-window:]
    return sum(w) / window


def _detect_base_simple(
    dates: List[str],
    highs: List[float],
    lows: List[float],
    base_lookback_days: int,
    min_base_len_bars: int,
    min_depth: float,
    max_depth: float,
) -> Tuple[Optional[Dict[str, Any]], Tuple[str, ...]]:
    """
    v1 base detector:
      - consider last `base_lookback_days` bars (trading days)
      - base starts at the lowest low within that window
      - pivot = max(high) from base_start to now
      - filter by base length and depth
    """
    reasons: List[str] = []
    n = len(dates)
    if n == 0:
        return None, ("No bars available",)

    start_i = max(0, n - base_lookback_days)
    window_lows = lows[start_i:]
    if not window_lows:
        return None, ("No lows in base window",)

    rel_low_i = min(range(len(window_lows)), key=lambda i: window_lows[i])
    low_i = start_i + rel_low_i

    base_len = n - low_i
    if base_len < min_base_len_bars:
        return None, (f"Base too short: {base_len} bars < {min_base_len_bars}",)

    base_high = max(highs[low_i:])
    base_low = min(lows[low_i:])

    if base_high <= 0:
        return None, ("Invalid base_high <= 0",)

    depth = (base_high - base_low) / base_high
    if depth < min_depth or depth > max_depth:
        return None, (f"Base depth {depth:.3f} outside [{min_depth:.3f}, {max_depth:.3f}]",)

    info = {
        "base_start": dates[low_i],
        "base_end": dates[-1],
        "base_high": float(base_high),
        "base_low": float(base_low),
        "base_depth": float(depth),
        "pivot": float(base_high),
    }

    reasons.append(f"Base: {info['base_start']} → {info['base_end']} (len={base_len})")
    reasons.append(f"Depth: {depth:.3f} within [{min_depth:.3f}, {max_depth:.3f}]")
    reasons.append(f"Pivot=base_high {info['pivot']:.2f}")

    return info, tuple(reasons)


async def pivot_signal_eod_trading_days(
    tradier: "TradierClient",
    symbol: str,
    *,
    end: Optional[date] = None,
    lookback_calendar_days: int = 260,

    # Base / pivot
    base_lookback_days: int = 90,
    min_base_len_bars: int = 15,
    min_depth: float = 0.05,            # loosen default
    max_depth: float = 0.45,            # loosen default

    # Breakout looseners
    allow_high_breakout: bool = True,
    pivot_wiggle: float = 0.005,

    # Volume confirm (optional)
    require_volume_confirm: bool = False,
    avg_volume_lookback: int = 50,
    vol_mult: float = 1.10,

    # "Don't chase" (optional)
    max_extension: float = 0.08,
    fail_on_extended: bool = False,
) -> PivotSignal:
    """
    EOD pivot detector (Stage 2 handled elsewhere).

    Returns:
      setup   = base_ok
      trigger = setup and breakout_ok
      signal  = trigger gated by optional volume + optional extension fail

    Intended usage:
      - stage2_candidates = ...
      - pivot = await pivot_signal_eod_trading_days(...)
      - buy_candidates = stage2_ok AND pivot.signal
    """
    if not symbol or not symbol.strip():
        raise ValueError("symbol is required")

    end = end or date.today()
    start = end - timedelta(days=lookback_calendar_days)
    sym = symbol.strip().upper()

    payload: Dict[str, Any] = await tradier.get_json(
        "/markets/history",
        params={"symbol": sym, "start": start.isoformat(), "end": end.isoformat(), "interval": "daily"},
    )

    history = (payload or {}).get("history") or {}
    days = history.get("day")

    if not days:
        return PivotSignal(
            symbol=sym,
            asof="",
            base_lookback_days=base_lookback_days,
            min_base_len_bars=min_base_len_bars,
            min_depth=min_depth,
            max_depth=max_depth,
            allow_high_breakout=allow_high_breakout,
            pivot_wiggle=pivot_wiggle,
            require_volume_confirm=require_volume_confirm,
            avg_volume_lookback=avg_volume_lookback,
            vol_mult=vol_mult,
            max_extension=max_extension,
            fail_on_extended=fail_on_extended,
            pivot=None,
            close=None,
            high=None,
            volume=None,
            avg_volume=None,
            vol_ratio=None,
            base_start=None,
            base_end=None,
            base_high=None,
            base_low=None,
            base_depth=None,
            base_ok=False,
            breakout_ok=False,
            volume_ok=False,
            extended=False,
            setup=False,
            trigger=False,
            signal=False,
            reasons=("No history returned from Tradier",),
            days_used=0,
        )

    if isinstance(days, dict):
        days = [days]

    days_sorted = sorted(days, key=lambda d: d.get("date", ""))

    dates: List[str] = []
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
        dates.append(str(dt))
        highs.append(float(h))
        lows.append(float(l))
        closes.append(float(c))
        volumes.append(float(v))
        asof = str(dt)

    n = len(closes)
    if n == 0:
        return PivotSignal(
            symbol=sym,
            asof="",
            base_lookback_days=base_lookback_days,
            min_base_len_bars=min_base_len_bars,
            min_depth=min_depth,
            max_depth=max_depth,
            allow_high_breakout=allow_high_breakout,
            pivot_wiggle=pivot_wiggle,
            require_volume_confirm=require_volume_confirm,
            avg_volume_lookback=avg_volume_lookback,
            vol_mult=vol_mult,
            max_extension=max_extension,
            fail_on_extended=fail_on_extended,
            pivot=None,
            close=None,
            high=None,
            volume=None,
            avg_volume=None,
            vol_ratio=None,
            base_start=None,
            base_end=None,
            base_high=None,
            base_low=None,
            base_depth=None,
            base_ok=False,
            breakout_ok=False,
            volume_ok=False,
            extended=False,
            setup=False,
            trigger=False,
            signal=False,
            reasons=("No usable bars after filtering missing fields",),
            days_used=0,
        )

    reasons: List[str] = []

    # Volume confirmation (optional; uses prior N bars excluding today)
    avg_vol = _mean_last(volumes[:-1], avg_volume_lookback) if len(volumes) >= avg_volume_lookback + 1 else None
    vol = float(volumes[-1])
    vol_ratio = (vol / avg_vol) if (avg_vol is not None and avg_vol > 0) else None

    volume_ok = False
    if not require_volume_confirm:
        volume_ok = True
        reasons.append("Volume confirm disabled")
    else:
        if avg_vol is None:
            reasons.append(f"Not enough volume history: have {len(volumes)} bars, need {avg_volume_lookback + 1}")
            volume_ok = False
        else:
            volume_ok = (vol_ratio is not None) and (vol_ratio >= vol_mult)
            if volume_ok:
                reasons.append(f"Volume OK: vol_ratio {vol_ratio:.2f} >= {vol_mult:.2f}")
            else:
                reasons.append(f"Volume NOT OK: vol_ratio {vol_ratio:.2f} < {vol_mult:.2f}")

    # Base / pivot
    base_info, base_reasons = _detect_base_simple(
        dates=dates,
        highs=highs,
        lows=lows,
        base_lookback_days=base_lookback_days,
        min_base_len_bars=min_base_len_bars,
        min_depth=min_depth,
        max_depth=max_depth,
    )
    reasons.extend(list(base_reasons))

    base_ok = base_info is not None
    pivot = float(base_info["pivot"]) if base_ok else None

    close_now = float(closes[-1])
    high_now = float(highs[-1])

    breakout_ok = False
    extended = False

    if not base_ok or pivot is None:
        reasons.append("Base not found => cannot compute pivot/breakout")
    else:
        if allow_high_breakout:
            breakout_ok = (high_now > pivot) and (close_now >= pivot * (1.0 - pivot_wiggle))
            reasons.append(
                f"Breakout check high>pivot and close>=pivot*(1-w): high {high_now:.2f}, close {close_now:.2f}, pivot {pivot:.2f}"
            )
        else:
            breakout_ok = close_now > pivot
            reasons.append(f"Breakout check close>pivot: close {close_now:.2f} vs pivot {pivot:.2f}")

        extended = close_now > pivot * (1.0 + max_extension)
        if extended:
            reasons.append(f"Extended: close {close_now:.2f} > pivot*(1+ext) {pivot*(1.0+max_extension):.2f}")
        else:
            reasons.append(f"Not extended: close {close_now:.2f} <= pivot*(1+ext) {pivot*(1.0+max_extension):.2f}")

    setup = bool(base_ok)
    trigger = bool(setup and breakout_ok)

    if fail_on_extended:
        signal = bool(trigger and volume_ok and (not extended))
    else:
        signal = bool(trigger and volume_ok)

    if signal:
        reasons.append("Signal TRUE")
    else:
        reasons.append("Signal FALSE")

    return PivotSignal(
        symbol=sym,
        asof=asof,
        base_lookback_days=base_lookback_days,
        min_base_len_bars=min_base_len_bars,
        min_depth=min_depth,
        max_depth=max_depth,
        allow_high_breakout=allow_high_breakout,
        pivot_wiggle=pivot_wiggle,
        require_volume_confirm=require_volume_confirm,
        avg_volume_lookback=avg_volume_lookback,
        vol_mult=vol_mult,
        max_extension=max_extension,
        fail_on_extended=fail_on_extended,
        pivot=pivot,
        close=close_now,
        high=high_now,
        volume=vol,
        avg_volume=float(avg_vol) if avg_vol is not None else None,
        vol_ratio=float(vol_ratio) if vol_ratio is not None else None,
        base_start=str(base_info["base_start"]) if base_ok else None,
        base_end=str(base_info["base_end"]) if base_ok else None,
        base_high=float(base_info["base_high"]) if base_ok else None,
        base_low=float(base_info["base_low"]) if base_ok else None,
        base_depth=float(base_info["base_depth"]) if base_ok else None,
        base_ok=base_ok,
        breakout_ok=bool(breakout_ok),
        volume_ok=bool(volume_ok),
        extended=bool(extended),
        setup=setup,
        trigger=trigger,
        signal=signal,
        reasons=tuple(reasons),
        days_used=n,
    )

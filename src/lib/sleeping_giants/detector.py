"""
Sleeping Giants detector — the shared, point-in-time gate logic.

Operationalizes Tito interview Note 2 ("compressed IV after a multi-year base ->
buy cheap LEAPS on the breakout"). This module is the single source of truth for the
gates; both the live scanner (run_sleeping_giants.py) and the backtest
(run_sleeping_giants_backtest.py) import `analyze()` from here.

This first pass uses REALIZED-vol compression as a proxy for the cheap-IV condition.
The IV-rank gate (Athena) is layered on separately.

The five gates:
  1. GIANT      — implicit via the large-cap universe the caller scans.
  2. SLEEPING   — ATR% in the bottom ATR_RANK_MAX of its multi-year (ATR_PCT_LOOKBACK)
                  history AND ATR(ATR_PERIOD) < ATR(ATR_SLOW_PERIOD).
  3. CAN WAKE   — multi-year H-L range >= MULTIYEAR_RANGE_MIN % of price.
  4. COILING    — price within the top (100 - POS_IN_BASE_MIN)% of its multi-year range.
  5. MULTI-YEAR — base has been working for >= BASE_LEN_MIN_YRS years.

`analyze(highs, lows, closes)` evaluates at the LAST bar of whatever series it is given,
so a backtest gets a point-in-time read simply by passing a truncated slice.

Reuses the tested ATR/percentile helpers from lib.commons.vol_compression.
"""
from __future__ import annotations

from typing import Optional, Dict, List

from lib.commons.vol_compression import (
    _true_range_series,
    _wilder_rma,
    _percentile_rank_of_last,
    _mean_last,
)

# ---- Gate parameters ----
ATR_PCT_LOOKBACK = 756          # ~3yr of trading days for the percentile rank
ATR_PERIOD = 14
ATR_SLOW_PERIOD = 50
ATR_RANK_MAX = 0.25             # SLEEPING: ATR% in bottom 25% of its multi-year history
MULTIYEAR_RANGE_MIN = 50.0      # CAN WAKE: multi-year H-L >= 50% of current price
BASE_PROXIMITY = 0.05           # "within 5% of resistance" counts as working the base
POS_IN_BASE_MIN = 80.0          # COILING: price within top 20% of its multi-year range
BASE_LEN_MIN_YRS = 1.5          # MULTI-YEAR: base has been working for >= 1.5 years

TRADING_DAYS_PER_YEAR = 252


def to_floats(series) -> List[float]:
    return [float(x) for x in series]


def analyze(highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict]:
    """Compute the five gates + diagnostics at the LAST bar of the given series.
    Returns a dict, or None if there is insufficient history."""
    n = len(closes)
    if n < ATR_PCT_LOOKBACK // 2:   # need a meaningful multi-year window
        return None

    close_now = closes[-1]
    if close_now <= 0:
        return None

    # --- ATR / ATR% ---
    tr = _true_range_series(highs, lows, closes)
    tr_full = [float(t) for t in tr if t is not None]
    atr_series = _wilder_rma(tr_full, ATR_PERIOD)
    atr_slow_series = _wilder_rma(tr_full, ATR_SLOW_PERIOD)

    i = n - 1
    while i >= 0 and (atr_series[i] is None or atr_slow_series[i] is None):
        i -= 1
    if i < 0:
        return None

    atr_now = atr_series[i]
    atr_slow_now = atr_slow_series[i]

    atr_pct_series: List[float] = []
    for j in range(n):
        a = atr_series[j]
        c = closes[j]
        if a is None or c == 0:
            continue
        atr_pct_series.append(a / c)
    atr_pct_now = atr_now / close_now

    atr_rank = _percentile_rank_of_last(atr_pct_series, ATR_PCT_LOOKBACK)

    # --- Gate 2: SLEEPING ---
    atr_rank_ok = (atr_rank is not None) and (atr_rank <= ATR_RANK_MAX)
    atr_vs_slow_ok = atr_now < atr_slow_now
    sleeping = atr_rank_ok and atr_vs_slow_ok

    # --- Gate 3: CAN WAKE (multi-year H-L range) ---
    hi = max(highs)
    lo = min(lows)
    multiyr_range_pct = (hi - lo) / close_now * 100.0
    can_wake = multiyr_range_pct >= MULTIYEAR_RANGE_MIN

    # --- Base length: time spent working under current resistance R = window high ---
    prox = hi * (1 - BASE_PROXIMITY)
    base_start_idx = next((k for k in range(n) if highs[k] >= prox), n - 1)
    base_len_days = (n - 1) - base_start_idx
    base_len_yrs = base_len_days / TRADING_DAYS_PER_YEAR
    base_capped = base_start_idx == 0

    # --- Gates 4 & 5: COILING near resistance + MULTI-YEAR base length ---
    pos_in_base = (close_now - lo) / (hi - lo) * 100.0 if hi > lo else 0.0
    pct_below_high = (hi - close_now) / hi * 100.0
    coiling_ok = pos_in_base >= POS_IN_BASE_MIN
    base_len_ok = base_len_yrs >= BASE_LEN_MIN_YRS

    # --- Diagnostics (not gates) ---
    daily_range_pct = [(highs[k] - lows[k]) / closes[k] for k in range(n) if closes[k] != 0]
    r5 = _mean_last(daily_range_pct, 5)
    r20 = _mean_last(daily_range_pct, 20)
    r60 = _mean_last(daily_range_pct, 60)
    range_chain_ok = (r5 is not None and r20 is not None and r60 is not None
                      and r5 < r20 < r60)

    is_sleeping_giant = sleeping and can_wake and coiling_ok and base_len_ok

    return {
        "atr_rank": atr_rank,
        "atr_pct_now": atr_pct_now,
        "atr_rank_ok": atr_rank_ok,
        "atr_vs_slow_ok": atr_vs_slow_ok,
        "sleeping": sleeping,
        "multiyr_range_pct": multiyr_range_pct,
        "can_wake": can_wake,
        "pos_in_base": pos_in_base,
        "pct_below_high": pct_below_high,
        "coiling_ok": coiling_ok,
        "base_len_ok": base_len_ok,
        "range_chain_ok": range_chain_ok,
        "base_len_yrs": base_len_yrs,
        "base_capped": base_capped,
        "resistance": hi,          # R = multi-year-window high at this point in time
        "close": close_now,
        "is_sleeping_giant": is_sleeping_giant,
    }

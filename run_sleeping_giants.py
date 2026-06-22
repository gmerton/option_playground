#!/usr/bin/env python3
"""
Sleeping Giants scanner (first pass — RV proxy for the IV gate).

Operationalizes Tito interview Note 2: "compressed IV after a multi-year base ->
buy cheap LEAPS on the breakout." This first pass uses REALIZED-vol compression as a
proxy for the cheap-IV condition (fast, no Athena join). The IV-rank gate — the actual
heart of Note 2 — is layered on next, before we trust any results.

Three gates:
  1. GIANT     — implicit via the large-cap universe below (liquidity + real LEAPS chains).
  2. SLEEPING  — realized-vol compression: ATR% in the bottom ATR_RANK_MAX of its
                 multi-year (ATR_PCT_LOOKBACK) history AND ATR(14) < ATR(50).
  3. CAN WAKE  — multi-year H-L range >= MULTIYEAR_RANGE_MIN % of price (it HAS moved big).

Diagnostics (not gates): position-in-base (price vs 3yr high), range-contraction chain.
Sorted most-compressed first.

Reuses tested helpers from lib.commons.vol_compression.
"""

import asyncio
import sys
from datetime import date, timedelta
from typing import Optional, Dict, List
import os

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
from lib.commons.vol_compression import (
    _true_range_series,
    _wilder_rma,
    _percentile_rank_of_last,
    _mean_last,
)

# ---- Gate parameters ----
LOOKBACK_CALENDAR_DAYS = 1500   # ~4yr calendar -> ~3yr trading + buffer
ATR_PCT_LOOKBACK = 756          # ~3yr of trading days for the percentile rank
ATR_PERIOD = 14
ATR_SLOW_PERIOD = 50
ATR_RANK_MAX = 0.25             # SLEEPING: ATR% in bottom 25% of its multi-year history
MULTIYEAR_RANGE_MIN = 50.0      # CAN WAKE: 3yr H-L >= 50% of current price
BASE_PROXIMITY = 0.05           # "within 5% of resistance" counts as working the base
POS_IN_BASE_MIN = 80.0          # COILING: price within top 20% of its multi-year range (near resistance)
BASE_LEN_MIN_YRS = 1.5          # MULTI-YEAR: base has been working for >= 1.5 years

# ---- Universe: sector-diverse large caps (the GIANT gate is implicit) ----
# Deliberately spread across sectors so we can see whether the signal is an
# energy-2026 artifact or a real cross-sector pattern.
UNIVERSE = [
    # Mega tech / comms
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AVGO", "ORCL", "CRM", "ADBE",
    "CSCO", "QCOM", "TXN", "INTC", "IBM", "NFLX", "AMD",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA",
    # Healthcare
    "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "BMY", "AMGN",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY",
    # Industrials
    "CAT", "DE", "BA", "HON", "GE", "UPS", "LMT", "RTX",
    # Staples / discretionary
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "HD", "NKE", "DIS",
    # Materials / utilities
    "LIN", "FCX", "NEM", "NEE", "DUK",
    # Sector ETFs (XLE was an actual Note-2 example)
    "XLE", "XLF", "XLV", "XLI", "XLK", "XLP", "XLU", "GLD", "SLV",
]


def _to_floats(series) -> List[float]:
    return [float(x) for x in series]


async def fetch_history(client: TradierClient, ticker: str, asof: date):
    """Fetch multi-year daily bars ending at `asof` (point-in-time, no lookahead).
    Returns (highs, lows, closes, dates) or None."""
    end = asof
    start = end - timedelta(days=LOOKBACK_CALENDAR_DAYS)
    df = await get_daily_history(ticker, start, end, client=client)
    if df is None or df.empty:
        return None
    df = df.reset_index().sort_values("date")
    try:
        highs = _to_floats(df["high"])
        lows = _to_floats(df["low"])
        closes = _to_floats(df["close"])
    except Exception:
        return None
    dates = list(df["date"])
    return highs, lows, closes, dates


def analyze(highs, lows, closes) -> Optional[Dict]:
    """Compute the three gates + diagnostics. Returns a dict or None if insufficient data."""
    n = len(closes)
    if n < ATR_PCT_LOOKBACK // 2:   # need a meaningful multi-year window
        return None

    close_now = closes[-1]
    if close_now <= 0:
        return None

    # --- ATR / ATR% (mirror vol_compression) ---
    tr = _true_range_series(highs, lows, closes)
    tr_full = [float(t) for t in tr if t is not None]
    atr_series = _wilder_rma(tr_full, ATR_PERIOD)
    atr_slow_series = _wilder_rma(tr_full, ATR_SLOW_PERIOD)

    # last index with both defined
    i = n - 1
    while i >= 0 and (atr_series[i] is None or atr_slow_series[i] is None):
        i -= 1
    if i < 0:
        return None

    atr_now = atr_series[i]
    atr_slow_now = atr_slow_series[i]

    # ATR% series for percentile rank
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
    hi_3y = max(highs)
    lo_3y = min(lows)
    multiyr_range_pct = (hi_3y - lo_3y) / close_now * 100.0
    can_wake = multiyr_range_pct >= MULTIYEAR_RANGE_MIN

    # --- Base length: time spent working under current resistance R = window high ---
    # First bar whose high reached within BASE_PROXIMITY of R; base length = that bar -> now.
    # (Censored at the fetch window; endpoint-sensitive, same as pos_in_base.)
    prox = hi_3y * (1 - BASE_PROXIMITY)
    base_start_idx = next((k for k in range(n) if highs[k] >= prox), n - 1)
    base_len_days = (n - 1) - base_start_idx
    base_len_yrs = base_len_days / 252.0
    base_capped = base_start_idx == 0   # base extends to/beyond the fetch window

    # --- Gates 4 & 5: COILING near resistance + MULTI-YEAR base length ---
    # position in base: how close is price to the 3yr high? (near top = coiling under resistance)
    pos_in_base = (close_now - lo_3y) / (hi_3y - lo_3y) * 100.0 if hi_3y > lo_3y else 0.0
    pct_below_3y_high = (hi_3y - close_now) / hi_3y * 100.0
    coiling_ok = pos_in_base >= POS_IN_BASE_MIN
    base_len_ok = base_len_yrs >= BASE_LEN_MIN_YRS

    # --- Diagnostics (not gates) ---
    # range-contraction chain (Minervini 5<20<60)
    daily_range_pct = [(highs[k] - lows[k]) / closes[k] for k in range(n) if closes[k] != 0]
    r5 = _mean_last(daily_range_pct, 5)
    r20 = _mean_last(daily_range_pct, 20)
    r60 = _mean_last(daily_range_pct, 60)
    range_chain_ok = (r5 is not None and r20 is not None and r60 is not None
                      and r5 < r20 < r60)

    return {
        "atr_rank": atr_rank,
        "atr_pct_now": atr_pct_now,
        "atr_rank_ok": atr_rank_ok,
        "atr_vs_slow_ok": atr_vs_slow_ok,
        "sleeping": sleeping,
        "multiyr_range_pct": multiyr_range_pct,
        "can_wake": can_wake,
        "pos_in_base": pos_in_base,
        "pct_below_3y_high": pct_below_3y_high,
        "coiling_ok": coiling_ok,
        "base_len_ok": base_len_ok,
        "range_chain_ok": range_chain_ok,
        "base_len_yrs": base_len_yrs,
        "base_capped": base_capped,
        "close": close_now,
    }


async def scan_ticker(client: TradierClient, ticker: str, asof: date) -> Optional[Dict]:
    hist = await fetch_history(client, ticker, asof)
    if hist is None:
        return None
    highs, lows, closes, _dates = hist
    result = analyze(highs, lows, closes)
    if result is None:
        return None
    result["ticker"] = ticker
    return result


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set")
        sys.exit(1)

    # Optional as-of date for point-in-time scans: --asof YYYY-MM-DD
    asof = date.today()
    if "--asof" in sys.argv:
        asof = date.fromisoformat(sys.argv[sys.argv.index("--asof") + 1])

    print(f"Sleeping Giants scan — {len(UNIVERSE)} large caps  (as-of {asof.isoformat()})")
    print(f"SLEEPING: ATR% in bottom {ATR_RANK_MAX:.0%} of {ATR_PCT_LOOKBACK}d  &  ATR(14)<ATR(50)")
    print(f"CAN WAKE: multi-year range >= {MULTIYEAR_RANGE_MIN:.0f}% of price")
    print("=" * 78)

    passed: List[Dict] = []
    all_results: List[Dict] = []
    scanned = 0
    no_data = []

    async with TradierClient(api_key=api_key) as client:
        for ticker in UNIVERSE:
            r = await scan_ticker(client, ticker, asof)
            scanned += 1
            if r is None:
                no_data.append(ticker)
                continue
            all_results.append(r)
            if r["sleeping"] and r["can_wake"] and r["coiling_ok"] and r["base_len_ok"]:
                passed.append(r)

    # --- Per-gate diagnostics (why did/didn't things pass?) ---
    n_rank_ok = sum(1 for r in all_results if r["atr_rank_ok"])
    n_slow_ok = sum(1 for r in all_results if r["atr_vs_slow_ok"])
    n_sleeping = sum(1 for r in all_results if r["sleeping"])
    n_can_wake = sum(1 for r in all_results if r["can_wake"])
    n_coiling = sum(1 for r in all_results if r["coiling_ok"])
    n_base_len = sum(1 for r in all_results if r["base_len_ok"])
    print("Per-gate pass counts (of {} with data):".format(len(all_results)))
    print(f"  ATR%rank <= {ATR_RANK_MAX:.0%}:        {n_rank_ok}")
    print(f"  ATR(14) < ATR(50):         {n_slow_ok}")
    print(f"  SLEEPING (both):           {n_sleeping}")
    print(f"  CAN WAKE (range):          {n_can_wake}")
    print(f"  COILING (PosInBase>={POS_IN_BASE_MIN:.0f}%):   {n_coiling}")
    print(f"  MULTI-YEAR (base>={BASE_LEN_MIN_YRS:.1f}y):    {n_base_len}")
    print()

    # Dump the 15 most-compressed regardless of gates, to eyeball thresholds
    diag = sorted(all_results, key=lambda r: (r["atr_rank"] if r["atr_rank"] is not None else 9))
    print("15 most-compressed (by ATR%rank), gates aside:")
    print(f"{'TICKER':<7} {'ATR%rank':>8} {'ATR<slow':>9} {'3yrRange':>9} {'CanWake':>8} {'PosInBase':>9} {'BaseLen':>8}")
    for r in diag[:15]:
        rank = r["atr_rank"] * 100 if r["atr_rank"] is not None else float('nan')
        cap = "+" if r["base_capped"] else " "
        print(f"{r['ticker']:<7} {rank:>7.0f}% {str(r['atr_vs_slow_ok']):>9} "
              f"{r['multiyr_range_pct']:>8.0f}% {str(r['can_wake']):>8} {r['pos_in_base']:>8.0f}% "
              f"{r['base_len_yrs']:>6.1f}y{cap}")
    print()

    # Sort most-compressed first
    passed.sort(key=lambda r: r["atr_rank"])

    print(f"\n{'TICKER':<7} {'ATR%rank':>8} {'ATR%':>6} {'3yrRange':>9} "
          f"{'PosInBase':>9} {'%BelowHi':>8} {'BaseLen':>8} {'RangeChain':>10}")
    print("-" * 86)
    for r in passed:
        cap = "+" if r["base_capped"] else " "
        print(f"{r['ticker']:<7} {r['atr_rank']*100:>7.0f}% {r['atr_pct_now']*100:>5.1f}% "
              f"{r['multiyr_range_pct']:>8.0f}% {r['pos_in_base']:>8.0f}% "
              f"{r['pct_below_3y_high']:>7.0f}% {r['base_len_yrs']:>6.1f}y{cap} {str(r['range_chain_ok']):>10}")

    print("\n" + "=" * 78)
    print(f"SLEEPING GIANTS: {len(passed)}/{scanned} scanned "
          f"({len(no_data)} no-data: {', '.join(no_data) if no_data else 'none'})")
    print("\nPosInBase ~100 = coiling near 3yr highs (constructive, watch for breakout);")
    print("PosInBase ~0   = compressed near 3yr lows (needs a base/turn first).")
    print("Next: layer the IV-rank gate (Athena) to confirm the cheap-LEAPS condition.")


if __name__ == "__main__":
    asyncio.run(main())

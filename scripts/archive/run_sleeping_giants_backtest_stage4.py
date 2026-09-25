#!/usr/bin/env python3
"""
Sleeping Giants backtest — STAGE 4: exit-rule study.

Stage 3 showed a ~150pp gap between naive-hold (median -9%) and MFE (median +142%):
the setup finds real moves but a mechanical hold gives them back. This stage simulates
realistic exit rules on the actual daily LEAP marks to find how much of that MFE is
harvestable.

Exit rules tested (per trade, on the real daily call mids entry->expiry):
  - HOLD          : to +180d-or-expiry, and to expiry (the Stage-3 baselines)
  - PT x%         : profit target, exit at entry*(1+x) when first touched, else expiry
  - TRAIL y%      : trail y% off the running peak (from entry), else expiry
  - ARM a% TRAIL y%: trail only after first reaching +a% (let it breathe, then trail)
  - 2REGIME pt/tr : Adhikary-style — take half at +pt%, trail the other half at y%

Marks are fetched once from Athena and cached to parquet so rule iteration is free.
Caveats: PT fills assumed at the target price; trail/stop fills at the breaching daily
mark (no intraday). Split-artifact entries (Stage-3 `incomplete`) excluded.

Usage: PYTHONPATH=src python run_sleeping_giants_backtest_stage4.py [--refetch]
"""
import sys
import os
from typing import Optional, List, Dict

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

import pandas as pd
import numpy as np

from run_sleeping_giants_backtest_stage3 import fetch_forward_marks

TRADES_CSV = "data/studies/Adhikary/sleeping_giants_trades.csv"
MARKS_CACHE = "data/studies/Adhikary/sleeping_giants_marks.parquet"


# ---------- exit-rule simulators (operate on ordered marks for one trade) ----------
def _roc(px, entry_mid):
    return (px - entry_mid) / entry_mid * 100.0


def sim_hold(d, m, entry_mid, horizon=None):
    if horizon is None:
        return _roc(m[-1], entry_mid)
    for di, mi in zip(d, m):
        if di >= horizon:
            return _roc(mi, entry_mid)
    return _roc(m[-1], entry_mid)


def sim_pt(d, m, entry_mid, pt_pct):
    target = entry_mid * (1 + pt_pct / 100.0)
    for mi in m:
        if mi >= target:
            return _roc(target, entry_mid)      # filled at the target
    return _roc(m[-1], entry_mid)               # never hit -> expiry


def sim_trail(d, m, entry_mid, trail_pct):
    peak = entry_mid
    for mi in m:
        peak = max(peak, mi)
        if mi <= peak * (1 - trail_pct / 100.0):
            return _roc(mi, entry_mid)
    return _roc(m[-1], entry_mid)


def sim_arm_trail(d, m, entry_mid, arm_pct, trail_pct):
    peak = entry_mid
    armed = False
    arm_level = entry_mid * (1 + arm_pct / 100.0)
    for mi in m:
        peak = max(peak, mi)
        if mi >= arm_level:
            armed = True
        if armed and mi <= peak * (1 - trail_pct / 100.0):
            return _roc(mi, entry_mid)
    return _roc(m[-1], entry_mid)


def sim_two_regime(d, m, entry_mid, pt_pct, trail_pct):
    """Take half at +pt%; trail the other half at trail% off the peak."""
    target = entry_mid * (1 + pt_pct / 100.0)
    peak = entry_mid
    half1 = None
    rest = None
    for mi in m:
        peak = max(peak, mi)
        if half1 is None and mi >= target:
            half1 = target
        if mi <= peak * (1 - trail_pct / 100.0):
            rest = mi
            break
    if rest is None:
        rest = m[-1]
    if half1 is None:
        return _roc(rest, entry_mid)            # PT never hit -> whole position trailed
    return _roc(0.5 * half1 + 0.5 * rest, entry_mid)


def summarize(rocs: np.ndarray) -> Dict:
    return {
        "n": len(rocs),
        "win%": (rocs > 0).mean() * 100,
        "median": float(np.median(rocs)),
        "mean": float(np.mean(rocs)),
    }


def main():
    trades = pd.read_csv(TRADES_CSV)
    trades = trades[~trades["incomplete"].fillna(False)].copy()
    trades["entry_date"] = pd.to_datetime(trades["entry_date"]).dt.date
    trades["expiry"] = pd.to_datetime(trades["expiry"]).dt.date
    print(f"Loaded {len(trades)} clean trades (split artifacts excluded)")

    # ---- marks: fetch once, cache ----
    if os.path.exists(MARKS_CACHE) and "--refetch" not in sys.argv:
        marks = pd.read_parquet(MARKS_CACHE)
        print(f"Loaded {len(marks)} cached marks from {MARKS_CACHE}")
    else:
        print("Fetching forward marks from Athena (caching)...")
        marks = fetch_forward_marks(trades)
        marks.to_parquet(MARKS_CACHE, index=False)
        print(f"Cached {len(marks)} marks -> {MARKS_CACHE}")

    marks["trade_date"] = pd.to_datetime(marks["trade_date"])

    # pre-build per-trade ordered (days, mark) arrays
    per_trade: Dict[int, Dict] = {}
    for _, t in trades.iterrows():
        g = marks[marks["row_id"] == t["row_id"]].sort_values("trade_date")
        if g.empty:
            continue
        d = (g["trade_date"] - pd.Timestamp(t["entry_date"])).dt.days.to_numpy()
        m = g["mark_mid"].to_numpy(dtype=float)
        per_trade[int(t["row_id"])] = {"d": d, "m": m, "entry_mid": float(t["entry_mid"]),
                                       "arm": t["arm"], "regime": t.get("regime", "?")}

    # ---- run rules ----
    rules = [
        ("HOLD +180d/expiry", lambda d, m, e: sim_hold(d, m, e, 180)),
        ("HOLD to expiry",    lambda d, m, e: sim_hold(d, m, e, None)),
        ("PT +50%",           lambda d, m, e: sim_pt(d, m, e, 50)),
        ("PT +100%",          lambda d, m, e: sim_pt(d, m, e, 100)),
        ("PT +200%",          lambda d, m, e: sim_pt(d, m, e, 200)),
        ("PT +300%",          lambda d, m, e: sim_pt(d, m, e, 300)),
        ("TRAIL 30%",         lambda d, m, e: sim_trail(d, m, e, 30)),
        ("TRAIL 40%",         lambda d, m, e: sim_trail(d, m, e, 40)),
        ("TRAIL 50%",         lambda d, m, e: sim_trail(d, m, e, 50)),
        ("ARM+50 TRAIL30",    lambda d, m, e: sim_arm_trail(d, m, e, 50, 30)),
        ("ARM+100 TRAIL40",   lambda d, m, e: sim_arm_trail(d, m, e, 100, 40)),
        ("2REGIME 200/40",    lambda d, m, e: sim_two_regime(d, m, e, 200, 40)),
        ("2REGIME 100/30",    lambda d, m, e: sim_two_regime(d, m, e, 100, 30)),
    ]

    def run(rule_fn, arm=None, regime=None):
        rocs = []
        for tr in per_trade.values():
            if arm and tr["arm"] != arm:
                continue
            if regime and tr["regime"] != regime:
                continue
            rocs.append(rule_fn(tr["d"], tr["m"], tr["entry_mid"]))
        return np.array(rocs)

    print("\n" + "=" * 76)
    print(f"{'RULE':<20} {'n':>4} {'win%':>6} {'median':>9} {'mean':>9}   (all clean trades)")
    print("=" * 76)
    for name, fn in rules:
        s = summarize(run(fn))
        print(f"{name:<20} {s['n']:>4} {s['win%']:>5.1f}% {s['median']:>8.1f}% {s['mean']:>8.1f}%")

    # MFE ceiling reference
    mfe = np.array([(tr["m"].max() - tr["entry_mid"]) / tr["entry_mid"] * 100 for tr in per_trade.values()])
    print(f"{'(MFE ceiling)':<20} {len(mfe):>4} {(mfe>0).mean()*100:>5.1f}% {np.median(mfe):>8.1f}% {np.mean(mfe):>8.1f}%")

    # best practical rules by arm
    print("\n" + "=" * 76)
    print("By arm — a few candidate rules")
    print("=" * 76)
    for name, fn in [("HOLD +180d/expiry", rules[0][1]), ("PT +100%", rules[3][1]),
                     ("ARM+50 TRAIL30", rules[9][1]), ("2REGIME 100/30", rules[12][1])]:
        for arm in ("A", "B"):
            s = summarize(run(fn, arm))
            print(f"  {name:<20} arm {arm}  n={s['n']:>3}  win={s['win%']:>5.1f}%  "
                  f"median={s['median']:>7.1f}%  mean={s['mean']:>7.1f}%")

    # ---- OOS check: does arm-then-trail hold pre-2022 (not just the 2023-24 bull)? ----
    rules_by_name = dict(rules)
    print("\n" + "=" * 76)
    print("OOS CHECK — arm-then-trail by REGIME (pre2022 = quasi-OOS, non-bull)")
    print("=" * 76)
    for name in ["HOLD +180d/expiry", "ARM+50 TRAIL30", "ARM+100 TRAIL40"]:
        fn = rules_by_name[name]
        for reg in ("pre2022_OOS", "2022plus"):
            s = summarize(run(fn, regime=reg))
            print(f"  {name:<18} {reg:<12} n={s['n']:>3}  win={s['win%']:>5.1f}%  "
                  f"median={s['median']:>7.1f}%  mean={s['mean']:>7.1f}%")
        print()

    print("=" * 76)
    print("Best cell (Arm B + ARM+50 TRAIL30) by REGIME")
    print("=" * 76)
    for reg in ("pre2022_OOS", "2022plus"):
        s = summarize(run(rules_by_name["ARM+50 TRAIL30"], arm="B", regime=reg))
        print(f"  Arm B ARM+50 TRAIL30  {reg:<12} n={s['n']:>3}  win={s['win%']:>5.1f}%  "
              f"median={s['median']:>7.1f}%  mean={s['mean']:>7.1f}%")

    print("\nFloor = HOLD (Stage 3). Ceiling = MFE (unreachable). "
          "Best rule = most of the MFE captured at a tradeable win rate.")


if __name__ == "__main__":
    main()

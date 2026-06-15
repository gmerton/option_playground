#!/usr/bin/env python3
"""Sweep EMA (fast, slow) pairs for the crossover, holding the validated config
(close>VWAP + open-hour) fixed, pooled across the whole cache.

The point is NOT to pick the single best pair (that's curve-fitting one number)
-- it's to see whether there's a STABLE NEIGHBORHOOD of good pairs (a plateau =
robust) or a lone spike (= luck). A flat surface also tells us trigger-tuning
doesn't matter much, consistent with "the trigger can't buy precision."

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_pairs.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_pairs.py --metric avg
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_backtest import backtest  # noqa: E402

FASTS = [5, 8, 9, 12, 15, 20]
SLOWS = [13, 20, 21, 26, 34, 50]
BASE = {"trend_vwap": True, "entry_before": "10:30"}   # held-fixed validated config


def pf(pnls):
    gw = sum(p for p in pnls if p > 0)
    gl = -sum(p for p in pnls if p <= 0)
    return (gw / gl) if gl else float("inf")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--metric", default="pf", choices=["pf", "avg", "total", "win"])
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    sessions = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, g in df.groupby(df["time"].dt.date):
            if len(g) >= a.min_bars:
                sessions.append(g.sort_values("time").reset_index(drop=True))

    print(f"\n9/20-EMA crossover -- (fast,slow) pair sweep   "
          f"[base: close>VWAP + open-hour, {len(sessions)} sessions]")
    print(f"metric = {a.metric}  (rows=fast EMA, cols=slow EMA; '.' = fast>=slow)\n")
    # compute grid
    grid = {}
    for fa in FASTS:
        for sl in SLOWS:
            if fa >= sl:
                continue
            pnls = []
            for sess in sessions:
                tr, _ = backtest(sess, fast_span=fa, slow_span=sl, **BASE)
                pnls += [t["ret_pct"] for t in tr]
            wins = [p for p in pnls if p > 0]
            grid[(fa, sl)] = {
                "pf": pf(pnls),
                "avg": sum(pnls) / len(pnls) if pnls else 0.0,
                "total": sum(pnls),
                "win": 100 * len(wins) / len(pnls) if pnls else 0.0,
                "n": len(pnls),
            }

    # print as matrix
    print("  fast\\slow " + "".join(f"{sl:>9}" for sl in SLOWS))
    for fa in FASTS:
        cells = []
        for sl in SLOWS:
            if (fa, sl) not in grid:
                cells.append(f"{'.':>9}")
                continue
            v = grid[(fa, sl)][a.metric]
            cells.append(f"{v:>9.2f}" if a.metric != "n" else f"{v:>9.0f}")
        print(f"  {fa:>6}    " + "".join(cells))

    # highlight default 9/20 and the best
    d = grid.get((9, 20))
    best = max(grid.items(), key=lambda kv: kv[1][a.metric])
    print(f"\n  default 9/20: PF {d['pf']:.2f}  avg {d['avg']:+.2f}  "
          f"win {d['win']:.1f}  total {d['total']:+.1f}  n {d['n']}")
    bk, bv = best
    print(f"  best {a.metric}: pair {bk}  PF {bv['pf']:.2f}  avg {bv['avg']:+.2f}  "
          f"win {bv['win']:.1f}  total {bv['total']:+.1f}  n {bv['n']}")
    print("\n  Look for a PLATEAU (many neighbors near the top), not a lone spike.")
    print("  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

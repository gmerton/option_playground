#!/usr/bin/env python3
"""Entry/exit ANTICIPATION band sweep for the crossover.

Spread s = (ema_fast - ema_slow)/price*100 (pct pts). Plain crossover = enter on
up-cross of 0, exit on down-cross of 0. This sweeps a band around 0:

  enter_th <= 0  -- enter BEFORE the real cross (anticipate; more false starts)
  exit_th  >= 0  -- exit BEFORE the real down-cross (lock the trend, less giveback)

(0, 0) == the plain crossover (verified to reproduce baseline exactly). Grid rows
= enter_th, cols = exit_th. Base config held fixed: close>VWAP + open-hour + 12/34.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_anticipate.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_anticipate.py --metric avg
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

BASE = {"trend_vwap": True, "entry_before": "10:30", "fast_span": 12, "slow_span": 34}
ENTERS = [-0.15, -0.10, -0.05, 0.0]
EXITS = [0.0, 0.05, 0.10, 0.15]


def pf(pnls):
    gw = sum(p for p in pnls if p > 0)
    gl = -sum(p for p in pnls if p <= 0)
    return (gw / gl) if gl else float("inf")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--metric", default="pf", choices=["pf", "avg", "win", "total", "n"])
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    sessions = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, g in df.groupby(df["time"].dt.date):
            if len(g) >= a.min_bars:
                sessions.append(g.sort_values("time").reset_index(drop=True))

    grid = {}
    for en in ENTERS:
        for ex in EXITS:
            pnls = []
            for sess in sessions:
                tr, _ = backtest(sess, enter_th=en, exit_th=ex, **BASE)
                pnls += [t["ret_pct"] for t in tr]
            wins = [p for p in pnls if p > 0]
            grid[(en, ex)] = {
                "pf": pf(pnls), "avg": sum(pnls) / len(pnls) if pnls else 0.0,
                "win": 100 * len(wins) / len(pnls) if pnls else 0.0,
                "total": sum(pnls), "n": len(pnls),
            }

    print(f"\nEntry/exit ANTICIPATION band -- metric={a.metric}   "
          f"[base VWAP+openhr+12/34, {len(sessions)} sessions]")
    print(f"  rows = enter_th (<=0 anticipate entry), cols = exit_th (>=0 exit early)")
    print(f"  (0.00, 0.00) = plain crossover\n")
    print("  enter\\exit " + "".join(f"{ex:>9.2f}" for ex in EXITS))
    for en in ENTERS:
        cells = []
        for ex in EXITS:
            v = grid[(en, ex)][a.metric]
            cells.append(f"{v:>9.0f}" if a.metric == "n" else f"{v:>9.2f}")
        print(f"  {en:>7.2f}   " + "".join(cells))

    b = grid[(0.0, 0.0)]
    best = max(grid.items(), key=lambda kv: kv[1][a.metric])
    print(f"\n  plain (0,0): PF {b['pf']:.2f}  avg {b['avg']:+.2f}  win {b['win']:.1f}  "
          f"total {b['total']:+.1f}  n {b['n']}")
    (be, bx), bv = best
    print(f"  best {a.metric}: enter {be:+.2f} exit {bx:+.2f} -> PF {bv['pf']:.2f}  "
          f"avg {bv['avg']:+.2f}  win {bv['win']:.1f}  total {bv['total']:+.1f}  n {bv['n']}")
    print("\n  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

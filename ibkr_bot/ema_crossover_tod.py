#!/usr/bin/env python3
"""Does time-of-day matter for the 9/20-EMA crossover?

Pools every crossover trade across the cache and buckets it by ENTRY time into
30-minute slots, reporting two distinct things:

  |move|  -- mean |ret%| per trade : are the MOVES bigger in the morning?
  edge    -- win% / avg% / PF      : is the strategy better at that hour?

(Move-size and edge are different questions: mornings can have bigger moves AND
a better hit rate, or bigger-but-choppier moves. We separate them.)

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_tod.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_tod.py --config "trend: close>VWAP"
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_backtest import PRESETS, backtest  # noqa: E402


def slot(hhmm: str) -> str:
    """Map 'HH:MM' to its 30-min bucket label, e.g. '09:30'."""
    h, m = int(hhmm[:2]), int(hhmm[3:])
    m0 = 0 if m < 30 else 30
    return f"{h:02d}:{m0:02d}"


def stats(pnls: list[float]) -> dict:
    wins = [p for p in pnls if p > 0]
    gw = sum(wins)
    gl = -sum(p for p in pnls if p <= 0)
    return {
        "n": len(pnls),
        "win": 100 * len(wins) / len(pnls) if pnls else 0.0,
        "avg": sum(pnls) / len(pnls) if pnls else 0.0,
        "absmove": sum(abs(p) for p in pnls) / len(pnls) if pnls else 0.0,
        "total": sum(pnls),
        "pf": (gw / gl) if gl else float("inf"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--config", default="baseline (no filter)")
    a = ap.parse_args()

    kw = dict(PRESETS).get(a.config)
    if kw is None:
        print(f"unknown config '{a.config}'. options: {[n for n, _ in PRESETS]}")
        return 2

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    by_slot: dict[str, list[float]] = {}
    sessions = 0
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            sessions += 1
            trades, _ = backtest(g, **kw)
            for t in trades:
                by_slot.setdefault(slot(t["entry_t"]), []).append(t["ret_pct"])

    all_pnls = [p for ps in by_slot.values() for p in ps]
    grand = len(all_pnls)
    print(f"\n9/20 EMA crossover by ENTRY time-of-day  [config: {a.config}]")
    print(f"{sessions} sessions, {grand} trades\n")
    print(f"  {'entry slot':<12}{'trades':>7}{'share%':>8}{'|move|%':>9}"
          f"{'win%':>7}{'avg%':>7}{'PF':>6}{'total%':>9}")
    print("  " + "-" * 63)
    for s_label in sorted(by_slot):
        s = stats(by_slot[s_label])
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        share = 100 * s["n"] / grand
        print(f"  {s_label:<12}{s['n']:>7}{share:>8.1f}{s['absmove']:>9.2f}"
              f"{s['win']:>7.1f}{s['avg']:>+7.2f}{pf:>6}{s['total']:>+9.1f}")
    print("\n  |move|% = mean |ret| per trade (move SIZE); avg%/PF = EDGE.")
    print("  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

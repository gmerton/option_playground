#!/usr/bin/env python3
"""Buy&hold CALL: the delta frontier -- return vs ruin.

Goal: improve buy&hold-call by choosing delta for a return/ruin tradeoff. KEY
(counter-intuitive): LOWER delta (cheap OTM) = MORE leverage/dollar = HIGHER
return AND HIGHER ruin (-99% tail). To LOWER ruin (accepting lower return) go
HIGHER delta / deeper ITM (behaves more like the stock; delta=1.0 IS the stock).

For each delta we buy at the open, hold to close, and report arithmetic return
PLUS geometric growth g(f)=mean(log(1+f*r)) at fixed position sizes f -- because
geometric growth is what COMPOUNDS, and it penalizes the -99% tail that the
arithmetic mean ignores. The delta maximizing g(f) is the growth-optimal vehicle
for that size, and it shifts toward ITM as size (ruin pressure) rises.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_bh_delta.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_bh_delta.py --iv 0.6 --dte 5
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_options import opt_return  # noqa: E402

DELTAS = [0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25]
SIZES = [0.05, 0.10, 0.20]          # fixed fraction of bankroll spent on premium/trade


def g_of_f(r: np.ndarray, f: float) -> float:
    """Per-trade geometric (log) growth at fixed size f; -inf if a single trade ruins."""
    step = 1.0 + f * r
    if np.any(step <= 0):
        return float("-inf")
    return float(np.mean(np.log(step)))


def mc_dd(r: np.ndarray, f: float, rng, horizon=250, paths=8000):
    idx = rng.integers(0, len(r), size=(paths, horizon))
    eq = np.cumprod(1.0 + f * r[idx], axis=1)
    runmax = np.maximum.accumulate(eq, axis=1)
    maxdd = (1.0 - eq / runmax).max(axis=1)
    return float(np.median(maxdd)) * 100, float(np.mean(maxdd > 0.5)) * 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--iv", type=float, default=0.60)
    ap.add_argument("--dte", type=int, default=5)
    ap.add_argument("--haircut", type=float, default=0.0,
                    help="pct-points shaved off each pick's open->close move "
                         "(simulates a weaker real edge than the mover-biased cache)")
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    bh = []   # (open, close, hold_min)
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            mod = g["time"].dt.hour * 60 + g["time"].dt.minute
            o, c = g["open"].iloc[0], g["close"].iloc[-1]
            if a.haircut:                         # weaken the edge to a realistic level
                c = o * (1 + (c / o - 1) - a.haircut / 100)
            bh.append((o, c, int(mod.iloc[-1] - mod.iloc[0])))

    rng = np.random.default_rng(42)
    # stock (delta=1.0) reference
    stock = np.array([(c / o - 1) * 100 for (o, c, _) in bh]) / 100.0

    print(f"\nBUY&HOLD CALL -- delta frontier (return vs ruin)   "
          f"[IV={a.iv:.0%}, DTE={a.dte}, haircut={a.haircut:.1f}pp, {len(bh)} sessions]\n")
    print(f"  {'vehicle':<11}{'arithMean%':>11}{'win%':>6}{'worst%':>8}"
          f"{'wrongMean%':>11}{'g@5%':>9}{'g@10%':>9}{'g@20%':>9}")

    def row(label, r):
        wins = (r > 0).mean() * 100
        wrong = r[r <= 0]
        wm = wrong.mean() * 100 if len(wrong) else 0.0
        gs = [g_of_f(r, f) for f in SIZES]
        gtxt = "".join((f"{x:>9.4f}" if np.isfinite(x) else f"{'RUIN':>9}") for x in gs)
        print(f"  {label:<11}{r.mean()*100:>+11.2f}{wins:>6.1f}{r.min()*100:>+8.1f}"
              f"{wm:>+11.2f}{gtxt}")
        return [g_of_f(r, f) for f in SIZES]

    grid = {}
    grid["stock"] = row("stock 1.0Δ", stock)
    dist = {"stock": stock}
    for d in DELTAS:
        r = np.array([opt_return(o, c, max(1, h), a.dte, a.iv, d) for (o, c, h) in bh
                      if opt_return(o, c, max(1, h), a.dte, a.iv, d) is not None]) / 100.0
        dist[f"{d:.2f}"] = r
        grid[f"{d:.2f}"] = row(f"{d:.2f}Δ call", r)

    # growth-optimal delta at each size + drawdown context
    print()
    keys = list(grid.keys())
    for j, f in enumerate(SIZES):
        vals = [(k, grid[k][j]) for k in keys]
        best = max(vals, key=lambda kv: kv[1] if np.isfinite(kv[1]) else -1e9)
        print(f"  best geometric growth @ {int(f*100)}% size: {best[0]}  "
              f"(g={best[1]:+.4f}/trade)")
    print()
    for k in ["stock", "0.85", "0.65", "0.45", "0.25"]:
        if k in dist:
            mdd, p50 = mc_dd(dist[k], 0.10, rng)
            print(f"  @10% size, {k:<5}: median maxDD {mdd:.0f}%, P(DD>50%) {p50:.0f}%")

    print("\n  g(f)=mean(log(1+f*r)); higher=faster compounding; RUIN=a single trade")
    print("  wipes the bankroll at that size. % on premium; cache mover-biased.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

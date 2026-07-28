#!/usr/bin/env python3
"""Does the option-leverage conclusion survive HONEST vol pricing?

Every option result so far (ema_crossover_options / _hybrid_options / _bh_delta)
priced EVERY name at a flat IV=60%. But the cache spans SPY (~1%/day) to AAOI
(13.5% ADR). A flat IV therefore sells calls on the high-vol names far too
CHEAP -- and those are exactly the names that throw the big winners that
convexity feeds on. So "lower delta is better" may be an artifact of
systematically underpriced vol on the fattest-tailed names, not a real edge.

Real IV tracks each name's own vol. Here each session's call is priced with an
IV built from THAT SYMBOL's realized vol (leave-one-out over its other sessions,
so the day being priced never sets its own IV), optionally scaled by a
volatility-risk-premium multiplier (real IV usually exceeds subsequent RV --
you pay up).

Reports the delta frontier under three pricing regimes so they're directly
comparable:
  flat        -- IV = --iv for every name (the old, flawed basis)
  per-name    -- IV = symbol's leave-one-out realized vol
  per-name*VRP-- same, scaled by --vrp (what you'd actually be charged)

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_iv_calib.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_iv_calib.py --vrp 1.25
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_options import opt_return  # noqa: E402

DELTAS = [0.85, 0.65, 0.45, 0.25]
SIZES = [0.05, 0.10, 0.20]
IV_FLOOR, IV_CAP = 0.15, 3.0


def g_of_f(r: np.ndarray, f: float) -> float:
    step = 1.0 + f * r
    if np.any(step <= 0):
        return float("-inf")
    return float(np.mean(np.log(step)))


def load_sessions(glob_pat: str, min_bars: int):
    """-> list of (sym, o, c, hold_min)."""
    out = []
    for f in sorted(glob.glob(glob_pat)):
        sym = os.path.basename(f).split("_")[0]
        df = pd.read_csv(f, parse_dates=["time"])
        for _, g in df.groupby(df["time"].dt.date):
            if len(g) < min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            mod = g["time"].dt.hour * 60 + g["time"].dt.minute
            out.append((sym, float(g["open"].iloc[0]), float(g["close"].iloc[-1]),
                        int(mod.iloc[-1] - mod.iloc[0])))
    return out


def loo_iv(sessions):
    """Leave-one-out annualized IV per session, from the symbol's own open->close vol."""
    by = defaultdict(list)
    for i, (sym, o, c, _) in enumerate(sessions):
        by[sym].append((i, c / o - 1.0))
    iv = np.zeros(len(sessions))
    for sym, rows in by.items():
        rets = np.array([r for _, r in rows])
        n = len(rets)
        if n < 3:                                   # too few to self-calibrate
            iv[[i for i, _ in rows]] = np.nan
            continue
        s1, s2 = rets.sum(), (rets ** 2).sum()
        for i, r in rows:                           # leave-one-out mean/var
            m = (s1 - r) / (n - 1)
            var = max(1e-8, (s2 - r * r) / (n - 1) - m * m)
            iv[i] = np.sqrt(var) * np.sqrt(252.0)
    med = np.nanmedian(iv)
    iv = np.where(np.isnan(iv), med, iv)
    return np.clip(iv, IV_FLOOR, IV_CAP)


def frontier(label, sessions, ivs, dte, sizes=SIZES):
    stock = np.array([c / o - 1.0 for (_, o, c, _) in sessions])
    print(f"\n  {label}")
    print(f"    {'vehicle':<12}{'arithMean%':>11}{'win%':>7}{'worst%':>8}"
          f"{'g@5%':>9}{'g@10%':>9}{'g@20%':>9}")

    def row(name, r):
        gs = "".join((f"{g_of_f(r, f):>9.4f}" if np.isfinite(g_of_f(r, f))
                      else f"{'RUIN':>9}") for f in sizes)
        print(f"    {name:<12}{r.mean()*100:>+11.2f}{(r > 0).mean()*100:>7.1f}"
              f"{r.min()*100:>+8.1f}{gs}")

    row("stock 1.0d", stock)
    for d in DELTAS:
        vals = []
        for (sym, o, c, h), iv in zip(sessions, ivs):
            v = opt_return(o, c, max(1, h), dte, float(iv), d)
            if v is not None:
                vals.append(v / 100.0)
        row(f"{d:.2f}d call", np.array(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--iv", type=float, default=0.60, help="flat IV for the old basis")
    ap.add_argument("--dte", type=int, default=5)
    ap.add_argument("--vrp", type=float, default=1.15,
                    help="multiplier on per-name IV (real IV > subsequent RV)")
    a = ap.parse_args()

    sessions = load_sessions(
        a.glob if os.path.isabs(a.glob) else os.path.join(HERE, a.glob), a.min_bars)
    ivs = loo_iv(sessions)

    print(f"\nIV CALIBRATION: flat vs per-name   "
          f"[{len(sessions)} sessions, DTE={a.dte}]")
    q = np.percentile(ivs, [10, 25, 50, 75, 90])
    print(f"\n  per-name IV (leave-one-out, annualized): "
          f"p10 {q[0]:.0%}  p25 {q[1]:.0%}  med {q[2]:.0%}  p75 {q[3]:.0%}  p90 {q[4]:.0%}")
    print(f"  flat basis was {a.iv:.0%} -> "
          f"{100*np.mean(ivs > a.iv):.0f}% of sessions were UNDERPRICED by the flat IV")

    frontier(f"FLAT IV={a.iv:.0%}  (the old, flawed basis)",
             sessions, np.full(len(sessions), a.iv), a.dte)
    frontier("PER-NAME IV  (leave-one-out realized vol)", sessions, ivs, a.dte)
    frontier(f"PER-NAME IV x {a.vrp:.2f} VRP  (what you'd actually pay)",
             sessions, ivs * a.vrp, a.dte)

    print("\n  Buy at 09:30 open, sell 16:00 close. g(f)=mean(log(1+f*r)).")
    print("  Cache is mover-biased -> all levels are UPPER BOUNDS; the COMPARISON")
    print("  across pricing regimes is the point, not the absolute numbers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

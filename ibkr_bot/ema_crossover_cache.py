#!/usr/bin/env python3
"""Cache-wide sweep of the 9/20-EMA crossover chop filters.

Runs each filter config in ema_crossover_backtest.PRESETS over EVERY (symbol,
day) session in the 1-min cache (the multi-day CSVs are split per trading date,
same loader convention as mday_backtest.py), pools every trade across all
sessions, and ranks the configs.

This is the out-of-sample-ish test of the single-day AAOI finding: a filter that
only helps on the one in-sample day is curve-fit; one that survives 1000+
sessions is real. (Cache is still hand-picked movers -> totals are an upper
bound, same caveat as the VCB work.)

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_cache.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_cache.py --glob 'data/*_1min.csv' --min-bars 200
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


def stats(pnls: list[float], n_days: int) -> dict:
    wins = [p for p in pnls if p > 0]
    gw = sum(wins)
    gl = -sum(p for p in pnls if p <= 0)
    return {
        "n": len(pnls),
        "win": 100 * len(wins) / len(pnls) if pnls else 0.0,
        "total": sum(pnls),
        "avg": sum(pnls) / len(pnls) if pnls else 0.0,
        "worst": min(pnls) if pnls else 0.0,
        "pf": (gw / gl) if gl else float("inf"),
        "per_day": sum(pnls) / n_days if n_days else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200,
                    help="skip sessions with fewer bars (partial days)")
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    # pooled pnl list per preset name
    pooled: dict = {name: [] for name, _ in PRESETS}
    sessions = 0
    days = set()
    syms = set()
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            sess = g.sort_values("time").reset_index(drop=True)
            sessions += 1
            days.add(str(day))
            syms.add(sym)
            for name, kw in PRESETS:
                trades, _ = backtest(sess, **kw)
                pooled[name] += [t["ret_pct"] for t in trades]

    print(f"\n9/20 EMA crossover -- cache-wide filter sweep")
    print(f"{sessions} sessions, {len(syms)} symbols, {len(days)} distinct days"
          f"  ({min(days)} .. {max(days)})\n")
    hdr = (f"  {'config':<30}{'n':>5}{'win%':>6}{'total%':>9}{'avg%':>7}"
           f"{'worst%':>8}{'PF':>6}{'/day%':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    rows = [(name, stats(pooled[name], len(days))) for name, _ in PRESETS]
    for name, s in rows:
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        print(f"  {name:<30}{s['n']:>5}{s['win']:>6.1f}{s['total']:>+9.1f}"
              f"{s['avg']:>+7.2f}{s['worst']:>+8.1f}{pf:>6}{s['per_day']:>+7.2f}")
    print("\n  Pooled across all sessions; gross of costs; % on the underlying.")
    print("  Cache is hand-picked movers -> totals are an UPPER BOUND.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

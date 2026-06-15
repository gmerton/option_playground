#!/usr/bin/env python3
"""Synthesis test: combine the two ROBUST, CAUSAL levers found for the 9/20
crossover -- open-hour entry (time-of-day finding) + relative strength vs SPY
(the selection lever / VCB discriminator) -- and see if they stack.

Both are usable LIVE (unlike full-day range/chop, which are look-ahead). RS at a
bar = (name ret-from-open) - (SPY ret-from-open), in pct points, computed only
from data available at that bar.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_synth.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_synth.py --index QQQ
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
from vcb import load_index  # noqa: E402

INDEX_SYMS = {"SPY", "QQQ"}

# each config layered on the validated base (close>VWAP); rs_min in pct points
CONFIGS = [
    ("VWAP only (base)", {"trend_vwap": True}),
    ("VWAP + open-hour", {"trend_vwap": True, "entry_before": "10:30"}),
    ("VWAP + RS>=0", {"trend_vwap": True, "rs_min": 0.0}),
    ("VWAP + RS>=+1", {"trend_vwap": True, "rs_min": 1.0}),
    ("VWAP + open-hr + RS>=0", {"trend_vwap": True, "entry_before": "10:30", "rs_min": 0.0}),
    ("VWAP + open-hr + RS>=+1", {"trend_vwap": True, "entry_before": "10:30", "rs_min": 1.0}),
    ("VWAP + open-hr + RS>=+2", {"trend_vwap": True, "entry_before": "10:30", "rs_min": 2.0}),
]


def stats(pnls, n_days):
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
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--index", default="SPY")
    a = ap.parse_args()

    idx = load_index(a.index)   # {date_str: Series(ts -> idx ret-from-open)}
    # reduce to {date: {"HH:MM": ret}} for robust alignment
    idx_hhmm = {d: {ts.strftime("%H:%M"): v for ts, v in s.items()}
                for d, s in idx.items()}
    if not idx_hhmm:
        print(f"no index data for {a.index} -- pull it: fetch_intraday.py {a.index} --days 40")
        return 2

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    pooled = {name: [] for name, _ in CONFIGS}
    sessions = 0
    days = set()
    skipped_no_idx = 0
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        if sym in INDEX_SYMS:                       # don't trade the benchmark itself
            continue
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            ds = str(day)
            day_idx = idx_hhmm.get(ds)
            if day_idx is None:                     # need the index that day for RS
                skipped_no_idx += 1
                continue
            g = g.sort_values("time").reset_index(drop=True)
            sessions += 1
            days.add(ds)
            for name, kw in CONFIGS:
                trades, _ = backtest(g, idx_by_hhmm=day_idx, **kw)
                pooled[name] += [t["ret_pct"] for t in trades]

    print(f"\n9/20 crossover synthesis -- open-hour x RS-vs-{a.index}")
    print(f"{sessions} tradeable sessions, {len(days)} days"
          f"  ({skipped_no_idx} sessions skipped: no {a.index} that day)\n")
    hdr = (f"  {'config':<26}{'n':>5}{'win%':>6}{'total%':>9}{'avg%':>7}"
           f"{'worst%':>8}{'PF':>6}{'/day%':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for name, _ in CONFIGS:
        s = stats(pooled[name], len(days))
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        print(f"  {name:<26}{s['n']:>5}{s['win']:>6.1f}{s['total']:>+9.1f}"
              f"{s['avg']:>+7.2f}{s['worst']:>+8.1f}{pf:>6}{s['per_day']:>+7.2f}")
    print(f"\n  RS = (name ret-from-open) - ({a.index} ret-from-open) in pts, "
          f"causal at the entry bar.")
    print("  gross of costs; % on underlying; cache = hand-picked movers (upper bound).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

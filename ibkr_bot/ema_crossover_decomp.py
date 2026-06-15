#!/usr/bin/env python3
"""Decomposition: is VOLUME's edge INCREMENTAL to RS, or does it just re-discover
the same "this name is the day's mover" signal?

Base held fixed: close>VWAP + open-hour + 12/34. Then layer RS and volume alone
and together. If (RS + vol) >> (RS alone), volume adds independent edge -> stack
them. If (RS + vol) ~= (RS alone), they overlap -> pick whichever is cleaner.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_decomp.py
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
EARLY_CUTOFF = "09:45"
BASE = {"trend_vwap": True, "entry_before": "10:30", "fast_span": 12, "slow_span": 34}

CONFIGS = [
    ("base (VWAP+openhr+12/34)", {}),
    ("+ RS>=+1", {"rs_min": 1.0}),
    ("+ vol>=1.5x (trigger)", {"vol_mult": 1.5}),
    ("+ rvol>=1.5 (select)", {"rvol_min": 1.5}),
    ("+ RS>=+1 + vol>=1.5x", {"rs_min": 1.0, "vol_mult": 1.5}),
    ("+ RS>=+1 + rvol>=1.5", {"rs_min": 1.0, "rvol_min": 1.5}),
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
        "pf": (gw / gl) if gl else float("inf"),
        "per_day": sum(pnls) / n_days if n_days else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--index", default="SPY")
    a = ap.parse_args()

    idx = load_index(a.index)
    idx_hhmm = {d: {ts.strftime("%H:%M"): v for ts, v in s.items()}
                for d, s in idx.items()}
    if not idx_hhmm:
        print(f"no index data for {a.index}")
        return 2

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    sess_by: dict = {}
    early: dict = {}
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        if sym in INDEX_SYMS:
            continue
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars or str(day) not in idx_hhmm:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            hhmm = g["time"].dt.strftime("%H:%M")
            sess_by[(sym, str(day))] = g
            early.setdefault(sym, {})[str(day)] = g.loc[hhmm <= EARLY_CUTOFF, "volume"].sum()

    rvol = {}
    for sym, byday in early.items():
        for date, ev in byday.items():
            others = [v for d, v in byday.items() if d != date]
            typ = (sum(others) / len(others)) if others else ev
            rvol[(sym, date)] = (ev / typ) if typ > 0 else 1.0

    pooled = {name: [] for name, _ in CONFIGS}
    days = set()
    for (sym, date), g in sess_by.items():
        days.add(date)
        di = idx_hhmm[date]
        srv = rvol[(sym, date)]
        for name, kw in CONFIGS:
            tr, _ = backtest(g, idx_by_hhmm=di, session_rvol=srv, **BASE, **kw)
            pooled[name] += [t["ret_pct"] for t in tr]

    print(f"\nVOLUME vs RS decomposition   [{len(sess_by)} sessions, {len(days)} days, "
          f"index {a.index}]\n")
    hdr = (f"  {'config':<28}{'n':>5}{'win%':>6}{'total%':>9}{'avg%':>7}"
           f"{'PF':>6}{'/day%':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for name, _ in CONFIGS:
        s = stats(pooled[name], len(days))
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        print(f"  {name:<28}{s['n']:>5}{s['win']:>6.1f}{s['total']:>+9.1f}"
              f"{s['avg']:>+7.2f}{pf:>6}{s['per_day']:>+7.2f}")
    print("\n  Compare '+RS>=+1' vs '+RS>=+1 + vol/rvol': lift = incremental edge.")
    print("  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Does volume add value to the 9/20 (here 12/34) crossover? Tested in its two
roles, the same split that mattered for RS:

  TRIGGER   (vol_mult)  -- require the CROSS BAR to print on >= k x its trailing
                           20-bar average volume. Prior (from PHB/VCB): volume is
                           necessary-not-sufficient -> expect ~no discrimination.
  SELECTION (rvol_min)  -- is THIS NAME unusually active today? early-session
                           (<=09:45) volume / the name's leave-one-out typical
                           early volume. Causal for entries >=09:45 (open-hour
                           entries with a slow pair cluster later). Prior: a
                           selection lever like RS could actually help.

Base config held fixed: close>VWAP + open-hour + 12/34 EMAs.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_volume.py
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

INDEX_SYMS = {"SPY", "QQQ"}
EARLY_CUTOFF = "09:45"
BASE = {"trend_vwap": True, "entry_before": "10:30", "fast_span": 12, "slow_span": 34}

CONFIGS = [
    ("base (VWAP+openhr+12/34)", {}),
    ("+ TRIGGER vol >=1.5x", {"vol_mult": 1.5}),
    ("+ TRIGGER vol >=2.0x", {"vol_mult": 2.0}),
    ("+ TRIGGER vol >=3.0x", {"vol_mult": 3.0}),
    ("+ SELECT rvol >=1.0", {"rvol_min": 1.0}),
    ("+ SELECT rvol >=1.5", {"rvol_min": 1.5}),
    ("+ SELECT rvol >=2.0", {"rvol_min": 2.0}),
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
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    # pass 1: collect sessions + each session's early-volume, keyed for leave-one-out
    sess_by: dict = {}          # (sym, date) -> df
    early: dict = {}            # sym -> {date: early_vol}
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        if sym in INDEX_SYMS:
            continue
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            hhmm = g["time"].dt.strftime("%H:%M")
            ev = g.loc[hhmm <= EARLY_CUTOFF, "volume"].sum()
            sess_by[(sym, str(day))] = g
            early.setdefault(sym, {})[str(day)] = ev

    # leave-one-out typical early volume per (sym, date) -> session_rvol
    rvol: dict = {}
    for sym, byday in early.items():
        for date, ev in byday.items():
            others = [v for d, v in byday.items() if d != date]
            typ = (sum(others) / len(others)) if others else ev
            rvol[(sym, date)] = (ev / typ) if typ > 0 else 1.0

    pooled = {name: [] for name, _ in CONFIGS}
    days = set()
    for (sym, date), g in sess_by.items():
        days.add(date)
        srv = rvol[(sym, date)]
        for name, kw in CONFIGS:
            tr, _ = backtest(g, session_rvol=srv, **BASE, **kw)
            pooled[name] += [t["ret_pct"] for t in tr]

    print(f"\n9/20->12/34 crossover -- does VOLUME help?   "
          f"[{len(sess_by)} sessions, {len(days)} days]\n")
    hdr = (f"  {'config':<28}{'n':>5}{'win%':>6}{'total%':>9}{'avg%':>7}"
           f"{'PF':>6}{'/day%':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for name, _ in CONFIGS:
        s = stats(pooled[name], len(days))
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        print(f"  {name:<28}{s['n']:>5}{s['win']:>6.1f}{s['total']:>+9.1f}"
              f"{s['avg']:>+7.2f}{pf:>6}{s['per_day']:>+7.2f}")
    print("\n  TRIGGER = cross-bar surge; SELECTION = name's early RVOL (causal >=09:45).")
    print("  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

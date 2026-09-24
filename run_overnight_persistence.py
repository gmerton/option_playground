#!/usr/bin/env python3
"""
Overnight-return persistence as a trade (pre-registered 2026-09-24, before the first run; Gabe's "other ideas" #4).
The 2026-09-22 row "Overnight vs intraday variance as a stock trait" found overnight MEAN return weakly persistent
(+0.07/+0.16/+0.18 rank corr) but never priced a trade. Lou, Polk & Skouras (2019, "A tug of war"): stocks with high
past overnight returns keep earning overnight and give it back intraday.

DESIGN
  panel     liquid_panel_2009 (yfinance-adjusted OHLC), eligible names, 2010 ->.
  signal    at each month-end, a name's mean overnight return (open_t / close_{t-1} - 1) over the trailing 252 sessions
            (>= 200 observations); TOP decile vs BOTTOM decile.
  ARM A     "overnight only": hold the top decile from each close to the next open, every day of the next month.
            Monthly return = sum of daily overnight returns (equal weight) minus the eligible universe's mean overnight
            return the same day (so the market's overnight drift is not credited). Cost: 2 bp per side (close and open
            auctions), i.e. 4 bp per day held -- reported gross and net.
  ARM B     "just hold them": the same top decile held close-to-close for the month, excess vs the eligible universe.
            Tests whether the persistence reaches total return (the tug-of-war says intraday reversal offsets it).
  PRIMARY   ARM A net monthly excess, t across months; bar t >= 3, both halves (2018-01) > 0.
  SECONDARY ARM A gross; top-minus-bottom decile spread (A); ARM B; per year.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_overnight_persistence.py   (log -> data/studies/logs/overnight_persistence.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/overnight_persistence.log"
COST_SIDE = 0.0002
SPLIT = pd.Period("2018-01", "M")


def t(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    O, C, E = P.open.loc[keep], P.close.loc[keep], P.elig.loc[keep].fillna(False)
    on = (O / C.shift(1) - 1).where(E.shift(1).fillna(False))          # overnight: yesterday's close -> today's open
    cc = (C / C.shift(1) - 1).where(E.shift(1).fillna(False))
    sig = on.rolling(252, min_periods=200).mean()
    mkt_on, mkt_cc = on.mean(axis=1), cc.mean(axis=1)
    idx = C.index
    ends = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    rows = []
    for k in range(len(ends) - 1):
        d0, d1 = ends.iloc[k], ends.iloc[k + 1]
        if d0 < pd.Timestamp("2010-01-29"):
            continue
        s = sig.loc[d0][E.loc[d0]].dropna()
        if len(s) < 200:
            continue
        top, bot = s[s >= s.quantile(0.9)].index, s[s <= s.quantile(0.1)].index
        win = (idx > d0) & (idx <= d1)
        onw, ccw = on.loc[win], cc.loc[win]
        a_top = (onw[top].mean(axis=1) - mkt_on[win]).sum()
        a_bot = (onw[bot].mean(axis=1) - mkt_on[win]).sum()
        ndays = int(win.sum())
        b_top = ((1 + ccw[top].fillna(0)).prod() - 1).mean() - ((1 + ccw.fillna(0)).prod() - 1)[ccw.columns[E.loc[d0]]].mean()
        rows.append(dict(month=d1.to_period("M"), A_gross=100 * a_top, A_net=100 * (a_top - 2 * COST_SIDE * ndays),
                         A_spread=100 * (a_top - a_bot), B=100 * b_top,
                         top_intraday=100 * ((ccw[top].mean(axis=1) - mkt_cc[win]).sum() - a_top)))
    M = pd.DataFrame(rows).set_index("month")
    h = M.index < SPLIT
    out = ["# Overnight-return persistence as a trade (pre-registration in the docstring)\n",
           f"{len(M)} months {M.index.min()} -> {M.index.max()}; top/bottom decile of trailing-252 mean overnight return\n"]
    for c, lab in (("A_net", "ARM A overnight-only, NET 4 bp/day (PRIMARY)"), ("A_gross", "ARM A overnight-only, gross"),
                   ("A_spread", "ARM A top - bottom decile, gross"), ("top_intraday", "top decile INTRADAY excess (the give-back)"),
                   ("B", "ARM B hold top decile close-to-close")):
        x = M[c]
        out.append(f"{lab:46s} {x.mean():+7.3f}%/month  t {t(x):+6.2f}  halves {x[h].mean():+.3f} / {x[~h].mean():+.3f}  "
                   f"{100 * (x > 0).mean():.0f}% +")
    x = M.A_net
    ok = t(x) >= 3 and x[h].mean() > 0 and x[~h].mean() > 0
    out.append(f"\nPRIMARY bar (t >= 3, both halves > 0): {'PASS' if ok else 'FAIL'}")
    out.append("ARM A gross by year (%/month): " + "  ".join(f"{y} {v:+.2f}" for y, v in M.A_gross.groupby(M.index.year).mean().items()))
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

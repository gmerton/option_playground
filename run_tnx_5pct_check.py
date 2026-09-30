#!/usr/bin/env python3
"""Eisman 2026-09-24: 'should the 10-year remain above 5%, a correction is probably imminent' -- index check 1962->2026.
PRE-REGISTERED in data/steve_eisman/videos/2026-09-24_vKLPLywZcp0/notes.md (committed f60e8cd before this ran).
Usage: .venv/bin/python3 run_tnx_5pct_check.py > data/steve_eisman/videos/2026-09-24_vKLPLywZcp0/tnx_5pct_check.log
"""
from math import sqrt

import numpy as np
import pandas as pd
import yfinance as yf

H, SPLIT = 63, "1994-01-01"


def welch(a, b):
    return (a.mean() - b.mean()) / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


d = yf.download(["^TNX", "^GSPC"], start="1962-01-01", end="2026-09-26", progress=False, auto_adjust=False)["Close"].dropna()
y, s = d["^TNX"], d["^GSPC"]
print(f"{d.index.min().date()} -> {d.index.max().date()}, {len(d):,} sessions; last 10y {y.iloc[-1]:.2f}%, share of sessions > 5%: {(y > 5).mean():.1%}")
C, n = s.values, len(s)
fwd = np.full(n, np.nan); dd = np.full(n, np.nan)
for i in range(n - H - 1):
    path = C[i + 1:i + 1 + H]
    fwd[i] = path[-1] / C[i] - 1
    dd[i] = path.min() / C[i] - 1
F = pd.DataFrame({"y": y.values, "fwd": fwd, "corr10": dd <= -0.10}, index=s.index).iloc[::H].dropna()
F["hi"] = F.y > 5
print("\nC1 (non-overlapping 63-session blocks)")
for lab, g in (("ALL", F), ("1962-1993", F[F.index < SPLIT]), ("1994-2026", F[F.index >= SPLIT])):
    a, b = g[g.hi], g[~g.hi]
    if len(a) < 5 or len(b) < 5:
        print(f"  {lab}: >5% n {len(a)}, <=5% n {len(b)} -- too few"); continue
    print(f"  {lab:10s} >5%: n {len(a):3d} fwd {a.fwd.mean()*100:+.2f}% P(>=10% dd) {a.corr10.mean():.1%} | <=5%: n {len(b):3d} "
          f"fwd {b.fwd.mean()*100:+.2f}% P {b.corr10.mean():.1%} | diff fwd {100*(a.fwd.mean()-b.fwd.mean()):+.2f}pp t {welch(a.fwd, b.fwd):+.2f}; "
          f"diff P {100*(a.corr10.mean()-b.corr10.mean()):+.1f}pp t {welch(a.corr10.astype(float), b.corr10.astype(float)):+.2f}")
print("\nC2 crossings: first close > 5% after >= 60 sessions at or below")
below = (y <= 5).astype(int)
run = below.groupby((below != below.shift()).cumsum()).cumsum()
ev = [i for i in range(1, n) if y.iloc[i] > 5 and y.iloc[i - 1] <= 5 and run.iloc[i - 1] >= 60]
for i in ev:
    f = fwd[i] * 100 if np.isfinite(fwd[i]) else np.nan; m = dd[i] * 100 if np.isfinite(dd[i]) else np.nan
    print(f"  {s.index[i].date()}  10y {y.iloc[i]:.2f}%  fwd63 {f:+.1f}%  maxDD63 {m:+.1f}%")

#!/usr/bin/env python3
"""
The size lever: does scaling risk by setup grade beat flat size on the SAME trades?

Breitstein varies risk ~10x by grade ($10k B -> $100k A); Tito's barbell implies the same. Position size is
the only mechanism large enough to explain the returns these traders report -- but it only works if an
EX-ANTE grade predicts R. That is what this tests, on our own breakout pool.

Set before running:
  Pool     house breakout (15d pivot, RVOL>=1.1, upper-half close, stacked, ADR>=3, 52w range>=17%),
           entry at the breakout-day close, stop = that day's low, exit = first close under the 20 EMA
           (the book's grind trail, cap 60 sessions). R = return / (entry - stop).
  Grades   fixed in advance from PRIOR findings, no fitting here:
             A = precision tier (ADR 4-7, within 15% of the 52w high, stack 5-40) AND the entry-day close
                 sits 1.5-3% above its low (the stop-distance finding, adhikary_stop_study)
             B = precision tier only
             C = everything else in the pool
  Schemes  flat (1x everywhere) · graded 3x/1.5x/1x · graded 10x/3x/1x (Breitstein's spread) · A-only
           All are normalised to the SAME total risk deployed, so this compares allocation, not leverage.
  Test     walk-forward: 2019-22 in sample (do the grades separate there?), 2023-26 out of sample.
           Also equity-curve variance: mean R, worst month, max drawdown at equal total risk.

Usage: PYTHONPATH=src .venv/bin/python3 run_size_lever_study.py > data/studies/size_lever_2026-09-18.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
COST = 0.0005

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
range52 = (hi52 - lo52) / C * 100; off52 = (C / hi52 - 1) * 100
piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
stack = stack_run(C, adr=adr)
brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5)
       & (stack >= 5) & (gap < .05) & (chg < .08) & (C.shift(1) < piv15))
idx = C.index
Cv, Lv, E20v = C.values, L.values, e20.values
mm = brk.fillna(False).astype(bool); mm = mm[mm.index >= "2019-10-01"]
ii, jj = np.where(mm.values); ii = ii + (len(C) - len(mm))
rows = []
for i, j in zip(ii, jj):
    entry, stop = Cv[i, j], Lv[i, j]
    if not np.isfinite(entry) or not np.isfinite(stop) or entry <= stop:
        continue
    risk = entry - stop
    r = np.nan
    for k in range(i + 1, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or c < E20v[k, j]:
            r = (c * (1 - COST) - entry * (1 + COST)) / risk
            break
    if not np.isfinite(r):
        k = min(i + 60, len(Cv) - 1)
        r = (Cv[k, j] * (1 - COST) - entry * (1 + COST)) / risk
    rows.append(dict(date=idx[i], year=idx[i].year, sym=C.columns[j], R=np.clip(r, -10, 10),
                     adr=adr.values[i, j], off52=off52.values[i, j], stack=stack.values[i, j],
                     off_low=100 * (entry / stop - 1)))
T = pd.DataFrame(rows)
T["precision"] = T["adr"].between(4, 7) & (T["off52"] > -15) & T["stack"].between(5, 40)
T["grade"] = np.where(T["precision"] & T["off_low"].between(1.5, 3.0), "A", np.where(T["precision"], "B", "C"))
T["month"] = T.date.dt.to_period("M").astype(str)
T.to_parquet("data/cache/size_lever_trades.parquet", index=False)
print(f"{len(T):,} breakouts 2019-10 -> {T.date.max().date()} | grade mix "
      f"{T.grade.value_counts().to_dict()}")
print("\n=== mean R by grade, in sample vs out of sample ===")
g = T.assign(half=np.where(T.year <= 2022, "2019-22", "2023-26")).groupby(["half", "grade"]).R.agg(["size", "mean", "median"])
print(g.round(3).to_string())

SCHEMES = {"flat": {"A": 1, "B": 1, "C": 1}, "graded 3/1.5/1": {"A": 3, "B": 1.5, "C": 1},
           "graded 10/3/1": {"A": 10, "B": 3, "C": 1}, "A only": {"A": 1, "B": 0, "C": 0},
           "A+B only": {"A": 1, "B": 1, "C": 0}}
def sleeve(x, w):
    ww = x.grade.map(w).astype(float)
    if ww.sum() == 0:
        return dict(n=0)
    wr = (ww * x.R).sum() / ww.sum()                       # R per unit of risk deployed
    m = x.assign(w=ww).groupby("month").apply(lambda z: (z.w * z.R).sum() / max(z.w.sum(), 1e-9))
    eq = (1 + 0.01 * m).cumprod()                          # 1% of equity per unit risk, monthly rebalanced
    return dict(n=int((ww > 0).sum()), R_per_risk=wr, monthly_mean=m.mean(), t=m.mean() / m.std() * np.sqrt(len(m)),
                worst_month=m.min(), max_dd=100 * (eq / eq.cummax() - 1).min())
for half, x in (("2019-22 (in sample)", T[T.year <= 2022]), ("2023-26 (out of sample)", T[T.year >= 2023]), ("all", T)):
    print(f"\n=== {half} ===")
    print(pd.DataFrame({k: sleeve(x, w) for k, w in SCHEMES.items()}).T.round(3).to_string())

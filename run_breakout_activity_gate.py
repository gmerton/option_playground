#!/usr/bin/env python3
"""
Does a LIVE count of breakouts say when the breakout book pays? (2026-09-22; item 3 of the post-correction queue,
pre-registered here before the first run.)

From the O'Neil run this morning: the precision-tier book is +0.448R trade-weighted (date-clustered t 3.29) but
**-0.007R month-weighted (t -0.04)** -- the expectancy lives in the months with many breakouts. The regime-feedback
study already showed that LAGGED MONTHLY activity does not forecast (rank corr ~0). This tests the shorter,
contemporaneous version, which is knowable in real time: how many precision-tier breakouts have fired in the last
N sessions, as of the morning of the entry?

SIGNAL (strictly prior, no look-ahead): cnt_N = number of precision-tier breakouts across the whole universe in
the N sessions BEFORE the entry day (N = 5, 10, 20), and the same as a percentile of its own trailing 252-session
history. Also breadth: share of the eligible universe above its 20 EMA on the prior close.
POOL / TRADE: identical to run_oneil_pyramid_8wk.py -- close entry, stop = min(day low, close x 0.98), exit on a
close under the stop or the 20 EMA, 60-session cap, 5bp/side, R capped at +/-20.
TESTS: mean R by quintile of each signal, date-clustered t on the top-minus-bottom difference, both halves
(split 2023-01-01), plus the share of trades and of total R each quintile carries.
PRE-REGISTERED PASS: top-minus-bottom |t| >= 2 with the same sign in both halves for at least one N, AND the top
quintile's mean R must beat the pooled mean by >= 0.2R. Otherwise NULL and the desk rule stays "fixed small size,
always on".

Usage: PYTHONPATH=src .venv/bin/python3 run_breakout_activity_gate.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd, statsmodels.api as sm
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
COST, CAP, FLOOR = 0.0005, 20.0, 0.02

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw)
O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
range52 = (hi52 - lo52) / C * 100
piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
stack_days = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
       & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)).fillna(False)

# ---- signals, all strictly prior to the entry day
daily_cnt = prec.sum(axis=1)                       # precision breakouts per session, universe-wide
sig = pd.DataFrame(index=C.index)
for N in (5, 10, 20):
    sig[f"cnt{N}"] = daily_cnt.rolling(N).sum().shift(1)
    sig[f"cnt{N}_pct"] = sig[f"cnt{N}"].rolling(252, min_periods=150).apply(lambda w: (w[-1] > w[:-1]).mean() * 100, raw=True)
above = (C > e20) & elig
sig["breadth"] = (above.sum(axis=1) / elig.sum(axis=1).replace(0, np.nan)).shift(1) * 100

m = prec[prec.index >= "2019-10-01"]
ii, jj = np.where(m.values); ii = ii + (len(C) - len(m))
Cv, Lv, E = C.values, L.values, e20.values
N_ = len(Cv)
rows = []
for i, j in zip(ii, jj):
    if i + 12 >= N_: continue
    entry = Cv[i, j]; stop = min(Lv[i, j], entry * (1 - FLOOR)); risk = entry - stop
    if not (np.isfinite(entry) and np.isfinite(stop)) or risk <= 0: continue
    R = np.nan
    for k in range(i + 1, min(i + 61, N_)):
        c = Cv[k, j]
        if not np.isfinite(c): continue
        if c < stop or c < E[k, j]:
            R = ((c * (1 - COST) - entry * (1 + COST)) / risk); break
    if not np.isfinite(R):
        k = min(i + 60, N_ - 1); R = (Cv[k, j] * (1 - COST) - entry * (1 + COST)) / risk
    d = C.index[i]
    rows.append(dict(date=d, sym=C.columns[j], R=float(np.clip(R, -CAP, CAP)), **sig.loc[d].to_dict()))
T = pd.DataFrame(rows).dropna(subset=["cnt20_pct"])
print(f"{len(T):,} precision-tier trades, {T.date.min().date()}..{T.date.max().date()}, {T.date.nunique()} dates")
print(f"pooled mean R {T.R.mean():+.3f}  |  breakouts/session: median {daily_cnt.median():.0f}, p90 {daily_cnt.quantile(.9):.0f}")


def dt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def by_q(col):
    q = pd.qcut(T[col], 5, labels=False, duplicates="drop")
    g = T.assign(q=q).groupby("q")
    tab = pd.DataFrame({"n": g.size(), "meanR": g.R.mean(), "share_of_R": g.R.sum() / T.R.sum() * 100})
    hi = T[q == q.max()]; lo = T[q == 0]
    dd = hi.R.mean() - lo.R.mean()
    # date-clustered t on the difference: regress R on a top-quintile dummy over the two extreme quintiles
    j = T.assign(q=q); j = j[j.q.isin([0, q.max()])]
    fit = sm.OLS(j.R.values, sm.add_constant((j.q == q.max()).astype(float).values)).fit(
        cov_type="cluster", cov_kwds={"groups": j.date.astype(str).factorize()[0]})
    t_dd = float(fit.tvalues[1])
    h1 = T[(q == q.max()) & (T.date < "2023-01-01")].R.mean() - T[(q == 0) & (T.date < "2023-01-01")].R.mean()
    h2 = T[(q == q.max()) & (T.date >= "2023-01-01")].R.mean() - T[(q == 0) & (T.date >= "2023-01-01")].R.mean()
    print(f"\n{col}: " + "  ".join(f"Q{i+1} {v:+.2f}(n{int(n)})" for i, (v, n) in enumerate(zip(tab.meanR, tab.n))))
    print(f"    top-bottom {dd:+.3f}  t {t_dd:+.2f}  halves {h1:+.2f} / {h2:+.2f}  | top quintile carries {tab.share_of_R.iloc[-1]:.0f}% of total R")
    return dd, t_dd, h1, h2, tab.meanR.iloc[-1]


print("\n== mean R by quintile of each prior-session activity signal ==")
res = {c: by_q(c) for c in ("cnt5", "cnt10", "cnt20", "cnt5_pct", "cnt10_pct", "cnt20_pct", "breadth")}
ok = [c for c, (dd, t, h1, h2, top) in res.items()
      if abs(t) >= 2 and np.sign(h1) == np.sign(h2) and top - T.R.mean() >= 0.2]
print("\nPRE-REGISTERED PASS:", ok or "NONE")
T.to_csv("data/studies/breakout_activity_gate_2026-09-22.csv", index=False)

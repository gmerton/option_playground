#!/usr/bin/env python3
"""
Two checks on the breakout pool (2026-09-17), written up in data/studies/breakout_regime_and_stop_distance_2026-09-17.md.

Pool = precision-shaped breakouts (ADDV >= $50M, ADR 4-7, within 15% of the 52wk high, stacked w/ house slack, close
clears the 15-day pivot on RVOL >= 1.1, upper-half close, gap < 5%, day < 8%), 2019-10 .. 2026-09, stop = entry-day low
judged on the close, exit = first close under the stop or the 20 EMA, 60-session cap. R = return / (entry - stop).

A. STOP DISTANCE: return per unit risked by how far the entry (the close) sat above the day's low, and by prior range
   contraction (10d range / prior 20d range).
B. REGIME FEEDBACK: for each session, does anything knowable that day predict the mean R of the NEXT month's new
   breakouts? Signals: last month's breakouts' 10-day return, their 10-day stop-out share, their count, SPY state.
   "Last month" = breakouts 15-45 days back, so their 10-day outcome is known. t-stats on non-overlapping months.

Usage: PYTHONPATH=src .venv/bin/python3 run_regime_feedback.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); piv = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None); run = stack_run(C, adr=adr)
r10 = H.rolling(10).max() - L.rolling(10).min(); r20p = H.shift(10).rolling(20).max() - L.shift(10).rolling(20).min(); contr = (r10 / r20p).shift(1)
pool = (elig & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (run > 0) & (C >= piv) & (rvol >= 1.1) & (pos >= 0.5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv)).fillna(False)
pool = pool[pool.index >= "2019-10-01"]; ii, jj = np.where(pool.values); ii = ii + (len(C) - len(pool)); Cv, Lv, E = C.values, L.values, e20.values


def hold(i, j):
    e, s = Cv[i, j], Lv[i, j]
    if not np.isfinite(e) or e <= s: return np.nan, np.nan
    for k in range(i + 1, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if np.isfinite(c) and (c < s or c < E[k, j]): return (c - e) / (e - s), c / e - 1
    k = min(i + 60, len(Cv) - 1); return (Cv[k, j] - e) / (e - s), Cv[k, j] / e - 1


d = pd.DataFrame([dict(date=C.index[i], dist=100 * (Cv[i, j] / Lv[i, j] - 1), adr=adr.values[i, j], contr=contr.values[i, j],
                       r10=(Cv[min(i + 10, len(Cv) - 1), j] / Cv[i, j] - 1) * 100, stop10=float(np.nanmin(Cv[i + 1:i + 11, j]) < Lv[i, j]) if i + 11 < len(Cv) else np.nan,
                       **dict(zip(("R", "ret"), hold(i, j)))) for i, j in zip(ii, jj)]).dropna(subset=["R"])
d["ret"] *= 100
print(f"breakout pool: {len(d):,} events {d['date'].min().date()}..{d['date'].max().date()}  mean R {d['R'].mean():+.2f}  ret {d['ret'].mean():+.2f}%")

print("\n== A. stop distance: entry (close) above the day's low ==")
for lo, hi in ((0, 1.5), (1.5, 3), (3, 5), (5, 8), (8, 99)):
    g = d[d["dist"].between(lo, hi)]
    print(f"  {lo:>3}-{hi:<3}%  n={len(g):5d}  R {g['R'].mean():+5.2f}  ret {g['ret'].mean():+5.2f}%  win {100*(g['R']>0).mean():.0f}%  stopped {100*(g['R']<=-0.99).mean():.0f}%  ret per 1% risked {g['ret'].mean()/g['dist'].mean():+.2f}")
print("  by prior contraction (10d range / prior 20d range):")
for lo, hi in ((0, 0.5), (0.5, 0.7), (0.7, 1.0), (1.0, 9)):
    g = d[d["contr"].between(lo, hi)]
    print(f"  {lo}-{hi}  n={len(g):5d}  stop dist {g['dist'].median():.1f}%  R {g['R'].mean():+5.2f}  ret {g['ret'].mean():+5.2f}%")

print("\n== B. regime feedback: next month's mean R of new breakouts, conditioned on what was knowable that day ==")
days = C.index[(C.index >= "2019-10-01") & (C.index <= d["date"].max() - pd.Timedelta(days=95))]
rows = []
for t in days:
    past = d[(d["date"] < t - pd.Timedelta(days=15)) & (d["date"] >= t - pd.Timedelta(days=45))]
    fut = d[(d["date"] > t) & (d["date"] <= t + pd.Timedelta(days=30))]
    if len(past) < 8 or len(fut) < 8: continue
    rows.append(dict(date=t, sig_r10=past["r10"].mean(), sig_stop=past["stop10"].mean(), n_past=len(past), fwd=fut["R"].mean()))
df = pd.DataFrame(rows).set_index("date")
s50, s200 = spy.rolling(50).mean(), spy.rolling(200).mean()
df["spy"] = pd.Series(np.where((spy > s50) & (s50 > s200), "up", np.where(spy < s200, "bear", "chop")), index=spy.index).reindex(df.index).ffill()


def show(lab, groups):
    print(f"  {lab}")
    for g, x in groups:
        w = x["fwd"].iloc[::21]
        print(f"    {str(g):<20} sessions {len(x):5d}  next-month R {x['fwd'].mean():+5.2f}  positive {100*(x['fwd']>0).mean():3.0f}%  (non-overlapping t {w.mean()/(w.std(ddof=1)/sqrt(len(w))):+.1f}, n {len(w)})")


show("last month's breakouts' 10-day return (quartiles, worst -> best)", df.groupby(pd.qcut(df["sig_r10"], 4, labels=["q1 worst", "q2", "q3", "q4 best"])))
show("share of last month's breakouts stopped within 10 days", df.groupby(pd.qcut(df["sig_stop"], 4, labels=["q1 fewest", "q2", "q3", "q4 most"])))
show("number of breakouts last month", df.groupby(pd.qcut(df["n_past"], 4, labels=["q1 quietest", "q2", "q3", "q4 busiest"])))
show("SPY state", df.groupby("spy"))
print(f"\n  rank corr with next-month R: own r10 {df['sig_r10'].corr(df['fwd'], method='spearman'):+.2f}, stop share {df['sig_stop'].corr(df['fwd'], method='spearman'):+.2f}, activity {df['n_past'].corr(df['fwd'], method='spearman'):+.2f}")
print(f"  unconditional next-month R {df['fwd'].mean():+.2f}; positive in {100*(df['fwd'].iloc[::21]>0).mean():.0f}% of non-overlapping months")
m = d.groupby(d["date"].dt.to_period("M"))["R"].agg(["sum", "size", "mean"]); top = m["sum"].sort_values(ascending=False)
print(f"  concentration: {len(m)} months; the top {max(1, len(m)//10)} months (10%) supply {100*top.head(max(1, len(m)//10)).sum()/top[top>0].sum():.0f}% of all positive R; months with mean R > 0: {100*(m['mean']>0).mean():.0f}%")

#!/usr/bin/env python3
"""
Gap share x entry/stop on the breakout pool (2026-09-22, queued in TEST_INDEX §10 the same day).

Gap share = var(ln open/prev close) / (that + var(ln close/open)) over the prior 504 sessions (min 250), known
strictly before the entry day. It is a stable stock trait (rank corr ~0.5 period to period). The question is
whether it changes which entry / stop works.

Pool = the precision-shaped breakout pool from run_regime_feedback.py (ADDV >= $50M, ADR 4-7, within 15% of the
52wk high, stacked, close clears the 15-day pivot on RVOL >= 1.1, upper-half close, gap < 5%, day < 8%).
Stop = entry-day low. Exits: first close under the 20 EMA, 60-session cap, plus the stop:
  close_judged   exit at the first CLOSE under the stop (the house method)
  resting        a resting intraday stop at the low: filled at min(open, stop) the first day low <= stop
  ideal          same trigger as resting but always filled AT the stop (no gap-through) -- the ceiling on what a
                 gap-proof vehicle (defined-risk option) could save before its own costs
Entries: at the breakout close (house) vs the next session's open (misses the overnight).

Pre-registered pass (written before the run): top-tercile minus bottom-tercile difference in a quantity with
|t| >= 2 on month-clustered means, same sign in both halves (split 2023-01-01).

Usage: PYTHONPATH=src .venv/bin/python3 run_gap_share_study.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); piv = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None); run = stack_run(C, adr=adr)
pool = (elig & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (run > 0) & (C >= piv) & (rvol >= 1.1) & (pos >= 0.5)
        & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv)).fillna(False)

# gap share, strictly prior data
on = np.log(O / C.shift(1)); intra = np.log(C / O)
on, intra = on.where(on.abs() < 0.5), intra.where(intra.abs() < 0.5)
vo = on.rolling(504, min_periods=250).var().shift(1); vi = intra.rolling(504, min_periods=250).var().shift(1)
gshare = vo / (vo + vi)

pool = pool[pool.index >= "2019-10-01"]; off = len(C) - len(pool)
ii, jj = np.where(pool.values); ii = ii + off
Cv, Ov, Lv, E, G = C.values, O.values, L.values, e20.values, gshare.values
N = len(Cv)


def walk(i, j, entry, start, mode):
    """R of one trade. entry price, first day to check exits, stop mode."""
    s = Lv[i, j]
    if not (np.isfinite(entry) and entry > s): return np.nan
    risk = entry - s
    for k in range(start, min(i + 61, N)):
        o, lo, c = Ov[k, j], Lv[k, j], Cv[k, j]
        if not np.isfinite(c): continue
        if mode != "close_judged" and np.isfinite(lo) and lo <= s:
            fill = s if mode == "ideal" else min(o, s) if np.isfinite(o) else s
            return (fill - entry) / risk
        if (mode == "close_judged" and c < s) or c < E[k, j]:
            return (c - entry) / risk
    k = min(i + 60, N - 1); return (Cv[k, j] - entry) / risk


rows = []
for i, j in zip(ii, jj):
    if not np.isfinite(G[i, j]) or i + 2 >= N: continue
    ce, ne = Cv[i, j], Ov[i + 1, j]
    r = dict(date=C.index[i], sym=C.columns[j], gshare=G[i, j])
    for m in ("close_judged", "resting", "ideal"):
        r[f"close_{m}"] = walk(i, j, ce, i + 1, m)
    # next-open entry: same stop, exits from the entry day's close onward (the open is the fill)
    r["nextopen_close_judged"] = walk(i, j, ne, i + 1, "close_judged") if np.isfinite(ne) and ne > Lv[i, j] else np.nan
    r["overnight_R"] = (ne - ce) / (ce - Lv[i, j]) if np.isfinite(ne) else np.nan
    rows.append(r)
d = pd.DataFrame(rows).dropna(subset=["close_close_judged"])
d = d.assign(**{c: d[c].clip(-10, 10) for c in d.columns if c.startswith(("close_", "nextopen_", "overnight"))})
# terciles within each year so the cut is not driven by market-wide vol regimes
d["terc"] = d.groupby(d.date.dt.year)["gshare"].transform(lambda x: pd.qcut(x, 3, labels=["low", "mid", "high"]))
d["gap_through"] = d["close_resting"] < d["close_ideal"] - 1e-9
d["blow"] = d["close_ideal"] - d["close_resting"]            # R lost to gapping through the resting stop
d["open_minus_close"] = d["nextopen_close_judged"] - d["close_close_judged"]
d["resting_minus_cj"] = d["close_resting"] - d["close_close_judged"]
d["month"] = d.date.dt.to_period("M")

print(f"breakout pool with a gap share: {len(d):,} events, {d.date.min().date()}..{d.date.max().date()}, "
      f"{d.month.nunique()} months, {d.date.nunique()} entry dates")
print(f"gap share tercile cuts (median by tercile): {d.groupby('terc')['gshare'].median().round(3).to_dict()}\n")


def mt(x):
    x = x.dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def diff_t(col, sub):
    m = sub.groupby(["month", "terc"])[col].mean().unstack()
    dd = (m["high"] - m["low"]).dropna(); return dd.mean(), mt(dd), len(dd)


cols = [("close_close_judged", "R, close entry, close-judged stop (house)"),
        ("close_resting", "R, close entry, resting intraday stop"),
        ("close_ideal", "R, close entry, ideal stop (no gap-through)"),
        ("nextopen_close_judged", "R, next-open entry, close-judged stop"),
        ("overnight_R", "overnight move after the breakout close, in R"),
        ("blow", "R lost to gap-through (ideal - resting)"),
        ("gap_through", "share of trades that gapped through the stop"),
        ("open_minus_close", "next-open entry minus close entry"),
        ("resting_minus_cj", "resting stop minus close-judged stop")]
tab = d.groupby("terc")[[c for c, _ in cols]].mean().T
tab["high-low"] = tab["high"] - tab["low"]
for half, sub in (("all", d), ("<2023", d[d.date < "2023-01-01"]), (">=2023", d[d.date >= "2023-01-01"])):
    tab[f"t {half}"] = [diff_t(c, sub)[1] for c, _ in cols]
    tab[f"diff {half}"] = [diff_t(c, sub)[0] for c, _ in cols]
tab.index = [lab for _, lab in cols]
pd.set_option("display.width", 250)
print(tab[["low", "mid", "high", "high-low", "t all", "diff <2023", "t <2023", "diff >=2023", "t >=2023"]].round(3).to_string())
print(f"\nn per tercile: {d.terc.value_counts().sort_index().to_dict()}")

passed = []
for c, lab in cols:
    _, ta, _ = diff_t(c, d); d1, t1, _ = diff_t(c, d[d.date < "2023-01-01"]); d2, t2, _ = diff_t(c, d[d.date >= "2023-01-01"])
    if abs(ta) >= 2 and np.sign(d1) == np.sign(d2): passed.append(lab)
print("\npre-registered pass (|t|>=2 month-clustered, same sign both halves):", passed or "NONE")
d.to_csv("data/studies/gap_share_study_events.csv", index=False)

# ---- control: same names, random other eligible days (same stop/exit), so a gap-share effect that is just
# "these stocks drift up" (the overnight tug-of-war) shows up in the control too
rng = np.random.default_rng(7)
elv = (elig & (run > 0)).values
tick_ix = {s: k for k, s in enumerate(C.columns)}
crow = []
for r in d.itertuples():
    j = tick_ix[r.sym]; i = C.index.get_loc(r.date)
    cand = [k for k in range(max(260, i - 250), min(N - 61, i + 250)) if elv[k, j] and np.isfinite(G[k, j]) and k != i]
    for k in rng.choice(cand, size=min(3, len(cand)), replace=False) if cand else []:
        crow.append(dict(date=C.index[k], sym=r.sym, terc=r.terc, R=walk(k, j, Cv[k, j], k + 1, "close_judged")))
K = pd.DataFrame(crow).dropna(); K["R"] = K["R"].clip(-10, 10); K["month"] = K.date.dt.to_period("M")
print("\n== control: same names, random eligible days ==")
kt = K.groupby("terc")["R"].mean(); bt = d.groupby("terc")["close_close_judged"].mean()
print(pd.DataFrame({"breakout R": bt, "control R": kt, "edge": bt - kt}).round(3).to_string())
for half, sub in (("all", K), ("<2023", K[K.date < "2023-01-01"]), (">=2023", K[K.date >= "2023-01-01"])):
    m = sub.groupby(["month", "terc"])["R"].mean().unstack(); dd = (m["high"] - m["low"]).dropna()
    print(f"  control high-low {half:7} {dd.mean():+.3f}  t {mt(dd):+.2f}")
# edge (breakout - control) high vs low, month clustered
d["ctrl"] = d.set_index(["sym"]).index.map(K.groupby("sym")["R"].mean())
d["edge"] = d["close_close_judged"] - d["ctrl"]
for half, sub in (("all", d), ("<2023", d[d.date < "2023-01-01"]), (">=2023", d[d.date >= "2023-01-01"])):
    a, t, _ = diff_t("edge", sub); print(f"  edge high-low {half:7} {a:+.3f}  t {t:+.2f}")
im = pd.read_csv("data/ticker_industry_map.csv").set_index("ticker")
print("\nsector mix by tercile (% of events):")
print((pd.crosstab(d.sym.map(im.sector).fillna("?"), d.terc, normalize="columns") * 100).round(0).to_string())
print("\nR by tercile within the two biggest sectors:")
for sec in d.sym.map(im.sector).value_counts().index[:2]:
    print(f"  {sec}: {d[d.sym.map(im.sector) == sec].groupby('terc')['close_close_judged'].agg(['mean', 'size']).round(3).to_dict('index')}")

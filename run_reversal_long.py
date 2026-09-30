#!/usr/bin/env python3
"""Reversal LONG: buy the fresh 15-close low in a downtrend, survivorship-free chain-spot series (2026-09-30).

PRE-REGISTERED: data/studies/reversal_long_2026-09-30.md (committed before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_reversal_long.py   (log -> data/studies/logs/reversal_long.log)
"""
from __future__ import annotations

import sys
from math import sqrt

import numpy as np
import pandas as pd

import run_dip_survivorship as ds

START, END, SPLIT, COST, SEED = "2010-06-01", "2025-11-30", "2018-01-01", 0.0010, 20260930
LOG = ds.REPO / "data/studies/logs/reversal_long.log"


def build(C: pd.DataFrame, V: pd.DataFrame, k: float, surv: set, spy_ok: pd.Series,
          lags=(1, 0), holds=(10, 5, 20)) -> pd.DataFrame:
    idx, cols = C.index, np.array(C.columns)
    ret = C.pct_change(fill_method=None)
    adrp = ret.abs().shift(1).rolling(20, min_periods=15).mean() * k * 100
    s10, s20, s50 = (C.rolling(n, min_periods=int(n * .8)).mean() for n in (10, 20, 50))
    stack5 = ((s10 < s20) & (s20 < s50)).astype(float).rolling(5).sum() >= 5
    low15 = C.shift(1).rolling(15, min_periods=12).min()
    liq = (V.rolling(50, min_periods=30).mean() >= 1000) & (C >= 5)
    brk = (C < low15) & ~(C.shift(1) < low15.shift(1)) & stack5 & (adrp >= 3) & (ret >= -0.08) & liq
    brk.loc[(idx < START) | (idx > END)] = False
    Cv, A = C.values, adrp.values
    EL, B = (liq & adrp.notna()).fillna(False).values, brk.fillna(False).values
    n = len(Cv)
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                     for j in range(Cv.shape[1])])
    healthy = spy_ok.reindex(idx).fillna(False).values

    def long_ret(i, j, lag, hold):
        e_i = i + lag
        if e_i >= n or not np.isfinite(Cv[e_i, j]):
            return np.nan
        x_i = min(e_i + hold, n - 1, last[j])
        if x_i <= e_i:
            return np.nan
        seg = Cv[e_i:x_i + 1, j]
        seg = seg[np.isfinite(seg)]
        return 100 * (seg[-1] * (1 - COST) / (Cv[e_i, j] * (1 + COST)) - 1)

    is_surv = np.isin(cols, list(surv))
    rng = np.random.default_rng(SEED)
    rows = []
    for i, j in zip(*np.where(B)):
        ok = EL[i] & ~B[i] & (is_surv == is_surv[j])
        if ok.sum() < 30:
            continue
        q = np.nanquantile(A[i, ok], [1 / 3, 2 / 3])
        tc = lambda v: 0 if v <= q[0] else (1 if v <= q[1] else 2)
        pool = np.flatnonzero(ok)
        pool = pool[np.array([tc(v) for v in A[i, pool]]) == tc(A[i, j])]
        if not len(pool):
            continue
        ctl = rng.choice(pool, size=min(3, len(pool)), replace=False)
        rec = dict(date=idx[i], sym=cols[j], surv=bool(is_surv[j]), healthy=bool(healthy[i]))
        for lag in lags:
            for h in holds:
                r = long_ret(i, j, lag, h)
                cs = [long_ret(i, int(c), lag, h) for c in ctl]
                rec[f"r_{lag}_{h}"] = r
                rec[f"c_{lag}_{h}"] = np.nanmean(cs) if np.isfinite(cs).any() else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def cell(T: pd.DataFrame, lag=1, h=10) -> dict:
    r, c = f"r_{lag}_{h}", f"c_{lag}_{h}"
    T = T.dropna(subset=[r, c]).copy()
    if len(T) < 20:
        return dict(n=len(T))
    T["x"] = T[r] - T[c]
    g, gr = T.groupby("date").x.mean(), T.groupby("date")[r].mean()
    hh = g.index < SPLIT
    yr = T.groupby(T.date.dt.year).x.mean()
    xs = T.x.sort_values(ascending=False)
    top1 = xs.head(max(1, len(xs) // 100)).sum() / xs.sum() if xs.sum() > 0 else np.nan
    return dict(n=len(T), dates=len(g), names=T.sym.nunique(), long_net=T[r].mean(),
                t_abs=gr.mean() / gr.std(ddof=1) * sqrt(len(gr)), ctrl=T[c].mean(), excess=T.x.mean(),
                t=g.mean() / g.std(ddof=1) * sqrt(len(g)), h1=g[hh].mean(), h2=g[~hh].mean(),
                yrs=f"{int((yr > 0).sum())}/{len(yr)}", yrs_share=(yr > 0).mean(), win=100 * (T[r] > 0).mean(),
                top1_share=top1)


def main():
    Cc, V = ds.adjust_and_clean(ds.pull())
    surv = set(pd.read_parquet(ds.REPO / "data/cache/liquid_panel_2009.parquet", columns=["ticker"]).ticker.unique())
    k = ds.k_scale()
    spy = Cc["SPY"].dropna()
    s50 = spy.rolling(50).mean()
    spy_ok = (spy > s50) & (s50 > s50.shift(10))
    T = build(Cc, V, k, surv, spy_ok)
    fmt = lambda d: pd.DataFrame(d).round(3).to_string(index=False)
    print(f"# reversal long (pre-registration in the md); k {k:.3f}; signals {len(T):,}")
    P = cell(T)
    print("\n## PRIMARY: ALL, entry t+1 close, 10-day hold")
    print(fmt([dict(cell="ALL t+1 h10", **P)]))
    ok = (P["excess"] > 0 and P["t"] >= 3 and P["h1"] > 0 and P["h2"] > 0 and P["yrs_share"] > .5
          and P["long_net"] > 0)
    print(f"PRIMARY bar: {'PASS' if ok else 'FAIL'}")
    r, c = "r_1_10", "c_1_10"
    yr = T.dropna(subset=[r, c]).assign(x=lambda d: d[r] - d[c]).groupby(T.date.dt.year)[[r, "x"]].mean().round(2)
    print("per year: long net % / excess %\n" + yr.T.to_string())
    print("\n## pre-declared checks")
    print(fmt([dict(cell="(a) HEALTHY tape", **cell(T[T.healthy])), dict(cell="(a) UNHEALTHY tape", **cell(T[~T.healthy]))]))
    print(f"(b) top-1% share of summed excess: {P['top1_share']:.1%}")
    raw = pd.read_parquet(ds.REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    raw["date"] = pd.to_datetime(raw.date)
    Cp = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    cols = sorted(set(Cp.columns) & set(Cc.columns))
    Tp = build(Cp.reindex(index=Cc.index, columns=cols), V[cols], k, set(cols), spy_ok, lags=(1,), holds=(10,))
    print(fmt([dict(cell="(c) method check SURV on panel closes", **cell(Tp))]))
    print("\n## secondary (Sidak k = 4, |t| >= 2.8; house 3 governs)")
    print(fmt([dict(cell="entry t close, h10", **cell(T, 0, 10)), dict(cell="t+1, h5", **cell(T, 1, 5)),
               dict(cell="t+1, h20", **cell(T, 1, 20)), dict(cell="SURV t+1 h10", **cell(T[T.surv])),
               dict(cell="NONSURV t+1 h10", **cell(T[~T.surv]))]))
    T.to_csv(ds.REPO / "data/studies/logs/reversal_long_trades.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

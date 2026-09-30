#!/usr/bin/env python3
"""Close-only mirror-breakdown short on the survivorship-free chain-spot series (2026-09-29).

PRE-REGISTERED: data/studies/breakdown_survivorship_2026-09-29.md (committed b276450 before this ran).
Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_breakdown_survivorship.py \
         > data/studies/breakdown_survivorship_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

import run_dip_survivorship as ds

START, END, SPLIT, COST, SEED = "2010-06-01", "2025-11-30", "2018-01-01", 0.0010, 20260929


def signals_and_trades(C: pd.DataFrame, V: pd.DataFrame, k: float, surv: set, groups=("ALL", "SURV", "NONSURV")):
    idx, cols = C.index, np.array(C.columns)
    ret = C.pct_change(fill_method=None)
    adrp = ret.abs().shift(1).rolling(20, min_periods=15).mean() * k * 100
    s10, s20, s50 = (C.rolling(n, min_periods=int(n * .8)).mean() for n in (10, 20, 50))
    down = (s10 < s20) & (s20 < s50)
    stack5 = down.astype(float).rolling(5).sum() >= 5
    low15 = C.shift(1).rolling(15, min_periods=12).min()
    liq = (V.rolling(50, min_periods=30).mean() >= 1000) & (C >= 5)
    brk = (C < low15) & ~(C.shift(1) < low15.shift(1)) & stack5 & (adrp >= 3) & (ret >= -0.08) & liq
    brk.loc[(idx < START) | (idx > END)] = False
    e20 = C.ewm(span=20, adjust=False).mean().values
    Cv, A, EL, B = C.values, adrp.values, (liq & adrp.notna()).fillna(False).values, brk.fillna(False).values
    n = len(Cv)
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1 for j in range(Cv.shape[1])])

    def short_trade(i, j):
        e = Cv[i, j]
        if not np.isfinite(e) or i < 1:
            return np.nan, False
        stop = max(Cv[i - 1, j] if np.isfinite(Cv[i - 1, j]) else e, e * 1.02)
        kx, delist = None, False
        for k_ in range(i + 1, min(i + 61, n)):
            c = Cv[k_, j]
            if not np.isfinite(c):
                if k_ > last[j]:
                    delist = True; break
                continue
            kx = k_
            if c > stop or c > e20[k_, j]:
                break
        if kx is None:
            return np.nan, delist
        x = Cv[kx, j]
        return 100 * ((e * (1 - COST)) - x * (1 + COST)) / e, delist and kx == last[j]

    is_surv = np.isin(cols, list(surv))
    rng = np.random.default_rng(SEED)
    rows = []
    for i, j in zip(*np.where(B)):
        r, dl = short_trade(i, j)
        if not np.isfinite(r):
            continue
        ok = EL[i] & ~B[i] & (is_surv == is_surv[j])       # control from the signal's own group-universe
        a = A[i, ok]
        if ok.sum() < 30:
            continue
        q = np.nanquantile(a, [1 / 3, 2 / 3])
        tc = lambda v: 0 if v <= q[0] else (1 if v <= q[1] else 2)
        pool = np.flatnonzero(ok)
        pool = pool[np.array([tc(v) for v in A[i, pool]]) == tc(A[i, j])]
        cs = [short_trade(i, int(c))[0] for c in rng.choice(pool, size=min(3, len(pool)), replace=False)] if len(pool) else []
        cm = np.nanmean(cs) if len(cs) and np.isfinite(cs).any() else np.nan
        rows.append(dict(date=idx[i], sym=cols[j], surv=bool(is_surv[j]), ret=r, ctrl=cm, delist=dl))
    return pd.DataFrame(rows)


def cell(T: pd.DataFrame) -> dict:
    T = T.dropna(subset=["ret", "ctrl"]).copy()
    T["x"] = T.ret - T.ctrl
    g = T.groupby("date").x.mean()
    h = g.index < SPLIT
    yr = T.groupby(T.date.dt.year).x.mean()
    gr = T.groupby("date").ret.mean()
    return dict(n=len(T), dates=len(g), names=T.sym.nunique(), short_ret=T.ret.mean(), t_abs=gr.mean() / gr.std(ddof=1) * sqrt(len(gr)),
                ctrl=T.ctrl.mean(), excess=T.x.mean(), t=g.mean() / g.std(ddof=1) * sqrt(len(g)), h1=g[h].mean(), h2=g[~h].mean(),
                yrs=f"{int((yr > 0).sum())}/{len(yr)}", yrs_share=(yr > 0).mean(), win=(T.ret > 0).mean() * 100,
                delisted_pct=100 * T.delist.mean())


def main():
    Cc, V = ds.adjust_and_clean(ds.pull())
    surv = set(pd.read_parquet(ds.REPO / "data/cache/liquid_panel_2009.parquet", columns=["ticker"]).ticker.unique())
    k = ds.k_scale()
    T = signals_and_trades(Cc, V, k, surv)
    rows = [dict(group="ALL (PRIMARY)", **cell(T)), dict(group="SURV", **cell(T[T.surv])), dict(group="NONSURV", **cell(T[~T.surv]))]
    # method check: same rule on the survivor panel's own closes (same tickers/dates, chain option volume as the gate)
    raw = pd.read_parquet(ds.REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    raw["date"] = pd.to_datetime(raw.date)
    Cp = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    cols = sorted(set(Cp.columns) & set(Cc.columns))
    Tp = signals_and_trades(Cp.reindex(index=Cc.index, columns=cols), V[cols], k, set(cols))
    rows.append(dict(group="method check: SURV on panel closes", **cell(Tp)))
    R = pd.DataFrame(rows)
    print(f"# mirror-breakdown short, close-only (pre-registration in the md); k {k:.3f}; tickers {Cc.shape[1]:,}")
    print(R.round(3).to_string(index=False))
    p = R.iloc[0]
    ok = p.excess > 0 and p.t >= 3 and p.h1 > 0 and p.h2 > 0 and p.yrs_share > 0.5 and p.short_ret > 0
    print(f"\nPRIMARY (ALL: excess t >= 3, halves > 0, majority yrs, absolute net > 0): {'PASS' if ok else 'FAIL'}")
    yr = T.dropna(subset=["ctrl"]).assign(x=lambda d: d.ret - d.ctrl).groupby(T.date.dt.year)[["ret", "x"]].mean().round(2)
    print("\nper year (ALL): short ret % / excess %\n" + yr.T.to_string())
    T.to_csv(ds.REPO / "data/studies/logs/breakdown_survivorship_trades.csv", index=False)


if __name__ == "__main__":
    main()

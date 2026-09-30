#!/usr/bin/env python3
"""D1 dollar-volume ranking on the 2010-19 holdout; D2 up/down volume ratio on breakouts (2026-09-29).
PRE-REGISTERED: data/studies/dolvol_holdout_and_udvr_2026-09-29.md (committed 6220099 before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_dolvol_holdout_udvr.py > data/studies/dolvol_holdout_and_udvr_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

import run_rvol_drop_and_score as rv
from lib.studies.pattern_test import load_panel
from run_retrace_entry import masks

BAR = 3.2


def d1():
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "volume"])
    raw["date"] = pd.to_datetime(raw.date)
    V = raw.pivot(index="date", columns="ticker", values="volume").reindex(index=P.close.index, columns=P.close.columns)
    brk, _, _ = masks(P, 20, 0.0)
    C, L, A = P.close, P.low, P.adr
    e20 = C.ewm(span=20, adjust=False).mean()
    cv, lv, av, E = C.values, L.values, A.values, e20.values
    dv = (C * V / 1e6).values
    idx = C.index
    recs = []
    for i, j in np.argwhere(brk.values):
        d = idx[i]
        if d < pd.Timestamp("2010-01-01") or d > pd.Timestamp("2019-09-30") or i + 5 >= len(idx):
            continue
        e, a = cv[i, j], av[i, j]
        if not (np.isfinite(e) and np.isfinite(a)) or a <= 0:
            continue
        stop = e * (1 - a / 100); risk = e - stop
        pl, pc = lv[i + 1:i + 6, j], cv[i + 1:i + 6, j]
        if not np.isfinite(pc).all():
            continue
        hit = np.flatnonzero(pl <= stop)
        R5 = ((stop if len(hit) else pc[-1]) - e) / risk
        recs.append(dict(date=d, R=R5, Rh=rv.trade(cv, lv, E, i, j), dolvol=dv[i, j], adr=a))
    D = pd.DataFrame(recs).dropna(subset=["dolvol"])
    D["terc"] = D.groupby("date").adr.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False) if len(s) >= 3 else 0)

    def cell(d, n, col="R", by=None):
        use = d.dropna(subset=[col])
        grp = ["date"] + ([by] if by else [])
        sizes = use.groupby(grp)[col].transform("size")
        use = use[sizes >= max(5, 2 * n)]
        picks = use.sort_values(grp + ["dolvol"], ascending=[True] * len(grp) + [False]).groupby(grp).head(n)
        sel = picks.groupby(grp)[col].mean(); day = use.groupby(grp)[col].mean()
        delta = (sel - day).dropna()
        if by:
            delta = delta.groupby(level=0).mean()
        t = delta.mean() / delta.std(ddof=1) * sqrt(len(delta))
        half = len(delta) // 2
        yr = delta.groupby(delta.index.year).mean()
        return dict(N=n, R=col, by=by or "-", dates=len(delta), delta=delta.mean(), t=t, h1=delta.iloc[:half].mean(),
                    h2=delta.iloc[half:].mean(), yrs_pos=f"{int((yr > 0).sum())}/{len(yr)}", yrs_share=(yr > 0).mean(),
                    per_year=" ".join(f"{y}:{v:+.3f}" for y, v in yr.items()))
    rows = [cell(D, n) for n in (1, 2, 3, 5)] + [cell(D, 2, "Rh"), cell(D, 2, by="terc")]
    return pd.DataFrame(rows), len(D)


def d2():
    C, L, e20, elig, pool, A, B, F = rv.build()
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "volume"])
    raw["date"] = pd.to_datetime(raw.date)
    V = raw.pivot(index="date", columns="ticker", values="volume").reindex(index=C.index, columns=C.columns)
    up, dn = C > C.shift(1), C < C.shift(1)
    udvr = (V.where(up, 0).rolling(50, min_periods=40).sum() / V.where(dn, 0).rolling(50, min_periods=40).sum().replace(0, np.nan))
    pct = udvr.where(elig).rank(axis=1, pct=True)
    idx = C.index
    Cv, Lv, E = C.values, L.values, e20.values
    ctl = rv.Ctl(Cv, Lv, E, elig.values, pool.values, F["adr"].values)
    win = (idx >= "2010-01-01") & (idx <= "2026-06-30")
    PV, AV = pct.values, A.values
    rows = []
    for i, j in zip(*np.where(pool.values)):
        if not win[i] or not np.isfinite(PV[i, j]):
            continue
        r = rv.trade(Cv, Lv, E, i, j)
        if not np.isfinite(r):
            continue
        c = ctl(i, j)
        if np.isfinite(c):
            rows.append(dict(date=idx[i], pct=PV[i, j], tier=bool(AV[i, j]), ex=r - c))
    X = pd.DataFrame(rows)
    X["q"] = pd.cut(X.pct, [0, .2, .4, .6, .8, 1.0001], labels=False, include_lowest=True)

    def topbot(Z):
        m = Z.date.dt.to_period("M")
        top = Z[Z.pct >= 2 / 3].groupby(m[Z.pct >= 2 / 3]).ex.mean()
        bot = Z[Z.pct < 1 / 3].groupby(m[Z.pct < 1 / 3]).ex.mean()
        d = (top - bot).dropna(); h = d.index < pd.Period("2018-01", "M")
        return dict(n=len(Z), months=len(d), diff=d.mean(), t=d.mean() / d.std(ddof=1) * sqrt(len(d)), h1=d[h].mean(), h2=d[~h].mean())
    res = pd.DataFrame([dict(pop="broad pool (PRIMARY)", **topbot(X)), dict(pop="precision tier", **topbot(X[X.tier]))])
    dose = X.groupby("q").ex.agg(["size", "mean"]).rename(columns={"size": "n", "mean": "mean_excess_R"})
    return res, dose


def main():
    out = ["# RVOL-proxy tests (pre-registration in the md)"]
    R1, n1 = d1()
    out.append(f"\n== D1: top-N by dollar volume within day, 2010-01 -> 2019-09 holdout ({n1:,} breakouts) ==")
    out.append(R1.drop(columns=["per_year", "yrs_share"]).round(4).to_string(index=False))
    p = R1[(R1.N == 2) & (R1.R == "R") & (R1.by == "-")].iloc[0]
    ok = p.delta > 0 and p.t >= BAR and p.h1 > 0 and p.h2 > 0 and p.yrs_share > 0.5
    out.append(f"per year (N=2): {p.per_year}")
    out.append(f"D1 PRIMARY (N=2): delta {p.delta:+.4f}R t {p.t:+.2f}, halves {p.h1:+.4f}/{p.h2:+.4f}, yrs+ {p.yrs_pos} -> {'PASS' if ok else 'FAIL'}")
    R2, dose = d2()
    out.append("\n== D2: UDVR top vs bottom tercile (cross-sectional pct among eligible), excess R vs same-date controls ==")
    out.append(R2.round(4).to_string(index=False))
    out.append("dose-response by UDVR quintile (broad pool):\n" + dose.round(4).to_string())
    q = R2.iloc[0]
    ok2 = q["diff"] > 0 and q.t >= BAR and q.h1 > 0 and q.h2 > 0
    out.append(f"D2 PRIMARY: top - bottom {q['diff']:+.4f}R t {q.t:+.2f}, halves {q.h1:+.4f}/{q.h2:+.4f} -> {'PASS' if ok2 else 'FAIL'}")
    print("\n".join(out))


if __name__ == "__main__":
    main()

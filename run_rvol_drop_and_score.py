#!/usr/bin/env python3
"""T1: does the RVOL gate do joint work in the precision tier?  T2: walk-forward ridge score vs the tier's box.
PRE-REGISTERED: data/studies/rvol_drop_and_score_vs_box_2026-09-29.md (committed effa552 before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_rvol_drop_and_score.py > data/studies/rvol_drop_and_score_vs_box_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

COST, CAP, FLOOR, SEED = 0.0005, 20.0, 0.02, 20260929
SPLIT1, SPLIT2 = pd.Timestamp("2018-01-01"), pd.Timestamp("2019-01-01")


def build():
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    F = dict(adr=adr, range52=(hi52 - lo52) / C * 100, rvol=V / V.shift(1).rolling(50).mean(),
             pos=(C - L) / (H - L).replace(0, np.nan), stack=stack_run(C, adr=adr).fillna(0), gap=O / C.shift(1) - 1,
             chg=C.pct_change(fill_method=None), off52=(C / hi52 - 1) * 100, laddv=np.log(p.dolvol.rolling(50, min_periods=40).mean()))
    piv15 = H.shift(1).rolling(15).max()
    pool = elig & (C >= piv15) & (C.shift(1) < piv15)
    common = ((F["adr"] >= 3) & (F["range52"] >= 17) & (F["pos"] >= 0.5) & (F["stack"] >= 5) & (F["gap"] < 0.05) & (F["chg"] < 0.08)
              & (F["adr"] >= 4) & (F["adr"] <= 7) & (F["off52"] > -15) & (F["stack"] <= 40))
    A = (pool & common & (F["rvol"] >= 1.1)).fillna(False)
    B = (pool & common).fillna(False)
    e20 = C.ewm(span=20, adjust=False).mean()
    return C, L, e20, elig, pool.fillna(False), A, B, F


def trade(Cv, Lv, E, i, j):
    n = len(Cv)
    entry = Cv[i, j]
    if not np.isfinite(entry) or i + 2 >= n:
        return np.nan
    stop = min(Lv[i, j], entry * (1 - FLOOR)); risk = entry - stop
    if not np.isfinite(stop) or risk <= 0:
        return np.nan
    k = None
    for k_ in range(i + 1, min(i + 61, n)):
        c = Cv[k_, j]
        if not np.isfinite(c):
            continue
        k = k_
        if c < stop or c < E[k_, j]:
            break
    if k is None:
        return np.nan
    return float(np.clip((Cv[k, j] * (1 - COST) - entry * (1 + COST)) / risk, -CAP, CAP))


class Ctl:
    """3 random same-date eligible non-pool names in the signal's ADR tercile; cached per (i, j) so every arm sees the same controls."""
    def __init__(self, Cv, Lv, E, elig, pool, adr):
        self.Cv, self.Lv, self.E, self.EL, self.PO, self.A = Cv, Lv, E, elig, pool, adr
        self.cache = {}

    def __call__(self, i, j):
        if (i, j) in self.cache:
            return self.cache[(i, j)]
        ok = self.EL[i] & ~self.PO[i] & np.isfinite(self.A[i]) & np.isfinite(self.Cv[i])
        val = np.nan
        if ok.sum() >= 30:
            q = np.nanquantile(self.A[i, ok], [1 / 3, 2 / 3])
            t = lambda a: np.where(a <= q[0], 0, np.where(a <= q[1], 1, 2))
            pool = np.flatnonzero(ok & (t(self.A[i]) == t(self.A[i, j])))
            rng = np.random.default_rng((i * 1_000_003 + j + SEED) % 2 ** 32)
            rs = [trade(self.Cv, self.Lv, self.E, i, int(c), ) for c in rng.choice(pool, size=min(3, len(pool)), replace=False)] if len(pool) else []
            rs = [r for r in rs if np.isfinite(r)]
            val = float(np.mean(rs)) if rs else np.nan
        self.cache[(i, j)] = val
        return val


def arm_table(sig: list[tuple[int, int]], R: dict, ctl: Ctl, idx) -> pd.DataFrame:
    rows = []
    for i, j in sig:
        r = R.get((i, j))
        if r is None or not np.isfinite(r):
            continue
        c = ctl(i, j)
        if np.isfinite(c):
            rows.append(dict(date=idx[i], R=r, ctl=c, ex=r - c))
    return pd.DataFrame(rows)


def month_stats(T: pd.DataFrame, split) -> dict:
    m = T.groupby(T.date.dt.to_period("M")).ex.mean()
    h = m.index < pd.Period(split, "M")
    return dict(n=len(T), meanR=T.R.mean(), excess=T.ex.mean(), months=len(m), t=m.mean() / m.std(ddof=1) * sqrt(len(m)),
                h1=m[h].mean(), h2=m[~h].mean())


def main():
    C, L, e20, elig, pool, A, B, F = build()
    idx = C.index
    Cv, Lv, E = C.values, L.values, e20.values
    ctl = Ctl(Cv, Lv, E, elig.values, pool.values, F["adr"].values)
    win = (idx >= "2010-01-01") & (idx <= "2026-06-30")
    PI = [(i, j) for i, j in zip(*np.where(pool.values)) if win[i]]
    R = {(i, j): trade(Cv, Lv, E, i, j) for i, j in PI}
    out = [f"# RVOL drop + score vs box (pre-registration in the md). pool events {len(PI):,}"]

    # ---- T1
    Aset = {(i, j) for i, j in zip(*np.where(A.values)) if win[i]}
    Bset = {(i, j) for i, j in zip(*np.where(B.values)) if win[i]}
    X = sorted(Bset - Aset)
    st = {k: month_stats(arm_table(sorted(s), R, ctl, idx), SPLIT1) for k, s in (("A tier (RVOL>=1.1)", Aset), ("B tier w/o RVOL", Bset), ("X = B minus A", X))}
    out.append("\n== T1: does RVOL do joint work? (excess R vs 3 same-date ADR-tercile non-breakout names) ==")
    out.append(pd.DataFrame(st).T.round(3).to_string())
    a, x = st["A tier (RVOL>=1.1)"], st["X = B minus A"]
    drop = x["excess"] >= 0.5 * a["excess"] and x["h1"] >= 0 and x["h2"] >= 0
    out.append(f"T1 RULE: X excess {x['excess']:+.3f} vs 0.5 x A {0.5 * a['excess']:+.3f}; X halves {x['h1']:+.3f}/{x['h2']:+.3f} -> "
               f"{'DROP RVOL' if drop else 'KEEP RVOL'}")

    # ---- T2
    feats = list(F)
    Fv = {k: F[k].values for k in feats}
    D = pd.DataFrame([dict(i=i, j=j, date=idx[i], R=R[(i, j)], box=(i, j) in Aset, **{k: Fv[k][i, j] for k in feats}) for i, j in PI])
    D = D.replace([np.inf, -np.inf], np.nan).dropna(subset=feats + ["R"]).reset_index(drop=True)
    D["y"] = D.R.clip(-5, 5)
    D["pred"] = np.nan; D["sel"] = False
    coefs = {}
    for Y in range(2012, 2027):
        tr = D.date < pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=90)
        te = D.date.dt.year == Y
        if tr.sum() < 2000 or te.sum() == 0:
            continue
        mu, sd = D.loc[tr, feats].mean(), D.loc[tr, feats].std().replace(0, 1)
        Xtr = ((D.loc[tr, feats] - mu) / sd).values; ytr = D.loc[tr, "y"].values
        Xa = np.column_stack([np.ones(len(Xtr)), Xtr]); I = np.eye(Xa.shape[1]); I[0, 0] = 0
        b = np.linalg.solve(Xa.T @ Xa + 1.0 * I, Xa.T @ ytr)
        coefs[Y] = dict(zip(["const"] + feats, b))
        ptr = Xa @ b
        share = D.loc[tr, "box"].mean()
        thr = np.quantile(ptr, 1 - share)
        Xte = np.column_stack([np.ones(te.sum()), ((D.loc[te, feats] - mu) / sd).values])
        D.loc[te, "pred"] = Xte @ b
        D.loc[te, "sel"] = D.loc[te, "pred"] >= thr
    oos = D[D.pred.notna()]
    sc = arm_table(list(zip(oos[oos.sel].i, oos[oos.sel].j)), R, ctl, idx)
    bx = arm_table(list(zip(oos[oos.box].i, oos[oos.box].j)), R, ctl, idx)
    out.append(f"\n== T2: walk-forward ridge SCORE vs the tier BOX (OOS 2012-2026; pool {len(oos):,}) ==")
    out.append(pd.DataFrame({"SCORE": month_stats(sc, SPLIT2), "BOX": month_stats(bx, SPLIT2)}).T.round(3).to_string())
    ms = sc.groupby(sc.date.dt.to_period("M")).ex.mean(); mb = bx.groupby(bx.date.dt.to_period("M")).ex.mean()
    d = (ms - mb).dropna(); h = d.index < pd.Period(SPLIT2, "M")
    t = d.mean() / d.std(ddof=1) * sqrt(len(d))
    ok = d.mean() > 0 and t >= 3 and d[h].mean() > 0 and d[~h].mean() > 0
    out.append(f"PRIMARY SCORE - BOX monthly excess: {d.mean():+.3f}R t {t:+.2f} ({len(d)} months), halves {d[h].mean():+.3f}/{d[~h].mean():+.3f} "
               f"-> {'SCORE BEATS BOX' if ok else 'FAIL'}")
    rc = oos[["pred", "R"]].corr(method="spearman").iloc[0, 1]
    out.append(f"OOS rank corr(pred, realised R) over the pool: {rc:+.3f}; SCORE/BOX overlap {len(set(zip(oos[oos.sel].i, oos[oos.sel].j)) & set(zip(oos[oos.box].i, oos[oos.box].j)))} "
               f"of {int(oos.sel.sum())} / {int(oos.box.sum())}")
    out.append("coefficients (standardised) by fit year:\n" + pd.DataFrame(coefs).T.round(3).to_string())
    print("\n".join(out))


if __name__ == "__main__":
    main()

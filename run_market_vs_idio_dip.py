#!/usr/bin/env python3
"""
Market-driven vs stock-specific dips in uptrend names (pre-registered 2026-09-28, before any run).

WHY. Gabe 2026-09-28: "a lot of times it's just down on market over-reaction". The ladder (2026-09-25) found that
uptrend names which dipped >= 1 ADR beat same-date non-dippers by +0.7..+1.4pp/20d (t 2.5-5.5), PARKED on
survivorship; the survivorship-free re-spec flipped sign. Nobody has split the dip by its CAUSE. A dip the market
explains (beta x the market's fall) should revert with the market's noise; a dip on the stock's own news may carry
information (and pooling both could be why the pooled effect is fragile).

PRE-REGISTRATION (frozen before the first run; nothing below changed after it)
  Population  P2: close > 50 SMA > 200 SMA and ADR >= 3%, eligible -- measured at t-10 (before the dip starts), so
              the dip itself cannot remove a name from the population.
  Dip event   drawdown from the highest close of the last 10 sessions >= 1.5 ADR at the close of t, first crossing
              (the prior close was < 1.5 ADR down). Peak p = the session of that 10-day high close.
  Beta        252-session OLS beta of daily returns on SPY, ending at p-1 (known before the dip).
  Split       over p -> t: stock return r_s (negative); market part = beta x SPY return over p -> t.
              MKT share = market part / r_s.   MKT arm: share >= 2/3.   IDIO arm: share <= 1/3 (incl. market up).
              MID: in between (reported, not tested).
  Outcome     entry at the close of t, forward 20-session close-to-close return (costs cancel in the contrast).
  Control     same-date P2 names NOT in a pullback (drawdown from the 10-day high close < 0.5 ADR), in the same
              ADR tercile x beta tercile cell (terciles over that date's P2 names). Beta is matched because a
              market-driven dip is by construction a high-beta name on a market-down day.
  Statistic   event-weighted mean excess, standard error clustered by calendar month (events cluster on market-down
              days; month clustering absorbs that). Split 2018-01-01; per-year table.
  PRIMARY     MKT arm, 20d excess, on liquid_panel_2009 (OHLC ADR). Bar: |t| >= 3, both halves the same sign,
              majority of years positive.
  Secondary   (a) IDIO arm; (b) MKT - IDIO (difference of the two arms' monthly means, months with both);
              (c) RESIDUAL outcome: fwd return minus beta x SPY fwd return (does the stock rebound beyond the
              market's own rebound?); (d) 5d and 60d horizons.
  Survivorship  the same engine on silver.chain_spot_daily (closes only, incl. delisted; ADR proxy = k x mean
              |return|, k fitted on the panel as in run_dip_survivorship.py; liquidity = 50d option volume >= 1,000,
              px >= $5; 2010 -> 2026-01). METHOD CHECK first: the panel run with the SAME close-only ADR proxy must
              give the primary the same sign as the OHLC run, and chain-spot SURV must give the same sign as the
              panel close-only run; if either check fails the survivorship read is uninterpretable (as on 9/25).
              READ: MKT effect SURVIVES if ALL passes |t| >= 3 AND NONSURV > 0; ARTEFACT if NONSURV <= 0 or ALL
              < half of SURV; else stays PARKED.
  Caveat      the market part is a one-factor split; sector moves count as "idiosyncratic" here.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_market_vs_idio_dip.py > data/studies/logs/market_vs_idio_dip.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
SPLIT = pd.Timestamp("2018-01-01")
START = pd.Timestamp("2010-06-01")
DD, CLEAN, H = 1.5, 0.5, 20
ETF = {"SPY", "QQQ", "IWM", "RSP", "DIA"}


def beta_frame(R: pd.DataFrame, m: pd.Series, n=252) -> pd.DataFrame:
    mm = m.reindex(R.index)
    ex = R.mul(mm, axis=0).rolling(n, min_periods=180).mean()
    er = R.rolling(n, min_periods=180).mean()
    em = mm.rolling(n, min_periods=180).mean()
    vm = mm.rolling(n, min_periods=180).var(ddof=0)
    return (ex - er.mul(em, axis=0)).div(vm, axis=0)


def engine(C: pd.DataFrame, adr: pd.DataFrame, elig: pd.DataFrame, spy: pd.Series, end=None) -> pd.DataFrame:
    """returns one row per dip event with arm, excess (raw and residual) at 5/20/60."""
    spy = spy.reindex(C.index)
    R = C.pct_change(fill_method=None)
    B = beta_frame(R, spy.pct_change(fill_method=None))
    s50, s200 = C.rolling(50, min_periods=40).mean(), C.rolling(200, min_periods=160).mean()
    P2 = (elig & (C > s50) & (s50 > s200) & (adr >= 3)).shift(10).fillna(False).astype(bool)
    hi10 = C.rolling(10, min_periods=10).max()
    dd = (1 - C / hi10) * 100 / adr
    ev_mask = P2 & (dd >= DD) & (dd.shift(1) < DD)
    clean = P2 & (dd < CLEAN)
    ev_mask[ev_mask.index < START] = False; clean[clean.index < START] = False
    if end is not None:
        ev_mask[ev_mask.index > end] = False
    Cv, Bv, Sv, Av = C.values, B.values, spy.values, adr.values
    fwd = {h: (C.shift(-h) / C - 1) for h in (5, 20, 60)}
    mfwd = {h: (spy.shift(-h) / spy - 1) for h in (5, 20, 60)}
    n = len(C)
    rows = []
    ii, jj = np.where(ev_mask.values)
    for i, j in zip(ii, jj):
        if i < 11:
            continue
        w = Cv[i - 9:i + 1, j]
        if not np.isfinite(w).all():
            continue
        p = i - 9 + int(np.argmax(w))
        if p >= i or p < 1:
            continue
        b = Bv[p - 1, j]
        if not np.isfinite(b):
            continue
        rs = Cv[i, j] / Cv[p, j] - 1
        rm = Sv[i] / Sv[p] - 1
        if not (np.isfinite(rs) and np.isfinite(rm)) or rs >= 0:
            continue
        share = b * rm / rs
        arm = "MKT" if share >= 2 / 3 else ("IDIO" if share <= 1 / 3 else "MID")
        rows.append(dict(i=i, j=j, date=C.index[i], sym=C.columns[j], arm=arm, share=share, beta=b, rs=rs, rm=rm))
    E = pd.DataFrame(rows)
    if E.empty:
        return E
    # same-date control cells: ADR tercile x beta tercile over that date's P2 names (beta as of the date)
    Bnow = B.shift(1)
    for h in (5, 20, 60):
        E[f"f{h}"] = fwd[h].values[E.i, E.j]
        E[f"r{h}"] = E[f"f{h}"] - E.beta * mfwd[h].values[E.i]
    out = []
    for d, g in E.groupby("date"):
        pop = P2.loc[d]
        names = pop.index[pop.values]
        a = adr.loc[d, names]; bb = Bnow.loc[d, names]
        ok = a.notna() & bb.notna()
        a, bb = a[ok], bb[ok]
        if len(a) < 30:
            continue
        ta = pd.qcut(a.rank(method="first"), 3, labels=False)
        tb = pd.qcut(bb.rank(method="first"), 3, labels=False)
        cl = clean.loc[d, a.index]
        ctrl = pd.DataFrame(dict(ta=ta, tb=tb, c=cl, beta=bb))
        for h in (5, 20, 60):
            ctrl[f"f{h}"] = fwd[h].loc[d, a.index]
            ctrl[f"r{h}"] = ctrl[f"f{h}"] - ctrl.beta * mfwd[h].loc[d]
        cc = ctrl[ctrl.c]
        cm = cc.groupby(["ta", "tb"])[[f"f{h}" for h in (5, 20, 60)] + [f"r{h}" for h in (5, 20, 60)]].mean()
        for r in g.itertuples():
            if r.sym not in ta.index:
                continue
            key = (ta[r.sym], tb[r.sym])
            if key not in cm.index:
                continue
            row = dict(date=d, sym=r.sym, arm=r.arm, share=r.share, beta=r.beta)
            for h in (5, 20, 60):
                row[f"x{h}"] = getattr(r, f"f{h}") - cm.loc[key, f"f{h}"]
                row[f"xr{h}"] = getattr(r, f"r{h}") - cm.loc[key, f"r{h}"]
            out.append(row)
    return pd.DataFrame(out)


def clus(x: pd.Series, dates: pd.Series):
    """event-weighted mean with month-clustered SE -> (mean pp, t, n, months)."""
    d = pd.DataFrame(dict(x=x.values, m=pd.to_datetime(dates.values).to_period("M"))).dropna()
    if len(d) < 10:
        return np.nan, np.nan, len(d), 0
    mu = d.x.mean()
    g = d.groupby("m").x
    s, n = g.sum(), g.size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return 100 * mu, mu / se if se > 0 else np.nan, len(d), g.ngroups


def table(X: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for arm in ("MKT", "IDIO", "MID"):
        a = X[X.arm == arm]
        for col in ("x20", "xr20", "x5", "x60"):
            mu, t, n, mo = clus(a[col], a.date)
            h1 = a[a.date < SPLIT]; h2 = a[a.date >= SPLIT]
            rows.append(dict(run=label, arm=arm, outcome=col, n=n, months=mo, excess_pp=mu, t=t,
                             h1_pp=100 * h1[col].mean(), h2_pp=100 * h2[col].mean()))
    # MKT - IDIO, monthly means, months with both
    mo = X.assign(m=X.date.dt.to_period("M")).groupby(["m", "arm"]).x20.mean().unstack()
    if {"MKT", "IDIO"} <= set(mo.columns):
        dfm = (mo["MKT"] - mo["IDIO"]).dropna()
        t = dfm.mean() / (dfm.std(ddof=1) / np.sqrt(len(dfm)))
        rows.append(dict(run=label, arm="MKT-IDIO", outcome="x20", n=len(dfm), months=len(dfm), excess_pp=100 * dfm.mean(),
                         t=t, h1_pp=100 * dfm[dfm.index.to_timestamp() < SPLIT].mean(),
                         h2_pp=100 * dfm[dfm.index.to_timestamp() >= SPLIT].mean()))
    return pd.DataFrame(rows)


def main():
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    p = Panel.from_long(raw)
    spy = p.close["SPY"]
    keep = [c for c in p.close.columns if c not in ETF]
    C, Hh, Ll = p.close[keep], p.high[keep], p.low[keep]
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect())[keep].fillna(False)
    adr = (Hh / Ll - 1).shift(1).rolling(20).mean() * 100
    import run_dip_survivorship as ds
    k = ds.k_scale()
    adrp = C.pct_change(fill_method=None).abs().shift(1).rolling(20, min_periods=15).mean() * k * 100
    print(f"panel {C.shape} {C.index.min().date()} -> {C.index.max().date()} | close-only ADR scale k = {k:.3f}")

    XA = engine(C, adr, elig, spy)
    print(f"\n[A] panel, OHLC ADR: {len(XA):,} matched dip events, arms {XA.arm.value_counts().to_dict()}")
    TA = table(XA, "A panel OHLC")
    XB = engine(C, adrp, elig, spy)
    TB = table(XB, "B panel close-only")

    d = ds.pull()
    Cs, Vs = ds.adjust_and_clean(d)
    spy_s = Cs["SPY"] if "SPY" in Cs.columns else spy
    surv = set(keep)
    liq = (Vs.rolling(50, min_periods=30).mean() >= ds.OPTVOL_MIN) & (Cs >= ds.PX_MIN)
    cols = [c for c in Cs.columns if c not in ETF]
    Cs, liq = Cs[cols], liq[cols]
    adrs = Cs.pct_change(fill_method=None).abs().shift(1).rolling(20, min_periods=15).mean() * k * 100
    XS = engine(Cs, adrs, liq.fillna(False), spy_s, end=pd.Timestamp(ds.END))
    XS["grp"] = np.where(XS.sym.isin(surv), "SURV", "NONSURV")
    TS = pd.concat([table(XS, "C chain ALL"), table(XS[XS.grp == "SURV"], "C chain SURV"),
                    table(XS[XS.grp == "NONSURV"], "C chain NONSURV")])
    T = pd.concat([TA, TB, TS])
    print("\n" + T.round(3).to_string(index=False))

    a = XA[XA.arm == "MKT"]
    yr = a.groupby(a.date.dt.year).x20.agg(["mean", "size"]); yr["mean"] *= 100
    print("\n[A] PRIMARY MKT x20 per year (pp, events):"); print(yr.round(2).T.to_string())
    pr = TA[(TA.arm == "MKT") & (TA.outcome == "x20")].iloc[0]
    maj = (yr["mean"] > 0).mean() > 0.5
    ok = abs(pr.t) >= 3 and np.sign(pr.h1_pp) == np.sign(pr.h2_pp) == np.sign(pr.t) and maj
    print(f"\nPRE-REGISTERED BAR (primary, A MKT x20): {'PASS' if ok else 'FAIL'}  (majority of years positive: {maj})")
    g = lambda TT, run: TT[(TT.run == run) & (TT.arm == "MKT") & (TT.outcome == "x20")].iloc[0]
    b, sv, al, ns = g(TB, "B panel close-only"), g(TS, "C chain SURV"), g(TS, "C chain ALL"), g(TS, "C chain NONSURV")
    m1 = np.sign(b.excess_pp) == np.sign(pr.excess_pp); m2 = np.sign(sv.excess_pp) == np.sign(b.excess_pp)
    print(f"METHOD CHECK: close-only panel same sign as OHLC: {m1} | chain SURV same sign as close-only panel: {m2}")
    if m1 and m2:
        if abs(al.t) >= 3 and ns.excess_pp > 0:
            v = "SURVIVES survivorship"
        elif ns.excess_pp <= 0 or al.excess_pp < sv.excess_pp / 2:
            v = "SURVIVORSHIP ARTEFACT"
        else:
            v = "in between -> PARKED"
    else:
        v = "UNINTERPRETABLE (method check failed)"
    print(f"SURVIVORSHIP READ (MKT x20): SURV {sv.excess_pp:+.2f} / ALL {al.excess_pp:+.2f} (t {al.t:+.2f}) / NONSURV {ns.excess_pp:+.2f} -> {v}")
    XA.to_csv("data/studies/logs/market_vs_idio_dip_events_panel.csv", index=False)
    T.to_csv("data/studies/market_vs_idio_dip_2026-09-28.csv", index=False)


if __name__ == "__main__":
    main()

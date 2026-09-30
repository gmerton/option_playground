#!/usr/bin/env python3
"""
Audit List A #9: the single-name SHORT family on the survivorship-free series (pre-registered 2026-09-30, committed
BEFORE the run). The mirror-breakdown half ran 9/29 (INVERTED, t -7.02 as a short). This runs the other two members:
the follow-on OFFERING short (9/25: -0.21pp t -1.23 at +20, -0.67pp t -1.85 at +60) and CRASH-H (9/23: -0.96pp t -1.28).

WHY. All three ran on liquid_panel_2009 = names liquid in 2026. Delisted / failed names -- a short's best outcomes --
are absent, so the panel is biased AGAINST shorts. chain_spot_daily (parity closes, ~10.8k optionable tickers incl.
delisted, 2010 -> 2026-02) is the only series that includes them. Gabe 2026-09-30: "yes" (run #9).

DATA  run_dip_survivorship.pull() + adjust_and_clean() (split-adjusted closes, unexplained +/-45% jumps cut the series).
      Closes only. Groups: SURV = tickers in liquid_panel_2009, NONSURV = the rest, ALL = both.
      Eligible (as in the parent): 50-session mean option volume >= 1,000 and close >= $5.
      ADRp = 20-session mean |close-to-close return| x k (k = run_dip_survivorship.k_scale()).
      A series that ENDS inside the window exits at its last close. ⚠ For a bankruptcy the last exchange close is above
      the eventual OTC value, so a short's best outcome is still UNDERSTATED here -- noted, not fixable with this data.

A. OFFERING SHORT (events = the 9/25 EDGAR full-text cache, data/cache/offerings/offering_filings.parquet, ATM excluded,
   primary-issuer + secondary; CIK -> ticker via the Polygon master incl. delisted, NOT restricted to the panel).
   Dedupe: first filing per name in any 20-session window. Entry: SHORT at the close of the session AFTER the file date
   (no opens in this series; the parent used the next open). Exit: close at +20 (PRIMARY) and +60.
   Control: same-date eligible non-event names in the same prior-5-session-return quintile x ADRp tercile (parent's).
B. CRASH-H (state, not event): close <= 0.60 x the 252-session high CLOSE while SPY > a rising 200 SMA (SPY 200 SMA
   above its value 20 sessions earlier). Sampled on the LAST trading day of each month (one observation per name-month,
   as the universe test did). Entry = that close; exit = close +20. Control: same-date eligible names in the same ADRp
   tercile (ADR-matched, as the parent), not in the state.
COSTS  10 bp a side + 1%/yr borrow (the parent's); also reported with 10%/yr (crashed names are often hard to borrow).
PRIMARY CELLS (2): A ALL +20 and B ALL +20.  Sidak(2) |t| >= 2.24; the house |t| >= 3 GOVERNS.
BAR (unchanged from the parents): a cell PASSES as a SHORT only if ALL of: excess < 0 with |t| >= 3 (month-clustered);
     both halves (split 2018-01) negative; a majority of years negative; ABSOLUTE short P&L after costs + borrow > 0.
     Excess criteria met without the absolute = long-book VETO candidate, not a short.
READ (declared now): the survivorship effect = ALL minus SURV on the same rule. If ALL passes where SURV did not, the
     ledger's short nulls were a survivorship artefact; if ALL ~ SURV, they were not.
Secondary (no verdict): A at +60, A PRIMARY-ISSUER only, B with 10%/yr borrow, NONSURV alone.
Local, cached; minutes.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_short_family_survivorship.py  (log -> data/studies/logs/short_family_survivorship.log)
"""
from __future__ import annotations

import sys
from math import sqrt

import numpy as np
import pandas as pd

import run_dip_survivorship as ds

REPO = ds.REPO
LOG = REPO / "data/studies/logs/short_family_survivorship.log"
START, END, SPLIT, COST, BORROW = "2010-06-01", "2025-11-15", "2018-01-01", 0.0010, 0.01


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def fwd(Cv, last, i0, j, h):
    """close-to-close return from row i0 to i0+h, exiting at the series' last close if it ends first."""
    n = len(Cv)
    e = Cv[i0, j]
    if not np.isfinite(e):
        return np.nan
    i1 = min(i0 + h, n - 1, last[j])
    if i1 <= i0:
        return np.nan
    seg = Cv[i0 + 1:i1 + 1, j]
    seg = seg[np.isfinite(seg)]
    return seg[-1] / e - 1 if len(seg) else np.nan


def report(T, h, label, borrow=BORROW):
    T = T.dropna(subset=["ret", "ctl"])
    if len(T) < 30:
        return dict(label=label, n=len(T))
    x = 100 * (T.ret - T.ctl)
    mo = x.groupby(T.date.dt.to_period("M")).mean()
    hh = mo.index < pd.Period(SPLIT, "M")
    yr = x.groupby(T.date.dt.year).mean()
    sp = -100 * T.ret - 100 * (2 * COST + borrow * h / 252)
    r = dict(label=label, h=h, n=len(T), names=T.sym.nunique(), fwd=100 * T.ret.mean(), ctl=100 * T.ctl.mean(),
             excess=mo.mean(), t=tstat(mo), h1=mo[hh].mean(), h2=mo[~hh].mean(),
             yrs_neg=f"{int((yr < 0).sum())}/{len(yr)}", short_pnl=sp.mean(),
             t_short=tstat(sp.groupby(T.date.dt.to_period("M")).mean()))
    core = r["excess"] < 0 and r["t"] <= -3 and r["h1"] < 0 and r["h2"] < 0 and (yr < 0).mean() > .5
    r["verdict"] = "PASS" if core and r["short_pnl"] > 0 else ("VETO-candidate" if core else "fail")
    return r


def main():
    C, V = ds.adjust_and_clean(ds.pull())
    k = ds.k_scale()
    surv = set(pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["ticker"]).ticker.unique())
    idx, cols = C.index, np.array(C.columns)
    col = {c: j for j, c in enumerate(cols)}
    Cv = C.values
    n = len(Cv)
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                     for j in range(Cv.shape[1])])
    ret = C.pct_change(fill_method=None)
    adrp = (ret.abs().shift(1).rolling(20, min_periods=15).mean() * k * 100).values
    elig = ((V.rolling(50, min_periods=30).mean() >= 1000) & (C >= 5)).fillna(False).values
    r5 = (C / C.shift(5) - 1).values
    is_surv = np.isin(cols, list(surv))
    out = []

    # ---------------- A. offering short ----------------
    D = pd.read_parquet(REPO / "data/cache/offerings/offering_filings.parquet")
    atm = set(D[D.kind == "atm"].acc)
    D = D[(D.kind != "atm") & ~D.acc.isin(atm)].copy()
    D["cik"] = D.ciks.str.split(",").str[0]
    tk = pd.read_parquet(REPO / "data/cache/pit/tickers.parquet")[["ticker", "cik"]].dropna()
    tk = tk[tk.ticker.isin(col)].drop_duplicates("cik")
    D = D.merge(tk, on="cik", how="inner")
    D["prio"] = (D.kind == "primary").astype(int)
    D = D.sort_values("prio", ascending=False).drop_duplicates("acc")
    D["file_date"] = pd.to_datetime(D.file_date)
    D = D[(D.file_date >= START) & (D.file_date <= END)].sort_values(["ticker", "file_date"])
    D["i"] = idx.searchsorted(D.file_date.values)
    keep, lastpos = [], {}
    for r in D.itertuples():                                    # first filing per name in any 20-session window
        if r.ticker in lastpos and r.i - lastpos[r.ticker] < 20:
            continue
        lastpos[r.ticker] = r.i
        keep.append(r)
    E = pd.DataFrame(keep)
    ev = np.zeros(Cv.shape, bool)
    for r in E.itertuples():
        if r.i < n:
            ev[r.i, col[r.ticker]] = True
    rowsA = {20: [], 60: []}
    cache = {}
    for r in E.itertuples():
        i, j = r.i, col[r.ticker]
        if i + 1 >= n or not elig[i, j]:
            continue
        if i not in cache:
            ok = elig[i] & np.isfinite(r5[i]) & np.isfinite(adrp[i]) & np.isfinite(Cv[i + 1])
            if ok.sum() < 100:
                cache[i] = None
            else:
                rq = pd.qcut(pd.Series(r5[i, ok]), 5, labels=False, duplicates="drop").values
                aq = pd.qcut(pd.Series(adrp[i, ok]), 3, labels=False, duplicates="drop").values
                cell = np.full(Cv.shape[1], -1); cell[ok] = rq * 3 + aq
                cache[i] = (cell, ok)
        if cache[i] is None or cache[i][0][j] < 0:
            continue
        cell, ok = cache[i]
        for h in (20, 60):
            peers = np.flatnonzero(ok & ~ev[i] & (cell == cell[j]))
            ctl = np.nanmean([fwd(Cv, last, i + 1, p, h) for p in peers]) if len(peers) else np.nan
            rowsA[h].append(dict(date=idx[i], sym=r.ticker, kind=r.kind, surv=bool(is_surv[j]),
                                 ret=fwd(Cv, last, i + 1, j, h), ctl=ctl))
    A20, A60 = pd.DataFrame(rowsA[20]), pd.DataFrame(rowsA[60])
    out += [report(A20, 20, "A offering ALL +20 (PRIMARY)"), report(A20[A20.surv], 20, "A offering SURV +20"),
            report(A20[~A20.surv], 20, "A offering NONSURV +20"), report(A60, 60, "A offering ALL +60"),
            report(A20[A20.kind == "primary"], 20, "A offering PRIMARY-ISSUER ALL +20")]

    # ---------------- B. CRASH-H ----------------
    spy = C["SPY"]
    s200 = spy.rolling(200).mean()
    healthy = ((spy > s200) & (s200 > s200.shift(20))).reindex(idx).fillna(False).values
    hi252 = C.rolling(252, min_periods=200).max().values
    me = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    rowsB = []
    for d in me[(me >= START) & (me <= END)]:
        i = idx.get_loc(d)
        if not healthy[i] or i + 1 >= n:
            continue
        ok = elig[i] & np.isfinite(adrp[i]) & np.isfinite(Cv[i])
        state = ok & (Cv[i] <= 0.60 * hi252[i])
        if state.sum() == 0 or ok.sum() < 100:
            continue
        aq = np.full(Cv.shape[1], -1)
        aq[ok] = pd.qcut(pd.Series(adrp[i, ok]), 3, labels=False, duplicates="drop").values
        fr = np.array([fwd(Cv, last, i, j, 20) if ok[j] else np.nan for j in range(Cv.shape[1])])
        ctl = pd.Series(fr[ok & ~state]).groupby(aq[ok & ~state]).mean()
        for j in np.flatnonzero(state):
            if aq[j] in ctl.index:
                rowsB.append(dict(date=d, sym=cols[j], surv=bool(is_surv[j]), ret=fr[j], ctl=ctl[aq[j]]))
    B = pd.DataFrame(rowsB)
    out += [report(B, 20, "B CRASH-H ALL +20 (PRIMARY)"), report(B[B.surv], 20, "B CRASH-H SURV +20"),
            report(B[~B.surv], 20, "B CRASH-H NONSURV +20"), report(B, 20, "B CRASH-H ALL +20, 10%/yr borrow", 0.10)]

    R = pd.DataFrame(out)
    pd.set_option("display.width", 250)
    print(f"# Audit #9 short family on chain_spot (pre-registration in the docstring); k {k:.3f}; "
          f"offering events kept {len(E):,}")
    print(R.round(2).to_string(index=False))
    for lab in ("A offering ALL +20 (PRIMARY)", "B CRASH-H ALL +20 (PRIMARY)"):
        print(f"{lab}: {R.set_index('label').loc[lab, 'verdict']}")
    A20.to_csv(REPO / "data/studies/logs/short_family_offering_trades.csv", index=False)
    B.to_csv(REPO / "data/studies/logs/short_family_crashh_obs.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

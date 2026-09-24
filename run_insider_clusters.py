#!/usr/bin/env python3
"""
Undervalued idea #2: insider CLUSTER buying (pre-registered 2026-09-24, before the first run; Gabe's undervalued
brainstorm). First insider test in the ledger. Data: run_sec_insider_pull.py -> data/cache/insider_purchases.parquet
(SEC Form 4 open-market purchases, code P, point-in-time on the FILING date).

DESIGN
  universe  liquid_panel_2009 eligible names (ADDV >= $50M, px >= $5), 2010 ->. ⚠ Insider buying is concentrated in
            small caps; this tests it where we can actually trade it.
  purchase  a Form 4 open-market purchase line with value >= $10,000.
  CLUSTER   >= 3 DISTINCT insiders (owner CIK) with purchase filings inside a trailing 30-calendar-day window; the event
            is the filing date that brings the count to 3. One event per ticker per 60 sessions.
  SINGLE    (control) a purchase filing with NO other insider purchase filed in the ticker within +/- 60 days.
  entry     the CLOSE of the first session AFTER the event filing date (Form 4s are often filed after the close).
  outcome   forward 20 / 60 / 120-session return minus the same-date mean of eligible names in the same ADR band
            (<2, 2-3, 3-4, 4-6, 6+). No stop.
  PRIMARY   CLUSTER 60-session ADR-matched excess, t clustered by entry date; bar t >= 3, both halves (2018-01) > 0,
            and CLUSTER > SINGLE (difference t reported).
  SECONDARY (exploratory) 20 / 120 sessions; cluster in a BEATEN-DOWN name (close <= 0.70 x 252d high -- the
            "undervalued" core); officer-led clusters (any buyer titled CEO/CFO/President/Chair); large clusters
            (total value >= $1M); per year.
  caveat    survivor panel flatters the beaten-down cell; 10% owners are included as insiders (they file Form 4).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_insider_clusters.py   (log -> data/studies/logs/insider_clusters.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/insider_clusters.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")


def tstat_by(x: pd.Series, g: pd.Series) -> float:
    m = pd.Series(np.asarray(x), index=np.asarray(g)).groupby(level=0).mean()
    return float(m.mean() / m.std(ddof=1) * sqrt(len(m))) if len(m) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, H, A, E = P.close.loc[keep], P.high.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    F = {h: ((C.shift(-h) / C - 1) * 100) for h in (20, 60, 120)}
    bench = {}
    Av, Ev = A.values, E.values
    for h, Fh in F.items():
        b = np.full(Fh.shape, np.nan); Fv = Fh.values
        for lo, hi in BANDS:
            mk = Ev & (Av >= lo) & (Av < hi) & np.isfinite(Fv)
            s = np.where(mk, Fv, 0).sum(axis=1); c = mk.sum(axis=1)
            m = np.where(c >= 10, s / np.maximum(c, 1), np.nan)
            b = np.where((Av >= lo) & (Av < hi), m[:, None], b)
        bench[h] = b
    col = {t: k for k, t in enumerate(C.columns)}

    ip = pd.read_parquet(REPO / "data/cache/insider_purchases.parquet")
    ip = ip[(ip.value >= 10_000) & ip.ticker.isin(col) & ip.filing_date.notna() & (ip.filing_date >= "2010-01-01")]
    ip["officer"] = ip.rptowner_title.fillna("").str.contains(r"CEO|Chief Exec|CFO|Chief Fin|President|Chair", case=False)
    # one row per (ticker, filing_date, owner)
    f = (ip.groupby(["ticker", "filing_date", "rptownercik"])
           .agg(value=("value", "sum"), officer=("officer", "max")).reset_index().sort_values(["ticker", "filing_date"]))

    def score(ticker, d_file, kind, extra):
        j = col[ticker]
        i = idx.searchsorted(d_file, side="right")          # first session AFTER the filing date
        if i >= len(idx) - 20 or not Ev[i, j]:
            return None
        rec = dict(kind=kind, ticker=ticker, date=idx[i], beaten=bool(C.values[i, j] <= 0.70 * hi252.values[i, j]), **extra)
        for h in (20, 60, 120):
            rec[f"ex{h}"] = F[h].values[i, j] - bench[h][i, j] if i + h < len(idx) else np.nan
        return rec

    rows = []
    for t, g in f.groupby("ticker"):
        dates = g.filing_date.values
        last_i = -10 ** 9
        for k in range(len(g)):
            d = g.filing_date.iloc[k]
            w = g[(g.filing_date > d - pd.Timedelta(days=30)) & (g.filing_date <= d)]
            if w.rptownercik.nunique() >= 3 and (g.iloc[:k].pipe(lambda x: x[x.filing_date > d - pd.Timedelta(days=30)]).rptownercik.nunique() < 3):
                i = idx.searchsorted(d, side="right")
                if i - last_i < 60:
                    continue
                r = score(t, d, "CLUSTER", dict(n_buyers=w.rptownercik.nunique(), value=w.value.sum(), officer=bool(w.officer.any())))
                if r:
                    rows.append(r); last_i = i
        # singles: an owner-filing with no other insider purchase filing within +/- 60 days
        for k in range(len(g)):
            d = g.filing_date.iloc[k]
            near = g[(g.filing_date >= d - pd.Timedelta(days=60)) & (g.filing_date <= d + pd.Timedelta(days=60))]
            if near.rptownercik.nunique() == 1 and len(near.filing_date.unique()) == 1:
                r = score(t, d, "SINGLE", dict(n_buyers=1, value=g.value.iloc[k], officer=bool(g.officer.iloc[k])))
                if r:
                    rows.append(r)
    R = pd.DataFrame(rows).dropna(subset=["ex60"])
    Cl, Si = R[R.kind == "CLUSTER"], R[R.kind == "SINGLE"]

    out = []; pr = out.append
    pr("# Undervalued #2: insider cluster buying (pre-registration in the docstring)\n")
    pr(f"purchase lines used {len(ip):,}; events: CLUSTER {len(Cl):,} ({Cl.ticker.nunique()} names) | SINGLE {len(Si):,}\n")
    pr(f"{'cell':32s} {'n':>6s} {'ex20':>7s} {'ex60':>7s} {'t60':>6s} {'ex120':>7s} {'%+60':>5s}")
    cells = [("CLUSTER", Cl), ("SINGLE", Si), ("CLUSTER, beaten-down", Cl[Cl.beaten]), ("CLUSTER, not beaten", Cl[~Cl.beaten]),
             ("CLUSTER, officer-led", Cl[Cl.officer]), ("CLUSTER, total >= $1M", Cl[Cl.value >= 1e6]),
             ("SINGLE, beaten-down", Si[Si.beaten])]
    for lab, X in cells:
        pr(f"{lab:32s} {len(X):>6,} {X.ex20.mean():>+7.2f} {X.ex60.mean():>+7.2f} {tstat_by(X.ex60, X.date):>6.2f} "
           f"{X.ex120.mean():>+7.2f} {100 * (X.ex60 > 0).mean():>5.0f}")
    t = tstat_by(Cl.ex60, Cl.date)
    h1, h2 = Cl[Cl.date < SPLIT].ex60, Cl[Cl.date >= SPLIT].ex60
    a = Cl.groupby("date").ex60.mean(); b = Si.groupby("date").ex60.mean()
    dcs = a.mean() - b.mean(); tcs = dcs / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    pr(f"\n## PRIMARY: CLUSTER 60d excess {Cl.ex60.mean():+.2f}pp (median {Cl.ex60.median():+.2f}), t {t:+.2f}; halves "
       f"{h1.mean():+.2f} (n {len(h1)}) / {h2.mean():+.2f} (n {len(h2)}); CLUSTER - SINGLE {dcs:+.2f}pp (t {tcs:+.2f})")
    ok = t >= 3 and h1.mean() > 0 and h2.mean() > 0 and dcs > 0
    pr(f"  bar (t >= 3, both halves > 0, CLUSTER > SINGLE): {'PASS' if ok else 'FAIL'}")
    pr("  CLUSTER per year ex60: " + "  ".join(f"{y} {v:+.1f}" for y, v in Cl.groupby(Cl.date.dt.year).ex60.mean().items()))
    R.to_csv(REPO / "data/studies/insider_clusters_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

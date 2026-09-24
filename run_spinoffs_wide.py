#!/usr/bin/env python3
"""
Spin-offs beyond the S&P 500 (pre-registered 2026-09-24, before the first run; TEST_INDEX §10 row queued the same day
from undervalued #5, where S&P 500 spincos showed +22.9pp at 120d, t 2.12, n 16).

EVENTS  SEC EDGAR quarterly form indexes 2009 -> 2026: every registrant filing a Form 10-12B (the exchange registration a
        spin-off uses) -> data/cache/edgar_form10_12b.csv (430 registrants). CIK -> ticker via the SEC Form 4 issuer data
        (data/cache/insider_purchases.parquet: issuercik + the ticker at filing time) and SEC company_tickers.json.
        A registrant counts as a SPIN-OFF only if its ticker's FIRST bar in liquid_panel_2009 falls between 30 days
        before and 540 days after its first 10-12B (newly listed, not an old company re-registering) and after
        2009-06 (so the panel start is not mistaken for a listing).
ENTRY   the close of the 20th session after the first bar (after the parent's holders dump the unwanted shares);
        requires the name to be eligible (ADDV >= $50M) on that day.
OUTCOME forward 60 / 120 / 250-session return minus (a) the same-date ADR-matched eligible field and (b) the same-date
        mean of eligible names in the same industry (data/ticker_industry_map.csv).
PRIMARY 120-session ADR-matched excess, t across events; bar t >= 3, both halves (2018-01) > 0. Report S&P-500 spincos
        vs the rest (does the #5 lead generalise?).
caveat  survivor panel: spincos that later failed or were acquired are missing -- this FLATTERS spin-offs, which the
        literature says have a fat left tail. A pass needs that read against it.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spinoffs_wide.py   (log -> data/studies/logs/spinoffs_wide.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/spinoffs_wide.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai"}


def t(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "dolvol"])
    DV = raw.pivot(index="date", columns="ticker", values="dolvol").sort_index()
    im = pd.read_csv(REPO / "data/ticker_industry_map.csv").set_index("ticker").industry
    F = {h: ((C.shift(-h) / C - 1) * 100) for h in (60, 120, 250)}
    Av, Ev = A.values, E.values
    bench = {}
    for h, Fh in F.items():
        b = np.full(Fh.shape, np.nan); Fv = Fh.values
        for lo, hi in BANDS:
            mk = Ev & (Av >= lo) & (Av < hi) & np.isfinite(Fv)
            s = np.where(mk, Fv, 0).sum(axis=1); c = mk.sum(axis=1)
            m = np.where(c >= 10, s / np.maximum(c, 1), np.nan)
            b = np.where((Av >= lo) & (Av < hi), m[:, None], b)
        bench[h] = b

    reg = pd.read_csv(REPO / "data/cache/edgar_form10_12b.csv", dtype={"cik": str}, parse_dates=["first_10_12b"])
    ip = pd.read_parquet(REPO / "data/cache/insider_purchases.parquet", columns=["issuercik", "ticker", "filing_date"])
    m1 = ip.dropna().sort_values("filing_date").groupby("issuercik").ticker.last()
    ct = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=60).json()
    m2 = pd.Series({str(v["cik_str"]).zfill(10): v["ticker"] for v in ct.values()})
    reg["ticker"] = reg.cik.map(m2).fillna(reg.cik.map(m1))
    first_bar = C.apply(lambda s: s.first_valid_index())
    sp500 = pd.read_csv(REPO / "data/cache/sp500_changes_wikipedia.csv", header=[0, 1])
    sp_spin = set(sp500.iloc[:, 1].dropna().astype(str))

    rows, skipped = [], {"no ticker": 0, "not in panel": 0, "not newly listed": 0, "not eligible at entry": 0}
    for r in reg.itertuples(index=False):
        tk = r.ticker
        if not isinstance(tk, str):
            skipped["no ticker"] += 1; continue
        if tk not in C.columns:
            skipped["not in panel"] += 1; continue
        fb = first_bar[tk]
        if fb is None or fb < pd.Timestamp("2009-06-01") or not (r.first_10_12b - pd.Timedelta(days=30) <= fb <= r.first_10_12b + pd.Timedelta(days=540)):
            skipped["not newly listed"] += 1; continue
        i = idx.get_loc(fb) + 20
        j = C.columns.get_loc(tk)
        # the panel's eligibility needs 30 sessions of ADDV history, which a 20-session-old spinco never has:
        # use its own first-20-session mean dollar volume instead (same $50M / $5 thresholds)
        dv20 = DV[tk].loc[fb:].iloc[:20].mean() if tk in DV else np.nan
        if i >= len(idx) or not (dv20 >= 50e6 and C.values[i, j] >= 5):
            skipped["not eligible at entry"] += 1; continue
        rec = dict(ticker=tk, company=r.company, filed=r.first_10_12b.date(), first=fb.date(), entry=idx[i],
                   sp500=tk in sp_spin, first20=100 * (C.values[i, j] / C.loc[fb, tk] - 1))
        g = im.get(tk)
        peers = [p for p in im[im == g].index if p in C.columns and p != tk] if g is not None else []
        for h in (60, 120, 250):
            if i + h >= len(idx):
                rec[f"ex{h}"] = rec[f"ind{h}"] = np.nan; continue
            rec[f"ex{h}"] = F[h].values[i, j] - bench[h][i, j]
            pf = F[h].iloc[i][peers][E.iloc[i][peers]] if peers else pd.Series(dtype=float)
            rec[f"ind{h}"] = F[h].values[i, j] - pf.mean() if pf.notna().sum() >= 4 else np.nan
        rows.append(rec)
    S = pd.DataFrame(rows)
    S.to_csv(REPO / "data/studies/spinoffs_wide_2026-09-24.csv", index=False)

    out = ["# Spin-offs beyond the S&P 500 (pre-registration in the docstring)\n",
           f"10-12B registrants {len(reg)}; screened out: {skipped}; SPIN-OFF events {len(S)} "
           f"({int(S.sp500.sum())} S&P 500 spincos, {int((~S.sp500).sum())} others), first bars {S['first'].min()} -> {S['first'].max()}",
           f"first 20 sessions (the dumping window): {S.first20.mean():+.2f}% raw (median {S.first20.median():+.2f})\n"]
    for lab, X in (("ALL", S), ("S&P 500 spincos", S[S.sp500]), ("others", S[~S.sp500])):
        out.append(f"{lab:16s} n {len(X):3d} | 60d {X.ex60.mean():+6.2f} (t {t(X.ex60):+.2f}) | 120d {X.ex120.mean():+6.2f} "
                   f"(t {t(X.ex120):+.2f}, n {X.ex120.notna().sum()}) | 250d {X.ex250.mean():+6.2f} (t {t(X.ex250):+.2f}) | "
                   f"120d vs industry {X.ind120.mean():+6.2f} (t {t(X.ind120):+.2f})")
    x = S.ex120.dropna(); e = pd.to_datetime(S.entry)
    h1, h2 = S.ex120[e < SPLIT].dropna(), S.ex120[e >= SPLIT].dropna()
    ok = t(x) >= 3 and h1.mean() > 0 and h2.mean() > 0
    out.append(f"\n## PRIMARY 120d ADR-matched excess, ALL: {x.mean():+.2f}pp (median {x.median():+.2f}), t {t(x):+.2f}, "
               f"{100 * (x > 0).mean():.0f}% +; halves {h1.mean():+.2f} (n {len(h1)}) / {h2.mean():+.2f} (n {len(h2)}) -> "
               f"{'PASS' if ok else 'FAIL'}")
    out.append("per entry year 120d: " + "  ".join(f"{y} {v:+.1f} (n {k})" for y, (v, k) in
               S.assign(y=e.dt.year).groupby("y").ex120.agg(["mean", "size"]).iterrows()))
    out.append("\nevents (120d excess): " + ", ".join(f"{r.ticker} {r.ex120:+.0f}" for r in S.sort_values("entry").itertuples()
                                                    if np.isfinite(r.ex120)))
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

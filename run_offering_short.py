#!/usr/bin/env python3
"""
Follow-on EQUITY OFFERINGS as a single-name SHORT (pre-registered 2026-09-25, before the first run; Gabe's #2 of
the "information, not chart pattern" short ideas).

WHY. Price-pattern shorts fail because weak names drift up and the breakdown event carries no information
(failed-retest test). An equity offering IS information: management and insiders sell stock when they think it is
richly priced (Loughran-Ritter 1995 "new issues puzzle": multi-year SEO underperformance; the short-run literature
finds an announcement drop and a partial rebound). The ledger's only offering idea (Veprek dilution fade, WL-5i) is
BLOCKED on small-cap data; this is the LIQUID-name version, which the panel can answer. NEW axis: no row in
TEST_INDEX uses offering filings.

DATA (new; cached under data/cache/offerings/)
  EDGAR full-text search (efts.sec.gov, 2001+), forms 424B4 / 424B5 / 424B7, per calendar quarter 2010Q1 -> 2026Q2:
    PRIMARY-ISSUER  "we are offering" AND "shares of our common stock"
    SECONDARY       "selling stockholders" | "selling stockholder" | "selling shareholders", each AND "shares of our common stock"
    ATM exclusion   any accession also matching "sales agent" (at-the-market programs dribble; no discrete event)
  CIK -> ticker via data/cache/pit/tickers.parquet (Polygon master incl. delisted) restricted to liquid-panel names.
  Event date = the 424B FILE date (the prospectus is filed at/after pricing, so the deal is public by then).

DESIGN
  panel     data/cache/liquid_panel_2009.parquet (adjusted), harness eligibility (ADDV >= $50M, px >= $5) on the
            event date. Events 2010-01 -> 2026-06 (60-session exits land by 2026-09).
  dedupe    first qualifying filing per name in any 20-session window (one deal = several 424Bs).
  trade     SHORT at the NEXT OPEN after the file date, cover at the close of session +h. Costs 10 bp/side +
            1.0%/yr borrow (post-deal borrow can be tighter; noted, not modelled).
  CONTROL   (declared now) same-date eligible non-event names in the same prior-5-session-return quintile x ADR
            tercile -- the 5-session window contains the announcement drop, so the control asks whether the
            OFFERING predicts beyond a same-sized drop.
  cells     {ALL (primary+secondary), PRIMARY-ISSUER only, SECONDARY only} x {+20 (PRIMARY), +60} = 6.
            PRIMARY CELL = ALL +20. Sidak(6) at 0.05 -> |t| >= 2.64; the house |t| >= 3 GOVERNS.
  t         clustered by event month.
  BAR       (declared now) a cell PASSES as a SHORT only if ALL of: (a) excess < 0 with |t| >= 3; (b) both halves
            (split 2018-01) negative; (c) ABSOLUTE short P&L after costs + borrow > 0; (d) negative excess in a
            majority of years. (a)+(b)+(d) without (c) = long-book VETO candidate, not a short.
  PRIOR     the announcement drop is mostly over by the file date; the likeliest outcome is a small negative excess
            with a positive absolute return (the short-universe pattern).
  EXPLORATORY  split by the prior 60-session run-up (>= +30% vs the rest: "issuer sells into strength", the liquid
            analogue of the Veprek setup) and by the file-day return (<= -3% vs the rest).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_offering_short.py [--pull-only]
       (log -> data/studies/logs/offering_short.log)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from lib.studies.pattern_test import load_panel, SLIP

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/offering_short.log"
CACHE = REPO / "data/cache/offerings"
PANEL = "data/cache/liquid_panel_2009.parquet"
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai"}
FORMS = "424B4,424B5,424B7"
QUERIES = {
    "primary": ['"we are offering" "shares of our common stock"'],
    "secondary": ['"selling stockholders" "shares of our common stock"', '"selling stockholder" "shares of our common stock"',
                  '"selling shareholders" "shares of our common stock"'],
    "atm": ['"sales agent"'],
}
START, END, SPLIT = "2010-01-01", "2026-06-30", "2018-01-01"
BORROW, HORIZONS = 0.01, (20, 60)
RNG = np.random.default_rng(20260925)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def efts(q: str, a: str, b: str) -> list[dict]:
    out, frm = [], 0
    while True:
        for attempt in range(5):
            try:
                r = requests.get("https://efts.sec.gov/LATEST/search-index",
                                 params={"q": q, "forms": FORMS, "dateRange": "custom", "startdt": a, "enddt": b, "from": frm},
                                 headers=UA, timeout=30)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"efts failed {q} {a} {frm}")
        h = r.json()["hits"]
        for x in h["hits"]:
            s = x["_source"]
            out.append(dict(acc=x["_id"].split(":")[0], form=s.get("form"), file_date=s.get("file_date"),
                            ciks=",".join(s.get("ciks") or [])))
        frm += len(h["hits"])
        time.sleep(0.15)
        if not h["hits"] or frm >= h["total"]["value"] or frm >= 9900:
            if frm >= 9900:
                print(f"  ⚠ 10k cap hit: {q} {a}", flush=True)
            return out


def pull() -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "offering_filings.parquet"
    if f.exists():
        return pd.read_parquet(f)
    rows = []
    for q0 in pd.period_range(START, END, freq="Q"):
        a, b = str(q0.start_time.date()), str(q0.end_time.date())
        for kind, qs in QUERIES.items():
            for q in qs:
                for r in efts(q, a, b):
                    r["kind"] = kind; rows.append(r)
        print(f"  {q0}: {len(rows):,} hits so far", flush=True)
    D = pd.DataFrame(rows)
    D.to_parquet(f, index=False)
    return D


def events(P) -> pd.DataFrame:
    D = pull()
    atm = set(D[D.kind == "atm"].acc)
    D = D[(D.kind != "atm") & ~D.acc.isin(atm)].copy()
    D["cik"] = D.ciks.str.split(",").str[0]
    tk = pd.read_parquet(REPO / "data/cache/pit/tickers.parquet")[["ticker", "cik"]].dropna()
    tk = tk[tk.ticker.isin(P.close.columns)].drop_duplicates("cik")
    D = D.merge(tk, on="cik", how="inner")
    # one row per accession: primary wins if it matched both phrase sets
    D["prio"] = (D.kind == "primary").astype(int)
    D = D.sort_values("prio", ascending=False).drop_duplicates("acc")
    D["file_date"] = pd.to_datetime(D.file_date)
    return D[["ticker", "file_date", "form", "kind", "acc"]].sort_values(["ticker", "file_date"])


def score(E, P, h):
    idx, cols = P.close.index, P.close.columns
    O, C = P.open.values, P.close.values
    col = {c: j for j, c in enumerate(cols)}
    r5 = (P.close / P.close.shift(5) - 1).values
    r60 = (P.close / P.close.shift(60) - 1).values
    r1 = (P.close / P.close.shift(1) - 1).values
    adr, elig = P.adr.values, P.elig.fillna(False).values
    ev = np.zeros(C.shape, bool)
    rows = []
    for e in E.itertuples():
        i = idx.searchsorted(e.file_date)
        if i >= len(idx) or e.ticker not in col:
            continue
        ev[i, col[e.ticker]] = True
        rows.append((i, col[e.ticker], e.kind))
    out, cache = [], {}
    for i, j, kind in rows:
        if i + h >= len(idx) or not elig[i, j] or not np.isfinite(O[i + 1, j]) or not np.isfinite(C[i + h, j]):
            continue
        if i not in cache:
            ok = elig[i] & np.isfinite(O[i + 1]) & np.isfinite(C[i + h]) & np.isfinite(r5[i]) & np.isfinite(adr[i])
            if ok.sum() < 100:
                cache[i] = None; continue
            rq = pd.qcut(pd.Series(r5[i, ok]), 5, labels=False, duplicates="drop").values
            aq = pd.qcut(pd.Series(adr[i, ok]), 3, labels=False, duplicates="drop").values
            cell = np.full(C.shape[1], -1); cell[ok] = rq * 3 + aq
            fr = C[i + h] / O[i + 1] - 1
            ctl = pd.Series(fr[ok & ~ev[i]]).groupby(cell[ok & ~ev[i]]).mean()
            cache[i] = (cell, fr, ctl)
        if cache[i] is None or cache[i][0][j] < 0:
            continue
        cell, fr, ctl = cache[i]
        if cell[j] not in ctl.index:
            continue
        out.append(dict(date=idx[i], sym=cols[j], kind=kind, ret=fr[j], ctl=ctl[cell[j]],
                        runup60=r60[i, j], day0=r1[i, j]))
    return pd.DataFrame(out)


def report(T, h, label, out):
    if len(T) < 30:
        out.append(f"\n# {label} +{h}: n {len(T)} -- too few"); return None
    T = T.copy(); T["x"] = 100 * (T.ret - T.ctl)
    mo = T.groupby(T.date.dt.to_period("M")).x.mean()
    hh = mo.index < pd.Period(SPLIT, "M")
    cost = 100 * (2 * SLIP + BORROW * h / 252)
    sp = -100 * T.ret - cost
    yr = T.groupby(T.date.dt.year).x.mean()
    r = dict(label=label, h=h, n=len(T), names=T.sym.nunique(), abs_ret=100 * T.ret.mean(), ctl=100 * T.ctl.mean(),
             excess=mo.mean(), t=tstat(mo), h1=mo[hh].mean(), h2=mo[~hh].mean(), short_pnl=sp.mean(),
             t_short=tstat(sp.groupby(T.date.dt.to_period("M")).mean()), yrs_neg=f"{(yr < 0).sum()}/{len(yr)}")
    core = r["excess"] < 0 and abs(r["t"]) >= 3 and r["h1"] < 0 and r["h2"] < 0 and (yr < 0).sum() > len(yr) / 2
    r["PASS"] = bool(core and r["short_pnl"] > 0); r["VETO"] = bool(core and not r["PASS"])
    out.append(f"\n# {label} +{h}: {r['n']} events, {r['names']} names")
    out.append(f"  event fwd {r['abs_ret']:+.2f}% vs matched control {r['ctl']:+.2f}% | excess {r['excess']:+.2f}pp t {r['t']:+.2f} "
               f"| halves {r['h1']:+.2f} / {r['h2']:+.2f} | years negative {r['yrs_neg']}")
    out.append(f"  SHORT P&L after {cost:.2f}% costs+borrow: {r['short_pnl']:+.2f}% per trade (t {r['t_short']:+.2f})")
    out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
    return r


def main():
    if "--pull-only" in sys.argv:
        D = pull(); print(D.groupby("kind").size()); return
    P = load_panel(PANEL)
    E = events(P)
    E = E[(E.file_date >= START) & (E.file_date <= END)]
    # dedupe: first filing per name within 20 sessions
    idx = P.close.index
    E["i"] = idx.searchsorted(E.file_date)
    keep, last = [], {}
    for r in E.sort_values(["ticker", "i"]).itertuples():
        if r.ticker in last and r.i - last[r.ticker] < 20:
            continue
        last[r.ticker] = r.i; keep.append(r.Index)
    E = E.loc[keep]
    out = ["# Follow-on equity offerings as a short (pre-registration in the docstring)",
           f"# events after dedupe: {len(E):,} ({E.kind.value_counts().to_dict()}), {E.ticker.nunique()} names, "
           f"{E.file_date.min().date()} -> {E.file_date.max().date()}; forms {E.form.value_counts().to_dict()}"]
    R = []
    for h in HORIZONS:
        T = score(E, P, h)
        for lab, m in (("ALL", slice(None)), ("PRIMARY-ISSUER", T.kind == "primary"), ("SECONDARY", T.kind == "secondary")):
            tag = " *PRIMARY CELL*" if (lab == "ALL" and h == 20) else ""
            r = report(T[m] if lab != "ALL" else T, h, lab + tag, out)
            if r: R.append(r)
        if h == 20:
            T["x"] = 100 * (T.ret - T.ctl)
            for lab, m in (("run-up60 >= +30%", T.runup60 >= 0.30), ("run-up60 < +30%", T.runup60 < 0.30),
                           ("file-day <= -3%", T.day0 <= -0.03), ("file-day > -3%", T.day0 > -0.03)):
                mo = T[m].groupby(T[m].date.dt.to_period("M")).x.mean()
                out.append(f"  [exploratory +20] {lab:18s} n {int(m.sum()):5d} excess {mo.mean():+.2f}pp t {tstat(mo):+.2f} "
                           f"| abs {100*T[m].ret.mean():+.2f}%")
            T.to_csv(REPO / "data/studies/logs/offering_short_events.csv", index=False)
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    out.append("\nVERDICT: " + "; ".join(f"{r.label} +{r.h}: " + ("PASS (short)" if r.PASS else "VETO candidate" if r.VETO else "fail")
                                      for r in D.itertuples()))
    D.to_csv(REPO / "data/studies/offering_short_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    if "--pull-only" in sys.argv:
        main()
    else:
        real = sys.stdout; sys.stdout = open(LOG, "w")
        try:
            main()
        finally:
            sys.stdout.close(); sys.stdout = real
        print(open(LOG).read())

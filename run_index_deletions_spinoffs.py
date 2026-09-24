#!/usr/bin/env python3
"""
Undervalued idea #5: forced selling -- S&P 500 DELETIONS and SPIN-OFFS (pre-registered 2026-09-24, before the first run;
Gabe's undervalued brainstorm). Event list: Wikipedia "List of S&P 500 companies", Selected-changes table, revision
1365256480 (2026-07-21; the table was later removed from the live page) -> data/cache/sp500_changes_wikipedia.csv.

(a) DELETIONS  removals whose reason is a market-cap demotion (NOT acquisitions/mergers, where the price is pinned to a
               deal). Index funds must sell at the close before the effective date regardless of value.
    entry      the CLOSE of the session before the effective date (the rebalance close, when the forced selling prints);
               secondary: the effective-date close.
    outcome    20 / 60 / 120-session forward return minus the same-date ADR-matched eligible field.
    PRIMARY    60-session excess, t across events (dates rarely overlap); bar t >= 3, both halves (2018-01) > 0.
    also       the drawdown INTO the event (20 sessions before -> rebalance close) -- the forced-selling footprint.
(b) SPIN-OFFS  additions whose reason says the company was spun off from an S&P 500 constituent (the spinco).
    entry      the close of the 20th session after the spinco's first panel session (after parent holders have dumped
               the unwanted shares); outcome 60 / 120 sessions, same excess. Descriptive: n is small.
caveat         the panel holds names liquid as of 2026: deleted names that later failed are missing -> flatters (a).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_index_deletions_spinoffs.py   (log -> data/studies/logs/index_deletions_spinoffs.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/index_deletions_spinoffs.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")


def t(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    F = {h: ((C.shift(-h) / C - 1) * 100) for h in (20, 60, 120)}
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
    col = {tk: k for k, tk in enumerate(C.columns)}

    raw = pd.read_csv(REPO / "data/cache/sp500_changes_wikipedia.csv", header=[0, 1])
    ch = pd.DataFrame({"date": pd.to_datetime(raw.iloc[:, 0], errors="coerce"), "add": raw.iloc[:, 1],
                       "rem": raw.iloc[:, 3], "reason": raw.iloc[:, 5].astype(str)})
    ch = ch[ch.date >= "2010-01-01"]

    def ex_at(tk, i, h):
        j = col[tk]
        if i + h >= len(idx) or not np.isfinite(F[h].values[i, j]):
            return np.nan
        return F[h].values[i, j] - bench[h][i, j]

    out = []; pr = out.append
    pr("# Undervalued #5: forced selling -- S&P 500 deletions and spin-offs (pre-registration in the docstring)\n")
    dels = ch[ch.rem.notna() & ch.reason.str.contains("market cap", case=False)]
    rows = []
    for r in dels.itertuples(index=False):
        tk = str(r.rem).strip()
        if tk not in col:
            continue
        i_eff = idx.searchsorted(r.date)                 # first session on/after the effective date
        i = i_eff - 1                                    # the rebalance close
        if i < 21 or i + 20 >= len(idx) or not np.isfinite(C.values[i, col[tk]]):
            continue
        rows.append(dict(ticker=tk, eff=r.date.date(), into=100 * (C.values[i, col[tk]] / C.values[i - 20, col[tk]] - 1),
                         ex20=ex_at(tk, i, 20), ex60=ex_at(tk, i, 60), ex120=ex_at(tk, i, 120),
                         ex60_eff=ex_at(tk, i_eff, 60)))
    D = pd.DataFrame(rows)
    pr(f"(a) DELETIONS for market cap since 2010: {len(dels)} on the list, {len(D)} in the panel with prices")
    x = D.ex60.dropna(); dts = pd.to_datetime(D.eff)
    h1, h2 = D.ex60[dts < SPLIT].dropna(), D.ex60[dts >= SPLIT].dropna()
    pr(f"  20 sessions INTO the rebalance close: {D.into.mean():+.2f}% raw (median {D.into.median():+.2f})")
    pr(f"  PRIMARY 60d excess from the rebalance close: {x.mean():+.2f}pp (median {x.median():+.2f}), t {t(x):+.2f}, "
       f"{100 * (x > 0).mean():.0f}% +; halves {h1.mean():+.2f} (n {len(h1)}) / {h2.mean():+.2f} (n {len(h2)})")
    ok = t(x) >= 3 and h1.mean() > 0 and h2.mean() > 0
    pr(f"  bar (t >= 3, both halves > 0): {'PASS' if ok else 'FAIL'}")
    pr(f"  20d {D.ex20.mean():+.2f} (t {t(D.ex20):+.2f}) | 120d {D.ex120.mean():+.2f} (t {t(D.ex120):+.2f}) | "
       f"60d from the effective-date close {D.ex60_eff.mean():+.2f} (t {t(D.ex60_eff):+.2f})")
    pr("  per year 60d: " + "  ".join(f"{y} {v:+.1f} (n {k})" for y, (v, k) in
                                     D.assign(y=dts.dt.year).groupby("y").ex60.agg(["mean", "size"]).iterrows()))

    ch["add_name"] = raw.iloc[:, 2].astype(str).str.split().str[0].str.replace(r"[^A-Za-z]", "", regex=True)
    # the ADDED company must be the one named as spun off (not a constituent replaced by someone else's spin-off)
    spin = ch[ch["add"].notna() & [bool(__import__("re").search(r"(spun off|spin-?off of|spinoff of)\W+(\w+\W+){0,3}?" + n, r, __import__("re").I))
              for n, r in zip(ch.add_name, ch.reason)]]
    rows = []
    for r in spin.itertuples(index=False):
        tk = str(r.add).strip()
        if tk not in col:
            continue
        s = C[tk].dropna()
        s = s[s.index >= r.date - pd.Timedelta(days=10)]
        if len(s) < 25:
            continue
        i = idx.get_loc(s.index[20])
        rows.append(dict(ticker=tk, first=s.index[0].date(), ex60=ex_at(tk, i, 60), ex120=ex_at(tk, i, 120),
                         first20=100 * (s.iloc[20] / s.iloc[0] - 1)))
    S = pd.DataFrame(rows)
    pr(f"\n(b) SPIN-OFFS added to the S&P 500 since 2010: {len(spin)} on the list, {len(S)} in the panel")
    if len(S):
        pr(f"  first 20 sessions (the dumping window): {S.first20.mean():+.2f}% raw")
        pr(f"  60d excess from session 20: {S.ex60.mean():+.2f}pp (t {t(S.ex60):+.2f}, n {S.ex60.notna().sum()}); "
           f"120d {S.ex120.mean():+.2f}pp (t {t(S.ex120):+.2f}, n {S.ex120.notna().sum()})")
        pr("  " + ", ".join(f"{r.ticker} {r.ex120:+.0f}" for r in S.itertuples() if np.isfinite(r.ex120)))
    D.to_csv(REPO / "data/studies/index_deletions_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

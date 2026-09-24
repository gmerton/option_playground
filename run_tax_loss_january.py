#!/usr/bin/env python3
"""
Undervalued idea #4: the January tax-loss reversal (pre-registered 2026-09-24, before the first run; Gabe's undervalued
brainstorm). Classic claim: December tax-loss selling pushes the year's losers below value; they rebound in January.

DESIGN
  panel     liquid_panel_2009, eligible names; Januaries 2011 -> 2026 (16 years).
  losers    on the LAST session of December: calendar-year return (last Dec session of Y-1 -> last Dec session of Y) in
            the BOTTOM DECILE of eligible names (secondary: down >= 40% on the year).
  entry     the last December close; exit the last January close (secondary: first 10 January sessions).
  outcome   January return minus the same-date mean of eligible names in the same ADR band (the field).
  unit      one observation per YEAR (the losers' mean excess) -> 16 observations; t across years. Stock-level numbers
            are shown but years are the honest n.
  control   is JANUARY special? The same construction (bottom decile of the trailing 12-month return, next-month
            excess) at every OTHER month-end; January minus the other-month average, paired by year.
  PRIMARY   January excess of the bottom decile, t across years; bar t >= 3 AND January > other months (paired t
            reported). With 16 years, UNDERPOWERED is the expected verdict unless the effect is large.
  caveat    survivor panel: losers that went on to fail are missing -> flatters the losers.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_tax_loss_january.py   (log -> data/studies/logs/tax_loss_january.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/tax_loss_january.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]


def t(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    month_end = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).max()
    me = list(month_end.values)

    def excess(i0, i1, members_mask):
        """members' (i0 close -> i1 close) return minus the ADR-band-matched eligible field."""
        r = (C.iloc[i1] / C.iloc[i0] - 1) * 100
        e, a = E.iloc[i0] & r.notna(), A.iloc[i0]
        out = []
        for lo, hi in BANDS:
            band = e & (a >= lo) & (a < hi)
            mem, fld = band & members_mask, band & ~members_mask
            if mem.sum() and fld.sum() >= 10:
                out.append((r[mem] - r[fld].mean()).values)
        return np.concatenate(out) if out else np.array([])

    rows = []
    for k in range(12, len(me) - 1):
        d0, d1, dprev = me[k], me[k + 1], me[k - 12]
        i0, i1, ip = idx.get_loc(d0), idx.get_loc(d1), idx.get_loc(dprev)
        r12 = C.iloc[i0] / C.iloc[ip] - 1
        e = E.iloc[i0] & r12.notna()
        if e.sum() < 100:
            continue
        cut = r12[e].quantile(0.10)
        dec = e & (r12 <= cut)
        x = excess(i0, i1, dec)
        rec = dict(entry=pd.Timestamp(d0), month=pd.Timestamp(d1).month, year=pd.Timestamp(d1).year,
                   n=int(dec.sum()), ex=x.mean() if len(x) else np.nan)
        if pd.Timestamp(d1).month == 1:
            deep = e & (r12 <= -0.40)
            xd = excess(i0, i1, deep); rec.update(n_deep=int(deep.sum()), ex_deep=xd.mean() if len(xd) else np.nan)
            i10 = min(i0 + 10, len(idx) - 1)
            x10 = excess(i0, i10, dec); rec["ex_10d"] = x10.mean() if len(x10) else np.nan
        rows.append(rec)
    M = pd.DataFrame(rows)
    J = M[M.month == 1].set_index("year")
    O = M[M.month != 1].groupby("year").ex.mean()
    out = []; pr = out.append
    pr("# Undervalued #4: January tax-loss reversal (pre-registration in the docstring)\n")
    pr(f"Januaries {J.index.min()}–{J.index.max()} ({len(J)} years); bottom-decile losers per year: median {J.n.median():.0f}\n")
    pr("year  n   Jan excess   first-10d   deep(<=-40%) n / excess   other-month avg")
    for y, r in J.iterrows():
        pr(f"{y}  {r.n:3.0f}  {r.ex:+8.2f}    {r.ex_10d:+8.2f}     {r.n_deep:3.0f} / {r.ex_deep:+7.2f}        {O.get(y, np.nan):+7.2f}")
    d = (J.ex - O.reindex(J.index)).dropna()
    pr(f"\n## PRIMARY: January excess of the bottom decile {J.ex.mean():+.2f}pp (median {J.ex.median():+.2f}), t {t(J.ex):+.2f} "
       f"across {len(J)} years, {100 * (J.ex > 0).mean():.0f}% of years +")
    pr(f"  January minus other months (paired by year): {d.mean():+.2f}pp, t {t(d):+.2f}")
    ok = t(J.ex) >= 3 and d.mean() > 0
    pr(f"  bar (t >= 3 and January > other months): {'PASS' if ok else 'FAIL'}")
    pr(f"  secondary: first 10 sessions {J.ex_10d.mean():+.2f} (t {t(J.ex_10d):+.2f}); deep losers (<= -40%) "
       f"{J.ex_deep.mean():+.2f} (t {t(J.ex_deep):+.2f}); other-month losers overall {O.mean():+.2f} (t {t(O):+.2f})")
    M.to_csv(REPO / "data/studies/tax_loss_january_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

#!/usr/bin/env python3
"""
Intermediate-horizon momentum (Novy-Marx 2012, "Is momentum really momentum?") as a filter on the precision-tier book
(pre-registered 2026-09-24, before the first run). New axis: the tier selects on RECENT trend (EMA stack, near the
52wk high); the Trend Template 12-month RS criterion (c9) did not separate (-0.090pp, t -0.95). Novy-Marx: the return
from 12 to 7 months ago predicts better than the recent 6 months.

IH(t) = close[t-147] / close[t-252] - 1 (sessions ~ months 12 -> 7), ranked into terciles across ELIGIBLE names that day.
RECENT(t) = close[t-21] / close[t-126] - 1 (months 6 -> 2), for contrast.
A (factor check): each month-end, eligible names' IH top vs bottom decile -> 60-session ADR-matched excess, t across months.
PRIMARY: precision-tier house trades (close entry, day-low stop floored 2%, 20-EMA exit, % of price) by IH tercile at
  entry: TOP - BOTTOM tercile, Welch on entry-date means. Bar t >= 3, both halves (2023-01) the same sign.
SECONDARY: the same split on RECENT; IH quintiles for monotonicity.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_intermediate_momentum.py   (log -> data/studies/logs/intermediate_momentum.log)
"""
from __future__ import annotations

import contextlib
import io
import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/intermediate_momentum.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def welch(a, b):
    a, b = a.dropna(), b.dropna(); d = a.mean() - b.mean()
    return d, d / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def main() -> None:
    out = ["# Intermediate-horizon momentum (Novy-Marx 2012) on the precision tier (pre-registration in the docstring)\n"]
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    IH = C.shift(147) / C.shift(252) - 1
    idx = C.index
    F60 = (C.shift(-60) / C - 1) * 100
    ends = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    ends = ends[(ends >= "2010-06-01") & (ends <= idx[-61])]
    rows = []
    for d in ends.values:
        d = pd.Timestamp(d); e = E.loc[d]; ih = IH.loc[d][e].dropna()
        if len(ih) < 200:
            continue
        f, a = F60.loc[d], A.loc[d]
        def ex(names):
            vals = []
            for lo, hi in BANDS:
                band = e & (a >= lo) & (a < hi) & f.notna()
                mem = band & band.index.isin(names); fld = band & ~band.index.isin(names)
                if mem.sum() and fld.sum() >= 10:
                    vals.append((f[mem] - f[fld].mean()).values)
            return np.concatenate(vals).mean() if vals else np.nan
        rows.append(dict(month=d, top=ex(ih[ih >= ih.quantile(0.9)].index), bot=ex(ih[ih <= ih.quantile(0.1)].index)))
    M = pd.DataFrame(rows)
    out.append(f"A factor check ({len(M)} months): IH top decile {M.top.mean():+.2f}pp (t {tstat(M.top):+.2f}), bottom "
               f"{M.bot.mean():+.2f}pp (t {tstat(M.bot):+.2f}), top - bottom {(M.top - M.bot).mean():+.2f}pp (t {tstat(M.top - M.bot):+.2f})")

    from run_precision_tier_control import build
    from run_adr_floor_test import house
    with contextlib.redirect_stdout(io.StringIO()):
        P2, brk, prec = build()
        T = house(P2, prec)
    C2, E2 = P2.close, P2.elig.fillna(False)
    ih2 = (C2.shift(147) / C2.shift(252) - 1).where(E2).rank(axis=1, pct=True)
    rc2 = (C2.shift(21) / C2.shift(126) - 1).where(E2).rank(axis=1, pct=True)
    T["ih"] = [ih2.values[i, j] for i, j in zip(T.i, T.j)]
    T["rc"] = [rc2.values[i, j] for i, j in zip(T.i, T.j)]
    T["date"] = pd.to_datetime(T.date)
    h = pd.Timestamp("2023-01-01")
    for col, lab, tag in (("ih", "INTERMEDIATE (12->7m)", "PRIMARY"), ("rc", "RECENT (6->2m)", "secondary")):
        K = T.dropna(subset=[col])
        top, bot = K[K[col] > 2 / 3], K[K[col] <= 1 / 3]
        d, t = welch(top.groupby("date").pct.mean(), bot.groupby("date").pct.mean())
        d1, _ = welch(top[top.date < h].groupby("date").pct.mean(), bot[bot.date < h].groupby("date").pct.mean())
        d2, _ = welch(top[top.date >= h].groupby("date").pct.mean(), bot[bot.date >= h].groupby("date").pct.mean())
        out.append(f"\n## {tag}: {lab} tercile at entry ({len(K):,} tier trades)")
        out.append(f"  top {len(top):,}: {top.pct.mean():+.2f}%/trade (R {top.R.mean():+.3f}) | bottom {len(bot):,}: {bot.pct.mean():+.2f}% "
                   f"(R {bot.R.mean():+.3f}) | top - bottom {d:+.2f}pp, t {t:+.2f}, halves {d1:+.2f} / {d2:+.2f}")
        if tag == "PRIMARY":
            ok = abs(t) >= 3 and np.sign(d1) == np.sign(d2)
            out.append(f"  bar (|t| >= 3, halves same sign): {'PASS' if ok else 'FAIL'}")
            q = pd.qcut(K[col], 5, labels=False)
            out.append("  by quintile (%/trade): " + "  ".join(f"Q{int(k) + 1} {v:+.2f}" for k, v in K.groupby(q).pct.mean().items()))
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

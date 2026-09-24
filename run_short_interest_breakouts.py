#!/usr/bin/env python3
"""
[BB-1] Short interest as a filter on the house breakout (pre-registered 2026-09-23, before any return was computed).

Gabe: "one factor we've never looked at is short interest." Two competing mechanisms, so the test is TWO-SIDED:
  squeeze fuel   -- heavily shorted names that break out force short covering (forced buyers) -> better breakouts
  informed shorts -- the literature's short-interest anomaly: high-SI names underperform -> worse breakouts
Data: FINRA bi-monthly short interest via Polygon (`data/cache/short_interest.parquet`, 2017-12 -> 2026-08;
  run_short_interest_pull.py). No float history -> the measure is DAYS TO COVER (SI / avg daily volume).
  ⚠ PUBLICATION LAG: SI is known only ~8 business days after its settlement date; a report is usable from
  settlement + 8 BDays. Every breakout uses the latest report published by t-1.
  DTC percentile is ranked cross-sectionally among the liquid-panel names in each report.
Trade: house breakout = close > prior 20d high, ADR20 >= 3%, liquid-eligible (liquid_panel_2009.parquet), 2018-02 ->
  2026-09; enter at the close, stop = breakout day's low judged on the close, 20-EMA trail, max 60 sessions, 0.10% a
  side; metric % per trade (V.pct_trade, as in the VCP / ADX tests).
PRIMARY: HIGH (DTC top quintile) minus LOW (bottom quintile) breakouts, SAME-DATE paired (dates with both arms), t
  clustered by date. Bar |t| >= 3, both halves (split 2022-01-01) the same sign, per-year shown (2020-21 meme years
  flagged -- they could dominate either way).
Secondary (exploratory, no verdict of their own):
  squeeze variant -- HIGH-DTC breakouts on RVOL >= 2 vs same-date LOW;
  SI change -- DTC rising (latest report / prior report >= 1.25) vs falling (<= 0.8) at the breakout;
  the classic anomaly off-breakout -- all eligible names, 20-session forward return, top vs bottom DTC quintile, on
  non-overlapping 20-session dates (is it a breakout effect or a stock effect?);
  held-the-level share HIGH vs LOW.

Run: PYTHONPATH=src .venv/bin/python3 run_short_interest_breakouts.py   (log -> data/studies/logs/short_interest_breakouts.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel
import run_vcp_damped_sine as V

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/short_interest_breakouts.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, SPLIT, LAG_BD = "2018-02-01", "2022-01-01", 8


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def si_panel(P):
    """DTC percentile and DTC change, as known on each panel date (publication-lagged, forward-filled)."""
    si = pd.read_parquet(REPO / "data/cache/short_interest.parquet")
    si = si[si.ticker.isin(P.close.columns) & (si.days_to_cover > 0)].copy()
    si["pub"] = si.settlement_date + pd.offsets.BDay(LAG_BD)
    si["pct"] = si.groupby("settlement_date").days_to_cover.rank(pct=True)
    si = si.sort_values(["ticker", "settlement_date"])
    si["chg"] = si.days_to_cover / si.groupby("ticker").days_to_cover.shift(1)
    idx = P.close.index

    def spread(col):
        w = si.pivot_table(index="pub", columns="ticker", values=col, aggfunc="last")
        w = w.reindex(idx.union(w.index)).sort_index().ffill()
        return w.reindex(idx).shift(1).reindex(columns=P.close.columns)       # known by t-1
    return spread("pct"), spread("chg")


def main():
    P = load_panel(PANEL)
    raw = pd.read_parquet(REPO / PANEL)
    Vol = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(index=P.close.index,
                                                                                           columns=P.close.columns)
    rvol = (Vol / Vol.shift(1).rolling(50).mean()).values
    pct, chg = si_panel(P)
    lvl = P.high.shift(1).rolling(20).max()
    hb = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    hb[hb.index < START] = False
    rows = []
    for i, j in zip(*np.where(hb.values)):
        q = pct.values[i, j]
        if not np.isfinite(q):
            continue
        r = V.pct_trade(P, j, i, P.low.values[i, j], lvl.values[i, j])
        if r is None:
            continue
        rows.append(dict(date=P.close.index[i], sym=P.close.columns[j], pct=q, chg=chg.values[i, j],
                         rvol=rvol[i, j], ret=r[0], held=r[1]))
    T = pd.DataFrame(rows)
    T["arm"] = np.where(T.pct >= 0.8, "HIGH", np.where(T.pct <= 0.2, "LOW", "mid"))
    print(f"# Short interest x house breakout [BB-1] -- {len(T):,} breakouts with a published SI report, "
          f"{T.date.min().date()} -> {T.date.max().date()}")
    print(T.groupby("arm").agg(n=("ret", "size"), mean=("ret", "mean"), median=("ret", "median"),
                               win=("ret", lambda x: 100 * (x > 0).mean()), held=("held", "mean")).round(3).to_string())

    def paired(a, b, col="ret", data=T):
        g = data[data.arm2.isin([a, b])].groupby(["date", "arm2"])[col].mean().unstack()
        if a not in g or b not in g:
            return None
        return (g[a] - g[b]).dropna()

    T["arm2"] = T.arm
    d = paired("HIGH", "LOW")
    h = d.index < SPLIT
    print(f"\n## PRIMARY: HIGH-DTC minus LOW-DTC breakouts, same date: {d.mean():+.3f}pp  t {tstat(d):+.2f}  "
          f"(dates {len(d)}) | halves {d[h].mean():+.3f} / {d[~h].mean():+.3f}")
    print("per year (pp):\n" + d.groupby(d.index.year).agg(["size", "mean"]).round(3).T.to_string())
    dh = paired("HIGH", "LOW", "held")
    print(f"held-the-level share HIGH - LOW: {100 * dh.mean():+.1f}pp (t {tstat(dh):+.2f})")
    print("\n## exploratory")
    T["arm2"] = np.where((T.arm == "HIGH") & (T.rvol >= 2), "SQUEEZE", T.arm)
    s = paired("SQUEEZE", "LOW")
    if s is not None:
        print(f"squeeze (HIGH DTC & RVOL >= 2) - LOW: {s.mean():+.3f}pp t {tstat(s):+.2f} (dates {len(s)})")
    T["arm2"] = np.where(T.chg >= 1.25, "RISING", np.where(T.chg <= 0.8, "FALLING", "flat"))
    c = paired("RISING", "FALLING")
    print(f"DTC rising (>= 1.25x) - falling (<= 0.8x): {c.mean():+.3f}pp t {tstat(c):+.2f} (dates {len(c)})")
    # the classic anomaly, off-breakout: all eligible names, 20-session forward return, non-overlapping dates
    C = P.close
    fr = (C.shift(-20) / C - 1) * 100
    dates = C.index[(C.index >= START)][::20]
    dates = dates[dates <= C.index[-21]]
    e = P.elig.fillna(False)
    rows = []
    for dt in dates:
        q = pct.loc[dt]; f = fr.loc[dt]; ok = e.loc[dt] & q.notna() & f.notna()
        hi, lo = f[ok & (q >= 0.8)], f[ok & (q <= 0.2)]
        if len(hi) >= 10 and len(lo) >= 10:
            rows.append(dict(date=dt, diff=hi.mean() - lo.mean()))
    A = pd.DataFrame(rows).set_index("date")["diff"]
    ha = A.index < SPLIT
    print(f"classic anomaly, all eligible names, 20d fwd, top - bottom DTC quintile: {A.mean():+.3f}pp t {tstat(A):+.2f} "
          f"(dates {len(A)}) | halves {A[ha].mean():+.3f} / {A[~ha].mean():+.3f}")
    T.drop(columns=["arm2"]).to_csv(REPO / "data/studies/logs/short_interest_breakouts_trades.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

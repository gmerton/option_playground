#!/usr/bin/env python3
"""
[WL-5e] Qullamaggie's index 10/20-day filter on the house breakout (pre-registered 2026-09-23; spec from
data/qullamaggie/README.md "Highest-value tests" #3, written before running).

His words (CWT 00:47): "breakouts don't exist in a falling market". Relay rule: index 10 > 20-day SMA and both rising
= good; 10 < 20 and both falling = no breakouts. Resolves the split between Carter REGIME.md (SPY > 200 halves drawdown
2006-26) and the 2019-26 regime-feedback null (market state doesn't forecast breakout R).

Index = QQQ (he trades growth). State at the PRIOR close (known before the breakout):
  RED   = SMA10 < SMA20 and both falling (vs one session earlier)
  GREEN = SMA10 > SMA20 and both rising
  MIXED = otherwise
Comparator: SPY below its 200-day SMA (prior close) vs above.
Pool: house breakouts (close > prior 20d high, ADR >= 3%, liquid-eligible) on liquid_panel_2009.parquet, 2010-01 ->
  2026-09. Trade: close entry, stop = breakout-day low judged on the close, 20-EMA trail, max 60 sessions, % per trade.
PRIMARY: mean % per trade of RED-state breakouts minus all other breakouts; OLS on a RED dummy with SEs clustered by
  calendar month (the spec's month-clustered t). Expect negative. Bar |t| >= 3, both halves (split 2018-01-01) the same
  sign, per-year shown.
Secondary: GREEN vs rest; SPY<200 vs rest; monthly book (equal-weight mean % of the month's breakouts) with vs without
  the RED filter: mean, t, max drawdown of the cumulative sum.
Prior: low (market state didn't forecast breakout R 2019-26; the localisation regime sweep found nothing).

Run: PYTHONPATH=src .venv/bin/python3 run_index_filter.py   (log -> data/studies/logs/index_filter.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.studies.pattern_test import load_panel
import run_vcp_damped_sine as V

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/index_filter.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, SPLIT = "2010-01-01", "2018-01-01"


def states(P):
    q = P.close["QQQ"]
    s10, s20 = q.rolling(10).mean(), q.rolling(20).mean()
    red = (s10 < s20) & (s10 < s10.shift(1)) & (s20 < s20.shift(1))
    green = (s10 > s20) & (s10 > s10.shift(1)) & (s20 > s20.shift(1))
    spy = P.close["SPY"]
    below200 = spy < spy.rolling(200).mean()
    return red.shift(1), green.shift(1), below200.shift(1)


def clustered(y: pd.Series, x: pd.Series, groups: pd.Series):
    X = sm.add_constant(x.astype(float))
    f = sm.OLS(y.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})
    return f.params[1], f.tvalues[1]


def main():
    P = load_panel(PANEL)
    red, green, b200 = states(P)
    lvl = P.high.shift(1).rolling(20).max()
    hb = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    hb[hb.index < START] = False
    for c in ("SPY", "QQQ", "IWM", "RSP"):
        if c in hb.columns:
            hb[c] = False
    rows = []
    for i, j in zip(*np.where(hb.values)):
        r = V.pct_trade(P, j, i, P.low.values[i, j], lvl.values[i, j])
        if r is not None:
            d = hb.index[i]
            rows.append(dict(date=d, ret=r[0], red=bool(red.iloc[i]), green=bool(green.iloc[i]), b200=bool(b200.iloc[i])))
    T = pd.DataFrame(rows)
    T["month"] = T.date.dt.to_period("M")
    print(f"# Index filter [WL-5e] -- {len(T):,} house breakouts {T.date.min().date()} -> {T.date.max().date()}; "
          f"all mean {T.ret.mean():+.2f}%")
    print(f"state shares of breakouts: RED {T.red.mean():.1%}, GREEN {T.green.mean():.1%}, SPY<200 {T.b200.mean():.1%}")
    out = {}
    for lab, col in (("PRIMARY RED (QQQ 10<20, both falling)", "red"), ("GREEN (10>20, both rising)", "green"),
                     ("SPY < 200d", "b200")):
        a, b = T[T[col]], T[~T[col]]
        coef, t = clustered(T.ret, T[col], T.month)
        h = T.date < SPLIT
        c1, _ = clustered(T[h].ret, T[h][col], T[h].month)
        c2, _ = clustered(T[~h].ret, T[~h][col], T[~h].month)
        print(f"\n## {lab}: in-state n {len(a):,} mean {a.ret.mean():+.2f}% | rest n {len(b):,} mean {b.ret.mean():+.2f}% | "
              f"diff {coef:+.2f}pp month-clustered t {t:+.2f} | halves {c1:+.2f} / {c2:+.2f}")
        yr = pd.DataFrame({"in": a.groupby(a.date.dt.year).ret.mean(), "rest": b.groupby(b.date.dt.year).ret.mean(),
                           "n_in": a.groupby(a.date.dt.year).size()})
        yr["diff"] = yr["in"] - yr.rest
        print("per year (%):\n" + yr.round(2).T.to_string())
        out[col] = (coef, t, c1, c2)
    print("\n## monthly book: equal-weight mean % of each month's breakouts")
    for lab, X in (("unfiltered", T), ("skip RED", T[~T.red]), ("skip SPY<200", T[~T.b200])):
        m = X.groupby("month").ret.mean()
        cum = m.cumsum()
        tt = m.mean() / m.std(ddof=1) * np.sqrt(len(m))
        print(f"{lab:14s} months {len(m):3d} | mean {m.mean():+.3f}%/month-trade t {tt:+.2f} | "
              f"max drawdown of cumulative {(cum.cummax() - cum).max():.2f} | worst month {m.min():+.2f}")
    T.to_csv(REPO / "data/studies/logs/index_filter_trades.csv", index=False)
    return out


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

#!/usr/bin/env python3
"""
Turn-of-the-month effect in SPY / QQQ (pre-registered 2026-09-24, before the first run; Gabe's "other ideas" #2).
First calendar-seasonality row in the ledger. Published by Ariel (1987) and Lakonishok & Smidt (1988), so 2000 -> 2026
is genuinely OUT OF SAMPLE for the original claim.

DESIGN
  data      yfinance adjusted daily closes (backtesting use is fine per project_data_sources): SPY 1993 ->, QQQ 1999 ->.
  TOM days  the LAST trading day of a month and the FIRST THREE trading days of the next (the classic -1..+3 window);
            each day's close-to-close return.
  PRIMARY   SPY, 2000-01 -> 2026-09: mean daily return on TOM days minus non-TOM days, OLS with HAC (5 lags) t.
            Bar: t >= 3, both halves (2000-2012 / 2013-2026) positive.
  TRADE     hold SPY only over the window (buy the close two sessions before month-end, sell the close of day +3),
            else cash (0%): CAGR, Sharpe, max drawdown, % time invested vs buy-and-hold; cost 1 bp per side.
  SECONDARY QQQ; per-day profile -3 .. +5; pre-1993..1999 in-sample check; per-decade.

Usage: PYTHONPATH=src .venv/bin/python3 run_turn_of_month.py   (log -> data/studies/logs/turn_of_month.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/turn_of_month.log"
COST = 0.0001


def tom_frame(sym: str) -> pd.DataFrame:
    px = yf.download(sym, start="1993-01-01", end="2026-09-24", auto_adjust=True, progress=False)["Close"].squeeze()
    d = pd.DataFrame({"r": px.pct_change()}).dropna()
    ym = d.index.to_period("M")
    pos = d.groupby(ym).cumcount()                      # 0 = first trading day of the month
    size = d.groupby(ym).r.transform("size")
    d["k"] = np.where(pos <= 4, pos + 1, pos - size)    # +1..+5 from the start, -1 = last day, -2 ...
    d["tom"] = d.k.isin([-1, 1, 2, 3])
    return d


def test(d: pd.DataFrame, a: str, b: str):
    x = d.loc[a:b]
    fit = sm.OLS(x.r * 1e4, sm.add_constant(x.tom.astype(float))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return fit.params.iloc[1], fit.tvalues.iloc[1], x[x.tom].r.mean() * 1e4, x[~x.tom].r.mean() * 1e4


def trade(d: pd.DataFrame, a: str, b: str) -> dict:
    x = d.loc[a:b].copy()
    inpos = x.tom.values
    ret = np.where(inpos, x.r.values, 0.0)
    entries = np.diff(np.r_[0, inpos.astype(int)]) == 1
    ret = ret - COST * 2 * entries                       # a round trip per window
    eq, bh = (1 + pd.Series(ret, index=x.index)).cumprod(), (1 + x.r).cumprod()
    yrs = len(x) / 252
    f = lambda e, r: dict(cagr=100 * (e.iloc[-1] ** (1 / yrs) - 1), sharpe=np.mean(r) / np.std(r) * sqrt(252),
                          maxdd=100 * (e / e.cummax() - 1).min())
    return dict(tom=f(eq, ret), bh=f(bh, x.r.values), invested=100 * inpos.mean())


def main() -> None:
    out = ["# Turn-of-the-month in SPY / QQQ (pre-registration in the docstring)"]
    for sym in ("SPY", "QQQ"):
        d = tom_frame(sym)
        out.append(f"\n## {sym} ({d.index.min().date()} -> {d.index.max().date()})")
        for lab, a, b in (("OOS 2000-2026 (PRIMARY)" if sym == "SPY" else "2000-2026", "2000-01-01", "2026-12-31"),
                          ("  half 2000-2012", "2000-01-01", "2012-12-31"), ("  half 2013-2026", "2013-01-01", "2026-12-31"),
                          ("in-sample-era 1993-1999", "1993-01-01", "1999-12-31")):
            if d.loc[a:b].empty:
                continue
            diff, t, tm, nt = test(d, a, b)
            out.append(f"  {lab:26s} TOM {tm:+6.2f} bp/day vs other {nt:+6.2f} | diff {diff:+6.2f} bp, t {t:+.2f}")
        if sym == "SPY":
            diff, t, _, _ = test(d, "2000-01-01", "2026-12-31")
            h = [test(d, "2000-01-01", "2012-12-31")[0], test(d, "2013-01-01", "2026-12-31")[0]]
            out.append(f"  PRIMARY bar (t >= 3, both halves > 0): {'PASS' if t >= 3 and min(h) > 0 else 'FAIL'}")
        prof = d.loc["2000":].groupby("k").r.agg(["mean", "size"])
        out.append("  day profile 2000+ (bp): " + "  ".join(f"{int(k):+d}:{v * 1e4:+.1f}" for k, v in prof["mean"].items() if -3 <= k <= 5))
        dec = d.loc["2000":].groupby(d.loc["2000":].index.year // 10 * 10).apply(lambda x: (x[x.tom].r.mean() - x[~x.tom].r.mean()) * 1e4)
        out.append("  diff by decade (bp): " + "  ".join(f"{k}s {v:+.1f}" for k, v in dec.items()))
        tr = trade(d, "2000-01-01", "2026-12-31")
        out.append(f"  TRADE 2000+: TOM-only CAGR {tr['tom']['cagr']:+.2f}% Sharpe {tr['tom']['sharpe']:.2f} maxDD {tr['tom']['maxdd']:.1f}% "
                   f"(invested {tr['invested']:.0f}% of days) | buy-and-hold CAGR {tr['bh']['cagr']:+.2f}% Sharpe {tr['bh']['sharpe']:.2f} maxDD {tr['bh']['maxdd']:.1f}%")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

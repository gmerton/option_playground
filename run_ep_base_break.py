#!/usr/bin/env python3
"""
[WL-5d] Episodic pivot OUT OF A LONG BASE vs the plain catalyst-day buy (pre-registered 2026-09-23; spec from
data/qullamaggie/README.md "Highest-value tests" #2, written before running).

Question: DR-EP arm A (buy the close of a catalyst gap day) is -0.173R, t -4.70. Qullamaggie's EP adds a condition our
catalyst gate lacked: the gap breaks out of a multi-month base. Does that one condition change the sign?

Data: liquid_panel_2009.parquet (same universe from 2009), earnings dates from MySQL earnings_report (275 names,
2010 -> 2026). Window 2010-01-01 -> 2026-09.
Event: the earnings REACTION day = of the first session on/after raw_date and the next one, the one with the larger
  |close-to-close return| (as run_ledger_rerun.earnings_patterns); require gap = open / prior close - 1 >= 5% and
  RVOL = volume / trailing-50 mean >= 3, liquid-eligible.
Arms:
  BASE-BREAK  event AND close > max(high over the prior 252 sessions)   <- Qullamaggie's EP
  NO-BREAK    event, close <= that high                                 <- the DR-EP arm A analogue on earnings gaps
Trade (both): enter at the event CLOSE, stop = event-day low judged on the close, 20-EMA close trail, max 60 sessions.
PRIMARY: BASE-BREAK through the upgraded harness (paired edge t vs control="post", p_search over the 5 arms; bar = the
  harness bar: paired t >= 3, halves > 0, p_search < 0.003). control="xname" reported (ledger=False).
Secondary: BASE-BREAK minus NO-BREAK in % per trade (pct_trade exit), Welch t, halves (split 2018-01-01), per-year.
Prior: low-moderate. Catalyst-day buys fail here, but the 252-day-high condition is exactly the missing piece.

Run: AWS/MySQL env; PYTHONPATH=src .venv/bin/python3 run_ep_base_break.py   (log -> data/studies/logs/ep_base_break.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from lib.studies.pattern_test import daily_signals, load_panel, run_daily
import run_vcp_damped_sine as V

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/ep_base_break.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, SPLIT = "2010-01-01", "2018-01-01"


def events(P, raw):
    from lib.mysql_lib import _get_engine
    C, O, H = P.close, P.open, P.high
    vol = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(index=C.index, columns=C.columns)
    ret = C.pct_change(fill_method=None)
    gap = O / C.shift(1) - 1
    rvol = vol / vol.shift(1).rolling(50).mean()
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    idx, colpos = C.index, {c: k for k, c in enumerate(C.columns)}
    E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
    E["raw_date"] = pd.to_datetime(E.raw_date)
    E = E[(E.raw_date >= START) & (E.raw_date <= idx[-1]) & E.ticker.isin(colpos)].drop_duplicates()
    brk = pd.DataFrame(False, index=idx, columns=C.columns)
    nob = brk.copy()
    n_all = 0
    for r in E.itertuples(index=False):
        j = colpos[r.ticker]
        i0 = idx.searchsorted(r.raw_date)
        if i0 + 1 >= len(idx):
            continue
        rr = [ret.values[i, j] for i in (i0, i0 + 1)]
        if not np.isfinite(rr).any():
            continue
        i = (i0, i0 + 1)[int(np.nanargmax(np.abs(rr)))]
        n_all += 1
        if not (gap.values[i, j] >= 0.05 and rvol.values[i, j] >= 3 and P.elig.values[i, j]):
            continue
        if np.isfinite(hi252.values[i, j]) and C.values[i, j] > hi252.values[i, j]:
            brk.iat[i, j] = True
        elif np.isfinite(hi252.values[i, j]):
            nob.iat[i, j] = True
    return brk, nob, n_all


def pct_book(P, m):
    rows = []
    for i, j in zip(*np.where(m.values)):
        r = V.pct_trade(P, j, i, P.low.values[i, j], np.nan)
        if r is not None:
            rows.append(dict(date=m.index[i], sym=m.columns[j], ret=r[0]))
    return pd.DataFrame(rows)


def main():
    P = load_panel(PANEL)
    raw = pd.read_parquet(REPO / PANEL)
    brk, nob, n_all = events(P, raw)
    print(f"# EP base-break [WL-5d] -- {n_all:,} earnings reactions 2010+; gap>=5% & RVOL>=3: BASE-BREAK "
          f"{int(brk.values.sum())}, NO-BREAK {int(nob.values.sum())}")
    A, B = pct_book(P, brk), pct_book(P, nob)
    h = lambda x: x.date < SPLIT
    print("\n## secondary: % per trade (close entry, day-low stop on the close, 20-EMA trail, max 60)")
    for lab, X in (("BASE-BREAK", A), ("NO-BREAK", B)):
        t = X.ret.mean() / X.ret.std(ddof=1) * np.sqrt(len(X))
        print(f"{lab:10s} n {len(X):4d} | mean {X.ret.mean():+.2f}% (t vs 0 {t:+.2f}) | median {X.ret.median():+.2f}% | "
              f"win {100 * (X.ret > 0).mean():.0f}% | halves {X[h(X)].ret.mean():+.2f}/{X[~h(X)].ret.mean():+.2f}")
    w = stats.ttest_ind(A.ret, B.ret, equal_var=False).statistic
    print(f"BASE-BREAK - NO-BREAK: {A.ret.mean() - B.ret.mean():+.2f}pp, Welch t {w:+.2f} | halves "
          f"{A[h(A)].ret.mean() - B[h(B)].ret.mean():+.2f} / {A[~h(A)].ret.mean() - B[~h(B)].ret.mean():+.2f}")
    yr = pd.DataFrame({"n_brk": A.groupby(A.date.dt.year).size(), "brk": A.groupby(A.date.dt.year).ret.mean(),
                       "n_nob": B.groupby(B.date.dt.year).size(), "nob": B.groupby(B.date.dt.year).ret.mean()})
    print("per year (%):\n" + yr.round(2).T.to_string())
    A.to_csv(REPO / "data/studies/logs/ep_base_break_trades.csv", index=False)
    B.to_csv(REPO / "data/studies/logs/ep_no_break_trades.csv", index=False)
    print("\n\n# PRIMARY: harness, paired rule (close entry, day-low stop, hold 60)")
    pat = lambda _P: daily_signals(brk, stop=P.low, side="long", since=START)
    run_daily("EP base-break (earnings gap>=5% RVOL>=3 close>252d high)", pat, hold=60, entry_at="close",
              control="post", panel=P, split=SPLIT, note="WL-5d Qullamaggie EP out of a long base; liquid_panel_2009, 2010+")
    run_daily("EP base-break xname", pat, hold=60, entry_at="close", control="xname", panel=P, split=SPLIT, ledger=False)
    patn = lambda _P: daily_signals(nob, stop=P.low, side="long", since=START)
    run_daily("EP no-break (DR-EP A analogue on earnings) post", patn, hold=60, entry_at="close", control="post",
              panel=P, split=SPLIT, ledger=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    txt = open(LOG).read()
    print(txt.split("# PRIMARY")[0])
    for ln in txt.splitlines():
        if ln.startswith("===") or "paired edge by half" in ln or "passes the bar" in ln:
            print(ln)
    import re
    for blk in re.findall(r"paired edge by year.*?\n(.*?\n.*?\n.*?)\n", txt, re.S):
        print(blk)

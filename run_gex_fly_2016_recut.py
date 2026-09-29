#!/usr/bin/env python3
"""1-day 2x iron fly on positive-gamma days, re-cut at 2016, SPY and QQQ (2026-09-29, audit List A #4).

PRE-REGISTERED: data/studies/gex_fly_2016_recut_2026-09-29.md (committed before this ran). Reads the existing
trade-level outputs of run_gex_spy_ironfly.py; no engine re-run. Bar t >= 3.2 (second look, Sidak k = 2).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_gex_fly_2016_recut.py > data/studies/gex_fly_2016_recut_2026-09-29.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

pd.set_option("display.width", 230)
START, SPLIT, BAR = pd.Timestamp("2016-01-01"), pd.Timestamp("2021-01-01"), 3.2
FILES = {"SPY": "data/studies/gex_spy_ironfly_2026-09-21.csv", "QQQ": "data/studies/gex_qqq_ironfly_2026-09-22.csv"}


def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def summ(g):
    mo = g.groupby(g.day.dt.to_period("M")).pnl_usd.sum()
    h1, h2 = g[g.day < SPLIT].ret_risk, g[g.day >= SPLIT].ret_risk
    return dict(n=len(g), ret_risk=g.ret_risk.mean(), t=tstat(g.ret_risk), h1=h1.mean(), t1=tstat(h1), n1=len(h1),
                h2=h2.mean(), t2=tstat(h2), n2=len(h2), t_month=tstat(mo), win=(g.pnl_usd > 0).mean() * 100,
                usd_mean=g.pnl_usd.mean(), worst_usd=g.pnl_usd.min())


def main():
    out, verdict = [], {}
    for tk, f in FILES.items():
        x = pd.read_csv(f, parse_dates=["day"])
        x = x[(x.w == 2.0) & (x.day >= START)]
        wk = x.day.dt.dayofweek != 0  # entry Fri -> Mon expiry means the fly settles on a Monday
        for lab, g in [("POS", x[~x.NEG]), ("NEG", x[x.NEG]), ("ALL", x), ("POS weekday-only", x[~x.NEG & wk])]:
            out.append(dict(tk=tk, gamma=lab, **summ(g)))
        R = pd.DataFrame(out); pos = R[(R.tk == tk) & (R.gamma == "POS")].iloc[0]; neg = R[(R.tk == tk) & (R.gamma == "NEG")].iloc[0]
        verdict[tk] = pos.ret_risk > 0 and pos.t >= BAR and pos.h1 > 0 and pos.h2 > 0 and pos.ret_risk > neg.ret_risk
        print(f"\n{tk} POS by year (mean return on max risk %, n):")
        p = x[~x.NEG]
        print(pd.DataFrame({"mean": p.groupby(p.day.dt.year).ret_risk.mean(), "n": p.groupby(p.day.dt.year).size()}).round(1).T.to_string())
    R = pd.DataFrame(out)
    print("\n== w = 2.0, 2016-01 -> 2026-02, return on max risk at the real fill (%); halves split 2021-01-01 ==")
    print(R.round(2).to_string(index=False))
    for tk, ok in verdict.items():
        print(f"PASS {tk} (POS: mean > 0, t >= {BAR}, both halves > 0, POS > NEG): {'YES' if ok else 'no'}")
    R.to_csv("data/studies/gex_fly_2016_recut_2026-09-29.csv", index=False)


if __name__ == "__main__":
    main()

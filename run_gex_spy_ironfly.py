#!/usr/bin/env python3
"""SPY 1-day ATM iron butterfly by dealer-gamma sign (2026-09-21).

PRE-REGISTERED: data/studies/gex_spy_ironfly_2026-09-21.md -- implements that spec; do not tune against its output.
Same days / entry / expiry / ATM strike / GEX sign as run_gex_spy_straddle.py; wings at K +/- w x (straddle mid),
nearest listed strike, w in {1.0, 2.0}. House fills: shorts at mid - 25% BA, longs at mid + 25% BA, $0.0065/sh/leg.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_gex_spy_ironfly.py | tee data/studies/gex_spy_ironfly_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

import run_gex_regime_pin as base

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
SLIP, COMM, MIN_MID = 0.25, 0.0065, 0.10
WINGS = (1.0, 2.0)


def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def streak(neg: pd.Series) -> int:
    best = cur = 0
    for v in neg:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def main():
    bars = base.daily_bars("SPY")
    _, net, _ = base.gex_series("SPY", bars)
    q = pd.read_parquet("data/cache/gex/SPY_short_expiry_quotes.parquet")
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    days = bars.index
    nxt = pd.Series(days[1:], index=days[:-1])
    q = q[q.trade_date.isin(nxt.index)]
    q = q[q.expiry == q.trade_date.map(nxt)]
    q = q[(q.ask >= q.bid) & (q.ask < 9999) & (q.bid >= 0)]
    q["mid"] = (q.bid + q.ask) / 2; q["ba"] = q.ask - q.bid
    q = q.sort_values("ba").drop_duplicates(["trade_date", "strike", "cp"], keep="first")

    rows = []
    for d, g in q.groupby("trade_date"):
        c = g[g.cp == "C"].set_index("strike").sort_index(); p = g[g.cp == "P"].set_index("strike").sort_index()
        ks = c.index.intersection(p.index)
        if not len(ks) or c.loc[ks].delta.isna().all() or d not in net.index:
            continue
        K = (c.loc[ks].delta - 0.5).abs().idxmin()
        smid = c.loc[K, "mid"] + p.loc[K, "mid"]
        if smid < MIN_MID:
            continue
        t = nxt[d]; S_t = bars.close.get(t, np.nan)
        if not np.isfinite(S_t):
            continue
        for w in WINGS:
            cw = c[(c.index > K) & (c.bid > 0)]; pw = p[(p.index < K) & (p.bid >= 0) & (p.ask > 0)]
            if cw.empty or pw.empty:
                continue
            kc = cw.index[np.abs(cw.index - (K + w * smid)).argmin()]
            kp = pw.index[np.abs(pw.index - (K - w * smid)).argmin()]
            if not (c.loc[kc, "ask"] > 0 and p.loc[kp, "ask"] > 0):
                continue
            short_leg = lambda r: r.mid - SLIP * r.ba
            long_leg = lambda r: r.mid + SLIP * r.ba
            credit = (short_leg(c.loc[K]) + short_leg(p.loc[K]) - long_leg(c.loc[kc]) - long_leg(p.loc[kp])) - 4 * COMM
            if credit <= 0:
                continue
            width = max(kc - K, K - kp)
            maxrisk = width - credit
            if maxrisk <= 0:
                continue
            pay = min(max(S_t - K, 0), kc - K) + min(max(K - S_t, 0), K - kp)
            pnl = credit - pay
            rows.append(dict(day=t, w=w, gex=net[d], credit=credit, maxrisk=maxrisk, width_c=kc - K, width_p=K - kp,
                             straddle_mid=smid, pnl_usd=pnl * 100, ret_risk=pnl / maxrisk * 100, ret_credit=pnl / credit * 100))
    X = pd.DataFrame(rows)
    X["NEG"] = X.gex < 0
    X["half"] = np.where(X.day < base.SPLIT, "2010-2017", "2018-2026")
    X["month"] = X.day.dt.to_period("M")
    print(f"SPY 1-day iron flies: {X.day.nunique():,} days; per wing width: {X.groupby('w').size().to_dict()}")

    out = []
    for w, gw in X.groupby("w"):
        for lab, g in [("POS", gw[~gw.NEG]), ("NEG", gw[gw.NEG]), ("ALL", gw)]:
            h1 = g[g.half == "2010-2017"].ret_risk; h2 = g[g.half == "2018-2026"].ret_risk
            mo = g.groupby("month").pnl_usd.sum()
            out.append(dict(w=w, gamma=lab, n=len(g), credit=g.credit.median(), width=((g.width_c + g.width_p) / 2).median(),
                            ret_risk=g.ret_risk.mean(), t=tstat(g.ret_risk), half1=h1.mean(), t1=tstat(h1), half2=h2.mean(), t2=tstat(h2),
                            ret_credit=g.ret_credit.mean(), win=(g.pnl_usd > 0).mean() * 100, usd_mean=g.pnl_usd.mean(),
                            worst_usd=g.pnl_usd.min(), pos_months=(mo > 0).mean() * 100,
                            longest_losing_days=streak((g.sort_values("day").pnl_usd < 0).tolist())))
    R = pd.DataFrame(out)
    print("\n== Iron butterfly, return on max risk at the real fill (%) ==")
    print(R.round(2).to_string(index=False))
    for w in WINGS:
        pos = R[(R.w == w) & (R.gamma == "POS")].iloc[0]; neg = R[(R.w == w) & (R.gamma == "NEG")].iloc[0]
        ok = pos.ret_risk > 0 and pos.t >= 3 and pos.half1 > 0 and pos.half2 > 0 and pos.ret_risk > neg.ret_risk
        print(f"PASS wings {w:.0f}x implied move: {'YES' if ok else 'no'}")
    print("\nby year, POS days, mean return on max risk (%):")
    X["yr"] = X.day.dt.year
    print(X[~X.NEG].pivot_table(index="w", columns="yr", values="ret_risk", aggfunc="mean").round(1).to_string())
    X.drop(columns="month").to_csv("data/studies/gex_spy_ironfly_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

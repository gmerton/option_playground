#!/usr/bin/env python3
"""
[WL-5c] Fixed-width "WiFly-style" 1-day SPY iron fly, gamma-gated vs ungated (pre-registered 2026-09-23; spec from
data/option_alpha/videos/2026-03-16_O2vTwL4R6kI/notes.md "Not tested, could be" #2, written before running).

Question: does Option Alpha's structure (a wide fly with fixed wings ~0.9% of spot, ~SPX 60 points) carry the same
gamma sort as our PASSING fly (wings 2x the implied move: POS gamma +5.8% on max risk, t 3.4; same fly every day 0.0%)?
His unfiltered WiFly went flat for months, which is what our "every day = 0.0%" predicts.

Engine: run_gex_spy_ironfly.py UNCHANGED except the wing rule -- same days (prior close -> next-day expiry), ATM strike
(call delta nearest 0.50), GEX sign (prior-day net, run_gex_regime_pin.gex_series), house fills (shorts at mid - 25% BA,
longs at mid + 25% BA, $0.0065/sh/leg), settle at the expiry-day close, return on max risk.
Wings: call wing = listed strike nearest K + 0.009 x S, put wing = nearest K - 0.009 x S (S = entry-day close).
ONE pre-registered cell (charged to the GEX family). PASS = POS-gamma mean > 0 with t >= 3, both halves (split 2018)
positive, and POS > NEG -- the engine's own rule. Report ALL days (the unfiltered WiFly) alongside.

Run: PYTHONPATH=src:. .venv/bin/python3 run_gex_wifly.py   (log -> data/studies/logs/gex_wifly.log)
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

import run_gex_regime_pin as base
from run_gex_spy_ironfly import COMM, MIN_MID, SLIP, streak, tstat

warnings.filterwarnings("ignore")
LOG = "data/studies/logs/gex_wifly.log"
WING_PCT = 0.009


def main():
    tk = "SPY"
    bars = base.daily_bars(tk)
    _, net, _ = base.gex_series(tk, bars)
    q = pd.read_parquet(f"data/cache/gex/{tk}_short_expiry_quotes.parquet")
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
        t = nxt[d]; S_t = bars.close.get(t, np.nan); S0 = bars.close.get(d, np.nan)
        if not (np.isfinite(S_t) and np.isfinite(S0)):
            continue
        cw = c[(c.index > K) & (c.bid > 0)]; pw = p[(p.index < K) & (p.bid >= 0) & (p.ask > 0)]
        if cw.empty or pw.empty:
            continue
        kc = cw.index[np.abs(cw.index - (K + WING_PCT * S0)).argmin()]
        kp = pw.index[np.abs(pw.index - (K - WING_PCT * S0)).argmin()]
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
        rows.append(dict(day=t, gex=net[d], credit=credit, maxrisk=maxrisk, wing_pct=100 * width / S0,
                         wing_vs_implied=width / smid, pnl_usd=pnl * 100, ret_risk=pnl / maxrisk * 100))
    X = pd.DataFrame(rows)
    X["NEG"] = X.gex < 0
    X["half"] = np.where(X.day < base.SPLIT, "2010-2017", "2018-2026")
    X["month"] = X.day.dt.to_period("M")
    print(f"SPY fixed-0.9% 1-day iron flies: {len(X):,} days {X.day.min().date()} -> {X.day.max().date()}; "
          f"median wing {X.wing_pct.median():.2f}% of spot = {X.wing_vs_implied.median():.2f}x the straddle mid")
    out = []
    for lab, g in (("POS", X[~X.NEG]), ("NEG", X[X.NEG]), ("ALL (unfiltered WiFly)", X)):
        h1 = g[g.half == "2010-2017"].ret_risk; h2 = g[g.half == "2018-2026"].ret_risk
        mo = g.groupby("month").pnl_usd.sum()
        out.append(dict(gamma=lab, n=len(g), credit=g.credit.median(), ret_risk=g.ret_risk.mean(), t=tstat(g.ret_risk),
                        half1=h1.mean(), t1=tstat(h1), half2=h2.mean(), t2=tstat(h2), win=(g.pnl_usd > 0).mean() * 100,
                        usd_mean=g.pnl_usd.mean(), worst_usd=g.pnl_usd.min(), pos_months=(mo > 0).mean() * 100,
                        longest_losing_days=streak((g.sort_values("day").pnl_usd < 0).tolist())))
    R = pd.DataFrame(out)
    print("\n== fixed-0.9% iron fly, return on max risk at the real fill (%) ==")
    print(R.round(2).to_string(index=False))
    pos, neg = R.iloc[0], R.iloc[1]
    ok = pos.ret_risk > 0 and pos.t >= 3 and pos.half1 > 0 and pos.half2 > 0 and pos.ret_risk > neg.ret_risk
    print(f"PASS (POS t >= 3, both halves > 0, POS > NEG): {'YES' if ok else 'no'}")
    ref = pd.read_csv("data/studies/gex_spy_ironfly_2026-09-21.csv", parse_dates=["day"])
    ref = ref[ref.w == 2.0]
    print("\nreference, our 2x-implied fly (same engine): POS "
          f"{ref[~ref.NEG].ret_risk.mean():+.2f}% (t {tstat(ref[~ref.NEG].ret_risk):+.2f}) | NEG {ref[ref.NEG].ret_risk.mean():+.2f}% "
          f"| ALL {ref.ret_risk.mean():+.2f}% (t {tstat(ref.ret_risk):+.2f})")
    X["yr"] = X.day.dt.year
    print("\nby year, mean return on max risk (%):")
    print(X.pivot_table(index="NEG", columns="yr", values="ret_risk", aggfunc="mean").round(1).to_string())
    X.drop(columns="month").to_csv("data/studies/gex_spy_wifly_2026-09-23.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

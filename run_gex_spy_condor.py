#!/usr/bin/env python3
"""SPY 1-day iron condor (16/5 delta) and put credit spread (16/5 delta) by dealer-gamma sign, vs the 2x iron fly (2026-09-21).
PRE-REGISTERED: data/studies/gex_spy_condor_putspread_2026-09-21.md. Same data/entry/fills as run_gex_spy_ironfly.py.
Usage: PYTHONPATH=src:. .venv/bin/python3 run_gex_spy_condor.py | tee data/studies/gex_spy_condor_putspread_2026-09-21.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
import run_gex_regime_pin as base
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
SLIP, COMM = 0.25, 0.0065
FLY = {"2010-2017": 7.72, "2018-2026": 5.39, "full": 5.82}


def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def near(df, target):
    d = df.dropna(subset=["delta"]); return None if d.empty else (d.delta - target).abs().idxmin()


def main():
    bars = base.daily_bars("SPY"); _, net, _ = base.gex_series("SPY", bars)
    q = pd.read_parquet("data/cache/gex/SPY_short_expiry_quotes.parquet")
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    nxt = pd.Series(bars.index[1:], index=bars.index[:-1])
    q = q[q.trade_date.isin(nxt.index)]; q = q[q.expiry == q.trade_date.map(nxt)]
    q = q[(q.ask >= q.bid) & (q.ask < 9999) & (q.bid >= 0) & (q.ask > 0)]
    q["mid"] = (q.bid + q.ask) / 2; q["ba"] = q.ask - q.bid
    q = q.sort_values("ba").drop_duplicates(["trade_date", "strike", "cp"], keep="first")
    sell = lambda r: r.mid - SLIP * r.ba; buy = lambda r: r.mid + SLIP * r.ba
    rows = []
    for d, g in q.groupby("trade_date"):
        if d not in net.index: continue
        S_t = bars.close.get(nxt[d], np.nan)
        if not np.isfinite(S_t): continue
        c = g[g.cp == "C"].set_index("strike").sort_index(); p = g[g.cp == "P"].set_index("strike").sort_index()
        ksp = near(p[p.bid > 0], -0.16)
        if ksp is not None:
            klp = near(p[(p.index < ksp)], -0.05)
            if klp is not None:
                cr = sell(p.loc[ksp]) - buy(p.loc[klp]) - 2 * COMM; width = ksp - klp
                if cr > 0 and width - cr > 0:
                    pnl = cr - min(max(ksp - S_t, 0), width)
                    rows.append(dict(day=nxt[d], struct="put spread 16/5", gex=net[d], credit=cr, maxrisk=width - cr, pnl_usd=pnl * 100, ret_risk=pnl / (width - cr) * 100))
                ksc = near(c[c.bid > 0], 0.16)
                if ksc is not None:
                    klc = near(c[c.index > ksc], 0.05)
                    if klc is not None:
                        cr2 = sell(p.loc[ksp]) + sell(c.loc[ksc]) - buy(p.loc[klp]) - buy(c.loc[klc]) - 4 * COMM
                        wmax = max(ksp - klp, klc - ksc)
                        if cr2 > 0 and wmax - cr2 > 0:
                            pay = min(max(ksp - S_t, 0), ksp - klp) + min(max(S_t - ksc, 0), klc - ksc)
                            pnl = cr2 - pay
                            rows.append(dict(day=nxt[d], struct="iron condor 16/5", gex=net[d], credit=cr2, maxrisk=wmax - cr2, pnl_usd=pnl * 100, ret_risk=pnl / (wmax - cr2) * 100))
    X = pd.DataFrame(rows); X["NEG"] = X.gex < 0
    X["half"] = np.where(X.day < base.SPLIT, "2010-2017", "2018-2026")
    out = []
    for s, gs in X.groupby("struct"):
        for lab, g in [("POS", gs[~gs.NEG]), ("NEG", gs[gs.NEG]), ("ALL", gs)]:
            h1, h2 = g[g.half == "2010-2017"].ret_risk, g[g.half == "2018-2026"].ret_risk
            out.append(dict(struct=s, gamma=lab, n=len(g), credit=g.credit.median(), maxrisk=g.maxrisk.median(), ret_risk=g.ret_risk.mean(), t=tstat(g.ret_risk),
                            half1=h1.mean(), t1=tstat(h1), half2=h2.mean(), t2=tstat(h2), win=(g.pnl_usd > 0).mean() * 100,
                            usd_mean=g.pnl_usd.mean(), worst_usd=g.pnl_usd.min(), pos_months=(g.groupby(g.day.dt.to_period("M")).pnl_usd.sum() > 0).mean() * 100))
    R = pd.DataFrame(out)
    print(f"reference, 2x iron fly on POS days: full {FLY['full']:+.2f}%  2010-17 {FLY['2010-2017']:+.2f}%  2018-26 {FLY['2018-2026']:+.2f}%\n")
    print(R.round(2).to_string(index=False))
    for s in R.struct.unique():
        r = R[(R.struct == s) & (R.gamma == "POS")].iloc[0]
        ok = r.ret_risk > 0 and r.t >= 3 and r.half1 > FLY["2010-2017"] and r.half2 > FLY["2018-2026"]
        print(f"PASS {s} (beats the 2x fly in both halves, t>=3): {'YES' if ok else 'no'}")
    X.to_csv("data/studies/gex_spy_condor_putspread_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

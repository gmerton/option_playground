#!/usr/bin/env python3
"""
UUP ATM short straddle, with costs + a test statistic (2026-09-22; the last untested Friday-screener entry).

The screener sells an ATM straddle on UUP every ~20 DTE cycle with a 50% profit take, max bid-ask 35% of mid,
Tier C, $2,000 allocation, on the strength of "+17.4% ROC, 73.1% win" from the March playbook -- priced at mid,
no statistic. UVXY and UVIX died the same way today (gross positive, net negative), and UUP is the thinnest chain
of the three, so the prior is bad.

Structure as the screener defines it: Friday entry, expiry closest to 20 DTE (15-30 accepted), sell the call and
put nearest the money (|delta| closest to 0.50), exit at 50% of the credit if the daily mid touches it, else hold
to expiry and settle at intrinsic. Spot from the chain (lib.studies.chain_spot), since v3 strikes are RAW.
Costs: sell at the BID, buy back at the ASK, $0.0065/share/leg/side; a leg that expires pays no exit cost.
Capital: Reg-T-ish naked-straddle margin approximated as 20% of spot x 100 per contract (the playbook's own basis),
so ROC is comparable to the screener's table.
t is month-clustered; halves split at the sample midpoint.

PRE-REGISTERED: net ROC > 0 with month-clustered t >= 2 and both halves positive, or the entry is retired like
UVXY/UVIX. k for the ledger = the playbook's delta x DTE search, ~12.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_uup_straddle_significance.py
"""
from __future__ import annotations
import os, warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.athena_lib import athena
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
CACHE = "data/cache/uup_chain.parquet"
COMM, TAKE = 0.0065, 0.50


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE): return pd.read_parquet(CACHE)
    sql = """
    SELECT trade_date, expiry, cp, strike, CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask,
           CAST(delta AS DOUBLE) d, CAST((bid_iv+ask_iv)/2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker = 'UUP' AND trade_date >= TIMESTAMP '2018-01-01 00:00:00'
      AND trade_date <= TIMESTAMP '2026-02-27 23:59:59'
      AND bid > 0 AND delta IS NOT NULL AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 40
    """
    df = athena(sql); df.to_parquet(CACHE, index=False); return df


d = pull()
d["trade_date"] = pd.to_datetime(d.trade_date).dt.normalize(); d["expiry"] = pd.to_datetime(d.expiry).dt.normalize()
d["ticker"] = "UUP"
SPOT = spot_from_chain(d[d.dte.between(5, 40)], delta="d")
marks = {(r.expiry, r.strike, r.cp, r.trade_date): (r.bid, r.ask) for r in d.itertuples()}
rows = []
for dt_, g in d[(d.trade_date.dt.weekday == 4) & d.dte.between(15, 30)].groupby("trade_date"):
    g = g.copy(); g["gap"] = (g.dte - 20).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[g.expiry == exp]
    c = g[g.cp == "C"]; p = g[g.cp == "P"]
    if c.empty or p.empty: continue
    ci = c.iloc[(c.d - 0.50).abs().argsort()[:1]].iloc[0]
    pi = p.iloc[(p.d + 0.50).abs().argsort()[:1]].iloc[0]
    if abs(ci.d - 0.5) > 0.12 or abs(abs(pi.d) - 0.5) > 0.12 or ci.strike != pi.strike: continue
    S = SPOT.get(("UUP", dt_), np.nan); ST = SPOT.get(("UUP", exp), np.nan)
    ba = (ci.ask - ci.bid) + (pi.ask - pi.bid); mid = (ci.bid + ci.ask + pi.bid + pi.ask) / 2
    if not np.isfinite(S) or mid <= 0 or ba / mid > 0.35: continue        # the screener's liquidity gate
    credit = (ci.bid + pi.bid) - 2 * COMM                                  # sold at the bid
    if credit <= 0: continue
    # daily path: 50% take if the straddle's mid falls to half the entry credit
    path = d[(d.expiry == exp) & (d.strike == ci.strike) & (d.trade_date > dt_) & (d.trade_date <= exp)]
    pv = path.pivot_table(index="trade_date", columns="cp", values=["bid", "ask"], aggfunc="last")
    exit_kind, pnl = "expiry", np.nan
    for td, r_ in pv.iterrows():
        try: m_ = (r_[("bid", "C")] + r_[("ask", "C")] + r_[("bid", "P")] + r_[("ask", "P")]) / 2
        except KeyError: continue
        if np.isfinite(m_) and m_ <= (1 - TAKE) * (credit + 2 * COMM):
            buy = r_[("ask", "C")] + r_[("ask", "P")] + 2 * COMM          # bought back at the ask
            pnl = credit - buy; exit_kind = "take"; break
    if not np.isfinite(pnl):
        if not np.isfinite(ST): continue
        pnl = credit - (abs(ST - ci.strike))                               # settles at intrinsic, no exit cost
    margin = 0.20 * S                                                      # per share; playbook's Reg-T basis
    rows.append(dict(date=dt_, expiry=exp, strike=float(ci.strike), S=S, ST=ST, credit=credit, pnl=pnl,
                     roc=pnl / margin, exit=exit_kind, ba_pct=ba / mid))
T = pd.DataFrame(rows)
if T.empty:
    print("no qualifying UUP straddles — the liquidity gate or the chain excludes them all"); raise SystemExit
T["month"] = T.date.dt.to_period("M")
mid_date = T.date.min() + (T.date.max() - T.date.min()) / 2
m = T.groupby("month").roc.mean()
t = m.mean() / (m.std(ddof=1) / sqrt(len(m)))
print(f"UUP ATM short straddle: {len(T)} trades, {T.date.min().date()}..{T.date.max().date()}, {T.month.nunique()} months")
print(f"  net ROC/trade {100*T.roc.mean():+.2f}%   month-weighted {100*m.mean():+.2f}%   t {t:+.2f}")
print(f"  win {100*(T.pnl>0).mean():.0f}%   take-profit exits {100*(T.exit=='take').mean():.0f}%   "
      f"median credit ${T.credit.median():.2f}/sh   median bid-ask {100*T.ba_pct.median():.0f}% of mid")
print(f"  halves: {100*T[T.date<mid_date].roc.mean():+.2f}% / {100*T[T.date>=mid_date].roc.mean():+.2f}%")
print("  by year:", {y: round(100 * g.roc.mean(), 1) for y, g in T.groupby(T.date.dt.year)})
print("PRE-REGISTERED PASS:", "YES" if (t >= 2 and T[T.date < mid_date].roc.mean() > 0 and T[T.date >= mid_date].roc.mean() > 0) else "NO")
T.to_csv("data/studies/uup_straddle_2026-09-22.csv", index=False)

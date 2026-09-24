#!/usr/bin/env python3
"""
Does PREMIUM-TO-WIDTH rank credit spreads? (2026-09-22, pre-registered here before the first run.)

OptionsPlay's credit-spread report (video YfrZT_kTo_4, 2026-07-25) ranks candidates by premium / width and sets a
floor of 2:1 risk-reward (credit >= 33% of width), preferring ~1.5:1 (credit >= 40%). His argument is the
break-even win rate: a 3:1 spread needs 75% wins to break even, a 1.5:1 needs 60%.

The prior from our own work (Ravish review, 2026-09-20): cost/width IS the risk-neutral loss probability, so
ranking by credit/width may be ranking how much risk you take, not how much edge you have -- the break-even win
rate and the actual win rate move together. It only works if credit/width proxies something real (implied richer
than realised).

DATA: the 20-name Friday chain cache (options_daily_v3, real bid/ask + greeks, 2018-01 -> 2026-01; corrected 2026-09-24,
this line said 18 names from 2019-10), RAW spot from
lib.studies.chain_spot, held to expiry.
ARM A (his ranking, structure held FIXED): the 30d/20d bull put on every name-date; quintile-sort by
   credit / width (credit = short bid - long ask - commissions, i.e. a real fill) and compare net ROC.
ARM B (the coordinate test): on the SAME name-date, build four widths from the same 30d short leg (wing at
   0.25/0.20/0.15/0.10 delta). Width changes credit/width mechanically. If his rule is an edge, the high
   credit/width variants should earn more net ROC; if it is a coordinate, they should be flat, and only the
   realised win rate should move with the break-even win rate.
PRE-REGISTERED PASS: in ARM A the top credit/width quintile beats the bottom by month-clustered t >= 2 with the
same sign in both halves (split 2022-07); in ARM B net ROC must rise monotonically with credit/width. Anything
else = his ranking is a risk coordinate, not a filter.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_premium_to_width.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
COMM = 0.0065
raw = pd.read_parquet("data/cache/ivrank_vehicle_chains.parquet")
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize()
raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.06 else None


rows = []
for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
    g = g.copy(); g["gap"] = (g.dte - 30).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[(g.expiry == exp) & (g.cp == "P")]
    short = pick(g, 0.30)
    if short is None: continue
    ST = SPOT.get((tk, exp), np.nan); S = SPOT.get((tk, d), np.nan)
    if not (np.isfinite(ST) and np.isfinite(S)): continue
    for wing_d in (0.25, 0.20, 0.15, 0.10):
        lng = pick(g, wing_d)
        if lng is None or lng.strike >= short.strike: continue
        width = short.strike - lng.strike
        credit = (short.bid - lng.ask) - 2 * COMM
        if credit <= 0 or credit >= width: continue
        loss = min(max(short.strike - ST, 0.0), width)
        rows.append(dict(sym=tk, date=d, expiry=exp, wing=wing_d, width=width, credit=credit,
                         cw=credit / width, roc=(credit - loss) / (width - credit),
                         win=(credit - loss) > 0, iv=float(short.iv), S=S, ST=ST))
T = pd.DataFrame(rows)
T["month"] = T.date.dt.to_period("M")
print(f"{len(T):,} spreads · {T.sym.nunique()} names · {T.date.nunique()} dates · {T.month.nunique()} months")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


print("\n== ARM A: his ranking, structure held fixed (30d/20d), quintiles of credit/width ==")
A = T[T.wing == 0.20].copy()
A["q"] = pd.qcut(A.cw, 5, labels=False, duplicates="drop")
tab = A.groupby("q").agg(n=("roc", "size"), cw=("cw", "mean"), net_roc=("roc", lambda x: 100 * x.mean()),
                         win=("win", lambda x: 100 * x.mean()), iv=("iv", "mean"))
tab["breakeven_win"] = 100 * (1 - tab.cw)          # what his arithmetic says you need
print(tab.round(2).to_string())
hi = A[A.q == A.q.max()]; lo = A[A.q == 0]
mh = hi.groupby("month").roc.mean(); ml = lo.groupby("month").roc.mean(); dd = (mh - ml).dropna()
h1 = dd[dd.index < pd.Period("2022-07", "M")]; h2 = dd[dd.index >= pd.Period("2022-07", "M")]
print(f"  top-bottom net ROC {100*dd.mean():+.2f}pp  t {mt(dd):+.2f}  halves {100*h1.mean():+.2f} / {100*h2.mean():+.2f}")
passA = abs(mt(dd)) >= 2 and np.sign(h1.mean()) == np.sign(h2.mean())

print("\n== ARM B: same date+name, only the wing moves (credit/width is dialled mechanically) ==")
B = T.groupby("wing").agg(n=("roc", "size"), cw=("cw", "mean"), net_roc=("roc", lambda x: 100 * x.mean()),
                          win=("win", lambda x: 100 * x.mean()), width=("width", "mean"))
B["breakeven_win"] = 100 * (1 - B.cw)
B["actual_minus_breakeven"] = B.win - B.breakeven_win
print(B.round(2).to_string())
monot = B.sort_values("cw").net_roc.is_monotonic_increasing
print(f"  net ROC monotone in credit/width? {monot}")
print("\nPRE-REGISTERED PASS:", "YES" if (passA and monot) else "NO",
      "-> his premium-to-width ranking is an edge" if (passA and monot) else "-> it is a risk coordinate, not a filter")
T.to_csv("data/studies/premium_to_width_2026-09-22.csv", index=False)

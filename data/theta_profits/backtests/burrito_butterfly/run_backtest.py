#!/usr/bin/env python3
"""
Mechanical EOD backtest of the Burrito Butterfly (Dan / Boomer Dan), SPX, 2-DTE. v2.

v1 marked legs at raw bid/ask on EOD snapshots -> deep-ITM quote asymmetry produced
impossible losses (>debit on a defined-risk fly). v2 fixes valuation:
  - mark pre-expiry at MID,
  - SETTLE at intrinsic using real SPX spot (^GSPC) -> losses correctly bounded by debit,
  - model costs explicitly: commission $0.65/leg + slippage = SLIP_FRAC x quoted spread/leg,
    paid at entry (and at early exit); expiry is cash-settled (no spread cost).

Bullish, call-based (his stated default). Always-long benefits from SPX drift, so the
real question is the head-to-head vs the structure's own parts (FLY, SPREAD) which share
that drift. Structures (ATM K = call delta ~0.50, rounded to 5):
  A_FLY     +C(K-15) -2C(K) +C(K+15)
  B_BURRITO +C(K-15) -2C(K) +2C(K+15) -C(K+20)     (fly + upper 5-wide call spread; our reading)
  C_SPREAD  +C(K) -C(K+5)
"""
from __future__ import annotations
import sys, pandas as pd, numpy as np

SCRATCH = "/private/tmp/claude-501/-Users-gmerton-v2-options-playground/b713dd7e-1183-4b1a-9089-64cbc98849d6/scratchpad"
COMMISSION = 0.65 / 100.0      # $/share/leg
SLIP_FRAC  = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
STOP   = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10

df = pd.read_parquet(f"{SCRATCH}/spx_shortdte_calls.parquet")
df = df[(df.bid >= 0) & (df.ask > 0) & (df.ask >= df.bid)].copy()
df['strike'] = df.strike.astype(float)
df['mid'] = (df.bid + df.ask) / 2
df['spread'] = df.ask - df.bid
spot = pd.read_parquet(f"{SCRATCH}/spx_spot.parquet")['spx'].to_dict()

q = df.set_index(['expiry', 'strike', 'trade_date'])[['mid', 'spread']].sort_index()
exp_dates = {ex: sorted(g.trade_date.unique()) for ex, g in df.groupby('expiry')}

def leg(ex, k, td):
    try:
        r = q.loc[(ex, k, td)]
    except KeyError:
        return None
    if isinstance(r, pd.DataFrame): r = r.iloc[0]
    return float(r.mid), float(r.spread)

def mark_mid(legs, ex, td):
    v = 0.0
    for k, qty in legs.items():
        l = leg(ex, k, td)
        if l is None: return None
        v += qty * l[0]
    return v

def slip_cost(legs, ex, td):
    c = 0.0
    for k, qty in legs.items():
        l = leg(ex, k, td)
        if l is None: return None
        c += (SLIP_FRAC * l[1] + COMMISSION) * abs(qty)
    return c

def intrinsic(legs, S):
    return sum(qty * max(0.0, S - k) for k, qty in legs.items())

def structures(K):
    return {'A_FLY': {K-15:+1, K:-2, K+15:+1},
            'B_BURRITO': {K-15:+1, K:-2, K+15:+2, K+20:-1},
            'C_SPREAD': {K:+1, K+5:-1}}

entries = df[df.dte == 2][['trade_date', 'expiry']].drop_duplicates()
hold, managed = {n: [] for n in ['A_FLY','B_BURRITO','C_SPREAD']}, {n: [] for n in ['A_FLY','B_BURRITO','C_SPREAD']}

for _, e in entries.iterrows():
    td0, ex = e.trade_date, e.expiry
    if ex not in spot: continue
    chain = df[(df.expiry == ex) & (df.trade_date == td0)].dropna(subset=['delta'])
    if chain.empty: continue
    K = round(chain.iloc[(chain.delta - 0.5).abs().argmin()].strike / 5) * 5
    inter = [d for d in exp_dates[ex] if td0 < d < ex]   # EOD marks before expiry
    for name, legs in structures(K).items():
        em = mark_mid(legs, ex, td0); es = slip_cost(legs, ex, td0)
        if em is None or es is None or em <= 0: continue
        cost = em + es           # what you actually pay (mid + slippage + commission)
        risk = cost
        settle = intrinsic(legs, spot[ex])    # cash settle at expiry intrinsic
        # --- hold-to-expiry (clean structural EV) ---
        hold[name].append({'date': td0, 'risk': risk, 'pnl': settle - cost})
        # --- managed: check each intermediate EOD for target/stop, else settle ---
        ex_pnl, reason = settle - cost, 'expiry'
        for td2 in inter:
            mm = mark_mid(legs, ex, td2); sc = slip_cost(legs, ex, td2)
            if mm is None or sc is None: continue
            pnl_close = (mm - sc) - cost
            if pnl_close >= TARGET * risk: ex_pnl, reason = pnl_close, 'target'; break
            if pnl_close <= -STOP * risk: ex_pnl, reason = pnl_close, 'stop'; break
        managed[name].append({'date': td0, 'risk': risk, 'pnl': ex_pnl, 'reason': reason})

def report(title, res):
    print(f"\n=== {title} ===")
    print(f"{'structure':12}{'n':>5}{'win%':>7}{'meanP&L$':>10}{'medP&L$':>9}{'EV%risk':>9}{'worst$':>9}{'best$':>9}{'avgRisk$':>9}")
    for name, rows in res.items():
        if not rows: continue
        d = pd.DataFrame(rows); p = d.pnl * 100
        print(f"{name:12}{len(d):>5}{(d.pnl>0).mean()*100:>6.1f}%{p.mean():>10.2f}{p.median():>9.2f}"
              f"{d.pnl.div(d.risk).mean()*100:>8.1f}%{p.min():>9.0f}{p.max():>9.0f}{d.risk.mean()*100:>9.0f}")

print("SPX 2-DTE bullish | mid marks + intrinsic settle | cost = $0.65/leg + 25% of spread/leg")
report("HOLD TO EXPIRY (clean structural EV)", hold)
report(f"MANAGED (target +{TARGET*100:.0f}% / stop -{STOP*100:.0f}% at intermediate EOD)", managed)
b = pd.DataFrame(managed['B_BURRITO'])
if len(b): print("\nB_BURRITO managed exit reasons:", b.reason.value_counts().to_dict())

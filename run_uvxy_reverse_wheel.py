#!/usr/bin/env python3
"""
UVXY reverse wheel — sell 50Δ call, accept assignment (short 100 shares), then
write a put, repeat. Tests whether UVXY's structural decay can be harvested this way.

TWO PUT-STRIKE VARIANTS (the difference turns out to matter enormously):
  A  put struck at the SHORT BASIS (as specified). If assigned you buy back at the
     same price you shorted, so SHARE P&L IS ZERO BY CONSTRUCTION — all profit is
     premium, and the share leg contributes only drawdown.
  B  put struck at the current 50Δ (a normal wheel roll). Assignment covers BELOW
     the short basis, so the share leg actually captures the decay.

Spot is derived per date via put-call parity from the option chain itself. UVXY's
Tradier prices are not on the same scale as historical Athena strikes (reverse-split
adjustment), which is why other UVXY studies avoid underlying prices entirely —
parity sidesteps that.

Reverse splits are applied to the live short position (shares /= r, basis *= r):
  2018-09-18 1:5 · 2021-05-26 1:10 · 2023-06-23 1:10 · 2024-04-11 1:5 · 2025-11-20 1:5

NOT MODELLED — read before believing any number:
  * borrow cost (swept: 0% / 5% / 15% annualised on short notional)
  * early assignment (American style; bites exactly when it hurts)
  * margin calls (a spike can force covering at the worst price)

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_uvxy_reverse_wheel.py
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from lib.constants import DB, TABLE

START, END = date(2018, 1, 12), date(2026, 2, 20)   # post 1.5x leverage change
DTE_TGT, DTE_TOL = 20, 6
CALL_DELTA = 0.50
SPLITS = {date(2018,9,18):5, date(2021,5,26):10, date(2023,6,23):10,
          date(2024,4,11):5, date(2025,11,20):5}


def fetch() -> pd.DataFrame:
    d = athena(f"""
        SELECT trade_date, expiry, strike, cp, bid, ask, delta
        FROM "{DB}"."{TABLE}"
        WHERE ticker='UVXY' AND bid>0 AND ask>0
          AND trade_date >= TIMESTAMP '{START} 00:00:00'
          AND trade_date <= TIMESTAMP '{END} 00:00:00'
    """)
    d["trade_date"] = pd.to_datetime(d.trade_date).dt.date
    d["expiry"] = pd.to_datetime(d.expiry).dt.date
    for c in ("strike","bid","ask","delta"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["mid"] = (d.bid + d.ask) / 2.0
    return d


def spot_series(d: pd.DataFrame) -> dict:
    piv = d.pivot_table(index=["trade_date","expiry","strike"], columns="cp",
                        values="mid", aggfunc="first")
    if not {"C","P"}.issubset(piv.columns):
        return {}
    piv = piv.dropna(subset=["C","P"]).reset_index()
    piv["S"] = piv.strike + piv.C - piv.P
    piv["gap"] = (piv.C - piv.P).abs()
    out = {}
    for dt, g in piv.groupby("trade_date"):
        n = g.nsmallest(8, "gap")
        if len(n) >= 3:
            out[dt] = float(n.S.median())
    return out


def run(d: pd.DataFrame, spots: dict, variant: str, borrow: float) -> dict:
    dates = sorted(spots)
    by_date = {dt: g for dt, g in d.groupby("trade_date")}
    cash, shares, basis = 0.0, 0, 0.0     # shares NEGATIVE when short
    i, log, splits_hit = 0, [], 0
    peak, maxdd = 0.0, 0.0

    while i < len(dates):
        today = dates[i]
        chain = by_date.get(today)
        if chain is None:
            i += 1; continue
        S = spots[today]
        cand = chain[(chain.expiry - today).map(lambda x: abs(x.days - DTE_TGT)) <= DTE_TOL]
        if cand.empty:
            i += 1; continue
        exp = min(cand.expiry.unique(), key=lambda e: abs((e - today).days - DTE_TGT))
        leg_chain = chain[chain.expiry == exp]

        if shares == 0:                                   # FLAT -> sell a call
            calls = leg_chain[(leg_chain.cp=="C") & leg_chain.delta.notna()]
            if calls.empty: i += 1; continue
            leg = calls.loc[(calls.delta - CALL_DELTA).abs().idxmin()]
            K, prem, side = float(leg.strike), float(leg.mid), "call"
        else:                                             # SHORT -> sell a put
            puts = leg_chain[(leg_chain.cp=="P") & leg_chain.delta.notna()]
            if puts.empty: i += 1; continue
            if variant == "A":
                leg = puts.loc[(puts.strike - basis).abs().idxmin()]
            else:
                leg = puts.loc[(puts.delta + CALL_DELTA).abs().idxmin()]
            K, prem, side = float(leg.strike), float(leg.mid), "put"

        cash += prem * 100                                # collect premium

        # carry the position to expiry, applying splits and borrow along the way
        j = i
        while j < len(dates) and dates[j] < exp:
            nxt = dates[j+1] if j+1 < len(dates) else exp
            if shares < 0:
                cash -= abs(shares) * spots[dates[j]] * borrow / 365.0 * max((nxt-dates[j]).days,0)
            for sd, r in SPLITS.items():
                if dates[j] < sd <= nxt and shares != 0:
                    shares = int(shares / r); basis *= r; splits_hit += 1
            j += 1
        ST = spots.get(exp)
        if ST is None:
            i = j + 1; continue

        if side == "call" and ST > K:                     # assigned short
            shares, basis = -100, K
        elif side == "put" and ST < K:                    # assigned long -> covers
            cash += (basis - K) * 100                     # realise share P&L
            shares, basis = 0, 0.0
            if side == "put" and variant == "A":
                pass                                      # basis==K so this is 0 by design

        equity = cash + (shares * (ST - basis) if shares else 0.0)
        peak = max(peak, equity); maxdd = min(maxdd, equity - peak)
        log.append(dict(date=exp, side=side, K=K, prem=prem, ST=ST,
                        shares=shares, basis=basis, cash=cash, equity=equity))
        i = j + 1

    L = pd.DataFrame(log)
    return dict(variant=variant, borrow=borrow, cycles=len(L), splits=splits_hit,
                final=cash + (shares*(spots[dates[-1]]-basis) if shares else 0),
                cash=cash, maxdd=maxdd,
                pct_short=(L.shares < 0).mean()*100 if len(L) else np.nan, log=L)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()
    print("fetching UVXY chains ...")
    d = fetch()
    spots = spot_series(d)
    print(f"  {len(d):,} rows, parity spot on {len(spots)} dates "
          f"({min(spots)} -> {max(spots)})")

    print(f"\n{'='*96}")
    print(f"  REVERSE WHEEL — 1 contract / 100 shares, {DTE_TGT} DTE legs, 2018-01→2026-02")
    print(f"{'='*96}")
    print(f"  {'variant':<40}{'borrow':>8}{'cycles':>8}{'final $':>12}{'max DD $':>12}{'% short':>9}")
    print("  " + "-"*94)
    rows = []
    for v, lab in [("A","A  put @ short basis (as specified)"),
                   ("B","B  put @ 50Δ (normal wheel roll)")]:
        for b in [0.0, 0.05, 0.15]:
            r = run(d, spots, v, b); rows.append(r)
            print(f"  {lab if b==0 else '':<40}{b*100:>7.0f}%{r['cycles']:>8}"
                  f"{r['final']:>12,.0f}{r['maxdd']:>12,.0f}{r['pct_short']:>8.1f}%")
        print("  " + "-"*94)

    best = [r for r in rows if r["variant"]=="B" and r["borrow"]==0.0][0]
    L = best["log"].copy(); L["yr"] = pd.to_datetime(L.date).dt.year
    print(f"\n  === variant B, 0% borrow — equity by year ===")
    print(f"  {'yr':<6}{'cycles':>8}{'premium+share $':>18}{'end equity $':>15}")
    prev = 0.0
    for y, g in L.groupby("yr"):
        end = g.equity.iloc[-1]
        print(f"  {y:<6}{len(g):>8}{end-prev:>18,.0f}{end:>15,.0f}"); prev = end
    if a.csv:
        best["log"].to_csv("uvxy_reverse_wheel.csv", index=False)
        print("\n  saved -> uvxy_reverse_wheel.csv")


if __name__ == "__main__":
    main()

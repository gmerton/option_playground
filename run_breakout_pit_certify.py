#!/usr/bin/env python3
"""
Certify or kill the house breakout on a POINT-IN-TIME universe (pre-registered 2026-09-30, committed BEFORE the run).

WHY. The 9/25 audit downgraded the precision-tier breakout to "uncertified selection, regime-dependent": its only cell
over the bar (+0.44R t 3.52 vs a random other name) ran on a 2026-SURVIVOR panel, and 2024-26 carry ~87% of R. The
settling test named there: a point-in-time universe, control = same-date NON-tier breakouts, per-year paired edge.
Gabe 2026-09-30: test 2 of 3.

DEVIATION FROM THE AUDIT SPEC (declared now). The audit named chain_spot, but that series is CLOSE-ONLY: the tier needs
highs, lows and share volume (ADR, 15-day-high pivot, RVOL, upper-half close). Used instead: the point-in-time S&P 500
(run_sleeping_giants_sp500: 2026-06 constituents with the Wikipedia change log reverse-applied; yfinance adjusted
H/L/C/V 2008 -> 2025-07-14 incl. removed names yfinance still returns; coverage REPORTED). A name is eligible on a date
only if it was a member that day. Consequences: large caps only (ADR >= 3 is a minority of member-days), and the
GAP < 5% gate is DROPPED (no open in the cache; 0/9 gates earned their place in the 9/24 ablation, so this is minor).

DEFINITIONS (run_precision_tier_control.build, minus GAP):
  base breakout  member & ADDV >= $50M & px >= $5 & ADR20 >= 3 & 52wk range >= 17% & close >= prior 15-day high (first
                 cross) & RVOL >= 1.1 & close in the upper half of the day & EMA stack >= 5 sessions & day change < 8%
  TIER           base & ADR 4-7 & within 15% of the 52wk high & stack 5-40 sessions
  NON-TIER       base & not TIER
  process        house: entry at the signal CLOSE (+10 bp), stop = the day's low floored at 2% below the close, judged
                 on the close; exit on the first close < EMA20; max 60 sessions; -10 bp. METRIC = % per trade (R second).
PRIMARY    TIER minus NON-TIER, same date (dates with >= 1 of each), t on date means.
BAR        diff > 0, t >= 3, both halves (split 2018-01-01) > 0, majority of years > 0 -> CERTIFIED selection.
           |t| < 3 -> NULL: the tier adds nothing to a plain breakout on a PIT universe.
SECONDARY  (a) TIER vs 3 random same-date members (any, same process, their own day-low stop) -- the audit's original
           +0.44R cell re-run point-in-time; (b) base breakout vs 3 random members; (c) 2023+ vs before (the tier is a
           regime finding); (d) the same PRIMARY in R.
Window: signals 2010-01-01 -> 2025-04-15 (60-session room). Local.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_breakout_pit_certify.py  (log -> data/studies/logs/breakout_pit_certify.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from types import SimpleNamespace

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
import run_sleeping_giants_sp500 as sg

REPO = sg.REPO
LOG = REPO / "data/studies/logs/breakout_pit_certify.log"
START, END, SPLIT, SLIP, HOLD, SEED = "2010-01-01", "2025-04-15", "2018-01-01", 0.0010, 60, 20260930


def panel():
    px = pd.read_parquet(sg.PX_CACHE)
    px["date"] = pd.to_datetime(px.date)
    pv = lambda c: px.pivot_table(index="date", columns="ticker", values=c).sort_index()
    H, L, C, V = pv("High"), pv("Low"), pv("Close"), pv("Volume")
    cur, changes = sg.membership()
    mem = pd.DataFrame(False, index=C.index, columns=C.columns)
    for d in C.index[C.index >= "2009-01-01"]:
        m = sg.members_on(cur, changes, d)
        mem.loc[d, [t for t in C.columns if t in m]] = True
    return H, L, C, V, mem


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def main():
    H, L, C, V, mem = panel()
    ever = mem.any()
    print(f"# PIT breakout certification; tickers with prices {C.shape[1]}, ever-members w/ prices {int(ever.sum())}")
    cur, changes = sg.membership()
    cov = [len(set(C.columns) & sg.members_on(cur, changes, d)) / max(1, len(sg.members_on(cur, changes, d)))
           for d in pd.date_range("2010-06-30", "2025-06-30", freq="YE")]
    print("member coverage with prices, year-ends 2010..2024: " + " ".join(f"{c:.0%}" for c in cov))
    dolvol = (C * V).shift(1).rolling(20).mean()
    elig = mem & (dolvol >= 50e6) & (C >= 5)
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max()
    rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan)
    chg = C.pct_change(fill_method=None)
    stack = stack_run(C, adr=adr)
    off52 = (C / hi52 - 1) * 100
    base = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv15) & (C.shift(1) < piv15) & (rvol >= 1.1) & (pos >= 0.5)
            & (stack >= 5) & (chg < 0.08)).fillna(False)
    tier = (base & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack <= 40)).fillna(False)
    base.loc[(base.index < START) | (base.index > END)] = False
    tier.loc[(tier.index < START) | (tier.index > END)] = False
    Cv, Lv, E = C.values, L.values, C.ewm(span=20, adjust=False).mean().values
    n = len(Cv)

    def trade(i, j):
        e = Cv[i, j]
        if not np.isfinite(e) or not np.isfinite(Lv[i, j]) or i + 1 >= n:
            return None
        stop = min(Lv[i, j], e * 0.98)
        x = np.nan
        for k in range(i + 1, min(i + 1 + HOLD, n)):
            c = Cv[k, j]
            if not np.isfinite(c):
                continue
            x = c
            if c < stop or (np.isfinite(E[k, j]) and c < E[k, j]):
                break
        if not np.isfinite(x):
            return None
        r = 100 * (x * (1 - SLIP) / (e * (1 + SLIP)) - 1)
        return r, float(np.clip(r / (100 * (e - stop) / e), -20, 20))

    rng = np.random.default_rng(SEED)
    EL, B, T = elig.fillna(False).values, base.values, tier.values
    rows = []
    for i, j in zip(*np.where(B)):
        t = trade(i, j)
        if t is None:
            continue
        pool = np.flatnonzero(EL[i] & ~B[i])
        cs = [trade(i, int(c)) for c in rng.choice(pool, size=min(3, len(pool)), replace=False)] if len(pool) else []
        cs = [c for c in cs if c is not None]
        rows.append(dict(date=C.index[i], sym=C.columns[j], tier=bool(T[i, j]), ret=t[0], R=t[1],
                         cret=np.mean([c[0] for c in cs]) if cs else np.nan, cR=np.mean([c[1] for c in cs]) if cs else np.nan))
    D = pd.DataFrame(rows)
    print(f"base breakouts {len(D):,} ({D.sym.nunique()} names), TIER {int(D.tier.sum()):,}; "
          f"{D.date.min().date()} -> {D.date.max().date()}")

    def paired(col):
        g = D.groupby(["date", "tier"])[col].mean().unstack("tier").dropna()
        d = g[True] - g[False]
        yr = d.groupby(d.index.year).agg(["size", "mean"]).round(2)
        return dict(dates=len(d), tier=g[True].mean(), non=g[False].mean(), diff=d.mean(), t=tstat(d),
                    h1=d[d.index < SPLIT].mean(), h2=d[d.index >= SPLIT].mean(),
                    yrs=f"{int((yr['mean'] > 0).sum())}/{len(yr)}", share=(yr['mean'] > 0).mean(), _yr=yr, _d=d)

    P = paired("ret")
    print("\n## PRIMARY: TIER - NON-TIER breakouts, same date, % per trade")
    print(f"dates {P['dates']} | TIER {P['tier']:+.2f}% vs NON-TIER {P['non']:+.2f}% | diff {P['diff']:+.2f}pp "
          f"t {P['t']:+.2f} | halves {P['h1']:+.2f}/{P['h2']:+.2f} | yrs+ {P['yrs']}")
    ok = P["diff"] > 0 and P["t"] >= 3 and P["h1"] > 0 and P["h2"] > 0 and P["share"] > .5
    print(f"BAR: {'PASS -> CERTIFIED selection' if ok else 'FAIL'}")
    print("per year (dates, mean diff pp):\n" + P["_yr"].T.to_string())
    PR = paired("R")
    print(f"(d) same in R: TIER {PR['tier']:+.3f} vs NON {PR['non']:+.3f} | diff {PR['diff']:+.3f} t {PR['t']:+.2f} "
          f"| halves {PR['h1']:+.3f}/{PR['h2']:+.3f}")
    d = P["_d"]
    print(f"(c) regime: before 2023 diff {d[d.index < '2023-01-01'].mean():+.2f} t {tstat(d[d.index < '2023-01-01']):+.2f}"
          f" | 2023+ diff {d[d.index >= '2023-01-01'].mean():+.2f} t {tstat(d[d.index >= '2023-01-01']):+.2f}")
    print("\n## SECONDARY: vs 3 random same-date members (same process)")
    for lab, m in (("(a) TIER", D.tier), ("(b) all base breakouts", pd.Series(True, index=D.index))):
        X = D[m.values].dropna(subset=["cret"])
        for col, cc in (("ret", "cret"), ("R", "cR")):
            x = (X[col] - X[cc]).groupby(X.date).mean()
            print(f"  {lab:24s} {col:3s}: n {len(X):5d} | signal {X[col].mean():+.3f} vs random {X[cc].mean():+.3f} | "
                  f"edge {x.mean():+.3f} t {tstat(x):+.2f} | halves {x[x.index < SPLIT].mean():+.3f}/"
                  f"{x[x.index >= SPLIT].mean():+.3f}")
    D.to_csv(REPO / "data/studies/logs/breakout_pit_certify_trades.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

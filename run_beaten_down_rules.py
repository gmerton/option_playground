#!/usr/bin/env python3
"""
A second rule set for BEATEN-DOWN names on the rise (pre-registered 2026-09-24, before the first run; Gabe: "consider a
second set of rules for stocks that are badly beaten down and on the rise ... the bitcoin names surged ... Martin and
Tito would both look at stocks with very long bases, as a start").

WHAT IS ALREADY ANSWERED: crash-leader study (buying deep drawdowns = regime bet, veto in a healthy tape); EP out of a
long base (earnings gap) NULL; Sleeping Giants (multi-year base, LEAP vehicle, large caps) MARGINAL; industry rotation
(bottom-3 sectors beat top-3, t 2.6, but not front-runnable); weak-tape leaders NULL. NEW AXES: (1) a STOCK rule for the
break of a long base in a beaten-down name; (2) a GROUP washout-rebound rule. Forensics that motivated (2):
data/studies/logs/crypto_breakout_forensics_2026-09-24.log -- the Aug-2026 crypto surge came from a median -54% drawdown,
below the 200-day, with NO base breakout (2 of 17 broke a 6-month high); the group signal was its equal-weight index
reclaiming the 50-day with in-group breadth (% > 20 EMA) jumping from ~25% to ~65%. One episode = a hypothesis only.

TEST 1 -- LONG-BASE BREAKOUT (Tito: completed downtrend -> basing -> break on volume with the SMAs stacked; Luk: long
  base, EMAs clustered, higher lows). Pattern harness, liquid_panel_2009, signals 2012 ->.
  beaten    close <= 0.70 x the prior 756-session (3-year) high.
  base      the prior 126-session (6-month) high was set >= 60 sessions ago (no new 6-month high for 3+ months).
  trigger   FIRST close above that 126-session high; RVOL >= 1.5 (50d); close in the upper half; ADR >= 3; eligible;
            10 > 20 > 50 stack running >= 5 sessions (house slack).
  process   harness, entry_at="close", stop = signal-day low, hold 60; controls "post" (timing) and "xname" (selection).
  bar       the harness bar: paired edge t >= 3 on the best arm, both halves > 0, p_search < 0.003.
  vs tier   descriptive: the same trades' ema20 R next to the precision tier's.

TEST 2 -- GROUP WASHOUT REBOUND (the crypto pattern; Luk: "out-of-favor groups ... shakeout-and-reclaim").
  groups    industries in data/ticker_industry_map.csv with >= 6 eligible names that day.
  washed    median member close <= 0.60 x its prior 252-session high (>= 40% down).
  thrust    the group equal-weight index closes above its 50-day SMA for the first time in >= 40 sessions AND
            >= 60% of members close above their 20 EMA (<= 35% did at some point in the prior 10 sessions).
  entry     every eligible member at that close, equal weight; one episode per group per 60 sessions.
  outcome   forward 20 / 40-session return of the member basket, minus (a) the same-date ADR-matched field and
            (b) the same group's basket from a random LATER session within 20 (post control).
  PRIMARY   40-session ADR-matched excess per episode, t across episodes; bar t >= 3, both halves (2018-01) > 0.
  regime    split by market breadth at entry (% of eligible names above the 50 SMA < 40 vs >= 40) -- the crash-leader
            result predicts it pays only in a broken tape.
  caveat    survivor panel (flatters rebounds of names that survived); the industry map is as of 2026.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_beaten_down_rules.py   (log -> data/studies/logs/beaten_down_rules.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/beaten_down_rules.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")
RNG = np.random.default_rng(20260924)


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    raw = pd.read_parquet(REPO / PANEL)
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    Vol = raw.pivot(index="date", columns="ticker", values="volume").sort_index()
    P = pt.load_panel(PANEL)
    # drop partial panel days (tail rows with a handful of names)
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    for f in ("open", "high", "low", "close", "adr", "elig", "ema20"):
        setattr(P, f, getattr(P, f).loc[keep])
    Vol = Vol.reindex(P.close.index)
    C, H, L, A, E = P.close, P.high, P.low, P.adr, P.elig.fillna(False)
    out = []
    pr = out.append

    # ── TEST 1: long-base breakout ───────────────────────────────────────────
    def long_base(P):
        hi3y = H.shift(1).rolling(756, min_periods=500).max()
        hi126 = H.shift(1).rolling(126, min_periods=120).max()
        age = H.shift(1).rolling(126, min_periods=120).apply(lambda x: 125 - int(np.argmax(x)), raw=True)
        rvol = Vol / Vol.shift(1).rolling(50).mean()
        pos = (C - L) / (H - L).replace(0, np.nan)
        sd = stack_run(C, adr=A)
        first = (C > hi126) & (C.shift(1) <= hi126.shift(1))
        hit = (E & (C <= 0.70 * hi3y) & (age >= 60) & first & (rvol >= 1.5) & (pos >= 0.5) & (A >= 3) & (sd >= 5))
        return pt.daily_signals(hit, stop=L, side="long", since="2012-01-01")

    for ctl in ("post", "xname"):
        buf = __import__("io").StringIO()
        real = sys.stdout; sys.stdout = buf
        try:
            tab = pt.run_daily(f"long-base breakout (beaten >=30% off 3y high) [{ctl}]", long_base, hold=60,
                               entry_at="close", control=ctl, panel=P, split="2018-01-01",
                               note="Gabe 9/24 second rule set; Tito/Luk long base")
        finally:
            sys.stdout = real
        pr(f"\n# TEST 1 -- LONG-BASE BREAKOUT, control = {ctl}\n" + buf.getvalue())

    # ── TEST 2: group washout rebound ────────────────────────────────────────
    im = pd.read_csv(REPO / "data/ticker_industry_map.csv").set_index("ticker").industry
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    dd = C / hi252
    e20 = C.ewm(span=20, adjust=False).mean()
    above20 = (C > e20)
    ret = C.pct_change(fill_method=None)
    sma50m = C.rolling(50).mean()
    breadth = 100 * ((C > sma50m) & E).sum(axis=1) / (E & sma50m.notna()).sum(axis=1)
    F20, F40 = (C.shift(-20) / C - 1) * 100, (C.shift(-40) / C - 1) * 100
    band = pd.DataFrame(np.select([(A >= lo) & (A < hi) for lo, hi in BANDS], range(len(BANDS)), -1),
                        index=A.index, columns=A.columns)

    def field_excess(i, members, Fw):
        d = C.index[i]
        fw, e, bd = Fw.loc[d], E.loc[d], band.loc[d]
        ok = e & fw.notna()
        mem = ok & ok.index.isin(members)
        fld = ok & ~ok.index.isin(members)
        ex = []
        for k in range(len(BANDS)):
            a, b = fw[mem & (bd == k)], fw[fld & (bd == k)]
            if len(a) and len(b) >= 10:
                ex.append((a - b.mean()).values)
        return np.concatenate(ex).mean() if ex else np.nan

    rows = []
    idx = C.index
    for g, mem in im.groupby(im):
        m = [t for t in mem.index if t in C.columns]
        if len(m) < 6:
            continue
        Eg = E[m]
        cnt = Eg.sum(axis=1)
        gret = ret[m].where(Eg).mean(axis=1).fillna(0)
        gi = (1 + gret).cumprod()
        g50 = gi.rolling(50).mean()
        above_g50 = gi > g50
        first50 = above_g50 & ~above_g50.shift(1).rolling(40, min_periods=40).max().fillna(1).astype(bool)
        med_dd = dd[m].where(Eg).median(axis=1)
        pct20 = 100 * (above20[m] & Eg).sum(axis=1) / cnt.replace(0, np.nan)
        was_low = pct20.shift(1).rolling(10).min() <= 35
        sig = (cnt >= 6) & (med_dd <= 0.60) & first50 & (pct20 >= 60) & was_low
        last = -10 ** 9
        for d in sig[sig].index:
            i = idx.get_loc(d)
            if d < pd.Timestamp("2011-01-01") or i - last < 60 or i + 40 >= len(idx):
                continue
            last = i
            members = [t for t in m if Eg.loc[d, t]]
            j = min(i + int(RNG.integers(5, 21)), len(idx) - 41)          # post control: a random later session
            rows.append(dict(group=g, date=d.date(), n=len(members), med_dd=round(100 * (med_dd[d] - 1), 1),
                             breadth=round(breadth[d], 1),
                             raw20=F20.loc[d, members].mean(), raw40=F40.loc[d, members].mean(),
                             ex20=field_excess(i, members, F20), ex40=field_excess(i, members, F40),
                             post40=F40.loc[idx[j], members].mean()))
    G = pd.DataFrame(rows)
    G.to_csv(REPO / "data/studies/beaten_down_group_rebound_2026-09-24.csv", index=False)
    pr("\n# TEST 2 -- GROUP WASHOUT REBOUND")
    pr(f"episodes {len(G)} ({G.group.nunique()} groups), 2011 -> {G.date.max()}")
    x = G.ex40.dropna(); dts = pd.to_datetime(G.date)
    h1 = G.ex40[dts < SPLIT].dropna(); h2 = G.ex40[dts >= SPLIT].dropna()
    pr(f"PRIMARY 40d ADR-matched excess: {x.mean():+.2f}pp (median {x.median():+.2f}), t {tstat(x):+.2f}, "
       f"{100 * (x > 0).mean():.0f}% +, halves {h1.mean():+.2f} (n {len(h1)}) / {h2.mean():+.2f} (n {len(h2)})")
    ok = tstat(x) >= 3 and h1.mean() > 0 and h2.mean() > 0
    pr(f"  bar t >= 3, both halves > 0: {'PASS' if ok else 'FAIL'}")
    pr(f"  20d excess {G.ex20.mean():+.2f} (t {tstat(G.ex20):+.2f}); raw 40d {G.raw40.mean():+.2f}%; "
       f"signal - post (same basket, random later session) {(G.raw40 - G.post40).mean():+.2f}pp t {tstat(G.raw40 - G.post40):+.2f}")
    for lab, msk in (("broken tape (breadth < 40)", G.breadth < 40), ("healthy tape (breadth >= 40)", G.breadth >= 40)):
        z = G[msk]
        pr(f"  {lab:28s} n {len(z):3d}  40d excess {z.ex40.mean():+.2f} (t {tstat(z.ex40):+.2f})  raw {z.raw40.mean():+.2f}%")
    pr("  per year 40d excess: " + "  ".join(f"{y} {v:+.1f}" for y, v in G.groupby(dts.dt.year).ex40.mean().items()))
    crypto = G[G.group.str.contains("Crypto", na=False)]
    pr(f"  crypto episodes: {crypto[['date', 'n', 'med_dd', 'ex40']].round(1).to_dict('records')}")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

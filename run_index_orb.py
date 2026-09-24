#!/usr/bin/env python3
"""
[WL-5a] Index opening-range breakout on SPY and QQQ (pre-registered 2026-09-23; spec copied from
data/orb_backtests/README.md "Single best follow-up" BEFORE running).

Data: SPY + QQQ 1-min RTH (data/cache/intraday_hist/*_1min.parquet), 2007-01 -> 2025-12 for the verdict; 2026 HELD
OUT and reported separately after the verdict is fixed.
PRIMARY cell (per instrument): 15-min OR (09:30-09:44); signal = first 15-min bar (09:45-09:59, 10:00-10:14, ...,
  11:45-11:59) CLOSING outside the OR; enter at the next 1-min bar's open, in the direction of the break (both
  directions); stop = opposite side of the OR; exit at +1.5R or the 15:59 close.
Secondary cells (charged): 30-min OR (09:30-09:59, 15-min bars from 10:00); hold-to-close (no target); ATR filter
  (skip if OR range / daily ATR14 < 0.15 or > 0.60, ATR from prior days only); midpoint-retest entry (after the break,
  a limit at the OR midpoint filled on the first touch at or before 12:00, stop = opposite side, 1.5R of that risk).
Controls:
  (a) PRIMARY: same entry minute, OPPOSITE direction, mirrored bracket (same risk distance on the other side, 1.5R
      target) -- an index ORB is a direction call; this nets out drift.
  (b) same direction, random entry minute 09:45-12:00 on the same day, same risk %, 1.5R / 15:59.
  (c) always-long 09:30 open -> 15:59 close (descriptive).
Costs: 1bp per side + $0.005/sh; the stop fills one tick ($0.01) through; a bar touching both stop and target = stop.
Metric: % return per trade (not R). Bar: |t| >= 3 on (trade - control a) per day, both halves (split 2016-07-01) the
  same sign, per-year shown (2020 and 2022 flagged). Sidak over 2 instruments x 5 cells = 10 -> |t| >= 2.8; the house
  3.0 governs the primary. PASS needs the primary |t| >= 3 in one instrument and the same sign in the other.
Prior ~25% pass: the noise band (a better-specified cousin) is only MARGINAL net of costs and dead 2009-17.

Run: PYTHONPATH=src .venv/bin/python3 run_index_orb.py   (log -> data/studies/logs/index_orb.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/index_orb.log"
COST_BP, PER_SH, TICK, TGT = 1.0, 0.005, 0.01, 1.5
SPLIT, HOLDOUT = "2016-07-01", "2026-01-01"
RNG = np.random.default_rng(20260923)


def load(sym):
    df = pd.read_parquet(REPO / f"data/cache/intraday_hist/{sym}_1min.parquet")
    df["day"] = df.ts.dt.normalize()
    df["m"] = df.ts.dt.hour * 60 + df.ts.dt.minute - 570
    df = df[(df.m >= 0) & (df.m < 390)]
    days = np.array(sorted(df.day.unique()))
    di = pd.Series(np.arange(len(days)), index=days)[df.day].values
    g = {}
    for c in ("open", "high", "low", "close"):
        a = np.full((len(days), 390), np.nan)
        a[di, df.m.values] = df[c].values
        g[c] = a
    # daily ATR14 from prior days only
    dh, dl, dc = np.nanmax(g["high"], 1), np.nanmin(g["low"], 1), np.array([r[np.isfinite(r)][-1] if np.isfinite(r).any() else np.nan for r in g["close"]])
    pc = np.r_[np.nan, dc[:-1]]
    tr = np.nanmax(np.c_[dh - dl, np.abs(dh - pc), np.abs(dl - pc)], 1)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    return days, g, atr


def cost(px):
    return px * COST_BP / 1e4 + PER_SH


def run_trade(g, d, m0, side, entry, stop, target):
    """Walk 1-min bars from m0 (entry bar, entered at its open). Returns % return net of costs."""
    H, L, C = g["high"][d], g["low"][d], g["close"][d]
    last = int(np.flatnonzero(np.isfinite(C))[-1])
    exit_px = None
    for m in range(m0, last + 1):
        h, l = H[m], L[m]
        if not np.isfinite(h):
            continue
        if side > 0:
            if l <= stop:
                exit_px = stop - TICK; break
            if target is not None and h >= target:
                exit_px = target; break
        else:
            if h >= stop:
                exit_px = stop + TICK; break
            if target is not None and l <= target:
                exit_px = target; break
    if exit_px is None:
        exit_px = C[last]
    gross = side * (exit_px - entry)
    return 100 * (gross - cost(entry) - cost(exit_px)) / entry


def signals(g, d, or_len):
    O, H, L, C = g["open"][d], g["high"][d], g["low"][d], g["close"][d]
    orh, orl = np.nanmax(H[:or_len]), np.nanmin(L[:or_len])
    if not (np.isfinite(orh) and np.isfinite(orl)) or orh <= orl:
        return None
    for end in range(or_len + 14, 150, 15):              # 15-min bar closes: m = or_len+14, ..., 149 (11:59)
        c = C[end]
        if not np.isfinite(c):
            continue
        if c > orh or c < orl:
            m0 = end + 1
            if m0 >= 390 or not np.isfinite(O[m0]):
                return None
            return dict(side=1 if c > orh else -1, m0=m0, orh=orh, orl=orl)
    return None


def cell(days, g, atr, or_len=15, target=True, atr_filter=False, midpoint=False):
    rows = []
    for d in range(len(days)):
        s = signals(g, d, or_len)
        if s is None:
            continue
        orh, orl, side, m0 = s["orh"], s["orl"], s["side"], s["m0"]
        if atr_filter:
            ratio = (orh - orl) / atr[d] if np.isfinite(atr[d]) and atr[d] > 0 else np.nan
            if not (0.15 <= ratio <= 0.60):
                continue
        O, H, L = g["open"][d], g["high"][d], g["low"][d]
        if midpoint:
            mid = (orh + orl) / 2
            fill = None
            for m in range(m0, 151):
                if np.isfinite(L[m]) and L[m] <= mid <= H[m]:
                    fill = m; break
            if fill is None:
                continue
            entry, m0 = mid, fill
        else:
            entry = O[m0]
        stop = orl if side > 0 else orh
        risk = side * (entry - stop)
        if not np.isfinite(risk) or risk <= 0:
            continue
        tgt = entry + side * TGT * risk if target else None
        r = run_trade(g, d, m0, side, entry, stop, tgt)
        # (a) same minute, opposite direction, mirrored bracket
        a = run_trade(g, d, m0, -side, entry, entry + side * risk, (entry - side * TGT * risk) if target else None)
        # (b) same direction, random minute 09:45-12:00 (m 15..150), same risk %
        mr = int(RNG.integers(15, 151))
        while mr == m0:
            mr = int(RNG.integers(15, 151))
        eb = O[mr]
        b = np.nan
        if np.isfinite(eb):
            rk = risk / entry * eb
            b = run_trade(g, d, mr, side, eb, eb - side * rk, (eb + side * TGT * rk) if target else None)
        C = g["close"][d]
        last = C[np.isfinite(C)][-1]
        c_ = 100 * (last - O[0] - cost(O[0]) - cost(last)) / O[0] if np.isfinite(O[0]) else np.nan
        rows.append(dict(day=days[d], side=side, ret=r, ctl_a=a, ctl_b=b, long_oc=c_))
    return pd.DataFrame(rows)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def summarize(T, label, lines, per_year=False):
    V = T[T.day < HOLDOUT]
    da, db = V.ret - V.ctl_a, V.ret - V.ctl_b
    h1 = V.day < SPLIT
    lines.append(f"{label:34s} n {len(V):5d} | ORB {V.ret.mean():+.4f}% (t {tstat(V.ret):+.2f}) | vs (a) opp-dir "
                 f"{da.mean():+.4f} t {tstat(da):+.2f} halves {da[h1].mean():+.4f}/{da[~h1].mean():+.4f} | vs (b) rand-min "
                 f"{db.mean():+.4f} t {tstat(db):+.2f} | long o->c {V.long_oc.mean():+.4f}")
    if per_year:
        y = pd.DataFrame({"n": V.groupby(V.day.dt.year).size(), "orb": V.groupby(V.day.dt.year).ret.mean(),
                          "vs_a": da.groupby(V.day.dt.year).mean(), "vs_b": db.groupby(V.day.dt.year).mean()})
        lines.append("   per year (%):\n" + y.round(3).T.to_string())
    return dict(t_a=tstat(da), d_a=da.mean(), h1=da[h1].mean(), h2=da[~h1].mean())


def main():
    lines = ["# Index ORB [WL-5a] (pre-registration in the docstring); verdict window 2007-01 -> 2025-12"]
    res, held = {}, {}
    for sym in ("SPY", "QQQ"):
        days, g, atr = load(sym)
        lines.append(f"\n## {sym}: {len(days)} sessions {pd.Timestamp(days[0]).date()} -> {pd.Timestamp(days[-1]).date()}")
        P = cell(days, g, atr)
        res[sym] = summarize(P, "PRIMARY 15m OR, 1.5R/15:59", lines, per_year=True)
        held[sym] = P[P.day >= HOLDOUT]
        for lab, kw in (("30m OR", dict(or_len=30)), ("hold to close", dict(target=False)),
                        ("ATR filter 0.15-0.60", dict(atr_filter=True)), ("midpoint retest", dict(midpoint=True))):
            summarize(cell(days, g, atr, **kw), lab, lines)
        P.to_csv(REPO / f"data/studies/logs/index_orb_{sym}_primary_trades.csv", index=False)
    print("\n".join(lines))
    s, q = res["SPY"], res["QQQ"]
    passed = any(abs(r["t_a"]) >= 3 and np.sign(r["h1"]) == np.sign(r["h2"]) == np.sign(r["d_a"]) for r in (s, q)) \
        and np.sign(s["d_a"]) == np.sign(q["d_a"])
    print(f"\nVERDICT (primary vs control a): SPY t {s['t_a']:+.2f}, QQQ t {q['t_a']:+.2f} -> "
          f"{'PASS' if passed else 'no pass'}")
    print("\n## 2026 HOLD-OUT (reported after the verdict, primary cell)")
    for sym, H in held.items():
        if len(H):
            d = H.ret - H.ctl_a
            print(f"{sym}: n {len(H)} | ORB {H.ret.mean():+.4f}% | vs (a) {d.mean():+.4f} (t {tstat(d):+.2f})")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

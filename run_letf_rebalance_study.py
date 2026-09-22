#!/usr/bin/env python3
"""
Leveraged-ETF close-rebalancing flow on QQQ (2026-09-22, QQQ intraday project item #2; pre-registered here
before the first run).

Mechanism: a daily-reset L-times ETF must trade AUM x L(L-1) x (day return) in the SAME direction as the day's move
near the close (TQQQ/SQQQ: L = +3 / -3, both give L(L-1) > 0 -> same-sign flow). So on big days a predictable wave
of buying (up days) or selling (down days) hits the last half hour. Gao-Han-Li-Zhou 2018, Baltussen et al. 2021.

Signal: r = QQQ return from the prior session's close to the 15:30 price (close of the 15:29 bar).
Trade: at 15:30 go long QQQ if r > 0, short if r < 0; exit at the 16:00 close (close of the 15:59 bar).
Full sessions only (last bar 15:59). Returns in basis points of QQQ.
Costs: 1 bp round trip (institutional-ish QQQ), also shown at 2 bp (the $10k "game", IBKR minimums).

PRIMARY cell (the one that decides): |r| >= 1.5%, 2010-02-11 (TQQQ launch) .. 2026-09-17.
PRE-REGISTERED PASS, all of:
  1. mean net (1 bp) > 0 with t >= 3
  2. both halves positive (2010-2017, 2018-2026)
  3. 2020 and 2022 each not negative (the high-vol years the mechanism should love)
  4. beats the CONTROL by t >= 2 (paired by day): same day, a random 30-minute window starting 12:00-14:59,
     direction = the day's move known at the window start -- separates close-timed flow from generic
     trend-day momentum (first run had a look-ahead in this direction; fixed, see the comment in the loop)
Descriptive (do not decide): dose-response across |r| buckets (mechanism predicts it rises with |r|),
the |r| >= 2% cell, all days, and a PLACEBO on 2007-01 .. 2010-02 (before TQQQ/SQQQ; only 2x ETFs, much smaller AUM)
where the effect should be weaker.

Usage: PYTHONPATH=src .venv/bin/python3 run_letf_rebalance_study.py
"""
from __future__ import annotations
from math import sqrt
import numpy as np, pandas as pd

pd.set_option("display.width", 220)
q = pd.read_parquet("data/cache/intraday_hist/QQQ_1min.parquet")
q["d"] = q.ts.dt.normalize(); q["hm"] = q.ts.dt.strftime("%H:%M")
full = q.groupby("d").hm.max() == "15:59"
q = q[q.d.isin(full[full].index)]
px = q.pivot_table(index="d", columns="hm", values="close", aggfunc="last")
need = ["15:29", "15:59"]
px = px.dropna(subset=need)
prev_close = px["15:59"].shift(1)
r = px["15:29"] / prev_close - 1
last30 = (px["15:59"] / px["15:29"] - 1) * 1e4 * np.sign(r)

# control: random 30-min window starting 12:00-14:59, same direction, same day
rng = np.random.default_rng(22)
starts = [f"{h:02d}:{m:02d}" for h in (12, 13, 14) for m in range(60)]
ctrl = []
for d in px.index:
    s = starts[rng.integers(len(starts))]; hh, mm = map(int, s.split(":")); e = f"{hh + (mm + 30) // 60:02d}:{(mm + 30) % 60:02d}"
    a, b = px.at[d, s] if s in px.columns else np.nan, px.at[d, e] if e in px.columns else np.nan
    # direction = the move known AT the window start (prior close -> start); the first run used sign(r), which
    # includes the window itself = look-ahead (control read +10bp). Corrected before any verdict was drawn.
    pc = prev_close.get(d, np.nan)
    ctrl.append((b / a - 1) * 1e4 * np.sign(a / pc - 1) if np.isfinite(a) and np.isfinite(b) and np.isfinite(pc) else np.nan)
D = pd.DataFrame({"r": r, "g": last30, "ctrl": ctrl}).dropna(subset=["r", "g"])
D = D[D.index > D.index[0]]
D["yr"] = D.index.year


def t(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def line(lab, x, cost=1.0):
    n = x.g - cost
    return (f"{lab:34} n {len(x):4d}  gross {x.g.mean():+6.2f}bp  net1 {n.mean():+6.2f} (t {t(n):+5.2f})  net2 {(x.g-2).mean():+6.2f}  "
            f"win {100*(x.g>1).mean():3.0f}%  ctrl {x.ctrl.mean():+6.2f}  g-ctrl {(x.g-x.ctrl).mean():+6.2f} (t {t(x.g-x.ctrl):+5.2f})")


post = D[D.index >= "2010-02-11"]; pre = D[D.index < "2010-02-11"]
print(f"QQQ sessions: {len(D)} full days {D.index.min().date()}..{D.index.max().date()} ; post-TQQQ {len(post)}")
print("\n== PRIMARY: |r| >= 1.5%, 2010-02-11 .. ==")
P = post[post.r.abs() >= 0.015]
print(line("primary", P))
h1, h2 = P[P.index < "2018-01-01"], P[P.index >= "2018-01-01"]
print(line("  2010-2017", h1)); print(line("  2018-2026", h2))
print("  by year (net1 mean bp / n):", {y: (round(g.g.mean() - 1, 1), len(g)) for y, g in P.groupby("yr")})
print("  up days vs down days:", f"up {P[P.r>0].g.mean():+.2f}bp (n {(P.r>0).sum()}), down {P[P.r<0].g.mean():+.2f}bp (n {(P.r<0).sum()})")
n1 = P.g - 1
c = [n1.mean() > 0 and t(n1) >= 3, (h1.g - 1).mean() > 0 and (h2.g - 1).mean() > 0,
     all((P[P.yr == y].g - 1).mean() >= 0 for y in (2020, 2022)), t(P.g - P.ctrl) >= 2]
print(f"  criteria: t>=3 {c[0]} | both halves {c[1]} | 2020 & 2022 >= 0 {c[2]} | beats control t>=2 {c[3]}")
print("  PRE-REGISTERED PASS:", "YES" if all(c) else "NO")

print("\n== descriptive ==")
print(line("all days (post)", post))
for lo, hi in ((0, .005), (.005, .01), (.01, .015), (.015, .02), (.02, .03), (.03, 1)):
    print(line(f"|r| {lo*100:.1f}-{hi*100:.1f}%", post[(post.r.abs() >= lo) & (post.r.abs() < hi)]))
print(line("|r| >= 2% (post)", post[post.r.abs() >= 0.02]))
print(line("PLACEBO pre-TQQQ |r|>=1.5%", pre[pre.r.abs() >= 0.015]))
D.to_csv("data/studies/letf_rebalance_days.csv")

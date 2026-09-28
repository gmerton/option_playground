#!/usr/bin/env python3
"""
Add to an OPEN WINNER: second precision signal and retest add vs a FRESH precision breakout (2026-09-28).
TEST_INDEX §10, queued 2026-09-24. Specs: data/optionsplay/videos/2026-06-20_DqtBkL1qalU/notes.md ("not tested,
could be" #1) and 2026-09-05_iXOULnIGEKk/notes.md ("add on a RETEST").

WHAT IS NEW. Row 121 (run_oneil_pyramid_8wk.py) added at FIXED session counts (3/5/10) and compared the add with an
unconditional add. The creator claim is different on both axes: the trigger is a fresh SIGNAL (a re-fire, or a
retest of the breakout level), and the comparison is against a FRESH idea. The decision it answers is the live one:
"my next unit of risk -- press the working name, or open a new one today?"

PRE-REGISTRATION (frozen before the first run; nothing below changed after it)
  Panel     liquid_panel_2009, 2010-01 -> 2026-09; eligible = ADDV50 >= $50M, px >= $5, not a split artefact.
  Signal    the precision tier exactly as run_oneil_pyramid_8wk.py builds it (ADR 4-7, within 15% of the 52wk high,
            stacked 5-40 sessions, close clears the 15-day pivot on RVOL >= 1.1, upper-half close, gap < 5%, day < 8%,
            first close above the pivot).
  House     every entry (base, add, fresh) is the same trade: buy the close; stop = min(entry-day low, close x 0.98)
            judged on the close; exit = first close under the stop or the 20 EMA; 60-session cap; 5 bp per side.
            Outcome in % of entry price (stop widths differ across arms, so not R).
  Base      per name, chronologically: a precision signal opens a BASE trade only if no base trade is open.
  FRESH     control = base-trade openings (names with no open trade) on the SAME date as the event.
  Arm S     SECOND SIGNAL: a precision signal at session s in a name whose base trade is open (s < base exit) and in
            profit at the close of s (C_s > base entry). Every such re-fire is an event.
  Arm T     RETEST: the first session s after the base entry with low_s <= pivot x (1 + 0.25 x ADR%) and
            close_s > pivot, base still open. (No in-profit condition: a retest of the level often sits below the
            base entry; the in-profit subset is reported as exploratory.)
  Metric    per event: event % minus the mean % of same-date FRESH trades (dates with >= 1 fresh trade). Averaged by
            calendar month, t over months.
  PRIMARY   two cells, S and T. Each must clear |t| >= 3.2 (Sidak-2 on the house |t| 3), both halves the same sign
            (split 2018-01-01), per-year signs reported.
  Explor.   (not certifiable) S under water (C_s <= base entry); T in profit; each arm vs the UNCONDITIONAL add at the
            same age bucket (1-5 / 6-10 / 11-20 / 21+ sessions after the base entry, any open base trade, pooled).
  Caveats   survivorship (today's liquid names; the same-date contrast is what is tested); the base trade is what
            the add is conditioned on, so any add is priced from s onward only -- the base's banked gain is excluded.

Usage: PYTHONPATH=src .venv/bin/python3 run_add_to_winner.py > data/studies/logs/add_to_winner.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
COST, FLOOR, HOLD = 0.0005, 0.02, 60
SPLIT = pd.Timestamp("2018-01-01")
START = pd.Timestamp("2010-01-01")

raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
p = Panel.from_long(raw)
O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
range52 = (hi52 - lo52) / C * 100
piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
stack_days = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
gate = (adr >= 3) & (range52 >= 17) & elig
brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08)
       & (C.shift(1) < piv15))
prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)).fillna(False).astype(bool)
prec[prec.index < START] = False

Cv, Lv, E, PV, AV = C.values, L.values, e20.values, piv15.values, adr.values
N = len(Cv)
dates = C.index


def trade(i, j):
    """house trade from the close of i: returns (% net, exit index) or (nan, None)."""
    entry = Cv[i, j]
    if not np.isfinite(entry) or i + 1 >= N:
        return np.nan, None
    stop = min(Lv[i, j], entry * (1 - FLOOR))
    for k in range(i + 1, min(i + HOLD + 1, N)):
        c = Cv[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or c < E[k, j]:
            return (c * (1 - COST) - entry * (1 + COST)) / entry * 100, k
    k = min(i + HOLD, N - 1)
    if k == i:
        return np.nan, None
    return (Cv[k, j] * (1 - COST) - entry * (1 + COST)) / entry * 100, k


fresh, events, uncond = [], [], []
for j in range(C.shape[1]):
    sig = np.flatnonzero(prec.values[:, j])
    if len(sig) == 0:
        continue
    sig_set = set(sig.tolist())
    i = None; bx = -1
    for s in sig:
        if s <= bx:
            continue
        # open a base trade
        r, x = trade(s, j)
        if x is None:
            continue
        i, bx = s, x
        fresh.append(dict(i=i, j=j, date=dates[i], pct=r))
        entry, piv, a = Cv[i, j], PV[i, j], AV[i, j]
        retest_done = False
        for m in range(i + 1, bx):                    # sessions while the base is open (exit happens AT bx)
            c = Cv[m, j]
            if not np.isfinite(c):
                continue
            age = m - i
            ar, ax = trade(m, j)
            if ax is None:
                continue
            uncond.append(dict(date=dates[m], age=age, pct=ar))
            if m in sig_set:
                events.append(dict(arm="S" if c > entry else "S_under", i=m, j=j, date=dates[m], age=age, pct=ar))
            if (not retest_done and np.isfinite(piv) and np.isfinite(a) and Lv[m, j] <= piv * (1 + 0.25 * a / 100)
                    and c > piv):
                retest_done = True
                events.append(dict(arm="T", i=m, j=j, date=dates[m], age=age, pct=ar, inprofit=c > entry))

F = pd.DataFrame(fresh); Ev = pd.DataFrame(events); U = pd.DataFrame(uncond)
fmean = F.groupby("date").pct.mean()
bucket = lambda a: pd.cut(a, [0, 5, 10, 20, 999], labels=["1-5", "6-10", "11-20", "21+"])
U["b"] = bucket(U.age); Ev["b"] = bucket(Ev.age)
ub = U.groupby("b").pct.mean()


def mt(x):
    x = pd.Series(x).dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan


def cell(df, label):
    d = df.copy()
    d["fresh"] = d.date.map(fmean)
    d = d.dropna(subset=["fresh"])
    d["diff"] = d.pct - d.fresh
    mo = d.groupby(d.date.dt.to_period("M"))["diff"].mean()
    h1, h2 = mo[mo.index.to_timestamp() < SPLIT], mo[mo.index.to_timestamp() >= SPLIT]
    d["vsU"] = d.pct - d.b.map(ub).astype(float)
    mu = d.groupby(d.date.dt.to_period("M"))["vsU"].mean()
    return dict(cell=label, events=len(d), months=len(mo), event_pct=d.pct.mean(), fresh_pct=d.fresh.mean(),
                diff_pp=mo.mean(), t=mt(mo), h1_pp=h1.mean(), h2_pp=h2.mean(),
                vs_uncond_pp=mu.mean(), t_vs_uncond=mt(mu), win_event=100 * (d.pct > 0).mean(),
                win_fresh=100 * (d.fresh > 0).mean()), d


print(f"panel {C.shape}, {dates.min().date()} -> {dates.max().date()} | precision signals {int(prec.values.sum()):,}")
print(f"base (fresh) trades {len(F):,}: mean {F.pct.mean():+.2f}%  win {100*(F.pct>0).mean():.0f}%  "
      f"| unconditional adds {len(U):,}: mean {U.pct.mean():+.2f}%")
print("unconditional add mean % by age bucket:", ub.round(2).to_dict())
rows, keep = [], {}
for lab, sub in [("PRIMARY S: second signal, base in profit", Ev[Ev.arm == "S"]),
                 ("PRIMARY T: retest of the pivot", Ev[Ev.arm == "T"]),
                 ("S under water (explor.)", Ev[Ev.arm == "S_under"]),
                 ("T in profit (explor.)", Ev[(Ev.arm == "T") & (Ev.inprofit == True)])]:
    r, d = cell(sub, lab); rows.append(r); keep[lab] = d
T = pd.DataFrame(rows)
print("\n" + T.round(3).to_string(index=False))
for lab in ("PRIMARY S: second signal, base in profit", "PRIMARY T: retest of the pivot"):
    d = keep[lab]
    y = d.groupby(d.date.dt.year)["diff"].agg(["mean", "size"])
    print(f"\n{lab} -- per year (event minus same-date fresh, pp):")
    print(y.round(2).T.to_string())
for _, r in T.iloc[:2].iterrows():
    ok = abs(r.t) >= 3.2 and np.sign(r.h1_pp) == np.sign(r.h2_pp) == np.sign(r.t)
    print(f"PRE-REGISTERED BAR {r.cell}: {'PASS' if ok else 'FAIL'}")
Ev.to_csv("data/studies/logs/add_to_winner_events.csv", index=False)

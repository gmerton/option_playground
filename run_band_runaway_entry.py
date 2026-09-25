#!/usr/bin/env python3
"""
Buy early, buy the close, or skip? The close-entry rule vs the 1-ADR location band (pre-registered 2026-09-25,
before any run; from DELL 2026-09-25: in the band at 09:30 at ~$558, closed +6.5% at 1.26 ADR over the 21 EMA, so the
close rule said wait and the band rule then said skip).

WHY THIS IS NEW. entry_study_2026-09-17 (CLOSE beats every intraday entry, paired -1.2 / -2.3pp) always bought the
close however extended it was, so it never met the band. The band (<= 1 ADR over the 21 EMA) comes from the August
journal lens -- Gabe's own trades, which are NOT admissible for setup selection. No ledger row tests the two rules
TOGETHER.

⚠ OUTCOME-CONDITIONING TRAP (declared now). Selecting days on "ran out of the band by the close" makes the open
entry win by construction (it banks the day's rally). So the events are EVERY morning a candidate was buyable, chosen
on information available at 09:30, and the policies are compared on the SAME events. The "ran away" subset is
printed as DESCRIPTIVE ONLY, labelled outcome-conditioned, and is not evidence.

EVENTS (daily bars, data/cache/liquid_panel_2009.parquet, adjusted; 2010-01 -> 2026-08)
  candidate at the PRIOR close d-1: precision tier (ADR 4-7%, within 15% of the 252d high, 10>20>50 stack held
  5-40 sessions via lib.commons.ma_stack.stack_run) AND close within [0, 1] ADR of its 21 EMA (the band), harness
  eligible (ADDV >= $50M, px >= $5).
  morning of d: open within the band vs the d-1 EMA, and gap < +3% (the no-gap-up-buy rule).
  one event per name-episode: the first qualifying day after >= 10 sessions without one.

POLICIES (paired on each event; 10 bp per side; % return, NOT R -- stop width must not move the score)
  OPEN        buy d's open.
  HOUSE       buy d's close only if the close is still in the band (ext21 at d's close <= 1 ADR), else no trade.
  CLOSE-ANY   buy d's close regardless of extension.
  exit        the close of session d+h, h in {5, 20}; PRIMARY h = 20. No stop (the policies differ only in entry;
              a stop would change the denominator and the path -- stop behaviour is a separate question).
  no-trade    scores 0 for the event (HOUSE only); per-trade means are also reported.

COMPARISONS (the question actually faced)
  PRIMARY  OPEN - HOUSE, per event, +20, month-clustered t.
  2        OPEN - CLOSE-ANY (the pure open-to-close drift on candidate mornings, unconditioned).
  3        CLOSE-ANY - HOUSE (is the band skip worth anything at the close?).
  M = 3 comparisons x 2 horizons = 6; Sidak(6) |t| >= 2.64; the house |t| >= 3 GOVERNS; both halves (split 2018-01)
  the same sign and a majority of years the same sign.
  READ: PRIMARY passes positive -> "enter the morning" beats the house rule on candidate days. PRIMARY fails and
  comparison 3 passes positive -> keep the close, drop the band on strong closes. Both fail -> keep the house rule.

SECONDARY (1-min, 2026-02 -> 2026-09 only; declared underpowered; exploratory, not bar-bearing)
  the same events where data/cache/intraday_1min has the name-day: entries at 09:45 / 10:30 / 12:00 / 14:00 vs HOUSE,
  +5 sessions. Reported with n; a daily-bar result is the one that counts.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_band_runaway_entry.py   (log -> data/studies/logs/band_runaway_entry.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.studies.pattern_test import load_panel, SLIP

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/band_runaway_entry.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, END, SPLIT = "2010-01-01", "2026-08-31", "2018-01-01"
HORIZONS, GAP_MAX, EPISODE_GAP = (20, 5), 0.03, 10
INTRA = REPO / "data/cache/intraday_1min"
INTRA_TIMES = ["09:45", "10:30", "12:00", "14:00"]


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def build(P):
    C, O, H, L = P.close, P.open, P.high, P.low
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    e21 = C.ewm(span=21, adjust=False).mean()
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    stack = stack_run(C, adr=adr)
    ext_close = (C / e21 - 1) * 100 / adr                       # at the close, EMA incl. that close
    ext_open = (O / e21.shift(1) - 1) * 100 / adr               # at the open, vs the prior EMA
    prec = ((adr >= 4) & (adr <= 7)) & (C / hi52 - 1 > -0.15) & ((stack >= 5) & (stack <= 40))
    cand_prev = (prec & ((ext_close >= 0) & (ext_close <= 1)) & P.elig.fillna(False)).shift(1).fillna(False).astype(bool)
    gap = O / C.shift(1) - 1
    morning = cand_prev & ((ext_open >= 0) & (ext_open <= 1)) & (gap < GAP_MAX)
    win = (C.index >= START) & (C.index <= END)
    m = morning.values & win[:, None]
    ev = np.zeros_like(m)
    for j in range(m.shape[1]):
        last = -10_000
        for i in np.flatnonzero(m[:, j]):
            if i - last > EPISODE_GAP:
                ev[i, j] = True
            last = i
    return ev, ext_close.values


def policies(P, ev, extc, h):
    idx, cols = P.close.index, P.close.columns
    O, C = P.open.values, P.close.values
    rows = []
    for i, j in zip(*np.nonzero(ev)):
        if i + h >= len(idx) or not np.isfinite(C[i + h, j]) or not np.isfinite(O[i, j]):
            continue
        exit_ = C[i + h, j] * (1 - SLIP)
        r_open = 100 * (exit_ / (O[i, j] * (1 + SLIP)) - 1)
        r_close = 100 * (exit_ / (C[i, j] * (1 + SLIP)) - 1)
        inband = bool(extc[i, j] <= 1)
        rows.append(dict(date=idx[i], sym=cols[j], exit_px=exit_, OPEN=r_open, CLOSE_ANY=r_close, HOUSE=r_close if inband else 0.0,
                         house_traded=inband, day_ret=100 * (C[i, j] / O[i, j] - 1)))
    return pd.DataFrame(rows)


def compare(T, a, b, h, label, out):
    d = T[a] - T[b]
    mo = d.groupby(T.date.dt.to_period("M")).mean()
    hh = mo.index < pd.Period(SPLIT, "M")
    yr = d.groupby(T.date.dt.year).mean()
    same = (np.sign(yr) == np.sign(mo.mean())).sum()
    ok = abs(tstat(mo)) >= 3 and np.sign(mo[hh].mean()) == np.sign(mo[~hh].mean()) and same > len(yr) / 2
    out.append(f"  {label:26s} +{h:2d}: {mo.mean():+.3f}pp t {tstat(mo):+.2f} | halves {mo[hh].mean():+.3f} / {mo[~hh].mean():+.3f} "
               f"| years same sign {same}/{len(yr)} -> {'PASS' if ok else 'fail'}")
    return dict(cmp=label, h=h, diff=mo.mean(), t=tstat(mo), h1=mo[hh].mean(), h2=mo[~hh].mean(), pass_=ok)


def intraday_secondary(T, out):
    """Entries at fixed minutes (close of the first bar at/after t, ET index) vs HOUSE, same exit, same costs."""
    rows = []
    for r in T.itertuples():
        f = INTRA / f"{r.sym}_{r.date.date()}.parquet"
        if not f.exists():
            continue
        b = pd.read_parquet(f)
        hm = b.index.strftime("%H:%M")
        rec = dict(date=r.date, sym=r.sym)
        for t in INTRA_TIMES:
            s = b.close[hm >= t]
            rec[t] = 100 * (r.exit_px / (float(s.iloc[0]) * (1 + SLIP)) - 1) if len(s) else np.nan
        rec["HOUSE"] = r.HOUSE
        rows.append(rec)
    out.append(f"\n# SECONDARY (1-min 2026-02 -> 09, exploratory, underpowered): n {len(rows)} events with bars, +5")
    if len(rows) < 10:
        return
    I = pd.DataFrame(rows)
    for t in INTRA_TIMES:
        d = (I[t] - I.HOUSE).dropna(); dd = d.groupby(I.date[d.index]).mean()
        out.append(f"  entry {t} - HOUSE: {d.mean():+.3f}pp (date-clustered t {tstat(dd):+.2f}, n {len(d)})")


def main():
    P = load_panel(PANEL)
    ev, extc = build(P)
    out = ["# Buy early / buy the close / skip (pre-registration in the docstring)"]
    R = []
    for h in HORIZONS:
        T = policies(P, ev, extc, h)
        if h == HORIZONS[0]:
            out.append(f"# events {len(T):,} on {T.sym.nunique()} names, {T.date.min().date()} -> {T.date.max().date()}; "
                       f"HOUSE trades {T.house_traded.mean():.0%} of them (the rest closed > 1 ADR over the 21 EMA)")
        out.append(f"\n# +{h}: mean % per event  OPEN {T.OPEN.mean():+.2f}  CLOSE-ANY {T.CLOSE_ANY.mean():+.2f}  HOUSE {T.HOUSE.mean():+.2f} "
                   f"(HOUSE per trade {T.loc[T.house_traded, 'HOUSE'].mean():+.2f})")
        R.append(compare(T, "OPEN", "HOUSE", h, "PRIMARY OPEN - HOUSE" if h == 20 else "OPEN - HOUSE", out))
        R.append(compare(T, "OPEN", "CLOSE_ANY", h, "OPEN - CLOSE-ANY", out))
        R.append(compare(T, "CLOSE_ANY", "HOUSE", h, "CLOSE-ANY - HOUSE", out))
        run = T[~T.house_traded]
        out.append(f"  [DESCRIPTIVE, outcome-conditioned -- not evidence] ran-away days n {len(run)}: OPEN {run.OPEN.mean():+.2f}  "
                   f"CLOSE-ANY {run.CLOSE_ANY.mean():+.2f}  (day open->close {run.day_ret.mean():+.2f}%)")
        if h == 5:
            intraday_secondary(T, out)
        T.to_csv(REPO / f"data/studies/logs/band_runaway_entry_h{h}.csv", index=False)
    pd.DataFrame(R).to_csv(REPO / "data/studies/band_runaway_entry_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

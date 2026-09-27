#!/usr/bin/env python3
"""
FORWARD HOLDOUT: gap-up fade in a stock's own downtrend, breadth-free (pre-registered 2026-09-26, before any forward
data exists; Gabe: "do it" -- the follow-up to gap_fade_breadth_2026-09-26).

WHY FORWARD. gap_fade_breadth_2026-09-26 passed its primary (falling breadth +0.54%, t 3.87) but showed the breadth
condition adds nothing significant (falling - rising t 1.70); the stock's own down-cycle carries it. The breadth-free
version on the same 2010-2026 data is already implied by the two arms we saw (in-sample descriptive: +0.375%/date,
t 3.41, 13/17 years), so re-running it there is not a test. The only independent evidence is data nobody has seen:
events after 2026-09-26.

RULE (identical to run_gap_fade_breadth.py's down50 cell, breadth removed)
  universe  FROZEN: the 1,728 tickers in data/studies/gap_fade_forward_universe.txt (liquid_panel_2009 as of
            2026-09-23). Later panel refreshes add/drop names; only these count, so membership can't leak survivorship.
  eligible  ADDV >= $50M and price >= $5 on the PRIOR day (pattern_test eligibility).
  event     open >= 1.05 x prior close AND gap >= 1.5 x ADR (20-day, lagged); prior close < SMA50 AND SMA50 below its
            value 5 sessions earlier.
  trade     short at the open, cover at the close, net 10 bp/side.
  control   same-date eligible names with |gap| < 1%: excess = -(r_event - r_ctrl) - 20 bp.
WINDOW    events dated 2026-09-28 or later (the first session after this registration).
EVALUATE  when >= 150 forward events exist, or on 2027-09-30, whichever comes first (in-sample 2025-26 ran ~460
          events/yr, so ~4 months). Refresh the panel first:
            PYTHONPATH=src python run_build_liquid_panel.py --start 2009-01-01 --out data/cache/liquid_panel_2009.parquet
BAR       mean excess per date > 0 with date-clustered t >= 2 (one-sided confirmation of a pre-specified effect on
          independent data), AND the forward mean >= 1/3 of the in-sample +0.375% (a real effect shrinks, a fake one
          vanishes). Report raw net short return, win rate, the worst 5 events, and slippage sensitivity (+10/+20 bp).
          A pass is still not ADOPTED until real auction fills (MOO short / MOC cover) are measured on live size.
Local. This script only evaluates; there is nothing to schedule. Before the evaluation date it prints the event count.

Run: PYTHONPATH=src:. .venv/bin/python3 run_gap_fade_forward.py   (log -> data/studies/logs/gap_fade_forward.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/gap_fade_forward.log"
UNIV = REPO / "data/studies/gap_fade_forward_universe.txt"
FWD_START, EVAL_DATE, N_EVAL, SLIP, IN_SAMPLE = "2026-09-28", "2027-09-30", 150, 0.0010, 0.375


def events() -> pd.DataFrame:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    univ = set(UNIV.read_text().split())
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    O, C, ADR = P.open.loc[keep], P.close.loc[keep], P.adr.loc[keep]
    E = P.elig.loc[keep].fillna(False).shift(1).fillna(False).astype(bool)
    E = E & pd.DataFrame({c: c in univ for c in E.columns}, index=E.index)
    gap = O / C.shift(1) - 1
    oc = C / O - 1
    s50 = C.rolling(50).mean()
    down50 = ((C < s50) & (s50 < s50.shift(5))).shift(1)
    big = (gap >= 0.05) & (gap * 100 >= 1.5 * ADR) & E & oc.notna() & down50.fillna(False).astype(bool)
    r_ctrl = oc.where(E & (gap.abs() < 0.01) & oc.notna()).mean(axis=1)
    ii, jj = np.where(big.values)
    ev = pd.DataFrame(dict(date=C.index[ii], sym=C.columns[jj], gap=gap.values[ii, jj], oc=oc.values[ii, jj]))
    ev = ev[ev.date >= FWD_START].copy()
    ev["ctrl"] = r_ctrl.reindex(ev.date).values
    ev = ev.dropna(subset=["ctrl"])
    ev["raw"] = 100 * (-ev.oc - 2 * SLIP)
    ev["exs"] = 100 * (-(ev.oc - ev.ctrl) - 2 * SLIP)
    return ev


def main() -> None:
    ev = events()
    last = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date"]).date.max()
    out = [f"# Gap-up fade in a down-cycle, FORWARD holdout from {FWD_START} (panel through {pd.Timestamp(last).date()})",
           f"forward events so far: {len(ev)} on {ev.date.nunique() if len(ev) else 0} dates"]
    due = len(ev) >= N_EVAL or pd.Timestamp.today() >= pd.Timestamp(EVAL_DATE)
    if not due:
        out.append(f"NOT DUE: evaluate at >= {N_EVAL} events or on {EVAL_DATE}. (Refresh the panel first; see docstring.)")
        print("\n".join(out)); return
    g = ev.groupby("date").exs.mean()
    m, t = g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g))
    ok = m > 0 and t >= 2 and m >= IN_SAMPLE / 3
    out.append(f"excess per date {m:+.3f}% t {t:+.2f} (in-sample +{IN_SAMPLE:.3f}) | raw net {ev.raw.mean():+.3f}% | "
               f"win {100 * (ev.exs > 0).mean():.0f}%")
    for extra in (10, 20):
        y = (ev.exs - 2 * extra / 100).groupby(ev.date).mean()
        out.append(f"  +{extra} bp/side: {y.mean():+.3f}% t {y.mean() / y.std(ddof=1) * np.sqrt(len(y)):+.2f}")
    out.append("worst 5: " + ", ".join(f"{r.sym} {r.date.date()} {r.exs:+.1f}%" for r in ev.nsmallest(5, "exs").itertuples()))
    out.append(f"BAR: {'PASS' if ok else 'NOT MET'} (mean > 0, t >= 2, >= 1/3 of in-sample)")
    ev.to_csv(REPO / "data/studies/logs/gap_fade_forward_events.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

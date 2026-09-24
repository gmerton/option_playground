#!/usr/bin/env python3
"""
Failed-retest breakdown SHORT (2026-09-24, pre-registered; template = FDX Jun-Sep 2026).

Question: after a top (H1), a failed retest (lower high H2) and a multi-week range, is the FIRST CLOSE BELOW THE
RANGE LOW a shortable event? New axis: every prior short in TEST_INDEX was a STATE screen (short_universe_test
2026-09-23: 0/10, weak names still drift up) or a FADE (bouncy ball, capitulation, pullback-short arrival, VWAP
double rejection). This is the mirror of the house breakout -- an EVENT, entered on the close.

PRE-REGISTRATION (written before running):
  universe   liquid panel 2019-10 -> 2026-09, harness eligibility (ADDV >= $50M, px >= $5) AND 50d ADDV >= $100M
  event      at day t, over the prior 90 sessions:
               H1 = highest high, at session a;  t - a >= 30 (the range is at least 30 sessions old)
               H2 = highest high from a+15 .. t-1, with 0.95*H1 <= H2 < H1 (a lower high, a failed retest)
               RL = lowest low from a .. b (b = session of H2)  -- the range low
               every close from b .. t-1 >= RL, and close_t < RL   (the FIRST close below the range low)
             ⚠ the 90-session lookback (not the 60 first proposed) was chosen so FDX's 6/15 top is inside the window:
               it is fitted to the template. FDX fires on 2026-09-16.
  entry      short at the event close (entry_at="close"), harness slippage 10 bp
  stop       1 ADR above the event close, judged on the CLOSE (harness stops are close-through levels)
  exit arms  the harness's 5 (stop_hold / t1R / t2R / trail_bar / ema20); ⭐ PRIMARY = ema20 (close back above the
             20 EMA, the mirror of the house trail) with hold = 20 sessions
  controls   "post" (same name, random later session in the next 20: TIMING) and "xname" (random other eligible name,
             same date, same stop %: SELECTION). Both must be beaten.
  bar        harness daily bar (paired edge t >= 3, both halves' paired edge > 0, p_search < 0.003) against BOTH
             controls, per-year paired edge the same sign, AND the event's own mean return must be a GAIN FOR THE
             SHORT (stock down) -- a short must beat drift, borrow and financing, not just a control.
  report     % returns alongside R (R = % / ADR% here, since risk = 1 ADR); hold 5 and 60 as exploratory
             (ledger=False). Sector-ETF gate arm DEFERRED: no panel-wide sector map exists yet.
  charge     2 ledger rows (post, xname) for the primary; everything else exploratory.
  caveat     survivor panel: delisted names -- a short's best outcome -- are missing, so this understates shorts.

Usage: PYTHONPATH=src .venv/bin/python3 run_failed_retest_breakdown.py > data/studies/logs/failed_retest_breakdown.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from lib.studies.pattern_test import REPO, daily_signals, load_panel, run_daily

LOOK, MIN_AGE, MIN_GAP, RETEST = 90, 30, 15, 0.95


def events(P) -> pd.DataFrame:
    H, L, C = P.high.values, P.low.values, P.close.values
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2019.parquet")
    dv = raw.pivot(index="date", columns="ticker", values="dolvol").reindex(index=P.close.index, columns=P.close.columns)
    liq = (dv.rolling(50).mean() >= 100e6).values & P.elig.values
    hit = np.zeros_like(C, dtype=bool)
    n, m = C.shape
    for j in range(m):
        h, l, c = H[:, j], L[:, j], C[:, j]
        for t in range(LOOK, n):
            if not liq[t, j] or not np.isfinite(c[t]):
                continue
            w = h[t - LOOK:t]
            if not np.isfinite(w).all():
                continue
            a = t - LOOK + int(np.argmax(w)); h1 = h[a]
            if t - a < MIN_AGE or a + MIN_GAP > t - 1:
                continue
            seg = h[a + MIN_GAP:t]
            b = a + MIN_GAP + int(np.argmax(seg)); h2 = h[b]
            if not (RETEST * h1 <= h2 < h1):
                continue
            rl = np.nanmin(l[a:b + 1])
            if c[t] < rl and np.nanmin(c[b:t]) >= rl:
                hit[t, j] = True
    hit = pd.DataFrame(hit, index=P.close.index, columns=P.close.columns)
    return hit


if __name__ == "__main__":
    P = load_panel()
    hit = events(P)
    stop = P.close * (1 + P.adr / 100)
    sig = lambda _P: daily_signals(hit, stop=stop, side="short")
    S = sig(P)
    print(f"events: {len(S):,} on {S.sym.nunique()} names; FDX: "
          f"{[str(d.date()) for d in S[S.sym == 'FDX'].date][-5:]}")
    note = "FDX template; first close below the range low after a failed retest; stop 1 ADR close-judged"
    for ctl in ("post", "xname"):
        run_daily("failed-retest breakdown short", sig, hold=20, entry_at="close", control=ctl, panel=P,
                  note=note + " [PRIMARY hold 20]")
    for hold in (5, 60):
        for ctl in ("post", "xname"):
            run_daily(f"failed-retest breakdown short h{hold}", sig, hold=hold, entry_at="close", control=ctl,
                      panel=P, ledger=False, perms=0, note=note + " [exploratory]")
    # % returns: R x risk%, risk = 1 ADR (entry at the close, so risk% ~= ADR%)
    T = pd.read_parquet(REPO / "data/cache/pattern_failed-retest_breakdown_short_h60_daily.parquet")
    for h in (20,):
        T = pd.read_parquet(REPO / "data/cache/pattern_failed-retest_breakdown_short_daily.parquet")
    adr = P.adr.stack().rename("adr").reset_index().rename(columns={"level_0": "date", "level_1": "sym"})
    adr.columns = ["date", "sym", "adr"]; adr["date"] = adr.date.astype(str).str[:10]
    T = T.merge(adr, on=["date", "sym"], how="left")
    for a in ("ema20", "stop_hold"):
        pct = T[a] * T.adr
        yr = pd.to_datetime(T.date).dt.year
        print(f"\nPRIMARY hold 20, arm {a}: short P&L {pct.mean():+.2f}% mean, {pct.median():+.2f}% median, "
              f"win {(pct > 0).mean():.0%}, n {len(pct)} | stock move = the negative of this")
        print(pct.groupby(yr).agg(["size", "mean"]).round(2).T.to_string())

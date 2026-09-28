#!/usr/bin/env python3
"""
BREAKOUT-ACTIVITY GATE on the UNUSED 2010-2019 HOLDOUT: "press when the market is producing working breakouts"
(pre-registered 2026-09-27, before any run; Gabe: "yes, pre-register both"; this is item (2) of AUDIT STEP 3 in
TEST_INDEX section 10, list A of audit_top_down_2026-09-25.md. ⛔ NOT RUN -- queued, run on command.)

WHY. The top traders' years are made in a few hot months at heavy size, and our book has the same shape: +0.45R
trade-weighted but ~0 month-weighted; the top 10% of months give 68% of positive R. Pressing on one's OWN results
fails (adaptive-trader sim 2026-09-27 NULL; WL-2b rho -0.01). The MARKET-level version was PARKED on 2019-26:
run_breakout_activity_gate.py (2026-09-22) found the 5-session precision-tier breakout count, as a percentile of its
own trailing 252 sessions, sorted outcomes Q1 +0.06R -> Q5 +0.86R, top - bottom +0.81R, t 2.59, both halves positive;
but raw counts were flat-to-inverted and the 10/20-session neighbours weak (no plateau). The 2010-01 -> 2019-09
period of liquid_panel_2009 has never been used for it: an out-of-time holdout.

FROZEN from the original, not re-fit: the precision-tier signal and trade exactly as run_breakout_activity_gate.py
(close entry; stop = min(day low, close x 0.98); exit on a close under the stop or the 20 EMA; 60-session cap;
5 bp/side; R capped at +/-20); the signal cnt5_pct = the count of precision-tier breakouts across the eligible
universe in the 5 sessions BEFORE entry, as a percentile of its trailing 252 sessions; quintile cuts computed on
the holdout itself (the gate is a percentile, so no level is carried over).
HOLDOUT  entries 2010-01-01 -> 2019-09-30 on data/cache/liquid_panel_2009.parquet (the 2019-10+ data is the
         original sample and is NOT re-scored here).
PRIMARY  top-minus-bottom quintile of cnt5_pct, mean R, t on entry-date cluster means.
         BAR: t >= 3 (a second look at a parked result is charged: the house bar, not the original 2), both halves
         (split 2015-01-01) positive, AND positive in a majority of years; AND the plateau check the original failed:
         cnt10_pct and cnt20_pct top-minus-bottom must have the same sign with t >= 1.5.
ALSO (declared) the audit's two controls: vs same-date other-name random entries (xname) and vs the same name on a
         later random session (post); % return next to R; per year; share of total R in the top quintile.
PRESS VERSION (descriptive, only if the primary passes): a book that runs 1.5x size in the top quintile and 0.5x in
         the bottom vs flat size -- terminal wealth, max drawdown, using the adaptive-trader event simulator.
⚠ Survivor-biased panel (liquid as of 2026): flatters breakouts in every quintile alike; the gate is a relative sort.
PRIOR  low-moderate: the original had no plateau, and the market-state gates tried since (index filter, breadth
       deferral, distribution days) were all NULL.
Local.

Run (when approved): PYTHONPATH=src .venv/bin/python3 run_activity_gate_holdout.py
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-27, not built/run yet. See the docstring and TEST_INDEX section 10.")

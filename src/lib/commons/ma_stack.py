"""One definition of the 10 > 20 > 50 SMA "stacked" state, shared by run_adhikary_scan.py, run_adhikary_validation.py
and run_scan_clusters.py (2026-09-17, Gabe: a one-day dip of the 10 under the 20 should not reset the trend).

stack_run(C, ...) returns the trailing run length, in sessions, of the stacked state. Two kinds of tolerance:
magnitude slack (10d > (1 - slack) x 20d and 20d > (1 - slack) x 50d; slack as a fraction and/or in the name's own ADR)
and day fuzz (a violation lasting <= N sessions does not break the run). All zero = the strict rule. No look-ahead: on day k of a violation the run survives only while k <= N; on day N+1 it resets to 0.
A name is "stacked" when its run is > 0. A run can only start on a strictly stacked day.
"""
from __future__ import annotations
import numpy as np, pandas as pd

# House defaults. Validated 2026-09-17 on the precision tier (run_adhikary_validation.py, 2019-2026, breakouts, mean R):
#   strict                      n 1,847  R +0.65   (stacked = 34% of all ticker-days)
#   day fuzz 1 / 2 / 3 / 5      R +0.64 / +0.64 / +0.66 / +0.67   -> the edge does not depend on it
#   pct slack 0.5/1/2/3/5%      R +0.68 / +0.72 / +0.83 / +0.98 / +1.06   n 1,943 / 1,999 / 1,911 / 1,709 / 1,158
#   ADR slack 0.25 / 0.5 / 1.0  R +0.74 / +0.83 / +1.21                   n 2,024 / 1,928 / 1,305  (stacked = 42 / 50 / 63%)
# Gabe asked for magnitude slack instead of day fuzz. House choice = 0.25 ADR: forgives noise, keeps "stacked" a
# trend filter (42% of ticker-days), scale-free across quiet and volatile names. The larger slacks score better but
# change what the rule MEANS (the run becomes "sessions since the last real breakdown", and the <= 40 cap then picks
# names early in a repaired trend). That is a candidate rule to walk-forward, not a fuzz setting. Re-run the check
# before changing any of these.
STACK_FUZZ = 0
STACK_TOL_PCT = 0.0   # magnitude slack as a fraction of the slower average (0.01 -> 10d > 0.99 x 20d)
STACK_TOL_ADR = 0.25  # magnitude slack in units of the name's own ADR20 (needs `adr`, in percent)

def stack_run(close: pd.DataFrame, fuzz: int | None = None, tol_pct: float | None = None, tol_adr: float | None = None,
              adr: pd.DataFrame | None = None) -> pd.DataFrame:
    """fuzz = sessions of violation tolerated; tol_pct = slack as a fraction (0.01 -> 10d > 0.99 x 20d, 20d > 0.99 x 50d);
    tol_adr = slack in units of the name's own ADR (needs `adr` in percent). None = the house defaults above."""
    fuzz = STACK_FUZZ if fuzz is None else fuzz; tol_pct = STACK_TOL_PCT if tol_pct is None else tol_pct; tol_adr = STACK_TOL_ADR if tol_adr is None else tol_adr
    s10, s20, s50 = close.rolling(10).mean(), close.rolling(20).mean(), close.rolling(50).mean()
    slack = tol_pct + (tol_adr * adr / 100 if (tol_adr and adr is not None) else 0.0)
    strict = ((s10 > s20 * (1 - slack)) & (s20 > s50 * (1 - slack))).values
    run = np.zeros(strict.shape, dtype=np.int32); gap = np.zeros(strict.shape[1], dtype=np.int32)
    for i in range(strict.shape[0]):
        prev = run[i - 1] if i else np.zeros(strict.shape[1], dtype=np.int32)
        ok = strict[i]
        tolerated = ~ok & (prev > 0) & (gap + 1 <= fuzz)
        gap = np.where(ok, 0, np.where(tolerated, gap + 1, 0))
        run[i] = np.where(ok | tolerated, prev + 1, 0)
    return pd.DataFrame(run, index=close.index, columns=close.columns)

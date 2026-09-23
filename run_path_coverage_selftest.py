#!/usr/bin/env python3
"""Self-test for lib.studies.path_coverage — proves the guard catches the failure it exists for.

CASE A reproduces the run_iv_condor_study.py mechanism: low-coverage trades never get their stop
tested, so they fall through to a win at expiry. CASE B is the same study with honest coverage and
must NOT be flagged. Run after any change to the module.

    PYTHONPATH=src .venv/bin/python3 run_path_coverage_selftest.py
"""
import numpy as np, pandas as pd
from lib.studies.path_coverage import report, enforce_floor, sensitivity, compute_coverage
rng = np.random.default_rng(0)

# CASE A — the real bug: low-coverage trades never get their stop tested, so they land at expiry as wins.
n = 4000
cov = np.clip(rng.beta(0.6, 2.2, n), 0.02, 1.0)            # mostly poor coverage, like the 14.3% median
stop_would_fire = rng.random(n) < 0.35                      # 35% of paths genuinely breach the stop
# a breach is only SEEN if the path is covered; unseen breaches fall through to a win at expiry
seen = stop_would_fire & (rng.random(n) < cov)
pnl = np.where(seen, -rng.uniform(2.0, 6.0, n), rng.uniform(0.3, 1.0, n))
bug = pd.DataFrame({"mark_cov": cov, "pnl": pnl})

# CASE B — clean: coverage is good and unrelated to the outcome.
cov2 = np.clip(rng.beta(6, 1.2, n), 0.05, 1.0)
pnl2 = np.where(rng.random(n) < 0.35, -rng.uniform(2.0, 6.0, n), rng.uniform(0.3, 1.0, n))
clean = pd.DataFrame({"mark_cov": cov2, "pnl": pnl2})

print("### CASE A — reproduces the iv_condor failure mode")
va = report(bug, label="synthetic short strangle, coverage-biased")
print("\n\n### CASE B — a study with honest coverage")
vb = report(clean, label="synthetic, coverage independent of outcome")

print("\n\n=== DID THE GUARD DO ITS JOB? ===")
print(f"  CASE A flagged: median_below_floor={va['median_below_floor']}  decays_with_floor={va['decays_with_floor']}"
      f"  -> {'CAUGHT' if (va['median_below_floor'] or va['decays_with_floor']) else '*** MISSED ***'}")
print(f"  CASE B flagged: median_below_floor={vb['median_below_floor']}  decays_with_floor={vb['decays_with_floor']}"
      f"  -> {'correctly passed' if not (vb['median_below_floor'] or vb['decays_with_floor']) else '*** FALSE ALARM ***'}")
# enforce_floor must refuse a frame with no coverage column at all
try:
    enforce_floor(pd.DataFrame({"pnl": [1, 2]}))
    print("  missing-column guard: *** DID NOT RAISE ***")
except KeyError:
    print("  missing-column guard: raises as intended")

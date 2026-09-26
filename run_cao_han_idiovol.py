#!/usr/bin/env python3
"""
IDIOSYNCRATIC VOLATILITY -> DELTA-HEDGED SINGLE-STOCK OPTION RETURNS (Cao & Han 2013) -- pre-registered 2026-09-26,
before any code or data pull; Gabe: "let's register all three and run 1". ⛔ NOT RUN -- queued in TEST_INDEX section 10.

CLAIM. Delta-hedged option returns fall with the underlying's idiosyncratic volatility: options on high-IVOL
("lottery") stocks are overpriced, so hedged longs there lose and hedged shorts earn. Cao-Han (JFE 2013), 1996-2010:
decile spread ~1-2%/month on delta-hedged calls and straddles, robust to IV-HV controls.

WHY NEW. The ledger has vol LEVEL (VRP panel), IV rank / percentile, skew and the Cremers-Weinbaum spread, all on
their own terms; nothing sorts on the STOCK's idiosyncratic risk. Distinct from Goyal-Saretto (run_goyal_saretto.py,
IV vs HV): the question here is whether IVOL adds anything once HV-IV is controlled.

DESIGN (reuses run_goyal_saretto.py's machinery exactly: universe, formation dates, the ATM ~30-DTE straddle, daily
delta hedge with v3 raw deltas and raw chain spot, the house cost model, split exclusion, 2011-01 -> 2026-01)
  signal   IVOL_t = std of residuals of daily returns on SPY (market model), trailing 252 sessions to t, annualised;
           split-adjusted chain_spot closes. Needs >= 200 observations.
  PRIMARY  decile 1 (lowest IVOL) minus decile 10 (highest IVOL), LONG delta-hedged straddle returns, equal weight,
           net of costs (long at mid + cost, short at mid - cost). Predicted sign: positive.
  CONTROL  (declared now) double sort: terciles of HV-IV first, IVOL deciles within each; report the within-tercile
           average spread. A spread that vanishes inside HV-IV terciles is Goyal-Saretto re-counted, not a new edge.
  BAR      Newey-West t (lag 3) >= 3 on the monthly net spread, both halves (split 2018-01) the same sign, a majority of
           years the same sign; AND the double-sort spread >= half the primary with t >= 2.
Local vs cloud: the option pull is shared with run_goyal_saretto.py's cache (data/cache/goyal_saretto/); if that cache
exists this runs locally in minutes.
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-26, not built/run yet. See the docstring and TEST_INDEX section 10.")

#!/usr/bin/env python3
"""
HAR-RV FORECAST vs IMPLIED VOL as the single-stock mispricing signal -- pre-registered 2026-09-26, before any code or
data pull; Gabe: "let's register all three and run 1". ⛔ NOT RUN -- queued in TEST_INDEX section 10.

CLAIM. Mispricing is only as good as the volatility forecast. Goyal-Saretto sort on trailing 12-month HV - IV; a
better forecast of the NEXT month's realised vol should sort better. Corsi's HAR-RV (daily / weekly / monthly
realised-vol components) is the standard cheap forecaster and beats trailing HV out of sample in the vol literature.

WHY NEW. Nothing in the ledger forecasts single-stock realised vol; the VRP panel measures IV - RV after the fact.

DESIGN (reuses run_goyal_saretto.py's machinery: universe, formation dates, the ATM ~30-DTE straddle, daily delta
hedge, house costs, split exclusion, 2011-01 -> 2026-01)
  forecast per name, at each formation t: fit log RV_{t+1..t+21} = a + b_d log RV_d + b_w log RV_w + b_m log RV_m
           on that name's own history ONLY up to t (expanding window, >= 500 sessions, refit monthly -> no
           look-ahead). RV from split-adjusted chain_spot close-to-close returns (no intraday data 2011-2026).
           Pooled-coefficient version (fit across all names up to t) as the fallback when a name is short.
  signal   S_t = HAR forecast - IV_t (ATM ~30-DTE mid IV).
  PRIMARY  decile 10 minus decile 1 of S, LONG delta-hedged straddle returns, net of costs (as Goyal-Saretto).
  CONTROL  (declared now) the Goyal-Saretto spread on the SAME months and names: HAR must beat it, paired by month.
           Also report the forecast's own accuracy (out-of-sample R^2 of HAR vs trailing HV for next-month RV).
  BAR      the primary passes at NW t >= 3, halves same sign, majority of years; AND HAR - Goyal-Saretto paired
           monthly difference > 0 with t >= 2. A better forecast that doesn't improve the P&L is a METHOD yield only.
Local vs cloud: shares run_goyal_saretto.py's option cache; the HAR fits are local CPU (minutes to ~1 h).
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-26, not built/run yet. See the docstring and TEST_INDEX section 10.")

#!/usr/bin/env python3
"""
EXIT SPEED BY MARKET STATE AT ENTRY: should breakout exits be faster when the tape is unstable? (pre-registered
2026-09-26, before any code or run; Gabe: calibrating exits to market conditions -- "perhaps in some markets we exit
faster". The FEEDBACK version of the same idea -- retuning knobs from recent results -- is an arm of the queued
simulated-adaptive-trader row, not this test.) ⛔ NOT RUN -- queued in TEST_INDEX section 10.

WHY NEW. The dealer-gamma regime is the ledger's strongest certified MECHANISM: negative SPY net gamma -> ~+8%
realised vol beyond VIX (t 7.7). It was tested on the 7-DTE book straddles (NULL, t 0.55) and on 1-day SPY option
structures, never on how long to hold a stock breakout. Every exit test so far used one exit rule for all states.

POOL     the precision-tier house breakouts and the generic pool (ADR >= 3), built by run_precision_tier_control.build()
         exactly as run_vol_decay_exit.py / run_qullamaggie_exit.py: entry = breakout CLOSE + slip, initial stop =
         breakout-day low on the CLOSE, 2% risk floor, 25% cap, 60-session max hold, 2019-10 -> 2026-02 (the SPY GEX
         series ends with v3 bid/ask).
STATE    at the entry close, declared now (no look-ahead):
         GAMMA  SPY net GEX sign from run_gex_regime_pin.gex_series("SPY") -- NEG vs POS.   <- PRIMARY state
         VIX    VIX close tercile over the trailing 252 sessions (exploratory state).
ARMS     every arm on the SAME trades, initial stop kept, exits judged on the close:
         BASE    the house 20-EMA close trail
         FAST    10-EMA close trail
         TIME10  exit at the 10th session's close (or earlier at the stop)
         SLOW    hold to the stop or 60 sessions, no trail (the queued STOP_ONLY arm)
PRIMARY  the interaction on the precision pool, in % return per trade (not R):
           I = [FAST - BASE | NEG gamma] - [FAST - BASE | POS gamma]
         Paired per trade, t on entry-date cluster means, I = difference of the two cluster means with SE from the two
         independent date sets. The idea predicts I > 0 (faster exits help more in negative gamma).
         BAR: t >= 3, both halves (split 2023-01) the same sign, a majority of years the same sign where both states
         occur. Secondary (declared): the same I for TIME10 and SLOW, and all three on the generic pool; 6 cells
         -> Sidak |t| ~ 2.6 for the secondaries; the house 3 governs the primary.
REPORTED per state: each arm's mean %, win rate, held days, top-decile winners' mean (does the fast exit cut the tail
         in NEG gamma less than in POS?), n trades / dates per state, per year.
DEPENDENCY  run AFTER the queued "does the 20-EMA trail cost money? STOP_ONLY vs BASE, exposure-matched" test: if the
         trail itself loses once beta is removed, the baseline arm changes and this is re-read against SLOW.
PRIOR    low-moderate. Gamma forecasts SPY vol, but a single stock's breakout path is mostly idiosyncratic; the NULL on
         the book straddles says market gamma didn't separate single-name outcomes there.
Local vs cloud: local (cached liquid panel + cached SPY GEX strikes; minutes).
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-26, not built/run yet. See the docstring and TEST_INDEX section 10.")

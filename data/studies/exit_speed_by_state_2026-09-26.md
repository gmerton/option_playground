# Exit speed by SPY gamma state at entry (2026-09-26)

`run_exit_speed_by_state.py` (pre-registered in its docstring 2026-09-26, body built to that spec and run the same
day). Log `logs/exit_speed_by_state.log`. Precision pool 1,506 trades / 702 dates (2019-10 → 2026-02-27, where the
SPY GEX series ends); generic pool 6,130 trades. Negative-gamma entries: 35% / 32% of trades.

## Verdict: NULL · faster exits don't help in unstable tapes · exploratory hint points the OTHER way

**PRIMARY** I = [10-EMA − 20-EMA | NEG gamma] − [same | POS gamma], precision pool, % per trade:
**+0.18pp, t 0.18**, halves −1.75 / +1.95, same sign in 1 of 7 years. Not met.

| secondaries (I, NEG − POS) | precision | generic |
|---|---|---|
| TIME10 (exit day 10) − BASE | +0.80pp, t 0.66 | +0.63pp, t 1.45 |
| SLOW (stop / 60 d) − BASE | −0.16pp, t −0.18 | −0.22pp, t −0.47 |
| FAST (10-EMA) − BASE | (primary) | +0.02pp, t 0.04 |

**Within every state, fast exits lose:** precision NEG gamma BASE +2.00% vs FAST +0.19% vs TIME10 +0.32%; POS gamma
+2.40 / +0.57 / +0.42. They cut the top-decile winners in half (NEG: +45.9% → +21.6%) in both states. Same lesson as
every earlier exit test: the book's edge lives in the few big winners, and anything that exits sooner gives it away.
Market gamma doesn't change that.

**Exploratory (not bar-bearing):** by VIX tercile instead of gamma, faster exits are WORSE in the high-VIX third:
FAST − BASE, top tercile minus the rest, −3.50pp (t −2.27) precision / −1.74pp (t −3.73) generic; TIME10 the same
sign. The opposite of "exit faster when the tape is unstable": in high-vol tapes the fast trail whipsaws out of
trades that go on to work. Consistent with the stress-bucket result (buy/sell into fear, don't flee it). It would
need its own pre-registration to count.

## Consequences
- No state-dependent exit. Keep the 20-EMA trail in all regimes.
- The idea's feedback version (knob adaptation) remains queued inside the adaptive-trader sim; its prior is now lower
  still, since neither market state nor, previously, trailing results pick a better exit.

# Breitstein test 3: the capitulation counter-trend long (prior-bar-high trigger), A/B against the bare trigger

_2026-09-19 · `run_counter_trend_long.py` · log `logs/counter_trend_long_2026-09-19.log` · summary
`counter_trend_long_summary_2026-09-19.csv` · spec `data/lance_breitstein/principles/trend-definition-and-counter-trend-entry.md`_

## Verdict

**Fails, as the mirror of the bouncy-ball short predicted.** Every exit arm of every cell is negative.
The extension gate (≥ 3 ADR below the 20 EMA, still in a down leg) does not rescue the prior-bar-high
trigger: it makes the absolute result *worse* (−0.15R vs −0.08R on the slow arms) while inflating the
"edge vs control" only because the same-name control is falling harder (−0.43R). Deeper extension and
the capitulation-volume arm are worse still. His trail (`trail_bar`) never beats `ema20`. Both ledger
rows `passed = False`.

## What was run

Liquid panel, 1,743 names, signals 2019-10 → 2026-09, long at next open, 10 bps each side, hold 5,
stop = the signal bar's low, control = same name, random session, same month.

| cell | definition | n |
|---|---|---|
| A | as of yesterday `(ema20 − close)/(close·ADR/100) ≥ 3` and `close < close[−5]`; today `close > high[−1]` | 9,015 |
| B | the same trigger in a down leg with extension < 3 ADR (disjoint from A: the trigger without the setup) | 155,514 |
| B-all | the trigger in a down leg, any extension | 164,529 |
| A sweeps | extension ≥ 2 / ≥ 5 ADR; flush-low stop `min(low[−1], low)`; hold 10 | 25,079 / 1,594 / 9,567 / 9,015 |
| V | A + flush-bar dollar volume ≥ 2× its trailing-20 mean (the capitulation definition) | 1,044 |

Extension below the 20 EMA on trigger days: median 0.6 ADR, p90 2.4, p99 5.1 — so ≥ 3 ADR is the top
~5% of down-leg breaks.

## Results (mean R)

| cell | stop_hold | t1R | trail_bar | ema20 | best-arm ctrl | edge | t (best) | win |
|---|---|---|---|---|---|---|---|---|
| **A ≥3 ADR** | −0.154 | −0.326 | −0.149 | −0.149 | −0.43 | +0.33 | −2.4 | 38% |
| **B <3 ADR (no gate)** | −0.085 | −0.290 | −0.093 | −0.084 | −0.15 | +0.06 | −4.2 | 40% |
| B-all any extension | −0.089 | −0.292 | −0.096 | −0.087 | −0.15 | +0.06 | −4.4 | 40% |
| A ≥2 ADR | −0.092 | −0.270 | −0.091 | −0.090 | −0.25 | +0.33 | −3.3 | 43% |
| A ≥5 ADR | −0.401 | −0.472 | −0.380 | −0.238 | −0.14 | +0.18 | −2.2 | 34% |
| A, flush-low stop | −0.116 | −0.185 | −0.101 | −0.083 | −0.14 | +0.24 | −4.0 | 42% |
| V (+2× volume) | −0.401 | −0.458 | −0.311 | −0.227 | −0.17 | +0.10 | −2.7 | 33% |
| A, hold 10 | −0.106 | −0.300 | −0.176 | −0.148 | −0.52 | +0.41 | −1.5 | 42% |

Halves (A, ema20): −0.13 / −0.16. Halves (B, ema20): −0.10 / −0.07. Nothing positive anywhere.

## Reading

1. **The trigger alone is a coin flip with costs.** B's edge vs its control is +0.00 to +0.06R on
   155k signals: a close above the prior bar's high in a down leg selects nothing.
2. **The extension gate selects names that keep falling.** A's control is −0.43R (vs −0.15R for B):
   a random session in a name that is 3+ ADR under its 20 EMA loses money over the next week. The
   trigger picks a slightly less bad day inside that (+0.33R vs control) but the trade is still −0.15R.
   This is a *day* selection inside a losing *name* selection — the same shape as every failed
   pattern in the ledger, and the precision-over-recall rule says the absolute sign is what counts.
3. **More capitulation, worse result.** ≥ 5 ADR: −0.24 to −0.47R, 34% win. Adding the 2× volume
   flush: −0.23 to −0.46R, 33% win. His "the flush is the only invalidation" reads as: the flush low
   gets taken out.
4. **Mirror of the bouncy-ball short confirmed, with a twist.** The short lost −0.34R *against* a
   control that made +0.34/+0.48 (short exposure paid; the break trigger threw it away). The long
   loses −0.15R against a control that loses −0.43R (long exposure in these names bleeds; the
   trigger salvages a little). In both directions the names are trending and the counter-trend
   break entry is the wrong side of it on daily bars.
5. **`trail_bar` vs `ema20`:** tied in A (−0.149 each), `ema20` best in 6 of 8 cells. His trail
   does not win; the exit-timing ordering holds again (`t1R` worst in every cell).
6. The flush-low stop and the 2-ADR gate are the "least bad" cells (−0.08 to −0.09R) and both are
   indistinguishable from the bare trigger. Nothing to sharpen.

## What was not run

The intraday VWAP-veto arm (long entries above session VWAP ≥ 15 min vs the same detector below
VWAP without a capitulation bar). Parked: the daily A/B was the deliverable and the intraday
detector family is already measured at −0.10 to −0.13R (Stage A). A daily-bar null is not a
refutation of the intraday claim; it is a refutation of the daily-bar version we could trade.

Nothing changes in the repo. Counter-trend entries on daily bars: 0 for 2 (short and long).

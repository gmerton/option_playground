# Cut size before earnings on an open breakout — Kell principle 9 (2026-09-27)

`run_earnings_cut.py` (pre-registered; one declared change: 2019–26 pools, as every exit test). Log
`logs/earnings_cut.log`; events `logs/earnings_cut_{precision,generic}.csv`.

## Verdict: NULL on return · a RISK lever that costs what any trim costs

Trades still open at a pre-print close, each matched to same-date open trades with **no** print within ±10 sessions
(same days-in-trade and open-gain buckets) that get the same cut, so the general cost of trimming is netted out.

| | precision (196 events) | generic (873 events) |
|---|---|---|
| **CUT40 diff-in-diff (PRIMARY)** | **+0.94pp, t 0.72** (halves +1.98 / −0.24) | −0.25pp, t −0.59 |
| raw CUT40 − HOLD / same cut with no print | −1.99 / −2.48pp | −1.12 / −0.74pp |
| EXIT diff-in-diff | +2.36pp, t 0.72 | −0.63pp, t −0.59 |
| cushion ≥ 1 ADR / < 1 ADR (CUT40 DiD) | +1.46 (t 0.78) / −0.56 (t −0.35) | −0.34 / −0.20 |

Per year the primary swings from +4.8 (2020) to −7.4 (2024): no stable sign.

**What cutting does do (on print trades, precision):** sd 46.9 → 41.9%, p5 −11.4 → −7.4%, top-decile mean +139 →
+121%; mean +25.1 → +23.1%. Exiting fully: p5 −2.4%, mean +20.1%.

## Read
- Earnings add nothing to the decision beyond the general trade-off of trimming a winner: a cut before a print costs
  about what the same cut costs on any other day (≈ −2pp on a +25% average open winner) and buys a smaller left tail.
  The cushion split doesn't change that.
- Kell's rule is a legitimate RISK preference (smaller gap risk for less upside), not an edge. Same classification as
  the 21-DTE close and the drawdown-cut sizing rule.
- The cohort is conditioned on still being open at the print (mean +25%); the matched control carries the same
  conditioning, so the comparison is fair.

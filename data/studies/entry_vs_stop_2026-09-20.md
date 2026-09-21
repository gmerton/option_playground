# The ledger's biggest anomaly: our patterns select well and enter badly (2026-09-20)

**Found by following up the FTD split.** That test showed post-FTD breakout names had a *positive*
random-later control (+0.045 to +0.080R) and a *negative* signal (−0.08 to −0.20R). Checking the
ledger, that is not a one-off:

- **22 of 40** daily patterns have the same-name random-later control beating the signal.
- **9** have a positive control against a negative signal.
- Every breakout variant: signal **−0.21 to −0.33R**, control **+0.13 to +0.21R**. A **~0.4R swing
  from entry timing alone**, holding name selection, stop rule and exit arm constant.

## Entry or stop?

Two explanations with opposite fixes. **A (entry):** the breakout bar is by definition extended, so
you buy the worst price of the move. **B (stop):** the breakout bar is a wide-range bar, so a stop
struck off it sits in that day's noise; the move is fine, the stop converts it to a loss.

They separate by measuring the same entries with and without a stop. `run_entry_vs_stop.py`,
44,062 house breakouts vs 43,344 same-name later controls:

| stop 1 ADR | sig raw % | ctl raw % | **raw gap** | sig R | ctl R | sig stopped | ctl stopped |
|---|---|---|---|---|---|---|---|
| 5d | 0.040 | 0.451 | **−0.411** | 0.014 | 0.103 | 48.4% | 48.0% |
| 10d | 0.614 | 0.874 | **−0.259** | 0.051 | 0.140 | 62.4% | 61.9% |
| 21d | 1.549 | 1.623 | **−0.074** | 0.123 | 0.199 | 73.1% | 73.2% |

**It is the entry (A).** Two independent confirmations:

1. **The raw gap is negative at every horizon** — with *no stop at all*, the breakout entry still
   underperforms a random later entry in the same name.
2. **Stop-out rates are identical** (48.4 vs 48.0, 62.4 vs 61.9, 73.1 vs 73.2). The stop is not
   discriminating between the two, so it cannot be the cause. Same at a 2-ADR stop.

## The mechanism, measured

Entry location relative to the prior 20-session high, in ADR:

- **breakout entry: +0.52 ADR above it**
- **random later entry: −2.09 ADR below it**

**A 2.6 ADR difference in price paid for the same name.** That is the whole gap, and it is the panel-
scale version of the house rule already on the desk from the August lens: *within 1 ADR of the 21 EMA;
the 1–2 ADR band lost −$4.6k; >2 ADR is a chase.* The breakout, as a rule, systematically buys the
extended end of that distribution.

⚠ The R levels here (+0.01 to +0.12) are milder than the ledger's (−0.21 to −0.33) because this
version has no slippage, no `t1R` take-profit cap and no `R_CLIP`. The t1R arm caps winners at 1R
while letting losers run to the stop, which amplifies any entry disadvantage. Direction and ranking
match; magnitudes are not comparable.

⚠ Tension to resolve: the pullback study found breakout entries *best* on raw percent (+2.6%/trade)
against pullback entries' +1.2–2.4%. Different cohort and horizon, so not a direct contradiction, but
it is not yet reconciled and should not be waved away.

## What to build

The control is "a random later session", which is not tradeable. The finding makes it one: the useful
variable is **extension at entry**, and it is already computable (`(entry / prior 20d high − 1) / ADR`).

**Next test, ~20 lines in the harness:** the same house breakout, but entry deferred until price
retraces to ≤0 ADR above the prior 20-session high (i.e. back to the breakout level), with a cap on
how long to wait. If the 2.6-ADR location gap is the mechanism, that rule should recover most of the
0.4R — and unlike the control, it can actually be traded.

# The straddle's −50% stop is a cost, not a rescue (2026-09-20)

**VERDICT: INVERTED · MECHANISM.** The playbook's −50% stop does not rescue trades — it destroys
value. **Drop it.**

**What it replaces.** The playbook modelled the stop as a loss clip, `max(roc, −50)`, worth +6.69pp
and 43% of arm 4's headline by "rescuing" 29.3% of trades. That was an assumption: it presumed you
always exit at exactly −50%. This path-simulates it on real daily marks for both legs of all 4,573
arm-4 entries (100% coverage, 43,203 leg-days).

## Two things the clip got wrong

**1. You do not exit at −50%.** A 7-DTE straddle gaps through the level rather than gliding to it.
**Median exit −59.7%, mean −64.3%.** The clip's whole contribution was the gap between the assumed
−50% and where you actually get out.

**2. Stopping means selling, so you cross the spread a second time.** The entry-slippage study could
treat cost as one-sided only because a held straddle settles at intrinsic. A stopped one does not.

| arm 4, folds 2021–25 | mean |
|---|---|
| no stop, mid entry | +8.77% |
| **CLIP assumption** `max(roc,−50)`, mid entry | **+15.46%** ← the published number |
| PATH, mid entry / sell at mid | **+8.86%** ← *identical to no stop* |
| PATH, mid entry / sell the bid | +4.80% |
| **PATH, measured entry fill / sell the bid** | **+2.89%** |

**At mid, a path-simulated stop is worth nothing** (+8.86% vs +8.77% unstopped). The entire +6.69pp
was the −50%-exactly assumption. Once the exit crossing is added it goes clearly negative.

## Why: the stopped cohort would have done better held

1,910 of 4,573 trades (41.8%) breach the level.

| stopped cohort (n 1,910) | mean | median |
|---|---|---|
| exit at the stop | **−64.26%** | −59.69% |
| **held to expiry instead** | **−54.75%** | −62.95% |
| **cost of stopping** | **−9.51pp** | |

**69.8% of stopped trades would have done better held**, and **7.6% would have finished positive.**
Meanwhile the never-stopped cohort returns **+54.33%** — that is where the strategy's money is.

This is the convexity argument, measured: a long straddle is **already defined-risk**. The stop does
not reduce the maximum loss — you cannot lose more than the premium either way — it just realises a
bounded loss early, at a worse price, and forfeits the trades that would have come back.

## The honest number

| arm 4, measured entry fill | mean |
|---|---|
| **no stop** | **+6.73%** |
| with the path-simulated stop | +2.89% |

**Dropping the stop is worth +3.84pp.** Per fold, unstopped and filled: every year positive.
With the stop, 2025 is −0.32%.

⚠ Marks are **daily closes**. A real intraday stop triggers more often and at worse prices, so every
number here is an **upper bound** on the stop's value. The conclusion only strengthens.

## Convergence

Three independent lines in this book now say the same thing about long convex positions:
the event-convexity study (a stop ejects you from the right tail that is the only source of P&L),
the exit-timing study (same-day exits are the negative bucket in both books), and Ravish's
"position for zero" — the one piece of his advice that tested well. This is the fourth.

## What changes

- **Remove the −50% stop from the straddle playbook.** Size so the full premium can be lost, which
  is what a defined-risk long-premium position already implies.
- The strategy's honest expectation is **+6.73%** at a realistic fill — lower than the +13.57% quoted
  this morning, because that figure still carried the clip. It is now assumption-free: real entry
  quotes, real exit path, no modelled rescue.

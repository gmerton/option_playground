# Can the hold/fail split be called at entry? (2026-09-20) — NO

`retrace_entry_2026-09-20.md` found the breakout book is bimodal: 23.6% of breakouts never return to
the level and average **+1.273R**, 76.4% return and average **−0.374R**. A **1.647R spread**, and the
+0.014R book average is a blend of the two. That made the question: **is the split callable at entry?**

**Answer: no.** Nine features already in the book, scored against this target for the first time.
The best single gate captures **3.5% of the available spread** and nothing approaches the house bar.

**Method.** `run_breakout_hold_predictors.py`, 43,970 house breakouts. Two numbers per bucket, and
only the second is tradeable: **held%** (share that never returned — the classification) and **meanR**
(every breakout in the bucket — what gating on it would actually earn).

## Univariate, ranked by meanR spread

| feature | held% spread | **meanR spread** | monotonic | best bucket meanR |
|---|---|---|---|---|
| dist_21ema_ADR | 13.7pp | **0.110** | 0.9 | +0.071 |
| rvol20 | 18.8pp | 0.081 | 0.9 | +0.054 |
| pct_off_52w_high | 4.2pp | 0.078 | 0.8 | +0.059 |
| dolvol | 10.7pp | 0.077 | 0.9 | +0.052 |
| range_pos | 3.4pp | 0.051 | 0.2 | +0.042 |
| adr_pct | 1.0pp | 0.044 | 0.2 | +0.035 |
| gap_ADR | 14.0pp | 0.041 | 0.8 | +0.030 |
| **ext_above_level_ADR** | **28.7pp** | **0.036** | 0.5 | +0.033 |
| sma_stacked | 0.3pp | 0.013 | 1.0 | +0.022 (**un**stacked) |

Baseline (no gate): **+0.014R**. Ceiling if the split were called perfectly: **+1.273R**.

## Three things worth keeping

**1. The best classifier is not the best gate.** `ext_above_level_ADR` has by far the largest held%
spread (28.7pp) and nearly the smallest meanR spread (0.036). Classification ≠ profit: bigger
extension means further to fall before the level is touched again, so it predicts *returning* partly
**mechanically** — it is close to tautological and carries almost no earnings information. Any future
work on this target must score meanR, never hit-rate.

**2. Distance to the 21 EMA is the best of a weak lot**, monotonic at 0.9, best bucket −0.7 to 1.8 ADR.
That **directionally confirms the August lens rule** (within 1 ADR of the 21 EMA) at panel scale — but
it is worth +0.057R over baseline, not a regime change.

**3. `sma_stacked` inverts** — the unstacked bucket earns more (+0.022 vs +0.009). The spread is 0.013R,
almost certainly noise, but it is the third time a "leadership" filter has failed to sort in this book
(after leading-group filtering and the top-40 group claim).

## Combinations do not stack

| gate | n | held% | meanR | vs base | t |
|---|---|---|---|---|---|
| close to 21 EMA | 8,800 | 18.9% | +0.071 | +0.057 | +1.97 |
| rvol20 > 1.66 | 8,797 | 35.9% | +0.054 | +0.039 | +1.83 |
| 21EMA + rvol | 696 | 23.0% | **+0.112** | +0.098 | 1.39 |
| 21EMA + rvol + near 52w high | 292 | 22.6% | +0.070 | +0.056 | 0.88 |
| 21EMA + rvol + upper half | 480 | 21.2% | +0.048 | +0.034 | 0.07 |
| five gates | 89 | — | too thin | | |

The best combination is **+0.112R on 696 trades with t 1.39** — it buys ~7% of the 1.647R spread and
falls apart as more conditions are added. (The t here is rough: it compares a day-clustered mean against
a trade-weighted baseline. Treat it as an order of magnitude, not a test.)

## Verdict

**The bimodality is real and it is not selectable.** The +1.27R cohort exists but cannot be identified
at entry from anything currently in the book. This is consistent with everything else the book has
learned: [[the size lever]] is exclusion rather than prediction, regime state does not forecast, and
the alert study found signals mark states rather than moments.

Practical position is unchanged — fixed small sizing, location discipline near the 21 EMA (now with
panel-scale support), and no attempt to pick which breakouts will hold. The honest read is that the
breakout book's average is what it is because the good cohort is **unknowable in advance**, not because
the entry rule is fixable.

# Is there any stop level or timing that helps? (2026-09-20) — no, and the gradient says why

**VERDICT: NULL across the whole family · MECHANISM.** Twenty combinations of stop depth × timing.
**None beats not stopping.** The optimum of the stop family is the null stop.

**The question.** Killing the −50% stop left an obvious objection: −50% is one arbitrary point. Two
levers were worth sweeping — a **deeper** stop fires only when the position is nearly dead, cutting
far fewer trades that still have time to come back; and a **late** stop targets the Wed/Thu before a
Friday expiry, where theta is brutal and a straddle down hard has little chance of recovering.

Baseline: arm 4, folds 2021–25, measured entry fill, **no stop: +6.73%**.

## The sweep

Selling the bid to close (a stopped trade crosses the spread), `vs_nostop` in pp:

| exit when down | any DTE | ≤3d | ≤2d | **≤1d** |
|---|---|---|---|---|
| −50% | −3.84 | −3.77 | −3.69 | −3.05 |
| −65% | −2.76 | −2.68 | −2.63 | −2.21 |
| −75% | −1.99 | −2.00 | −1.87 | −1.58 |
| −85% | −1.37 | −1.37 | −1.31 | −1.01 |
| **−90%** | −0.92 | −0.92 | −0.85 | **−0.71** |

**Both intuitions are directionally right.** Deeper is better at every timing (−3.84 → −0.92), and
later is better at every depth (the DTE≤1 column wins its row every time) — the theta reasoning
holds. The best cell, **exit at −90% with one day left**, stops only 7.6% of trades and loses just
**−0.71pp**.

But **0 of 20 cells cross zero**. The gradient in both levers points the same way — *stop less* — and
its limit is *don't*.

## Why even a −90% / 1-DTE stop loses

The bid/ask spread on a straddle widens sharply as it approaches worthlessness:

| straddle worth | median spread | mean |
|---|---|---|
| **<15% of cost** | **16.0%** | **26.7%** |
| 15–35% | 9.8% | 15.5% |
| 35–60% | 8.4% | 14.2% |
| 60–150% | 7.7% | 13.8% |
| >150% | 8.1% | 12.0% |

**The cost of cutting is at its worst exactly when you want to cut.** Selling a near-dead straddle
means crossing a spread worth a sixth to a quarter of what is left, against a residual that is only a
tenth of the position. Add the small share that still comes back on gamma in the last day, and the
deepest, latest stop still cannot pay for itself.

## What this settles

The −50% stop was not badly *calibrated* — the whole family is dominated. Combined with
[straddle_stop_path_2026-09-20.md](straddle_stop_path_2026-09-20.md), the straddle's exit rule is
**hold to expiry, no stop**, and the honest expectation stays **+6.73%** at a realistic fill.

One thing the sweep does add: **every stopped variant has zero negative folds except −50%/any DTE**,
which is the one currently in the playbook. So the published rule is also the single worst cell in a
20-cell grid — not merely suboptimal.

⚠ Daily marks throughout, so an intraday stop triggers more often and worse. Upper bounds again.

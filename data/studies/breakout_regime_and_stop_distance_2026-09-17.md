# Breakout pool: stop distance and regime feedback (2026-09-17)

`run_regime_feedback.py`. Pool = 3,539 precision-shaped breakouts 2019-10 .. 2026-09 (ADDV >= $50M, ADR 4-7, within 15% of the 52wk high, stacked with the house slack, close clears the 15-day pivot on RVOL >= 1.1, upper-half close, gap < 5%, day < 8%). Stop = entry-day low judged on the close; exit = first close under the stop or the 20 EMA; 60-session cap. Mean R +0.55, +2.6% per trade.

## A. Where tight stops come from (Gabe: "how do we get those really tight Luk / Qullamaggie stops?")

| entry (close) above the day's low | n | R | ret | win | stopped | ret per 1% risked |
|---|---|---|---|---|---|---|
| 0-1.5% | 21 | -0.94 | -1.0% | 19% | 76% | -0.74 |
| **1.5-3%** | 562 | **+0.90** | +2.0% | 31% | 65% | **+0.82** |
| 3-5% | 1,277 | +0.61 | +2.3% | 29% | 61% | +0.57 |
| 5-8% | 947 | +0.44 | +2.6% | 33% | 47% | +0.42 |
| 8%+ | 182 | +0.23 | +1.6% | 40% | 35% | +0.17 |

The % return is flat across buckets; the return per unit of risk doubles from the 5-8% bucket to the 1.5-3% bucket because the denominator shrinks. **Tightness that pays is structural** -- a breakout day whose low sits 1.5-3% under the close -- not manufactured by placing a stop 1% under an entry that is 5% above the low (see the entry study: tight stops by entry timing lose under any execution). Below 1.5% the stop is inside the noise.

Surprise: by prior contraction (10d range / prior 20d range) 0-0.5: R +0.18 · 0.5-0.7: +0.36 · 0.7-1.0: +0.42 · >1.0: **+0.91**. Breakouts after range EXPANSION did better than after tight contraction, on hundreds of trades each. Anti-VCP. Unverified beyond this cut; check before believing.

**Rule candidate (fits the daily-close process):** prefer breakouts whose entry day closed 1.5-3% off its low; size to that low.

## B. Can the paying months be forecast? (Gabe: "are the only good setups in March-May?")

Yes for 2026: the layer-2 close entry returned Feb -0.3 / Mar +10.9 / Apr +24.1 / May +9.8 / Jun +0.6 / Jul -1.7 / Aug +0.7 / Sep +1.1%. Across 2019-2026 the pool is negative or flat in 2019, 2021, 2022 and carried by 2023-2025.

For each session, what was knowable that day vs the mean R of the NEXT month's new breakouts (1,223 sessions, t on non-overlapping months):

| signal | next-month R by quartile / state |
|---|---|
| last month's breakouts' 10-day return (worst -> best) | +0.37 / +0.28 / +0.12 / +0.41 -- no ordering, rank corr +0.01 |
| share of last month's breakouts stopped within 10 days (fewest -> most) | **+0.79 (61% positive, t 2.0)** / +0.05 / +0.16 / +0.17 -- rank corr -0.12 |
| number of breakouts last month | +0.40 / -0.04 / +0.46 / +0.34 -- none |
| SPY state | bear +0.32 / chop +0.57 / up +0.22 -- none |

Unconditional next-month R +0.29; **positive in 47% of non-overlapping months**; of 83 months, 42% have a positive mean R and **the top 8 months supply 68% of all positive R**.

**Reading.** The edge is episodic and, by every signal tested here (including the strategy's own recent results), unforecastable a month ahead. The one lean is Luk's own-P&L rule in the direction he states -- when last month's breakouts were rarely stopped out, the next month tends to keep paying -- but the reverse is not true (a stop-out-heavy month is not followed by a worse one). Regime management is therefore the SIZING: fixed small risk per trade keeps the strategy alive through the ~53% of months that do not pay, and the few that do carry the year. Nudge, not switch: after a month where breakouts held, keep size or lean in; after a month of stop-outs, do not add risk. Consistent with `trailing_regime_validation.md` (no persistence in market-level regime) and `industry_rotation_detection_study.md` Part IV.

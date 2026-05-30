# Morning Flush Reversal (MFR)

**Status:** exploring (N=1 — collecting examples before committing thresholds)

## Idea
A sharp morning capitulation selloff ("flush") drives price deep below VWAP into
oversold, sellers exhaust, and price reverses to trend up for the rest of the
session. We want to buy the *reclaim* off the flush low — not the falling knife,
and not so late that the move is gone.

## Anatomy (gate → trigger → invalidation)
*Thresholds below are PROVISIONAL — drawn from one example (PL). To be confirmed
as more examples accumulate.*

- **Gate (the flush):** within roughly the first hour, price is sharply down from
  the open (≈ −5% or more), **deeply below VWAP**, and **RSI oversold (~25)**.
  Volume need not be a dramatic climax (PL's low bar was only ~1.0× average).
- **Trigger (the reclaim):** the first momentum reclaim after the low. Candidates,
  earliest→latest on PL: RSI back up through 40, two consecutive higher-high/
  higher-low bars, 9 EMA reclaiming 20 EMA, then close back above VWAP.
- **Invalidation:** a close that undercuts the flush low. (PL never did — the low
  held all day.)

## Open questions
- Earliest triggers (RSI>40, higher-highs) caught PL within 3 min and 93% of the
  move — but how often do they *fire and fail* on days with no real reversal?
  Need non-reversal days to measure the false-positive rate.
- Does the gate need a volume-climax condition, or is below-VWAP + oversold enough?
- Is the "morning" timing constraint real, or do afternoon flushes behave the same?
- Best trigger is a tradeoff: earlier = more of the move but more whipsaw; VWAP
  reclaim = later but cleaner confirmation.

## Examples
| Symbol | Date | Open→Low (drop) | Low→High (rally) | Low time | Ctx @ low (VWAP / RSI / vol) | Best early trigger (entry, %off low, %ahead) |
|---|---|---|---|---|---|---|
| PL | 2026-05-29 | 49.12→44.78 (−8.8%) | 44.78→51.27 (+14.5%) | 10:26 | −4.3% / 25 / 1.0× | RSI>40 @10:29 (45.26, +1.1%, 93% ahead) |

<details><summary>PL 2026-05-29 full card</summary>

```
===== PL  2026-05-29  (390 bars) =====
  open 49.12  low 44.78@10:26 (-8.8%)  high 51.27@15:58 (+14.5% off low)  close 51.14
  CONTEXT @ low: -4.3% vs VWAP, RSI 25, vol 49641 (1.0x ma)
  SHAPE: low-before-high (reversal)
  TRIGGERS after low:   fires   entry  %off_low  %ahead
    RSI up through 40      10:29   45.26     +1.1%     93%
    2x higher-high+low     10:29   45.26     +1.1%     93%
    9 EMA > 20 EMA         10:33   45.74     +2.1%     85%
    close reclaims VWAP    10:55   46.66     +4.2%     71%
```
</details>

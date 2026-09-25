# Volume signature at the pullback low (2026-09-25)

Script: `run_volume_low_signature.py` (pre-registered 239d2ef), on the look-ahead-fixed ladder events.
Log: `data/studies/logs/volume_low_signature.log`; table `volume_low_signature_2026-09-25.csv`.

## Verdict: NULL 0/12 · volume identifies lows that HOLD, but the price already reflects it · MECHANISM

K1 entries (first close above the low bar's high) after ≥ 1-ADR pullbacks: P2 14,405, P1 2,647. Each cell compares
tagged vs untagged entries in the same rung (a within-rung difference), excess vs the same-date control,
month-clustered.

| P2 (PRIMARY population) | tagged | excess diff +20 | t | low holds 20d, tagged vs rest |
|---|---|---|---|---|
| V1 dry pullback (≤ 0.8× avg vol) | 28% | −0.14pp | −0.31 | **33% vs 39% (z −6.9)** |
| V2 turn day ≥ 1.5× avg vol | 11% | +0.21pp | +0.27 | **44% vs 37% (z +6.0)** |
| **V3 both (PRIMARY)** | 1% (n 108) | −0.19pp | −0.10 | 44% vs 37% (z +1.3) |

P1: every difference fails (t ≤ |2.3|, too few early-sample months for halves). V3 leaves only 17 entries.

- **The expanding-volume turn day does mark lows that hold:** 44% vs 37%, z +6. **It earns nothing extra.** The
  +20 difference is +0.2pp (t 0.27) and +60 is +1.0pp (t 0.80). That is the ladder's lesson again: the market prices
  the information you would use to be sure.
- **The textbook "pullback on drying volume" is backwards here:** dry pullbacks hold *less* often (33% vs 39%, z −6.9)
  and earn no more. Light-volume dips drift lower instead of reversing.
- **Both together is rare** (1% of entries) and flat.

## What it taught
- **MECHANISM:** hold rate and return are separate. A feature can raise the probability that the low holds while
  adding no expected return, because the entry price already moved to reflect it. For this question, the target to
  test is return (or return per unit of risk), never hold rate alone.
- Across the ladder, the support tag and volume: **on daily bars there is no signal that you are exiting a low that
  earns more than buying the dip or the close.** The remaining untested layer is intraday (Polygon backfill).

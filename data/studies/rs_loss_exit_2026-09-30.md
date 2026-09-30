# RS-loss exit vs the house 20-EMA trail (2026-09-30)

**Verdict: NULL · UNDERPOWERED-by-construction (primary) · MECHANISM (arm C's pass is exposure, not RS).**
Source claim: OptionsPlay 9VylBGWJVT8 [21:05–22:26], "get out when the name drops off the leaderboard".
Spec, pre-registration: `run_rs_loss_exit.py` docstring (committed before the run). Log: `logs/rs_loss_exit.log`;
exploratory controls: `logs/rs_loss_exit_exploratory.log` (script `logs/rs_loss_exit_exploratory_controls.py`).

RS tier = count of h ∈ {21, 63, 126} with name/SPY relative return > 0. Close entry on the breakout, day-low stop on
the close, 60-session cap, % per trade, paired, t clustered by entry date, halves split 2023-01-01.

## Primary: B (tier drops to ≤ 1, or the 20-EMA trail) − A (20-EMA trail), precision pool

| pool | n | B − A | t | halves | B ≠ A | B − A on that subset |
|---|---|---|---|---|---|---|
| precision (PRIMARY) | 1,965 | +0.023pp | 2.49 | +0.059 / −0.000 | **1.1% (21 trades)** | +2.13pp (t 2.35) |
| generic | 7,666 | +0.053pp | 0.46 | +0.056 / +0.051 | 4.0% (309) | +1.31pp (t 2.70) |

Fails the bar (t < 3, back half zero). **The test barely exists:** 93% of precision entries are already tier 3,
and the 20-EMA trail fires before the tier falls to ≤ 1 on 99% of trades. Losing RS *is* the price fall the trail
catches. On the differing subset, B beats a random earlier exit of the same length by +0.92pp (t 1.30, precision)
and +0.29pp (t 1.36, generic), so exiting earlier accounts for most of B − A.

## Arm C (the RS condition alone, no trail): clears the bar, and it is an artefact

C − A = **+1.25pp, t 3.68**, halves +1.25/+1.25 (generic +1.13pp, t 4.53). C holds 22 sessions against A's 14.
Exploratory controls (not pre-registered):

| C minus … | precision | generic |
|---|---|---|
| stop + 60 cap only, no trail (HOLD60) | **−0.07pp, t −0.69** | −0.14pp, t −2.08 |
| 50-SMA close trail | +0.41pp, t 3.00 | +0.31pp, t 1.84 |
| 50-EMA close trail | +0.35pp, t 3.09 | +0.34pp, t 1.62 |
| a random hold length drawn from C's own | +1.21pp, t 2.88 (halves −0.14/+2.06) | +0.26pp, t 1.12 |

The RS-only exit is no better than having no trail at all. Its lead over A is the STOP_ONLY − BASE gap already
measured and shown to be about ¾ beta (`trail_cost_exposure_2026-09-26.md`: +0.30pp t 1.16 after a beta-matched
SPY fill). The RS state contributes nothing beyond holding longer in high-beta names during a bull sample.

## Consequences

- Keep the 20-EMA trail. No RS-based exit is adopted.
- The spec's follow-on (three-horizon RS tier as a *selection* sort) was gated on "the RS state carries any
  information". It does not, so the follow-on is not queued.

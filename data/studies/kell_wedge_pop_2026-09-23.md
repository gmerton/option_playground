# Kell Wedge Pop — base vs no base, and vs the house breakout (queue [WL-1]) — 2026-09-23

**Verdict: NULL · YIELD MECHANISM.** The wedge pop matches neither same-date control. Kell's claim that the
tight base with a higher low is what matters (vs merely crossing back above the EMAs) gets no support: +0.24pp,
t 0.40, halves of opposite sign. The setup's raw return looks better than the house breakout's
(+1.26% vs +0.54%) only because it fires on **good dates**, the rebound sessions after a correction. On those
same dates, ordinary breakouts earned more.

Script: `run_kell_wedge_pop.py` (pre-registration in the docstring, taken from
`data/traderlion/setups/kell_wedge_pop.md` §7–8 before running). Log: `data/studies/logs/kell_wedge_pop.log`.
Trades: `data/studies/logs/kell_wedge_pop_EMA{20,10}_trades.csv`.

## Spec (as registered)

- **Context:** close ≥ EMA100; weekly extension (close/EMA50 − 1)/ADR ≤ 3; ADR ≥ 3%, liquid.
- **Correction:** ≥ 5 closes below EMA20 in t−40..t−1, and some session in t−40..t−8 at least 1.5 ADR below EMA20.
- **Higher low:** min low of t−7..t−1 > the correction low.
- **Base (t−5..t−1):** span ≤ 2 ADR, mean daily range ≤ 0.8 ADR, base low within 1 ADR of EMA20.
- **Trigger:** close > base high and > EMA10 and > EMA20; one per correction.
- **Entry, stop, exit:** entry at the close. Stop = base low on the close, floored at 0.5 ADR. Exit on the first
  close < EMA20 (primary) or < EMA10, cap 120 sessions, 0.10% slippage a side, scored in %.

**3,602 wedge pops in 1,166 names, 2019-10 → 2026-09.** The setup is not rare: it has power.

## Results

| exit | group | n | mean % | median entry vs 20d high (ADR) |
|---|---|---|---|---|
| EMA20 | wedge pop | 3,602 | **+1.26** (win 32%) | −0.17 |
| | all house breakouts | — | +0.54 | +0.33 |
| | MA-cross-only (structure control pool) | — | +0.48 | −1.85 |
| EMA10 | wedge pop | 3,602 | +0.40 (win 34%) | |

**Paired, same date** (per-signal diff, date-clustered t):

| cell | n | wedge pop | same-date control | diff | t | halves (<2023 / ≥2023) |
|---|---|---|---|---|---|---|
| **Q1 PRIMARY: vs other names' house breakouts, EMA20** | 3,579 | +1.18% | **+1.56%** | **−0.38pp** | **−0.28** | +0.71 / −1.25 |
| Q2 Kell's claim: vs MA-cross-only (no base / no higher low), EMA20 | 3,279 | +0.88% | +0.64% | +0.24pp | +0.40 | −0.13 / +0.51 |
| Q1, EMA10 | 3,579 | +0.34% | +0.69% | −0.35pp | −1.02 | +0.14 / −0.75 |
| Q2, EMA10 | 3,279 | +0.28% | −0.01% | +0.29pp | +0.35 | −0.49 / +0.87 |

**Neighbourhood (Q1 / Q2, EMA20; each rule moved alone):** every cell has |t| ≤ 1.75 and none has a sign that
holds. Depth 1.0: −0.33/+0.17. Depth 3.0: −0.23/+0.32. Span 1.5: −0.37/+0.19. Span 3.0: −0.17/+0.23.
Near 0.5: −0.48 (t −1.75)/+0.15. Near 1.5: −0.39/+0.09. It's a flat null, not a spike we missed.
(⚠ A few cells show the pooled mean diff and the date-clustered t with opposite signs; the t is the mean of
date means, so dates carry equal weight.)

**Harness (R, hold 120):** the best arm is ema20, edge +0.004R over `post` and +0.015R over `xname`, t 0.61.
Fails.

## Reading

1. **The raw +1.26% is date selection, not setup.** A wedge pop fires on a stock's rebound out of a correction,
   and those sessions cluster on market rebound days. House breakouts **on the same dates** earned +1.56%. An
   undated comparison (+1.26% vs the +0.54% pool) would have read as a +0.7pp edge. This is the same lesson as the
   VCP test, from the other side: the control must hold the date fixed.
2. **The structure adds nothing measurable.** Crossing back above both EMAs after a correction without the tight
   base or the higher low does about as well on the same date (+0.24pp, t 0.40, halves split). Kell's "it's the
   structure, not the MA cross" is **not supported** on daily bars.
3. **Entry location didn't rescue it either.** The wedge pop buys ~0.5 ADR lower relative to the 20-day high than
   the house breakout (−0.17 vs +0.33). The entry-extension mechanism predicted that would help. On the same
   dates it didn't, so that mechanism doesn't carry over to this setup at this small an offset.

## Caveats

- Daily bars only. Kell executes on 10–30-min bars using the daily EMAs, and re-enters on a 65-min higher low.
  Per the timeframe rule, a daily null doesn't refute the intraday version (1-min cache is 2026 only).
- Rule 5 is operationalised as "at some session in the window", slightly looser than "at the min-low session".
- His weekly-chart context (no trades under the 20-week EMA) is approximated by EMA100 on daily closes.

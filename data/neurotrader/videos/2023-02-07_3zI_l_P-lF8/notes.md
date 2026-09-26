# Do Moving Averages Actually Work as Support and Resistance?

**Video:** `3zI_l_P-lF8` · **Watched:** 2026-09-26 · **Published:** 2023-02-07 · 7:11

> **2.5/5 · no new test.** A neat, reusable way to score ANY level (bounce vs penetration through a ±0.5 ATR band),
> and the optimiser is inside the permutation null (good). But the null is wrong for the claim: shuffling returns
> destroys trend persistence too, so "price bounces off the MA" can't be told apart from "trends persist". And a
> bounce rate isn't a return. For us, the actionable version is already answered: EMA-pullback entries were
> +1.2–2.4%/trade, t ≤ 1.4, below the breakout entry (pullback entry study).

## Raw notes
- [00:47] Method: bands = MA ± 0.5 × ATR(200). Price above the MA = uptrend. Enters the band and leaves upward =
  **bounce**; leaves downward = **penetration**; a bar that jumps the whole band = penetration. Mirror for downtrends.
  Source: Osler (2000), "Support for resistance: technical analysis and intraday exchange rates".
- [02:23] BTC/USDT hourly 2018 → 2023, MA 72: 535 bounces / 332 penetrations = **61.7%** support bounce rate.
- [02:23–03:11] Sweep 24–200: support best 145 (64%), worst 36 (56%); resistance best 195 (65%); combined best 200 (64%).
  Longer MAs = fewer interactions.
- [03:59–05:35] Monte Carlo permutation: shuffle log returns, re-optimise the period on each of 1,000 paths. Best
  permuted ≈ 54%; real 64% beats all → p < 0.001. "I thought I was going to be disproving [it]... I was wrong."
- [06:21] Same on ETH and other coins, "some slightly weaker".

## Critique
- ⚠ **The null tests "any structure", not "MA-specific structure"** — the same flaw noted in his permutation-test
  video. Shuffling returns kills volatility clustering and trend persistence along with any MA-watching. Under
  momentum, a price above a rising MA will tend to "bounce" whether or not anyone watches the line. The right
  control holds the path fixed and moves the LINE: same-distance random levels, or a block bootstrap that keeps
  autocorrelation.
- A 60% bounce rate says nothing about payoff: penetrations can be larger than bounces. No P&L, no costs.
- Crypto hourly only.

## For this book
- No test: the tradeable form (buy the touch of the MA in an uptrend) is the EMA-pullback entry, already measured
  on our panel and weaker than the breakout entry (`project_pullback_entry_study`).
- ⭐ METHOD worth keeping: the band-exit classification is a neutral way to score a level. If we ever test "does
  the 20-EMA hold" for the trail, use this scorer with a **moved-line control**, not a return shuffle.

# Using Trade Dependence to Improve the Donchian Breakout Trading Strategy

**Video:** `BM3KZPg6zic` · **Watched:** 2026-09-26 · **Published:** 2023-06-26 · 12:03 · code: github.com/neurotrader888/TradeDependenceRunsTest

> **3/5 as METHOD · no new test; amends the queued adaptive-trader sim.** A clean, cheap tool (the Wald–Wolfowitz
> runs test on win/loss signs) and a result that points the OPPOSITE way to "push the gas after winners": on a
> trend-following system, trades after a LOSER were better and trades after a WINNER lost.

## Raw notes
- [00:00] Trade dependence = a strategy's trade outcome depends on the previous trade's outcome. Turtle rule: take a
  breakout only if the previous signal was a loser.
- [00:48] System: Donchian stop-and-reverse (long at a new N-bar closing high, short at a new N-bar low, always in),
  BTC hourly, lookback 24. **No fees or slippage**; he says costs "would destroy" it (small average trade).
- [04:01] Trade distribution: mode slightly below zero, fat right tail (a few trades make the money).
- [04:50] Scatter of previous vs next trade return: the big winners mostly follow a loss; after a winner the mean
  next trade is negative.
- [05:40] **Runs test**: count runs of equal signs, compare with the expected mean/variance under independence →
  z. Positive z = more alternation than chance (winner→loser, loser→winner). Lookback 24: **z 2.7**.
- [07:14] z across lookbacks 12–168: positive and "fairly high" nearly everywhere, highest at short lookbacks.
- [08:02–10:27] Filter "only after a loser": profit factor better than the base at **every** lookback; "only after
  a winner" unprofitable at almost every lookback.
- [11:14] ⚠ "In my experience trade dependence is rather uncommon. I've only seen strong trade dependence on trend
  following strategies." Autocorrelation of trade returns (vs sign): "never found it effective."

## Critique
- No costs, one asset (BTC hourly), no permutation test — the tool he sells in his own permutation video isn't used
  here. The "filter improves PF at every lookback" chart is his neighbourhood check, which is good practice.
- Partly mechanical in a stop-and-reverse system: consecutive trades share a price path (one's exit is the next's
  entry), so a big trend winner is followed by a reversal entry into a choppy top. The dependence may be structural
  to always-in systems, not a behavioural edge; our breakout book is NOT always-in, so don't assume it transfers.

## For this book
- ⭐ **Amend the queued adaptive-trader sim (TEST_INDEX §10)**: (1) run the runs test on each strategy's real
  trade sequence FIRST — it's minutes of work, and if z ≈ 0 the sim's shuffled-order control will show feedback
  sizing only reshapes risk, as the row already predicts; (2) add the **Turtle arm (skip / size down after a
  WINNER)** — the row's arms are all anti-martingale, and this is the one direction with a published precedent.
- Related: strategy localisation (WL-2b) found month-level persistence ρ −0.01; this is the trade-level version,
  which that study didn't measure.

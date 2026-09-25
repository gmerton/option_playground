# Self-regime holdout (A): do the strategy's own recent results say when to press? (2026-09-25)

Script: `run_self_regime_holdout.py` (pre-registered b20b0f6). Log: `data/studies/logs/self_regime_holdout.log`; trades
`logs/self_regime_trades.csv` (entry AND exit dates, reusable for the queued adaptive-trader simulation).

## Verdict: NULL on the holdout (primary underpowered) · the trade-level signal leans INVERTED · MECHANISM: the house breakout LOST money in 2010–19

2,226 house breakouts (the 9/17 pool definition) on liquid_panel_2009: **380 in the 2010-01→2019-09 holdout, 1,758 in
2019-10→2026-08.** Mean +0.86%/trade overall.

- **S1 PRIMARY — months after the fewest 10-day stop-outs** (cut fixed on 2019–26, stop share ≤ 0.43): holdout
  **+1.89pp, Welch t 0.94** (9 vs 9 months; halves +1.41 / +2.29); the in-sample replay is only +1.13pp t 0.52 with this
  trade set. Only 18 holdout months had enough trades, so this is underpowered, not a refutation. It does not confirm.
- **S2 — the last 20 CLOSED trades net positive (HOT) vs not (COLD):** holdout **HOT −1.82% vs COLD −0.89%, diff −3.71pp,
  t −2.17, both halves negative, 5/6 years**; the same sign inside SPY > 50d (t −1.75) and SPY < 50d (t −2.36), so it is
  not the market trend. Replay 2019–26: +0.69pp, t 0.46. **"Push the gas after a winning run" is not supported; if
  anything, a hot run precedes worse trades.**
- **⭐ The house breakout lost money out of time:** the 380 holdout trades average about **−1.2% per trade** (HOT −1.82 /
  COLD −0.89) vs +1.3% on the 2019–26 set. This agrees with the ADX holdout's −0.27%/trade on a broader breakout mask. The
  breakout's edge is concentrated in recent years, and the panel's survivor bias (names that later became big) did not
  rescue it.
- Book view (⚠ the log's "%/mo" is the SUM of trade percents per month, i.e. 100× a 1%-per-trade book): holdout ALWAYS
  Sharpe −0.81, HOT-only −0.82, 2×/0.5× −0.99; replay 0.69 / 0.53 / 0.67. No sizing rule improves the Sharpe in either
  window.

## What it taught
- **MECHANISM:** results do not come in exploitable streaks at the trade or month level (third NULL after the 9/17
  regime feedback and WL-2b). The queued adaptive-trader simulation should therefore expect feedback sizing to reshape
  risk, not add return. Its shuffled-order control will show that directly.
- **The bigger yield:** out of time, the house breakout is not a bread-and-butter strategy.

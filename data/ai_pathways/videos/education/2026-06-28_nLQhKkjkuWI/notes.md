# Supplemental Notes — 2026-06-28 "Claude Tested Over 9,000 Trading Strategies" (nLQhKkjkuWI)

Presenter Brendan (AI Pathways). Reviewed 2026-09-22 → `../../../2026-06-28_9000_strategies_review.md` (2/5).

⚠ **Chronology**: this video is the EARLIER of the two AI Pathways videos in the KB (2026-06-28 vs the ICT
video's 2026-08-06). Guardrails present in the ICT build — coin-flip null, an explicit luck-correction step in
the funnel, a sealed 2-year holdout run once — are **absent here**. Their method improved between June and
August; do not read this as a regression.

## The funnel, as narrated
- [02:34] 9,000+ backtests → **524** survivors after six filters
- [03:11] filter 1 = **out-of-sample Sharpe > 0.5** → removes "almost 8,000", leaves **1,218**
- [03:33] filter 2 = **max drawdown ≤ 35%**
- [04:10] filter 3 = in-sample-vs-out-of-sample degradation (overfit check)
- [04:18] filter 4 = minimum trade count → **524**
- (filters 5–6 never named on screen or in narration)
- [09:31] 524 → **478** after restricting to assets with ≥10 years of history (XLC excluded, launched mid-2018)
- [09:43] **64% of the 478 are mean-reversion** strategies

## Other numbers spoken
- [01:07] universe = 30 liquid assets: SPY/QQQ, all sector ETFs, gold, oil, bonds, BTC, ETH, large caps (AAPL, NVDA). Daily bars only — explicitly not intraday, futures or options
- [01:29] window = 15 years (≈2010–2025)
- [05:18] "**only 44% stayed strong out of sample**" of those that looked strong in-sample
- [07:30] mean reversion = the only family positive on average; trend, volume, composite, volatility, pattern all negative
- [08:27] bootstrap = surviving strategies' trades **reshuffled 500 times**
- [08:55] dual-momentum on NVDA: bootstrap max drawdown −61% / −51%
- [10:32] **top survivor by "score" = Turtle on Apple, 1.18** (unit never defined; a few other trend strategies rank high)
- [11:30] RSI mean reversion survives on **20 tickers**; Keltner reversion on **18**
- [13:39] cross-sectional momentum (rank a basket, long strongest / short weakest) "scored way better" than the
  ~0 of single-asset momentum — run separately, **outside the 9,000**; no figures given
- [15:02] regime layer = a **hidden Markov model** to label bear/trending/choppy/bull, then momentum in
  trending, mean reversion in chop. Asserted, not tested
- [17:36] prompt layer 3 is described as adding "multiple test corrections and realistic transaction costs" —
  ⚠ neither appears as a step in the funnel and no corrected count or cost figure is reported anywhere

## ⚠ What is never given
No CAGR, no Sharpe for any survivor, no equity curve number, no trade count, no parameter values, no benchmark
(buy-and-hold is never mentioned), no cost assumption, no null/control pass rate. The video is not reproducible
from its own content; the prompt screenshots are the deliverable.

## Caption garbles
- [00:00] "Claude's run" = "Claude to run"
- [10:54] "the fraud ones" = the flawed/fraught ones (the high-drawdown trend survivors)
- [11:59] "Great trend, volume, positive volatility, and pattern strategies" is garbled — from context this is
  the negative-category list, matching [07:40]
- [16:39] "school community" = **Skool** (paid community; the funnel)

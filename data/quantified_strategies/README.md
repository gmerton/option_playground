# Quantified Strategies KB

YouTube channel "Quantified Strategies" (quantifiedstrategies.com; Skool community "rulebasedtrading"). Short videos,
each presenting one fully specified, rule-based daily strategy with a backtest summary (Norgate data, which includes
delisted stocks). Skeptic-default scoring like every KB here.

`videos/<date>_<id>/` holds `transcript.txt` and `notes.md`.

| video | date | verdict |
|---|---|---|
| [This RSI Strategy Won 68% of 1,321 Trades](videos/2026-09-26_tjL4wcI403E/notes.md) | 2026-09-26 | **2.5/5 · no new test.** Fully specified Connors-style rules (close > 200 SMA, RSI(3) < 20, IBS < 0.3, exit on a close above the prior day's high, next-open fills) on Nasdaq-100 stocks incl. delisted. No costs, no control, and a win rate is not an edge. The mechanism, short-term reversal inside an uptrend, is already measured here: real (dip beats same-date non-dippers, t 2.5–5.5) but PARKED on survivorship |

# Quantified Strategies KB

YouTube channel "Quantified Strategies" (quantifiedstrategies.com; Skool community "rulebasedtrading"). Short videos,
each presenting one fully specified, rule-based daily strategy with a backtest summary (Norgate data, which includes
delisted stocks). Skeptic-default scoring like every KB here.

`videos/<date>_<id>/` holds `transcript.txt` and `notes.md`.

**Channel triage (2026-09-30):** [channel_triage_2026-09-30.md](channel_triage_2026-09-30.md) — 321 videos, 40 transcripts read. Three tests proposed: the dip family settled with one 2012-published rule (existing queue row), TLT month-end, third-Friday open-to-close short. **The first was run the same day: PASS on the discovery bar** (SPY +0.468pp over any-day entry, t 3.72, 2013–26), see `../studies/index_dip_family_2026-09-30.md`.

| video | date | verdict |
|---|---|---|
| [This RSI Strategy Won 68% of 1,321 Trades](videos/2026-09-26_tjL4wcI403E/notes.md) | 2026-09-26 | **2.5/5 · no new test.** Fully specified Connors-style rules (close > 200 SMA, RSI(3) < 20, IBS < 0.3, exit on a close above the prior day's high, next-open fills) on Nasdaq-100 stocks incl. delisted. No costs, no control, and a win rate is not an edge. The mechanism, short-term reversal inside an uptrend, is already measured here: real (dip beats same-date non-dippers, t 2.5–5.5) but PARKED on survivorship |
| [I Fixed the Darvas Box: 74.2% Win Rate Over 33 Years](videos/2026-09-28_b8Usenu2QIY/notes.md) | 2026-09-28 | **2.5/5 · tested: NULL.** SPY 12-day-high breakout (close ≤ 0.75% above, volume > 15d avg), exit on a close above the prior day's high. His numbers replicate (282 trades, 74.8% win, +0.343%, PF 2.94 vs 279 / 74.2% / +0.34% / 3.08), but any-day entry with the same exit wins 69.5% and averages +0.283%; signal vs other days +0.006pp, t 0.09. QQQ/IWM PF 1.16 / 1.31. `run_darvas_spy.py` |

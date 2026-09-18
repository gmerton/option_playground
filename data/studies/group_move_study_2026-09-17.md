# Catching multi-month industry moves early (2026-09-17)

**Question (Gabe).** Multi-month group moves like semis Apr-Jun 2026 and oil in recent months: can we catch them as early as possible? Follow-up to `industry_rotation_detection_study.md` (July), which asked whether a rotation can be *predicted* (no). This asks whether one can be *joined early and managed*.

**Data.** 31 sector/industry ETFs vs SPY, yfinance adjusted closes 2006-01 -> 2026-09 (`run_group_move_study.py`, cache `data/cache/group_etf_closes.parquet`). Signal S = 21-day return minus SPY's >= +5pp and the ETF above its 50-day; first firing after 21 quiet sessions. SEs clustered by entry month.

| part | result |
|---|---|
| A. anatomy (hindsight) | 255 relative up-legs of >= +20pp lasting >= 40 sessions = **12 per year** across the 31 groups; median 88 sessions, +32pp |
| B. recall | S fires inside **99%** of them, median **day 19 of 88**, with a median **65% of the move still ahead**. SMH 2025-26: day 20, 88% ahead. XLE / XOP summer 2026: day 9 / 18, 53% / 65% ahead |
| C. precision (no hindsight) | 1,160 firings = 56 per year; **26%** land in the first half of a real move. Fixed 63d excess **-0.72pp** (t -2.1), 126d -0.65pp, win 45% |
| D. managed (exit when ETF/SPY closes under its 50-day average) | excess **-0.03pp** per trade (n 1,156), win 28%, avg win +7.1pp / avg loss -2.8pp, payoff 2.54 -> 0.28 x 7.1 - 0.72 x 2.8 = 0. Both halves ~0, every 4-year era within +/-1pp. Absolute +0.84% per 25-session hold = market beta |
| E. discriminators at the signal | leader base -0.02pp, middle -0.10, laggard turn +0.03; commodity groups -0.05 vs others -0.03; SPY above its 200-day -0.26, **below +0.83pp (t 1.7, n 245)** -- the only lean, one of seven cuts |
| F. driver price (crude -> XLE/XOP/OIH, gold -> GDX, copper -> XME) | commodity in an uptrend at the signal +0.50pp (t -0.5 clustered; halves -0.43 / +1.37); **commodity already +15% in 63d: -2.11pp, win 15%** (late) |

**Reading.**
1. Detection is not the problem. A plain relative-strength signal is inside essentially every multi-month move within about four weeks, with two thirds of it left. Being a month late is fine.
2. Precision is the whole problem. The identical signature appears 56 times a year and three in four are false starts. The losses on those cancel the winners exactly, under a fixed horizon and under a trend-following exit with a 2.5:1 payoff. The ETF/SPY ratio behaves as a martingale after the signal.
3. Nothing measurable in price at the signal separates real from false: not the base (leader vs laggard), not the group type, not the driver commodity's own trend. Buying the equities after the commodity has already spiked is the one clearly negative cell.
4. Twelve big moves a year means some group is always in one. Hindsight makes each look catchable; the 74% that fizzled are not remembered.

**What follows for the process.** Do not gate or pick on group strength (consistent with the July rule and with rotation Part III, where leading-group filtering was inverted). A real multi-month move does not need a group call to be caught: its members keep producing layer-2 setups (precision cohort / SETUP list) for the length of the move, each with its own stop. Build the *clustering view* flagged in July as a lead-time tool, not an edge: when the nightly scan's qualifying names concentrate in one industry (`data/ticker_industry_map.csv` now exists), surface the cluster so the watchlist is pointed at it; the individual name still has to trigger.

**Still untested (needs non-price data).** Clustered earnings gaps / guidance inside a group as the start of a move (inconclusive in July for want of an earnings calendar; the TradingView MCP now has one). Semis in April coincided with earnings season.

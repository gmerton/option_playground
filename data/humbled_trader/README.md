# Humbled Trader KB

YouTube channel "Humbled Trader" (`@HumbledTraderOfficial`, Shay): small-cap / momentum day trading (gap-ups, VWAP,
dip buys, shorting runners), swing-trading tutorials, and long-form interviews with "verified millionaire" traders.
Funnels to her community and courses. Skeptic-default scoring like every KB here.

- `index/video_index.csv`: all 412 videos from the videos tab (2026-09-28), with a heuristic category
  (interview / strategy / live-recap / tools-AI / other). `channel_rank` 1 = newest.
- `videos/<date>_<id>/`: transcript, notes.

| video | date | verdict |
|---|---|---|
| [I Replaced my 6AM Premarket Trading Routine with Claude + Codex](videos/2026-06-30_PKFkJ4TprVo/notes.md) | 2026-06-30 | **2.5/5 (process), no strategy claim.** ⭐ METHOD: blind second model re-derives the report, then an agree/disagree merge → candidate guard for the 9/23 verify-before-asserting error set |
| [Claude + IBKR API: Complete AI Trading Bot Guide](videos/2026-06-20_UgWQtQ3MEVE/notes.md) | 2026-06-20 | **2/5, no new test.** TJL bot on IBKR paper; she reports live results 'very meh' vs the backtest and her own discretion. TJL pieces (gap/ORH/HOD entry, partials, BE) already CONTRADICTED. ⚠ order-placing agent in auto mode |
| [I Built an AI Trading System With Claude + TradingView](videos/2026-06-06_IqvnryFzZD4/notes.md) | 2026-06-06 | **1.5/5.** 14-trade / 30-day backtests, no costs or control; two-stage scanner shape we already run |
| [How to Use Interactive Brokers TWS 2026](videos/2025-05-27_fFSKgXZQ7Wg/notes.md) | 2025-05-27 | **n/a (tutorial).** Bracket stop legs rest intraday → disaster stop only, never the close-judged tight stop |
| [From Beginner to Making $1.6M Day Trading - Mari's Full Story](videos/2026-08-01_M5thAKMJsrw/notes.md) | 2026-08-01 | **2/5** (process 2.5, claims 1). Career biography, candid about losses; 'size up when runners follow through' = the RETRACTED activity gate; starter-then-add = pyramid NULL; 'gapper fades stopped working late 2025' untested (small-cap panel blocked) |
| [Verified 8-Figure Trader Explains Statistics & Trader Psychology (Steven Dux)](videos/2023-11-16_cR7jWckuoXw/notes.md) | 2023-11-16 | **2.5/5.** Good statistical instincts (25-bucket runner grid, fixed-size expectancy check, 3-4 trades/month) but no samples/controls; 10x sizing on 90%-win patterns CONTRADICTED (size lever, priced win rate). ⭐ METHOD: capture ratio (realised P&L ÷ the rule's fixed-size signals) → folded into the lived-experience stats row |
| [Gap Up Day Trading Strategy Crash Course](videos/2023-08-10_9BVf72n8p8Y/notes.md) | 2023-08-10 | **2/5.** Five large-cap gap setups, five hand-picked winners. Earnings-gap long, pre-market-high entry, VWAP-bounce short, scale-outs all CONTRADICTED; gap-up short on a downtrend = our PARKED gap fade. New cell queued: gap-down after a strong prior day |
| [VWAP Trading Strategy Crash Course](videos/2023-05-25_dgfQkFSzhiY/notes.md) | 2023-05-25 | **2/5.** Her own live trades break her rules; reclaim / rejection / 'loses VWAP' entries all already NULL or worse than random. Untested premise: does VWAP side at 11:00 predict the rest of the day? (Breitstein VWAP-veto arm, §10) |
| [Simple Part-Time SWING TRADING STRATEGY](videos/2024-06-06_5zgBtnPHwbY/notes.md) | 2024-06-06 | **1.5/5, no new test.** Large-cap earnings-gap buy over the pre-market high, 1-5% risk, partial sells: catalyst-day buy, ORH entry, partials all CONTRADICTED; one hand-picked NVDA winner |

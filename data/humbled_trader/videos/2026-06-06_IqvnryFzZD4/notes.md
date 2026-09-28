# I Built an AI Trading System With Claude + TradingView (IqvnryFzZD4, 2026-06-06, 31 min)
**1.5/5 · no new test.** TradingView-desktop MCP (Mac only), a Yahoo + Benzinga pre-market gap scanner (> 5%, > $3, > 50k pre-market volume), a TJL strategy scanner, a Pine Script backtest, a Python backtest, and Telegram pushes. Also a short tour of TradingView's beta AI co-pilot.

**Evidence:** MU 5-min backtest, 14 trades, 9 wins, PF 2.48. Mag-7 on 15-min. 32 watchlist names × **30 days**, 54% win. No costs, no control, no out-of-sample test; the universe and window were chosen after the fact. Her follow-up video (UgWQtQ3MEVE) reports the live bot as "meh".

**Operational:** scanner A (broad gap list) → scanner B (strategy rules on A's output) is a sensible two-stage pipeline, and we already run the same shape (preferred list → EOD scan → alerts). Nothing new for us here. We have the TradingView MCP too; the 403 gotcha is in memory.

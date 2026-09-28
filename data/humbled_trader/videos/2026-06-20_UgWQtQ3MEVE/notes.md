# Claude + IBKR API: Complete AI Trading Bot Guide (UgWQtQ3MEVE, 2026-06-20, 23 min)
**2/5 · no new test.** A build walkthrough that turns her "Trend Join Long" (TJL) setup into an IBKR paper bot: TWS API → rules.json → S&P 500 gap ≥ 3% pre-filter → 30-min decision loop → Telegram alerts → R-multiple dashboard. Sponsor: BetaPro leveraged ETFs.

**What she admits (the valuable part):** "the backtested numbers don't perfectly translate to live execution… the results are just very meh", and her discretionary TJL still beats the bot. She attributes this to (1) a tiny backtest and (2) discretionary execution she can't code. That is our capture-ratio / real-fills lesson again.

**Strategy (TJL, 5-min):** after 10:00, price > prior-day high, prior close > 200 SMA, > pre-market high, new high of day. Stop 1% under the low of day (resting intraday), partial at 0.75R, breakeven at 1R, trail the 5-min swing lows, flat by the close. Ledger: gap/catalyst-day buys, pre-market-high/ORB entries and intraday triggers (Stage A ≈ a random minute) are all CONTRADICTED. Partials cost −0.25…−0.33R; BE after +1R is harmless at best (profit-lock study). No new cell.

**Operational:** API setup = paper port 7497 / live 7496, trusted IP 127.0.0.1, untick Read-Only API, and the first API order raises a precaution pop-up. We already run ib_async on Gateway 4002 / TWS 7496. ⚠ She runs the order-placing agent in auto mode, which clashes with our IBKR rules (clientId 0 cancels, never stack stops, audit with reqAllOpenOrders). Keep the live agent read-only or confirm-per-order.

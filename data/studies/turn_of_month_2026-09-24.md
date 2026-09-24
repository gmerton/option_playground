# Turn-of-the-month in SPY / QQQ (2026-09-24)

`run_turn_of_month.py` (pre-registration in the docstring); log `data/studies/logs/turn_of_month.log`. yfinance daily,
TOM = last trading day + first three of the next month; 2000–2026 is out of sample for the 1987–88 papers.

**NULL — faded after publication.** SPY TOM days +6.5 bp/day vs +3.3 otherwise: **+3.26 bp, t 0.94**; halves +7.33
(2000–12) / **−0.60** (2013–26). QQQ +5.24 bp (t 1.02), halves +10.3 / +0.5. Trading only the window (19% of days):
SPY 2.6% CAGR, Sharpe 0.36 vs buy-and-hold 8.3%, 0.51 — lower drawdown, but no better risk-adjusted. Residual:
the first trading day of the month is the strongest single day (SPY +17.7 bp, QQQ +21.7 bp) — exploratory, not
tested, and one day a month is too thin to matter for the book.

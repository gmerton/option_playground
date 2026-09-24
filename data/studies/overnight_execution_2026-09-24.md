# Overnight-aware execution on the precision-tier book (2026-09-24)

`run_overnight_execution.py` (pre-registration in the docstring); log `data/studies/logs/overnight_execution.log`;
trades `overnight_execution_2026-09-24.csv`. 1,918 house trades 2019-10 → 2026-09, paired per trade: move the exit
(or the entry) from the close to the next open; decile = the name's trailing-252 mean overnight return that day.

**PRIMARY FAIL.** Selling top-overnight-decile names at the next open instead of the exit close: **+0.151% of entry,
t 1.66** (n 691), halves +0.10 / +0.18; across the book +0.05%/trade.

**The secondary pattern is not the overnight effect.** Selling at the next open helps across ALL trades (+0.180%,
t 2.30) with no dose-response in the overnight decile (corr +0.005; decile 1 +0.35, decile 8 +0.41, decile 10 +0.15).
That is a generic bounce after the exit-signal close (a close under the 20 EMA), not the overnight premium — a
separate, unregistered exit-timing lead, below the bar, and exposed to the yfinance open-price caveat.
**Entries: the close is right.** Buying at the next open instead costs −0.32% (t −2.7) in decile 9 and −0.32%
(t −2.1) in decile 10 — and breakout names are overwhelmingly overnight winners (56% sit in deciles 9–10). The house
close entry already harvests the effect; nothing to add.

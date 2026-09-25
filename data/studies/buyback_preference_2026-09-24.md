# Buyback preference (2026-09-24)

`run_buyback_preference.py` (pre-registration in the docstring); log `data/studies/logs/buyback_preference.log`;
monthly table `buyback_preference_2026-09-24.csv`. Follow-up to the net-issuance lead (+0.71pp, t 2.94), with the two
changes that could break it: an ADR × SIZE-matched control, and a 2010–2012 out-of-time holdout (yfinance split
history → `data/cache/splits_yfinance.parquet`).

**PRIMARY FAIL.** Bottom-decile issuers (net buybacks), 60d vs the ADR × size-matched field: **+0.53pp, t 2.28**;
halves +0.25 / +0.84; **holdout 2010–12 +0.85pp (t 2.09, n 29)** — the right sign out of time.
**Plateau, not a spike:** all 12 threshold × horizon cells positive (t 1.5–2.8), rising with horizon (decile 20/60/120d
+0.17 / +0.53 / +1.01).
**But it is an INDUSTRY effect.** Against same-industry peers the same cell is **−0.38pp (t −1.56)**. Buyback-heavy
industries outperformed; within an industry, the buyback names did not beat their peers. As a stock-selection tilt
it has nothing; as a sector tilt it is the industry-rotation question again (not front-runnable, ledger).
Descriptive (lead's own sample): precision-tier trades in buyback names +1.72%/trade (n 241) vs +0.26% (t 1.31).
**Verdict: NULL as stock selection · MECHANISM (sector composition).**

# Volatility-managed sizing of the book (2026-09-24)

`run_vol_managed_book.py` (pre-registration in the docstring); log `data/studies/logs/vol_managed_book.log`.
Moreira–Muir: scale each trade's risk by 1 / (SPY 20d realized variance at entry), normalised on prior dates, cap 3×;
monthly book series; alpha of managed on unmanaged (HAC t).

| sleeve | Sharpe unmanaged → 1/var | alpha t | halves |
|---|---|---|---|
| **BRK precision breakouts (primary)** | **0.41 → 0.20** | −0.68 | −2.93 / +0.38 |
| PUT certified SPY/QQQ bearish-high-IV | 1.48 → 1.74 | +1.21 | +0.022 / +0.017 |
| ETF put roster (50% take) | −0.47 → −0.62 | −1.24 | |

**FAIL — INVERTED for the breakout book.** Its per-trade R is HIGHEST when the market is volatile (high-vol tercile
+0.21R vs +0.12 / +0.14), the opposite of the Moreira–Muir premise, so shrinking size in volatile markets cuts the
best trades. Same with VIX as the signal (0.41 → 0.33). Consistent with "the book's edge lives in busy months".
PUT: Sharpe rises and both halves' alpha are positive, but t 1.21 on 41 months and it runs at a 0.27 average weight
(it mostly de-risks) — not adopted. ETF: worse.

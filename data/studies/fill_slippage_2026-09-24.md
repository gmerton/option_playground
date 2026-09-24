# Slippage calibration from real fills: the 25% charge is CONSERVATIVE (2026-09-24)

`run_fill_slippage.py` (pre-registered in its docstring). Log: `logs/fill_slippage_2026-09-24.log`; per-order CSV
`fill_slippage_2026-09-24.csv`; quotes cached in `data/cache/fill_quotes_ibkr_1min.parquet`.

**Question.** `src/lib/studies/costs.py` charges **25% of each leg's quoted bid-ask per side**. It was copied from one
calendar study and never measured, and every after-cost number in the ledger runs through it. The journal is
admissible for exactly this (cost realism).

**Data.**
- Fills: Gabe's option fills from `journal_trades` (ExchTrade).
- Quotes: IBKR 1-minute `BID_ASK` bars for the fill minute (bar open = time-averaged bid, close = time-averaged ask).
- ⚠ IBKR serves no history for expired options, so only fills in contracts still listed on 2026-09-24 are measurable:
  **403 of 1,224 fills → 248 orders, 35 trading days (Aug 4 → Sep 23)**, median DTE at fill 31 vs 16 for all fills.

**Measure.** Fraction of the quoted spread paid vs mid, signed so that positive is worse: 0 = filled at mid, 0.5 = at
the far touch. Multi-leg orders are scored net at the order level (IB's per-leg allocation of a combo price is
arbitrary).

## Result

**PRIMARY: mean 0.133 of the spread per order, 95% CI [0.111, 0.154] (day-block bootstrap), median 0.143. The CI
excludes 0.25, so the model is CONSERVATIVE.**

| cut (exploratory) | orders | mean (95% CI) | median | $/contract vs mid |
|---|---|---|---|---|
| single-leg | 169 | 0.153 [0.116, 0.183] | 0.174 | $4.11 |
| **multi-leg (combo, net)** | 79 | **0.092 [0.066, 0.120]** | 0.090 | $2.62 |
| opening | 145 | 0.108 [0.076, 0.136] | 0.118 | $2.62 |
| closing | 96 | 0.173 [0.131, 0.216] | 0.181 | $5.40 |
| spread tight (2.5% of mid) | 83 | 0.141 | 0.187 | $1.60 |
| spread wide (16.5% of mid) | 83 | 0.132 | 0.140 | $4.99 |
| August / September | 95 / 153 | 0.141 / 0.129 | | |

- 30% of legs filled at or better than mid; 6% at or through the far touch.
- The fraction is flat across spread width, so a *proportional* charge is the right form of model.
- Stable across the two months.

## Checks (a clean result is a bug until proven otherwise)

- **Timestamp alignment.** At the fill minute, 95% of fills sit inside [bid, ask]. Shifting the quote degrades the fit
  on both sides: ±1 min gives 86–93%, ±5 min 71–77%, ±60 min about 50%. The match is real.
- ⚠ **Arrival-price sensitivity.** Against the quote **one minute before** the fill, the paid fraction is **0.20**. It
  falls to 0.09 one minute after. The market tends to come to Gabe's limit and keep going, which is the adverse-selection
  signature of resting limits. A backtest charges against the quote at decision time, so **0.20 is the fairer
  comparison for the ledger** and 0.13 the flattering one. Both are below 0.25.
- ⚠ **What isn't in the sample:**
  - Unfilled limit orders are invisible (their cost is opportunity, not slippage), so this is a lower bound for patient
    limits.
  - Expired, short-dated contracts (the 0–14 DTE bulk of his trading) can't be quoted historically.
  - These are Gabe's orders in liquid names; a backtest across thin chains may do worse.

## Reading and recommendation

**The 25% charge is harsh by roughly a quarter to a half: 0.20 at arrival, 0.13 at the fill minute, 0.09 for
combos.** It errs in the safe direction, and "precision over recall" says keep it. **Recommendation: leave
`SLIPPAGE_FRAC = 0.25` as the house default. Do not loosen it on this sample.**

Two follow-ups, not run:
1. **False-negative check.** Re-score the strategies the 2026-09-22 cost sweep killed at 0.13 and 0.20 (`costs.py` is
   one constant). Only a strategy that turns positive at 0.20 is worth reopening.
2. **Re-measure monthly.** Pull the quotes before each month's contracts expire, so short-dated fills get covered too.

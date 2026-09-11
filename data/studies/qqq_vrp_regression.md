# QQQ VRP regression: the oquants-style model on a single ticker (2026-09-10)

Script: `run_qqq_vrp_regression.py` (trades in `data/studies/qqq_vrp_regression_trades.csv`).
Question: do oquants' VRP inputs (from their VRP video) pick better weeks to sell a 30-day ATM QQQ
straddle? The inputs are log(IV/RV), the 1-year IV percentile and a term-structure measure.

**Setup.** Every Friday, 2018-06 .. 2026-02 (387 trades, median 28 DTE): sell the ATM straddle at the
expiry nearest 30 days, hold it to expiry, settle at |S_T - K|. Return is on the credit, net of the
house cost model. IV is backed out of the traded straddle itself; RV is trailing 21-day. The IV
percentile is vs its own prior 252 days. The term-structure input is oquants' forward factor, from
the 30- and 60-day straddles; it stands in for their Flat Fwd Ratio, which has no published formula.
OLS was trained on 2018-2022 and tested on 2023-2026, with Newey-West t-stats (4 lags) for the
overlapping holds. An iron fly (wings about one straddle-width out, return on max loss) was run alongside.

## Results

| Period | n | Straddle mean, net | Median | Win % | Worst | t |
|---|---|---|---|---|---|---|
| All | 387 | +1.61% | +7.1% | 54.8% | −465% | +0.44 |
| Train 2018-22 | 228 | −2.69% | −0.9% | 49.6% | −465% | −0.54 |
| Test 2023-26 | 159 | +7.76% | +21.5% | 62.3% | −201% | +1.47 |

- **The model has no skill.** Training R² was 0.009 and no coefficient had |t| above 1. In the test
  period corr(predicted, realized) was −0.07. Test weeks above the 67th-percentile prediction averaged
  +8.9% vs +7.1% for the weeks skipped, which is no difference.
- **No input was monotone across quintiles in either period.** The lowest IV-percentile quintile was
  the WORST from 2023 on (−12.4%), which cuts against the "sell VRP at low IV" claim on QQQ. The top
  log(IV/RV) quintile was best in both periods (+7.4% / +17.3%), but the middle quintiles were noisy.
- **Simple gates add nothing:** IVP < 0.8, IV > RV, contango, and all three together (test period).
- **The iron fly at these tight wings loses:** −11.4% on max loss overall, median −72%. Its wings sit
  roughly at the breakevens; oquants' fly is presumably wider. That's not a verdict on flies.

## Reading
1. **QQQ short vol is regime-dependent:** negative through 2018-22 (Q4 2018, 2020, 2022), positive in
   the 2023-26 bull. Consistent with our QQQ IV-gate study (index IV richness warns of a systematic
   move; it isn't a premium to harvest).
2. **One ticker doesn't have the statistical power.** 387 overlapping trades with −465% tails can't
   detect a 2-3% edge; oquants pools the whole liquid-ETF universe.
3. **Management isn't modeled.** Their exit rules (close on IVP above 90-95 or a term-structure
   inversion) may matter more than the entry model, and holding to expiry takes every tail.

## Next
- Pool the liquid ETFs in `options_cache` into one panel, with the same features plus ticker fixed effects.
- Add their exit rules using daily marks from `options_cache`.
- Only then compare against their Plays ranking.

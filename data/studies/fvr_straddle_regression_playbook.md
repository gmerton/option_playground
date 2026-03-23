# FVR → Short Straddle P&L Regression — Study Playbook

**Last updated:** 2026-03-22
**Status:** 10-30d interval tested and rejected. 30-90d confirmed as superior predictor.

---

## Hypothesis

The 30-90d forward vol ratio (fvr_put_30_90) measured on the entry date predicts
the profitability of a 10-DTE short ATM straddle held to expiry.

- **FVR < 1 (backwardation):** near-term IV elevated relative to far-term →
  IV likely overstates near-term realized vol → seller benefits
- **FVR > 1 (contango):** near-term IV compressed relative to far-term →
  market pricing in future vol expansion → seller at a disadvantage

---

## Study Design

| Parameter | Value |
|-----------|-------|
| X variable | `fvr_put_30_90` on entry date |
| Y variable | `profit_pct_seller` = (entry_premium − payout) / entry_premium × 100 |
| Entry | Friday, ~10 DTE (±5), ATM straddle (same strike call + put) |
| Exit | Hold to expiry; payout = call_last_expiry + put_last_expiry |
| Universe | 987-ticker MySQL study universe |
| Date range | 2018-01-01 → 2026-02-20 |
| Liquidity filters | bid > 0, ask > 0, open_interest > 0; bid-ask ≤ 35% of mid; \|delta ∓ 0.50\| ≤ 0.08 |
| Outlier handling | Winsorize profit_pct at p1/p99 before OLS (removes ~2% of rows) |

**Profit_pct interpretation:**
- 100% = straddle expired worthless (maximum seller profit)
- 0% = break-even
- Negative = loss for seller

---

## Results

### Dataset

| Metric | Value |
|--------|-------|
| Total observations (post-winsorize) | 52,385 |
| Unique tickers | 886 |
| Mean entry premium | $6.16/share |
| Post-winsorize mean profit_pct | +1.60% |
| Post-winsorize median profit_pct | +18.02% |
| Overall win rate (seller) | 58.8% |
| FVR range | 0.030 – 6.911 (mean 1.094) |

### Pooled Regression

| Statistic | Value |
|-----------|-------|
| OLS slope (β) | −4.63 [***] |
| OLS intercept | +6.67 |
| t-stat | −4.39 |
| p-value (OLS) | 1.1e-05 |
| Pearson r | −0.019 |
| R² | 0.0004 |
| Spearman ρ | −0.018 [***] |
| p-value (Spearman) | 6.4e-05 |

**Direction confirmed by both OLS and rank-based Spearman.**
Low R² is expected: FVR is a regime signal, not a single-name return predictor.
The actionable signal lies in the bucket-level differences.

### FVR Bucket Analysis (ANOVA F=7.21, p=9.4e-07 ***)

| FVR bucket | N | Mean profit% | Median profit% | Win rate |
|------------|---|-------------|---------------|----------|
| **< 0.80 (backwardation)** | 7,839 | **+4.6%** | **+21.3%** | **60.6%** |
| 0.80–0.90 | 5,410 | +1.6% | +17.8% | 58.8% |
| 0.90–1.00 | 7,064 | +1.2% | +17.0% | 58.0% |
| 1.00–1.10 | 7,782 | +3.2% | +19.3% | 59.8% |
| 1.10–1.20 | 7,339 | +2.5% | +19.2% | 59.2% |
| **≥ 1.20 (deep contango)** | 16,951 | **−0.8%** | **+16.0%** | **58.1%** |

**Key spread:** < 0.80 outperforms ≥ 1.20 by ~5.4pp mean / ~5.3pp median.
Win rate drops from 60.6% to 58.1% in deep contango.

### Per-Ticker Spearman (n ≥ 15)

- **61.6%** of 396 qualifying tickers show negative ρ (expected direction)
- **19 significantly negative** (p < 0.05) vs **9 significantly positive** — 2:1 ratio

**Strongest negative ρ (FVR predicts seller profits well):**
NKTR (−0.642**), IBKR (−0.448*), ETHA (−0.406*), VNQ (−0.382*), RRC (−0.326***)

**Strongest positive ρ (signal reverses for these names):**
AMSC (+0.596*), CALM (+0.532***), DDS (+0.397*), KGC (+0.322**), CMI (+0.314**)

---

## Interpretation and Trading Implications

1. **Signal is real and robust** — confirmed by OLS, Spearman, and ANOVA across
   53K observations and 886 tickers over 8 years.

2. **Effect lives in the tails:** Backwardation (FVR < 0.80) materially benefits
   straddle sellers. Deep contango (FVR ≥ 1.20) is the danger zone.

3. **Practical filter:**
   - FVR < 0.90 → **favors selling** near-term straddles (elevated premium likely to mean-revert)
   - FVR > 1.20 → **avoid selling** near-term straddles; consider buying instead
   - FVR 0.90–1.20 → neutral; rely on other signals

4. **Low R² is not a problem** — this is a screening filter, not a return predictor.
   Same dynamic as VIX regime filters: directionally correct, not precise.

5. **Ticker-level heterogeneity exists** — a minority of names have positive ρ
   (contango favors selling there). Worth investigating whether these share common
   characteristics (sector, vol regime, earnings cadence).

---

## Interval Comparison: 10-30d vs 30-90d (2026-03-22)

Hypothesis tested: the 10-30d FVR (near leg aligned with straddle DTE) would be
a stronger predictor than the 30-90d baseline.

**Result: hypothesis rejected.** The 10-30d ratio has essentially zero predictive power.

| Metric | `fvr_put_10_30` | `fvr_put_30_90` |
|--------|:-----------:|:-----------:|
| Spearman ρ | −0.0018 **[ns]** | −0.0174 **[***]** |
| p-value | 0.68 | 0.0001 |
| Bucket spread (pp) | 1.4 | **5.4** |
| Low FVR mean% (<0.80) | +2.8% | **+4.6%** |
| High FVR mean% (≥1.20) | +1.4% | **−0.7%** |

**Interpretation:** When the near leg of the FVR overlaps heavily with the straddle's
own DTE (10d), the ratio measures something correlated with near-term realized vol
rather than an independent regime signal. The 30-90d works *because* it measures the
vol surface far beyond the noise band of the trade being predicted — it's a regime
indicator, not a direct vol comparison.

The `silver.fwd_vol_daily` table now stores both columns (`fvr_put_10_30`,
`fvr_put_30_90`, plus `iv_put_10`, `iv_put_30`, `iv_put_90`).

---

## Known Limitations / Future Work

1. **Other long-end ratios not yet tested.** Next candidates: 30-60d, 60-90d, 30-120d.
   Given the 10-30d failure, the key question is whether anything *longer* than 30-90d
   (e.g., 30-120d) captures even more of the structural term structure signal.

2. **Stale `last` prices at expiry** can inflate payouts for leveraged ETFs and
   thinly-traded names. The p1/p99 winsorize handles this but a proper fix is to
   compute payout from the underlying price at expiry (requires stock price join).

3. **No per-ticker normalization** — pooling raw profit_pct across names with very
   different IV regimes (NVDA 60% vs KO 15%) may dilute the signal. Consider
   standardizing Y by per-ticker rolling IV before regression.

4. **Other straddle DTEs not tested** — the 30-90d FVR may be more predictive for
   20-DTE or 30-DTE straddles than for 10-DTE. Study the DTE dimension.

5. **Long-only bias** — most of the 986-name universe is equities with positive
   drift. The short straddle P&L distribution is right-skewed (median >> mean),
   typical of short-vol strategies. The FVR signal is more visible in the median
   than the mean — prefer median/rank analysis for future iterations.

---

## Key Scripts

```bash
# Build / refresh fvr_put_30_90 for all tickers:
AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_fwd_vol.py

# Re-run full regression study:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_fvr_straddle_regression.py --csv

# Specific tickers or date range:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_fvr_straddle_regression.py \
    --tickers AAPL MSFT NVDA --start 2022-01-01

# Ticker file (987-ticker list from MySQL):
MYSQL_PASSWORD=cthekb23 python3 -c "
from lib.mysql_lib import _get_engine; import pandas as pd
pd.read_sql('SELECT DISTINCT ticker FROM study_summary WHERE study_id=12', _get_engine()
)['ticker'].to_csv('/tmp/tickers.txt', index=False, header=False)"
```

**Key source files:**
- `src/lib/studies/fwd_vol_study.py` — FVR compute engine (Athena → S3/Glue)
- `run_build_fwd_vol.py` — build/refresh `silver.fwd_vol_daily`
- `run_fvr_straddle_regression.py` — regression runner
- `silver.fwd_vol_daily` (Glue table) — 560K+ rows, 1,030 tickers, 2018–2026
  Columns: `iv_put_10`, `iv_put_30`, `iv_put_90`, `fvr_put_10_30`, `fvr_put_30_90`
- `fvr_straddle_data.csv` — full merged dataset (53K obs) from 2026-03-22 run

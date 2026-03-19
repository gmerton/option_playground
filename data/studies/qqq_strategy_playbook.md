# QQQ Options Strategy — Trading Playbook

**Last updated:** 2026-03-18
**Status:** Research complete. Regime-optimized with per-regime deltas and stop rules.

---

## Overview

QQQ's bull put spread wins in **all four regimes**, but the optimal delta and stop rule
vary significantly by regime. The final configuration uses regime-specific parameters
derived from a full delta sweep (7 short deltas × 4 wing widths × 4 regimes) with
and without a 2× stop loss.

| Regime | Condition | Short Δ | Long Δ | Stop | ROC | Win% | Weeks/yr |
|--------|-----------|---------|--------|------|-----|------|----------|
| **Bearish_HighIV** | Below 50MA + VIX ≥ 20 | 0.25Δ | 0.15Δ | None | +7.38% | 92.3% | ~10 |
| **Bearish_LowIV** | Below 50MA + VIX < 20 | 0.35Δ | 0.15Δ | None | +8.32% | 90.5% | ~5 |
| **Bullish_HighIV** | Above 50MA + VIX ≥ 20 | 0.45Δ | 0.35Δ | 2× credit | +14.11% | 80.9% | ~8 |
| **Bullish_LowIV** | Above 50MA + VIX < 20 | 0.45Δ | 0.35Δ | None | +5.90% | 80.5% | ~27 |

All regimes: ~20 DTE, 50% profit take. Wing = 0.10Δ throughout.

---

## Entry Decision (Every Friday)

**Step 1:** Is QQQ above its 50-day moving average?
**Step 2:** Is VIX ≥ 20?

```
                    VIX ≥ 20                     VIX < 20
QQQ below 50MA  → Bull put 0.25Δ/0.15Δ, no stop  → Bull put 0.35Δ/0.15Δ, no stop
QQQ above 50MA  → Bull put 0.45Δ/0.35Δ, 2× stop  → Bull put 0.45Δ/0.35Δ, no stop
```

**Common parameters across all regimes:**
- Target DTE: ~20 days
- Profit take: 50% of credit
- Allocation: 2–3% of portfolio (1.5% max when SPY also fires)

---

## Why the Deltas and Stops Differ by Regime

### Bearish regimes → go OTM, skip the stop

In a downtrend (below 50MA), the market is choppy. When a 0.35Δ spread gets hit,
it often whipsaws back before expiry — the stop cuts trades that would have recovered.
Removing the stop improves ROC by +3–9% depending on delta. Going to 0.25Δ (Bearish_HighIV)
or 0.35Δ (Bearish_LowIV) captures less premium but takes far fewer losses.

**The stop hurt by -3.17% in Bearish_HighIV and -8.86% in Bearish_LowIV** at the current
0.35Δ/0.10Δ structure. These are the largest regime-specific effects found in the analysis.

### Bullish_HighIV → go aggressive, keep the stop

When QQQ is in an uptrend and VIX spikes (transient fear events), put premium is fat AND
the bullish trend protects the short put. Going to 0.45Δ more than doubles ROC vs 0.35Δ
(+14.11% vs +6.45%). The stop is kept here because in this regime, the ~19% of trades
that go wrong tend to *keep* going wrong rather than recovering — the stop limits those.

### Bullish_LowIV → go aggressive, skip the stop

Calm bull market. Losses are small and typically recover. Stop is neutral-to-slightly
harmful. 0.45Δ vs 0.35Δ improves ROC from +1.97% to +5.90%.

---

## Comparison: Original vs Optimized

| Regime | Original (0.35Δ/0.10Δ, 2× stop) | Optimized | Improvement |
|--------|----------------------------------|-----------|-------------|
| Bearish_HighIV | +2.83% ROC, 70.5% win | +7.38%, 92.3% win | **+4.55%** |
| Bearish_LowIV | −0.79% ROC, 69.0% win | +8.32%, 90.5% win | **+9.11%** |
| Bullish_HighIV | +6.45% ROC, 80.9% win | +14.11%, 80.9% win | **+7.66%** |
| Bullish_LowIV | +1.97% ROC, 72.3% win | +5.90%, 80.5% win | **+3.93%** |

---

## What Doesn't Work on QQQ

| Strategy | Overall ROC | Reason |
|----------|-------------|--------|
| Bear call spreads | −26.8% | QQQ's upward drift makes OTM calls cheap to buy back |
| Iron condors | −6.0% | Two-sided exposure on a volatile, trending index |
| Short straddle (0.50Δ) | +1.1% | Barely breaks even; QQQ moves overwhelm the premium |
| Blanket 2× stop | See above | Hurts in bearish regimes; helps only in Bullish_HighIV |

---

## SPY / QQQ Correlation Warning

**SPY and QQQ are highly correlated (~0.95).** Both strategies sell put spreads:

- In stress regimes (VIX ≥ 20), both fire simultaneously → double put delta exposure
- A sharp market selloff affects both positions in the same direction
- **Sizing:** If both SPY and QQQ fire in the same week, reduce each to 1.5% of portfolio.
- **QQQ vs SQQQ:** Running QQQ puts alongside SQQQ bear calls is NOT double-dipping —
  they hedge directionally. Combined exposure is appropriate.

---

## Regime Distribution by Year

| Year | Bearish_HighIV | Bearish_LowIV | Bullish_HighIV | Bullish_LowIV |
|------|---------------|---------------|----------------|---------------|
| 2018 | 10 | 11 | 0 | 29 |
| 2019 | 1 | 8 | 0 | 42 |
| 2020 | 10 | 0 | 31 | 8 |
| 2021 | 4 | 1 | 14 | 31 |
| 2022 | 32 | 2 | 14 | 3 |
| 2023 | 7 | 8 | 2 | 34 |
| 2024 | 3 | 4 | 3 | 41 |
| 2025 | 7 | 4 | 8 | 31 |

---

## Key Scripts

```bash
# Full regime strategy study
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_tlt_strategy_study.py --ticker QQQ

# Per-regime delta sweep (with and without stop)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_qqq_regime_put_sweep.py

# Strangle sweep
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_tlt_strangle_study.py --ticker QQQ --regime ALL
```

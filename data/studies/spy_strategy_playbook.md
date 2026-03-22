# SPY Regime-Switching Options Strategy — Trading Playbook

**Last updated:** 2026-03-21
**Status:** Research complete. Double calendar added for Bearish_HighIV and Bullish_LowIV.

---

## Overview

Each Friday, classify SPY's regime using two signals — its position relative to the 50-day
MA (trend direction) and the VIX level (implied vol environment). Deploy a different options
structure depending on the regime:

| Regime | Condition | Strategy | Backtest ROC | Win% |
|--------|-----------|----------|-------------|------|
| **Bearish_HighIV** | Below 50MA + VIX ≥ 20 | Bull put spread 0.25Δ/0.15Δ, no stop **+ Double calendar 0.25P/0.10C** | +7.5% / +23.7% | 94.7% / 50.0% |
| **Bearish_LowIV** | Below 50MA + VIX < 20 | Long straddle 0.50Δ | +22.6% | 57.9% |
| **Bullish_HighIV** | Above 50MA + VIX ≥ 20 | Bull put spread 0.45Δ / 0.35Δ, no stop | +8.26% | 81.9% |
| **Bullish_LowIV** | Above 50MA + VIX < 20 | **Double calendar 0.25P/0.25C, 50%PT** | **+10.4%** | **59.3%** |

**Regime frequencies (2018–2026):** Bearish_HighIV 75 wks (~9/yr), Bearish_LowIV 39 wks
(~5/yr), Bullish_HighIV 72 wks (~9/yr), Bullish_LowIV 225 wks (~28/yr).
Active ~51 Fridays/year (all regimes now covered except Bearish_LowIV is low-frequency).

**Key finding:** Bear call spreads are definitively rejected on SPY in all regimes
(-20% ROC in Bearish_HighIV, -17.6% in Bullish_HighIV). SPY's structural upward bias
means elevated put premium in high-IV regimes is more reliably captured by bull put spreads.

**Bullish_LowIV now uses a double calendar.** Short strangles show +14.6% average ROC in
that regime but produced -481% ROC in 2020 (COVID) and -163% in 2022. The double calendar
at 0.25Δ/0.25Δ with 50% profit take yields +10.4% ROC, 59.3% win rate, with max loss
capped at the net debit (~$2.15/shr). No tail risk.

**Bearish_HighIV now runs two strategies simultaneously** — the put spread (high win rate,
lower ROC) and the double calendar (lower win rate, much higher ROC). Size each at 1.5%
rather than a single position at 2–3%. See sizing section below.

---

## Entry Decision (Every Friday)

**Step 1:** Is SPY's close above its 50-day moving average?
**Step 2:** Is VIX ≥ 20?

```
                    VIX ≥ 20                              VIX < 20
SPY below 50MA  → Put spread 0.25/0.15 (no stop)      → Long straddle 0.50
                  + Double cal 0.25P/0.10C (hold)
SPY above 50MA  → Put spread 0.45/0.35 (no stop)      → Double cal 0.25P/0.25C (50%PT)
```

**No stop loss on either put spread regime.** SPY mean-reverts even in elevated-VIX
environments — the stop fires on temporary breaches and cuts trades that would have
recovered. Stop penalty: −2.84% in Bearish_HighIV, −0.46% in Bullish_HighIV.

---

## Strategy Details

### Bearish_HighIV — Bull Put Spread (go OTM)

SPY is in a downtrend and VIX is elevated. Use a more OTM strike to reduce exposure to
continued downside. Whipsaws are common — the spread often recovers without a stop needed.

| Parameter | Value |
|-----------|-------|
| Short put delta | 0.25Δ |
| Long put delta | 0.15Δ (wing = 0.10Δ) |
| Target DTE | ~20 days |
| Profit take | 50% of credit |
| Stop loss | **None** |
| Allocation | 2–3% of portfolio |

### Bullish_HighIV — Bull Put Spread (go aggressive)

SPY is in an uptrend and VIX spikes — transient fear event. The structural bull trend
protects the short put, and the elevated premium rewards a more aggressive strike.

| Parameter | Value |
|-----------|-------|
| Short put delta | 0.45Δ |
| Long put delta | 0.35Δ (wing = 0.10Δ) |
| Target DTE | ~20 days |
| Profit take | 50% of credit |
| Stop loss | **None** |
| Allocation | 2–3% of portfolio |

### Bearish_LowIV — Long Straddle

SPY is below its 50MA (downtrend) but VIX is suppressed below 20 — the "quiet slide" /
coiling regime. Realized vol is outpacing implied vol; the market is building tension for
a directional move. Long gamma is the play.

| Parameter | Value |
|-----------|-------|
| Call delta | ~0.50Δ (ATM) |
| Put delta | ~0.50Δ (ATM) |
| Target DTE | ~20 days |
| Profit take | +50% of debit |
| Stop loss | −40% of debit |
| Allocation | 1–2% of portfolio (debit strategy, capped loss) |

**Why it works:** When SPY is in a downtrend but VIX is calm, IV is compressed relative to
the actual movement occurring. The straddle buys this cheap vol and profits from either a
continued breakdown (vol expansion + downward move) or a sharp recovery (whipsaw).

**Caution:** 39 weeks of data (2018–2026), concentrated in 2018 (12 wks) and 2019 (8 wks).
All credit strategies are negative in this regime — long straddle is the only viable option.
Win rate 57.9% reflects the debit structure (you need a move > the combined premium paid).

---

## Why the Deltas and Stops Differ by Regime

### Bearish_HighIV → go OTM, skip the stop

In a downtrend with high IV, SPY makes choppy moves. A 0.35Δ spread frequently gets
touched and then recovers — the stop cuts winners. Going to 0.25Δ improves win rate from
74% to 95% and ROC from +4.02% (with stop) to +7.49% (no stop). Removing the stop alone
adds +2.84% ROC; going to 0.25Δ adds another +0.63%.

### Bullish_HighIV → go aggressive, skip the stop

SPY is in an uptrend but VIX spikes — the trend is your protection. Going from 0.35Δ to
0.45Δ captures more premium (+8.26% vs +5.03%). Unlike QQQ, SPY's 500-stock diversification
means losers in this regime tend to recover rather than persist, so the stop fires
unnecessarily. Removing stop adds +0.46% at the current 0.35Δ; combined optimization
(0.45Δ + no stop) gains +3.69% vs original.

### Why SPY differs from QQQ in Bullish_HighIV

On QQQ, the stop *helped* in Bullish_HighIV (+4.24% improvement). On SPY, it hurts (-0.46%).
QQQ's tech concentration means a sector crisis (e.g., single large-cap breakdown) can drag
QQQ continuously in one direction — those losers keep losing. SPY's diversification absorbs
individual sector shocks and tends to mean-revert, so touched positions recover more often.

---

## Comparison: Original vs Optimized

| Regime | v1 | v2 (optimized) | v3 (+ double cal) |
|--------|----|----------------|-------------------|
| Bearish_HighIV | +4.02% (put spread w/stop) | +7.49% (no stop, OTM) | **+7.49% + +23.7% (dual)** |
| Bearish_LowIV | — | +22.6% (long straddle) | unchanged |
| Bullish_HighIV | +4.57% (spread w/stop) | +8.26% (no stop, aggressive) | unchanged |
| Bullish_LowIV | Skip | Skip | **+10.4% (double cal)** |

---

## Regime Distribution by Year

| Year | Bearish_HighIV | Bearish_LowIV | Bullish_HighIV | Bullish_LowIV (skip) |
|------|---------------|---------------|----------------|----------------------|
| 2018 | 10 | 12 | 0 | 28 |
| 2019 | 1 | 8 | 0 | 42 |
| 2020 | 10 | 0 | 31 | 8 |
| 2021 | 4 | 1 | 14 | 31 |
| 2022 | 32 | 2 | 14 | 3 |
| 2023 | 7 | 8 | 2 | 34 |
| 2024 | 3 | 4 | 3 | 41 |
| 2025 | 7 | 4 | 8 | 31 |

**Current regime (2026-03-21): Bearish_HighIV** — SPY below 50MA, VIX elevated.
→ **Trades: (1) Bull put spread 0.25Δ/0.15Δ, ~20 DTE, no stop, 1.5% sizing.**
→ **         (2) Double calendar 0.25P/0.10C, ~12 DTE short / ~19 DTE long, hold, 1.5% sizing.**

---

## Sizing & Portfolio Context

- **Bearish_HighIV:** Run put spread (1.5%) + double calendar (1.5%) simultaneously.
  Total 3% = same as prior single put spread, but split across two uncorrelated structures.
  Further reduce put spread to 1% if QQQ also fires that week (correlated put delta).
- **Bullish_HighIV:** Bull put spread 2–3%. Reduce to 1.5% if QQQ fires same week.
- **Bearish_LowIV:** Long straddle 1–2%. Debit strategy; max loss = premium paid.
- **Bullish_LowIV:** Double calendar 2–3%. Max loss = net debit (~$2.15/shr). ~7 contracts
  at $1,500 deployment per entry.
- **Double calendar sizing note:** At avg debit $2.15/shr, $1,500 → ~7 contracts.
  Max loss $1,505/trade. Two concurrent entries possible (12-day hold, weekly entries).

---

## What Doesn't Work on SPY

| Strategy | Reason |
|----------|--------|
| Bear call spreads | -20% ROC in Bearish_HighIV, -17.6% in Bullish_HighIV. SPY upward drift makes OTM calls cheap to buy back. |
| 2× stop loss | Hurts in all 4 regimes. −2.84% in Bearish_HighIV, −5.44% in Bearish_LowIV, −0.46% in Bullish_HighIV. SPY mean-reverts through stops. |
| Iron condors | 31.4% win rate overall (67.8% stop rate). Too much two-sided exposure on a macro index. |
| Short strangles | +14.6% avg ROC in Bullish_LowIV but -481% in 2020, -163% in 2022. Unbounded risk on SPY is a portfolio-killer. |
| Short straddle | -19.9% ROC in Bearish_LowIV — worst single-strategy result in any regime. |

---

## Key Scripts

```bash
# Full regime strategy study
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_tlt_strategy_study.py --ticker SPY

# Per-regime delta sweep (with and without stop)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_qqq_regime_put_sweep.py --ticker SPY
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_qqq_regime_put_sweep.py --ticker SPY --no-stop

# Strangle sweep
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \
    PYTHONPATH=src .venv/bin/python3 run_tlt_strangle_study.py --ticker SPY --regime ALL
```

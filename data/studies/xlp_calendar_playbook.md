# XLP Put Calendar Spread — Trading Playbook

**Last updated:** 2026-03-22
**Status:** Research complete. Ready to trade.

---

## Overview

Buy a put calendar spread on XLP (Consumer Staples Select Sector SPDR Fund) on eligible Fridays
when the forward volatility factor is favorable. The strategy shares the same structural edge as
the XLU put calendar:

1. **Mean-reverting price behavior** — Consumer staples (PG, KO, PEP, CVS, etc.) have stable
   earnings and steady dividend demand. XLP oscillates around rate/valuation expectations rather
   than trending aggressively, keeping it pinned near the ATM strike at short expiry.

2. **Near-term IV periodically elevated** — FOMC meetings and CPI/PPI prints create recurring
   vol spikes in defensive sectors. When the front-month IV is elevated vs. the forward window,
   the calendar buys cheap longer-dated vol and sells overpriced short-dated vol at the same
   strike. The `fwd_vol_factor ≤ 0.90` filter selects these episodes (~20% of Fridays).

This is a **net debit** strategy. Max loss = net debit paid.

---

## Entry Rules

### Every Friday, ~20 DTE — check fwd_vol_factor:

| Condition | Action |
|---|---|
| **fwd_vol_factor ≤ 0.90** | Buy put calendar spread (primary filter) |
| **fwd_vol_factor 0.91–1.00** | Optional entry (lower edge, use judgment) |
| **fwd_vol_factor > 1.00** | Skip — market expects vol to rise in forward window |

The ≤ 0.90 filter fires on approximately **~10 Fridays per year** (78 trades over 8 years,
2018–2025). It selects the highest-quality entries where near-term IV is most elevated relative
to the forward window.

**Entry mechanics:**
- Short leg: ATM put (~0.50Δ), front monthly expiry (~20 DTE)
- Long leg: ATM put, **same strike**, next monthly expiry (25–50 day gap from short expiry)
- Max bid-ask spread: 25% of mid on the short leg
- Both legs must have positive bid

**Forward vol factor formula** (identical to XLU):
```
short_iv = BS_IV(short_mid, K=strike, T=short_dte/365, r=0.04)
long_iv  = BS_IV(long_mid,  K=strike, T=long_dte/365,  r=0.04)
var_fwd  = (long_iv² × T_long − short_iv² × T_short) / (T_long − T_short)
fwd_vol_factor = √var_fwd / short_iv

< 1.0 → vol expected to FALL in forward window → ENTER
> 1.0 → vol expected to RISE → SKIP
NaN   → extreme backwardation (var_fwd < 0) → ENTER (most favorable)
```

**Note on tiny debits:** XLP options trade at $0.07–$0.16/share ($7–$16/contract). Commission
efficiency is critical — use IBKR Pro (~$0.50–$0.65/contract) and trade at least 5 contracts
per entry.

---

## Exit Rules

| Trigger | Action |
|---|---|
| Spread value ≥ 1.25× net debit (**+25% ROC**) | Close entire spread — profit take |
| Short leg reaches expiry (target not hit) | Close entire spread at market |

Close both legs simultaneously. Do not leg out.

**Why 25% target:** Testing across profit targets (10%, 15%, 25%, 35%, 50%) on the unfiltered
universe confirms 25% as the sweet spot — higher targets gain minimal extra ROC while dropping
win rate sharply (35%: 69.8% win / +24.5% ROC vs 10%: 86.7% win / +18.7% ROC). At the
fwd_vol_factor ≤ 0.90 filter level, the 25% target achieves 82.1% win / +54.7% avg ROC.

---

## Parameters

| Parameter | Value |
|---|---|
| Underlying | XLP |
| Option type | Put calendar (long calendar, net debit) |
| Delta target | ~0.50Δ (ATM) |
| Short DTE | ~20 DTE (front monthly) |
| Long DTE | Next monthly expiry, 25–50 day gap from short |
| Primary filter | fwd_vol_factor ≤ 0.90 (~10 trades/year) |
| Alternative filter | fwd_vol_factor ≤ 1.00 (~22 trades/year, lower edge) |
| VIX filter | None required (VIX alone does not improve performance) |
| Spread filter | BA ≤ 25% of mid on short leg |
| Profit target | +25% ROC (spread value ≥ 1.25× debit) |
| Max hold | Short expiry (no stop-loss — defined risk) |
| Entry day | Friday |
| Study start date | 2018-01-01 |

---

## Backtested Performance (2018–2025)

### fwd_vol_factor ≤ 0.90 — Primary Filter (78 trades):

| Metric | Value |
|---|---|
| Total trades | 78 (~9.75/year) |
| Win rate | **82.1%** |
| Avg ROC / trade | **+54.7%** |
| Avg fwd_vol_factor at entry | 0.811 |

**Per-year breakdown:**

| Year | N | Win% | Avg ROC% | Notes |
|------|---|------|----------|-------|
| 2018 | 12 | 91.7% | +35.7% | Solid first year |
| 2019 | 8 | 100.0% | +43.1% | Range-bound XLP |
| 2020 | 7 | 85.7% | +106.3% | COVID volatility |
| 2021 | 6 | 66.7% | +29.2% | Weakest year — reopening drift |
| 2022 | 16 | 56.2% | +6.7% | Rate hike cycle — marginal positive |
| 2023 | 12 | 83.3% | +20.4% | Recovery |
| 2024 | 8 | 87.5% | +174.0% | Exceptional — XLP range-bound in Fed cut cycle |
| 2025 | 9 | 100.0% | +92.3% | Strong recent performance |

### fwd_vol_factor ≤ 0.90 — VIX subsets:

| VIX Condition | N | Win% | Avg ROC% |
|---|---|---|---|
| All VIX | 78 | 82.1% | +54.7% |
| VIX < 25 | 54 | 88.9% | +62.2% |
| VIX < 20 | 36 | 94.4% | +69.5% |

VIX < 20 improves both win rate and ROC substantially. Use as a secondary confirmation:
at VIX ≥ 25, consider sizing down or skipping marginal (FVF 0.85–0.90) entries.

---

## Priority Score

```
Priority = (Avg_ROC% × Win_Rate) × (52 / Weeks_Active_Per_Year)
         = (54.7 × 0.821) × (52 / 9.75)
         = 44.9 × 5.33
         ≈ 239   →  Tier A
```

---

## Relationship to XLU Calendar

XLP and XLU share the same entry logic (fwd_vol_factor ≤ 0.90, ATM put, ~20 DTE, 25–50d gap,
25% PT). The two strategies are largely uncorrelated because the XLP vol events come from
consumer/CPI catalysts while XLU is driven by pure rate/utility demand. However, during FOMC
weeks, BOTH may simultaneously be in backwardation — treat them as correlated and size
accordingly (combined 2–3% debit exposure max, not 2% each independently).

---

## Risks and Known Limitations

1. **2022 rate hike cycle** — 16 entries, 56.2% win, +6.7% avg ROC. XLP drifted directionally
   during the rate shock. The filter still fired (vol events during hikes), but performance was
   marginal. Still positive, but a weak year to keep in mind.

2. **Tiny debit — commission sensitivity** — At $7–$16/contract, commissions of $1–2/round trip
   can eat 6–28% of P&L. Only viable with very cheap execution (IBKR Pro). Trade ≥5 contracts.

3. **FOMC overlap with XLU** — Both can fire in the same week. Treat as correlated for sizing.
   If both XLU and XLP fire simultaneously, allocate 1% each (not full size) unless combined
   debit exposure stays under 3%.

4. **Narrow expiry selection** — Requires a standard monthly expiry 25–50 days from short leg.
   Confirm availability before entry on expiry-dense or expiry-sparse calendar weeks.

---

## Live Trading Checklist

**Pre-market Friday:**
1. Find ATM put at ~20 DTE and same-strike put at next monthly expiry (25–50 day gap)
2. Compute short_iv and long_iv via BS implied vol (S ≈ K approximation)
3. Compute fwd_vol_factor = √[(long_iv²×T_long − short_iv²×T_short) / (T_long−T_short)] / short_iv
4. If fwd_vol_factor ≤ 0.90 → enter; if > 1.00 → skip; 0.90–1.00 → judgment
5. Check short leg BA ≤ 25% of mid
6. Note VIX: if VIX ≥ 25, consider reducing to half size
7. Enter: buy calendar at net debit (limit order at mid)

**Daily management:**
- Check spread value = long_mid − short_mid
- If spread value ≥ 1.25 × entry debit → close immediately (both legs)
- Otherwise hold; no stop-loss (defined risk)

**On short expiry day:**
- Close both legs at market if profit target not yet hit

---

## CLI Command

```bash
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  .venv/bin/python3 run_calendar.py \
  --ticker XLP --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
  --deltas 0.50 --profit-target 0.25 --max-fwd-vol-factor 0.90 \
  --detail-delta 0.50 --no-csv
```

---

*Playbook written: 2026-03-22*
*Based on: silver.option_legs_settled + VIX cache, 2018–2025, ~384 eligible Fridays*

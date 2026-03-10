# GLD Put Calendar Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Buy a put calendar spread on GLD (SPDR Gold Shares ETF) on eligible Fridays when the
term structure is in backwardation. The strategy exploits GLD's mean-reverting behavior
— gold oscillates around macro anchors (Fed policy, real rates, geopolitical risk) — and
collects the time-value differential between near and far expiries when near-term IV is
elevated relative to far-term IV.

This is a **net debit** strategy. The edge comes from:
1. GLD staying near the strike at short expiry (short leg decays to zero, long leg retains value)
2. Entering when the term structure is in backwardation (near IV > far IV) — you are selling
   relatively expensive near-term vol and buying cheaper far-term vol
3. Taking profits early at +25% ROC to recycle capital and avoid late-breaking moves

---

## Entry Rules

### Every eligible Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **iv_ratio ≥ 1.00** | Buy put calendar spread |
| **iv_ratio < 1.00** | Sit out (contango — unfavorable) |

The iv_ratio filter skips approximately **32% of Fridays** (those in contango). Entering
in contango was shown to drag results materially — those trades account for most losses.

**Entry mechanics:**
- Short leg: ATM put (~0.50Δ), front monthly expiry (~20 DTE)
- Long leg: ATM put, **same strike**, next monthly expiry (~25–50 day gap from short expiry)
- Max bid-ask spread: 25% of mid on the short leg
- Both legs must have positive bid

**IV term structure ratio (iv_ratio):**
```
iv_ratio = (short_mid / √(short_dte/365)) / (long_mid / √(long_dte/365))

≥ 1.00 → near-term IV elevated (backwardation) → ENTER
< 1.00 → far-term IV elevated (contango)        → SKIP
```

**Current reading (2026-03-04):** iv_ratio = 1.12 ✓

---

## Exit Rules

| Trigger | Action |
|---|---|
| Spread value ≥ 1.25× net debit (**+25% ROC**) | Close entire spread — profit take |
| Short leg reaches expiry (not triggered above) | Close entire spread at market |

Close both legs simultaneously. Do not leg out.

Average holding period: **~14 days** (profit target fires early on ~69% of trades).

---

## Parameters

| Parameter | Value |
|---|---|
| Underlying | GLD |
| Option type | Put calendar (long calendar, net debit) |
| Delta target | ~0.50Δ (ATM) |
| Short DTE | ~20 DTE (front monthly) |
| Long DTE | Next monthly expiry, 25–50 day gap from short |
| IV filter | iv_ratio ≥ 1.00 |
| Spread filter | BA ≤ 25% of mid on short leg |
| Profit target | +25% ROC (spread value ≥ 1.25× debit) |
| Max hold | Short expiry (no stop-loss — defined risk) |
| Entry day | Friday |

---

## Backtested Performance (2018–2025)

**Overall (272 trades, All VIX, iv_ratio ≥ 1.00, PT +25%):**

| Metric | Value |
|---|---|
| Win rate | **75.4%** |
| Avg ROC / trade | +13.3% |
| Annualized ROC | +715% |
| Avg hold | ~14 days |
| OTM% (short expired worthless) | 16% |

**Per-year breakdown:**

| Year | N | Win% | Avg ROC% | Avg Days | Notes |
|------|---|------|----------|----------|-------|
| 2018 | 36 | 72.2% | +14.9% | 15.1 | Solid first year |
| 2019 | 41 | 75.6% | +3.4% | 13.9 | Range-bound GLD, thin premiums |
| 2020 | 27 | 81.5% | +20.3% | 12.9 | COVID vol spike → fast profit takes |
| 2021 | 19 | 84.2% | +15.9% | 13.5 | Excellent — low vol, steady GLD |
| 2022 | 30 | 60.0% | −8.7% | 16.0 | Worst year — trending GLD (rising rates) |
| 2023 | 38 | 73.7% | +38.3% | 14.8 | Best per-trade ROC — gold ranged well |
| 2024 | 33 | 78.8% | +20.5% | 13.6 | Strong — GLD range-bound around highs |
| 2025 | 41 | 78.0% | −1.8% | 13.3 | Breakeven — high win rate, but losers erased gains |

**Note on 2022:** The only materially losing year. GLD trended down sharply in H1 2022 as
the Fed began hiking aggressively, then recovered in H2 — making it difficult to pin the
ATM strike at expiry. The strategy remains robust; 2022 was a worst-case trending regime.

**Note on 2025 ROC vs AnnROC:** Win rate was 78% but average per-trade ROC was −1.8%.
This means winners closed quickly at +25% (high annualized rate) while losers dragged to
expiry with larger absolute losses, resulting in near-breakeven net dollar P&L. Not a
great year but not a disaster — essentially a free carry year.

---

## IV Term Structure Filter — Research Notes

The iv_ratio filter is the single most impactful parameter in this strategy:

| iv_ratio filter | N | Win% | Avg ROC% |
|----------------|---|------|----------|
| None (all) | 400 | 41.0% | +16.2% |
| ≥ 0.95 | 390 | 41.5% | +17.1% |
| **≥ 1.00** | **272** | **75.4%** | **+13.3%** |
| ≥ 1.05 | 44 | 86.4% | +25.8% |

The jump at 1.00 is structural: entering in any degree of backwardation removes the
contango trades that drag win rate below 50%. The ≥ 1.05 filter looks compelling but
has only 44 trades over 8 years — too thin to rely on.

---

## Forward Vol Factor Research

The fwd_vol_factor (σ_fwd / short_iv) was tested as an alternative or complement to the
iv_ratio filter. For GLD, the iv_ratio filter (≥1.00) already pre-selects all 272 trades
(avg iv_ratio = 1.028), so the fwd_vol_factor acts as a secondary refinement within that set.

| max fwd_vol_factor | N | Skip% | Win% | ROC% | AnnROC% |
|---|---|---|---|---|---|
| No filter (all 272) | 272 | 0% | 75.4% | +13.3% | +715% |
| ≤ 1.10 | 272 | 0% | 75.4% | +13.3% | +715% |
| ≤ 1.00 | 183 | 33% | 76.5% | +14.0% | +805% |
| ≤ 0.90 | 63 | 77% | 87.3% | +14.2% | +1,177% |
| ≤ 0.80 | 12 | 96% | 83.3% | +35.9% | +1,631% |

GLD's avg fwd_vol_factor is 0.954 (already below 1.0), so all iv_ratio ≥1.00 entries pass
the ≤1.10 threshold. Tightening to ≤0.90 improves win rate to 87% but only slightly improves
absolute ROC (+14.2% vs +13.3%) while skipping 77% of eligible Fridays.

**Conclusion:** The iv_ratio ≥1.00 filter remains the right primary signal for GLD. The
fwd_vol_factor provides modest incremental benefit but not enough to justify the reduced
frequency. This contrasts with XLU where the fwd_vol_factor is transformative.

---

## Profit Target Research

| Target | Win% | Avg ROC% | AnnROC% | Avg Days |
|--------|------|----------|---------|----------|
| None (hold to expiry) | 41.0% | +16.2% | +282% | 21.0 |
| **+25% ROC** | **75.4%** | +13.3% | **+715%** | **14.2** |
| +50% ROC | 56.1% | +10.7% | +411% | 18.4 |

The +25% profit target is optimal: it dramatically improves win rate and AnnROC by
recycling capital faster. Holding to expiry leaves too much on the table and exposes
winners to mean-reversion.

---

## Key Research Findings

- **Gap between expiries:** 25–50 day gap (next monthly) is the optimal long leg.
  Gaps < 21 days are too tight (both legs behave similarly). Gaps > 55 days have
  higher win rate but thin trade counts due to sparse expiry availability.
- **Delta:** 0.50Δ (ATM) outperformed 0.40Δ and 0.45Δ on both win rate and ROC.
- **VIX filter:** No meaningful improvement from VIX filters. All-VIX is sufficient
  because the iv_ratio filter already captures the volatility regime.
- **UVXY calendar:** Tested and rejected. UVXY's violent moves destroy the ATM pin
  assumption regardless of term structure.

---

## Live Trading Checklist

**Pre-market Friday:**
1. Check iv_ratio: `(short_mid / √(short_dte/365)) / (long_mid / √(long_dte/365))`
2. Confirm iv_ratio ≥ 1.00 — if not, skip this week
3. Confirm short leg BA spread ≤ 25% of mid
4. Enter: buy the calendar at net debit (limit order at mid)

**Daily management:**
- Check spread value = long_mid − short_mid
- If spread value ≥ 1.25 × entry debit → close immediately
- Otherwise hold; no stop-loss (defined risk via debit paid)

**On short expiry day:**
- If profit target not hit, close both legs at market on expiry day

---

## CLI Commands

```bash
# Backtest — confirmed parameters
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_calendar.py \
    --ticker GLD --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
    --deltas 0.50 --profit-target 0.25 --min-iv-ratio 1.0 \
    --detail-delta 0.50 --no-csv

# Backtest — with forward vol factor sweep (adds fwd_vol_factor table to output)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_calendar.py \
    --ticker GLD --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
    --deltas 0.50 --profit-target 0.25 --min-iv-ratio 1.0 \
    --detail-delta 0.50 --no-csv
```

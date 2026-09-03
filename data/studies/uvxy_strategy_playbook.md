# UVXY Combined Strategy — Trading Playbook

**Last updated:** 2026-08-06
**Status:** Entry/exit parameters confirmed and locked. Capital allocation corrected
2026-08-06 — see the Capital Allocation section; prior per-contract sizing figures were
wrong and oversized the call spread by ~4–10×.

---

## Overview

Sell volatility premium on UVXY using two complementary short options structures entered every other Friday at ~20 DTE. The two sides are structurally hedged — call spreads profit when UVXY is stable or falling; short puts profit when UVXY is stable or rising modestly. In 8 years of backtesting, both sides never lost simultaneously.

---

## Entry Rules

### Every other Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Always** | Sell bear call spread (short 0.50Δ call / long 0.40Δ call) |
| **VIX < 20** | Also sell short put (0.40Δ) |
| **VIX ≥ 20** | Call spread only — skip the put |

**Shared entry filters (both sides):**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target
- DTE tolerance: ±5 days around target

---

## Exit Rules

- **Profit take:** Close when position value ≤ 50% of credit received (i.e., keep 50% of premium)
- **Expiry:** If profit target never reached, close/let expire on expiration day
- **Stop-loss:** None — the spread has defined risk by construction; position sizing controls max dollar loss

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.50Δ |
| Long call delta | 0.40Δ (wing = 0.10Δ) |
| Short put delta | 0.40Δ |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday (bi-weekly) |
| Max spread (bid-ask/mid) | 25% on short legs |
| Profit take | 50% of credit |
| Put VIX filter | VIX < 20 (skip put when VIX ≥ 20) |
| Call VIX filter | None — enter call spread regardless of VIX |
| Start date | 2018-01-12 (UVXY leverage change to 1.5×) |

---

## Capital Allocation ($100k portfolio)

**Budget:** 2% ($2,000) per side, per `capital_allocation_framework.md` — the
portfolio-level authority. This supersedes the 2.5%/side ($10,000 peak) figure this
playbook previously carried.

**Bi-weekly entry → max 2 concurrent positions:**

| Per position | Call spread | Short put |
|---|---|---|
| Capital budget | $2,000 | $2,000 |
| Capital per contract | `(spread width − credit) × 100` at entry | Reg T at entry |
| Contracts | budget ÷ capital-per-contract | budget ÷ capital-per-contract |

**Equal-capital rule:** Allocate $2,000 to each side per trade. The call spread requires
far less capital per contract than the put, so you'll run more spread contracts than puts.

### Size off the actual chain at entry — never off a fixed per-contract figure

Capital required per contract scales with UVXY's price level and the vol regime, and
varies by more than an order of magnitude. Observed 2018–2026 (0.50/0.40 spread and
0.40Δ put, all VIX, split-spanning trades excluded):

| Percentile | Call spread max loss | Short put Reg T |
|---|---:|---:|
| 5th | $37 | $165 |
| 25th | $75 | $323 |
| **Median** | **$117** | **$523** |
| Mean | $158 | $633 |
| 95th | $368 | $1,513 |
| Max | $2,308 | $4,948 |

At the median that is roughly **17 spread contracts** and **4 put contracts** per $2,000
side. In 2020 the spread's mean max loss was $300 and the put's Reg T averaged $958 —
less than half those counts.

**Deployed at any time:**
- VIX ≥ 20 (call spread only): $2,000 per open position
- VIX < 20 (both sides): $4,000 per open position
- Peak (2 concurrent positions, both sides active): **$8,000** (8% of portfolio)

**Priority context:** UVXY is Tier C, score 8 — second-lowest in the book. Under the 25%
($25,000) total open-risk cap it is among the first positions dropped when higher-tier
signals compete for capital. 8% is a ceiling, not a standing allocation.

> **Corrected 2026-08-06.** This section previously stated max loss of ~$38–76/contract
> (call spread) and ~$200–300 (short put), implying 65–130 and 8–12 contracts. Those
> per-contract figures were the 5th–25th percentile of the actual distributions — the
> cheap tail, not the typical case (only 21% and 13% of trades respectively fell in those
> bands). The spread's contract range was additionally ~2× its own arithmetic
> ($2,500 ÷ $38–76 = 33–66, not 65–130). Combined, the call-spread line oversized by
> roughly 4–10×. Sizing off the cheap tail is the dangerous direction: both distributions
> are heavily right-skewed, so the assumed per-contract cost is lowest precisely when a
> widening spread is about to make it much higher.

---

## Backtested Performance (2018–2025)

| Metric | Call Spread only | Short Put only | Combined |
|---|---|---|---|
| Per-trade ROC | +5.06% | +5.22% | **+5.60%** |
| Annualized ROC | +593% | +433% | **+557%** |
| Win rate | 86.6% | 73.2% | 74.6% |
| Worst year ROC | −7.08% (2018) | −5.68% (2019) | **+0.31% (2018)** |
| "Both sides lose" | — | — | **0 of 228 weeks** |

*Every year 2018–2025 was profitable on a combined basis.*

### Per-year combined ROC:

| Year | N trades | Avg combined ROC% |
|---|---|---|
| 2018 | 45 | +0.31% |
| 2019 | 51 | +6.19% |
| 2020 | 48 | +9.22% |
| 2021 | 46 | +8.22% |
| 2022 | 50 | +7.74% |
| 2023 | 41 | +3.48% |
| 2024 | 46 | +3.17% |
| 2025 | 42 | +10.08% |

---

## Research & Validation Notes

- **Optimizer (Optuna, 200 trials):** Ran walk-forward optimization (train ≤ 2022, val ≥ 2023). Best trial achieved Sharpe 0.51 on training but −3.52% combined ROC on validation — worse than the original hand-crafted parameters. Original parameters kept.
- **Stop-loss test:** Tested exits at 2× and 3× credit received. Stop at 2× cut avg ROC from +5.06% to +0.54% (fired on 29% of trades — too many false positives). Stop at 3× cut ROC to +2.96%. Neither eliminated max losses because UVXY spikes gap through stop levels intraday. Decision: no stop-loss.
- **Backtest cadence:** Weekly in the model. Bi-weekly preferred for live trading (half the concurrent positions, 2× size per trade, same catastrophic-loss budget).

---

## Code

```bash
# Full combined study (all data, prints results):
MYSQL_PASSWORD=xxx AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 run_uvxy_combined.py

# Optimizer (200 Optuna trials):
MYSQL_PASSWORD=xxx AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 run_uvxy_optimizer.py

# Stop-loss sensitivity test:
MYSQL_PASSWORD=xxx AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 run_uvxy_stop_loss_test.py
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/put_study.py` — short put engine
- `src/lib/studies/combined_study.py` — merges both strategies, computes equal-capital ROC
- `src/lib/studies/optimizer.py` — Optuna walk-forward optimizer
- `data/studies/uvxy_combined_strategy.md` — full research output with detailed tables

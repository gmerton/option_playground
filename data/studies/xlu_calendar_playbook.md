# XLU Put Calendar Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters updated with forward vol factor findings.

---

## Overview

Buy a put calendar spread on XLU (Utilities Select Sector SPDR Fund) on eligible Fridays
when the forward volatility factor is favorable. The strategy exploits two structural features
of the utilities sector:

1. **Mean-reverting price behavior** — XLU oscillates around rate expectations. Fed meeting
   cycles, CPI prints, and employment data move XLU sharply in one direction, then it
   reverts as the market digests the news. This keeps the underlying pinned near the ATM
   strike at short expiry on most trades.

2. **Near-term IV frequently elevated** — FOMC meetings occur roughly every 6 weeks, and each
   one creates a near-term vol event that elevates the front expiry. However, XLU is NOT
   always in backwardation — ~38% of Fridays are in contango (iv_ratio < 1.0). The forward
   vol factor is a more precise signal for identifying the best entries.

This is a **net debit** strategy. The edge comes from:
- XLU staying near the strike at short expiry (short leg decays to zero, long leg retains value)
- Entering when the market implies vol will be LOWER in the forward window than currently
- +25% ROC profit target recycles capital in ~11 days on average

---

## Entry Rules

### Every Friday, ~20 DTE — check fwd_vol_factor:

| Condition | Action |
|---|---|
| **fwd_vol_factor ≤ 0.90** | Buy put calendar spread (best quality) |
| **fwd_vol_factor 0.90–1.00** | Optional entry (good but lower edge) |
| **fwd_vol_factor > 1.00** | Sit out — market expects vol to rise in forward window |

The ≤0.90 filter skips approximately **76% of Fridays** but selects only the highest-quality
entries. Use ≤1.00 for higher frequency (~54% skip rate) with modestly lower performance.

**Entry mechanics:**
- Short leg: ATM put (~0.50Δ), front monthly expiry (~20 DTE)
- Long leg: ATM put, **same strike**, next monthly expiry (25–50 day gap from short expiry)
- Max bid-ask spread: 25% of mid on the short leg
- Both legs must have positive bid

**Forward vol factor:**
```
Step 1 — Compute BS implied vol for each leg (S ≈ K, ATM approximation):
  short_iv = BS_IV(short_mid, K=strike, T=short_dte/365, r=0.04)
  long_iv  = BS_IV(long_mid,  K=strike, T=long_dte/365,  r=0.04)

Step 2 — Forward variance:
  var_fwd = (long_iv² × T_long − short_iv² × T_short) / (T_long − T_short)

Step 3 — Forward vol factor:
  fwd_vol_factor = √var_fwd / short_iv

< 1.0 → market expects vol to FALL in forward window → ENTER
> 1.0 → market expects vol to RISE                  → SKIP
NaN   → extreme backwardation (var_fwd < 0)          → ENTER (most favorable)
```

**Note on tiny debits:** XLU options trade at very low premiums ($0.10–$0.20/share, $10–$20/contract).
Commission efficiency is critical — use a low-cost broker (e.g., IBKR Pro at ~$0.50–$0.65/contract)
and trade at least 5 contracts per entry to keep commission as a small fraction of the debit.

---

## Exit Rules

| Trigger | Action |
|---|---|
| Spread value ≥ 1.25× net debit (**+25% ROC**) | Close entire spread — profit take |
| Short leg reaches expiry (not triggered above) | Close entire spread at market |

Close both legs simultaneously. Do not leg out.

Average holding period: **~11 days** (profit target fires early on the majority of trades).

---

## Parameters

| Parameter | Value |
|---|---|
| Underlying | XLU |
| Option type | Put calendar (long calendar, net debit) |
| Delta target | ~0.50Δ (ATM) |
| Short DTE | ~20 DTE (front monthly) |
| Long DTE | Next monthly expiry, 25–50 day gap from short |
| Primary filter | fwd_vol_factor ≤ 0.90 (~11 trades/year) |
| Alternative filter | fwd_vol_factor ≤ 1.00 (~22 trades/year) |
| VIX filter | None |
| Spread filter | BA ≤ 25% of mid on short leg |
| Profit target | +25% ROC (spread value ≥ 1.25× debit) |
| Max hold | Short expiry (no stop-loss — defined risk) |
| Entry day | Friday |
| Study start date | 2018-01-01 |

---

## Backtested Performance (2018–2025)

### fwd_vol_factor ≤ 0.90 — Primary Filter (93 trades):

| Metric | Value |
|---|---|
| Total trades | 93 (~11/year) |
| Win rate | **93.5%** |
| Avg ROC / trade | **+78.8%** |
| Annualized ROC | +6,249% |
| Avg hold | ~11 days |
| Short expired OTM | 3% |
| Avg fwd_vol_factor at entry | 0.799 |

### fwd_vol_factor ≤ 1.00 — Higher Frequency (175 trades):

| Metric | Value |
|---|---|
| Total trades | 175 (~22/year) |
| Win rate | **85.7%** |
| Avg ROC / trade | **+49.6%** |
| Annualized ROC | +4,094% |

### All trades, no filter (384 trades) — for reference:

| Metric | Value |
|---|---|
| Total trades | 384 |
| Win rate | 81.5% |
| Avg ROC / trade | +32.9% |
| Annualized ROC | +2,572% |

**Per-year breakdown (no filter):**

| Year | N | Win% | Avg ROC% | Avg Days | Notes |
|------|---|------|----------|----------|-------|
| 2018 | 51 | 90.2% | +27.7% | 11.0 | Solid first year |
| 2019 | 51 | 82.4% | +22.7% | 12.0 | Range-bound XLU |
| 2020 | 48 | 68.8% | +15.4% | 14.6 | COVID vol — more movement |
| 2021 | 50 | 82.0% | +12.2% | 13.0 | Reopening rotation drift |
| 2022 | 51 | 84.3% | +51.9% | 12.4 | Rate hike IV spikes → fast exits |
| 2023 | 51 | 68.6% | +2.6% | 13.8 | Weakest year — rate path uncertainty |
| 2024 | 49 | 83.7% | +79.4% | 10.4 | Exceptional — XLU range-bound in Fed cut cycle |
| 2025 | 33 | 97.0% | +61.7% | 8.7 | Strong recent performance |

---

## Forward Vol Factor Filter — Research Notes

The fwd_vol_factor is the primary signal for this strategy. It captures something the iv_ratio
proxy misses: the *direction* the market expects vol to move in the forward window specifically.

| max fwd_vol_factor | N | Skip% | Win% | ROC% | AnnROC% | OTM% | Avg Factor |
|---|---|---|---|---|---|---|---|
| No filter | 384 | 0% | 81.5% | +32.9% | +2,572% | 11% | 1.056 |
| ≤ 1.30 | 339 | 12% | 82.6% | +35.6% | +2,785% | 10% | 0.976 |
| ≤ 1.20 | 323 | 16% | 83.6% | +37.7% | +2,897% | 10% | 0.963 |
| ≤ 1.10 | 277 | 28% | 84.8% | +42.4% | +3,274% | 8% | 0.934 |
| ≤ 1.00 | 175 | 54% | 85.7% | +49.6% | +4,094% | 7% | 0.871 |
| **≤ 0.90** | **93** | **76%** | **93.5%** | **+78.8%** | **+6,249%** | **3%** | **0.799** |
| ≤ 0.80 | 41 | 89% | 97.6% | +99.6% | +8,867% | 0% | 0.727 |

The ≤0.80 filter looks compelling but with only 41 trades over 8 years (~5/year) the sample
is too thin. ≤0.90 (93 trades) is the practical sweet spot.

---

## iv_ratio vs fwd_vol_factor — Why the Factor Wins

| Filter | N | Win% | ROC% | AnnROC% |
|---|---|---|---|---|
| No filter | 384 | 81.5% | +32.9% | +2,572% |
| iv_ratio ≥ 1.00 (old approach) | 237 | 87.3% | +46.9% | +3,618% |
| fwd_vol_factor ≤ 1.00 | 175 | 85.7% | +49.6% | +4,094% |
| **fwd_vol_factor ≤ 0.90** | **93** | **93.5%** | **+78.8%** | **+6,249%** |

The iv_ratio proxy uses option mid prices as a shortcut. The fwd_vol_factor uses actual
Black-Scholes implied vols and the variance decomposition formula, making it a more precise
measure of what the term structure actually implies about the forward window.

**Note:** XLU is NOT always in backwardation (iv_ratio avg = 0.995 across all 384 trades).
The earlier playbook claim was based on a filtered subset (the 237 iv_ratio ≥ 1.00 trades).

---

## Risks and Known Limitations

1. **Tiny debit — commission sensitivity** — At $10–$20/contract, commissions of $1–2/round
   trip can eat 5–20% of the P&L. Only viable with very cheap execution (IBKR Pro, etc.).
   Trade at least 5 contracts per entry.

2. **Low entry frequency** — The ≤0.90 filter produces ~11 entries/year. In some years
   there may be stretches of several weeks without a qualifying entry.

3. **Trending rate environment** — In a sustained rate-driven trend, the ATM put calendar
   can move against you as the short leg goes deep ITM. The 2020 and 2023 results were the
   weakest years, both characterized by XLU drifting away from the entry strike.

4. **Narrow expiry selection** — The 25–50 day gap constraint requires a standard monthly
   expiry to exist in that window. Confirm expiry availability before entry.

---

## Live Trading Checklist

**Pre-market Friday:**
1. Find ATM put at ~20 DTE and the same-strike put at the next monthly expiry (25–50 day gap)
2. Compute short_iv and long_iv using BS implied vol (S ≈ K approximation is fine)
3. Compute fwd_vol_factor = √[(long_iv²×T_long − short_iv²×T_short)/(T_long−T_short)] / short_iv
4. If fwd_vol_factor ≤ 0.90 → enter; if > 1.00 → skip
5. Confirm short leg BA spread ≤ 25% of mid
6. Enter: buy the calendar at net debit (limit order at mid)

**Daily management:**
- Check spread value = long_mid − short_mid
- If spread value ≥ 1.25 × entry debit → close immediately (both legs)
- Otherwise hold; no stop-loss (defined risk via debit paid)

**On short expiry day:**
- If profit target not hit, close both legs at market on expiry day

---

## CLI Commands

```bash
# Backtest — primary filter
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_calendar.py \
    --ticker XLU --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
    --deltas 0.50 --profit-target 0.25 --max-fwd-vol-factor 0.90 \
    --detail-delta 0.50 --no-csv

# Backtest — higher frequency alternative
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_calendar.py \
    --ticker XLU --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
    --deltas 0.50 --profit-target 0.25 --max-fwd-vol-factor 1.00 \
    --detail-delta 0.50 --no-csv

# Full sweep with no filter (shows fwd_vol_factor distribution)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_calendar.py \
    --ticker XLU --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
    --deltas 0.50 --profit-target 0.25 \
    --detail-delta 0.50 --no-csv
```

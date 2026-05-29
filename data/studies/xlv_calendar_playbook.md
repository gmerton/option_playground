# XLV Put Calendar Spread — Trading Playbook

**Last updated:** 2026-03-22
**Status:** Research complete. Ready to trade.

---

## Overview

Buy a put calendar spread on XLV (Health Care Select Sector SPDR Fund) on eligible Fridays
when the forward volatility factor is favorable. The strategy exploits two structural features
of the healthcare sector:

1. **Mean-reverting price behavior** — Healthcare demand is structurally inelastic. XLV is one
   of the lowest-drift sector ETFs; it rarely trends strongly for extended periods. Earnings
   across the diversified holdings (JNJ, UNH, LLY, ABT, etc.) average out idiosyncratic moves,
   keeping XLV pinned near the ATM strike at short expiry on the majority of entries.

2. **Near-term IV periodically elevated** — FOMC meetings (valuation discount rate impact),
   healthcare budget/policy events, and CPI prints periodically elevate the front-month IV.
   The `fwd_vol_factor ≤ 0.90` filter selects these episodes (~8 Fridays per year), where the
   near-term IV is most elevated vs. the forward window.

This is a **net debit** strategy. Max loss = net debit paid.

---

## Entry Rules

### Every Friday, ~20 DTE — check fwd_vol_factor:

| Condition | Action |
|---|---|
| **fwd_vol_factor ≤ 0.90** | Buy put calendar spread (primary filter) |
| **fwd_vol_factor 0.91–1.00** | Optional entry (lower edge, use judgment) |
| **fwd_vol_factor > 1.00** | Skip — market expects vol to rise in forward window |

The ≤ 0.90 filter fires on approximately **~8 Fridays per year** (62 trades over 8 years,
2018–2025). This is the lowest frequency of the sector calendar strategies (XLU, XLP, XLV),
which is why the priority score is highest — when it fires, it's the most selective signal.

**Entry mechanics:**
- Short leg: ATM put (~0.50Δ), front monthly expiry (~20 DTE)
- Long leg: ATM put, **same strike**, next monthly expiry (25–50 day gap from short expiry)
- Max bid-ask spread: 25% of mid on the short leg
- Both legs must have positive bid

**Forward vol factor formula** (identical to XLU and XLP):
```
short_iv = BS_IV(short_mid, K=strike, T=short_dte/365, r=0.04)
long_iv  = BS_IV(long_mid,  K=strike, T=long_dte/365,  r=0.04)
var_fwd  = (long_iv² × T_long − short_iv² × T_short) / (T_long − T_short)
fwd_vol_factor = √var_fwd / short_iv

< 1.0 → vol expected to FALL in forward window → ENTER
> 1.0 → vol expected to RISE → SKIP
NaN   → extreme backwardation (var_fwd < 0) → ENTER (most favorable)
```

**Note on debits:** XLV options trade at $0.11–$0.39/share ($11–$39/contract). This is
slightly larger than XLU/XLP, giving better commission efficiency. Still use IBKR Pro and
trade ≥5 contracts per entry.

---

## Exit Rules

| Trigger | Action |
|---|---|
| Spread value ≥ 1.25× net debit (**+25% ROC**) | Close entire spread — profit take |
| Short leg reaches expiry (target not hit) | Close entire spread at market |

Close both legs simultaneously. Do not leg out.

**Why 25% target:** Profit target sweep on the full universe (379 trades):
- 10% target: 89.4% win / +19.7% ROC
- 15% target: 85.5% win / +22.8% ROC
- 35% target: 72.6% win / +27.9% ROC
- 50% target: 66.5% win / +31.4% ROC

The ROC gain from 25% → 50% is minimal (+31.4% vs ~+26% at 25%) while win rate drops 20pp.
The FVF-filtered 62 trades at 25% target achieves 87.1% win / +49.0% avg ROC — the selectivity
of the filter makes holding for 25% very achievable on most entries.

---

## Parameters

| Parameter | Value |
|---|---|
| Underlying | XLV |
| Option type | Put calendar (long calendar, net debit) |
| Delta target | ~0.50Δ (ATM) |
| Short DTE | ~20 DTE (front monthly) |
| Long DTE | Next monthly expiry, 25–50 day gap from short |
| Primary filter | fwd_vol_factor ≤ 0.90 (~8 trades/year) |
| Alternative filter | fwd_vol_factor ≤ 1.00 (~16 trades/year, lower edge) |
| VIX filter | None required (VIX alone does not improve performance) |
| Spread filter | BA ≤ 25% of mid on short leg |
| Profit target | +25% ROC (spread value ≥ 1.25× debit) |
| Max hold | Short expiry (no stop-loss — defined risk) |
| Entry day | Friday |
| Study start date | 2018-01-01 |

---

## Backtested Performance (2018–2025)

### fwd_vol_factor ≤ 0.90 — Primary Filter (62 trades):

| Metric | Value |
|---|---|
| Total trades | 62 (~7.75/year) |
| Win rate | **87.1%** |
| Avg ROC / trade | **+49.0%** |
| Avg fwd_vol_factor at entry | 0.794 |

**Per-year breakdown:**

| Year | N | Win% | Avg ROC% | Notes |
|------|---|------|----------|-------|
| 2018 | 8 | 75.0% | +12.4% | Conservative first year |
| 2019 | 2 | 100.0% | +86.5% | Rare signal, high quality |
| 2020 | 9 | 77.8% | +20.3% | COVID volatility |
| 2021 | 2 | 100.0% | +41.7% | Rare signal, high quality |
| 2022 | 9 | 88.9% | +40.0% | Resilient in rate hike cycle |
| 2023 | 10 | 80.0% | +8.2% | Weakest year — policy uncertainty |
| 2024 | 13 | 100.0% | +110.9% | Exceptional — XLV pinned in Fed cut cycle |
| 2025 | 9 | 88.9% | +68.5% | Strong recent performance |

**Key observation:** XLV is more resilient than XLP in rate hike environments. In 2022 (rate
shock), XLV calendar produced 88.9% win / +40.0% ROC vs. XLP's 56.2% / +6.7%. Healthcare
demand is less rate-sensitive than consumer staples pricing power.

### fwd_vol_factor ≤ 0.90 — VIX subsets:

| VIX Condition | N | Win% | Avg ROC% |
|---|---|---|---|
| All VIX | 62 | 87.1% | +49.0% |
| VIX < 25 | 45 | 86.7% | +55.6% |
| VIX < 20 | 31 | 90.3% | +71.6% |

VIX < 20 shows improved ROC (+71.6% vs +49.0%). Use VIX as a sizing signal: at VIX ≥ 25,
consider reducing to half size on marginal entries.

---

## Priority Score

```
Priority = (Avg_ROC% × Win_Rate) × (52 / Weeks_Active_Per_Year)
         = (49.0 × 0.871) × (52 / 7.75)
         = 42.7 × 6.71
         ≈ 286   →  Tier A (ranks #2 behind XLU, ahead of XLP)
```

---

## Relationship to XLU and XLP Calendars

All three sector put calendars (XLU, XLP, XLV) use identical entry logic. Correlation risk:

- **FOMC weeks**: all three may simultaneously be in backwardation. When more than one fires,
  treat them as correlated and cap combined debit exposure at 3% of portfolio ($3,000 on $100K).
- **Relative priority when capped**: XLV > XLP > XLU by priority score, but if XLU fires with
  FVF ≤ 0.80 (deep backwardation), prioritize it — the ≤0.80 bucket historically produces
  the strongest outcomes across all three.
- **Avoid trading all three simultaneously** at full size. If all three fire the same Friday,
  pick the two with the lowest fwd_vol_factor at entry.

---

## Risks and Known Limitations

1. **2023 policy uncertainty** — 10 entries, 80.0% win, +8.2% avg ROC. Drug pricing/Medicare
   negotiations created sustained XLV directionality. Still positive but weakest year.

2. **Low trade frequency** — ~8 entries/year. Some years only 2 entries (2019, 2021). Extended
   periods without a qualifying signal are normal; do not lower the FVF threshold to force entries.

3. **Debit commissions** — At $11–$39/contract, commissions matter less than XLU/XLP but still
   require IBKR Pro at ≥5 contracts per entry.

4. **FOMC overlap with XLU/XLP** — See correlation note above.

---

## Live Trading Checklist

**Pre-market Friday:**
1. Find ATM put at ~20 DTE and same-strike put at next monthly expiry (25–50 day gap)
2. Compute short_iv and long_iv via BS implied vol (S ≈ K approximation)
3. Compute fwd_vol_factor = √[(long_iv²×T_long − short_iv²×T_short) / (T_long−T_short)] / short_iv
4. If fwd_vol_factor ≤ 0.90 → enter; if > 1.00 → skip; 0.90–1.00 → judgment
5. Check short leg BA ≤ 25% of mid
6. Note VIX: if VIX ≥ 25 and FVF is marginal (0.85–0.90), consider half size
7. Check for simultaneous XLU/XLP signals — cap combined debit at 3%
8. Enter: buy calendar at net debit (limit order at mid)

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
  --ticker XLV --short-dte 20 --min-gap 25 --max-gap 50 --spread 0.25 \
  --deltas 0.50 --profit-target 0.25 --max-fwd-vol-factor 0.90 \
  --detail-delta 0.50 --no-csv
```

---

*Playbook written: 2026-03-22*
*Based on: silver.option_legs_settled + VIX cache, 2018–2025, ~379 eligible Fridays*

# TMF Bear Call Spread — Trading Playbook

**Last updated:** 2026-03-19
**Status:** Directionally confirmed. 0.35Δ/0.05Δ wing confirmed optimal. 50% fixed profit take confirmed (ann-target rejected). Data limited to ~2 usable years — treat as watch list until more post-split history accumulates.

---

## Overview

Sell a bear call spread on TMF (Direxion Daily 20+ Year Treasury Bull 3X Shares) every
Friday, regardless of VIX level. TMF is a 3x leveraged long-TLT product — it amplifies the
daily return of 20+ year Treasury bonds by 3x. This creates two structural tailwinds for
short calls:

1. **Rate direction:** When rates are rising (TLT falling), TMF falls 3x as fast. The 2018–
   2026 period has generally been a rising-rate environment, making TMF a natural short-call
   candidate.
2. **Volatility drag:** 3x daily leverage creates compounding decay even in sideways markets.
   This decay is slower than UVIX/UVXY (no structural contango analog) but meaningful over
   20+ DTE holding periods.

TMF's 3x leverage also generates much higher IV than TLT (~40–60% vs TLT's ~15–20%), which
means substantially more premium per delta. This is why, unlike TLT (which needs a VIX≥20
filter to collect enough credit), TMF call spreads work in **all VIX regimes** — the premium
is sufficient even when the broader market is calm.

A bull put spread side was also tested and showed positive results in 2024–2025, but is
discussed in the Research Notes below rather than confirmed as a primary strategy.

---

## ⚠️ Critical Data Limitation

**This is effectively a 2-year backtest, not 8 years.**

TMF's option chain was nearly untradeable from 2018 through 2023 due to the stock's low
price (~$5–28, with a floor at $5–6 in late 2023). The 25% bid-ask spread filter screened
out most entries during this period, leaving only 1–8 qualifying trades per year. After the
December 2023 reverse split (1:10, price: ~$6 → ~$60), liquidity improved dramatically and
trade counts jumped to 47/year.

**Per-year trade count (0.35Δ / 0.05Δ call spread):**

| Year | N trades | Usable? |
|---|---|---|
| 2018 | 0 | No |
| 2019 | 1 | No |
| 2020 | 7 | Marginal |
| 2021 | 5 | Marginal |
| 2022 | 3 | No |
| 2023 | 5 | No (split year) |
| **2024** | **47** | **Yes** |
| **2025** | **47** | **Yes** |

**80% of all trades are from 2024–2025.** The pre-2024 data is too sparse to draw statistical
conclusions. Critically, **2022 — the most severe stress test for a long-bond ETF in 40 years
(Fed +425bp, TLT −31%, TMF −70%+) — produced only 3 call spread trades**, which is
statistically worthless.

**Implication:** Until 2–3 more years of post-split data accumulate (or another stress event
tests the strategy with adequate trade count), treat TMF as a **watch list candidate** with a
directionally sound thesis, not a fully backtested strategy.

This is the same problem UVIX faces at its current ~$6 price. TMF avoided it after the Dec
2023 split but will encounter it again if TMF decays back below ~$15 before the next split.

---

## Entry Rules

### Every Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bear call spread (short 0.35Δ call / long 0.30Δ call) |

No VIX filter — enter every eligible Friday. Unlike TLT (which needs VIX≥20 to collect
adequate premium at its lower IV), TMF's 3x leverage produces sufficient IV-driven premium
in all market regimes.

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target
- Both legs must be in the same expiry
- **Price gate:** If TMF is below ~$15, premium per contract will be marginal — consider
  pausing entries until after the next reverse split

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — spread has defined risk by construction

~87% of trades exit early (profit take fires), average holding period ~11 days.

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.35Δ |
| Long call delta | ~0.30Δ (wing = 0.05Δ — confirmed; see Research Notes) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~28–30% |
| Study start date | 2018-01-01 (usable data from 2024-01-01) |

---

## Capital Allocation

**Approximate spread economics (TMF ~$50–70 at current levels):**

| Item | Approximate value |
|---|---|
| Short call strike (0.35Δ) | ~5–10% OTM |
| Long call strike (~0.30Δ) | ~$1 above short |
| Spread width | $1.00 |
| Credit collected (~29% of width) | ~$0.29/share = $29/contract |
| Max loss per contract | ~$0.71/share = $71/contract |
| 50% profit target | Exit when spread worth ~$0.145 ($14.50/contract) |

**Example sizing ($100k portfolio, 5% max risk = $5,000):**
- Contracts: $5,000 / $71 ≈ 70 contracts per entry
- Max concurrent positions: 2 (overlapping 20-DTE trades)
- Peak capital at risk: ~$10,000

---

## Backtested Performance (2018–2025, usable: 2024–2025)

### Full period (118 trades, 2019–2026):

| Metric | Value |
|---|---|
| Total closed trades | 118 |
| Win rate | 87.3% |
| Mean ROC per trade | +15.07% |
| Early exits (profit take) | 87% |
| Avg holding period | ~11 days |

### Per-year results (0.35Δ / 0.05Δ, All VIX):

| Year | N | Win% | Mean ROC% | Notes |
|---|---|---|---|---|
| 2019 | 1 | 100% | +25.00% | Single trade — ignore |
| 2020 | 7 | 100% | +22.18% | COVID: TMF initially spiked then fell |
| 2021 | 5 | 80% | −1.95% | Fed pivot fears; TMF briefly recovered |
| **2022** | **3** | **67%** | **−13.38%** | **Worst scenario; only 3 trades — unreliable** |
| 2023 | 5 | 80% | +1.86% | Split year (Dec 2023 reverse split) |
| **2024** | **47** | **87.2%** | **+10.93%** | **First full usable year** |
| **2025** | **47** | **87.2%** | **+21.34%** | **Second full usable year** |
| 2026 | 3 | 100% | +40.61% | Partial year |

**The 2022 data point is the most concerning:** a 3-trade sample in the worst possible year
for long-bond ETFs tells us almost nothing about how the strategy would have performed with
proper liquidity. TLT's bear call spread (well-sampled in 2022) lost money that year too
despite the structural tailwind, because rate-driven TLT declines often happen in high-VIX
environments where a volatility spike can temporarily push calls in-the-money.

---

## Split History

| Date | Type | Ratio | Price before | Price after |
|---|---|---|---|---|
| 2016-08-25 | Forward split | 4:1 | ~$116 | ~$29 |
| 2023-12-05 | Reverse split | 1:10 | ~$6 | ~$60 |

The 2016 split predates the 2018 study window. The 2023 reverse split is within the window —
any positions open spanning December 5, 2023 are excluded from backtest statistics. In live
trading, close all positions before any announced reverse split effective date.

**Decay trajectory:** TMF went from ~$29 (post-2016 split) to ~$6 (pre-2023 split) over
7 years — a 1:10 reverse split was inevitable. At current ~$50–70, another 1:10 reverse split
would be triggered if TMF decays to ~$5–7, which at 3x leverage during a bond rally cycle
could happen within 3–5 years. Monitor ProShares/Direxion announcements.

---

## Comparison to TLT

| | TMF | TLT |
|---|---|---|
| Leverage | 3x | 1x |
| Strategy | Bear call spread | Bear call spread |
| VIX filter | None needed | VIX ≥ 20 only |
| Best call combo | 0.35Δ / 0.05Δ, All VIX | 0.35Δ / 0.05Δ, VIX ≥ 20 |
| Mean ROC/trade | +15.07% | +11.57% |
| Win rate | 87.3% | 81.4% |
| Active entries/year (2024–25) | ~47 | ~17 |
| Usable history | **2 years** | **8 years** |
| Credit/spread width | ~29% | ~29% |

TMF is structurally superior on a per-trade basis — higher IV means more entries pass the
liquidity filter and more premium per delta. The same thesis (short bonds in a rising-rate
world) simply earns more per trade at 3x leverage.

However, TLT's 8-year history — including the 2020 COVID flight-to-safety (TLT +20%, lethal
for short calls without a VIX filter), 2022 hike cycle, and 2019 low-rate environment — is
a far more complete stress test than TMF's 2 years.

**Portfolio use:** TMF could substitute or complement TLT calls once 3+ years of post-split
data accumulate. For now, TLT is the more trustworthy strategy. If running both, be aware
they are highly correlated (both short 20yr Treasury direction).

---

## Bull Put Spread — Research Notes (Not Confirmed)

Bull put spreads on TMF showed surprisingly positive results in 2024–2025 (same liquidity
window as the call side):

- **0.25Δ / 0.05Δ / All VIX:** 126 trades, 85.7% win, +7.10% avg ROC (2024–25 bulk)
- **0.25Δ / 0.05Δ / VIX<25:** 114 trades, 87.7% win, +8.66% avg ROC

This is unexpected given TLT's put side was decisively rejected (−221% cumulative SumROC).
The difference is TMF's much higher IV: the premium from a 0.25Δ TMF put is large enough to
compensate for the directional headwind in many environments.

**Per-year (0.25Δ / 0.05Δ puts, All VIX):**

| Year | N | Win% | ROC% |
|---|---|---|---|
| 2019 | 3 | 67% | −17.78% |
| 2020 | 7 | 86% | +25.79% |
| 2021 | 4 | 75% | −6.99% |
| 2022 | 3 | 67% | −17.76% |
| 2023 | 8 | 88% | +10.02% |
| **2024** | **49** | **83.7%** | **+4.55%** |
| **2025** | **47** | **89.4%** | **+9.39%** |

The 2022 and 2019 put data (both losing) suffered the same sample-size problem. The 2024–
2025 results are promising. A combined strategy (calls + puts, similar to UVXY) is worth
investigating once more data accumulates — but for now, the call side is the primary
recommendation.

**Not confirmed for live trading yet.** Revisit in 2027 with 3+ years of post-split data.

---

## Forward Vol Factor

Overall avg fwd_vol_factor: **1.101** (mild contango, less extreme than UVIX's 1.421).

```
  Calls (short=0.35, wing=0.05, All VIX):
    max factor     N   Skip%   Win%    ROC%   AnnROC%
    (no filter)   118    0.0%  87.3%  +15.07%  +1247.3%
    <= 1.00        44   62.7%  93.2%  +18.57%  +1007.3%
    <= 0.90        23   80.5%  91.3%  +15.81%  +1031.1%
```

The ≤1.00 filter improves win rate (93.2%) and per-trade ROC (+18.57%) but skips 63% of
entries, leaving only ~17 trades/year. At that frequency, transaction costs and execution
uncertainty matter more. **No filter recommended** — the full dataset delivers the best
annualized return.

---

## Risks and Known Limitations

1. **2-year backtest** — The primary risk. TLT's 8-year history stress-tests the strategy
   through genuinely diverse rate regimes; TMF's 2 usable years do not. A significant bond
   rally (rate cuts, flight to safety) could produce losses not yet reflected in the data.

2. **2022 not stress-tested** — The worst year for 20yr bonds in 40 years produced only 3
   TMF call spread entries. We do not know how the strategy would have performed with normal
   liquidity in 2022. TLT's call spread lost money in 2023 (TLT bounced) — TMF likely
   would have too, but the magnitude is unknown.

3. **Reverse split risk** — If TMF decays to ~$5–7 before the next split, the option chain
   will become illiquid again and the strategy will be untradeable (same as 2018–2023).
   Monitor TMF price and close positions if approaching low-liquidity territory.

4. **3x leverage amplifies spikes** — A 10% TLT rally moves TMF ~30% in a day. Short call
   spreads can go from profitable to near-max-loss in a single session during a Treasury
   flight-to-safety event (geopolitical shock, bank run, recession fears).

5. **Correlation with TLT** — Running TMF calls alongside TLT calls is not diversification;
   they respond to the same underlying rate movement.

---

## Research Notes

### 2026-03-19: Wing sweep + profit target optimization

**Wing sweep (0.05Δ vs 0.10Δ vs 0.15Δ):** Swept all three wings. 0.05Δ is clearly optimal for TMF:

| Wing | Short Δ | ROC% | Win% | Notes |
|------|---------|------|------|-------|
| 0.05Δ | 0.35Δ | +15.07% | 87.3% | **Confirmed** |
| 0.10Δ | 0.35Δ | +9.63% | 87.8% | −5.4pp penalty |
| 0.10Δ | 0.40Δ | +11.17% | 83.6% | Best 0.10Δ combo, still worse |

The 0.10Δ wing standard (adopted 2026-03-09) does **not** apply to TMF. Rationale: at $50–70,
TMF's strikes are $1 apart. The 0.30Δ long leg is only $1 above the short and fills fine — the
practical fill concern driving the 0.10Δ upgrade was about very far OTM options. The 0.05Δ wing
delivers +15% ROC vs +9.6% for 0.10Δ; retaining it is justified.

**Profit target optimization (IS 2018–2022 / OOS 2023–2026):** Swept 50%–2000% ann-ROC targets.
Every ann_target fires at ~6.3d hold vs 11.5d baseline (TMF's high IV generates enough daily
pnl/margin×365/days to clear any target on day 1–2). Result:

- Baseline (50% fixed): OOS $748.00, +16.4% avg ROC, +1294.7% ann ROC, 11.5d hold
- Any ann_target: OOS $507.50, +10.5% avg ROC, +1236.3% ann ROC, 6.3d hold
- IS SumPnL collapses to $0 with ann_target (thin IS sample can't afford to give up winner upside)

**50% fixed take confirmed optimal.** Ann_target exits winners too early on a fast-decaying,
high-IV underlying — same dynamic as ASHR calls.

---

## Code

```bash
# Bear call spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker TMF --spread 0.25

# Per-year detail for confirmed parameters (0.35Δ/0.05Δ):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker TMF --spread 0.25 --detail-short-delta 0.35 --detail-wing 0.05 --no-csv

# Profit target sweep (reproduces optimization):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_profit_sweep.py \
    --ticker TMF --strategy call_spread --short-delta 0.35 --wing 0.05 --vix none

# Bull put spread sweep (research — not confirmed):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker TMF --spread 0.25 --no-csv
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — TMF parameter configuration
- `src/lib/studies/straddle_study.py` — `TMF_SPLIT_DATES` constant
- `data/studies/tmf_strategy_playbook.md` — this file
- `data/studies/tlt_strategy_playbook.md` — TLT equivalent for comparison

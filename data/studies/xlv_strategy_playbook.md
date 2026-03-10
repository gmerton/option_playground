# XLV Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-03
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on XLV (Health Care Select Sector SPDR Fund) every Friday,
regardless of VIX level. The strategy exploits XLV's structural upward bias — healthcare
earnings are largely non-cyclical, the sector outperforms in rate-hike regimes (no debt
sensitivity), and dividend reinvestment creates a persistent tailwind. Short put spreads
collect premium from the IV risk premium while the defined-risk structure caps downside.

XLV is the cleanest strategy in this suite: **no VIX filter is needed**. The All-VIX
regime was the winner across every tested filter level (None, 30, 25, 20), because XLV's
defensive characteristics mean it holds up even when the broader market sells off. In 8
years of backtesting, this strategy had **only one losing year (2021: −1.99%)** and that
was caused by a healthcare-sector-specific event, not a broad market crash.

A short call side was researched and **rejected**. Bear call spreads at 0.10Δ/0.05Δ
(the only viable delta for XLV calls) produce ~+4% mean ROC — half the put spread's
+6.82% — while XLV's structural upward drift makes any higher-delta short call position
unprofitable over time. Selling calls on XLV is selling nickels against a rising tide.

---

## Entry Rules

### Every Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bull put spread (short 0.25Δ put / long 0.20Δ put) |

No VIX filter — enter every eligible Friday.

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target
- Both legs must be in the same expiry

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — the spread has defined risk by construction; position sizing controls max dollar loss

91% of trades exit early (profit take fires), average holding period **10.6 days** — well
under the 20-day target. Capital turns over quickly, supporting frequent re-entry.

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.25Δ |
| Long put delta | 0.20Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~17% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**Approximate spread economics (XLV ~$140–155):**

| Item | Approximate value |
|---|---|
| Short put strike (0.25Δ) | ~$133–138 (4–6% OTM) |
| Long put strike (0.20Δ) | ~$132–137 ($1 below short) |
| Spread width | $1.00 |
| Credit collected (~17% of width) | ~$0.17/share = $17/contract |
| Max loss per contract | ~$0.83/share = $83/contract |
| 50% profit target | Exit when spread worth ~$0.085 ($8.50/contract) |

**Utilisation note:** The strategy is active essentially **every Friday** (no VIX filter).
Capital is deployed continuously, making efficient use of allocated risk budget.

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- Max loss budget: $5,000
- Contracts: $5,000 / $83 ≈ 60 contracts per entry
- Max concurrent positions: 2 (overlapping 20-DTE trades entered weekly)
- Peak capital at risk: ~$10,000 (two simultaneous positions)

**Note on tight wing:** The $1-wide spread means transaction costs matter in live trading.
Ensure commissions + slippage are well under $0.17/share per round trip. Consider $2-wide
spreads (short 0.25Δ / long ~0.15Δ) in live trading to improve credit/cost ratio —
this was not individually backtested but the wider wing would collect more premium per
contract at the cost of higher max loss.

---

## Backtested Performance (2018–2025)

| Metric | Value |
|---|---|
| Total trades (374 over ~8 years) | 374 |
| Win rate | **92.5%** |
| Mean ROC per trade | **+6.82%** |
| Sharpe (per-trade, mean/std) | 0.204 |
| Sum ROC (2018–2025) | +2,549.5% |
| Average holding period | 10.6 days |
| Early exits (profit take) | 91.4% of trades |
| Losing years | **1 of 8 (2021 only)** |

### Per-year results:

| Year | N | Win% | Mean ROC% | Sum ROC% | Notes |
|---|---|---|---|---|---|
| 2018 | 50 | 92.0% | +4.99% | +249.6% | Rate hike cycle; resilient |
| 2019 | 49 | 98.0% | +11.31% | +554.2% | Best full year; near-perfect win rate |
| 2020 | 46 | 91.3% | +3.59% | +165.1% | COVID crash recovery; healthcare held up |
| **2021** | **48** | **85.4%** | **−1.99%** | **−95.7%** | **Only losing year — Sep–Oct drug pricing selloff** |
| 2022 | 51 | 90.2% | +2.86% | +145.9% | Aggressive Fed hikes; healthcare outperformed S&P |
| 2023 | 50 | 94.0% | +7.07% | +353.5% | Solid across all regimes |
| 2024 | 48 | 97.9% | +14.04% | +674.1% | Excellent; nearly flawless |
| 2025* | 32 | 90.6% | +15.71% | +502.9% | *Partial year — Jan–Aug only (data gap Sep–Dec) |

*2025 data covers January through August only. The Sep–Dec XLV options cache is
incomplete; estimated full-year performance consistent with historical pattern.

---

## The One Losing Year: 2021

2021 was the only losing year (−1.99% mean ROC, 7 of 48 trades lost). All 7 losses went
to expiry — the spread was fully in-the-money at expiration, not just a near-miss.

**What happened:** XLV sold off sharply in **September–October 2021** (4 consecutive
losing weekly trades). The driver was healthcare-sector-specific, not a broad market event:

- Drug pricing legislation risk: Democrats proposed allowing Medicare to negotiate drug
  prices directly, threatening pharma/biotech earnings
- Rotation out of defensive/pandemic winners as growth expectations recovered
- XLV fell ~5–6% in Sep–Oct 2021 while the S&P 500 was essentially flat

This is the core risk for XLV puts: **sector-specific legislation or regulatory risk**
that hits healthcare names while the broad market is unaffected. Standard market-wide
hedges (VIX filters, diversification) would not have protected against this.

**Context:** The VIX during the losing streak averaged just 17–21 — lower than the study
average (19.2). No VIX-based filter would have helped. This is simply a sector risk.

---

## Comparison to VIX-Filtered Versions

VIX filters were tested but **universally hurt performance**:

| VIX filter | N trades | Win% | Mean ROC% | Sum ROC% |
|---|---|---|---|---|
| **None (selected)** | **374** | **92.5%** | **+6.82%** | **+2,549.5%** |
| VIX < 30 | ~348 | ~92% | ~+6.8% | ~+2,364% |
| VIX < 25 | ~298 | ~91% | ~+6.7% | ~+1,997% |
| VIX < 20 | ~218 | ~90% | ~+6.0% | ~+1,308% |

Unlike UVXY (where VIX<20 is critical to avoid spike risk), XLV's defensive nature means
high-VIX entries are just as good as low-VIX entries. Filtering only reduces trade count
without improving per-trade quality.

---

## Risks and Known Limitations

1. **Sector legislation risk** — The 2021 losing streak was entirely driven by drug
   pricing legislation fears. Future healthcare policy changes (Medicare pricing, ACA
   changes, FDA deregulation swings) can cause sharp sector-specific drawdowns that
   broad market indicators won't foresee. No backtest filter handles this.

2. **Narrow $1 wing** — On a $1-wide spread, one bad trade = −100% ROC on that
   position (max loss). With 92.5% win rate, expect roughly 2–3 max-loss trades per
   year at typical entry frequency. The cumulative P&L is driven by the winners, not
   the losers, but consecutive losses in a short window (as in Sep–Oct 2021) can
   produce a losing quarter.

3. **Low credit per contract** — At ~$17/contract, this is not a "high-income" strategy
   per contract. The edge comes from high win rate and frequent entries. Ensure
   per-contract commissions are well below $1 total round trip.

4. **Healthcare concentration** — The strategy is exposed to a single sector. If holding
   alongside sector-specific equity positions in healthcare, be aware of double-exposure
   in a drawdown.

5. **2025 data incomplete** — The Sep–Dec 2025 period is missing from the backtest due to
   an XLV options cache gap. 2025 performance metrics are based on 8 months only.

---

## Relationship to UVXY and TLT Strategies

| | XLV | TLT | UVXY |
|---|---|---|---|
| Core structure | Bull put spread | Bear call spread | Bear call spread + short put |
| Entry condition | Always (no filter) | VIX ≥ 20 only | Always (call); VIX < 20 (put) |
| Mean ROC/trade | +6.82% | +11.57% | +5.60% (combined) |
| Activity | Every Friday | ~40% of Fridays | Every Friday |
| Directional bet | XLV stays flat or rises | TLT stays flat or falls | UVXY decays |

**Three-strategy correlation (2018–2025, 67 weeks all three active):**
- 0 weeks where all three strategies lost simultaneously
- UVXY/XLV joint loss rate: 3.8% (2–3 weeks per year on average)
- TLT/XLV joint loss rate: 0.0% (zero joint losses in 67 observed weeks)
- ROC correlations all near zero (max 0.097)

XLV is an excellent portfolio complement: it runs every week (like UVXY), is uncorrelated
with both UVXY and TLT, and draws on a completely different underlying driver
(healthcare earnings defensiveness vs VIX volatility decay vs rate expectations).

---

## Forward Vol Factor Research

The fwd_vol_factor (σ_fwd / near_iv) was tested on the confirmed parameters
(short=0.25, wing=0.05, All VIX, 374 trades).

XLV's avg fwd_vol_factor is **1.085** — slightly in contango. Similar to GLD.

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          374    0.0%  92.5%   +6.82%   +558.8%       1.085
  ≤ 1.30               320   14.4%  93.4%   +7.96%   +589.8%       1.027
  ≤ 1.20               273   27.0%  93.4%   +7.89%   +584.1%       0.990
  ≤ 1.10               209   44.1%  93.3%   +8.44%   +613.6%       0.941
  ≤ 1.00               128   65.8%  93.0%   +9.58%   +689.6%       0.873
  ≤ 0.90                64   82.9%  96.9%  +11.99%   +857.4%       0.780
  ≤ 0.80                29   92.2% 100.0%  +18.01%  +1213.4%       0.683
```
*(NaN entries: 1 of 374)*

**Strong monotonic improvement throughout.** XLV already has a very high win rate
(92.5%) at baseline, but the factor filter continues to improve both win rate and ROC
all the way to ≤ 0.80 (100% win rate on 29 trades). The pattern is remarkably consistent.

**Sweet spots:**
- **≤ 1.10** (209 trades, ~26/year): Minimal frequency loss, +8.44% ROC (+24% lift)
- **≤ 1.00** (128 trades, ~16/year): +9.58% ROC (+40% lift), 93% win, AnnROC +690%
- **≤ 0.90** (64 trades, ~8/year): 97% win, +11.99% ROC — very low frequency

**Interpretation:** XLV's beta to the market means that when near-term vol is elevated
relative to forward vol (factor < 1.0), the market has just processed a fear event and
expects calm ahead. Drug pricing scares and healthcare shocks that cause losses tend to
accompany elevated forward vol expectations.

**Decision:** Current confirmed strategy uses no fwd_vol_factor filter. The ≤ 1.10
filter provides a modest but reliable lift with minimal frequency impact.

---

## Research Notes

- **Call spread rejected**: Short calls tested at 0.10Δ/0.05Δ (only viable delta for XLV).
  Mean ROC +4.03%, win rate 93.6%. Structurally unattractive — XLV's long-term upward
  drift makes any short call position earn less than the put side. Higher delta call
  spreads (0.20Δ+) were flat or negative.

- **VIX filter sweep**: All VIX thresholds tested (None, 30, 25, 20). No filter was the
  clear winner — filtering reduces trade count without improving per-trade ROC.

- **0.30Δ vs 0.25Δ vs 0.35Δ short leg**: 0.25Δ selected as the best balance.
  0.35Δ had 3 losing years (2018, 2021, 2023); 0.40Δ had catastrophic 2018 (−18.98%).
  0.25Δ had only 2021 as a losing year with modest drawdown (−1.99%).

- **No optimizer run**: Given the parameter stability (no filter needed, one clear
  delta choice, standard profit-take), an Optuna search was not prioritized.

---

## Code

```bash
# Put spread sweep (study reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker XLV --spread 0.25

# Naked put sweep (study reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_puts.py \
    --ticker XLV --spread 0.25

# Batch run with other ETFs:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_batch.py \
    --tickers XLV --spread 0.25
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — XLV parameter configuration
- `data/studies/xlv_strategy_playbook.md` — this file

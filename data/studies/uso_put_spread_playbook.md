# USO Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-04
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on USO (United States Oil Fund) every Friday, regardless of VIX
level. USO holds WTI crude oil futures and was restructured in June 2020 (shifting from
100% front-month contracts to a spread of maturities after WTI went negative in April 2020).
This playbook covers the post-restructuring period only (July 2020 onward).

The strategy collects premium from the IV risk premium on crude oil options while using
the spread structure to cap downside. Unlike equity-sector ETFs (XLV, XLU), USO has no
structural upward bias — the edge here is purely the IV risk premium and time decay, not
a directional bet on oil rising.

**Key differentiation from other portfolio strategies:**
- Pure oil price driver — uncorrelated to GLD (inflation hedge), XLV (healthcare earnings),
  XLU (rate cycle), and UVXY (volatility decay)
- Adds genuine diversification to the portfolio
- Higher credit/width (~20%) than XLV (~17%) due to higher oil IV

---

## Entry Rules

### Every Friday, ~30 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bull put spread (short 0.25Δ put / long 0.20Δ put) |

No VIX filter — enter every eligible Friday. VIX filters were tested and showed no
improvement; oil volatility is driven by OPEC+ decisions and supply/demand shocks that
are largely independent of the equity fear gauge.

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 30-day target
- Both legs must be in the same expiry

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — defined risk by construction; position sizing controls max dollar loss

Average holding period: **~14 days** (~91% of trades exit early via profit take).

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.25Δ |
| Long put delta | 0.20Δ (wing = 0.05Δ) |
| Target DTE | 30 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~20% |
| Study start date | 2020-07-01 (post-restructuring) |

---

## Backtested Performance (2020–2025)

**Overall (258 trades, All VIX, 0.25Δ/0.20Δ, 50% take, 30 DTE):**

| Metric | Value |
|---|---|
| Total trades | 258 |
| Win rate | **92.3%** |
| Mean ROC per trade | **+9.58%** |
| Avg annualized ROC | ~+639% |
| Avg hold | ~14 days |
| Early exit rate | ~91% |
| Losing years | **0 of 6** |

**Per-year breakdown:**

| Year | N | Win% | Avg ROC% | Avg Days | Notes |
|------|---|------|----------|----------|-------|
| 2020 | 21 | 95.2% | +7.60% | 11.6 | Post-restructuring H2 only; oil recovering from COVID lows |
| 2021 | 47 | 93.6% | +8.75% | 13.3 | Oil ran $40→$80; put sellers consistently OTM |
| 2022 | 46 | 89.1% | +8.79% | 14.3 | Oil spiked to $120 then crashed; still profitable |
| 2023 | 51 | 88.2% | +8.39% | 15.4 | Range-bound oil; consistent |
| 2024 | 45 | 91.1% | +8.22% | 12.5 | Steady; no major disruptions |
| 2025 | 42 | 97.6% | +15.71% | 13.5 | Excellent — oil ranged well, vol elevated |

**Note on 2022:** Despite oil spiking to $120 in H1 2022 and crashing back to $70 in H2,
the strategy remained profitable (89.1% win rate, +8.79% avg ROC). This is because OTM
puts at 0.25Δ sit far enough below spot that even a sharp decline needs to be sustained —
a spike up followed by a reversal still leaves the puts OTM at entry.

---

## DTE Comparison (0.25Δ/0.20Δ, 0.05Δ wing, All VIX)

| DTE | Win% | Avg ROC% | Avg Hold | Losing Years | Notes |
|-----|------|----------|----------|--------------|-------|
| 20 | 91.0% | +8.25% | ~11d | 0 | Faster capital recycling |
| **30** | **92.3%** | **+9.58%** | **~14d** | **0** | **Selected — best balance** |
| 45 | 92.0% | +9.55% | ~18d | 0 | Higher year-to-year variance |

30 DTE wins on avg ROC with better year-to-year consistency than 45 DTE. The 2023–2024
period showed thin ROC at 45 DTE (+2.15%, +2.93%) while 30 DTE held up at +8–9%.

---

## Delta Sweep Summary (30 DTE, 0.05Δ wing, All VIX)

| Short Δ | N | Win% | ROC% | Losing years | Notes |
|---------|---|------|------|--------------|-------|
| 0.20 | ~259 | 95.8% | +7.42% | 1 (2023: -0.56%) | Too conservative |
| **0.25** | **258** | **92.3%** | **+9.58%** | **0** | **Selected** |
| 0.30 | ~262 | 87.0% | +8.34% | 1 (2020: -1.05%) | Near-miss in 2020 |
| 0.35 | ~265 | 84.9% | +11.98% | 0 | Higher ROC but 2022 near-miss (+2.38%) |

The 0.25Δ is the only delta with zero losing years across all tested DTE targets. The
0.35Δ looks attractive on ROC but exposed more risk in 2022 (oil supercycle) and has a
lower win rate that could result in a losing year in a sustained oil downturn.

---

## Forward Vol Factor Research

The fwd_vol_factor (σ_fwd / near_iv) was tested on the confirmed parameters
(short=0.25, wing=0.05, All VIX, 30 DTE, 258 trades).

USO's avg fwd_vol_factor is **1.079** — slightly in contango. Near-neutral, similar
to GLD and XLV. Consistent with oil's mean-reverting behavior around OPEC+ anchors.

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          258    0.0%  92.2%   +9.97%   +651.1%       1.079
  ≤ 1.30               240    7.0%  91.7%   +9.44%   +648.0%       1.052
  ≤ 1.20               210   18.6%  91.4%   +9.41%   +657.3%       1.024
  ≤ 1.10               161   37.6%  93.2%  +11.62%   +722.6%       0.986
  ≤ 1.00                78   69.8%  96.2%  +13.67%   +755.4%       0.915
  ≤ 0.90                24   90.7% 100.0%  +21.04%  +1114.4%       0.790
  ≤ 0.80                12   95.3% 100.0%  +20.34%  +1070.9%       0.684
```
*(NaN entries: 4 of 258 — treated as most favorable, always included)*

**Strong monotonic improvement, particularly below 1.00.** The ≤ 1.30 and ≤ 1.20
filters are noise (slightly worse), but below 1.10 the pattern becomes compelling:

**Sweet spots:**
- **≤ 1.10** (161 trades, ~27/year): +11.62% ROC (+16% lift), 93% win, good frequency
- **≤ 1.00** (78 trades, ~13/year): +13.67% ROC (+37% lift), 96% win
- **≤ 0.90** (24 trades, ~4/year): 100% win rate, +21% ROC — extremely thin

**Interpretation:** When the crude oil market prices in falling forward vol (factor < 1.0),
USO is in a consolidating, range-bound regime — the ideal environment for short puts.
Elevated forward vol (factor > 1.10) signals that the market is bracing for a move,
often ahead of major OPEC+ meetings or macro events that could send oil sharply lower.

**Decision:** Current confirmed strategy uses no fwd_vol_factor filter. The ≤ 1.10 filter
(161 trades, ~27/year) provides meaningful lift with still-viable trade frequency.

---

## Risks and Known Limitations

1. **Short study period** — Only 5.5 years of post-restructuring data (vs 8 years for
   GLD/XLV). The 2020 COVID oil crash (negative WTI) occurred before the study window
   and cannot be backtested. A comparable demand shock post-restructuring would be a
   true out-of-sample test of this strategy.

2. **No structural upward bias** — Unlike XLV or GLD, USO does not have an inherent
   directional tailwind. This strategy relies on oil staying above the short put strike
   at expiry, which requires either a flat/rising oil price or a large enough buffer.
   OPEC+ production decisions can cause overnight gaps of 5–10%.

3. **Contango roll drag** — USO suffers from structural contango drag (near-month
   futures are cheaper than far-month). This suppresses USO's long-term price appreciation
   and keeps it range-bound over time — which is actually favorable for put sellers.

4. **Geopolitical tail risk** — A sudden demand collapse (pandemic) or supply shock
   (major producer offline) can move oil 20%+ in days. The 0.25Δ strike sits ~4–6%
   OTM, which is not a wide buffer against a geopolitical gap-down.

5. **Narrow $0.05Δ wing** — The spread width will typically be $0.50–$1.00. Commissions
   matter; ensure per-contract costs are well under $0.05/share round trip.

---

## Comparison to Other Portfolio Strategies

| | USO | GLD | XLV | UVXY |
|---|---|---|---|---|
| Structure | Bull put spread | Bull put spread | Bull put spread | Bear call spread |
| Delta | 0.25Δ/0.20Δ | 0.30Δ/0.25Δ | 0.25Δ/0.20Δ | 0.50Δ/0.40Δ |
| DTE | 30 | 20 | 20 | 20 |
| VIX filter | None | VIX<25 | None | None |
| Win rate | 92.3% | 87.1% | 92.5% | 74.6% |
| ROC/trade | +9.58% | +7.98% | +6.82% | +5.60% |
| Driver | Oil price | Inflation/safe-haven | Healthcare earnings | Vol decay |
| Correlation to others | Near zero | — | — | — |

USO adds the highest per-trade ROC of the put spread strategies and is driven by an
entirely different macro factor (crude oil supply/demand) vs gold, healthcare, or
volatility. It is the purest diversifier in the portfolio.

---

## Code

```bash
# Backtest
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_put_spreads.py \
    --ticker USO --spread 0.25 --short-deltas 0.25 --wing-widths 0.05 \
    --dte 30 --detail-short-delta 0.25 --detail-wing 0.05 --no-csv
```

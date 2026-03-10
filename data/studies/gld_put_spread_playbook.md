# GLD Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on GLD (SPDR Gold Shares ETF) when the VIX is below 25.
The strategy exploits GLD's long-term upward bias driven by inflation hedging demand,
central bank buying, and safe-haven flows — while using the spread structure to cap
downside. The VIX<25 filter avoids the most volatile macro environments where gold can
trend sharply in either direction.

---

## Entry Rules

### Every Friday when VIX < 25, ~20 DTE:

| Condition | Action |
|---|---|
| **VIX < 25** | Sell bull put spread (short 0.30Δ put / long 0.25Δ put) |
| **VIX ≥ 25** | No trade — sit out |

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — defined risk by construction; position sizing controls max dollar loss

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.30Δ |
| Long put delta | 0.25Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | VIX < 25 |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~26% |
| Study start date | 2018-01-01 |

---

## Backtested Performance (2018–2025)

**Overall (319 trades, VIX<25, 0.30Δ/0.25Δ, 50% take):**

| Metric | Value |
|---|---|
| Total trades | 319 |
| Win rate | **87.1%** |
| Mean ROC per trade | **+7.98%** |
| Annualized ROC | +795% |
| Early exit rate | ~87% |
| Losing years | 2018, 2021 only |

---

## Delta / Wing Sweep Summary (VIX<25, All Wings)

| Short Δ | Wing | N | Win% | ROC% | AnnROC% | Credit% |
|---------|------|---|------|------|---------|---------|
| 0.15 | 0.05 | 337 | 96.7% | +3.61% | +327% | 9% |
| 0.20 | 0.05 | 336 | 94.0% | +5.96% | +505% | 15% |
| **0.30** | **0.05** | **319** | **87.1%** | **+7.98%** | **+795%** | **26%** |
| 0.35 | 0.05 | 312 | 84.0% | +9.81% | +998% | 31% |

The 0.30Δ/0.25Δ is the sweet spot: high win rate (87%) with meaningful ROC. The 0.35Δ
has higher ROC but more losing years. Lower deltas (0.15Δ–0.20Δ) have near-perfect win
rates but thin credits that don't justify the capital commitment.

---

## Forward Vol Factor Research

The fwd_vol_factor (σ_fwd / near_iv) was tested as a secondary entry filter on the
confirmed parameters (short=0.30, wing=0.05, VIX<25, 319 trades).

GLD's avg fwd_vol_factor is **1.058** — slightly in contango, close to neutral.
The market does not aggressively price vol changes in either direction for GLD.

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          319    0.0%  87.1%   +7.98%   +795.1%       1.058
  ≤ 1.30               294    7.8%  86.7%   +7.76%   +788.3%       1.027
  ≤ 1.20               275   13.8%  87.3%   +8.60%   +808.2%       1.012
  ≤ 1.10               217   32.0%  89.9%  +11.39%   +869.7%       0.976
  ≤ 1.00               112   64.9%  92.9%  +15.86%  +1013.1%       0.907
  ≤ 0.90                39   87.8%  92.3%  +17.43%  +1016.1%       0.818
  ≤ 0.80                14   95.6%  92.9%  +16.65%  +1055.2%       0.730
```
*(NaN entries: 1 of 319)*

**Strong monotonic improvement.** Unlike TLT where the signal collapses at ≤ 1.00, GLD
shows consistent improvement all the way through the range. The ≤ 1.00 filter is
particularly compelling: 93% win rate and +15.86% ROC (vs 87% and +7.98% baseline) by
targeting entries where the market implies declining vol in the forward window.

**Sweet spots:**
- **≤ 1.10** (217 trades, ~27/year): Good frequency, +11.39% ROC (+43% lift), 89.9% win
- **≤ 1.00** (112 trades, ~14/year): High alpha, +15.86% ROC (+99% lift), 92.9% win, but skips 65%

**Interpretation:** When GLD's term structure prices in falling forward vol (factor < 1.0),
the underlying is in a low-volatility, consolidating regime — exactly when short puts on
GLD perform best. The 2018 and 2021 losing years (trending GLD) were likely characterized
by elevated forward vol factors. The filter is a direct proxy for "is gold calm right now?"

**Decision:** Current confirmed strategy uses All-factor (no filter) for simplicity and
frequency. The ≤ 1.10 filter is a meaningful upgrade worth considering for live trading.

**How to run:**
```bash
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_put_spreads.py \
    --ticker GLD --spread 0.25 --short-deltas 0.30 --wing-widths 0.05 --vix-thresholds 25 \
    --detail-short-delta 0.30 --detail-wing 0.05 --detail-vix 25 --no-csv
```

---

## Risks and Known Limitations

1. **Trending gold environment** — When GLD trends sharply downward (e.g., H1 2022 rate
   hike cycle), the 0.30Δ put can move ITM. The VIX<25 filter reduces but does not
   eliminate this risk.
2. **VIX<25 utilisation** — The strategy is active ~75–80% of Fridays. ~20–25% of weeks
   are skipped. Capital should be deployed elsewhere during VIX≥25 weeks.
3. **Narrow wing** — At 0.05Δ wing, the spread is typically $1–2 wide. Commissions matter.

---

## Relationship to Other GLD Strategy

GLD now has two complementary strategies:
- **Bull Put Spread** (this playbook): credit strategy, ~87% win rate, ~$79/trade at $1k
- **Put Calendar**: debit strategy, ~75% win rate, ~$133/trade at $1k, requires iv_ratio filter

The two can be run simultaneously on different expiry cycles — the put spread is a credit
on a near-term OTM strike while the calendar is an ATM debit. They have different
directional sensitivities and different vol regime requirements.

---

## Code

```bash
# Put spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_put_spreads.py \
    --ticker GLD --spread 0.25 --no-csv
```

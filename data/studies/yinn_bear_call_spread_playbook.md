# YINN Bear Call Spread — Trading Playbook

**Last updated:** 2026-03-09
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bear call spread on YINN (Direxion Daily FTSE China Bull 3X Shares) every Friday,
regardless of VIX level. The strategy exploits YINN's structural downward decay — as a
3x leveraged China ETF reset daily, it suffers compounding (variance drag) that steadily
erodes its value even when China's market moves are modest. Short call spreads collect
this decay premium while the defined-risk structure caps loss to the spread width in the
event of a China bull market surge.

**YINN is structurally similar to SQQQ for this strategy.** The edge is leveraged ETF
decay; the known risk is a strong sustained rally in the underlying (China) pushing YINN
sharply above the short strike.

A bull put spread on YINN was researched and **rejected**. Put spread ROC topped out at
~+6.5% (vs call spread's +12.4%) because YINN's structural downward drift means short
puts are fighting the trend — the stock keeps falling through your short strikes.

---

## Entry Rules

### Every Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bear call spread (short 0.35Δ call / long 0.30Δ call) |

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

~86% of trades exit early (profit take fires).

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.35Δ |
| Long call delta | 0.30Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~27% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**YINN pricing varies widely due to leveraged decay and reverse splits (~$10–$80 range
depending on period). Always verify current price and strike spacing on the live chain.**

| Item | Approximate value |
|---|---|
| Spread width | ~$2.50–5.00 (check live chain) |
| Credit collected (~27% of width) | ~$0.68–1.35 per share |
| Max loss per contract | ~$1.82–3.65 per share |
| 50% profit target | Exit when spread worth ~50% of opening credit |

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- With a $3-wide spread ($219 max loss/contract): ~23 contracts per entry
- Max concurrent positions: ~2 (overlapping 20-DTE trades entered weekly)

---

## Backtested Performance (2018–2026)

| Metric | Value |
|---|---|
| Total closed trades | 237 |
| Win rate | **86.5%** |
| Mean ROC per trade | **+12.44%** |
| Credit as % of spread width | ~27% |
| Losing years | **1–2 of 8 (2019 marginal, 2025 genuine)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2018 | 7 | 100.0% | +22.11% | Sparse entries; YINN was lower-priced |
| **2019** | **2** | **50.0%** | **−33.33%** | 2 trades — statistical noise, not a real losing year |
| 2020 | 24 | 79.2% | +26.37% | COVID crash then China recovery; YINN decayed |
| 2021 | 35 | 88.6% | +16.32% | |
| 2022 | 34 | 91.2% | +13.29% | China lagged US bear market; YINN structural decay |
| 2023 | 49 | 93.9% | +14.80% | |
| 2024 | 47 | 87.2% | +9.88% | |
| **2025** | **38** | **73.7%** | **−0.54%** | China AI/DeepSeek rally + PBOC stimulus; YINN spiked |
| 2026 | 1 | 100.0% | +34.93% | Partial year |

**2019 note:** Only 2 trades active (YINN options were illiquid in early 2019). Not
statistically meaningful. The loss came from a single max-loss trade.

**2025 note:** The genuine losing year. China's AI narrative (DeepSeek) and PBOC
stimulus drove YINN sharply higher mid-year. This is the known risk — identical in
nature to SQQQ's 2022 loss when QQQ crashed and SQQQ surged.

---

## The Structural Thesis

YINN's decay mechanism is mathematical and persistent:

- **Daily rebalancing compounding:** A 3x leveraged product reset daily suffers variance
  drag in volatile or flat markets. Even if China's market ends flat for a month, daily
  volatility erodes YINN's value.
- **China's long-term underperformance vs US:** Over the 2018–2025 study window, China
  markets broadly underperformed US markets. YINN's 3x leverage amplified this.
- **Short call alignment:** When YINN decays, calls above the current price expire
  worthless. The structural decay is the seller's edge.

**The risk:** A genuine China bull market — driven by stimulus, policy reversal, or
a major AI/tech narrative — can push YINN 30–60%+ in weeks. Short calls go ITM and
the spread takes max loss. This is cyclical, not a structural surprise.

---

## Forward Vol Factor Filter

fwd_vol_factor = σ_fwd / near_iv. Overall avg: **1.059** (mild contango; market
slightly expects YINN vol to rise).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%
  -----------------------------------------------------------
  (no filter)          237    0.0%  86.5%  +12.44%  +1320.5%
  ≤ 1.30               223    5.9%  87.0%  +13.28%  +1346.6%
  ≤ 1.20               193   18.6%  88.1%  +14.73%  +1450.8%
  ≤ 1.10               143   39.7%  89.5%  +17.07%  +1631.0%
  ≤ 1.00                80   66.2%  88.8%  +17.59%  +1848.9%
  ≤ 0.90                36   84.8%  94.4%  +32.17%  +3189.4%
  ≤ 0.80                14   94.1%  92.9%  +54.39%  +6263.3%
```

**The ≤1.10 filter is compelling:** skip 40% of entries but raise ROC from +12.44% to
+17.07% and win rate from 86.5% to 89.5%. Trade-off: ~3 trades/month → ~2 trades/month.

**Practical recommendation:** The All-VIX baseline is the primary entry. Consider using
≤1.20 or ≤1.10 as a light screen if you want higher per-trade efficiency.

---

## VIX Filter Analysis

Unlike SQQQ where All-VIX is clearly best, YINN shows some improvement from VIX<20
on per-trade ROC but not enough to justify the lost entries:

| VIX filter | N | Win% | ROC% |
|---|---|---|---|
| **None (selected)** | **237** | **86.5%** | **+12.44%** |
| VIX < 30 | 226 | 86.7% | +12.73% |
| VIX < 25 | 205 | 87.3% | +13.71% |
| VIX < 20 | 143 | 90.2% | +17.35% |

VIX<20 is the best per-trade regime (+17.35% ROC, 90.2% win), skipping 40% of entries.
Decision: **use All-VIX** to maximize total return; the fwd_vol_factor filter is a
better discriminator than VIX for this ticker.

---

## Relationship to SQQQ Bear Call Spread

| | YINN | SQQQ |
|---|---|---|
| Underlying | 3x China Bull (FTSE China 50) | 3x Inverse Nasdaq 100 |
| Structural decay | Yes (leveraged compounding) | Yes (leveraged compounding) |
| Bad scenario | China rallies strongly | QQQ crashes (SQQQ surges) |
| Win rate | 86.5% | 82.7% |
| Mean ROC | +12.44% | +10.04% |
| Losing years | 2025 | 2018, 2022 |
| Correlation | **Low** — YINN loses when China surges; SQQQ loses when QQQ crashes |

**YINN and SQQQ are excellent portfolio companions.** They share the same mechanism
(leveraged decay) but their risk events are uncorrelated: a China bull market year does
not necessarily coincide with a US bear market year (and vice versa). In 2022, SQQQ lost
(QQQ crashed) while YINN won (China underperformed). In 2025, YINN lost (China rallied)
while SQQQ won (QQQ rallied). The two strategies provided natural diversification.

---

## Risks and Known Limitations

1. **China bull markets** — Any sustained China rally of 20%+ will produce a losing year.
   PBOC stimulus, policy reversal, or a technology narrative can drive YINN sharply
   higher. 2025 was the first genuine losing year in the study window.

2. **YINN reverse splits** — YINN periodically undergoes reverse splits as the price
   approaches zero. One confirmed split in the study window: 2021-09-21. Monitor for
   announced splits and close positions that would span the split date.

3. **Variable liquidity** — YINN options can be thin, especially in the 20-DTE window.
   The 25% bid-ask filter rejects some entries. Trade count varies by year (2 in 2019
   vs 49 in 2023). Always verify the live chain before entry.

4. **Near-ATM risk at high deltas** — The 0.35Δ short is moderately OTM but can go
   ITM quickly on a large China gap-up. The spread structure caps the loss, but a
   single week of sharp China rally can flip a profitable position to max loss.

---

## Code

```bash
# Call spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker YINN --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker YINN --spread 0.25 --no-csv \
    --detail-short-delta 0.35 --detail-wing 0.05

# Put spread sweep (research reference — inferior to calls, do not trade):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker YINN --spread 0.25
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — YINN parameter configuration
- `data/studies/yinn_bear_call_spread_playbook.md` — this file

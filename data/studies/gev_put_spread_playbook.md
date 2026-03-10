# GE Vernova (GEV) Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-09
**Status:** PROVISIONAL — 2 years of data (April 2024–present). Parameters look strong but regime is narrow. Deploy small; revisit after 2027 data available.

---

## Overview

Sell a bull put spread on GEV (GE Vernova) every Friday at 20 DTE. GEV is a power generation equipment company spun off from General Electric on April 2, 2024. It makes gas turbines, wind turbines, and grid equipment — the infrastructure at the center of the data center power demand and grid electrification buildout.

**Structural thesis:** AI data centers require 24/7 dispatchable power. Gas turbines are the only scalable solution in the near term. GEV is one of only three Western large gas turbine manufacturers (alongside Siemens Energy and Mitsubishi). Order books are reported to be 2–3 years deep. Grid electrification (EVs, industrial reshoring, AI compute) adds a second, independent multi-decade demand driver.

**Why put spreads work:** GEV's consistent upward trend since the spinoff makes short puts structurally favorable. The defined-risk spread caps loss while theta decay works in the seller's favor.

**Critical caveat:** All backtest data covers April 2024–March 2026 only — a strong bull market / AI infrastructure narrative environment. We do not yet have data for a sector correction or a bear market. Treat results as provisional until 3+ years of data are available.

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
- **Stop-loss:** None — defined risk by construction; position sizing controls max dollar loss

~94–100% of trades exit early (profit take fires within ~10 days on average).

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
| Credit as % of spread width | ~25% |
| Study start date | 2024-04-07 (post-spinoff) |

### Wing width rationale

The 0.05Δ wing (long at 0.20Δ) outperforms wider wings for GEV:
- Higher credit-to-spread-width ratio → better ROC per dollar of capital at risk
- The long at 0.20Δ provides meaningful delta hedge in sharp selloffs
- Wider wings (0.10–0.15Δ) produce lower ROC with no measurable improvement in win rate

---

## Capital Allocation

**GEV price range: ~$150–$400 (April 2024–March 2026); currently ~$300–$350.**

| Item | Approximate value |
|---|---|
| Short put strike (0.25Δ) | ~7–12% OTM |
| Long put strike (0.20Δ) | ~1 strike below short |
| Spread width | ~$5–15 (check live chain; GEV has wide strike spacing) |
| Credit collected (~25% of width) | ~$1.25–3.75 per share |
| Max loss per contract | ~$3.75–11.25 per share |
| 50% profit target | Exit when spread worth ~50% of opening credit |

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- With a $10-wide spread ($750 max loss/contract): ~7 contracts per entry
- Max concurrent positions: ~2 (overlapping 20-DTE trades entered weekly)

**Position sizing note:** Given the provisional status (only 2 years of data), consider limiting GEV to 2–3% of portfolio max risk rather than the standard 5% until more data is available.

---

## Backtested Performance (2024–2026)

**⚠ WARNING: Only ~2 years of data, entirely within the AI infrastructure bull market.**

| Metric | Value |
|---|---|
| Total closed trades | 71 |
| Win rate | **94.4%** |
| Mean ROC per trade | **+17.90%** |
| Credit as % of spread width | ~25% |
| Losing years | **0 of 2 (2024, 2025)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2024 | 17 | 100.0% | +27.63% | Post-spinoff; AI power demand narrative exploding |
| 2025 | 48 | 91.7% | +14.41% | Win rate dipped as GEV faced some volatility |
| 2026 | 6 | 100.0% | +18.27% | Partial year |

**2025 note:** Win rate dropped from 100% to 91.7% as GEV experienced more price volatility. Still strongly profitable (+14.41% avg ROC). This is the more "honest" regime — 2024 was a near-perfect environment for new spinoffs in AI-adjacent infrastructure.

### Alternative: 0.30Δ short / 0.25Δ long (higher delta)

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2024 | 15 | 100.0% | +27.18% | Fewer fills at higher delta |
| 2025 | 49 | 93.9% | +18.93% | Better ROC than 0.25Δ in a volatile year |
| 2026 | 6 | 100.0% | +31.41% | |

At 0.30Δ: 70 trades, 95.7% win, +21.77% avg ROC. Marginally better overall — but 0.30Δ is closer to ATM and will be hit harder in a sector downturn. In the absence of bear market data, both are viable; 0.25Δ is more conservative.

---

## Forward Vol Factor Filter

fwd_vol_factor = σ_fwd / near_iv. Overall avg: **1.083** (mild contango; market slightly expects GEV vol to rise).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%
  -----------------------------------------------------------
  (no filter)           71    0.0%  94.4%  +17.90%  +1186%
  ≤ 1.10                41   42.3%  92.7%  +17.14%  +1304%
  ≤ 1.00                25   64.8%  96.0%  +20.20%  +1356%
  ≤ 0.90                14   80.3%  100.0%  +26.95%  +1806%
```

The filter helps per-trade ROC but skips too many entries to be practically useful with only 2 years of data. **Recommendation: no filter** for now. Revisit once we have 100+ trades.

---

## Structural Thesis

GE Vernova's position in power infrastructure is uniquely strong:

- **Gas turbine oligopoly:** GEV, Siemens Energy, and Mitsubishi are the only large-frame gas turbine manufacturers. Lead times are 2–3 years and growing. New entrants are essentially impossible (the manufacturing expertise and supplier networks took decades to build).
- **AI data center demand shock:** Every major hyperscaler (Microsoft, Google, Meta, Amazon) has committed to building gigawatt-scale data center campuses. Each GW of compute requires ~1 GW of reliable power. Utilities are signing gas turbine orders at unprecedented rates.
- **Grid electrification:** Beyond data centers, EV adoption, industrial electrification, and reshoring of manufacturing all require grid expansion. GEV's grid solutions segment (transformers, HVDC) is also capacity-constrained.
- **Wind exposure (risk):** GEV inherited GE's struggling onshore and offshore wind businesses. Offshore wind in particular has faced cost overruns and project cancellations. This is the main near-term earnings risk and the reason GEV's IV is elevated relative to pure industrials.

**The risk scenario for put sellers:** A broad industrial/energy selloff (Fed-driven recession, oil price collapse, policy reversal on natural gas) could push GEV down 20–30% from elevated levels. With only 2 years of history, we have not stress-tested this scenario. The 2025 win rate of 91.7% suggests some resilience, but a true bear market test has not occurred.

---

## Comparison to Suite

| | GEV | SOXX | XLV | BJ |
|---|---|---|---|---|
| Structure | Bull put spread | Bull put spread | Bull put spread | Bull put spread |
| DTE | 20 (weekly) | 20 (weekly) | 20 (weekly) | 45 (monthly) |
| Win rate | 94.4% | 89.3% | 92.5% | 94.2% |
| Mean ROC | +17.90% | +17.98% | +6.82% | +9.24% |
| Years of data | **2 ⚠** | 8 | 8 | 7 |
| Structural edge | Power infra oligopoly | Semiconductor cycle | Healthcare defensive | Warehouse club moat |

GEV's raw numbers rival SOXX — but SOXX has 8 years including the 2022 semiconductor bear market. GEV is unproven under stress.

---

## Risks and Known Limitations

1. **Only 2 years of data, all in a bull market.** This is the dominant risk. The win rates and ROC figures are exceptional but have never been tested in a bear market, a sector rotation, or a macro downturn. Position sizing should be conservative until a longer track record exists.

2. **Single-name risk:** GEV can drop sharply on earnings misses, wind business writedowns, or a broad industrial selloff. Unlike ETFs, there is no diversification within the position.

3. **Wind business drag:** GEV's offshore wind portfolio has been a source of negative surprises. A major wind project failure or additional cost overruns could trigger a sharp single-day selloff.

4. **Valuation sensitivity:** GEV trades at a premium valuation reflecting its AI/infrastructure narrative. If AI capex cools (e.g., efficiency improvements reduce power demand growth projections), GEV could de-rate quickly.

5. **Strike spacing:** GEV's options chain has wide strike spacing relative to the stock price. Always verify the live chain to ensure the short and long strikes are achievable near the target deltas.

---

## Code

```bash
# Put spread sweep at 20 DTE:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker GEV --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker GEV --spread 0.25 --no-csv \
    --detail-short-delta 0.25 --detail-wing 0.05

# Higher-delta alternative:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker GEV --spread 0.25 --no-csv \
    --detail-short-delta 0.30 --detail-wing 0.05
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — GEV parameter configuration
- `data/studies/gev_put_spread_playbook.md` — this file

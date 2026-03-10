# Celestica (CLS) Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-09
**Status:** PROVISIONAL — viable options data only from 2024 onward (~2 years). Strong numbers but narrow regime. Deploy small; revisit after 2027 data available.

---

## Overview

Sell a bull put spread on CLS (Celestica Inc.) every Friday at 20 DTE. Celestica is an electronics manufacturing services (EMS) company that has transformed from a generic contract manufacturer into a leading hyperscaler infrastructure supplier. Their Connectivity & Cloud Solutions (CCS) segment — AI servers, networking switches, and storage hardware — now accounts for ~60% of revenue and is growing rapidly. Major customers include Microsoft, Google, and Meta.

**Structural thesis:** AI infrastructure capex is a multi-year secular spend cycle. Every dollar Microsoft or Google spends on building data centers flows partly to their EMS partners for server and networking assembly. Celestica has specifically won hyperscaler compute and AI networking contracts that make it a direct proxy for AI capex. The stock reflects this — CLS rose from ~$15 in 2022 to ~$90+ by 2024, driven by contract wins.

**Why put spreads work:** CLS has a strong structural upward trend driven by AI capex. The defined-risk spread captures theta decay while the underlying's upward drift keeps puts well OTM.

**Critical caveats:**
1. Options were too illiquid to trade (failed 25% bid-ask filter) from 2018–2023. All viable backtest data is from 2024–present — approximately 2 years.
2. CLS is a **single-name stock with heavy customer concentration** (2–3 hyperscalers represent the bulk of CCS revenue). An AI capex pullback or a major customer loss would hit CLS disproportionately.
3. At certain delta/wing combinations (0.15Δ/0.05Δ, 0.20Δ/0.10Δ, 0.25Δ/0.15Δ), the backtest shows **negative cumulative SumROC despite positive average ROC** — evidence of fat-tail losses from sharp CLS selloffs in 2024. Stick to the confirmed parameters below.

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

~92% of trades exit early (profit take fires within ~10 days on average).

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
| Credit as % of spread width | ~25–26% |
| Study start date | 2024-01-01 (effective — earlier data is pre-liquidity) |

### Wing width rationale — critical for CLS

The 0.05Δ wing is **mandatory** for CLS. Wider wings showed severe fat-tail behavior:

| Combo | Win% | AvgROC | SumROC | Verdict |
|---|---|---|---|---|
| 0.25Δ / 0.05Δ wing | 93.4% | +17.47% | **+50.7%** | ✓ Use this |
| 0.25Δ / 0.10Δ wing | 91.5% | +11.43% | +41.4% | ✓ Acceptable |
| 0.25Δ / 0.15Δ wing | 91.6% | +10.09% | **-99.3%** | ⛔ Fat tail |

The 0.15Δ wing places the long put at 0.10Δ — so far OTM that it provides almost no real hedge in a sharp selloff. CLS dropped ~40% twice in 2024; at those moments the wide spread takes full max loss while the narrow spread is partially hedged. This is not theoretical — the -99.3% SumROC reflects it directly.

---

## Capital Allocation

**CLS price range: ~$15–$100 (2018–2026); currently ~$60–$80 (post-2024 pullback from highs).**

| Item | Approximate value |
|---|---|
| Short put strike (0.25Δ) | ~7–12% OTM |
| Long put strike (0.20Δ) | ~1–2 strikes below short |
| Spread width | ~$2.50–5.00 (check live chain) |
| Credit collected (~25% of width) | ~$0.63–1.25 per share |
| Max loss per contract | ~$1.88–3.75 per share |
| 50% profit target | Exit when spread worth ~50% of opening credit |

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- With a $3-wide spread ($225 max loss/contract): ~22 contracts per entry
- Max concurrent positions: ~2 (overlapping 20-DTE trades entered weekly)

**Position sizing note:** Given the provisional status and single-name concentration risk, consider limiting CLS to 2–3% of portfolio max risk (half the standard allocation) until more regime data is available.

---

## Backtested Performance (2024–2026)

**⚠ WARNING: Only ~2 years of viable data (2024–2026). Options were illiquid 2018–2023.**

| Metric | Value |
|---|---|
| Total closed trades | 76 |
| Win rate | **93.4%** |
| Mean ROC per trade | **+17.47%** |
| Credit as % of spread width | ~25–26% |
| Losing years | **0 of 2 (2024, 2025)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2024 | 21 | 95.2% | +26.15% | AI capex boom; CLS rose strongly |
| 2025 | 49 | 91.8% | +12.69% | More volatile; AI sentiment softened mid-year |
| 2026 | 6 | 100.0% | +26.07% | Partial year |

**2025 note:** Win rate held at 91.8% despite CLS being volatile — evidence that 0.25Δ / 0.05Δ provides adequate OTM buffer. ROC dropped to +12.69% from +26.15% in 2024, which is a more realistic expectation. The +12.69% figure is still well above XLV (+6.82%) and comparable to BJ (+9.24%).

### Fat-tail warning — what happens at wrong parameters

At 0.25Δ/0.15Δ (wide wing, long at 0.10Δ): SumROC = **-99.3%** despite 91.6% win rate. This means a handful of max-loss trades (when CLS dropped sharply through both strikes) wiped out the cumulative gains from 83 winning trades. Position sizing alone cannot fix this — use the 0.05Δ wing.

---

## Forward Vol Factor Filter

fwd_vol_factor = σ_fwd / near_iv. Overall avg: **1.156** (contango; market expects CLS vol to stay elevated or rise).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%
  -----------------------------------------------------------
  (no filter)           76    0.0%  93.4%  +17.47%  +1129%
  ≤ 1.30                56   26.3%  92.9%  +15.33%  +1173%
  ≤ 1.20                46   39.5%  93.5%  +16.27%  +1203%
  ≤ 1.10                38   50.0%  92.1%  +15.02%  +1182%
  ≤ 1.00                27   64.5%  96.3%  +20.66%  +1213%
```

The filter does not improve results materially — skipping 26–50% of entries barely changes ROC. **Recommendation: no filter.** With only 2 years of data, preserving every entry matters more than marginal efficiency gains.

---

## Structural Thesis

Celestica's CCS (Connectivity & Cloud Solutions) segment is the core:

- **Hyperscaler compute:** CLS assembles AI training and inference servers for major cloud providers. As GPU clusters scale, the assembly demand scales with them. CLS is a pure-play beneficiary of AI capex — without the valuation risk of chip companies themselves.
- **AI networking:** CLS manufactures high-speed switching and routing hardware (400G/800G Ethernet switches) that connects GPU clusters within data centers. This is a faster-growing segment than compute assembly.
- **Diversified EMS base:** Beyond hyperscalers, CLS has aerospace/defense, industrial, and healthcare EMS businesses that provide earnings stability if AI capex slows.

**The risk scenario for put sellers:** AI capex pulls back. If hyperscalers reduce server orders — as happened briefly in late 2024 when DeepSeek-style efficiency narratives circulated — CLS can drop 30–40% in weeks. At 0.25Δ, the short put is ~7–12% OTM, which is not enough buffer against a 30–40% move. The spread structure caps the loss, but position sizing must account for this tail risk.

A secondary risk: customer concentration. If one of the 2–3 key hyperscaler customers internalizes manufacturing or shifts to a competing EMS provider, CLS revenue can drop abruptly. This is a known risk for EMS companies broadly.

---

## Comparison to Suite

| | CLS | GEV | SOXX | XLV |
|---|---|---|---|---|
| Structure | Bull put spread | Bull put spread | Bull put spread | Bull put spread |
| DTE | 20 (weekly) | 20 (weekly) | 20 (weekly) | 20 (weekly) |
| Win rate | 93.4% | 94.4% | 89.3% | 92.5% |
| Mean ROC | +17.47% | +17.90% | +17.98% | +6.82% |
| Years of data | **2 ⚠** | **2 ⚠** | 8 | 8 |
| Structural edge | AI EMS / hyperscaler infra | Power grid / gas turbines | Semiconductor cycle | Healthcare defensive |
| Tail risk | Customer concentration | Wind business; AI capex | Semiconductor bear | Drug pricing legislation |

CLS and GEV are natural portfolio complements — both AI-adjacent, but their risk events are different (customer loss vs. energy sector rotation). Together they add a higher-ROC "AI infrastructure" sleeve to a portfolio anchored by XLV, GLD, and BJ.

---

## Risks and Known Limitations

1. **Only 2 years of viable data.** Pre-2024 options were too illiquid to trade. All performance numbers come from the AI bull market regime. Unknown behavior in a bear market.

2. **Fat-tail loss risk at wrong wing widths.** The 0.05Δ wing is mandatory. At wider wings, catastrophic losses (-99% cumulative SumROC at 0.25Δ/0.15Δ) occur from sharp CLS selloffs. Do not deviate from the confirmed parameters.

3. **Customer concentration.** 2–3 hyperscalers drive the majority of CCS revenue. A single large customer can make or break a quarter.

4. **AI capex cyclicality.** Hyperscaler infrastructure spending can slow suddenly if cloud revenue growth disappoints or if AI efficiency improvements reduce compute demand growth. CLS would be directly impacted.

5. **Single-name vs. sector ETF.** Unlike XLV or SOXX, there is no diversification within the position. Earnings surprises (both directions) can cause sharp single-day moves.

---

## Code

```bash
# Put spread sweep at 20 DTE:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker CLS --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker CLS --spread 0.25 --no-csv \
    --detail-short-delta 0.25 --detail-wing 0.05

# Higher-delta alternative (better ROC, more risk):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 PYTHONPATH=src python3 run_put_spreads.py \
    --ticker CLS --spread 0.25 --no-csv \
    --detail-short-delta 0.30 --detail-wing 0.05
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — CLS parameter configuration
- `data/studies/cls_put_spread_playbook.md` — this file

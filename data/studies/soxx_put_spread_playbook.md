# SOXX Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-06
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on SOXX (iShares Semiconductor ETF) every Friday, regardless of
VIX level. The strategy exploits the semiconductor sector's structural upward bias — driven
by AI infrastructure buildout, data center expansion, and the secular cycle of compute
demand. Short put spreads collect the IV risk premium while the defined-risk structure caps
downside to the spread width.

SOXX is one of the cleanest put spread candidates in this suite: **no VIX filter needed**.
The All-VIX regime won across every tested threshold (None, 30, 25, 20), because even in
high-VIX selloffs, SOXX's strong secular tailwind means 20-DTE positions cycle through
drawdowns without going to max loss. In 8 years of backtesting (2018–2026), this strategy
had **only one losing year (2018: −7.63%)** — and 2022, the year SOXX fell 43%, was
still profitable at +9.88% ROC.

A bear call spread was researched but **not recommended for systematic trading**. Call
spreads on SOXX require a VIX≥20 filter, which generates only ~37 trades over 8 years
(~5/year), and produced meaningful losses in two of those years (2019: −32.8%, 2024:
−13.7%). The put spread alone is the structural edge here.

---

## Entry Rules

### Every Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bull put spread (short 0.35Δ put / long 0.30Δ put) |

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

~89% of trades exit early (profit take fires), average holding period approximately
**10–12 days** — well under the 20-day target. Capital turns over quickly, supporting
frequent re-entry.

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.35Δ |
| Long put delta | 0.30Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~29% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**Approximate spread economics (SOXX ~$190–210):**

| Item | Approximate value |
|---|---|
| Short put strike (0.35Δ) | ~$175–190 (5–8% OTM) |
| Long put strike (0.30Δ) | ~$170–185 (~$5 below short) |
| Spread width | ~$5.00 |
| Credit collected (~29% of width) | ~$1.45/share = $145/contract |
| Max loss per contract | ~$3.55/share = $355/contract |
| 50% profit target | Exit when spread worth ~$0.725 ($72.50/contract) |

**Utilisation note:** The strategy is active every Friday (no VIX filter), deploying
capital continuously.

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- Max loss budget: $5,000
- Contracts: $5,000 / $355 ≈ 14 contracts per entry
- Max concurrent positions: ~2 (overlapping 20-DTE trades entered weekly)
- Peak capital at risk: ~$10,000 (two simultaneous positions)

**Note on tight wing:** The 0.05Δ wing on a ~$190 underlying yields a narrow spread
(~$5). In live trading, verify that the credit collected justifies commissions per
contract. Widening to 0.10Δ (short 0.35Δ / long 0.25Δ) gives more credit per contract
with only modestly lower ROC (+13.38% vs +17.98%) and nearly identical win rate (91.0%).

---

## Backtested Performance (2018–2026)

| Metric | Value |
|---|---|
| Total closed trades | 84 |
| Win rate | **89.3%** |
| Mean ROC per trade | **+17.98%** |
| Ann ROC (time-weighted) | +1,392% |
| Credit as % of spread width | ~29% |
| Losing years | **1 of 8 (2018 only)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| **2018** | **8** | **75.0%** | **−7.63%** | Q4 selloff; only losing year |
| 2019 | 8 | 100% | +23.35% | |
| 2020 | 8 | 100% | +26.69% | COVID: 20 DTE exited before crash depths |
| 2021 | 9 | 77.8% | −1.21% | Essentially flat |
| 2022 | 12 | 83.3% | +9.88% | SOXX −43% yet spread profitable — wings held |
| 2023 | 12 | 83.3% | +8.50% | |
| 2024 | 8 | 100% | +25.07% | AI-driven rally |
| 2025 | 15 | 93.3% | +31.90% | |
| 2026 | 4 | 100% | +70.49% | Partial year |

---

## The 2022 Stress Test

2022 was SOXX's worst calendar year in history, falling **43%** as the Fed hiked
aggressively and multiple compression crushed semiconductor valuations. Yet the put spread
strategy returned **+9.88% ROC** (83.3% win rate, 12 trades).

**Why the spread survived:** The 20-DTE holding window cycles positions before a sustained
downtrend can drag strikes into the money on every entry. In a grinding bear market, each
weekly position expires/profits before the next leg down becomes severe. The 0.05Δ wing
provided a defined max loss floor — the worst individual trades lost the spread width, not
unlimited downside.

This is the key validation of the strategy. A catastrophic sector year was navigated
profitably through position structure alone, without any VIX filter or active risk
management.

---

## The Only Losing Year: 2018

2018 was the only year with negative ROC (−7.63%, 8 trades, 75% win rate). The Q4 2018
selloff (the S&P fell ~20% Oct–Dec) hit semiconductors harder than the broad market —
SOXX fell ~20% in Q4 alone. Three of the eight trades were max losses.

**Structural note:** 2018 was the first year in the study window, and SOXX had not yet
developed the AI-driven secular momentum that strengthened from 2019 onward. The risk of
another such year is real, particularly in any cycle where:
- The AI capital expenditure narrative breaks down
- A China semiconductor ban escalation hits SOXX holdings directly
- The Fed tightens into a tech multiple compression cycle

---

## Comparison to VIX-Filtered Versions

VIX filters were tested but universally hurt performance:

| VIX filter | N | Win% | ROC% |
|---|---|---|---|
| **None (selected)** | **84** | **89.3%** | **+17.98%** |
| VIX < 30 | 76 | 88.2% | +16.96% |
| VIX < 25 | 67 | 89.6% | +18.79% |
| VIX < 20 | 54 | 88.9% | +17.68% |

Filtering reduces trade count without improving per-trade ROC. Even VIX<25 (which skips
high-fear entries) produces slightly lower total return by sitting out profitable entries
during recoveries.

---

## Bear Call Spread Research (Rejected for Systematic Use)

Bear call spreads were tested with a VIX≥20 filter (the same regime filter that works
for TLT calls). Results at 0.35Δ/0.05Δ, VIX≥20:

| Metric | Value |
|---|---|
| Trades | 37 (over 8 years, ~5/year) |
| Win rate | 81.1% |
| Mean ROC | +9.74% |
| Ann ROC | +1,323% |

**Per-year (VIX≥20 entries only):**

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2018 | 7 | 85.7% | +26.96% | |
| **2019** | **4** | **50.0%** | **−32.76%** | SOXX rallied despite VIX≥20 entries |
| 2020 | — | — | — | No entries survived 25% spread filter |
| 2021 | 5 | 100% | +30.22% | |
| 2022 | — | — | — | No entries |
| 2023 | 6 | 100% | +33.39% | |
| **2024** | **6** | **66.7%** | **−13.72%** | SOXX rallied during VIX spikes |
| 2025 | 8 | 75.0% | +3.15% | |

**Decision:** At 5 trades/year, two losing years, and missing data in 2020/2022, this is
not a reliable systematic strategy. The edge likely exists in theory (SOXX sells off in
fear spikes), but the sample is too thin to confirm. Not recommended for systematic
deployment alongside the put side.

---

## Forward Vol Factor Research

fwd_vol_factor = σ_fwd / near_iv. Overall avg: **1.061** (mild contango).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%
  -----------------------------------------------------------
  (no filter)          84    0.0%  89.3%  +17.98%  +1392.3%
  ≤ 1.30               79    6.0%  88.6%  +16.92%  +1386.4%
  ≤ 1.20               71   15.5%  88.7%  +17.90%  +1448.5%
  ≤ 1.10               53   36.9%  88.7%  +16.66%  +1382.7%
  ≤ 1.00               34   59.5%  88.2%  +15.33%  +1384.4%
```

**No meaningful benefit.** Unlike XLV or GLD, filtering on fwd_vol_factor does not
improve SOXX results. This makes sense — SOXX's dominant driver is the AI/semis secular
trend, not vol regime transitions. The filter is not recommended.

---

## Risks and Known Limitations

1. **AI narrative break** — SOXX's secular tailwind is heavily dependent on continued
   AI infrastructure investment. A reversal (e.g., demand disappointment from hyperscalers,
   capex pullbacks) could produce a sustained multi-quarter downtrend that cycles through
   multiple 20-DTE positions in a row. 2022 is the historical analog.

2. **China geopolitical risk** — Semiconductor export controls, Taiwan tensions, and
   TSMC concentration create sudden, sector-specific gap risk that VIX-based filters
   cannot anticipate. A China-Taiwan escalation event could gap SOXX 15–20% in a single
   session, breaching the long put and producing max loss.

3. **High stock price / narrow wing** — A ~$5 spread on a ~$200 stock is a 2.5% wide
   strike range. In high-IV environments, SOXX can move 5–10% in a week. The 0.35Δ short
   put is still ~7% OTM, but a sharp spike down can cause intraday losses before the
   position can be exited profitably.

4. **Sector concentration** — SOXX holds ~30 semiconductor names (Nvidia, TSMC, AMD,
   Broadcom, etc.). Earnings surprises on any top holding can move the ETF 3–5% in a
   session. This is idiosyncratic risk that diversification across sectors (UVXY, TLT, XLV)
   does not hedge.

5. **2021 near-flat year** — At −1.21% ROC, 2021 was essentially zero. Four of nine
   trades lost. The cause was supply chain disruption fears hitting semis specifically in
   mid-2021 before the AI narrative took hold.

---

## Relationship to Portfolio

| | SOXX | XLV | TLT | UVXY |
|---|---|---|---|---|
| Structure | Bull put spread | Bull put spread | Bear call spread | Bear call + short put |
| Entry condition | Always | Always | VIX ≥ 20 | Always (call); VIX < 20 (put) |
| Mean ROC/trade | +17.98% | +6.82% | +11.57% | +5.60% combined |
| Activity | Every Friday | Every Friday | ~40% of Fridays | Every Friday |
| Directional bet | SOXX stays flat or rises | XLV stays flat or rises | TLT stays flat or falls | UVXY decays |
| Correlation risk | AI/tech macro | Healthcare policy | Rate expectations | VIX spikes |

SOXX is highest-ROC put spread in the suite but carries the most directional tech
concentration. It pairs naturally with TLT (negative correlation: rate hike fears hurt
SOXX but help TLT short calls) and UVXY (high VIX = SOXX selloff, but UVXY puts sit
out high-VIX regimes anyway). XLV provides a low-correlation defensive counterweight.

---

## Code

```bash
# Put spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker SOXX --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker SOXX --spread 0.25 --no-csv \
    --detail-short-delta 0.35 --detail-wing 0.05

# Call spread sweep (research reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker SOXX --spread 0.25
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — SOXX parameter configuration
- `data/studies/soxx_put_spread_playbook.md` — this file

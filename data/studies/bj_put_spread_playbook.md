# BJ's Wholesale Club (BJ) Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-09
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on BJ (BJ's Wholesale Club Holdings) targeting **monthly expirations
at 45 DTE**. BJ only has monthly options (no weekly expirations), so the strategy is
inherently a monthly cadence (~10–15 entries per year). The structural edge is BJ's
defensive consumer spending model, membership fee moat (similar to Costco), and
consistent upward price trend since its 2018 IPO.

**Key insight: target 45 DTE, not 20 DTE.** At 20 DTE, the monthly expiration is only
rarely within the ±5 day window, yielding ~4 entries/year. At 45 DTE ±10, the strategy
reliably catches each monthly expiration for 10–31 entries/year.

---

## Entry Rules

### Monthly (~every 3–5 Fridays), ~45 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bull put spread (short 0.20Δ put / long 0.10Δ put) |

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±10 days around 45-day target
- Both legs must be in the same expiry

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — defined risk by construction; position sizing controls max dollar loss

~91% of trades exit early (profit take fires).

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.20Δ |
| Long put delta | 0.10Δ (wing = 0.10Δ) |
| Target DTE | **45 days** |
| DTE tolerance | ±10 days |
| Entry day | Friday (enter when expiry is 35–55 DTE) |
| VIX filter | None — enter every eligible Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~12% |
| Study start date | 2019-01-01 |

### Note on monthly-only options

BJ has ~14 Friday expirations per year (monthly + a few quarterly). There are no weekly
expirations. This means the strategy enters roughly once per month when the next monthly
expiration falls 35–55 days out. Trade count: 10–31 per year, averaging ~19/year.

The forward vol factor (σ_fwd/near_iv) is **unavailable** for BJ — the computation
requires two nearby expirations, which monthly-only chains don't provide. Do not apply
this filter.

---

## Capital Allocation

**BJ price range: ~$28–$95 (2019–2026); currently mid-$70s.**

| Item | Approximate value |
|---|---|
| Short put strike (0.20Δ) | ~5–10% OTM |
| Long put strike (0.10Δ) | ~1–2 strikes below short |
| Spread width | ~$2.50–5.00 (check live chain) |
| Credit collected (~12% of width) | ~$0.30–0.60 per share |
| Max loss per contract | ~$2.20–4.40 per share |
| 50% profit target | Exit when spread worth ~50% of opening credit |

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- With a $3-wide spread ($255 max loss/contract): ~20 contracts per entry
- Max concurrent positions: ~2 (45-DTE overlapping with following month's entry)

---

## Backtested Performance (2019–2026)

| Metric | Value |
|---|---|
| Total closed trades | 156 |
| Win rate | **94.2%** |
| Mean ROC per trade | **+9.24%** |
| Credit as % of spread width | ~12% |
| Losing years | **1 of 7 (2023)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| 2019 | 10 | 90.0% | +2.92% | First year; BJ IPO'd June 2018, options still developing |
| 2020 | 15 | 100.0% | +9.13% | COVID recovery; BJ warehouse clubs benefited |
| 2021 | 19 | 100.0% | +12.20% | Strong consumer spending recovery |
| 2022 | 31 | 93.5% | +6.45% | Resilient; BJ rose while broader market fell |
| **2023** | **21** | **85.7%** | **−3.85%** | Consumer pullback; BJ sold off mid-year |
| 2024 | 27 | 100.0% | +8.74% | Strong year; BJ trends higher |
| 2025 | 31 | 90.3% | +21.78% | Outstanding; defensive retail caught a strong bid |
| 2026 | 2 | 100.0% | +6.77% | Partial year |

**2023 note:** The only losing year. Consumer spending concerns and retail sector
rotation weighed on BJ. The spread structure capped the loss at a manageable −3.85%
mean ROC — not a catastrophic drawdown.

---

## Structural Thesis

BJ's Wholesale Club is a membership-based warehouse retailer competing with Costco and
Sam's Club in the Eastern US. Key characteristics that support short put selling:

- **Membership fee moat:** Recurring revenue from membership fees provides earnings
  stability regardless of near-term consumer sentiment.
- **Defensive retail profile:** Wholesale club shoppers are value-conscious — in
  recessions, consumers trade down to warehouse clubs. BJ often outperforms discretionary
  retail in downturns.
- **Consistent upward price trend:** BJ has risen from ~$30 at IPO (2018) to ~$75–$95
  by 2025. Short puts benefit from this structural upward drift.
- **Low IV:** BJ's IV is ~25–35%, moderate for a single-name stock. The 0.20Δ strike is
  typically 5–10% below spot — a meaningful buffer.

**The risk:** A broad consumer/retail selloff (like 2023) can push BJ down sharply enough
to breach the short strike. Since BJ's options are monthly-only, there is no weekly
roll opportunity — the position holds until expiry or the profit target is hit.

---

## Comparison to Similar Strategies

| | BJ | XLV | SOXX |
|---|---|---|---|
| Structure | Bull put spread | Bull put spread | Bull put spread |
| DTE | 45 (monthly only) | 20 (weekly) | 20 (weekly) |
| Entry | ~1×/month | Every Friday | Every Friday |
| Win rate | 94.2% | 92.5% | 89.3% |
| Mean ROC | +9.24% | +6.82% | +17.98% |
| Losing years | 1 of 7 | 1 of 7 | 1 of 7 |
| Correlation | Low (single name) | Low (sector) | Low (sector) |

BJ has the highest win rate of the three, slightly better ROC than XLV, and
comparable drawdown profile. The monthly entry cadence makes it easy to manage —
one trade per month vs weekly decision-making for XLV and SOXX.

---

## Risks and Known Limitations

1. **Single-name risk:** BJ can drop sharply on earnings surprises, comp-sales misses,
   or sector rotation. Sector ETFs (XLV, SOXX) benefit from diversification; BJ does not.
   Position sizing should be smaller than for sector ETFs to account for this.

2. **Monthly-only chain:** No weekly rolls. If a position moves against you, the only
   option is to close early at a loss or hold to expiry. There is no "roll to next week"
   like with ETF weeklies.

3. **Lower credit/width:** The ~12% credit-to-spread-width is on the lower end (vs
   XLV ~9%, SOXX ~15%). The 0.20Δ strike is conservative, but the lower credit means
   a larger adverse move is needed to generate a meaningful winner. The 50% profit target
   fires reliably (~91% of trades) because the position has time to decay over 45 DTE.

4. **Forward vol filter unavailable:** Monthly options cannot compute σ_fwd/near_iv
   (need two expirations). This filter, which improved results for GLD, XLF, and other
   tickers, is not applicable here.

---

## Code

```bash
# Put spread sweep at 45 DTE (correct for BJ's monthly-only chain):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker BJ --spread 0.25 --dte 45 --dte-tol 10

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker BJ --spread 0.25 --dte 45 --dte-tol 10 --no-csv \
    --detail-short-delta 0.20 --detail-wing 0.10

# NOTE: 20 DTE sweep (incorrect — produces only ~4 entries/year):
# run_put_spreads.py --ticker BJ --dte 20   ← do not use; monthly-only chain
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — BJ parameter configuration
- `data/studies/bj_put_spread_playbook.md` — this file

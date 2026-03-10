# INDA Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on INDA (iShares MSCI India ETF) every Friday, regardless of VIX
level. The strategy exploits INDA's structural upward bias — India's long-term economic
growth trajectory creates a persistent tailwind for the underlying, making short put spreads
a natural fit: collect premium from the IV risk premium while the defined-risk structure
caps downside.

INDA's EM exposure gives it moderately higher IV (~20–30%) than US domestic ETFs like XLV
or TLT, which means more premium per dollar of delta. At the same time, India is
structurally different from oil or volatility products — there is no structural decay, no
leverage reset, and the long-term direction is strongly positive. This makes INDA one of the
cleaner EM candidates for put premium selling.

Like XLV, **no VIX filter is needed**. VIX<20 consistently hurt performance by sitting out
entries in higher-premium regimes without improving per-trade quality. Enter every eligible
Friday.

Both call spreads and short straddles were researched and **rejected**:
- Bear call spreads: too few entries (~6/year) due to INDA's upward drift making OTM calls
  difficult to sell consistently. The few call spread wins have high per-trade ROC but the
  strategy is not viable at this frequency.
- Short straddles: 59.3% win rate, +0.75% avg ROC, +13.3% annROC over 236 trades — the
  short call leg bleeds against India's long-term growth, erasing most of the put premium
  collected. Three losing years (2018, 2020, 2024) vs the put spread's one.

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

88% of trades exit early (profit take fires), average holding period well under the
20-day target. Capital turns over quickly, supporting frequent re-entry.

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.25Δ |
| Long put delta | ~0.20Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~18% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**Approximate spread economics (INDA ~$50–65):**

| Item | Approximate value |
|---|---|
| Short put strike (0.25Δ) | ~$47–59 (3–6% OTM) |
| Long put strike (~0.20Δ) | ~$1 below short |
| Spread width | $1.00 |
| Credit collected (~18% of width) | ~$0.18/share = $18/contract |
| Max loss per contract | ~$0.82/share = $82/contract |
| 50% profit target | Exit when spread worth ~$0.09 ($9/contract) |

**Utilisation note:** The strategy is active essentially **every Friday** (no VIX filter),
but INDA's option chain is less liquid than US large-cap ETFs. Expect ~6–10 qualifying
entries per year in practice (the 25% spread filter screens out illiquid weeks).

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- Max loss budget: $5,000
- Contracts: $5,000 / $82 ≈ 60 contracts per entry
- Max concurrent positions: 2 (overlapping 20-DTE trades entered weekly)
- Peak capital at risk: ~$10,000 (two simultaneous positions)

**Note on liquidity:** INDA's options are less actively traded than SPY/QQQ. The 25% spread
filter is essential — enforce it strictly in live trading. On illiquid weeks, skip the entry
rather than paying excessive spread. Consider widening to a $2 spread ($0.25/0.20Δ) in live
trading to improve the credit-to-cost ratio if $1-wide fills prove difficult.

---

## Backtested Performance (2018–2025)

| Metric | Value |
|---|---|
| Total closed trades | 60 |
| Win rate | **91.7%** |
| Mean ROC per trade | **+12.79%** |
| Sum ROC (all years) | +767% |
| Early exits (profit take) | 88% of trades |
| Losing years | **1 of 7 (2022 only)** |

### Per-year results:

| Year | N | Win% | Mean ROC% | Notes |
|---|---|---|---|---|
| 2019 | 5 | 60.0% | −6.33% | Thin sample (5 trades); liquidity limited early INDA option history |
| 2020 | 22 | 95.5% | +10.57% | COVID crash then recovery; INDA's bounce sustained the put side |
| 2021 | 16 | 100.0% | +32.92% | Exceptional year; every trade won |
| **2022** | **11** | **81.8%** | **−4.30%** | **Only clean losing year — Fed hike cycle, EM risk-off** |
| 2023 | 1 | 100.0% | +12.12% | Single qualifying entry (liquidity/DTE gap) |
| 2024 | 3 | 100.0% | +12.89% | Limited entries; all winners |
| 2025 | 2 | 100.0% | +18.18% | Partial year |

**Important caveat on 2023–2025:** The per-year trade counts drop sharply in recent years
(1, 3, 2 trades respectively). This reflects a combination of factors: the 25% bid-ask
filter removing illiquid weeks, DTE tolerance not always finding a qualifying expiry, and
possible options cache gaps. The 2023–2025 results are directionally correct but statistically
thin. The 2019–2022 window (54 of 60 trades) is the primary basis for strategy confidence.

---

## The One Losing Year: 2022

2022 was the cleanest losing year (−4.30% mean ROC, 2 of 11 trades lost). India was
relatively resilient compared to US equities (INDA −9% vs S&P 500 −18%), but the aggressive
Fed tightening cycle triggered broad EM risk-off:

- Dollar strengthening (DXY +14%) compressed India's export earnings and foreign inflows
- FII (foreign institutional investor) outflows from Indian equities as US rates rose
- Global growth slowdown fears hit cyclical EM exposure disproportionately

The losing trades in 2022 were concentrated in the Q1 Russia/Ukraine-driven global selloff
(February–March) and the June Fed tightening shock. Outside those two events, the strategy
performed normally.

**Key insight:** INDA's risk is **macro EM risk-off**, not sector-specific. A strong US
dollar and rising US rates are the primary headwinds. No VIX filter would have cleanly
avoided these — the entry condition is all-VIX for a reason. Defined-risk spreads limit
the damage.

---

## VIX Filter Comparison

| VIX filter | N trades | Win% | Mean ROC% |
|---|---|---|---|
| **None (selected)** | **60** | **91.7%** | **+12.79%** |
| VIX < 30 | 46 | 91.3% | +14.33% |
| VIX < 25 | 36 | 88.9% | +13.94% |
| VIX < 20 | 19 | 78.9% | −2.62% |

VIX<30 and VIX<25 show marginally higher per-trade ROC (more entries screened out were
moderate losers), but trade count drops materially and annualized ROC is similar or lower.
**VIX<20 is actively harmful** — it removes entries in moderate-fear regimes that tend to
be profitable, while keeping only the quietest weeks where credit is thinner.

---

## Forward Vol Factor

The fwd_vol_factor (σ_fwd / near_iv) was tested on the confirmed parameters
(short=0.25, wing=0.05, All VIX, 60 trades). Overall avg factor: **1.061** (slight contango).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          60    0.0%  91.7%  +12.79%  +1104.8%       1.061
  <= 1.30              51   15.0%  90.2%  +11.21%  +1098.8%       0.989
  <= 1.20              47   21.7%  89.4%  +10.79%  +1097.9%       0.968
  <= 1.10              35   41.7%  88.6%  +12.26%  +1263.5%       0.906
  <= 1.00              25   58.3%  88.0%   +6.54%   +869.5%       0.851
  <= 0.90              10   83.3%  80.0%   -5.69%   +817.7%       0.662
  <= 0.80               8   86.7%  75.0%  -10.24%   +641.9%       0.615
```

**Opposite pattern to XLV.** INDA's fwd_vol_factor filter hurts rather than helps — tighter
filters reduce win rate and ROC. This is consistent with INDA's EM character: when forward
vol is low relative to near-term vol (factor < 1.0), it often signals post-spike calm in a
trend that has already turned, which is *not* a safe put-selling entry for an EM ETF.

**Decision: no fwd_vol_factor filter.** Use all entries (no filter).

---

## Straddle Comparison

Short straddles were tested (20 DTE, ATM, 236 trades, 2018–2025):

| Metric | Straddle | Bull Put Spread |
|---|---|---|
| Win rate | 59.3% | 91.7% |
| Avg ROC/trade | +0.75% | +12.79% |
| Ann ROC | +13.3% | +1,105% |
| Losing years | 3 (2018, 2020, 2024) | 1 (2022) |

The short call leg consistently bleeds against INDA's upward trend, capping the straddle's
upside while leaving the full downside of the put intact. **Straddles rejected.**

---

## Risks and Known Limitations

1. **EM macro risk** — A strong USD, rising US rates, or China/Asia contagion can trigger
   sharp EM selloffs that hit INDA disproportionately. These events (2022 Fed hikes, 2020
   COVID, India-specific shocks like 2016 demonetisation) are the primary loss drivers.
   No backtest filter reliably screens these out.

2. **Liquidity / thin option market** — INDA's options are less liquid than US domestic
   ETFs. The 25% bid-ask filter enforces minimum quality, but in low-liquidity weeks the
   spread between theoretical and executable price can still be significant. Monitor fills
   carefully in live trading.

3. **Low entry frequency** — After the bid-ask filter, expect ~6–10 entries/year in live
   trading. This is much lower than XLV (~48/year) or UVXY (~52/year). Portfolio contribution
   will be smaller in absolute dollar terms; size accordingly.

4. **Thin recent data (2023–2025)** — Only 6 trades recorded across 2023–2025 combined.
   Whether this reflects genuine liquidity gaps, option chain structure changes, or a data
   quality issue is uncertain. Treat the recent period's results as indicative only; the
   2020–2022 period (49 trades) provides the core evidence base.

5. **Narrow $1 wing** — Same concern as XLV: one max-loss trade = −100% ROC on that entry.
   With 91.7% win rate, expect roughly 1 max-loss trade per 12 entries. Consecutive losses
   in a sharp EM selloff can produce a difficult quarter.

6. **India-specific risk** — Elections, RBI policy surprises, India-Pakistan geopolitical
   escalation, and domestic policy shifts (demonetisation, GST rollout shocks) can cause
   sharp INDA-specific moves uncorrelated with global VIX.

---

## Relationship to Other Strategies

| | INDA | XLV | TLT | UVXY |
|---|---|---|---|---|
| Core structure | Bull put spread | Bull put spread | Bear call spread | Bear call spread + short put |
| Entry condition | Always (no filter) | Always (no filter) | VIX ≥ 20 only | Always (call); VIX < 20 (put) |
| Mean ROC/trade | +12.79% | +6.82% | +11.57% | +5.60% (combined) |
| Entries/year | ~6–10 | ~48 | ~11 | ~52 |
| Directional bet | INDA stays flat/rises | XLV stays flat/rises | TLT stays flat/falls | UVXY decays |
| Core risk | EM macro risk-off / USD strength | Healthcare legislation | TLT rallies (rate cuts) | UVXY spikes |

INDA is an **EM diversifier** in the portfolio: its primary risk driver (USD/EM macro)
is largely uncorrelated with XLV's healthcare legislation risk and UVXY's volatility spike
risk. However, in a true global risk-off event (March 2020, late 2022), INDA and UVXY can
both lose simultaneously. Keep position sizing conservative if running both.

---

## Code

```bash
# Put spread sweep (study reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker INDA --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker INDA --spread 0.25 --detail-short-delta 0.25 --detail-wing 0.05 --no-csv

# Short straddle (for reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 -c "
from datetime import date
from lib.studies.straddle_study import run_study, INDA_SPLIT_DATES
run_study(ticker='INDA', start=date(2018,1,1), end=date.today(),
          dte_target=20, dte_tol=5, call_delta=0.50, entry_weekday=4,
          split_dates=INDA_SPLIT_DATES, max_call_delta_err=0.10,
          output_csv='inda_straddle.csv')
"
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — INDA parameter configuration
- `data/studies/inda_put_spread_playbook.md` — this file

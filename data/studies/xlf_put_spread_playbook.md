# XLF Bull Put Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bull put spread on XLF (Financial Select Sector SPDR Fund) every Friday, regardless
of VIX level. XLF tracks large-cap US financials — banks, insurance, asset managers, and
brokerages. The structural thesis mirrors XLV: the US financial sector has a long-term
upward bias driven by economic growth, earnings power, and the compounding effect of
retained capital. Short put spreads collect premium from the IV risk premium while the
defined-risk structure caps downside.

XLF is structurally different from XLV in one important way: **financials are rate-sensitive
and exposed to systemic credit events** (bank runs, credit crises). This is reflected in the
higher delta target (0.35Δ vs XLV's 0.25Δ) — you need to go further from the money to find
adequate premium — and the one sharp losing year (2022: −13.07%) which combined aggressive
Fed hikes with early signs of regional bank stress.

Like XLV, **no VIX filter is needed**. All VIX produces the best trade count and overall
annualized return. A fwd_vol_factor ≤1.10 filter provides a meaningful per-trade lift
(+15.90% vs +11.82%) and is worth monitoring as an optional entry refinement.

Bear call spreads were tested and **rejected** — XLF's $28→$55 upward trend from 2018–2026
kills short calls. Only the 0.10Δ call combo produced marginally positive results (+0.34%
avg ROC) which is not viable. XLF is a pure put-spread play.

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

**Optional refinement:** fwd_vol_factor ≤1.10 improves per-trade ROC by ~35% (see Forward
Vol Factor section). Consider skipping entries where near-term vol is significantly lower
than forward vol (factor > 1.10), signalling the market expects a near-term vol jump.

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — spread has defined risk by construction; position sizing controls max dollar loss

~84% of trades exit early (profit take fires), average holding period ~12 days.

---

## Parameters

| Parameter | Value |
|---|---|
| Short put delta | 0.35Δ |
| Long put delta | ~0.30Δ (wing = 0.05Δ) |
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

**Approximate spread economics (XLF ~$50–57 at current levels):**

| Item | Approximate value |
|---|---|
| Short put strike (0.35Δ) | ~$46–50 (5–8% OTM) |
| Long put strike (~0.30Δ) | ~$1 below short |
| Spread width | $1.00 |
| Credit collected (~27% of width) | ~$0.27/share = $27/contract |
| Max loss per contract | ~$0.73/share = $73/contract |
| 50% profit target | Exit when spread worth ~$0.135 ($13.50/contract) |

**Example sizing ($100k portfolio, 5% max risk = $5,000):**
- Contracts: $5,000 / $73 ≈ 68 contracts per entry
- Max concurrent positions: 2 (overlapping 20-DTE trades entered weekly)
- Peak capital at risk: ~$10,000

**Note on trade frequency:** XLF generates ~26 qualifying entries/year after the 25% spread
filter — roughly 2 per month, lower than XLV (~48/year). This is because XLF's option chain
at 0.35Δ is thinner than XLV's at 0.25Δ. Size accordingly — capital is not continuously
deployed, so account for idle periods in position sizing.

---

## Backtested Performance (2018–2025)

| Metric | Value |
|---|---|
| Total closed trades | 206 |
| Win rate | **86.4%** |
| Mean ROC per trade | **+11.82%** |
| Sum ROC (2018–2025) | +2,434% |
| Early exits (profit take) | 84% of trades |
| Avg holding period | ~12 days |
| Losing years | **1 of 8 (2022 only)** |

### Per-year results (short=0.35Δ, wing=0.05Δ, All VIX):

| Year | N | Win% | Mean ROC% | Notes |
|---|---|---|---|---|
| 2018 | 20 | 90.0% | +12.05% | Rate hike cycle; XLF held up well |
| 2019 | 22 | 90.9% | +10.60% | Strong year across financials |
| 2020 | 24 | 91.7% | +14.77% | COVID crash then sharp V-recovery |
| 2021 | 33 | 84.8% | +8.22% | Solid; higher trade count |
| **2022** | **28** | **67.9%** | **−13.07%** | **Only losing year — see below** |
| 2023 | 21 | 85.7% | +7.73% | Recovery year; regional bank fears faded |
| 2024 | 24 | 83.3% | +8.15% | Good; rate cut cycle started |
| 2025 | 30 | 96.7% | +18.75% | Best full year |

---

## The One Losing Year: 2022

2022 was XLF's worst year in the study (−13.07% mean ROC, 9 of 28 trades lost). XLF fell
~24% over the course of the year, from ~$38 to ~$29, driven by:

- **Federal Reserve aggression:** 425bp of rate hikes in 2022 — the fastest tightening
  cycle since Volcker. While higher rates are nominally good for bank NIM, the speed of
  hikes compressed loan demand and raised credit risk fears.
- **Yield curve inversion:** The 2-year/10-year inversion deepened through 2022, squeezing
  bank net interest margins and signalling recession risk.
- **Pre-SVB stress signals:** Regional bank vulnerabilities were building in H2 2022
  (Silicon Valley Bank and Signature Bank ultimately failed in March 2023, but their
  balance sheet risks were accumulating in 2022).

**Recovery:** 2023 returned to profitability (+7.73%) despite the March 2023 regional bank
crisis, because by then XLF had re-priced lower and the 0.35Δ short strikes were further
from spot. The sector stabilized after FDIC intervention.

**Key insight:** The 2022 loss was driven by a slow, sustained sector decline — not a sharp
one-day spike. This is the characteristic XLF risk: extended rate/credit-driven drawdowns
that grind puts into the money over multiple weeks. The 0.05Δ wing limits max loss per
trade to ~$0.73/share, which contains the damage, but 9 of 28 trades going to max loss
in a single year is the worst-case scenario.

---

## Comparison to XLV

| | XLF | XLV |
|---|---|---|
| Short put delta | 0.35Δ | 0.25Δ |
| Mean ROC/trade | **+11.82%** | +6.82% |
| Win rate | 86.4% | **92.5%** |
| Entries/year | ~26 | ~48 |
| Losing years | 1 of 8 (2022) | 1 of 8 (2021) |
| Core risk | Bank/credit systemic events | Healthcare legislation |
| Upward drift | Strong ($28→$55, +96% since 2018) | Moderate, defensive |

XLF earns nearly double the per-trade ROC of XLV (+11.82% vs +6.82%) but with a lower
win rate, fewer annual entries, and a more severe losing year (−13.07% vs XLV's −1.99%).
XLF rewards more risk with more return — consistent with financials being a cyclical sector
vs healthcare's defensive nature.

Running both simultaneously provides genuine diversification: XLF's 2022 loss (rate/credit
shock) and XLV's 2021 loss (healthcare legislation) occurred in different years and were
driven by completely different mechanisms.

---

## VIX Filter Comparison

| VIX filter | N | Win% | Mean ROC% |
|---|---|---|---|
| **None (selected)** | **206** | **86.4%** | **+11.82%** |
| VIX < 30 | 190 | 85.8% | +11.42% |
| VIX < 25 | 171 | 87.1% | +13.20% |
| VIX < 20 | 127 | 85.8% | +13.48% |

VIX<25 and VIX<20 modestly improve per-trade ROC but reduce trade count materially.
All VIX delivers the best annualized return. No filter recommended.

---

## Forward Vol Factor

Overall avg fwd_vol_factor: **1.077** (mild contango, similar to XLV at 1.085).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          206    0.0%  86.4%  +11.82%   +803.2%      1.077
  <= 1.30              169   18.0%  85.8%  +11.67%   +805.6%      0.947
  <= 1.20              155   24.8%  86.5%  +13.06%   +839.7%      0.921
  <= 1.10              131   36.4%  88.5%  +15.90%   +912.5%      0.878
  <= 1.00              104   49.5%  86.5%   +8.45%   +772.2%      0.833
  <= 0.90               61   70.4%  80.3%   +0.46%   +582.3%      0.750
  <= 0.80               28   86.4%  75.0%   -6.94%   +461.6%      0.637
```

**≤1.10 is the sweet spot:** +15.90% avg ROC (+35% improvement), 88.5% win rate, skipping
36% of entries. Unlike most tickers where tighter filters monotonically improve results,
XLF shows a clear peak at ≤1.10 — going tighter than 1.00 actually hurts, likely because
the very lowest-contango environments in XLF correspond to post-crisis calm periods where
puts are cheap (low credit) and any residual volatility still bleeds the position.

**If using the fwd_vol_factor filter:** Set threshold at ≤1.10. Skip entries where near-
term vol is substantially below forward vol (factor > 1.10), as this signals the market
anticipates a vol event that could push XLF lower through the short strike.

---

## Risks and Known Limitations

1. **Systemic financial risk** — Bank runs, credit crises, and rapid rate tightening cycles
   are XLF's primary threat. These events can be non-linear (SVB failed in ~48 hours) and
   are not predictable from VIX or fwd_vol_factor. Position sizing is the primary control.

2. **Lower trade frequency** — ~26 qualifying entries/year means the strategy has less
   statistical averaging than XLV. A bad cluster of 3–4 trades in a stress event has an
   outsized impact on annual P&L.

3. **Higher delta = wider swings** — Selling at 0.35Δ (vs XLV's 0.25Δ) means the position
   is closer to the money and more sensitive to adverse moves. The 0.05Δ wing is narrow
   ($1-wide spread on a $50 stock), so max loss per contract is contained, but the
   probability of max loss is higher than XLV.

4. **Narrow $1 wing** — Same as XLV: one max-loss trade = −100% ROC on that entry.
   Commissions must be well under $0.27/contract total round trip to preserve edge.

5. **Rate sensitivity** — XLF benefits from gradual rate increases (wider bank margins)
   but is hurt by rapid hikes (credit risk) and rate cuts (margin compression). The
   2019 and 2024 rate-cut environments were both profitable but modestly so.

---

## Code

```bash
# Put spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker XLF --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker XLF --spread 0.25 --detail-short-delta 0.35 --detail-wing 0.05 --no-csv

# Bear call spread sweep (for reference — rejected):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker XLF --spread 0.25 --no-csv
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/ticker_config.py` — XLF parameter configuration
- `data/studies/xlf_put_spread_playbook.md` — this file
- `data/studies/xlv_strategy_playbook.md` — XLV equivalent for comparison

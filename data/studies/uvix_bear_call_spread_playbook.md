# UVIX Bear Call Spread — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bear call spread on UVIX (ProShares Ultra VIX Short-Term Futures ETF) every Friday,
regardless of VIX level. UVIX is a 2x leveraged long-VIX product that decays structurally
toward zero via VIX futures contango — the same mechanism that makes UVXY (1.5x) a reliable
short-call target, but with higher leverage and therefore higher IV and more premium per delta.

The strategy is structurally identical to the UVXY bear call spread: sell a call above the
current price, buy a further OTM call as protection, collect premium from the structural
decay. UVIX's 2x leverage amplifies both the decay tailwind (good for calls) and the spike
risk (bad for calls during VIX events).

Like UVXY, **no VIX filter is needed**. Filtering by VIX level makes no meaningful
difference to per-trade outcomes — UVIX calls are profitable across all regimes tested.

Bull put spreads were tested and **rejected**: win rates of 33–65%, mostly negative P&L.
UVIX is a structurally decaying product and selling puts against it fights the trend
directly. The ROC numbers for put spreads appear artificially inflated in some combos due
to near-zero credit denominators (a numerical artifact when buying worthless long puts).

---

## Entry Rules

### Every Friday, ~20 DTE:

| Condition | Action |
|---|---|
| **Any VIX level** | Sell bear call spread (short 0.50Δ call / long 0.40Δ call) |

No VIX filter — enter every eligible Friday.

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target
- Both legs must be in the same expiry
- **Minimum dollar credit:** Skip if net credit < $0.10/contract (see Liquidity section)

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — spread has defined risk by construction; position sizing controls max dollar loss

92% of trades exit early (profit take fires), average holding period ~10 days.

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.50Δ |
| Long call delta | ~0.40Δ (wing = 0.10Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~21% |
| Study start date | 2022-04-14 (UVIX launch date) |

---

## Capital Allocation

**Approximate spread economics (UVIX ~$40–70 at current levels, post-splits):**

| Item | Approximate value |
|---|---|
| Short call strike (0.50Δ) | ~ATM to slightly OTM |
| Long call strike (~0.40Δ) | ~1 strike above short |
| Spread width | $1.00–$5.00 (depends on chain spacing) |
| Credit collected (~21% of width) | ~21¢ per $1 width / ~$1.05 per $5 width |
| Max loss per contract | ~79¢ per $1 width / ~$3.95 per $5 width |
| 50% profit target | Exit when spread worth ~50% of credit |

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- For a $1-wide spread (max loss $0.79/share = $79/contract): ~63 contracts
- For a $5-wide spread (max loss $3.95/share = $395/contract): ~12 contracts
- Max concurrent positions: 2 (overlapping 20-DTE trades entered weekly)

---

## Liquidity Warning

UVIX trades at a **low price** relative to its option chain, creating real execution risk:

**The core problem:** When UVIX trades at $5–15 (as it did through most of 2023–2024 between
reverse splits), a 0.10Δ wing call spread may have only $0.50–$1.00 of spread width, yielding
$0.10–$0.21/share in credit. After commissions ($0.65/contract typical), the net becomes
marginal or negative.

**Current state (post-2025 split, ~$40–70):** Spreads are wide enough to collect reasonable
dollar credits. The liquidity problem is most acute near or after a reverse-split event
when the price is freshest from a new low.

**Live trading rules:**
1. Always apply the 25% bid-ask filter on the short leg
2. Check the dollar credit: if net credit < $0.10/share ($10/contract), skip the entry
3. Use limit orders — UVIX options can have wide markets; never pay the ask on the long leg
4. Consider 5-wide spreads if 1-wide is too illiquid to fill efficiently
5. Monitor open interest on the strike you intend to trade; prefer strikes with OI > 100

**Reverse split risk:** UVIX has had two reverse splits since launch. Any open position
spanning a split date becomes unmanageable (strikes rescale). The study flags and excludes
these — replicate this in live trading by closing positions before announced split effective
dates.

---

## Backtested Performance (2022–2025)

| Metric | Value |
|---|---|
| Total closed trades | 139 |
| Win rate | **92.8%** |
| Mean ROC per trade | **+11.00%** |
| Sum ROC (all years) | +1,529% |
| Early exits (profit take) | 92% of trades |
| Avg holding period | ~10 days |
| Losing years | **0 of 4** |

### Per-year results (short=0.50Δ, wing=0.10Δ, All VIX):

| Year | N | Win% | Mean ROC% | Notes |
|---|---|---|---|---|
| 2022 | 20 | 85.0% | +4.86% | Partial year (Apr–Dec); UVIX launch; high-vol regime |
| 2023 | 38 | 94.7% | +12.46% | VIX normalization; decay tailwind strong |
| 2024 | 38 | 97.4% | +15.94% | Best year; very low vol environment |
| 2025 | 42 | 90.5% | +8.00% | Includes April Liberation Day tariff VIX spike |

Zero losing years across all four periods. The 2025 April spike (VIX ~60, UVIX briefly
$90–120) was the hardest test in the data — the strategy still closed the year at +8%
mean ROC, though individual spread losses during the spike window were significant.

---

## Split History

Two reverse splits within the study window; any backtest position spanning these dates
is excluded from performance statistics:

| Date | Ratio | Pre-split price | Post-split price |
|---|---|---|---|
| 2023-10-11 | ~1:4 | ~$10 | ~$40 |
| 2025-01-15 | ~1:4 | ~$8 | ~$33 |

The April 2025 price surge to $90–120 was **not a split** — it was the Liberation Day
tariff-driven VIX spike (VIX hit ~60) and subsequently reversed.

---

## VIX Filter Comparison

| VIX filter | N trades | Win% | Mean ROC% |
|---|---|---|---|
| **None (selected)** | **139** | **92.8%** | **+11.00%** |
| VIX < 30 | 134 | 92.5% | +10.81% |
| VIX < 25 | 125 | 93.6% | +11.69% |
| VIX < 20 | 93 | 93.5% | +11.78% |

Filtering slightly improves per-trade ROC but reduces trade count and annualized returns.
The difference is modest and not worth the complexity. Enter every Friday.

---

## Forward Vol Factor

Overall avg fwd_vol_factor: **1.421** — UVIX sits in steep contango (forward vol priced
above near-term vol), consistent with its structural decay profile.

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%   AvgFactor
  -----------------------------------------------------------------------
  (no filter)          139    0.0%  92.8%  +11.00%   +943.7%      1.421
  <= 1.30               47   66.2%  93.6%   +9.97%   +951.8%      1.083
  <= 1.20               36   74.1%  91.7%   +8.12%   +932.1%      1.033
  <= 1.10               21   84.9%  95.2%  +10.21%   +999.4%      0.945
  <= 1.00               15   89.2%  93.3%   +7.97%   +855.6%      0.893
  <= 0.90                9   93.5%  88.9%   +1.34%   +521.4%      0.839
  <= 0.80                3   97.8%  66.7%  -28.29%   -357.5%      0.754
```

**No filter is optimal.** Unlike XLV (where the factor filter monotonically improved
results), UVIX shows that tighter filters actually hurt — skipping 66%+ of entries (factor
≤1.30) leaves only unusual low-contango days where the decay premium is thinner. The
structural contango (avg 1.421) is the edge itself; filtering it away is
counterproductive.

**Decision: no fwd_vol_factor filter.**

---

## Comparison to UVXY

| | UVIX | UVXY |
|---|---|---|
| Leverage | 2x | 1.5x |
| Strategy | Bear call spread only | Bear call spread + short put |
| Best call combo | 0.50Δ / 0.10Δ, All VIX | 0.50Δ / 0.10Δ, All VIX |
| Mean ROC/trade (calls) | +11.00% | ~+5.06% |
| Win rate (calls) | 92.8% | ~92% |
| Study history | 3.75 years (Apr 2022–) | 8 years (Jan 2018–) |
| Reverse splits | 2 (2023, 2025) | 5 (2018–2025) |
| Short put side | Rejected | VIX < 20 only, +5.60% combined |
| Max tested VIX spike | ~60 (Apr 2025) | ~82 (Mar 2020) |
| Low-price liquidity risk | **Yes — monitor closely** | Minimal (price > $20 post-splits) |

**Key differences:**
- UVIX's 2x leverage yields meaningfully higher per-trade ROC on the call side (+11% vs +5%)
- UVXY's 8-year history includes the 2020 COVID spike (VIX 82) and 2018 Volmageddon —
  UVIX has not been tested through a comparable event
- UVXY supports a profitable short put side (VIX<20 filter); UVIX puts are not viable
- UVIX's low price creates execution friction that UVXY does not have at current levels

**Portfolio use:** Running both UVIX and UVXY call spreads simultaneously would be highly
correlated — they respond to the same VIX dynamics. Treat them as alternatives, not
diversifiers. UVIX offers higher per-trade ROC at the cost of shorter history and liquidity
risk. If forced to choose one for a live portfolio, UVXY's 8-year track record (including
the 2020 and 2018 stress tests) is more trustworthy. UVIX is a viable complement if you
want additional notional exposure to the same structural decay trade.

---

## Risks and Known Limitations

1. **Short history (3.75 years)** — The study window does not include a major VIX event
   comparable to COVID-19 (March 2020, VIX 82) or Volmageddon (February 2018, VIX 50+).
   The April 2025 spike (~60) is the hardest test in the dataset. UVIX at 2x leverage would
   have experienced much larger drawdowns in 2020 than UVXY did, potentially wiping out
   multiple spread positions simultaneously.

2. **Liquidity / low price** — See Liquidity Warning section above. The most critical risk
   for live trading. Between reverse splits, UVIX can trade at $3–10, making option premiums
   too small to trade efficiently after commissions.

3. **Reverse split execution risk** — With two splits in four years (~every 2 years), expect
   another split within 2–3 years at current decay rates. Any open position must be closed
   before the split effective date. Monitor ProShares announcements.

4. **2x leverage amplifies spikes** — A 10% VIX spike moves UVXY ~15%; the same event moves
   UVIX ~20%. Short call spreads lose proportionally more in a VIX spike than UVXY spreads
   at the same delta. The defined-risk structure caps absolute loss, but the max-loss
   threshold is hit more easily.

5. **Correlation with UVXY** — Running UVIX calls alongside UVXY calls does not diversify
   risk. Both positions lose in a VIX spike, potentially doubling drawdown during the
   worst weeks.

---

## Code

```bash
# Bear call spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker UVIX --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker UVIX --spread 0.25 --detail-short-delta 0.50 --detail-wing 0.10 --no-csv

# Bull put spread sweep (for reference — rejected):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker UVIX --spread 0.25 --no-csv
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — UVIX parameter configuration
- `src/lib/studies/straddle_study.py` — `UVIX_SPLIT_DATES` constant
- `data/studies/uvix_bear_call_spread_playbook.md` — this file
- `data/studies/uvxy_bear_call_spread.md` — UVXY equivalent for comparison

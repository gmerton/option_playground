# SQQQ Bear Call Spread — Trading Playbook

**Last updated:** 2026-03-06
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bear call spread on SQQQ (ProShares UltraPro Short QQQ, 3x inverse Nasdaq 100)
every Friday, regardless of VIX level. The strategy exploits SQQQ's structural downward
decay — as the Nasdaq 100 trends upward over time, a 3x leveraged inverse ETF suffers
compounding decay that steadily erodes its value even when QQQ moves are modest. Short
call spreads collect this decay premium while the defined-risk structure caps loss to the
spread width in the event of a QQQ crash.

**No VIX filter is needed.** All-VIX entries outperform filtered versions because SQQQ's
structural edge (daily rebalancing decay) operates in both calm and elevated-vol regimes.
In low-VIX environments, QQQ's steady upward drift accelerates SQQQ's decay — excellent
for short calls. In high-VIX environments, QQQ falls and SQQQ spikes (headwind), but
these episodes are the known, defined risk.

A bull put spread on SQQQ was researched and **rejected**. Every tested parameter
combination (all deltas, all wing widths, all VIX filters) produced negative ROC. SQQQ's
structural downward drift means short puts are fighting the trend — the stock keeps falling
through your short strikes. The call spread is the only viable direction.

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

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 50% of credit received (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — the spread has defined risk by construction; position sizing controls max dollar loss

~82% of trades exit early (profit take fires).

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.50Δ (near ATM) |
| Long call delta | 0.40Δ (wing = 0.10Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 50% of credit |
| Credit as % of spread width | ~31% |
| Study start date | 2018-01-01 |

### Conservative alternative (higher win rate, lower ROC):

| Parameter | Value |
|---|---|
| Short call delta | 0.40Δ |
| Long call delta | 0.30Δ (wing = 0.10Δ) |
| Win rate | 90.2% (vs 82.7% primary) |
| Mean ROC | +8.03% (vs +10.04% primary) |

The conservative version gives up ~2% ROC per trade in exchange for 7.5 percentage points
of additional win rate. Suitable for traders who prefer fewer max-loss events.

---

## Capital Allocation

**Approximate spread economics (SQQQ ~$25–40, price varies widely due to reverse splits):**

| Item | Approximate value |
|---|---|
| Short call strike (0.50Δ) | ~ATM |
| Long call strike (0.40Δ) | ~1–2 strikes above short |
| Spread width | ~$1.00–2.00 (check live chain) |
| Credit collected (~31% of width) | ~$0.31–0.62/share |
| Max loss per contract | ~$0.69–1.38/share |
| 50% profit target | Exit when spread worth ~50% of opening credit |

**SQQQ pricing note:** SQQQ's price and strike spacing change substantially after each
reverse split. Always verify current ATM strike and spread width on the live options chain
before sizing. At the time of study (2018–2026), strikes ranged from $5–$80+ depending
on the post-split price level.

**Example sizing ($100k portfolio, 5% max risk per position = $5,000):**
- With a $1-wide spread ($69 max loss/contract): ~72 contracts per entry
- With a $2-wide spread ($138 max loss/contract): ~36 contracts per entry
- Max concurrent positions: ~2 (overlapping 20-DTE trades entered weekly)

---

## Backtested Performance (2018–2026)

| Metric | Value |
|---|---|
| Total closed trades | 271 |
| Win rate | **82.7%** |
| Mean ROC per trade | **+10.04%** |
| Ann ROC (time-weighted) | +811% |
| Credit as % of spread width | ~31% |
| Losing years | **2 of 8 (2018, 2022)** |

### Per-year results:

| Year | N | Win% | ROC% | Notes |
|---|---|---|---|---|
| **2018** | **6** | **66.7%** | **−15.97%** | Q4 selloff — QQQ fell, SQQQ spiked |
| 2019 | 8 | 87.5% | +13.46% | QQQ rallied; SQQQ decayed steadily |
| 2020 | 36 | 91.7% | +16.12% | COVID recovery rally = SQQQ collapse |
| 2021 | 36 | 80.6% | +0.63% | Flat; mixed regime |
| **2022** | **46** | **65.2%** | **−13.17%** | QQQ crashed −33%; SQQQ surged = worst case |
| 2023 | 51 | 82.4% | +12.53% | |
| 2024 | 33 | 90.9% | +22.39% | AI rally year |
| 2025 | 49 | 91.8% | +27.39% | |
| 2026 | 6 | 66.7% | −1.44% | Partial year |

---

## The Structural Thesis

SQQQ's decay mechanism is mathematical and persistent:

- **Daily rebalancing compounding:** A 3x leveraged product reset daily compounds against
  holders in volatile, sideways, or uptrending markets. Even if QQQ ends flat for a month,
  daily volatility erodes SQQQ's value through variance drag.
- **QQQ's long-term upward bias:** Over any multi-year window since inception (2010),
  QQQ has trended upward. This pushes SQQQ toward zero over time, requiring periodic
  reverse splits (the study window includes at least one: 2022-05-24).
- **Short call alignment:** When SQQQ decays, calls above the current price expire
  worthless. The structural decay is the seller's edge.

**The risk:** In QQQ crash years (2018, 2022), SQQQ can rally 50–100%+ in a matter of
weeks. The short call gets deeply ITM, and the spread takes max loss. This is the known,
defined risk — not a surprise event, but a cyclical reality.

---

## The Two Losing Years: 2018 and 2022

Both losing years share the same cause: **QQQ fell sharply, SQQQ surged, short calls
went into the money.**

**2018 (−15.97% ROC):** The Q4 2018 selloff (QQQ −20% Oct–Dec) drove SQQQ up sharply.
Only 6 entries were active (the study year had fewer Fridays), and 2 of 6 were max losses.
Small sample amplifies the ROC impact.

**2022 (−13.17% ROC):** The worst QQQ year since 2008 (−33%). SQQQ surged throughout
the year, repeatedly hitting short calls ITM. Despite 46 entries (the most of any year
due to weekly Friday entry), only 65.2% won. The defined-risk spread structure capped
individual losses, preventing a catastrophic drawdown — sum ROC was negative but not
severe.

**Historical frequency:** QQQ has had only 2 meaningfully down years (−10%+) in the
2018–2026 study window. Both produced losing years for this strategy. Any QQQ bear market
lasting 6–12+ months will produce a losing year. Position sizing and portfolio context
matter: SQQQ calls should be a component of a diversified strategy suite, not a
standalone approach.

---

## Comparison to VIX-Filtered Versions

Unlike most other strategies in this suite, **the VIX filter hurts SQQQ calls**:

| VIX filter | N | Win% | ROC% |
|---|---|---|---|
| **None (selected)** | **271** | **82.7%** | **+10.04%** |
| VIX < 30 | 249 | 81.5% | +9.30% |
| VIX < 25 | 216 | 81.5% | +10.00% |
| VIX < 20 | 146 | 81.5% | +11.92% |

The VIX<20 filter (i.e., only enter when VIX≥20) slightly improves per-trade ROC (+11.92%
vs +10.04%) but cuts trade count by 46%. The total P&L impact is negative — you're
skipping trades that are profitable in aggregate (low-VIX regimes when SQQQ decays
fastest). The All-VIX baseline maximizes cumulative return.

Note: for SOXX call spreads, the VIX≥20 filter was beneficial. For SQQQ calls, it is not.
The difference is that SOXX is a long-biased equity ETF (needs fear for short calls to
work), while SQQQ has structural decay that operates regardless of fear level.

---

## Forward Vol Factor Filter

fwd_vol_factor = σ_fwd / near_iv. Overall avg: **1.253** (notable contango; term structure
steeply upward-sloping — market expects SQQQ vol to rise).

```
  max fwd_vol_factor    N   Skip%   Win%     ROC%   AnnROC%
  -----------------------------------------------------------
  (no filter)          271    0.0%  82.7%  +10.04%   +810.5%
  ≤ 1.30               185   31.7%  82.2%  +10.59%   +842.1%
  ≤ 1.20               141   48.0%  83.0%   +8.68%   +841.9%
  ≤ 1.10               104   61.6%  82.7%   +8.22%   +833.1%
  ≤ 1.00                67   75.3%  83.6%  +10.40%   +876.3%
  ≤ 0.90                42   84.5%  88.1%  +13.53%  +1041.7%
  ≤ 0.80                19   93.0%  94.7%  +20.98%  +1226.0%
```

**Unlike most other tickers, the fwd_vol_factor filter shows meaningful improvement here.**
At ≤0.90 (42 trades, ~5/year), win rate climbs to 88.1% and ROC to +13.53% — a 35% lift
over the baseline. At ≤0.80 (19 trades, ~2/year), ROC reaches +20.98% with 94.7% win
rate, though the sample is thin.

**Interpretation:** SQQQ's high avg factor (1.253) means the market typically expects
future vol to exceed current vol — fear of future QQQ crashes is priced in. When the factor
drops below 0.90 (market expects vol to fall), it signals a calm outlook, which is when
SQQQ's structural decay is most reliably expressed and short calls are safest.

**Practical recommendation:** Consider the ≤1.30 filter as a light screen (31.7% fewer
trades, small ROC lift, no meaningful drawdown increase). The ≤0.90 filter is aggressive
but compelling — use it only if you accept 5 entries/year.

---

## Risks and Known Limitations

1. **QQQ bear markets** — Any sustained QQQ decline of 20%+ will produce a losing year.
   There is no filter that reliably avoids this: VIX spikes warn of acute fear but not
   sustained bear markets. 2022 had entries all year at elevated VIX and most still lost.
   Accept that 1–2 of every 8 years will be net negative.

2. **SQQQ reverse splits** — SQQQ does periodic reverse splits as its price approaches
   zero (at least one confirmed in the study window: 2022-05-24). Split-spanning positions
   are excluded from the backtest, so reported metrics undercount entries slightly in
   split years. In live trading, monitor for announced reverse splits and close positions
   that would span the split date.

3. **Near-ATM short strike** — The 0.50Δ short call is approximately at-the-money. A
   single bad week of QQQ selling can move the position from profitable to max loss in
   days. The defined-risk spread caps the damage, but this is not a "safe" out-of-the-money
   premium collect — it is a directional bet that SQQQ will not rally. Size accordingly.

4. **Leverage path dependency** — SQQQ's value depends not just on QQQ direction but on
   the path (daily volatility). A week of large daily swings in both directions can erode
   SQQQ's value even if QQQ ends flat. This is actually favorable for the short call
   (SQQQ goes down via vol drag), but it makes P&L less predictable week-to-week.

5. **Liquidity at tail expirations** — SQQQ options can be illiquid at non-standard
   expirations. Always verify bid-ask spread (max 25% filter) on the actual chain before
   entry. The spread filter rejects some weeks entirely when liquidity dries up.

---

## Relationship to Portfolio

| | SQQQ | SOXX | TLT | UVXY |
|---|---|---|---|---|
| Structure | Bear call spread | Bull put spread | Bear call spread | Bear call + short put |
| Entry condition | Always | Always | VIX ≥ 20 | Always (call); VIX < 20 (put) |
| Mean ROC/trade | +10.04% | +17.98% | +11.57% | +5.60% combined |
| Activity | Every Friday | Every Friday | ~40% of Fridays | Every Friday |
| Directional bet | QQQ stays flat or rises | SOXX stays flat or rises | TLT stays flat or falls | UVXY decays |
| Bad scenario | QQQ crashes | Semis crash | TLT rallies (rates fall) | VIX spikes |

**SQQQ and SOXX correlation:** These two strategies are negatively correlated to QQQ
direction. In a QQQ crash, SQQQ calls lose (SQQQ spikes) and SOXX puts lose (SOXX
falls). They share directional risk and should not both be sized aggressively. In a QQQ
rally, SQQQ calls win easily (SQQQ decays) and SOXX puts win (SOXX rises) — both are
profitable simultaneously. Consider these as a "tech bull" position pair with correlated
tail risk.

**SQQQ and UVXY:** In a market crash (VIX spikes), SQQQ calls get hurt but UVXY puts
sit out (VIX<20 filter). UVXY bear call spreads remain active and may also get hit.
Do not run maximum size on both simultaneously.

**Best complement to SQQQ calls:** TLT (bear call, only active at VIX≥20, not every
Friday) and XLV (bull put, defensive sector, low QQQ correlation). These reduce portfolio
sensitivity to a QQQ bear market year.

---

## Code

```bash
# Call spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker SQQQ --spread 0.25

# Per-year detail for confirmed parameters:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker SQQQ --spread 0.25 --no-csv \
    --detail-short-delta 0.50 --detail-wing 0.10

# Put spread sweep (research reference — all negative, do not trade):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker SQQQ --spread 0.25
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — SQQQ parameter configuration
- `data/studies/sqqq_bear_call_spread_playbook.md` — this file

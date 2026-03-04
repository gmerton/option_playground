# TLT Bear Call Spread — Trading Playbook

**Last updated:** 2026-03-03
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell a bear call spread on TLT (iShares 20+ Year Treasury Bond ETF) when the VIX is
elevated (≥ 20). The strategy exploits the structural tendency for TLT to sell off or
trade flat during periods of market fear, when rising rate expectations or risk-off
rotation into cash (rather than bonds) keeps TLT under pressure. The VIX≥20 entry
filter is the core edge: it restricts entries to regimes where TLT is more likely to
be stationary or declining, and avoids the low-VIX, falling-rate environment (e.g.
2019) where TLT rallied sharply and short calls lose.

A short put leg was researched and **rejected**. TLT puts earn negligible ROC (+0.04%
mean per trade in VIX<20 environments), and in the VIX 20–25 joint window the put
earns less than the call spread, creating a capital-allocation drag. The put contributed
−221.7% cumulative SumROC over the study period (only helping materially in 2022).

---

## Entry Rules

### Every Friday when VIX ≥ 20, ~20 DTE:

| Condition | Action |
|---|---|
| **VIX ≥ 20** | Sell bear call spread (short 0.35Δ call / long 0.30Δ call) |
| **VIX < 20** | No trade — sit out entirely |

**Entry filters:**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target
- Both legs must be in the same expiry

---

## Exit Rules

- **Profit take:** Close when spread value ≤ 30% of credit received (i.e., keep 70% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — the spread has defined risk by construction; position sizing controls max dollar loss

---

## Parameters

| Parameter | Value |
|---|---|
| Short call delta | 0.35Δ |
| Long call delta | 0.30Δ (wing = 0.05Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX entry floor | ≥ 20 (skip entirely when VIX < 20) |
| Max spread (bid-ask/mid) | 25% on short leg |
| Profit take | 70% of credit |
| Credit as % of spread width | ~30% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**Approximate spread economics (TLT ~$90):**

| Item | Approximate value |
|---|---|
| Short call strike (0.35Δ) | ~$94–96 |
| Long call strike (0.30Δ) | ~$96–98 |
| Spread width | ~$2.00 |
| Credit collected (30% of width) | ~$0.60 per share = $60/contract |
| Max loss per contract | ~$1.40 per share = $140/contract |
| 70% profit target (keep $0.42/share) | Exit at ~$0.18 debit |

**Utilisation note:** The VIX≥20 filter means the strategy is active roughly **40% of
Fridays** (140 of ~350 available entry dates over the study period). Capital is idle
60% of the time and should be deployed elsewhere (e.g. UVXY combined strategy).

**Example sizing ($100k portfolio, 5% max risk allocation = $5,000):**
- Max loss budget: $5,000
- Contracts: $5,000 / $140 ≈ 35 contracts per entry
- Max concurrent positions: 2 (overlapping 20-DTE trades entered weekly)
- Peak capital at risk: ~$10,000 (two simultaneous positions)

---

## Backtested Performance (2018–2026)

| Metric | Value |
|---|---|
| Total trades (140 over 8 years) | 140 |
| Win rate | 81.4% |
| Mean ROC per trade | **+11.57%** |
| Mean annualized ROC | +723% |
| Sharpe (per-trade) | 0.237 |
| Capital utilisation | ~40% of Fridays |
| Worst year | 2023: −7.94% mean ROC (9 trades) |
| Best year | 2024: +36.29% mean ROC (6 trades) |

### Per-year results:

| Year | N | Win% | Mean ROC% | Sum ROC% | VIX context |
|---|---|---|---|---|---|
| 2018 | 9 | 88.9% | +14.63% | +131.7% | Rate hike cycle |
| 2019 | 1 | 100% | +30.99% | +31.0% | Fed pivot; VIX rarely ≥ 20 — nearly sat out all year |
| 2020 | 40 | 82.5% | +15.45% | +617.9% | COVID spike; VIX ≥ 20 most of the year |
| 2021 | 18 | 88.9% | +17.69% | +318.4% | Taper uncertainty |
| 2022 | 44 | 75.0% | +2.90% | +127.7% | Aggressive hikes, TLT −31%; high-VIX entries rescued by spread structure |
| **2023** | **9** | **66.7%** | **−7.94%** | **−71.5%** | **TLT bounced in high-VIX windows; only losing year** |
| 2024 | 6 | 100% | +36.29% | +217.7% | VIX rarely elevated; few but excellent entries |
| 2025 | 13 | 84.6% | +18.97% | +246.5% | Rate-cut cycle |

### Regime breakdown:

| Regime | Weeks | Mean ROC% |
|---|---|---|
| VIX ≥ 25 (most fear, call spread only) | 63 | **+16.74%** |
| VIX 20–25 (moderate fear) | 77 | +7.34% |
| VIX < 20 (calm — sit out) | ~267 | — |

The highest-alpha regime is VIX ≥ 25 — extreme fear periods when TLT is most likely
selling off as capital flees to cash rather than bonds, or rates are rising sharply.

---

## Comparison to Baseline (All VIX, 50% profit take)

| Metric | Baseline | **Selected (VB)** |
|---|---|---|
| Entry filter | All VIX | VIX ≥ 20 only |
| Profit take | 50% | 70% |
| N trades | 348 | 140 |
| Mean ROC/trade | +5.07% | **+11.57%** |
| Sharpe | 0.099 | **0.237** |
| 2019 ROC | −11.89% (44 trades) | **+30.99% (1 trade)** |
| Total SumROC | +1,763% | +1,620% |

The baseline generates marginally more total return (+143%) assuming idle capital earns
nothing. For idle capital to make Version B break even, it would need to earn ~0.67% per
unused Friday (~35% annualised) — an unrealistic bar. In the context of a broader
portfolio where idle capital is deployed elsewhere, Version B's superior risk-adjusted
return and near-elimination of 2019-style blowups make it the right choice.

---

## Risks and Known Limitations

1. **2023: the one losing year** — TLT bounced in the specific high-VIX windows the
   strategy targeted, producing −7.94% mean ROC on 9 trades. This is a small-sample
   year (9 trades) and may not repeat, but it is real and represents the core risk:
   TLT can rally even when VIX is elevated (flight-to-safety bid).

2. **Rate-cutting cycle risk** — When the Fed pivots aggressively to cuts and VIX
   is elevated due to growth fears (not rate fears), TLT can rally sharply while VIX
   stays elevated. 2019 is the canonical example, but the VIX≥20 filter reduced this
   to a single trade that year.

3. **Thin entries in calm years** — In low-volatility years (2019: 1 trade, 2024: 6
   trades), statistics are thin. The strategy is nearly inactive; ensure capital is
   deployed elsewhere.

4. **Short wing (0.05Δ) = tight protection** — The long call at 0.30Δ is only ~$2
   above the short call. A rapid large TLT spike (e.g. 5%+ in a few days) will push
   both legs deep ITM and realise near-maximum loss. Position sizing is the only
   defence; the spread structure limits but doesn't eliminate loss.

5. **No stop-loss tested** — Stop-loss research was not conducted for TLT (only for
   UVXY). Given the defined-risk nature of the spread, position sizing controls
   catastrophic loss.

---

## Relationship to UVXY Strategy

| | TLT | UVXY |
|---|---|---|
| Core structure | Bear call spread only | Bear call spread + short put |
| Entry condition | VIX ≥ 20 | Always (call spread); VIX < 20 (put) |
| Mean ROC/trade | +11.57% | +5.60% (combined) |
| Activity | ~40% of Fridays | ~100% of Fridays |
| Correlation to UVXY | Low — different underlying dynamics | — |

The two strategies are complementary in a portfolio: UVXY runs nearly every week while
TLT waits for elevated VIX. When VIX is elevated, UVXY's put leg sits out but the TLT
call spread activates — creating a natural regime handoff.

---

## Research Notes

- **Put leg research:** Short put (0.30Δ, VIX<25) was fully backtested and rejected.
  Net contribution to portfolio: −221.7% cumulative SumROC. Only year it added value:
  2022 (+135.7%). Every other year it was a drag. See analysis session 2026-03-03.

- **Optimizer (Optuna, 200 trials):** Ran walk-forward (train ≤ 2022, val ≥ 2023).
  Best trial found `call_vix_min=20`, `profit_take=0.70`, but with a degenerate
  `short_delta=0.20/wing=0.20` configuration (long call at ~0.00Δ). The VIX≥20 and
  70% profit take findings were validated and adopted; the degenerate wing was
  discarded in favour of the hand-studied 0.35Δ/0.05Δ structure.

- **Baseline comparison:** Total SumROC (Baseline +1,763% vs Version B +1,620%) shows
  the baseline earns marginally more total return. Version B is preferred for
  risk-adjusted return (Sharpe 0.237 vs 0.099) and portfolio context (idle capital
  deployed to UVXY and other strategies).

---

## Code

```bash
# Put sweep (study reference — not live trading):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_puts.py \
    --ticker TLT --spread 0.25

# Call spread sweep (study reference):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker TLT --spread 0.25

# Optimizer:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_optimizer.py \
    --ticker TLT --trials 200
```

**Key source files:**
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — TLT parameter configuration
- `src/lib/studies/optimizer.py` — Optuna walk-forward optimizer

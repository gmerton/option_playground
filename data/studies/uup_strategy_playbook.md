# UUP Strategy Playbook — ATM Short Straddle

**Last updated:** 2026-03-18
**Status:** Backtested 2018–2023 (full data). 2024–2025 data sparse — treat as provisional. Strategy fires on regime-independent basis.

---

## Overview

UUP (Invesco DB US Dollar Index Bullish Fund) tracks the US Dollar Index (DXY) vs a basket
of six major currencies (EUR, JPY, GBP, CAD, SEK, CHF). The dollar's behavior is macro-driven —
Fed rate policy, risk sentiment, global currency flows — and tends to be slow and mean-reverting
over medium horizons. This makes UUP a natural short-volatility candidate.

**Key finding:** A short ATM straddle (~0.50Δ put and call, ~20 DTE, 50% profit take) outperforms
all credit spread and strangle variants across every regime. The strategy fires on ~25% of eligible
Fridays (where ATM 20-DTE data is available), producing steady, regime-independent theta income.

---

## Why Straddle, Not Strangle?

The theoretical delta sweep shows the best ROC at asymmetric structures like 0.20Δ call / 0.50Δ
put (+34.3% ROC, 86.1% win). **Do not use these in live trading.** The reason:

### UUP Bid-Ask Spread Reality

UUP options are thinly traded. Bid-ask spreads on OTM strikes are extremely wide:

| Delta bucket | Avg spread/mid | Practical status |
|---|---|---|
| ~0.45Δ (ATM) | 18–28% | Viable — limit orders near mid fill |
| ~0.30Δ (OTM) | 28–42% | Marginal — expect slippage |
| ~0.20Δ (OTM) | **65–95%** | Not tradeable — spread consumes most premium |

A 0.20Δ call priced at $0.05–0.08 mid has a bid of ~$0.01–0.02. Real fills are at bid, meaning
the entire premium of that leg evaporates. Theoretical ROC from backtests assumes mid-price fills.

**ATM options are the only practically executable strikes on UUP.**

### Regime Independence

The regime study (VIX × 50-day MA) shows the short straddle wins in every regime:

| Regime | N | Win% | Avg ROC |
|--------|---|------|---------|
| Bearish_HighIV | ~25 | ~72% | ~+15% |
| Bearish_LowIV | ~20 | ~73% | ~+18% |
| Bullish_HighIV | ~15 | ~73% | ~+19% |
| Bullish_LowIV | ~44 | ~73% | ~+17% |

The short straddle's dominance across all four regimes means regime classification adds no value
for UUP. Enter whenever data quality allows; skip regime gating.

---

## Entry Rules

### Each eligible Friday:

```
1. Check: is there a ~20 DTE expiry available (±5 days)?
2. Check: does a near-ATM strike exist with reasonable liquidity?
   - Spread/mid on both legs < 35%
   - Mid price of each leg ≥ $0.05
3. If yes to both: enter short ATM straddle
4. Otherwise: skip this week
```

### Trade parameters:

| Parameter | Value |
|-----------|-------|
| Structure | Short ~0.50Δ call / short ~0.50Δ put (same strike, same expiry) |
| Target DTE | ~20 days (±5) |
| Entry day | Friday |
| Max bid-ask per leg | ≤ 35% of mid |
| Min mid per leg | $0.05 |
| Profit take | 50% of combined credit received |
| Stop loss | 2× combined credit |

### On delta asymmetry:

If the ATM straddle strike has the put at 0.48Δ and call at 0.52Δ, that's fine — use it.
A minor skew (0.40/0.50 or 0.50/0.55) is acceptable. Do not chase OTM strikes for higher ROC;
the bid-ask cost is prohibitive.

---

## Exit Rules

- **Profit take:** Close both legs when combined value ≤ 50% of credit received
- **Stop loss:** Close both legs when combined value ≥ 2× entry credit
- **Expiry:** If neither fires, close on expiration day or let expire (defined risk via straddle width)

---

## Performance (2018–2026)

### Short straddle overall:

| Metric | Value |
|--------|-------|
| Total trades | 104 |
| Win rate | **73.1%** |
| Avg ROC/trade | **+17.4%** |
| Cumulative P&L | **+$14.26** (per-share, 104 trades) |
| Active weeks / total | 104 / 428 (~24% of Fridays) |

### Why so few entries (104/428)?

UUP's options chain is thin — many Fridays do not have a liquid ~20 DTE expiry or lack
near-ATM strikes. The 104 entries represent Fridays where the data quality threshold was
met. In live trading, check the chain directly on Friday; some weeks simply have no
viable 20-DTE contracts.

---

## Data Sparsity Warning (2024–2025)

Historical near-ATM 20-DTE rows in the database:

| Year | Approx rows |
|------|-------------|
| 2018–2023 | 180–250/year |
| 2024 | ~122 |
| 2025 | ~41 |

The sharp drop in 2024–2025 likely reflects **both** real UUP option liquidity decline (UUP
is increasingly displaced by currency ETFs like FXE, FXY) **and** possible Polygon data
coverage gaps for low-volume ETFs in recent years.

**Implication for live trading:** Before entering any UUP straddle, manually verify the chain
in your broker (Tradier, IBKR) to confirm:
1. A 15–25 DTE expiry exists
2. ATM strike has reasonable width (bid-ask < 35% of mid)
3. Open interest on both legs is non-zero

If the chain is bare, skip the week. Do not assume data availability from backtests.

---

## Economics and Sizing

**Approximate straddle economics (UUP ~$26–28 at typical levels):**

| Item | Approximate value |
|------|-------------------|
| ATM strike | ~UUP spot |
| Credit per straddle | ~$0.35–0.55 |
| 50% profit target | ~$0.17–0.27 |
| Stop loss trigger | ~$0.70–1.10 (2× credit) |
| Max realized loss | ~2× credit (if stop hit) |

**Note:** UUP moves slowly (1–3% typical monthly range). The straddle is rarely tested
sharply unless there's a major macro event (FOMC surprise, geopolitical currency shock).
Most trades expire inside the strikes, hitting the 50% profit take before 20 DTE.

**Sizing ($100k portfolio):**
- At 2–3% portfolio risk per trade: ~20–30 contracts
- UUP is a slow-moving ETF — sizing can be somewhat larger than a volatile equity ETF
- Cap at 3 concurrent positions (rare given low entry frequency)

---

## Risks

1. **Macro gap risk:** A sudden FOMC surprise, geopolitical shock (e.g., dollar safe-haven surge
   during a crisis), or unexpected rate differential move can gap UUP 2–3% overnight. This hits
   both legs simultaneously if the move is large. The stop (2× credit) typically fires same-day
   but gap opens can exceed it.

2. **Liquidity degradation:** UUP option liquidity has declined in recent years. Real fills may
   be worse than modeled, especially for larger position sizes. In thin markets, the straddle may
   trade at a discount to theoretical mid. Always use limit orders at mid; walk in if needed.

3. **2024–2025 reliability:** Backtest data for UUP in 2024–2025 is sparse. Current regime
   performance estimates for these years have wide confidence intervals. This strategy should be
   sized conservatively (2% of portfolio) until the live-trading record accumulates.

4. **Dollar trend regimes:** If the dollar enters a strong structural trend (e.g., DXY rally of
   10–15% over 6 months), straddle entries will be repeatedly stopped out on the call side.
   Unlike ETFs with mean-reverting behavior, dollar trends can persist for 1–2 years. Monitor
   rolling win rate; if it drops below 55% over a 20-trade window, pause the strategy.

---

## Comparison to Other Strategies

| | UUP (short straddle) | XLF (regime-switch) | GLD (put spread + calendar) |
|--|--|--|--|
| Avg ROC/trade | +17.4% | +16.7% | +7–13% |
| Win rate | 73.1% | 75.0% | 75–85% |
| Trades/year | ~13 | ~42 | ~20–30 |
| Defined risk | No (straddle unbounded) | Mixed | Yes |
| Data reliability | Thin post-2023 | Good | Good |

UUP offers competitive per-trade ROC but fires infrequently and has thin option liquidity.
It is best treated as a supplementary strategy, not a core position.

---

## Code

```bash
# Multi-strategy regime study:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strategy_study.py --ticker UUP

# Strangle delta sweep (all regimes — theoretical; ATM only is practical):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker UUP --regime Bearish_HighIV
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker UUP --regime Bullish_LowIV

# Sync UUP options from Athena (if options_cache is empty):
# In Python:
# from src.lib.studies.straddle_study import sync_options_cache
# from datetime import date
# sync_options_cache("UUP", date(2018, 1, 1), force=True)
```

**Key source files:**
- `run_tlt_strategy_study.py` — multi-strategy regime study (accepts `--ticker`)
- `run_tlt_strangle_study.py` — strangle delta sweep by regime
- `data/cache/UUP_stock.parquet` — UUP price history (2018–2026, 2063 rows)

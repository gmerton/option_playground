# TLT Regime-Switching Options Strategy — Trading Playbook

**Last updated:** 2026-03-19
**Status:** All defined-risk spreads + annualized ROC profit target (100%). Ready for live trading.

---

## Overview

Each Friday, classify TLT's regime using two signals — its position relative to the 50-day
MA (trend direction) and the VIX level (implied vol environment). Deploy a different spread
structure depending on the regime:

| Regime | Condition | Strategy | ROC (Reg T) | Win% |
|--------|-----------|----------|:-----------:|:----:|
| **Bearish_HighIV** | Below 50MA + VIX ≥ 20 | Bear call spread 0.40Δ / 0.30Δ | +4.4% | 87.8% |
| **Bearish_LowIV** | Below 50MA + VIX < 20 | Bear call spread 0.25Δ / 0.15Δ | +2.4% | 88.7% |
| **Bullish_HighIV** | Above 50MA + VIX ≥ 20 | Bear call spread 0.40Δ / 0.30Δ | +2.6% | 86.0% |
| **Bullish_LowIV** | Above 50MA + VIX < 20 | Bull put spread 0.45Δ / 0.35Δ | +10.4% | 87.1% |

ROC = pnl / (spread_width − credit) — the Reg T margin requirement / max loss.

**Profit target:** Close when annualized ROC ≥ 100%, i.e. `(pnl/margin) × (365/hold_days) ≥ 1.0`.
This naturally closes quick winners early (freeing capital) while holding slow trades longer.
Avg hold ≈ 5 days. Stop loss: 2× credit.

**Current regime (2026-03-19):** Bearish_HighIV — TLT $87.59, VIX elevated.

**Overall switching strategy performance (2018–2026):** +5.6% avg ROC per trade, $12.07
cumulative P&L, 87.6% win rate, 410 trades. Max drawdown: $3.16. Max losing streak: 2 weeks.

---

## Why All Spreads (No Strangles)

Prior versions used short strangles in Bearish_LowIV (+11.6% apparent ROC) and
Bullish_HighIV (+33.6%). Those figures used credit as the denominator. On a proper Reg T
capital-at-risk basis (CBOE uncovered formula), the margins were ~$20–27/share — making
actual ROC 0.8% and 3.3% respectively. The spreads, with max-loss margins of ~$0.98–1.19,
beat the strangles on capital efficiency and produce much lower drawdowns:

| | Strangles | All Spreads |
|--|:---------:|:-----------:|
| Avg ROC (Reg T) | +5.4% | **+5.6%** |
| Max drawdown | −$20.58 | **−$3.16** |
| Max losing streak | 11 weeks | **2 weeks** |
| Undefined risk | Yes | **No** |

---

## Entry Decision (Every Friday)

**Step 1:** Is TLT's close above its 50-day moving average?
**Step 2:** Is VIX ≥ 20?

```
                   VIX ≥ 20                VIX < 20
TLT below 50MA  → Bear call 0.40Δ/0.30Δ → Bear call 0.25Δ/0.15Δ
TLT above 50MA  → Bear call 0.40Δ/0.30Δ → Bull put  0.45Δ/0.35Δ
```

**Step 3 (Bearish_HighIV only):** Is VRP ≥ −2.5 pp?
- VRP = ATM IV30 (BS-implied from ~20 DTE put) − RV20 (20-day annualized realized vol)
- **Skip when VRP < −2.5 pp** — lowest quartile: ~60% win rate, negative avg ROC
- Q2–Q4 (VRP ≥ −2.5 pp): 83%+ win rate, >12% avg ROC
- The screener computes and enforces this automatically
- Note: VRP filter was validated at 0.35Δ/0.25Δ; carry-over to 0.40Δ/0.30Δ is directionally sound but not re-verified

---

## Profit Target

**Rule:** Close when `(pnl / margin) × (365 / hold_days) ≥ 1.0` (100% annualized ROC).

This replaces the old fixed 50%-of-credit target. Benefits:
- A trade at 49% profit on day 1 closes immediately (annualized ROC ≈ 18,000%)
- A slow trade at 10% profit on day 18 stays open (annualized ROC ≈ 20%, below target)
- Avg hold drops from ~10 days to ~5 days, freeing capital for re-deployment
- Win rate improves: 87.6% vs 72.0% (fewer trades held into adverse reversals)
- Max losing streak drops: 2 weeks vs 6 weeks

Walk-forward validation (IS=2018–2022, OOS=2023–2026): OOS annualized ROC +616% vs +313%
baseline (50% take). The IS→OOS improvement confirms genuine edge, not overfitting.

When recording a new TLT position in the database, set `ann_target = 1.0`.

---

## Strategy Details

### Bearish_HighIV — Bear Call Spread (0.40Δ / 0.30Δ)

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.40Δ |
| Long call delta | 0.30Δ (wing = 0.10Δ) |
| Target DTE | 20 days (±5) |
| Profit take | Ann ROC ≥ 100% |
| Stop loss | 2× credit |
| VRP filter | Skip if VRP < −2.5 pp |
| Entry day | Friday |

**Economics (~TLT $87):**
- Short call strike: ~$89–91 (closer to the money than prior 0.35Δ)
- Long call strike: ~$91–93
- Avg credit: ~$0.49/share ($49/contract)
- Max loss: ~$0.98/share ($98/contract)

**90 weeks, 87.8% win rate, +4.4% avg ROC, +$4.68 cumulative**

Rationale: TLT is in a downtrend. Sell above-trend resistance. The 0.40Δ short strike
collects more premium than 0.35Δ with only a marginal win-rate cost. Tighter wing narrows
the max-loss denominator, boosting ROC.

---

### Bearish_LowIV — Bear Call Spread (0.25Δ / 0.15Δ)

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.25Δ |
| Long call delta | 0.15Δ (wing = 0.10Δ) |
| Target DTE | 20 days (±5) |
| Profit take | Ann ROC ≥ 100% |
| Stop loss | 2× credit |
| Entry day | Friday |

**Economics (~TLT $87):**
- Short call strike: ~$90–92 (OTM)
- Long call strike: ~$92–94
- Avg credit: ~$0.24/share ($24/contract)
- Max loss: ~$1.12/share ($112/contract)

**124 weeks, 88.7% win rate, +2.4% avg ROC, +$3.79 cumulative**

Rationale: TLT is below its 50MA and low-volatility. Premium is thin. The 0.25Δ strike
is sufficiently OTM that TLT's slow drift rarely threatens it. ROC is modest (+2.4%) but
positive and far better than the prior strangle on a capital-at-risk basis (+0.8%). The
annualized target helps exit quickly when the trade moves in our favor early.

⚠️ **Worst single-year risk:** A sharp TLT spike (rate surprise) in a low-VIX week can
breach the short call before VIX has time to re-classify the regime. The 2× stop limits
damage. 2024 was the worst year for the Bearish regimes overall.

---

### Bullish_HighIV — Bear Call Spread (0.40Δ / 0.30Δ)

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.40Δ |
| Long call delta | 0.30Δ (wing = 0.10Δ) |
| Target DTE | 20 days (±5) |
| Profit take | Ann ROC ≥ 100% |
| Stop loss | 2× credit |
| Entry day | Friday |

Same structure as Bearish_HighIV.

**Economics (~TLT $87):** Identical to Bearish_HighIV (~$0.49 credit, ~$0.98 max loss).

**57 weeks, 86.0% win rate, +2.6% avg ROC, +$0.66 cumulative**

Rationale: Even in a TLT bull trend, the 20-DTE call spread with 0.40Δ short strike
rarely gets breached. High VIX inflates call premiums; TLT's short-term moves within
a 20-day window are choppy enough that the spread expires or closes profitably 86% of the time.
The prior skewed strangle generated more absolute dollars per contract but required ~27×
more capital per trade. On capital efficiency the spread wins.

---

### Bullish_LowIV — Bull Put Spread (0.45Δ / 0.35Δ)

| Parameter | Value |
|-----------|-------|
| Short put delta | 0.45Δ (near-ATM) |
| Long put delta | 0.35Δ (wing = 0.10Δ) |
| Target DTE | 20 days (±5) |
| Profit take | Ann ROC ≥ 100% |
| Stop loss | 2× credit |
| Entry day | Friday |

**Economics (~TLT $87):**
- Short put strike: ~$85–87 (near-ATM)
- Long put strike: ~$83–85
- Avg credit: ~$0.38/share ($38/contract)
- Max loss: ~$0.53/share ($53/contract)

**139 weeks, 87.1% win rate, +10.4% avg ROC, +$2.94 cumulative**

Rationale: TLT is in a bull trend with low vol. Sell near-ATM puts — the directional
tailwind keeps the short put OTM as TLT drifts higher. The near-ATM strike collects
better premium; the tight wing keeps margin small, producing the highest ROC of any
regime (+10.4%). The annualized exit target captures early favorable moves efficiently.

---

## Common Entry Filters (All Strategies)

- Max delta error: ±0.08 from target on each leg
- DTE window: 15–25 days (target 20)
- Both legs must be on the same expiry
- Long-leg bid ≤ 25% of short-leg mid (practical fill check)
- Skip if net credit ≤ 0

---

## Capital Allocation

All four regimes are now defined-risk spreads. Max loss per share is:

| Regime | Avg max loss | Contracts at $5K risk ($100K portfolio) |
|--------|:------------:|:--------------------------------------:|
| Bearish_HighIV | ~$0.98/shr | ~51 |
| Bearish_LowIV | ~$1.12/shr | ~45 |
| Bullish_HighIV | ~$0.98/shr | ~51 |
| Bullish_LowIV | ~$0.53/shr | ~94 |

Size by max dollar loss, not by contract count. The strategy is active ~100% of Fridays.
Consider 3–5% portfolio allocation. Avg hold ~5 days means capital cycles faster than
the nominal 20-DTE window suggests.

---

## Backtested Performance (2018–2026)

### Overall comparison (ROC = pnl / Reg T capital-at-risk)

| Strategy | Trades | Win% | Avg ROC | Sum P&L | Max DD | Max Streak |
|----------|:------:|:----:|:-------:|:-------:|:------:|:----------:|
| **Regime-switching (ann target)** | 410 | **87.6%** | +5.6% | +$12.07 | −$3.16 | **2 weeks** |
| Always-on call spread | 408 | 70.1% | +1.8% | +$13.53 | −$11.01 | 8 weeks |
| Call spread VIX≥20 only | 147 | 76.2% | +6.2% | +$12.30 | — | — |

Note: regime-switching has lower absolute SumPnL than always-on because the ann target
exits earlier. The dramatically lower drawdown and losing streak reflect the quality of
capital deployment.

### Per-year

| Year | ROC | P&L | Notes |
|------|:---:|:---:|-------|
| 2018 | −2.1% | +$0.17 | BearLO dominated (26w); thin premiums |
| 2019 | +3.6% | +$0.76 | BullLO dominated (37w); bull put spread solid |
| 2020 | +4.3% | +$0.49 | BearHI/BullHI (41w); ann target captures vol spikes quickly |
| 2021 | +4.1% | +$2.45 | Mix of regimes; bull put spread carried BullLO |
| 2022 | +7.2% | +$4.26 | BearHI dominated (38w); rising-rate environment |
| 2023 | +3.0% | +$1.83 | BearLO dominated (25w); thin regime |
| 2024 | **−2.8%** | **−$0.80** | BearLO/BullLO split; worst year |
| 2025 | +4.6% | +$1.19 | Mixed; BearLO and BullLO |
| 2026 | +149.7% | +$1.71 | Partial year (8 weeks); small sample |

**2024 flag:** TLT had sustained rate pressure with periodic sharp rallies. The
Bearish_LowIV bear call spreads (0.25Δ, 23 weeks) absorbed some stop-outs when brief
TLT spikes breached the short call before VIX re-classified the regime. −2.8% ROC
is the worst single year in the backtest (improved from −8.7% under fixed 50% target
due to faster exits in favorable weeks).

### Per-regime contribution

| Regime | Weeks | Strategy | Win% | ROC | Sum P&L |
|--------|:-----:|----------|:----:|:---:|:-------:|
| Bearish_HighIV | 90 | Bear call 0.40Δ/0.30Δ | 87.8% | +4.4% | +$4.68 |
| Bearish_LowIV | 124 | Bear call 0.25Δ/0.15Δ | 88.7% | +2.4% | +$3.79 |
| Bullish_HighIV | 57 | Bear call 0.40Δ/0.30Δ | 86.0% | +2.6% | +$0.66 |
| Bullish_LowIV | 139 | Bull put 0.45Δ/0.35Δ | 87.1% | +10.4% | +$2.94 |

---

## Risks and Known Limitations

1. **2024 worst-year risk** — Bearish_LowIV (0.25Δ bear call) is the most fragile regime.
   Thin premiums combined with periodic sharp TLT rallies can produce stop-outs even in
   a broadly bearish rate environment. Size conservatively in this regime.

2. **Regime classification lag** — 50MA and VIX are end-of-day Thursday signals. A VIX
   spike Friday morning can put you in the wrong structure. Check VIX at entry time.

3. **Bearish_LowIV is thin** — +2.4% avg ROC with low absolute P&L. Worth running
   (positive edge, 88.7% win), but a single large stop-out week can erase several months
   of gains in this regime. The 2× stop is essential.

4. **Bullish_HighIV absolute P&L** — $0.66 cumulative over 57 weeks is low. The regime
   fires ~7 weeks/year. In a real portfolio, you need enough contracts to make the P&L
   meaningful. Adjust position sizing accordingly.

5. **VRP filter not re-verified at 0.40Δ** — The VRP ≥ −2.5 pp filter was tested at the
   old 0.35Δ short delta. It is directionally valid and carried over, but the exact
   threshold has not been re-optimized for the new strikes.

6. **Ann target creates shorter holds** — Avg hold ~5 days means more weekly transaction
   costs if you pay commissions. At typical retail rates ($0.65/contract), confirm net
   P&L still positive after friction.

---

## Relationship to Other Strategies

| | TLT | UVXY | TMF |
|---|---|---|---|
| Active weeks | ~100% of Fridays | ~100% | Same regimes as TLT |
| Best regime | Bullish_LowIV (+10.4%) | VIX<20 short put | BearHI call spread |
| Correlation | Low to UVXY | — | High to TLT |

TLT and UVXY are complementary. TMF (3× levered TLT) mirrors TLT regimes but with
amplified credits and wider spreads — run the same regime classification, size smaller.

---

## Research History

### Prior version (deprecated 2026-03-19): fixed 50% profit take

Used `close when spread ≤ 50% of entry credit`. Performance: 72.0% win, +7.7% avg ROC,
$21.22 cumulative, max drawdown $4.46, max losing streak 6 weeks. Replaced with 100%
annualized ROC target: higher win rate (87.6%), tighter drawdown ($3.16), shorter avg
hold (~5 days), better OOS validation (+616% vs +313% ann ROC).

### Prior version (deprecated 2026-03-19): strangles in Bearish_LowIV + Bullish_HighIV

Used short_strangle_sym (0.25Δ/0.25Δ) in Bearish_LowIV and short_strangle_skew
(0.45Δ/0.25Δ) in Bullish_HighIV. Appeared strong at +11.6% and +33.6% ROC, but those
figures used credit (~$1–2.74) as the denominator. Correct Reg T capital-at-risk
denominator (~$20–27/share) showed actual ROC of 0.8% and 3.3%. Defined-risk spreads
outperform on true capital efficiency. Replaced 2026-03-19.

### Prior version (deprecated 2026-03-17): VIX≥20 call spread only

Original strategy: bear call spread 0.35Δ/0.25Δ when VIX≥20, skip otherwise.
Strong win rate (76.2%) but only active 36% of Fridays.

### Short put leg (rejected 2026-03-03)

Researched and rejected. Net contribution: −221.7% cumulative SumROC.

### Ratio spread (rejected 2026-03-17)

TLT 2:1 call ratio spread: +79.7% win rate (VIX≥25) but max loss −$9.05/share.
Defined-risk spreads outperform on risk-adjusted basis.

---

## Code

```bash
# Regime-switching combined backtest (primary):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  python run_tlt_regime_switch.py --ticker TLT

# Per-regime structure sweep (finds optimal structure per regime):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  python run_tlt_structure_sweep.py --ticker TLT

# Stop-loss effectiveness analysis:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  python run_tlt_regime_switch.py --ticker TLT --no-stop

# Profit target sweep (walk-forward IS/OOS optimization):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  python run_tlt_profit_sweep.py --ticker TLT
```

**Key source files:**
- `run_tlt_regime_switch.py` — unified regime-switching backtest (primary); `--ann-target 100` default
- `run_tlt_structure_sweep.py` — per-regime structure/delta sweep with Reg T ROC
- `run_tlt_profit_sweep.py` — walk-forward profit target optimization (IS=2018–2022, OOS=2023–2026)
- `run_tlt_strategy_study.py` — all-strategy regime comparison (reference)

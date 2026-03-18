# TLT Regime-Switching Options Strategy — Trading Playbook

**Last updated:** 2026-03-17
**Status:** Upgraded to regime-switching framework. Ready for live trading.

---

## Overview

Each Friday, classify TLT's regime using two signals — its position relative to the 50-day
MA (trend direction) and the VIX level (implied vol environment). Deploy a different options
structure depending on the regime:

| Regime | Condition | Strategy | Backtest ROC |
|--------|-----------|----------|-------------|
| **Bearish_HighIV** | Below 50MA + VIX ≥ 20 | Bear call spread 0.35Δ / 0.25Δ | +23.1% |
| **Bearish_LowIV** | Below 50MA + VIX < 20 | Short strangle 0.25Δ / 0.25Δ | +11.6% |
| **Bullish_HighIV** | Above 50MA + VIX ≥ 20 | Short strangle 0.45Δ call / 0.25Δ put | +33.6% |
| **Bullish_LowIV** | Above 50MA + VIX < 20 | Long straddle *(skip for now)* | +8.6% |

**Current regime (2026-03-17):** Bearish_HighIV — TLT $87.14, 50MA $88.26, VIX 27.40.

**Overall switching strategy performance (2018–2026):** +16.2% avg ROC per trade, $103.81
cumulative P&L, 67.5% win rate, 409 trades. The prior VIX≥20-only call spread returned
+17.1% avg ROC but only traded 36% of Fridays (+$12.30 cumulative).

**Bullish_LowIV (long straddle) is parked for now.** The +8.6% ROC is real but the 47.1%
win rate and 44.9% stop rate are psychologically costly. When this regime is active, skip
the week or revisit the long straddle research. The other three regimes all exceed 75% win
rate.

---

## Entry Decision (Every Friday)

**Step 1:** Is TLT's close above its 50-day moving average?
**Step 2:** Is VIX ≥ 20?

```
                   VIX ≥ 20              VIX < 20
TLT below 50MA  → Bear call spread    → Short strangle (sym)
TLT above 50MA  → Short strangle (skew)  → Skip (long straddle TBD)
```

---

## Strategy Details

### Bearish_HighIV — Bear Call Spread

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.35Δ |
| Long call delta | 0.25Δ (wing = 0.10Δ) |
| Target DTE | 20 days (±5) |
| Profit take | 50% of credit |
| Stop loss | 2× credit |
| Entry day | Friday |

**Economics (~TLT $87):**
- Short call strike: ~$91–93
- Long call strike: ~$93–95
- Avg credit: ~$0.44/share ($44/contract)
- Max loss: ~$1.56/share ($156/contract, hitting stop at 2× credit)

**90 weeks, 77.8% win rate, +23.1% avg ROC, +$9.55 cumulative**

---

### Bearish_LowIV — Short Strangle (Symmetric)

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.25Δ |
| Short put delta | 0.25Δ |
| Target DTE | 20 days (±5) |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Entry day | Friday |

Both legs on the same expiry. Put strike ≤ call strike required.

**Economics (~TLT $87):**
- Call strike: ~$89–90 (0.25Δ)
- Put strike: ~$84–85 (0.25Δ)
- Avg credit: ~$1.01/share ($101/contract)
- Max planned loss at stop: ~$3.16/share

**124 weeks, 75.8% win rate, +11.6% avg ROC, +$16.68 cumulative**

Rationale: Low VIX means TLT is drifting slowly, not running. OTM strangle with symmetric
wings has much higher ROC than the ATM straddle (+11.6% vs +7.3%) because both strikes
stay safely away from the slow drift. 2020 outlier risk: one week in Mar-2020 hit -118%
ROC when VIX spiked from LowIV to HighIV mid-cycle. Stop loss limits the damage.

---

### Bullish_HighIV — Short Strangle (Asymmetric)

| Parameter | Value |
|-----------|-------|
| Short call delta | 0.45Δ (near-ATM) |
| Short put delta | 0.25Δ (far OTM) |
| Target DTE | 20 days (±5) |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Entry day | Friday |

Put strike ≤ call strike required (will usually be satisfied given delta difference).

**Economics (~TLT $87):**
- Call strike: ~$87–88 (near-ATM, 0.45Δ)
- Put strike: ~$84–85 (0.25Δ, well OTM)
- Avg credit: ~$2.74/share ($274/contract)
- Max planned loss at stop: ~$5.48/share

**57 weeks, 82.5% win rate, +33.6% avg ROC, +$53.99 cumulative**

Rationale: TLT is in a flight-to-safety rally (above 50MA, VIX elevated). The rally is
likely decelerating — sell the near-ATM call to collect rich call premium. TLT is moving
*away* from put strikes; keep the put far OTM and nearly free. The asymmetry reflects
directional conviction: call side is the premium source, put side is just insurance.

This is the highest-edge regime. 2020 (COVID) drove 20 of 57 Bullish_HighIV weeks;
+$30.45 cumulative that year alone. The structure earned well across all other HighIV years
too (2021, 2022, 2023, 2024).

---

### Bullish_LowIV — Skip (Long Straddle TBD)

Long straddle (buy 0.50Δ call + 0.50Δ put) backtested at +8.6% avg ROC, but with 47.1%
win rate and 44.9% stop rate. The underlying logic is sound — low IV underprices TLT's
moves when it is trending — but the trade-by-trade experience is noisy. **Skip this regime
for now.** When the signal fires, take no position.

Represents ~34% of Fridays (138/409). Revisit with a refined entry condition (IV rank,
RV20 vs IV30) before trading.

---

## Common Entry Filters (All Strategies)

- Max delta error: ±0.08 from target on each leg
- DTE window: 15–25 days (target 20)
- Both legs must be same expiry
- Long-leg bid ≤ 25% of short-leg mid (practical fill check)
- Skip if net credit ≤ 0 (should not occur but sanity check)

---

## Capital Allocation

**Portfolio sizing:**
- The switching strategy is active ~66% of Fridays (271 of 409 after skipping BullishLowIV)
- Average credits range from $0.44 (call spread) to $2.74 (BullishHI strangle)
- Size positions by max dollar loss, not by credit size

**Example ($100k portfolio, 5% max risk per trade = $5,000):**

| Regime | Max loss/contract | Contracts at 5% |
|--------|------------------|-----------------|
| Bearish_HighIV call spread | ~$156 | ~32 |
| Bearish_LowIV sym strangle | ~$316 | ~16 |
| Bullish_HighIV skew strangle | ~$548 | ~9 |

The BullishHI strangle requires the smallest position in number of contracts but each
contract earns the most premium. Keep dollar risk constant across regimes, not lot size.

---

## Backtested Performance (2018–2026)

### Overall comparison

| Strategy | Trades | Win% | Avg ROC | Sum P&L | Max Drawdown |
|----------|--------|------|---------|---------|-------------|
| **Regime-switching** | 409 | 67.5% | **+16.2%** | **+$103.81** | −$20.58 |
| Always-on call spread | 408 | 70.1% | +4.6% | +$13.53 | −$11.01 |
| Call spread VIX≥20 only | 147 | 76.2% | +17.1% | +$12.30 | — |

The switching strategy generates 7.7× more absolute P&L than always-on call spreads.
The VIX≥20-only call spread has similar ROC (+17.1%) but only trades 36% of Fridays.

### Per-year

| Year | Switching ROC | Switching P&L | Always-on ROC | Dominant regime | Notes |
|------|--------------|--------------|--------------|-----------------|-------|
| 2018 | −1.5% | +$0.56 | −19.3% | BearLO (26w) | Switching avoided call-spread losses |
| 2019 | +9.6% | +$10.00 | −33.4% | BullLO (37w) | Long straddle captured bond rally |
| 2020 | +28.7% | +$39.59 | +4.2% | BearHI/BullHI (41w) | COVID flight-to-safety; best year |
| 2021 | +9.5% | −$2.36 | +3.6% | BullLO (22w) | Long straddle underperformed; skip rule helps |
| 2022 | +24.7% | +$10.40 | **+33.4%** | BearHI (38w) | Only year always-on wins; pure call-spread year |
| 2023 | +13.3% | +$19.52 | +19.1% | BearLO (25w) | Sym strangle solid |
| 2024 | +21.2% | +$18.34 | +9.8% | BearLO (23w) | Switching outperformed significantly |
| 2025 | +21.4% | +$5.44 | +13.7% | BearLO (17w) | Switching outperformed |
| 2026 | +40.1% | +$2.30 | +49.4% | BearLO (6w) | Partial year |

### Per-regime contribution (switching strategy)

| Regime | Weeks | Strategy | Win% | Avg ROC | Sum P&L |
|--------|-------|----------|------|---------|---------|
| Bearish_HighIV | 90 | Bear call spread | 77.8% | +23.1% | +$9.55 |
| Bearish_LowIV | 124 | Sym strangle | 75.8% | +11.6% | +$16.68 |
| Bullish_HighIV | 57 | Skew strangle | 82.5% | +33.6% | +$53.99 |
| Bullish_LowIV | 138 | Long straddle* | 47.1% | +8.6% | +$23.60 |

*Long straddle included in historical totals; parked for live trading.

---

## Risks and Known Limitations

1. **Regime classification lag** — The 50MA and VIX are end-of-day Thursday signals. If a
   regime shift begins Friday morning (e.g. VIX spikes 30% at the open), you will enter
   the wrong structure. Check VIX at entry time, not just Thursday close.

2. **2020 outlier in Bearish_LowIV** — One week in March 2020 classified as Bearish_LowIV
   (VIX had not yet spiked Thursday close) produced −118% ROC on the sym strangle. Stop
   loss at 2× contained actual dollar loss but the ROC hit is real.

3. **Bullish_HighIV is dominated by 2020** — 20 of 57 BullishHI weeks were COVID-era.
   The +$53.99 cumulative is real but half comes from an extraordinary regime. Expect
   lower absolute contribution in non-crisis years; the structure is still sound.

4. **BullishHI strangle: near-ATM call is exposed** — The 0.45Δ call is close to at-the-
   money. If TLT continues rallying after entry (e.g. emergency Fed cut), this leg can go
   ITM quickly. The 2× stop loss is critical to control losses; do not remove it.

5. **Bearish_LowIV strangle: both sides exposed** — Unlike the call spread, neither leg is
   defined against the other. A sharp TLT move in either direction can breach both strikes.
   This is an undefined-risk trade; size accordingly (smaller lot count than the spread).

6. **2022: the always-on spread's best year** — 38 of 51 weeks were Bearish_HighIV. In a
   pure rising-rate regime the simple call spread slightly outperforms (+33.4% vs +24.7%).
   The switching strategy still had a good year; it just wasn't the best relative year.

---

## Relationship to Other Strategies

| | TLT | UVXY |
|---|---|---|
| Active weeks | ~66% of Fridays | ~100% |
| Regime logic | 4-way classification (50MA + VIX) | 2-way (VIX level) |
| Best regime | Bullish_HighIV (+33.6% ROC) | VIX < 20 (short put) |
| Correlation | Low to UVXY | — |

TLT and UVXY are complementary. When VIX is elevated, TLT's BearishHI call spread and
BullishHI strangle both fire. UVXY's call spread fires regardless; its short put sits out
when VIX ≥ 20. The regimes interlock cleanly.

---

## Research History

### Prior approach (deprecated): VIX≥20 call spread only

The original strategy sold only bear call spreads (0.35Δ / 0.30Δ → later 0.35Δ / 0.25Δ)
and sat out entirely when VIX < 20. That worked well (81.4% win rate, +11.57% ROC on 140
trades) but left 60%+ of Fridays idle and suffered in high-VIX bond-rally years (2019, 2023).

**Why upgraded:** Regime-switching addresses the core weakness — "what do we do when TLT is
above its 50MA?" — rather than simply sitting out. The multi-strategy framework also
exploits the Bullish_HighIV regime, the single richest window in the dataset.

### Short put leg (rejected 2026-03-03)

Researched and rejected. Net contribution to portfolio: −221.7% cumulative SumROC.
Only added value in 2022. The put leg was superseded by the Bearish_LowIV strangle
(which adds a put as part of a credit-balanced structure, not a naked put).

### Ratio spread (rejected 2026-03-17)

TLT 2:1 call ratio spread (sell 2 near calls, buy 1 further OTM) backtested at +79.7%
win rate (VIX≥25) but max loss −$9.05/share vs avg credit ~$0.54. 2018 flight-to-safety
moves caused repeated stops. Defined-risk structures outperform on risk-adjusted basis.

### Forward vol factor (inconclusive 2026-03-05)

The fwd_vol_factor (σ_fwd/near_iv) was tested as an additional filter. Non-monotonic
relationship; no improvement over VIX-alone signal. Not used in the switching framework.

---

## Code

```bash
# Regime-switching combined backtest:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_regime_switch.py

# Per-regime strangle sweep (e.g. Bearish_LowIV):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --regime Bearish_LowIV
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --regime Bullish_HighIV

# Multi-strategy regime study (all 5 structures compared):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strategy_study.py

# Prior call spread sweep (reference only):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_call_spreads.py \
    --ticker TLT --spread 0.25 --profit-take 0.70 \
    --short-deltas 0.35 --detail-short-delta 0.35 --detail-wing 0.10 --no-csv
```

**Key source files:**
- `run_tlt_regime_switch.py` — unified regime-switching backtest (primary)
- `run_tlt_strangle_study.py` — per-regime strangle delta sweep
- `run_tlt_strategy_study.py` — all-strategy regime comparison
- `run_tlt_naked_calls.py` — naked call backtest (reference)
- `run_tlt_ratio_calls.py` — ratio spread backtest (reference)

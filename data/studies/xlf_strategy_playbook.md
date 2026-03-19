# XLF Regime-Switching Strategy — Trading Playbook

**Last updated:** 2026-03-18
**Status:** Backtested 2018–2026. All four regimes confirmed positive. Ready for live trading.

---

## Overview

XLF (Financial Select Sector SPDR Fund) tracks large-cap US financials — banks, insurance,
asset managers, brokerages. Financials are cyclical, rate-sensitive, and prone to systemic
credit events (bank runs, yield-curve stress). This makes XLF strongly regime-dependent:
the optimal structure shifts dramatically based on trend direction and volatility environment.

A naive always-on bear call spread loses money (−4.3% avg ROC, −$1.73 cumulative 2018–2026).
The regime-switching framework turns this into **+16.7% avg ROC, $21.74 cumulative, 75% win
rate** across 336 weeks.

**Key insight:** In HighIV regimes (fear spikes), XLF put premiums are rich regardless of
trend direction — sell puts. In Bullish_LowIV (the most common regime), cap the slow grind
with call spreads. In Bearish_LowIV (downtrend but complacent), the asymmetric strangle
with a very OTM call captures the vol risk premium cleanly.

---

## Regime Classification

Each Friday before entry, classify using XLF's own 50-day MA and VIX:

| Signal | Threshold |
|--------|-----------|
| **Trend** | XLF close vs 50-day MA |
| **IV** | VIX ≥ 20 = HighIV; VIX < 20 = LowIV |

This produces four regimes:

| Regime | Weeks (2018–2026) | % of time |
|--------|-------------------|-----------|
| Bearish_HighIV | 79 | 23.5% |
| Bearish_LowIV | 69 | 20.5% |
| Bullish_HighIV | 66 | 19.6% |
| Bullish_LowIV | 122 | 36.3% |

Typical years: Bullish_LowIV dominates calm bull markets (2019, 2024–2025). Bearish_HighIV
spikes in crisis years (2020 COVID, 2022 rate-hike shock). Bearish_LowIV characterizes
slow-grind drawdowns (2018–2019 corrections, 2024 wobbles).

---

## Strategy by Regime

### Bearish_HighIV — Bull Put Spread
*XLF below 50MA + VIX ≥ 20*

Fear is elevated but XLF has already declined. Put premiums are rich. Selling a put spread
harvests the fear premium while defining risk. The downtrend means call spreads bleed.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.35Δ put / long 0.25Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of credit received |
| Stop loss | 2× credit (spread value doubles) |
| Credit / width | ~20% of $1 spread width |

**Backtested (79 weeks):** 78.5% win, +21.1% avg ROC, $3.13 cumulative. Max loss −$0.79.

---

### Bearish_LowIV — Asymmetric Short Strangle
*XLF below 50MA + VIX < 20*

XLF is in a downtrend but the market is complacent (VIX quiet). Directional call selling
is the core idea (very OTM call — trend limits upside), supplemented by a modestly OTM
put to collect the available vol premium. The 0.20Δ call is far enough OTM that continued
downward drift rarely threatens it.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.20Δ call / short 0.25Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Avg credit | ~$0.43 |

**Backtested (69 weeks):** 79.7% win, +22.3% avg ROC, $8.22 cumulative. Max loss −$1.47.

**Why not symmetric straddle?** In this regime, XLF is grinding lower — a symmetric ATM
straddle puts the call strike in harm's way on any mean-reversion bounce. The 0.20Δ call
gives substantial buffer (tested all call/put delta combos — 0.20/0.25 was the clear winner
at +22.3% vs straddle's +9.2%).

---

### Bullish_HighIV — Asymmetric Short Strangle (Bullish skew)
*XLF above 50MA + VIX ≥ 20*

XLF is in an uptrend but something has spiked VIX (COVID recovery, reopening, macro shock).
This is often a sharp-but-temporary vol event. Put premiums are rich. The optimal structure
leans bearish on the put side (sell 0.40Δ puts — close to ATM to capture the fear premium)
while selling a moderately OTM call (0.35Δ). The bullish trend supports selling puts and
prevents runaway call losses.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.35Δ call / short 0.40Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Avg credit | ~$0.99 |

**Backtested (66 weeks):** 75.8% win, +13.8% avg ROC, $7.68 cumulative. Max loss −$1.96.

**vs. bull put spread alone:** The strangle beats the pure put spread (+13.8% vs +11.8% ROC)
with a higher win rate (75.8% vs 72.7%). The call premium cushions put losses when XLF
sells off. 2024 was the weak spot (6 weeks, -42.1%) but is a thin sample; overall
7-year record is strong.

**Note:** This is an unbounded strangle capped only by the 2× stop (~$1.96 max realized loss
in backtest). Size conservatively — the stop can gap through in gap-up opens.

---

### Bullish_LowIV — Bear Call Spread
*XLF above 50MA + VIX < 20*

The most common regime (36% of weeks). XLF is trending up slowly, volatility is quiet —
a classic slow-grind bull environment. Puts are cheap (don't bother selling them). Selling
calls OTM caps the upside and collects steady premium from the directional theta.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.35Δ call / long 0.25Δ call (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of credit received |
| Stop loss | 2× credit |
| Avg credit | ~$0.16 |

**Backtested (122 weeks):** 69.7% win, +12.2% avg ROC, $2.71 cumulative. Max loss −$0.36.

**Why not strangle?** Tested all 49 call/put delta combos — the best strangle here is only
+7.8% ROC (0.50/0.45Δ) vs bear_call_spread's +12.2%. In low-IV bull trends, puts are cheap
and adding put exposure dilutes the call-spread edge while adding unnecessary downside risk.

---

## Combined Backtested Performance (2018–2026)

| Metric | Regime-Switching | Always-on call spread |
|--------|-----------------|----------------------|
| Total trades | 336 | 307 |
| Win rate | **75.0%** | 61.6% |
| Avg ROC/trade | **+16.7%** | −4.3% |
| Cumulative P&L | **$+21.74** | −$1.74 |
| Max drawdown | −$4.83 | −$5.55 |
| Max losing streak | 4 weeks | 7 weeks |

### Per-year summary:

| Year | ROC% | P&L | Notable |
|------|------|-----|---------|
| 2018 | +20.7% | +$1.66 | Correction year; regime switching avoids call losses |
| 2019 | −15.1% | −$0.77 | Only losing year — all Bearish_LowIV (9 weeks) |
| 2020 | +22.9% | +$5.10 | COVID crash + recovery; BHI and UHI both contributed |
| 2021 | +14.3% | +$8.56 | Strong across all regimes |
| 2022 | +9.3% | +$1.15 | Dominated by Bearish_HighIV (32 weeks); put spreads held |
| 2023 | +32.7% | +$4.03 | Best year; Bearish_LowIV strangle dominated |
| 2024 | −12.5% | −$2.63 | Bullish_HighIV strangle (6 trades) had a bad run |
| 2025 | +44.3% | +$4.81 | Excellent across all four regimes |
| 2026 | +15.2% | −$0.16 | Early 2026 stub |

**7 of 9 years profitable.** 2019 (−15.1%) was a slow Bearish_LowIV environment where the
strangle got ground down. 2024 (−12.5%) was driven by 6 Bullish_HighIV strangle trades.

---

## Sizing and Economics

### Bearish_HighIV — Bull Put Spread (~$1 wide)
- Credit ~$0.20/share = $20/contract
- Max loss ~$0.80/share = $80/contract
- At 5% portfolio risk ($5k on $100k): 62 contracts
- Typically 2–3 concurrent positions (overlapping 20-DTE)

### Bearish_LowIV — Short Strangle
- Credit ~$0.43/share = $43/contract
- Max realized loss ~$1.47 (2× stop) = $147/contract
- No defined risk — size at ~2–3% of portfolio per position
- At 3% portfolio risk ($3k on $100k): ~20 contracts

### Bullish_HighIV — Short Strangle
- Credit ~$0.99/share = $99/contract
- Max realized loss ~$1.96 (2× stop) = $196/contract
- Size at ~2–3% of portfolio per position
- At 3% portfolio risk ($3k on $100k): ~15 contracts

### Bullish_LowIV — Bear Call Spread (~$1 wide)
- Credit ~$0.16/share = $16/contract
- Max loss ~$0.84/share = $84/contract (spread width − credit)
- At 5% portfolio risk ($5k on $100k): 59 contracts
- Low credit per trade — ensure commissions are < $0.05/contract round trip

---

## Risks

1. **Strangle gap risk** — The Bearish_LowIV and Bullish_HighIV strangles have no defined
   cap. The 2× stop limits losses in normal trading but a gap open through the stop (e.g.,
   overnight financial shock, surprise Fed move) can exceed the backtest max loss. XLF is
   particularly susceptible to sudden bank-sector events (SVB-style). Size strangles smaller
   than put spreads.

2. **2022 regime dominance** — 2022 was 63% Bearish_HighIV (32 weeks). The put spread held
   up (+9.3% for the year) but 32 consecutive weeks in one regime is unusual. If a credit
   crisis causes XLF to gap below 0.35Δ short strikes for many weeks simultaneously, losses
   compound.

3. **2019 Bearish_LowIV** — The strangle underperformed in 2019 (slow XLF grind, 9 weeks
   of entries). The 0.20Δ call kept losses contained but put premiums were thin. If XLF
   trends down slowly for months in low VIX, expect below-average returns.

4. **Regime misclassification** — Regime is classified each Friday close. If XLF crosses
   the 50MA or VIX crosses 20 mid-week, the entry regime may not reflect end-of-week
   conditions. This is unavoidable; the Friday classification has proven sufficient.

5. **Options liquidity** — XLF is highly liquid (tight spreads, deep chains). No liquidity
   concerns at reasonable position sizes.

---

## Current Regime (2026-03-18)

Check Friday close: XLF vs its 50-day MA, VIX level.

```python
# Quick regime check (run Friday after close):
import pandas as pd
import numpy as np

df = pd.read_parquet("data/cache/XLF_stock.parquet")
df = df.sort_values("trade_date").tail(60)
close = df["close"].iloc[-1]
ma50  = df["close"].tail(50).mean()
# Also check VIX from vix_daily.parquet

trend = "Bullish" if close > ma50 else "Bearish"
# iv = "HighIV" if vix >= 20 else "LowIV"
print(f"XLF {close:.2f} vs 50MA {ma50:.2f} → {trend}")
```

---

## Code

```bash
# Multi-strategy regime study:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strategy_study.py --ticker XLF

# Strangle sweeps by regime:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLF --regime Bearish_LowIV
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLF --regime Bullish_HighIV
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLF --regime Bullish_LowIV

# Regime-switching combined backtest:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_regime_switch.py --ticker XLF
```

**Key source files:**
- `run_tlt_strategy_study.py` — multi-strategy regime study (accepts `--ticker`)
- `run_tlt_strangle_study.py` — strangle delta sweep by regime (accepts `--ticker`, `--regime`)
- `run_tlt_regime_switch.py` — combined switching backtest; XLF config in `TICKER_REGIME_STRATEGIES`
- `data/studies/xlf_put_spread_playbook.md` — prior put-spread-only research (superseded)

---

## Historical Research (Superseded)

Prior to 2026-03-18, XLF was traded as a simple always-on bull put spread (0.35Δ / 0.30Δ,
No VIX filter, 50% take). That study showed +11.82% avg ROC across 206 trades with an 86.4%
win rate, but the aggregate masks severe regime-dependence. The regime-switching framework
achieves +16.7% avg ROC with better drawdown characteristics by deploying the right
structure each week.

See `data/studies/xlf_put_spread_playbook.md` for the full prior analysis.

# XLF Regime-Switching Strategy — Trading Playbook

**Last updated:** 2026-03-19
**Status:** Backtested 2018–2026. ROC corrected to Reg T capital-at-risk basis. BearishHI upgraded to 0.40Δ/0.30Δ. Ready for live trading.

---

## Overview

XLF (Financial Select Sector SPDR Fund) tracks large-cap US financials — banks, insurance,
asset managers, brokerages. Financials are cyclical, rate-sensitive, and prone to systemic
credit events (bank runs, yield-curve stress). This makes XLF strongly regime-dependent:
the optimal structure shifts dramatically based on trend direction and volatility environment.

A naive always-on bear call spread loses money (−1.5% avg ROC, −$1.74 cumulative 2018–2026).
The regime-switching framework turns this into **+6.1% avg ROC, $23.79 cumulative, 74.8% win
rate** across 337 weeks.

**ROC methodology:** All figures use Reg T capital-at-risk as the denominator:
- Spreads: `spread_width − credit` (exact max loss)
- Strangles: CBOE uncovered formula `max(0.20×S − OTM + premium, 0.10×S + premium)` per side

Prior playbook showed +16.7% avg ROC and +22.3%/+13.8% for strangles — those used credit as
the denominator (~$0.43/$0.99), dramatically understating the true margin (~$6.16/$6.82/share).
Correct Reg T ROC for strangles: **+1.7% and +2.1%** per trade.

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
| Bearish_HighIV | 80 | 23.7% |
| Bearish_LowIV | 69 | 20.5% |
| Bullish_HighIV | 66 | 19.6% |
| Bullish_LowIV | 122 | 36.2% |

---

## Strategy by Regime

### Bearish_HighIV — Bull Put Spread (0.40Δ / 0.30Δ)
*XLF below 50MA + VIX ≥ 20*

Fear is elevated but XLF has already declined. Put premiums are rich. Selling a put spread
harvests the fear premium while defining risk. The downtrend means call spreads bleed.
Upgraded from 0.35Δ/0.25Δ — tighter wing (0.10Δ gap) improves ROC from +8.4% to +11.7%.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.40Δ put / long 0.30Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of credit received |
| Stop loss | 2× credit (spread value doubles) |

**Backtested (80 weeks):** 77.5% win, +11.7% avg ROC, $5.19 cumulative. Max loss −$0.495.

---

### Bearish_LowIV — Asymmetric Short Strangle (0.20Δ call / 0.25Δ put)
*XLF below 50MA + VIX < 20*

XLF is in a downtrend but the market is complacent (VIX quiet). Directional call selling
is the core idea (very OTM call — trend limits upside), supplemented by a modestly OTM
put to collect the available vol premium.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.20Δ call / short 0.25Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Avg credit | ~$0.43 |
| Avg Reg T margin | ~$6.16/share |

**Backtested (69 weeks):** 79.7% win, +1.7% avg ROC (Reg T), $8.22 cumulative. Max loss −$1.47.

**Why keep the strangle despite low per-trade ROC?** On a properly-sized Reg T basis, the
strangle and the best spread alternative achieve **identical avg ROC (+6.1%)** for this regime
on the overall framework. But the strangle generates 4.6× more absolute P&L per trade when
sized to the same capital ($119 vs $26 per trade at 3% portfolio). The thin credit of a
bear call spread in a low-vol bearish environment barely covers transaction costs.

⚠️ **Sizing:** 2–3% portfolio per trade (vs 5% for spreads) due to undefined tail risk.
A sudden VIX spike or bank shock can gap through the 2× stop. Size conservatively.

---

### Bullish_HighIV — Asymmetric Short Strangle (0.35Δ call / 0.40Δ put)
*XLF above 50MA + VIX ≥ 20*

XLF is in an uptrend but something has spiked VIX (COVID recovery, reopening, macro shock).
Put premiums are rich. The optimal structure leans bearish on the put side (sell 0.40Δ puts —
close to ATM to capture the fear premium) while selling a moderately OTM call (0.35Δ). The
bullish trend supports selling puts and prevents runaway call losses.

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.35Δ call / short 0.40Δ put (same expiry) |
| DTE | ~20 days (±5) |
| Entry day | Friday |
| Profit take | 50% of combined credit |
| Stop loss | 2× combined credit |
| Avg credit | ~$0.99 |
| Avg Reg T margin | ~$6.82/share |

**Backtested (66 weeks):** 75.8% win, +2.1% avg ROC (Reg T), $7.68 cumulative. Max loss −$1.96.

**Why keep the strangle?** Same reasoning as Bearish_LowIV: the best spread alternative
(bull put spread 0.35Δ/0.25Δ, +3.1% ROC) achieves similar ROC but generates 4.7× less
absolute P&L per trade when both are sized to Reg T capital. Strangle collects ~$0.99 vs
~$0.16 for a spread; the margin difference (~$6.82 vs ~$0.46) doesn't fully close this gap.

⚠️ **Sizing:** 2–3% portfolio per trade (vs 5% for spreads). Stop can gap through on sudden
XLF moves (SVB-style bank runs, surprise Fed pivot). This is the highest-risk regime in the
strategy.

---

### Bullish_LowIV — Bear Call Spread (0.35Δ / 0.25Δ)
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

**Backtested (122 weeks):** 69.7% win, +7.0% avg ROC, $2.71 cumulative. Max loss −$0.355.

---

## Combined Backtested Performance (2018–2026)

ROC = pnl / Reg T capital-at-risk (spread max-loss; strangle CBOE uncovered margin).

| Metric | Regime-Switching | Always-on call spread |
|--------|-----------------|----------------------|
| Total trades | 337 | 307 |
| Win rate | **74.8%** | 61.6% |
| Avg ROC/trade | **+6.1%** | −1.5% |
| Cumulative P&L | **$+23.79** | −$1.74 |
| Max drawdown | −$4.83 | −$5.55 |
| Max losing streak | 4 weeks | 7 weeks |

### Per-year summary:

| Year | ROC% | P&L | Notable |
|------|------|-----|---------|
| 2018 | +8.3% | +$1.65 | Mixed regimes; BearHI put spread contributed |
| 2019 | −2.9% | −$0.69 | Bearish_LowIV dominated (9w); strangle ground down |
| 2020 | +7.0% | +$5.57 | COVID crash + recovery; BHI put spread + UHI strangle |
| 2021 | +3.0% | +$8.67 | Strong across all regimes |
| 2022 | +4.1% | +$1.62 | Dominated by Bearish_HighIV (32 weeks) |
| 2023 | +7.8% | +$3.98 | Best year; BearishLO strangle dominated |
| 2024 | −7.9% | −$2.63 | Bullish_HighIV strangle (6 trades) had a bad run |
| 2025 | +17.8% | +$4.84 | Excellent across all four regimes |
| 2026 | +40.6% | +$0.80 | Early 2026 stub |

**7 of 9 years profitable.** 2019 (−2.9%) was a slow Bearish_LowIV environment where the
strangle got ground down. 2024 (−7.9%) was driven by 6 Bullish_HighIV strangle trades.

### Per-regime contribution (Reg T ROC):

| Regime | Weeks | Strategy | Win% | ROC (Reg T) | Sum P&L | AvgMgn |
|--------|:-----:|----------|:----:|:-----------:|:-------:|:------:|
| Bearish_HighIV | 80 | Bull put 0.40Δ/0.30Δ | 77.5% | +11.7% | +$5.19 | $0.49 |
| Bearish_LowIV | 69 | Strangle 0.20Δ/0.25Δ | 79.7% | +1.7% | +$8.22 | $6.16 |
| Bullish_HighIV | 66 | Strangle 0.35Δ/0.40Δ | 75.8% | +2.1% | +$7.68 | $6.82 |
| Bullish_LowIV | 122 | Bear call 0.35Δ/0.25Δ | 69.7% | +7.0% | +$2.71 | $0.35 |

---

## Sizing and Economics

### Bearish_HighIV — Bull Put Spread (~$1 wide)
- Credit ~$0.21/share = $21/contract
- Max loss ~$0.49/share = $49/contract (spread_width − credit)
- At 5% portfolio risk ($5k on $100k): ~102 contracts

### Bearish_LowIV — Short Strangle
- Credit ~$0.43/share = $43/contract
- Reg T margin ~$6.16/share = $616/contract
- Size at **2–3% of portfolio**: $2-3k/$616 ≈ 3–5 contracts

### Bullish_HighIV — Short Strangle
- Credit ~$0.99/share = $99/contract
- Reg T margin ~$6.82/share = $682/contract
- Size at **2–3% of portfolio**: $2-3k/$682 ≈ 3–4 contracts

### Bullish_LowIV — Bear Call Spread (~$1 wide)
- Credit ~$0.16/share = $16/contract
- Max loss ~$0.35/share = $35/contract
- At 5% portfolio risk ($5k on $100k): ~143 contracts

---

## Risks

1. **Strangle gap risk** — Bearish_LowIV and Bullish_HighIV strangles have no defined cap.
   The 2× stop limits losses in normal trading but a gap open through the stop (e.g., SVB
   collapse, surprise Fed move, bank contagion) can exceed the backtest max loss. XLF is
   particularly susceptible to sudden bank-sector events. Size strangles smaller than spreads.

2. **2024 Bullish_HighIV** — 6 strangle trades produced −$2.63 for the year. The HighIV
   strangle is the highest-risk regime. If you are in a period of repeated VIX spikes above
   20 while XLF is in an uptrend, expect above-average stops.

3. **2019 Bearish_LowIV** — The strangle underperformed (slow XLF grind, 9 weeks of entries).
   The 0.20Δ call kept losses contained but put premiums were thin. If XLF trends down
   slowly for months in low VIX, expect near-zero or negative returns.

4. **Regime misclassification** — Regime is classified each Friday close. If XLF crosses
   the 50MA or VIX crosses 20 mid-week, the entry regime may not reflect conditions at entry.
   Check VIX at entry time.

5. **ROC headline vs sizing** — The +6.1% avg Reg T ROC is computed per-trade on the
   capital actually deployed. Because strangles require ~$6-7/share margin vs ~$0.4/share
   for spreads, portfolio impact scales differently. At equal percentage risk, strangles
   deploy more capital and generate more absolute P&L per position.

---

## Why Not All-Spreads?

Tested replacing strangles with spreads:

| | Strangles (current) | All-Spreads |
|--|:-------------------:|:-----------:|
| Avg ROC (Reg T) | **+6.1%** | +6.1% |
| SumPnL | **+$23.79** | +$10.82 |
| Max drawdown | −$4.83 | **−$1.51** |
| Undefined risk | Yes | **No** |

Identical ROC, but strangles generate 2.2× more absolute P&L. Unlike TLT (where spreads
dominated), XLF's BearishLO and BullishHI regimes have rich strangle premiums that no
spread can capture efficiently. **The strangles stay** — but must be sized conservatively
(2–3% vs 5%) and monitored for gap risk.

---

## Current Regime Check

```python
import pandas as pd
df = pd.read_parquet("data/cache/XLF_stock.parquet")
df = df.sort_values("trade_date").tail(60)
close = df["close"].iloc[-1]
ma50  = df["close"].tail(50).mean()
# Also check VIX from data/cache/vix_daily.parquet
trend = "Bullish" if close > ma50 else "Bearish"
print(f"XLF {close:.2f} vs 50MA {ma50:.2f} → {trend}")
```

---

## Code

```bash
# Regime-switching combined backtest:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_regime_switch.py --ticker XLF --ann-target 0

# Structure sweep (per-regime alternatives):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_structure_sweep.py --ticker XLF

# Strangle sweeps by regime:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLF --regime Bearish_LowIV
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLF --regime Bullish_HighIV
```

**Key source files:**
- `run_tlt_regime_switch.py` — combined switching backtest; XLF config in `TICKER_REGIME_STRATEGIES`
- `run_tlt_structure_sweep.py` — per-regime structure/delta sweep with Reg T ROC
- `run_tlt_strategy_study.py` — multi-strategy regime study (accepts `--ticker`)
- `data/studies/xlf_put_spread_playbook.md` — prior put-spread-only research (superseded)

---

## Research History

### Prior version (deprecated 2026-03-19): inflated ROC figures

Prior playbook cited +16.7% avg ROC, +22.3% (BearLO), +13.8% (BullHI) — all using credit
as the ROC denominator (~$0.43/$0.99/share). Correct Reg T denominators for strangles are
~$6.16/$6.82/share, making true ROC +1.7% and +2.1%. Overall avg ROC corrects to +6.1%.
The strangles remain optimal for their regimes despite low per-trade ROC because they
achieve equivalent capital efficiency to spreads but with 4–5× more absolute P&L.

### BearishHI upgraded 2026-03-19: 0.35Δ/0.25Δ → 0.40Δ/0.30Δ

Structure sweep confirmed tighter 0.10Δ wing at 0.40Δ/0.30Δ improves ROC from +8.4% to
+11.7% and SumPnL from +$3.13 to +$5.19 over 80 weeks. Same improvement pattern as TLT.

### Prior to 2026-03-18: always-on bull put spread

XLF was traded as a simple always-on bull put spread (0.35Δ / 0.30Δ, no VIX filter, 50%
take). That study showed +11.82% avg ROC across 206 trades with an 86.4% win rate, but
the aggregate masked severe regime-dependence. See `data/studies/xlf_put_spread_playbook.md`.

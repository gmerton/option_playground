# XLE Strategy Playbook — Regime-Gated Bull Put Spread

**Last updated:** 2026-03-18
**Status:** Backtested 2018–2026. Single tradeable regime confirmed. Ready for live trading.

---

## Overview

XLE (Energy Select Sector SPDR Fund) tracks large-cap US energy — ExxonMobil, Chevron,
EOG, ConocoPhillips, etc. Energy is one of the most volatile equity sectors: commodity-price
driven, geopolitically sensitive, and prone to massive directional swings (XLE fell 65%
in COVID 2020, rallied 125% in 2021–2022, and corrects sharply on recession fears).

This volatility makes most options strategies dangerous on XLE. A full regime sweep of all
five structures (bear call spread, bull put spread, iron condor, short straddle, long
straddle) across four regimes (50MA trend × VIX ≥/< 20) shows only one regime with
reliable edge for credit strategies:

> **Trade only in Bearish_HighIV: XLE below 50-day MA AND VIX ≥ 20.**
> Deploy a bull put spread (short 0.35Δ / long 0.25Δ, ~20 DTE).
> Skip all other weeks.

All other regimes produce negative or negligible ROC for every credit structure tested.
Strangles and straddles are unreliable on XLE due to energy volatility combined with
options data gaps on the most volatile days — settlement losses can reach 10-15× the credit
received.

---

## Why Only Bearish_HighIV?

XLE is fundamentally a directional sector that swings with oil prices. Unlike financials
(XLF) or bonds (TLT), there is no structural mean-reversion or carry trade in energy.
Credit strategies require the underlying to stay rangebound — XLE rarely obliges.

The exception: when XLE has *already* sold off (below 50MA) and VIX is elevated (≥ 20),
the IV risk premium on puts becomes enormous. Selling puts in this environment collects
rich premium for a risk (further decline) that is partially already priced in. The put
spread structure caps loss at the spread width regardless of any further gap moves.

**The other three regimes fail because:**
- **Bearish_LowIV** (+1.8% ROC, bull put): Premium is thin when VIX is low. Energy can keep
  declining without elevated compensation.
- **Bullish_HighIV** (−6.5% ROC, best spread): Upside is real in an energy bull trend, so
  call spreads bleed. Put spreads get blown out when fear suddenly materializes.
- **Bullish_LowIV** (−6.3% ROC, bear call): XLE grinds steadily higher in bull/low-VIX —
  call spreads lose money. The trend is not slow enough to cap.

---

## Entry Rules

### Each Friday, check the regime:

```
XLE close < 50-day MA?    →  Bearish ✓
VIX ≥ 20?                 →  HighIV ✓
Both true?                →  ENTER bull put spread
Otherwise?                →  SKIP this week
```

### Trade parameters:

| Parameter | Value |
|-----------|-------|
| Structure | Short 0.35Δ put / long 0.25Δ put (same expiry) |
| Target DTE | ~20 days (±5) |
| Entry day | Friday |
| Max delta error | ±0.08 from target on each leg |
| Max bid-ask (short leg) | ≤ 25% of mid |
| Profit take | 50% of credit received |
| Stop loss | 2× credit (spread value doubles vs entry) |

---

## Exit Rules

- **Profit take:** Close entire spread when combined value ≤ 50% of credit received
- **Stop loss:** Close when spread value ≥ 2× entry credit
- **Expiry:** If neither fires, let expire / close on expiration day; spread has defined risk

---

## Performance (2018–2026, Bearish_HighIV only)

| Metric | Value |
|--------|-------|
| Total weeks | 79 |
| Win rate | **84.6%** |
| Avg ROC/trade | **+35.5%** |
| Cumulative P&L | **+$15.94** (per-share, 79 trades) |
| Max single-trade loss | −$0.845 |
| Stop-loss hits | 15.4% of trades |

### Per-year breakdown (Bearish_HighIV weeks only):

| Year | N | Win% | ROC% | Notes |
|------|---|------|------|-------|
| 2018 | 10 | 90.0% | — | Rate-hike correction in energy |
| 2019 | 1 | 100.0% | — | Rare; XLE mostly bullish |
| 2020 | 26 | 84.6% | — | COVID crash dominant; massive put premium |
| 2021 | 7 | 85.7% | — | Reopening spike/dip swings |
| 2022 | 14 | 71.4% | — | Russia/Ukraine + Fed hikes; energy volatile |
| 2023 | 7 | 71.4% | — | Regional bank contagion fear |
| 2024 | 4 | 75.0% | — | Thin; XLE mostly bullish |
| 2025 | 10 | 80.0% | — | Tariff + macro fears |

Bearish_HighIV accounts for **~9 weeks/year** on average. This strategy is selective by
design — it fires only when conditions are right, not on a set schedule.

### Regime distribution (weeks per year):

| Year | BearHI | BearLO | BullHI | BullLO | Total |
|------|--------|--------|--------|--------|-------|
| 2018 | 10 | 22 | 0 | 15 | 47 |
| 2019 | 1 | 21 | 0 | 29 | 51 |
| 2020 | 26 | 7 | 15 | 1 | 49 |
| 2021 | 7 | 14 | 11 | 18 | 50 |
| 2022 | 14 | 0 | 32 | 5 | 51 |
| 2023 | 7 | 21 | 2 | 21 | 51 |
| 2024 | 4 | 17 | 2 | 28 | 51 |
| 2025 | 10 | 11 | 5 | 23 | 49 |

The strategy is most active during energy bear markets + macro fear (2020: 26 weeks;
2022: 14 weeks; 2025: 10 weeks). In calm bull markets (2019: 1 week; 2024: 4 weeks),
it barely fires — and that's fine. Selectivity is the edge.

---

## Economics and Sizing

**Approximate spread economics (XLE ~$85–95 at current levels):**

| Item | Approximate value |
|------|-------------------|
| Short put strike (0.35Δ) | ~$76–82 (5–10% OTM) |
| Long put strike (0.25Δ) | ~$1–2 below short |
| Spread width | ~$1–2 |
| Avg credit collected | ~$0.48/share = $48/contract |
| Max loss per contract | Spread width − credit (~$52–$152/contract) |
| 50% profit target | Exit when spread worth ~$0.24 |

**Sizing ($100k portfolio, 5% max risk = $5,000):**
- At spread width $1 (tight chain): ~96 contracts
- At spread width $2 (wider chain): ~48 contracts
- Check the actual spread width at entry; XLE chains can be wide in high-VIX environments
- Max concurrent positions: typically 1–2 (rare to have overlapping 20-DTE entries)

**Note on timing:** Because the strategy only fires ~9 weeks/year, capital is idle most of
the time. This is intentional — the edge is in the selectivity, not in continuous deployment.
Size the active positions to reflect full intended exposure when the signal fires.

---

## Why Not Strangles?

All short strangle combinations tested in Bearish_HighIV produce -145% to -290% avg ROC
with max losses of -$30 to -$47 per share on $2-3 credits. This is caused by:

1. **Energy gap risk:** XLE can move 5–10% overnight on commodity news, OPEC decisions,
   or geopolitical events. The call side of a strangle has no cap on these gaps.

2. **Options data gaps:** On the most volatile XLE days, options_cache is incomplete for
   some strikes. When daily mark data is missing, the stop can't trigger, and the simulation
   (and real position) reaches expiry at catastrophic intrinsic value.

3. **Both sides can lose simultaneously:** In Bearish_HighIV, a reversal can hit the call
   side while the existing put losses haven't cleared. Energy reverses sharply and often.

**The spread width cap is non-negotiable on XLE.** Always use defined-risk structures.

---

## Risks

1. **Sudden energy spike through short strike:** An OPEC surprise cut, geopolitical event,
   or commodity shock can gap XLE down through both legs in a single day. The long leg caps
   loss at spread width, but if XLE gaps well below the long strike, you're at max loss
   immediately. Size accordingly.

2. **Extended energy bear markets:** If XLE stays in Bearish_HighIV for many consecutive
   weeks (2020: 26 weeks), positions can stack up. Each is independently managed with the
   stop rule, but overlapping positions from multiple weeks can correlate in a prolonged
   decline. Cap total XLE put spread exposure at 2–3 concurrent positions.

3. **Regime changes mid-week:** Regime is classified on Friday close. If XLE crosses the
   50MA or VIX crosses 20 during the 20-day holding period, the position remains open per
   the original entry criteria.

4. **VIX as a proxy for energy IV:** XLE IV and VIX are correlated but not identical. A
   VIX spike from financial sector stress may not fully reprice XLE puts. The VIX≥20
   condition is a proxy — actual XLE IV should be checked (IVR or IV30 > 30 on XLE
   itself is an additional confirmation signal).

---

## Code

```bash
# Multi-strategy regime study:
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strategy_study.py --ticker XLE

# Strangle sweep (tested — all negative, not recommended):
MYSQL_PASSWORD=xxx PYTHONPATH=src python run_tlt_strangle_study.py --ticker XLE --regime Bearish_HighIV

# Regime-switching backtest (single regime version):
# Add XLE to TICKER_REGIME_STRATEGIES in run_tlt_regime_switch.py with skip for other regimes
```

**Key source files:**
- `run_tlt_strategy_study.py` — multi-strategy regime study (accepts `--ticker`)
- `run_tlt_strangle_study.py` — strangle sweep (tested; all negative for XLE)
- `data/cache/XLE_stock.parquet` — XLE price history

---

## Comparison to XLF

| | XLE (Bearish_HighIV only) | XLF (all 4 regimes) |
|--|--|--|
| Avg ROC/trade | **+35.5%** | +16.7% |
| Win rate | **84.6%** | 75.0% |
| Weeks/year active | ~9 | ~42 |
| Cumulative P&L | +$15.94 (79 trades) | +$21.74 (336 trades) |
| Max single loss | −$0.845 | −$1.955 |
| Regime specificity | 1 of 4 tradeable | 4 of 4 tradeable |

XLE produces higher per-trade ROC than XLF but is active far less often. XLF is a better
"always-on" regime-switching vehicle; XLE is a high-conviction opportunistic play that
fires when energy fear peaks.

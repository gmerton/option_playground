# SPY Double Calendar Spread — Trading Playbook

**Last updated:** 2026-03-21
**Status:** Backtested 2018–2026. Two tradeable regimes confirmed. Ready for live trading.

---

## Overview

Sell a double calendar spread on SPY every eligible Friday — a put calendar below spot
and a call calendar above spot, both sharing the same short and long expiry dates.

**Structure:**
- Sell OTM put at ~short_expiry (~12 DTE)  |  Buy OTM put at long_expiry (+7 days), same strike
- Sell OTM call at ~short_expiry           |  Buy OTM call at long_expiry, same strike

This is a net-debit, defined-risk strategy. Max loss = net debit paid. Profit is maximized
when SPY pins near the short strikes at the short expiry, allowing both short legs to decay
to zero while the long legs retain residual time value.

**Regime gating is essential.** A full regime sweep shows only two of four regimes with
reliable edge:

| Regime | Put Δ | Call Δ | Profit Take | AvgROC% | Win% | ~Freq |
|--------|-------|--------|-------------|---------|------|-------|
| **Bearish_HighIV** | 0.25Δ | 0.10Δ | Hold to expiry | **+23.7%** | 50.0% | ~8 wks/yr |
| **Bullish_LowIV** | 0.25Δ | 0.25Δ | 50% ROC | **+10.4%** | 59.3% | ~26 wks/yr |
| Bullish_HighIV | — | — | Skip | −3.4% | 46.4% | ~9 wks/yr |
| Bearish_LowIV | — | — | Skip | +10.5% | 55.6% | ~5 wks/yr |

> **Bearish_LowIV is not traded despite positive ROC.** Only 36 entries in 8 years
> (~5/yr); result is dominated by 2018 (+20.8%) and 2022 (+25.2%). Insufficient frequency
> to rely on as a standalone regime. Review if sample grows.

---

## Entry Rules

### Each Friday, classify the regime:

```
SPY close vs 50-day MA?   →  Bullish (above) or Bearish (below)
VIX ≥ 20?                 →  HighIV or LowIV

Bearish_HighIV  →  ENTER asymmetric double calendar (0.25P / 0.10C)
Bullish_LowIV   →  ENTER symmetric double calendar  (0.25P / 0.25C)
Bullish_HighIV  →  SKIP  (also trading bull put spread in this regime)
Bearish_LowIV   →  SKIP  (too infrequent; also long straddle available)
```

### Expiry selection:

| Parameter | Value |
|-----------|-------|
| Short expiry DTE | ~12 days (±3) — target the Friday 2 weeks out |
| Long expiry DTE  | Short DTE + ~7 days (±2) — next Friday after short |
| Entry day | Friday |

With SPY's weekly options, the short expiry is typically the Friday 12 DTE from entry
and the long expiry is the Friday 7 days after that.

### Strike selection:

| Regime | Short put | Short call |
|--------|-----------|------------|
| **Bearish_HighIV** | 0.25Δ (OTM put, ~4–5% below spot) | 0.10Δ (far OTM call, ~3–4% above spot) |
| **Bullish_LowIV**  | 0.25Δ (OTM put, ~2–3% below spot) | 0.25Δ (OTM call, ~2–3% above spot) |

Long legs are matched to the **same strike** as the corresponding short leg.

### Entry filters:

- Max bid-ask spread: 25% of mid on each short leg
- Max delta error: ±0.08 from target on each leg
- Both legs of each calendar must share the same expiry

---

## Exit Rules

| Regime | Rule |
|--------|------|
| **Bearish_HighIV** | **Hold to short expiry.** Short legs settle at intrinsic value; close long legs at market. No early exit. |
| **Bullish_LowIV** | **50% profit take.** Close entire position when combined spread value ≥ net_debit × 1.50. Otherwise hold to short expiry. |

**Combined spread value** = (long_put_mid − short_put_mid) + (long_call_mid − short_call_mid)

**Why no profit take in Bearish_HighIV?** In a high-IV bear regime, the short legs often
spike intraday before reverting. An early exit fires on temporary moves that subsequently
recover. Hold-to-expiry captures the full theta decay of the ~12 DTE short legs. The 75%PT
and hold-to-expiry produce nearly identical results (+19.87% vs +19.64%), so simplicity
favors hold.

**Why 50% take in Bullish_LowIV?** SPY drifts upward in this regime. The 50% take exits
winners before a late-week drift threatens the call side. It improves ROC from +8.45% (hold)
to +10.35% (50%PT) and reduces average hold from 12.0 to 11.8 days.

---

## Performance (2018–2026)

### Bearish_HighIV — 0.25Δ put / 0.10Δ call / hold

Avg net debit: ~$2.15/shr | Avg put strike: ~$383 | Avg call strike: ~$412 (on SPY ~$400)

| Year | N | Win% | AvgROC% | Notes |
|------|---|------|---------|-------|
| 2018 | 8 | 62.5% | +47.7% | Rate-hike correction, IV rich |
| 2019 | 1 | — | — | Single trade (SPY mostly bullish) |
| 2020 | 10 | 40.0% | +68.2% | COVID vol extreme; huge winners when SPY pinned |
| 2021 | 4 | 50.0% | +42.5% | Rotation fear spikes |
| 2022 | 30 | 70.0% | +24.1% | Rate hike grind; chop favors calendar |
| 2023 | 7 | 28.6% | −24.9% | Regional bank whipsaw — worst year |
| 2024 | 3 | 33.3% | −7.6% | Thin (only 3 BearishHI weeks) |
| 2025 | 6 | 33.3% | +17.5% | Tariff/macro fear spikes |
| **TOTAL** | **69** | **53.6%** | **+25.6%** | |

> **2023 warning:** 7 entries, 28.6% win rate, −24.9% ROC. Regional bank contagion created
> large intraday swings that moved SPY away from both calendar strikes. The 0.25Δ put was
> hit on most trades. In whipsaw-dominant bear regimes, the calendar underperforms a simple
> put spread. Keep sizing conservative (~1.5% per trade).

### Bullish_LowIV — 0.25Δ put / 0.25Δ call / 50% take

Avg net debit: ~$2.15/shr | Avg put strike: ~$440 | Avg call strike: ~$453 (on SPY ~$447)

| Year | N | Win% | AvgROC% | Notes |
|------|---|------|---------|-------|
| 2018 | 21 | 66.7% | +21.0% | Chop before Q4 selloff |
| 2019 | 38 | 57.9% | +7.2% | Steady uptrend; moderate |
| 2020 | 8 | 50.0% | −9.3% | COVID spike mid-year in this regime |
| 2021 | 31 | 32.3% | +3.8% | Melt-up; SPY drifted through call strikes |
| 2022 | 3 | 66.7% | +25.8% | Very few BullishLO weeks in 2022 |
| 2023 | 34 | 50.0% | +4.1% | Mixed; some drift |
| 2024 | 37 | 81.1% | **+17.4%** | Fed cut cycle; SPY range-bound |
| 2025 | 30 | 66.7% | **+17.3%** | Continued range-bound behavior |
| **TOTAL** | **209** | **59.3%** | **+10.4%** | |

> **2021 weakness:** 32.3% win rate, +3.8% ROC. SPY's steady melt-up in 2021 (low VIX,
> above MA all year) meant the 0.25Δ call was breached regularly as SPY ground higher. Still
> profitable in aggregate, but this is the worst Bullish_LowIV year. Accept ~1–2 weak years
> per 8-year cycle.

---

## Why the Asymmetry in Bearish_HighIV?

In a bear regime with elevated VIX, the put side carries almost all the premium. The 0.10Δ
call is intentionally cheap — it adds minimal debit but creates a synthetic "call wing" that
benefits if SPY reverses sharply upward (the calendar collects time value on both sides of
a bounce). Without the call, a pure put calendar would have no upside recovery optionality.

Using 0.25Δ on the call side (symmetric) wastes premium — paying for a long call that is
OTM in the direction SPY is trending away from. The asymmetric structure improves avg ROC
from +19.6% (symmetric 0.15/0.15) to +23.7% (0.25P/0.10C).

---

## The Structural Edge

A double calendar exploits **term structure** and **time decay differential**:

1. **Short legs decay fast:** At 12 DTE, theta (daily time decay) is at its steepest.
   The short legs lose most of their extrinsic value in the final 10 trading days.
2. **Long legs retain value:** At ~19 DTE, the long legs still have meaningful time value
   when the short legs expire. The residual value partially offsets the debit.
3. **SPY's tendency to range-revert:** SPY is a 500-stock index. Intraday moves tend to
   mean-revert more than single stocks or sector ETFs. This keeps SPY near the entry
   strikes on most weeks.

**The enemy of the calendar:** A sustained directional move. If SPY moves >2–3% in a
single direction and holds there, both short legs expire deep ITM (put side) or deep OTM
(call side), collapsing the time value differential. 2021 (steady uptrend) and 2023
(whipsaw bear) are the canonical bad-calendar years.

---

## Comparison: Double Calendar vs SPY Put Spread (Bearish_HighIV)

| Strategy | AvgROC% | Win% | Notes |
|----------|---------|------|-------|
| Double calendar 0.25P/0.10C | **+23.7%** | 50.0% | Higher ROC, lower win rate |
| Bull put spread 0.25Δ/0.15Δ | +7.5% | **94.7%** | Much higher win rate, lower ROC |

These strategies suit different temperaments. The put spread wins ~19 of 20 trades at
+7.5% ROC. The double calendar wins ~1 of 2 at +23.7% ROC. Over 8 years the double
calendar produces substantially higher cumulative P&L, but the losing streaks are more
frequent. **Consider running both simultaneously at reduced sizing** (1.5% each) rather
than choosing one exclusively.

---

## Capital Allocation

**Sizing ($100K portfolio — $3,000 allocation, $1,500/trade at max_concurrent=2):**

At avg net debit $2.15/shr:
- $1,500 / ($2.15 × 100) ≈ **7 contracts** per entry
- Max loss = net debit × contracts × 100 = $2.15 × 7 × 100 = **$1,505**
- Full condor (both sides enter simultaneously) = $1,500 deployment

**Concurrent positions:** Short expiry is ~12 DTE, held ~12 days. With weekly Friday
entries, two consecutive entries may overlap briefly. Max concurrent = 2.

**Reduce size in Bearish_HighIV to 1.5% (~$750/trade)** given the 50% win rate and
2023's -24.9% ROC year. The put spread can absorb the other 1.5%.

---

## Risks and Known Limitations

1. **Large directional SPY move** — A >3% move in one week will push one calendar
   deep ITM and the other far OTM. The deep ITM calendar collapses to near-zero time
   value; the far OTM calendar also loses value. Max loss = net debit. Typical bad trade:
   SPY moves sharply; both calendars worth near zero at short expiry.

2. **Vol crush after entry** — If VIX drops sharply right after entry (e.g., Fed meeting
   resolves uncertainty), both short and long legs reprice lower. The net calendar value
   can decline even if SPY stays near the strikes, because the long leg's premium shrinks
   more than the short leg's (more DTE = more vega exposure).

3. **Wide bid-ask spreads** — At 12 DTE, SPY options are liquid, but entering 4 legs
   simultaneously can widen effective fills. Use limit orders at mid; avoid market orders.
   The 25% bid-ask filter removes the worst liquidity days, but slippage still matters
   at this debit size.

4. **2021/2023 regime risk** — Sustained melt-ups (BullishLO) and intraday-whipsaw
   bear markets (BearishHI) are the known failure modes. Both appear 1–2 times per
   8-year window. The defined-risk structure (max loss = debit) prevents catastrophic
   drawdown — but consecutive weak trades are possible.

5. **Calendar vs SPY put spread decision** — In Bearish_HighIV weeks when both strategies
   are active: the put spread is tactically safer (94.7% win) while the calendar is
   tactically more profitable (+23.7% vs +7.5%). Running both at reduced size is the
   recommended approach.

---

## Code

```bash
# Full double calendar sweep (all deltas, all profit targets):
PYTHONPATH=src .venv/bin/python3 run_spy_double_calendar.py

# Single combo detail:
PYTHONPATH=src .venv/bin/python3 run_spy_double_calendar.py \
    --delta 0.25 --profit-target 0.50 --detail-delta 0.25 --detail-pt 0.50

# Asymmetric regime sweep (reproduces this playbook):
# See inline script in session notes; uses double_calendar_study.py directly
```

**Key source files:**
- `src/lib/studies/double_calendar_study.py` — double calendar backtest engine
- `run_spy_double_calendar.py` — symmetric sweep runner
- `data/cache/SPY_options.parquet` — SPY options data (2018–2026)

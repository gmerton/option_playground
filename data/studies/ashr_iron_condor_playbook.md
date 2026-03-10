# ASHR Iron Condor — Trading Playbook

**Last updated:** 2026-03-05
**Status:** Parameters confirmed. Ready for live trading consideration.

---

## Overview

Sell an iron condor on ASHR (Xtrackers Harvest CSI 300 China A-Shares ETF) every
Friday. The strategy sells both a bull put spread and a bear call spread simultaneously,
collecting premium from both sides of the market.

ASHR tracks mainland China A-shares via the CSI 300 index. Unlike most of the other
ETFs in this portfolio, ASHR has **no structural directional bias** over the 2018–2025
study window — it has been range-bound (~$20–35), oscillating around Chinese macro
events (PBOC policy, trade war, COVID, regulatory crackdowns, property sector stress)
without a persistent upward or downward trend. This makes it uniquely suited for
two-sided premium selling.

**The key structural advantage:** In every year from 2018 to 2025, at least one side
of the condor is profitable. The put and call sides exhibit negative correlation — when
China rallies (hurting short calls), the puts profit, and vice versa. **Zero joint-loss
years in 8 years of backtesting.**

---

## Entry Rules

### Every Friday, ~20 DTE — sell both sides:

| Side | Action |
|---|---|
| **Put spread** | Short 0.25Δ put / Long 0.20Δ put (~0.05Δ wing) |
| **Call spread** | Short 0.20Δ call / Long 0.10Δ call (~0.10Δ wing) |

Enter both sides simultaneously every eligible Friday. No VIX filter — enter every week.

**Entry filters (applied to each leg independently):**
- Max bid-ask spread: 25% of mid on the short leg
- Max delta error: ±0.08 from target on each leg
- DTE tolerance: ±5 days around 20-day target
- All four legs must be in the same expiry

**If only one side qualifies (liquidity filter rejects the other):** Enter the qualifying
side alone. Running only puts or only calls is still valid — both sides are independently
profitable.

---

## Exit Rules

- **Profit take (each side independently):** Close when spread value ≤ 50% of credit
  received on that side (keep 50% of premium)
- **Expiry:** If profit target not reached, close/let expire on expiration day
- **Stop-loss:** None — both spreads have defined risk by construction

Manage each spread leg independently — do not wait for both sides to hit their profit
targets simultaneously.

Average holding period: ~11–14 days (early exits dominate).

---

## Parameters

| Parameter | Value |
|---|---|
| Underlying | ASHR |
| Put spread | Short 0.25Δ / Long ~0.20Δ (wing = 0.05Δ) |
| Call spread | Short 0.20Δ / Long ~0.10Δ (wing = 0.10Δ) |
| Target DTE | 20 days |
| DTE tolerance | ±5 days |
| Entry day | Friday |
| VIX filter | None — enter every Friday |
| Max spread (bid-ask/mid) | 25% on each short leg |
| Profit take | 50% of credit per side |
| Credit as % of spread width | Puts ~21% / Calls ~12% |
| Study start date | 2018-01-01 |

---

## Capital Allocation

**Approximate spread economics (ASHR ~$28–35 at current levels):**

| Item | Put spread | Call spread |
|---|---|---|
| Short strike (Δ target) | ~$26–30 (8–12% OTM) | ~$30–34 (5–8% OTM) |
| Long strike | ~$1 below short | ~$2–3 above short |
| Spread width | $1.00 | $2.00–3.00 |
| Credit (~21% / ~12% of width) | ~$0.21/share = $21/contract | ~$0.24–0.36/share = $24–36/contract |
| Max loss per contract | ~$0.79 = $79 | ~$1.76–2.76 = $176–276 |
| 50% profit target | Close at ~$0.105 | Close at ~$0.12–0.18 |

**Note on ASHR liquidity:** ASHR has a less active option chain than US large-cap ETFs.
The 25% bid-ask filter is essential — enforce strictly. On any given Friday, one side
may not qualify (wide spread, no matching delta). Running only the qualifying side is
the right response.

**Example sizing ($100k portfolio, 5% max risk per spread = $5,000):**
- Put spread: $5,000 / $79 ≈ 63 contracts
- Call spread: $5,000 / $176–276 ≈ 18–28 contracts
- Both sides simultaneously when both qualify

---

## Backtested Performance (2018–2025)

### Put spread (short=0.25Δ, wing=0.05Δ, All VIX):

| Metric | Value |
|---|---|
| Total closed trades | 194 |
| Win rate | **86.6%** |
| Mean ROC per trade | **+8.49%** |
| Annualized ROC | +656% |
| Avg holding period | ~12 days |
| Losing years | 2 of 8 (2018: −1.43%, 2025: −2.02%) |

### Call spread (short=0.20Δ, wing=0.10Δ, All VIX):

| Metric | Value |
|---|---|
| Total closed trades | 232 |
| Win rate | **90.1%** |
| Mean ROC per trade | **+8.19%** |
| Annualized ROC | +456% |
| Avg holding period | ~13 days |
| Losing years | 1 of 8 (2020: −3.99%) |

### Per-year breakdown (All VIX):

| Year | Put N | Put Win% | Put ROC% | Call N | Call Win% | Call ROC% | Joint Loss? |
|------|-------|----------|----------|--------|-----------|-----------|-------------|
| 2018 | 11 | 81.8% | −1.43% | 7 | 100% | +10.48% | **No** |
| 2019 | 23 | 87.0% | +6.95% | 24 | 83.3% | +11.15% | No |
| 2020 | 31 | 100% | +20.44% | 26 | 80.8% | −3.99% | **No** |
| 2021 | 39 | 89.7% | +6.76% | 40 | 92.5% | +7.51% | No |
| 2022 | 36 | 86.1% | +1.92% | 31 | 83.9% | +0.92% | No |
| 2023 | 22 | 68.2% | +7.19% | 31 | 100% | +15.63% | No |
| 2024 | 19 | 94.7% | +21.27% | 37 | 91.9% | +16.55% | No |
| 2025 | 13 | 69.2% | −2.02% | 36 | 91.7% | +6.56% | **No** |

**Zero joint-loss years in 8 years.** The put and call sides naturally hedge each other:
- When China rallies sharply (calls threatened), puts profit easily
- When China sells off (puts threatened), calls expire worthless

---

## Why ASHR Works for Condors (and FXI Does Not)

ASHR's range-bound behavior reflects the CSI 300 index's mean-reverting character:
China's domestic market oscillates around PBOC policy, earnings cycles, and periodic
regulatory waves, but has not established a persistent multi-year trend in either
direction over 2018–2025.

**FXI was tested and rejected:** FXI (iShares China Large-Cap, H-shares) fell ~40%
from $50 to ~$25–30 over the same period due to regulatory crackdowns on tech, the
property crisis (Evergrande), and US delisting fears on Hong Kong-listed shares. This
sustained downtrend made put spreads nearly unusable (best put ROC: +4.17%, most
combos negative or zero). Call spreads were viable but thin (+2–6% ROC). See
`data/studies/fxi_analysis_summary.md`.

---

## Forward Vol Factor

**Put spread (0.25Δ/0.05Δ):** avg factor = 1.074

| max factor | N | Skip% | Win% | ROC% | AnnROC% |
|---|---|---|---|---|---|
| (no filter) | 194 | 0% | 86.6% | +8.49% | +656% |
| ≤ 1.10 | 128 | 34% | 84.4% | +8.41% | +664% |
| ≤ 1.00 | 67 | 65% | 85.1% | +15.06% | +851% |

**Call spread (0.20Δ/0.10Δ):** avg factor = 1.137

| max factor | N | Skip% | Win% | ROC% | AnnROC% |
|---|---|---|---|---|---|
| (no filter) | 232 | 0% | 90.1% | +8.19% | +456% |
| ≤ 1.00 | 81 | 65% | 92.6% | +14.62% | +691% |
| ≤ 0.90 | 45 | 81% | 93.3% | +19.28% | +811% |

The ≤1.00 filter doubles per-trade ROC on both sides but skips 65% of entries (~7
trades/year per side). **No filter recommended** — the full dataset provides better
annualized return and maintains the condor's negative-correlation benefit. Using a tight
filter would leave too many weeks with only one side or neither active.

---

## Risks and Known Limitations

1. **China-specific policy risk** — ASHR can gap sharply on PBOC announcements,
   regulatory crackdowns (2021 tech/education sector bans), or US-China trade
   escalations. These moves can be non-linear and arrive overnight. The defined-risk
   spread structure caps losses, but max-loss events are possible.

2. **Lower trade frequency than US ETFs** — ASHR generates fewer qualifying entries
   than XLV or XLF because the option chain is less liquid. ~19–40 trades/year per
   side; some years are thin (2018: only 7 call spread trades; 2025 puts: 13 trades).
   The 2018 and 2025 put-side data are statistically noisy.

3. **Unequal wing widths** — The call spread uses a 0.10Δ wing (wider) vs the put
   spread's 0.05Δ wing. This means max loss per contract is larger on the call side.
   Size accordingly — do not automatically assume equal contracts on both sides.

4. **Currency and trading hours** — ASHR holds mainland China A-shares which trade
   on the Shanghai/Shenzhen exchanges. ASHR trades on NYSE Arca in USD, but the
   underlying can gap on Chinese trading sessions overnight.

5. **Liquidity variability** — On some Fridays, ASHR's option chain is too wide to
   meet the 25% filter on one or both sides. Running the condor is opportunistic;
   expect 1–2 skipped entries per month across one or both sides.

---

## Code

```bash
# Put spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker ASHR --spread 0.25

# Put spread per-year detail (confirmed params):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_put_spreads.py \
    --ticker ASHR --spread 0.25 --detail-short-delta 0.25 --detail-wing 0.05 --no-csv

# Call spread sweep:
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker ASHR --spread 0.25

# Call spread per-year detail (confirmed params):
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python3 run_call_spreads.py \
    --ticker ASHR --spread 0.25 --detail-short-delta 0.20 --detail-wing 0.10 --no-csv
```

**Key source files:**
- `src/lib/studies/put_spread_study.py` — bull put spread engine
- `src/lib/studies/call_spread_study.py` — bear call spread engine
- `src/lib/studies/ticker_config.py` — ASHR parameter configuration
- `data/studies/ashr_iron_condor_playbook.md` — this file
- `data/studies/fxi_analysis_summary.md` — FXI analysis (discarded)

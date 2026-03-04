# UVXY Short Put Sweep — 30 DTE, 50% Profit Take

**Run date:** 2026-03-02

**Output files:**
- `uvxy_puts_2026-03-02.csv` — no spread filter (9,689 rows, all delta × VIX threshold combos)
- `uvxy_puts_spread25_2026-03-02.csv` — spread ≤ 25% of mid (8,662 rows)

**Options cache:** MySQL `stocks.options_cache` — 1,476,601 UVXY rows (2018-01-12 → 2026-02-20)

---

## Setup

| Parameter | Value |
|---|---|
| Ticker | UVXY |
| Strategy | Short OTM put (sell put at target delta) |
| Start date | 2018-01-12 (post leverage change: 2× → 1.5× VIX) |
| End date | 2026-02-20 (last available Athena data) |
| Entry day | Fridays |
| DTE target | 30 days |
| DTE tolerance | ±5 days (accepts 25–35 DTE only) |
| Delta sweep | 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40 (unsigned put delta) |
| Delta tolerance | ±0.08 |
| VIX filter | Skip entry when VIX ≥ threshold on entry date |
| VIX thresholds tested | None (all), VIX<30, VIX<25, VIX<20 |
| Profit take | Exit early when put mid ≤ 50% of entry mid |
| Exit at expiry | Use `last` price; fallback to `mid`; 0 if expired worthless |
| Capital / Margin | Reg T naked put: `(0.20 × strike × 100) + (entry_mid × 100)` |
| Data source | MySQL `options_cache` (synced from Athena `options_daily_v3`) |
| VIX data | Tradier `VIX` daily close, cached to `data/cache/vix_daily.parquet` |
| Reverse splits | Trades spanning a split date are excluded (same as straddle study) |

---

## Spread Analysis

Bid-ask spread as % of mid for UVXY puts, across all dates in the cache (bid > 0, ask > 0):

| Delta bucket | N rows | Median spread% | p75 spread% | p90 spread% | Median mid |
|---|---|---|---|---|---|
| < 5Δ | 26,588 | 66.7% | 120.0% | 168.0% | $0.05 |
| 5–10Δ | 22,035 | 32.8% | 66.7% | 141.9% | $0.25 |
| 10–15Δ | 16,001 | 20.3% | 41.3% | 96.1% | $0.45 |
| 15–20Δ | 14,633 | 16.5% | 33.4% | 76.7% | $0.73 |
| 20–25Δ | 14,910 | 13.3% | 26.7% | 60.4% | $1.11 |
| 25–30Δ | 15,519 | 10.9% | 22.4% | 48.5% | $1.56 |
| 30–35Δ | 16,556 | 9.0% | 19.0% | 41.2% | $2.08 |
| 35–40Δ | 17,867 | 7.5% | 15.9% | 35.6% | $2.72 |
| 40–50Δ | 41,185 | 6.1% | 12.9% | 29.1% | $3.76 |

The 10-delta bucket has a **median spread of 33%** of mid. At p75 it's 67%. Entering a 10-delta put at mid-price is largely a theoretical exercise — in practice you'd likely give up 15–30% of the premium just crossing the spread. The 30–35-delta bucket has a median spread of 9%, which is meaningfully tighter.

---

## Results — No Spread Filter (baseline, mid pricing)

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  383(89%) 90.3%  +9.4% +2.50%  +249%  355(89%) 90.4%  +7.3% +2.21%  +232%  319(89%) 90.0%  +3.6% +1.92%  +221%  238(91%) 92.0% +25.4% +3.05%  +207%
    0.15  386(84%) 83.9%  -0.1% +0.91%  +255%  358(84%) 84.4%  -1.4% +0.65%  +243%  322(84%) 84.8%  +0.1% +0.66%  +238%  240(88%) 88.3% +21.4% +2.63%  +239%
    0.20  385(79%) 80.5%  +0.0% +1.02%  +294%  357(80%) 81.0%  -0.7% +0.87%  +287%  321(80%) 81.3%  +0.3% +0.82%  +283%  241(86%) 86.7% +21.2% +3.52%  +340%
    0.25  383(76%) 77.5%  +2.1% +1.48%  +309%  355(78%) 78.9%  +2.6% +1.64%  +308%  319(78%) 79.3%  +3.2% +1.59%  +307%  239(84%) 84.1% +19.3% +4.40%  +370%
    0.30  385(71%) 73.2%  +2.5% +1.21%  +308%  357(73%) 74.8%  +2.9% +1.36%  +309%  321(74%) 75.7%  +4.4% +1.49%  +309%  241(79%) 80.1% +17.5% +4.46%  +374%
    0.35  385(66%) 68.8%  +1.0% +1.09%  +306%  357(68%) 70.9%  +2.3% +1.64%  +315%  321(69%) 72.3%  +3.8% +1.98%  +321%  241(74%) 76.3% +15.5% +4.88%  +387%
    0.40  388(62%) 65.5%  +1.3% +0.83%  +288%  360(65%) 67.8%  +3.4% +1.81%  +302%  324(66%) 68.8%  +4.6% +2.05%  +308%  244(70%) 72.1% +13.7% +4.77%  +370%
```

---

## Results — Spread ≤ 25% of Mid

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  295(87%) 87.5%  +3.9% +0.72%  +234%  272(87%) 87.5%  +1.6% +0.44%  +218%  238(87%) 87.8%  +2.9% +0.46%  +216%  179(92%) 92.2% +30.9% +2.99%  +221%
    0.15  324(83%) 83.0%  +1.7% +0.82%  +254%  300(83%) 83.7%  +1.3% +0.70%  +241%  266(84%) 84.2%  +3.0% +0.69%  +237%  199(88%) 87.9% +27.9% +3.14%  +250%
    0.20  342(79%) 80.1%  +1.6% +1.05%  +278%  316(80%) 81.0%  +1.5% +1.04%  +271%  282(81%) 81.6%  +3.6% +1.12%  +264%  212(85%) 86.3% +22.0% +3.49%  +310%
    0.25  357(76%) 76.8%  +4.4% +1.70%  +304%  329(78%) 78.7%  +5.6% +2.14%  +307%  293(79%) 79.2%  +6.2% +1.98%  +303%  221(84%) 83.7% +21.1% +4.48%  +359%
    0.30  366(72%) 73.5%  +5.6% +1.81%  +307%  338(74%) 75.1%  +6.7% +2.14%  +311%  302(75%) 75.8%  +8.1% +2.15%  +308%  228(80%) 80.3% +20.9% +5.09%  +372%
    0.35  369(66%) 68.8%  +3.0% +1.31%  +300%  341(69%) 71.0%  +4.7% +1.98%  +309%  305(70%) 72.5%  +6.6% +2.36%  +315%  229(75%) 76.9% +18.4% +5.45%  +386%
    0.40  378(61%) 64.3%  -0.2% +0.19%  +271%  351(64%) 66.7%  +2.0% +1.19%  +288%  315(65%) 67.6%  +3.0% +1.37%  +293%  237(69%) 70.9% +12.1% +4.13%  +358%
```

`N` = closed trades (split-spanning excluded) | `E%` = % that hit 50% profit take | `Pnl%` = avg P&L as % of premium collected | `ROC%` = avg P&L / Reg T margin

---

## Impact of Spread Filter by Delta (VIX<20)

| Delta | N (no filter) | N (spread ≤ 25%) | % retained | ROC% before | ROC% after | Change |
|---|---|---|---|---|---|---|
| 0.10 | 238 | 179 | 75% | +3.05% | +2.99% | −0.06% |
| 0.15 | 240 | 199 | 83% | +2.63% | +3.14% | +0.51% |
| 0.20 | 241 | 212 | 88% | +3.52% | +3.49% | −0.03% |
| 0.25 | 239 | 221 | 92% | +4.40% | +4.48% | +0.08% |
| 0.30 | 241 | 228 | 95% | +4.46% | +5.09% | **+0.63%** |
| 0.35 | 241 | 229 | 95% | +4.88% | +5.45% | **+0.57%** |
| 0.40 | 244 | 237 | 97% | +4.77% | +4.13% | −0.64% |

---

## Per-Year Detail — delta=0.35, VIX<20 (no spread filter)

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 36 | 81% | 80.6% | +30.0% | +9.83% | +634% | 15.1 |
| 2019 | 50 | 56% | 58.0% | -24.0% | -6.24% | +174% | 19.9 |
| 2020 | 8 | 100% | 100.0% | +66.5% | +20.89% | +822% | 13.6 |
| 2021 | 29 | 72% | 75.9% | +28.9% | +9.67% | +367% | 18.4 |
| 2022 | 5 | 100% | 100.0% | +61.0% | +18.20% | +782% | 9.0 |
| 2023 | 35 | 77% | 77.1% | +6.0% | +1.70% | +283% | 17.4 |
| 2024 | 41 | 80% | 82.9% | +32.9% | +8.22% | +449% | 15.8 |
| 2025 | 31 | 71% | 77.4% | +8.2% | +3.49% | +298% | 17.9 |
| 2026 | 6 | 100% | 100.0% | +60.6% | +15.31% | +497% | 13.0 |

---

## Per-Year Detail — delta=0.10, All VIX (baseline reference)

High win rate but severe fat-tail behavior.

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 46 | 96% | 95.7% | +52.1% | +5.99% | +444% | 9.9 |
| 2019 | 51 | 88% | 88.2% | +26.1% | +2.11% | +173% | 14.5 |
| 2020 | 49 | 98% | 98.0% | +54.6% | +6.87% | +369% | 12.1 |
| 2021 | 46 | 85% | 89.1% | -25.5% | -0.74% | +168% | 12.5 |
| 2022 | 51 | 88% | 90.2% | -9.5% | +1.38% | +212% | 11.8 |
| 2023 | 45 | 78% | 80.0% | -66.1% | -4.63% | +36% | 15.7 |
| 2024 | 44 | 91% | 90.9% | +18.2% | +1.01% | +143% | 13.2 |
| 2025 | 46 | 89% | 89.1% | +15.4% | +7.26% | +436% | 14.0 |
| 2026 | 5 | 80% | 100.0% | +61.5% | +6.13% | +351% | 12.0 |

---

## Key Observations

### Spread filter confirms the 10-delta edge is largely illusory

The 25% spread filter removes 23% of 10-delta entries. More tellingly, the All VIX ROC for 0.10 delta drops from +2.50% to +0.72% after filtering — suggesting that a meaningful part of the reported "edge" came from entries where mid-price fills were not achievable. At the 10-delta bucket, the median spread is 33% of mid and p75 is 67%. In practice, a seller would receive the bid price, not mid — so the true entry premium is roughly half of what the baseline study assumes for a typical quote.

### The 25–35 delta range holds up under scrutiny

Applying the spread filter to 0.25–0.35 delta / VIX<20 retains 92–95% of entries and ROC either holds flat or improves slightly. The improvement is not coincidental: the filter removes the most illiquid entry days, which tend to be lower-premium, lower-conviction setups. The 0.30 delta / VIX<20 / spread ≤ 25% combination emerges as the most robust configuration at +5.09% per-trade ROC and +372% annualized.

### 0.40 delta is fragile

The 0.40-delta row looks competitive without the spread filter (VIX<20: +4.77% ROC) but deteriorates after filtering (VIX<20: +4.13%). This suggests the higher-premium trades in that bucket include many wide-spread entries where the mid premium is relatively inflated. Above 0.40 delta, spread quality likely continues to improve, but you're increasingly selling puts with high assignment risk.

### The VIX filter is the primary edge — the spread filter refines it

The VIX<20 filter triples per-trade ROC across virtually every delta level. The spread filter provides a secondary refinement: it removes roughly 5–25% of entries depending on delta and makes the reported results more realistic. Neither filter alone is sufficient; together they define a tradeable regime.

### Why 0.35 delta works despite structural decay (revisited)

UVXY bleeds downward during calm markets, which should push a 0.35 delta put toward the money. But three factors offset this:

1. **UVXY put skew.** The market prices in the known structural decay. Put buyers pay elevated IV for downside protection, leaving sellers with premium that compensates for the expected drift.
2. **The 50% profit take exits early.** 74% of 0.35 delta / VIX<20 trades exit at ~15 days average — before structural decay has meaningfully pressured the position.
3. **2019 proves the risk is real.** With VIX comfortably below 20 all year but UVXY still bleeding, 2019 produced 58% win rate and -24% Pnl% for 0.35 delta. The profit-take trigger was hit only 56% of the time (vs 74–80% in better years), meaning many positions ran to expiry with intrinsic value.

### Beware AnnROC as a summary metric

AnnROC is computed per trade, then averaged. Fast-expiring wins look enormous annualized; absolute losses from slow-burn ITM moves are underweighted in the average. Use `Pnl%` and per-trade `ROC%` as primary reliability metrics. `AnnROC` is useful for comparison across DTE regimes but misleads when loss distributions are skewed.

### Small-N caution (2020, 2022)

The 100% win rates for 0.35 delta / VIX<20 in 2020 (8 trades) and 2022 (5 trades) reflect the filter correctly sitting out elevated-VIX periods. These years had a handful of brief calm windows and are not meaningful evidence of robustness.

---

## Code

```bash
# Default run — no spread filter (reproduces baseline results):
PYTHONPATH=src python run_uvxy_puts.py

# With 25% spread filter (more realistic execution):
PYTHONPATH=src python run_uvxy_puts.py --spread 0.25 --output uvxy_puts_spread25_$(date +%F).csv

# Per-year detail for best combo:
PYTHONPATH=src python run_uvxy_puts.py --spread 0.25 --detail-delta 0.35 --detail-vix 20 --no-csv

# Re-sync options cache from Athena:
PYTHONPATH=src python run_uvxy_puts.py --refresh

# Custom delta range or VIX thresholds:
PYTHONPATH=src python run_uvxy_puts.py --spread 0.25 --deltas 0.25,0.30,0.35 --vix-thresholds none,25,20,18
```

**Key files:**
- `run_uvxy_puts.py` — CLI runner (`--spread`, `--deltas`, `--vix-thresholds`, `--detail-delta`, etc.)
- `src/lib/studies/put_study.py` — generic engine (delta sweep, VIX filter, spread filter, profit take)
- `src/lib/studies/straddle_study.py` — `sync_options_cache()` (Athena → MySQL sync, shared with straddle study)
- `src/lib/mysql_lib.py` — `options_cache` table helpers
- `uvxy_puts_2026-03-02.csv` — baseline results, no spread filter (9,689 rows)
- `uvxy_puts_spread25_2026-03-02.csv` — spread ≤ 25% filter (8,662 rows)
- `data/cache/vix_daily.parquet` — cached VIX daily closes (Tradier)
- MySQL table: `stocks.options_cache` (1,476,601 UVXY rows)

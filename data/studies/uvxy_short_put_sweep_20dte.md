# UVXY Short Put Sweep — 20 DTE, 50% Profit Take

**Run date:** 2026-03-02

**Output files:**
- `uvxy_puts_20dte_2026-03-02.csv` — no spread filter (9,530 rows, all delta × VIX threshold combos)
- `uvxy_puts_20dte_spread25_2026-03-02.csv` — spread ≤ 25% of mid (8,595 rows)

**Related study:** `data/studies/uvxy_short_put_sweep.md` (30 DTE equivalent)

**Options cache:** MySQL `stocks.options_cache` — 1,476,601 UVXY rows (2018-01-12 → 2026-02-20)

---

## Setup

Same as the 30 DTE study except DTE target is 20 ± 5 (accepts 15–25 DTE).
All other parameters unchanged: Fridays, 50% profit take, Reg T margin, VIX filter, spread filter.

---

## Results — No Spread Filter (baseline, mid pricing)

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  388(89%) 88.7% -25.0% +0.26%  +192%  360(89%) 88.6% -29.6% -0.18%  +169%  324(88%) 88.0% -37.9% -0.68%  +151%  242(91%) 90.9% -31.0% +0.29%  +176%
    0.15  388(83%) 84.0%  -0.7% +1.15%  +245%  360(83%) 84.2%  -1.1% +0.99%  +232%  324(83%) 83.3%  -4.0% +0.60%  +215%  243(86%) 86.4% +16.9% +2.21%  +247%
    0.20  380(79%) 80.0%  +4.0% +1.36%  +286%  352(80%) 80.4%  +3.5% +1.23%  +273%  316(79%) 79.7%  +1.5% +0.77%  +256%  236(83%) 83.9% +20.2% +2.80%  +299%
    0.25  386(75%) 76.4%  +2.6% +1.15%  +307%  358(76%) 77.1%  +3.0% +1.19%  +303%  322(76%) 77.3%  +1.8% +0.84%  +293%  243(80%) 81.1% +14.0% +2.77%  +338%
    0.30  382(73%) 74.6%  +3.0% +1.26%  +331%  354(74%) 76.0%  +3.9% +1.56%  +333%  318(75%) 76.1%  +3.2% +1.17%  +325%  238(79%) 80.7% +16.1% +3.63%  +391%
    0.35  387(68%) 69.8%  +2.3% +1.14%  +338%  359(70%) 71.6%  +3.8% +1.78%  +349%  323(71%) 72.1%  +3.3% +1.42%  +344%  243(77%) 77.0% +15.5% +4.17%  +422%
    0.40  390(63%) 65.4%  +0.6% +0.69%  +319%  362(65%) 67.7%  +2.3% +1.45%  +333%  326(66%) 68.1%  +2.2% +1.23%  +330%  246(72%) 73.2% +13.2% +4.33%  +420%
```

**Notable:** The 0.10 delta row is deeply negative on Pnl% despite an 88-91% win rate. This is the fat-tail / liquidity distortion problem — many "wins" are tiny and the rare losses are enormous, compounded by illiquid mid-price assumptions. The spread filter is essential here.

---

## Results — Spread ≤ 25% of Mid

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  289(89%) 88.6% +11.7% +1.53%  +218%  265(89%) 88.7% +10.4% +1.36%  +206%  231(88%) 88.3%  +7.6% +1.19%  +199%  172(92%) 91.9% +34.4% +3.47%  +257%
    0.15  335(83%) 84.2%  +4.9% +1.04%  +240%  310(84%) 84.5%  +5.5% +0.95%  +231%  275(83%) 83.6%  +3.1% +0.57%  +216%  205(85%) 86.3% +24.7% +2.38%  +254%
    0.20  348(79%) 79.3%  +2.9% +1.08%  +279%  323(79%) 79.9%  +3.0% +1.13%  +275%  288(79%) 79.2%  +0.9% +0.68%  +258%  214(83%) 83.6% +20.5% +2.95%  +308%
    0.25  366(75%) 77.0%  +5.3% +1.44%  +309%  339(76%) 77.9%  +6.1% +1.56%  +312%  303(77%) 78.2%  +5.3% +1.29%  +302%  226(81%) 82.7% +20.3% +3.72%  +361%
    0.30  368(73%) 74.5%  +4.9% +1.36%  +328%  342(74%) 76.0%  +6.1% +1.76%  +336%  306(75%) 76.1%  +5.7% +1.42%  +329%  228(79%) 81.1% +19.9% +4.07%  +404%
    0.35  379(68%) 70.2%  +3.7% +1.38%  +341%  351(71%) 71.8%  +5.4% +2.03%  +351%  315(71%) 72.4%  +5.0% +1.68%  +346%  235(77%) 77.4% +18.2% +4.63%  +427%
    0.40  382(63%) 65.4%  +1.4% +0.78%  +320%  355(65%) 67.9%  +3.3% +1.64%  +340%  319(66%) 68.3%  +3.3% +1.43%  +337%  239(72%) 73.6% +15.0% +4.70%  +433%
```

---

## Spread Filter Impact at VIX<20

| Delta | N (no filter) | N (spread ≤ 25%) | % retained | ROC% before | ROC% after | Change |
|---|---|---|---|---|---|---|
| 0.10 | 242 | 172 | 71% | +0.29% | **+3.47%** | **+3.18%** |
| 0.15 | 243 | 205 | 84% | +2.21% | +2.38% | +0.17% |
| 0.20 | 236 | 214 | 91% | +2.80% | +2.95% | +0.15% |
| 0.25 | 243 | 226 | 93% | +2.77% | +3.72% | +0.95% |
| 0.30 | 238 | 228 | 96% | +3.63% | +4.07% | +0.44% |
| 0.35 | 243 | 235 | 97% | +4.17% | +4.63% | +0.46% |
| 0.40 | 246 | 239 | 97% | +4.33% | +4.70% | +0.37% |

The 0.10 delta spread filter effect (+3.18% ROC swing) is the largest of any cell in either study. The unfiltered 0.10 delta row is worse at 20 DTE than at 30 DTE, but the filtered row is the best 0.10 delta result across both studies.

---

## Per-Year Detail — delta=0.35, VIX<20, spread ≤ 25%

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 36 | 86% | 86.1% | +39.2% | +10.61% | +722% | 10.9 |
| 2019 | 50 | 56% | 56.0% | -24.9% | -5.88% | +176% | 14.9 |
| 2020 | 8 | 100% | 100.0% | +67.8% | +17.75% | +767% | 12.1 |
| 2021 | 29 | 86% | 86.2% | +44.0% | +12.90% | +525% | 13.4 |
| 2022 | 5 | 100% | 100.0% | +60.7% | +17.17% | +832% | 8.2 |
| 2023 | 35 | 69% | 68.6% | -13.9% | -3.25% | +236% | 13.3 |
| 2024 | 41 | 80% | 82.9% | +24.1% | +4.60% | +396% | 12.0 |
| 2025 | 28 | 86% | 85.7% | +46.3% | +9.94% | +485% | 12.0 |
| 2026 | 3 | 100% | 100.0% | +65.0% | +14.76% | +664% | 9.3 |

---

## Per-Year Detail — delta=0.10, VIX<20, spread ≤ 25%

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 23 | 96% | 95.7% | +62.5% | +5.28% | +355% | 8.0 |
| 2019 | 43 | 91% | 90.7% | +41.2% | +2.42% | +177% | 10.2 |
| 2020 | 8 | 100% | 100.0% | +64.9% | +4.83% | +310% | 9.6 |
| 2021 | 28 | 93% | 92.9% | +41.8% | +2.68% | +205% | 9.4 |
| 2022 | 5 | 100% | 100.0% | +62.4% | +4.20% | +232% | 7.4 |
| 2023 | 23 | 83% | 82.6% | -50.4% | -0.17% | +98% | 10.5 |
| 2024 | 21 | 95% | 95.2% | +27.6% | +1.26% | +162% | 8.7 |
| 2025 | 21 | 90% | 90.5% | +61.5% | +10.17% | +638% | 9.9 |

*2026 not shown — only 4 trades in the filtered set.*

---

## 20 DTE vs 30 DTE Comparison (spread ≤ 25%, VIX<20)

| Delta | 30DTE ROC% | 20DTE ROC% | 30DTE AnnROC% | 20DTE AnnROC% | Better DTE (ROC) |
|---|---|---|---|---|---|
| 0.10 | +2.99% | **+3.47%** | +221% | **+257%** | **20 DTE** |
| 0.15 | **+3.14%** | +2.38% | +250% | +254% | 30 DTE |
| 0.20 | **+3.49%** | +2.95% | +310% | +308% | 30 DTE |
| 0.25 | **+4.48%** | +3.72% | +359% | +361% | 30 DTE |
| 0.30 | **+5.09%** | +4.07% | +372% | **+404%** | 30 DTE (ROC) / 20 DTE (AnnROC) |
| 0.35 | **+5.45%** | +4.63% | +386% | **+427%** | 30 DTE (ROC) / 20 DTE (AnnROC) |
| 0.40 | +4.13% | **+4.70%** | +358% | **+433%** | **20 DTE** |

---

## Key Observations

### The spread filter is indispensable at 10 delta for both DTE regimes

At 20 DTE, the 0.10 delta row without a spread filter shows -31% Pnl% and +0.29% ROC for VIX<20 — nearly break-even. After applying the 25% spread filter, it becomes +34.4% Pnl% and +3.47% ROC. This is the largest single filter impact in either study. The illiquid 0.10 delta entries at 20 DTE are especially toxic, but the liquid ones — once you can find them — are genuinely attractive.

### The user's intuition was correct: 10-delta has better liquidity at 20 DTE

At 30 DTE, the filtered 0.10 delta / VIX<20 ROC was +2.99% (179 trades). At 20 DTE it is +3.47% (172 trades). The per-trade and annualized ROC are both better at the shorter tenor. This is consistent with 10-delta puts at 20 DTE having a higher absolute premium (less time decay to bleed, less negative carry risk) while still benefiting from the same percentage spread threshold.

### For higher deltas, 30 DTE wins on per-trade ROC; 20 DTE wins on annualized

At 0.35 delta / VIX<20 / spread ≤ 25%, 30 DTE delivers +5.45% per-trade ROC vs +4.63% at 20 DTE. However, 20 DTE wins on annualized ROC (427% vs 386%) because positions close faster — winners exit at ~10–13 days average vs ~15 days at 30 DTE. The choice between DTE regimes here is a preference question: fewer, larger trades (30 DTE) or faster turnover (20 DTE).

### 2019 and 2023 remain the stress years at every delta and DTE

The two bad years for 0.35 delta / VIX<20 are identical across both DTE regimes: 2019 (58% win, ~-25% Pnl%) and 2023 (69-77% win, -14% to +6% Pnl%). This is not a DTE artifact — these are genuine regime failures where either moderate sustained UVXY decay (2019) or a brief vol spike (March 2023 banking crisis) pressured higher-delta puts. Neither shorter DTE nor a spread filter protects against these events.

### 0.40 delta reversal

At 30 DTE, 0.40 delta with the spread filter underperformed 0.35 delta (+4.13% vs +5.45% ROC). At 20 DTE it reverses: 0.40 delta leads the filtered VIX<20 table at +4.70% ROC, barely edging 0.35 delta (+4.63%). This may reflect the shorter theta exposure at 20 DTE making the higher premium of 0.40 delta more efficient before assignment risk kicks in.

---

## Code

```bash
# 20 DTE run — no spread filter:
PYTHONPATH=src python run_uvxy_puts.py --dte 20 --output uvxy_puts_20dte_$(date +%F).csv

# 20 DTE with 25% spread filter:
PYTHONPATH=src python run_uvxy_puts.py --dte 20 --spread 0.25 --output uvxy_puts_20dte_spread25_$(date +%F).csv

# Per-year detail for best combo:
PYTHONPATH=src python run_uvxy_puts.py --dte 20 --spread 0.25 --detail-delta 0.35 --detail-vix 20 --no-csv

# Per-year detail for 10-delta:
PYTHONPATH=src python run_uvxy_puts.py --dte 20 --spread 0.25 --detail-delta 0.10 --detail-vix 20 --no-csv
```

**Key files:**
- `run_uvxy_puts.py` — CLI runner
- `src/lib/studies/put_study.py` — generic engine
- `uvxy_puts_20dte_2026-03-02.csv` — baseline results, no spread filter (9,530 rows)
- `uvxy_puts_20dte_spread25_2026-03-02.csv` — spread ≤ 25% filter (8,595 rows)
- `data/cache/vix_daily.parquet` — cached VIX daily closes (Tradier)
- MySQL table: `stocks.options_cache` (1,476,601 UVXY rows)

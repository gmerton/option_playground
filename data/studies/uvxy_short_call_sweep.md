# UVXY Short Call Sweep — 20 & 30 DTE, 50% Profit Take

**Run date:** 2026-03-02

**Output files:**
- `uvxy_calls_30dte_2026-03-02.csv` — 30 DTE, no spread filter (11,094 rows)
- `uvxy_calls_30dte_spread25_2026-03-02.csv` — 30 DTE, spread ≤ 25% (10,355 rows)
- `uvxy_calls_20dte_2026-03-02.csv` — 20 DTE, no spread filter (11,019 rows)
- `uvxy_calls_20dte_spread25_2026-03-02.csv` — 20 DTE, spread ≤ 25% (10,502 rows)

**Related studies:**
- `data/studies/uvxy_short_put_sweep.md` (30 DTE puts)
- `data/studies/uvxy_short_put_sweep_20dte.md` (20 DTE puts)

**Options cache:** MySQL `stocks.options_cache` — 1,476,601 UVXY rows (2018-01-12 → 2026-02-20)

---

## Setup

Same parameters as the put studies except:
- Calls instead of puts (`cp == "C"`, delta is positive)
- Delta sweep extended to include 0.50 (ATM) given better call liquidity at higher deltas
- All other parameters unchanged: Fridays, 50% profit take, Reg T margin, VIX filter, spread filter

---

## Results — 30 DTE, Spread ≤ 25%

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  320(98%) 98.8% -103.6% -3.58%   +91%  310(98%) 98.7% -108.9% -3.81%   +86%  279(98%) 98.6% -127.7% -4.65%   +74%  215(98%) 98.1% -183.6% -7.41%   +21%
    0.15  332(98%) 98.5%  -57.9% -3.22%  +147%  319(98%) 98.4%  -62.7% -3.58%  +137%  288(98%) 98.3%  -76.1% -4.55%  +122%  223(97%) 97.8% -115.2% -7.59%   +63%
    0.20  341(98%) 98.2%  -27.0% -2.50%  +222%  325(98%) 98.2%  -31.4% -3.01%  +207%  292(98%) 97.9%  -42.0% -4.25%  +186%  224(97%) 97.3%  -72.5% -7.98%  +111%
    0.25  351(96%) 96.3%  -16.9% -2.17%  +302%  332(96%) 96.1%  -21.5% -2.92%  +275%  298(96%) 95.6%  -30.8% -4.36%  +247%  228(95%) 94.7%  -57.6% -8.67%  +152%
    0.30  360(96%) 96.1%   -5.8% -0.82%  +383%  338(96%) 95.9%  -10.2% -1.73%  +342%  303(95%) 95.4%  -18.3% -3.33%  +309%  230(94%) 94.3%  -41.5% -8.02%  +197%
    0.35  370(96%) 95.9%   +0.2% +0.79%  +469%  345(95%) 95.7%   -4.2% -0.32%  +416%  310(95%) 95.5%  -11.3% -1.95%  +381%  234(94%) 94.4%  -32.5% -6.95%  +253%
    0.40  376(95%) 95.2%   +3.3% +1.52%  +521%  350(95%) 94.9%   -1.0% +0.25%  +457%  315(95%) 94.6%   -7.5% -1.57%  +419%  238(94%) 93.7%  -26.9% -6.75%  +289%
    0.50  378(93%) 93.9%  +12.0% +3.91%  +617%  351(92%) 93.4%   +8.4% +2.39%  +535%  315(91%) 93.0%   +3.1% +0.32%  +489%  237(90%) 92.0%  -12.6% -5.46%  +346%
```

---

## Results — 20 DTE, Spread ≤ 25%

```
   Delta             All VIX                          VIX<30                          VIX<25                          VIX<20
          N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%  N(E%)  Win%   Pnl%   ROC%  AnnROC%
  -----------------------------------------------------------------------------------------------------------------------------------------------
    0.10  289(98%) 88.6%  +11.7% +1.53%  +218%  ...
    0.30  368(95%) 95.5%  +10.2% +1.97%  +441%  353(95%) 95.2%   +6.6% +1.22%  +396%  318(94%) 94.7%   +0.6% +0.14%  +370%  241(94%) 94.2%  -14.8% -2.76%  +278%
    0.35  382(94%) 94.5%  +12.9% +3.07%  +515%  356(94%) 94.1%   +9.3% +2.19%  +460%  321(93%) 93.5%   +3.5% +0.89%  +427%  243(92%) 92.6%  -10.7% -2.22%  +317%
    0.40  383(94%) 93.7%  +15.4% +3.98%  +576%  356(93%) 93.3%  +12.0% +2.95%  +518%  321(93%) 92.8%   +7.0% +1.58%  +483%  243(92%) 91.8%   -5.7% -1.70%  +363%
    0.50  381(91%) 91.3%  +14.7% +4.43%  +660%  353(90%) 90.9%  +12.3% +3.53%  +593%  318(90%) 90.3%   +7.5% +1.77%  +548%  240(88%) 88.8%   -3.5% -2.05%  +398%
```

`N` = closed trades (split-spanning excluded) | `E%` = % that hit 50% profit take | `Pnl%` = avg P&L as % of premium | `ROC%` = avg P&L / Reg T margin

---

## Per-Year Detail — delta=0.50, All VIX, spread ≤ 25%

### 30 DTE

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 46 | 76% | 78.3% | -52.3% | -16.69% | +255% | 15.4 |
| 2019 | 49 | 94% | 93.9% | +41.2% | +12.95% | +671% | 12.0 |
| 2020 | 48 | 96% | 95.8% | **-122.7%** | **-44.41%** | +123% | 12.2 |
| 2021 | 46 | 98% | 97.8% | +51.8% | +19.16% | +821% | 12.5 |
| 2022 | 51 | 96% | 96.1% | +48.3% | +16.83% | +752% | 12.6 |
| 2023 | 45 | 98% | 97.8% | +51.9% | +16.80% | +824% | 11.4 |
| 2024 | 45 | 89% | 95.6% | +30.8% | +11.57% | +694% | 13.6 |
| 2025 | 44 | 93% | 95.5% | +45.6% | +14.91% | +834% | 12.0 |
| 2026 | 4 | 100% | 100.0% | +59.7% | +17.92% | +395% | 19.2 |

### 20 DTE

| Year | N | E% | Win% | Pnl% | ROC% | AnnROC% | AvgDays |
|---|---|---|---|---|---|---|---|
| 2018 | 45 | 76% | 77.8% | -60.7% | -18.51% | +103% | 12.5 |
| 2019 | 51 | 94% | 94.1% | +45.6% | +12.78% | +762% | 9.7 |
| 2020 | 49 | 90% | 91.8% | **-68.4%** | **-22.75%** | +300% | 10.1 |
| 2021 | 46 | 98% | 97.8% | +47.4% | +16.16% | +883% | 10.1 |
| 2022 | 50 | 92% | 92.0% | +41.5% | +13.70% | +820% | 10.1 |
| 2023 | 45 | 91% | 91.1% | +43.7% | +13.03% | +859% | 9.5 |
| 2024 | 48 | 96% | 95.8% | +30.6% | +9.66% | +747% | 10.3 |
| 2025 | 43 | 91% | 90.7% | +33.8% | +10.41% | +822% | 10.5 |
| 2026 | 4 | 75% | 75.0% | +49.3% | +14.99% | +406% | 16.2 |

---

## The Dominant Finding: VIX Filter Works in Reverse

This is the most important result from the call study. In the put study, the VIX<20 filter was the single largest performance driver — it roughly tripled per-trade ROC. **For calls, VIX<20 is the worst regime at every delta and DTE:**

| VIX Regime | N | Win% | Pnl% | ROC% | AnnROC% |
|---|---|---|---|---|---|
| All VIX | 378 | 93.9% | +12.0% | **+3.91%** | +617% |
| VIX<30 | 351 | 93.4% | +8.4% | +2.39% | +535% |
| VIX<25 | 315 | 93.0% | +3.1% | +0.32% | +489% |
| VIX<20 | 237 | 92.0% | -12.6% | -5.46% | +346% |

*(0.50 delta, 30 DTE, spread ≤ 25%)*

The more you restrict to calm-VIX entries, the worse the results. This is structurally opposite to the put study.

**Why:** Writing calls when VIX is low means entering when UVXY is already at a depressed level from structural decay. A spike from a low VIX base hits call sellers with maximum pain — UVXY doubles or triples from a floor rather than declining further from an elevated level. High-VIX entries, by contrast, benefit from UVXY's accelerated structural decay from elevated levels; the premium collected is also larger.

**Implication for the optimizer:** the optimal VIX regime for call writing is likely a *band* — a minimum VIX (avoid extreme complacency) and possibly a maximum (avoid extreme panic where calls get blown through immediately). A simple upper-bound filter is the wrong shape for the call side. Optuna should discover this; the parameter to add is `vix_min`, not just `vix_max`.

---

## The Two Bad Years: 2018 and 2020

Six of nine full years are highly profitable at 0.50 delta. The two blowup years are structural:

- **2018**: Feb 5 "Volmageddon" spike — VIX went from 14 to 37 intraday, UVXY surged. Short call positions entered in late January were deep ITM by expiry. Q4 2018 equity sell-off added further pain.
- **2020**: COVID March spike — UVXY more than tripled in ~3 weeks. Any short call position entered February/March 2020 was catastrophic. The 30 DTE version saw -122% Pnl% because positions were held through more of the spike; 20 DTE limited the damage to -68% by reducing exposure time.

These events share a key characteristic: both started from a low-VIX, complacent environment and accelerated rapidly. A VIX minimum threshold (e.g., only write calls when VIX > 15–18) would have reduced exposure in February 2018 and early 2020 — exactly what the optimizer should find.

---

## 20 DTE vs 30 DTE (0.50 delta, All VIX, spread ≤ 25%)

| Metric | 30 DTE | 20 DTE |
|---|---|---|
| Per-trade ROC | +3.91% | **+4.43%** |
| AnnROC | +617% | **+660%** |
| Avg days held | ~12.3 | **~10.2** |
| 2020 Pnl% | -122.7% | **-68.4%** |
| 2018 Pnl% | -52.3% | -60.7% |
| Win rate (All VIX) | 93.9% | 91.3% |

20 DTE wins on ROC, AnnROC, and dramatically reduces 2020 losses (10 vs 12 average days held means less time inside the spike). The tradeoff is marginally lower win rate. Overall 20 DTE is the preferred starting point for a live implementation.

---

## Calls vs Puts: Summary Comparison

| | Best Put Config | Best Call Config |
|---|---|---|
| Strategy | Sell OTM put, 30 DTE | Sell ATM call (0.50Δ), 20 DTE |
| VIX filter | VIX < 20 (avoid spikes) | **No filter** (All VIX is best) |
| Spread filter | ≤ 25% (essential) | ≤ 25% (less impactful) |
| Per-trade ROC | +5.09–5.45% | +4.43% |
| Bad years | 2019 (slow bleed) | 2018, 2020 (vol spikes) |
| Risk type | Structural decay | Sudden spike |
| VIX filter direction | Max threshold | **Min threshold (TBD)** |

Calls and puts fail in different years from different causes — a strong argument for running them together (the optimizer joint study), after first finding the optimal VIX band for calls.

---

## What the Optimizer Should Find

The call study demonstrates that the optimal VIX regime is not a simple upper bound — it's a range. Optuna should search over:
- `vix_min` ∈ [10, 25]: skip entries when VIX is too low (complacency risk)
- `vix_max` ∈ [25, 60]: skip entries when VIX is too high (immediate spike risk)
- `delta` ∈ [0.25, 0.55]: higher delta appears better for calls
- `profit_take_pct` ∈ [0.30, 0.75]
- `max_spread_pct` ∈ [0.15, 0.40]

Walk-forward validation (2018–2022 train, 2023–2025 validate) will guard against overfitting to the 2020 event.

---

## Code

```bash
# 30 DTE, with spread filter:
PYTHONPATH=src python run_uvxy_calls.py --spread 0.25

# 20 DTE, with spread filter (recommended):
PYTHONPATH=src python run_uvxy_calls.py --dte 20 --spread 0.25

# Per-year detail for best combo:
PYTHONPATH=src python run_uvxy_calls.py --dte 20 --spread 0.25 --detail-delta 0.50 --no-csv

# Custom deltas:
PYTHONPATH=src python run_uvxy_calls.py --dte 20 --spread 0.25 --deltas 0.35,0.40,0.50
```

**Key files:**
- `run_uvxy_calls.py` — CLI runner
- `src/lib/studies/call_study.py` — call sweep engine (imports `fetch_vix_data`, `find_exits` from `put_study.py`)
- `src/lib/studies/put_study.py` — `find_exits` now accepts `entry_mid_col` and `cp` params
- `uvxy_calls_30dte_spread25_2026-03-02.csv` — 30 DTE filtered results (10,355 rows)
- `uvxy_calls_20dte_spread25_2026-03-02.csv` — 20 DTE filtered results (10,502 rows)
- MySQL table: `stocks.options_cache` (1,476,601 UVXY rows)

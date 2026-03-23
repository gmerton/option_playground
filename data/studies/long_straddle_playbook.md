# Long Straddle Playbook

**Strategy:** Buy ATM straddle (long call + long put, same strike)
**Perspective:** Buyer — profit when stock moves more than implied by premium
**Universe:** 140-ticker approved list (walk-forward validated, 2021–2025)
**Status:** Research complete. Ready to trade.

---

## Strategy Structure

| Leg | Type | Delta | DTE | Action |
|-----|------|-------|-----|--------|
| Call | ATM call | ~+0.50Δ | ~10 DTE | Buy 1x |
| Put  | ATM put  | ~−0.50Δ | ~10 DTE | Buy 1x |

- Same strike for both legs
- Entry: Friday morning, ~10 DTE expiry
- Same expiry for both legs (weekly options)

**P&L:**
- Cost = call_mid + put_mid (debit paid)
- Payout = call_settlement + put_settlement at expiry
- Profit = payout − cost
- ROC = profit / cost × 100%

---

## Entry Conditions (all required)

1. **Ticker on approved list** (see below)
2. **FVR ≥ 1.20** — forward vol ratio (30→90d) must be in contango
   - FVR = fvr_put_30_90 from `silver.fwd_vol_daily`
   - FVR ≥ 1.20 means 90-day implied vol > 30-day → market expects vol to expand
   - Check on the Friday morning of entry
3. **Liquid chain** — verify bid > 0 / ask > 0 / OI > 0 on both legs in broker before entering
   - Approved list includes some thinly-traded names; always confirm fills are realistic

---

## Sizing

**Per-trade allocation is based on premium paid (= max loss).**

| FVR at entry | Size | Dollar amount ($100K account) |
|---|---|---|
| FVR ≥ 1.40 | Full | 1.5% = **$1,500 in premium** |
| FVR 1.20–1.39 | Half | 0.75% = **$750 in premium** |

**Example:** Straddle costs $3.00 ($1.50 call + $1.50 put) with FVR = 1.45
→ Buy 5 contracts ($1,500 ÷ $300/contract)

**Portfolio cap:** Maximum 3% of account in open straddle positions at any time.
Multiple signals may fire the same week; if total open premium would exceed $3,000,
skip the weakest FVR signals first.

---

## Exit Rules

| Condition | Action |
|-----------|--------|
| Position value drops to ≤50% of premium paid | **Exit immediately (stop-loss)** |
| Expiry | Let expire (payout is settlement value) |
| No other take-profit rule | Do not exit early on winners — let them run |

**Why no profit cap:** The long straddle is a right-skewed payoff. OOS testing showed
that any profit cap reduces Sharpe (Cap 100% drops Sharpe from +0.17 to −0.04).
The large wins are not anomalies — they are the strategy.

**Why stop at −50%:** Removing trades that lose >50% of premium improves OOS Sharpe
from +0.072 (hold to expiry) to +0.170 — a 2.4× improvement, positive in every
test year 2021–2025. By day 5–7 on a 10 DTE straddle, a position down 50% has
minimal recovery potential (remaining value is mostly time value decay).

---

## Performance (OOS Walk-Forward, 2021–2025)

Walk-forward design: qualify tickers on IS data (2018→N−1), trade approved
list in test year N with FVR≥1.20 gate. Five folds: 2021, 2022, 2023, 2024, 2025.
Minimum straddle cost $0.50 (penny straddles excluded).

**With stop at −50% of premium:**

| Year | N trades | Win% | Avg ROC% | Sharpe |
|------|----------|------|----------|--------|
| 2021 | 1,932 | 41.7% | +10.1% | +0.125 |
| 2022 | 1,187 | 47.5% | +17.9% | +0.236 |
| 2023 | 1,608 | 44.4% | +13.8% | +0.176 |
| 2024 | 1,993 | 42.5% | +10.2% | +0.140 |
| 2025 | 2,116 | 44.5% | +13.6% | +0.175 |
| **OOS avg** | **1,767** | **44.1%** | **+13.1%** | **+0.170** |

Baseline (hold to expiry, no filter): Sharpe −0.003
Baseline (FVR≥1.20, all tickers, hold to expiry): Sharpe +0.036
This strategy (approved list + FVR gate + stop): Sharpe +0.170

---

## FVR Signal Interpretation

FVR = fvr_put_30_90 = (30→90d forward vol) / (spot 30d IV)

| FVR | Interpretation | Action |
|-----|----------------|--------|
| < 1.00 | Backwardation — vol term structure inverted | Skip (seller's market) |
| 1.00–1.19 | Neutral | Skip |
| 1.20–1.39 | Mild contango — some buyer edge | Half size |
| ≥ 1.40 | Strong contango — market expects vol to expand | Full size |

The FVR signal works because options at ~10 DTE are priced from the short-end of
the vol surface. When the term structure is in contango (FVR ≥ 1.20), the 10 DTE
options are relatively cheap vs the market's own 90-day implied vol forecast —
creating structural edge for the straddle buyer.

---

## Approved Ticker Lists

### Core List — All 5 Folds (82 tickers)
*Qualified in every test year 2021–2025. Full-size eligible.*

AAL, AAOI, AAPL, AFL, AG, AMC, ANET, AVGO, BAC, BK, BKNG, BSX, CAT, CMG,
COF, COP, COTY, CSCO, CVNA, CVS, CYBR, EOG, ERX, ET, ETN, EW, FCX, FDX, FEZ,
GM, GS, HAL, HCA, HD, IBM, INTU, IYR, JNJ, JPM, KKR, LB, LLY, LOW, LRCX,
MCK, MET, MRK, MRVL, MT, MU, NOV, NTAP, NTES, NVDA, OIH, PAA, PBR, PSX,
RCL, RIG, RRC, SCHW, SLB, STX, SU, SYY, TECK, TEVA, TPR, TQQQ, TSM, UAL,
ULTA, UPRO, URI, VLO, VOD, WFC, WMB, XLK, XRT, YUM

### Extended List — 3–4 Folds (58 additional tickers)
*Qualified in 3 or 4 of 5 test years. Use at 0.5× the tier sizing above.*

ABBV, AGNC, AMAT, AMRN, ASML, AXP, BP, BURL, C, CF, CLF, COST, CVX, DAL,
DB, DE, ED, EPD, FAS, FSLR, FUTU, GD, HPE, INTC, JETS, KLAC, KR, LEN, LVS,
MAR, MARA, MDB, NET, NOK, NTR, NUE, NUGT, OXY, PLTR, PM, PNC, REGN, ROST,
RVLV, SIG, SLV, SMH, STEM, TAP, TJX, TNA, TXN, UNP, WDC, WPM, XHB, XOM, ZIM

---

## Top Performers (FVR≥1.20, full period, ≥3/5 folds)

| Ticker | N | Avg ROC% | Win% | Sharpe | Folds |
|--------|---|----------|------|--------|-------|
| OIH | 24 | +77.4% | 66.7% | 0.582 | 5/5 |
| NOV | 22 | +58.7% | 54.5% | 0.476 | 5/5 |
| AG | 30 | +84.6% | 66.7% | 0.397 | 5/5 |
| RRC | 37 | +32.8% | 54.1% | 0.363 | 5/5 |
| LOW | 86 | +30.7% | 61.6% | 0.361 | 5/5 |
| VLO | 103 | +32.3% | 53.4% | 0.309 | 5/5 |
| CAT | 209 | +24.9% | 52.6% | 0.265 | 5/5 |
| EOG | 76 | +23.7% | 59.2% | 0.266 | 5/5 |
| SU | 82 | +22.4% | 56.1% | 0.280 | 5/5 |

Energy and commodities dominate the top tier. Their options chronically underprice
realized moves due to commodity price sensitivity and geopolitical event risk.

---

## What Not To Do

- **Do not cap profits.** Every profit target tested (50%, 75%, 100%, 150%, 200%)
  reduced OOS Sharpe below baseline. The large wins are the edge, not anomalies.
- **Do not trade without the FVR gate.** Unfiltered straddle buying on all tickers
  has negative Sharpe (−0.003 OOS). The FVR filter is essential.
- **Do not trade tickers not on the approved list.** The per-trade ML model
  (LogReg + LGBM, 10 features) produced AUC ~0.50 across all 5 test years —
  individual trade prediction does not work. Ticker selection is the edge.
- **Do not exceed 3% total open straddle premium.** Simultaneous signals are
  correlated (they all win or lose in a vol spike week).

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `run_long_straddle_study.py` | Full IS study, FVR bucket breakdown, per-ticker leaderboard |
| `run_straddle_ticker_walkforward.py` | Walk-forward ticker validation (generates approved lists) |
| `run_straddle_exit_analysis.py` | Exit rule simulation (cap/floor ROC analysis) |
| `run_long_straddle_model.py` | ML model (LogReg + LGBM) — AUC ~0.50, not actionable |

**Data source:** `silver.option_legs_settled` (3M rows, 987 tickers 2018–2026)
**FVR source:** `silver.fwd_vol_daily` → cached at `data/cache/fvr_daily.parquet`

---

## Research Notes

- **Individual trade ML model failed (AUC ~0.50):** Features (VIX, FVR, IVR, RV20,
  premium_pct) cannot predict whether a specific stock moves in a specific week.
  Straddle outcomes are event-driven and path-dependent at the trade level.
- **Ticker-level signal is real:** Structural alpha exists in tickers where IV
  chronically underprices realized moves. The walk-forward validates this signal
  persists OOS year-over-year.
- **OOS improves on IS for top names:** OIH, AG, VLO OOS Sharpe exceeds IS —
  no overfitting concern for the top tier.
- **2022 note:** High baseline ROC in 2022 reflects the market crash (straddles
  exploded in value across the board). The approved list showed lower 2022 ROC
  than the unfiltered baseline — it filters out high-RV crash-sensitive names,
  which is the correct behavior for a stable strategy.

*Playbook written: 2026-03-22*
*Based on: silver.option_legs_settled, 987 tickers, 2018–2026*

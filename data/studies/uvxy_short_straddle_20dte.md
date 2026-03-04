# UVXY ATM Short Straddle — 20 DTE

**Run date:** 2026-03-02
**CSV output:** `uvxy_straddle_2026-03-02.csv`

---

## Setup

| Parameter | Value |
|---|---|
| Ticker | UVXY |
| Strategy | Short ATM straddle (sell call + put at same strike) |
| Start date | 2018-01-12 (post leverage change: 2× → 1.5× VIX) |
| End date | 2026-02-20 (last available Athena data) |
| Entry day | Fridays |
| DTE target | 20 days |
| DTE tolerance | ±5 days (accepts 15–25 DTE only) |
| ATM selection | Call with delta closest to 0.50; put at same strike |
| Max call delta error | ±0.10 |
| Put delta | Unconstrained (same-strike logic; UVXY skew means put delta ≈ -0.55 to -0.60) |
| Exit | Option `last` price on expiry date (from Athena); fallback to `mid`; 0 for expired worthless |
| Pricing basis | Mid price for P&L; bid price for worst-case |
| Capital / Margin | Reg T: `(0.20 × strike × 100) + (entry_premium_mid × 100)` using ATM strike as spot proxy |
| Delta hedging | None |
| Data source (options) | Athena `options_daily_v3` → MySQL `options_cache` |
| Data source (underlying) | Not used (Tradier historical prices are not on the same scale as Athena option strikes for UVXY due to reverse split history) |

### Why no Tradier underlying prices?
UVXY's historical stock prices from Tradier are on a fundamentally different scale than the Athena option strikes for pre-2024 dates. Athena stores actual historical option strikes (e.g., $12–13 ATM in Jan 2022), while Tradier returns values in the thousands for the same period — the result of their split-adjustment methodology interacting with UVXY's complex reverse/forward split history. Since ATM selection uses delta (not price matching), and all P&L is computed from option mids, no Tradier data is needed.

### Reverse splits handled
UVXY reverse splits within the study window are hardcoded. Any straddle whose holding period spans a split date is **excluded** from statistics (flagged `split_flag=True` in CSV):

| Date | Ratio |
|---|---|
| 2018-09-18 | 1:5 |
| 2021-05-26 | 1:10 |
| 2023-06-23 | 1:10 |
| 2024-04-11 | 1:5 |
| 2025-11-20 | 1:5 |

---

## Results

### Overall (392 closed trades)

| Metric | Value |
|---|---|
| Closed trades | 392 |
| Win rate | 66.1% |
| Avg P&L (mid) | +$42.40 / contract |
| Avg P&L % of premium | +6.6% |
| Avg Reg T margin | $995 |
| Avg ROC | +3.51% |
| Avg annualized ROC | +60.8% |
| Avg breakeven move | 22.4% |
| Split-spanning (excluded) | 11 trades |
| Open (no exit data) | 5 trades |

### Per-year breakdown

| Year | N | Win% | Avg P&L | P&L% | Avg Margin | ROC% | Ann ROC% | Breakeven% |
|---|---|---|---|---|---|---|---|---|
| 2018 | 47 | 61.7% | -$4.84 | -7.1% | $1,206 | -3.17% | -55.8% | 22.4% |
| 2019 | 51 | 52.9% | +$55.65 | +10.2% | $1,274 | +5.06% | +87.8% | 18.1% |
| 2020 | 49 | 75.5% | -$86.14 | -39.5% | $1,593 | -21.38% | -370.5% | 28.9% |
| 2021 | 47 | 68.1% | +$97.77 | +17.2% | $940 | +9.68% | +167.6% | 27.6% |
| 2022 | 51 | 64.7% | +$111.69 | +23.7% | $602 | +13.97% | +243.4% | 23.2% |
| 2023 | 47 | 63.8% | +$17.84 | +11.4% | $442 | +5.01% | +86.9% | 20.0% |
| 2024 | 49 | 71.4% | +$63.64 | +19.1% | $900 | +9.85% | +171.2% | 18.8% |
| 2025 | 46 | 67.4% | +$29.76 | +10.1% | $945 | +5.31% | +91.4% | 20.6% |
| 2026 | 5 | 100.0% | +$523.00 | +77.1% | $1,400 | +36.50% | +634.4% | 18.0% |

*2026 is only 5 trades (Jan–Feb) — treat with caution.*

---

## Key Observations

**Tail risk is the dominant concern.** 2020 illustrates the core short-vol problem on a leveraged instrument: 75.5% win rate, but the losing trades were catastrophic enough to produce an average loss of -$86/contract and -370% annualized ROC. Short UVXY straddles are a positive-expectancy strategy on average (6 of 8 full years are profitable) but carry existential left-tail risk during volatility spikes.

**Breakeven ~22% sounds comfortable but isn't.** UVXY routinely moves 30–50%+ during VIX spikes (March 2020, Aug 2024, etc.). The 22% breakeven understates risk because the distribution is heavily right-skewed.

**2022 is the best year (+$111/trade, +243% ann ROC).** Post-COVID vol regime: elevated but stable realized vol with high implied vol. Ideal for short straddles.

**2018 was slightly negative** — Sep 2018 vol spike right before the reverse split. The 11 excluded split-spanning trades likely would have made 2018 look even worse.

**The strategy may be better suited as a defined-risk structure** (e.g., iron condor or short straddle with OTM long strangle for tail protection) given the 2020 blowup. A pure short straddle on UVXY requires careful position sizing and active management.

---

## Code

```bash
# Run (incremental sync + study):
PYTHONPATH=src python run_uvxy_straddle.py

# Re-sync from scratch:
PYTHONPATH=src python run_uvxy_straddle.py --refresh

# Different DTE:
PYTHONPATH=src python run_uvxy_straddle.py --dte 30

# Custom date range:
PYTHONPATH=src python run_uvxy_straddle.py --start 2020-01-01 --end 2023-12-31
```

**Key files:**
- `run_uvxy_straddle.py` — CLI runner
- `src/lib/studies/straddle_study.py` — generic engine (extensible to other tickers/deltas/DTE)
- `src/lib/mysql_lib.py` — `options_cache` table + sync/fetch helpers
- MySQL table: `stocks.options_cache` (ticker, trade_date, expiry, cp, strike, bid, ask, last, mid, delta, open_interest, volume)

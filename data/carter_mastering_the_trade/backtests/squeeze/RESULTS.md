# Squeeze — backtest results

Run 2026-07-26. Scripts in this directory; `squeeze_lib.py` holds the vectorized indicator.

## Implementation

Standard TTM formulation, validated before use:
- BB = SMA(close,20) ± 2.0·stdev(close,20); KC = SMA(close,20) ± 1.5·SMA(TrueRange,20)
- ON when BB sits inside KC; **FIRE** = ON at t−1, not ON at t
- Momentum = 20-bar linear-regression endpoint of `close − (donchian_mid(20) + SMA20)/2`

Self-tests: linreg endpoint matches `numpy.polyfit` to 1e-15; duration counter exact; fire
triggers once, only on the ON→OFF transition, with correct momentum sign on a synthetic
flat-then-trend series.

## Data

| Test | Universe | Window | Purpose |
|---|---|---|---|
| #1 cross-section | 5,302 names (Minervini cache) | 2025-05 → 2026-07, 295 sessions | current tape, max breadth |
| #2 era-split | 299 liquid names (yfinance) | 2006-01 → 2026-07, 5,171 sessions | regime decay |
| #3 vol expansion | same as #2 | same | the direction-free claim |

Every number is **signal minus same-universe baseline** over the same dates — otherwise you
measure market drift, not signal. Significance is the **date-level t-stat** (mean excess per
date, then stats across ~1,100–5,100 dates); raw n is not independent, since signals cluster.

Universe for #2/#3 is names liquid *today*, so it is survivorship-biased. Baseline differencing
largely cancels that, but absolute return levels are not the deliverable — the excesses are.

## Result 1 — the direction rule has no edge, in any era

`fire + momentum > 0` (Carter's long trigger), excess return vs baseline:

| Era | 5d | 10d | 20d | n |
|---|---:|---:|---:|---:|
| 2006–2011 | −0.47% | −0.56% | −0.53% | 3,627 |
| 2012–2018 | −0.09% | −0.05% | −0.05% | 5,466 |
| 2019–2021 | −0.15% | −0.41% | −0.67% | 2,992 |
| 2022–2026 | −0.26% | −0.25% | +0.06% | 4,399 |
| **All 2006–2026** | **−0.23%** (t=−2.56) | **−0.29%** (t=−2.70) | **−0.26%** | 16,484 |

Negative in all four eras. The 14-month cross-section test (#1, 5,302 names) agrees
independently: −0.10% / −0.10% / −0.10% at 5/10/20d.

**This is not regime decay — there is no era in which it worked.** The best era is 2012–2018
(≈0), which is the tape the 3rd edition was written against. The decay hypothesis this KB was
built around is the wrong frame for this setup.

The momentum filter is mildly **anti**-predictive: `fire + mom<0` beats `fire + mom>0` at every
horizon (+0.04/+0.09/+0.45 vs −0.23/−0.29/−0.26). Taking the *opposite* of the book's direction
rule would have done better — though not significantly so, and that is a data-mined observation,
not a strategy.

## Result 2 — "longer squeeze = bigger move" is contradicted, monotonically

|fwd 10d return| by length of the squeeze that just ended, vs baseline:

| Squeeze length | ratio vs baseline | t | n |
|---|---:|---:|---:|
| 1–5 bars | 1.003 | −0.83 | 16,591 |
| 6–11 bars | 0.987 | +0.60 | 7,359 |
| 12–19 bars | 0.950 | **−3.40** | 3,726 |
| 20+ bars | 0.906 | **−4.22** | 1,763 |

Monotone in the wrong direction: the longer the coil, the *smaller* the subsequent move. The
stated rule is not merely unsupported, it is backwards on this data.

## Result 3 — compression→expansion is real, but the *fire* is not the signal

Direction-free version of the claim. Post-fire vs baseline:

| Metric | signal | baseline | ratio | t |
|---|---:|---:|---:|---:|
| \|fwd return\| 10d | 4.86% | 4.93% | 0.986 | −2.09 |
| fwd realized vol 20d (ann.) | 31.0% | 31.6% | 0.980 | −4.80 |
| **fwd20 RV / trailing20 RV** | **1.152** | **1.100** | **1.047** | **+12.37** |

Two things at once:
- **In absolute terms a fired squeeze is a BELOW-average-volatility name** (0.98× baseline vol).
  Squeezes form in quiet names and they stay comparatively quiet.
- **Relative to its own prior vol it does expand more than typical** (+4.7%, t=12.4). Real, highly
  significant, and present in every era — *strongest* in 2022–2026 (1.067, t=8.8). No decay here.

**But the control kills the trigger.** Bars still *inside* the squeeze show a **stronger**
expansion ratio (1.203 vs 1.100, ratio 1.093, t=+67) than bars where it fired. The predictive
content belongs to the **compression state**, not the release event. That is ordinary volatility
mean-reversion — low vol is followed by higher vol — which is well known and not proprietary to
this indicator. Carter's trigger is a late, noisier read of a condition you could observe directly.

## Result 4 — the expansion is fully priced: no options edge either

The decisive test for an options book. If the squeeze marks a coming expansion, the options should
be cheap relative to what follows. Data: ATM ~30d IV from Athena `silver.options_daily_v3`
(4.07B rows, 2010–2026; calls, |δ| 0.45–0.55, DTE 25–35, ≥2 contracts/day), 348,511 ticker-days,
**9,143 fires with IV**. `VRP = fwd-21d realized vol − IV`, in annualized vol points.

| Cohort | VRP | baseline | diff | t |
|---|---:|---:|---:|---:|
| squeeze FIRED | −0.82 | −0.69 | **−0.13** | 0.24 |
| still IN squeeze | −1.29 | −0.69 | **−0.59** | **−2.64** |
| fired + mom>0 | −0.94 | −0.69 | −0.25 | 0.58 |
| fired, dur≥12 | −0.99 | −0.69 | −0.30 | 0.52 |

**No cheapness anywhere.** Fired squeezes show no significant VRP difference; bars *inside* the
squeeze are significantly **worse** — premium there is relatively expensive, not cheap.

The components show exactly why:

| | IV30 | fwd RV | RV/IV |
|---|---:|---:|---:|
| baseline | 36.46% | 35.76% | 0.982 |
| fired | 35.55% (**−0.91**, t=−3.6) | 34.73% (**−1.03**, t=−3.1) | 0.980 (t=0.10) |
| in squeeze | 34.80% (−1.66, t=−8.8) | 33.51% (−2.26, t=−9.7) | 0.968 |

Options on coiled names **are** cheaper in absolute terms (IV −0.91 vol points). But realized vol
comes in **even lower** (−1.03). The discount you're offered is smaller than the quiet you actually
get. **RV/IV is 0.980 vs 0.982 baseline — statistically indistinguishable (t=0.10).** The market
prices compression correctly, and if anything slightly over-prices it.

By era, the VRP difference is noisy and sign-inconsistent (2010–13 +0.58 on only n=72; 2014–18
−0.10; 2019–21 −0.72; 2022–26 +0.29, t=1.89). Nothing survives. By squeeze duration, no monotone
pattern and nothing significant.

**This closes the last avenue.** The relative expansion found in Result 3 is real but is already
in the price — it does not convert into an options edge.

## What was NOT tested

- **Earnings contamination.** A 30-day window frequently contains a print, inflating both IV and
  RV. Signal-minus-baseline cancels much of this, but if squeezes cluster in the quiet stretch
  *before* earnings the residual bias is real. Excluding windows containing a print is the obvious
  refinement.
- **Actual long-premium P&L.** RV vs IV is the right first cut, but a real straddle is path- and
  gamma-dependent and pays spreads. Actual P&L would be *worse* than these numbers, not better.
- **Skew / non-ATM structures.** ATM calls only; a strangle buyer faces a different surface.
- **Intraday.** Carter trades this on futures/indices intraday with discretion and context. This
  is a daily-bar cross-sectional test of the mechanical rule only.
- **In combination.** The squeeze as a *filter* on an existing trend/leadership setup — rather
  than a standalone entry — is a different and untested question, and a more plausible use.
- **Any discretionary overlay** ("only in the right market"), by construction.

## Reproduce

```bash
PYTHONPATH=src:data/carter_mastering_the_trade/backtests/squeeze .venv/bin/python3 \
  data/carter_mastering_the_trade/backtests/squeeze/run_cache_backtest.py
# fetch_longhistory.py first (yfinance, ~1.3M rows), then:
  ... run_longhistory_backtest.py
  ... run_vol_expansion.py
```

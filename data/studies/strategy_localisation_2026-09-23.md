# Strategy localisation [WL-2b] — do strategies have predictable good stretches? — 2026-09-23

**Verdict: NULL on all three tests · YIELD REFRAME.**

Gabe's question: "Strategy A may be good for one 6-month stretch and B for another; is it wrong to treat all
occurrences over 10 years as equal?"

On 26 strategies with ≥ 24 months of trades:
- A strategy's recent stretch does **not** predict its next month.
- Rotating into the recent winners is **not** reliably better than holding all of them equally.
- **No** strategy has a regime cell (VIX tercile × SPY vs its 200-day) that survives the family-wise charge.

The **pooled average is the right expectation**, with one stated exception: strategies that are regime-gated by
construction, like the certified put sale and the GEX fly, already carry their regime in their rule.

Script: `run_strategy_localisation.py` (pre-registration in the docstring). Log: `data/studies/logs/strategy_localisation.log`.
Data: `strategy_localisation_monthly_2026-09-23.csv`, `strategy_localisation_regime_cells_2026-09-23.csv`.
Local run, ~10 min CPU.

## Data

Monthly series = mean return of trades **entered** that month (≥ 3 trades), from per-trade logs already on disk, with
no re-simulation.
- **Equity (12 families, 2019-10 → 2026-09, R on the house 20-EMA exit):** precision-tier and all breakouts,
  counter-trend long, earnings drift good+muted, in-play up/down movers, bouncy ball, boring-stock violent move, VCP,
  Kell wedge pop, DR-EP, reclaim.
- **Options (14 qualifying, 2010 →, % on risk or credit, net where logged):** 10 Tier C screener spreads, the QQQ
  bull put Bullish_LowIV cell, SPY 1-day iron fly (2× wings, all days), ETF 7-DTE long straddle, UVXY combined, ETF
  45-DTE put-spread roster.
- **Excluded by the ≥ 24-month rule:** the regime-gated Tier A/B cells (SPY bull put Bearish_HighIV fires in 12
  qualifying months; the SPX condors 9–11). They are regime strategies already.

**No look-ahead:** trades hold up to ~60 sessions, so the "trailing 6 months" at month t = entry months t−8..t−3.

## Results

**1. PRIMARY — localisation persistence** (pooled Spearman, strategy-demeaned trailing score vs month-t return):
**ρ −0.011, permutation p 0.77** (null 95% band −0.066 / +0.021). By strategy, the ρ are scattered around zero,
−0.27 … +0.39, with no family pattern. The highest are earnings drift +0.39 (n 50 pairs), Kell +0.23 and GLD bull put
+0.21. The precision-tier breakout is **−0.20**: a good stretch is followed by a *worse* one, if anything.
These are descriptive only.

**2. Rotation** (top 3 by trailing score vs equal weight, in each strategy's expanding-std units):

| window | months | mean diff | t | top-3 beats EW |
|---|---|---|---|---|
| in-sample 2021–2023 | 36 | −0.083 sd | −0.66 | 53% |
| **held-out 2024+** (registered primary) | 33 | +0.180 sd | +2.02 | 70% |

Held-out p vs a random-3 null = **0.023**. That's below the 0.003 bar, and the in-sample sign is **opposite**. It's
consistent with noise, or at most with a 2024+ regime. Not a rotation rule.

**3. Regime sweep** (99 strategy × cell tests; VIX tercile at the prior month end × SPY vs 200-day SMA; 5 cells
populated, "VIX low & SPY < 200" never occurs):
- max |t| **3.53** (in-play down-mover short, better in VIX-low / SPY>200)
- **family-wise permutation p 0.36** (null max |t| p50 3.23, p99 5.92)
- **0 cells** clear the p < 0.003 threshold (|t| ≥ 6.30)

⚠ Bug found and fixed before the verdict: the first run summed two numpy booleans (a logical OR), so the VIX tercile
could only be 0/1 and VIX-high months were merged into "mid". Tests 1–2 were unaffected; test 3 above is the
corrected run.

## Reading

- **Localisation exists in the returns but it is not predictable.** The breakout book's paying months are real
  (top 8 of 83 months = 68% of positive R), but neither a strategy's own recent history nor a simple observable
  regime says which months those will be. This extends the 21-day result (`trailing_regime_validation.md`) to a
  6-month lagged window and to the cross-section of strategies.
- **So pooling is correct for decisions.** The pooled mean is what a trader gets without an ex-ante regime call.
- **Where regime conditioning DOES work here, it is built into the rule and tested as such:** the GEX positive-gamma
  fly (0.0% → +5.8%, t 3.4) and the bearish-high-IV put sale. Those were single pre-registered splits with a mechanism,
  not a sweep.

## Power caveats (why this is NULL, not "proven absent")

- About 84 months per equity family, 5 populated regime cells, and cell sizes of 6–93 months: only a large effect
  could clear a family-wise bar. The regime sweep is **UNDERPOWERED** for modest regime effects. The null p99 max |t|
  of 5.92 shows how much searching 99 cells costs.
- Monthly means of R and % ROC mix units; all tests are within-strategy or in strategy-std units, never raw levels.
- VIX × SPY-trend is one regime grid. Others (gamma sign, breadth, rates) weren't swept; each would be a new
  registered test.

## What would change the verdict

A pre-registered, mechanism-backed regime split for a *specific* strategy (as the GEX fly was). A sweep over all
strategies × cells can't reach the bar at this sample size.

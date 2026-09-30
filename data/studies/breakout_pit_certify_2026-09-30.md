# House breakout on a point-in-time universe (2026-09-30)

**Verdict: NOT CERTIFIED. PRIMARY FAIL (UNDERPOWERED), plus a SURVIVORSHIP finding · YIELD MECHANISM.** On the point-in-time S&P 500 the precision tier does not beat same-date non-tier breakouts at the bar. Neither the tier nor the plain breakout beats a random member. The tier's apparent edge over random names on the survivor version of the same universe comes from selecting the universe with hindsight.

- Pre-registered in the docstring of `run_breakout_pit_certify.py` and committed before the run (f719a3c). Log: `logs/breakout_pit_certify.log`. Post-hoc diagnostic: `logs/breakout_pit_certify_diag.log`.
- The spec was changed at pre-registration: chain_spot is close-only, and the tier needs H/L/volume. Instead: the point-in-time S&P 500 (2026 list with the Wikipedia change log reversed; yfinance OHLCV including removed names). Member coverage with prices is 70% in 2010, rising to 97% in 2024. The GAP gate is dropped because the cache has no opens.
- House process: close entry, day-low stop floored at 2% and judged on the close, EMA20 exit, 60 sessions, 10 bp a side.

| cell (PIT S&P, 2010-01 to 2025-04) | n | result | t |
|---|---|---|---|
| **PRIMARY** TIER − NON-TIER, same date | 154 dates / 310 tier | **+1.50pp** (TIER −1.08% vs NON −2.58%) | **+1.90**. Halves +1.09/+1.62, 11/14 yrs, but 2023+ −0.80 |
| (d) same in R | | +0.40R | +1.82 |
| (a) TIER vs 3 random same-date members | 310 | −0.73pp | −1.20 |
| (b) all base breakouts vs random members | 2,391 | **−0.87pp** | **−3.71**, both halves negative |

**Post-hoc diagnostic (not pre-registered).** Same code and definitions, universe varied:

| universe | TIER %/trade | TIER vs random | base vs random |
|---|---|---|---|
| PIT S&P (members on the day) | **−1.21** | **−0.73pp, t −1.20** | −0.87pp, t −3.71 |
| survivor: today's S&P members, liquid panel | **+2.61** | **+2.37pp, t 2.30** | +0.24pp, t 0.81 |
| same, from the yfinance cache (method check) | +2.61 | +2.36pp, t 2.22 | +0.16pp, t 0.53 |
| survivor liquid panel, all 875 names | +0.13 | −0.29pp, t −0.61 | −0.37pp, t −2.08 |

- **The cache reproduces the panel**, so this is not a data bug.
- **Survivorship moves the tier by about 3.8pp per trade** on large caps. A name that became an S&P member later was, by construction, a winner, and the survivor universe includes its breakouts from *before* it was a member. That is look-ahead, not selection skill.
- **Not covered:** non-S&P mid and small caps, where most house breakouts fire (875 survivor-panel names vs 334). A point-in-time mid/small-cap universe with OHLCV does not exist here; chain_spot has closes only.

**What it means for the book now.**
- The house breakout stays **uncertified**, and the one universe where we *can* remove survivorship shows no selection edge.
- Keep it at token size and treat it as execution around discretionary picks, per "conviction selection IS the strategy". It is not a system.
- The survivor-panel positives in §4 all inherit this bias to an unknown degree.
- The next step, if wanted, is building a point-in-time OHLCV panel for non-S&P names (Polygon grouped daily; the free tier blocks it today).

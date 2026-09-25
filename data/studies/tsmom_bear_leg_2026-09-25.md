# TSMOM (trend-following) as the book's bear leg — 2026-09-25

Script: `run_tsmom_bear_leg.py` (pre-registration in its docstring, committed before the run).
Logs: `data/studies/logs/tsmom_bear_leg.log`, CSVs `tsmom_bear_leg_2026-09-25.csv`, `tsmom_bear_leg_overlay_2026-09-25.csv`.

## Verdict: NOT A CANDIDATE · return edge RETRACTED as asset drift · MECHANISM (timed insurance, pays in slow bears)

**Primary (multi-asset TSMOM, 12-month sign, inverse-vol; VFINX/VGTSX/VUSTX/VFITX + GLD/DBC/UUP), 1998-01 → 2026-08, 344 months, net:**
- Standalone **+0.35%/mo, t 4.12**, halves +0.53 / +0.18, 24/29 years, beta to S&P −0.05. That passes the
  pre-registered return bar *against zero*.
- ⛔ **But against the obvious control, it is beta to a balanced long book.** The same assets held **long** with
  inverse-vol weights earn **+0.49%/mo (t 6.76)**; TSMOM minus long-only = **−0.13%/mo, t −1.43** (halves −0.10 / −0.17).
  The permutation null (shuffled signal months) gives p 0.028, which is still not |t| ≥ 3. **The timing is a cost
  in normal years, not a source of return.** This check was not pre-registered; it was run after the t 4.12 came back
  because of the house rule that a clean result is a bug until proven otherwise. Read the row as RETRACTED, not PASS.
- **Where the timing pays (vs long-only):** 2001 +9.9, 2002 +8.3, 2008 +9.8, 2022 +13.3 pp; it costs in almost every
  other year (≈ −1.6%/yr on average). That is the profile of insurance with a premium.
- **Crisis episodes:** positive in all 4, with each well above a beta-equivalent S&P short: 2000-02 **+29.5%** (the
  sector-momentum sleeve LOST −10.3% here), 2008 +16.1%, 2020 crash +0.7% (too fast for a monthly signal), 2022 **+13.0%**.

**Overlay (2018-04 → 2026-02, 50% of book vol), fails bar (iii):**
- Full book: maxDD 24.97 → 25.56 (worse); Sharpe +0.08. Mean in the book's 10 worst months +0.07%.
- No-straddle book: maxDD 38.1 → 34.8, Sharpe +0.18. **But the DE-MEANED sleeve RAISES maxDD (+4.4)**, so the cut
  comes from the sleeve's positive mean, not from hedging (same defect as the RV sleeve). The sector sleeve is still
  the only one that survived de-meaning.

**Family A (index short-or-flat, 6 cells):** no return edge (−0.29 to +0.02%/mo, t ≤ |1.4|). The timing beats a same-vol
always-short decisively on SPY and QQQ (diff t +3.6 to +4.0), with large crisis payoffs (SPY sma10: 2000-02 +43.5%,
2008 +61.5%), but SPY sma10 made 0.0% in 2022 and every cell bleeds in bull years (4–6 of 29 years positive).
Not overlay-tested (not pre-registered).

## What it taught
- **MECHANISM:** trend timing on its own is a *priced* hedge. It pays in slow bears (2000-02, 2008, 2022), misses a fast
  crash (2020), and costs ≈ 1.6%/yr against holding the assets. It is the complement of the sector sleeve on 2000-02, the
  only episode where that sleeve failed.
- **METHOD:** a multi-asset sleeve must be scored against the same assets held long, not against zero. A t 4 against zero
  here was mostly the 1998–2020 bond bull market.
- **Open decision for Gabe (not a test):** if you want a bear leg, the evidence says you have to *pay for one*. The two
  candidates are the sector 12-1 sleeve (hedges 2008/2020/2022, costs ~0.14 Sharpe) and index TSMOM short-or-flat
  (hedges 2000-02/2008, bleeds in bull years). Neither earns its keep on return.

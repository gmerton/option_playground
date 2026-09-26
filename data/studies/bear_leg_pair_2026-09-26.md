# Bear-leg pair: sector-momentum 12-1 spread + multi-asset TSMOM (2026-09-26)

`run_bear_leg_pair.py` (pre-registered in its docstring before the run). Log: `logs/bear_leg_pair.log`; table
`bear_leg_pair_2026-09-26.csv`. Parents: `sector_overlay_test_2026-09-24`, `tsmom_bear_leg_2026-09-25.md`.

**Question.** The two sleeves fail different bears (sector lost 2000-02; TSMOM missed 2020). Does the equal-vol pair
cover all four and cut more drawdown than either alone?

## Verdict: NOT A CANDIDATE by the pre-registered bar (fails iii; iv BLOCKED) · MECHANISM confirmed · METHOD

| criterion | result |
|---|---|
| (i) positive in all 4 episodes, beats beta-equivalent short | **PASS** — 2000-02 +28.5, 2008 +31.5, 2020 +7.5, 2022 +26.9 (%) vs beta-short 6.8 / 10.5 / 3.2 / 2.7 |
| (ii) de-meaned pair cuts proxy-book maxDD more than either alone (50% vol) | **PASS** — −21.1 pts vs sector −9.3, TSMOM −15.1 |
| (iii) beats a same-vol SPY short on maxDD; mean in book's 20 worst months > 0 | **FAIL** — −23.7 vs −33.6 (worst-20 mean +3.09%/mo passes) |
| (iv) house-book overlay | **BLOCKED** — `data/cache/rsi_straddle.parquet`, `rsi_putspread.parquet` and their sources (`etf_condor_recon`, `straddle_recenter/leg_decomp`) were deleted from the untracked cache and have no backup |

Proxy book = VFINX total return, 2000-01 → 2026-08, 320 months, book maxDD 67.1 (cum-sum %), Sharpe 0.60.
corr(S, T) = +0.37. Pair carry vs zero +3.3%/yr, but that is TSMOM's bond/gold drift (the parent's METHOD note:
vs the assets held long TSMOM costs ~1.6%/yr), so the de-meaned rows are the honest hedge measure.

## ⚠ The control that failed it is degenerate on this book (found after the run; verdict NOT changed)

A same-vol short of SPY laid over a SPY book is simply **deleveraging**: it cuts maxDD 33.6 by halving the return
(0.76 → 0.38 %/mo, Sharpe unchanged 0.60). The de-meaned pair cuts maxDD 21.1 (31%) with the return and Sharpe
unchanged (0.76 %/mo, 0.60). Delevering by 31% to get the same DD cut would give up ~0.24 %/mo. So per unit of
return given up the pair is the better hedge. This is an EXPLORATORY reading; the control was declared, so the bar
stands. The control was inherited from the parent overlays, where the book's correlation with SPY is 0.22 and a SPY
short is a genuine alternative; on a SPY proxy book it is not. METHOD: on an index proxy book, the control must be
delevering at matched return cost, not a same-vol index short.

## Exploratory
- Trailing-36m vol sizing (no look-ahead in size): same picture, de-meaned DD cut −22.2 (window starts 2002).
- Sector + SPY 10-month SMA short-or-flat: larger DD cut (de-meaned −29.4) but 0.0% in 2022 on the SMA leg and a
  bleed in bull years (8/27 years positive).

## What it settles / next
- **MECHANISM:** the complementarity is real — the pair is the only construction positive in all four bears, and
  it hedges more than either leg per unit of vol.
- **Open:** (iv) on the house book needs the RSI study caches rebuilt (Athena; not re-run here). Whether to re-test
  (iii) with a matched-return delever control is a new pre-registration, not a re-read of this one.

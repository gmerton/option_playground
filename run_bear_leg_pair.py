#!/usr/bin/env python3
"""
BEAR-LEG PAIR: sector-momentum 12-1 spread + multi-asset TSMOM, equal-vol, as one hedge sleeve (pre-registered
2026-09-26, before any code or run; Gabe: "I don't think we have any strategies that will help us in a sustained
bear market"). ⛔ NOT RUN -- pre-registered only. Queued in TEST_INDEX section 10.

WHY NEW. Each sleeve was tested alone, never together:
  sector_overlay_test_2026-09-24  sector 12-1 K3 spread = the ONLY sleeve whose drawdown cut survives de-meaning
                                  (a real hedge); pays 2008 +25.4 / 2020 +16.0 / 2022 +30.8, but LOST -10.3% in
                                  2000-02; costs ~0.14 Sharpe on the book.
  tsmom_bear_leg_2026-09-25       multi-asset TSMOM (family B) = positive in all 4 episodes (2000-02 +29.5, 2008
                                  +16.1, 2020 +0.7, 2022 +13.0) but a priced hedge (~-1.6%/yr vs the assets held
                                  long) whose overlay cut did NOT survive de-meaning.
  The two fail in different places: sector misses the slow 2000-02 bear, TSMOM misses the fast 2020 crash. The
  question is whether the PAIR covers every bear at a lower cost per point of drawdown than either sleeve alone.
  The 2000-02 episode is outside the house book's window (2018-04 ->), so the complementarity can only show on a
  long-history proxy book -- that is the PRIMARY here, and the house-book overlay is the confirmation.

SLEEVES (built by the existing, already-audited functions; nothing re-fit)
  S   run_sector_momentum_spread.spread_series(12, 3): net of 20 bp + borrow (the sector test's PRIMARY).
  T   run_tsmom_bear_leg.family_b(): 12-month sign, inverse-vol, 7 assets, 5 bp/side + 0.25%/yr borrow (its PRIMARY).
  T_A run_tsmom_bear_leg.family_a(SPY, "sma10"): index short-or-flat. EXPLORATORY partner only.
  PAIR = S / sd(S) + T / sd(T), rescaled to the target vol. FIXED 50/50 risk weights declared now -- no weight
  search (a search over weights on ~5 bear episodes would fit the episodes). Vol scaling on the full-sample sd, as
  in both parent overlays (a mild look-ahead in SIZE, not in sign; EXPLORATORY: trailing 36-month sd instead).

PRIMARY (long history)  proxy long book = VFINX total return (S&P 500), monthly, 2000-01 -> 2026-08 (~320 months;
  first month the sector sleeve has a 12-1 signal). Overlay each of {S, T, PAIR} at 50% of the proxy book's vol.
  Episodes (as tsmom_bear_leg): 2000-03->2002-09, 2007-11->2009-02, 2020-02->2020-03, 2022-01->2022-10.
SECONDARY (house book)  exactly as the parent overlays: run_put_overlay_study.book_series() (straddle + bull put +
  breakout) and the no-straddle book, 2018-04 -> 2026-02, sizes 25 / 50 / 100%, PRIMARY 50%.

CONTROLS (declared now)
  (1) each sleeve ALONE at the same vol -- the pair must beat BOTH, or it adds nothing over the better one;
  (2) the DE-MEANED pair (mean set to 0) -- the drawdown cut must be hedging, not the sleeve's own drift (the
      defect that sank the RV sleeve and TSMOM alone);
  (3) a same-vol SPY (VFINX) SHORT -- is the pair better than simply shorting the index?

BAR  (a hedge screen, not a return test; the pair has no return edge to certify -- neither parent does)
  The PAIR is a CANDIDATE only if ALL hold:
  (i)   positive in all 4 episodes standalone, and beats the beta-equivalent index short on aggregate across them;
  (ii)  PRIMARY proxy book at 50%: the DE-MEANED pair cuts maxDD by more than the de-meaned S alone and the
        de-meaned T alone (hedging efficiency: the only reason to hold two sleeves);
  (iii) PRIMARY proxy book at 50%: maxDD falls more than with the same-vol SPY short, and the pair's mean in the proxy
        book's 20 worst months > 0;
  (iv)  SECONDARY house book at 50%, BOTH books: maxDD falls and the de-meaned pair still cuts maxDD (Sharpe may
        fall -- it is insurance -- but report dSharpe per point of maxDD cut vs S alone; the pair must not be the
        more expensive of the two).
  Also reported, not gated: the carry (standalone mean, %/yr) of S, T, PAIR over 2000-2026 -- that IS the premium.
  Multiple testing: one primary pairing (S+T), one primary size (50%). S+T_A and the other sizes are exploratory.
  POWER: ~4 bear episodes in 26 years. A pass is a screen for a paper-tracked sleeve, never an adoption; a fail at
  (ii) means "hold the better single sleeve", not "no hedge exists".

READ  pass -> the pair is the bear leg to paper-track alongside the momentum sleeve, sized by the carry Gabe is
      willing to pay. Fail at (ii) -> the sector sleeve alone remains the only de-meaning-robust hedge.
      Prior: the S-T correlation is low (they fail in different episodes), so (i) is likely to pass; (ii) is the
      real question.

Local vs cloud: local (yfinance monthly closes + two existing sleeve builders; minutes of CPU, no Athena).

Usage (when approved): PYTHONPATH=src:. .venv/bin/python3 run_bear_leg_pair.py > data/studies/logs/bear_leg_pair.log
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-26, not built/run yet. See the docstring and TEST_INDEX section 10.")

# QQQ intraday project, idea 1: noise-band intraday momentum replication (2026-09-17)

`run_intraday_pull.py` (IBKR 1-min RTH bars, resumable; QQQ / SPY 2007-01 ->, TQQQ / SQQQ 2010-02 ->, ~1.9M bars each, `data/cache/intraday_hist/`, gitignored) and `run_noise_band.py` (Zarattini-Aziz-Barbon 2024 rules as recalled: 14-day per-minute noise band around max/min(open, prior close), decisions at HH:00/HH:30, VWAP trailing stop, flat at the close; conservative next-bar fills). 2026 held out throughout.

**Engine calibration on SPY, paper mode** (compounding, vol-target sizing to 4x, paper costs), 2007-01 .. 2024-03: **17.5%/yr net, Sharpe 1.18, maxDD -29.8%** vs published 19.6% / 1.33 / ~25%. Close enough, with the conservative fills accounting for most of the gap, so the rule recollection is right and the QQQ numbers can be trusted.

**QQQ in Gabe's game** ($10,000 fixed every session, 1x, flat overnight, IBKR $0.005/sh with $1 minimum + $0.005/sh slippage), 2007-01 .. 2025-12, 4,674 sessions:

| | ann | vol | Sharpe | t | maxDD (of the $10k) |
|---|---|---|---|---|---|
| strategy NET | **+2.5%** | 9.0% | **0.28** | 1.2 | **-48.7%** |
| strategy gross | +7.0% | 9.0% | 0.78 | 3.4 | -29.4% |
| hold open -> close, 1x | +6.4% | 18.1% | 0.35 | 1.5 | -59.3% |
| buy and hold | +16.8% | 22.4% | 0.75 | 3.2 | -70.0% |

Trades 60% of days, 0.86 round trips/day, 40% winning days, avg win +0.62% / avg loss -0.39%, cost drag 4.5%/yr (the $1 minimums on ~16 shares). Long-only: +2.2%, Sharpe 0.36, maxDD -19%.

By year (net): 2007 +6.9 · 2008 +8.6 · **2009 -21.9 · 2010 -13.5** · 2011 +0.4 · 2012 +3.7 · 2013 -4.9 · 2014 +2.2 · 2015 +2.0 · **2016 -8.6** · 2017 -1.2 · **2018 +27.4** · 2019 -1.6 · 2020 +2.2 · 2021 +3.0 · **2022 +14.5 · 2023 +13.1** · 2024 +6.5 · 2025 +7.4.

Sensitivities: $100k capital 4.6%/yr, Sharpe 0.51 (costs 2.5%/yr, still -42% fixed-capital DD). 2018-2025 only: **9.2%/yr, Sharpe 0.98, maxDD -11.7%** -- the interim read from the first 3 years of data was this window. QQQ paper mode (4x vol-target, compounding) 12.1%/yr, Sharpe 0.81. SPY in the game: 3.5%/yr, Sharpe 0.46.

**Reading.**
1. In the game as set (fixed $10k, 1x, IBKR minimums) the strategy makes ~2.5% a year with a 9-year dead stretch (2009-2017, -49% of the stake) -- no. The published headline needs compounding and up to 4x vol-target leverage; at 1x on SPY it is 3.5%/yr.
2. The edge, such as it is, is 2018+ (Sharpe ~1, +9%/yr), exactly the NQ replication's warning ("flat 2010-2017"). Gross of costs it is a real but modest Sharpe 0.78 phenomenon; costs at this size take two thirds of it.
3. It is not a path to large returns and it is not a QQQ vehicle worth capital at $10k. It IS a working, calibrated engine + 20 years of 1-min data for the rest of the project (idea 2: TQQQ/SQQQ close-rebalancing flow; parked ideas 3-6 in memory).

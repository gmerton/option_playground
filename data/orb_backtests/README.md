# ORB backtests — knowledge base

Opened 2026-09-23 as a **false-negative check on our opening-range-breakout nulls**: creator videos that
either backtest an ORB or sell a fix for it, read against what we have actually run. Skeptic mandate as in
every creator KB here: record the claims, test what is testable against our own data at real fills, score
0–5; a claim without a track record is a hypothesis.

Layout: `videos/<upload-date>_<id>/` (meta.json, transcript.txt, notes.md). Related KB:
[`../fit_mom_trader/`](../fit_mom_trader/2026-07-24_orb_mistakes_review.md) (the retest remedy, 3/5).

## Leaderboard

| video | score | one line |
|---|---|---|
| [Trading Steady — ORB breakout + pullback, 5-yr backtest (2025-09-27)](videos/2025-09-27_ZF8uKPqAu8M/notes.md) | **3/5** | Publishes a **null** from his own S&P 500 backtest of the retest remedy (n 130, flat 2020–22) and diagnoses it as we did: waiting deselects the runaways. No costs, no control, in-sample target sweep; his *baseline* ORB profitability is asserted, not shown |
| [Raghee Horner — why most traders fail the ORB (2026-07-02)](videos/2026-07-02_T06ayy3-zs8/notes.md) | **2/5** | Fit Mom's diagnosis (don't chase the break) plus a 38–62% retreat entry, a 30-min range and a stack of context filters; zero evidence; "most breakouts reverse" is contradicted on our panel (39% VWAP / 14% midpoint retest); cites 3% risk per trade |

## What our ORB evidence actually covers (verified at TEST_INDEX §5, 2026-09-23)

| test | verdict |
|---|---|
| ORB9 break vs a random minute, same name-day (`alert_triggers_2026-09-23`) | **INVERTED** — +0.351% vs +0.775%, −0.425pp, t −8.50, both halves |
| ORB retest vs break, VWAP / midpoint arms (`orb_retest_vs_break_2026-09-23`) | **FAILS as a strategy** (−0.601pp / −0.695pp vs random, t −5.56 / −4.92); conditional on firing, beats random (+0.32pp t 4.45 / +0.58pp t 6.68) |
| Stage A ORB9 intraday arms, 1R/2R targets (`stage_a_intraday_2026-09-18`) | **FAIL** — ORB9 −0.25R, t −5 to −12; targets ≈ random minute |
| ORB15 vs buying the close (`entry_study_2026-09-17`) | **FAIL** — −1.22pp, t −3.4 |
| OR-high level trigger, break and hold (`level_trigger_test_2026-09-21`) | **NULL 0/12** |
| ORB9 stop floor 0.6 ADR | **ADOPTED (mechanics only)**, no edge |

⚠ **Every one of these is single-name equities (curated or layer-2 names), 1-min bars, 2026-02 → 09.**
No ORB has ever been run on an index here, although we hold SPY and QQQ 1-min RTH bars from 2007
(`data/cache/intraday_hist/`). The nearest index work: noise-band intraday momentum **MARGINAL** (gross
Sharpe 0.78, net 2.5%/yr at $10k, dead 2009–17), its negative-gamma arm **UNDERPOWERED** (t 2.92), and the
ICT sweep-fade on QQQ **FAIL** (t −8.2).

## Does anything here overturn our ORB nulls?

**No.** Both videos agree with the single-name nulls: Trading Steady's own backtest fails the retest
remedy for the reason ours does (the break earned +1.264% on the days that never came back), and Raghee's
remedy is the midpoint arm we already ran. What they **refine** is the scope: the claims are about index
futures / the S&P index, and our ORB nulls say nothing about an index. That is a gap, not a hidden positive.

## ⭐ Single best follow-up (not queued, not run)

**Index ORB on SPY and QQQ, with controls that isolate direction and timing.**

- **Data:** SPY + QQQ 1-min RTH, 2007-01 → 2025-12; 2026 held out.
- **Primary cell (pre-register):** 15-min OR (09:30–09:45); signal = first 15-min bar closing outside the
  OR at or before 12:00; enter at the next bar's open, **both directions**; stop = opposite side of the OR;
  exit at 1.5R or 15:59. (Trading Steady's baseline as stated.)
- **Secondary cells (charged):** 30-min OR (Raghee); hold-to-close exit; ATR range filter fixed in advance
  (skip OR / ATR14 < 0.15 or > 0.60); midpoint-retest entry as a cross-check of the single-name result.
- **Controls:** (a) **same entry minute, opposite direction** — the ORB on an index is a direction call,
  and this nets out drift; (b) **same direction, random minute 09:45–12:00** — the control that inverted
  ORB9; (c) always-long open→close.
- **Costs:** 1bp per side + $0.005/sh; stop fills one tick through; bar touching stop and target = stop.
- **Bar:** |t| ≥ 3 vs control (a) on % return (not R), both halves the same sign, per-year table with 2020
  and 2022 shown, Šidák over all cells (≈ 2 instruments × 5 cells → |t| ≥ 2.8, house 3.0 governs).
- **Prior:** ~25% pass. The noise band (a better-specified cousin) is only MARGINAL net of costs and dead
  2009–17; a 15-min-bar ORB with a 1.5R target is cruder.
- **Effort:** ~½ day — `run_noise_band.py` engine and the 1-min caches exist.

Cheaper and lower-prior: the **context hybrid** from Raghee (buy the break when price is above the prior
close with a rising 5-min trend, else wait for the midpoint retreat) as a 1–2 h re-cut of
`orb_retest_vs_break_2026-09-23.csv` joined to the alert metadata. Expected to discriminate little, since
ORB9 names are mostly gap-up.

> ⚠ Correction (2026-09-23, parent review): "no index ORB has ever been run" overstates the gap. The ledger has index
> intraday breakout tests: QQQ noise-band momentum (Zarattini–Aziz–Barbon replication, MARGINAL, 2.5%/yr) and its
> negative-gamma cell (UNDERPOWERED, t 2.92). A plain 15-min SPY/QQQ ORB is still untested, but as a close relative of
> those, not a blank spot.

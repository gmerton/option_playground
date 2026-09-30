# Haber setups: LAUNCHPAD and FIRST 50-DAY PULLBACK in an early-stage base (2026-09-29)

## Pre-registration (written BEFORE any run; do not edit this section after the results)

**Source.** `data/traderlion/videos/interviews/2026-09-29_koi4YL-hTUc/notes.md` (Ross Haber, 2.5/5). Queued by Gabe 96911ca.
**Common.** `pattern_test.run_daily` harness on `liquid_panel_2009` (eligibility ADDV ≥ $50M, price ≥ $5), signals
2010-01 → 2026-06, **entry at the signal close**, hold cap 60, harness fills/costs. Each setup is run against BOTH
controls: **xname** (random eligible names same date, same stop %) and **post** (same name, random session in the next
20). Split for halves = 2018-01-01. A name can fire again only after 20 sessions. **The exit arm is fixed per setup
below (no arm search is charged because none is done).** PASS per setup = paired edge vs xname (PRIMARY, selection)
**t ≥ 3.2** (two setups → Šidák-2), both halves > 0; vs post reported. Two looks total.

**H1 LAUNCHPAD.** MAs on the close: SMA10, SMA21, EMA23, SMA50, EMA65. spread = (max − min of the five) ÷ close.
Tight = spread ≤ its own trailing-252-session 10th percentile on any of the prior 10 sessions. Signal day: close > all
five MAs while the prior close was not; all five MAs above their level 5 sessions earlier; close above the declining-
tops line (DTL) = the line from the highest high of sessions t−120…t−10 to the highest high between that point + 10
sessions and t−3 (must be lower; no valid second point → no signal). Stop = min(lowest of the five MAs, close × 0.98),
judged on the close. **Exit arm: ema20** (house trail).
**H2 FIRST 50-DAY PULLBACK.** Stage-2 break at day b: close > the prior 252-session high, with no such close in the
prior 126 sessions; SMA50 > SMA50 ten sessions earlier; 126-session return in the top 30% of eligible names that day.
Signal = the FIRST session in b+3 … b+60 whose close is within [0.98, 1.01] × SMA50 (one per break). Stop = SMA50 × 0.975,
judged on the close. **Exit arm: stop_hold** (hold to the 60 cap or the stop; the ema20 arm would exit a pullback on
day one because price sits below the 20 EMA). Also reported: the same names' breakout-day entry (the house breakout
entry at b, same exit) vs the pullback entry.
**Prior.** H1 low–moderate (RMV tightness gate NULL; VCP NULL). H2 low–moderate (EMA-pullback entries t ≤ 1.4, retrace
NULL), but first-touch-after-a-stage-2-break is untested. Local, ~1–1.5 h total.

---

## Results (run 2026-09-29, after ec69b3b; `run_haber_setups.py`, summary `.log`, harness detail `logs/haber_setups.log`)

**Verdict: both NULL on the pre-registered bar. MECHANISM: in stage-2 names, the pullback entry is much better than the
breakout-day entry — but neither beats random names.**

| setup | exit arm | n | mean R | paired edge vs **xname** (PRIMARY) | t (bar 3.2) | halves | vs post (edge, t) |
|---|---|---|---|---|---|---|---|
| **Launchpad** | ema20 | 2,917 | +0.10 | **+0.101R** | **1.01** | +0.17 / +0.07 | +0.107, **t 2.38** (p_search 0.031) |
| **First 50-day pullback** | stop_hold | 1,804 | −0.26 | **−0.118R** | **−1.49** | −0.12 / −0.12 | +0.020, t 0.61 |
| stage-2 breakout-day entry, same names (reported) | stop_hold | 1,804 | −0.48 | **−0.489R** | **−6.29** | −0.49 / −0.49 | — |

- **Launchpad:** right sign on both controls and both halves; the timing edge vs a later day in the same name (t 2.38)
  is stronger than the selection edge (t 1.01). Short of the bar → NULL (a timing lead, UNDERPOWERED at best).
- **First 50-day pullback:** loses slightly to random names and ties a later day in the same name. "Almost always a
  buy" is not supported.
- **The breakout day itself (secondary, not pre-registered as a test):** buying the first 52-week-high break after
  ≥ 6 months in the same names is −0.49R vs random names (t −6.3, both halves) — the ledger's standing finding
  ("we select well, we enter badly": the breakout entry buys too high) in a new population. Waiting for the first
  50-day touch recovers ~0.37R of that, which is Haber's point about entry — but it only gets back to ≈ random.

**What it means for the book now.** Nothing to add. The one live implication is a reinforcement: don't buy the day of
a fresh stage-2 / 52-week-high break; if a name is wanted, the first 50-day pullback is the better of the two entries.

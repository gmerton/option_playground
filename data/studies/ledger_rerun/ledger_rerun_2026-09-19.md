# Pattern-ledger re-run with honest controls — 2026-09-19

_`run_ledger_rerun.py` (daily, 19 patterns) · `run_stage_a_score.py --control post|xname` · `run_bouncy_ball_intraday.py
--control post|xname` · logs in `logs/` · table `rerun_2026-09-19.csv` · 23 new rows in `../pattern_ledger.md`
(same names as the originals, note begins "RERUN")_

## Why

The harness's original control (`month`: random session, same name, same calendar month) draws sessions from
*before* the signal in a name known to be about to fire. On the house breakout it earned +1.70R, three times
the signal ([precision_tier_control_2026-09-19.md](../breitstein_tests/precision_tier_control_2026-09-19.md)).
Every ledger row before that note used it, and Stage A's random-minute control had the same pre-trigger
look-ahead. So "0 for 25, random beats the pattern" needed to be re-scored against controls that cannot see
the future:

- **post** — same name, random session (minute) in the 20 sessions (rest of the day) AFTER the signal. *Timing*:
  is the signal day/minute better than a later one in a name that fired?
- **xname** — random eligible OTHER name, same date (minute), same stop %. *Selection*: does the name matter?

Same arms, same R cap (10), same split (2023-01-01), same |t| ≥ 3 bar. Honest bar = beats BOTH controls,
positive in both halves, |t| ≥ 3.

## Verdict

**Still 0 for 23. The month control was wrong in both directions, and the old "edge" column was mostly the
control's error — but no pattern crosses the bar once the control is honest either.**

1. **Continuation patterns had their control inflated.** Breakouts, in-play movers: the month control earned
   +0.14 to +0.21R (pre-signal days in a name about to break out); the honest controls earn −0.17 to +0.14R.
   The patterns' own means did not change; their "edge" moved from −0.37…−0.49 to −0.09…+0.11.
2. **Reversal patterns had their control deflated.** Boring/violent, counter-trend long: the month control
   earned −0.48 to −0.86R (pre-signal days in a name still falling); honest controls earn −0.05 to −0.19R. The
   old "+0.33 to +0.45R edge over control" for those cells was entirely the control. Honest edge −0.09 to +0.03.
3. **Intraday triggers ≈ a random later minute.** Stage A's UR/ORB9/LVL: on every intraday arm the trigger is
   within ±0.03R of a random later minute (post) or a random other watchlist name at the same minute
   (xname). The swing-hold arm's gap now flips sign with the control (UR −0.07/−0.29, ORB9 −0.23/+0.15, LVL
   −0.25/+0.09): noise around zero, dominated by the name-day pool's drift. Conclusion unchanged: the trigger
   carries no information; don't fund Stage B.
4. **Bouncy ball short**: daily −0.08R (was reported −0.34 on the t1R arm; best arm is now stop_hold), edge
   +0.12 post / +0.07 xname, t 0.4, halves +0.08 / −0.17 → fail. Intraday: every arm −0.41 to −0.67R on the signal
   AND on both controls (edge −0.07 to +0.05) → shorting these name-days loses whatever the trigger; the
   universe (long-side in-play names) is the reason, not the pattern.
5. **Closest to the bar**: earnings drift after a good+MUTED reaction — +0.27R stop_hold, beats post by +0.25
   and xname by +0.26, both halves positive (+0.19 / +0.33), **t 2.65 on n 437**. Fails on t only. Second:
   delayed bump after good+MUTED (+0.25R ema20, +0.18 / +0.30 vs controls, t 1.6, n 335). Both were "fails"
   under the month control because that control was +0.11 / +0.05 vs their honest +0.03 / +0.07 — the
   earnings-drift cohort is the one place the re-run changes the reading from "no edge" to "small, unproven".
6. **House breakout** (precision tier, harness convention, cap 10): next-open hold 60 +0.14R stop_hold, edge
   +0.10 / +0.11, t 1.0; close entry hold 60 +0.17R, edge +0.03 / +0.06, t 1.1. Consistent with yesterday's
   MARGINAL-PASS at cap 20 (the cap, not the control, is what moves this one).

Seven of 19 daily patterns have a positive mean AND beat both controls on their best arm (the two house-breakout
hold-60 rows, the three earnings-drift cells, the two delayed-bump cells). None has |t| ≥ 3; the largest is 2.65.
Ten of 19 "beat both controls" if negative means are allowed — a negative pattern beating a more-negative control
is not an edge and is not counted.

## Daily — old (month control) vs honest, best arm by post edge, R per trade at cap 10

| pattern | n | old ctrl | old edge | arm | meanR | post ctrl | post edge | xname ctrl | xname edge | t | halves |
|---|---|---|---|---|---|---|---|---|---|---|---|
| in-play up mover (+4% on 2× vol) ¹ | 13,331 | −0.07 | −0.16 | ema20 | −0.08 | −0.02 | −0.05 | −0.06 | −0.02 | −0.4 | −0.11 / −0.06 |
| in-play down mover (−4% on 2× vol) ¹ | 13,955 | +0.08 | −0.16 | ema20 | −0.06 | −0.15 | +0.09 | −0.04 | −0.02 | −2.6 | +0.06 / −0.14 |
| bouncy ball short (daily) ² | 1,404 | −0.00 | −0.34 | stop_hold | −0.08 | −0.20 | +0.12 | −0.15 | +0.07 | +0.4 | +0.08 / −0.17 |
| 20d breakout ADR≥3, HIGH-vol regime | 17,281 | +0.15 | −0.37 | t1R | −0.22 | −0.17 | −0.05 | −0.16 | −0.06 | −5.7 | −0.35 / −0.12 |
| 20d breakout ADR≥3, LOW-vol regime | 24,514 | +0.14 | −0.37 | t1R | −0.22 | −0.16 | −0.06 | −0.13 | −0.09 | −10.5 | −0.22 / −0.23 |
| boring stock, violent move (≥4× ADR, boring tercile) | 628 | −0.61 | +0.45 | ema20 | −0.16 | −0.13 | −0.03 | −0.19 | +0.03 | −3.6 | −0.01 / −0.24 |
| violent move, any ADR (≥4× ADR) | 1,644 | −0.86 | +0.44 | ema20 | −0.13 | −0.11 | −0.03 | −0.07 | −0.06 | −3.2 | −0.08 / −0.16 |
| counter-trend long A (≥3 ADR below 20 EMA + bar-high break) | 9,015 | −0.48 | +0.33 | trail_bar | −0.15 | −0.05 | −0.09 | −0.18 | +0.03 | −2.5 | −0.19 / −0.12 |
| counter-trend B (same trigger, <3 ADR) | 155,514 | −0.15 | +0.06 | ema20 | −0.08 | −0.10 | +0.01 | −0.11 | +0.03 | −4.2 | −0.10 / −0.07 |
| precision-tier breakout, next-open, hold 5 | 1,944 | +0.15 | −0.43 | ema20 | −0.04 | −0.01 | −0.03 | −0.07 | +0.04 | −0.6 | −0.20 / +0.07 |
| precision-tier breakout, next-open, hold 60 | 1,944 | +0.17 | −0.48 | stop_hold | **+0.14** | +0.04 | +0.10 | +0.03 | +0.11 | 1.0 | −0.09 / +0.30 |
| precision-tier breakout, CLOSE entry, hold 60 | 2,023 | +0.21 | −0.48 | stop_hold | **+0.17** | +0.14 | +0.03 | +0.12 | +0.06 | 1.1 | −0.01 / +0.29 |
| earnings drift, good+MUTED | 437 | +0.11 | +0.09 | stop_hold | **+0.27** | +0.03 | +0.25 | +0.01 | +0.26 | **2.65** | +0.19 / +0.33 |
| earnings drift, good+BIG | 1,069 | +0.10 | −0.08 | t1R | +0.04 | 0.00 | +0.03 | −0.02 | +0.06 | 2.0 | +0.04 / +0.04 |
| earnings drift, bad reaction | 3,684 | −0.09 | +0.19 | stop_hold | +0.10 | +0.05 | +0.05 | +0.01 | +0.09 | 0.4 | +0.10 / +0.09 |
| delayed bump after good+MUTED | 335 | +0.05 | −0.24 | ema20 | **+0.25** | +0.07 | +0.18 | −0.05 | +0.30 | 1.6 | +0.49 / +0.10 |
| delayed bump after good+BIG | 796 | −0.14 | −0.22 | ema20 | +0.05 | −0.02 | +0.08 | −0.20 | +0.25 | 0.4 | −0.28 / +0.30 |
| breakout 0–3d after earnings ³ | 256 | +0.13 | −0.34 | t1R | −0.18 | −0.17 | −0.01 | −0.12 | −0.06 | −1.9 | −0.14 / −0.21 |
| breakout, no earnings nearby ³ | 1,286 | +0.16 | −0.49 | t1R | −0.31 | −0.25 | −0.07 | −0.24 | −0.07 | −6.8 | −0.42 / −0.23 |

Per-arm means for every pattern and both controls are in `rerun_2026-09-19.csv`.

## Intraday — Stage A (11,227 fires) and the bouncy ball (1,430), R per trade

| detector / arm | signal | post ctrl (later minute) | xname ctrl (other name, same minute) |
|---|---|---|---|
| ALL, intraday arms (stop_close … time30) | −0.10 to −0.13 | −0.12 to −0.14 (edge +0.01…+0.02) | −0.10 to −0.12 (edge −0.01…+0.01) |
| ALL, swing_trail | +0.52 | +0.63 (−0.12) | +0.69 (−0.18) |
| UR swing_trail (n 8,296) | +0.50 | +0.58 (−0.07) | +0.79 (−0.29) |
| ORB9 swing_trail (n 2,246) | +0.46 | +0.69 (−0.23) | +0.31 (+0.15) |
| LVL swing_trail (n 685) | +0.89 | +1.14 (−0.25) | +0.80 (+0.09) |
| bouncy ball short, best arm t2R | −0.41 | −0.46 (+0.05) | −0.42 (+0.02) |
| bouncy ball short, stop_close | −0.57 | −0.53 (−0.04) | −0.51 (−0.07) |

The old Stage A control ("random minute 09:45–15:30, same name-day") mixed pre-trigger minutes in; the honest
versions give the same answer with smaller gaps. The xname control here is a random other name *with bars
that day*, i.e. another watchlist name, so it measures selection within the in-play list, not against the market.

## Reconstruction caveats

The 2026-09-18 in-play-mover and earnings-proximity rows were inline runs with no script; they are rebuilt here
under stated rules and the counts differ. 13 of 19 daily patterns reproduce their original n exactly.

1. **In-play movers**: close-to-close ≥ +4% (≤ −4%) on volume ≥ 2× the trailing-50 mean, eligible, stop = bar
   low (high). n 13,331 / 13,955 vs 9,294 / 8,693 originally — the original had one more gate (unknown).
2. **Bouncy ball daily**: `run_bouncy_ball_daily.py`'s signal loop ported verbatim, but scored by the harness,
   which drops stops < 0.5% or > 25% of price and starts 2019-10; n 1,404 vs 1,811.
3. **Earnings-proximity breakouts**: the generic breakout pool (`run_precision_tier_control.build`) on the 241
   names with earnings dates, "after" = an earnings date in the prior 0–3 sessions, "none nearby" = none within
   ±10 sessions; n 256 / 1,286 vs 258 / 1,833.

## What changes

- `lib.studies.pattern_test.run_daily` now defaults to `control="post"`; `"month"` stays only to reproduce the
  old rows. Run `xname` alongside for anything that gets near the bar.
- `run_stage_a_score.py` and `run_bouncy_ball_intraday.py` take `--control post|xname` (`month` = original).
- Ledger: 23 RERUN rows appended (same names); the pre-re-run rows stay for the record, their `ctrl`/`edge`
  columns are not to be quoted.
- Readings that move: the bouncy ball daily is "no edge" (−0.08R), not "−0.34R, the exposure paid" — the
  exposure claim was the month control. The boring/violent and counter-trend "+0.3–0.45R vs control" lines in
  the Breitstein test notes were the control; those tests fail on their own means (−0.13 to −0.16R) regardless.
  The earnings-drift good+MUTED cell moves from "control matches it" to "+0.25R over both controls, t 2.65,
  unproven" — worth a true out-of-sample look if the earnings coverage ever widens past 241 names.

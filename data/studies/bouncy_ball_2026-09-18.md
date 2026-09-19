# The "bouncy ball" short (Breitstein) — tested daily and intraday (2026-09-18)

**Verdict: fails at both timeframes in our universe, and loses to its own control.** Shorting the break of
support after a sequence of fading bounces was worse than shorting the same name at a random time.

Spec from `data/lance_breitstein/principles/setup-grading-chart-nuance.md` §2e: leg lower → each bounce lower
than the last → final bounce barely bounces → bars tighten → short the break of support, trail prior bar highs.
Pre-registered translations, controls and thresholds are in the two scripts' docstrings.

## Daily bars, 2019-2026 (`run_bouncy_ball_daily.py`)

1,858 signals on 880 names (median leg 4.8 ADR, 2 bounces, 5-day range 0.50x the prior 5).

| arm | mean R | win% | t | control | edge |
|---|---|---|---|---|---|
| stop, else 5-day close | −0.108 | 41% | 0.6 | **+0.480** | −0.588 |
| 1R target | −0.338 | 48% | −4.3 | −0.002 | −0.336 |
| 2R target | −0.227 | 44% | −1.9 | +0.170 | −0.397 |
| trail prior-day highs | −0.111 | 38% | 0.1 | +0.404 | −0.515 |
| cover on a close over the 20 EMA | −0.108 | 41% | 0.6 | +0.341 | −0.448 |

Control = the same name, a random session in the same month, same stop distance. **Being short these falling
names paid (+0.34 to +0.48R); waiting for the break of support did not.** The pattern picks the worst moment in a
month that was otherwise profitable to be short — you short the low. Both halves negative (2019-22 −0.13,
2023-26 −0.10 on the trail arm); only 2020 is positive (+0.74). Deep legs of 8-12 ADR are positive (+0.05 to
+0.24, n=94) — the one cell worth remembering, and it is small.

## 5-min structure / 1-min fills, Feb-Sep 2026 (`run_bouncy_ball_intraday.py`)

1,430 signals on 175 names, 9.1 per session, median leg 0.73 ADR, 3 bounces.

| arm | mean R | win% | t | control | edge |
|---|---|---|---|---|---|
| stop, else 16:00 | −0.573 | 18% | −11.6 | −0.111 | −0.462 |
| 1R | −0.411 | 38% | −10.9 | −0.245 | −0.167 |
| 2R | −0.408 | 27% | −9.9 | −0.184 | −0.224 |
| VWAP reclaim | −0.562 | 18% | −11.7 | −0.293 | −0.269 |
| 30-min | −0.464 | 28% | −13.0 | −0.256 | −0.208 |
| trail 5-min highs | −0.481 | 21% | −14.9 | −0.334 | −0.147 |
| hold to next close | −0.669 | 13% | −7.3 | −0.313 | −0.356 |

Worse than the daily version and worse than its control on every arm. The 18% win rate on the base arm is the
mechanism: the stop sits at the trigger bar's high — exactly the "really, really close" stop he praises — and in
liquid names that level gets tagged on the bounce that follows the break.

## Why this does not refute him

- **Universe.** His stated habitat is in-play small caps and recent IPOs with a catalyst. Our cache is 192 liquid
  names (intraday) and the $50M-ADDV panel (daily). The pattern may live where we cannot see it.
- **Discretion.** "The final bounce barely bounces", "bars go very tight", "ideally into the close" are graded by
  eye; my thresholds (fractal highs, last bounce smallest, 3-bar range ≤ 0.6x prior 3) are a translation.
- **Borrow.** Not modelled — irrelevant here, since it loses before costs.

## What it adds to the book

Third independent measurement of the same thing: [[project_stage_a_intraday]] (11,227 long triggers),
`exit_timing_study_2026-09-18.md` (same-day exits), and now this. **The trigger is not where the money is.**
In all three, a random entry in the same name over the same window matched or beat the pattern.

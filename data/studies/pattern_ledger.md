# Pattern ledger

_Every entry pattern tested with `lib.studies.pattern_test`, newest last._

**Bar to pass:** beats the same-name random control, positive in both halves, |t| >= 3.
**Multiple testing:** 9 patterns tested so far — at 5% significance, expect ~0.5 to clear by chance. Discount accordingly.

| tested | name | timeframe | n | best_arm | meanR | ctrl | edge | t | half1 | half2 | passed | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-18 | UR reclaim (alert engine) | intraday | 8296 | swing_trail | 0.502 | 0.577 | -0.076 | 3.097 | nan | nan | False | Stage A; intraday arms -0.06 to -0.09R; control = random minute same name-day |
| 2026-09-18 | ORB9 opening-range break | intraday | 2246 | swing_trail | 0.461 | 0.872 | -0.411 | 1.232 | nan | nan | False | Stage A; worst detector, intraday arms -0.25 to -0.30R, t -5 to -12 |
| 2026-09-18 | LVL pivot break | intraday | 685 | swing_trail | 0.89 | 1.2 | -0.31 | 2.44 | nan | nan | False | Stage A; flattest intraday of the three, thinnest sample |
| 2026-09-18 | Bouncy ball (Breitstein short) | daily | 1811 | t1R | -0.338 | -0.002 | -0.336 | -4.29 | -0.307 | -0.357 | False | control = same name, random session same month, earned +0.34 to +0.48R: short exposure paid, the break entry did not |
| 2026-09-18 | Bouncy ball (Breitstein short) | intraday | 1430 | t1R | -0.411 | -0.245 | -0.167 | -10.913 | nan | nan | False | 5-min structure, 1-min fills; 18% win on the base arm; stop at the trigger bar high gets tagged |
| 2026-09-18 | Precision-tier breakout (house) | daily | 1962 | ema20 trail | 0.79 | nan | nan | 4.3 | nan | nan | nan | exit_timing_study: our own book, entry at the breakout close. NOT run through this harness - no same-name random control yet. Re-test before trusting the comparison |
| 2026-09-18 | in-play up mover (+4% on 2x vol) | daily | 9294 | t1R | -0.236 | -0.074 | -0.162 | -8.823 | -0.31 | -0.188 | False | Tito-frequency universe, long continuation |
| 2026-09-18 | in-play down mover (-4% on 2x vol) | daily | 8693 | ema20 | -0.082 | 0.075 | -0.158 | -2.215 | 0.037 | -0.174 | False | Tito-frequency universe, short continuation |
| 2026-09-18 | Archetype D: buy high-beta before FOMC | event | 55 | buy T-1, sell decision close | 0.497 | -0.006 | 0.503 | 1.501 | 0.855 | 0.2 | False | returns in %, not R; edge flips sign across k (T-1 +0.50, T-2 -0.01, T-3 +0.23, T-5 -0.60) = noise; pre-FOMC drift real but t<2 |

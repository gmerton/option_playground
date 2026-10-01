# Swing-low structural trail vs the 20-EMA trail (2026-09-30)

**Verdict: NULL (lean positive, width-fragile) · keep the 20-EMA trail.** Source: Ariel Hernandez (TraderLion
-dv_2h61a2o [1:43–1:45]), "trail on structure, not MAs". Pre-registration: `run_swing_low_trail.py` docstring.
Log `logs/swing_low_trail.log`.

The rule: a 3-bar pivot low, confirmed 3 sessions later. The stop ratchets up to each confirmed pivot and exits on a
close below it. The comparison is the house 20-EMA trail on the same trades, with the same initial stop and 60-session
cap. Exposure-matched means the earlier-exiting arm is filled with beta × SPY until the later exit.

| precision pool, 1,965 trades | Δ (pp/trade) | t | halves | years |
|---|---|---|---|---|
| **PRIMARY SW − BASE, exposure-matched** | **+0.44** | **1.71** | +0.44 / +0.45 | 7/8 |
| raw SW − BASE | +0.81 | 2.88 | +0.75 / +0.84 | 7/8 |
| SW − random exit of the same length | +2.45 | 4.95 | +1.12 / +3.28 | 8/8 |
| exploratory: width 2 / width 5, exposure-matched | +0.17 / +0.17 | 0.29 / 0.36 | flip / flip | 5/8 |
| generic pool (7,666), exposure-matched | +0.12 | 0.54 | +0.23 / +0.05 | 5/8 |

- The swing-low trail is simply *looser*: it holds 17.5 vs 13.8 sessions, exits earlier on only 3% of trades, and
  differs on 33%. Raw, that buys +0.81pp, and about half of it is market exposure (+0.44 after the beta fill).
  Same shape as the RS-loss and STOP_ONLY results.
- What is left (t 1.71) is consistent across halves and years, but it does not survive the neighbourhood: pivot
  widths 2 and 5 drop to ~+0.17pp with flipping halves. A parameter-specific bump = noise.
- SW beating a random same-length exit (t 4.95) is not evidence for structure. Any trend trail beats a random time
  exit on breakouts, because random exits cut the right tail (RAND top decile +25% vs +64%).
- The cost is in the distribution: win 28% vs 31%, median −4.6% vs −4.1%, worse p5.

**Consequence:** no exit change. The looser-trail family (STOP_ONLY, RS-only, swing-low) now consistently earns about
+0.3–0.4pp beyond beta at t < 2. If anything is ever worth re-asking, it is "how loose", not "which structure".

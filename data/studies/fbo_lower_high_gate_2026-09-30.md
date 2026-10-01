# FBO short: lower-high gate (2026-09-30)

**Verdict: NULL (primary leans negative), and the literal MULN form is INVERTED · FBO stays retired.** Source:
Breitstein's MULN day-2 short (`data/lance_breitstein/principles/muln-layup-anatomy.md`): drive above the level, fail,
lower high, break the mini-support below VWAP. Pre-registration: `run_fbo_lower_high_gate.py` docstring. Log
`logs/fbo_lower_high_gate.log`; per-alert `logs/fbo_lower_high_gate_alerts.csv`.

**Sample:** the 9/23 set, 3,175 curated FBO alerts from 2026-02-02 to 09-10 (153 dates, 95 names).

**Trade:** short at the alert close, the emitted stop (median 0.50 ADR), exit at the stop or the session close.

**Control:** same name, same day, a random minute between 09:50 and 15:00 with the same stop width (5 draws averaged).

| cell | n | signal | random minute | edge | t | halves |
|---|---|---|---|---|---|---|
| all FBO (reproduces 9/23) | 3,175 | −0.148% | +0.008% | −0.156pp | −4.04 | −0.16 / −0.15 |
| **PRIMARY: lower high (detector definition)** | 1,444 | −0.083% | −0.001% | **−0.082pp** | **−2.25** | −0.02 / −0.14 |
| no lower high | 1,731 | −0.203% | +0.016% | −0.218pp | −4.10 | −0.29 / −0.16 |
| lower high + mini-support break (his literal sequence) | 2,090 | −0.170% | +0.015% | −0.185pp | **−4.14** | −0.15 / −0.22 |

- The gate halves the damage but does not create an edge. The primary is still below a random minute, in both halves.
  The lower-high group minus the no-lower-high group, paired by date, is +0.05pp (t 0.57), indistinguishable.
- His full sequence (lower high, then a break of the support below it) is the worst-timed version (t −4.14): by the
  time support breaks, the move has been paid for. It is the same entry-extension result as ORB9, mirrored for shorts.
- ⚠ Disclosed fix: the first run's mini-support cell returned n = 0. The trough included the alert bar, so a close
  below it was impossible. It was redefined as the low before a lower high that printed before the alert, then
  re-run. No result for that cell was seen before the fix; the primary was unaffected.

**Consequence:** FBO stays retired as a short entry (9/23). The lower-high condition in `detectors.py` is not an edge
filter. It can stay as a descriptive tag at most.

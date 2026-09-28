# Catalyst as a SELECTION filter ("in play") — NULL (2026-09-28)

**Question** (Breitstein/Luk, queued 2026-09-21): buying the catalyst event fails. Does a recent catalyst instead mark the *name* as worth owning over the next weeks?
**Script:** `run_catalyst_selection.py`. The pre-registration is in its docstring. **Log:** `logs/catalyst_selection.log`. Per-date primary series: `logs/catalyst_selection_primary_dates.csv`.

## Design
- **Panel:** liquid_panel_2009, 2010-03 → 2026-09, 1,724 names.
- **Catalyst:** a gap of at least 3× pre-gap ADR on at least 3× the 50-day volume. This found 2,410 UP and 2,829 DOWN events.
- **Flag:** an UP catalyst in the 20 sessions before entry. Entry is at the close; the outcome is the forward close-to-close return.
- **Control:** unflagged names on the same date, in the same quintile of baseline ADR (measured over sessions t−60 … t−21, so the gap can't inflate it). The date is held fixed. What varies is catalyst-ness plus the recent move, so the mechanism arm also matches on the 20-session return.
- **Test dates:** non-overlapping, needing at least 5 flagged names each.

## Result
| cell | dates | excess (pp) | t | halves (pp) |
|---|---|---|---|---|
| **PRIMARY UP, 20d, ADR-matched** | 155 | **+0.02** | **0.05** | +0.25 / −0.15 |
| UP 20d, ADR + return-matched (mechanism) | 155 | −0.02 | −0.06 | +0.27 / −0.23 |
| DOWN 20d | 167 | −0.20 | −0.88 | −0.16 / −0.23 |
| ANY 20d | 198 | −0.06 | −0.29 | |
| UP 5d / 60d | 625 / 50 | +0.02 / +0.44 | 0.34 / 0.44 | |
| UP inside INT / HYB-B (2020–) | 7 / 6 | −3.7 / +0.1 | — | UNDERPOWERED (too few flagged names per date) |

- **Per year:** the sign changes 11 times in 17 years, with no regime pattern.
- **Power:** SE ≈ 0.31pp per 20 days, so the test would have caught an effect of about 0.9pp or more per month at t 3. This is a NULL, not UNDERPOWERED.

## Verdict
**NULL · YIELD MECHANISM.** A recent catalyst gap does not make a name a better random-entry holding than a same-volatility name without one, at 5, 20 or 60 sessions. That holds with or without matching the recent move. Together with the event-day failures (DR-EP A t −4.7, in-play movers −0.08R, PEAD NULL), the catalyst carries no information for this book, either as an entry or as a selection flag. The second item of the catalyst trio (the 21-EMA pullback after a catalyst) now rests on a flag that selects nothing. Its prior drops accordingly; run it only as an entry-location test.

**Caveats:** gap + volume is a news proxy dominated by earnings gaps; it doesn't see guidance, FDA or contract news without a gap. The panel carries survivorship bias, but the same-date contrast is unaffected.

# Add to an open winner: second signal / retest vs a fresh breakout — NULL (2026-09-28)

**Question** (OptionsPlay DqtBkL1qalU + iXOULnIGEKk, queued 2026-09-24): is the next unit of risk better spent pressing a working name (on a *signal*, not at a fixed session count as in row 121) or on a fresh precision breakout the same day?
**Script:** `run_add_to_winner.py`, pre-registration in the docstring. **Log:** `logs/add_to_winner.log`. Events: `logs/add_to_winner_events.csv`.

## Design
- **Pool:** precision tier (built as in `run_oneil_pyramid_8wk.py`) on liquid_panel_2009. Every entry is the same house trade: close entry, day-low stop (2% floor) judged on the close, 20-EMA exit, 60-session cap, 5 bp per side. Outcome in %.
- **Arm S (second signal):** a new precision signal while the name's base trade is open and in profit. **Arm T (retest):** the first retest of the pivot (low within 0.25 ADR of the pivot, close back above it) while the base is open.
- **Control:** same-date FRESH precision breakouts. The date is held fixed; the kind of entry varies.

## Result
| cell | events | pre-registered: month-weighted diff vs fresh | t | halves | vs unconditional add, same age |
|---|---|---|---|---|---|
| **S second signal, in profit** | 572 | −0.77pp | **−0.55** | −5.98 / +0.15 | −0.54pp (t −0.45) |
| **T retest of the pivot** | 536 | −0.79pp | **−0.57** | +1.67 / −1.08 | **−1.80pp (t −2.48)** |
| T, base in profit (explor.) | 310 | −4.28pp | −1.24 | | −2.18pp (t −2.84) |

**Both pre-registered primaries fail.**

⚠ **METHOD: the pre-registered month-weighting was the wrong estimator for this sample.** The panel's precision tier is thin before 2020 (13–46 fresh trades a year, against 100–350 from 2020 on). A handful of 2014–16 events each got the weight of a whole month, which drove S's first half to −5.98pp. The event-weighted, month-clustered read (exploratory):

| S second signal | n | diff vs fresh | cluster t | median diff |
|---|---|---|---|---|
| all | 572 | **+2.75pp** | **1.64** | −0.54 |
| 2020–22 / 2023–25 / 2026 | 201 / 130 / 206 | +1.57 / +3.19 / +4.55 | 0.90 / 0.83 / 1.34 | all negative |

Retest T, event-weighted: −0.83pp (t −0.83), with no era positive at t > 0.4.

## Verdict
**NULL · YIELD MECHANISM + METHOD.**
- **Second signal (S):** no pass on either estimator. There is a weak right-tail lead: the mean is positive in all three post-2020 eras but the median is negative. Re-firing leaders have fatter tails, and the typical press does worse than a fresh name. This is row 121's conclusion again (adds scale the same edge, they don't improve it), now against the right control. Not actionable at t 1.64 with 2026 carrying 36% of the events.
- **Retest add (T):** the one leaning finding. A retest add does **worse than simply adding to any live trade at the same age** (−1.80pp, t −2.48; in-profit subset −2.18pp, t −2.84). This fits the pool's structure: 76% of breakouts come back to the level and average −0.37R, so a retest mostly marks the ones failing. **Don't add on the retest.**
- **METHOD:** pre-register an event-weighted, month-clustered estimator whenever events per month are this uneven. Month-weighting sparse early years hands noise the weight of data.

**Caveats:** survivorship bias (today's liquid names), though the same-date contrast is unaffected. The effective sample is 2020–26.

# Laggard-breakdown contagion (2026-09-30)

**Verdict: NULL · MECHANISM (the shock is shared on day 0, with no follow-through).** Source: Ariel Hernandez,
TraderLion -dv_2h61a2o [00:47:45–00:49:30]: "when the laggard breaks structure first, the leader is usually one to
three weeks away from doing the same" (his example: CIEN breaking its 50-day on earnings, then the other optics names).
Pre-registration: `run_laggard_contagion.py` docstring. Log `logs/laggard_contagion.log`; events
`logs/laggard_contagion_events.csv`.

**Event:** a former industry leader (top RS quintile of its industry on 126d returns, 20 sessions earlier) closes
below its 50-day after ≥ 40 closes above it. The industry needs ≥ 4 eligible names, and only the first event per
industry per 20 sessions counts. That gives 2,662 events on 1,417 dates in 103 industries, 2010–2026.

**Peers:** the industry's other names still above their 50-day (median 4).

**Control:** same-date names above their 50-day in industries with no event in the *past* 20 sessions, reweighted to
the peers' ADR mix.

| | 5d | 10d | **15d (PRIMARY)** |
|---|---|---|---|
| peer − control, pp | −0.03 (t −0.37) | +0.06 (t 0.84) | **+0.09 (t 0.10)** |
| halves 2010–17 / 2018–26 | −0.01 / −0.04 | +0.04 / +0.06 | +0.02 / +0.12 |
| peers closing below their own 50-day (vs ADR × distance-matched) | 31.7% vs 30.4% (t 1.63) | 46.2% vs 44.2% (t 2.15) | 55.7% vs 54.2% (t 1.87) |

- **Day 0 is where the contagion is:** peers −1.06% vs control −0.38% on the breakdown day itself (t −20). The
  laggard usually breaks *with* its group, a common industry shock. That is what makes the pattern look real on a
  chart.
- **After day 0, nothing.** The 15-day return gap is +0.09pp (10 of 17 years positive), and its sign is the opposite
  of the claim. His literal claim, that peers break their own 50-day next, shows up as only +1–2pp over a 54% base
  rate. That is under the bar and not something you could trade.
- His "1–3 weeks later" is the base rate: more than half of names above their 50-day close below it within 15 sessions.
  With a 54% base rate, one memorable episode (optics, 2026) can't tell a signal from the background.

**Consequence:** no peer veto or exit rule. A laggard's breakdown is information about the day it happens, which the
close already prices; it carries none about the leaders' next three weeks.

# Daily loss limit / tilt: ARM 0 on Gabe's journal (2026-09-30)

**Verdict: NULL (arm 0 (a) is flat, so three queue rows settle together) · YIELD MECHANISM (lean only: size creeps
after losses).** Breitstein test 1 (Cameron's "80% chance of doubling the loss"), restructured 2026-09-22 to run
arm 0 first. Pre-registration: `run_loss_limit_arm0.py` docstring. Log `logs/loss_limit_arm0.log`; episodes
`logs/loss_limit_arm0_episodes.csv`. Admissible use only: conformance/execution, never setup selection.

Data: `journal_trades`, 41 sessions (2026-08-03 → 09-29), 585 scored underlying-level episodes (23 carried-in
excluded, 55 still open). Win 30.6%, mean −$8.9, total −$5.2k realized. ⚠ Power ceiling declared in advance: this
cannot certify a rule, and the bar is |t| ≥ 3.

| test | result |
|---|---|
| **(a) PRIMARY: after ≥ 2 same-session consecutive losses, minus k = 0 same session** | **+$12.1/episode, t +0.60** (221 episodes, 32 sessions). Wrong sign for tilt |
| (a) k ≥ 1 / k ≥ 3 | +$13, t 0.80 / +$38, t 0.81. Win rate is *higher* after losses (+10–16pp, t 2.0–2.4, below the bar) |
| (b) size vs his own median notional | **creeps up after losses**: median 0.93× at k = 0 → 1.07× (k ≥ 1) → 1.17× (k ≥ 2) → 1.19× (k ≥ 3). Paired +0.18 / +0.20 / +0.37, t 1.24 / 1.40 / 1.66. Monotone, under the bar |
| (c) stock loss in ADR units | no overrun: median loss −0.15 ADR (k ≥ 1) vs −0.20 (k = 0); past the 1-ADR disaster stop on 2.0% vs 2.2% |
| (d) Cameron's "80% close at ≤ 2× the breach" | **25–26%** at every limit ($500: 27 sessions; $1,000: 12; 1% NAV: 16). Rest-of-day realized P&L after the breach is *positive* on average (+$89 to +$173) |
| (e) ~90-min shutoff: opened after 11:00 minus before | −$18, t −0.71; win −0.9pp, t −0.14 |

**Reading.** On this log, outcomes after losses are not conditionally worse. The positive-leaning win rate is
probably composition: k = 0 over-weights each session's first trades, and first trades are the worst (early mean
−$17.6 vs late −$1.8). The i.i.d. argument therefore governs. A daily loss limit, a stop after 2 losses and an 11:00
shutoff only change n. On a book with negative expectancy that "helps" mechanically and carries no information.
Cameron's 80% does not replicate here (25%).

**The one signature worth watching is size.** Position size rises monotonically with the loss streak (+20 to +37%
of his median), which is the revenge fingerprint in its execution form. At t 1.7 it is a lean, not a finding. If
anything is adopted, it is a *size cap after 2 losses* (conformance hygiene), not a trading halt.

**Same-day round trips (standing flag):** 336 of 585 episodes opened and closed the same session, **−$11.6k at a
21% win rate** (September alone 165, −$4.3k). Still the largest measured leak.

Settles NULL: Cameron max-loss doubling (Breitstein #1), IQCapital "stop after 2 consecutive losses", ~90-min shutoff.

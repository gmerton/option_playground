# Does a scheduled macro catalyst help? FOMC event study (2026-09-18)

**Question.** Tito's archetype D — buy below the pivot ahead of a macro event, sell into the run-up — his two
40x election trades being the showcase. Elections give n=4; FOMC gives 55 decisions, so that is where it can be
tested. Dates: `data/fomc_dates.json` (fetched from federalreserve.gov, 2019-10 → 2026-09, decision day of each
two-day meeting; the two unscheduled 2020 meetings kept separate).

**Verdict: no tradeable edge.** The known pre-FOMC drift is visible and below our bar; buying high-beta names
ahead of the meeting does not beat buying them on a random day of the same month.

## Index

| window | SPY mean | t | QQQ mean | t |
|---|---|---|---|---|
| T−5 → T0 | +0.47% | 1.46 | +0.65% | 1.56 |
| T−3 → T0 | +0.39% | 1.53 | +0.63% | 1.90 |
| decision day | +0.11% | 0.65 | +0.35% | 1.52 |
| T0 → T+1 | −0.08% | −0.43 | −0.08% | −0.32 |
| T0 → T+5 | +0.28% | 0.78 | +0.48% | 0.99 |
| T−5 → T+5 | +0.76% | 1.85 | +1.14% | 2.12 |

The drift into the announcement is real and positive, and it is not significant at |t| ≥ 3 on 55 events.

## Archetype D on high-beta names (ADR ≥ 4, liquid): buy T−k close, sell the decision-day close

| entry | events | mean | win | t | control | edge | 2019-22 | 2023-26 |
|---|---|---|---|---|---|---|---|---|
| T−1 | 55 | +0.50% | 62% | 1.50 | −0.01% | +0.50 | +0.86 | +0.20 |
| T−2 | 55 | +0.31% | 58% | 0.69 | +0.32% | −0.01 | +0.65 | +0.02 |
| T−3 | 55 | +0.66% | 56% | 1.35 | +0.43% | +0.23 | +1.06 | +0.33 |
| T−5 | 55 | +0.60% | 58% | 0.93 | +1.19% | −0.60 | +0.38 | +0.78 |

Control = the same holding length starting on a random non-event session in the same month, 5 draws per event.
**The edge flips sign across k** (+0.50, −0.01, +0.23, −0.60), which is what noise looks like. Every window is also
weaker in the recent half.

⚠ With one control draw per event the T−1 "edge" printed as +1.42 — noise in the control, not signal. Five draws
collapsed it to +0.50. Any event study here needs multiple control draws.

## Unscheduled meetings, for context (not tradeable ex ante)

SPY 2020-03-02 +4.33% on the day, then −11.28% over five sessions. SPY 2020-03-15 −10.94% on the day, −6.50%
after. The emergency cuts marked panic, they did not stop it.

## Reading

**Scheduled macro is not a catalyst in the sense that matters.** The date is public months ahead, so there is
nothing to discover; what moves is the surprise, which is unknowable beforehand. Contrast the same pool split by
company news:

| | breakout mean R |
|---|---|
| 0–3 days after an earnings report | **+0.42** (precision tier +1.52, n=32) |
| 46+ days after | −0.07 |
| within 5 days *before* earnings | −0.39 |

**Catalysts that reveal something about the company change the odds; scheduled macro does not.** Next step is
therefore earnings coverage (241 of 1,743 panel names today), not more macro dates.

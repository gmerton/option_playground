# 16 Years of Swing Trading Lessons in 12 Minutes

**Video:** `bZ7-iBaI_Xw` · **Type:** talks · **Watched:** 2026-09-26 · **Published:** 2026-09-26 · 11:58

> **2/5 · no new test.** Ten lessons on moving from intraday to swing trading. It's a list of principles with no
> numbers, base rates or examples beyond famous winners (QBTS/RGTI/IONQ, his Nikkei trade), plus a course pitch at
> [06:40–07:55]. Everything testable is already in the ledger. The two claims that bear on this book point opposite
> ways: sizing/gap risk AGREES; "be adaptive to the regime" is the claim our data most consistently refuses.

## Raw notes

- [00:00] Credential: "over a hundred million dollars" (Trillium prop). Now swings for lifestyle.
- **L1 [00:30]** Higher timeframes = more scalability, **less edge**. Highest-EV opportunities are the shortest
  timeframes (order flow, news, behavioural mistakes); "traders at Trillium make money almost every single day."
  Swing = more randomness between entry and exit.
- **L2 [01:30]** Day traders must cut size **far more** than stop distance implies: overnight **gap risk** means
  the risk taken ≠ the risk planned. He anchored to intraday size and "would continually shake myself out of
  trades that were otherwise not violating my system." Smaller size ≠ smaller opportunity when the target is 5–10×.
- **L3 [02:55]** TA is fractal: the same breakouts/reversals on 2-min and monthly charts.
- **L4 [03:50]** Strategies are the same across timeframes (continuation vs mean reversion). His intraday
  capitulation playbook = the Nikkei panic long he held for days ("greatest trade of my career").
- **L5 [04:50]** Long momentum swing is "one of the most powerful strategies," esp. in hot bull cycles
  (Qullamaggie). Asymmetry: extended names can double and double again; mean-reversion instincts say "too late."
- **L6 [05:50]** Know your regime; swing traders fail by not adapting — a strategy works for 6 months, they keep
  running it after conditions change. Qullamaggie struggled in 2022 (Market Wizards).
- [06:40–07:55] ⚠ Course pitch (theonelanceb.com), "you pissed away $5,000 this week" framing.
- **L7 [07:55]** Buying power: swing positions tie up capital for days/weeks, so every new trade has an opportunity
  cost vs existing positions — a portfolio-management layer intraday traders don't have.
- **L8 [08:50]** Lifestyle/psychology: more prep time, sleep on it; you give up speed as an edge.
- **L9 [09:40]** More tail risk, especially **overnight shorts** (buyouts, micro-caps gapping hundreds of %).
  "You cannot build your risk management around the assumption that you will always be able to exit where you want."
- **L10 [10:25]** Find your style; the transition took him "a couple of years" to relearn sizing, patience,
  portfolio management and noise tolerance.

## Claims against the ledger (none new)

| claim | verdict on our data | where |
|---|---|---|
| L1 intraday = more edge | ⚠ **Contradicted for this book.** Our intraday triggers = a random later minute (11,227 alerts); CLOSE entry beats every intraday entry; ORB9 −0.425pp vs a random minute. May hold for a prop desk with his execution; unfalsifiable here. | Stage A; entry study 2026-09-17; ORB9 re-examination 2026-09-23 |
| L2 size down for swing, gap risk, shaking out | **AGREES** (repeat of `stops-and-sizing.md` / `risk-management-15-lessons.md`). Matches the house split: tight stop judged on the CLOSE, disaster stop 1 ADR resting; DINO 2026-09-22 is the "shake out" case. | `stop_definitions.md`; entry study |
| L3–L4 fractal patterns | AGREES as method (`feedback_timeframe_agnostic_patterns`), but single-name capitulation fades are **0 for 4** on daily bars, incl. his own 10-variable scorecard. The Nikkei (index/asset-class) version remains the untested residual. | TEST_INDEX capitulation SCORECARD row |
| L5 long momentum, extended can double again | **AGREES**: 12-1 momentum SUPPORTED (t 2.93, the sleeve being built); "extended → tighten" INVERTED; Qullamaggie's early partial INVERTED — don't sell strength. Note the breakout book itself is uncertified. | momentum portfolio 2026-09-25; profit-lock; WL-4 |
| L6 adapt to regime | ⚠ **Contradicted as actionable.** Good stretches are real but not forecastable: persistence ρ −0.01, regime sweep p 0.36; breakout paying months unforecastable; FTD and distribution days NULL. The direct test of "react to feedback" is QUEUED (simulated adaptive trader, §10). | WL-2b localisation; breakout regime feedback; §10 |
| L7 buying-power opportunity cost | Process; untested. Nearest evidence: momentum buffer book (hold while top quintile) = same return at a third of the turnover. | momentum buffer 2026-09-25 |
| L9 overnight short tail risk | AGREES; moot here — no short-selectable universe exists (0/10). | short-universe test 2026-09-23 |
| L8, L10 | lifestyle / style — not testable. | — |

## Reactions / conflicts

- L1 + L6 together are the channel's recurring frame: edge lives in skill (speed, adaptivity). This book's evidence
  says the reverse for Gabe — the entries/intraday machinery add nothing and regime-switching can't be timed; what
  survives is selection plus fixed sizing. Don't import "be more adaptive" without the §10 simulation.
- L2 is the one to keep: it's the same size-down-for-overnight rule as `risk-management-15-lessons.md`
  (overnight size = ½–⅓ intraday), restated.

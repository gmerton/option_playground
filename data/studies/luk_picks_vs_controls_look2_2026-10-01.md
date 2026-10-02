# Martin Luk's picks vs our selection: interim look 2 (2026-10-01)

**Verdict: UNDERPOWERED, and the look-1 lead is gone. Picked at the close and held 20 sessions, his longs perform
about the same as our precision tier.** Script `run_luk_picks_vs_controls.py` (look-2 amendment committed before
scoring, 21ef402), log `logs/luk_picks_vs_controls_look2.log`. Bar at this look: t >= 3.2 (Sidak over 2 looks).

Scope: the clarification worklist went from 64 open rows to 6 on 2026-10-01. Gabe resolved some rows, and the rest
were read from his **on-screen TradingView watchlists** (LONGS / SHORTS / FOCUS / TRACKING) and the chart symbol
in 1080p frames, which counts as "what he shows on screen" under the declared rule. **149 picks scored (102 long, 47
short), 75 fill dates, 2025-11-26 -> 2026-09-18** (look 1: 106 picks, 62 dates).

## Long picks, 20 sessions (primary)
| | n | mean 20-session return, net |
|---|---|---|
| his long picks | 89 | +2.66% (median +2.30%, 53% winners) |
| our precision tier, same dates (C2) | | +2.89% |
| same-date market, same ADR tercile (C1) | | +2.13% |

- **Primary, picks minus C2: -0.22pp, date-cluster t -0.07** (46 dates; week-cluster t +0.05). Halves -1.98 / +1.50.
  MDE at 80% power 8.9pp, so UNDERPOWERED by rule, but the point estimate is now about zero (look 1: +3.44pp, t 0.92).
- vs C1 -0.24pp (t -0.09); vs C3 same name later -2.16pp (t -0.54); excluding levered ETFs -0.17pp (t -0.05).
- 5 sessions: vs C2 +0.87pp (t 0.60), vs C1 +0.44pp (t 0.36), vs C3 +0.52pp (t 0.34).

## Short picks
39 with a 20-session window: +2.38% signed net, 64% winners; vs the ADR-matched market +2.56pp, t 0.44 (MDE 16.3pp).
Nothing measurable.

## Profile (descriptive; unchanged from look 1)
ADR 6.7% vs 4.7%; 17.5% below the 52-week high vs at it; EMA stack 7 days vs 15. **0% of his long picks were a house
breakout that day**, 2% within 3 sessions. He buys a different event: faster names, earlier, inside the base.

## Reading against the goal
- With the worklist mostly resolved, **his selection, entered at the close, carries no measurable edge over ours.**
  The +3.4pp at look 1 was the small sample. Selection does not explain his returns.
- What remains untested is his execution: an intraday trigger with a 1-2.5% stop (large size for 0.3% risk), fast
  stop-outs and re-entries, and trailing the winners. That is the queued **tight-stop survival test**
  (`run_luk_tight_stop_survival.py`, pre-registered). Gabe's condition for running it was more worklist
  disambiguation, which is now met (6 open).
- ⚠ Unchanged: one regime, 46 dates. Aggregate only; no per-pick outcomes printed (the 6 open rows stay blind).

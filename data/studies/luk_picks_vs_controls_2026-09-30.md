# Martin Luk's picks vs our selection: interim look 1 (2026-09-30)

**Verdict: UNDERPOWERED (interim). His long picks are ahead of ours, not significantly, and they are a different
event from our breakout.** Script `run_luk_picks_vs_controls.py` (pre-registered 2026-09-27; interim amendment and
implementation committed before scoring, f27bafe), log `logs/luk_picks_vs_controls.log`.

Scope of this look (Gabe 2026-09-30: "run it now on the unambiguous trades"): 205 entry rows in his log; 64 still open
on the clarification worklist and 28 retrospective rows are excluded. **106 picks scored (69 long, 37 short), 62 fill
dates, 2025-11-26 -> 2026-09-18.** Entry at the close of his fill date, so this scores selection, not his intraday
execution. Results are aggregate only, so the remaining clarifications stay blind.

## Long picks, 20 sessions (primary)
| | n | mean 20-session return, net |
|---|---|---|
| his long picks | 66 | +6.52% (median +6.16%, 58% winners) |
| our precision-tier breakouts, same dates (C2) | | +5.08% |
| same-date market, same ADR tercile (C1) | | +2.95% |

- **Primary, picks minus C2: +3.44pp on fill-date means, t 0.92** (38 dates; week-cluster t 1.05). Halves -1.51 /
  +4.38. The minimum detectable effect at 80% power is 10.4pp, so this sample cannot see a gap of the size observed.
- vs C1 (market, volatility held fixed): +3.03pp, t 0.98 (week-cluster t 1.81). vs C3 (same name later): +3.02pp,
  t 0.73.
- 5 sessions: vs C2 +0.09pp (t 0.05), vs C1 +0.39pp (t 0.32), vs C3 +1.76pp (t 1.05).
- Excluding leveraged and inverse ETFs: +3.71pp vs C2, t 0.98.

## Short picks
30 with a 20-session window: +1.75% signed net, 63% winners; vs the ADR-matched market +0.94pp, t 0.13 (MDE 19.7pp).
Nothing measurable.

## What his picks look like next to ours (descriptive; the pre-registered trigger for this section, t >= 2, was not met)
| | his long picks | our precision tier, same dates |
|---|---|---|
| ADR | 6.5% | 4.7% |
| distance from the 52-week high | -15.3% | +1.1% |
| EMA-stack days | 9 | 16 |

- **None of his 61 in-panel long picks was a house breakout that day, and only 2% had one within three sessions.** 8%
  closed above the 15-day pivot. Median entry is about 1 ADR above the 20 EMA, 15% below the 52-week high.
- So he is not buying our signal on better names. He buys faster stocks earlier, inside the base, and our screen
  does not see those entries at all.

## Reading against the goal
- A fixed 20-session hold from the close earns +6.5% on his picks and +5.1% on ours over the same dates. Selection
  measured this way does not explain a triple-digit year; in this tape both lists went up.
- The measured differences are the entry location (early, not at the pivot) and the volatility of the names. His
  stated method adds two things this test does not score: a tight intraday stop (which sets a large position for a
  small fixed risk) and trailing the winners. Those are the untested parts.
- One regime (a strong tape for leaders) and 38 dates. The verdict is interim; each re-run on a fuller worklist is
  another look and the bar rises (3.2 at look 2).

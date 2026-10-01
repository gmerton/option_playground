# Index dip family: one 2012-published rule on 2013-2026 (2026-09-30)

**Verdict: PASS on the discovery bar. Candidate, not adopted (Gabe's decision).**
Script `run_index_dip_family.py` (pre-registered and committed before the run, bfd3fd0), log
`logs/index_dip_family.log`. Origin: the Quantified Strategies channel triage
(`../quantified_strategies/channel_triage_2026-09-30.md`); this closes the section 10 row "Daily ETF mean reversion
benchmarked against buy-and-hold" (parked 2026-09-22).

## The rule
Buy the close when SPY closes below the lowest low of the previous 5 trading days. Sell the close on the first day
that closes above the prior day's high, or after 5 trading days. No stop. One position; a signal while long is ignored.

The author posted this entry in October 2012 (Wayback capture of his post dated 2012-10-24), so 2013 -> 2026 is out
of sample for it and it has no free parameter. That is why this rule was chosen out of the channel's dozens of
oscillator variants. The exit is the channel's standard one as stated in video `UkoTdKV65yk`; the 2012 post's own exit
was not recoverable.

## Primary cell (SPY, 2013-01 -> 2026-09-18)
Same instrument, same exit, only the entry day varies: return from the close of d to the exit close, for every day d.

| | n | win | mean |
|---|---|---|---|
| signal days | 344 | 76.7% | +0.645% |
| all other days | 3,103 | 73.5% | +0.177% |
| **difference** | | | **+0.468pp, HAC t 3.72** |

- Halves: 2013-19 +0.429pp (t 3.64), 2020-26 +0.493pp (t 2.34). Years positive 13 of 14 (2023 negative).
- Book (non-overlapping): 209 trades, 75.1% winners, +0.478% gross, **+0.454% net**, PF 1.82, 3.0 bars held.
- In-sample 1993-2012 (descriptive): +0.488pp, t 4.01. No decay after publication.

## Secondary cells (same test; four cells in all, Sidak bar 2.49)
| cell | signal vs other | t | halves | years + | book net |
|---|---|---|---|---|---|
| QQQ, 5-day low | +0.584pp | 4.43 | +0.577 / +0.574 | 11/14 | 200 trades, +0.434% |
| SPY, down Monday | +0.318pp | 3.68 | +0.188 / +0.494 | 13/14 | 272 trades, +0.493% |
| QQQ, down Monday | +0.321pp | 2.83 | +0.280 / +0.385 | 11/14 | 255 trades, +0.543% |

## Robustness (pre-registered)
- **R1 volatility control: survives.** With lagged 20-day realised vol in the regression the signal is +0.445pp,
  t 3.57. By RV tercile: low +0.238pp (t 1.99), mid +0.290pp (t 1.32), high +0.699pp (t 3.04). The edge is larger in
  volatile tape but is not only a volatility premium.
- **R2 random-entry null: survives.** Same number of entries drawn at random, same book and exit, 2,000 draws: median
  mean trade +0.21% (5-95%: 0.08-0.33) vs the book's +0.48%; no draw reached it. Per long day 16.0 bp vs 8.1 bp median
  (0.5% of draws higher). The win rate is NOT special (75.1% vs 73.9% median): the exit makes any entry win ~74%.
- **R3 exposure-matched: weaker.** Long days +16.0 bp vs flat days +3.9 bp, t 2.19. Book net CAGR 6.77% at 18.3%
  exposure, max drawdown -13.3%; buy-and-hold 14.97%, -33.7%. It does not beat holding SPY in absolute return; it
  earns about four times the average day while invested.

## Checks added after the first run (labelled post hoc)
- **Real-fill check (P1).** The rule decides and fills on the same closing print, which cannot be traded. Taking the
  signal from the last 1-minute price ten minutes before the close and filling at the close: 338 signal days (313
  shared with the close-based 340), **+0.469pp, t 3.59**; book net +0.479%. QQQ t 3.68.
- Next-open entry and exit (exploratory): SPY +0.328pp, t 2.98; QQQ +0.485pp, t 3.78. About 30% of the SPY edge is the
  first overnight.
- **Regime (exploratory).** Above the 200-day: +0.328pp (t 2.41), signal mean +0.463%, n 245. Below: +0.674pp
  (t 2.04), signal mean +1.096%, n 99. **Today (2026-09-30): SPY above the 200-day, RV20 10.8% annualised (low
  tercile), no signal.** In that regime the measured edge is about half the headline and under the bar on its own.
- Book net return by year: 2013 +10.4, 2014 +5.8, 2015 +0.8, 2016 +1.1, 2017 +6.8, 2018 -3.0, 2019 +1.9, 2020 +14.0,
  2021 +26.5, 2022 -1.9, 2023 +0.8, 2024 +9.8, 2025 +16.3, 2026 +7.0 (to 9/18).
- Five worst trades: 2020-02-21 -11.2%, 2018-12-17 -7.7%, 2020-03-16 -6.5%, 2018-10-04 -6.0%, 2018-03-16 -5.9%. There
  is no stop; the 5-day time exit is the only limit.

## What this is and is not
- It is index short-term reversal: SPY bought after a short-term low earns more over the next few days than SPY
  bought on any other day. The Darvas test saw the mirror image (breakout days -0.180pp, t -3.60, exploratory).
- It is not evidence for the channel's other ~110 indicator videos one by one; they are the same effect with fitted
  parameters. It says nothing about single names (the confirmation-ladder dip is still PARKED on survivorship).
- Not measured: overlap with the live calm weekly SPY put and with the momentum sleeve.

## Open decisions
1. Adopt as a paper or small live sleeve? About 15 trades a year, SPY at the close, 3 days held.
2. If so, SPY only (primary) or SPY + QQQ, and whether to add the down-Monday rule (correlated, not independent).

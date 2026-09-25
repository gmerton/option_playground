# Buy early, buy the close, or skip? The close rule vs the 1-ADR band (2026-09-25)

Script: `run_band_runaway_entry.py` (pre-registered 1579425; one mechanical fix after, `DataFrame.between` → explicit
comparisons, spec unchanged). Log: `data/studies/logs/band_runaway_entry.log`; events `logs/band_runaway_entry_h{5,20}.csv`.
Prompted by DELL 9/25.

## Verdict: NULL on all 6 comparisons · the band rule is NOT SUPPORTED (it neither helps nor hurts) · METHOD

Events: every morning a precision-tier name, in the band at the prior close, opened in the band with gap < 3%. That is
**2,862 events on 772 names, 2010→2026**, chosen at 09:30 with no knowledge of the close. The house rule traded 82% of
them; the other 18% closed > 1 ADR over the 21 EMA.

| comparison (+20, % return, paired) | diff | t | halves |
|---|---|---|---|
| **PRIMARY: OPEN − HOUSE** | +0.28pp | +1.05 | −0.17 / +0.65 |
| OPEN − CLOSE-ANY | +0.10pp | +1.01 | +0.09 / +0.10 |
| CLOSE-ANY − HOUSE (value of skipping extended closes) | +0.18pp | +0.79 | −0.26 / +0.55 |

+5 sessions: every comparison within ±0.13pp, |t| ≤ 1.1.

- **Entry timing on a candidate morning does not matter.** The open, the close and the house rule return +1.42 / +1.43 /
  +1.44% per trade over 20 sessions. That agrees with the 9/17 entry study (no intraday entry beats the close) from the
  other side: nothing beats the open either.
- **The 1-ADR band adds nothing.** Buying the close anyway on the days that ran out of the band returned **+1.34%** over
  20 sessions, against +1.44% for in-band closes. The August-journal claim that a 1–2 ADR entry is a chase that loses
  does not show up on 2,862 panel events. Skipping those closes cost +0.18pp on average (not significant).
- **Descriptive only, outcome-conditioned:** on the 523 runaway days the open entry made +5.0% vs +1.3% at the close.
  That gap is the day's own +3.65% rally, and nobody knows at 09:30 which days those are. This is the trap the
  pre-registration excluded, and the DELL question lived inside it.
- **1-min secondary** (2026 only, n 77): morning entries were +0.46 to +0.80pp vs the house rule, t ≤ 1.2. Underpowered;
  re-run on the Polygon backfill (2024-10 onward) when it lands.

## What it taught
- **METHOD:** "would earlier have been better?" asked about a day that ran is always yes, and always outcome-conditioned.
  The honest unit is the morning, not the outcome.
- **Rule change (daily_routine rule 1):** UNVALIDATED → **NOT SUPPORTED**. No evidence to skip a precision-tier close
  because it is 1–2 ADR over the 21 EMA, and no evidence to rush in at the open. The close remains the default because
  it is simplest and gives the day's low as the stop, not because it earns more.

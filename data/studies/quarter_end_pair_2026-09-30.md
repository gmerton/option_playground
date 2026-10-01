# Quarter-end pair: Karsan's quarter-end flow (2026-09-30)

**Verdict: UNDERPOWERED × 2 (both point estimates positive, both halves agree, neither near the bar) · his stated
mechanism (S1) runs the WRONG way.** Source: tastylive QAFDAuK_tqU. Specs A and B were pre-registered in
`data/tastylive/videos/2026-09-30_QAFDAuK_tqU/notes.md` (committed before any data was touched). Script
`run_quarter_end_pair.py`, log `logs/quarter_end_pair.log`.

## A. SPY: quarter-end turn (day −1 and day +1) minus non-quarter month-end turn, HAC(5), bp/day

| window | QE_W | ME_W | QE − ME | t |
|---|---|---|---|---|
| **PRIMARY 2000–2026** (214 / 428 days) | +18.2 | +3.6 | **+14.6** | **1.49** |
| half 2000–12 | +23.7 | +7.4 | +16.2 | 1.01 |
| half 2013–26 | +13.1 | +0.0 | +13.0 | 1.15 |
| in-sample era 1993–99 | −7.5 | +19.6 | −27.1 | −1.64 |

- Positive and same-signed in both halves, but t 1.49, against a pre-declared MDE of ~35 bp/day. Positive in 15 of 27
  years. The 1993–99 era runs the other way. Pre-registered reading: **UNDERPOWERED**, not NULL.
- **S1, his mechanism ("up quarter → collateral → re-leveraging"):** up-quarter turns minus down-quarter turns
  = **−18.6 bp/day, t −0.79**. Down quarters' turns are *stronger* (+31 vs +13 bp). The story he gives does not
  describe the data that exists.
- S2 (descriptive): year-end turn +7.5 bp vs other quarter ends +21.7. The day −1 return does not forecast the next
  quarter (Spearman −0.05).

## B. VIX "V" around the quarter-end roll (JHEQX): V = Δlog[0→+5] − Δlog[−5→0], quarter ends minus other month ends

| series | 2017–26 | t | halves 17–21 / 22–26 | placebo (pre-2017) | dose |
|---|---|---|---|---|---|
| **VIX (PRIMARY)** | **+5.2 pts** | **1.23** | +6.9 / +3.7 | −3.0 | +8.2 |
| VIX3M | +2.6 | 1.02 | +3.8 / +1.6 | −2.5 | +5.1 |

- Every directional check the spec named lines up: both halves positive, a negative placebo, a positive dose, and the
  trough share is 34% at quarter ends vs 19% at other month ends. But t is 1.23 on 38 events. It is positive in only
  5 of 10 years, and 2020–21 carry it. **UNDERPOWERED.** VIX3M, where a ~3-month collar should show most, is weaker
  than VIX.
- If it ever passed, it would be a calendar MECHANISM shared with SPX quarterly expiry and rebalances, not
  attributable to JHEQX alone (pre-declared).

**Consequence:** nothing to trade. Neither cell can reach |t| 3 on the history that exists (~107 turns, ~38 rolls).
B's consistent direction makes it a forward-only watch item at most: each quarter adds one event. Not queued as a test.

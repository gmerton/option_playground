# Episodic pivot out of a long base vs the plain earnings-gap buy [WL-5d] — 2026-09-23

**Verdict: NULL · YIELD MECHANISM.** Qullamaggie's extra EP condition (the earnings gap closes above its prior
252-session high) doesn't change the result. Base-break EPs fail the timing control (paired t 2.28, p_search 0.044), and
they earn **less** per trade than earnings gaps that *don't* break out of a base (+0.69% vs +1.18%, −0.49pp, t −0.64).
The one near miss is again a *selection* cell: vs a random other name the same day, t 2.94, p_search 0.0035 (bar
0.003), both halves positive.

Script: `run_ep_base_break.py` (pre-registration in the docstring, from the Qullamaggie KB). Log:
`data/studies/logs/ep_base_break.log`. Trades: `logs/ep_{base,no}_break_trades.csv`. Local, minutes. Data:
`liquid_panel_2009.parquet` + MySQL `earnings_report` (275 names, the options/PEAD universe), 2010-01 → 2026-09.
12,223 earnings reactions. Gap ≥ 5% and RVOL ≥ 3: 309 base-break, 463 no-break.

## Results

**Primary: base-break EPs through the upgraded harness** (close entry, day-low stop on the close, hold 60):

| control | best arm | paired t | halves | p_search | verdict |
|---|---|---|---|---|---|
| `post` (timing) | t2R | **2.28** | +0.14 / +0.32 | 0.044 | fails |
| `xname` (selection) | stop_hold | 2.94 | +0.38 / +0.68 | 0.0035 | narrow miss |
| (no-break events vs `post`) | trail_bar | 0.53 | +0.52 / −0.09 | 0.58 | fails |

**Secondary: % per trade** (20-EMA trail):

| arm | n | mean | t vs 0 | median | win | halves (<2018 / ≥2018) |
|---|---|---|---|---|---|---|
| BASE-BREAK | 308 | +0.69% | 1.34 | −1.50% | 39% | +0.44 / +0.84 |
| NO-BREAK | 463 | +1.18% | 2.09 | −1.72% | 36% | +0.49 / +1.43 |
| **difference** | | **−0.49pp** | **Welch −0.64** | | | −0.05 / −0.59 |

By year, neither arm leads consistently (base-break ahead in 7 of 17 years).

## Reading

- **The long-base qualifier adds nothing.** It picks a similar set of trades with no better outcome. The missing piece
  in our catalyst gate was not the base.
- **The earnings-gap book itself is mildly positive here** (+0.7% to +1.2% per trade on the house exit, 2010–26, 275
  names). That's unlike generic catalyst gaps (DR-EP arm A −0.173R, liquid panel 2019+). But neither beats its timing
  control, so buying the gap day is not better than buying the same name on a later day. Same shape as PEAD NULL and
  DR-EP.
- **Selection again:** these names beat random names on the same date (t 2.94). Consistent with the book-wide
  "selection yes, entry timing no".

# RMV tightness gate [WL-3a] and Flanders breadth deferral [WL-3b] — 2026-09-23

Both are **NULL**. Both ran locally on the daily liquid panel in a few minutes each, pre-registered in the script
docstrings from the Deepvue and USIC review specs.

## WL-3a — RMV tightness gate on the house breakout (`run_rmv_gate.py`, log `logs/rmv_gate.log`)

**Verdict: NULL, leaning INVERTED · YIELD MECHANISM.**

Deepvue's "tight before the breakout" claim, reconstructed as RMV15: min-max over 15 bars of the 3-bar true range per
close. The gate is ≤ 10 in any of the 3 sessions before the breakout day. It's applied to 42,876 house breakouts
(1,455 names, 2019-10 → 2026-09). 40.6% are gated.

| cell (same date, other names, % per trade) | dates | gated | ungated | diff | t | halves |
|---|---|---|---|---|---|---|
| **PRIMARY** | 1,417 | +0.63 | +1.05 | **−0.43pp** | **−1.43** | −1.08 / +0.09 |
| held-the-level share | | 12.3% | 14.0% | **−1.7pp** | **−2.83** | |
| R (stop floor 2%, cap 20) | | +0.090 | +0.180 | −0.090 | −1.46 | |
| within low / mid / high extension tercile | | | | −0.06 / −0.53 / −0.55 | −0.15 / −1.52 / −0.95 | |
| ADR-tercile matched within date | 1,342 | | | −0.38 | −1.13 | −1.02 / +0.11 |

- **Per year:** negative in 6 of 8 years (2024 +1.07 and 2025 +0.58 are the exceptions).
- **Harness (paired rule):** vs `post` best-arm t 0.80, p_search 0.49. vs `xname` t −0.92, p_search 0.98. Fails.
- **Confound check:** gated breakouts are slightly *less* extended (0.30 vs 0.34 ADR) and have tighter stops (0.73 vs
  0.80 ADR), which should have helped them. The deficit holds within extension terciles, so it is not the
  entry-extension effect.

**Reading:** a breakout out of a tight 3-week range is, if anything, *less* likely to hold the level. Together with
the VCP null (swing geometry) this closes the "contraction precedes expansion *upward*" family on daily bars. His own
caveat was right: contraction says nothing about direction.

**Exploratory (Šidák k = 8, |t| ≈ 2.9; no verdict of their own):**

| cell | share | diff | t | halves |
|---|---|---|---|---|
| RMV5 ≤ 10 | 60% | −0.56 | −1.76 | −1.29 / +0.00 |
| RMV15 ≤ 5 | 32% | −0.04 | −0.13 | |
| RMV15 ≤ 15 | 49% | −0.70 | −2.52 | −1.04 / −0.43 |
| inner = 1-bar TR | 50% | −0.02 | −0.06 | |
| inner = ATR3 | 41% | −0.14 | −0.46 | |
| ⭐ **Brandt ADX(14) ≤ 12 at t−1** | **4.7%** | **+1.48** | **+2.87** | **+0.68 / +2.15** |

**One lead:** a breakout out of a *trendless* tape (ADX ≤ 12 the day before) is the only positive cell. It sits just
under the exploratory threshold, with both halves positive, on 4.7% of breakouts (784 dates). By the rules, it needs
its own pre-registered test with a paired rule and per-year check before it means anything. It's the opposite of
RMV's "tight *range*": ADX measures the absence of *trend*, not narrowness. `vol_compression.is_compressing` was in the
spec's list but was not run (a 252-day screen, a different object).

## WL-3b — Flanders 5-day breadth deferral (`run_breadth_deferral.py`, log `logs/breadth_deferral.log`)

**Verdict: NULL (primary) · lean at the extreme, UNDERPOWERED · YIELD MECHANISM (retrace trap again).**

b5 = share of eligible names closing above their own 5-day SMA; median 0.55. It's ≥ 0.80 on 11.8% of days and
≥ 0.90 on 2.6%. The trades are 2,014 precision-tier breakouts. A = enter at the breakout close. B = defer to the
first close within 10 sessions with b5 < 0.60 and ≤ 1 ADR above the level; otherwise abandoned at 0%.

| threshold | breakouts / dates | A (now) | B (defer) | **A − B** | t | halves |
|---|---|---|---|---|---|---|
| **b5 ≥ 0.80 (PRIMARY)** | 251 / 116 | +1.54% | −0.30% | **+3.03pp (deferring costs)** | **+1.24** | −0.93 / +7.73 |
| b5 ≥ 0.90 | 45 / 23 | −0.52% | +0.64% | −1.13pp | −1.57 | −2.02 / +0.26 |

- **What B's outcome was (primary):** 163 entered, 51 stopped out before any entry (A made −6.6% on those), 37
  abandoned. **The 37 abandoned names made +24.6% under A.** Among names that came back, B paid less (−0.46% vs
  −1.15%), but that subgroup is selected by its own outcome.
- **The A − B figure is 2024-driven** (+21.7pp in 2024; the other years are mixed and small).
- **Filter reading:** breakouts on b5 ≥ 0.80 days +1.54% vs ADR-matched other days +2.85% (date-level t −0.12).
  At ≥ 0.90: −0.52% vs +2.85% (t −2.18), and the panel's next 5 sessions in ADR units are −0.146 vs +0.088
  (t −2.18). Both are below the Šidák 2.8, on only 23 dates.
- **Independent of the activity gate:** rank correlation with cnt5_pct is −0.03, so it doesn't contradict the PARKED
  activity result.

**Reading:** deferring on a stretched tape fails for the same reason every "wait for the pullback" rule has failed
here. The names that don't come back are the big winners, and deferral skips exactly those. The one thing in
Flanders' favour is that at the extreme (≥ 90% of names above their 5-day) new breakouts and the next week look weak.
That's 23 dates, so it can't be tested to significance on this panel.

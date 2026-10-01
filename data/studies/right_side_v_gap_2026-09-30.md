# Right side of the V: index opening-gap fade (2026-09-30)

**Verdict: NULL (primary) · secondaries lean INVERTED · MECHANISM: the turn is paid for in price.** Source: Lance
Breitstein (`data/lance_breitstein/principles/right-side-of-the-v.md`). Pre-registration: `run_right_side_v_gap.py`
docstring. Log `logs/right_side_v_gap.log`. Data: SPY/QQQ RTH 1-min bars, 2007-01 → 2026-09. Fade gaps of
≥ 0.5 ATR14 toward the prior close, exit at the gap fill or 15:59, 1 bp per side. Stop and target are ordered on
1-min bars (a minute that touches both counts as the stop).

Arms:
- **A (left side):** fade at the first 5-min close, with no stop.
- **A_s:** the same entry, with a stop as wide as B's that day.
- **B (right side):** fade at the first 5-min close that breaks the prior 5-min bar's extreme. Stop = the session
  extreme so far.
- **R:** a random 5-min close in the same window, with the same stop logic.

| SPY, gaps ≥ 0.5 ATR (B fires on 1,067 of 1,092 days) | Δ bp/trade | t | halves 07–16 / 17–26 | years + |
|---|---|---|---|---|
| **PRIMARY B − A** | **+0.21** | **0.09** | +0.46 / −0.01 | 10/20 |
| B − R (trigger vs random minute) | −2.13 | −2.24 | −1.04 / −3.08 | 5/20 |
| B − A_s (width-matched left side) | −3.23 | −2.57 | −5.70 / −1.09 | 7/20 |
| QQQ B − A / B − R / B − A_s | +3.07 / −0.31 / −2.58 | 1.13 / −0.29 / −1.44 | | 12 / 7 / 8 of 20 |
| SPY gaps ≥ 0.25 ATR: B − A / B − R / B − A_s | −1.03 / −1.58 / −3.07 | −0.76 / −2.79 / **−3.85** | −5.85 / −0.49 (B − A_s) | 9 / 2 / 7 of 20 |

- **His mechanism does not show up.** The win rate does not rise once the stop is real. B wins 29.2% and the
  width-matched left side wins 28.0%. A's 48% is the no-stop artefact he describes. Expected value: B −2.5 bp,
  A −2.7, A_s +0.8.
- **The trigger itself is mildly harmful.** It is worse than a random minute in both SPY cells (t −2.24, −2.79;
  2–5 of 20 years positive), and the right side loses to a left side with the same stop (t −2.57, −3.85 on the wider
  sample). Neither clears the house |t| ≥ 3 on the primary-size cell with both halves strong. Recorded as a lean,
  not a finding.
- This is the confirmation ladder's result in intraday form: waiting for the turn buys a better-looking setup and
  pays for it 1-for-1 in entry price.
- The underlying index gap fade is negative at these fills on every arm (A on all gap days −4.9 bp SPY, −6.0 QQQ).

**Consequence:** no trigger rule is adopted. Breitstein's "same price, different EV" is not supported on index gaps;
his 4× EV arithmetic was assumed, not measured. The 98% firing rate also shows that "break of the prior bar" fires
on almost every day, as he concedes ("death by a thousand paper cuts").

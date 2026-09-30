# Sleeping Giants on a point-in-time S&P 500, vs same-date random S&P LEAPs, + cheap-IV gate (2026-09-29)

## Pre-registration
The full pre-registration (universe, detector, arms, vehicle, control, primary bar, IV gate, reported items) is the
docstring of `run_sleeping_giants_sp500.py`, committed with this file BEFORE any run. Do not edit either after results.

Primary in one line: arm B (enter on the breakout above the signal-time resistance) SG LEAP ROC minus the mean of 3
same-date random S&P-member LEAPs, +180 d exit, real fills; t on entry-date clusters ≥ 3, both halves (2020 split)
positive, majority of years positive; top-5 share reported. Secondary: call50_iv percentile ≤ 0.25 at the signal.

---

## Results (run 2026-09-29, after the pre-registration was committed in 0001f98; `run_sleeping_giants_sp500.py`, summary `.log`, trades `.csv`)

**Verdict: NULL — Sleeping Giants is LEAP beta. On a point-in-time S&P 500 its LEAPs earn what random S&P LEAPs bought
the same day earn; the original +94% was the hand-picked universe and a bull sample, measured against zero.**

772 ever-members 2013+, 604 with yfinance prices (~90% of member-weeks covered; 14+ delisted names missing).
999 SG episodes on 405 names; 66% broke out within 180 sessions; 5,248 LEAPs priced (62 split exclusions).

| arm | n | SG ROC mean / median | control mean | **excess mean / median** | t (bar 3) | halves (2014–19 / 2020–25) | top-5 share |
|---|---|---|---|---|---|---|---|
| **B breakout (PRIMARY)** | 514 | +18.4% / −40.5% | +15.6% | **+2.9pp / −6.3pp** | **0.29** | +16.6 / −5.3 | **3.06** |
| A signal date | 778 | +12.2% / −52.9% | +13.8% | −1.6pp / −13.6pp | 0.13 | −0.3 / −2.5 | n/a |
| B, cheap IV (pct ≤ 0.25) | 313 | +21.4% / −32.0% | +15.8% | +5.5pp / −6.0pp | 0.82 | +11.2 / +2.4 | 2.10 |
| B, not cheap IV | 197 | +15.2% / −53.5% | +17.1% | −1.9pp | −0.27 | +24.4 / −19.1 | n/a |

- **Top-5 share 3.06:** the five best episodes contribute three times the total excess, so the other 509 are net
  negative. Median excess is negative in every cut. Win rate vs control 46%.
- The underlying stock does not outperform either (+0.3pp): nothing about the setup selects the name.
- The real cheap-IV gate (99% coverage) points the right way (+5.5pp) but t 0.82.
- Exploratory: the in-sample best exit (ARM+50/TRAIL-30) is +3.4pp vs control — the exit lever is not SG-specific.
- Per year 9/12 positive, but 2020 −39, 2021 −14, 2024 −14; the original's "holds OOS" did not survive the universe.

**What it means for the book now.** Retire Sleeping Giants as a strategy (MARGINAL → NULL). Owning a 0.40Δ LEAP on a
large cap made ~+15% per 180 days in this sample whether or not the name was a "sleeping giant"; that is the
exposure, not an edge. The 9/27 quiet-knife veto stands (it was measured against the same kind of control).

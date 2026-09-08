# Adhikary-archetype detectors — validation 2019–2026

*2026-09-08. `run_adhikary_validation.py` replays the exact event definitions in `run_adhikary_scan.py` (recipe v1 of `tito_selection_playbook.md`) across the 1,765-name liquid panel, eligibility point-in-time (trailing-50 ADDV ≥ $50M), events 2019-10 → 2026-09. Forward returns at 5/10/21 sessions, excess vs the same-date every-stock baseline, and a simulated Tito hold: stop = close below the entry bar's low, exit = first daily close below the 20 EMA, capped at 60 sessions; R = return ÷ (entry − entry-day low). Survivorship: the universe is today's liquid names, so absolute levels are flattered; read the relative comparisons.*

## Verdict

The recipe reproduces the *shape* of his winners (29% win rate, losers at −1R, a fat right tail) but as written it carries almost no edge at the stock level. Three of its levers do nothing, one is inverted, and one narrow cohort is worth keeping.

| Detector | n | 10s excess | t | 21s raw | mean R | median R | R win | stopped |
|---|---|---|---|---|---|---|---|---|
| A breakout, 15d pivot, recipe as written | 6,685 | +0.10pp | 1.3 | +1.25% | +0.16 | −1.08 | 29% | 58% |
| A without the ADR ≥ 3 gate | 13,017 | +0.01 | −2.4 | +0.38% | +0.04 | −1.02 | 32% | 52% |
| A with a 50d pivot instead of 15d | 6,436 | +0.10 | 1.2 | +1.24% | +0.18 | −1.08 | 29% | 58% |
| A not stacked (<5d) | 8,479 | +0.11 | 1.5 | +1.42% | +0.18 | −1.01 | 31% | 51% |
| A preceded by a SETUP day (contraction + dry-up) | 1,467 | **+0.56** | 1.9 | +1.17% | +0.09 | −1.04 | 30% | 55% |
| B catalyst (gap/8% day, ≥2× vol, clears pivot) | 2,139 | +0.25 | 0.5 | +1.30% | +0.11 | −0.57 | 35% | 33% |
| C exhaustion, daily proxy (long returns shown) | 423 | **+0.46** | 0.7 | **+1.78%** | +3.15 | −2.08 | 19% | 78% |
| SETUP day itself | 17,109 | +0.07 | −0.1 | +2.20% | +0.73 | −1.36 | 23% | 66% |

- **ADR ≥ 3 gate: keep.** Dropping it halves mean R. Inside the gate, 4–7% is the sweet spot (ADR 4–5: +0.70pp excess, R +0.38); ADR > 10% is negative (R −0.57).
- **15d local pivot vs 50d pivot: identical.** The "local base" refinement changes nothing; nearly every 15d break is also a 50d break.
- **Stack ≥ 5d: adds nothing.** Non-stacked breaks did marginally better. Stack > 40 days is negative (late-stage, R −0.09).
- **Breakout RVOL (1.1 → 3): no monotone edge** at 10 or 21 sessions. His "loose volume" is right; the 1.5–2.0 bucket is the worst.
- **Distance from the 52-wk high: within 5% is best** (r21 +2.5%, R +0.33); breakouts >30% off the high are negative. Same finding as the August regime validation: laggard breakouts lose.
- **SETUP list is the one thing with a signal.** A setup day raises the chance of a pivot break within 10 sessions from 44.9% to 56.7%, and breaks that follow a setup carry +0.56pp 10-session excess (t 1.9). It does not improve R, which says the contraction predicts the *break*, not the *run*.
- **B catalyst: noise.** Sign flips by year (2024 +3.6pp, 2021 −2.0pp). Chasing the close of a catalyst day has no edge here, consistent with the August EP finding.
- **C exhaustion, daily version: inverted.** A new 20-day high that closes near its low on ≥2.3× volume is followed by +1.1% at 10 sessions and +1.8% at 21. On daily bars it is a continuation signal, not a top. The playbook already says the daily detector is only a candidate-narrower for an intraday 0DTE trade; this confirms the daily bar must not be shorted on its own. The intraday version remains untested (blocked on intraday data).

## Regime dependence

Mean R of the A recipe by year: 2019 −0.30, 2020 −0.04, 2021 −0.21, 2022 −0.43, 2023 +0.21, 2024 +0.41, 2025 +0.58, 2026 +0.28. Negative four years running, positive four years running. Whatever edge exists is a 2023–2026 phenomenon, and the survivor universe is most flattering in exactly those years.

## What survives: the precision tier

Combining the three levers that each tilted positive (ADR 4–7, within 15% of the 52-week high, stack 5–40 days):

| Cohort | n | 10s excess | 21s raw | mean R | R win | R positive in years |
|---|---|---|---|---|---|---|
| All A | 6,685 | +0.10 | +1.25% | +0.16 | 29% | 4 of 8 |
| **ADR 4–7 & off-high > −15% & stack ≤ 40** | 1,824 | **+0.67** | **+2.67%** | **+0.67** | 31% | 6 of 8 (2019 −0.09, 2021 −0.27) |
| … and preceded by a SETUP day | 356 | +1.32 | +2.11% | +0.57 | 33% | 4 of 8 |

The precision tier quadruples mean R on a quarter of the events and is the only cohort with a positive R in the 2022 bear (−0.07, effectively flat) as well as the bull years. Adding the SETUP requirement on top raises the 10-session excess but drops n to 356 and the by-year R turns noisy, so SETUP is better used as the *alert list* (it anticipates the break) than as a gate on the break.

## Implications

1. `run_adhikary_scan.py` now flags a **precision** column on the A and SETUP blocks: ADR 4–7, within 15% of the 52-week high, stacked 5–40 days. Trade those; treat the rest of the A block as context.
2. The C block is relabelled a **daily proxy only**. Do not short it from the daily bar.
3. The B block stays for awareness but has no validated edge; the ROIV-type print needs the pivot to hold in the cash session and is still a coin flip on this data.
4. The stock-level system is a 29–31% win, +0.16 to +0.67R book. That only works with his two other halves: losers cut at −1R without exception, and a convex vehicle plus sell-the-spike on the winners. Neither is tested here; the vehicle study says naked calls on 0-day holds are the wrong instrument, so the vehicle for this tier is the recipe's own: ≥15 DTE, 0.2–0.35 delta, scaled out at 200–300% on a spike, trailed on the 20 EMA close otherwise.

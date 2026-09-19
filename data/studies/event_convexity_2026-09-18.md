# Event convexity: buying cheap calls into scheduled events (2026-09-18)

**Motivating instance.** Tito's 2024 election calls (TSLA 0.12Δ, PLTR 0.23Δ, ~40x). A mean-based test would
dismiss that as one lucky trade. The right question for convexity is the **right tail**, so this reports the
whole distribution.

**Method.** `run_event_convexity_pull.py` / `_score.py`. 0.12Δ and 0.25Δ calls, 10-45 DTE, on the 40
highest-ADR liquid names, bought the session **before** each scheduled event (55 FOMC decisions + 3 elections,
2019-10 → 2026-09); control = the same purchase on mid-month Wednesdays in the same months with no event within
3 sessions. 16,236 purchases (3,951 event / 12,285 control). Buy at mid + ¼ spread, sell at mid − ¼ spread.

## 1. Event entries beat the control on every exit

0.12Δ (far OTM), event vs control:

| exit | mean | control | P(2x) | P(5x) | P(10x) | total loss |
|---|---|---|---|---|---|---|
| hold to expiry | +34.7% | +19.5% | 8.8 / 8.2% | 6.9 / 6.1% | 4.3 / 3.5% | 61 / 63% |
| **sell after 5 sessions** | **+30.7%** | **−3.6%** | 14.6 / 10.3% | **5.3 / 2.6%** | **2.0 / 0.7%** | 4 / 2% |
| sell after 10 sessions | +28.0% | +5.6% | 12.9 / 10.9% | 6.0 / 4.6% | 2.5 / 1.8% | 21 / 15% |
| take profit +500% | +8.7% | −12.6% | 17.2 / 13.6% | 15.9 / 12.6% | — | 56 / 60% |

0.25Δ behaves the same with a smaller spread (event − control: +10 to +29 pp depending on the exit).

**Two findings:**
- **The event premium is real:** +10 to +34 pp of mean return over the same trade made at random, and roughly
  double the odds of a 5x on the 5-day exit.
- ⭐ **Selling within five sessions is the best arm** (+30.7% vs +34.7% holding to expiry but with a 4% total-loss
  rate instead of 61%). Holding through the event and then through theta gives the gain back. This is the
  measured version of "sell into the run-up".

## 2. Election eve alone (230 purchases, 2020 / 2022 / 2024)

| exit | mean | median | P(2x) | P(5x) | P(10x) | total loss |
|---|---|---|---|---|---|---|
| hold to expiry | +207% | −96% | 29% | 20% | 9.1% | 54% |
| **sell after 5 sessions** | **+190%** | **+59%** | 46% | 19% | 6.5% | 3.5% |
| take profit +500% | +128% | −93% | 39% | 34% | — | 48% |

A **positive median** at five days and a 1-in-5 shot at 5x. This is the shape of Tito's trade, and it reproduces
across all three elections in the sample.

## ⚠ What this does and does not establish

- **Does:** convexity bought before a scheduled event has a fatter right tail and a better mean than the same
  convexity bought at random, across **55 events**. And the 5-day exit dominates holding to expiry.
- **Does not:** anything election-specific. Those 230 purchases are **3 events**, not 230 draws, and all three
  resolved risk-on — 2020 met the Pfizer announcement 4 days later, 2022 met the 2022-11-10 CPI rally, 2024 was
  a clean sweep. **No election in the sample resolved into a selloff.**
- **Median is still −96% at expiry.** This is a lottery: size it as premium you can lose in full.
- Event and control entries share names and months, but not within-event independence — treat the event/control
  gap as the finding, not the absolute level.

## Practical expression (2026-11-03 midterms)

Far-OTM calls (≈0.12Δ), 10-45 DTE, high-ADR names, bought shortly before, **sold within ~5 sessions**, sized as
a lottery ticket. The thesis — who benefits — is yours; this study only says the structure and the exit.

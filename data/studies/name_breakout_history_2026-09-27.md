# Per-name breakout history as a selection signal — NULL (2026-09-27)

**Prompt (Gabe):** Luk checks individual stocks' historical price action. Do some names behave differently on breakouts, so that pooling them loses signal?
**Script:** `run_name_breakout_history.py`. The pre-registration is in its docstring and was frozen before the run. **Log:** `data/studies/logs/name_breakout_history.log`. Events: `logs/name_breakout_history_events.csv`.

## Design (one line each)
- Data: liquid_panel_2009 (2009-02 → 2026-08). House breakouts (close > prior 20-day high, ADR ≥ 3), de-clustered with a 10-session gap: 19,659 events across 1,461 names.
- Outcome: 20-session % return from the close entry, minus the mean of that day's other breakouts. The date is held fixed and only the name varies.
- Signal: the name's shrunk mean excess over prior breakouts whose outcomes had completed (k0 = 5, n ≥ 3), split into terciles within each year.
- Control: the name's own drift (mean date-demeaned return on all prior days) plus 12-1 momentum, in a month-clustered regression.

## Result
| cell | top − bottom (pp) | t | halves (pp) | TR t after drift/mom |
|---|---|---|---|---|
| **PRIMARY h20 k0=5 n≥3** (15,543 events, 199 months) | **−0.39** | **−1.13** | −0.88 / +0.06 | +0.59 |
| k0=0 / k0=20 / n≥6 | −0.30 / −0.41 / −0.50 | −0.87 / −1.19 / −1.34 | mixed | ≤ 1.2 |
| h5 / h60 | −0.14 / −0.73 | −0.70 / −1.00 | mixed | ≤ 0.1 |

- Per year: the spread's sign changes 9 times across 18 years (full table in the log).
- Split-half per-name rank correlation (125 names with ≥ 10 events in each half): **+0.023**. The within-date shuffle null gives 95th percentile +0.144 and p = 0.42, so this is indistinguishable from noise. Row 187's gap-reclaim trait at least reached 99th-percentile noise; this one does not.
- The drift placebo sort is also null (−0.43pp, t −1.16).

## Verdict
**NULL · YIELD REFRAME.** A name's own breakout track record predicts nothing about its next breakout. The spread even leans negative, meaning names whose breakouts worked before do slightly worse next time, but that lean is not significant. Taken with row 187 (tactic affinity, ~90% noise) and rows 188–189 (gap share, a risk-shape trait only), the finding is that stocks differ in the *shape* of their risk, not in which setups work on them. Pooling is the correct expectation. When Luk reads a name's history, the defensible use is sizing and stops (ADR, gap share), not selection.

Caveats: the panel is built from names that are liquid today, which adds survivorship. The date-demeaned contrast is unaffected. The power is adequate: ~15.5k events and 199 months of monthly spreads, with an SE of about 0.35pp.

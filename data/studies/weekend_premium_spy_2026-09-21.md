# Weekend premium in SPY 1-day options, and its overlap with the positive-gamma fly (2026-09-21)

## Pre-registration (written BEFORE this analysis ran; do not edit this section after the results)

**Why.** A diagnostic in the post-shock study (NOT a verdict) showed Friday → Monday 1-day SPY straddles realising
0.86–0.89 of implied vs 0.94–0.96 for next-calendar-day ones, in both eras. Options decay in calendar time; prices
move in trading time. The positive-gamma fly's sample includes these Friday entries, so part of its edge could be a
weekend effect.

**Data and trade.** Exactly the positive-gamma fly's setup (gex_spy_ironfly_2026-09-21.md): entry at day d's close
into the expiry settling on the NEXT trading day, ATM by call delta nearest 0.50, **2× iron fly** (wings at K ± 2 × the
straddle mid, nearest listed strike), house fills, settle at SPY's close; `SPY_short_expiry_quotes.parquet`,
2010 → 2026-02. **WEEKEND = the expiry is ≥ 3 calendar days after entry** (Friday → Monday, incl. long weekends);
WEEKDAY = 1 calendar day. GEX sign as in the fly study.

**Test W1 (weekend premium).** Weekend flies (any gamma): mean return on max risk at the real fill > 0 with t ≥ 3
(one trade per entry day), positive in both halves (2010–2017 / 2018–2026-02, where 2010–17 weekend entries exist),
AND higher than weekday flies. Short straddle reported alongside.

**Test W2 (overlap with gamma, decisive for the live paper trade).** 2 × 2 cells (weekend/weekday × positive/negative
gamma) and the regression ret = a + b·WKND + c·POS + d·WKND×POS (HC robust). **The positive-gamma edge survives
without weekends if, on WEEKDAY entries only, positive-gamma flies beat negative-gamma flies with t ≥ 2** (a
robustness check of an existing result, hence the lower bar).

**Not tested:** other structures, entries on other days of the week, holiday-only effects, other tickers.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_weekend_premium.py`, log `.log`, table `.csv`)

**Verdicts: W1 (weekend premium, as a fly) FAIL · W2 (gamma edge survives without weekends) PASS.** 1,942 entries:
412 weekend (Friday → Monday; SPY Monday expiries only really exist from 2018 — 6 weekend entries before), 1,530 weekday.

**W1.** Weekend 2× fly +3.4% on max risk (t 1.3) vs weekday −0.9%: +4.3pp, Welch t 1.5. The weekend options ARE
richer (realised/implied 0.89 vs 0.95; short straddle +10.5% vs +4.0%), but the fly's capped payoff doesn't turn that
into a reliable edge, and with almost no pre-2018 weekend entries there's effectively one era. Not a standalone trade.

**W2.** 2 × 2 cells, 2× fly return on max risk:

| | negative gamma | positive gamma |
|---|---|---|
| weekday | −6.1% (n 813, t −3.1) | **+4.9% (n 717, t 2.5)** |
| weekend | −2.4% (n 201) | +8.9% (n 211, t 2.7) |

Regression (HC robust): positive gamma **+11.0pp (t 3.9)**, weekend +3.7pp (t 0.8), interaction +0.4pp (t 0.06).
**On weekday entries alone, positive vs negative gamma = +11.0pp, Welch t 3.9, both halves** (2010–17 +7.4% vs −1.3%;
2018–26 +4.1% vs −8.0%). The two effects are separate and roughly additive; **the gamma edge is not a weekend
artefact.** The live paper trade stays as built (all days, positive gamma). Not acted on: weekend × positive-gamma is
the best cell (+8.9%), but slicing further after the fact would be fitting.

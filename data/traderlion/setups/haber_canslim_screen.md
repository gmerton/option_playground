# CAN SLIM Leader Screen (RS-sorted + C/A fundamentals) -- Ross Haber

> **Verdict:** An O'Neil-lineage screening routine. Three broad Deepvue screens are sorted by 12-month RS, then
> cut by eye for "tight and orderly" charts, and finally by CAN SLIM fundamentals: quarterly EPS YoY ≥ 25% for
> 3+ quarters, accelerating, confirmed by sales. Zero evidence on camera. Our ledger already answers the
> technical half: RS12 = TT c9 (UNDERPOWERED); low ADR is contradicted by HYB-B; group confirmation is NULL; the
> "leaders outperform in corrections" sibling is INVERTED. ⭐ **The fundamental half has never been tested
> here**, and its EPS leg is codable on cached data.
> **Type:** universe / watch-list selection (not an entry) · **Instrument:** US equities, liquid growth names
> **Conviction:** 2/5 · **Risk:** 4/10 (as a universe filter; his 10-20% positions on 1-2% stops: 7/10) ·
> **Tested?** **partial** (technical half answered by existing rows; fundamental half NOT RUN)
> **Source:** [notes](../videos/interviews/2026-09-23_afkUTFNVpso/notes.md) (TraderLion bootcamp session 1,
> 2026-09-23, 2 h)

---

## 1. Who, and what's being sold

Ross Haber is an ex-William O'Neil + Co. money manager (from 1998), co-ran O'Neil's workshops, and was later
the technical half of a ~$660M (with margin) growth fund. All of this is self-reported and unaudited. The host,
Richard, built the "DV Leaders" preset and is a Deepvue co-founder. The session sells the TraderLion bootcamp
(free now, "paid in the future"), a Deepvue discount and IBD.

## 2. Mechanics (codable form)

**Stage 1: broad screens, sorted by RS12 descending** (`RS12 = 2·C/C[63] + C/C[126] + C/C[189] + C/C[252]`,
percentile; identical to `run_universe_test.py`):
- *Up on Volume:* `close > prior close ∧ vol / avg50 ≥ k` (k not stated on camera);
- *DV Leaders:* proprietary (liquidity + RS + EPS growth + sales growth, recency-weighted);
- *"Ry 62.5%":* outperformed SPY on ≥ 62.5% of days during a correction, ∧ avg volume ≥ 250K.

**Stage 2: personality (by eye):**
- 10/20-day ADR ~2–4% preferred, ≥ 6% avoided;
- not a "retracer" (alternating inside/outside days);
- liquid enough to exit at market;
- off the list after 2–3 closes under the 21-day.

**Stage 3: fundamentals (the deciding cut, "70% fundamentals"):**
- **C:** quarterly EPS YoY ≥ 25% for ≥ 3 consecutive quarters (triple digits preferred), **accelerating**;
- sales growing to confirm (waived for big steady sales with no earnings);
- **A:** annual EPS and sales ≥ 20–25%;
- big forward estimates; quality-fund accumulation; group confirmation in early-stage bases.

## 3. Claimed edge

None quantified. The one statistic, "7–9 of 10 early-stage CAN SLIM breakouts never fall > 7% from the pivot"
[1:17], is relayed from O'Neil without a source.

## 4. What our data already says

| piece | row | result |
|---|---|---|
| RS12 ≥ 70 | TT ablation c9 | −0.090pp, t −0.95: UNDERPOWERED |
| TT as a whole | universe test | +0.56 ADR-matched, t 1.30: weakest of 5 |
| low ADR preference | universe test | HYB-B (ADR ≥ 4) best, +1.79, t 2.60, PARKED |
| liquidity | TT ablation c10 / within-date rank | floor helps (−0.259pp); dolvol sort t 3.48 but all 2025–26 |
| group confirmation | theme co-breakouts [WL-5h] | NULL, +1.61pp t 1.80; leading-group INVERTED |
| outperform in corrections | down-day RS | INVERTED, −3.51pp at 63d, t −3.33 |
| EPS surprise | PEAD | NULL |
| **EPS growth level / acceleration** | none | **never tested** |
| sales / estimates / institutions | none | no data |

## 5. Testability

- **EOD-testable now:** C (EPS growth, 3-in-a-row, acceleration) on `data/cache/earnings_yf.parquet`
  (1,330 names from 2002; 1,303 on the liquid panel). Measured: C fires on 8.8% of 2019+ report events (3,200
  events, 793 names).
- **Needs a new pull:** quarterly sales from SEC EDGAR companyfacts (~1 day).
- **Untestable:** estimates and revisions (no history), institutional quality (no 13F), N, DV Leaders
  (proprietary).

## 6. Proposed test (NOT RUN, not queued)

**INT ∧ C vs INT**, paired per non-overlapping 20d date, ADR-decile matched, membership as of the prior close,
on `liquid_panel_2009.parquet`, 2010–26.
- **Secondaries:** C alone vs panel; acceleration; YoY ≥ 100%; 63d; excluding 10 sessions after each report
  (the PEAD confound).
- **Bar:** paired t ≥ 3 + halves + per-year; Šidák k = 5 on the secondaries.
- **Effort:** ~½ day, local. **Prior:** low-moderate.

Full pre-registration draft in the notes, "Not tested, could be" §1.

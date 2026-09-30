# Pre-earnings IV ramp on a 30–45 DTE straddle (2026-09-30)

## Pre-registration (written BEFORE any chain was pulled; do not edit this section after the results)

**Why.** `earnings_ramp_2026-09-20.md` found the pre-print IV ramp is real (+40 to +57 vol points on the FRONT
expiry) but a front-expiry ATM straddle bought 3–10 sessions out and sold on the pre-print session loses even at
mid (−3.4 / −6.9 / −14.3%): theta outruns vega. Its named follow-up, never run: the same trade on a **30–45 DTE**
expiry, where theta per day is far smaller but the ramp in vol points is also smaller (the event variance is
spread over more days). Which side wins is an open question. TEST_INDEX has no back-tenor ramp row (checked).

**Events.** `data/cache/earnings_yf.parquet` (report timestamp → BMO/AMC), names in `liquid_panel_2019.parquet`,
prints 2019-02-01 → 2026-02-27 (bid/ask coverage ends ~Mar 2026), BMO/AMC only (midday dropped), 20-session mean
dollar volume ≥ $50M as of the entry date. **Pre-print session P** = the session before the report for BMO, the
report session itself for AMC (the last close with the event still ahead). Entry E = P − 5 sessions (PRIMARY);
−3 and −10 reported.

**Trade.** At E's close, the expiry whose DTE is nearest 37 within [30, 45] (must also be after the print, which
it is by construction); the ATM strike = the strike whose call and put mids are closest (same rule as the parent
test). Sell the SAME two contracts at P's close. Both legs need bid > 0, ask ≥ bid at E and P. Return = % of the
entry cost. Three fills: mid; **house** (`lib.studies.costs`: mid ± 25% of the quoted spread, + $0.65/contract/leg/
side); crossing (buy ask, sell bid).

**Control — what it varies.** For each event, up to 3 names drawn at random (seed fixed) from the panel's ≥ $50M
names on the same E, with **no earnings report from E through the control option's expiry**, traded identically
(same E and P dates, same tenor rule, same fills). It holds the dates fixed, so market-wide vol moves, the day-of-week
and the holding length cancel; it varies only "an earnings print is inside the option". Edge = event return −
mean of that event's control returns.

**PRIMARY.** −5 session entry, house fill: paired edge vs control, mean > 0 with **t ≥ 3** clustered by P date,
AND the event trade's own house-fill mean > 0 (a trade must make money, not just lose less), AND both halves
(prints 2019–2022 / 2023–2026-02) the same sign on the edge. Per-year table reported. One primary cell, no
multiple-testing charge; the 3 entries × 3 fills are exploratory.

**Mechanism reported alongside (no verdict):** ATM IV at E and P for the back tenor vs the parent's front-tenor
ramp; the event's vega P&L vs theta at mid.

**Not tested (named so they can't be added quietly):** other tenors (60/90 DTE), calendars or any short leg,
holding through the print, IV or liquidity gates on the entry, single-name or sector selection. One run.

**Where it runs.** Local: one Athena join for the event and control chains (2019–2026, a few minutes), then pandas.

---

## Results (run 2026-09-30, after the pre-registration above; `run_earnings_ramp_back_tenor.py`, log `logs/earnings_ramp_back_tenor.log`)

**VERDICT: NULL (FAIL as a trade) · YIELD MECHANISM.** 17,056 prints on 1,072 names; 10,612 priced at the −5 entry
(median 37 DTE); 9,945 with ≥ 1 same-date control (mean 2.37).

| entry | n | ATM IV in → out | ramp | MID | HOUSE | CROSS | t (house, by date) | rt spread | neg yrs |
|---|---|---|---|---|---|---|---|---|---|
| −3 | 9,601 | 0.432 → 0.448 | +1.7 vp | +0.79% | −6.26% | −11.70% | −25.1 | 18.5% | 8/8 |
| **−5** | 10,612 | 0.422 → 0.445 | +2.3 vp | **−0.06%** | **−7.15%** | −12.63% | −23.5 | 18.7% | 8/8 |
| −10 | 11,021 | 0.412 → 0.463 | +5.1 vp | −5.71% | −12.14% | −17.09% | −34.7 | 17.0% | 8/8 |

**Primary (−5, house fill):** event −7.14% (t −23.3); controls −9.51%; **paired edge +2.37pp, t 13.4**, halves
+1.93 / +2.83, positive in 8/8 years. The pre-registered PASS required the event trade itself to make money; it
loses in every year. **FAIL.**

**What it says.** Moving to the back tenor fixed the parent's problem: theta no longer beats vega. At mid the
trade breaks even (−0.06%, versus −6.9% on the front expiry) and the earnings print is worth a real +2.4pp over an
identical no-earnings straddle (the ramp is +2.3 vp vs +0.3 vp for controls). But a 37-DTE straddle's round trip
costs ~19% of its price in spread, so any fill short of mid gives it all back and more. The edge-vs-control is the
ramp itself (a mechanism, like the parent's +47 vp): it is not a trade, because the counterfactual isn't "buy a
no-earnings straddle", it's "don't trade". ⚠ Don't read t 13 as a signal: both arms are long straddles, so it only
says earnings straddles lose LESS.

**Closes the ramp line.** Front tenor: theta wins. Back tenor: spread wins. A long-vega harvest of the ramp needs
a cheaper vehicle than an ATM straddle (a calendar or other structure with a short leg), and those are outside this
registration.

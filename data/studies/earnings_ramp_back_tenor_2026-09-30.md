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

## Results

*(pending)*

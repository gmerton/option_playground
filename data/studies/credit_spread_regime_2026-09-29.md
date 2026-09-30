# Credit-spread widening as a regime input: does it predict equity returns / vol beyond VIX? (2026-09-29)

## Pre-registration (written BEFORE any outcome was computed; do not edit this section after the results)

**Why.** New axis for the ledger (no credit-spread test on file). Eisman's 9/24 argument points at credit (AI SPV debt,
Oracle BBB−, SoftBank junk), and the book's regime inputs (SPY trend × breadth, GEX sign, VIX) have no credit
component. Question for trading now: does credit widening tell us something about the next month that VIX and the
tape don't already?

**Data.** FRED `BAA10Y` (Moody's Baa corporate yield − 10y Treasury, daily, 1986→; the ICE HY OAS on FRED is now
truncated to 3 years, so it cannot be used); yfinance ^GSPC, ^VIX (1990→); HYG and IEF (2007→) for a high-yield proxy.
Signal known at the close of day t; outcomes start t+1.

**Signal.** ΔCS = 20-session change in BAA10Y (percentage points). 
**Outcomes.** (1) S&P forward 21-session log return; (2) S&P forward 21-session realised vol (log, annualised from
daily closes).
**PRIMARY (two, Šidák-2 → |t| ≥ 3.2 each), daily observations 1990-01 → 2026-08, Newey-West 21 lags:**
- **P1 returns:** fwd21 return ~ ΔCS + VIX(t) + S&P trailing 21-session return. Pass iff ΔCS coefficient < 0,
  |t| ≥ 3.2, same sign in both halves (1990–2007 / 2008–2026).
- **P2 vol:** log fwd21 RV ~ ΔCS + log VIX(t) + log trailing-21 RV. Pass iff ΔCS coefficient > 0, |t| ≥ 3.2, same sign in
  both halves.
**Reported, not in the bar:** the level of BAA10Y (trailing-252 percentile) in the same regressions; a flag version
(ΔCS ≥ +0.30 pp) → P(≥ 10% S&P drawdown within 63 sessions) vs not; the HYG−IEF 20-session relative return (2007→) as
a high-yield replication of P1/P2; 2010–2026 with SPY GEX sign added as a control (does credit add beyond our GEX
regime?); today's reading.

**Read.** A pass in P2 alone = credit is a vol input (sizing / premium-selling gate), not a direction call. A pass in P1 =
a directional regime input. Neither = credit adds nothing to VIX + tape for our purposes.
Local (FRED + yfinance), minutes.

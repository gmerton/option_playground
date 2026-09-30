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

---

## Results (run 2026-09-29, after f9f3b17; `run_credit_spread_regime.py`, `.log`)

**Verdict: P1 NULL · P2 UNDERPOWERED (near miss). Credit widening says nothing about the next month's direction beyond
VIX and the tape, and only a little about vol — most of which our GEX regime already carries.**

9,230 daily observations, 1990-01 → 2026-08, NW 21 lags.

| test | ΔCS coefficient | t (bar 3.2) | halves (1990–2007 / 2008–2026) |
|---|---|---|---|
| **P1 fwd 21d return** | −0.0002 | **−0.01** | +0.016 (t 1.07) / −0.005 (t −0.22) |
| **P2 fwd 21d log RV** | +0.164 per pp | **3.03** | +0.20 (t 2.34) / +0.16 (t 2.43) |

- P2: a +0.30pp widening over 20 sessions ≈ +5% higher next-month realised vol beyond VIX and trailing RV. Same sign
  both halves, t 3.03 < 3.2 → UNDERPOWERED. Since 2010 with the SPY GEX sign added: ΔCS t 1.53, GEX t 2.00 — credit adds
  little beyond the regime input we already use.
- Flag (ΔCS ≥ +0.30pp, 4.2% of sessions): P(≥ 10% drawdown in 63 sessions) 26.8% vs 13.2%, but forward 21d return
  +1.27% vs +0.68% — widening marks a two-tailed, high-vol state, not a sell signal.
- Level (percentile) and HYG − IEF: P2-type vol links t 2.3, no return link. (HYG's "first half" is only 2007-04 →
  2007-12 and is not interpretable.)
- **Today:** BAA10Y **1.46** (2026-09-28), 20-session change **−0.08pp**, the **3rd percentile of the last year and 2.6%
  since 1986** — credit is about as tight as it gets and not widening.

**What it means for the book now.** No new regime input. Credit is calm despite the 5.2% 10-year; the vol-sizing lead
is UNDERPOWERED and mostly redundant with GEX. If it's ever added, it belongs as a vol/sizing flag (widening ≥ 0.30pp),
never a direction call.

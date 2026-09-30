# Steve Eisman, "The Weekly Wrap" (recorded 2026-09-24) — video vKLPLywZcp0

Source: YouTube auto-captions (en-orig), `transcript.txt` in this folder. ~28 min; 4,240 words.

## What it is
Macro/credit commentary from a famous short-seller (The Big Short). Topics: Iran war, oil and the 10-year; Oracle's
force-majeure notice to Blue Owl on the Project Jupiter data center (debt ~90c); Paramount antitrust settlement;
SoftBank raising $11B junk to fund a $10B OpenAI equity stake; AI circular financing and **off-balance-sheet SPVs**
(Meta's $27B "Beignet" VIE, flagged by EY as a critical audit matter; Enron/SIV history); Meta's Muse agent and
brand-advertising cannibalisation; mailbag on shorting against the box (IRC 1259). Includes sponsor reads (Webroot,
SelectQuote) and Substack promotion.

## Claims
| # | claim (timestamp) | type | testable here? |
|---|---|---|---|
| 1 | "The only two variables that matter right now are oil prices and the 10-year yield… neither predictable" [00:00, 02:50] | regime framing | partly — "unpredictable" agrees with our oil map (no lag / no continuation edge) |
| 2 | **"Should the 10-year remain above 5%, a correction is probably imminent"; 5% is "the Rubicon"** [03:30] | directional, dated | ✅ yes — index-level, 1962→ |
| 3 | Hyperscaler capex (~$700B) has consumed their free cash flow; off-balance-sheet SPV debt is returning, ratings agencies will under-count it [15:00–21:00] | fundamental / credit | no (no credit or 10-K data in the repo); logged as a thesis |
| 4 | Oracle nervous about cash flow; Project Jupiter debt at stress levels [04:00] | single-name credit | no |
| 5 | Agentic AI (Muse) shifts spending, lacks moats, cannibalises brand ads [22:00–25:00] | narrative | no |

## Pre-registration for claim 2 (written BEFORE the run; do not edit after the results)
**Data.** yfinance ^TNX (10-year yield, ×1) and ^GSPC closes, 1962-01 → 2026-09-25. Correction = a ≥ 10% peak-to-trough
decline in ^GSPC closes. Signal known at the close; everything forward starts the next session.
- **C1 (literal state, PRIMARY):** 10y close > 5.00% vs ≤ 5.00%. Outcomes on NON-OVERLAPPING 63-session blocks (sampled
  every 63rd session): (a) forward 63-session S&P return, (b) whether a ≥ 10% drawdown from the entry close occurs
  within 63 sessions. Stat: difference (>5% minus ≤5%), Welch t on blocks. **Claim supported only if** (b) is higher
  AND (a) lower with |t| ≥ 3, same sign in both halves (1962–1993 / 1994–2026).
- **C2 (the "Rubicon" crossing, descriptive):** every first close above 5.00% after ≥ 60 sessions at or below it;
  list each with the forward 63-session return and max drawdown. Too few events for a t; reported as a table.
- **Known confound, stated now:** > 5% was the norm 1966–2002 and rare since 2008, so C1 is largely an era split. The
  halves check is the partial guard. Local, minutes.

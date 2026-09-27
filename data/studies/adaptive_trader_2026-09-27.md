# Simulated adaptive trader (2026-09-27)

`run_adaptive_trader.py` (pre-registered in its docstring, committed before the run). Log `logs/adaptive_trader.log`.
Spec = the TEST_INDEX §10 row with both 2026-09-26 amendments (knob adaptation; runs test + Turtle arm).

## Verdict: NULL — reacting to your own results doesn't pay, even though results DO cluster

**Part 0, runs test** on the 2,226 house breakouts (2009–2026), outcomes ordered by exit: **z −10.65, strong
streaking.** Check (after the run): one outcome per exit date z −5.17, per week −3.48, per month −2.06, monthly
lag-1 autocorrelation +0.05. So good and bad *weeks* for breakouts cluster (common market shocks; 29% of trades exit
on days with ≥ 5 exits), and it fades by the month.

**Part 1, sizing feedback** (notional 10% of equity × multiplier; event-ordered, only trades closed before entry
inform a rule; control = 1,000 within-year shuffles of outcomes):

| rule | log wealth | CAGR | max DD | vs FIXED (real) | value of feedback vs shuffle | p |
|---|---|---|---|---|---|---|
| FIXED | +0.888 | +5.1% | 54.0% | — | — | — |
| AM_STREAK (size up after 3 wins) | +0.583 | +3.3% | 45.8% | −0.305 | −0.255 | 0.91 |
| AM_20 (trailing 20 trades) | +0.844 | +4.8% | 44.4% | −0.044 | −0.592 | 0.96 |
| DD_CUT (halve size in a 15% drawdown) | +0.521 | +2.9% | 37.7% | −0.368 | −0.186 | 0.94 |
| QUIT (28-day pause after 6 losers) | +0.418 | +2.3% | 37.9% | −0.471 | +0.002 | 0.51 |
| TURTLE_SKIP (skip after a winner) | +0.121 | +0.7% | 7.2% | −0.767 | +0.684 | 0.000 |
| TURTLE_SIZE (half after win, 1.5× after loss) | +0.923 | +5.3% | 65.9% | +0.035 | +0.057 | 0.45 |

No rule clears the bar (p ≤ 0.0083 AND a gain over FIXED in both halves). TURTLE_SKIP beats its own shuffle
(p 0.000) but still loses to FIXED (−0.77 log wealth; halves +0.36 / −1.16): it mostly just stops trading (max DD
7%, CAGR 0.7%). The anti-martingale "push the gas after winners" rules lose outright, both in the real order and
against their shuffles. The drawdown rules (DD_CUT, QUIT) cut max DD from 54% to ~38% at the cost of ~half the
growth: risk reshaping, not an edge.

**Part 2, knob adaptation** (precision pool 2019-10 → 2026-09, 2,016 trades, evaluated from 2020-07; control = 1,000
month-order permutations of the selection history):
- **ADAPT3 (primary): +2.35%/trade vs HOUSE +2.76% → −0.41pp, t −0.98**, halves +0.12 / −0.68, permutation p 0.65.
- ADAPT6: −0.02pp, t −0.06, p 0.60.
- Fixed cells (hindsight): the 1.0-ADR stop-only cell is best (+3.86%), which is the longer-hold beta effect already
  measured (trail_cost_exposure: the lead was ~3/4 beta). The adaptive picker chooses it most often and still loses to
  HOUSE because it keeps switching.

## Read
- The clustering is real but arrives too late to act on: by the time a bad week's stop-outs have closed and told the
  rule to size down, the bad week is over. Month-scale persistence (+0.05) is what a sizing rule could use, and there
  isn't any. Consistent with WL-2b (ρ −0.01), the trailing-30d rule failures and the self-regime holdout NULL.
- Pressing after winners hurts; the only rules that help anything help drawdown, and they pay for it in growth.

## Consequences
- Trade the rule flat. No feedback sizing, no knob-switching.
- If drawdown matters more than growth, DD_CUT is the honest lever: known cost (~−2 pts CAGR here) for ~16 pts less
  max drawdown. That's a preference choice, not an edge.

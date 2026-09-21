# The pre-earnings volatility ramp (2026-09-20) — the ramp is real; the straddle can't hold it

**VERDICT: NULL · MECHANISM.** The IV run-up into a print is large and reliable — **+40 to +57 vol
points** — and a front-expiry ATM straddle bought to harvest it **loses money even at mid**, before a
single spread is paid. Theta on a short-dated straddle outruns the vega gain.

**Source.** `src/lib/earnings/earnings.py` (2025-10-12), the repo's oldest earnings code: buy the ATM
pair N business days before a print, sell it on the pre-print session, never hold through the event.
It ran on one ticker (AXP) against `options_daily_v2` and flagged its own BMO/AMC gap. This runs the
same trade on 3,163 events / v3, with the report hour known so the exit is the last clean session
*before* the print, ATM chosen at **entry** (call/put mids closest) and the **same contracts** priced
at exit — faithful to the script.

## Result (% of straddle cost)

| entry | n | ATM IV in → out | **ramp** | **MID** | limit fill | crossing | t (day) | win (limit) | rt spread | neg yrs |
|---|---|---|---|---|---|---|---|---|---|---|
| −3 bd | 2,572 | 0.70 → 1.10 | **+40 vp** | **−3.4%** | −10.0% | −15.7% | −22.8 | 21% | 16.1% | 8/8 |
| −5 bd | 2,262 | 0.63 → 1.09 | **+47 vp** | **−6.9%** | −13.3% | −18.8% | −26.1 | 18% | 16.3% | 8/8 |
| −10 bd | 1,762 | 0.53 → 1.10 | **+57 vp** | **−14.3%** | −20.7% | −26.1% | −36.9 | 10% | 16.5% | 8/8 |

**The mechanism is arithmetic, not noise.** The vehicle is the *first expiry after the print* — the
one the old script chose because it carries the most event vol. At −10 bd it has ~12 days to expiry;
by the pre-print session, ~2. A straddle's value scales with σ·√T: σ roughly doubles (+57 vp) while
√T falls to ~0.4, so the position is worth ~0.85× what it cost **before any cost is paid**. Entering
later eats less theta but catches less ramp; the trade-off never crosses zero. The IV ramp is a
textbook fact and this confirms it at scale; harvesting it on the front expiry is a theta bet you lose.

## Liquidity does not rescue it (the review's check)

| −5 bd | n | MID | limit | crossing | t | rt spread | neg yrs |
|---|---|---|---|---|---|---|---|
| all | 2,262 | −6.9% | −13.3% | −18.8% | −26.1 | 16.3% | 8/8 |
| volume top 40% | 905 | −9.0% | −12.9% | −16.4% | −19.2 | 10.0% | 8/8 |
| avg_volume ≥ 5M | 673 | −9.6% | −13.2% | −16.6% | −18.1 | 8.4% | 8/8 |

Liquid names halve the round-trip spread (16% → 8% of cost) and are *still* negative at mid, because
the loss is theta, not friction. Every year negative in every cell; the best year (2024) is −6.9%.

## What this closes

This was the last open earnings idea and the only one that avoided the print's blown-out quote. It
fails for the opposite reason to the others: not the spread, but time decay on the tenor that carries
the ramp. The full earnings ledger for 2026-09-20:

| idea | verdict | why |
|---|---|---|
| PEAD on the real surprise | NULL | market prices the surprise (corr 0.20) |
| tape-reaction signal on the straddle pool | **PARKED** | edge +0.244R, t 1.9, both halves + |
| sell the event — straddle, liquid names | **PARKED** | +0.28% bid / +0.44% limit, 7/8 yrs |
| sell the event — calendar, any back leg | NULL | 3 spread crossings; liquidity can't remove two |
| calculator.py vol gates | NULL | `iv30_rv30` inert & inverted; slope passes 90% |
| **pre-earnings ramp** | **NULL** | **theta > vega on the front expiry** |

**Obvious follow-up, not run:** the same ramp on a **longer tenor** (30–45 DTE) — less theta, and the
ramp in vol points is smaller further out (term structure), so it is a genuine question which side
wins. It is the ramp analogue of the calendar's back-leg test and would need one more pull.

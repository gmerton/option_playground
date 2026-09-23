# Tenor-window long call — buy 90 / exit 60 vs buy 60 / exit 30 vs buy 30 / hold (2026-09-23)

**Verdict: NULL on the primary · INVERTED at the full cross · YIELD: MECHANISM.**
Script `run_tenor_window_calls.py` (pre-registration in its docstring) · log `logs/tenor_window_calls.log` ·
trades `tenor_window_calls_2026-09-23.csv` (59 MB, local only — regenerate from the `data/cache/tenor_window/` pulls) · summary `tenor_window_calls_summary_2026-09-23.csv`.
Source claim: Cashflow Academy 5a ([review](../cashflow_academy/2026-06-03_brutal_options_advice_review.md)).

## Design (recap)

Same Friday entry, same exit day (the 28-DTE leg's expiry), ATM calls (delta ~0.50 on every leg), 330 names from
`straddle_pool_323`, 409 Fridays 2018-01 → 2026-01, **50,564 paired trades**. The arms differ **only in tenor**:

| arm | entry DTE (median) | DTE left at exit | exit | entry premium, % spot | entry spread, % mid |
|---|---|---|---|---|---|
| A (the claim) | 91 | 63 | sold at the bid/ask on exit day | 5.90 | 3.2 |
| B | 49 | **21** | sold | 4.67 | 4.3 |
| C (control, "beginner") | 28 | 0 | settles at intrinsic (chain-implied raw spot) | 3.38 | 6.0 |

⚠ B landed at 49→21, not the claim's 60→30: the target was 30 DTE left, but the available expiries put the median at 21.
Settlement check: C's own expiry-day mid vs our chain intrinsic, corr **0.9986**, median gap 0.06% of spot.
Exit quotes found for 99.5% of A/B legs.

## Result — P&L per share, % of entry spot (all legs ≈ 0.50 delta, so this is P&L per unit of exposure)

| | mid | **house** | full cross |
|---|---|---|---|
| A | +0.758 | +0.577 | +0.423 |
| B | +0.722 | +0.532 | +0.370 |
| C | +0.708 | **+0.626** | +0.558 |
| **A − C (PRIMARY)** | +0.049 (t 1.93; halves +0.12 / +0.01) | **−0.049 (t −1.09; halves +0.02 / −0.09; 3/9 yrs)** | −0.134 (**t −3.75**, 1/9 yrs) |
| B − C | +0.014 (t 1.18) | −0.094 (**t −3.78**, halves −0.03 / −0.14, 1/9 yrs) | −0.187 (t −7.90, 0/9) |
| A − B | +0.036 (t 2.50) | +0.044 (**t 3.74**, halves +0.06 / +0.05, 7/9 yrs) | +0.053 (t 4.90, 8/9) |

NW t on the weekly entry-date series, lag 4. Every arm's positive level is the bull sample (beta, 8/9 years), not
the question. The question is the difference between arms.

**Reading, at the pre-registered house fills:**
1. **The claim's headline, "3-month-then-sell beats 1-month-held", is NULL** (t −1.09, wrong sign, back half
   negative). At mid it points the claimed way (+0.05% of spot, t 1.9), but the back half is ~0. **At the
   full cross it inverts** (t −3.75): the beginner arm wins.
2. **The middle arm is the worst.** B − C is significantly negative (t −3.78, clears Šidák 2.39 and the house
   3.0, both halves negative, 1 of 9 years positive): **INVERTED.** The claim says B should beat C.
3. **A beats B** (t 3.74, both halves, 7/9 years). This is the only link of the claimed ordering that holds. At mid
   it's t 2.5, so roughly half theta and half the wider exit spread B pays at 21 DTE.

Realised ordering: **C ≥ A > B**, not the claimed A > B > C.

## Mechanism — the tenors trade gamma for theta at a fair price

By the underlying's move over the 4-week window (house, % spot):

| move | A | B | C | A − C |
|---|---|---|---|---|
| < −10% | −6.63 | −6.08 | −5.07 | −1.56 |
| −10..−3 | −3.68 | −3.77 | −3.64 | −0.04 |
| flat ±3% | −1.23 | −1.60 | −2.65 | **+1.42** |
| +3..+10 | +2.18 | +1.99 | +2.00 | +0.19 |
| > +10% | +10.69 | +11.03 | +12.44 | −1.75 |

The claim is right that the short tenor bleeds more when nothing happens (flat: C loses 2.65 vs A 1.23). It leaves out
the other side: C wins more on big moves (gamma), and loses less on crashes because it paid less premium. The two
sides roughly cancel at mid. That's what the VRP panel predicts: **no premium at 30d or 90d**, so neither tenor is
mispriced relative to the other. The theta saving isn't an edge, just a different payoff shape. Costs then decide
the result, and holding to expiry skips the exit spread.

**Liquidity terciles (exploratory):** A − C at mid grows with the A leg's spread (tight −0.06, mid +0.06, wide +0.16),
and house fills erase it in every tercile (−0.10 / −0.02 / −0.03). Whatever A gains at mid sits where friction is
largest.

## Caveats

- `straddle_pool_323` is today's liquid list, so it has survivorship/bull tilt. That affects the arms' **levels**
  roughly equally, the **differences** much less. 2022 A − C = +0.01, so the bear year doesn't change the answer.
- One holding window (4 weeks) and one strike (ATM). An OTM version would load more on the gamma side and likely
  favour C further; not run.
- The claim was about theta, not about beating stock. None of the arms is benchmarked against delta-matched stock
  here; for that see `vehicle_benchmark_2026-09-22.csv`.

## What to do with it

Nothing changes in the book. For any long-call use (the always-call benchmark, the uptrend-gated call rule), **tenor
isn't a lever**. If an early exit is planned, exit a longer tenor rather than a mid one (A > B), but holding a 28-DTE
option to expiry is at least as good at house fills and strictly better at the full cross.

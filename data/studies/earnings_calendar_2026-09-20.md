# The earnings calendar — the gate's own vehicle (2026-09-20)

**VERDICT: NULL after costs · MECHANISM. The `ts_slope` null stands, now measured on the right
instrument.** Gabe caught that testing a *term-structure* gate against a front-expiry-only straddle
was a mis-pairing. This prices the actual vehicle. The gate still does not sort — and the calendar
itself loses to the spread in all three variants, in **all eight years**.

**Structure.** Entered the last session before the print, at the same delta-selected, parity-checked
ATM strike **K** as the straddle study: **short the front expiry** (first after the print), **long
the next expiry out** (3–45 days later; median front 2 DTE, median gap 7d). At front expiry the short
settles at intrinsic and the long is **marked from a real quote on that date** — never modelled. An
event whose back leg has no quote is dropped, not assumed. 3,118 events, 284 names.

That discipline is the point: the original calendar path study's erratum found **87% of paths with a
>3% move were truncated** before the loss finished, and an earnings move *is* a >3% move.

**Two modelling choices, both stated:**
- The long back leg is **floored at intrinsic**. 17.4% of call marks and 14.6% of put marks have a
  **bid below intrinsic** (deep-ITM, wide quotes) and nobody sells there — you exercise. Without the
  floor the cost arm charges losses larger than the debit, which a long calendar cannot produce. This
  matches the erratum's own convention: shorts at intrinsic, longs at the mark with an intrinsic floor.
- Costs: buy the back at the **ask**, sell the front at the **bid**, and sell the back at the **bid**
  at exit. The short front settles, so closing it is free.

## Result

| variant | n | median debit | MID | **paying the spread** | win (real) | negative years |
|---|---|---|---|---|---|---|
| call calendar | 3,064 | $0.55 | +0.092% | **−0.777%** | 23.8% | **8/8** |
| put calendar | 3,067 | $0.52 | +0.228% | **−0.767%** | 27.6% | **8/8** |
| **DOUBLE calendar** | 3,082 | $1.07 | +0.326% | **−1.530%** | 25.1% | **8/8** |

At mid the calendar is roughly flat — a small positive mean against a median near zero. Paying the
spread it is clearly negative, every year, every variant.

**The double loses almost exactly twice the single** (−1.530 ≈ −0.777 + −0.767). Friction scales with
legs, which is the same arithmetic the event-spread study measured when a second leg tripled the
friction bill. A four-leg condor would be worse again.

**Win rate collapses from ~50% at mid to ~25% at real prices.** The spread is not shaving the mean;
it is moving the typical outcome.

## Does `ts_slope` sort the calendar? No.

| slope quintile (most backwardated first) | MID | REAL |
|---|---|---|
| (−0.081, −0.023] | +0.397 | **−1.801** |
| (−0.023, −0.014] | +0.309 | −1.512 |
| (−0.014, −0.0098] | +0.363 | −1.321 |
| (−0.0098, −0.0060] | +0.322 | −1.077 |
| (−0.0060, +0.036] | +0.236 | −1.936 |

**Flat at mid** (0.236–0.397, no monotonicity), and at real prices the **most backwardated quintile is
the worst** — steep backwardation means wide spreads, the same inversion that killed the implied-move
sort. The gate itself passes **90%** of prints and moves the needle +0.025pp at mid, +0.113pp real.

**So the earlier null was right, and is now right for the right reason.** It was measured on the wrong
instrument before; on the correct one the conclusion is unchanged.

⚠ The −55% worst case is a low-price artefact: 3.8% of events sit under $10 spot, where a fixed-dollar
debit is a large share of spot. Median spot is $69 and the means/medians are unaffected.

## Where this leaves the oquants question

Selling earnings vol is a real premium at mid and is not harvestable in any expression tested:
**short straddle** −0.428% at the bid, **calendar** −0.78%, **double calendar** −1.53%. Each added leg
costs more than it saves. The condor remains formally untested — it needs wings the 0.25–0.75 delta
pull excluded — but it is four legs, and the ordering here is monotone in leg count.

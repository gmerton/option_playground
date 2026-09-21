# Earnings calendar — the further-out back leg (2026-09-20)

**VERDICT: NULL after costs at every back-leg distance · MECHANISM.** The review flagged that the
calendar had been tested at one geometry (short front / long *next* expiry, ~7-day gap), while
oquants and tastylive use a 30–45 day back leg. This runs +30d and +45d with the same discipline:
same delta-selected ATM strike, real exit marks on the front-expiry date, long leg floored at
intrinsic, events without a quote dropped.

## The mid premium grows with the back leg — and the cost grows faster

Double calendar, % of spot:

| back leg | n | median debit | **MID** | limit fill (mid ± 25%) | bid/ask | neg years (real) |
|---|---|---|---|---|---|---|
| next expiry (~7d) | 3,082 | $1.07 | +0.326 | −0.627 | −1.530 | 8/8 |
| **+30d** | 2,604 | $2.30 | +0.466 | −0.985 | −2.358 | 8/8 |
| **+45d** | 1,786 | $2.95 | +0.558 | −0.952 | −2.415 | 8/8 |

The intuition behind the further-out leg is right: at mid the double calendar's premium rises from
+0.33% to +0.56% as the back leg moves out, and the win rate at mid rises from 50% to 56%. **But the
debit nearly triples** ($1.07 → $2.95), and the spread you pay scales with the debit. Every extra
point of mid premium buys more than a point of extra friction. Single-leg calls and puts show the same
shape (+45d call −1.28%, put −1.19% real, both 8/8 negative).

## The liquidity gate does NOT rescue it (the review's check, applied)

The straddle's parked cell survives on liquid names. The calendar does not — at any distance:

| back | cell | n | MID | **limit fill** | t (day) | neg years |
|---|---|---|---|---|---|---|
| next | volume top 40% | 1,233 | +0.162 | **−0.337** | −5.80 | 8/8 |
| +30d | volume top 40% | 1,042 | +0.356 | **−0.671** | −5.44 | 8/8 |
| +45d | volume top 40% | 714 | +0.472 | **−0.537** | −3.30 | 8/8 |
| +45d | avg_volume ≥ 5M | 607 | +0.477 | **−0.543** | −3.59 | 7/8 |

Even on the most liquid names, at the *generous* limit-fill assumption, every cell is negative with
|t| ≥ 3.3 and 7–8 of 8 years negative. This is a decisive null, not an underpowered one.

**Why the straddle survives liquidity-gating and the calendar does not:** the straddle crosses the
spread **once** (it settles). The calendar crosses it on **two legs at entry and one at exit** — and
the back leg it must sell at front expiry is the leg whose quote the print has just blown out.
Liquidity narrows each crossing; it cannot remove two of them.

## `ts_slope` at the further-out legs

Still does not sort at mid (+30d: 0.28–0.76 non-monotonic; +45d: 0.34–0.83), and at real prices the
most-backwardated quintile remains the worst (−2.83, −3.01). The gate passes 89% of prints at both
distances. Same conclusion as before, now at the geometry the gate was designed for.

## Where the earnings-vol question finally lands

| expression | legs | best after-cost cell |
|---|---|---|
| short ATM straddle, liquid names | 2 | **+0.28% at bid / +0.44% limit — PARKED** |
| short ATM straddle, all | 2 | −0.43% |
| calendar, next expiry | 2 | −0.34% (liquid, limit) |
| double calendar, +45d | 4 | −0.54% (liquid, limit) |

The only earnings-vol cell alive is the **simplest structure on the most liquid names**. Every
refinement — a long leg, a further leg, a second pair — adds a spread crossing that costs more than
the premium it protects. The condor (four legs, wings excluded from the pull) remains untested and
sits at the wrong end of a monotone ordering.

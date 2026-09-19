# The size lever: does scaling risk by grade beat flat size? (2026-09-18)

**Question.** Breitstein varies risk ~10x by setup grade ($10k B → $100k A); Tito's barbell implies the same.
Position size is the only mechanism large enough to explain the returns these traders report — but it only pays
if an **ex-ante** grade predicts R. Tested on our own breakout pool.

**Verdict: the lever is real, but it is "don't trade grade C", not "10x the A's".** Dropping the ungraded
two-thirds of the pool lifts R per unit of risk from −0.002 to **+0.286** out of sample; widening the risk spread
from 3x to 10x adds little on top. One of our own refinements fails as a grade.

## Setup (pre-registered; `run_size_lever_study.py`)

8,244 house breakouts, 2019-10 → 2026-09 (15-day pivot break, RVOL ≥ 1.1, upper-half close, stacked, ADR ≥ 3,
52-week range ≥ 17%). Entry at the breakout-day close, stop = that day's low, exit = first close under the 20 EMA
(the book's grind trail, cap 60 sessions). R = return / (entry − stop), clipped at ±10, 5 bps per side.

Grades fixed in advance from **prior** findings, nothing fitted here:
- **A** = precision tier **and** the entry day closed 1.5–3% above its low (`adhikary_stop_study`'s stop-distance cell)
- **B** = precision tier (ADR 4–7, within 15% of the 52-week high, stack 5–40)
- **C** = the rest of the pool

Schemes are normalised to the same total risk deployed, so this compares **allocation, not leverage**.
Walk-forward: 2019–22 in sample, 2023–26 out of sample.

## 1. Do the grades separate? Only the precision tier does

| grade | 2019–22 mean R | n | 2023–26 mean R | n |
|---|---|---|---|---|
| A | −0.151 | 159 | +0.266 | 220 |
| B | −0.024 | 631 | +0.290 | 1,014 |
| C | −0.343 | 2,321 | −0.093 | 3,899 |

⚠ **The A refinement does not work.** Grading up entries that closed 1.5–3% above their low is no better than B
in either half. The stop-distance result from `adhikary_stop_study.md` improves *sizing arithmetic* (smaller
denominator) but does **not** predict the outcome, so it must not be used as a quality grade.

## 2. Sizing schemes, R per unit of risk deployed

| scheme | 2019–22 | **2023–26 (OOS)** | all | max DD (all) |
|---|---|---|---|---|
| flat | −0.269 | −0.002 | −0.103 | −20.5% |
| graded 3 / 1.5 / 1 | −0.238 | +0.042 | −0.065 | −20.1% |
| graded 10 / 3 / 1 | −0.186 | +0.121 | +0.002 | −21.0% |
| **A+B only (drop C)** | **−0.049** | **+0.286** | **+0.155** | −21.2% |
| A only | −0.151 | +0.266 | +0.091 | −28.5% |

Monotone in both halves — rare in this repo. But the ordering says the gain is **exclusion, not amplification**:
going 10x on A rather than 3x adds ~0.08R OOS, while dropping C adds ~0.29R. A-only is worse than A+B: fewer
trades, a 28% drawdown, and no better mean.

## 3. Reading

1. **The creators' emphasis is misplaced for us.** "Risk 10x on an A" is downstream of the real decision, which is
   refusing the ordinary setup. Our precision tier already encodes that; this quantifies what it is worth.
2. **Concentration costs drawdown.** −20% flat → −28% A-only. A+B keeps almost all the mean at flat-like
   drawdown, which is why it is the sweet spot rather than the purest version.
3. **2019–22 is negative for every scheme.** The pool's edge is a 2023+ phenomenon (same conclusion as
   `adhikary_detector_validation.md`). The honest number is the OOS column.
4. **Most months are negative in every scheme** (monthly t ≤ 0 throughout) — the mean lives in a right tail, the
   same barbell as Tito's duration table. Sizing changes which trades carry the tail; it does not remove the shape.

## What to do with it

- **Keep the precision tier as the grade.** Do not add the stop-distance cell to it.
- **The actionable rule is exclusion:** if a breakout is not in the precision tier, it is not a trade — not a
  smaller trade.
- **A 3x spread within A/B is enough**; 10x buys ~0.08R OOS for real drawdown.

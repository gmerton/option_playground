# SPY 1-day iron condor and put credit spread on positive-gamma days, vs the 2× iron fly (2026-09-21)

## Pre-registration (written BEFORE any code ran; do not edit this section after the results)

**Why.** The 2×-wing iron fly on positive-GEX days passed (+5.8% on max risk, t 3.4; gex_spy_ironfly_2026-09-21.md).
Two alternatives have a mechanism-based reason to do better: a condor wins whenever the move stays inside the short
strikes (positive-gamma days have fewer big moves), and index premium is known to sit in OTM puts (skew). Exactly two
structures, judged against the fly, so the comparison can't turn into a search.

**Structures** (same days, entry at day t−1 close, expiry settling on day t, GEX sign, fills and costs as the fly):
1. **Iron condor:** sell the call with delta nearest +0.16 and the put nearest −0.16; buy the call nearest +0.05 and
   the put nearest −0.05 (each wing strictly beyond its short). Max risk = wider wing − credit.
2. **Put credit spread:** sell the put nearest −0.16, buy the put nearest −0.05 (strictly lower). Max risk = width − credit.
Deltas from day t−1's quotes. Skip a day if any leg lacks a two-sided quote or the net credit ≤ 0.

**Fills.** Shorts at mid − 25% of their bid-ask, longs at mid + 25%, $0.0065/share/leg; settle at expiry, no exit cost.

**Pass bar (each structure, positive-gamma days, return on max risk at the real fill).** Mean > 0 with |t| ≥ 3 (days),
AND higher than the 2× fly in BOTH halves (fly: +7.72% in 2010–2017, +5.39% in 2018–2026-02). If neither passes, the
fly stays the trade. Negative-gamma and all-day results reported alongside.

**Not tested:** other deltas or widths, call-side spreads, broken wings, stops, other tickers.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_gex_spy_condor.py`, log `.log`, table `.csv`)

**Verdict: neither passes. The 2× iron fly stays the trade.** Positive-gamma days, return on max risk at the real fill:

| structure | days | median credit / max risk | return on max risk | t | 2010–17 | 2018–26 | win | $ mean / worst | positive months |
|---|---|---|---|---|---|---|---|---|---|
| **2× iron fly (reference)** | 928 | $2.10 / ~$2.90 | **+5.8%** | 3.4 | **+7.7%** | **+5.4%** | 61% | +$19.8 / −$709 | 67% |
| iron condor 16/5Δ | 928 | $0.32 / $2.74 | +1.8% | 2.4 | +0.8% (t 0.6) | +2.0% (t 2.4) | 82% | +$8.1 / −$545 | 72% |
| put spread 16/5Δ | 928 | $0.17 / $2.86 | +1.9% | 3.5 | +0.7% (t 0.6) | +2.2% (t 3.6) | 94% | +$7.8 / −$564 | 82% |

- Both lose to the fly by 3–4 points of return on risk, and neither is meaningfully positive in 2010–2017.
- Moving the short strikes out to 16Δ raises the win rate (82–94%) but collects a small credit against almost the
  same max risk; the premium the signal identifies is AT the money, where positive-gamma days move less than priced.
- The put spread's steadiness (94% win, 82% positive months, t 3.5) comes from a small return on risk; it doesn't
  support the "premium lives in the put skew" idea on a 1-day horizon.
- Same pattern as the fly: the gamma filter matters (all days: condor −0.3%, put spread +0.7%; negative-gamma
  days: −2.3% / −0.5%).

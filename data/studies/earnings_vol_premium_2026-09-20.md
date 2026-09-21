# Is earnings vol overpriced? (the oquants "sell the event" claim) — 2026-09-20

**VERDICT: NULL after costs · MECHANISM.** The premium is **real at mid** and **does not survive the
bid/ask**. Crossing the spread costs **171% of the gross premium**. And the selectivity lever — sell
the richest implied moves — makes it **worse** after costs, not better.

**Why measured, not simulated.** Our only prior evidence was the tastylive "earnings between the
expiries, +10–15%" cut, **retracted today**: it came from the calendar path study whose steps 4–12
were invalidated, and whose erratum says 87% of paths with a >3% move were truncated before the loss
finished — an earnings move *is* a >3% move. So this measures implied vs realised directly, the move
that made the VRP panel several times more powerful than P&L simulation. Settlement is at intrinsic,
so nothing can truncate.

**Method.** `run_earnings_vol_premium.py`. 4,477 earnings events, 392 names, 2019–2026. ATM straddle
on the last session before the print, first expiry after it (median 3 DTE), from `options_daily_v3`.

## ⚠ A data trap that would have produced a spectacular false positive

The first run returned a short-straddle premium of **+6.37% of spot at a 74% win rate**. It was wrong.
The panel close is **dividend/split adjusted** while v3 strikes and prices are **raw**, so selecting
"ATM" by moneyness off the panel close picked deep-ITM calls — `ABBV 2019-01-24` showed a 65-strike
call at $20.43 against a 62.68 "spot". Fixed by selecting the ATM strike **by delta** and recovering
the raw spot from **put–call parity** (`K + C − P`). Post-fix the strike is properly centred:
median |C−P|/straddle = 0.079, median K/spot = 1.000.

## The premium, and what the spread does to it

Straddle bid/ask: **median 10.5% of mid, mean 23.1%.**

| short ATM straddle, % of spot | mean | median | win | p05 | worst |
|---|---|---|---|---|---|
| sell at **MID** (no costs) | **+0.601%** | +1.315% | 61.0% | −10.53% | −60.05% |
| sell at mid − 25% of spread | +0.087% | +1.019% | 58.3% | −10.98% | −60.17% |
| **sell at the BID** (realistic) | **−0.428%** | +0.597% | 55.1% | −11.93% | −60.29% |

**Crossing the spread costs 1.030pp of a 0.601pp gross premium — 171% of it.** At mid the premium is
positive in all 8 years; at the bid, **7 of 8 years are negative**.

## The selectivity lever inverts after costs

At mid the premium sorts beautifully on implied-move size — exactly oquants' "sell when it's rich":

| implied move quintile | mid | **at the bid** |
|---|---|---|
| q1 (1.3–4.3%) | −0.042 | −0.377 |
| q3 (5.8–7.9%) | +0.370 | −0.359 |
| **q5 (11–83%)** | **+1.700** | **−0.718** ← *worst* |

**The events with the richest premium have the widest spreads**, and the spread takes more than the
extra premium. The monotonic sort at mid becomes a non-sort with the richest bucket worst at the bid.
This is the same shape as the existing 10-DTE single-name finding (costs = 136% of gross); here it is
171%.

## On condors and calendars specifically

Not directly tested — the chain pull kept 0.25–0.75 delta, so there are no wings to build one. But the
inference is strong and points the wrong way: a condor is **four legs against the straddle's two**, and
today's event-spread study measured that a second leg **triples** the friction bill (−37.3pp vs −12.3pp).
A cheaper, capped structure risks less premium but pays more spread per unit of premium sold. Nothing
here suggests the condor rescues a bet the straddle cannot carry; it should be measured before use.

## What this settles

Earnings vol **is** overpriced — the market charges about 0.6% of spot more than the move delivers.
**The market also charges about 1.0% of spot to take the other side.** The edge is real and smaller
than the toll. Combined with the event-spread study (friction, not capping, killed a debit spread) and
the straddle stop (the exit crossing turned a neutral rule negative), this is the **third** time today
that friction, not the idea, decided the outcome.

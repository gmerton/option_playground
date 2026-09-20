# Does capping the tail destroy the event-convexity edge? (2026-09-20)

**Queued from** the Ravish "super bull call spread" review (2026-09-20). **Hypothesis on entry:**
the event-convexity result (+30.7% at the 5-day exit, 0.12Δ) is a *right-tail* result, so replacing
the naked call with a debit spread should destroy it.

**The hypothesis is refuted.** The cap is nearly irrelevant. What kills the spread is the second
leg's transaction cost.

**Method.** `run_event_spread_study.py`, on the cached event-convexity pull. For every
(ticker, entry date, expiry) holding both a ~0.25Δ and a ~0.12Δ call at distinct strikes, build
**long 0.25Δ / short 0.12Δ** and compare against each leg bought naked **on exactly the same
entries** — 3,377 constructible spreads, 755 event / 2,622 control, 53 distinct event dates.
Every arm is priced twice: at the house fill (mid ± 25% of the spread, per leg, both directions)
and at mid, which separates friction from the cap. Median width $5, median debit $0.68 (12% of
width), median 30 DTE.

Sanity check: the parent result replicates on this subset — naked 0.12Δ, 5-day exit, event +25.4%
vs control −6.5% (parent: +30.7% vs −3.6%).

## 1. The event premium survives capping

Event minus control, mean pp, 5-day exit:

| arm | house fill | mid-to-mid |
|---|---|---|
| naked 0.12Δ | +31.9 | +36.1 |
| naked 0.25Δ | +24.5 | +24.2 |
| **spread** | **+20.0** | **+20.5** |

The spread still earns ~20pp more into an event than at random. The *relative* edge is intact.

## 2. But its absolute expectancy is negative, and the cap is not why

Event entries, 5-day exit, mean return: naked 0.12Δ **+25.4%**, naked 0.25Δ **+23.5%**,
spread **−3.6%**.

The cap almost never binds — only **1.7%** of event trades at the 5-day exit (4.2% holding to
expiry) had the long leg exceed the spread's capped max return. Paired per-trade differences on the
same 755 entries, t clustered by entry date (53 clusters, the honest unit):

| paired difference, 5-day exit | house fill | mid-to-mid |
|---|---|---|
| spread − naked 0.25Δ | **−27.1pp, t −5.51** | **−2.0pp, t −0.45** |
| spread − naked 0.12Δ | −29.0pp, t −2.79 | −21.5pp, t −1.90 |

**At mid the spread is indistinguishable from the naked 0.25Δ call (−2pp, t −0.45).** Capping the
upside costs almost nothing, because the tail that the cap would have cut is rare enough not to
matter over 755 trades. At realistic fills the same comparison is −27pp with t −5.5. Friction cost
on event entries: spread **−37.3pp**, naked 0.25Δ **−12.3pp**. The second leg roughly triples the
bill, and the extra ~25pp is larger than the entire event premium.

The mechanism is mundane: a debit spread crosses **four** bid/asks round trip against the naked
call's two, and these are far-OTM contracts where the relative spread is enormous — a 25%-of-spread
penalty on each leg of a $0.68 debit.

## 3. Bonus, and it qualifies the parent study

Naked 0.12Δ − naked 0.25Δ, same entries, 5-day exit: **+19.5pp (t +2.73) at mid, but +1.9pp
(t +0.29) at the house fill.** The far-OTM preference is itself mostly a mid-price artefact. At
realistic fills 0.12Δ and 0.25Δ are indistinguishable, so the parent study's choice of 0.12Δ should
not be treated as established.

## Verdict

**FAIL for the debit spread as the vehicle for the event trade** — but for cost reasons, not tail
reasons, and the distinction matters for where the result generalises.

⚠ **This does not refute Ravish's structure.** The constructible spread here is far cheaper and
wider-ratio than his — median 12% of width (~7:1) against his ~25% (~3:1) — and it is built from
thin far-OTM contracts. His NVDA example measured 3% of the debit per side on 50–60k OI. **The
friction finding is conditional on cheap, far-OTM, thin legs and does not transfer to a 30-delta
spread on an ultra-liquid name.** Testing his geometry needs its own entry signal, which the video
does not supply.

**Carry-forward:** when adding a leg to a convex structure, price the friction before the payoff.
On far-OTM contracts the second leg can cost more than the edge being harvested.

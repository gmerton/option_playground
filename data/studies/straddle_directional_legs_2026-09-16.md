# Should the straddle become a call, a put, or a straddle depending on trend? (2026-09-16)

**Gabe's proposal.** On the gated 7-DTE straddle signals, buy only the call when the name is in a clear uptrend, only
the put in a clear downtrend, and the full straddle when it is flat.

**Method.** Every gated straddle decomposed into its two legs from the study's own path data: entry at mid + 25% of
that leg's bid-ask + $0.0065/sh, settlement at intrinsic against a spot recovered from expiry-day put-call parity
(the basis the strikes are on). Trend label at entry from `liquid_panel_2019.parquet`: extension from the 21 EMA in
ADR units, the house measure, with UP/DOWN bands at 0.3, 0.5 and 1.0 ADR. 4,795 of the 5,886 gated trades (81%) have
panel coverage, 2019-02 → 2026-02, 229 tickers. Data: `data/cache/straddle_recenter/leg_decomp.parquet`.

## The proposal does beat the straddle — but it loses to simply always buying the call

Band 0.3 ADR (UP 2,869 / DOWN 1,255 / FLAT 671):

| rule | mean | median | win | weekly t | monthly t | mean ex-top-1% |
|---|---|---|---|---|---|---|
| always straddle (baseline) | +4.34% | −15.9% | 43% | 0.75 | 1.94 | +0.72% |
| **proposal** (up→call, down→put, flat→straddle) | **+7.91%** | −59.9% | 37% | 1.76 | 2.76 | +0.65% |
| inverted control | +0.95% | −77.0% | 35% | −1.03 | −0.04 | −5.96% |
| **always call** | **+9.47%** | −90.8% | 36% | 1.43 | 2.03 | +2.12% |
| always put | −0.58% | −100% | 33% | −0.65 | −0.19 | −7.68% |

Wider bands are worse for the proposal (0.5 ADR +6.58%, 1.0 ADR +6.09%), so the tighter the band — i.e. the more
trades routed to the call — the better it looks. That is the first clue.

## Why: the call is the best leg in *every* bucket, not just uptrends

| trend label | n | call-only | put-only | straddle | best leg |
|---|---|---|---|---|---|
| UP | 2,869 | **+12.17%** | −1.40% | +5.02% | call ✓ (rule agrees) |
| DOWN | 1,255 | **+5.57%** | +1.14% | +3.86% | call ✗ (rule buys the put) |
| FLAT | 671 | **+5.27%** | −0.26% | +2.37% | call ✗ (rule buys the straddle) |

The rule is right in one of three buckets. On down-trending and flat names the call still beats both the put and the
straddle, so the proposal gives back value in two thirds of its cases. Its entire advantage over the baseline comes
from routing uptrend names to the call, which is also what "always call" does — only more often.

**The trend label barely predicts direction.** Over the 7-day hold, UP names rose 52.3% of the time against 49.8%
for DOWN and 48.9% for FLAT. A 2.5pp spread is real but far too small to pay for giving up a leg. The call's
advantage on UP names (+12.17% vs +9.47% for calls overall) is the honest measure of the signal's content: ~2.7pp.

## The two reasons not to adopt it

**1. It is a bull-sample bet, and 2022 shows the bill.**

| year | straddle | proposal | always call |
|---|---|---|---|
| 2019 | −8.4 | +1.3 | +0.5 |
| 2020 | +16.6 | +25.3 | +18.5 |
| 2021 | +4.9 | +7.7 | +5.5 |
| **2022** | **+7.1** | **−0.9** | **−24.6** |
| 2023 | +6.5 | +4.8 | +10.6 |
| 2024 | +4.8 | +11.0 | +14.9 |
| 2025 | +5.1 | +13.9 | +18.9 |
| 2026 | +20.2 | +23.1 | +63.0 |

The proposal beats the straddle in 6 of 8 years and loses 8 points in the one bear year. Always-call loses 32 points
there. 2022 is precisely when the straddle earns its place as the convex half of the two-sleeve book
(`audit_review_2026-09-16.md` §4) — converting it to a directional bet removes the reason to hold it.

**2. It concentrates an already-concentrated edge and wrecks the median.** Excluding the top 1% of trades the
proposal earns +0.65% against the straddle's +0.72%, so its whole advantage is in the extreme tail. Meanwhile the
median trade falls from −15.9% to −59.9%: a straddle usually retains value in one leg, a single option usually
expires near zero. Same mean story, far worse trade-by-trade experience, and it needs every signal taken to work.

## Verdict

**Not adopted.** The observation underneath it is sound — in uptrends the call leg is what carries the straddle — but
the rule as specified is wrong in two of three buckets, its apparent gain is bull-market beta that "always call"
captures better, the directional signal it rests on is worth about 2.5pp of hit rate, and it destroys the one
property that makes the straddle worth owning alongside a short-vol sleeve.

**If revisited,** the benchmark is *always call*, not the straddle, and the question is whether some signal predicts
direction well enough to beat it while keeping 2022 survivable. Extension from the 21 EMA does not.

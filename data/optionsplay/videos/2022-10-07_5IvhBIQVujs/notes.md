# OptionsPlay: "Generating Income with Index Options using Iron Condors" (2022-10-07, 8 min)

_Reviewed 2026-09-24. Scripted explainer: two hand-picked NDX dates and three rules._

## Verdict: 2 / 5

The volatility risk premium is stated correctly, and "higher IV = wider break-evens" is true arithmetic. The timing
rule ("initiate after a large outsized move, markets consolidate") is **contradicted at the same VIX level** on SPY.
The adjustment rule is untested and sold as free. Two dates (VolQ <15 vs >38) are an illustration, not a sample.
Everything is at the mid, with no costs.

**Selection rule:** index (NDX), 30 DTE, **25Δ short call and put with fixed $100 wings**, timed by the level of the
volatility index (VolQ) and entered after a big move.

| @ | Claim | Tag | Our evidence |
|---|---|---|---|
| 00:21–01:16 | Premiums consistently overstate realised vol, across decades and asset classes | AGREES | VRP panel 10d **+1.75vp, t 8.93, 17/17 years**. The confirmed index-options positives in the multiple-testing pass are all of this family |
| 02:31–05:13 | High IV (VolQ 38 vs 15) pays more credit and **doubles the break-even cushion** (7.3/8.2% vs 3.7/2.7%) | AGREES (arithmetic) · PARTIAL (edge) | The only certified condor is **SPX bearish-high-IV 0.20c/0.30p, 71 trades, t 5.21**, halves +11.6/+7.3 (`tierab_significance_2026-09-22.csv`). But **bullish-high-IV + 200MA is t 2.26, with 51% of trades in one year**, so high IV alone is not the gate. It is also the same stress episodes as the SPY bull put: one bet |
| 05:37–06:03 | Condors are "best initiated after a large outsized move": "our statistics show" markets consolidate after a large move | **CONTRADICTED (weak)** | `post_shock_vol_premium_2026-09-21.md`: 156 SPY shock episodes, VIX-decile matched. The 10-day short straddle after a shock is **−10.8pp vs a normal day at the same VIX (t −1.8)**, and **−20.7pp after UP shocks (t −2.1)**, because realised vol clusters. At 1 day it is +4.0pp, t 1.0, gone in 2018–26. The IV *level* is what pays, not the move. His "statistics" are never shown |
| 01:18–01:33 | Short premium needs many small, spread-out trades (insurance analogy) | AGREES | Sizing to max loss / size as exclusion |
| 06:03–06:55 | **Roll the untested side toward the market for more credit "without adding any additional risk"** (new width ≤ old) | UNTESTED · the "no added risk" half is false | Max loss per side is unchanged, and even falls by the extra credit. But the probability of loss on the rolled side rises, the trade becomes more directional, and it costs four extra legs of bid/ask. Rolling the put side up in a rally adds long beta, and our put-side edge is mostly beta (`etf_condor_call_side_2026-09-16.md` §2) |
| 01:42 | Condors are "directionally neutral" | PARTIAL | The ETF condor that nets the direction out has **no edge: +0.36%/trade, monthly t 0.60** (`etf_condor_call_side_2026-09-16.md`). Only the SPX stress cell survives |

**What's new / test candidates.** The one untouched axis is the **untested-side roll**: grep TEST_INDEX for
"untested" / "adjust" and nothing comes back. If it is ever tested, run it only inside the certified SPX
bearish-high-IV cell (the ETF condor has nothing to improve). Pre-register roll-vs-hold paired at real fills. The
prior is negative (four legs of friction plus added beta), so it is **low priority, not queued**. Everything else is
answered (§32 condor, §53 post-shock, Tier A/B certification).

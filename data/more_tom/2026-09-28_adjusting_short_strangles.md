# More Tom: "Everyone Is Wrong About Adjusting Short Strangles" (sRBMNxrVIws, 2026-09-28, 6:21)
Reviewed 2026-09-28. Transcript: `2026-09-28_adjusting_short_strangles_transcript.txt`. This is a clip of Sosnoff and Tony Battista chatting live at the desk.

**Score 1.5/5.** The title promises a verdict but the clip gives none. Tony rolls the untested side; Tom used to do that and now mostly re-centers. The stated "new rule" is "whenever you're uncomfortable, just adjust", which can't be coded. No numbers, no sample.

| claim | ledger | verdict |
|---|---|---|
| On a strangle under pressure, roll the untested side toward the stock (Tony) vs re-center both sides (Tom) | **Untested on SHORT strangles.** The nearest rows are long-straddle re-centering (FAIL, −3 to −7pp) and 21-DTE management (FIX-1: close at 21 costs −$0.52/sh, t −2.42) | New axis, low prior. Each adjustment adds up to 4 legs at real fills, and the old and new positions carry the same expected edge per unit of premium. Rolling the untested side also narrows the strangle *into* the trend |
| When re-centering, sell more delta on the richer (skewed) side: puts for an index, calls for crude oil or equities with call skew | Skew exists by name in `silver.options_iv_daily`; untested as a strike-selection rule | Minor. Our VRP work says the premium is in the level, not the side |
| Stay in the same expiry until ~21–28 DTE, then roll out at 25–30% smaller size | FIX-1: managing at 21 DTE earns LESS than holding (t −2.42); it only reduces risk | Contradicted as a return claim, agrees as risk reduction |
| "VIX up only 1% on a −47 S&P day": vol is cheap versus the move | Descriptive. Post-shock premium FAILS vs VIX-matched days; GEX regime (certified mechanism) is the better lens | No test |

**Possible test (not queued):** the untested-side roll vs re-center vs hold, on the FIX-1 engine (45 DTE 20Δ, 44 names, real fills). Trigger: tested-side |Δ| ≥ 0.35. Arms: hold / roll the untested side to 20Δ / re-center both sides to 20Δ. Primary = paired P&L per unit of initial risk vs hold, month-clustered. It runs locally on the FIX-1 caches, ~1 h.

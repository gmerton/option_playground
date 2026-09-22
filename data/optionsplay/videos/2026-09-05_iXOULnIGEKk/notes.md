# OptionsPlay — "Why You're Selling Winning Stocks Too Early (Fix This)" (Tony Zhang, 2026-09-05, 47 min)

_Reviewed 2026-09-22, the same day we tested O'Neil-style pyramiding on our own book._

## Verdict: 2.5 / 5 — right about the disease, and the cure is the one we tested this morning and could not confirm

No new mechanism, no data, and the "process" resolves to his daily-play signals telling you when they add. But the
diagnosis matches our own journal findings almost line for line, so it is useful as independent agreement — with one
central claim that our data does not support and one number that is materially wrong.

## Claims

| @ | Claim | Our evidence |
|---|---|---|
| 34:05 | **"We take profits at the first push"** and severely underperform; "you can't go broke taking profits — but you can severely underperform" | ✅ **Confirmed and quantified.** Our profit-lock study: trims cost −0.25…−0.33R, "extended → tighten" INVERTS (−0.19R, t −2.8; 10-EMA trail −0.47R, t −4.8); only breakeven-after-+2R is harmless. Same-day exits are the negative bucket in both books (scalp −0.13R vs trail +0.89R; your own 278 same-day cycles, −$8.3k) |
| 16:13 | **The fix: when a winner keeps outperforming, ADD exposure** — buy more at 105 after buying at 100 | ⚠ **Tested 2026-09-22 (`run_oneil_pyramid_8wk.py`) — NULL.** Adds at session 3/5/10 earn +0.30…+0.66R on their own risk, but **no condition beats adding to any still-open trade** (best +0.15R, t 1.25). Adding scales the same edge; it does not improve it. His "the market has proven your thesis" framing is exactly the endogeneity trap: trades that are up at day 3 finish at +3.4R vs +0.35R, but that gap is the gain already made, not the gain to come |
| 21:17 | The add should come **on a retest of prior support**, not at the highs | ⚠ Closest thing we have is the retrace entry: better than the breakout in all 6 cells, but **t 0.48 → PARKED**. His version is untested as an ADD (our test added at fixed session counts, not at a retest) — the one genuinely open variant in this video |
| 17:53 | **"30 to 40% of breakouts go nowhere"** | ❌ **Wrong by about 2× on our pool.** 76.4% of breakouts return to the level (and average −0.37R); only 23.6% never return, and those carry everything (+1.27R). His number would make the strategy far easier than it is |
| 18:22 | **A stop on every trade, accept the fixed loss, never average down** — a defined-risk option counts as the stop | ✅ Agrees with our vetoes (never widen; stops ≤2% or size down) and with the defined-risk finding from the vehicle benchmark (the call spread's whole advantage over delta-matched stock is its capped downside, +$204/contract in down months) |
| 14:32 | Traders "take profits and run" because a winner turning into a loss hurts more | Behavioural, untestable, and matches the journal: your too-soon exits are the recurring grade deduction |

## What I would take

1. **Nothing new to adopt.** The agreement on exits is real but it is agreement with what we already run (20-EMA
   trail, no trims, no tightening).
2. **One open test worth queuing:** add on a RETEST (first close back above the breakout level after a pullback to
   it), rather than at a fixed session count. That is the intersection of his rule and our PARKED retrace entry, and
   the harness already supports it.
3. **Treat his 30–40% failure rate as marketing.** On our data it is 76%. Any process built on his number will
   under-reserve for stop-outs.

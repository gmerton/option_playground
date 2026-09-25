# tastylive / Market Measures: "Why I Just Changed My Scalping Strategy After 20 Years" (2025-08-01, 17:05)

_Reviewed 2026-09-24. Tom Sosnoff with a researcher (Thomas) presenting slides on intraday ranges in futures. It
was recorded on a big down day ("today we'd be way outside of this"). Transcript (`en-orig` auto) is in this
folder. Slides aren't in the transcript, so every number below was spoken._

## Verdict: 2.5 / 5

The study is **descriptive and honest about it**: 12 months of 1-minute bars on ES, NQ, RTY, CL, GC, SI, BTC and ETH,
with the 50th / 75th / 95th percentile of the 08:30–15:00 CT range per product. Nothing in it is an edge claim. The
interesting part is Sosnoff's reaction, which is the actual "change" in the title. It is a **regime rule for intraday
index scalping:**

> Inside the normal range (≲ 0.5–1 SD of the expected move, "the IQR") **fade** the move. Beyond about 1 SD, the
> 95th-percentile day, **stop fading and go with it** ("down 30 or 50 handles I'd get long… down 100 handles I'd get
> short", 09:14–09:40).

That rule has an academic twin that we have already partly tested: **index intraday momentum outside a noise band,
driven by dealer gamma**. Our evidence agrees with the "go with it on big days" half in sign, but it isn't certified.
The fade half, done directionally, is untested. Its options form, selling the 1-day SPY straddle or fly on
positive-gamma days, is certified. It gets 2.5 rather than 2 because the rule is specific and lines up with a real
mechanism. It isn't higher because the video gives no test of it: the range study says how far prices move, not
whether fading or following pays.

## Claims

| @ | claim | verdict | evidence |
|---|---|---|---|
| 02:10–04:50 | each product has its own range "personality"; the index IQR is tight, crypto's median day exceeds ES's 95th percentile; ES ≈ 70 handles/day over 12 months (≈ 60 lately) | **descriptive, plausible** | We hold no futures data. Index ranges are consistent with our SPY/QQQ 1-min cache (`data/cache/intraday_hist/`) |
| 05:40–06:40 | ranges spiked in April (tariffs) and compressed after; ranges track implied vol | **AGREES** | Vol clusters and mean-reverts: VRP panel; **GEX regime PASS**, where negative dealer gamma adds +8.1% realised vol beyond VIX (SPY t 7.7). ⚠ "Peaks in April" is one year, not a seasonal. The hosts say so themselves |
| 07:10–08:00 | base-case day: **fade extremes, scalp reversals, tight targets** | **UNTESTED directionally · AGREES in options form** | No directional intraday index fade in the ledger. The options expression of "the day stays in its range" is **certified**: SPY 1-day short straddle on **positive-gamma** days +13.7% (t 5.6), 2×-wing fly +5.8% (t 3.4). On negative-gamma days the fly loses −5.4% (t −3.1). Single-name fades are 0 for 5 (exhaustion fade FAIL + retraction, bouncy ball, capitulation, counter-trend) |
| 08:00–09:50 | trending day (75th pct): lean into the trend (Thomas) vs **keep fading** (Sosnoff). 95th pct: **stop fading, go with the move** | **PARTIAL, right sign, UNDERPOWERED** | Noise-band momentum (Zarattini–Aziz–Barbon): engine replicates on SPY (17.5%/yr, Sharpe 1.18 gross); QQQ in the $10k game 2.5%/yr net, Sharpe 0.28, dead 2009–17. **Negative-gamma days only: +4.16 bp/session, t 2.92** (bar 3), both halves positive, but 2018 + 2022 ≈ two-thirds of it (`gex_noise_band_2026-09-21.md`). The late-day leveraged-ETF flow version FAILED (`run_letf_rebalance_study.py`) |
| 13:50 | "when price is already at the 95th percentile, the odds of further extension are low" (Thomas; Sosnoff agrees) | **CONTRADICTS his own rule** | If extension odds are low at the extreme, fading is right there, and that's the opposite of "go with it". The data leans toward Sosnoff's version (momentum is stronger on the high-realised-vol, negative-gamma days) but uncertified. Nobody on set notices the conflict |
| 09:00 | trailing stops are **mental, not resting** | **PARTIAL** | For entries, resting a tight stop intraday is the rejected variant (entry study; DINO case). Our resting stop is the 1-ADR disaster stop. Intraday scalp stops are untested |
| 11:00–12:40 | size by volatility and buying power; don't treat ES and BTC the same | **AGREES (qualitative)** | Size is the only non-inverted tail lever (size-lever study: works as exclusion). BTC futures are ~10× ES margin, which the hosts point out themselves |
| 11:10 | **don't chase**; "if you miss it, you miss it" | **AGREES** | Panel: the breakout entry pays ~2.6 ADR more than a random later entry in the same name, a ~0.4R swing (`entry_vs_stop_2026-09-20.md`) |
| 12:50 | be product-indifferent; take a day off when nothing works | not testable | — |

**Data audit:** 12 months, 1-min OHLC, 8 futures, RTH only. Percentiles of the daily range as a % of the open. No
trade is simulated, so there are no fills, no costs, no n of trades and no statistic. This is a description of
ranges. The fade/follow rule is Sosnoff's 20-year pit experience, offered as opinion.

## What's new / test candidate (not queued; Gabe's call)

**A gamma-switched intraday index rule, the directional form of his switch.** On SPY 1-min bars from 2010 on, with
daily GEX from the existing build:
- on **positive-GEX** days, fade a move that reaches 0.5–1.0 × the day's expected move (VIX-implied) back toward VWAP;
- on **negative-GEX** days, follow a move beyond 1.0 × with the existing noise-band engine.

What makes it new:
- The fade half has never been tested directionally on an index.
- The switch variable is gamma, not a range percentile. That makes it knowable at the open, whereas "is today a
  95th-percentile day" is only known in hindsight, as Sosnoff admits (11:30).

The prior is modest:
- the options form already captures the positive-gamma half more efficiently (the certified 1-day fly);
- the momentum half is a near-miss that depends on 2018 and 2022;
- at $10k, costs ate the noise-band engine (4.5%/yr).

Data is local (1-min cache plus GEX), so it would run locally.

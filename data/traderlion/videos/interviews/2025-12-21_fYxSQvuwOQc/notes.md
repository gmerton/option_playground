# TraderLion -- "The Wedge Pop Swing Trading Setup - How a Trading Champion Enters a Position" (Oliver Kell, uploaded 2025-12-21, 66 min)

_Reviewed 2026-09-23. A TraderLion conference presentation (host Richard) of Kell's "cycle of price action" and
its entries: wedge pop, EMA crossback, base-and-break. Case studies HOOD, COIN, SMR/OKLO, NVDA, CRWD ("Crowd").
The talk dates from mid-2025 (HOOD's S&P non-inclusion, an SMR/OKLO run, a "trend since late April"); the upload
is December. Auto-captions; a gap at 04:00-05:27 was lost in captioning, and the teaser [00:00-02:00] repeats the
talk. Setup write-up and codable spec: [setups/kell_wedge_pop.md](../../../setups/kell_wedge_pop.md)._

## Verdict: 2.5 / 5

- **The most objective framework in this batch, and he says what the entry is not.** 10/20 EMA state (green
  above, red below) [03:00]; a weekly filter (don't trade below the 20-week EMA) [12:00]; and a precise trigger
  definition: the buy is the **break of the mini-base swing high, not the moving-average cross** [01:01, 05:27].
  That makes it codable with few free parameters.
- **Honest about the distribution.** "Most of your trades are going to be losers, probably 60 to 70%" [48:59];
  scratches and stop-outs shown on NVDA before the winner [47:01]; one trade can "pay for all the scratches"
  [49:30]. That matches our house breakout (30% win, median -1.08R) and our right-tail book.
- **The evidence is zero.** No count, no return, no base rate for the wedge pop. Every chart is his own open or
  past winner (HOOD, COIN, SMR, NVDA). "Go back through hundreds of charts and see if you can see it" [08:02] is
  the only validation offered.
- **The parts that adjoin tested claims mostly fail here:** the EMA crossback is our pullback-entry FAIL, "RS while
  the index capitulates" is our down-day RS INVERTED, "sell the exhaustion extension" is our tightening INVERTED.
- Sizing to 30-35% of the account in a top name [51:00] is a risk flag for anyone copying it.

## Provenance

- The host introduces him as **"US Investing Champion of 2020 and record holder"** [02:00]. The figure isn't given
  on camera. It's widely reported as ~+941% in the 2020 stock division; I haven't verified that here. USIC checks
  broker statements for one calendar year; the entrant pool is opt-in; account size isn't disclosed. 2020 was a
  one-sided post-crash momentum year, the best possible year for a 10/20 EMA trend follower.
- Commercial: kelltrading.com (a book that "basically outlines what I went over"), The Swing Report newsletter, a
  Swing Trading Masterclass sold through TraderLion University [01:04:50]; a "Free Price Cycle Course" link in the
  description.
- Soreide's clip cites him as the benchmark ("try to be like Oliver and get the thousand %") [mpe2 06:14]. Two
  USIC winners citing each other is marketing, not replication.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 03:00-04:00 | Green light = above the 10 and 20 EMA, red = below; adjust exposure by position in the cycle | **Framework, and it is roughly our trail.** The house exit is a close under the 20 EMA; nothing tested beats it (tightening INVERTED -0.19R t -2.8; switching to a 10-EMA trail once >= 2 ADR extended **-0.47R, t -4.8**, the worst exit in `profit_lock_2026-09-20.md`; 8-week hold NULL). ⚠ His switch to the 10-day "after 3-4 holds" [36:01] is triggered differently (by holds, not by extension) but tightens the same way. Untested in his form, and the prior is negative |
| 00:00, 04:00-05:27 | The cycle: reversal extension (capitulation below the MAs) -> snap back -> high-volatility retest -> tightening -> higher low -> **wedge pop** through the swing high | **Untested as a pattern.** Pieces tested: counter-trend long off >= 3 ADR below the 20 EMA **FAIL** (-0.15 to -0.33R), so the reversal extension is not itself an entry, which is also his view. The wedge pop is a **reclaim**: nearest test is reclaim vs pullback-low, reclaim arm **+0.048 to +0.178R, t 1.84-2.69, edge vs `post` -0.004 to +0.108R** (`reclaim_vs_pullback_2026-09-23.csv`). That reclaim is of a 10-session high, not of a tight mini-base after a correction, and his definition adds the structure (higher low + contraction) |
| 01:01, 05:27, 26:01 | ⭐ **"Typically you are moving through the moving averages, but that's not the buy area, which I think a lot of people misinterpret. It's breaking through the price structure, the swing high."** "You want a tight area ... a mini base, and that's really the key" | ⭐ **This is the testable claim, and it comes with its own control.** Same date, same state (correction then close back above the 10/20 EMA), with vs without the tight mini-base + higher low. That holds the name-state fixed and varies only the structure he says matters. Our VCP NULL is a warning: tightening added **-0.37pp** vs same-date breakouts |
| 06:04, 15:01, 21:02 | **EMA crossback**: the first pullback into the 10/20 EMA after the pop is "another low-risk area"; "if you miss the wedge pop, wait for the cross back ... no excuse to ever chase" | ❌ **The daily version is our pullback-entry FAIL.** Luk/Ariel EMA pullbacks on leaders: **+1.2-2.4%/trade (t <= 1.4), below the breakout entry**; the tight version negative. ✅ "Never chase" agrees with the entry-extension finding (+2.6 ADR paid by the breakout vs a later entry). He buys the crossback on 65-min strength, which is intraday and untested (§10 parked row "intraday versions of the daily nulls") |
| 06:30-07:02 | Base-and-break: 1-3 week consolidations into the MAs; 1 in a weak market, 3 in a strong one | Untested. It's the house breakout from a short base; the house breakout loses to its own `post` control (-0.21 to -0.33R vs +0.13 to +0.21R) |
| 07:02-08:02 | **Exhaustion extension** (greed) -> flush -> lower high -> **wedge drop** = the end of the cycle; sell into extensions | **Tested adjacent and not supported as a return lever.** Profit-lock: "extended -> tighten" **INVERTED** (-0.19R, t -2.8). Spike exit on calls: **NULL** (t 0.18); cumulative-extension variant **PARKED** (t 2.12-2.51, fails Sidak). It's a risk lever at best |
| 08:02-10:01, 12:00 | Pair the weekly with the daily; best when a weekly wedge pop contains daily up-cycles; don't trade below the 20-week EMA | **Untested as a gate.** Trend Template ablation: the MA criteria are **redundant or UNDERPOWERED** (full TT buys +0.575pp). A 20-week (~100-day) EMA floor is looser than the TT's 150/200 SMA. Default ON in the spec, not tested separately |
| 11:01 | Buy as close as possible to the 5-week (= ~20-day EMA); prefer 5-8 week pullbacks into the 10/20-week | Entry-location claim, consistent with entry-extension. Codable as a covariate: extension above the 20 EMA in ADR at entry. ⚠ **Extension is a TIMING variable, not a SELECTION one**: within a date the less-extended candidate was weaker (t -2.06 to -0.95), so don't use it to pick names |
| 13:01-16:02 | Manage on the daily + 65-min; enter on 10-30-min charts using the *daily* EMAs; "don't create trades on the lower time frame" | ✅ **Agrees.** Stage A: intraday triggers ≈ a random later minute; alert funnel: intraday alerts add nothing beyond the daily state; entry study: **the close beats every intraday entry** (-0.9 to -2.3pp, t to -3.4). His "5-min stops get you stopped five times" is our stop-execution finding |
| 15:01 | "Break and recapture" of the prior day/week high or low lining up with the 10/20 EMA | **NULL where tested.** Level triggers (PDH/PDL/21 EMA/50 SMA/AVWAP/ORH): **0/12**, every arm -0.06 to -0.10R; break = hold |
| 20:02-21:02 | Buy stocks already set up while the index is still between reversal extension and wedge pop (relative strength during the correction) | ❌ **INVERTED here.** Down-day RS as a selection filter: dose >= 2 **-3.51pp at 63d, t -3.33, both halves negative**, monotone dose-response |
| 29:01-30:00, 58:01-63:00 | Trade the strongest liquid stocks in the in-play themes (crypto, AI layers, SMR) | Contradicted where tested: rotation can't be front-run; the leading-group filter INVERTED (t 2.6). His theme calls are narrative (Hood via a friend-of-a-friend options trader [57:00]) |
| 32:02-36:01 | HOOD: sold on earnings day (a mistake), rebought 4 days running, held on the 20-day then switched to the 10-day | One open winner. The re-entry is the pyramid pattern: **NULL** (adds earn the base edge; no add condition beats the unconditional add, best +0.15R t 1.25) |
| 36:01-38:01 | Buy 3-4 times inside the base and ratchet the stop to build size; prefers stocks that take 2-3 days to go | Same pyramid NULL. The ratchet shrinks the stop, which inflates R (house rule: judge in percent) |
| 38:01-41:00 | COIN: "committed to holding it back to the moving averages" through an extension; "I almost feel like I got lucky" | One winner, his own word "lucky". Consistent with our finding that overriding the trail costs |
| 48:59-49:30 | **60-70% of trades are losers**; one trade pays for the scratches | ✅ **Agrees.** House breakout 30% win, median -1.08R; the book's edge is in the right tail (month-weighted -0.007R vs +0.448R trade-weighted) |
| 51:00-52:00 | Size: 30-35% of the account in a top liquid name; 15-20% liquid core; 7-12% in volatile names | ⚠ **Size lever: exclusion helps (+0.29R OOS), amplification doesn't** (10x spread +0.08R, costs drawdown). Concentration is where the USIC return comes from, and where a copier's drawdown will too |

## Codable spec (summary; full version in the setup file)

Daily bars, liquid panel, entry at the close. Discretionary parameters: **default [range]**.

1. **Context:** close >= 20-week EMA (~100-day EMA) [12:00]; ADR >= 3; eligible.
2. **Correction ("red light"):** in the last 40 sessions, >= **5** [3-10] closes below the 20 EMA [03:00], and
   a low >= **1.5 ADR** [1-3] below the 20 EMA (reversal extension) [04:00].
3. **Higher low:** the mini-base low is above the correction low [05:27, 25:01].
4. **Mini base (tight area):** the last **5** [3-10] sessions before the trigger span <= **2.0 ADR** [1.5-3]
   high-to-low, with mean daily range <= **0.8x** [0.6-1.0] the 20d ADR [00:00, 29:00]. The base low is within
   **1 ADR** [0.5-1.5] of the 20 EMA ("consolidates down into the 20 day") [01:01].
5. **Trigger (wedge pop):** close > the base's highest high **and** close > 10 EMA and 20 EMA; the first such
   close since the correction [01:01, 05:27].
6. **Stop:** the base low, judged on the close; report stop/ADR, floor 0.5 ADR.
7. **Exit:** first close < 20 EMA [36:01] (arm: 10 EMA), cap 120 sessions; 0.10% slippage a side.

## What I would take

1. **The "structure, not the MA cross" claim** as the one test worth running from this video. It has a built-in
   same-date, same-state control, so it can separate "tight base + higher low" from "back above the EMAs".
2. **"Don't create trades on the lower time frame"** [16:02]: our intraday results in his words.
3. **"60-70% losers"**: a creator stating the real distribution. Useful to quote against the "90%+ winners"
   thumbnail above.

## Not tested, could be

- **Wedge pop vs (a) same-date house breakouts in other names and (b) same-date "EMA reclaim without a mini-base"
  names.** Primary arm, controls and the pre-registered bar in
  [setups/kell_wedge_pop.md](../../../setups/kell_wedge_pop.md). ~1 day, reusing `run_reclaim_vs_pullback.py`
  scaffolding. Events should be plentiful (a correction-and-reclaim happens several times a year per name), so
  unlike the HTF this one can reach power.

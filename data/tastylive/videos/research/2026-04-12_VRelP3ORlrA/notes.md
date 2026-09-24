# tastylive / Market Measures: "Most Traders Stop Selling Strangles When the Market Drops 3%. The Data Says That's the Wrong Move." (2026-04-12, 9:59)

_Reviewed 2026-09-23 for the Sosnoff-doctrine batch (Tier 1). This is the closest tastylive claim to our one
certified short-premium cell. Transcript (`en-orig` auto-captions) in this folder. Slide values are only known where
the host read them out._

## Verdict: 2.5 / 5 (the best-designed of the five, and the claim points the same way as our certified cell)

**What it does right:** there's a **control**. The same structure entered on "any day" is compared with entries after
down days of increasing size. That's the right shape of test (condition on the trigger, hold the structure fixed).
The conclusion ("sell premium into a sell-off, keep size small") lines up with the only short-premium bucket that
certifies in our ledger.

**Why it isn't higher:**

1. **The sample starts "after the big part of the COVID move" (01:14).** That removes the one episode where the
   hypothesis's failure mode ("down days can be the beginning of larger moves", 09:43) ran hardest. SPY closed
   down ≥ 3% on **12 days in Feb–Apr 2020**, almost as many as the **14 in the entire window they kept**
   (2020-05 → 2026-09; `data/cache/SPY_stock.parquet`, quick lookup). A 16Δ strangle sold on 2020-02-27 (SPY
   −4.5%, VIX 39) and closed at 21 DTE (~2020-03-20) would have met SPY 23% lower (297.51 → 228.80). That's the trade the study doesn't contain.
2. **The "down 3%" bucket is ~14 entry days in ~4 episodes:** Jun/Sep/Oct 2020, Apr–Sep 2022 (9 days) and Apr 2025
   (3 days). Daily overlapping entries ("about 100 and something" a year, 02:09) inflate the apparent n of the "any
   day" bucket, but they can't inflate a 14-day trigger. The host guesses "five of these or 10 of these" (06:22). No
   n, no t, no per-episode breakdown.
3. **Fills:** unstated; the channel disclaimer says "not presented net of all commissions". Treat as mid. On a
   16Δ SPY strangle, mid vs bid/ask is roughly the size of the "any day" mean (see below).
4. **Win rate is traded for size and not bounded.** They say win rate "goes down" in the 3% bucket but never show
   the worst trade, or how many 3% entries lost and by how much. "Largest loss as a % of buying power also
   decreases" (06:11) is stated with no number.

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY only |
| period | "from 2020… after the big part of the COVID move" → **~mid-2020 to early 2026** ("six-year", description) |
| n | **not stated.** Entries are made "essentially every day… about 100 and something" per year (01:43–02:12) |
| entry rule | four buckets by the entry day's SPY return: **any day**; down **up to 1%**; down **2%**; down **3%+** |
| strikes / DTE | **16Δ strangle, 45 DTE** |
| management | **closed at 21 DTE** ("that management is going to just depend on each single trade", 02:25; no 50% take stated) |
| fills | **unstated**, no commissions or slippage mentioned; channel disclaimer: not net of all commissions |
| control | ⭐ **"any day"**: same structure, unconditional entry. The right kind of control; no significance test against it |
| win rate / avg / tail | avg P&L and ROC read out; win rate "relatively stable… modest decline" (no values spoken); **no worst trade, no drawdown**; largest loss/BP "decreases" (no value) |
| significance | none |
| selection | ⚠ **excludes Feb–Apr 2020 by design**; the 3% bucket is dominated by 2022; overlapping entries |

## Numbers as spoken

| @ | number |
|---|---|
| 01:14–01:40 | SPY, from 2020 after the COVID crash, **16Δ strangle, 45 DTE**, managed at **21 DTE** |
| 02:02–02:12 | not 10–12 occurrences a year but "like **200**… about **100 and something**" (entries at each available 45-DTE expiry) |
| 02:40–02:53 | buckets: **any day / down up to 1% / down 2% / down 3%+** |
| 03:30–03:38 | "all the trades bucketed together in the six year: **$105** average P&L from the entry to the close" |
| 04:37–04:44 | down 3%: "your average P&L… is **more than double**" the any-day basket |
| 05:22–05:28 | return on capital "**1%** versus almost **3%**… **2 and 1/2%**" (any day vs down 3%) |
| 05:51–06:10 | win rate "goes down" in the bigger sell-off buckets, average P&L goes up (values not read) |
| 07:58–08:27 | premium / buying power: **≈ 8%** on a big down move vs **≈ 5%** "just in general" |
| 08:35 | "your largest loss as a percentage of that buying power also decreases" (no value) |
| 06:22 | "you might get **five of these or 10 of these** in this data set. I don't know how many 3% moves" |

(Description text: "average P&L more than doubles on 3% down days vs. any day", "return on capital jumps from 5% to 8%
of buying power". That second phrase mixes up premium/BP with ROC. The spoken ROC is 1% → ~2.5–3%.)

## ⭐ Is "sell after a 3% drop" the same as our certified bearish-high-IV cell?

**Same family, different trade, and our cell is the stronger evidence for the idea.**

| | tastylive "down 3%" | our certified cell (Tier A/B, 2026-09-22) |
|---|---|---|
| trigger | an **event**: SPY closes −3% or worse on the entry day | a **state**: SPY below its 50-DMA **and** VIX ≥ 20, checked each Friday |
| structure | **naked 16Δ strangle** (short put + short call) | **defined-risk bull put 0.25/0.15**, put side only |
| tenor / exit | 45 DTE, closed at 21 DTE | 20 DTE, 50% take, no stop, else expiry |
| fills | unstated (likely mid) | real fills + house cost model (net ROC on max loss) |
| period | ~mid-2020 → 2026, **COVID crash excluded** | 2018-02 → 2026-02, **COVID crash included** |
| n | ~14 trigger days, ~4 episodes (our count) | **75 trades, 37 months** |
| result | avg P&L > 2× any-day; ROC ~1% → ~2.5–3% | **+6.76% net of max loss, 94.7% win, month-clustered t 6.07, 8/9 years**; worst −100.7%; **42.7% of trades in 2022**; SPX condor same regime t 5.21 = the same episodes, **one bet** |
| significance | none | CONFIRMED after the ledger-wide BH/Šidák charge |

- **Overlap:** of the 14 SPY ≤ −3% days since May 2020, **11 fell inside Bearish_HighIV** (below 50-DMA, VIX ≥ 20).
  The three that didn't (2020-06-11, 2020-09-03, 2022-08-26) were sharp drops from above the 50-DMA. So tastylive's
  trigger is largely a **subset** of our state, and it fires ~14 times where our state gives 75 weekly entries.
- **The COVID test they skipped, we passed:** our cell's Feb–Apr 2020 entries were +13.8%, **−100.1%** (2020-03-06,
  max loss), +20.6%, +12.3%, +16.8%, +13.1% (`tierab_trades_2026-09-22.csv`). The defined-risk wing capped that
  one trade at −100% of max loss. **A naked strangle has no cap**, and no call-side hedge either. The same crash
  would have cost it many multiples of credit (their own sister video, saFY8btmLZ0, puts the worst 25Δ managed
  strangle at 13× credit).
- **Their extra ingredient, the short call, is the side we have no edge on:** ETF condor call side **+0.36%/trade,
  t 0.6** (FAIL). After a −3% day, the call mainly adds whipsaw risk from V-shaped reversals (April 2025).

**Verdict on the claim:** ✅ **AGREES in direction.** Selling index premium after a sell-off is the one short-premium
idea that certifies here. ⚠ **Not the same test**: their evidence (n ≈ 14 days, COVID excluded, naked, likely mid,
no t) couldn't support the claim alone, and the certified version is a put-only, defined-risk, trend × VIX state.

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 03:30 | The any-day SPY 16Δ 45/21 strangle averaged **+$105** over six years | ⚠ **Probably mid, and window-dependent.** Our nearest measurement: SPY **20Δ** 45/21 strangle, Friday entries, **sell bid / buy ask**, in the same post-May-2020 window: **managed +$0.225/share (+$22.50/contract), 64% win, month-clustered t 1.91** (n 160, 55 months); held to expiry **−$0.66/share**. Across the full 2018–2025 sample SPY managed is **−$0.46/share** and the 44-name panel **−$1.02/share** (`exit_21dte_2026-09-23.csv`, a descriptive slice, not a pre-registered test). Their $105 vs our ~$22 ≈ the fill convention plus daily vs Friday entries. The COVID exclusion is what turns our SPY number from negative to positive. |
| 04:37 | Down 3%: average P&L more than doubles | ✅ **Direction agrees** with the certified Bearish_HighIV cell (t 6.07). ⚠ Their own n is ~14 days in ~4 episodes, with COVID excluded. |
| 05:22 / 07:58 | ROC rises (~1% → ~2.5–3%) because premium/BP rises (5% → 8%) | **Mechanically true**: naked Reg-T BP is roughly fixed while premium scales with vol. Not an edge by itself; the premium/BP ratio is highest exactly when realized vol is also highest. Our post-shock premium test: after ≥ 2σ SPY days, 10-day straddles vs VIX-matched days **−10.8pp (t −1.8)**. The extra premium after a shock is the VIX level, not an extra over-statement. |
| 05:51 | Win rate is only modestly lower after big down days | No numbers given. Our cell has a **94.7%** win rate *with* a −100% worst trade: a high win rate doesn't bound the tail. |
| 07:06 | Why it works: vol contracts faster than price moves against you | **Plausible, consistent with our GEX work.** Negative dealer gamma adds realized vol beyond VIX (**+8%, t 7.7**), and VIX ≥ 20 + below-50MA is the regime where that tends to happen, so the premium has to be large to compensate. It evidently is, for 20-DTE defined-risk puts. |
| 07:16 | "If you put it on prior to volatility expansion, you get the worst of both" | ✅ **Agrees**, and it's the reason the trigger must be *after* the drop. A pre-spike entry is the Freedom Income 2/27 case (TEST_INDEX §9: modelled ≈ −106% of credit at 21 DTE). |
| 08:49–09:53 | Be nimble, stay small, take profits quickly; down days can start larger moves | ✅ **Sizing agrees** (our bucket is sized as ONE position across SPY/SPX/QQQ, "Index stress bucket", $3k total). ⚠ **"Take profits quickly" isn't supported by our exits:** on ETF bull puts the 50% take / 2× stop is **−4.3%/trade, t −5.4** vs holding. The certified cell uses 50% take on SPY, but that wasn't tested against hold in that cell. |

## What I would take

1. **Confirmation, not new evidence.** tastylive's research desk reaches the same conclusion as our certified cell:
   sell index premium after a sell-off. Their test is weaker than ours on every axis (n, fills, COVID, t), so it
   adds no confidence. It does show the idea is standard doctrine, which is a mild warning about crowding.
2. **Keep the put-only, defined-risk version.** The strangle adds a call side we can't show pays, plus an uncapped
   tail in exactly the regime where tails happen.
3. **The trigger vs state question is worth one test** (below): does the −3% day add anything *within* our
   Bearish_HighIV state?

## Not tested, could be

- **⭐ "Event trigger within the state": does entering the day after a SPY ≤ −2%/−3% close improve the certified
  Bearish_HighIV bull put, vs the Friday-entry cell and vs non-trigger days in the same state?**
  - **Spec:** same engine as `run_tierab_significance.py` (`build_put_spread_trades`, 0.25/0.15, 20 DTE, 50% take,
    no stop, cost model on). Entries on (a) the Friday cell as-is, (b) the session after a SPY ≤ −3% (and ≤ −2%)
    close in the state, (c) matched non-trigger days in the same state as control. Primary = (b) − (c), clustered by
    episode.
  - **Data:** `data/cache/SPY_puts_v3_2018_2026.parquet` covers it at real fills (bid/ask through ~Mar 2026).
    Recover spot from the chain; v3 strikes are RAW.
  - **Effort:** ~½ day. **Prior: UNDERPOWERED.** ~20–30 trigger days in 2018–2026, ~5 episodes; the answer will
    almost certainly be "can't distinguish".
  - **Worth recording, not worth running** unless Gabe wants to use a −3% day as an entry-timing rule inside the
    bucket.
- **Their exact test at real fills, COVID included:** SPY 16Δ strangle 45/21, daily entries, four return buckets.
  - Needs a SPY call pull from v3 (puts are cached).
  - **Effort:** ~½ day.
  - The answer that matters is the 2020-02/03 rows. Prior: the ≤ −3% bucket's mean survives without COVID and
    breaks with it.

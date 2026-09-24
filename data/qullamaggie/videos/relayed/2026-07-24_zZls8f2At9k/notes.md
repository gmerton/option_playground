# Jack Corsellis: "The 1 Change for How I Improve Win Rate Trading Qullamaggie's Breakout Strategy" (2026-07-24, 9 min)

_Reviewed 2026-09-23. Solo bar-by-bar replay of one session (2026-06-22): 5-minute opening-range breakouts in AMD
and CIFR, shown on a wall of 5-minute charts grouped by theme. Transcript (auto-captions) in this folder._

⚠ **Second-hand relay.** Corsellis sells a community and live room, and the video is sponsored (MarketSurge).
Kullamägi is invoked by name only. The primary spec is in [`../../../README.md`](../../../README.md), and where the
two differ, the primary source governs.

## Verdict: 1.5 / 5

The "one change" is **group/theme confirmation**. He only takes a 5-minute ORB when most of the stock's theme
(semis, AI storage, crypto-miners-turned-data-centres) is breaking out at the same open and leading SPY/QQQ. A
"lone ranger" breakout is "more failure prone in my view" (08:39). It's a coherent idea and it's cheap to code.

The evidence is one session, picked afterwards, on which "you literally could have thrown a dart at any of those,
including the indexes" (07:39). He says that himself, and it's the problem. On that day the *market* won, so the
day proves nothing about the filter. He shows no count, no win rate before and after the change, and no stop.

What we have on the nearest questions points the other way:
- **At the daily level,** breakouts from the weakest sectors beat those from the strongest. Same-date paired, the
  gap is +5.60pp at 63 days (t 2.61).
- **Intraday,** our ORB trigger loses to a random minute in the same name at t −8.50.

**The change plausibly moves WIN RATE, not expectancy.** On a day when the whole theme and the index are ripping,
almost any long entry is green by the close. That's theme and market beta, and it raises the hit rate of *any*
entry on that day, not the edge of the trigger. The only control that separates the two is holding the name-day
fixed and moving the entry. Our ORB9 test did exactly that, and the trigger lost.

## Where he departs from Kullamägi's primary spec

| element | Corsellis (this video) | Kullamägi (primary, README) | consequence |
|---|---|---|---|
| when the ORB is valid | AMD "basing along some moving averages" (00:56); the ORB *is* the signal | ORH entry only "once the daily breakout is under way"; the breakout "has to be obvious on the **daily** chart" (CWT 00:35:51, 00:37:28) | Corsellis trades an intraday trigger with no daily-breakout condition. That's closer to our Stage A / ORB9 alerts than to Q's breakout |
| first-candle quality | the opening 5-min bar must open near its low and close near its high ("go go gadget", 02:54–03:26), via his TradingView indicator | not in the spec. Q takes the 1-, 5- or 60-min ORH | an added filter, untested by anyone on camera |
| stop | **never stated** | LOD, absolute, intraday (CWT 00:41:43) | a win rate with no stop defined can't be scored |
| group/theme | the "one change": the whole theme lit up, plus the index | not in the four primary videos. Q's scan is **bottom-up** single-stock momentum (top 2% by 1–18-month return, $150M) | the headline rule isn't Kullamägi's |
| market | "preferably the indexes also showing strength" (05:55), a gap-down reversal bar on SPY/QQQ | "breakouts don't exist in a falling market", read on the **daily** index (CWT 00:28:43) | direction agrees, timeframe doesn't |
| daily trend | above all key daily MAs; avoid overhead 50-day (07:06–07:22) | pullback holds the 10/20-day, higher lows, tightening | consistent |
| objective | "improve the win rate" (title, 09:00) | runs a **25–35%** win rate on purpose; ~20% of trades make the money (CWT 00:39:19) | Q doesn't optimise win rate. A filter that raises it by giving up the lone right-tail names can lower his expectancy |
| attribution | ORB "first taught by Toby Crabel, then popularised by Qullamaggie" (00:08) | — | fair. Crabel's *Day Trading with Short Term Price Patterns and Opening Range Breakout* (1990) predates Q |

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:42–01:27 | AMD and CIFR each go green on his 5-min ORB indicator; entry = the break of the first 5-min high into new high of day | ❌ **Contradicted as a trigger.** TEST_INDEX §5, "intraday alert suite re-examined" (`alert_triggers_2026-09-23.md`, 1,411 ORB9 alerts, 153 sessions): with the name-day fixed, ORB9 earns **+0.351%** vs **+0.775%** for a random minute in its own window. That's **−0.425pp, t −8.50**, both halves. Stage A (11,227 fires): every arm −0.10 to −0.13R, and a random minute beats the trigger. Entry study (2026-09-17): **ORB15 + re-entry −1.22pp vs buying the close, t −3.4** |
| 02:33–03:40 | The opening bar opening on its low and closing on its high = "demand instantaneous… in control" | **Untested as an ORB gate.** The nearest daily analogue is close-in-range on the breakout day. That's flat and non-monotone vs forward return, the strongest closes are the WORST 60d cell, and close-in-range mostly measures stop distance (`close_strength_2026-09-22.md`). No reason to expect a 5-min version to differ, but it hasn't been run |
| 03:44–05:00 | ⭐ **"The one change": group/theme confirmation.** Take the ORB only when the whole theme is breaking out, not AMD alone | ❌ **Contradicted at the daily level (nearest test); the intraday version is untested.** `industry_rotation_detection_study.md` Part III: RVOL ≥ 1.8 50-day-high breakouts, 299 names, 2006–26, tagged by sector 63d RS rank. **Top-3 sector +7.11% vs bottom-3 +14.55% at 63d.** Net of the stock's own sector ETF the gap is still **+6.13pp**. **Same-date paired over 265 dates: +5.60pp, t 2.61**, in favour of the lone name in a weak group. Not the same object: 11 GICS sectors on a 63-day RS rank, not same-morning co-breakouts within a theme, and 63d, not intraday. But the direction is the reverse of "lone rangers fail". ⚠ t 2.61 is below the house bar |
| 05:00–05:53 | Group the chart wall by theme so you can see "where is the money flowing" at a glance | **A workflow, not a claim.** The desk already has this: `clusters_latest.csv` (SECTORS/INDUSTRIES with lead/prec/brk counts) and industry-ETF context per alert in `lib/alerts/detectors.py`. Our alert-funnel test found the intraday layer adds nothing beyond the daily layer-2 state |
| 05:55–06:08 | Prefer the indexes showing strength (a gap-down reversal on SPY/QQQ) | **Mixed, not certified.** Market-wide breakout activity (5-session breakout count as a percentile of its trailing year) sorts the precision-tier book: Q1 +0.06R → Q5 +0.86R, **t 2.59, PARKED**, and it fails the Šidák-7 charge. Trailing-30d breadth rules all **FAIL** 2019–26 (weak breadth is a mild BUY). No intraday index-reversal gate has been tested |
| 06:24–06:58 | The pick breaks out "ahead of the cues… ahead of the spy" (intraday RS vs index) | **Contradicted on the adjacent daily measure.** Down-day RS as a selection filter is **INVERTED: −3.51pp at 63d, t −3.33**, both halves negative. An intraday "leads the index at 09:35" variant hasn't been run |
| 07:04–07:28 | Prefer names above all key daily MAs; skip ones with overhead 50-day | ✅ **Consistent with the house vetoes.** The rotation study's by-products added vetoes below the 200 SMA / 6-month < −10%, and the precision tier requires the EMA stack. ⚠ The tier itself is NULL on freeze-forward (a regime finding, not a selection one) |
| 07:37–07:55 | "Throw a dart at any of them, you're in the money… does that happen every time? Absolutely not" | **This sentence is the review.** If a dart wins, the day did the work. That's precisely what the random-minute and random-peer controls exist to subtract. In the ORB9 test a random *peer* name at the same minute earned **+1.029%**, more than the trigger's own name at a random minute (+0.775%) or the trigger (+0.351%). On the curated list, the day and the universe carried the return |
| 08:15–08:46 | "If you can't see this [layout], I can't help you"; lone-ranger stocks are "more failure prone in my view" | **Opinion, no count.** See the theme row: the only measured version favours the lone name |

## What I would take

1. **Nothing to adopt.** The trigger he's filtering (a 5-min ORB) is INVERTED against its right control here, and
   a filter can't make an inverted trigger positive. At best it picks better days to lose less on.
2. **A clean statement of the win-rate trap.** Theme-plus-index confirmation raises the share of green entries on
   the days it allows, because on those days everything is green. Win rate goes up, and the edge over a random entry
   that same day doesn't have to move at all. Useful as a worked example of why the house bar is *signal minus
   same-name-day control*, not raw hit rate.
3. **A portfolio point he doesn't make.** Taking AMD, CIFR and "a couple of others" off one confirmed theme at one
   open is **one bet at several times the size**. The ORB9 peer control shows how much of an intraday result is
   the common day. If the filter were ever adopted, cap entries per theme per day.

## Not tested, could be

The group-confirmation gate is codable at two resolutions. **Run the daily one first**: it has two decades of data
and it asks the question the rotation study didn't (same-day co-breakouts, not 63-day sector RS).

**A. Daily co-breakout gate (primary). ~½ day on `lib/studies/pattern_test.py`.**
- **Pool:** house breakouts (20d-high close, RVOL ≥ 1.8, above the 50/200 SMA), liquid panel 2019-10→2026-09;
  the precision tier as a secondary cut only (it's NULL on freeze-forward).
- **Group:** the industry map behind `clusters_latest.csv` / `data/watchlist/group_etfs.csv`, frozen, groups with
  ≥ 5 members. `peer_brk` = share of the *other* members that also close at a 20-day high on the same date. Uses
  only same-day closes, so it's knowable at the entry close.
- **Arms:** `CONFIRMED` peer_brk ≥ 30% · `LONE` peer_brk = 0 · middle reported, not tested.
- **Primary cell, named in advance:** CONFIRMED − LONE, **same-date paired**, 20-EMA close trail, in **% return and
  R both**, t clustered by date. Also report the **win rate** of each arm so the win-rate/expectancy split is
  visible, not argued.
- **Controls:** `post` (same name, random later day) and `xname` (same day, random non-breakout name in the same
  group). The second holds the theme-day fixed, so it measures whether the *breakout* adds anything once you know
  the theme is running.
- **Bar:** |t| ≥ 3, both halves the same sign, per-year table. 2 arms × 3 horizons (10/21/63d) → Šidák-6 ≈ 2.64,
  so the house 3 governs.
- **Prior:** CONFIRMED has the higher 10-day win rate and the *lower* 63-day return, since the rotation study
  favours lone names by +5.6pp. A positive CONFIRMED − LONE at 63d would contradict it and would need the
  outcome-conditioning check first.

**B. Intraday version (his actual rule). ~1 day; power-limited.**
- 1-min cache (`data/cache/intraday_1min/`, curated list, 2026-02→09, ~150 sessions). ORB5 = first 1-min close above
  the 09:30–09:35 high, 09:35–11:00. Optional first-bar filter: open in the bottom 25% and close in the top 25% of
  the bar's range. Stop = 0.6-ADR floor (the adopted ORB9 mechanics). Session VWAP rebuilt from price × volume (the
  cached `vwap` column is per-bar).
- `theme_conf` at the entry minute = share of ≥ 3 cached same-industry peers whose own ORB5 has fired, plus the
  industry ETF above its 5-min high.
- **Primary:** ORB5 minus a random minute in the same name-day, **within** CONFIRMED vs within LONE (difference-in-
  differences). That's the only design where the theme can't pass as a trigger edge. Month-clustered t is
  meaningless on 7 months; cluster by date.
- ⚠ The universe is hindsight-curated, and the ORB9 control already shows the curated universe carries the result.
  Treat any positive as a forward-lockbox candidate at most.

**Not queued** unless Gabe asks. Given the rotation study and ORB9, the prior for A is NULL-to-INVERTED on
expectancy.

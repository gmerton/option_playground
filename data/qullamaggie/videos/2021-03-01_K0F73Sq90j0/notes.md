# Chat With Traders #212 — Kristjan Kullamägi, "Breakouts, Home Runs & Exponential Returns" (2021-03-01, 76 min)

_Reviewed 2026-09-23. Aaron Fifield's podcast. Background (2011 start, blow-ups, day trading → swing), then a
deep dive on **one** setup, the breakout: entry, stop, partials, trail, market filter, portfolio size and sizing.
Timestamps marked **exact** are from `transcript.txt`. Others are the start of ~45-s blocks (±45 s)._

## Verdict: 3.5 / 5 (best in the KB, as a *specification*)

This is the **primary-source** statement of the breakout system, in his own unclipped words. It supersedes the
Breitstein relay (`data/lance_breitstein/principles/qullamaggie-system-relayed.md`) wherever they differ.

He's also unusually candid about his weaknesses:
- win rate **~35% in 2020 and ~25% in 2019** (exact 00:39:19–00:39:30);
- ~20% of trades make all the money;
- "I'm so good at the entries but my exits are just so bad… **three quarters of the time** it doesn't pay" to
  override his own trail (exact 00:57:41–00:58:29).

It stays at 3.5 and no higher because there's **zero evidence**: no P&L, no expectancy (he says he doesn't
know his average win/loss, 00:52:43), and no losing examples. The host's "eight-figure club" introduction is an
assertion.

## ⭐ The exit rule, verbatim, and how it differs from the relayed/queued version

| @ (exact) | His words |
|---|---|
| 00:19:58–00:20:43 | "You can hold them for maybe **three to five days** and just sell into strength, **or** you can try to hold for bigger moves… use the **10 and 20 day moving averages** trailing stops… do fewer trades that way, or do more trades by just buying breakouts and selling after… **day three or five**, because that's how stocks move, in **momentum bursts**" (credited to Stockbee) |
| 00:23:21–00:23:58 | "I **always sell some into that first burst** to lock in a little bit of profits, **maybe I sell 20 or 25 [%], or it can vary a lot**… now it's a stress-free trade… worst case **break even** or maybe even make money, **depending on how much I move the stop higher**" |
| 00:35:14–00:35:30 | "With a breakout method I just **buy everything at once** and then I scale out. I usually scale some into strength and then I use a trailing stop, it's usually a **10 or 20 day moving average for the rest**" |
| 00:41:43–00:42:29 | "Initially my stop is always **low of the day**… the faster moving stocks I use the **10-day** and the slower moving ones I use the **20-day**… once the moving averages start to catch up… **once the 10-day catches up to my initial stop** and moves higher, then I start moving my stop with the 10-day" |
| 00:42:29–00:42:58 | "I wait for the **first close**. I have **one absolute stop** where I get out no matter what, and the trailing stop is, if it violates it intraday I'm not worried, **I only wait for the close**… if it's 10–15 minutes before the close and it's obvious it's going to close below that moving average, that's when I close the rest" |

**Differences from the queued row** ("sell ⅓–½ on day 3–5, stop to breakeven, trail 10/20-day"):
1. **Partial size.** Here it's **20–25%, "can vary a lot"**. The ⅓–½ comes from the relayed clip (date unknown,
   possibly a later era) and from his TSLA practice in the 2020-07-02 stream ("sold a third… down to half").
   The size should be a swept parameter {20, 33, 50%}, not fixed at ⅓–½.
2. **Partial timing.** "Into that first burst": **strength-triggered, not a fixed day**. Days 3–5 appear as the
   horizon of a momentum burst and of an *alternative full-exit style*, not as the partial date. A fair test
   needs arms for both day 3/5 and "first +k ADR close" triggers.
3. **Breakeven is implied, not stated.** "Worst case break even… depending on how much I move the stop higher."
   The stop moves to ≥ entry after the partial.
4. **The trail activates only when the MA overtakes the initial stop** (stop = max(entry-day low or breakeven,
   MA)). It isn't applied from day one. That's the detail the risk-architecture "`close<10EMA` negative in all ten
   stop rows" test did not replicate.
5. **Two-speed trail keyed to the name**: 10-day for fast movers, 20-day for slow. He never gives the speed
   threshold. The mechanisable proxy is ADR (e.g. ADR ≥ 5% → 10-day).
6. **Execution:** the initial LOD stop is **absolute (intraday)**; the trail is **close-only**.
7. **MA type unspecified** here ("moving average"). The relay says SMA; the house uses EMA. Minor
   (parameter-insensitivity is his own admission in the relay).

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:04:39–00:07:41 | Blew up 3–4 times with $3–5k accounts in 2011–12; first million mostly day trading | Biography, unverifiable. The Breitstein relay says Swedish tax records are public. Not checked here |
| 00:14:37–00:15:23 | Setups came from **Stockbee** and **O'Neil's HMMIS**; "same patterns in the 1800s, 50s, 80s" | Provenance note. O'Neil pieces we tested: FTD **NULL**, pyramid **NULL**, 8-week hold **NULL** (`oneil_8wk_trades.csv`) |
| 00:16:10–00:17:42 | Build confidence by "back-testing": screenshots of hundreds or thousands of examples in Evernote | ⚠ **Not a back-test.** A screenshot library of setups that moved is outcome-selected, so it can't give a base rate. See the 2020-05-27 notes |
| 00:18:28–00:19:58 | The breakout: stair-steps. A leg up, then sideways or a pullback with **contracting volatility**, then "buy it **just as it is about to break out** into the next step" | **The trigger is our measured leak.** The house breakout buys **+0.52 ADR above the prior 20d high vs −2.09 ADR for a random later entry = 2.6 ADR paid**, and the **same-name later control beats the signal** (−0.21…−0.33R vs +0.13…+0.21R) (`entry_vs_stop_2026-09-20.md`). ⚠ "Contracting volatility" = VCP, **never tested here** (§10 QUEUED) |
| 00:20:43–00:21:28 | "The stronger the stock the better… the stocks that make the biggest moves keep making the biggest moves"; mid/large caps, not pumps | **Supported at the universe level:** momentum universes beat the TT (AH +0.87, INT +1.44 vs TT +0.56 at 20d, ADR-matched), but "no arm passes on breakouts → **the universe carries the return, not the trigger**" (`universe_test_2026-09-21.md`) |
| 00:25:18–00:26:04 (exact 00:25:21–00:25:58) | **Scan**: **top 2%** of all stocks by return over **1, 3, 6, 12, 18 months**, with a **$150M** dollar-volume cutoff (was $20M two years earlier) | **Not run as specified.** Closest is the universe test above. HYB-B's $100M ADDV + ADR ≥4 is PARKED (t 2.6), and the TT ablation says the $200M ADDV floor is the criterion to re-tune (it drops 60% of names). ⚠ His cutoffs move with his account size. That's a capacity constraint, not a signal |
| 00:26:49–00:28:19 | Quality: after doubling in ~3 months, a pullback retracing ~⅓ into the **10/20-day MA**, then a bounce or **higher lows getting tighter** ("linearity"). "It's very intuitive, **you can't really scan for this**" | Partly untested (VCP §10), partly NULL: trend smoothness **NULL**; `sma_stacked` **INVERTS** (−0.013); distance to the 21 EMA is the best single hold predictor but only +0.057R (t ~2). His own "can't scan for it" puts linearity outside mechanical testing |
| exact 00:28:43–00:29:08 | "The best time to trade this breakout method is **after a pullback in the markets**… stocks that **held up the most**… coming out of a 5, 10, 15% correction, that's **almost like free money**" | ❌ **Our closest test is INVERTED.** Down-day relative strength as a selection filter (`run_downday_rs_selection.py`, 2026-09-23): names that held up on QQQ ≤ −1.5% days, dose ≥2, then the next breakout → **−3.51pp at 63d, t −3.33, both halves negative, monotone dose-response**, vs undosed near-high breakouts. ⚠ Definitions differ (ours = single down days; his = held up through a multi-week correction and built higher lows). The multi-week version is §10 QUEUED "Stocks that hold up in a weak tape". **"Free money" is contradicted in its nearest form** |
| 00:30:36–00:33:37 | Combine with fundamentals: EPS/revenue growth or a hot theme (EV/lithium, QS). "If I took the fundamentals out my profitability would drop a lot". Gives him conviction → size | **Untested as a filter.** Nearest: leading-group filtering **INVERTED** (bottom-3 sectors beat top-3, t 2.6); PEAD surprise **NULL**. His claim is about *size conviction*, and we can't observe that |
| exact 00:35:14–00:35:30 | Buys the full position at once; scales out into strength; trails the rest on the 10/20-day | See the exit section. Scale-out cells in our data: **trim half at +2R −0.26R (t −3.8)**, at 2 ADR ext −0.33R, at 3 ADR ext −0.25R. BE after +1R **−0.08R**; BE after a +2R close **+0.01R (harmless)** (`profit_lock_2026-09-20.md`). **Every component of his management that we've tested separately costs expectancy**, but never as his combination with a *delayed* trail |
| exact 00:35:43–00:36:56 | **Entry = opening-range high** (1-min, 5-min or 60-min candle) **once the daily breakout is obvious**; if it isn't obvious on the 1-min, take the 5-min when it is. **Stop = low of the day** | ❌ **Contradicted on the entry.** Entry study: **buying the daily CLOSE beats every intraday entry**, ORB15 + re-entry **−1.22pp, t −3.4**. The disaster-stop addendum still finds ORB +5.41% < CLOSE +5.94% (`entry_study_2026-09-17.md`). ORB9 vs a random minute in its own window **−0.425pp, t −8.50**. ⚠ His **60-min** ORH is untested. It's the closest to "buy when the daily breakout is obvious" and nearest to our close entry |
| exact 00:38:56–00:39:38 | Stopped out within minutes "all the time", especially on 1-min ORH, re-buys on a retake of the highs. **Win rate ~35% (2020), ~25% (2019)** | ✅ **Mechanism AGREES; it's the cost we measured.** Intraday stop execution + re-entry: re-entry "repairs only part" (entry study). A 25–35% win rate is consistent with our 23.6% hold cohort. It also means his record is a **right-tail** record, so it's statistically fragile at any trade count he could have (§10 lived-experience row: the AI Pathways illustration, 37% win at 2R, needs n ≈ 1,854 for t 3) |
| 00:40:32–00:41:17 | Never hesitate on a stop: "your stop is twice as big… three times as big" | ✅ **AGREES** with house practice and the August lens (stops blown past 2%) |
| exact 00:41:43–00:42:58 | Stop at LOD, **absolute**; trail on the 10-day (fast) / 20-day (slow) once the MA catches up; **exit on the first CLOSE below**, never intraday | ✅ **Close-only trail AGREES:** the close-judged stop beats intraday execution (entry study; gap-share study: a resting stop costs −0.13/−0.17R in mid/high terciles, t −2.46). ⚠ **The absolute intraday LOD stop CONFLICTS** with the house tight stop, which is judged on the **close** (`stop_definitions.md`, DINO 2026-09-22), unless it's read as our 1-ADR resting disaster stop |
| 00:43:33–00:45:05 | Adds only when a **new setup** develops; the add is a new trade with its own rules | Pyramid test: adds earn +0.30…+0.66R on their own risk (t 0.4–1.5), and **no add condition beats the unconditional add** (best +0.15R, t 1.25) → **NULL**. Treating the add as its own trade is harmless bookkeeping |
| exact 00:47:01–00:47:39 | "Breakouts **don't exist in a falling market**… don't touch it, it's going to fail most likely"; uptrending/sideways works, downtrending → cash, smaller size | **Our evidence is SPLIT.** Carter risk-architecture regime test (2,684 names, 2006–26, portfolio level): SPY > 200SMA+up gate "the single most valuable variable… halves drawdown, doubles CAGR" (`carter_mastering_the_trade/backtests/risk_architecture/REGIME.md`). But on the 2019–26 breakout pool the **SPY state doesn't forecast next-month breakout R** (bear +0.32 / chop +0.57 / up +0.22) (`breakout_regime_and_stop_distance_2026-09-17.md`). ⚠ His relayed **10/20-day index filter** is untested |
| exact 00:50:40–00:51:07 | Portfolio grows to 20–30 names in a bull run; "every time I ended up with 30 positions (**3 times** in 12 months), in the next few days the market pulled back" = "a proprietary indicator" | **n = 3, and it points the other way from our nearest measure.** Breakout activity as a regime gate: **the top quintile of the 5-session breakout-count percentile = +0.86R next** (t 2.59, PARKED, fails the ledger correction). High breakout activity preceded *better* breakouts, not a pullback. ⚠ Different target (index pullback vs breakout R) |
| 00:52:43–00:55:00 (exact 00:54:14–00:54:49) | Doesn't know his average win/loss. "Maybe 20% of my trades, that's where all my money comes from"; "home-run trader" | ✅ **Shape AGREES:** 23.6% of breakouts hold = +1.27R; the top 8 of 83 months = 68% of positive R. ⚠ That's a *shape*, not an edge. Our own shape-matched book is **month-weighted −0.007R** (O'Neil test) |
| 00:55:47–00:58:51 (exact 00:57:41–00:58:29) | Biggest flaw: overriding the MA trail by selling "overextended" names (NVAX doubled after he sold); overriding "doesn't pay three quarters of the time" | ✅ **Strong AGREEMENT with our exits:** "extended → tighten" **INVERTED** (BE −0.19R t −2.8; 10-EMA once ≥2 ADR extended **−0.47R t −4.8**); single-day spike override **NULL** (+1.2pp, t 0.18) on real call prints. ⭐ Note the tension with his own partial rule: selling "some into the first burst" is also an override of the trail, and our trims cost −0.25…−0.33R |
| 00:59:37–01:03:24 | Scale size with the account (double account → double risk, lagged a few months); **use margin only when things are going well**, "you have to deserve it" | **Equity-curve conditioning is unsupported here.** Own trailing results don't forecast the next month (rank corr +0.01); hot alert stretches aren't followed by better sessions (edge corr −0.09…−0.23); only one lean survives (a low-stop-out month → +0.79R, t 2.0). Keeping risk a constant % of equity is uncontroversial |
| 01:04:37–01:05:40 | "An inverse correlation between the number of indicators and profitability"; price only | ✅ **AGREES** (TT ablation: 2 criteria logically redundant, the rest underpowered; within-date ranking 71/72 cells fail) |

## What I would take

1. ⭐ **The exit spec above** replaces the relayed version as the thing to test. It differs from the queued row on
   partial size (20–25% here), partial trigger (first burst, not a fixed day), and trail activation (only once the
   MA overtakes the initial stop).
2. **The close-only trail** is house practice already. His intraday LOD stop maps onto our 1-ADR resting disaster
   stop, not the tight stop. Don't import it as a resting tight stop.
3. **His exit self-diagnosis is corroborated by our data**: don't sell because it's "extended".

## Not tested, could be

- ⭐ **The partial-then-trail exit as he states it** (README test 1). ~½ day on `run_profit_lock_study.py`.
  **Prior: slightly negative on mean R, positive on drawdown.** Every component (trim −0.25…−0.33R, BE-after-+1R
  −0.08R, 10-day trail on fast names) has cost R separately. The delayed trail activation is the one untested
  twist.
- **The 60-min ORH entry** vs the close entry, on the entry-study name-days (the 1-min cache has it). ~½ day.
  Prior low (ORB15 already −1.22pp).
- **The 10/20-day index filter** vs SPY>200 on the breakout pool (the relay's test 2). ~½ day.

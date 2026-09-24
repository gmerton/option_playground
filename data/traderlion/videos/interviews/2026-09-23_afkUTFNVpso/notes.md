# TraderLion: "How to Find A+ Trades Like a Market Wizard | Best Screens for CANSLIM Traders" (Ross Haber with Richard, 2026-09-23, 2 h 02 min)

_Reviewed 2026-09-23. Session 1 of a 5-part "Growth Stock Trading Workshop" (CAN SLIM). Slides, then a live
Deepvue screening demo, then Q&A. Transcript (`en-orig` auto-captions) in this folder. Timestamps below are
`[h:mm]` to the minute, from the transcript. Numbers are as captioned; tickers flagged `(?)` are caption guesses._

⚠ **The title and description don't match the video.**
- **No Market Wizard appears.** Ross Haber is a former William O'Neil + Co. money manager (from 1998 [0:21]).
  He is not in Schwager's books, and nobody claims he is.
- **The description's timestamps are wrong for most sections.** It says quarterly EPS/sales at "1:30:15"; that
  is actually [0:24]-[0:38]. Double bottoms are listed at "15:30" but come at [1:14]. "Analyst estimates vs
  printed growth" is listed at "1:44:50" but comes at [1:54]. Cyclicals are listed at "1:53:59" but come at [1:56].
- **"Best Screens" is overstated.** He names three screens, but the criteria for two of them are only shown on
  screen or described as "advanced logic". Only one criterion (a 250K volume floor he added) is ever read out.

## Verdict: 2 / 5

**What's good.** Haber is a real practitioner with a real lineage, and he is candid in places:
- "I have not done a study on this, this is pure observation" [1:20];
- he admits losing money by spreading across three names instead of buying the one with the best earnings [0:51];
- he says he changed his rules because of his age and temperament, not because of evidence [1:45].

The screen **is** codable in outline: RS-sorted, liquid, "up on volume", with CAN SLIM fundamentals (C and A)
as the final cut.

**The evidence is zero.** There's no track record, no base rate and no losers. The fundamentals examples are
four stocks picked for the slide ("I didn't pick perfect ones" [0:24]). The one statistic, "7 to 9 out of 10"
early-stage CAN SLIM breakouts never fall 7% [1:17], is a relayed O'Neil claim with no source.

**Our ledger already answers or contradicts most of the technical half:**
- **12-month RS** is exactly our Trend Template's c9 RS, which is UNDERPOWERED.
- **"Tight and orderly", low ADR** runs against our best universe arm, which requires ADR ≥ 4.
- **Group confirmation** is NULL, and the leading-group filter is INVERTED.
- **The "62.5% of correction days" leader screen** is a sibling of down-day RS, which is INVERTED at t −3.33.
- **"Picking is the easy part, risk management is everything"** is backwards on our data.

⭐ **The fundamentals half has never been tested in this repo.** Quarterly EPS growth and acceleration, sales
confirmation, estimates and institutional quality: no row in TEST_INDEX touches any of them. EPS growth
**is** testable on data we already cache. That is the one lead worth taking from this video.

## Provenance: who is speaking, what's being sold

- **Ross Haber** says he joined William O'Neil + Co. in 1998 and co-ran O'Neil's workshops for about three
  years (200–600 attendees each) [0:09]-[0:10]. He says he built "Model X" portfolios with Mike Webster and
  Charles Harris (caption "Mike and Charles") [0:08]. Later he was the technical partner to a former Fidelity
  mid-cap growth PM at a fund that "got up to about 660 [million] at its high", counting margin [1:32]. He now
  manages his own money [0:09]. Nothing here is audited, and no returns are given.
- **Richard** is the host. He built the "DV Leaders" screen [1:01]-[1:04], and he calls "Ry" "the other
  co-founder of Deepvue" [1:09], i.e. he is a Deepvue co-founder himself.
- **What's being sold:**
  - the TraderLion 5-part bootcamp: free live, "in the future … a paid workshop" [0:04];
  - a Deepvue discount link, pushed at [0:31]-[0:32], [0:53] and [1:07] (the product-roadmap pitch);
  - "over $250 in value" of bonuses behind an email capture [0:06];
  - IBD, "the best stock market newspaper on the planet" [0:08], [1:59].

  **The whole screening demo runs on the host's own platform, using the host's own proprietary preset.**
- Haber's "TML report" watch list (as captioned) [0:48], [1:03] appears to be his own publication; not verified.

## Inventory: every screen / filter stated, written codably

`D` = daily bars. `RS12` = IBD-style 12-month weighted RS percentile, `2·C/C[63] + C/C[126] + C/C[189] + C/C[252]`
ranked across the market. That is exactly the formula in `run_universe_test.py:54`.

### A. The three "go-to" screens (Deepvue presets) [0:43]-[1:09]

| # | Screen | Criteria as stated | Stated size | Codable? |
|---|---|---|---|---|
| S1 | **Up on Volume** (IBD / WONDA origin, his favourite) [0:43], [0:54] | "the stocks that are up doing the most volume for the day", **sorted by RS12 descending (99 down)**. The on-screen criteria are **not read aloud** ("a very simple screen" [0:54]) | ~200–250 names [0:44] | **Proxy only:** `close > prior close ∧ volume / avg50(volume) ≥ k`, sort RS12 desc. `k` is **not stated**; IBD's version is usually a volume %-change vs 50d avg. ⚠ Any `k` we choose is ours, not his |
| S2 | **DV Leaders** (built by the host) [1:01]-[1:04] | "liquidity, RS, earnings growth, sales growth, weighting recent stocks a little higher", "advanced logic" | 200–350 names [1:04] | **No: proprietary.** Only the ingredient list is public |
| S3 | **"Ry 62.5%"** RS screen [1:08]-[1:09] | stocks that outperform the market on **≥ 62.5% of days during a correction** (from a Deepvue co-founder's study of how leaders behave in corrections, unpublished), + Haber's add-on **average daily volume ≥ 250K** ("last over five", i.e. unclear window, probably a 50-day average) | "more manageable" | **Yes, approximately:** in a correction window (e.g. SPY ≥ 8–10% off its high), `share of days with r_i > r_SPY ≥ 0.625` ∧ `avgvol ≥ 250K`, sort RS12. The correction definition is not stated |

**How he uses them.** He runs all three through the day, sorted by RS12 (sometimes RS6) [0:58]. He spends under
a second per chart, adds names to one of two lists (the focused "TML report" list and a long list), and sets
alerts [0:44]-[0:46], [0:57]. Then he walks the leading groups for confirmation [0:46], and cross-checks with
Deepvue's theme tracker [0:47]. The whole routine takes about 30 minutes [0:46].

### B. CAN SLIM fundamentals: the final cut ("70% fundamentals, 30% technicals" per O'Neil [0:07], "more than twice as important as the chart" [0:23])

| # | Letter | Criteria as stated | Codable? / our data |
|---|---|---|---|
| F1 | **C** EPS [0:13], [0:24]-[0:26] | quarterly EPS **YoY (same quarter last year) ≥ 25% for ≥ 3 consecutive quarters**; "more is better"; his focus list targets **triple digits** ; ⭐ **acceleration** (growth rate rising quarter over quarter, e.g. "1 2 3 4 5 quarters of accelerating earnings" [0:26]) | ✅ **Yes on cached data.** `earnings_yf.parquet`: 1,330 names from 2002, 1,303 of them on the liquid panel, `eps_act` per report with a known session. Measured 2026-09-23: 2019+ has 36,177 events, 29,562 with a positive year-ago base; **30.3%** have YoY ≥ 25%, and **3 in a row fires on 8.8% of events (3,200 events, 793 names)**. ⚠ His loss-shrinking example (−$0.33 → −$0.11 called "+67%" [0:25]) has no defined growth rate. Exclude negative bases |
| F2 | **C** sales [0:28]-[0:30] | sales must "back up" earnings (growing too; not shrinking). **Exception:** big, steady sales (~$1B/qtr) with **no** earnings is fine for biotech/R&D-heavy names | ❌ **Not cached.** Quarterly revenue history would need SEC EDGAR companyfacts (free, point-in-time by filing date), about 1 day to pull. ⚠ The exception makes F2 non-mandatory, so as stated it is unfalsifiable |
| F3 | **A** annual [0:32]-[0:37] | annual EPS **and** sales growth **≥ 20%** (O'Neil), he prefers **25–30%+ and rising**. He lets deceleration slide when forward estimates are big | EPS: derivable (sum of 4 quarters). Sales: see F2 |
| F4 | Estimates [0:25], [1:54]-[1:55] | big forward estimates (analysts are "conservative", so O'Neil scales them up); estimates are "more and more important"; revisions/surprises for "the best of the best" | ❌ **No estimate history.** `eps_est` is only the consensus for the quarter being reported, not forward estimates or revisions. Surprise alone = PEAD, already NULL |
| F5 | **N** new product / disruptor [0:13], [0:19], [0:38] | "the one changing the way we work, live, communicate"; find it via IBD or AI [1:59] | ❌ Discretionary |
| F6 | **S** supply/demand [0:15], [0:39], [1:53] | **Ignore float/shares outstanding**; prefer the biggest, most liquid names that can still move **50–100% in 4–6 months** | Partly: liquidity yes, "can move 50–100%" is hindsight unless defined on the trailing window |
| F7 | **L** leader [0:20]-[0:21] | = **RS12**; also "first to new highs / first to reclaim the MAs after a correction" (host's question, accepted [0:20]) | ✅ RS12 = our c9. First-to-new-highs = FTD-names row |
| F8 | **I** institutions [0:21]-[0:22], [0:40] | accumulation by **high-quality** institutions: he tracks the ~10 best-performing funds and wants 1–3 of them adding | ❌ No 13F history here |
| F9 | **M** market [0:22], [0:42] | market in an uptrend; "3 out of 4 stocks follow the general market" | ✅ Tested repeatedly (see claims) |
| F10 | Group type [0:33]-[0:35], [1:56]-[1:58] | "3 of 4 leaders come from traditional growth groups (tech, biotech, specialty retail), 1 of 4 cyclical/commodity"; trade cyclicals only in a sector-wide surge | Descriptive; no rule |

### C. Technical / personality filters

| # | Filter | As stated | Codable form |
|---|---|---|---|
| T1 | **Tight and orderly** [1:12]-[1:14], [1:24]-[1:28] | 10/20-day ADR **~2–4%** preferred (AMD at 3.5–4% [1:24]; "20-day ADR of 2 to 3%" is his ideal [1:24]); avoids **≥ 6%** ADR ("a 10 or 20 day ADR percentage of … 6% or more" — O'Neil "never one time" bought one [1:12]); crypto name with ADR "more than double" = avoid [1:25] | `ADR20 ≤ 4%` (preferred), veto `ADR20 ≥ 6%` |
| T2 | **Not a "retracer"** [1:28]-[1:29] | alternating outside day / inside day, "barely making progress" | e.g. `share of inside+outside days over 20 sessions ≥ x` ∧ `|20d return| small`. **x not stated** |
| T3 | Liquidity [1:41]-[1:42] | can sell the whole position at market without moving the stock; 30–70 cents of slippage acceptable | position size ≤ a small fraction of ADDV. **No number given** |
| T4 | Watch-list removal [0:48] | **2–3 closes under the 21-day** and a weakening group → off the list | `close < EMA21 for ≥ 2 of the last 3 sessions` |
| T5 | Group confirmation [0:45]-[0:47], [0:51]-[0:52], [1:23] | other high-RS, high-quality names in the same group are also setting up; group in **early-stage bases**, not late (memory names "later stage … more failure-prone" [0:55]) | peer share at/near highs in the industry. Stage = base count, **not defined** |
| T6 | Base rules (O'Neil) [1:14]-[1:22] | **double bottom:** 2nd low **undercuts** the 1st, pivot = the middle high of the W; **cup / double bottom ≥ 6–7 weeks**, **flat base ≥ 5 weeks**, narrower is better; buy **within 15% of the high** on the right side [1:33], [1:40] (up to 20–25% after a big correction) | Codable geometry. ⚠ He then says improper bases work too [1:15]-[1:16] and "I don't even care if you can name the base" [1:23] |
| T7 | Stop [1:17]-[1:19] | **max 7–8%** from entry, **usually 3–5%**; the 7% figure only applies to 1st–2nd stage bases | percent stop |
| T8 | "Stan Slim" early entry [1:34]-[1:41] | Weinstein stage-1→2 **"consolidation pivots" in the lower half of the base**, "sometimes 70%, 60%, 50% off the high"; best when a **group's MAs converge in a tight bunch beneath price** together after a follow-through day | Entry rule, covered in session 2. MA convergence ≈ `(max(EMA10,21,50) − min(…)) / close ≤ y` ∧ `close > all`. **y not stated** |
| T9 | Host's tip [0:59] | after a market low, a **1-month RS** column = the best performers since the bottom | `RS over the window since the index low`, sort desc |

**Not in this video:** the "RS line at a new high before price" rule. It is a common IBD rule, but neither
speaker states it. RS appears here only as a **rating used to sort**.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 0:00, 0:42 | Market direction is "at least half the ball game"; sit on your hands unless the market is trending up | **Timing can't be done here, though the direction claim is fine.** FTD as a regime switch: **NULL** (eff. n 16–37). QQQ 10/20 index filter on 55k breakouts: **NULL** (RED −0.86pp, t −1.68, halves flip); SPY < 200 breakouts slightly *better*. Breakout pool: **47% of months positive, top 8 of 83 months = 68% of positive R**, and nothing tested forecasts them (`breakout_regime_and_stop_distance_2026-09-17.md`). "3 of 4 stocks follow the market" is beta, not a lever |
| 0:17, 0:44 | "Picking stocks is the easy part … managing risk is all that matters"; "we all wound up with the same stupid list" | ❌ **Backwards on our data** (same finding as the Brandt row, §9). The precision-tier pass is **SELECTION** (vs xname +0.438R, t 3.52, p 0.0015), not timing. Management adds nothing measurable: trims −0.26/−0.33R, the O'Neil pyramid is NULL, profit-locks cost. Exclusion is the size lever (+0.29R OOS) |
| 0:13, 0:24–0:26 | C: quarterly EPS YoY ≥ 25% for ≥ 3 quarters; triple digits and **acceleration** are best | **Untested: no ledger row touches EPS growth.** Nearest: PEAD on the actual surprise **NULL** (12,232 events; `corr(surprise, reaction)` 0.203, "the market prices surprise about right"). The earnings good+MUTED near-miss is a *tape* signal, not a fundamental one (t 2.65; vs xname t 3.17 after the harness re-score; candidate, not adopted). Growth *level* and *acceleration* are a different variable from surprise. **Testable now; see below** |
| 0:28–0:30 | Sales must confirm EPS, **unless** sales are big and steady with no earnings (biotech/R&D) | **Untestable on current data** (no revenue history). The exception means the rule can always be waived, so as stated it can't be falsified |
| 0:25, 1:54 | Big forward estimates matter (analysts are conservative); estimates matter more now than they used to | **Untestable** (no estimate or revision history). Relatedly, the surprise-based PEAD is NULL: beating the consensus isn't an edge by itself here |
| 0:15, 0:39, 1:53 | S doesn't matter any more; the biggest, most liquid names now move like growth stocks | **Half supported, and era-bound.** In the TT ablation, c10 (ADDV ≥ $200M) is the **largest** single contributor (−0.259pp, t −1.46) but costs 60% of the universe. HYB-B, which **lowers** the floor to $100M, beats TT. Within-date, dollar-volume-descending is the **one** breakout sort that clears Šidák (top-2, +0.089R, t 3.48), but **all of it is 2025–26**; 6 of 8 years are weak or negative (`breakout_within_date_rank_2026-09-22.md`). So "most liquid wins" is a recent regime here, not a constant |
| 0:20–0:21, 0:43, 0:58 | Sort everything by 12-month RS (IBD weighting); 6/3/1-month are personal preference | **Same variable as our TT c9, and UNDERPOWERED.** Leave-one-out: dropping RS ≥ 70 costs **−0.090pp** of 20d ADR-matched excess, **t −0.95**, halves −0.03/−0.14 (`trend_template_ablation_2026-09-22.md`). Directionally it adds, but it can't be resolved on about 85 dates. And the whole TT, RS included, is the **weakest** of five universes (+0.56, t 1.30). ⚠ He uses RS as a *sort*, not a threshold. A within-date RS rank has not been run; the within-date study's 9 features did not include RS |
| 0:21, 0:40 | Accumulation by the ~10 best-performing funds | **Untestable** (no 13F history). Proprietary as he does it |
| 0:45–0:47, 0:51, 1:23 | Group confirmation: other high-RS names in the group setting up; prefer groups in early-stage bases | **NULL, leaning the other way at longer horizons.** Same-day theme co-breakouts [WL-5h]: CONFIRMED − LONE **+1.61pp, t 1.80**, 2020-driven; **at 63d it tips to lone names** (−0.57). Leading-group filtering: **INVERTED** (bottom-3 sectors beat top-3, t 2.6). "Early vs late stage group" is untested (no stage definition) |
| 1:08–1:09 | "Ry 62.5%": leaders outperform the market on 62.5% of days during a correction, so screen for names already doing that | ❌ **The nearest test is INVERTED.** Down-day RS as a selection filter (`downday_rs_selection_2026-09-23.md`): names flat-or-green on QQQ ≤ −1.5% days, near the 52wk high, more than once, earn **+3.99% vs +7.50%** for matched near-high breakouts = **−3.51pp at 63d, t −3.33**, both halves negative, monotone dose-response. ⚠ The operationalisation differs: his is the share of *all* correction days beating the market, ours is a count of hold-ups on sharp down days. It's a sibling, not the same test. The 62.5% figure is an unpublished vendor study |
| 0:59 | (Host) 1-month RS after a market low = the new leaders | **UNDERPOWERED.** FTD → single names: eff. n **8 episodes**; post-FTD *controls* beat the field (+0.05–0.08R) while the post-FTD breakout entry **lost**. The state-not-moment version is queued (§10 "Stocks that hold up in a weak tape") |
| 1:12–1:14, 1:24–1:28 | Prefer tight, orderly names with 10/20d ADR ~2–4%; avoid ≥ 6%; O'Neil never held a wide-and-loose stock | **Contradicted for our book; his reason is capacity and temperament.** The TT's median ADR is **2.83%**, and it is the weakest universe even ADR-matched. The best arm, **HYB-B**, *requires* **ADR ≥ 4** and still leads after ADR matching (+1.79, t 2.60, PARKED). The in-book precision tier is **ADR 4–7**. O'Neil holding $500M positions [1:14] is a capacity constraint, not evidence that low ADR earns more. The behavioural half ("if you can't hold it, it doesn't matter") is fair, and our answer is size, not selection |
| 1:28–1:29 | Avoid "retracer" stocks (alternating inside/outside days, slow progress) | **Untested.** Low prior: candle-shape gates have measured nothing here (`prev_green` NULL and removed; close_strength NULL) |
| 1:14–1:16, 1:21–1:23 | Double bottom must undercut the first low; pivot = the middle high; cup ≥ 6–7 wk, flat ≥ 5 wk, tighter is better. **But** improper bases work too and the name of the base doesn't matter | **Self-undermining, and base geometry has tested badly here.** VCP (damped-sine) **NULL**; Kell Wedge Pop **NULL** (−0.38pp vs same-date breakouts); RMV tightness **NULL**, with tight breakouts holding the level *less* (12.3% vs 14.0%, t −2.83); HTF **UNDERPOWERED** (n = 1). Double-bottom undercut and base length specifically: untested |
| 1:17–1:19 | "7, 8, 9 out of 10" CAN SLIM early-stage breakouts never fall more than 7% from the pivot; so the stop is 7–8% max, 3–5% usual | **Not tested as stated, and our nearest number is a different quantity.** **76.4%** of house breakouts return to the breakout level (−0.374R) and 23.6% never do (+1.273R) (`retrace_entry_2026-09-20.md`). Returning to the pivot ≠ falling 7% below it, so this neither confirms nor refutes. It's a cheap descriptive count (below). ⚠ Judge stop changes in **percent**, not R |
| 1:20–1:21 | A cup that goes "straight up off the bottom" usually retests after breaking out ("I have not done a study") | ✅ **Consistent, and more general than he says.** Most breakouts retest (76.4%), and **the split can't be called at entry**: the best single gate (distance to the 21 EMA) recovers +0.057R of a 1.647R spread, and extension is the best *classifier* but the worst *gate* (`breakout_hold_predictors_2026-09-20.md`). Waiting for the retest (retrace entry) is **PARKED at t 0.48** |
| 1:33–1:41 | O'Neil buys within 15% of the high; Haber buys earlier, "sometimes 70, 60, 50% off the high", at Weinstein consolidation pivots | **Nothing here supports buying deep in the base; entry is session 2's topic.** TT c8 (within 25% of the high) *adds* directionally (−0.082pp, t −1.39). Crash-leader study: buying deep drawdowns is a **regime bet**, and in a healthy tape it's a **veto**. In the down-day RS test, near-high breakouts earned **+7.50%** at 63d. His version adds a fundamental filter we haven't tested, so not a refutation |
| 1:40–1:41 | A group's MAs converging in a tight bunch beneath price, together, means the group is "off to the races" | **Partly covered, not supported.** ADX(14) ≤ 12 before a breakout: exploratory +1.48pp (t 2.87) → **holdout NOT CONFIRMED** (t 1.49). `sma_stacked` **INVERTS** as a hold-the-level predictor. Group-level simultaneity untested (theme co-breakouts, the nearest, NULL) |
| 1:37–1:39 | You can be right a third of the time and still make a fortune if losses are small | ✅ **Matches the shape, not the promise.** Precision tier: 30% win, median −1.08R, honest +0.4R. But the fortune lives in a tail cohort (+1.27R, 23.6%) that **can't be identified at entry**, and month-weighted the base book is ~0 (−0.007R) |
| 1:38 | When the laggard in a moving group sits on its MA, put on 10–20% with a 1–2% stop | **Stop too tight by our rule.** On a 3–4% ADR name, a 1–2% stop is **~0.25–0.65 ADR**. Our rule: tight stops under ~0.5 ADR get widened and the size cut, and are **judged on the close** (DINO 2026-09-22: stopped at the post-entry low, closed back above 9 minutes later). Size ≠ conviction here |
| 0:33–0:35, 1:56–1:58 | 3 of 4 leaders are traditional growth, 1 of 4 cyclical; trade cyclicals only in a sector-wide surge | **Descriptive, untested.** Rotation study: can't front-run sector moves; weak-sector breakouts +5.60pp (t 2.61) |
| 1:32 | Fund reached ~$660M "with margin" | Unaudited; no returns, no dates, no drawdown |

## What I would take

1. ⭐ **The one genuinely new axis: fundamentals.** Every universe and selection test in this ledger has used
   price and volume. The within-date ranking doc says outright that the panel's features are "exhausted" and
   lists features *not* in the panel as the untested remainder. CAN SLIM's C (quarterly EPS growth ≥ 25%, three
   in a row, accelerating) is codable on `earnings_yf.parquet` today. It's the cleanest selection variable no
   prior test has touched. Spec below and in [setups/haber_canslim_screen.md](../../../setups/haber_canslim_screen.md).
2. **Nothing technical to adopt.** RS12 is already in the universe (TT c9 inside INT). The low-ADR preference,
   group confirmation and "leaders outperform in corrections" are UNDERPOWERED, contradicted or INVERTED here.
3. **Two process points that agree with us:**
   - screens feed a watch list, not an entry (= "we select well, we enter badly": the universe carries the return);
   - drop names after 2–3 closes under the 21-day (= the house 20-EMA close exit, applied to the list).
4. **A clean statement of the retest problem** [1:20] from someone who says he never measured it. We did:
   76.4% retest, and it can't be called at entry.

## Not tested, could be

### 1. ⭐ CAN SLIM "C" as a universe criterion (recommended, EPS-only first)

**Question:** do names whose last three reported quarters each grew EPS ≥ 25% YoY earn more over the next
20 sessions than same-date, same-ADR names that don't? And does adding it to the production universe (INT)
improve INT?

**Why it isn't already answered:**
- The universe test and TT ablation only vary **price/volume** criteria.
- PEAD tested the **surprise** (actual vs consensus), not growth **level** or **acceleration**. A +40% YoY grower
  can print an in-line quarter, so the two variables differ.
- Down-day RS / leading groups / RS12 are all price-based.

**Pre-registration (draft):**
- **Panel:** `liquid_panel_2009.parquet`, 2010-01 → 2026-09 (≈ 200 non-overlapping 20d dates vs ≈ 80 in the
  universe test). EPS from `earnings_yf.parquet`, membership **as of the prior close**, updated only on the
  report `session` (AMC → next session).
- **C_state(name, date):** the last 3 reported quarters each have `eps_act / eps_act[t−4] − 1 ≥ 0.25` with
  `eps_act[t−4] > 0`. Negative bases → not a member (his loss-shrink "+67%" has no defined rate).
- **Primary cell, named in advance:** **INT ∧ C vs INT**, paired per date. For each non-overlapping date, take
  the mean 20d forward return of INT∧C members minus that of INT members, ADR-decile matched (the TT-ablation
  method run as add-one).
- **Secondary:**
  - (a) C alone vs the eligible panel, ADR-matched (the universe-test Q1 frame);
  - (b) **acceleration**: C ∧ growth rising for 2 consecutive quarters;
  - (c) **triple digit**: YoY ≥ 100% last quarter;
  - (d) 63d horizon (fundamentals are slow, and the down-day RS effect only showed at 63d).
- **Confound control:** the PEAD drift window. Re-run the primary excluding member-days within 10 sessions after
  a report, so a "recent beat" can't pose as "growth". Name what the control varies: it holds the date and ADR
  fixed and varies the name. That makes it a **selection** test, like the universe test.
- **Bar:** paired t ≥ 3 + both halves + per-year sign table; Šidák over 5 cells (|t| ≥ 2.57) governs the
  secondaries, with the |t| ≥ 3 floor on the primary. Report in pp of 20d excess, not R.
- **Caveats to pre-declare:**
  - survivorship (today's liquid names);
  - yfinance `eps_act` is consensus-basis (usually adjusted), matching what screens use but not GAAP;
  - coverage is 1,303 of about 1,728 panel names;
  - the INT ∧ C basket may be thin in weak tapes (count first: C fires on 8.8% of report events 2019+).
- **Effort:** ~½ day (data cached; reuse the `run_trend_template_ablation.py` paired frame). Local, minutes of
  CPU. **Prior: low-moderate.** Every single-criterion effect in the TT ablation was ≤ 0.26pp and unresolvable,
  and the surprise is priced. But this is the only selection axis the ledger has never touched.
- **Sales-confirmation arm (F2/F3):** +~1 day to pull quarterly revenue from SEC EDGAR companyfacts
  (point-in-time by filing date). Run only if the EPS arm clears or nearly clears.

### 2. Cheap descriptive: the "7 of 10 never fall 7%" count (~1 h)

For house breakouts (and the INT ∧ C subset if #1 runs): the share whose lowest low within 20/60 sessions stays
above 0.93 × the breakout level. Descriptive only; it makes his stated stop width checkable. It isn't a strategy.

### 3. Already answered or not worth running

- **RS12 sort:** = TT c9 (UNDERPOWERED). A within-date RS rank of breakout candidates would be the only new
  cut, and the within-date study's null on 9 features makes the prior poor.
- **"Ry 62.5%" screen:** a sibling of down-day RS (**INVERTED**). A share-of-days version is codable in ~2 h,
  but not recommended unless Gabe wants the operationalisation gap closed.
- **Low-ADR (≤ 4%) preference inside INT:** ~1 h from the universe-test masks (INT ∧ ADR ≤ 4 vs INT ∧ ADR > 4,
  ADR-matched). Mostly answered: HYB-B (ADR ≥ 4) is the best arm, and the TT (median ADR 2.83) is the weakest.
- **Up on Volume** as a watch-list feeder: fold it into the queued §10 **"Catalyst as a SELECTION filter"** row
  as a lower-threshold arm (e.g. up day ∧ volume ≥ 1.5× avg50 in the last 20 sessions). Not its own test, and
  his threshold isn't stated.
- **Base stage count, double-bottom undercut, "Stan Slim" deep-base entry:** ambiguous definitions (stage
  counting especially), base geometry has gone 0-for-4 here, and deep-drawdown buying is a veto in healthy
  tapes. **Not recommended.** Revisit after session 2 (entries), if that video defines consolidation pivots.
- **Estimates, revisions, institutional quality, N:** untestable (no history).

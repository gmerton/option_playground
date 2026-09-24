# OptionsPlay — "How to Spot Leading Stocks Before It's Obvious" (Tony Zhang, 2026-04-20, 42 min)

_Reviewed 2026-09-24. A Monday-morning market session. The first 7 minutes are macro (the Strait of Hormuz, earnings
growth, forward P/E). Then comes the **first public preview of the "Flow Leaderboard"**, which replaces their manually
curated equity-research watch list with an automated three-tier relative-strength scan. The Early Breakout Detector
reviewed in [2H1z0vauisg](../2026-07-11_2H1z0vauisg/notes.md) is the bottom tier of this board. Transcript in this folder._

⚠ **This is vendor content**, and a product launch: "an early preview of what we will be publishing going forward"
[37:25], with a sign-up link in the description. No performance figure of any kind is claimed. There is no backtest
of the board. So there is no record to audit, only a definition to pin down.

## Verdict: 2 / 5

- **It is the most mechanical disclosure OptionsPlay has made about its equity scan.** The three tiers are defined by
  how many of three relative-strength time frames a name leads the S&P 500 on [15:39–16:20, 18:23–19:44]. A "theme"
  needs several names from one group [15:39]. That is enough to spec a test, which the detector video was not.
- **Every testable piece lands on a result we already have, and none of them in its favour.**
  - "Fish inside the leading theme" is the orthodoxy the rotation study **INVERTED**: bottom-3-sector breakouts beat top-3
    by +5.60pp at 63d on the same date (t 2.61).
  - Group confirmation is **NULL** (+1.61pp, t 1.80, 2020-driven).
  - Relative strength as a stock-level selection lever has failed five different ways.
- **The market-regime score gets a discretionary override on air.** It reads 5/5, "strong risk-on" [09:35], and the
  desk rating is moved green → yellow anyway on the weekend's news [39:28].
- **One claim agrees with us, and it is the useful one.** Don't buy a leader on the day its move is extended; wait for
  a pause [25:51–28:34]. That is the entry-extension finding in his words. But our attempts to *trade* the wait
  (retrace entry, breadth deferral) have not cleared the bar.
- **The genuinely open idea is the exit.** "Get out when the name or theme drops off the leaderboard" [21:05–22:26].
  No RS-based exit has ever been tested here (spec below).

## What the Flow Leaderboard computes: everything the transcript pins down

| @ | statement | implication |
|---|---|---|
| 15:39–16:20 | "we're scanning across three different time frames and only stocks that ... have leadership across all three ... are our confirmed leaders. If ... two of them, then we consider them building. ... just showing up in the short-term time frames ... that's when we consider them early breakout" | **Tier = the number of RS horizons (short / medium / long) on which the name outperforms the S&P 500.** 3 = confirmed, 2 = building, short-only = early. **The three horizons are not disclosed** |
| 18:23–19:44 | "these are not just stocks that are breaking out, but they're outperforming the market ... potentially some institutional accumulation" | an absolute breakout **plus** RS > 0 vs SPY. The breakout definition is not given. "Accumulation" is an interpretation, not a measurement |
| 19:04 (garbled) | building = "short and long-term, but have not shown up in the long time frame" | a slip of the tongue. Read it as short + medium |
| 15:39 | "it's not a particular theme until you have multiple names enter that specific theme"; 16 names in semis/AI = "a clear confirmed theme" | theme = at least k names in one group on the board, with k unstated ("multiple"). Travel entered with 4–5 names |
| 08:13–09:35 | **Market regime** = a count across five categories: additions to the board, upgrades to confirmed, theme breadth, downgrades. "5 out of 5 categories ... strong risk-on" | a breadth-of-leadership index. The scoring rule is not given |
| 29:54–36:03 | tiers move week to week: added / upgraded / dropped ("zero names have been downgraded this particular week") | the tier *transitions*, not the levels, are what he says to act on |
| 37:25 | a separate "directional edge indicator" = 1-month and 6-month trend plus the RS indicator, shown beside the earnings calendar | a different product. Undisclosed weights |
| description | "48 stocks and 17 ETFs actively leading" | the size of the board: 65 names |

**In our vocabulary:** a multi-horizon version of the Trend Template's RS criterion (TT c9 is a single weighted
12-month RS), stratified by how many horizons agree. The "early" tier is the stock-level **early-turn** rule (short-horizon RS positive while the longer ones are not). We tested that at the sector level: 21d RS crosses above 0 while 63d RS < 0 gave +0.28pp at 21d (t 2.55), −0.15 at 63d, and was
era-inconsistent (`industry_rotation_detection_study.md` §3a).

## Data audit

| claim | stated source | denominator | checkable? |
|---|---|---|---|
| "at least 50% of the themes" that enter early never reach confirmed [20:24–21:05] | none | none | no. It is also *uninformative* as stated: a 50% promotion rate says nothing about returns |
| 5/5 = "strong risk-on" [09:35] | their own model | one reading | no scoring rule, no history. Overridden on air [39:28] |
| earnings: "14 to 15% EPS growth ... as high as 18 to 19%" [05:30]; S&P "22 → 20 times forward" [06:11] | not stated | — | macro commentary, not a trading claim. Not audited |
| the example names (MRVL, VIK, IUSG, DLR, BNS, IWM, HOOD/IBIT, XYZ, EXPE) | the board as of the prior Friday | 65 names | a forward list. Its outcomes after 2026-04-20 are knowable but would be one draw, anecdote either way. Not scored |

## Claims against our ledger

| @ | claim | our evidence |
|---|---|---|
| 15:39–19:44 | **Confirmed leaders (RS on all three horizons) are "the most durable signal ... the highest confidence"** | ❌ **The RS-as-selection family has failed every way we have cut it.** TT c9 RS ≥ 70: −0.090, t −0.95, UNDERPOWERED (`trend_template_ablation_2026-09-22.md`). The Trend Template is the **weakest** of five universes (+0.56pp ADR-matched, t 1.30; `universe_test_2026-09-21.md`). Down-day RS is **INVERTED** (−3.51pp at 63d, t −3.33; `downday_rs_selection_2026-09-23.md`). Names holding up in a weak tape: NULL leaning INVERTED (−0.69pp, t −1.50; `weak_tape_leaders_2026-09-24.md`). Within 15% of the 52wk high: NULL (t 0.14, gate ablation). Sector 12-1 momentum spread: NULL (−0.17%/mo, t −0.75). **The multi-horizon *agreement* count itself has not been tested at the stock level.** That is the one new cut (spec below), at a low prior |
| 14:59–16:20, 22:26 | **Hunt inside themes with several leading names; "multiple names" makes a theme** | ❌ **INVERTED at the sector level, NULL at the industry level.** Volume-confirmed breakouts in the **bottom-3** sectors beat the top-3 by **+5.60pp at 63d on the same date (t 2.61)**. Net of their own sector ETF the gap is still +6.13pp, so it is stock-level (`industry_rotation_detection_study.md` §12–13). Same-day industry co-breakouts vs lone breakouts: **+1.61pp, t 1.80**, 2020-driven, and it tips toward lone names at 63d (`theme_cobreakout_2026-09-23.md`). "The industry RS ranking is descriptive, not predictive" (rotation study §3a) |
| 08:13–09:35, 36:03 | **Regime = breadth of leadership** (additions, upgrades, no downgrades → risk-on) | ⚠ **The nearest test is PARKED, and its raw-count form is flat.** The 5-session breakout count *as a percentile of its own trailing year* sorts the book (top − bottom +0.81R, t 2.59, both halves). But **raw counts are flat-to-INVERTED** (cnt20 −0.30), it has no plateau, and it fails the ledger correction (Šidák p 0.065) (TEST_INDEX §4, breakout-activity row). His score counts raw additions and upgrades. The QQQ 10/20 index filter: NULL (t −1.68, halves flip; `index_filter_2026-09-23.md`) |
| 39:28–40:08 | Desk rating moved from green to yellow on weekend news, despite the 5/5 model | a discretionary override of the model it was introduced to replace. Any record of the board is also a record of his overrides |
| 25:51–28:34 | **A leader with a "countertrend bearish signal" is too extended: don't buy today, wait for a pause.** "A lot of times chasing momentum ... we're buying high" | ✅ **Right diagnosis.** It is the entry-extension finding: the breakout entry sits **+0.52 ADR above the prior 20d high vs −2.09 ADR** for a random later entry in the same name, 2.6 ADR of price paid, and the stop is not the cause (`entry_vs_stop_2026-09-20.md`). ⚠ **But waiting has not been made to pay.** Deferring to a retrace beats the breakout in 6 of 6 cells at **t 0.48 → PARKED** (`retrace_entry_2026-09-20.md`). Deferring on hot breadth costs (A − B +3.03pp, t 1.24), and the names that never came back made +24.6% (Flanders deferral, TEST_INDEX §4). The trap is that the pullback you wait for does not come on the best names |
| 27:53, 39:28 | The board is a **watch list, not buy signals**; buy only when the platform issues a buy signal | the same structure as ours: rank, then trigger. Our finding is that the trigger adds ≈ 0 over the selection (universe test: edge vs the same name on a later day ≈ 0 in every universe). The buy signal itself is proprietary and untestable |
| 21:05–22:26 | **Exit plan: when the name or its theme drops off the leaderboard, reconsider or get out.** Banks (C, MS, JPM) dropped a week after strong earnings | **UNTESTED. The one new axis in either video** (spec below). Our exits are all price-based: 20-EMA trail, day-low stop, profit-locks. No exit keyed to losing relative strength has been run. Prior: weak to moderate. The rotation study says RS *describes* what has led, so losing RS may just restate the price fall the 20-EMA trail already catches |
| 20:24–21:05 | "At least 50%" of early themes never confirm | no source. The nearest number we have: the 2026-06-10 sector breadth thrust was a draw from a distribution centred on zero, **50.9% win at 21d over 224 events** (rotation study §3b) |
| 22:26–23:06 | Alt asset managers (KKR, BX, APO): relative strength faded, "aligns with our broader fundamental research" | a fundamental view confirmed by RS. That is two claims in one, and neither is testable here |

## What I would take

1. **The definition, for the record.** OptionsPlay's equity board = an absolute breakout that also beats the S&P on
   short / medium / long RS, tiered by how many horizons agree, with themes counted at k names per group. It is the
   first time they have said this much.
2. **Nothing to adopt.** The selection half duplicates levers we have tested and found empty or inverted. The
   regime half is a raw-count breadth score, which is the form of our activity gate that does *not* sort. Their
   own desk overrides it anyway.
3. **His "don't buy the extended day" is the right instinct**, and it is our biggest measured leak. It does not
   change anything, because we have no tradeable rule for the wait yet.

## Not tested, could be

### ⭐ RS-loss exit: sell when the name stops leading, vs the 20-EMA trail (pre-registerable)

**Why this one.** It is the only claim in either OptionsPlay equity video that the ledger has not touched. Our exit
research is all price-level (the profit-lock study, the Qullamaggie partial INVERTED, spike-vs-grind NULL). This asks
whether *relative* weakness exits earlier than *absolute* weakness on the trades where it matters. The prior is low to
moderate: a name that loses RS vs SPY while the tape rises may still be above its 20 EMA, and that is the case where
the two exits disagree.

- **Pool:** the in-book precision-tier trades (`breakout_activity_gate_2026-09-22.csv`, n ≈ 1,996). As a secondary,
  the house breakout on `liquid_panel_2019` (`run_vcp_damped_sine.house_breakout`), close entry.
- **RS state:** `rs_h = (C_t / C_{t−h}) / (SPY_t / SPY_{t−h}) − 1` for h ∈ {21, 63, 126}, **fixed before the run**.
  The name is "leading" at horizon h if rs_h > 0. Tier = the count of leading horizons (0–3).
- **Arms (identical entry, identical day-low stop judged on the close, 60-session cap):**
  - **A**: 20-EMA close trail (house).
  - **B (PRIMARY)**: exit at the first close where the tier drops to ≤ 1, *or* A's exit, whichever comes first.
  - **C**: B's RS condition alone, without the 20-EMA trail.
- **Metric:** **% per trade**, paired A vs B on the same trade, date-clustered t. R is reported second with the 2%
  stop floor and cap 20. Also report the **share of trades where B ≠ A**, and B − A on that subset only. That subset
  is the whole test; the rest are identical by construction.
- **Control:** the pairing itself holds entry, name and date fixed, so only the exit rule varies. As a secondary,
  B vs **A with a random exit on the same session count** as B's exit, to check whether B beats simply *exiting
  earlier*. That is the "clean result is a bug" check: an earlier exit can look good in a sample where winners
  mean-revert.
- **Bar:** |t| ≥ 3 on B − A, both halves (split 2023-01-01) the same sign, and a per-year table (the book lives in
  busy months: pyramid-row METHOD note). Šidák k = 2 for B and C.
- **Confounds to pre-declare:** in a bull sample, SPY's own rise makes RS-loss fire more often late in rallies, so
  also report by the SPY 63d return tercile at entry. Survivorship: the panel is names liquid as of 2026.
- **Effort:** about 2 hours, local. The panel, SPY closes, `pct_trade` and the date-paired t already exist.

### Stock-level three-horizon RS tier as a selection sort (spec only, low prior; do not queue ahead of the exit)

- **Event:** the first session a name enters tier 3 (confirmed) vs the first session it enters the early tier
  (short-horizon leading, 63d and 126d not). House breakout on that day, or within 5 sessions.
- **Primary:** same-date, ADR-decile-matched 20d excess, confirmed-entry minus early-entry, two-sided. Two-sided
  because his two videos pull opposite ways: this one calls confirmed "most durable", the detector video calls
  early "freshest".
- **Prior:** poor. Five RS-flavoured selection tests have failed (above). The 2H1z0vauisg exploratory check found
  the lowest-RS decile of breakouts the worst cell (−4.00pp at 60d on 6-month RS, overlap-inflated t −3.39), which
  predicts that early-tier entries (low long-horizon RS) lose to confirmed ones. Run it only if the RS-loss exit
  shows the RS state carries any information.

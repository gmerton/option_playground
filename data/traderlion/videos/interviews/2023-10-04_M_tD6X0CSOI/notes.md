# TraderLion -- "The Perfect VCP Trading Setup with Mark Minervini" (2023-10-04, 38 min)

_Reviewed 2026-09-23. Richard Moglen hosts Mark Minervini for a correction-era presentation: breadth divergence,
"leaders lead the cycle", progressive exposure, six winners-only case studies (AMGN 1990, FICO, PTON, CSCO,
DOCU, CMG), then a five-point "finding leaders" checklist. Transcript is `en-orig` auto-captions, in this folder._

WARNING: **The title oversells what's in the video.** The word "VCP" is spoken **once** ([00:13] in the teaser,
which repeats the CMG segment at ~[29:14]; that exact line falls in a 7-second caption gap at [29:13]-[29:20]):
*"it really matures, it tightens up, it meets my signature VCP ... look at the RS line going into the high ground,
this is where I bought it."* The description's "29:18 VCP Buy Point - Key point" is that one sentence. **He never
gives a contraction count, a depth schedule, a volume rule, a pivot definition or a stop rule.** The codable spec
below uses his words where they exist. Every other parameter is flagged as coming from his book or the 2026-07-29
MPA panel, or as a house default. It is not presented as something this video said.

## Verdict: 2 / 5

- **The process is coherent, and some of it agrees with our data:**
  - he lets the stocks lead and doesn't work from the group down ([18:24]; our rotation study inverted
    top-down group filtering);
  - he raises cash only when *his own* holdings deteriorate ([08:18]);
  - he tells beginners to sell a piece at 2-3x risk ([12:45]).
- **The evidence is zero:**
  - six case studies, all winners, all bought by him;
  - one US Investing Championship reference;
  - "tens of millions" with no denominator ([00:56]).
- **The one testable selection claim has already been tested here and is NULL or UNDERPOWERED:** buy the
  first names to new highs off an O'Neil follow-through day (FTD) in a correction.
- **The VCP itself, the thing the title sells, is only named.** He never defines it.
- The score is 0.5 below the 2026-07-29 MPA panel (2.5/5) because this video has *less* mechanism. It's a
  funnel for the Master Trader Program ([13:00], [19:21], [36:59]).

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 03:37-05:30 | A divergence between the index and the % of stocks above the 200-day SMA, especially in the 30s at new index highs, has "never" survived without a correction "in my 40 years" | **Untested as stated, and there's a close relative.** The Aug-2026 retro: weak breadth = a mild BUY, but **every trailing-30d breadth rule failed 2019-26**. The T2108 breadth-extreme gate (Bonde) is still **QUEUED, NOT RUN** (TEST_INDEX §10 "T2108 / breadth-extreme gate"). "Never in 40 years" is an n of a handful of tops, with no false-positive count |
| 08:18 | Don't raise cash because the index rolls over. Raise it when *your* holdings and watchlist deteriorate | **Consistent, not tested directly.** Our regime work says the paying months can't be forecast by index state (FTD NULL, breakout-regime feedback). The regime lives in the **names** (Stage A x market feedback: swing-trail autocorr 0.53 by month while the alert edge ~0). "Watch your names, not the index" is the same conclusion |
| 09:16, 16:18 | O'Neil rule: after a follow-through day, buy stocks coming out of bases with "nice tight right sides"; don't be scared off by "bear market rally" talk | **NULL / UNDERPOWERED.** FTD as a regime switch (SPY 1993-2026, 4 cells): **NULL**, no edge vs other correction days at +5/+10/+21d, IWM negative 10 of 12 cells. FTD -> single names: **UNDERPOWERED** (effective n 8 episodes), and post-FTD **breakouts were WORSE** (5d -0.196R vs -0.072R) while the post-FTD *controls* were better (+0.045-0.080R) -> **"the names are better, the breakout entry is the wrong way in."** That points straight at an entry-location question, which is VCP's claim |
| 12:01-12:57 | Profit-taking in R multiples: a beginner sells a portion at 2-3x risk (a 5-8% risk -> +12-20%) to "free-roll" the trade. The expert sells when "the downside outweighs the upside" | **Beginner rule tested and it COSTS; expert rule untestable.** Profit-lock exits: BE after +2R harmless, **BE +1R / lock / trims all cost**, and "extended -> tighten" **INVERTED**. OptionsPlay row: trims **-0.25...-0.33R**. "Downside outweighs upside" is discretion by definition |
| 13:56-14:50 | "Leaders lead the cycle": three watch phases in a correction, *predictive* (holding up while the market falls), *off the lows* (first to new highs after the FTD), *confirming* (broadening) | **Phase 1 is QUEUED here, not run.** TEST_INDEX §10 "Stocks that hold up in a weak tape" (queued 2026-09-20): names within ~10% of the 52wk high while < 35% of the universe is above its 50 SMA, **entry at the close / pullback, NOT the breakout**. ⚠ Adjacent result: down-day RS as a name-level SELECTION filter is **INVERTED at 63d (-3.51pp, t -3.33, monotone dose-response)**. "Held up on down days" picked *worse* breakouts than undosed near-high names. Minervini's phase 1 is a close cousin and the prior is now negative |
| 18:24 | "Let the stocks lead you to the group": he lost money for six years going top-down, then flipped to bottom-up | ✅ **Agrees.** Industry rotation detection: **FAIL to front-run**. Leading-group filtering **INVERTED** (bottom-3 sectors beat top-3, t 2.6). Same verdict as the MPA panel's "bottoms up" |
| 20:18-22:10 | Progressive exposure: ~25% on pilot buys; if they work, 50% fast; then 75-100% "within a week or two", concentrated | **Adjacent tests NULL.** O'Neil pyramid (adding to winners): adds earn the same edge as the base and no add condition beats the unconditional add (best +0.15R, t 1.25). "Scale up when the pilots work" is own-P&L feedback. Stage A x market feedback: the next session after a hot alert stretch is **not** better (lag-1 autocorr ~0). ⚠ The **name-level** regime does persist month to month (autocorr 0.53), so a monthly equity-curve rule is untested, not refuted |
| 22:55-23:53 | FICO/PTON: the ones that get to new highs **fastest** off the market low. PTON in 18 days, CSCO and DOCU in 10 | **Untested as a days-to-new-high rank.** Nearest: ranking breakout candidates within a date by 9 features (72 cells, Sidak 3.38) = **NULL**. Only dollar volume cleared, and it collapsed by year. "Speed to new high off the low" wasn't among the 9 features. Five hand-picked winners are not a rate |
| 24:08-25:00 | "The way I get leverage is by being in the leading stocks" (multiples of the market), not margin | **Framing, and partly right.** Our universe test: the **universe carries the return, not the trigger**. ⚠ But our Trend Template universe was the **weakest of 5** (+0.56pp 20d ADR-matched, t 1.3), and TT criteria one by one are all **UNDERPOWERED** (full TT buys +0.575pp). Only HYB-B (TT at $100M ADDV + ADR >= 4) is PARKED at t 2.6 |
| 27:25-28:08 | The RS line making new highs *before* price, even while price goes sideways | **Untested as an RS-line-leads-price rule.** Nearest: the down-day RS selection filter above is **INVERTED**. ⚠ It's measured on down days, not on the RS-line high, so it's a warning and not a refutation. Our Trend Template ablation doesn't test the RS line either |
| 28:08-29:13 | CMG: a stock that hit new highs first can fail a short base, undercut the lows, shake everyone out, and still be the leader. "It doesn't mean you take it off your list" | **Unfalsifiable as stated.** It excuses any failed breakout after the fact. It's worth noting against the bimodal finding: 76.4% of house breakouts return to the level (-0.37R). Minervini's answer is "keep watching and re-buy the next tight base", and that's the VCP test below |
| 29:14 (teaser 00:13) | CMG "tightens up, meets my signature VCP ... this is where I bought it" | **VCP has never been tested here** (TEST_INDEX §10 row, queued 2026-09-22). This video adds nothing definitional. See the spec below |
| 29:55-30:16 | Leader criterion 1: within **25% of a new high** when bought, never down 40-50% ("too much overhead supply") | **Consistent, and our data refines it.** The crash-leader study: buying deep drawdowns is a **regime bet, not selection**, so never in a healthy tape. The rotation study: "**don't require the 52-week high**", because the 3-15%-off-high cohort beats the at-the-high cohort. His 25% cap is looser than both |
| 30:16-30:33 | Criterion 2: base-building, consolidating within a long-term uptrend | = the Trend Template precondition. See the TT ablation above |
| 30:35-30:58 | Criterion 3: the fastest off the lows are often extended, so wait for **"ants"** (David Ryan: >= 12 up days of 15) and a *subsequent* entry point | ⭐ **The most interesting line in the video, because it's an entry-location statement:** don't buy the extended thrust, buy the *next* setup. That's our entry-extension finding in his words: the house breakout pays **+0.52 ADR above the prior 20d high vs -2.09 ADR for a random later entry (2.6 ADR)**, and the control beats the signal. The ants count is untested |
| 31:00-31:55 | Criterion 4: recent IPOs, first IPO base, best bought in a correction ("magnitude plays") | **Untested.** Our panels start 2019 with liquidity gates, so first-base IPOs are mostly excluded by construction. That would need its own universe |
| 00:56, 34:48 | Junior-high dropout, a couple of thousand dollars -> "tens of millions". Six losing years first | **Anecdote.** No CAGR, drawdown or audit. USIC is a small self-selected account (README red flag). The six losing years are honest and worth keeping |

## What I would take

1. **Nothing to adopt from this video.** Its one testable selection claim (FTD + first to new highs) is already
   NULL / UNDERPOWERED here, and its leverage claim ("be in the leaders") is what our universe tests found
   *weakest* for our own Trend Template.
2. **Criterion 3 as a framing** ([30:41]): *the fastest names are extended, so wait for a subsequent entry
   point.* That's his version of our entry-extension finding, and it's the reason VCP is worth testing: VCP is
   an **entry-location** claim, not a selection claim.
3. **Agreements to note, not act on:** bottom-up beats top-down (rotation study), and raise cash on your *names*
   rather than on the index.

## Not tested, could be

- **VCP itself.** It's already QUEUED (TEST_INDEX §10, 2026-09-22). The spec and pre-registration are below.
  ~1 day.
- **"First to new highs off the low" as a rank** (days from the SPY low to a new 52wk high, within the post-low
  cohort). Low prior: within-date ranking was NULL on 9 features, and FTD -> names is UNDERPOWERED at n=8
  episodes. Would need the panel extended pre-2019 to reach any power. **Not queued.**
- **Ants (>= 12 up days of 15) -> wait for the next base.** It folds into the VCP test as an optional
  pre-condition arm (exploratory, not primary).

---

## Codable VCP spec

**Sources, in order of authority:**
- **(V)** this video;
- **(P)** the 2026-07-29 MPA panel ([`2026-07-29_uMJXA_I9HDw`](../2026-07-29_uMJXA_I9HDw/transcript.txt);
  Ritchie/Hedgepath are Minervini's staff);
- **(B)** Minervini's own book definition, *Trade Like a Stock Market Wizard* (2013) ch. 10, which is **not**
  in this repo and should be checked before it's quoted as more than paraphrase;
- **(H)** house default.

⚠ The "25% -> 15% -> 8%" depth schedule and the "2-6 contractions" count are **(B)**. **Neither appears in
this video**, and the task brief's example numbers shouldn't be attributed to him.

All levels are on **daily bars, split-adjusted** (the liquid panel). The spec is scale-free where possible
(ADR-normalised), following the house rule that creator patterns have no fixed timeframe.

| # | Element | Rule (codable) | Source | Discretionary? -> default [sensitivity grid] |
|---|---|---|---|---|
| 0 | Prior uptrend | Trend Template member on the day **before** the base starts (the repo's `lib.minervini.scan` criteria: c3-c9 + liquidity; c1/c2 are redundant per the TT ablation) **and** a >= 30% advance from a low within the 252 sessions before the base high | V [30:19] "consolidating within a long-term uptrend"; B (prior advance >= 30%) | Yes -> TT on; prior advance >= 30% [20, 30, 50] |
| 1 | Base start = left-side high | H0 = the highest high in the 60 sessions before the pivot, which must itself be a 20-session swing high (5-bar fractal on each side) | B; H | Yes -> fractal 5 [3, 5] |
| 2 | Base length | sessions from H0 to the signal: **>= 15 and <= 65** (3-13 weeks) | B ("3 to 65 weeks" in the book; this video says nothing) | **Yes, wide open in the source** -> 15-65 [10-40, 15-65, 25-130] |
| 3 | Depth cap | (H0 - base low) / H0 <= 35%, and the pivot within 25% of the 52wk high | V [30:02] "within 25% of a new high"; B (first correction usually <= 35%) | Yes -> 35% [25, 35, 50] |
| 4 | Contractions | Walk the base H0 -> signal with swing points (5-bar fractals). Contraction k = swing high h_k -> the next swing low l_k; depth d_k = (h_k - l_k)/h_k. Need **N >= 2** contractions with **d_{k+1} <= r x d_k** for every k (monotone shrinking) | P [62:58] "classic one, two, three contractions" (a 5-min IPO-day chart -- timeframe-agnostic); B (2-6 typical, "each roughly half the prior") | **Yes (the central free parameter)** -> N >= 2, r = 0.75 [N 2/3; r 0.5/0.75/0.9] |
| 5 | Final contraction is tight | d_last <= 1.0 x ADR20 **and** <= 10% | V [00:13] "tightens up", [16:34] "nice tight right sides"; P "~5% cited for STX"; B ("the last one often < 10%") | Yes -> 1.0 ADR [0.6, 1.0, 1.5]. Stated in ADR, not percent, per the house scale-free rule |
| 6 | Higher lows | l_{k+1} >= l_k (each swing low above the prior) | B (implied by shrinking depth under a flat top) | Yes -> required [on/off] |
| 7 | Volume dry-up on the right side | mean volume over the last contraction <= 0.7 x mean volume over the first contraction, **and** the minimum-volume day of the base falls in the last 10 sessions | P [05:12] "right before we bought was one of the lowest volume days in that whole base"; B | Yes -> 0.7 [0.5, 0.7, 0.9]; the min-vol-in-last-10 flag [on/off] |
| 8 | Pivot | P* = the high of the final contraction (h_last) | B; P ("buy through the pivot high") | No, it's mechanical once #4 is fixed |
| 9 | Trigger | **CLOSE > P*** with RVOL >= 1.5 (volume / 50d average, same session). ⚠ He buys the intraday break; **the house enters on the CLOSE** (entry study: the close beats every intraday entry, paired -0.9 to -2.3pp, t -1.6 to -3.4) | P ("decisive move out"); H | Yes -> RVOL 1.5 [1.0, 1.5, 1.8]. 1.8 matches the rotation-study gate |
| 10 | Entry must not be extended | (close - P*) / ADR <= 0.5 | H (entry-extension finding); V [30:41] extended = wait | Yes -> 0.5 ADR [0.25, 0.5, 1.0] |
| 11 | Stop | **l_last = the final contraction's low**, judged on the CLOSE. Report stop/ADR for every signal. The house disaster stop (1 ADR below the close, resting intraday) is a separate reported variant | B; P (the tight structural stop); H (stop_definitions.md) | Mechanical. Expect stop/ADR ~1-1.5 given #5, wider than the house day-low stop's median ~0.5 |
| 12 | Market filter (optional arm) | SPY > its 50 SMA, or the FTD state | V [16:18] | Exploratory only, not primary |

Implementation note: `src/lib/commons/vol_compression.py` is **not** a VCP detector. It's a point-in-time
ATR/range-compression screen (ATR% bottom 20% of the year, 5d < 20d < 60d range, optional volume MA). It never
finds swing points, contractions, a pivot or a structural stop, and it pulls from Tradier live, not the panel.
Reuse its range-chain idea as a cheap **pre-filter** at most. The detector has to be written fresh: ~60-80 lines
of swing-point walking on the `DailyPanel` arrays, plus the ~20-line harness pattern.

## Pre-registered pattern_test design (sketch, NOT RUN)

**Question:** does a mechanically defined VCP pivot close earn more than the **house breakout in the same name**,
i.e. is VCP a better *entry location* than a 20d-high close?

- **Universe:** `liquid_panel_2019.parquet` (ADDV >= $50M, px >= $5, suspect-filtered; harness `elig`),
  2019-10 -> 2026-09, pre-conditioned on #0 (TT member). ⚠ Report the HYB-B universe (TT at $100M + ADR >= 4) as
  a secondary cut, because TT alone was the weakest universe.
- **Primary cell (named in advance):** N >= 2, r = 0.75, final contraction <= 1.0 ADR, volume ratio <= 0.7,
  base 15-65, RVOL >= 1.5, extension <= 0.5 ADR. Entry at the **close** (`entry_at="close"`), stop = l_last on
  the close, **`ema20` arm, hold 60**. That's the exit the house precision-tier book uses. The arm and hold are
  fixed in advance; the harness's "best arm by edge" is **not** the primary.
- **Arms:**
  - **A** VCP (primary);
  - **B** the house breakout in the same names (20d-high close + RVOL, the precision-tier definition with no
    VCP conditions), same entry/stop convention (day-low stop);
  - **C** VCP with the house day-low stop instead of l_last. This separates *where you buy* from *how wide you
    stop*: judge C vs A in **percent, not R**, per the stop-width rule;
  - **D** VCP minus the volume condition (#7 off);
  - **E** VCP with N >= 3.
- **Controls (the confound held fixed):**
  1. ⭐ **Same name, house breakout within +/-60 sessions that is NOT a VCP pivot.** This is the comparison that
     matters: same stock, same era, same exit, only the base structure differs. Paired per name, day-clustered.
  2. `post` (a random later session in the same name) for timing.
  3. `xname` (another eligible name on the same date, same stop %) for selection. ⚠ Per CLAUDE.md, `xname`
     measures **name selection, not the pattern**. Don't read an `xname` win as validating VCP.
- **Outcomes:** %-return at 5/21/60d **and** R. The primary statistic is **% return, paired A - control-1**,
  because A and B have different stop widths and R would be distorted by the denominator. Report gross and after
  the house slippage.
- **Bar:** |t| >= 3 on the day-clustered primary, **both halves (split 2023-01-01) the same sign**, **per-year
  table 2020-2026 with no single year carrying it** (the within-date dollar-volume cell collapsed this way).
- **Multiple-testing charge:** the sensitivity grid above is ~3^6 x 2^2 ~ 2,900 cells. It must **not** be
  searched. Register the primary plus the 4 arms (5 tests) at **Sidak |t| >= 2.97 (alpha 0.05 / 5)**, and in any
  case >= 3. Run the grid afterwards with `ledger=False`, only as a **parameter-neighbourhood robustness** check
  (the queued method upgrade): the primary counts only if >= 70% of its immediate neighbours share its sign.
- **Outcome-conditioning checks before believing any positive result:**
  1. the detector must use only bars <= the signal date. Swing points need 5 bars on the right, so a pivot
     "found" at t uses swing lows confirmed by t, never later;
  2. log the share of signals whose base low sits within 1 session of the entry. A contraction completed by the
     breakout bar itself is look-ahead;
  3. a large, monotone, high-t VCP result gets treated as a bug until those two checks pass.
- **What VCP has to show to add anything:**
  1. The house breakout's problem is the **entry**: +0.52 ADR above the prior 20d high vs -2.09 ADR for a
     random later entry, and the book is **bimodal** (23.6% never return = +1.27R; 76.4% return = -0.37R). Nothing
     in the book can call that split at entry (best gate: 21-EMA distance, +0.057R, t ~2).
  2. The close already beats every intraday trigger, so a VCP bought on the intraday pivot break would be
     expected to lose. The only fair test is the close.
  3. **VCP adds something only if, in the same names, (a) A beats control 1 on paired % return at |t| >= 3 with
     both halves the same sign, AND (b) its held-the-level share beats the house breakout's 23.6%.** That's the
     one mechanism by which a better base structure could matter: it would make the +1.27R cohort *callable*. A
     VCP that only matches the breakout, or only beats `xname`, adds nothing. It's the same trade with a
     narrower funnel.
  4. A secondary (not a pass condition): does the l_last stop give a smaller stop/ADR than the day-low stop at
     equal % return? That's the concentration argument in TEST_INDEX §10, and it's a sizing benefit, not an edge.
- **Effort:** ~1 day. Detector ~60-80 lines, harness pattern ~20, control-1 pairing ~40 (the harness has no
  "same-name other-pattern" control, so it needs a thin wrapper over `_daily_arms`), plus the pre-registration
  docstring.

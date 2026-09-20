# Trade grading (A/B/C/D → size) and the daily report card

> **Verdict:** ⭐ **The firsthand source for a system this repo already runs secondhand — and it
> turns out to be TWO systems, not one.** A **per-trade** grade assigned *before* entry whose only
> output is size, and a **per-day** report card assigned after the close whose only output is
> tomorrow's focus. The repo implements both, correctly split across two files; what the repo is
> missing is his *rotating single goal*, his *time-block grading*, his *state→risk dial*, and his
> *easiest-layup* field. What the repo should **not** import is his C-grade feeler trade, his
> "size up on A" (already tested here and only half-confirmed), and his validation loop (no
> control, and it uses your own book as setup evidence).
> **Type:** review-process
> **Conviction:** 3/5 · **Testability:** process/unfalsifiable (two of his rubric variables are
> EOD-testable, see §3) · **Tested?** partial — the *sizing* half is tested and partly refuted
> **Sources:** `vKy6Q9hwon4` — "Copy My Trading Report Card That Made Me $100 Million" (2025-08-08)
> · `ubofAZwgd4w` — "My Trade Grading System that Made Me $100M (A,B,C,D)" (2026-08-15)
> · cadence from `M-rpkVekvOQ` — "The 60-Day Trading Routine" (2026-09-12)
> **Supersedes:** the secondhand paraphrase in
> [`../notes/four-constraints-and-the-ai-trap.md`](../notes/four-constraints-and-the-ai-trap.md)
> ("pre-assign risk levels by trade quality, then grade yourself daily on whether you risked
> accordingly"), which fused the two systems into one and is what
> `run_journal_grades.py` was built from.

---

## 1. Mechanics

### System A — the per-TRADE grade (`ubofAZwgd4w`)

- **When:** before entry, every trade, written into the journal at that moment [10:04] — "not
  after. This helps hold you accountable and avoid hindsight bias."
- **Scale:** A / B / C / D, with plus and minus [01:09]. **Output = position size, nothing else.**

| Grade | Definition (his words) | Size | Repo verdict |
|---|---|---|---|
| **D** | no trade; "literally, 99.9% of charts are D grade or worse" [01:30]; a fold regardless of boredom [01:24] | zero | ✅ **confirmed** — `project_size_lever_study`: the lever is exclusion |
| **C** | "small capital or a feeler trade… paying a small fee to stay engaged" [01:52]; must be "at least marginally break even EV or better" | a fraction | ⛔ **reject** — see §8 |
| **B** | "bread and butter… boring is good. Boring pays the bills" [02:22]; should be most trades | standard | ✅ confirmed (A+B only was the winning cut) |
| **A** | "everything lines up. The chart, the catalyst, the market, the tape" [02:41]; best of the day/month | size up | ⚠ **not supported** — a 10× risk spread returned +0.08R with more drawdown vs +0.29R for plain exclusion |

- **The grade is a weighted scorecard, not a pattern match** [04:04]: grading a trade is like a
  teacher grading an essay — several categories, each scored, total sets the grade; "a paper can
  have beautiful writing and a garbage argument and land a C." Independently the same conclusion as
  `feedback_breakout_scorecard` (value + threshold + tier per gate).
- ⭐ **One rubric per setup** [05:15]: "you cannot grade a capitulation trade with a breakout
  rubric." The variables are "almost the opposite."
- **He disclaims objectivity outright** [03:24]: "it's all subjective, completely subjective. My A
  is not your A trade… The point is not to copy my rubric. The point is to have a rubric."

**His two sample rubrics** (4–6 variables each is his stated target [09:52]):

| # | Capitulation [05:36–07:48] | Breakout [07:59–09:42] |
|---|---|---|
| 1 | **rate of change** — a 3% grind down "is just a down day"; wants the waterfall | **consolidation quality** — long/tight/clean high, short/loose/messy low |
| 2 | ⭐ **how boring the stock is** — low-beta sleepy name dropping 15% is an overreaction; a momentum name doing it "is just, well, a Tuesday" | **volume** — confirmation the level mattered to everyone else |
| 3 | **daily chart** — into multi-year support or a flush in an uptrend, not a 6-month decliner | **in-play, ideally on fresh news**, leader in a hot sector, not "a random laggard drifting into a level" |
| 4 | **intraday chart — weighted heaviest**: "accounts for far more points than anything else on the rubric" | ⚠ **overall market conditions** — "can single-handedly downgrade an A setup to a C or worse" |
| 5 | **news** — wants **none**, or stale news overblown vs the move | **daily chart / MTF alignment** — "really great daily charts pull in everyone" |

### System B — the per-DAY report card (`vKy6Q9hwon4`)

- **When:** end of every session, without exception, including zero-trade days ("these are actually
  the most important days" [11:27]). "I refused to leave the office until mine was done" [11:49].
- **Output:** tomorrow's focus, plus — via "temp" — *today's* risk budget. Not size per trade.

Sections, in his order:

1. Date + a single grade A–F [02:05].
2. ⭐ **ONE process goal**, never P&L [02:29], broken down into solutions (his example: an
   overtrading problem becomes "only five trades each day" [02:53]).
3. ⭐ **The grade is that goal and nothing else** [03:04]: "solely based on did I make progress
   today at my goal."
4. Reminders / aphorisms, read pre-market [03:15].
5. ⭐ **Time-block grades** — 09:30–11:00 / 11:00–12:00 / 12:00–14:00 / 14:00–16:00 [03:37] — to
   "catch snowballing bad habits before they spiral," with the explicit property that a failed
   block doesn't lose the day [04:01]. The 11:00 check asks: was I on the play of the day, was I
   sizing properly, was I focused on the trades going in my favour [05:01].
6. ⭐ **"Temp"** — morning mental temperature: focus, sleep (Oura ring), stress, illness, hangover —
   feeding a **daily risk decision** [04:36]: "between all these factors, I would grade myself and
   decide how much I wanted to risk each day."
7. What I learned / improved today [05:23].
8. Changes to make tomorrow, **each with a solution** [05:44, 08:38].
9. Overview / miscellaneous [06:06].
10. ⭐ **"Easiest 50k"** — the day's *easiest* playbook trade, explicitly not the biggest [06:15]:
    "return on investment might be way more favorable in the really easy layup trades, which often
    get overlooked."
11. Tickers traded + writeups scaled to the size of the play [07:01].

**Goal rotation** [09:49–11:16]: swap the goal "when it is no longer the highest return on
investment goal for me," not when perfected; typically 3–4 weeks, sometimes 3–4 months; strictly
one at a time.

**Cadence** (`M-rpkVekvOQ`): ≥30 min intentional pre-market prep (what's in play, catalysts, review
your A+ setups, lock onto the constraint) [02:56]; ≥2 h post-close review [03:15]; 3 uninterrupted
hours of weekend deep work [03:33]; 20 written chart studies a week [04:10]; and the report-card
goal must be aimed at your **number one constraint**, chosen deliberately before the cycle starts
[02:18].

### Adoptable form for this repo

1. ⭐ **Add a rotating single goal to `run_journal_grades.py`** — a 6th, separately-reported line
   ("this month's constraint: X, hit/missed"), reviewed monthly, retired when it stops being the
   highest-ROI fix. Keep the five fixed components as the reproducible conformance meter; his goal
   is a different instrument, not a replacement.
2. ⭐ **Grade zero-trade sessions.** Today the grader iterates `journal_trades.trade_date`, so a
   flat day emits no row — the chain breaks silently on exactly the days he calls most important,
   and under `feedback_precision_over_recall` a correctly-flat day is a *win* we currently cannot
   score.
3. ⭐ **Time-block subscores.** `trade_datetime` is already in the table; scoring the fills and
   same-day-trip components per block turns a post-mortem into a mid-session trip-wire.
4. ⭐ **An "easiest layup" field.** Nominate the day's easiest playbook candidate **from the daily
   layer-2 in-play state** and record taken / missed. It is the only component that would score
   trades *not* taken. ⚠ Nominate from the day-state, **not** the alert stream —
   `project_alert_funnel_test` showed alerts add nothing beyond the layer-2 state, so an
   alert-sourced nomination would just re-measure the alerts.
5. **Pre-commit the grade.** Alerts already grade at fire time; discretionary entries have theirs
   reconstructed afterwards by `lib/journal/entry_grades.py`. Writing it before the fill removes
   the reconstruction and is nearly free.
6. **A state→risk ceiling**, if and only if it can be recorded honestly. Treat state as a *cap* on
   risk, not a *level* — which reconciles his "temp" dial with the KB's own
   [hot-streak protocol](../notes/hot-streak-protocol.md) rule that aggression should track the
   EV of the opportunity, not the emotional state.

## 2. ⚠ The sizing-lever question

Not an entry-location principle, so most of this section is n/a — but the video is the one that
was queued *because* of the lever, so the answer belongs here:

- **Stop distance / position size / stop-out rate:** not discussed. No stop, entry or invalidation
  appears anywhere in either video.
- **What it does say:** the lever is driven by **setup grade**, not by stop width — D 0, C a
  fraction, B standard, A up [01:19–03:12]. That is the "conviction risk varies by grade" mechanism
  already recorded in [`risk-framework-longform.md`](risk-framework-longform.md) ($10k B → $100k A),
  now stated as a general system rather than an anecdote.
- ⚠ **Already tested here, and only half-confirmed.** `project_size_lever_study` (2026-09-18): the
  exclusion half (A+B only) returned **+0.29R OOS vs 0.00 flat**; the spread half (10× risk across
  grades) returned **+0.08R with more drawdown**. So grade → *participate* is supported; grade →
  *size* is not, on our data. Also relevant: `project_breakout_regime_feedback` found the only
  regime lever that worked was **fixed small sizing**, not a switch.
- **What would settle the rest:** nothing new — this one is answered. The open lever stays where
  `HOW_THEY_DO_IT.md` left it (intraday entry location decoupling stop tightness from fragility),
  and neither video touches it.

## 3. Claimed edge & evidence

**There is none.** Across 23 minutes of video the total quantitative content is:

- [vKy6Q9hwon4 00:33] the report card "helped take me from being a top 10 trader to then take the
  number one spot at Trillium" — one unverifiable anecdote with no counterfactual, over the same
  years his playbook was maturing anyway.
- [ubofAZwgd4w 01:30] "literally, 99.9% of charts are D grade or worse" — rhetorical, but ⭐ cheaply
  checkable against our own funnel (universe ≈1,700 names × sessions vs 2,439 layer-2 name-days). If
  our gates pass far more than ~1% of name-days, our D line is much looser than his.
- [ubofAZwgd4w 03:01] "most traders' P&L comes from a small number of these trades" — ✅ agrees with
  the repo (`project_breakout_regime_feedback`: top 10% of months = 68% of positive R; his own
  [15 lessons](risk-management-15-lessons.md): 80% of profits from 1–5% of trades). ⚠ Note
  `project_vrp_straddle_reconcile` reaches the same shape (99.9% of straddle P&L from the top 0.1%
  of trades) and treats it as **fragility**, not a licence to size up.
- [ubofAZwgd4w 10:30] "all the traders at SMB Capital live and die by this framework" — appeal to
  authority, and SMB is itself a training business.
- [vKy6Q9hwon4 10:44] "the research backs up… one goal at a time" — no citation, and he concedes
  the psychology is "way beyond my intelligence."

**Flag: both videos are course marketing.** `vKy6Q9hwon4` is literally a paid-course module — at
[01:53] he says the template is "provided free as part of this course." `ubofAZwgd4w` carries an
explicit mid-video pitch [04:34–05:04]. Both titles lead with the $100M figure.

⭐ **The two claims in here that are actually testable on data already on disk:**

1. **"Boring stock, violent move"** [ubofAZwgd4w 06:15]. Rank selloffs by **drop% ÷ the name's own
   trailing ADR**, crossed with **low prior ADR**. This is a real refinement of
   [`project_crash_leader_study`](../../studies/), which concluded that buying deep selloffs is a
   *regime* bet rather than selection — but that study did not normalize the shock by the name's own
   normal range, which is exactly what he says does the work. Same normalization as the in-play gate
   in [`in-play-stocks.md`](in-play-stocks.md).
2. **The no-news veto on fades** [07:25]. Now the **fourth** independent statement of this rule in
   the repo (here, [`remaining-five.md`](remaining-five.md),
   [`capitulation-and-trade-writeups.md`](capitulation-and-trade-writeups.md), Carter's veto list)
   and still untested — the gap study never conditioned on catalyst at all.

And one claim that is **contradicted** rather than untested: "market conditions can single-handedly
downgrade an A breakout to a C or worse" [09:11] runs into `project_august_2026_retrospective`
(breadth gate nil, weak breadth a mild BUY not a sell, 2019–2026) and
`project_breakout_regime_feedback` (the paying months cannot be forecast from SPY state).

## 4. ⚠ Prop-infrastructure dependency

- **Depends on:** nothing technical. But two items are **prop-culture** dependent: the daily trading
  pod of two peer traders [vKy6Q9hwon4 07:43] has no retail equivalent, and the C-grade feeler trade
  [ubofAZwgd4w 01:52] is a seat-time argument that makes sense when your day job is being in the
  market and your marginal cost per trade is a rebate.
- **Retail-viable as stated?** partly — System B's template transfers wholesale; System A's grades
  transfer but its **size mapping does not survive our own test**, and its C tier should be dropped.

## 5. Decay risk

Low, unusually for this KB. A review loop is not a flow niche. The 2022 anecdote
[vKy6Q9hwon4 01:32] is 4 years old and the time-block structure assumes a 6.5-hour intraday
session — for a swing book the blocks carry much less content, which is the main thing that does
not age well here (a scoping limit, not decay).

## 6. Objective assessment

- ⚠ **Unfalsifiable by construction.** He declares the grades "completely subjective" [03:24] and
  the report-card grade self-assessed against a self-chosen goal. Nothing here can fail.
- ⚠ **His validation loop has no control.** Step 3 [10:10] — "are your A trades actually
  outperforming your B trades? If no, your criteria are wrong" — is the right *idea* and an
  insufficient *test*. Our own rubric revision is the counterexample: the v1 A grade (ORB9 ≥10:00)
  scored **+0.70R on the curated universe and −0.39R (83% stopped) on a 39-name no-hindsight
  control**, i.e. it was grading the universe, not the setup, and it was dropped for exactly that
  reason. Under his instructions it would have passed and been sized up.
- ⚠ **Every illustration is a winner described afterwards** (STRC, the anonymous utility) — zero
  base rates, zero numbers, in a video whose whole thesis is that grades should be validated
  against data.
- ⚠ **Both videos sell a course**, and `vKy6Q9hwon4` *is* a course module.
- The "one goal at a time" claim [10:44] is asserted from popular psychology, not evidence — though
  it is probably directionally right and cheap to follow either way.

## 7. What's genuinely sound

- ⭐ **Process, not P&L, as the grading axis**, with the reason stated plainly
  (`M-rpkVekvOQ`@[01:36]): P&L is noisy over short horizons, process is not. `run_journal_grades.py`
  already does this from a secondhand note; it is now **sourced rather than inferred**.
- ⭐ **A setup is a weighted scorecard, not a binary** [04:04] — arrived at independently by
  `feedback_breakout_scorecard`. Two sources, two routes, same conclusion.
- ⭐ **One rubric per setup** [05:15]. A fair criticism of our single shared rubric, which handles
  the short side with extra vetoes rather than its own scorecard.
- ⭐ **D is a fold no matter how bored you are** [01:24] — the one sizing claim our own data
  confirms, and the same conclusion as `feedback_precision_over_recall`.
- ⭐ **Grade before entry, never after** [10:04]. Cheap, and it removes a real reconstruction step
  from our journal.
- ⭐ **Easiest layup, not biggest winner** [06:15]. The only field on either card that scores what
  you *didn't* do.
- **Fill the card on slow days** [11:27]. Directly exposes a gap in our grader.
- **Solution-based reflections** [08:38] — identifying the leak is half the work.

## 8. Overlap / conflict with the rest of the repo

**Which of his systems is which of ours:**

| His | Ours | Status |
|---|---|---|
| System A — per-trade grade, pre-entry, → size | `src/lib/alerts/grading.py` (per-setup A/B/C/F, shared by alerts + journal) | ✅ same object. Ours is **more** validated (153-session replay, 19,456 alerts, with a control set); his is **broader** (structural variables ours dropped or never tested: consolidation length/tightness, volume confirmation, catalyst freshness, MTF alignment → natural v3 candidates). Ours does **not** map grade→size; his exists only to do that. |
| System B — per-day report card, post-close, → tomorrow's focus | `run_journal_grades.py` (5 components, 100 pts, A≥85 B≥70 C≥55 else D) | ⚠ same object, **different design** — see the delta table below. |

**Deltas, System B:**

- **Ours has, his doesn't:** vehicle doubling (15), exits reviewed `too_soon` (15), a hard fill cap
  (15), same-day round trips with an invalidation carve-out (25), a reproducible 100-point score
  computed from the database. His card has *no* exit component and *no* vehicle component, and
  overtrading appears only as an **example goal** [02:42], not a permanent line. Ours is
  effectively his card with Gabe's four named leaks frozen in as permanent scoring — defensible,
  and reproducible in a way his self-assessed prose is not.
- **His has, ours doesn't:** ⭐ the rotating single goal *as the grade* (ours never moves, so it
  cannot drive one fix to completion and retire it — the explicit instruction at [09:59]);
  ⭐ time-block grading; ⭐ the state→risk dial; ⭐ the easiest-layup field; a forward "changes for
  tomorrow, with solutions" field; and grading zero-trade days.
- **Per-trade or per-day:** the A/B/C/D of `ubofAZwgd4w` is **per trade, before entry, output =
  size**. The report card of `vKy6Q9hwon4` is **per day, after the close, output = tomorrow's
  focus**. Our per-day grader is his *report card*, not his *trade grade* — the secondhand note
  fused them, and the code has always been right.

**Three house-rule conflicts — do not import:**

1. ⛔ **The C-grade feeler trade** [01:52] contradicts `feedback_precision_over_recall`, contradicts
   the size study's finding that exclusion *is* the edge, and is the exact behaviour our own card
   penalises twice (fills cap + same-day round trips) and that the August lens costed at −$7.9k.
2. ⛔ **"Compare your grades to your results"** [10:10] contradicts
   `feedback_gabes_trades_are_not_evidence`: it makes your own book the evidence base for whether a
   *setup* rubric is real. Adoptable form: grade pre-entry and log it, but validate the rubric on
   the replay population (`run_alert_study.py --report grades`), never on the book. At our trade
   count his version would be noise even if the rule allowed it.
3. ⚠ **"Size up on A"** [03:01] — tested here, +0.08R with more drawdown vs +0.29R for plain
   exclusion. Keep grade→participate; hold grade→size at low conviction.

**And one scoping conflict:** his time-block structure, his C trades and his intraday-chart-weighted
capitulation rubric all assume an intraday prop seat. This book manages on the **daily close** with
no same-day exits unless the stop is hit. The blocks still translate (as a snowball trip-wire on
fills), but the trading content around them does not.

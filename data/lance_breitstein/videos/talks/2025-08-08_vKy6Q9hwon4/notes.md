# Copy My Trading Report Card That Made Me $100 Million

**Video:** `vKy6Q9hwon4` · **Type:** talks · **Watched:** 2026-09-19 · **Published:** 2025-08-08 · 12:16

> ⭐ **This is the primary source for the repo's own daily process grade.** `run_journal_grades.py`
> was built from a *secondhand* paraphrase in
> [`notes/four-constraints-and-the-ai-trap.md`](../../../notes/four-constraints-and-the-ai-trap.md)
> ("pre-assign risk levels by trade quality, then grade yourself daily on whether you risked
> accordingly"). Now that the actual video is in hand, **ours and his turn out to be different
> objects** — see "Reactions / conflicts".

## Raw notes

- [00:33] Claim: "Implementing a daily report card was the best practice that helped take me from
  being a top 10 trader to then take the number one spot at Trillium." No data, unverifiable.
- [00:44] Definition: "a daily review process done with the goal of efficiently improving one's
  trading." Framed as *metalearning* + deliberate practice; Tiger Woods never hitting a ball
  without reflecting on it [01:08].
- [01:32] 2022 regime anecdote: long breakout/momentum stopped working; "those that were following
  the process of daily review and reflection were so much quicker to adapt." Unfalsifiable but the
  mechanism he's claiming is *adaptation speed*, not edge.
- [01:53] ⚠ **"Provided free as part of this course is the template."** This video is a module of
  the paid course, released as marketing. Whole structure below is the course artifact.

### The template, section by section

1. [02:05] **Date + a grade A through F.** "Feel free to do whatever system makes sense to you."
2. [02:17–02:53] **ONE goal.** Process, never P&L: "this goal should not be P&L or outcome
   focused." His own examples: am I overtrading, am I deliberate with sizing, am I involved enough
   in certain setups, am I missing level-2 clues. Break the goal down into *solutions* — if
   overtrading, "create a goal that only allows you five trades each day."
3. [03:04] **The grade is SOLELY the goal.** "You grade yourself solely based on if you
   accomplished that one chosen goal for the day, not your P&L… It is solely based on did I make
   progress today at my goal."
4. [03:15] **Reminders / aphorisms**, read pre-market. Personal cue cards, not scored.
5. [03:37–04:12] **Day broken into time blocks** — 9:30–11:00, 11:00–12:00, 12:00–14:00,
   14:00–16:00 — graded separately. Purpose: "catch snowballing bad habits before they spiral,"
   and "even if you fail in one, you can still win the day by doing much better in the subsequent
   blocks."
6. [04:12–05:01] **"Temp"** = morning mental temperature (focus, sleep — tracked on an Oura ring,
   stress, illness, hangover). ⭐ **This is an input, not a score**: "between all these factors, I
   would grade myself and decide how much I wanted to risk each day." Explicitly: tired/sick/
   stressed/hungover → "in no way would I want to risk the same amount."
7. [05:01–05:23] **Mid-day check at 11:00** on the 9:30–11:00 block: "What is my grade this
   morning? Was I sticking to the play of the day? Was I sizing properly? Was I focusing on the
   trades that were going in my favor?" Repeat per block.
8. [05:23] **What I learned / improved today** — filled every day without exception, "even if there
   were zero opportunities."
9. [05:44–06:06] **Changes I need to make from today**, each with a proposed solution.
10. [06:06] **Overview** — miscellaneous: distractions, market trends.
11. [06:15–07:01] ⭐ **"Easiest 50k"** — the one trade of the day that was the *easiest* money and
    "directly linked to my playbook." Explicitly **not** the biggest: "So often people get seduced
    by where the biggest money was, but that oftentimes is a mistake… return on investment might be
    way more favorable in the really easy layup trades, which often get overlooked."
12. [07:01] **Tickers traded**, with writeups on the important ones, detail scaled to size of the
    play; skipped on slow days to save time.

### Advanced tactics

- [07:43–08:38] **Trading pod**: share your report card daily with 2 other traders and read theirs.
  "For the same effort, you're getting three times the benefit." He did this with two top traders
  for years.
- [08:38] **Solution-based reflections**: identifying the problem "is an important step, but you're
  missing half the battle."
- [08:57] **Celebrate wins** — cites BJ Fogg (Stanford) on celebration cementing habits.
- [09:17] **"Don't break the chain"** (Seinfeld). [11:49] "I refused to leave the office until mine
  was done."

### Goal rotation (the FAQ section)

- [09:49–10:33] Change the goal "when it is no longer the highest return on investment goal for me."
  Not when perfected — "perfection is the enemy of a lot of progress."
- [10:44–11:16] One goal at a time; "the research backs up the fact that people do much better with
  one goal at a time" (he concedes the psychology is "way beyond my intelligence"). Typical goal
  = 3–4 weeks; some have run 3–4 months.
- [11:27] Slow / barely-traded days: "Big resounding yes" — still fill it out, "these are actually
  the most important days."

## Named setups appearing here

None. This is pure review process — no setup, entry, stop or exit content in the entire video.

- [x] **Daily report card** — promoted to
      [`principles/trade-grading-and-report-card.md`](../../../principles/trade-grading-and-report-card.md)
      (jointly with `ubofAZwgd4w`).

## Claims to verify

- [ ] "Took me from top 10 to the number one spot at Trillium" [00:33]. **Unverifiable** — single
      anecdote, no counterfactual, and the same years he was also running a maturing playbook.
- [ ] "Research backs up… people do much better with one goal at a time" [10:44]. Checkable against
      the goal-setting / habit literature (Locke & Latham; Fogg). He cites nothing. The claim is
      probably directionally right and irrelevant to whether it improves *trading*.
- [ ] BJ Fogg on celebration cementing habits [08:57]. Real citation, correctly attributed
      (Tiny Habits). Not a trading claim.
- [ ] "Traders following daily review adapted faster in 2022" [01:32]. Not checkable as stated. The
      *repo* version of this claim IS checkable and has already been partly answered in the
      negative: `project_breakout_regime_feedback` found the paying months can't be forecast and
      that regime management is fixed small sizing, not a switch. Fast adaptation may be a story
      told about survivors.
- [ ] ⭐ **Testable on our own data:** does the grade produced by `run_journal_grades.py` lead
      subsequent P&L at all? He asserts process→outcome; the repo can measure it (grade on day t vs
      NAV day P&L days t+1..t+10). ⚠ n is small and `feedback_gabes_trades_are_not_evidence` limits
      what a positive result would mean — at most it validates the *conformance meter*, never a
      setup.

## Quotable rules

- [02:29] "This goal should not be P&L or outcome focused."
- [03:04] "You grade yourself solely based on if you accomplished that one chosen goal for the day,
  not your P&L."
- [04:01] "Even if you fail in one, you can still win the day by doing much better in the subsequent
  blocks."
- [04:36] "Between all these factors, I would grade myself and decide how much I wanted to risk each
  day."
- [06:50] "Return on investment might be way more favorable in the really easy layup trades, which
  often get overlooked."
- [08:47] "You need to figure out what you're going to do to fix this problem over the next few
  trading days."
- [09:59] "I change my daily report card goal when it is no longer the highest return on investment
  goal for me."
- [11:38] "If you are productive and find something new to improve upon, that is considered a win
  for a slow day."

## Reactions / conflicts

### ⚠ The repo's process grade is his *object*, but not his *design*

`run_journal_grades.py` is a **fixed five-component, 100-point composite** (entry quality 30 /
same-day round trips 25 / activity 15 / exits 15 / vehicles 15; A≥85 B≥70 C≥55 else D). His is a
**single rotating goal, graded pass/progress on that goal alone**, with the rest of the card as
unscored prose. Item by item:

| His card | Ours | Delta |
|---|---|---|
| One process goal, grade = that goal only [03:04] | five fixed components, always the same | ⭐ **biggest structural difference.** His is a *focus device* that changes every 3–4 weeks; ours is a *conformance meter* that never moves. Ours cannot drive one improvement to completion and then retire it. |
| Time-block grading 9:30–11 / 11–12 / 12–2 / 2–4 [03:37] | whole session as one unit | ⭐ **missing from ours**, and cheap: `journal_trades.trade_datetime` already carries fill times, so the same-day-trip and activity components could be scored per block. His stated purpose (catch the snowball at 11:00, not at 16:00) is exactly the failure mode the Sept journal shows. |
| "Temp" (sleep/state) → **that day's risk budget** [04:12–05:01] | no input-side component at all | **missing.** Ours grades only outputs, after the fact. This is the one item on his card that changes behaviour *before* the session. ⚠ It also sits in tension with the KB's own [hot-streak protocol](../../../notes/hot-streak-protocol.md), where the rule was "aggression matches the EV of the opportunity, **not** the emotional state." Reconcile as: state sets a *ceiling* on risk; opportunity EV sets the *level* within it. |
| "Easiest 50k" — name the day's easiest playbook layup [06:15] | nothing | **missing, and it is the only component that scores trades NOT taken.** Every one of ours grades trades that happened. The repo already has the ingredients (layer-2 in-play list + `alerts_latest.csv`) to auto-nominate the day's easiest playbook candidate and mark taken / missed. ⚠ Read it against `project_alert_funnel_test` — the nomination must come from the **daily in-play state**, not from the alert stream, since alerts were shown to add nothing beyond it. |
| Learned today / changes with solutions [05:23–06:06, 08:38] | score only, no forward field | **missing.** Ours emits a number and no commitment for tomorrow. |
| Fill it out on slow / zero-trade days [11:27] | grades only sessions that have fills | ⚠ **concrete bug-shaped gap:** `run_journal_grades.py` iterates `t.trade_date`, so a **no-trade day produces no row**. By his design that day is the *most* important to record (and under `feedback_precision_over_recall` a correctly-flat day is a win, not an absence). Today ours cannot award it. |
| Pod sharing with 2 traders [07:43] | n/a | Not transferable (single trader). The nightly AI review is the nearest analogue and is a weaker one — it does not bring two other people's best trades. |
| Grade A–F on one goal | grade A–D on five | cosmetic. |

### What ours has that he does not

Vehicle doubling (stock + option on one name, 15 pts), exits reviewed `too_soon` (15 pts), a hard
fill cap (15 pts), and same-day round trips as a permanent 25-point component with an
*invalidation* carve-out. **None of these appear on his card as components** — overtrading appears
only as an *example goal* [02:42]. That is defensible: ours are the repo's four named, measured
leaks, so ours is his card with Gabe's current constraints frozen into permanent scoring. The cost
is that they can never be retired, which is precisely what [09:59] says to do once a goal stops
being the highest-ROI fix.

Ours is also **reproducible from the database and cannot be argued with after the fact**, which his
self-assessed prose card is not. That is a genuine improvement, not a divergence to fix.

### Per-trade or per-day?

**Per DAY, unambiguously, and it drives nothing but tomorrow's focus** (plus, via "temp", today's
risk budget). The A/B/C/D that drives *size* is a different object entirely — see
`ubofAZwgd4w`. The repo already implements both, split correctly across two files
(`run_journal_grades.py` = per-day process card; `src/lib/alerts/grading.py` = per-setup grade).
**It is the secondhand note that conflated them, not the code.**

---

**Rating: 3.5/5** (the most directly adoptable process material in the KB, and the honest source
for a system the repo already runs — four named gaps fall out of it immediately, two of them
cheap. Capped well below 4 because there is zero evidence of any kind: one unverifiable Trillium
anecdote, no numbers, no control, and the whole artifact is a paid-course module. It is a good
design for a review loop, offered as if it were the cause of $100M.)

**Course-marketing content present: yes** — [01:53] the template is "provided free as part of this
course"; the video is a course module. The title itself ("$100 Million") is the pitch.

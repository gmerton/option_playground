# The 60-Day Trading Routine to Becoming Profitable

**Video:** `M-rpkVekvOQ` · **Type:** talks · **Watched:** 2026-09-19 · **Published:** 2026-09-12 · 6:18

> Short, promotional, and almost entirely a restatement of two videos already in the KB
> (`vKy6Q9hwon4` daily report card, `3sug7e1AYk8` four constraints). Its one contribution is a
> **time budget** — he finally puts hours on the routine.

## Raw notes

- [00:00] Pitch: the "level up 60-day trading challenge", explicitly modelled on 75 Hard, run as a
  community challenge for September–October 2026. "Not a challenge built around fake toughness, but
  one designed around the habits that actually produce better traders" [00:37].
- [00:45–01:22] The diagnosis: it is not intelligence — "I've seen some really not so smart traders
  make a hell of a lot of money on Wall Street." **"By far the biggest reason why people fail is
  that they lack consistency of intense productive effort."** The failure pattern he names:
  "They'll journal for 3 days, skip the next five, review one weekend, then disappear for 2 weeks."
- [01:22–01:43] ⭐ The framing sentence, and the only line worth carrying forward: **"The goal is not
  to make money over the next 60 days… the goal is to become the type of trader who deserves to
  make money. Your P&L is often noisy over short periods, but your process is not. For the next 60
  days, you're judged entirely by the work you put in. If you execute the process, you've won the
  day, regardless of whether you made or lost money."**

### The six rules

1. [01:43–02:18] **Show up 100% to every market day.** "If there are no opportunities, your job
   becomes studying." Athletes practise without a game; musicians rehearse without a concert.
2. [02:18–02:46] **A daily report card every session.** ⭐ Before starting, "spend a few hours trying
   to figure out what your number one constraint is" (explicit pointer to the four-constraints
   video), then aim the card's **process goal** at that constraint. "Putting superhuman effort into
   one prioritized constraint at a time is the fastest way to improve. Elite performers don't try
   to improve 10 things simultaneously."
3. [02:46–03:33] **≥30 min of intentional pre-market prep** — "not scrolling Twitter or watching
   CNBC": which stocks are in play, what catalysts to expect, review your A+ setups, and "lock in
   on your biggest constraint as a trader before the opening bell." Plus **≥2 hours of post-close
   review**: screenshot trades, write down reasoning, "ask yourself whether the execution matched
   your trading plan." ⭐ "Most traders are eager to watch another educational video before they've
   even learned from their own mistakes. That's backwards. Your own trades are the most educational
   material you'll ever have because they're perfectly customized to you."
4. [03:33–04:10] **3 uninterrupted hours of deep work every weekend** — no phone, no social media:
   charts, the week's performance data, refining strategies. Argued on attention quality: markets
   closed, not drained from a session.
5. [04:10–04:38] **20 written chart studies per week** (≈100+ over the 60 days). "Not just the
   screenshots, but an actual analysis of the nuances": what the market was like going in, **why
   the move happened, where the edge was, and how the trade should have been sized**.
6. [04:38–05:08] **≥7 hours sleep, clean eating, daily exercise, no alcohol.** "Trading psychology
   doesn't begin when you enter a position. It starts with how you live the previous 24 hours."
- [05:08–05:36] Milestones: day 15 you realise how inconsistent you normally are; day 30 you
  recognise patterns faster; day 60 "you probably might not be an elite trader yet… but you'll have
  built the habits of one."
- [05:36] "Stop looking for another strategy and start acting like a professional for the next 60
  days." [05:46] "Markets always reward preparation, discipline, and repetition far more often than
  they reward brilliance." [05:52] Honest disclaimer: "will not guarantee profits."
- [05:55] Call to action: post your report cards / writeups on X, tag him, link the video.

## Named setups appearing here

None. No entry, stop, exit, sizing or pattern content anywhere in the video.

- [ ] Nothing to promote on its own. Rule 2 + rule 3 are folded into
      [`principles/trade-grading-and-report-card.md`](../../../principles/trade-grading-and-report-card.md)
      as the **cadence** section (they are the hours behind `vKy6Q9hwon4`'s template).

## Claims to verify

- [ ] "By far the biggest reason why people fail is that they lack consistency" [01:03].
      **Unfalsifiable as stated**, and it is survivorship reasoning: he is describing the
      consistent people who made it. The base rate says most consistent day traders also lose.
- [ ] Day 15 / day 30 / day 60 milestones [05:08]. Motivational structure, not a measurement.
- [ ] ⭐ **Checkable on our own book:** "your P&L is noisy over short periods, but your process is
      not" [01:36]. We can measure the noise directly — variance of daily NAV P&L vs variance of
      the `run_journal_grades.py` score over the same sessions. If the process score is *not*
      materially more stable than P&L, our five-component card is measuring noise too, which would
      be a finding about our card rather than about him.
- [ ] "30 min pre-market / 2 h post-close / 3 h weekend / 20 chart studies a week" — the only
      numbers in the video, and they are **prescriptions, not evidence**. Nothing supports these
      magnitudes over half or double them.
- [ ] "100 meaningful charts in 60 days" [04:29] ≈ the KB's own throughput. Worth noting that the
      repo's equivalent of his chart-study rule already exists and is better instrumented:
      `reference_pattern_test_harness` (6 patterns tested, 0 passed) tests a pattern in ~20 lines
      with a same-name random control. His chart study has **no control** — it is 100 stories about
      moves that already happened, which is the hindsight problem
      [`setup-grading-chart-nuance.md`](../../../principles/setup-grading-chart-nuance.md) already
      flags on his drawn charts, industrialised to 100/quarter.

## Quotable rules

- [01:24] "The goal is not to make money over the next 60 days… the goal is to become the type of
  trader who deserves to make money."
- [01:36] "Your P&L is often noisy over short periods, but your process is not."
- [01:47] "If you execute the process, you've won the day, regardless of whether you made or lost
  money."
- [01:52] "Show up 100% to every market day. If there are no opportunities, your job becomes
  studying."
- [02:41] "Elite performers don't try to improve 10 things simultaneously. They solve one
  meaningful problem at a time."
- [03:33] "Your own trades are the most educational material you'll ever have because they're
  perfectly customized to you."
- [04:44] "Trading psychology doesn't begin when you enter a position. It starts with how you live
  the previous 24 hours."

## Reactions / conflicts

- ⭐ **Confirms the repo's grading choice from the source.** "Graded on PROCESS, not P&L" is the
  first line of `run_journal_grades.py`'s docstring, taken from a secondhand paraphrase; [01:36]
  and [01:47] state it firsthand and give the reason (P&L noise vs process stability). That
  decision is now sourced, not inferred.
- ⭐ **Rule 2 supplies the missing link between our card and his.** The report-card goal must be
  aimed at your **number one constraint**, re-derived deliberately before the cycle starts. Ours
  has five permanently-weighted components and no constraint-selection step at all — so it can
  never answer "what is the one thing to fix this month?", which is the entire point of his design.
  See the delta table in the `vKy6Q9hwon4` notes.
- ⚠ **"Show up 100% to every market day" collides with the repo's own results.** For him
  attendance is free: he is an intraday prop trader whose day is spent studying when nothing is in
  play. For this book, seat time is the *cost centre* —
  [`project_exit_timing_study`](../../../../studies/) found 278 same-day cycles at −$8.3k / 19%
  win, and `project_august_2026_luk_tito_lens` costed same-day round trips at −$7.9k. And the house
  rule is explicit: **no same-day exits unless the stop is hit; manage on the daily close.** His
  rule is safe only with the second clause attached ("if there are no opportunities, your job
  becomes *studying*") — quoted without it, it is an invitation to the exact leak our card
  penalises 40 points for. ⚠ Note the same tension sits inside his own material: this video says
  show up every day, while `ubofAZwgd4w`@[01:24] says a D setup is a fold "no matter that you've
  been bored all day."
- **Rule 3's post-close review is what `run_daily_journal.py` + the nightly AI review already do**,
  at a fraction of two hours. The honest read is that the repo has *automated* his rule 3 and
  should not treat the automation as equivalent — his version includes writing the reasoning by
  hand, which is where his claimed learning comes from. Automating the artifact does not
  automatically deliver the benefit he attributes to producing it.
- **Rule 6 (sleep/alcohol/exercise) is the input-side item `vKy6Q9hwon4`@[04:12] turns into a risk
  dial ("temp").** It is the only one of the six our card cannot ever observe, and the only one
  worth *not* trying to automate.
- ⚠ **Nothing here is evidence.** Zero data, zero examples, zero numbers other than the time
  budget. It is a community-engagement campaign with a real idea (consistency of deliberate
  practice) that the KB already had from a better video.

---

**Rating: 1.5/5** (one genuinely useful sentence — process is the stable signal, P&L is not, so
judge the day on work done — and one useful structural pointer: aim the report card at the number
one constraint. Everything else is restatement of `vKy6Q9hwon4` and `3sug7e1AYk8` wrapped in a
75-Hard-style challenge. No mechanics, no evidence, and one rule ["show up 100% of days"] that
would be actively harmful to this book if lifted without its second clause. The time budget
[30 min / 2 h / 3 h / 20 charts] is the only new content and it is asserted, not derived.)

**Course-marketing content present: yes** — the video *is* the marketing: a branded challenge
("level up 60-day challenge") with a dated September–October window, the "$100 million on Wall
Street" credential [00:18], a pointer to his constraints video, and a tag-me-on-X engagement ask
at [05:55], closing on a subscribe prompt.

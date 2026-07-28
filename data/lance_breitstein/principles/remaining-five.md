# Multi-timeframe, news, playbook, tape, scalping

Five shorter videos grouped. One contains a **testable conditioning rule that three independent
sources now agree on**; the rest are process or prop-dependent.

---

## A. ⭐ News: the mean-reversion conditioning rule — TESTABLE

> **Source:** `-ZV_EpqmUDQ` "How to Trade the News Like a Top Wall St Trader" (2025-11-01)

> Fading an outsized move **on fresh news** is "often going to be a fool's errand and **almost
> always negative expected value**. When there are outsized moves **on no fresh news**, that is
> often when mean-reversion traders want to bet."

The same condition appears in his Bollinger video — "stocks **without fresh news** can often
exhibit strong mean reversion characteristics" — so it is stated twice, independently, as the
gating variable on his single largest edge (mean reversion).

**⚠ Three independent sources now agree on this**, and the repo has never tested it:

1. **Breitstein** — don't fade moves with fresh news; fade moves without.
2. **Carter** (*Mastering the Trade*, ch. 7) — his gap-fade veto list leads with news and earnings
   gaps.
3. **This repo's own gap study** — found the unconditional fade worthless (+2.59 bp SPY, negative
   on DIA, every stopped variant bracketing zero) and never once conditioned on whether a catalyst
   caused the gap.

**The test:** re-run [`opening-gap-fade`](../../carter_mastering_the_trade/setups/opening-gap-fade.md)
splitting gaps by catalyst presence. Cheapest available proxy is earnings dates (already reachable
via the `lib.earnings` module) plus a relative-volume threshold. Prediction: the no-news cohort
carries the fade's entire edge, and the news cohort is negative — which, if true, would rescue a
setup currently written off at 1/5.

## B. Multi-timeframe: an explicit precedence rule

> **Source:** `k6I04ciE1KE` (2025-12-06)

> "If you are an intraday trader, the intraday chart will **always** be more important than the
> daily chart. If I had to approximate it, the intraday chart gets an **80% weighting** for my
> decisions. **Even if the daily chart is screaming short, if the stock is steadily grinding on
> the intraday chart, I will almost never fight that.**"

He always starts with daily-chart context, then lets the traded timeframe dominate the decision.
This is the same principle as his stop rule ("match the stop to the timeframe you're trading") and
is what makes the swing/intraday split in [swing-strategies.md](swing-strategies.md) coherent
rather than contradictory: **the timeframe you trade owns the decision; the higher timeframe only
supplies context.**

⚠ Not testable as stated (80% is a figure of speech), but it is the explicit resolution of a
tension that runs through the whole KB.

## C. The playbook process — four steps

> **Source:** `bKvEfCGJS4g` (2025-07-22)

1. **Identify a setup that works for you** — "an earnings breakdown, a panic capitulation, a VWAP
   reclaim, a trend-day breakout."
2. **Capture the context** — bigger picture, catalyst, sentiment, and **"who's trapped."**
3. **Screenshot** trades and charts with entries, exits, risk levels, and the reasoning.
4. **Grade it A+/B/C, and say why** — plus how you'd play it differently.

Explicitly **not** a full trade log: "you're not logging every trade."

⭐ **"Who's trapped" is the operative item.** It is the counterparty question — the exact test this
repo uses to separate live edges from dead setups — expressed as a routine field to fill in on
every review. Worth stealing verbatim for `data/studies/` write-ups.

The grading step is also what feeds the A/B/C/D sizing scheme in
[stops-and-sizing.md](stops-and-sizing.md); the playbook is where the grades get calibrated.

## D. Level 2 / tape reading — ⚠ prop-dependent, park it

> **Source:** `RKV1rncXSkg` (2026-05-30)

Mechanics of the Level 2 box, bid/ask ladder, size display in lots, spotting large buyers and
sellers. **Not retail-testable here** and not currently actionable — it needs a data feed and
screen time the repo has no path to.

One transferable process item: he **recorded his screen** (Camtasia/OBS), cut the day down to "the
most essential couple of minutes," and rewatched after hours. That is the highest-leverage part of
the video and costs nothing.

## E. Scalping — ⚠ intraday, park the evaluation

> **Source:** `2DXQqwKSwJE` (2026-04-11)

Sequence: in-play stock → **identify a tight, well-defined intraday support/resistance level** →
take the trade for asymmetric risk/reward while keeping a solid win rate. He weights it "the chart
is 70% of the setup" with tape reading as the decisive skill.

⚠ **Explicitly prop-flavoured** and needs minute/tape data. Park it.

Note the recurrence of **"a tight, well-defined level"** — the same idea as the naturally-tight
breakout bar in [stops-and-sizing.md](stops-and-sizing.md) and the turn in
[right-side-of-the-v.md](right-side-of-the-v.md). Across five unrelated videos his edge is always
described the same way: **find a place where being wrong is cheap and unambiguous.** That is the
most consistent theme in the entire corpus, and it is the thing daily bars cannot see.

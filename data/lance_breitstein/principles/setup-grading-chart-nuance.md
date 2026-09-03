# Setup grading — the chart nuances that separate an A setup from a no-play

> **Verdict:** ⭐ **The most operationalizable setup material in the KB, and the weakest evidence.**
> Twelve hand-drawn charts across four setup archetypes, each graded play / no-play with a stated
> reason. The specifications are unusually crisp — 4 of them are EOD-testable today — but the
> entire video is assertion illustrated by charts *he drew himself with the outcomes already on
> them*. Zero numbers, zero base rates, zero out-of-sample content.
> **Type:** setup quality / entry grading · **Conviction:** 2.5/5 · **Testability:** EOD ⭐⭐
> **Tested?** no · **Source:** `9SgNXrWTefY` (2026-07-25), "Which Charts Are Worth Trading?"

---

## 1. Why this one matters despite the evidence being nil

It is the **explicit prequel to the sizing lever**. Closing line, [19:41]:

> "These nuances allow you to then **grade the quality of a setup**… in one of my next videos, I
> discuss exactly how you can take these nuances and these variables to **grade your setup A
> through D and directly influence your sizing** on a trade."

That is the missing first link in the chain the repo has been chasing. `HOW_THEY_DO_IT.md` found
the sizing lever (position = risk% ÷ stop%) is the only mechanism large enough to explain real
momentum-trader returns; [risk-framework-longform.md](risk-framework-longform.md) found he varies
risk **10× by grade** ($10k B → $100k A); [right-side-of-the-v.md](right-side-of-the-v.md) found
the chain starts with *timing*, not the stop. **This video is where the grade comes from.**

And once, at [18:03], he states the mechanism outright — the one sentence in the video that bears
directly on stop *fragility* vs stop *tightness*:

> "If in theory we're supposed to buy ahead of support and we can't push off that, that shows that
> buyers are not stepping in… then the beauty is once you break through, if you use a trailing stop
> to the prior bar highs, **your stop is really, really close**. All of those factors help jack up
> your expected value."

The claim is that a *high-quality* pattern is one whose own structure places the invalidation
close by — tightness and fragility decouple **because the setup was selected for it**, not because
the trader chose a tighter number. That is exactly the hypothesis the KB was opened to test.

⚠ He gives no stop-out rate, so it does not settle anything. Daily-bar baseline to beat remains
**91% stop-out at a 1.5% stop**.

---

## 2. Mechanics — the four archetypes

Scope caveat he states himself, [05:51]: **in-play stocks only** — catalyst-driven names, IPOs,
"a lot of price discovery, emotions, volume, volatility." Explicitly *not* ordinary stocks. Plus a
magnitude floor, [06:11]: the move must have covered real ground ("if this down move is only 10
cents, I might only expect a 5-cent bounce") — the pattern is worthless on a small range.

### 2a. Long breakout — only the tight one is playable

| | shape | verdict |
|---|---|---|
| **A** | opening drive → higher low → another higher low, **tightening** into the level → break | ✅ **the only play** |
| **B** | drive → deep pullback as a % of the opening leg → **lower low** → covers a lot of ground back into the level | ❌ no play |
| **C** | grind higher, price repeatedly above/below the level → break | ❌ "not much of a level at all" |

Two rules extract cleanly:
- **Pullback depth relative to the prior leg** is the discriminator, plus range contraction into
  the breakout. "If we were so strong, we shouldn't be pulling away so far from the resistance."
- **Level cleanliness** — a level must have "a very uniform emotional reaction… so defined that
  everybody can see it," so that the break forces both scrambling longs and covering shorts. A
  level price has oscillated across repeatedly cannot do that.

### 2b. Long bounce (trend break) — buy the waterfall, not the grind

| | shape | rank |
|---|---|---|
| **C** | steady, then **severe acceleration into an asymptotic waterfall** | 🥇 best |
| **A** | clean steady downtrend, slope ≈ −1 | 🥈 playable |
| **B** | choppy — repeated bounce attempts on the way down | 🥉 worst |

⭐ **The falsifiable claim in this video**, [04:11]:

> "The cleaner a stock trends one way, so often **the cleaner the counter-trend will be**… I don't
> need to know what's going to trend cleanly. What I can find is: wow, this trended super cleanly
> — I'm going to catch a clean counter-trend with higher probability."

Evidence offered: **one example** (CAR/Avis, 2026). That is it.

Entry is deferred to [right-side-of-the-v.md](right-side-of-the-v.md) — break of prior bar highs
or a trendline break; stop at the lows or trailed on prior bar lows.

### 2c. Long bounce (turtle soup) — mostly no-plays, and the veto is the useful part

All three variants rejected or near-rejected. The generalizable veto:

- ⛔ **"Price acceptance" bars near the lows** — small/tight/doji bars at the bottom = buyers are
  not there = "pretty much almost always a no play." He wants **price expansion** into the low
  followed by a violent reclaim, not quiet settling.
- ⛔ **Failure to bounce off the support level at all** before breaking it.
- The only tolerable variant (C) has price *expanding* lower, a visible strength attempt that traps
  longs, then a flush below support on heavy volume and a hard reversal.

### 2d. Long continuation — shallow pullback, and wait for the actual break

| | shape | verdict |
|---|---|---|
| **B** | drive → **shallow** pullback staying near resistance → consolidation → break | ✅ "absolutely beautiful" |
| **C** | drive → **one** steep deep bar → break | ❌ one bar isn't enough consolidation (a doji/inside bar would have been fine) |
| **A** | drive → pullback retracing **100%** of the leg → back to resistance | ❌ worst |

Reason for rejecting A is a counterparty argument, [13:36]: after a full retrace, "so many longs
are going to want to take sales there and so many shorts are now getting the chance to reshort
again right by that resistance."

**Entry-location rule:** he waits for the **full break of the range**, not the earlier entry as the
trend curls up — that earlier one is a [no man's land](no-mans-land-and-process.md) entry. The
further from resistance, the more tempting and the more he refuses.

### 2e. Short continuation — the "bouncy ball"

His canonical setup and, he says, one of his favourites:

1. Leg lower, ideally on news or a technical catalyst.
2. Each subsequent bounce **lower than the last** — never surpassing previous highs.
3. Final bounce barely bounces at all.
4. **Bars go very tight right before the break**, ideally into the close.
5. Trigger = break of support; **trail on prior bar highs** → stop sits very close.

Rejections: a bounce that surpasses prior highs (A), and insufficient consolidation relative to how
much ground and time the down leg covered (B) — "the more ground that drive lower covers… the more
I need that price acceptance, that consolidation, so that all the people that want to buy have
their chance to buy."

Note the deliberate asymmetry with 2c: tight bars at the *lows of a long setup* are a veto, tight
bars *before a short break* are the confirmation. Same observable, opposite reading, because the
question is always "is the side that should be defending this level actually there?"

---

## 3. ⚠ Evidence — this is the weakest-evidenced document in the KB

- **He drew every chart, including the outcomes.** The green resolution bars on the right of each
  figure are his. There is no out-of-sample content of any kind.
- He pre-empts this at [03:29] and [04:11] — "obviously in the moment you don't know what the
  outcome is going to be," "this isn't retrospective hindsight analysis whatsoever" — which is
  **not true of a hand-drawn illustration**. Asserting the absence of hindsight bias while drawing
  both the setup and its resolution is the central methodological problem here.
- **Not one number in twenty minutes.** No win rate, no sample size, no P&L attribution, no base
  rate for any of the twelve patterns.
- Supporting examples are three cherry-picked winners: CAR/Avis, the $10M Nikkei trade, SpaceX
  against 165. No losing example anywhere.
- ⚠ **Course pitch at [06:44]–[07:20]**, mid-video. Notably self-aware in form ("most traders
  should not spend money on trading courses… maybe 1% of you watching are different") — which is a
  more effective sales frame, not a less commercial one. Discount accordingly.
- Appeals to authority for the method at [19:19] (Kyle Williams, Ariel Hernandez) — both peers in
  the same niche, not independent verification.

## 4. Prop-infrastructure dependency

- **Long setups (2a–2d): none.** This is pattern reading. Fully retail-viable as stated.
- ⚠ **Short setups (2e, bouncy ball): yes.** Shorting in-play small caps and recent IPOs is exactly
  where locates, borrow availability and borrow cost bind hardest, and where a prop desk's
  advantage is largest. The pattern may be real and still unreachable retail.
- The **universe** is the softer dependency — "in-play" names require a real-time catalyst/scanner
  workflow, which is closer to infrastructure than to method.

## 5. Decay risk

Moderate-to-high. The setups are generic enough (pullback depth, range contraction, level quality)
that they are unlikely to be *arbitraged* away, but the stated universe — parabolic in-play small
caps and IPOs — is the fastest-decaying niche in the repo. Video is dated 2026-07-25, so the claims
are current; the *behaviour* they rely on is not guaranteed to be.

## 6. What's genuinely sound

The nuances are real distinctions that most pattern definitions omit. The repo's own breakout
scorecard grades **RVOL, ADR, liquidity, trend** — none of which say anything about **pullback
geometry** or **bar-range contraction before the trigger**. On that axis this is new material, and
it is specified tightly enough to code.

The counterparty reasoning is also consistently applied and is the part that most resembles an
actual mechanism rather than a chart superstition: every verdict reduces to "who is trapped, and
does the level force them to act?" That matches the playbook field the KB already recommended
stealing ([remaining-five.md](remaining-five.md), "who's trapped").

## 7. ⭐ Extracted tests — four, all on data already on disk

⚠ **Read [the timeframe problem](../README.md#-the-timeframe-problem--read-this-before-testing-any-setup-here)
first — it now governs every test in this KB, and this video is where it was identified.** In
short: his bars have no fixed interval ([10:33]) and his patterns are specified in **bar counts**,
so a pattern is a property of the *(path, interval)* pair rather than of the path. Every feature
below must be coded in **scale-free / ATR-normalized** form, and a daily-bar null is **not** a
refutation (a daily-bar pass *is* confirmation).

1. **Clean trend → clean counter-trend** (the sharpest claim in the video). Define decline
   cleanliness (R² of log price vs time, or % of bars respecting prior-bar highs on the way down),
   then measure bounce quality after the turn. Prediction: cleanliness of the decline predicts
   cleanliness/size of the counter-trend. **Never tested here in any form.**
2. **Pullback depth + pre-breakout range contraction as breakout-quality gates.** Retracement of
   the prior leg, and ATR of the last N bars ÷ ATR of the leg, as continuous features on forward
   breakout returns. Slots directly into `run_breakout_scorecard.py` as two new graded gates.
3. **"Price acceptance" veto** — bar-range contraction near the lows as a *negative* filter on
   reversal entries.
4. **Bouncy ball** — sequence of lower bounce highs + terminal range contraction → break of
   support. Gives the repo a second mechanical short rule after
   [bollinger-bands.md](bollinger-bands.md).

## 8. ⭐ Direct collision with the crash-leader study — and a cheap synthesis

[`data/studies/crash_leader_reversion_study.md`](../../studies/crash_leader_reversion_study.md)
(2026-08-02) tested buying deep selloffs and found it is **a regime bet, not stock selection**:
the discriminator was *market breadth*, and the shape of the individual decline was never examined
at all. Breitstein is making the exact complementary claim — that **the shape of the decline is the
discriminator** (waterfall good, grind bad, price-acceptance bars fatal) — and says nothing about
regime.

These are not in conflict; they are two independent conditioning variables on the same trade, and
**the event set to test it already exists** (`data/studies/crash_leader_events.parquet`, with the
harness in `run_crash_leader_study.py`). Adding decline-shape features to those events is the
cheapest high-value test the KB has produced so far, because the expensive half is already built.

⚠ Worth stating the risk up front: the crash-leader study found the payoff is tail-carried (mean
excess *excluding* the top 5% of trades is negative). If decline-shape is real, it should show up
as an improvement in the **median**, not the mean. Anything that only lifts the mean is more tail,
not more edge — the same trap the entry-timing variants fell into.

## 9. Conflicts with the rest of the repo

- ⚠ **Against Minervini/Qullamaggie on pullback tolerance.** He rejects a 100% retrace of the prior
  leg outright; VCP explicitly tolerates deep initial contractions provided they tighten. Both
  agree on *tightening into the pivot*, disagree on *how deep the first leg may go*. Do not merge —
  they may simply be different timeframes.
- **With [stops-and-sizing.md](stops-and-sizing.md):** consistent, and supplies the missing
  antecedent — the setup whose bar is "naturally tight against resistance" is defined here.
- **With [no-mans-land-and-process.md](no-mans-land-and-process.md):** consistent and cross-
  referenced by him in-video ([12:41]).
- ⚠ **Note the tension inside his own material:** tight/contracting bars are a *veto* in 2c and the
  *confirmation* in 2e. He explains it by context (who should be defending the level), but as
  stated it is a discretionary joint — and it is the joint that would break first in code.

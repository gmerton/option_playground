# 99% of Traders Don't Know How to Trade with the Trend

**Video:** `ZOHG-OnQuos` · **Type:** talks (solo, ~11:41, 2025-12-20) · **Watched:** 2026-09-19

Solo educational. No guest. His stated goal: "how to define a trend, how to build rules around
trends, and how those rules help you capture massive moves or avoid catastrophic losses" [00:00].

⚠ **Transcript quality:** auto-captions. "VWOP" = VWAP throughout; "Brightstein" = Breitstein;
"heruristic" = heuristic; "Baba" = BABA; "Tory Trades" = a trendline-strategy YouTuber he
cross-promotes [05:26]. Charts are described but not shown in the audio — every example below is
his narration of a chart I have not seen.

## Raw notes

**Origin story / evidence base [00:31–01:25].** He reviewed "every trade of my career… a deep
forensic dissection of my entire body of work" and found "my best trades were with the trend, and
they worked immediately. My biggest losses all came from fighting the trend." Then the load-bearing
claim: *"your best trades tend to quickly work in your favor. That's not hindsight. That is a
repeatable heuristic."* ⚠ It is derived from his own trade log, which is exactly the class of
evidence this repo discounts by house rule (`feedback_gabes_trades_are_not_evidence`). The rule
applies symmetrically — a P&L log tells you about execution and conformance, not about whether the
conditional distribution supports the heuristic.

**Definition [02:15–02:46].** Trend = slope. Uptrend = positive, downtrend = negative, rangebound =
zero. Veto attached: "Most traders bleed themselves dry trading rangebound stocks because they
haven't defined a trend yet. They keep taking small losses instead of waiting for a breakout."

**Six ways he says he defines a trend** (this is the actual content of the video):

| # | definition | ref | testable on daily bars? |
|---|---|---|---|
| 1 | slope / higher highs + higher lows "stairstep structure" | [03:06–03:39] SPY legs 48→64→53, then retest-highs/higher-low ×3 | yes |
| 2 | shallow pullbacks + continuous legs | [03:47] NVDA pre-earnings; "I knew traders who were shorting it into earnings. That's insanity" | yes (pullback depth ÷ prior leg) |
| 3 | holding VWAP | [04:07–04:26] NVDA intraday held above VWAP all day | no — intraday only |
| 4 | holding a moving average | [04:26–04:37] FSLR 1-yr weekly, 20-period MA | yes |
| 5 | holding a trendline | [05:07–05:26] Bank of Hawaii held a trendline all morning; on the break "the counter trend is in… There was no reason to be long prior to that" | ⚠ hand-drawn anchor = discretionary |
| 6 | ⭐ **reference price** — "the unaffected price before a catalyst" | [05:35–05:56] AMD intraday news, unaffected price $83.50: above = news read positively, below = "something is off" | yes, if the pre-catalyst close is the anchor |

**Prior-bar trailing stop [04:37–05:07].** FRC breaking down: "we hold prior bar highs in what would
be considered a very aggressive downtrend. If I'm trying to catch trends as part of my playbook,
especially on stocks that are hyper in play, **prior bars is a very common trailing stop that I
use**." → this is the harness's existing `trail_bar` arm.

**Multi-timeframe alignment [05:56–06:37].** TSLA 2021: $300 resistance, two higher lows, retest,
break on an earnings catalyst = weekly breakout + daily breakout + intraday breakout + catalyst.
"the trends were aligning." Exit framing: "Even if you're using the weekly chart, you are catching
a solid chunk of that move using our prior bar lows to get out."

**⭐ The counter-trend rule [06:47–07:30]** — the one genuinely operational entry in the video. GME
28 Jan 2021: "Where this gets scary is if you're buying and averaging down as it goes lower. If you
buy $210 thinking this is overextended, guess what? We just went another 100 points… **So, the key
is to wait for the counter trend. I would define that here as the break of prior bar highs.** So I
would be buying in this bar if possible." Payoff claim: "When I started to wait for the counter
trend, I stopped drawing down significantly. That is one of the first things that transformed my
big losses into big gainers."

**⭐ The VWAP veto [08:00–08:32]**, credited jointly to "Kenny at SMB Capital": "we never want to be
long a stock if it's steadily holding below VWAP **unless it capitulates**. and vice versa. I never
want to be short a stock above VWAP unless it capitulates." He then names the discretionary joint
himself: "The nuance behind these rules is you have to define everything. What does capitulation
mean to you."

**How trends start [08:52–09:31].** Breaking news / fundamental catalyst; break of a consolidation
or range; and the participant-alignment argument — momentum traders buying, institutions buying,
"shorts that have stops at $300 thinking, oh my god I need to cover" → "Every single person, small
or large, is on your side."

**How trends end [09:31–10:40].** (a) "huge volume and price exhaustion that are capitulatory
signals… Those are my favorite signals to the end of a trend"; (b) multiple legs in one direction,
"the larger the legs are, especially if they accelerate in size, it becomes increasingly likely the
trend will end"; (c) a counter catalyst; (d) **absence of consolidation** — "Consolidation is
considered price acceptance where people find a little equilibrium and where price is agreed upon."
BABA on the Xi re-election: the flush printed a volume bar that was "multiples of any volume we had
done previously on the year" = peak pessimism = the foundation to counter-trend higher.

**Homework, ×3 [07:30, 08:32, 10:40, 10:59].** Write down your own trend definitions, your rules for
trending vs rangebound, and your begin/end criteria — "documenting it with actual charts and
writeups… Document, document, document."

## Named setups appearing here

- [x] **Counter-trend long after a flush** — trigger *and* invalidation both implicit: enter on the
      break of prior bar highs, and the flush low is the only place a stop can live. Promoted →
      `principles/trend-definition-and-counter-trend-entry.md`.
- [x] **VWAP directional veto** (with its own invalidation: "unless it capitulates") — same file,
      intraday arm.
- [ ] **Reference price** (unaffected pre-catalyst price as the intraday trend anchor) — new to this
      KB. Not promoted: needs intraday bars plus a news timestamp we do not have.
- [ ] **Prior-bar trailing stop** — already covered by `stops-and-sizing.md`; it is the `trail_bar`
      arm in the harness.

## Claims to verify

- [ ] **"Best trades work immediately"** [01:15]. Directly checkable two ways: (a) on
      `journal_trades`, time-to-favourable-excursion vs final P&L; (b) on the panel, MFE within the
      first session vs the 5-day R. ⚠ Beware the mechanical confound: a trade that works immediately
      has a wider cushion against the stop by construction, so *some* of this is arithmetic, not
      selection.
- [ ] **"Most traders bleed themselves dry trading rangebound stocks"** [02:36]. The range-vs-trend
      split is a one-line conditioning on ADX or on (close − ema20)/ADR; the repo has never cut the
      breakout book that way.
- [ ] **Prior-bar-low trail vs the 20 EMA trail.** Both are harness arms (`trail_bar`, `ema20`). Our
      own precision-tier breakout best arm was the **ema20 trail at +0.79R**; his claim is the
      prior-bar trail. Free comparison, already instrumented.
- [ ] **"$100M+ in verified profits", 8-figure/yr** [00:10]. Unverifiable; stated as credential.
- [ ] Every chart named (SPY, NVDA, FSLR, FRC, Bank of Hawaii, TSLA 2021, GME, BABA) is a winner
      chosen after the fact. Zero base rates, zero counts, zero failures shown.

## Quotable rules

- [01:15] "Your best trades tend to quickly work in your favor. That's not hindsight. That is a repeatable heuristic."
- [04:58] "Prior bars is a very common trailing stop that I use."
- [05:35] "You also have what I call reference prices. The unaffected price before a catalyst."
- [07:19] "The key is to wait for the counter trend. I would define that here as the break of prior bar highs."
- [08:07] "We never want to be long a stock if it's steadily holding below VWAP unless it capitulates. And vice versa."
- [10:01] "The larger the legs are, especially if they accelerate in size, it becomes increasingly likely the trend will end."
- [10:07] "Consolidation is considered price acceptance where people find a little equilibrium and where price is agreed upon."

## Reactions / conflicts

**⭐ Agrees with the repo, and the repo is more precise than he is.** "Don't fight the trend" is the
qualitative version of two rules already quantified here: the rotation study's **veto below the 200
SMA or with a 6-month return < −10%**, and the long-call study's winning cell — **0.3–1 ADR above a
*rising* 21 EMA**. Note what he never supplies: *how far above the trend is too far*. That number is
ours, not his, and it is the confirmed leak in the August book — **entries 1–2 ADR above the 21 EMA**
(which look "not extended" on a chart) were the losing cohort, while ≤1 ADR was roughly flat. His
[10:01] "accelerating legs mean the trend is ending" gestures at exactly this and stops one step
short of the measurement.

**⚠ His counter-trend long is the mirror image of a pattern this repo has already killed.** The
bouncy-ball short (break of prior bar *lows* after progressively lower bounces) was tested
2026-09-18 on both timeframes and failed badly: daily **−0.34R vs a same-name control of +0.34 to
+0.48R (t −4.3)**, intraday **−0.41R (t −10.9, 18% win)**. That is not a refutation of the long side —
different side, different regime — but it sets the prior hard: *the prior-bar-break trigger family
has now failed in two of two tests.* The long version is the obvious next ledger row and is specced
in the principles file.

**⚠ Collides with Stage A.** Five of his six trend definitions resolve to "price crossed a line"
(prior bar, MA, trendline, VWAP, reference price). Stage A tested exactly that family intraday —
11,227 fires across unfilled-gap reclaim, ORB-above-9-EMA and level breaks — and **every arm came in
at −0.10 to −0.13R, losing to a random entry in the same name-day**. Per the README's timeframe
rule this is not a refutation of *his* version (his bars have no fixed interval, and he adds
in-play selection that our detectors did not), but the burden of proof sits on his side of the table
now.

**✅ Third independent statement of the price-acceptance veto.** [10:07] is the same idea as
`setup-grading-chart-nuance.md` ("tight bars at the lows = buyers absent = no play") and
`no-mans-land-and-process.md`. Three separate videos, one concept, consistently stated — that is
about as much internal corroboration as this corpus offers.

**⚠ Evidence standard.** The whole video rests on a retrospective review of his own trade log plus
eight hand-picked winning charts. He asserts "that's not hindsight" [01:20] about a conclusion drawn
from known outcomes. By the repo's own rule, that is a hypothesis generator, not evidence — and the
rule cuts the same way against his log as against Gabe's.

**Rating: 2.5/5** (clean, well-organised taxonomy and two genuinely operational rules — the
counter-trend entry and the VWAP veto, both stated *with* their invalidation, which is what this KB
values most. Marked down hard for: zero numbers, eight cherry-picked winners, a self-log evidence
base explicitly labelled "not hindsight", and a mechanical core — the prior-bar break — that this
repo's ledger has already failed twice.)

**Course-marketing content present: yes** — subscribe plug at [02:06] ("over 50% of you watching
this are not subscribed"), a cross-promo to his own trendline video at [05:26], and the Magnum Opus
pitch at [11:19] ("the exact material used by trading firms around the world").

# OptionsPlay — "The ONLY #1 Options Strategy You May Need with Tom Sosnoff"

**Score: 3 / 5.** Reviewed 2026-09-22. Video `pQlGgcyrUoQ`, published 2024-10-14, recorded Thu 2024-10-10,
60:04, 157k views. Host **Tony Zhang** (OptionsPlay chief strategist); guests **Tom Sosnoff** (tastytrade) and
**Brian Overby** (OptionsPlay senior options strategist). Transcript and timestamped claim ledger:
[`videos/2024-10-14_pQlGgcyrUoQ/`](videos/2024-10-14_pQlGgcyrUoQ/notes.md).

⚠ **Caption trap for this channel:** the default `en` auto-caption track is a machine *translation* (round-tripped,
apparently via the Russian dub) — thinkorswim becomes "Thinker Swim", "gamma explosions" become "gamma-ray bursts",
"chip in a chair" becomes "chip on the chair". Pull `en-orig`. Both tracks are archived; only `en-orig` is quotable.

---

## The "#1 strategy", stated precisely

Sosnoff's, in his own construction:

> Sell a **strangle** at **~45 DTE**, strikes **just outside the expected move (~20 delta a side)**, skewed
> slightly if he has a lean; only in **highly liquid** underlyings with a **high IV rank**; **small size spread
> across many names** (70–80 equities/ETFs/indexes plus 10–12 futures products); **manage at 21 DTE** and roll to
> the next cycle; and as a standing default, **take the profit early** whenever the decision is a close call.

Around it: 75% undefined risk / 25% defined (the defined quarter is iron condors and short verticals); explicit
carve-outs for **volatility underlyings and biotechs**; the same rule applied unchanged to futures options; and
roughly **100 trades a day**.

Overby's answer is a different trade: a short-dated directional **skip-strike butterfly** (5 days on SPX, 18 days
on VIX), placed for a net credit where possible so the hedge is embedded before entry, with one adjustment — roll
the most expensive leg into a short vertical when wrong.

### Verdict on the strategy

**Untested by us as specified, and the nearest things we have read NULL.** The closest read is the short 7-DTE ATM
straddle, 41,757 trades across 317 names: **−1.83% at mid, before costs**; the high-IV cell is +3.19% with a 95%
CI of [−2.86, +8.57], and every positive cell's CI includes zero. Tenor is different, so this is evidence about
the family, not a refutation of the rule.

⚠ **The important caveat is about us, not him.** The one time we did build his actual structure — an IV-percentile
gated 0.25Δ ~20 DTE short strangle — the run printed **94–99% win rates and 86–100% ROC including 2020 and 2022
with zero stops**, and was then **invalidated**: median mark coverage was 14.3%, so with no path the engine booked
`expiry_win` at full credit. Return was a pure function of coverage. That is worth stating plainly, because
**the flattering shape this strategy family produces in a naive backtest is exactly the shape our own broken run
produced.** Anyone who reports that a 45/20Δ strangle wins 90-plus percent of the time — including tastytrade —
owes a path-coverage number before the win rate means anything.

Against the standards named in the brief: **no track record is offered, so the rule is a hypothesis**; it is
argued entirely at the mid except for one wrong cost claim; and the one place he quantifies success, he quantifies
it as **probability of profit**, which he then correctly says is not edge.

---

## ⭐ 1. Does an hour of the same man, unclipped, hold up better than the 26 clips?

**Yes on specification. No on evidence — and the second half is the finding.**

**Specification improves enormously.** Twenty-six clips produced opinions; one hour produces a complete, executable
rule set — instrument, filter, tenor, strike, size, management, exit — plus a live trade with real strikes, real
prices and a real date. The clip ledger could not have been traded from. This can.

Three ledger claims move once the context comes back:

| clip claim | what the long form actually says |
|---|---|
| "There's no such thing as a trend; I fade trends" | ⭐ **Materially wrong about his own book.** His trade is **delta-neutral** and he explicitly declines to forecast: *"I'm not necessarily right more than I'm wrong when I'm guessing market direction."* He is not fading trends; he is refusing to have a view. The clip inverted a humility claim into a directional one |
| "Outlier risk is managed by position size only" | **Incomplete.** Size **and** the 21-DTE truncation, which he calls the mechanism that "virtually eliminates your outlier risk" because the tail lives in the last week or two |
| "I haven't bought premium in 26 years" / never buy short-dated calls | **Qualified.** He is 75/25 undefined/defined; the defined quarter (iron condors) *requires* buying wings, and he demos exactly that. He also excludes vol products and biotechs entirely — a carve-out no clip carried |

So the More Tom criticism that **context belongs to the editor** is vindicated: two of six ledger claims changed
meaning, one of them completely.

**Evidence does not improve at all.** The hour is not short of numbers — but sort them and every one is either
(a) a live platform readout (IV rank 82.3, IV ~70, expected move $14.30, POP 82%, CVaR ~$7k), (b) a
market-structure factoid (retail derivatives 8% → dominant; ~50% of volume now ≤7 DTE), or (c) an **unsourced
appeal to the think tank** — "hundreds of thousands of hours over 14 years", "18 months of zero-day data",
results that are "incredibly different". Across sixty minutes there is **not one sample size, not one
distribution, not one confidence interval, not one P&L, and not one statistic attached to any of his five
rules.** The flagship 21-DTE rule — the single most propagated idea his firm has produced — is introduced with
the words *"this is basically a theoretical discussion."* The only counted statistic in the hour is a defensive
one, offered to correct his co-panelist: 14 of the last 26 October expirations up, 12 down.

⟹ **The absence of evidence is intrinsic to how he argues, not an artifact of clipping.** Given an hour, his own
platform, a research department and a friendly host, he cites no result. The More Tom 2.5 was therefore *unfair
to him on specification* and *exactly right on evidence*. That is a real finding and it should change how this
KB treats him: stop discounting his rules for being clipped, keep discounting them for being unevidenced.

---

## ⭐ 2. The credit/width collision — this KB's own best finding, denied on air, unchallenged

At **53:05–57:23** Sosnoff wings a strangle into an iron condor live and narrates the trade-off: POP 82 → ~67,
CVaR $7,000 → $500, max profit roughly halves, *"so your return on capital goes significantly higher."* That is
credit/width reasoning in ROC form. He then draws the general conclusion:

> Options are "symmetrically perfect" on risk and return — put-call parity plus efficient pricing mean every
> dollar at risk is the same. *"There's no theoretical difference with respect to edge of doing this tight iron
> condor versus that really wide strangle. The difference is in your probabilistic outcome and your risk/reward
> ratio, that's it."*

**Our data splits this claim cleanly in half, and both halves are informative.**

**Within one name he is right, and we paid to learn it.** ARM B of the premium-to-width test: dialling credit/width
with your own wing does nothing — net ROC non-monotone, realised win tracking break-even within 0.5–3pp. Inside
the certified index cell the sort actually **inverts** (high−low **−10.14pp, t −1.23**; the cheapest tercile won
at 100%). A creator claim that matches one of our nulls, reached from theory rather than data, is worth
recording — it is the same conclusion for the same reason (put-call parity, efficient pricing within a liquid
name), and it is *why* our ARM B was always going to be null.

**Across names he is wrong, and the refutation came from this very channel.** OptionsPlay's own 2026-07-25 video
gave us the only published filter that has ever survived our data: at a fixed 30Δ/20Δ structure, quintiles of
credit/width sort net ROC **−2.96% → +4.07%, top−bottom +8.57pp, t 3.74**, both halves; **within-date +7.64pp,
t 4.15**; holding in low-VIX (+9.17) and high-VIX (+7.84) terciles, so it is name selection and not regime
timing. Šidák p 0.00037 against a BH rank-1 line of 0.00038 — it passed by a hair, and it passed.

⟹ **Neither party notices there are two axes.** Sosnoff generalises a true within-name statement into a false
cross-name one. Tony Zhang — whose own firm's material produced the cross-sectional ranker — lets it stand
without a word. And the structure Sosnoff actually runs contains the contradiction in miniature: he says no
structure has an edge over another, then selects across names by **IV rank**, which is a claim that some names
are richer than others. He is running a cross-sectional premium-richness filter while denying cross-sectional
premium richness exists. Our finding is that he is right to run the filter and wrong about why, and that
**credit/width is the better-measured version of what IV rank is groping for** — its mechanism is entry IV
(0.25 → 0.48 across quintiles).

He also gets the corollary right where others get it wrong. Tony puts it squarely — an 82%-POP trade is no better
than a 49%-POP trade — and Sosnoff confirms it. That is the exact error that caps SMB at 2/5. ⚠ Our data is
**stronger than his**: he says the two are equal; across credit/width quintiles win rate **falls 79.6 → 75.7**
while net ROC **rises −2.96 → +4.07 (t 3.74)**. The lower-probability side is not equal, it is better.

---

## ⭐ 3. The futures book — the hour does not deliver it, but it reduces the question

This is the arena where his central claim is untested rather than refuted, so it was the most valuable thing the
video could have contained. **It is not in here.** What we get is three sentences: he uses *"the same exact
strategies in futures options as well"*; he trades roughly **10–12 futures products**; crude oil is at a **99% IV
rank** as he speaks. No futures-specific tenor, delta, sizing, margin treatment, or rationale for futures over
equities. He then steers the demo *away* from futures deliberately — equities, *"because these you can get a
little smaller on"* — a quiet admission that futures option size is lumpy for a retail audience, and the closest
thing to a reason anyone gives.

**The useful residue is a reduction, not an answer.** Because he states the rule is *identical*, the futures
question is no longer "what does he do differently in crude and gold?" — there is nothing to discover. It is
purely: **does the same 45-DTE / 20Δ / high-IV-rank strangle pay better in CL and GC than in equities, once
fills are real?** The liquidity objection that sinks our single-name premium selling (costs = 136% of gross)
plausibly does not bind there, and that is the whole hypothesis.

⛔ We still cannot test it — we have no futures options data, and nothing in this hour justifies funding any.
The More Tom position stands unchanged: **this is a limit on our evidence, not a verdict on his.**

---

## ⭐ 4. The demonstrated trade, audited

He puts on a live TSLA strangle and invites the audit, so here it is. This is the only checkable claim in the
video and it is worth more than the other fifty-nine minutes.

**Entry, 2024-10-10, TSLA 238.77**, IV rank 82.3, IV ~70. One-day expected move **$14.30** (We,Robot robotaxi
event that night). November cycle, 36 DTE, 36-day expected move **$36–37**. He sells roughly **2× the expected
move** on both sides: the **170 puts** ($70 OTM) and the **350 calls** ($111 OTM), priced at about the same
$1.35 because, as he explains correctly, the skew says the *velocity* of risk is upside. Delta-neutral, POP 82%,
CVaR ≈ $7k. His stated thesis: *"I'm hoping the Tesla news is kind of a non-event and it stays inside the
expected move of $14."* (ASR garbles the credit; the strikes and deltas are reliable.)

What happened:

| date | TSLA | |
|---|---|---|
| 2024-10-11 | **217.80** (−8.8%) | the robotaxi event disappointed. The overnight move was **−$20.97 = 1.47× his stated expected move.** The thesis he named failed on the first session |
| 2024-10-24 | **260.48** (+21.9%) | ⚠ **Q3 earnings, 2024-10-23 — a second binary event he never mentions, and which he had just placed inside the cycle** |
| 2024-10-25 (**≈21 DTE**) | **269.19** | his own management date. Both strikes far away, both events spent, IV crushed — a clean, profitable roll |
| 2024-11-11 | high **358.64**, close **350.00** | ⚠ **the short call strike, touched and closed exactly on it, with 4 DTE and maximum gamma** |
| 2024-11-15 (expiry) | **320.72** | both strikes expire worthless — a full-credit win, after a terrifying path |

**Read it honestly and it cuts three ways.**

1. ✅ **His management rule is the hero, and this is the best argument in the video** — an argument he never makes
   because he does not know yet. The 21-DTE exit harvests the trade cleanly on 2024-10-25, two weeks before the
   melt-up that touched the short strike. Held to expiry it also wins, but only via an excursion to $358.64 that
   would have been unholdable at size. **This is precisely the case the rule is designed for**, and it is n=1.
2. ❌ **His stated edge was wrong twice.** The event moved 1.47× the expected move, and his skew reading — which
   was *correct* — identified the side that later blew through. Being right about the skew did not help, because
   he sold that side anyway.
3. ⚠ **A real specification gap in a live demo.** He frames this as one binary event and sizes to one, while
   selecting a cycle containing Tesla's Q3 earnings. The +21.9% earnings day is what launched the stock toward
   his call strike. Nothing in his stated rule checks the calendar inside the tenor.

And the structural point: **this is an earnings/binary-event premium sale, the cell our earnings ledger closed.**
The vol premium there is real at mid (+0.601%) and **−0.428% at the bid**, with costs at **171% of gross**. He is
demonstrating the exact trade our own work says does not survive fills.

---

## ⚠ Commercial alignment, and the one genuinely dangerous claim

Sosnoff owns the brokerage; OptionsPlay runs the affiliate link; the webinar closes on a QR code and a funded-account
bonus. Both parties are paid by the same action, and a cluster of his advice points at it: *"the default is always
to take the profit"*, *"the more times you do something the better you get"*, *"the quicker you process stuff the
quicker you redeploy"*, ~100 trades a day. Every one of those is order flow.

The claim that makes it work is the cost claim, and it is the most dangerous sentence in the hour:

> *"The markets today, if you're trading liquid underlyings, are so efficient that you're only giving up a penny
> or two."*

Measured, on our own quotes: straddle spreads run a **median 6.5% of mid**. A penny or two on the $1.35 option he
is actually trading is **1–1.5% per leg** — call it 3–6% round trip on a four-legged condor, before commissions,
on a trade whose whole thesis is that you do it hundreds of times a year. The 2026-09-22 cost sweep killed nine
mid-priced strategies on exactly this gap; UVIX went from +11.0% and a 93% win rate at mid to **−8.8% and 46% at
fills**. "A penny or two" is the arithmetic that makes high-frequency management look free, and it is the single
point where his commercial interest and his analysis coincide most exactly.

⚠ **Second unreconciled contradiction:** he argues that trading many small occurrences makes the law of large
numbers work for you, and thirty minutes later that no structure carries an edge over another. Both cannot be
load-bearing. n only helps when per-occurrence edge is positive; with costs and no edge, more occurrences is a
faster loss. Our own book runs the other way — the size lever that works is **exclusion** (A+B only, +0.29R OOS
vs flat 0.00), not spreading thin.

---

## Where he agrees with results we paid for

* **Liquidity first, always.** Our hardest-won result. Credit/width discriminates within a liquid universe and not
  within a bad one — the rescue test salvaged 2 of 15 retired names, and every junk name stayed negative even in
  its rich half.
* **Vol products and biotechs excluded from premium selling.** Exactly our retirements: UVXY −3.5%/trade (t −2.65),
  UVIX −8.8% (t −2.81), neither rescued by credit/width.
* **7 DTE and in has a much lower success rate for individual investors** — volunteered against his own platform's
  interest. Our 1-DTE straddle study found no edge and every exit ≈ −30% of premium; short-dated single-name
  selling costs **136% of gross**; Stage A found every intraday arm −0.10…−0.13R across 11,227 alerts.
* **POP is not edge.** The SMB error, corrected.
* **Within one name, structure choice carries no edge** — our ARM B null, reached from put-call parity.
* **Skew is a velocity statement, not a probability statement.** Clean, and better than most creator explanations.
  (As a *signal* it is null for us: skew t −1.22 against vix_pct t **+6.54** jointly.)
* **He does not claim to forecast direction.** *"I'm not necessarily right more than I'm wrong."* Our book keeps
  confirming the same thing against its own interest.
* **October is not the most volatile month** — offered to correct his co-panelist, with a count.

## Contradicted or unsupported

* **"No theoretical difference with respect to edge"** — false across names: credit/width +8.57pp, t 3.74.
* **"A penny or two"** — see above.
* **Law of large numbers as a standalone justification** — incoherent alongside the no-edge claim.
* **Overby's adjustment rule** (flip the losing butterfly into a short vertical in the direction that just hurt
  you, "following the trend") — no evidence offered; adjacent to our roll test, where **69.8% of the breach cohort
  did better held** and the stop cost −9.51pp, and to the NULL pyramid.
* **Overby's VIX Sept/Oct seasonality** — unsourced, and partly refuted on air by his co-panelist.
* **The VIX butterfly anecdote** — n=1, winners-only, no P&L. Discounted entirely, per house rule on testimonials.

---

## Why 3 and not 2.5 or 3.5

**Above the More Tom 2.5** because the long form does three things the clips never could: it specifies a complete,
executable strategy; it puts a real, dated, checkable trade on the screen and invites the audit; and it gets two
genuinely hard things right — POP is not edge, and within-name structure choice carries no edge — both of which
we confirmed with paid compute, and one of which (POP ≠ edge) is the error that caps several creators at 2/5.
Nothing on the strategy side of his half is contradicted by our data; the disagreements are about scope.

**Below this KB's 3.5 record** because after sixty minutes with a think tank behind him and his own platform open,
there is still **not one test statistic attached to any rule he gives**; the flagship 21-DTE rule is explicitly
offered as theory; the cost claim is wrong in precisely the direction that sells brokerage; the no-edge /
law-of-large-numbers contradiction is never reconciled; and the trade he chose to demonstrate is the
earnings-premium cell our own ledger closed after fills. Overby's half is materially weaker than Sosnoff's — an
n=1 winners-only anecdote, an unsourced seasonality claim and an unevidenced reversal rule — and drags the video
down. Scored separately: **Sosnoff 3.5, Overby 2, host 3** (Tony Zhang asks the right questions and lets the one
answer his own firm could have refuted go by).

---

## Testable here?

Two items recommended, both cheap, both pre-registerable. Everything else declined.

### ⭐ Q1 — IV rank vs credit/width as the cross-sectional short-premium selector · RECOMMENDED

**Why:** his single cross-sectional filter is IV rank; ours is credit/width. IV rank is the industry-standard
screen (every tastytrade and OptionsPlay selector uses it), and this is the head-to-head that says whether our
adopted filter is actually better or merely differently packaged. We have measured IV rank only at the *low* end,
for the long straddle, where range-based IV rank **lost to rank-percentile at every threshold** (rank ≤20 +6.85
vs pct ≤20 +9.19) and OptionsPlay's own 33 line was inert. His use is the high end, for selling — a different
test we have never run.

**Test:** reuse `run_premium_to_width.py` exactly — 20-name liquid panel, 395 Fridays, structure fixed at
30Δ/20Δ, real fills, held to expiry. Add IV rank (52-week range definition, his) as a competing sort. Report
marginal quintiles for each, the double sort, and a joint regression of net ROC on credit/width and IV rank.
Pre-register the primary as the IV-rank top−bottom spread and its t.

**Prior:** credit/width wins and largely subsumes IV rank. Credit/width's mechanism is already entry IV
(0.25 → 0.48 across quintiles), so IV rank should carry a similar signal more noisily — it is own-history-relative
and therefore not comparable in units across names, which is the specific defect credit/width does not have.
Guess: IV rank top−bottom positive but around t 1.5–2.5, and insignificant once credit/width is in the regression.
⚠ If IV rank wins, that matters a lot: it is computable without a chain.

**Cost:** ~half a day. The pool, the fills and the harness all exist.

### Q2 — the 21-DTE management rule · RECOMMENDED BUT BLOCKED

**Why:** the single most propagated rule tastytrade has produced, it is untested by us, and it is the one exit
mechanism our existing exit results may not cover. Every non-size tail management we have tried **inverted** —
the straddle −50% stop is a cost (+6.73% unstopped vs +2.89%), BE+1R −0.08R, "extended → tighten" −0.19R
(t −2.8), the 10-EMA trail −0.47R (t −4.8). But all of those remove **losers**. The 21-DTE roll removes **gamma
symmetrically**, at a fixed date, regardless of P&L. That is a different mechanism, and it is exactly where our
"don't manage" result might fail to generalise. The TSLA audit above is one favourable anecdote for it.

**Test:** 45-DTE ~20Δ short strangles on the liquid panel, real fills both ends, paired by entry date and name.
Arms: hold to expiry · close at 21 DTE · close at 50% of max credit · close at 21 DTE **or** 50%, whichever first.
Primary = the 21-DTE arm minus hold-to-expiry, month-clustered t.

⛔ **Blocked, and this is the point of the entry.** A 21-DTE-exit test is *entirely* a path question, which makes
it maximally exposed to the bug that invalidated `run_iv_condor_study.py`: median mark coverage **14.3%**, 67% of
trades under 25%, no trade above 75%, and with no path the engine books `expiry_win` at full credit — producing
the 94–99% win rates that made the strategy look wonderful. **Do not run this until the min-coverage guard exists
and coverage at 45-DTE 20Δ strikes is measured and reported alongside the result.** Running it before then will
manufacture a confirmation of exactly the claim under test.

**Prior:** genuinely uncertain, which is why it is worth compute. Lean slightly toward a small positive for the
21-DTE arm on *risk* (drawdown, worst trade) and roughly flat on mean return — i.e. the rule buys path, not edge,
which is close to what he actually claims.

### Declined

* **Overby's VIX Sept/Oct seasonality** — his co-panelist half-refuted the adjacent version on air, our August
  2026 retrospective found every trailing-30d seasonal rule fails 2019–26, and a VIX-level calendar effect is a
  regime bet rather than a trade.
* **The skip-strike butterfly** — butterflies are the structure family the calendar/path erratum burned us on,
  evaluation is entirely path-dependent (see Q2's blocker), and the motivation is one winners-only anecdote.
* **The "flip the loser into a short vertical, following the trend" adjustment** — no evidence offered, and it is
  adjacent to two settled results (roll test: 69.8% better held; pyramid: NULL).
* **0DTE "manage before noon"** — Stage A settled the intraday-trigger question across 11,227 alerts, and the
  1-DTE straddle study found every exit ≈ −30% of premium. Already answered in spirit.
* **Futures strangles** — cannot be tested; we have no futures options data and nothing here justifies buying
  any. Stands as a documented limit on our evidence.

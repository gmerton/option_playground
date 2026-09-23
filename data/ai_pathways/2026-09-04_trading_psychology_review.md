# Review: "Which Trading Psychology Concepts Actually Work? (Tested With Claude)" (AI Pathways, Brendan, 2026-09-04, 9rBgnMnDp_0) — 2.5/5

Reviewed 2026-09-22. 23:11, 6.4k views. Funnels to the same paid Skool community; the last ~2 minutes are four
copy-paste Claude prompts. Transcript: `videos/education/2026-09-04_9rBgnMnDp_0/`.

**Third video from this channel in the KB.** Chronology matters and it is not the one the arc suggested:

| | June (nLQhKkjkuWI) | August (KML09tRtHM8) | **September (this)** |
|---|---|---|---|
| score | 2/5 | 3/5 | **2.5/5** |
| market data | daily bars, 30 assets, 15 yrs | 16 yrs 1-min NQ + ES | **none at all** |
| null / control | ✗ | coin flip, same risk | paired same-stream control ✓ |
| multiple-testing correction | ✗ | luck correction in the funnel ✓ | **✗ (83 concepts, uncorrected)** |
| sealed holdout | ✗ | 2 yrs locked, run once ✓ | **✗ (a second Monte Carlo draw)** |
| second market / instrument | n/a | ES cold ✓ | **n/a — no instrument exists** |
| costs | ✗ | commission + stop slippage ✓ | one 3× sensitivity only |

**Answer to the tracking question: the rig regressed.** Two of the three guardrails that earned the August video
its 3 — the multiple-testing correction and the sealed holdout — are gone. The third (a null) survives in a
better form: every rule is scored against the *identical trade stream in the identical order* with the rule
switched off, which is a properly paired control and is the single best thing in the video. But it is a paired
control on a **fictional** stream. August tested claims against the market. September tests claims against a
random number generator that Brendan specified.

That is not a small distinction. It is the whole review.

---

## What was actually done

83 psychology concepts were scraped from popular videos and sorted by testability [03:20]. The ones that survived
were turned into mechanical actions — *stand down, size up, size down, skip the next one, stop for the day* —
on the explicit and, in isolation, correct premise that **you cannot test a feeling, only the action attached to
it** [01:17]. Because those actions are strategy-agnostic, Brendan concludes he needs no strategy at all
[01:48], and generates a synthetic stream instead:

> 37% win rate · $500 risk/trade (1% of a $50,000 account) · "about $50 a trade" expectancy · 750 trades/year ·
> 10,000 simulated years.

One free parameter is layered on top: **streakiness**, i.e. injected autocorrelation in the win/loss stream
[03:04]. Its magnitude is never stated. Results are reported at "no streakiness" and "streaky", and the sign of
the headline result flips between them.

### Their generator reproduces every headline number exactly

Solve 0.37·W − 0.63·$500 = $50 → **W = $986 ≈ 1.97R**. From that alone, with no simulation:

| their claim | plain arithmetic | ✓ |
|---|---|---|
| "10 losses in a row happens in 94% of years" | 1 − exp(−750·0.37·0.63¹⁰) = **93.5%** | ✓ |
| "the median losing streak inside a year is 12" | ln(750·0.37)/ln(1/0.63) = **12.2** | ✓ |
| "you don't know your edge until ~800 trades" | σ/trade = $718, Sharpe/trade 0.0697 → n for **t = 2 is 824** | ✓ |
| "hesitation costs ~$600 per 1% of the year skipped — it's a straight line" | slope = annual profit ÷ 100 | ✓ |
| revenge trader's "average size ≈ 3.5× normal" | martingale **capped at 3 doublings** → E = 3.42× | ✓ (see below) |

This is the indictment and the compliment at once. The arithmetic is right — I could not find an error in the
numbers themselves — but *the arithmetic is all there is*. The 10,000 simulated years recover the closed form of
the model that was typed in. Nothing about markets, traders or psychology entered anywhere.

---

## The structural problem: the generator decides the answer before the test runs

The stream is i.i.d. (or i.i.d.-plus-a-knob) and **positive expectancy on every single trade by construction**.
Under that assumption, by linearity of expectation:

- **any rule that removes trades must lose money** — hesitation (−$17k), the green-day profit target (−$15k),
  stand-down-after-2 in the calm case (−$8,442), capping trades per day, being picky;
- **any rule that adds size must make money** — revenge doubling (+$60k), sizing A+ setups (+$32k);
- **any rule that only changes *when* you size, without changing *how much* on average, must be exactly zero** —
  which is precisely the "sizing up after a hot streak does nothing" null [15:30].

All three "discoveries" are `E[Σ] = n · EV` wearing three different costumes. The straight line in the
hesitation chart is the tell: a genuine behavioural finding would not be linear through the origin with slope
equal to per-trade expectancy. Brendan half-sees this — he says out loud that the revenge money "isn't coming
from revenge trading, it's just trading 3.5× bigger" [06:29] and that the skipping rules only help a losing
trader "by making you trade less" [11:40] — but does not take the next step and notice that the same collapse
voids most of the rest of the video.

**Only one lever in the whole design can change a sign: streakiness.** If losses cluster, the trade after a loss
really is worse than average and skipping it buys something. That is a real, empirical, answerable question about
a real trader's real log — and it is the one quantity the video does not measure. It is set by hand, off-screen,
and then read back out. **The headline tilt result is a knob-reading, not a measurement.** To his credit Brendan
says as much: "this is something that wouldn't be measured unless you yourself know how streaky you are" [09:10].
That sentence is an admission that the video cannot answer its own headline question.

### On the operationalization (the thing to interrogate hardest here)

Judged as operationalization rather than as evidence, the framing is **better than average for the genre**:

- "test the action, not the feeling" [01:17] is the correct move and is exactly what we do with creator claims;
- the actions chosen (stand down after k losses, skip the next setup, stop at a target, size up after wins) are
  the right mechanical shadows of tilt / fear / greed / overconfidence;
- the control is paired on the identical stream in the identical order, which is stronger than most creator work
  and stronger than the June video.

But three of the concepts are **silently substituted**, and these are the ones to be suspicious of:

1. **"Revenge trading" → a capped martingale.** See below. The behavioural claim is about *impaired judgement*
   after a loss — worse setups, wider stops, chasing. What is tested is a size schedule applied to an
   *unimpaired* stream. By construction the revenge trader's trades are exactly as good as anyone else's, so
   the entire behavioural content of the concept is assumed away before the test starts.
2. **"Be picky / take better trades" → a synthetic grading oracle.** The trader is handed a noisy ability to
   read a setup before entry [13:15]. The distribution of that ability, and crucially whether the *bottom*
   grades are negative-EV, is assumed, not measured. That assumption is the entire result (next section).
3. **"Protect your capital" → a 20×-planned-loss tail** [19:50]. The tail multiple drives the whole 1%/2%/5%
   table and is picked out of the air. The conclusion (risk 1%, Kelly needs an edge you don't know) is right,
   standard, and would be right for any plausible tail.

Concepts that genuinely cannot be reduced to an action — discipline, patience, confidence — were dropped, which
is honest. But what remains is not psychology. **It is a sizing-and-frequency study relabelled.** Every verdict in
the video is a statement about position size or trade count; none is a statement about a trader's state of mind,
because no trader's state of mind is in the data. There is no data.

### The revenge number is capped, and they don't say so

Reported: doubling after every loss lifts average position size to ~3.5× and "adds two percentage points to your
chance of losing half the account" [07:00].

An **uncapped** martingale on this stream has E[size] = 0.37·Σ(1.26)ᵏ, which **diverges** — average size is
infinite, not 3.5×. Solving for the cap: stopping after m doublings gives 2.42× at m=2 and **3.42× at m=3**. So
the tested rule is *double at most three times, cap at 8× base risk (4% of account), then reset*.

That silently contradicts their own chart two minutes earlier: **the median longest losing streak in the year is
12**. A true "double after every loss" trader hits streak 12 in a median year at 2¹² = **4,096× base risk —
$2.05M of risk on a $50,000 account**. That is not "two percentage points"; it is certain ruin in year one. The
video's own two exhibits are inconsistent, and the resolution is an undisclosed cap.

This matters beyond pedantry: **the version of revenge trading that destroys retail accounts is the uncapped
one**, and the video's single most quotable line — "revenge trading on average actually makes money, that's why
people keep doing it" [20:30] — is true only of the capped version it quietly tested. That is the most
irresponsible sentence in the video and it is in the summary.

---

## Where it contradicts our own evidence — and why

### ⭐ "Sizing up A+ setups is worth $32k; skipping bad ones is worth $0" is the exact inverse of our size-lever result

Their cleanest claim [14:00–17:30]: with a fixed ability to grade setups, *skipping* the weak ones returns you
roughly to break-even (−$85, "basically nothing") and being **more** selective is actively worse (top 17% ≪ top
50%), while *sizing up* the strong ones at 1.5× is worth **+$32,000/yr**. Same skill, opposite use, opposite
payoff.

Our size-lever study (2026-09-18) found the reverse on real trades: **the lever is exclusion** — A+B only gave
+0.29R OOS against 0.00 flat, while a graded 10× risk spread gave only **+0.08R with more drawdown**.

The two results are not both right, and the reconciliation is clean and instructive: **in his simulation the
setups he throws away are profitable.** Every trade is drawn from a +EV generator; grading only re-ranks within
a distribution whose worst member still makes money. Discarding is therefore pure loss and the pickier you get
the more you burn — which is exactly what his chart shows. In our book, the C/D/F trades are **negative** EV
(the rubric read on 8/13–9/21 had B −0.73%, C −0.65%, F −0.02%), so exclusion pays and the graded spread does
not. **His result is a restatement of his assumption that bad setups are still good setups.** Change that one
input and the $32k/$0 split reverses.

Keep the house rule: *precision over recall*, exclusion over graded sizing. Nothing here moves it. Log this as
the clearest example yet of why we score generators, not conclusions.

### Where it agrees with us, and adds nothing

- **Profit targets / stopping when green cost money** — agrees with our profit-lock study (BE at +1R, locks and
  trims all cost money; "extended → tighten" INVERTED at −0.19/−0.47R) and with the exit-timing study (same-day
  exits are the negative bucket in **both** books). Three independent routes to the same place. We already act
  on this; his version is weaker evidence than ours because his is a tautology and ours is a real-fill result.
- **"No psychology rule turns a losing system into a winner; it only changes how fast you lose"** [20:50] — the
  most defensible sentence in the video, and consistent with everything in the ledger. It is also the
  quantitative version of `feedback_gabes_trades_are_not_evidence`.
- **Sizing up after hot streaks = exactly zero across every variant tested** (2/3/4 wins, up-on-day/week/month,
  new equity high) [15:30] — an honest null, reported as a null, with no attempt to rescue it. Our own record
  here rhymes: O'Neil pyramiding NULL, 8-week hold NULL. **Do not queue this.** Two independent nulls is enough.

### ⭐ The one number worth stealing: ~800 trades for t = 2

His power result checks out exactly (σ/trade $718 on a $50 edge → Sharpe/trade 0.0697 → n = 824 for t = 2). Run
it at the house bar:

| | n required |
|---|---|
| t = 2 (his bar) | **824 trades** |
| **t = 3 (our bar)** | **1,854 trades** |
| Gabe's journal today (272 campaigns) | → **t = 1.15** |

So a trader with a *genuinely good* edge — 37% win rate at 2R, $50/trade — running Gabe's trade count would
observe t = 1.15 and could not tell himself apart from noise. **The journal is structurally underpowered by ~6.8×
in n for our own certification bar, and that is true even if Gabe is a good trader.** This is the cleanest
numerical defence of `feedback_gabes_trades_are_not_evidence` we have, and it should go into the memory note and
the report card next to the lived-experience stats already queued. It also quietly prices the paid-community
pitch: nobody in that Skool has 1,854 trades.

---

## Verdict — 2.5/5

**Method: 2.5/5.** The paired same-stream control is genuinely good and better than the June build. The
"test the action, not the feeling" framing is the right frame, the nulls are reported as nulls, and the
arithmetic is correct. Against that: **no market data, no multiple-testing correction across 83 concepts, and
the "tested twice on completely separate data" claim [17:45] is a second draw from the same generator, which is
not out-of-sample in any sense that matters** — it re-estimates a Monte Carlo mean, it does not validate a
hypothesis. The August video would have failed its own September self on two of three guardrails.

**Claims: 2/5.** Roughly seven of ten verdicts are `E[Σ] = n·EV` restated; one (sizing A+ setups) contradicts our
real-data result and is an artefact of assuming bad setups are profitable; one (revenge trading is fine on
average) is materially misleading because of an undisclosed cap that contradicts the video's own streak chart;
two (streaks are normal / ~800 trades, and risk 1%) are correct, standard and useful.

**Above the June 2/5** because the controls are paired, the nulls are honest, the framing is reusable, and it
sells no fake strategy — it explicitly says no rule can fix a losing system. **Below the August 3/5** because
August at least put its claims in front of a market that could have refused them. This one cannot be falsified
by any market observation whatsoever, and a claim that cannot lose is not evidence.

Risk to a retail follower: **6/10.** Nothing here is directly tradeable, and the sizing advice (1%, cap at 1.5×)
is sound. The damage is the two lines a viewer will actually remember: "revenge trading makes money on average"
and "never set a profit target" — both delivered with the authority of 10,000 simulated years, both true only
inside a generator where you are already profitable, you never tilt, and your losses are capped.

---

## Testable here?

Almost all of it is untestable-by-construction or already settled. Three items, one of which is worth real time.

### ⭐ 1 — Fold the "streakiness check" into the queued Breitstein test 1. **Do this.**

This is the payoff of the review. `TEST_INDEX.md` §10 already carries **Cameron's "80% chance of doubling the
loss after breaching max loss"**, with the 2026-09-20 IQCapital addition to also score **"stop after 2
consecutive losses"** and **a hard shutoff ~90 min after the open**. The video supplies the missing piece: a
clean statement of *the only condition under which any stopping rule can pay*.

> **The decomposition to adopt.** With i.i.d. outcomes, a stop-for-the-day rule applied to a profitable book is
> strictly negative and applied to an unprofitable book is strictly positive — in both cases for the trivial
> reason that it changes n. Therefore the rule has **no independent content** unless outcomes after the trigger
> are conditionally worse. So the test is not "would the limit have made money last year" (that answer is
> determined by the sign of the book's expectancy and tells us nothing). **The test is whether P&L after the
> trigger is worse than P&L on matched non-triggered occasions** — everything else is the trade-count tax.

Concretely, add to the Breitstein 1 spec:

- **Arm 0 (new, run first — the conditional check).** On `journal_trades` / `journal_campaigns`: mean R and win
  rate on the trade immediately after k = 1, 2, 3 consecutive losing closes, versus the unconditional mean and
  versus a same-day random-other-trade control. Then the same on `journal_nav` day P&L: distribution of
  rest-of-day P&L after the intraday limit is first breached, versus sessions that touched half the limit and
  recovered (already the queued Cameron design). **If arm 0 is flat, every stopping rule in this family is
  settled NULL at once and we never run the dollar replays.** That is a big saving: one test retires Cameron,
  the 2-consecutive-loss rule and the 90-minute shutoff together.
- **Arm 1 (the upgrade the video misses).** Brendan's model holds risk per trade *fixed*, so tilt can only show
  up as a worse win rate. In a real log tilt shows up in **size and execution**, and we already have a hint
  it does: the August Luk/Tito lens found **stops blown past 2%** and **same-day round trips −$7.9k**. So
  measure three signatures after the trigger, not one: (a) win rate / mean R, (b) **risk-per-trade vs the
  trader's own median** — the revenge-size fingerprint, (c) **realised loss ÷ planned stop**, i.e. how often the
  stop is honoured. (b) and (c) are conformance and execution measures, which is precisely what
  `feedback_gabes_trades_are_not_evidence` **permits** the journal to be used for. Discipline claims are
  conformance claims; this is the legitimate test bed and the only one we have.
- **Power, stated up front.** Per the 800-trade arithmetic above, 272 campaigns give t ≈ 1.15 against a good
  trader's edge. **Pre-register that this test cannot certify a positive stopping rule** and can only produce
  (i) a decisive NULL on the conditional check, or (ii) a flagged conformance signature to act on for reasons
  other than a t-stat. Write the bar down before pulling, or we will read a 1.5 as encouragement.

*Prior: 70% that the conditional check is flat* (Stage A found intraday state carries almost nothing, and the
i.i.d. null is the strong default), *but 45% that the **size/stop-honouring** signature (b)/(c) is present*,
because that one is about a human under stress rather than about the market, and the August lens already saw it.
A NULL on (a) plus a hit on (b) is the most likely outcome and would be a useful MECHANISM yield: *the daily
loss limit is not an edge, it is a governor on a known execution failure.* Cost: unchanged, ~½ day.

### 2 — Nothing to queue on sizing. **Explicitly declined.**

His +$32k A+ sizing result is the inverse of our size-lever study for a reason we fully understand (his discards
are +EV, ours are −EV). Re-running it would test his assumption, not a market fact. His "sizing up after a hot
streak = 0" agrees with our O'Neil pyramid NULL. His 1%-risk / Kelly section is standard and unfalsifiable as
presented. **Do not spend a slot on any of it.**

### 3 — One free reporting line, folds into an already-queued item.

The **"lived-experience stats for the book"** row already queued from the June review (2026-09-21) should also
carry the **power number**: alongside % positive days/weeks/months and longest losing streak, print **the n
required for t = 3 at the book's own observed Sharpe-per-trade**, and where the book currently sits. It costs
nothing, it is computed from numbers we already have, and it stops the recurring mistake of reading a
trade-count-limited result as a verdict. ~15 minutes on top of the queued ~2 hours.

---

Related: [[project_ai_pathways_kb]], [[project_breitstein_test_queue]], [[project_iqcapital_kb]],
[[project_size_lever_study]], [[project_profit_lock_study]], [[project_exit_timing_study]],
[[project_august_2026_luk_tito_lens]], [[project_stage_a_intraday]], [[project_oneil_management_tests]],
[[feedback_gabes_trades_are_not_evidence]], [[feedback_precision_over_recall]], [[reference_test_index]].

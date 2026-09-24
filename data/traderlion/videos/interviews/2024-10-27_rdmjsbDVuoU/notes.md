# TraderLion -- "+222% Return in 27 Days - The High Tight Flag Trading Setup | Leif Soreide" (2024-10-27, 50 min)

_Reviewed 2026-09-23. TraderLion podcast (host Richard) with Leif Soreide, recorded in late October 2024 as a
promo for his two-part HTF Masterclass (Nov 2 and Nov 9, 2024). Case studies: ASTS ("ests" in the captions),
CELH, CORZ ("Kors"/"coz"), RKLB, LUMN ("Lumen"/"Ln"), GEV, STX, FLR, CAVA, LOCO, CVNA. Auto-captions; tickers
resolved from context and marked where uncertain. Short companion: [2024-10-09 clip](../2024-10-09_mpe2_FCfpRg/notes.md).
Setup write-up and codable spec: [setups/soreide_high_tight_flag.md](../../../setups/soreide_high_tight_flag.md)._

⚠ **"+222% in 27 days" is not in the video.** The figure, and "27 days", appear only in the title and description.
Grep of the transcript finds neither. Nothing on camera says which trade, account or period it refers to. Treat it
as marketing copy.

## Verdict: 2 / 5

- **More honest than most in this KB.** He shows losers (LOCO rolled over the 50 [46:28]; STX stopped under 1%
  [29:05]; LUMN top-ticked on the third scale [23:00]). He says outright "if we go into a trade we're probably going
  to lose" [03:40] and "it's all about the protection" [14:40]. He also discloses that he trades with the contest
  leader (Leos, Champion Team Trading) [03:24].
- **But it's a class funnel.** The HTF Masterclass, a "model book", a preview offer by email [06:00, 46:00, 48:49]
  and a Deepvue scanner "with my name on it" [24:40]. The discretionary layer ("think beyond the pattern", themes,
  grading shakeouts, "dollar levels", "different grades for your HTFs" [12:30]) is exactly the part reserved for
  the class.
- **The testable mechanics are the entry and the flag geometry.** The management rules he gives (scale at 1-3R,
  sell into 100% round numbers, roll at the 50-day, pyramid) are already contradicted or NULL here.
- 0.5 above the 12-minute clip would be justified by the losers alone. I left both at 2/5 because this one has
  less definition and more selling.

## Provenance

- Billed as **2019 USIC champion**. No return, division or account size is given in the video. USIC checks broker
  statements for one calendar year; that is not an audit of a method, and the entrant pool is opt-in.
- He is not an independent practitioner in this video. It is sponsored content for his own paid class, on a
  channel that also sells the Deepvue screener where his scan lives. He also advertises a members' platform
  ("my members know a few techniques") [08:58].
- Every chart was selected after the fact. He says "I don't like hindsight trading, a lot of the stuff is really
  fresh" [04:40], but open positions are still survivors on the day of recording.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| title | "+222% in 27 days" | ❌ **Never said.** Not in the transcript |
| 02:40 | HTFs can go up 700%; "you're not always going to get a flag that's 25%" | Descriptive. Flag depth range 20-33% is in the spec as a discretionary parameter |
| 03:40, 11:01 | "It's really about being the best loser"; cut fast, "roll them out" | ✅ **Agrees in spirit** with our exit results: same-day exits are the negative bucket in both books, but the loss cap comes from a stop on the close, not from scalping. See the stop row below |
| 04:00, 32:00-33:00 | "Think beyond the pattern": trade HTFs within hot themes (rockets, nuclear, space) | **Contradicted where tested.** Industry rotation detection: **can't front-run rotations**; top-down leading-group filtering **INVERTED** (bottom-3 sectors beat top-3, t 2.6). His theme calls are discretionary and can't be scored as a rule |
| 08:40, 36:00-36:40 | "The 50 is a very important area for HTFs"; "big pop, I get a risk multiple, it rolls to the 50, I'm out" | **Adjacent NULLs.** O'Neil 8-week hold NULL (paired -0.013R, t -0.21). House trail = 20 EMA, and nothing tested beats it: tightening **INVERTED**, trims cost. A 50-day exit isn't tested on HTFs |
| 10:02, 26:01-27:01 | ⭐ Preferred entry: **early, inside the flag**, on a *low-volume inside day* ("dead volume, lowest volume in 10 days"), stop under that inside-day low. He'd "rather get in early" than buy the sloppy highs [25:01] | **Untested, and the most interesting thing in the video.** It's an entry *below* the flag high, so it's on the right side of the entry-extension finding (breakout **+0.52 ADR** above the prior 20d high vs **-2.09 ADR** for a random later entry; the control beats the signal). The nearest test, reclaim vs pullback-low, has the pullback arm at **+0.042 to +0.070R, t 1.51-2.04**, no cell at the bar. ⚠ An inside-day buy stop is an intraday trigger; on daily bars, code it as "close above the inside-day high". Codable as arm B in the spec |
| 13:01 | "Rocket base": a failed HTF that corrects 25-50% and rebuilds over 6-10 weeks | Codable as a separate arm (depth <= 50%, 30-50 sessions). Untested. Low prior: the VCP/base-tightening family is NULL |
| 15:01 | Not an HTF if the rise from the relevant level is only ~40%; it "needs a new base" | Definitional. Supports a hard 90% pole floor |
| 16:00 | "Break your rules and get stopped, you should be angry ... otherwise you're a random trader, random results" | Process point, not testable. Consistent with our view that the tested rule is the unit |
| 16:40-17:20 | Don't buy a tight area into earnings ("two risk multiples"); buy the *earnings pivot* after the report | **Half supported.** Earnings: don't hold short premium through, but for a stock buyer **PEAD on the actual surprise is NULL**, and buying the catalyst day is **-0.173R, t -4.70** (DR-EP arm A). Waiting past the event is the less-bad direction (DR-EP A->B +0.106R) but still NULL (-0.067R). "Avoid holding into the print" is untested for the stock book |
| 18:40, 22:00 | Prefers $10+; nothing below $5 | Trivially true of our panel (px >= $5, ADDV >= $50M). Note: this excludes most small-cap HTFs, which is where the pattern is most common |
| 19:01-20:00, 45:01 | Shakeouts at market lows are to be "discounted"; grade the shakeout; buy the turn after it | **Unfalsifiable as stated.** "You go in hindsight and say well that was the market low" [45:10] is his own caveat. The testable cousin (reclaim after a flush) is the reclaim arm: **+0.048 to +0.178R, t 1.84-2.69, edge over its `post` control -0.004 to +0.108R**, no cell at the bar |
| 22:44-23:00 | Stop ~5%, staggered under a prior inside-day low. Start scaling at ~3R | ⚠ **Quote it two ways.** A 5% stop on a name that just rose 90% is ~0.5-1.0 ADR (these names run ADR 5-10%). That is the tight-stop zone where the house rule says **judge on the close** (0.4-0.8 ADR). Scaling at 3R: trims **-0.25 to -0.33R** on the house book |
| 27:01 | "20% gives you four risk multiples betting 5%" -> sell into it | Same trim evidence. The R arithmetic depends on the 5% stop. In percent the question is just "does selling at +20% help", and our profit-lock test says no |
| 28:40-30:40 | ⭐ Earnings pops that get "sucked back down" in a market correction: attack them the next time they set up. "We did a lot of work recently" | **Untested and close to a queued idea.** It's the post-catalyst first-flag entry (TEST_INDEX §10, queued 2026-09-21) conditioned on a market pullback. DR-EP says the retrace entry only rescues bad to less-bad. His "work" is not shown |
| 38:02, 39:00 | Sell into round-number 100% gains; after earnings "be up 50%", then wind down to "trailing size 25% or less" | **Profit-lock evidence: trims cost.** Tito spike exit: a **risk** lever (win 14.6 -> 19.3%, caps the right tail), **not a return lever** (t 0.18) |
| 39:40, 41:00 | "Getting full, all my money, max margin" is his hardest problem; "press when things are working" | ⚠ **Size lever: exclusion helps, a 10x amplification doesn't** (+0.08R, costs drawdown). The "press when it's working" personal signal is untested as a rule. Nearest: breakout activity gate **PARKED** (t 2.59, fails Sidak) |
| 40:40 | HTFs "trade in their own universe", decoupling from the group | Consistent with our universe test (the universe carries the return, not the trigger). No direct test |
| 43:01 | "Not being able to hold something below the 50" is his biggest cost as a risk-first trader | Honest self-assessment. It argues against the 50-day as an exit for him, which contradicts [36:40] |
| 43:40-44:10 | First scale at 1R in a difficult tape; ~10% scale in a green tape | Same trim evidence |
| 46:28-47:00 | LOCO loser: second touch of the 50, rolled; CAVA the leader "doing the same trade" | ✅ A loser shown. One instance |
| 48:00 | "Only two pages in O'Neil's book on the HTF" | True of the literature. It also means there's no published base rate. Ours would be the first |

## What I would take

1. **The early-entry arm.** "Buy the low-volume inside day inside the flag, stop under it" moves the entry below
   the flag high. That's the only direction our data has ever rewarded (entry-extension, retrace PARKED). If HTF
   gets tested, this arm and the flag-high breakout on the same events are the within-setup timing comparison.
2. **Honest loss framing** ("best loser", losers shown). It's a behavioural point, not an edge.
3. Nothing to adopt. Every management rule shown (scale at 1-3R, sell 100% round numbers, press when working,
   max margin) is contradicted or NULL here.

## Not tested, could be

- **HTF, three arms (flag-high breakout / early inside-day entry / rocket base)** vs same-date house breakouts in
  other names. Spec, discretionary ranges and pattern_test design:
  [setups/soreide_high_tight_flag.md](../../../setups/soreide_high_tight_flag.md). **Count the signals before
  anything else** (~1 hour). The liquid panel starts 2019 with a $50M ADDV floor, and HTFs are rare. If the primary
  arm has fewer than ~300 events it's UNDERPOWERED by design, and the thresholds must not be loosened after the
  count to rescue it.
- **Post-earnings "sucked back" re-entry** [28:40]: fold into the queued post-catalyst first-flag test as a stratum
  (catalyst gap during an index drawdown), not as a separate test.

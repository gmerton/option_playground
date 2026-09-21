# Capitulation fade: the ten-variable scorecard

> **Verdict:** The fullest statement of his reversal selection rubric, and honest about the base rate ("we are
> looking for the 0.001%"). But it's a discretionary mental checklist ("everything's on a spectrum"), the evidence
> is hindsight-picked famous tops and bottoms, and **the parts we've already measured contradict it on single-name
> longs**: deeper extension and a volume flush made the counter-trend long WORSE, and "boring" INVERTED.
> **Type:** setup selection (mean reversion / capitulation, both sides) · **Conviction:** 2.5/5 · **Testability:**
> EOD ⭐ for 7 of 10 variables · **Tested?** **yes, 2026-09-20: FAIL both sides** (`data/studies/breitstein_tests/capitulation_scorecard_2026-09-20.md`)
> **Source:** SMB Capital channel talk, `P4Ijq-IJhE8` "The 10 Rules That Catch Big Reversals (BEFORE They Happen)"
> (uploaded 2026-09-08, 38:36; a conference talk, not his own channel, so outside `channel_videos.txt`).
> Transcript: `videos/talks/2026-09-08_P4Ijq-IJhE8_smb/transcript.txt`.

---

## 1. The rubric

**Prerequisite:** an in-play stock (huge volume, range > average, often news- or pattern-initiated) [04:49].
**Trade:** "right side of the V". Fade only once the turn is in: trendline break, break of prior bar lows/highs, an
intraday capitulation, or the break of a forced buyer/seller on the tape [38:02]. Execution is "the 201 lesson",
not covered here.

| # | variable | his operational hint | EOD-testable as |
|---|---|---|---|
| 1 | **Acceleration**: slope, not distance ("asymptote") [05:31] | linear moves are sustainable; fade only the curve | ratio of the last-k-day return to the prior-k-day return, in ADR |
| 2 | **Multiple days in one direction**, ideally ≥ 3 [08:26] | 9 down days can stand in for no parabola | consecutive same-sign closes |
| 3 | **Far outside the Bollinger Band** [09:34] | distance to the 20 MA = the reward | % beyond the 2σ band / distance to the 20 MA in ADR |
| 4 | **No fresh news**: don't fade day-1 news; fade days later [11:34] | news = fundamental repricing (oil / Hormuz vs silver) | earnings-date proxy only (news history ≈ 36 days) |
| 5 | **Volume multiples of average** [14:14] | compare 09:30–10:30 volume to yesterday's already-elevated 09:30–10:30 | volume ÷ 50d ADV; % of float |
| 6 | **More legs** [18:49] | the 3rd leg is often final; reward = the whole move back to the MA | swing-leg count (as in the bouncy-ball legs) |
| 7 | **Minimal consolidation** [20:49] | consolidation = price acceptance | inside-bar / narrow-range count during the run |
| 8 | **Extreme sentiment** [22:57] | "uninvestable", "new paradigm", Twitter polls | ✗ not testable historically |
| 9 | **The more boring the better** [29:39] | large cap, diversified, boring asset (Berkshire, Nikkei, silver, Treasuries) vs micro-cap biotech | **market cap / index / asset class** (≠ our own-ADR version, §2) |
| 10 | **Forced flows** magnify the move [34:07] | margin hikes, liquidations; CRCL forced buyer at 245 on the tape | margin-change dates (futures), borrow/short interest: mostly ✗ |

"Stacking" claim: the more variables align, the higher the win rate, and that's how he avoids the "paper cuts" of
fading every extension.

## 2. Against the repo's evidence

- **Variable 3 + 5 on the long side: contradicted.** Counter-trend long (≥ 3 ADR below the 20 EMA + prior-bar-high
  break), 2026-09-19: every arm negative (−0.15R), bare trigger ≈ control, and **deeper extension and the volume flush
  were WORSE**, the opposite of "further = higher probability and bigger reward".
- **Variable 9: INVERTED as we built it**, but that version isn't his. `boring_violent_2026-09-19.md` defined boring
  as low own-ADR, with the drop measured in own-ADR units, and the gate shrank the reversion. His examples here are
  about **market cap, diversification and asset class** (Berkshire, the Nikkei, silver, Treasuries). That's a
  different, still-untested hypothesis, and the only version with a real mechanism (fundamental value can't move
  30% in days for a diversified index).
- **Short side (variables 1, 2, 5, 6): mostly untested; the one cousin failed.** The bouncy-ball short failed daily
  and intraday, and the only live cell was legs 8–12 ADR (n = 94), i.e. variable 6 at the extreme. The 2×/2×
  blowoff short (variables 1 + 5) is queued.
- **Crash-leader study:** buying deep single-name drawdowns is a regime bet (pays only in a broken tape). His best
  trade (Nikkei, Aug 2024) was an **index** in a panic, which is consistent with "boring + forced flows" and not with
  single-name small caps.
- **Variable 10 is the order-flow idea we parked** (mechanical/forced flow, TEST_INDEX §10), from the other side:
  he fades the forced flow once it breaks.

## 3. What to test (one test, not ten)

**The stacking claim is the test.** Build a composite score from the mechanical variables (1, 2, 3, 5, 6, 7;
9 = market-cap tercile; 4 = not within 2 sessions of earnings), both sides, on the liquid panel. Enter on his
trigger (break of prior bar high/low after the extreme), 20-MA target, stop at the extreme. Pass = forward R
**monotone in the score** AND the top bucket beats the `post` + `xname` controls. It subsumes the queued 2×/2× short.
⚠ Power: he says the edge is in 0.001% of moves, so the top bucket will be small and clustered (panics arrive
together). Report effective n (distinct dates / episodes), not trades.
Prior: poor on single-name longs (two tests against). The live question is the short side and the
large-cap/index version of variable 9.

## 4. Tested 2026-09-20: FAIL

71k signals, 7 variables stacked, both sides, his trigger + trail. No score bucket is positive on the short side, and the top bucket is worst. The long side looks inverted, but that's March 2020 (ex panic months +0.055R = flat). Long buckets beat a random other name on the same date but lose to the same name later, so it's a date effect. The fresh-news veto isn't supported. See the study doc.

## 5. Verdict (pre-test)

2.5/5. A good vocabulary and an honest base rate, but a discretionary checklist evidenced by the most famous
reversals of the last five years (MSTR, SMCI, silver, the Nikkei, CRCL, Tesla), all selected after the fact. Where
our data could score a variable, it went against him on the long side.

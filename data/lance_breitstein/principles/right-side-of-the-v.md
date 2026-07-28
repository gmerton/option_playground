# Right side of the V — same price, different expected value

> **Verdict:** ⭐⭐ **His single unifying concept, and the most testable idea in the entire KB.**
> Every other setup he teaches is a special case of it. Fully EOD-testable, and it explains a
> result the repo already produced without understanding why.
> **Type:** entry timing (general principle) · **Conviction:** 3/5 · **Testability:** EOD ⭐⭐
> **Tested?** no · **Source:** `wtQIj6Apiq0` (2025-11-15)

---

## 1. The claim

> "**The same price does not always equal the same expected value.** This is one of the biggest
> trader fallacies of all time. A lot of traders assume same price, same result… **The pattern and
> timing change the expected value.**"

Poker analogy: a hand with 40% equity pre-flop can be 80% by the river. The card is the same; the
information isn't.

**Left side of the V** — buying while price is still falling. Two problems: (a) there is **no true
stop**, "when you're fighting the trend you don't necessarily have a stop, and that's one of the
most dangerous parts"; (b) win rate is only marginally above even.

**Right side of the V** — buying the same price *after the turn is in*. Two things change:
1. **A real stop exists** — the low of the day.
2. **Win rate rises** because you are now aligned with the immediate move.

His arithmetic: holding reward:risk constant and improving only the win rate, EV comes out **~4×
higher**. "That can be the difference between a career and failure."

## 2. How he defines "the turn" — three mechanical triggers

For a stock capitulating lower (mirror them for up-moves):

| trigger | up-move mirror |
|---|---|
| break of **prior bar highs** | break of prior bar lows |
| break of a **tight downtrend line** | break of an uptrend line |
| break of a **moving average** (for looser, bigger trends) | same, other direction |

He is explicit that the choice is system-dependent, and equally explicit that *some* confirmation
is mandatory.

## 3. ⭐ Why this matters to the repo — it retro-explains the gap study

The opening-gap study found the unconditional fade worthless: fading at the open with **no
confirmation** produced +2.59 bp on SPY (t=3.5) but negative on DIA, and every stopped variant
bracketed zero. That is textbook **left side of the V** — buying/selling into an unfinished move
with an arbitrary stop.

The two conditions that *did* work — after a ≥1 ATR move (+11.91 bp, t=6.53) and in the high-VIX
tercile (+6.90 bp, t=3.65) — are both proxies for *exhaustion*, i.e. situations where the turn is
more likely to be near. And Breitstein's ORB variant of the same trade
([opening-range-break.md](opening-range-break.md)) adds the missing piece: **wait for the opening
range to fail before shorting the gap.**

So the repo's own data already contains the shape of this claim. It has never been tested
directly.

## 4. ⭐ The test — clean, cheap, and never run here

Hold the *price* fixed and vary only the *timing*:

- **Arm A (left side):** enter when price reaches level P while still declining.
- **Arm B (right side):** enter at the same level P, but only after a turn trigger fires
  (close > prior bar high).
- Same universe, same stop convention (day's low), same exit, same horizon.

Prediction: Arm B has a materially higher win rate at similar reward:risk, and therefore higher
EV. This is directly implementable in `arch_lib` — it needs one new entry tier and no new data.

⚠ It also cleanly tests the **stop availability** half of his claim, which is the more interesting
half: on the left side the stop is undefined, so the honest simulation of Arm A has to either use
an arbitrary stop or none — and *that* is exactly the difference `RESULTS.md` measured when it
found structural stops no better than arbitrary ones at matched width. This test would separate
"the level is meaningful" from "the timing makes the level meaningful."

## 5. Sizing follow-on

> "The higher the expected value, the more size you can put on the trade… waiting for the turn
> allowed me to **size up, risk less, and stress less** while making more P&L."

This is the connective tissue to [stops-and-sizing.md](stops-and-sizing.md): the turn creates the
stop, the stop is tight, the tight stop permits size. **It is the same causal chain as the 6×
sizing lever in `HOW_THEY_DO_IT.md` — but with the missing first link supplied.** The lever starts
with *timing*, not with the stop.

## 6. Red flags

- The 4× EV figure comes from **assumed** win rates in a toy example, not from measured data. It
  illustrates the arithmetic; it evidences nothing.
- No losing example.
- ⚠ He raises the obvious objection himself — "isn't that death by a thousand paper cuts if you
  take every little turn?" — and answers it with "be more nuanced," i.e. discretion. That is the
  unfalsifiable joint, and it is load-bearing: the rule as stated would fire constantly.
- Two subscribe prompts and a forward-reference to another video inside four minutes.

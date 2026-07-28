# Opening Range Break (ORB)

> **Verdict:** ⭐ **Independently corroborates two findings the repo already produced statistically.**
> His three stated ORB use cases map almost exactly onto the two conditions where the gap study
> found real edge — and it is the same entry Qullamaggie names ("buy the opening range highs").
> **Type:** entry / intraday setup · **Conviction:** 3/5 · **Testability:** intraday-needed
> **Tested?** no (but see §3 — the EOD analogue is already tested and positive)
> **Source:** `QmPUp9ISuDw` — "ORB Trading Only Works If You Do These 3 Things" (2026-06-24)

---

## 1. Mechanics

- **Range:** wick high to wick low of roughly the **first 30 minutes**.
- **Trigger:** break of that range, "once price confirms momentum through it."
- **⚠ Hard precondition:** in-play stocks **only**. "If you try to trade opening range breaks on
  random low-volume garbage, you're going to get chopped into pieces." See
  [in-play-stocks.md](in-play-stocks.md).
- **Mechanism:** the open concentrates repositioning — overnight information is priced and
  everyone reacts simultaneously. The range is a compression zone where buyers and sellers
  establish temporary equilibrium; once one side loses control, "liquidity tends to cascade in the
  direction of momentum" and uncertainty collapses.

**Four stated nuances:** quality of the consolidation inside the range matters ("avoid really
noisy consolidation ranges"); volume confirmation ("weak volume breakouts are far more likely to
fail"); market context alignment; and "risk management matters more than the setup itself."

## 2. Three use cases

1. **Exhaustion gaps** — a stock gaps up massively *after already going vertical for days or
   weeks*, retail chasing, euphoric sentiment. If it then **fails the opening range and breaks
   lower**, the late buyers are trapped simultaneously and the unwind cascades. Examples: SMCI,
   MSTR. Explicitly: *don't* predict the top — "the opening range gives you that confirmation
   mechanism… you are waiting for price to prove momentum exhaustion instead of blindly guessing."
2. **Continuation, day one after a real catalyst** — earnings, FDA, guidance. Institutions cannot
   fully position at once and scale over days/weeks, so the range becomes a launchpad. He credits
   this to Qullamaggie's episodic pivots. Example: SNDK after 30 Apr earnings.
3. **Macro-volatility days** — index instruments during panic or euphoria. 2025 tariff panic, 2020
   COVID. "Some of the cleanest intraday trends I've ever traded came during periods of macro
   panic because the emotional intensity was so extreme."

## 3. ⭐ Convergence with the repo's own gap study

This is the first time an independent practitioner has corroborated a *statistical* result from
this repo rather than contradicting one. The opening-gap study
([`opening-gap-fade.md`](../../carter_mastering_the_trade/setups/opening-gap-fade.md)) found the
generic gap fade dead, with exactly two conditions surviving:

| gap-study finding (SPY, 1993–2026, EOD) | Breitstein's ORB use case |
|---|---|
| **Day after a ≥1 ATR move: +11.91 bp, t=6.53** vs +0.84 otherwise — and this *inverts* Carter's stated veto | **Use case 1: exhaustion gap** — gap up *after an extended vertical run*, fade the OR failure |
| **High-VIX tercile: +6.90 bp, t=3.65** vs −0.83 in low VIX | **Use case 3: macro-volatility days** |

Both of the gap study's positive conditions are ones he names independently. The difference is the
trigger: the study faded at the open with no confirmation, whereas he requires the **opening range
to fail first**. That is a confirmation filter the EOD test could not implement — and it is the
natural explanation for why the unconditional fade was worthless while these two conditions were
not.

**Consequence:** the gap study's conclusion ("the fade is a rare-condition volatility trade wearing
a daily setup's clothes — 5.7% of days carry half the P&L") and Breitstein's practice are the same
claim reached two ways.

## 4. Relevance to the open question

Qullamaggie's stated entry is **"buy the opening range highs of a breakout"** with the stop at the
breakout day's low ([qullamaggie-system-relayed.md](qullamaggie-system-relayed.md)). Breitstein
uses the same construct. **Two of the three traders under study enter on an opening-range break** —
which is a *specific, mechanical, intraday* entry rule, not a vague appeal to "precision."

That sharpens the minute-bar test named in `HOW_THEY_DO_IT.md` from "does intraday entry help?" to
a concrete specification: **enter on the 30-minute opening-range break, stop at the day's low, and
measure the stop-out rate against the 91% that daily-bar entries produce at comparable width.**

## 5. Red flags

- All examples (SMCI, MSTR, SNDK) are winners after the fact.
- Course plug, and a swipe at "oversimplified garbage taught by people who never actually traded
  size" — which is marketing, though the substantive point (ORB without an in-play filter is
  noise) is one this repo's own results support.
- ⚠ "Quality of the consolidation" and "noisy ranges" are the discretionary joint, and he says
  outright it takes "thousands of chart reps." A mechanical ORB test will be a strawman of what he
  does — the honest framing is that it tests the *trigger*, not the *selection*.

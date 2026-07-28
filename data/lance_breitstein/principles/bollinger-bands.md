# Bollinger Bands — pendulum, overextension, and "no man's land"

> **Verdict:** ✅ **Passes the skeptic check.** He does NOT repeat the Squeeze claim — he uses
> band contraction as a reason to **stop trading**, the opposite of Carter's coiled-spring trade,
> which this repo killed three ways. Independent corroboration from practice.
> **Type:** volatility context / overextension · **Conviction:** 2.5/5 · **Testability:** EOD ⭐
> **Tested?** no (but one component is already settled — see §5)
> **Source:** `ZZ-e9wxARSI` (2025-11-29). His self-described main indicator, 15 years of use.

---

## 1. Mechanics — three uses, none of them a level

Opens by ruling out the naive use, exactly as he did with AVWAP:

> "I want to make it explicitly clear that I **do not use Bollinger Bands as exact levels**. I am
> never buying the break above a Bollinger Band, or using a Bollinger Band as a price target."

1. **Pendulum / mean reversion.** Without fresh news, stretched price snaps back. He grades
   sentiment on a −10 (peak panic) to +10 (peak euphoria) scale and looks for *transitions* — e.g.
   PLTR going "+6 steady strong to −8 bearish panic in a matter of days" (Aug 2025), which he
   bought. Claim: "the further a stock is stretched, the higher the probability of a successful
   reversal **and the greater in magnitude** that reversal is likely to be."
2. **Overextension gauge.** Price accelerating *beyond* the band after already trending. "The
   absolute best capitulation plays tend to have price meaningfully extended below or above the
   bands after already trending." ⚠ Conditioned: only in **trending markets with expanding
   bands**. A breakout from a tight range will poke the upper band without being overextended
   (his IonQ counterexample).
3. **⭐ Volatility contraction = "no man's land" = STAND ASIDE.** "When Bollinger Bands are
   contracting, I often won't look to take any trades within the range without proper
   consolidation."

## 2. ⚠ The skeptic check this video was ingested for — result

`ZZ-e9wxARSI` is the same "…Edge Most Traders Never Discover" series as the AVWAP video, and the
repo has already **killed the Squeeze** (Bollinger inside Keltner) three separate ways: direction
rule negative in all four eras, "longer squeeze = bigger move" contradicted monotonically, and the
expansion **fully priced** in IV. So this was a live test of whether he repeats a falsified claim.

**He does not — he asserts the opposite.** Carter: band compression is a coiled spring, buy the
expansion. Breitstein: band compression is no man's land, *don't trade it*, and if you must, size
down hard.

Two independent lines of evidence now agree against Carter: this repo's backtest, and the stated
practice of a trader who has used the same indicator for 15 years. **That materially raises the
prior on his other material** and lowers it further on the Squeeze.

## 3. Testable extractions

- ⭐ **"Right side of the V" short, fully mechanical** (given here in passing, and the cleanest
  rule in the video): after an extended trend tops with capitulation volume, **short the break of
  prior daily bar lows, stop at prior daily bar highs.** EOD-testable today; also gives the repo
  its first *short* rule, and every backtest so far has been long-only.
- **The magnitude claim** — "further stretched ⇒ larger *and* more probable reversal." Directly
  testable by bucketing on distance beyond the band. ⚠ Note the repo's gap study found the
  analogous claim **half true**: larger gaps filled *less* often (85%→11% by size) but the
  1.0–2.0 ATR bucket had the *best* expectancy (+26 bp, t=2.99). Probability and magnitude moved
  in opposite directions. Expect the same split here.
- **"No man's land" as a veto filter** — band width percentile as a stand-aside gate. Cheap to add
  to the existing harness.

## 4. ⚠ Where it stays unfalsifiable

"Capitulatory volume", "proper consolidation", "context matters", and the −10/+10 sentiment scale
are all judgment. He is explicit that bands are "just one tool" and that "it is the confluence of
these systems that leads to successful trading" — which is honest, and also means the tested
version will always be a strawman of what he actually does. Say so rather than pretending
otherwise.

## 5. Objective assessment

- **Red flags:** all four examples (PLTR, UA, IonQ, MSTR) are winners shown after the fact. Course
  plug at the close. The "$100M verified profits" opener again, unevidenced.
- **Consistency in his favour:** across both indicator videos he refuses to trade an indicator as
  a level and insists on it as *context*. That is a coherent epistemic position, not a sales
  pitch, and it is the position most likely to survive testing — indicators-as-levels is exactly
  what dies in backtests.
- **The mechanism is stated and plausible** — bands are a volatility-normalized distance from a
  mean, so "beyond the band after a trend" is a standardized overextension measure. That is a real
  statistic, not a pattern.

## 6. Overlap with the rest of the repo

- **Directly contradicts** [[project-carter-mastering-the-trade]]'s Squeeze — and agrees with our
  backtest. See §2.
- **The PLTR example is the same trade** he uses in the moving-average video (`H01JbbEY7ac`) to
  illustrate MA-as-resistance-then-support. Same trade, two indicators, two videos — worth noting
  that a single position is generating multiple pieces of "evidence."
- **"No man's land" has its own video** (`fCp6CRu6E5Y`, ingested, not yet written up).

# 15 risk-management lessons — the quantified ones, and where they contradict Luk

> **Verdict:** Mostly process, but four rules carry numbers, and two of them contradict the Luk KB directly.
> **Type:** sizing + review-process + psychology
> **Conviction:** 3/5 (process rules from a survivor) · **Testability:** two rules EOD-testable on our own journal · **Tested?** no
> **Source:** `gb7nNveNBjg` — 15 Years of Trading Risk Management in 20 Minutes (2025-11-26)

---

## 1. The rules with numbers or mechanics

| # | Rule | Where it bites the repo |
|---|---|---|
| 1 | **Daily loss limit, enforced at the broker** ("every blown-up trader had just one bad day"; his started at −$150/day at Trillium) [00:32–02:09] | We have no daily loss limit anywhere in the tooling. `journal_nav` could compute the worst-day distribution to size one. |
| 2 | Stop decided **before** entry, every position, "even if that stop is accepting a full loss" [02:09–02:58] | Same as Luk; the 9/8–9/9 journal shows the failure mode is not the absence of a stop but its placement (inside noise). |
| 5 | **Keep dollar risk constant, not share count**: a 3x wider stop → ⅓ the size. **Overnight/swing size = ½ to ⅓ of intraday size** because you cannot manage a halt or a gap [05:30–06:52] | ⚠ **Contradicts Luk**, who runs no overnight stops at all and reasons gap-up/gap-down "even out." Breitstein's answer is size, not stops. Directly relevant to the SKHY overnight decision (9/9): the "half off" recommendation was this rule. |
| 5b | **"Never size so large that it changes how you behave in the trade"** — hesitation, early exits, attachment mean you have already lost discipline [06:52–07:22] | Testable on the journal: does exit quality (too_soon rate) degrade with position size? The 9/8 review has the raw material. |
| 6 | **80% of profits from 1–5% of trades**; elite traders make **100x** a normal trade on their best; beginners should aim for 150–200% [07:22–08:35] | ⚠ **Contradicts Luk's constant ~0.3% risk per trade** and matches `stops-and-sizing.md` (10x A/B/C/D). This is the conviction-risk lever `risk-framework-longform.md` said the sims lack. |
| 8 | **Mental temp check** each morning; cut limits if sleep/argument/anxiety ("double your normal error rate") [09:16–10:28] | Process. The daily-routine doc could carry a one-line check. |
| 11 | Shorting: his biggest loss was **−$2M in 30 minutes** on a +200% squeeze; more traders blow up shorting small caps than anywhere [14:17–15:41] | Context for the new short detectors: the stop-in-noise tag is the wrong worry on small caps; the halt is. Keep BIR/FBO on liquid names. |
| 12 | Never risk an amount that, lost, would hurt confidence and momentum ("the powerlifter analogy") [15:41–16:39] | Process. |
| 15 | Risk never disappears; cutting size trades blow-up risk for opportunity cost [19:08] | — |

Lessons 3 (external goals: the 2021 CAR trade, −$2M in an hour chasing a $20M year), 4 (never game over: wire out profits, 2-year reserve), 7 (drawdown protocol written before you need it), 9 (risk rules cannot be generalized — "asking what meal someone should eat"), 10 (EV drives every add/hedge/take-profit decision), 13 (P&L goes exponential, don't extrapolate linearly), 14 (systems over willpower) are process and filed as such.

## 2. ⚠ The sizing-lever question

He gives the **shape** of the lever (rule 6: 10–100x between worst and best setups) but refuses, at length, to give the number (rule 9). His own tolerance: "I'm okay stomaching huge drawdowns," a home-run hitter, not a sniper. For the open question this confirms `risk-framework-longform.md`: the lever the sims lack is conviction risk, and it is bounded by a daily loss limit and a behaviour test, not by a % rule.

## 3. Claimed edge & evidence

Anecdotes: the CAR loss, the crypto whale (−$62M on Oct 10 2025), "traders I've mentored who made 7–8 figures." No distribution, no rates. Course link at the drawdown-protocol and bet-sizing cross-references.

## 4. ⚠ Prop-infrastructure dependency

Rule 1 assumes a broker/firm that enforces a daily loss limit in software. IBKR can approximate it with account-level order restrictions, not natively.

## 5. Collisions with the repo

- ⭐ **Two testable items on our own data:** (a) size-vs-exit-quality (rule 5b) from `journal_trade_reviews` × fill sizes; (b) the worst-day distribution from `journal_nav` to set a daily loss limit. Both are a session's work.
- **Luk vs Breitstein, two direct disagreements:** overnight risk (Luk: no stops, it evens out · Breitstein: cut size ½–⅓) and risk skew (Luk: constant · Breitstein: 10–100x). The repo's August lens sided with tight stops sized to the level; it has not taken a position on either of these.

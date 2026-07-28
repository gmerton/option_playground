# Risk framework — the two long-form pieces

> **Verdict:** ⚠ **Refines the sizing thesis in `HOW_THEY_DO_IT.md` in a way that partly deflates
> it.** He caps position size at ~25% of account *independently of risk*, which means the
> stop-tightness lever is bounded — and my simulation's 30% cap was, if anything, generous. The
> genuinely uncapped lever turns out to be a different one.
> **Type:** sizing / risk philosophy · **Conviction:** 3/5 · **Testability:** partly EOD
> **Source:** `tIB72PAeZLU` "The Art of Betting Big" w/ Kyle Williams (2025-10-22, 60k chars) ·
> `hC4g7qY6UcQ` "52-Minute Risk Management Masterclass" (2026-07-15, 61k chars)

---

## 1. ⭐ The dual constraint — risk AND position size, separately

The clearest statement of how he actually sizes, from the interview:

> "When I'm day trading, usually in the small-cap space, it's going to be a **set risk amount** —
> by grade, exponential sizing. **If it's A+, I want to risk something like 50-60 grand.**"

> "The last thing I want to do, if I can get a really good risk-reward on a swing trade on a large
> cap — **I don't want to be 50% of my account in** just because my risk-reward… because I'm
> risking a fraction of a percent. So if I can get under, let's say, **one R of a loser**, but
> make sure I'm having **at least 10 to 20% of my account in the trade** — that's where I'm trying
> to look at both. Am I risking 12 grand, but do I have **10, 20, or at max 25%** of my account in
> that position?"

**He constrains both ends.** A floor (be meaningfully in it — at least 10-20%) and a ceiling (max
~25%), applied *on top of* the risk calculation.

## 2. ⚠ What this does to the 6× sizing lever

`HOW_THEY_DO_IT.md` §1 argued the gap comes from position = risk% ÷ stop%, so a 1.5% stop buys a
20% position where a 9.2% stop buys 3.3%. **He explicitly refuses to let that arithmetic run** —
capping at ~25% regardless of how tight the stop gets. My simulations capped at 30%.

⟹ **The simulation was not under-sizing relative to him.** The stop-tightness lever is bounded at
roughly the same place in both. Combined with correction C1 (the lever is intraday-only anyway),
this thesis is now substantially narrowed.

**But it separates out a second, genuinely unbounded lever the sims never had:**

| lever | what varies | bounded? | in my sims? |
|---|---|---|---|
| **Stop tightness** | position = risk ÷ stop | **Yes** — ~25% position cap | ✅ modelled (30% cap) |
| **Conviction** | the *risk budget itself*, ~$10k (B) → ~$100k (A) | not stated | ❌ **absent — flat risk** |

The conviction lever is a **10× swing in risk per trade**, and every backtest in this repo holds
risk fixed at 0.3%. That, not stop tightness, is the sizing mechanism the harness structurally
cannot see. Revised priority: **test tier-weighted risk before spending anything on minute bars.**

⚠ Prior is unfavourable — on the broad panel the higher scorecard tiers were *worse* per trade
(GATES +0.93% vs BOTH +0.01%), so exponential sizing on them would amplify a negative. That result
would itself be informative: it would show the tiers are not a valid conviction ranking.

## 3. The risk masterclass — four deliberately contrarian openers

He opens by attacking the standard advice:

- *"Do we always need to have a hard stop on our trades?"* — **No.**
- *"Should we ever violate our risk rules?"* — **"Maybe sometimes."**
- *"Is it okay to risk blowing up your whole account?"* — **"There are situations where it is."**
- *"Is undercapitalizing on big opportunities a sign of poor risk management?"* — **"100%."**

His definition: *"a set of processes and rules that allow you to **maximize the odds of achieving
your stated goals while minimizing the odds of encountering unacceptable outcomes**… risk
management is **not about maximizing safety**. It is about maximizing long-term expected value
while avoiding those outcomes that are unacceptable."*

⚠ Note how much weight "unacceptable" carries, and that it is defined per-person: a pension fund
cannot take a 20% drawdown; a hedge-fund trader's ruin may be "underperforming the market for
consecutive years"; a young trader may rationally risk 100% of a small account. **"Risk management
will always fundamentally be unique to the individual"** — which is honest but also means there is
no transferable number in 52 minutes.

## 4. Risk of ruin includes psychological ruin

> "A drawdown does not need to wipe out your account to fundamentally damage your ability to
> perform. **A loss large enough to destroy your confidence** [is ruin]."

> "Studies have shown that most people **greatly overestimate how much risk they think they can**
> [tolerate]… It sounds macho to think you could weather a 50% drawdown, but if your risk rules
> allow you to get there, experiencing it is a whole different thing."

This connects directly to the repo's own results: the best broad-universe configurations carried
**−50% to −58% drawdowns** before the regime filter, and −21% to −27% after
([`REGIME.md`](../../carter_mastering_the_trade/backtests/risk_architecture/REGIME.md)). By his
framing the pre-regime versions are untradeable regardless of their CAGR — not because the
arithmetic fails but because nobody executes them at the bottom. That is an argument for ranking
by **MAR rather than CAGR**, which is what the regime work ended up concluding independently.

## 5. Objective assessment

- **The "sometimes break your rules" framing is the most dangerous content in the KB**, and he
  half-acknowledges it by gating everything behind experience. For anyone without a measured edge
  it is licence to do the thing that kills accounts. Flag hard if any of this ever graduates.
- The interview format means the numbers are conversational asides, not a specified system —
  "$50-60 grand" is meaningless without knowing account size, which he never gives.
- Both videos are heavily philosophical and light on falsifiable claims. The dual-constraint
  passage in §1 is the single piece of hard content across 121k characters.
- ⚠ Kyle Williams is a friend and fellow course-adjacent trader; the interview is mutually
  flattering and contains no disagreement.

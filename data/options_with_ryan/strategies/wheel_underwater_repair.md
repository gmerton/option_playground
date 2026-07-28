# Below-Cost-Basis Covered Calls — repair protocol for deep-underwater wheel assignments

> **Verdict:** The most operationally specific video of the five — a real protocol with strikes, DTE, phase
> rules and a documented exit criterion. But it rests on the "not a loss until you sell" fallacy, and the
> asset-quality gates that decide hold-vs-fold were added *after* the one position (HIMS) they would have
> caught. Useful management grammar; unproven expectancy.
> **Conviction 2/5 · Risk 7/10 · Tested: no**
> Source: `videos/wheel/2026-03-01_9gkUoPpUJO8`. Context: assigned PLTR at 175/185, stock at 137 (−33% off highs).

## Mechanics (the protocol)

When assigned and the stock falls far below basis (CCs at basis yield <1%/mo):
- **Sell weekly CCs *below* cost basis: 8–12Δ, 7–10 DTE**, target 0.3–0.5%/wk while the stock consolidates.
- **Phase rules:** consolidation → keep rolling weekly at 8–12Δ. Moderate uptrend → roll strikes up each week
  (150→160→170) until back at basis, then revert to normal 30–45 DTE at-basis CCs.
- **Aggressive breakout (the risk case):** manage EARLY — buy back when the stock gets within ~$1–2 of the
  strike, book the small loss, **roll up-and-out 30–45 DTE to the original cost basis**. Cardinal rule:
  *never let shares be called away below basis.* (NVDA tariff-crash example: ~$4.5K premiums collected minus
  ~$1.5K buyback loss = ~+$3K net.)
- **Hold-vs-fold gates (all required to keep wheeling the name):**
  1. 18-month trendline still points up (drawn literally: today's price vs price 18mo ago);
  2. profitable company; PE < 100 OR cash ≈ covers debt;
  3. 30Δ/30-DTE put still yields ≥2%/mo (so re-entry pays once called away);
  4. **"double beat"**: beat EPS+revenue last quarter; zero tolerance for two consecutive misses w/ poor guidance.
  HIMS failed → sold at a loss ("the only realized loss in the portfolio").

## What checks out

- The early-management rule on breakouts is genuinely right for this structure: an 8–12Δ weekly call that
  goes ITM against you compounds fast; buying back at −$300 to protect a 20-point recovery is correct math.
- The premium arithmetic shown is honest about its smallness (0.3%/wk, "$41/contract").
- There IS a fold criterion — which is more than most "never sell" wheel content has.

## Red flags

1. **"You do not take a loss until you actually sell"** — stated verbatim. The whole protocol is anti-MTM:
   a −40% position yielding 0.3%/wk takes ~2.5 *years* of premium to fill the hole if the stock goes nowhere.
   Opportunity cost is never mentioned.
2. **The gates are post-hoc.** The double-beat rule was added *after* HIMS forced the loss. Every surviving
   position (PLTR, SOFI, HOOD, NVDA) "passes" — because the ones that wouldn't have passed are the losers,
   and there's exactly one of those acknowledged in five claimed years of +40%/yr returns.
3. **The 18-month trendline gate is a momentum filter with a 1.5-year lag** — it keeps you in anything that
   already had a huge run (it kept PLTR "wheelable" at −33%) and would have kept you in every 2021 darling
   through 2022. It's the survivorship generator dressed as risk management.
4. **Concentration & sequencing risk unpriced:** his own account was −18% at the tariff-crash bottom.
   "40% annually for 5 years straight" coexists with that only in a market where every dip V-recovered.
   The protocol has never met a dip that didn't come back (his one exception: HIMS, sold).
5. Caps the recovery leg: to earn 0.3%/wk you hand back the right tail of the exact rebound the thesis needs
   — mitigated by the roll-early rule, but the NVDA example shows the cost is real.

## Relevance to us

Directly applicable question for our own book (e.g., wheel assignments from MRVL/NBIS-class CSPs): **is
8–12Δ/7-10DTE below-basis premium worth the breakout give-back vs just holding assigned shares?** That's a
clean, falsifiable comparison. His phase/roll grammar is worth encoding even if his hold-forever premise isn't.

## Testability

**Medium-high.** Path-dependent but EOD-clean: simulate assignment episodes (stock −20% through −50% below
basis) on liquid names from Athena data; compare (a) his protocol, (b) plain hold, (c) sell + redeploy, over
2018–2025 including 2022 (the case where "it always comes back" fails for 2+ years). The 2022 cohort of
fallen wheel names (PYPL, SQ, ARKK-class) is the out-of-sample his examples omit.

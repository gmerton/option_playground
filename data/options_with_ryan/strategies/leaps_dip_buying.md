# LEAPS Dip-Buying — 70Δ 400+ DTE calls on oversold "approved" stocks

> **Verdict:** Reasonable entry gates wrapped around a backwards exit policy: he cuts winners at +10–40% in
> days-to-weeks but holds losers ("I have 497 days to be right") through 65% drawdowns — the disposition
> effect codified as a system. Backtest evidence is one cherry-picked 12-month window on a stock that 4×'d.
> **Conviction 1.5/5 · Risk 7/10 · Tested: no**
> Source: `videos/leaps/2025-09-07_vZgrQgk4IlI` ("LEAPS Masterclass"). Sized at ~10% of his portfolio ("icing on the cake").

## Mechanics (as stated)

- **Vehicle:** long calls, **~70Δ, 365–500 DTE** (he prefers 400+). Never held to expiry; hard rule: close by
  **90 days before expiration** to salvage premium.
- **Stock gates:** same as the wheel's — 18-month uptrend line, PE < 100, profitable ("95% of stocks don't
  qualify"; AMD and COIN-class negative-earners excluded; example approved name: HOOD).
- **Entry timing (all should line up):** price at/below **lower Bollinger band** (mid-band OK for beta>2 names);
  **RSI ≤ ~40**; **MACD** basing/anticipating a cross; **VIX > 15** (below 15 = complacency top, no entry).
- **Exits:** +10–20% within ~7 days → take it; +20–40% within ~4 weeks → take it; >100% ever → definitely take
  it. If down: hold ("time to be right"), exit at the 90-days-to-expiry line regardless.

## What checks out

- 70Δ/400+DTE as stock replacement is a legitimate structure: modest theta, mostly intrinsic, survivable timing errors.
- The VIX<15 no-entry rule is a real (if crude) complacency filter, and the 90-day salvage rule prevents the
  classic long-option bleed-to-zero ending.
- He's candid about leverage: his own backtest shows **65% max drawdown** on the option vs 47% on the stock.

## Red flags

1. **The exit asymmetry is the strategy, and it's backwards.** Quick profit-taking on winners + "wait for the
   rebound" on losers = systematically capped right tail, fat left tail — on a *long-options* book whose whole
   justification is convexity. (Cf. our Adhikary finding: the money is in cutting losers fast and letting
   winners run; this does the exact opposite on both sides.)
2. **Evidence = HOOD, Sep-2024→Sep-2025**: buy-and-hold +438%, LEAPS +1,172%. A 12-month window on one of the
   best-performing large caps in the market proves leverage works when the stock quadruples — nothing else.
   The "every day when VIX>15" backtest entry also bears no resemblance to the Bollinger/RSI/MACD entry taught.
3. His cautionary tale (clients holding AMD LEAPS too long) is an argument *against* his own hold-losers rule,
   resolved only by the post-hoc observation that AMD "wasn't on my approved list."
4. Indicator stack is soft: Bollinger "95% containment" is by construction; MACD anticipation is discretionary;
   nothing here is a defined, repeatable trigger you could code without choices.
5. "I charge thousands for this in my mastermind" — the content is a generic mean-reversion entry checklist.

## Relevance to us

- Contrast with our own LEAPS work: **Sleeping Giants** buys cheap LEAPS on multi-year-base breakouts (low IV,
  convex right tail, exit is the unbuilt lever) — momentum-continuation logic. Ryan's version is
  **mean-reversion dip-buying on extended leaders with the tail capped at +40%**. Same vehicle, opposite trade.
  His IV awareness is also thinner: no IV-rank gate at all (VIX>15 is the only vol condition, and it *raises*
  the premium he pays).

## Testability

**High.** All rules are daily-bar computable except MACD discretion: Bollinger touch + RSI≤40 + VIX>15 entries,
70Δ 400DTE BS-repriced calls (or real chains where Athena has them), his tiered exits vs. (a) hold-to-90-days,
(b) a trailing exit. The interesting question isn't whether it made money 2023–2025 (everything long did) —
it's whether the quick-profit tiers *underperform* simply holding the same entries, which the disposition-effect
critique predicts.

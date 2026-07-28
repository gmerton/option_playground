# ZEBRA (Zero Extrinsic Back Ratio) — Fauzia Timberlake

Source: `2026-04-12_ab5VmEh49Ek` — "How To Control 100 Shares With Less Money (ZEBRA Strategy
Explained)" ([watch](https://www.youtube.com/watch?v=ab5VmEh49Ek)). Guest: Fauzia Timberlake, Las
Vegas NV — engineer by training, former wire-house financial advisor, ~12 yrs trading options,
self-taught via tastytrade; also **mentors/coaches** options traders (soft motive). Host: John. The
ZEBRA is **not her strategy** — she attributes it to tastytrade (Liz & Jenny / "Tony Battista"),
"a fairly old strategy" (`@30:39`), so this is a walk-through of a well-known public structure, not
a proprietary edge.

## Verdict

> **Conviction: 2/5 · Risk: 4/10 (defined-risk debit, but leveraged 1:1 directional) · Tested: NO**
> A stock-*replacement* structure, not an income edge: buy 2 ITM calls / sell 1 ATM call to build a
> ~100-delta long with almost no extrinsic value, for a fraction of the cost of 100 shares. The best
> thing about this interview is the presenter's honesty — she states plainly that it is **"purely
> directional… there's nothing neutral about it"** and that results **"depend on your ability to
> pick the right direction"** (`@27:17`, `@27:58`). That candor, plus a legitimately correct
> break-even analysis vs. the other cheap 100-delta structures, lifts it above the pure-marketing
> tier. The cap is that **there is no edge in the structure and none is claimed** — zero win rate,
> zero ROC, zero track record, zero sample size are given anywhere in 33 minutes. It is leverage on a
> direction call, and the "defined / low risk" framing quietly understates that losing 100% of the
> debit is routine (the stock only has to drift, not go to zero). A clean tool, honestly presented,
> but nothing here to bank as alpha.

## Mechanics

- **Underlying:** any optionable stock/ETF you are outright **bullish** on (call ZEBRA) or bearish on
  (put ZEBRA, the mirror image, `@26:41`). Example shown: **OKLO** (Oklo). `@05:37`
- **Structure (call ZEBRA):** **buy 2 ITM calls, sell 1 ATM call**, same expiration → net **~90–100
  delta** ("dynamic stock position") with **minimal net extrinsic**. Example: buy 2× May 40 calls,
  sell 1× May 50 call; debit **$16.85**, net delta ~**103**, net extrinsic ~**−$0.25**. `@03:43`,
  `@05:49`, `@07:33`
- **The "zero extrinsic" logic:** each ITM long call carries ~$2.20 extrinsic (read off the same-strike
  put); buying 2 = ~$4.40 to neutralize; the ATM short call sold for ~$5+ collects roughly that much
  extrinsic back → net extrinsic ≈ 0. So (mostly) only intrinsic is paid. `@04:26`, `@07:03`
- **Strike/delta selection:** longs are ITM enough that extrinsic is small; short is ~ATM (~50Δ).
  "Come in closer and pay less duration" rather than buy cheaper (further-ITM) longs — don't shortcut
  the extrinsic. `@30:11`
- **DTE:** trader's choice; further out = more expensive but more time to manage and to sell front-month
  calls against it. "For every gimme there's a gotcha" (Dr. Jim, tastytrade) — more time costs more.
  May vs June example: ~$100 more for a month of duration. `@11:58`, `@12:25`
- **Entry conditions:** wants to get long a name; prefers **low IV** (example IV rank ~35, "would prefer
  ~20"); a beaten-down chart she's comfortable turning bullish on. `@10:56`, `@11:14`
- **Covered ZEBRA (optional income overlay):** sell a **30-delta front-month call** against the ~100-delta
  synthetic long (= a covered-stock analog) to reduce cost basis; keep selling calls on down moves.
  `@13:54`, `@14:16`
- **Profit target:** discretionary — e.g. **50%** of debit, placed as a **GTC** order. No fixed rule.
  `@15:40`, `@15:54`
- **Stop / max loss:** she **does not use stops**; max loss = the debit paid (if never managed).
  `@25:35`, `@23:40`
- **Adjustment ("ratchet"):** on an adverse move the strikes re-acquire extrinsic; you **close the
  extrinsic-laden legs and reopen a new zero-extrinsic ZEBRA further out** — done for a **debit** =
  realizing part of the loss and raising basis, then waiting for the stock to recover. `@16:29`,
  `@17:12`, `@18:32`
- **Sizing:** capital = the debit; "how much buying power the trader wants to tie up." `@13:39`
- **Self-rated risk:** **"low risk"** because "my risk is defined at entry." `@24:23`, `@24:36`

## Claimed edge & returns

- **No performance numbers of any kind.** No win rate, no ROC, no P&L history, no sample size, no
  years. When asked directly for results (`@26:03`) she answers only "pleased with them… it seems to
  work… the expectation is the same as buying long stock." That is the entire evidentiary basis.
- **Capital-efficiency claim (the only "number"):** OKLO ZEBRA costs **$1,685** vs **~$4,800** to buy
  100 shares — real and arithmetically true. `@11:00`, `@20:04`
- **Single illustrative payoff (theoretical, model-drawn):** if OKLO is 55 at May expiry, the tastytrade
  analysis tab shows **~$800 profit** on the $1,685 debit, with a stated **~35% probability** of getting
  past the short strike by then. This is a platform projection, not a realized fill. `@08:49`, `@09:16`
- **Comparison claims (correct):** vs synthetic long (buy ATM call / sell ATM put) the ZEBRA has a far
  better break-even (right at spot vs. ~$3.93 above); vs buying 2 ATM calls (~$790, ~$908 extrinsic) the
  ZEBRA wastes far less time value. She uses these to argue the ZEBRA is the most break-even-efficient of
  the cheap 100-delta builds. `@20:39`, `@21:50`, `@22:59`

## Objective assessment (where to be skeptical)

1. **There is no edge, and — to her credit — none is claimed.** The ZEBRA is a *leverage/financing
   vehicle*, not an income or vol strategy. Its P&L is the underlying's move times ~100 delta, minus a
   little extrinsic and three-leg costs. She says so explicitly: "**depends on your ability to pick the
   right direction**" (`@27:17`), "**this is outright bullish… nothing neutral about it**" (`@27:58`).
   So the whole return comes from a direction call the structure supplies zero help with. Evaluating the
   ZEBRA is therefore evaluating *your own direction model*, which the video does not provide.
2. **"Low risk / defined risk" understates the loss profile.** Yes, max loss = debit. But this is a
   **~100-delta leveraged long**: the stock only has to *drift down to the long strike* (not go to zero)
   for the position to bleed toward and reach a **100% loss of the debit**. Her risk framing leans on a
   strawman — "much less than if your stock went to zero" (`@23:54`) — but stock rarely loses 100%, while
   a ZEBRA reaching full max loss is an ordinary, high-probability event on a moderate adverse move. Per
   *dollar deployed*, this is more likely to be a total loss than owning the shares.
3. **The "ratchet" is loss deferral dressed as management.** Rolling the losing ZEBRA down/out "for a
   debit" (`@17:42`) = crystallizing a loss and adding fresh capital to a losing directional bet at a
   higher basis. It converts a clean defined-risk trade into a potentially open-ended averaging-down
   sink if you keep chasing. She concedes it "is essentially the same as recognizing the loss"
   (`@17:12`) — correct, and worth stating that the ratchet has **no positive expectancy of its own**.
4. **"Zero extrinsic" is an entry-only, ATM-only property.** The net extrinsic is ~0 *at setup while the
   short is near ATM*; she admits that on an adverse move "these strikes start gaining extrinsic value"
   (`@16:43`), which is exactly when it hurts. And "zero extrinsic" ignores the **bid/ask on three legs
   at entry (six on every ratchet)** — never netted anywhere.
5. **Edge over a plain deep-ITM call is small.** The ZEBRA's advantage over just buying one deep-ITM
   (~90Δ) LEAP call is only the incremental extrinsic saved by the 2-1 ratio around the short. That is a
   few tenths of a point of time value — real, but easily eroded by the extra legs' spread costs and by
   the reappearing extrinsic on any adjustment.
6. **No track record, benign framing, mild motive.** Zero separable evidence; she **mentors/coaches**
   traders (`@31:33`) and repeatedly funnels to the tastytrade learn center (`@30:39`, `@31:44`) — a
   platform affiliation, not a hard course sale, but a motive. The one payoff shown is a favorable
   OKLO-at-55 projection (winners-friendly, model-priced).

## What's genuinely sound (the diamond)

- **Unusually honest, low-hype presentation.** She volunteers that it is purely directional with no
  structural edge, that returns hinge on direction-picking, and that the ratchet is just realizing a
  loss. No "risk-free," no win-rate boast, no invented ROC — a refreshing contrast to most of this KB.
- **The break-even comparison is correct and pedagogically useful.** Among the cheap 100-delta builds
  (synthetic long, 2 ATM calls, single ITM call), the ZEBRA genuinely does have the break-even closest
  to spot *because* it zeroes extrinsic — a real, well-explained property, not marketing.
- **Legitimate, documented, public structure.** It's the established tastytrade ZEBRA; anyone can verify
  the mechanics independently. Defined max loss = debit at entry, no naked short, no assignment surprise
  while the short stays OTM/ATM.
- **Sensible entry hygiene:** prefers low IV (you're a net buyer of options), and the covered-ZEBRA
  overlay (sell 30Δ calls) is a coherent cost-basis-reduction analog to covered stock.

## Backtestability

- **The structure is a defined multi-leg EOD build on equities/ETFs** — buy 2 ITM calls + sell 1 ATM
  call, same expiry — which `silver.options_daily_v3` (thousands of equities/ETFs, full greeks +
  bid/ask, daily) *can* approximate at the close. So the mechanical skeleton is representable.
- **But the honest floor is that there is almost nothing strategy-specific to test.** Because the ZEBRA
  is pure directional leverage, a backtest of "does the ZEBRA make money" is really a backtest of the
  **direction signal you feed it** — which the video supplies none of. The only *structure* questions
  worth testing are relative: **does a ZEBRA beat a single ~90Δ ITM LEAP call, 2 ATM calls, or a
  synthetic long on the same name and horizon, after modeled multi-leg fills?** That comparison is
  testable and is the meaningful null. Warn that the extrinsic edge is small enough that mid-vs-intrinsic
  fill assumptions on 3 legs can swamp it.
- **The ratchet is discretionary and path-dependent** (when to roll, how far out) → not faithfully
  testable without inventing an adjustment rule the trader never specified.
- **OKLO specifically** is a recent listing with thin option history — pick liquid, long-history names
  for any structure-comparison test.

## Open questions / next step

- What direction filter, if any, does she use? None is disclosed — without one there is no P&L to
  attribute to the strategy, only to the underlying's drift.
- On a matched name/horizon, does the ZEBRA's zeroed-extrinsic actually beat a plain deep-ITM call after
  three-leg spread costs, or does the extra leg give the edge back?
- Over a full sample, how often does the position hit ~100% loss of debit vs. how often the underlying
  itself would have lost that much — quantifying the leverage the "low risk" framing hides.
- **Next step (on command only):** if ever pursued, this is a **structure-comparison** study under
  `backtests/zebra_back_ratio/` — ZEBRA vs. deep-ITM call vs. 2 ATM calls vs. synthetic long on a basket
  of liquid names, holding the direction signal constant — not a standalone edge backtest. Low priority:
  it's a well-known public leverage vehicle with no claimed or evident alpha.

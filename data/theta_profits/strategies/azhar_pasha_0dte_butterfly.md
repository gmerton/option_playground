# 0DTE Adaptive (Broken-Wing) Butterfly — Azhar Pasha

> ⚠ **Same trader** as [`gold_futures_credit_spreads.md`](gold_futures_credit_spreads.md) (his
> /GC gold-futures credit-spread interview). The gold trade exposes the same "never take a loss /
> roll / add size" tail this one hints at — read them together.

Source: `2025-10-19_YREhrh408Bs` — "10% a Month? Inside Azhar Pasha's Adaptive 0DTE Butterfly
Strategy for SPX Traders" ([watch](https://www.youtube.com/watch?v=YREhrh408Bs)). Guest: Azhar
Pasha (auto-captions garble the name to "Asar/Assaar"), an anesthesiologist / interventional-pain
physician in private practice 22 yrs, ~5 yrs full-time options trading, scaling down medicine to
2 days/week; host: John. **No product, course, Discord, or software is sold** — he's a retail
practitioner describing his own book, not a vendor. Track record is **3 months old.**

## Verdict

> **Conviction: 1.5 / 5 · Risk: 5 / 10 (defined-risk 0DTE flies, but discretionary flips + adverse-move size-adding) · Tested: NO**
> A 1-3-2 broken-wing butterfly on SPX 0DTE: one debit spread "facing the market" as a shield in
> front of two OTM credit spreads, entered for a small net credit, hand-managed all day to close
> near zero debit — and *adaptively flipped* put→call (or vice-versa) when the market runs against
> it, financed by the now-ITM debit spread. The genuinely sound idea is the debit-spread shield: it
> converts a potential 100% credit-spread loss into a ~50% loss and buys time to react — a real,
> honest improvement over selling a naked 0DTE vertical. The problem is everything the headline rests
> on: **"~10% a month" (~3× a year) over a 3-month, self-reported, strongly-bullish sample** with
> "one 0.01% loss day," a strategy that is **pure discretionary intraday management** (GEX-reading +
> feel), and an adjustment path — flip, then **add contracts to "stay positive"** on a second
> reversal *after* the debit shield is spent — that hides the exact martingale tail he rates away as
> "4/10." No sales motive and fair candor keep it off the floor; no separable evidence and an
> extraordinary claim in a benign regime keep it at 1.5.

## Mechanics

- **Underlying:** SPX 0DTE, cash-settled; explicit goal to be **100% cash every night** — same-day
  rolls only, never carried overnight. `@00:43`, `@01:41`, `@21:48`
- **Structure (1-3-2 broken-wing put butterfly, or call side):** on the example with SPX ~6620,
  **+1× 6600P / −3× 6590P / +2× 6570P**. Read as **one debit spread (6600/6590) sitting in front of
  two credit spreads (6590/6570)**. Chooses the put-side BWB on green/up-bias days, call-side on
  red/down-bias days — **trades with the morning trend, never counter-trend.** `@07:26`, `@00:43`,
  `@22:17`
- **Entry timing:** **pre-market or at the open** to "maximize implied volatility and get the most
  premium." No other filters — "I try to keep it very simple." `@09:57`, `@10:14`, `@12:06`
- **Strike selection:** buy the strike **facing the market at 5–10 delta**, chosen to coincide with
  a **dealer long-gamma strike** (per GEX data); short strikes **~10 points** below/above the long;
  the two far longs **~15–20 points** beyond the shorts (the "broken" wing that yields the credit).
  `@10:29`, `@11:23`
- **Net credit target:** **≥ $0.40**; the near-money debit spread is paid for out of the two credit
  spreads' premium. `@11:52`, `@12:06`
- **Profit management:** immediately rest a close order on the credit spreads at **$0.10 debit**,
  then **sell the debit spread back for ≥$0.05** — net closing the whole thing for ~zero debit,
  keeping the entry credit. Ideal exit ~**2–2.5 hrs** in. `@20:06`, `@20:23`
- **Adaptive flip (the "edge"):** if price runs toward the shorts, **monetize the now-profitable
  debit spread** and **flip the credit spreads to the opposite side**, placing the new shorts at a
  GEX dealer level for resistance/support. Friday example: had a 6670/6650 credit pair + 6670/6680
  debit (entered 40¢), market fell ~90 min in with VIX ~19–20, flipped to a **6700/6720 call credit
  spread at a credit** and sold the debit back for ~**$2**; the call side expired for full profit.
  `@01:11`, `@14:01`, `@17:45`
- **Second reversal (chopfest):** if it whipsaws *again*, **the debit shield is gone**, so he may
  "flip again" and **increase the number of contracts to stay positive / get a credit.** Explicitly
  "not ideal." `@23:37`
- **GEX / dealer positioning:** the central discretionary input — reads live gamma-exposure
  dashboards to place longs at market-maker long-gamma strikes (claimed support/resistance), because
  dealers hedge back toward neutral. Calls it "an MRI of the market"; "flying blind" without it.
  `@05:32`, `@14:33`, `@30:07`
- **Sizing:** starts each day using **~20% of account BP**, deliberately leaving room to **add
  contracts** for intraday flips. Account **$106K** (IBKR portfolio-margin minimum). `@27:44`,
  `@28:31`
- **Worst case / self-rated risk:** if it slices through the short strike while unattended, loss is
  **~50%** (not 100%) because the debit spread is fully ITM to offset. Self-rates **4/10**, vs 8–9
  for a naked SPX credit spread. `@24:23`, `@25:38`

## Claimed edge & returns

- **"On average about 10% a month"** — stated twice, first line of the video. `@00:00`, `@21:34`
- **~39–45 bps/day** target; "some days less, some more." `@27:11`
- **3 months traded; exactly one losing day at −0.01%** (forgot to close a debit spread). `@27:11`
- **Account $106K → "up around $30,000"** over the three months (~28%). `@28:31`
- Says he's applied the same BWB on other index options, stocks, **gold & crude-oil futures**
  options, but finds SPX the best fit. `@31:27`
- **All numbers are self-reported from IBKR Portfolio Analyst** — no separable log, no third-party
  audit, no per-trade record shown. `@26:42`

## Objective assessment (where to be skeptical)

1. **"10% a month" on a 3-month sample is the whole review.** ~10%/mo compounds to ~**3×/year**,
   which if real would be an extraordinary, top-decile-professional result — from a part-time
   physician, unlevered-sounding, in his first quarter running the strategy. Extraordinary claims
   need extraordinary evidence; three months is not a track record, it's a sample too short to
   contain a single bad tail event. Provisional at best.
2. **The near-100% win rate is vacuous — it's P(managed it in time) in a one-directional bull.** One
   −0.01% day in three months isn't precision, it's the signature of a benign regime: he himself
   says the "pain trade is to the upside," anyone short since April lost, and he only trades *with*
   that trend. `@22:48`, `@23:07` The entire risk of the structure lives in the fast gap-through
   that this window simply didn't deliver. The win rate measures the absence of the tail, not the
   presence of an edge.
3. **The "50% max loss" is the best case of the bad case, not the max.** The 50% figure assumes the
   shield stays intact and only *one* side slices. But he describes a worse path himself
   (`@23:37`): flip when the shield's spent, then on a *second* reversal **add contracts to stay
   positive** — that is adding size into an adverse move to average back to a credit, the same
   mechanic that blew up the 1-1-2 trader in this KB. After the debit spread is monetized and gone,
   the flipped credit spreads are a **single-side directional 0DTE bet with no shield**, and 0DTE
   gamma on a headline can move faster than any hand can flip. His self-rating of 4/10 prices the
   shielded case and ignores this path.
4. **This is 100% discretion, not a strategy you can hand to a rule.** Every profit-determining
   decision — which side to open (morning "bias" from the dollar and 10-yr), where the GEX levels
   are, when to flip, where to re-strike, whether to add size — is real-time judgment. The results
   are inseparable from his intraday attention; he's emphatic it "cannot be set and forget" and he
   *doesn't trade it on days he practices medicine.* `@29:04` So there is no mechanical object to
   reproduce or falsify.
5. **GEX is treated as more reliable than it is.** Dealer long-gamma *does* dampen moves — until
   gamma flips negative (dealers short gamma), in which case hedging **accelerates** moves, exactly
   on the down-days the shield is meant to survive. Calling dealer levels an "MRI" and near-"foolproof"
   (`@13:44`) over-trusts a signal that inverts precisely in the regime that matters. Levels also
   shift intraday, which he acknowledges but still leans on for the flip re-strikes.
6. **The per-trade edge is razor-thin and cost-heavy.** He enters for ~40¢ and works to close the
   whole thing for ~zero debit — a **6–7-leg** 0DTE structure managed with resting orders and at
   least one full flip (another 6+ legs). Commissions + bid/ask on that many 0DTE legs, plus the
   slippage on fast flips, are a large fraction of a 40¢ credit. None of the headline is netted
   against realistic multi-leg transaction cost.
7. **Credit given up front for the shield is a permanent drag.** He concedes the near-money debit
   spread "gives up some of the credit received." That's the honest price of protection — but it
   means the good-day payoff is structurally small, so the strategy *needs* the near-perfect hit
   rate of a benign tape to compound; a normal mix of chop days erodes it.

## What's genuinely sound (the diamond)

- **The debit-spread shield is a real, correct improvement over a naked 0DTE vertical.** Converting a
  possible 100% loss into ~50% and — more importantly — **buying reaction time** before the shorts go
  ITM is a legitimate structural idea, and monetizing that ITM debit spread to *finance the flip* is
  a clever use of the hedge. This is the honest core.
- **Disciplined defaults:** all-cash overnight (no gap risk), defined-risk contract-balanced flies,
  trade-with-trend only, small starting size (20% BP), a hard "don't trade it when you can't watch"
  rule. `@21:48`, `@29:04`
- **No sales motive and candid about limits:** no course/software/Discord; openly says it needs
  constant attention, admits the 50% unattended loss, admits the chopfest problem and the size-add,
  and warns about headline/Fed-speaker risk. Above-average honesty for the channel — the reason it's
  1.5 and not 1.0.

## Backtestability

- **Not faithfully testable on our stack — this is a hard 0DTE null.** The strategy is *defined by*
  intraday behavior: open-IV entry, GEX-level strike placement, a mid-day flip, possible second
  flip with size-adds, and a same-day near-zero-debit close. `silver.options_daily_v3` is
  **EOD-only** (daily bars), so none of the timing, the flip, or the management — i.e. the entire
  edge — is representable. Coverage of the *instrument* (SPX 2010→2026-02, full greeks) is fine; the
  *resolution* is the wall.
- **What a skeleton could show (and its honest floor):** a *static, held-to-expiry* SPX 1-3-2
  broken-wing put/call fly at 5–10Δ long / ~10-pt short / 15–20-pt far wing, entered near-open for
  ~40¢ credit, **no management, no flip** — would measure only the raw expiry distribution of the
  bare structure. That deliberately strips the shield-timing and the flip (the whole point), so it
  would understate his discretionary record and tell us little about *his* results — it would only
  answer "is the un-managed fly positive-EV?" Even that is approximate: 40¢ credits get eaten by
  modeled multi-leg fills marked at mid.
- **Futures version untestable:** the gold/crude-oil-futures application is out of scope — futures
  options aren't in the table.

## Open questions / next step

- Does the record survive a real down-trend / high-vol stretch? The 3-month sample is entirely a
  benign up-tape with the shorts rarely tested — the strategy has never met the gap-through it's
  built to survive.
- On a common denominator (account NAV, after realistic 0DTE multi-leg commissions + slippage on
  entries *and* flips), what's the net? The ~40¢ credit leaves little room.
- How often does the "second flip + add contracts" path fire, and what's the loss distribution when
  it does? That, not the shielded 50% case, is the tail.
- Related 0DTE-defined-risk analogs already in the KB: `pulver_0dte.md`,
  `zerodte_breakeven_iron_condor.md` (MEIC) — same thin-edge-vs-cost economics apply.
- **Next step (on command only):** at most a static-held SPX BWB skeleton under
  `backtests/azhar_pasha_0dte_butterfly/` to bound the *un-managed* fly's EV — but flag up front
  that it cannot represent the discretionary flip/GEX management that produces his numbers, so it's a
  weak floor, not a test of the strategy. Realistically **not worth prioritizing** over testable
  EOD structures.

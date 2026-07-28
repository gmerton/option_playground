# Multiple-Entry Iron Condor (MEIC / "MEIC plus") — Tammy Chambless

Source: `2025-09-24_o-CmLEeiaoU` — "Tammy Chambless Explains Her 0DTE Options Iron
Condor Strategy" ([watch](https://www.youtube.com/watch?v=o-CmLEeiaoU)). A "Theta Live"
excerpt. Guest: Tammy Chambless, a well-known retail 0DTE backtester/educator (referenced
approvingly in the channel's automation interviews as a MEIC authority); host: John. She is
explicit that she **did not develop MEIC** — several people built it and she "put her own spin
on it" (MEIC plus). Low direct sales motive: she recommends third-party tools (TAT/BYOB, Option
Omega, Trade Steward) she doesn't appear to sell, and points to her own longer free videos.
Transcript is short (~57 blocks / 14 min) but unusually dense and specific for this channel.

## Verdict

> **Conviction: 2.5 / 5 · Risk: 5 / 10 (defined-risk 0DTE condor, fast-move/gap slippage tail) · Tested: PARTIAL (skeleton only — MEIC proper is 0DTE-intraday, untestable on EOD; see `backtests/tammy_chambless_0dte_ic/`)**
>
> **🔬 Skeleton backtest finding (2026-07-05): the edge is the STOP, not the premium.** A 1DTE SPX
> IC held to expiry on real prices (2016–2025) is **net-NEGATIVE with no stop** (−$0.21 to −$0.81/lot
> full-sample, ~breakeven-to-negative even in her benign 2023–25 window) — high win rates swamped by
> trend-day losers. Cap each side's loss at 2× credit (≈ her per-side stop) and it turns **positive
> every year including 2022** (+$2.27 to +$4.92/lot). So MEIC is a **loss-capping edge, not a
> premium-harvesting edge** — which is exactly why she obsesses over broker stop-handling, and why
> the edge is un-improvable on our EOD stack (it lives in intraday stop execution). Her live ~20.7%
> vs 33% backtest is the whipsaw+slippage leak the optimistic cap can't see. Details: RESULTS.md.
> The single best-evidenced 0DTE iron-condor presentation in this KB. Same VRP-harvesting family
> as Yona's and Pulver's condors, but Tammy clears the bar higher on three counts the mandate cares
> about: (1) she gives **near-complete, reproducible mechanics** (entry cadence, credit targets,
> widths, per-side stops, sizing) rather than a fuzzy "feel"; (2) she shows a **separable BYOB
> backtest reconciled against a multi-year live record** — and her live result *underperforms* the
> backtest (~20.7% avg live vs 33.3% CAR backtest), which is the anti-oversell tell; (3) she did
> **real, quantified work on slippage and broker stop-handling**, the exact cost that eats this
> thin edge. The cap: it is still self-reported (slides, not audited statements), the 2023–2025
> sample is a benign, mostly low-vol/up regime, and it is **0DTE intraday** — untestable on our
> daily data and reliant on same-day hand/auto-management. She is honest about all of this. That
> honesty, plus reproducible mechanics on the correct (1-min) resolution, is why she ties the
> current 2.5 ceiling — not above it, because nothing here is independently audited.

## Mechanics

- **Underlying:** S&P (SPX), **0DTE** — cash-settled, "no overnight risk" is her stated headline
  advantage. `@01:01`, `@03:25`
- **Structure:** a standard **iron condor** legged in **multiple times per day** (MEIC). Sell a put
  spread + a call spread; profit if price stays between the short strikes. `@03:25`, `@05:04`
- **Entry cadence:** **6 trades/day, ~30–60 min apart, generally late-morning through afternoon.**
  `@03:25`
- **Credit target:** **$1.00–$1.75 credit per side** (recently *reduced* due to lower vol); higher
  credit → larger drawdowns "in my experience." `@03:41`
- **Width:** **50–60 wide typical, up to 100 wide** — deliberately wide so the long leg costs as
  little as possible. `@04:09`
- **Stop:** **1× net loss = 2× the initial credit**, set on **each side separately** (not on the
  whole condor). E.g. collect $150 on a side → stop that side at $150 loss. Leave every trade on
  until it either stops or expires worthless. `@04:24`, `@05:32`
- **Stop mechanics (a genuinely useful detail):** use **market** stops, not stop-limit (CBOE
  changes made stop-limits blow through); place stops on **single legs held at the exchange** for
  lowest slippage; and **remove the long leg from the stop once it's worth <5¢** — a sub-nickel
  option won't fill, so a spread stop containing it never triggers. `@01:16`, `@02:00`, `@12:01`
- **"MEIC plus" tweak:** ~**30% of days end at break-even**; to monetize them she sets the stop
  **10¢ tighter than the 1× net stop** (on a $1 credit, stop at $1.90 instead of $2.00). If one
  side stops and the other wins, the loss is slightly smaller than the win → a small profit on
  otherwise-break-even days. `@06:30`, `@07:04`
- **Sizing / risk cap:** **no more than 2% of account risked per trading day** — total across all
  sides such that being stopped out of *every* trade is < 2% loss. Plus the tastytrade rule: never
  risk **>50% of buying power** in a day (BP ≈ width − credit). `@08:16`, `@08:32`
- **Account minimum:** ≥ **$30,000** to avoid pattern-day-trader rules. `@00:44`
- **Automation:** rules are mechanical → she runs it via **TAT (Trade Automation Toolbox)** and
  **Trade Steward**. Backtests on **TAT BYOB or Option Omega, both 1-minute data.** `@02:28`,
  `@04:38`

## Claimed edge & returns

- **Backtest (BYOB, Jan 2023 → Sep 5 2025):** **33.3% CAR**, **max drawdown 7.41%**, **Calmar 4.5**,
  **~15,000 trades** over ~2.75 years. Self-run, on public 1-min tooling. `@08:59`, `@11:12`
- **Live trading:** **avg ~20.7%**; 2023 and 2024 "very close to 30%" each; **2025 flatter**
  (stated reasons); **live max drawdown 4.3%** (during "the election," where she scaled way back);
  **live Calmar 4.86** (higher than backtest, on the lower DD). `@00:00`, `@09:36`, `@10:09`
- **Daily shape:** all-positive day → +2%; all-negative day → −2%; most days land between 0 and ~1%
  either way, with more trades finishing positive than negative. `@10:37`
- **Anecdote:** "yesterday stopped out of every call, today stopped out of every put" — still made
  money both days via the MEIC-plus tweak. `@07:38`

All figures are **self-reported**, shown on slides in the video; no third-party-audited brokerage
statements are presented.

## Objective assessment (where to be skeptical)

1. **Not a new edge — it's crowded MEIC.** She says so herself (`@06:30`): she didn't invent it.
   This is the same 0DTE VRP-harvesting condor already covered in
   `zerodte_breakeven_iron_condor.md` (Yona) and `pulver_0dte.md`. The skeptical economics there
   apply here too: the per-side stop = 1× net = ~2× credit means a stopped side roughly cancels a
   winning side, so the whole book leans on **P(intraday range holds)** — a bet on small moves.
2. **Live is 37% below her own backtest.** ~20.7% live vs 33.3% CAR backtest is, to her credit, the
   number she leads with — but it *quantifies the 0DTE backtest-optimism haircut*: even an honest,
   careful operator loses roughly a third of the modeled return to real fills, slippage, and
   scaling back in stress. Any backtest we or anyone runs on this family should be discounted
   similarly before believing it.
3. **Benign regime.** Jan-2023→Sep-2025 is a mostly low-vol, up-trending stretch (post-2022 bear).
   The MEIC tail is a **fast trending/gap day** where the losing side's stop fills *worse than
   width* and, on a whipsaw, both sides can stop. Her 7.4% backtest / 4.3% live max DD are drawn
   from a sample largely missing a sustained high-vol trend. She names "the election" as the worst
   patch and admits she scaled down through it — i.e. the good live DD partly reflects
   *discretionary de-risking*, not the mechanical rules surviving unaltered.
4. **"No overnight risk" ≠ no tail.** True that 0DTE avoids gap-through-the-night, but the
   advertised virtue hides an intraday tail: a limit-move / illiquid-seconds gap can fill a
   single-leg market stop far from the trigger. She's honest that a "nuclear disaster / market
   shutdown" full loss "could happen" (`@05:47`), and the entire October-2025 slippage episode
   she describes is that tail showing up in miniature.
5. **Self-reported, not separable in the Simon-Black sense.** Unlike Time Flies (weekly-published +
   independent host replication), Tammy's live numbers are slides in a video — reproducible *in
   principle* on BYOB/Option Omega, but not independently audited or witnessed. Reproducible
   mechanics ≠ verified results.
6. **Thin per-trade edge vs 6×/day cost drag.** 6 condors/day × ~250 days ≈ 1,500 condors/yr (she
   cites ~15k trades / 2.75yr counting sides). Commissions + bid/ask on 0DTE spreads + stop
   slippage are exactly what erode a small credit — which is *why* she obsesses over broker stop
   handling. That obsession is a strength, but it also concedes how close to the margin the edge is.

## What's genuinely sound (the diamond)

- **Reproducible mechanics on the right data.** Entry cadence, credit targets, widths, per-side 1×
  stops, and the 2%-daily cap are specified precisely enough to backtest — and she backtests on
  **1-minute** data (BYOB/Option Omega), the correct resolution for 0DTE. This is the methodological
  stance the automation guests (Kyle Lisman) also insist on, and the reason our EOD stack can't do
  it justice.
- **Backtest-vs-live reconciliation with live *under* backtest** — the strongest anti-oversell
  signal on the channel after Simon Black. She doesn't quote the rosy 33% and stop; she foregrounds
  the ~21% she actually achieved and explains 2025's shortfall.
- **Real cost/slippage rigor.** Market-vs-stop-limit, exchange-held vs broker-held stops, the <5¢
  long-leg removal, the IBKR/Tasty-vs-Tradier/E-Trade/TradeStation cost comparison — concrete,
  specific, and about the thing that actually decides whether this book is net-positive. Most guests
  hand-wave costs; she did the work and talked to CBOE. `@11:29`, `@12:01`, `@12:40`
- **Disciplined, defined risk.** Defined-width condor, hard per-side stops, a strict 2%-of-account
  daily cap, the 50%-BP rule, and a stated preference for **low drawdowns over headline return**.
- **Low sales motive** relative to the channel — recommends free/third-party tools and her own free
  videos; no course/Discord funnel foregrounded.

## Backtestability

- **MEIC proper is not faithfully testable on our stack.** It is **0DTE with 6 intraday entries,
  intraday single-leg market stops, and a same-day break-even tweak.** `silver.options_daily_v3` is
  **EOD-only** — a 0DTE option's only row is at the close = expiration ≈ intrinsic, so the intraday
  **entry credit and stop-outs are unobservable** (confirmed: only 4,223 total 0DTE rows, all
  at-expiry). No daily-resolution approximation can represent the entry cadence or the per-side stop
  fills that she shows dominate the result.
- **✅ Skeleton DONE (`backtests/tammy_chambless_0dte_ic/`, 2026-07-05).** We tested the raw VRP
  floor that MEIC is built on: a **1DTE SPX iron condor held to expiry** with real EOD entry prices,
  2016–2025 (4,783 condors), bracketed by two scenarios — (A) no stop, (B) per-side loss capped at 2×
  credit ≈ her stop. **Finding: A is net-negative in nearly every year/delta; B is positive in every
  year including 2022. The entire edge is the per-side stop, not the premium.** MEIC's true EV sits
  A<MEIC<B, and B is optimistic (it can't charge for whipsaw stop-outs) — consistent with her live
  ~20.7% being ~37% below her 33% backtest. See RESULTS.md for the full table and caveats (the
  skeleton is 1DTE-overnight/single-entry, NOT her 0DTE/6-entry, so magnitudes are directional).
- **She already tested MEIC correctly** on BYOB/Option Omega 1-min data — the right tool. Our value
  was to *locate the edge* (it's the stop) and confirm it's un-improvable on EOD, plus flag her
  live/backtest ~37% haircut as the realistic discount for *any* 0DTE-IC backtest in this KB.
- **To evaluate MEIC proper:** needs minute-resolution SPX 0DTE data (CBOE/ORATS/OptionNet) in
  BYOB/Option Omega — out of scope for `options_daily_v3`.

## Open questions / next step

- How does MEIC hold up in a *sustained* high-vol trend (2022-style, or a multi-week 2018-Feb-type
  regime) rather than the isolated "election" wobble in her benign 2023–2025 window?
- What is the net edge after her own worst-case slippage table — i.e. run on a high-cost broker with
  broker-held stops, does the ~21% live survive?
- Does the MEIC-plus 10¢ tweak actually add positive EV net of the extra premature stop-outs it
  causes on days that would otherwise have expired worthless, or is it a wash she perceives as a win?
- **Cross-reference:** same family as `zerodte_breakeven_iron_condor.md` (Yona) and `pulver_0dte.md`;
  Tammy is the more complete/honest exponent — treat this as the reference write-up for 0DTE MEIC.
- **Next step:** **not worth a backtest on our EOD data** (intraday by construction — honest null,
  like the other 0DTE entries). If the user wants it evaluated, it needs 1-min SPX 0DTE data and
  belongs in BYOB/Option Omega, not `backtests/tammy_chambless_0dte_ic/` on `options_daily_v3`.

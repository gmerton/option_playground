# No-Loss Combo — Christian (Munich lawyer)

Source: `2025-04-13_WJfvBfaeuP4` — "This Lawyer's Options Trading Strategy Guarantees No
Loss (Here's How)" ([watch](https://www.youtube.com/watch?v=WJfvBfaeuP4)). Guest: Christian,
a 60-year-old lawyer/options trader from Munich, Germany (auto-caption surname "Chennich" —
uncertain); on Discord. Host: John. Recorded 2025-04-08, right after the April-2025 tariff
selloff.

## Verdict

> **Conviction: 2 / 5 · Risk: 3 / 10 (capital-protected, defined risk) · Tested: NO
> (mostly an arithmetic/rate identity, not an options backtest)**
> Unlike the Burrito Butterfly's "risk-free" (which a backtest **refuted**), this "no loss"
> claim is **arithmetically TRUE — but trivial**. The structure replaces one long-option leg
> with **synthetic long stock** (put-call parity), turning the position into a big **debit**
> that earns the risk-free rate as cost-of-carry; if that interest exceeds the original
> structure's loss-zone width, the trade can't lose **at expiration**. That's real, textbook
> finance — and the presenter is unusually honest about the catches. But the base-case return
> is **~1-2% (sub-T-bill)** on $50k-$84k of tied-up capital per combo, **before** multi-leg
> commissions and slippage that plausibly erase the thin interest edge. The eye-catching
> "20-25%/yr" comes **not** from the no-loss mechanic but from his **directional reads** being
> right — a skill he simultaneously **disclaims** ("really bad at reading the market short
> term") and for which there is **no separable track record**. So: a legitimate
> capital-preservation tool with a real but tiny edge, oversold by a headline that implies
> free profit. Hidden cost = **opportunity cost + execution drag + capital intensity**.

## Mechanics

- **Underlying:** **single stocks and ETFs only** (SPY, QQQ, MSFT, HPQ shown). **NOT
  cash-settled indexes** (SPX/RUT) — the trick requires going long *shares*, which indexes
  don't have. `@17:50`, `@18:05`
- **The core idea (put-call parity / cost-of-carry):** any long option can be replaced by a
  synthetic equivalent — a **long call ≡ long 100 shares + long put**. Replacing a long-call
  leg this way converts that leg into a large **debit** (you pay for the stock, ~$50k/100
  shares). Because a debit position is effectively lending the market money, you **receive the
  Fed funds rate** as cost-of-carry over the hold. `@07:01`, `@09:16`, `@11:25`
- **Worked example (the engine):** $52,798 debit × 3.9% Fed funds × (54/365) ≈ **$304** of
  interest earned over the trade. That interest is what "lifts the structure out of its loss
  zone." `@09:35`, `@10:48`
- **Construction recipe:** start with the structure you *want* (call butterfly / put
  butterfly / calendar / condor), then **replace one long leg with long-put + long-shares** so
  the position carries a large debit. If the carry interest over the DTE ≥ the structure's
  max-loss-zone depth, the payoff floor rises to **≥ $0 at expiration** (a small guaranteed
  profit). `@12:29`, `@13:05`
- **Structures shown:**
  - **20-wide SPY call butterfly**, 75 DTE → min profit ~$175 guaranteed. `@12:45`, `@13:23`
  - **25-wide QQQ put butterfly** with **200** shares (more capital → more interest). `@22:10`
  - **Call calendar / earnings calendar** (HPQ): works when the **front short call's extrinsic
    value > back long's extrinsic**; "nearly risk-free earnings plays." `@23:02`, `@24:07`
  - **Microsoft call condor and short condor** with a no-loss zone spanning most of the
    expected move. `@27:33`, `@28:27`
- **DTE:** 21-120 days; routine cadence 28-35 days, often laddered weekly (2-4 on at once).
  Explicitly **no 0-DTE, no naked**. `@03:14`, `@42:38`
- **Profit-taking:** treats the butterfly like a butterfly — close at **50-75%** of max, often
  10-15 days before expiry; or roll the shares + structure forward. `@17:10`, `@39:25`
- **Adjustments:** prefers to **leave trades alone** (claims backtests show 50/50 mean
  reversion); if underwater, **adds combos/shares** (second butterfly, double calendar) rather
  than rolling. `@36:32`, `@38:18`
- **Self-rated risk:** **2-3** ("you need to know your option math"; recommends paper
  trading first). `@41:35`

## Claimed edge & returns

- **"No loss at expiration… absolutely no risk to the downside."** `@01:08`, `@01:19`
- Butterfly example: **min profit $48, max $2,548, fixed.** `@01:33`
- **"20-25% average return per year… that's what I'm achieving,"** "practically no risk."
  `@42:12`, `@43:14`
- Base-case no-loss return openly stated as small: **$175 on $50,554 over 75 days = 1-2%.**
  `@14:05`
- **"What's the catch? There is no catch… it's simply mathematics, the cost to carry."**
  `@33:43`, `@34:26`
- **No separable track record** — self-reported only; no statements, no trade log shown.

## Objective assessment (where the "guarantee" really sits)

1. **The "no loss" is TRUE but trivial — and only at expiration.** This is genuine put-call
   parity: a deep-debit (synthetic-long-stock) position earns the embedded risk-free rate, and
   if that carry > the structure's loss-zone width, the floor is ≥$0 *at expiry*. To his
   credit, he says so plainly and even hands you the disqualifying cases (below). This is the
   **opposite** of Burrito's false "can't lose." But "no loss" ≠ "good trade."
2. **Hidden cost #1 — opportunity cost / sub-T-bill base return.** The guaranteed floor (~1-2%)
   is **less than the T-bill you could buy directly with the same $50k**, at zero options
   complexity, zero assignment risk, zero slippage. The structure is, at its base, an expensive
   synthetic bond + a butterfly *lottery overlay*. He even frames it that way ("if I earn 1-2%,
   so be it… you can't go broke if you lose time"). `@14:05`, `@14:42`
3. **Hidden cost #2 — execution drag eats the entire edge.** The whole base edge is ~1-2%
   interest. These are **4-leg stock+option combos**; multi-leg commissions + bid/ask slippage
   on stock-options on single names can easily exceed 1-2%. He admits market makers won't fill
   his "riskless" prices — "the trade shows a loss of $500… but I get no fill." `@36:51`,
   `@37:00` That cuts both ways: the model P&L is theoretical, and real fills can flip a paper
   no-loss into a real cost.
4. **Hidden cost #3 — capital intensity.** $50k-$84k of capital **per combo** ("you need the
   capital — that's the problem"). The %-return denominator is enormous, which is precisely why
   the headline % must come from somewhere other than the carry. `@22:28`, `@43:18`
5. **The 20-25%/yr is unverified and rests on DIRECTIONAL skill he disclaims.** The no-loss
   mechanic yields ~1-2%. To get to 20-25% the stock must land in the butterfly tent — i.e. his
   directional/timing read ("I see Microsoft going to 400-420") must be right. He then says he's
   **"really bad at reading the market short term… no idea if tomorrow goes up or down."** So the
   profit-driving step is an unproven discretionary edge, with **no separable track record** to
   confirm it. `@17:50`, `@39:40`, `@42:12`
6. **Path / early-exit risk.** No-loss is **only at expiration**; he confirms interim drawdowns
   are real and "if you close it at such a time you will have a real loss." Forced exits
   (margin, life, a portfolio call) break the guarantee. `@36:04`, `@36:17`
7. **Early-assignment & dividend risk (admitted).** Short calls can be assigned around
   ex-dividend (you lose the shares / go short stock). And any stock yielding **more than Fed
   funds** (his example: Altria ~7%) **cannot** form a no-loss trade — the dividend you forgo/pay
   swamps the carry. `@31:22`, `@37:10`
8. **Regime-dependent — dies at zero rates (admitted "the real catch").** The entire edge is the
   risk-free rate. "Didn't work for 12 years" (2008-2020 ZIRP); "if rates go to zero again, this
   trade is dead." So it's a **rate-cycle** strategy, not a permanent one. `@34:41`, `@36:04`
9. **Taxes/dividends not modeled.** Long shares + dividends + multi-leg options on single names
   = messy tax treatment and dividend mechanics; unaddressed.

## What's genuinely sound (the legitimate core)

- **The finance is correct and honestly explained.** Cost-of-carry embedded in option prices via
  put-call parity is textbook, uncontroversial, and was real in this rate regime. He correctly
  traces it to old long-box/short-box interest capture (McMillan, pre-2008). `@33:43`, `@34:41`
- **It IS a real capital-protection tool.** For a **risk-averse retiree who would otherwise hold
  the stock and eat a 50% crash**, wrapping a market view in this structure **floors the loss at
  ~breakeven** while keeping (capped) upside if right. As a *defensive* "stop the bleeding,
  lock today's price, sleep, look tomorrow" overlay on an existing portfolio, that's a coherent,
  legitimate use — arguably the strategy's truest value, more than the return chase. `@15:18`,
  `@43:29`, `@45:03`
- **Defined risk, no blow-up, no naked, no 0-DTE.** Self-imposed guardrails are conservative and
  consistent with the pitch.
- **Unusual candor.** He volunteers the disqualifiers (dividend stocks, zero-rate death, interim
  drawdowns, no fills, sub-2% base return). Low oversell relative to the channel — the oversell
  is almost entirely in the **title** ("guarantees no loss" → implies free money).

## Backtestability

- **This is more an arithmetic/rate-model check than an options backtest.** The "no loss at
  expiration" claim is a **pricing identity**: verify that `debit × rate × (DTE/365) ≥
  loss-zone width` for a given structure. No historical data is needed to confirm the floor —
  it's algebra (and it holds, given honest interest and ignoring fills/dividends).
- **What a test SHOULD measure is net realism, not the floor:** model **multi-leg commissions +
  bid/ask slippage** on the 4-leg stock+option combo and show whether the ~1-2% carry survives —
  i.e. whether the realized floor is still ≥0 after costs, or whether it's just a worse T-bill.
- **The 20-25%/yr is NOT faithfully testable** — it depends on his discretionary directional
  entry ("I see MSFT going to 420"). A mechanical version (e.g. always-ATM butterfly + synthetic
  long stock) would capture only the carry (~1-2%) by construction, not his stock-picking.
- **Data:** SPY/QQQ ETF coverage in `silver.options_daily_v3` needs confirmation (the table is
  ticker-bucketed; SPX/XSP are confirmed but **excluded here** since the trick needs shares).
  ⚠ **EOD-only** — fine for this slow style, but can't capture fills/early-assignment nuance.
- **Honest null comparison:** the structure vs. **(T-bill + a small defined-risk butterfly)** —
  to show the merged combo adds nothing over its parts except assignment/dividend/capital
  complications.

## Open questions / next step

- After realistic multi-leg commissions + slippage, does the ~1-2% carry floor stay ≥ 0, or does
  execution drag push the "no-loss" trade below a plain T-bill?
- Is there ANY separable evidence for the 20-25%/yr claim, or is it entirely the (disclaimed)
  directional overlay? Without a trade log it's unfalsifiable.
- Quantify the opportunity-cost gap vs. simply holding T-bills + a tiny lottery slice across a
  full rate cycle.
- Confirm SPY/QQQ single-name/ETF option coverage (greeks + 21-120 DTE) in Athena.
- **Next step (on command only):** an *arithmetic* check of the carry-vs-loss-zone identity plus
  a cost-drag model under `backtests/no_loss_combo/` — not a directional backtest.

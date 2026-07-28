# 0DTE Trade Automation (Trade Automation Toolbox) — Kyle Lisman

Source: `2025-07-06_plzrzv5vZlI` — "He Runs 48 0DTE Options Trades a Day — All Automated!
Here's How" ([watch](https://www.youtube.com/watch?v=plzrzv5vZlI)). Guest: Kyle Lisman, a
career CTO/software engineer (~20 yrs), ~3 yrs running this; host: John. Kyle is the **builder
and vendor of "Trade Automation Toolbox" (TAT)** — a paid retail order-automation platform — and
also wrote a free backtester, "BOB" (Build Your Own Backtest). So this is a **tool review with a
commercial motive**, not a disclosure of a novel edge.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 5 / 10 (defined-risk spreads, fast-move slippage) · Tested: NO**
> The single most **intellectually honest** point in this KB is made here and it's the reason to
> watch: **"automation is not a strategy in and of itself… it's just a way to implement a trading
> strategy you already have, that you've backtested"** (`@05:20`). Automation is *execution
> infrastructure* — it removes clicks, human error, and emotion; it does **not** create edge. As a
> *strategy* review this therefore adds nothing new: the thing being automated is a garden-variety
> **0DTE short-premium book (iron condors + trend-following credit spreads) harvesting VRP**, which
> the KB already covers (MEIC/Pulver/Yona). Conviction is low not because the presenter oversells —
> he's unusually measured — but because there is **no separable track record**, the returns are
> self-reported on a soft denominator, and the "48 trades/day" headline is about *throughput*, not
> *edge*. Credit for honesty; no independent evidence to bank.

## What's actually being automated (the underlying strategy)

- **Underlying:** SPX 0DTE (cash-settled, no assignment, 100% cash overnight → no gap risk). `@04:10`
- **Two complementary books run all day:** `@24:12`
  1. **Iron condors** — sell a put spread + call spread delta-neutral, ~**24 entries/day**,
     staggered (some morning, more afternoon). Wins on rangebound days. `@24:26`, `@26:17`
  2. **Trend-following single-side credit spreads** — ~**20 entries/day**; sell put spreads when
     price is above its intraday moving averages, call spreads when below. Meant to **offset the
     IC's stopped-out side on big trending days.** `@24:43`, `@25:13`
  - Total ≈ **48 structures/day (68 legs counting both IC sides)**. `@26:17`
- **Config per trade:** trade type, DTE, target credit *or* delta, spread width, stop-loss, profit
  target, scheduled entry/exit times — or a **TradingView webhook** to trigger on an external
  signal. `@08:22`, `@08:58`
- **Safety-first execution design (the genuinely good engineering):** the moment a position opens,
  its **stop-loss orders are pushed to the broker's servers (IBKR / TradeStation)** — so a crash of
  his software, home internet, or power does **not** leave positions unprotected. `@19:08`,
  `@19:22`
- **Not set-and-forget (his words):** "it's not a money printer… not set it and forget it"; still
  the trader's responsibility to monitor. His own routine is low-touch — watches email fill
  confirmations, logs in ~15 min before close. `@11:09`, `@17:55`, `@22:47`

## Claimed edge & returns

- **~30–40% "on the buying power I've used" each year, ~3 years** (started ~mid-2022). `@27:50`
- **No separable, verifiable track record** is shown — no statements, no per-trade log, no
  third-party audit. The claim is a round verbal range on a vaguely-defined denominator ("BP I've
  used").
- **April 9, 2025 (tariff-pause, +9–10% intraday spike):** did **not** make money — all call-side
  spreads stopped out on the jump; stops (already resting on broker servers for hours) filled with
  "a little higher than average slippage" but "well within expected range." He frames the day's
  result as "very typical." `@18:30`, `@19:58`

## Objective assessment (where to be skeptical)

1. **Commercial motive, twice over.** He sells the automation platform (TAT) and the video is a
   funnel (Discord, "sign up," a paired plug for a competitor tool "Trade Steward"). Not
   disqualifying, but the reason for the video is customer acquisition, not edge disclosure.
2. **No edge is actually disclosed.** By his own correct framing, automation ≠ strategy. The video
   never specifies the parameters that would make the *underlying* 0DTE book positive-EV (which
   deltas, which widths, which MA rule, stop/target levels). So there is nothing here to falsify or
   reproduce beyond "sell 0DTE premium, a lot."
3. **"48 trades/day" is throughput, not alpha.** More occurrences smooth variance toward the mean —
   but if the per-trade mean is ~zero after costs, more trades just converge faster to ~zero.
   Frequency is a *tooling* achievement, not evidence of an edge.
4. **Costs scale with the headline.** 48 structures/day × ~250 days ≈ **~12,000 trades/yr**, 68
   legs/day of commissions + bid/ask on 0DTE spreads + stop-fill slippage on fast moves. The thin
   VRP edge on 0DTE credit spreads is exactly the kind that heavy trade counts can eat. He never
   nets returns against this.
5. **Self-reported denominator.** "30–40% on the buying power I've used" is unauditable and elastic
   — "BP used" can be a small fraction of account equity, inflating the percentage vs a
   capital-at-risk or account-NAV basis. Compare on a common basis before ranking.
6. **The tail is capped but not absent.** 0DTE + defined-width spreads + broker-resident stops is a
   genuinely bounded structure (no overnight gap, no naked short) — but a **fast gap *through* both
   the short and long strike** (locked-limit / illiquid seconds) can fill the stop worse than the
   spread width, and the trend-following overlay adds a *second* directional bet that can stop out
   with the IC on a whipsaw. April 9 is the advertised proof it "handles" this; one benign-outcome
   crash day is not a distribution.

## What's genuinely sound (the diamond)

- **The honest thesis — automation is execution, not alpha — is correct and rare on this channel,**
  and it directly validates the user's own working belief (see
  `memory/feedback_conviction_selection_is_the_strategy.md`: intraday machinery is *insurance, not
  alpha*). Worth quoting back.
- **Safety-first order design** (stops pushed to broker servers on entry; software failure ≠
  unprotected position) is exactly the right engineering priority and a real differentiator worth
  demanding from any automation vendor.
- **Defined-risk, cash-settled, 100%-cash-overnight** structure — no assignment, no gap risk, known
  per-trade max loss.
- **Sober process discipline:** backtest first, forward-test live against the backtest, start in
  paper, start small, "it's not a money printer." Recommends *Trading in the Zone* (Douglas). Low
  oversell.
- **Backtester provenance:** he built BOB on **CBOE 1-minute then tick data** — i.e. he's aware EOD
  is too coarse for 0DTE, which is the correct methodological stance (and the reason *we* can't
  faithfully backtest this on `options_daily_v3`).

## Backtestability

- **Nothing new to test at the strategy level.** The automation layer is irrelevant to edge, and
  the embedded 0DTE IC + credit-spread book is **intraday** (dozens of same-day entries, intraday
  MA-triggered side selection, intraday stops). Our `silver.options_daily_v3` is **EOD-only**, so
  the timing that defines this strategy is unrepresentable — exactly why Kyle himself acquired
  1-minute/tick data. This is a hard **null for our backtest stack**, not a to-do.
- **Already-covered analog:** the *concept* (0DTE defined-risk premium selling, per-side stops ≈
  premium) is the same family as `zerodte_breakeven_iron_condor.md` (MEIC) and `pulver_0dte.md` —
  refer there for the skeptical economics; the same thin-edge-vs-costs critique applies.
- **If ever pursued:** would require minute-resolution SPX 0DTE data (CBOE/ORATS/OptionNet), out of
  current scope.

## Open questions / next step

- What are the *actual* parameters of the underlying book (deltas, widths, MA rule, stop/target)?
  The video withholds them — without them there is no strategy to evaluate, only a tool.
- On a common denominator (account NAV or capital-at-risk), what is the net return after ~12k
  trades/yr of commissions + slippage? Unanswerable from the video.
- **Cross-reference:** the same episode plugs **Scott Clark / Trade Steward** — reviewed in
  `automation_trade_steward_scott_clark.md`. Same category (automation tooling), even less strategy
  content.
- **Actionable takeaway (non-backtest):** if the user ever automates his *own* validated strategies,
  the checklist to demand from any vendor is Kyle's design: broker-resident stops on entry,
  failure-safe redundancy, fill/connectivity alerts, paper-first, per-side stop logic. That's the
  reusable value here — not a new trade.

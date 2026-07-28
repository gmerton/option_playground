# 0DTE Break-Even Iron Condor (MEIC) — "Yona" / John (Theta Profits host)

Source: `2026-02-22_Fj41ojAdwJ8` — "After 9,000 Trades, This Is Still My Most Profitable 0DTE
Strategy" ([watch](https://www.youtube.com/watch?v=Fj41ojAdwJ8)). Guest: **the channel host himself**
(Yon "Aina" Sanan, goes by "John" in English) — a former journalist / communications manager at a
Scandinavian media company, retired, now full-time options + running Theta Profits. This is a
**self-interview**, so there is no independent guest at all. The structure is explicitly the same as
**MEIC (Multiple Entry Iron Condors)**, a public community strategy associated with Tammy Chambless.
`@00:31`, `@08:38`, `@09:09`

## Verdict

> **Conviction: 2 / 5 · Risk: 5 / 10 (defined-risk per trade, intraday-tail exposed) · Tested: NO (not faithfully testable on EOD data)**
> A genuinely well-disciplined, defined-risk version of a **known, widely-practiced** 0DTE premium-
> selling structure (MEIC), run by an unusually candid presenter who correctly de-emphasizes win rate
> in favor of expectancy and runs strict daily risk caps. Those merits are real. But three things hold
> it down: (1) it's a **self-interview** — maximum incentive to oversell, zero independent witness;
> (2) the track record is **not separable** — he refuses to give a total return %, trades other
> strategies in the same account, and the "proof" is a self-drawn cumulative-profit curve, not
> statements; and (3) the per-trade edge is **razor-thin (0.28% of risk)** sitting on top of exactly
> the costs that are hand-waved — 4-leg-plus high-frequency SPX commissions and, critically,
> **stop slippage on fast moves**, which he himself admits can produce "catastrophic fills." The whole
> "break-even when one side stops" math is only true if the stop fills near its level — the tail days
> when it doesn't are the days that matter. The **"9,000 trades" headline measures frequency, not
> edge**: ~5-7 trades/day × ~250 days × 5 years arithmetically *is* 9,000; a big N from a high-cadence
> day-trade is not independent evidence of a positive expectancy.

## Mechanics

- **Underlying:** **SPX** (cash-settled, no assignment), 0 DTE. `@04:26`, `@04:46`
- **Structure:** an **iron condor** = sell a call credit spread above + a put credit spread below,
  opened together, **with equal premium targeted on each side** ("break-even iron condor"). Enters
  the call spread first, then the put spread immediately after — not legging for direction, just for
  fill quality / matched premium. `@04:46`, `@11:49`
- **Cadence (the "multiple entry" part):** sells iron condors **throughout the day, ~1 per hour**,
  first entry ~10-15 min after the open, then roughly hourly through the 3pm ET hour. Typically
  **6-7 condors running by end of day**, up to 10 max (rare). `@09:51`, `@13:38`
- **Entry timing (discretionary):** waits for the market to "stabilize" — at least **2-3 five-minute
  candles at roughly the same level** before entering; after a big move, waits for stabilization or
  signs of reversal. No fixed clock times. `@10:23`, `@10:54`
- **Strikes / width:** short strikes at **10-15 delta**; **width starts at 30 points**, then one side
  is adjusted (25 / 35 / 40+) to equalize premium. Collects **$100-200 per side → $200-300 per
  condor**; more in high vol. `@12:33`, `@13:05`
- **Stops (the defining feature):** a stop on **each side, set equal to the TOTAL premium of the whole
  condor.** Collect $300 total → put-side stop = $300, call-side stop = $300. If one side stops, you
  lose ~$300 there but keep the $300 premium → **~break even** (hence the name). You only take a real
  loss if **both** sides stop ("double stop"). `@01:01`, `@05:05`, `@05:20`
- **Stop placement detail:** stops are set **on the shorts only** (not the spreads) — claims less
  slippage and lets the order **rest at the exchange, not the broker**. Uses an **OCO**: a
  **stop-limit** (40 pts between stop and limit) as the intended fill, plus a **stop-market 30 pts
  further out** as a "last line of defense" if a fast move skips the limit. `@18:28`, `@19:24`
- **Profit/close rule:** let it run until a stop hits or the **short decays to $0.05**, at which point
  it's auto-closed. Closing the short at 5¢ (rather than holding to expiry) frees the long for reuse
  (buying-power efficiency) and **dodges the last-half-hour swing risk** where an expired-worthless
  short can suddenly regain value. `@16:14`, `@17:30`
- **Management:** the *only* management is **tightening stops** — to lock in profit on winners and to
  shed total risk when too many trades are threatened. **Never rolls, never adjusts the structure.**
  When a short stops, default is to close the long immediately; occasionally (if the move continues)
  he trails a stop on the long to capture extra profit — discretionary, "requires attention."
  `@22:14`, `@20:36`, `@23:23`
- **Risk caps:** never risk more than **1-2% of account on a single day** (measured as *all stops
  hitting on both sides on all open trades*); never use more than **50% of buying power** on this
  strategy in a day. `@14:13`, `@14:34`
- **Self-rated risk:** **4 / 10** — *conditional on discipline* (setting the stops, honoring the
  total-risk cap). "If you're not disciplined, it's not the four." `@28:00`

## Claimed edge & returns

- **9,000+ trades over ~5 years** (trading since April 2021), "consistently profitable… with quite
  low drawdowns." `@00:00`, `@01:28`, `@28:56`
- **Win rate ~40%** — and he correctly argues this is *not* the metric; expectancy is. Claims **wins
  average >2× the average loss**, giving positive expectancy despite the sub-50% win rate. `@32:17`,
  `@34:12`
- **Avg net profit per trade = 0.28% of risk** (net P&L ÷ [spread width − premium]); **premium-capture
  rate = 5.65%** (net P&L ÷ premium collected). Both measured across all 9,000+ trades. `@30:11`,
  `@31:12`
- **Double-stop (real-loss) rate ≈ 8%** of trades — but **rising** ("higher the last year… maybe more
  intraday volatility than before"). `@05:47`, `@24:18`
- **39.3% on the account last year** — but immediately caveated: trades other strategies in the same
  account, **won't disclose account size or a total %**. `@02:39`, `@29:14`
- Edge-by-hour/day: last 3 hours (1/2/3pm ET) and Mon/Fri historically best; Thu ~break-even — but he
  says these **vary so much quarter-to-quarter that he ignores them**. `@15:18`, `@34:54`

## Objective assessment (where to be skeptical)

1. **It's a self-interview.** The "guest" is the channel owner. Every red-flag normally split between
   an overselling guest and a probing host is here concentrated in one person with a direct commercial
   interest in the channel. Treat all numbers as **self-reported and self-curated** by default.
   `@00:31`
2. **No separable, verifiable track record.** He **explicitly declines to give a total return %**,
   trades other strategies in the same account, and the evidence is a **self-drawn cumulative-profit
   graph**, not brokerage statements. The per-trade stats (0.28%, 5.65%, 40%, 8%) come from his own
   trade log with no external audit. This is the README's "no separable track record" flag — softer
   than Burrito Butterfly's "I can't untangle them," but it lands in the same place: **not
   falsifiable.** `@29:14`
3. **9,000 trades ≠ edge.** A large N here is a *frequency* artifact of day-trading 5-7 condors/day,
   not independent confirmation. With a razor-thin 0.28%/trade, a big sample can still be a coin-flip
   plus drift; the count is presented as if it were statistical proof of edge. It isn't.
4. **The edge is thinner than the costs that are hand-waved.** 0.28% of ~$2,700-2,900 risk ≈ **$8 net
   per trade.** Each condor is **4 legs in**, plus closing the shorts at 5¢, plus any stop fills — a
   high-frequency, multi-leg SPX trade. Realistic commissions + bid/ask on the short closes can plausibly
   approach or exceed that $8. **He never quantifies commissions or slippage**, yet they are decisive at
   this margin. (His "0.28%" presumably is net of *his* commissions, but it's unverifiable and very
   broker-dependent.)
5. **The break-even mechanic depends on stops filling near their level — which he admits fails on the
   tail.** "Liquidity disappears… catastrophic fills"; the stop-market is the line that gets you out
   "before losses get astronomical." `@25:00`, `@20:07` On exactly the fast moves that trigger stops,
   the realized loss on the stopped side can blow past the premium collected → the "you're break-even"
   arithmetic quietly breaks, and a double-stop day can exceed the planned 1-2% cap.
6. **Benign regime + rising tail rate.** April 2021-2026 was mostly a strong/low-vol bull. The
   double-stop (real-loss) rate is **already creeping up**. The strategy has not been stress-tested
   through a sustained high-vol/whipsaw regime, where double-stops cluster across *all* open condors on
   the same day — the precise correlated-loss scenario the 1-2% cap is meant to bound, but only if fills
   cooperate.
7. **OCO double-fire = momentary net-long, undefined-ish path.** A few times a year both the stop-limit
   and stop-market fire, leaving him **long what he was short.** `@27:27` He says he usually escapes
   without loss, but it's an admitted, recurring uncontrolled-exposure event the clean "defined-risk"
   framing omits.
8. **Discretion is load-bearing but unmeasured.** Entry timing (candle-reading for "stabilization"),
   stop-tightening decisions, and the trail-the-long move are all by feel. The 0.28% bakes in this
   discretion and can't be reproduced mechanically.

## What's genuinely sound (the diamond)

- **Defined-risk structure.** The long wings cap the per-condor max loss at width − premium; SPX is
  cash-settled (no assignment). You can't be blown up by a single trade — real and valuable.
- **MEIC is a legitimate, widely-practiced structure**, not a proprietary pitch. Selling 0DTE theta as
  a delta-balanced condor with mechanical stops is a coherent, plausibly-positive-EV idea, and there is
  an outside community (Tammy Chambless / Quantum Options) practicing and discussing it — so the claims
  are at least *comparable* to others' work, unlike a one-off invention.
- **Closing shorts at 5¢ is genuinely smart** — it sidesteps the last-half-hour gamma whip where a
  "worthless" short suddenly reprices, and recycles buying power.
- **Strict, well-specified risk discipline:** worst-case-if-all-double-stop ≤ 1-2%/day, ≤ 50% BP,
  continuous "what's the worst that can happen right now" monitoring. This is the right way to run a
  short-premium book.
- **Intellectually honest on win rate.** He explicitly tells viewers a 40% win rate can be fine and
  that **expectancy, not win rate, is the metric** — the opposite of the channel's usual high-win-rate
  bragging. He also names the real risks (catastrophic fills, monitoring burden, rising double-stops).
  Low oversell *relative to the structure of a self-promo video* — though still self-reported.
- **Stops resting at the exchange + OCO stop-limit/stop-market backstop** is thoughtful execution
  design for a fast product.

## Backtestability

- **Fundamentally an intraday strategy — and that is fatal for our data.** The entire edge lives in
  things EOD data cannot see: ~hourly entries, the "wait for 2-3 stable 5-min candles" trigger,
  **intraday stop fills (the break-even mechanic itself)**, tightening stops through the day, and
  closing shorts at 5¢. None of it can be replayed at daily resolution.
- **What EOD data *can* do is only a crude caricature:** sell a 10-15Δ SPX 0DTE iron condor at the
  prior close and settle at expiry intrinsic — with **no intraday stops at all.** But removing the
  stops *removes the strategy* (the name is "break-even iron condor"); that test measures a different,
  un-managed thing and would tell us almost nothing about this trade.
- **✅ Data present, ⚠ wrong resolution:** Athena `silver.options_daily_v3` has **SPX** confirmed
  (46M rows, 2010 → 2026-02-20, full greeks + bid/ask, 0-DTE expirations present). But it is **EOD /
  daily only — no intraday bars.** A faithful test needs **minute-level (or finer) SPX option
  bid/ask**, which we do not have. So this strategy is **NOT faithfully testable here**, more so than
  any prior KB entry.
- **Better paths than our EOD data:** (a) reproduce/inspect the **public MEIC community backtests**
  (intraday data, Tammy Chambless / Quantum Options) and treat those as the reference; (b) if intraday
  SPX option data is ever sourced, model entry-per-hour, per-side stops *with explicit slippage
  assumptions*, and 5¢ short-closes — the slippage assumption will dominate the result.

## Open questions / next step

- **Does the per-trade edge survive realistic commissions + stop slippage?** At ~$8 net/trade the
  answer is entirely a cost-and-fill question — and the costs are the un-quantified part. Any honest
  evaluation must model slippage on the *stopped* side, not assume break-even fills.
- **How does double-stop frequency behave in a high-vol/whipsaw regime?** The 8% rate is from a benign
  era and already rising; correlated double-stops across all open condors on one bad day are the real
  risk, and the 1-2% cap holds only if fills cooperate.
- **Can the self-reported 0.28%/5.65%/40% be corroborated against the public MEIC track records?**
  That's the only available external check on numbers that are otherwise unauditable.
- **Next step (on command only):** rather than a near-useless EOD backtest, cross-reference the public
  MEIC backtest evidence and, if minute-level SPX option data is obtainable, build an intraday test
  under `backtests/zerodte_breakeven_iron_condor/` with slippage as the primary stress variable.

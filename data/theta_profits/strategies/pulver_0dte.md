# 0DTE Iron Condor + Defensive BWB + "Profit-Trap" Butterflies — Chris Pulver

Source: `2026-05-31_5MbQ_dnImR0` — "How Chris Pulver Achieves an 85% Win Rate With 0DTE
Options" ([watch](https://www.youtube.com/watch?v=5MbQ_dnImR0)). Guest: Chris Pulver,
options educator (course "Practical Options", many YouTube videos); host: John. Trading
since early 2000s; 0DTE since 2022.

## Verdict

> **Conviction: 2 / 5 · Risk: 5 / 10 (defined-risk, negatively skewed) · Tested: NO (not faithfully testable — it is an intraday strategy)**
> A defined-risk, cash-settled 0DTE book on SPX/XSP that is more honest than the channel
> norm — he gives a real denominator (600+ iron condors / 18 mo), reports **modest,
> separable** account returns (+27% in 2025, +15.3% YTD 2026), and openly states the
> iron condor's reward:risk is "not great." But the headline "**85% win rate**" is doing
> *all* the work and is razor-thin: at his own quoted terms (10-wide IC, ~$150 credit /
> ~$850 risk) the **breakeven win rate is, to the decimal, 85%** — so the entire edge is
> the ~4–5 points above it, exactly what commissions on **50+ trades/day**, multi-leg SPX
> slippage, defense debits, and the occasional tail day chew through. The win-determining
> steps (expected-move placement, gamma-level "pin" selection via Tanuki Trade, real-time
> defense) are **intraday discretion** that cannot be specified, replayed, or backtested on
> EOD data. Strong **course-sales motive**. Better than Burrito Butterfly (defined denominator,
> sober returns); capped below Time Flies (that record is once-a-day and self-skeptical; this
> one is a full-time discretionary day-trade with a vendor funnel).

## Mechanics

Three structures, layered "almost every day," all 0DTE, all defined-risk. He is explicit
that this is **one flexible approach**, not a fixed rule set — "very much of my trading day
is flexible." `@04:53`

- **Underlying:** S&P 500 index — **SPX** primarily ("very efficient index"), **XSP** (1/10
  size) for small accounts / fine-tuning. Both European-style, cash-settled, **no
  assignment, no post-4pm gap risk**, 60/40 (§1256) tax. Explicitly avoids **SPY/QQQ**
  (assignment + post-market gap, brokers force-closing). `@04:14`, `@43:39`, `@44:19`
- **Daily prep:** broker's **implied / expected move** (e.g. "±57.98"), VIX level
  (lows vs elevated), futures, gap. Builds a **gap-adjusted "expected-move box"**: top =
  *open* + EM points; bottom = *prior close* − EM points (deliberately wider than a plain
  open ± EM). Goal: keep open-to-close price *inside the box*. `@03:39`, `@12:25`, `@13:08`
- **Core trade — Iron Condor (the "ceiling & floor"):** bear call spread + bull put spread,
  **~10-delta shorts** (or less), often delta-neutral (match 10Δ call / 10Δ put), **10 (to
  15) points wide.** Wants **≥ $1.00–$1.50 credit on a 10-wide → risking ~$8.50–$9.00**
  ("not great rewards risk… it never is"). Entered **within the first 5–10 min of open.**
  `@06:09`, `@14:20`, `@14:40`, `@18:36`
- **NO stop-loss on the IC.** Started with a 20-wide IC + 100–200% premium stop (2022) but
  abandoned it: in 0DTE a 10Δ short can hit 25Δ in 10 minutes, so stops trigger on noise then
  the trade still finishes a winner inside the box. Instead: go tighter, accept the defined
  risk, **play defense.** `@15:31`, `@16:09`
- **Defense — Broken-Wing Butterfly (just inside the IC):** a BWB ~15–20 wide placed inside
  the short strike to add a **5–10 point buffer** beyond the IC break-even ("$10 profit trap /
  $10 of protection"). Targets a small **~10¢ credit**, but will pay **10–20¢ debit** for it.
  Adds **~$9.90 risk** per side. Decided ~5–10 min after the IC. He sets a **chart alarm** at
  the box edges; "almost every day" he places defense, but only **1–2 of every 15–20 days**
  actually needs it. `@07:48`, `@18:46`, `@19:48`, `@27:39`, `@28:00`
- **Offense — "Profit-Trap" Butterflies (standalone):** long flies (or BWBs) pinned at a
  **key intraday level** — "skate where the puck is going" (Gretzky). Level chosen from a
  **gamma tool (Tanuki Trade)**: the **HVL** ("high-volatility level" = positive/negative
  gamma pivot), GEX concentration, call walls. Pay **~$2–$4 debit (= max loss)** for a
  4:1–10:1 trap; gets *cheaper/narrower and richer* as the day decays. May run **multiple
  flies** at different levels. `@06:39`, `@29:00`, `@31:47`, `@37:40`
- **Butterfly exits:** best practice — **close at ~50% return on risk intraday** ("peace of
  mind"); or hold multiple flies and **book all when net +$100–300**; or hold to the close for
  an **end-of-day pin** (the 5:1–10:1 "lottery"). If a fly looks wrong, he often *opens a new
  one at a better level* rather than micromanaging. `@34:42`, `@37:16`, `@37:40`
- **Combined daily risk:** ~**$1,800** (IC ~$850 + BWB ~$990); "playing around with like
  $2 to $3,000 a day" total. **Self-rated risk:** IC 5–6, butterfly 2–3, combo **~4–4.5/10.**
  `@25:21`, `@46:20`, `@50:08`
- **Activity:** ~**50+ trades/day** across all accounts, opening-bell-to-close, "a lot of
  button pushing"; ~220–230 0DTE days/year. `@47:34`, `@47:53`

## Claimed edge & returns

- **"Win rate's over about 85%"** overall — denominator/unit left fuzzy. `@00:00`, `@46:47`
- **Iron condor alone: 600+ logged trades over ~18 months, ~89.6% win rate.** `@51:44`
- **"Never more than two losing days in a row"** on 600+ IC trades; cites a Tasty study that
  since 2022 SPX 0DTE iron condors never had >2 losing days in a row. Nearly broken in the
  Mar–Apr 2026 rip (4-of-5 bullish days breached the box) but defense held it to one loss.
  `@52:09`, `@52:15`
- **Account returns (separable, modest):** **+27% in 2025** on six-figure accounts (was +40%,
  gave back on Bitcoin); **+15.3% YTD 2026** on a "growth account" (~$50–60K → ~$75K), 1–2
  contracts. `@52:49`, `@53:02`
- **Butterfly upside:** "butterflies that have closed out for over a thousand% profit"
  (10:1); pays $3.70 → worth $4,730 at close if pinned. Bread-and-butter is 50–200% on the
  fly. `@00:00`, `@31:47`, `@38:30`
- **Best career year ever:** +150% in a currency fund — *followed by 20% drawdowns for
  6 months* (volunteered as a cautionary tale). `@53:51`

## Objective assessment (where to be skeptical)

1. **The 85% headline IS the breakeven line — not a margin of safety.** For a 10-wide IC at
   $150 credit / $850 risk, breakeven win rate = 850 / (850+150) = **exactly 85.0%.** So
   "over 85%" means "barely above break-even before costs." His 89.6% IC number gives a
   ~4.6-point cushion → naive gross EV ≈ 0.896·150 − 0.104·850 ≈ **+$46/trade** — real but
   thin, and that is **before** SPX multi-leg commissions/slippage, the BWB defense debits,
   and the days where layered defense pushes the actual loss *past* the bare $850. A high win
   rate on a 1-to-5.7 payoff is precisely the profile where costs and tails decide everything.
2. **It is an intraday, discretionary day-trade — the edge is unspecifiable.** Entry in the
   first 5–10 min, gap-adjusted box off the *open*, real-time defense decisions, and butterfly
   levels read off a live gamma tool ("skate where the puck is going"). None of the
   win-determining steps is a rule. A mechanical version is **not** this strategy.
3. **Negatively skewed "pick up pennies."** IC wins are small/capped ($150); losses are large
   and **cluster on outlier days** — his own examples: a 3pm Trump-tweet 1% move that "blew up
   my ceiling," and Jackson Hole/Powell (90-pt expected move, price 20–30 pts beyond his call
   side) netting −$400 only because defense bled the top. "It's going to take me seven wins to
   make up for a loss." `@25:12`, `@49:02`, `@49:23`
4. **50+ trades/day commissions are never addressed.** Multi-leg SPX structures (IC = 4 legs,
   BWB/fly = 3) at ~$1.00–1.50/leg, dozens of round-trips daily, ~225 days/year, is a
   structural drag aimed straight at that ~4-5-point cushion. Hand-waved entirely.
5. **No stop = the tail is uncapped per *trade* only by the defined structure, not by skill.**
   He's right that 0DTE stops whipsaw, but the consequence is he *holds losers into max loss*
   and relies on defense, which on the worst days loses on the IC *and* the defense.
6. **Benign regime.** 2022–2026 was mostly an efficient/bull tape ("market biased to the
   upside… wants to go up through thick and thin"). Short-gamma 0DTE condors have not faced a
   sustained intraday crisis regime; the COVID/"liberation day" events he cites as what kills
   *naked* strangles are exactly when his defined-risk days chain into max-loss clusters.
   `@56:11`
7. **Strong vendor motive.** Closes by pitching his **"Practical Options" course (13 favorite
   strategies)** and "hundreds of YouTube videos," positioning himself as "a pretty good
   resource." Treat the framing as marketing; the trade mechanics are the signal. `@58:00`
8. **Unit-of-measure drift.** "Win the day" vs. per-trade win rate are used interchangeably;
   the clean number is the IC's 89.6%/600 trades. The combined "85%" denominator (per trade?
   per day? incl. the lottery flies?) is unspecified and self-logged, not audited.

## What's genuinely sound (the diamond)

- **Defined risk everywhere, cash-settled, European, no assignment, no post-4pm gap.** You
  cannot blow up an account on one trade; the SPX/XSP instrument choice and the reasoning for
  avoiding SPY/QQQ are correct. `@43:39`, `@44:19`
- **XSP as a 1/10-size on-ramp** (same tax treatment, ~$30–130 risk) is a legitimately
  accessible way to learn the structure. `@40:08`, `@42:41`
- **Returns are modest and separable** (+27%, +15.3% on stated account sizes) — *not* the
  oversold "10x" pitch. He volunteers his worst stretch (+150% → 20% drawdowns 6 mo). That
  candor, plus a real IC denominator, is why this clears Burrito Butterfly.
- **Honest about the asymmetry** ("not great rewards risk… seven wins for a loss") and about
  abandoning stops for a documented 0DTE reason (delta sensitivity) — a real microstructure
  observation, not marketing.
- **The defensive-BWB and "fund a trap with the IC credit" layering** is a coherent
  risk-management idea; the butterflies add a positive-skew/lottery sleeve to offset the
  negative-skew IC engine — a sensible *portfolio* shape even if each piece is thin.

## Backtestability

- **Data: ✅ confirmed.** Athena `silver.options_daily_v3` has **SPX** and **XSP** with full
  greeks + bid/ask, 2010 → 2026-02-20, and **0-DTE expirations are present daily** — so the
  structures are constructible.
- **⚠ But this is fundamentally an INTRADAY strategy and EOD data cannot replay it.** The
  EOD table can only test a **crude prior-close → settle proxy**: e.g. "sell a 10Δ 10-wide
  SPX iron condor at the close, hold to next-session settlement, no defense, no
  butterflies." That loses *everything that makes it his*: the morning entry, the
  gap-adjusted box (needs the *open*), the intraday defense, the gamma-level butterfly
  selection, and the 50%-intraday profit-taking. None of these is faithfully testable without
  minute data.
- **Not testable at all:** the Tanuki-Trade HVL/GEX "pin" level selection, the discretionary
  defense timing, and "open a new fly when the first looks wrong."
- **Worth doing anyway as a null/floor:** the crude EOD 0DTE 10Δ iron condor (hold to settle)
  — to measure the *skeleton's* win rate and, critically, **EV after modeled
  commissions/slippage**, and to check the "85% breakeven" arithmetic against the realized
  distribution and the tail (2022, Aug 2024, Apr 2025). If even the skeleton can't clear
  costs, the discretionary version inherits the same gravity.

## Open questions / next step

- Does the bare EOD 0DTE 10Δ iron condor clear its own ~85% breakeven *after* realistic SPX
  multi-leg costs, and how much of the realized loss mass is concentrated in a handful of
  outlier days?
- What is the true combined-book win-rate *denominator* (per-trade vs per-day, condor-only vs
  incl. flies) — and is the 89.6% IC figure independently auditable (broker statements)?
- How much of the live edge is the positive-skew butterfly sleeve vs. the negative-skew
  condor? (The flies may be where any real alpha — or its absence — lives, and they are the
  least testable part.)
- **Next step (on command only):** backtest the EOD iron-condor skeleton under
  `backtests/pulver_0dte/` as a floor/null, with explicit cost modeling — not as a faithful
  replica of his intraday process.

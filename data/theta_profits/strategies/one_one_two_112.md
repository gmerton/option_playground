# 1-1-2 ("112") — Murray Lindholt

Source: `2025-06-22_4ByN7YEGuZY` — "Turned $50K to $500K Then Lost It All Trading the 112
Options Strategy | Real Trader Story"
([watch](https://www.youtube.com/watch?v=4ByN7YEGuZY)). Guest: Murray Lindholt, retired
40-year high-school AP math teacher; host: John. **This is a blow-up story** — Murray grew a
$50K cash account to ~$526K over four years (2020–2024) trading the 112 on /ES, then gave back
*all four years of profit* in a couple of days during the August 2024 carry-trade unwind. That
makes it the most instructive video in the KB so far: the realized tail the income-strategy
sellers pretend won't happen actually happened, on camera, to a disciplined, honest operator.

## Verdict

> **Conviction: 1 / 5 · Risk: 9 / 10 (UNDEFINED tail — naked short puts) · Tested: NO**
> The 1-1-2 is a real, well-known short-premium structure, and the **mechanics are not
> inherently "bad."** But it is **net short two naked puts** — undefined downside, short
> gamma and short vega — and is almost universally mis-sold as "low-risk, low-management"
> income (Murray himself rated it 1–2/10 *before* the blow-up) and mis-sized (he ran 50%
> buying power, then pushed to ~90% adding into a vol spike, and got margin-called to ruin at
> ~200% BP). The structure didn't fail; **sizing + naked premium + a fast vol spike** did,
> exactly as theory predicts. This write-up is filed primarily as a **cautionary tale on
> position sizing and naked short premium**. Conviction stays at the floor because (a) the
> only "track record" is a single survivor's self-reported, now-blown-up curve, (b) the edge
> is short vol in a benign regime that paid until it didn't, and (c) it is untested here.
> Note the math-teacher irony: he tracked everything daily for four years and *still* blew
> up — record-keeping is not risk management when the tail is undefined.

## Mechanics

- **Underlying:** **/ES** (E-mini S&P 500 futures options) — chosen for "massive liquidity"
  and the **Section 1256 60/40 tax treatment** plus ~23h/day trading. SPX is used by larger
  traders; the structure is identical on either. `@03:18`, `@12:18`, `@03:42`
- **Core structure (the "1-1-2"):** **net credit** package, ~120 DTE region:
  - **1 long put + 1 short put = a put DEBIT spread** near the money (~25-delta long put, short
    put one strike below). Murray frames this leg as a **down-move hedge / delta hedge**, not
    the profit center. `@00:58`, `@02:27`
  - **+ 2 short ("naked") puts far OTM** — these *finance* the debit spread and produce the net
    credit. **This is the risk-bearing leg.** `@01:00`, `@02:43`
  - Net result: collect a small credit; profit if market rises (keep credit) or drifts
    down/sideways (debit spread + theta/vega decay on the short puts); **biggest profit if price
    lands near the far short strikes at expiry** (the elevated "trap" zone). `@02:43`, `@02:57`
- **Concrete example given:** buy 5700 put / sell 5600 put (a 100-wide debit spread), then sell
  **2× 4500 puts**; target ~**$10 of net credit**. `@03:25`, `@01:14`
- **Strike/width selection:** historically a 50-wide debit spread at 25-delta long / ~20–22-delta
  short, then push the 2 naked puts **as far OTM as possible while still collecting ~$10 credit**
  (maximize the width of the "trap"). Aggressive traders take ~$20 credit (narrower safety
  margin); he prefers $10 for a "wide profit track." `@04:18`, `@05:15`, `@05:31`
- **DTE:** typically **45–90 DTE**, sometimes out to 135; he personally targets ~90. `@01:14`,
  `@05:00`
- **Entry cadence:** **1–2 trades/week, staggered/laddered** so positions roll off continuously;
  not waiting for a vol spike (though a spike helps premium). `@07:15`, `@07:42`
- **Profit-taking:** discretionary/market-dependent. Many 112 traders close at **~90% of max
  credit**; Murray often **held to expiration**, especially if price was sitting in the profit
  zone. `@08:22`, `@08:45`
- **Stop-loss: NONE.** Rationale: in four years no position ever breached the naked puts, so he
  saw no need. `@08:10` — **this is the fatal flaw made explicit** (see assessment).
- **Sizing:** working capital ~**50% of buying power** as the standing rule. `@06:48`
- **111 variation (his current default entry):** sell **only ONE** far-OTM put instead of two →
  smaller "trap," lower upside, but materially lower **vega/Vega-shock risk** (one naked put vs
  two). He now **enters 111, then converts to 112** only into a vol spike / pullback (buy back the
  single put, sell 2 further OTM for credit) to avoid taking the immediate vega hit of a 112 put
  on at low vol. `@09:35`, `@24:30`, `@24:42`
- **Post-blow-up changes (the lessons-learned version):**
  1. **Uncorrelated underlyings** — now spreads the 112/111 across /ES, gold, bonds, oil, nat-gas,
     corn ("uncorrelated, not merely diversified"). `@12:10`, `@23:21`, `@23:43`
  2. **Enter as 111, scale to 112** on spikes (above). `@24:42`
  3. **DTE-scaled debit-spread width:** 0–45 DTE → 50-wide; 45–90 → 100-wide; 90–135 → 150-wide
     (more delta hedge on the way down for the longer-dated trades). `@25:25`
  4. **Roll the debit spread narrower as theta decays** (e.g. 150→100→50 wide), banking
     ~$200–300 credit each step, turning an initial $10 credit into ~$15–18. `@26:00`, `@26:28`
  5. Still runs **~50% buying power**, arguing uncorrelation keeps real BP usage near 50% even on
     a single-asset vol spike. `@27:12`, `@34:45`

## Claimed edge & returns

- **2020 → mid-2024:** $50K cash account → **~$526K**. Year-by-year (self-reported, on-screen
  charts): 2020 strong, 2021 strong, **2022 the best year at +106%** (while S&P was down ~19–20%),
  2023 "banging." Account milestones: ~$137K, ~$209K, ~$431K, then ~$526K just before the crash.
  `@13:32`, `@14:15`, `@14:38`
- **"Never had a single losing trade in ~4 years."** `@20:45` — a textbook short-premium pattern:
  a long string of small wins masking one un-survived tail.
- **2022 outperformance is the real (and dangerous) tell:** the strategy is **net short vol** and
  pays best in steady declines/elevated-premium regimes — until the *fast* spike. `@14:15`,
  `@33:52`
- **Post-blow-up:** restarted at $50K; **+21% YTD 2025** at recording; new goal 2–4%/month
  (~20–25%/yr). `@27:40`, `@31:11`, `@32:07`
- **Risk self-rating: he refused to give a number.** Said it depends on understanding; a beginner
  would call it 1–2/10 and make money for years, then have "one bad day." Conceded he'd have said
  "1 or 2" before the loss; would not call it a 10 even after. `@28:55`, `@29:38` — *this refusal
  is itself the red flag.*

## Objective assessment (the realized failure mode)

1. **The downside is UNDEFINED. This is naked short premium.** The "1-1" debit spread hedges only
   a limited band; below the long-put strike you are **net short 1–2 puts with no floor**. Max
   loss is not the debit — it is effectively unbounded toward zero on /ES, multiplied by leverage.
   Risk = **9/10**, not the 1–2 the pitch implies.
2. **"No stop-loss because it never breached in four years"** is survivorship reasoning. `@08:10`
   The absence of a loss in a benign window was read as proof of safety, not as an unsampled tail.
   This is the single sentence that explains the blow-up.
3. **The blow-up mechanics (Aug 2024 carry-trade unwind):** Friday the VIX jumped ~14–15 → ~35,
   account −16%; buying power *appeared* to free up. He read a high-vol spike as "a great
   opportunity," **added new positions at the Friday close into surging premium, taking BP to
   ~90%.** Sunday futures reopened, **VIX spiked to ~65 Monday**, account bounced $30–50K per tick
   on wide weekend spreads, **BP hit ~200%** → forced liquidation (an hour of clicking out many
   small positions at $5–10K-wide spreads). Back to $50K. `@15:31`, `@16:10`, `@16:39`, `@17:31`,
   `@18:09`, `@19:51`, `@20:05` This is **short gamma + short vega + leverage + adding into the
   spike** = the canonical 1-1-2 ruin path.
4. **"The strategy was fine, I just couldn't stay in it."** `@19:51` He notes that a week later the
   position would have recovered to profit-plus. **This is a comforting half-truth:** a strategy
   you can be *margin-called out of at the worst tick* is not "fine" — surviving the path IS the
   strategy. Solvency is a constraint, not a footnote. The instrument that makes recovery possible
   (no forced exit) is sizing, which he didn't have.
5. **Vega risk is glossed as rare.** He says it "doesn't happen that often," tolerates a "5–6–7%
   VIX increase," and only worries "when it goes to 60." `@10:54`, `@11:33` But the whole P&L is
   short vega; the trade is *built* to be unhurt by small moves and destroyed by the rare big one.
   "Happens every 5–7 years" `@21:06` is precisely a tail you cannot ignore when sizing to survive.
6. **Single survivor, self-reported, unfalsifiable record.** Charts shown on screen, no separable
   statements, and the curve already blew up once — there is no clean track record to test against.
   The "+106% in 2022" is exactly what a short-vol book looks like right before it isn't.
7. **The "uncorrelated assets" fix is real but oversold.** Cross-asset diversification helps
   *idiosyncratic* moves (corn ≠ oil), but a true global risk-off / liquidity event correlates
   *everything* toward 1 — and that is exactly the scenario (VIX 65, carry unwind) that caused the
   loss. Spreading 112s across gold/bonds/oil/grains reduces ordinary variance but does **not**
   neutralize the systemic tail he actually got hit by. `@23:43`, `@34:45`

## What's genuinely sound

- **The structure itself is legitimate and well-understood** — a put debit spread financed by
  further-OTM short puts is a coherent way to express "modestly bullish-to-neutral, paid to wait,
  with a profit bulge on a measured decline." The mechanics are not a scam; the *selling* of it as
  low-risk is.
- **The 111 (one naked put) and "enter-111-convert-to-112-on-a-spike" refinements are real
  risk reductions** — fewer naked units, and adding the second short put only when premium is
  rich rather than paying up-front vega. Genuinely better than a static 112. `@24:42`
- **DTE-scaled debit-spread width + rolling the spread narrower for credits** are sensible
  delta-hedge and theta-harvesting tweaks. `@25:25`, `@26:00`
- **The cautionary lesson is the diamond:** *size to survive the path, not the expected case; never
  treat absence of a tail as proof of its absence; do not add risk into a vol spike on margin.*
  Murray's honesty (publicly posting the loss in the Facebook group) makes this the most valuable
  teaching artifact in the KB. `@21:46`
- **Tax/structural note:** /ES carries Section 1256 60/40 treatment and near-24h liquidity — real
  advantages over SPX for an active short-premium trader (lets you defend overnight). `@12:18`

## Backtestability

- **Mechanically testable core:** SPX (proxy for /ES), ~90–120 DTE, 25-delta put debit spread
  (50/100/150-wide variants) + 2 short puts far OTM sized to ~$10 net credit, laddered weekly,
  held toward expiration or closed at ~90% of credit. Measure win rate, mean P&L, **and — the only
  number that matters here — max drawdown and ruin frequency with modeled margin on the naked
  puts.**
- **✅ Data confirmed:** Athena `silver.options_daily_v3` has **SPX (46M rows, 2010 → 2026-02-20)
  and XSP**, full greeks + bid/ask, **with both short-DTE and longer (45–135 DTE) expirations
  present** — so the 112 is constructible end-to-end. **/ES futures options are NOT yet confirmed
  in the table; proxy with SPX** (cash index vs futures will differ slightly on basis/financing and
  on the 1256 tax overlay, but the option P&L is close enough for risk characterization).
- **⚠ EOD/daily resolution only — no intraday.** This is a *severe* caveat for this strategy
  specifically: **the blow-up was an intraday/overnight margin-call dynamic** (Friday-close add,
  weekend gap, Monday VIX 65, forced liquidation at wide ticks). An EOD test will mark P&L at the
  daily close and **cannot replay the margin spiral or the wide-spread forced exits** — so a naive
  backtest will **badly understate ruin risk** and may even show the position "recovering," exactly
  the false comfort Murray described.
- **A faithful test MUST:** (a) include the crash windows — **Feb 2018 (Volmageddon), Mar 2020
  (COVID), 2022 bear, and Aug 2024 (carry unwind)**; (b) **model margin/buying-power on the naked
  puts** (SPAN-like or a conservative reg-T proxy) and trigger forced liquidation when BP is
  breached; (c) apply realistic **spike-widened bid/ask** on exit, not mid. Without margin + crash
  windows the test is meaningless for this structure.
- **Honest null comparison:** vs the same debit spread **without** the 2 naked puts (i.e. is the
  short-put credit worth the undefined tail?), and vs a defined-risk 1-1-1-1 (buy back a wing).

## Open questions / next step

- Under modeled margin and the four crash windows, **what is the ruin probability and max
  drawdown** of a 50%-BP 112 ladder — and does the 111 / uncorrelated-asset version measurably
  reduce it, or just defer it?
- Does the short-put credit add positive expectancy **after** charging for the tail (e.g. CVaR /
  Kelly), or is the multi-year "+106%" purely benign-regime short-vol carry that a single tail
  erases?
- Confirm **/ES futures-option coverage** in Athena; otherwise quantify the SPX-proxy basis error.
- Cross-reference **Tom King's 112 material** (Murray's cited primary resource, `@36:09`) for the
  canonical rules if that content gets ingested.
- **Next step (on command only):** backtest the mechanical core *with margin modeling and crash
  windows* under `backtests/one_one_two_112/`. Until then, conviction stays at the floor and risk
  at 9/10 (undefined tail).

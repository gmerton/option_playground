# 0DTE Iron Fly ("18-Minute Trade") — Doc Severson

Source: `2025-12-21_ad27qIuhgQ4` — "The 0DTE Iron Fly Strategy That Trades in 18 Minutes (SPX)"
([watch](https://www.youtube.com/watch?v=ad27qIuhgQ4)). Guest: **Doc Severson** (auto-captions
mis-render him as "Duck Severson" `@00:20`; he is "Doc" throughout), a former engineer, ~20-yr
full-time options trader based in the Blue Ridge Mountains (northern SC); runs **readysettrade.com**
— paid classes and a **live trading room** where this strategy is taught (`@38:08`, `@38:21`). Host:
John. This is the third 0DTE iron-fly interview in the KB (John flags two prior ones `@42:16`).
**Commercial motive present** (courses / trading room), though the pitch is comparatively low-key.

## Verdict

> **Conviction: 2/5 · Risk: 5/10 (0DTE ATM short-gamma fly, manual intraday stops) · Tested: NO (0DTE = intraday, not faithfully testable on EOD data)**
> A disciplined, defined-risk 0DTE structure: an ATM iron fly with wings set at the day's expected
> move, entered only after a 30-minute opening-range filter, held ~18 minutes for a small fixed
> profit. The genuinely good parts are real — bounded max loss (~$915/contract on a $30 fly), a
> mechanical entry filter that explicitly stands the trade *down* in corrective regimes (he sat out
> 2022 and the first third of 2025), and a presenter who volunteers a **declining** profit factor
> (3.85→1.92) rather than only the best year. The cap: the returns are **pure verbal self-report with
> no separable statements**, the win rate sits right on top of its own breakeven (a $50 target against
> a $350 stop breaks even at ~87.5% wins — and his 2024 was *86%*), and the whole strategy is
> intraday hand-management with **no automated stops**, so nothing here is verifiable or testable on
> our stack. Same family and same conviction as MEIC / Pulver.

## Mechanics

- **Underlying:** SPX 0DTE (cash-settled, European, more granular strikes). Recommends beginners
  learn on **SPY or XSP** (1/10 notional) first, then graduate to SPX; SPX is what he trades daily.
  `@09:57`, `@10:13`, `@10:42`
- **Structure — iron fly:** a put credit spread married to a call credit spread with **both shorts at
  the same strike** (that's what makes an iron condor an iron *fly*). Short gamma, defined risk. `@03:45`,
  `@06:41`
- **Center (short) strike:** ATM — the **first strike *above* the current price**. Deliberately
  biased up because puts carry richer skew / are "usually overpriced." `@15:51`, `@16:07`
- **Wings (long strikes):** set at the **day's expected move**. Example given: spot ~6850, expected
  move 29.38 → wings 30 pts wide (long call 6880, long put 6820). Wider EM → wider wings; the point is
  to "do the same thing statistically every day." `@07:19`, `@07:56`, `@16:37`
- **Expected-move source:** thinkorswim's published expected move (says tastytrade's number differs
  and he finds it less useful); fallback = the **ATM straddle price**. `@17:19`, `@17:54`, `@18:04`
- **Entry timing / filter (the crux):** enters at **~10:00 ET, after the first 30 minutes** define
  the *opening range*. Two gates: **(macro)** avoid corrective / bear markets — sit out entirely
  (didn't trade this in 2022, nor the corrective first-third of 2025); **(micro)** price must still be
  **inside the opening range** after 30 min, ideally near its middle. If both hold, pull the trigger;
  else no trade. `@11:19`, `@12:14`, `@13:45`, `@14:49`
- **Profit target:** small and fast — **$50/contract (≈14.3% return-on-risk)**, sometimes up to
  **$100/contract (≈28.6%)**. Enters a limit close order immediately on fill (e.g. sold for $20.85
  credit → resting buy-to-close at $20.35 debit). Scales: first lot off at $50, second at $100.
  **Average hold ≈ 18 minutes** (as fast as 5 min on a vol crush; sometimes 30–45 min). `@18:33`,
  `@19:39`, `@19:54`, `@21:01`
- **Stop / loss rule:** **manual**. Pre-computes stop *price levels* (in the example, the expected-move
  boundaries 6821 / 6879) in a spreadsheet; if price hits them he "punches out" by hand. Explicitly
  **no OCO / no resting stop / no automation** (`@23:09`, `@23:24`). Typical realized loss **≈$350**;
  range roughly $200–$400 (`@24:59`, `@25:08`). **Worst-case / disaster risk ≈ $915** per contract on
  a $30-wide fly (= width $3000 − ~$2085 credit) = "about 3× a standard loss." `@27:11`, `@21:34`
- **Adjustments:** none. Tried converting to a "Batman" (second fly as a hedge) and abandoned it —
  costs hours of management and "the numbers don't bear out"; a trending market keeps trending, so
  just exit. Relies on "there's always tomorrow" (5 entries/week). `@23:38`, `@24:07`
- **Frequency / sizing:** trades **~50–60% of days** (121 in 2023, 144 in 2024; little in 2025 YTD due
  to corrective regime). This is **not the whole account** — a **wheel strategy is the base of the
  pyramid; the 0DTE fly is "the cherry on top"** income he says he doesn't need. `@33:50`, `@32:24`,
  `@33:28`
- **Self-rated risk: 4–5** ("relatively lower risk"; defines 10 = naked/OTM-call gambling, 1 = money
  market). `@30:19`, `@30:42`

## Claimed edge & returns

- **2023:** 121 trades, **95% win rate, profit factor 3.85** — his own words: "probably too high."
  `@27:55`, `@34:52`
- **2024:** 144 trades, **86% win rate, profit factor 1.92** — he got "more aggressive" and the numbers
  went *down*. `@28:31`, `@35:07`
- **2025 YTD:** "running about **90%** with a profit factor of **2.1**." `@35:33`
- **Return-on-risk per trade:** 14.3% at the $50 target, 28.6% at $100. `@21:34`, `@22:14`
- All figures are **self-reported verbally**; **no statements, no per-trade log, no third-party audit,
  no screenshot of a broker record** is shown. The sample is also **regime-filtered by design** (he
  removes corrective periods before counting), so the win rate is conditional on his own discretionary
  stand-down calls.

## Objective assessment (where to be skeptical)

1. **The win rate is essentially P(range day) — and it sits on its own breakeven.** With a **$50
   target against a ~$350 stop**, the breakeven win rate is 350/(350+50) = **87.5%**. His **2024 was
   86%** — i.e. *below* breakeven on the pure $50/$350 payoff (EV ≈ 0.86×50 − 0.14×350 = **−$6/contract**),
   yet he reports PF 1.92. Those two can only be reconciled if realized *wins* averaged well above $50
   (the $100 scale-outs) or *losses* were cut below $350 — either way the edge is **thin and entirely
   margin-sensitive**: a handful of $915 disaster days, or a season where losses cluster near the cap
   instead of $200, flips it. This is the exact "high win rate ≈ its own breakeven" pattern flagged in
   `pulver_0dte.md` and `zerodte_breakeven_iron_condor.md`.
2. **No separable track record.** Three years of numbers, zero evidence. Round, self-reported win
   rates and profit factors with no statements to audit. Per the skeptic mandate this cannot raise
   conviction regardless of how plausible the person is.
3. **Manual stops on a 0DTE ATM short-gamma position.** He explicitly runs **no automated / resting
   stops** and "punches out by hand" (`@23:24`). He waves off gap risk ("usually big moves happen
   pre-market or later in the day") — but this is precisely the structure (short straddle body, wings
   only 1 SD out) where a fast mid-morning move blows through a strike while he's the one who has to
   react. "I've never had an issue in the number of years" is survivorship, not a risk model; his own
   April-9-type move is the counterexample he's asked about and hand-waves (`@25:35`).
4. **Regime-filtered denominator.** Sitting out corrective markets is *good discipline*, but it also
   means the reported win rate/PF describe only the benign days he chose to trade — the record has
   removed exactly the environments that produce the losing tail. The strategy's true expectancy
   includes the discretionary "is today a range day?" call, which is unspecified and unverifiable.
5. **"More aggressive → worse" is quietly telling.** 2023→2024 he pushed for more and PF fell 3.85→1.92
   on a *higher* trade count. That's consistent with an edge that is thin enough that added activity
   dilutes rather than compounds it — frequency isn't free.
6. **Commercial motive.** Courses + a live trading room at readysettrade.com. Not disqualifying and
   the sell is soft, but the video is a funnel and the numbers are the marketing.
7. **Costs vs. a $50 target.** SPX 4-leg iron fly commissions + bid/ask on ~50–60% of ~250 days, taking
   a $50 target, means fills matter a lot; he never nets returns against commissions/slippage, and a
   thin per-trade edge is exactly what those eat.

## What's genuinely sound (the diamond)

- **Defined, bounded max loss** (~$915/contract on a $30 fly) — no naked short, no assignment
  (cash-settled SPX), no overnight/gap exposure (0DTE closes same day). The tail is *capped*, which is
  more than several undefined-risk strategies in this KB can say.
- **A real stand-down rule.** The macro filter (don't trade this in corrective/bear regimes) is the
  right instinct for a short-gamma tent and he actually followed it (sat out 2022 and early 2025).
  Most guests claim an all-weather strategy; he explicitly says his is not.
- **Honest about decay of edge.** Volunteering that PF fell to 1.92 and that 3.85 was "probably too
  high" is the opposite of oversell — credit it.
- **Correct position in the book.** He frames the 0DTE income as "cherry on top" of a wheel base, not
  a whole-account strategy — sane sizing philosophy.
- **Sober process:** pre-computed stop levels, immediate resting profit order, fast exit, no
  martingale "Batman" adjustments (he tried and rejected them). Recommends Natenberg's *Options,
  Volatility & Pricing* — a serious book, not a hype read.

## Backtestability

- **Not faithfully testable on our data.** This is a **0DTE, intraday** strategy: a 30-minute
  opening-range filter, a ~10:00 entry conditioned on price location, ~18-minute holds, and **manual
  intraday stops at pre-set price levels**. `silver.options_daily_v3` is **EOD-only (daily bars)** —
  it has no intraday resolution, so none of the timing, the filter, or the fast profit-take/stop can
  be represented. That's the **honest floor: untestable here**, the same null as `pulver_0dte.md`,
  `zerodte_breakeven_iron_condor.md`, and `automation_tat_kyle_lisman.md`.
- **What EOD *could* crudely simulate** — an ATM SPX iron fly entered near the open and marked to the
  daily close — would omit the entire entry filter, the 18-min exit, and the intraday stop, so it
  would **systematically misstate** both win rate and per-trade P&L (it would measure a hold-to-close
  fly, which is not this strategy). Not worth building as a proxy.
- **Faithful test would require** minute/tick SPX 0DTE data (CBOE/ORATS/OptionNet) — out of current
  scope, exactly as noted for the other 0DTE reviews.

## Open questions / next step

- What are the *realized* average win, average loss, and net-after-commission EV per contract? The
  reported PF is close enough to 1.0-adjacent breakeven that costs and loss-size distribution decide
  whether it's positive — and none of that is disclosed.
- How does the discretionary "range day" filter perform out-of-sample, and how much of the win rate is
  that call vs. the structure? Unspecifiable from the video.
- Cross-reference the KB's other 0DTE defined-risk premium sellers — **MEIC** (`zerodte_breakeven_iron_condor.md`),
  **Pulver** (`pulver_0dte.md`), and the two automation reviews — all share the thin-edge-vs-costs,
  win-rate≈breakeven, intraday-untestable profile. This is the ATM-fly variant of that family.
- **Next step:** none on our stack — 0DTE is intraday and not faithfully testable on `options_daily_v3`.
  Do **not** build an EOD proxy (it would measure a different strategy). Revisit only if minute/tick
  0DTE data is acquired.

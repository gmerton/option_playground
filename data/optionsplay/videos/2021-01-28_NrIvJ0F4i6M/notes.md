# OptionsPlay: "How to Sell Straddles and Strangles" (Tony Zhang, webinar, 2021-01-28, 93 min)

_Reviewed 2026-09-24. About 46 minutes of teaching, 30 of Q&A, then 15 minutes on GameStop. Hypothetical $100 stock plus
one live name (PLUG). No backtest is shown. The "at-the-money straddle report" is given to attendees as early access,
and that is the pitch._

## Verdict: 2 / 5

He is honest about the parts that are easy to get honest: unlimited risk, margin, Greeks, and why a short straddle
is short vega/theta and loses to delta. He also gets one subtle thing right that we paid to learn. **Range-based IV
rank is distorted for a year after a spike** (32:32–33:44). That is why OptionsPlay-style range rank lost to rank
percentile at every threshold in our straddle-gate test.

The rules that decide P&L are the problem:

- **High IV rank:** inert or contradicted on our data.
- **"Sell after a big move":** contradicted at the 10-day horizon.
- **Quick 25% / 50% profit-takes rolled into a fresh 45-day trade:** the nearest real-fill test says turnover is
  the loss.
- **Single names picked by share price:** the universe where our short premium dies on costs.

⭐ His strongest assertion, **"buying straddles… is not a profitable strategy in any scenario, I can assure you if
you backtest it"** (01:16:47), is **contradicted by the one option strategy we hold**: the gated 7-DTE long straddle.
It is also contradicted by his own observation that ranges precede big moves (25:42–26:32).

**Selection rule:** neutral view, **high IV rank**, **no earnings or catalyst** before expiry, "after a big move".
**Straddle (ATM) for stocks < $100, strangle (15–30Δ) for $100–500**, ~45 DTE.
**Straddle:** take profit at **25% of max gain**, ~2 weeks in. **Strangle:** take at **50%**, ~3–3.5 weeks.
**Stop at a loss of 50% of the credit.** On a take or a stop, roll to a new 45-DTE trade. Strangles: roll the
untested side toward the money **in the same expiry**.

## Data audit

| item | what was shown |
|---|---|
| Sample | a fictitious $100 stock, one JPM IV chart (no dates, "doesn't really matter what time frame"), one live name (PLUG) and a report list (PINS, SNAP, DBX, CHWY, PDD, FB, BIDU, LOGI) |
| Backtest | none for any rule. Two "back-tested" assertions are spoken without numbers (01:16:47 long straddles never pay; 01:17:51 IV ≈ realised "over the past 20–30 years") |
| Prices | platform quotes, mid vs fill not stated. PLUG straddle $21.35 on a $65.5 stock |
| Costs | not mentioned, apart from "a penny or two" to close a worthless option |
| Control | none. No comparison with the same trade at low IV rank, before the big move, or held to expiry |
| Management numbers | 25% / 50% takes, 2 / 3.5 weeks, 50%-of-credit stop: stated as "optimal", source not given |
| Pitch | "at-the-money straddle report" early access (29:37–36:18), liquidity report, 6 a.m. alert emails for members (01:07:47), CNBC Options Action plug |

## Claims as spoken

| @ | claim |
|---|---|
| 00:00–00:52 | Buying straddles/strangles is "almost virtually no way to make money… long term" |
| 00:52–01:45 | Level 4–5, high margin, truly unlimited risk ("GameStop"): not for small accounts |
| 05:14–08:21 | Short straddle = the risk of one side for the premium of both. $8 credit → profitable 92–108 at expiry |
| 08:49–09:48 | Margin ≈ the greater naked side + the other side's premium, ~20–30% of the stock |
| 10:12–14:22 | Short vega + short theta vs delta drift. Profitable if the stock doesn't drift far |
| 15:11–15:39 | **Straddles on stocks < $100**, not on AMZN at $3,000 |
| 15:32–17:25 | **High IV rank**: "the more elevated IV currently is, the higher the probability it's going to come down". Collect as large a % of the stock price as possible |
| 17:25–18:37 | **Avoid earnings and catalysts** (product events, "battery day") |
| 19:06–21:02 | Strangle: less credit, wider break-evens, slower delta drift ("same risk to reward ratio") |
| 21:02–22:26 | **Strangles on $100–500 stocks** |
| 22:50–24:03 | Strangle + wings = condor; straddle + wings = butterfly |
| 25:15–26:32 | **Don't sell into an identified range; ranges come *after* big moves, and by the time you see one it is "more likely to have a bigger move"** |
| 27:23–28:56 | IV rank = position in the 52-week IV range. Sell above 50, because spikes follow big moves and big moves are followed by sideways trade |
| 32:32–33:44 | The Feb–Mar 2020 spike skews the rank for a year: treat > 30 as high until March 2021 |
| 36:43–37:10 | **~45 DTE**. Straddle ATM, strangle **15–30Δ** |
| 39:58–40:49 | **Straddle: take at 25% of max gain, ~2 weeks. Strangle: 50%, ~3–3.5 weeks** |
| 41:12–42:03 | **Cut at a loss of 50% of the credit** (e.g. $4 on an $8 straddle) |
| 42:03–42:29 | On a take or a stop, roll into a new 45-DTE ATM straddle |
| 42:29–45:40 | Strangle adjustment: roll the untested side toward the money. "Not night and day": −$15 vs −$16 at 120 |
| 48:33–52:22, 01:15:05 | Always close "worthless" shorts before expiry: exercise is possible after the close (the $600k Biogen story) |
| 53:35–54:21 | You can delta-hedge with stock, but it's not practical for retail |
| 54:21–55:15 | The untested-side roll stays in the **same expiry**, not a new 45-day one |
| 01:00:30–01:01:28 | Never sell a 365-day straddle (theta ≈ 0) |
| 01:01:44–01:04:04 | If you expect a big move of unknown direction, **pick a direction** rather than buy a straddle. Buying straddles is "almost guaranteed" to lose |
| 01:08:22–01:09:39 | Closing a credit spread at 21 DTE vs holding: "marginally, roughly the same". Prefer closing to recycle capital |
| 01:11:21–01:13:43 | Unlimited vs defined risk: the PLUG straddle collects $26 vs $7.20 for a put vertical. "Even if the stock goes to 100 you only lose $15" |
| 01:16:47 | "If you backtest [buying straddles when IV is low] it is not a profitable strategy in any scenario" |
| 01:19:06–01:32:39 | GameStop: squeeze mechanics, call-skew may reprice, "someone has to sell" |

## Claims vs our ledger

| @ | claim | tag | our evidence |
|---|---|---|---|
| 00:00–00:52, 01:01:44–01:04:04, 01:16:47 | **Long straddles never pay; if unsure of direction, pick one** | **CONTRADICTED** | The gated **7-DTE long straddle is IN BOOK**: SUPPORTED at t 3.7 over 8 variants, moved to CONFIRMED (borderline) in the 9/22 update (`multiple_testing_correction_2026-09-22.md`). Its gates are **low IV percentile + FVR**. IV pct ≤ 30 earns +7.69% at mid vs +1.83% for the whole pool; ≤ 20 earns +9.19% mid / +7.29% net, t 2.72 (TEST_INDEX, straddle IV-gate row). Mirror test on the same pool: **selling** the 7-DTE ATM straddle loses −1.83% at mid, and the seller's worst cells are exactly the long's gates (FVR ≥ 1.20 −5.04%, CI excludes 0; IV pct ≤ 30 −4.51%) (`short_straddle_and_iv_strangle_2026-09-22.md` §1). "Pick a direction instead": straddle → call/put by trend **FAILS**, the gain is bull-market beta (TEST_INDEX, `straddle_directional_legs_2026-09-16.md`) |
| 25:15–26:32 | Identified ranges precede big moves | **AGREES, and it undercuts his own conclusion** | This is the long straddle's low-IV gate in chart language. Quiet names move more than their options price. It is a reason to **buy** straddles in ranges, the trade he says never works |
| 15:32–17:25, 27:23–28:56 | Sell at **high IV rank**: high IV is more likely to fall | **CONTRADICTED / inert** | Short 7-DTE straddle IV pct ≥ 85: +3.19% at mid, **95% CI [−2.86, +8.57]**, no costs (`short_straddle_and_iv_strangle_2026-09-22.md`). On bull puts, IV rank vs credit/width head-to-head: **zivr −1.89pp, t −1.25**; within-date +0.25pp, t 0.22 (TEST_INDEX). What pays is the **index** IV level in stress (SPY bearish-high-IV bull put t 6.07; SPX condor t 5.21, one bet; `tierab_significance_2026-09-22.csv`), not a name's own IV rank |
| 32:32–33:44 | Range-based IV rank is distorted for a year after a spike | **AGREES** | OptionsPlay's range IV rank is worse than rank-percentile at every threshold (rank ≤ 20 +6.85 vs pct ≤ 20 +9.19), and "his 33 line is inert" (+4.99 vs +5.05 ungated) (TEST_INDEX, straddle IV-gate row) |
| 25:42–28:56, 58:13, 01:13:43 | **Sell after a big move**: stocks go sideways after spikes | **CONTRADICTED (weak)** | `post_shock_vol_premium_2026-09-21.md`: 156 SPY shock episodes vs VIX-decile-matched normal days. 10-day short straddle **−10.8pp (t −1.8)**, after UP shocks **−20.7pp (t −2.1)**: realised vol clusters. The 1-day +4.0pp (t 1.0) is gone in 2018–26. The IV level pays, not the move |
| 15:11–15:39, 21:02–22:26 | Straddles < $100, strangles $100–500 | **NO BASIS** | Share price is not a volatility property. Premium as a % of spot is scale-free. What decides the sign is **liquidity**: 10-DTE single-name 0.30Δ put spreads lose −0.62% net on +1.70% gross, **costs = 136% of gross** (`vrp_shortdte_names_study.md`). PLUG, CHWY, PDD are the thin-chain names where this bites |
| 39:58–40:49, 42:03–42:29 | **Take at 25% (straddle) / 50% (strangle) and roll the capital into a new 45-DTE trade** | **CONTRADICTED (nearest analogue)** | No short-straddle take test exists. On the 20-ETF 45-DTE bull-put roster at real fills (`putspread_exit_capital_time_2026-09-24.md`): per trade **T25 −4.15% net (t −2.86)**, T50 −2.78%, HOLD −1.37%. On **capital-time**, one slot per ticker re-deployed, phase-averaged: **T25 −50.7%/yr (t −3.33 vs hold)**, T50 −34.1%/yr, HOLD −2.3%/yr. Gross, the fast takes look like the best use of capital; net, **the second round trip is the loss**. On a single-name straddle, with wider spreads than ETF puts, it would be worse |
| 41:12–42:03 | Stop at a loss = 50% of the credit | **CONTRADICTED (family)** | Every loss-conditioned exit on short premium we have tested loses. ETF bull puts, 50% take + 2× stop: **−4.3%/trade, t −5.4**, negative in both halves (`etf_put_spread_study.md` §2). His stop is tighter (0.5× credit on an ATM straddle), so it fires more often |
| 36:43–37:10 | 45 DTE, 15–30Δ strangle | PARTIAL | 45-DTE 20Δ strangle, 44 names, real fills, held: **+$0.23/share, 74% win**, worst −$617/share (`logs/exit_21dte_fixed.log`, FIX-1). The worst trade is pre-split AMZN entered 2022-04-01 on a $78.64 credit, a loss of **7.8× the credit** (`exit_21dte_2026-09-23_fixed.csv`). About flat, fat left tail |
| 01:08:22–01:09:39 | 21-DTE close ≈ holding; close to recycle capital | **PARTIAL (risk) · CONTRADICTED (recycling)** | FIX-1, 14,367 strangles: 21-DTE close − hold **−$0.52/share, t −2.42**, halves −0.63 / −0.40, below the bar, so "roughly the same" is fair. It halves risk (sd $9.33 vs $17.09, worst −$291 vs −$617) (`logs/exit_21dte_fixed.log`). "Recycle the capital": the capital-time result above says turnover costs more than it earns |
| 42:29–45:40, 54:21–55:15 | Roll the untested side toward the money, same expiry | UNTESTED · he rates it small himself | $1 of extra credit → −$15 vs −$16 at 120, "not night and day". No row. Already flagged in `2022-10-07_5IvhBIQVujs/notes.md` as the one untouched adjustment axis: low priority, prior negative (two more legs of friction, more short gamma at the money) |
| 01:11:21–01:13:43 | Undefined risk earns 3× the credit of a vertical, so the risk is worth it | **CONTRADICTED on the tail** | Every certified short-vol cell here is index, and the naked versions carry unpriced tails: SPY 1-day short straddle on positive-gamma days, **+13.7% of credit, t 5.6, worst day −604% of credit** → a defined-risk version is required (`gex_spy_straddle_2026-09-21.md`). The strangle panel's worst trade lost 7.8× its credit, on AMZN in the 2022 drawdown. That is the "$3,000 stock" he warns off at 15:11, but the loss is scale-free |
| 48:33–52:22, 01:15:05 | Close near-worthless shorts before expiry | **AGREES** (hygiene) | Post-close exercise is real. The cost is the ask plus $0.65/contract, small next to the tail. Not a return claim |
| 01:17:51 | IV ≈ future realised vol over 20–30 years | AGREES (loosely) | The 10-day VRP panel: **+1.75vp, t 8.93, 17/17 years**, i.e. IV slightly *above* realised on average (TEST_INDEX, VRP panel). That is the premium the seller is paid |
| 01:10:26–01:10:53 | (Jan 2021) complacent tape: sell covered calls now, buy puts on the acceleration | UNTESTABLE (narrative) | — |

## Not tested, could be

Nothing new is worth running. Each of his rules has a row or a close analogue:

- high IV rank: inert
- after a big move: contradicted
- quick takes: lose on turnover
- the 50%-of-credit stop: stop family negative
- 21 DTE: risk only
- long straddles: in book

The only cell without an exact row is his literal **45-DTE ATM short straddle on high-IV single names with a
25%-of-credit take and a 50%-of-credit stop**. Spec for the record, **not queued, prior strongly negative**:

- Straddle pool (the `bci_csp` / straddle names, 2018–26).
- Friday entry at the expiry nearest 45 DTE, ATM call + put sold at the bid.
- Gate: 52-week range IV rank ≥ 50 and no earnings before expiry.
- Arms (paired on the same entries): (A) his rule, 25% take / −50% stop / 21 trading-day backstop; (B) hold to
  expiry.
- House cost model on every traded leg. Month-clustered t on A − B and on A vs zero.
- Also score A against the same trade at IV rank < 50, to charge the gate.
- Expected, from the 7-DTE mirror test, the T25 capital-time result and the 2× stop result: A < B < 0 net.

# Simple Part-Time SWING TRADING STRATEGY (Humbled Trader, Shay)

**Video:** `5zgBtnPHwbY` · 25:35 · published 2024-06-06 · reviewed 2026-09-28 · auto-captions (prices garbled in places)

> **1.5/5 · no new test.** An "event-driven" swing strategy: buy a large-cap earnings gap-up (≥ 3%) in an uptrend, entered
> intraday on the break of the pre-market high, stopped at the pre-market low, sized by fixed dollar risk. Shown with
> **one** hand-picked winner (NVDA, the 10-for-1-split earnings gap) and zero statistics. The mechanisable core has
> already been tested three ways: buying the catalyst day, the earnings gap to a new high, and the intraday breakout
> trigger. All three are NULL or negative against their controls. Fixed-risk sizing and holding winners agree with the
> house; the 3–5% risk per trade and the partial sells do not. The residue that remains is
> catalyst *classification* ("raised guidance, forward-looking"), and forward test WL-5j already covers it.
> Promotional: her own scanner [06:16] and an email list for the calculator [22:05].

## Her rules, as stated

| @ | rule | quote / detail |
|---|---|---|
| 03:08 | Screen = her day-trade gapper scan | "scanning for the top gainers on the day with high volume" |
| 04:10 | Filters | price > $1; pre-market $-volume ≥ $1M (or ~20k shares); **gap > 3%**; **mkt cap > $800M**. "I do not swing trade small cap stocks anymore" [05:15] |
| 06:16–07:19 | Catalyst (the "most important step") | "extremely bullish catalyst and ideally one that's forward looking". Three kinds: earnings beat + raised guidance; sector hype (meme/crypto); IPO hype (the shortest-lived) |
| 09:23–10:27 | Daily chart | uptrend; **above the 200 SMA and the daily 8 EMA**, "riding along the 8 EMA and has a history of reclaiming that indicator" |
| 11:31 | Gap to an all-time high = bullish | "you technically don't have any ceiling… uncapped upside" |
| 12:33–13:37 | Entry | "get long… after it's able to break above pre-market highs". Actual fill: PM high ~1022, bought the pullback to VWAP ~1030 |
| 13:37–14:40 | Day-trade overlay | sold part into the ~20-point intraday move, re-added at the close: "lock in some profit for day trading and then I keep my good average" |
| 18:53–19:58 | Stop | **pre-market low** (1010), not the LOD (1016): "I don't want the stock to sell off the pre-market gap". Risk $20/share |
| 16:46 | Target | "aiming for 3x 4X 5x your risk". The calculator shows 1:1 / 1:2 / 1:3 [22:05] |
| 17:49 | Exits | small partials intraday or on day 2, "each sell was only about 1/10th"; hold the rest on the 15-min/hourly chart. **No mechanical exit rule is stated** |
| 21:01 | Sizing | shares = (account × risk%) ÷ (entry − stop). "3% to sometimes even 5%" if aggressive, 1% if conservative. $100k × 3% ÷ $20 = 150 shares |
| 24:11 | Separate day and swing accounts | "you do not kind of cut your winners too short" |
| 25:13 | Frequency | "you only need one swing trade a month or one or two a year" |

Time commitment: "part-time", but day 1 needs the open and a 5-min chart [15:44].

## Evidence

- **n = 1 winner**, chosen after the fact: NVDA held ~4 days, "at one point I was up… 100 points" [15:44]. She shows a P&L figure but never states it.
- "I traded this swing trading setup many times over the years" [18:53]. No count, win rate, expectancy, or any losers shown.
- Caption oddity: "I would recommend something like 1% risk or even 5% risk" for new traders [22:05] is probably ".5%".

## Claims vs the ledger (`data/studies/TEST_INDEX.md`)

| claim | ledger verdict | row |
|---|---|---|
| Buy a ≥3% catalyst gap on the gap day | **CONTRADICTED**. catalyst-day buy **−0.173R, t −4.70**, both halves negative | DR-EP (arm A), 2026-09-22 |
| Earnings gap = continuation edge | **CONTRADICTED / NULL**. PEAD on the actual surprise is NULL; earnings gaps don't beat their timing control | PEAD 2026-09-20; EP base break [WL-5d] |
| A gap to a new high has "no ceiling" | **NULL**. A close above the prior 252-day high adds **−0.49pp (t −0.64)** vs no break | EP base break [WL-5d]; More Tom ATH re-review |
| Enter on the intraday break of the pre-market high | **CONTRADICTED** (nearest proxy): ORH entry vs the close **−1.22pp, t −3.4**; ORB9 vs a random minute **t −8.50** | Qullamaggie KB row; Fit Mom / ORB9; Stage A |
| Uptrend: above the 200 SMA | **UNDERPOWERED**. c2 (close > 200 SMA) redundant; full Trend Template only +0.575pp/20d | Trend Template ablation 2026-09-22 |
| "Riding / reclaiming the 8 EMA" | **NULL** (nearest): closes-above-9/21-EMA share and slopes don't forecast | Trend smoothness 2026-09-22 |
| A forward-looking catalyst matters | **UNTESTED** (no news archive); mechanical gate adds nothing | DR-EP; [WL-5j] |
| Sell small partials on day 1–2 | **CONTRADICTED**. Trims cost −0.25…−0.33R; Qullamaggie's partial **INVERTED, t −4.39** | Profit-lock; [WL-4] |
| Hold winners on higher timeframes, don't cut short | **AGREES** in spirit: the 20-EMA close trail beats faster exits in every state; stop-only lead was ~¾ beta | Exit speed by state; trail_cost_exposure |
| Fixed-dollar risk → share count | **AGREES** (risk hygiene; the size lever is exclusion) | Size lever; Brandt review |
| Risk 3–5% per trade | **CONTRADICTED**: nothing certified carries 3–5%; 60–70 bp agrees | Brandt review |
| Stop at the pre-market low (gap-hold stop) | **UNTESTED**, but moot: the loss sits in the entry, not the stop (stop-out rates identical, 48.4 vs 48.0%) | Entry-vs-stop MECHANISM 2026-09-20 |

## New test?

**None worth queuing.** Every mechanisable piece (gap-day buy, gap to a new high, intraday breakout trigger, partials) has a
NULL or negative row. Pre-market levels are not in the daily panels; the nearest proxy (ORH) is already −1.22pp vs the close. The gap-hold stop (proxy: prior close) is a
new axis on paper, but it would re-stop an entry that loses to its control (DR-EP arm A). The ledger's entry-vs-stop
mechanism says stop placement cannot rescue that. Her one discretionary input, the forward-looking catalyst
classification, is exactly [WL-5j] (forward LLM classification of gappers)., already queued; not backtestable.

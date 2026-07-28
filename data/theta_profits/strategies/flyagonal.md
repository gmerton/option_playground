# Flyagonal — Steve Gunn

Source: `2025-08-10_y_7vCLAcc9c` — "The Flyagonal Options Strategy: 96% Win Rate and $24k in 2
Months" ([watch](https://www.youtube.com/watch?v=y_7vCLAcc9c)). Guest: Steve Gunn (sjgtrades.com),
career options educator — taught for Online Trading Academy, "educational contributor to OptionStrat,"
and helped develop Kirk Du Plessis's Option Alpha bot platform; sells a butterfly course, a diagonal
course, an alert service, and a forthcoming "flyagonal" class. Host: John.

**Cross-reference:** This is the same structure as Simon Black's **Time Flies** (`strategies/time_flies.md`)
— a **put diagonal below + call broken-wing butterfly above**, delta-neutral, on a cash-settled index.
Both interviews flag the connection: John points to the Simon Black episode at the end here `@34:08`,
and Time Flies' write-up notes Gunn's "fly diagonal" as the mechanically-similar, **independently
developed** twin. Read the two together — the *structure* is shared and genuinely clever; what differs
is the evidence base (Black: 3-yr weekly-published; Gunn: 10-week vendor-tracked) and the commercial
framing (Gunn is selling the method).

## Verdict

> **Conviction: 1.5 / 5 · Risk: 4 / 10 (defined-risk) · Tested: NO**
> The *structure* is sound — it's the same vega-aware construction as Time Flies (long-vol diagonal
> below to catch selloff-driven IV spikes, short-vol BWB above to catch grind-up IV bleed), and that
> core deserves the same respect it earned there. But the **evidence is materially weaker than Time
> Flies and the commercial conflict is much stronger.** The "96% win rate / $24k" rests on **60 trades
> over ~10 weeks of a single, benign, low-vol summer-2025 regime** — far too short and too few losers
> (just two) to estimate the tail of a structure whose own author names a "**large up-move grind**" as
> its Achilles heel `@30:12`. A defined-risk fly that wins 96% and rarely takes a near-max loss can
> still be negative-EV; with n=2 losers you cannot rule that out. The mechanics are **admittedly
> not finalized** ("still being tested," "I'm using AI to determine the exact amount") `@07:39`,
> `@21:53`, so there is no fixed rule set to lock down. The record is vendor-reported (Option Trader
> Assistant), not independently published, and the seller profits from courses/alerts. Conviction
> sits **below Time Flies (2.5)** because the same idea here comes with a thinner record, an
> unsettled rule set, and a louder sales motive — not above it on a flashier headline.

## Mechanics

- **Underlying:** **SPX** for most trades (cash-settled, no assignment, ~$5k buying power per trade);
  also traded RUT, QQQ ("the Q's"), SPY (~$500/trade, 1/10 size), and — notably — **individual
  stocks** (Google, Netflix, Tesla, Nvidia) and IWM as a deliberate robustness test. `@21:05`,
  `@21:42`, `@31:06`
- **Structure ("flyagonal"):** delta-neutral, two pieces sharing the short expiration `@03:16`:
  - **Above the market:** a **call broken-wing butterfly** (BWB) — two short calls at the center, one
    long call on each side, **unequal wing widths**. Example shown: long 6370 / short 6420 ×2 / long
    6480 → 50-pt and 60-pt wings, ~110 pts wide, placed above a 6360 market. Profit comes from decay
    of the two shorts; **negative vega** → it wants vol to *drop* (the usual companion of a grind-up).
    `@05:42`, `@06:12`, `@13:18`
  - **Below the market:** a **put diagonal** — sell a near-dated put, buy a **further-dated** put at a
    **different (lower) strike**. **Positive theta + positive vega** → it wants vol to *rise* (the usual
    companion of a selloff), and its "tent" widens to the downside as IV expands, giving partial
    self-adjustment. First short strike placed **~3% below the market** (still being fine-tuned).
    `@08:52`, `@12:05`, `@15:08`
  - Planned variants ("conagonal" = condor above; "vertagonal" = vertical above) are **not yet built**.
    `@03:03`
- **DTE:** short legs **8–10 days** out; the diagonal's **long put ~double** the short's DTE (16–20
  days). `@22:05`, `@22:19`
- **Profit target:** **10% of max loss measured at trade open**, typically hit in **~4.5 days**.
  Often **"phases out"** — closes one butterfly or one diagonal at +10% to free capital and rolls the
  remainder. **Always out at least 3–4 days before expiration** (avoids high-gamma final days).
  `@22:55`, `@24:04`, `@24:16`
- **Adjustments (<50% of trades):** discretionary, chart-driven. Most common = roll a short strike
  (e.g. center back up, or short put up toward the money) to return to ~delta-neutral; reads the chart
  for resistance/breakout before deciding ("if we're going to stall, I won't even make an upside
  adjustment"). Adjustments **can require additional capital**. `@24:51`, `@26:26`, `@27:51`
- **Self-rated risk:** **3** ("all defined risk… below a five for sure"). `@30:54`, `@31:32`
- **Tracking/reporting:** results pulled from **Option Trader Assistant** (broker-linked), reported as
  **% of capital deployed at trade open**, with commissions included. `@29:06`, `@29:30`

## Claimed edge & returns

- **"96% win rate so far, almost $24,000 in two months while developing the strategy."** `@00:11`
- Detailed stat page: **58 winners / 60 total trades (~97%)**, **2 losers** — one a **$1** loser, one a
  **~$600** loser (SPX, on a large up-move + continued run-up). **$24k total gains**, **avg gain $406**,
  **avg ~10% per trade**, **avg hold ~4.5 days**, ~$4–5k capital per trade, **commissions factored in**.
  `@20:26`, `@29:43`, `@29:58`
- **All trades live**, all "the same basic configuration," over **~10 weeks**. `@29:43`
- Stats "extracted by AI" from his trade log. `@20:15`
- **Self-named Achilles heel:** "a very large up move — 100 points followed by a day or two of grind
  up… you'll find yourself chasing." Downside moves "more forgiving" thanks to the diagonal. `@30:12`

## Objective assessment (where to be skeptical)

1. **n=60 over 10 weeks is not a track record — it's a sample.** A 96% win rate on 60 trades has a
   wide confidence interval, and **2 losers is far too few to estimate the loss tail** of a structure
   that, by the author's own admission, has a fat right-tail failure mode (large up-move grind). This
   is the canonical "high win rate can hide negative EV" trap: defined-risk flies routinely print long
   strings of small wins punctuated by rare near-max losses. The window (roughly June–Aug 2025) was a
   **low-vol, grinding-up regime** — close to ideal for this tent and **completely unrepresentative**
   of a 2022 trend-down or an Aug-2024/Apr-2025 vol shock. The headline measures the regime, not the
   edge.
2. **The strategy isn't finished.** Strike-width above market, the exact % below for the diagonal, the
   short/long DTE multiple — all are "**still being tested**," with AI being used to "determine the
   exact amount." `@07:39`, `@15:08`, `@21:53`, `@22:32` There is **no fixed rule set** to validate;
   any backtest must impose choices the author himself hasn't committed to. "While developing the
   strategy" `@00:11` is doing a lot of work — these are in-sample, optimized-on-the-fly results.
3. **Heavy commercial conflict.** Gunn **sells** butterfly and diagonal courses, an **alert service**,
   and a forthcoming flyagonal class, and is a **paid/affiliated OptionStrat educational contributor**
   — and the entire pitch is demonstrated **in OptionStrat**, which also gets a **sponsor read** at
   `@19:07`. Every favorable P&L tent shown is an OptionStrat **model price**, not a fill. The
   incentives all point toward an attractive headline.
4. **Vendor-reported, not independently published.** Unlike Time Flies' weekly Discord-witnessed,
   multi-year log, this record is **self-reported via a broker-linked app** and **AI-summarized**, with
   no third-party verification. Better than "I can't untangle the results" (Burrito), but still
   **not falsifiable by an outside party**.
5. **Denominator choice flatters the percentages.** "% of capital deployed at open" with ~$4–5k/SPX
   trade is a reasonable basis, but it's **self-chosen** and the "~10% average gain" is on that basis —
   compare on a common max-loss basis before ranking against other strategies. (Same caveat noted for
   Time Flies.)
6. **"Self-adjusting" is partial and discretionary.** The positive-vega downside cushion only helps **if
   vol actually rises** as price falls — not guaranteed (slow bleeds, vol-of-vol, term-structure shifts).
   He concedes time spreads "**act differently than they model**" `@32:17`. And the real adjustments are
   **discretionary chart reads** ("are we at resistance? breaking out?") `@28:07` — i.e. a directional
   judgment, re-introducing the very skill the "200-point range, don't have to be precise" framing
   claims to remove. Adjustments also **consume extra capital**, lowering realized return.
7. **Single-stock trades smuggle in extra risk.** Running it on TSLA/NVDA/GOOG/NFLX adds **earnings
   gaps, assignment (American-style), and idiosyncratic jumps** that the cash-settled-index framing
   quietly drops; lumping them into one 96% number mixes risk profiles.

## What's genuinely sound (the diamond)

- **The vega design is correct and clever — same core as Time Flies.** Pairing a **long-vol put
  diagonal** (profits when a selloff spikes IV) with a **short-vol call BWB** (profits when a grind-up
  bleeds IV) deliberately aligns each wing with the most common price↔vol behavior in its direction.
  This is a real structural idea, independently arrived at by two traders, and it's the strongest thing
  in the pitch.
- **Defined risk, cash-settled (on the index version), no assignment, no blow-up** beyond a known
  per-trade max. The self-rated "3" is defensible *for the index version*.
- **Sound discipline:** quick ~10% profit-taking, mandatory exit 3–4 days before expiry (avoids the
  worst gamma), partial scaling-out to recycle capital.
- **Methodologically literate:** the multi-symbol robustness test (don't trust a system that only works
  on one ticker) is a genuinely good instinct from his 1990s system-design background `@21:05`, and
  he names his own failure mode rather than hiding it `@30:12`.

## Backtestability

- **Testable mechanical skeleton:** SPX (or XSP for size), short legs 8–10 DTE, put diagonal short
  ~3% below market with long put ~2× the short DTE, call BWB above with ~50/60-pt unequal wings,
  delta-neutral at entry; exit at **+10% of entry max-loss** or by **3–4 days before expiry**, else
  flat. Measure win rate, mean P&L, **max loss, and EV after multi-leg SPX commissions + slippage**,
  and — critically — **isolate high-vol/trend-up windows** (2022, Aug-2024, Apr-2025) to probe the
  admitted up-move tail. Expect this floor to **underperform** the in-sample headline, because it
  strips the discretionary fine-tuning and adjustments.
- **Not faithfully testable:** the discretionary roll/adjustment logic, the chart-based "is this
  resistance?" reads, and the still-unfixed parameter choices (widths, % below, DTE multiple).
- **✅ Data confirmed for the index version:** Athena `silver.options_daily_v3` has **SPX and XSP**
  coverage (**46M rows, 2010 → 2026-02-20**, full greeks + bid/ask), and **short-DTE expirations are
  present**, so the 8–10 DTE diagonal + BWB is constructible. **RUT/IWM and QQQ coverage would need
  to be confirmed** before testing those variants; the single-stock trades (TSLA/NVDA/GOOG/NFLX) are a
  separate data + earnings-handling problem and should be excluded from a clean test.
- **⚠ EOD-only caveat:** the table is **daily resolution — no intraday**. The model fits a once-a-day
  cadence reasonably, but the "+10% then phase out partway through the day," the 3–4-day-pre-expiry
  exit, and any same-day adjustment can only be **approximated at the daily close** — intraday
  management cannot be faithfully replayed.
- **Honest null comparison:** vs (a) the **put diagonal alone**, (b) the **call BWB alone**, and (c) a
  generic delta-neutral weekly condor/BWB at matched widths and the same exits — to see whether the
  diagonal-plus-BWB combination adds anything over its parts (the same test prescribed for Time Flies;
  ideally run both on the same engine so the two cousins are directly comparable).

## Open questions / next step

- Over 2018–2026 (incl. 2022 bear, Aug-2024 and Apr-2025 vol shocks), does the mechanical skeleton keep
  positive EV after costs — or does the up-move tail (and a few near-max losses) flip a 96%-win-rate
  structure to negative expectancy? With only 2 historical losers, **the tail is the whole question.**
- How much of the live headline is the **benign summer-2025 regime** vs. the structure? Re-run on
  matched calm vs. stressed windows.
- Because the rule set is **admittedly unfinalized**, pin a single defensible parameterization before
  testing and report sensitivity to width / % below / DTE multiple.
- Confirm RUT/IWM + QQQ short-DTE coverage in Athena if those variants are to be tested.
- **Direct comparison with Time Flies** is the highest-value experiment: same structure, two traders —
  back-test both skeletons on one engine and see whether either's discretionary layer actually beats
  the shared mechanical core.
- **Next step (on command only):** backtest the mechanical skeleton under `backtests/flyagonal/`,
  sharing the engine with `backtests/time_flies/` if/when that is built.

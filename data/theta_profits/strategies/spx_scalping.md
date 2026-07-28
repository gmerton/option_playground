# Intraday SPX Options Scalping — Eddie Lee

Source: `2026-03-08_P5RgXh0bfuU` — "This trader scalps SPX options in seconds"
([watch](https://www.youtube.com/watch?v=P5RgXh0bfuU)). Guest: Eddie Lee, New Brunswick,
Canada; trading since age 15 (value → technical → options ~2018); host: John. Eddie **teaches a
paid course** ("it takes a week to go through the course… hours and hours of lessons," `@63:34`;
repeated references to "my students," "the way I teach") and runs a YouTube channel + Discord — so
this is a **pitch with a course-sale motive**, not a disclosed, independently verified edge.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 6 / 10 (long premium is defined per trade, but blow-up via
> hotkey over-sizing / tilt) · Tested: NO (fundamentally untestable on our data)**
> This is **discretionary intraday scalping of directional SPX calls/puts** — buy at-the-money,
> hold seconds to a few minutes, extract 50¢–$2 per contract off one to three momentum candles,
> repeat all morning. The single best thing is that he's **more honest than the channel norm**:
> he rates it 10/10 risk for beginners, says it takes 3–5 years to get consistent, admits his
> profit factor is only 1.36, and openly retired his old "lotto" trick once it stopped working.
> The single worst thing is that **the entire edge is un-transferable reaction speed and
> screen-reading feel** ("my hands work as my eyes watch the price," `@26:33`) — there is nothing
> mechanical to specify, nothing to falsify, and no separable brokerage track record (the one
> number shown is a self-entered one-month Tradezella journal). The low conviction is not because
> he oversells relative to peers — it's because there is **zero independent evidence and the thing
> being sold is a skill, not a rule.** Untestable on EOD data by construction.

## Mechanics

- **Underlying:** trades off **S&P 500 / SPX levels**; watches **ES futures** only to read
  volume-by-price. `@08:20`. Short-dated / 0DTE-style index options (references "four or five years
  into 0DTE options every day," `@63:13`).
- **Instrument:** **buys outright calls or puts, directionally** — "only buy calls" in an uptrend
  `@26:53`; occasionally sells a **slightly-ITM $10 vertical for a 1:1 risk/reward** at a rejected
  key level `@17:02`. Not a premium-selling strategy despite the channel.
- **Three setups** `@06:42`: (1) **trend/continuation** — consolidation breakout, "wavy" trends
  measured with Fibonacci (favorite, most forgiving); (2) **range** — trade between defined S/R;
  (3) **reversal** — exhaustion into a high-volume level, wait for trend break, fade it.
- **Tooling / signals:** TradingView charts; **8 & 21 EMA**, **VWAP**, volume-by-price, Fibonacci
  retracement (0.382/0.5/0.618) + extension (1.0/1.618), a "stacked EMA" (8/21/50/200 clustered)
  as the start-of-big-move tell `@24:12`, plus a custom "aggro" indicator, Ichimoku, cumulative
  TICK, net options flow (unusual whales), and open-interest / max-pain magnets `@38:29`–`@41:00`.
- **Timeframes:** analyze on **5-min**, execute on a zoomed **30-sec** chart `@21:30`, `@22:36`.
- **Entry:** price reclaims a Fibonacci level / EMA stack and prints a confirmation candle
  (engulfing the prior candle high); enters on the 30-sec break, **scaling in small (1–2 of a
  5-lot early, add on confirmation)** because option fills are hard `@23:42`.
- **Strike/delta:** **at-the-money ≈ 0.54 delta** `@29:06`; goes further OTM early in the day when
  premiums are fat (doesn't need theta — "not in it long enough for theta to decay," `@43:42`).
- **Exit / profit:** no fixed target — Fibonacci extension as a zone; exit on first red candle or
  a close below the 8 EMA `@28:15`. **Rolls winners down in delta:** once ~10 points ITM (~0.6–0.7
  delta), sells the ITM option and rebuys a lower-delta OTM to "lock profit and keep riding" —
  repeats until "risk is free" `@29:32`–`@30:37`.
- **Stop:** **no firm stop** — uses **hotkeys / a Stream Deck** to exit on price action ("risking
  one candle") `@26:15`. Broker = Interactive Brokers `@41:20`.
- **Session:** **first ~2 hours only** now (used to trade all day + power hour; says market makers
  killed the last-hour reversal, now only the final 5–15 min) `@31:51`, `@33:38`.
- **Sizing:** dedicated **$100k day-trade account, uses only $5–10k** of it; 2–5% typical, 10% max,
  10–20 contracts scaled; **daily max loss = a $ limit**; "don't give up >50% of the first half-hour's
  profit" `@42:28`–`@45:00`. Separates day/swing/invest accounts as a blow-up firewall.
- **Self-rated risk:** **10/10 for a beginner, low for the skilled** — "refined risk" if you hold
  your daily loss limit `@50:31`.

## Claimed edge & returns

- **"100–200% monthly"** during 2020–2021 COVID run; **90%+ win rate** then `@00:00`, `@03:57`,
  `@04:54` — self-described "easiest money of my life," a specific benign regime he says no longer
  exists ("selling options didn't work in 2022," `@02:45`).
- **Tradezella, one month, ~500 trades:** win rate **77.94%**, **385 wins / 109 losses**, cumulative
  **$19,211** on a $10k start, **profit factor 1.36** `@53:02`–`@53:58`. Self-entered journal, not a
  brokerage statement.
- **"About 300% in gains"** framing of that $19,211 `@53:38` — *arithmetically it's ~192%*
  ($19,211/$10,000), not 300%.
- **Fastest trade: 4 seconds for $2–3/contract** `@00:00`, `@26:33`.
- **2018→now: "over 2,000%"** — but explicitly a **blended** number across day-trade, swing,
  position, and investing `@58:35` (not separable).
- **"Medium" account up 80% YTD** `@57:29` — but "mostly" from **commodity (gold/silver) swing
  trades with LEAPs**, not scalping `@58:09`.
- **2022 "lotto":** buy cheap OTM near close, once turned "$5,000 into six figures"; **admits it
  stopped working** ~2 years ago `@32:41`–`@34:01`.

## Objective assessment (where to be skeptical)

1. **The edge is un-specifiable, un-transferable reaction speed.** "My hands work as my eyes watch
   the price… 4 seconds" (`@26:33`). There is no rule set to reproduce — entries are discretionary
   pattern recognition on a 30-sec chart executed by hotkey reflex. By construction this cannot be
   written down, replayed, or independently verified, and it is the *whole* strategy.
2. **No separable, verifiable track record.** The only hard number is a **one-month, self-entered
   Tradezella journal** — not a brokerage statement, not audited, trivially curated, and one month
   of a hand-speed strategy is pure noise on the question of edge. Every other figure is either
   blended across strategies (`@58:35`) or from a regime he says is gone (`@04:54`).
3. **Profit factor 1.36 with a 78% win rate means fat-tailed negative skew.** With 385W/109L
   (W:L ≈ 3.5) and PF 1.36, the average **loss is ≈2.6× the average win** — the textbook "pick up
   pennies, occasional big red candle" profile he half-admits (`@54:02`, "big candles on the
   downside can take more losses than my average profit"). A thin 1.36 PF is fragile: it survives
   only if the discipline never slips, and he repeatedly confesses it does ("hotkey hotkey hotkey…
   you blow the account," `@47:01`).
4. **The "300%" is inflated ~1.6×.** $19,211 on $10k is 192%, not the "about 300%" he states
   `@53:38`. Small thing, but it's the one checkable number and it doesn't check.
5. **"Risk is free / can't lose money" is the conditional zero-risk trope.** `@30:37` — you only
   reach "free money" **after** you're already deep green and have rolled to cheap OTM. That's
   locking in a win that already happened, not a structural edge; a trade that goes against you from
   the open never gets there.
6. **Headline returns come from a vanished regime and from non-scalping trades.** 100–200%/month
   and 90% win rate were 2020–2021 "any base breaks out" (`@04:40`); the 80% YTD is commodity LEAP
   swings; the 2,000% is everything blended. The scalping strategy *per se* is evidenced only by the
   one-month journal.
7. **Course-sale motive + survivorship marketing.** Repeated "my students," a week-long paid course,
   Discord, YouTube; the success stories are the ones "who stick around" and "spend the whole
   weekend looking at charts" (`@60:16`) — the ones who washed out aren't counted. He even says most
   students go "did really well → backwards → really well → backwards" and only reach consistency in
   **year 3–5** (`@63:59`), which is an honest admission and a devastating base rate at once.
8. **Health/behavioral tail is real and stated.** Over-size and "my heart rate gets elevated and I
   have to go see the doctor" (`@45:33`); tilt via repeated hotkey firing can blow the account
   (`@47:14`). The defined per-trade risk (long premium) is undermined by an undisciplined-execution
   failure mode he personally experiences.

## What's genuinely sound (the diamond)

- **Per-trade risk really is defined** — buying options outright, max loss = premium paid, no naked
  short-vol tail (contrast the 1-1-2 blow-up). The blow-up route is behavioral (over-sizing/tilt),
  not structural.
- **The risk-management scaffolding is legitimately good discipline**, independent of any edge:
  hard daily $ loss limit, "keep >50% of the first half-hour's gains," separate day/swing/invest
  accounts as a firewall, scale-in-small on hard fills, roll winners down in delta to bank profit.
  These are real, teachable habits (and echo the user's own "risk-first" instincts).
- **Unusual honesty for the channel:** rates it 10/10 for beginners, insists on months of paper
  trading first, admits PF is "not very big," admits the lotto strategy died, admits the 2020–2021
  regime is gone, and doesn't pretend it's passive income. Low oversell on *difficulty* even while
  the *return* numbers are soft.
- **Sensible book taste:** John Carter *Mastering the Trade*, Minervini, Anna Coulling *Volume Price
  Analysis* — mainstream, not guru fluff.

## Backtestability

- **Fundamentally NOT testable on `silver.options_daily_v3` (EOD-only, daily resolution).** This is
  the honest ceiling and it is a hard one: the strategy is defined by **seconds-to-minutes holds on
  a 30-second execution chart**, hotkey exits on individual candles, and intraday scale-in/scale-out.
  None of that has any representation in daily bars — there are no intraday prices, no 30-sec candle,
  no way to model a 4-second trade. Even the SPX 0DTE premium he trades can only be marked once a day
  at close.
- **Beyond the data gap, the alpha itself is untestable in principle** — it's discretionary reaction
  speed and real-time pattern reading, not a parameter set. Unlike Time Flies (whose *skeleton* can
  be stripped out and tested), there is **no mechanical skeleton to isolate**; "buy a call on a
  momentum candle and exit on the next red one" is not a specifiable rule.
- The one adjacent thing that *is* mechanical — the occasional **slightly-ITM 1:1 directional
  vertical at a rejected level** (`@17:02`) — is a plain directional debit spread whose EV is just a
  bet on his level-reading, and would need intraday data to enter/exit as described anyway.
- **How much can't be captured or transferred:** essentially all of it. Reaction speed, hotkey
  reflex, screen-time-earned pattern recognition, and the emotional discipline to hold a daily loss
  limit are the product. A backtest could at most measure "does buying SPX 0DTE ATM on an EMA-stack
  breakout and exiting at close have positive EV" — which is **not this strategy** and would strip
  exactly the intraday timing that is the entire claimed edge.

## Open questions / next step

- Is there **any** separable, multi-month brokerage statement for the *day-trade* account alone
  (not a self-entered journal, not blended with swings)? Without it the 78%/PF-1.36 is unverifiable.
- Does the 1.36 profit factor survive out-of-sample and a trending/high-vol month, given the ≈2.6×
  loss:win asymmetry? One benign month tells us nothing.
- **Next step: none — do not backtest.** This is the untestable end of the spectrum: intraday
  seconds-scale discretion with no mechanical core, on data we don't have and couldn't proxy
  faithfully. The reusable value here is the **risk-management scaffolding** (daily loss limit,
  profit-give-back cap, account separation, scale-in-small, roll-winners-down-in-delta), not a
  trade to evaluate. File and move on.

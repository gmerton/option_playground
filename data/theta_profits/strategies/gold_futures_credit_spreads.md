# Gold Futures Daily Credit Spreads — Azhar Pasha

> ⚠ **Same trader** as [`azhar_pasha_0dte_butterfly.md`](azhar_pasha_0dte_butterfly.md) (his SPX
> 0DTE adaptive-butterfly interview). Both are the same "never take a loss / roll it out / add
> size" pattern — read them together.

Source: `2026-02-01_FFGSFSk6Dn8` — "Selling Gold Futures Credit Spreads For Income (10% Per Month
Case Study)" ([watch](https://www.youtube.com/watch?v=FFGSFSk6Dn8)). Guest: "Azhar Pasha"
(name spoken as "Asha Pasha" `@00:29` / "Ashar" `@31:37` / "Assar" `@31:47` — auto-captions are
unreliable and `notes.md` is blank, so the spelling is uncertain), an anesthesiologist / pain
physician trading from Vietnam, seriously selling premium since 2020; host: John. Prior Theta
Profits guest for his "adaptive 0DTE butterfly" `@02:18`. No product of his own is sold here, but
he repeatedly plugs a **paid third-party tool, "Mentor Q"** (gamma/order-flow data) as central to
the strategy `@08:18`, `@30:16`.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 8 / 10 (never-take-a-loss rolling on leveraged futures; physical-assignment / naked tail) · Tested: NO (untestable — /GC not in our data, and it's intraday)**
> Directional one-sided credit spreads on gold-futures (/GC) **daily** options, picking put-spread
> vs call-spread by reading the London-open trend, 10-delta short / $10 wide, taken off at 80%
> profit. The single best thing is that the *base* structure is defined-risk and he sizes to ~10%
> of margin. The single worst thing — and the reason for the low number — is that **there is no
> stop; he "never takes a loss," he rolls** a spread that has gone 4× against him into the next
> day's expiry, flipping puts↔calls, for a credit. That is the classic loss-deferral pattern that
> looks like a 10%/month machine right up until the path kills it (see `one_one_two_112.md`,
> `short_strangle_reiner.md`). The "10% per month" is **one self-reported account over six months**
> inside a historic gold bull run — a benign regime for a bullish-biased premium seller — with
> realized losses admittedly folded into rolls he declines to book. n=1, unverifiable, and the tail
> (leveraged futures + physical assignment + naked-short-on-a-wrong-way-roll) is real.

## Mechanics

- **Underlying:** options on **/GC (COMEX gold futures)** — he sells options on /GC, not the
  future itself `@04:21`, `@04:35`. Contract ~$4,800/oz `@02:47`; **1 oz per contract**, and these
  are **physically settled, NOT cash** — ITM assignment = a real gold futures contract / physical
  delivery `@04:45`, `@05:03`.
- **Expiration:** **daily** — five expirations/week; the contract opens ~6:00 pm ET and the option
  "settles" the next day at **1:30 pm ET** (out-of-the-money at 1:30 pm = expires worthless; ITM
  after 1:30 pm "does not count against you") `@00:55`, `@05:36`, `@05:52`. He calls it a "1DTE"
  / 23-hour option `@01:16`, `@05:36`.
- **Structure:** a **single-sided vertical credit spread** — either a put credit spread OR a call
  credit spread, **never an iron condor** `@11:22`, `@11:56`. Directional bias by design.
- **Strike/width:** short at the **10-delta**, long **$10 lower/higher** (10-wide) → ~**$1,000
  margin, ~$900–920 max loss** per contract `@07:30`, `@12:47`. On-screen sample (near-money, not
  his standard): sell 4725 put / buy 4715 put = $1,000 margin, $265 credit, $745 max loss `@06:52`.
- **Credit:** his standard 10-delta/$10-wide collects **~$80–100** `@12:47`.
- **Entry timing / direction:** waits for the **4:00 am ET London open** "flurry of orders" to read
  the day's trend `@10:02`; **bullish day → put spread, bearish day → call spread** `@10:47`.
  Direction is informed by **Mentor Q** (paid tool: net gamma, order flow, 1-day max/min, momentum
  score, IV, expected move) `@08:18`–`@09:44`. Explicitly **does not go counter-trend** `@11:11`.
- **Profit target:** **80%**, entered as a GTC close order at open `@14:34`.
- **Stop-loss:** **none.** `@14:50`, `@19:31`
- **"Adjustment" = roll (the core of the risk):** when the **price-to-close reaches 4× the credit
  received** (i.e. a large paper loss), he **rolls to the next day's expiry**, often **flipping a
  call spread into a put spread** (or vice-versa) to re-align with the trend, aiming to roll **for a
  credit** and **never book the loss** `@15:00`, `@15:52`, `@18:40`. May roll **multiple times** and
  **increase contract count / margin** on the roll `@18:57`, `@27:07`. "As long as overall you get
  to close it for a profit, eventually it's not a loss… I know the purists don't look at it that
  way" `@25:55`.
- **Only forced loss:** when **margin runs out** and he can no longer roll `@20:05`, `@23:12`.
- **Sizing:** **≤10% of account margin** on initial trades — the buffer that lets him keep rolling
  `@20:21`; concedes rolls push margin higher `@27:07`.
- **Lower-risk variants offered:** $5-wide instead of $10 (max loss $500) `@23:48`; does **not**
  trade micro-gold (unfamiliar with liquidity) `@24:17`.
- **Self-rated risk: "at least a 7"** — "very volatile, you have to actively manage these" `@22:54`.

## Claimed edge & returns

- **"~10% of account size as profit per month," past 6 months, one dedicated account** `@00:00`,
  `@26:37`. Self-reported; no statements, no per-trade log, no third party. **n = 1 account, ~6
  months.**
- **Win/management split:** "**50 to 60%** of the time" the direction is right and it closes clean;
  "**30 to 40%**" of the time he must actively manage (roll); settles on "**around 60%**" clean
  trades `@25:15`, `@26:12`. Note this is the *clean* rate — rolled trades are counted as wins if
  they eventually close green, per his own accounting `@25:55`.
- **Gold IV** "about **3× that of S&P**" `@00:00`, `@00:37` — the premise, not a result.
- No dollar figures, no account size, no drawdown, no losing-streak example given.

## Objective assessment (where to be skeptical)

1. **"10% per month" is a six-month, single-account, self-reported case study in the best possible
   regime.** Gold has been on a "very bullish run," "up 1–2% every morning" `@13:33`, `@13:48`, and
   his default trade is a **bullish put spread** — so the headline is a bullish-biased premium
   seller measured across a straight-up gold market. That is a coin landing heads six times, not
   evidence of edge. Compounded, "10%/month" implies ~**214%/yr** — an extraordinary claim carried
   entirely by an unverifiable n=1.
2. **"I never take a loss, I roll" is the tell, not a feature.** Replacing a stop with a martingale-
   ish roll (trigger = **4× the credit**, i.e. already a large loss) that adds contracts/margin and
   flips direction is precisely the loss-deferral that converts a *defined-risk* spread into an
   open-ended management problem. It manufactures a high apparent win rate by refusing to book the
   losers — the same mechanism that ran the 1-1-2 from $50K to $526K to **zero** (`one_one_two_112.md`)
   and that his fellow guest's "100% win rate" strangle hides (`short_strangle_reiner.md`). His own
   escape hatch — "the only time you take a loss is a margin problem" `@20:05` — describes exactly
   the terminal state of every never-take-a-loss book.
3. **A $10 spread on a $4,800 underlying is trivially breached.** He himself says gold can move
   **4–5% ($200+) in a day** `@03:53`, `@11:38`. A 10-delta short is only ~10% to be touched, but
   when it *is* touched the move is many multiples of the $10 wing width, so a losing day is an
   instant **full** max loss, not a scratch. The whole strategy's survival therefore rests on the
   roll working every time — an untested assumption in a one-sided trend.
4. **The tail is genuinely nasty, not defined.** (a) **Physical assignment** of a real gold futures
   contract — $27,000 margin per contract at his broker `@21:14` — which he admits he has never
   actually let happen `@05:03`, so his live experience of the worst case is **zero**. (b) On a
   wrong-way **call-spread** that gets assigned, you are **short a gold future with theoretically
   infinite loss** `@22:03`, `@22:20` — the defined-risk framing evaporates at the boundary the
   strategy keeps flirting with. (c) Futures are leveraged, and the ITM-after-1:30 pm "doesn't count"
   quirk `@05:52` invites holding a loser past the point a cash-settled index would have closed it.
5. **Directional edge is disclaimed and outsourced.** The whole P&L hinges on guessing the day's
   direction from the 4 am London tape `@10:02` — reading a trend, which he concedes is "hard to
   miss" only *because* gold has been one-directional `@13:18`. Strip the trend and the direction
   call is a coin flip he pays a **paid subscription (Mentor Q)** to make `@08:18` — a recurring
   cost never netted against returns, and a soft dependency for anyone trying to replicate.
6. **Costs and slippage hand-waved.** Daily expirations = ~250 entries/yr **plus** every roll
   (30–40% of trades, sometimes multiple rolls) — futures-option commissions + bid/ask on each leg,
   on an ~$80–100 credit. None of this is netted against the 10%/month.
7. **Sizing discipline erodes exactly when it's needed.** The ≤10%-margin rule `@20:21` is sound,
   but he admits rolls **raise** contract count and margin `@27:07` — i.e. exposure grows into
   losing trades, the same procyclical sizing that turns a manageable drawdown into a margin call.

## What's genuinely sound (the diamond)

- **The base structure is legitimately defined-risk and sensibly built:** a 10-delta / $10-wide
  vertical, ~$900 max loss, no naked selling at entry — he explicitly warns against naked gold
  options `@12:24`, `@22:30`.
- **He is honest about the important things:** self-rates the risk a **7** (not a 2), stresses that
  it needs **active daily management** and is "not for the passive investor" `@22:54`, `@28:26`,
  leads his takeaways with **position sizing** `@29:06`, and flags the **short-gold danger** in a
  bull market `@14:04`, `@29:26`. He also openly concedes the purist view that a roll is a loss
  `@26:04` — more candor than most guests.
- **The vol premise is real:** gold-futures options do carry elevated IV, and daily expirations do
  offer frequent, liquid premium to sell. There is a plausible VRP to harvest; the problem is the
  *management* wrapped around it, not the premise.

## Backtestability

- **Untestable on our stack — twice over.** (1) **Futures options (/GC gold) are not in
  `silver.options_daily_v3`** at all (the table is SPX/XSP/NDX/RUT/VIX + equities/ETFs), so there is
  no gold-futures option data to test. (2) Even if there were, the strategy is **intraday** — 4 am
  London-open direction read, intraday 4× roll trigger, same-day 1:30 pm settlement, discretionary
  put↔call flips — none of which is representable at EOD/daily resolution.
- **Honest floor:** this is a hard **NULL** for our current data and tooling, not a to-do. The one
  potentially portable idea (sell one-sided verticals on a trending, high-IV underlying, exit at a
  profit target) could only be *analogized* on an index we do have (e.g. SPY/QQQ short verticals),
  which would test a different, tamer instrument and drop the entire roll-management scheme that
  actually drives the results. Not worth building.

## Open questions / next step

- What does the **realized** track record look like if every roll is booked as the loss it was when
  triggered (purist accounting)? The 10%/month almost certainly compresses hard.
- How does the book behave in a **gold selloff or a whippy range** — the one regime the six-month
  sample never saw — where the "don't go counter-trend" rule and the credit-only roll both fail at
  once?
- Actual account size, dollar drawdowns, worst losing streak, and the true cost of Mentor Q +
  commissions/rolls netted out — all withheld.
- **Next step:** none. Flag as **untestable** (no /GC options data + intraday). Do **not** open a
  `backtests/gold_futures_credit_spreads/` directory; if the user wants a proxy, the honest move is
  a separate SPY/QQQ short-vertical study, understood to be a *different* strategy.

# Covered Strangle — Lance Kaminsky

Source: `2024-11-17_-9N7BeCTYEc` — "How to Profit from Covered Strangle - with Lance Kaminsky"
([watch](https://www.youtube.com/watch?v=-9N7BeCTYEc)). Guest: Lance Kaminsky, a full-time high-school
chemistry/physics teacher and retail options trader in Texas, ~18 yrs investing / ~1.5 yrs running
this specific structure; host: John (Norway). Kaminsky runs **thetatraders.com**, where he mentors
"beginner/intermediate" traders — a soft education/sales motive, though he pitches no course price in
the interview. `@00:24`, `@21:18`

## Verdict

> **Conviction: 2 / 5 · Risk: 6 / 10 (short-vol, capped upside + ~2× amplified downside) · Tested: NO**
> A textbook, honestly-described structure — long 100 shares + a covered call + a cash-secured put —
> pitched with unusually little hype. Its single best feature is that Kaminsky doesn't oversell: he
> names the real failure mode himself ("the stock just keeps going down… you could have a pretty big
> loss," `@15:48`) and rates it 7–8/10 on volatile underlyings. The single worst feature is the
> **headline bait-and-switch**: the "75% return, highest-performing, never assigned all year" number
> that opens the video is **not the covered strangle at all** — it's a *different, leveraged, naked
> double-put strategy on /MES futures* run on ~2% of his account in an admittedly "very bullish
> market" (`@00:00`, `@18:47`, `@19:19`). On the covered strangle proper he offers **no separable
> track record and no win rate** — just "results have been pretty good." Conviction is 2/5 (real,
> disciplined, plausible, but unevidenced with a sales motive); it is not lower because the structure
> is legitimate and his risk disclosure is candid. The elephant: a cash-secured put stacked on long
> stock means at the tail you are **long up to 200 shares into a decline while the covered call caps
> your rebound** — asymmetric the wrong way, which "3–4/10" understates.

## Mechanics

- **Underlying:** stocks or ETFs you are **long-term bullish on and willing to hold**, chosen for
  *low* volatility and steady uptrend — "blue chip," dividend-growing names. Worked example is
  **SCHD** (Schwab US Dividend Equity ETF; transcribed "SCD/SD"); also mentions **Ford (F)** as a
  buy-and-hold he only lightly strangles. Can also be run on **futures (/MES, /ES)** with a large
  account. `@01:04`, `@04:57`, `@07:54`, `@08:22`
- **Structure (3 legs):** buy **100 shares** first; then sell **1 covered call** and sell **1
  cash-secured put** — i.e. a covered call + a short put combined. Needs ≥200 shares (or ≥2 futures
  contracts) of willingness because assignment on the put doubles the position. `@02:19`, `@03:14`,
  `@08:22`
- **Call strike (flexible):** slightly ITM for max premium + cost-basis reduction (buy $30, sell $29
  call), or OTM for capital-gains room (sell $32). His own default is **~0.10–0.20 delta OTM** — "not
  trying to make a ton on premium… I want to ride up with the position." `@03:39`, `@10:44`
- **Put strike:** a **cash-secured** OTM put at a price he'd be happy to add shares (e.g. 28 strike →
  $2,800 reserved). `@04:30`, `@04:44`
- **DTE:** ~**1 month** out, both legs. `@07:29`
- **Entry timing:** on individual stocks he **waits out earnings**, sells after; prefers ETFs to sidestep
  the issue. `@17:32`
- **Profit target / exit:** **none intraday — hold to expiration and let it resolve.** "I'm not going
  to manage before that because I'm okay with what happens in any scenario at expiration." `@09:01`,
  `@11:28` (The /MES variant is the exception — closed at **75% of premium**, not held to expiry,
  `@19:19`.)
- **Cost-basis mechanic:** subtract collected premiums from share cost each cycle; roll (re-sell both
  legs) monthly to keep lowering basis "toward infinity" if never assigned. `@06:20`, `@09:53`
- **Adjustments / assignment logic:**
  - *Price between the strikes:* both expire worthless, keep all premium, re-sell — possibly the call
    a bit higher on an up-move. `@09:01`
  - *Put breached (assigned):* now long **200 shares**; sell **2 covered calls, but only above cost
    basis** so a rebound doesn't lock a loss. Small drop → calls ~1 point up; **big drop (24/23 on a
    28 basis) → stop selling calls, wait for recovery, collect dividends.** `@11:28`, `@12:09`
  - *Continued decline:* optionally sell another CSP each round; concedes there is "a limit to how
    long you keep selling puts," suggests a **stop-loss tied to cost basis** for the worried.
    `@12:51`, `@13:05`
  - *Call breached:* "maximum profit at expiration" — capital gain on shares + both premiums; restart
    higher. `@13:30`
- **Sizing:** on the covered strangle, only *some* of his shares (holds the rest as pure buy-and-hold);
  on the /MES futures variant, "about 2% of total account." `@05:15`, `@19:44`
- **Self-rated risk:** **3–4** on "very conservative / strong long-term stocks," rising to **7–8** on
  "riskier positions" with big up/down moves; "not 10 because you take in premium on both sides."
  `@16:24`

## Claimed edge & returns

- **"~75% return this year… highest-performing strategy… haven't been assigned once all year."**
  `@00:00`, `@19:19`, `@19:31` — **but this is the /MES futures naked-double-put strategy, NOT the
  covered strangle.** Self-reported, one benign year, on ~2% of account (`@19:44`). The percentage is
  on a tiny, highly-leveraged futures sleeve (/MES = $5/point).
- **Covered strangle proper:** "results have been pretty good in general," only run **~1.5 years**
  (`@12:51`, `@18:47`). **No win rate, no ROC, no sample size, no per-trade log** is given.
- **Worked SCHD trade:** bought 100 @ 28.39, sold 29 call (+$20), sold 28 put (+$27) = **$47 premium**,
  stated cost basis **27.96**. `@05:27`–`@06:48`. Note an internal inconsistency: he collects "$27" on
  the put at `@05:46` but subtracts "$23" in the basis math at `@06:33` — a single illustrative fill,
  not a result.
- All numbers are **self-reported and unverifiable**; no statements, no third-party audit.

## Objective assessment (where to be skeptical)

1. **Headline bait-and-switch.** The video is titled "Covered Strangle" and opens with "75% return…
   highest-performing," but that number belongs to a *separate* strategy — **naked double short puts
   on /MES futures**, leveraged, closed at 75% PT, on 2% of account, in a year he himself calls "very
   bullish." A viewer anchors on 75% and attributes it to the covered strangle, which he never actually
   quantifies. This is the classic "the shown strategy isn't the one that made the number" pattern.
2. **The short put is the hidden risk, and "cash-secured" hides it.** A covered strangle = covered
   call **+ a naked put**. "Cash-secured" only means the cash is *reserved*, not that the loss is
   bounded to something small: get assigned and you are **long 200 shares**, i.e. up to **~2× the
   downside of buy-and-hold**, precisely when the name is falling. Meanwhile the two covered calls he
   then sells **cap the rebound** to his cost basis. The payoff is asymmetric in the wrong direction:
   full participation down, capped participation up. Rating that "3–4/10" on blue chips understates a
   structure that, by construction, loses faster than the stock it's built on in a real drawdown.
3. **Benign regime, short sample.** 1.5 years (mid-2023→2024) on the strangle and one year on the
   futures sleeve — an equity bull market with no sustained bear. "Haven't been assigned all year" is
   a *regime* statement, not an edge; the whole risk lives in the drawdown that hasn't happened yet.
   His own escape hatch ("wait for the eventual recovery, collect dividends") assumes mean reversion
   that a secular decline or a busted single name does not provide.
4. **Capped upside is a real, unpriced cost.** Selling ~0.10–0.20Δ calls on a name you're "long-term
   bullish on" means every strong up-year is truncated at the call strike. Over a bull run the covered
   strangle can *underperform* simply holding the shares — the premium (SCHD example: ~$47 on ~$2,839
   basis ≈ **1.6%/month gross, capped**) is small compensation for surrendering the right tail on your
   best convictions. He half-admits this by keeping most Ford/SCHD shares as un-optioned buy-and-hold.
5. **No separable track record + education motive.** thetatraders.com mentoring is the reason for the
   appearance; the "results" are a verbal "pretty good." Nothing here is falsifiable or reproducible
   at the strategy level.
6. **Assignment/roll frictions hand-waved.** Monthly re-selling of two legs on dividend ETFs invites
   **early assignment around ex-div on ITM calls**, pin risk, and per-cycle commissions/slippage that
   quietly erode a ~1.6%/month gross. None of this is netted out.

## What's genuinely sound (the diamond)

- **It is a real, textbook structure, described correctly** — no "risk-free," no "guaranteed," no
  invented mechanics. The covered strangle (covered call + CSP, a "wheel" cousin) is well understood
  and legitimately lowers cost basis in a rangebound-to-up tape.
- **Honest risk disclosure.** He volunteers the true failure mode ("the stock keeps going down… a
  pretty big loss," `@15:48`), rates volatile-underlying versions **7–8/10**, and stresses "only do
  this with names you're willing to hold long-term." That candor is above the channel norm.
- **Discipline that fits a busy trader:** low-touch, hold-to-expiry, no intraday management, blue-chip
  low-vol universe, waits out earnings, sizes the leveraged futures sleeve tiny (~2%). Sensible.
- **Cost-basis framing is legitimate** for a long-term holder who is *already* going to own the shares
  — turning idle long stock into monthly premium is a real (small) enhancement when the name behaves.

## Backtestability

- **Among the more testable strategies on this channel.** The covered strangle is **monthly, held to
  expiration, EOD-friendly** — no intraday scalping, no same-day hand-management. `silver.options_daily_v3`
  has SCHD, F, SPY, QQQ and thousands of equities/ETFs with greeks + bid/ask, so the skeleton
  (long 100 sh + short ~0.15Δ 1-mo call + short ~1-mo CSP, roll monthly, assignment-doubling logic)
  is approximable at daily close. This is a rare case where the trader's once-a-month, look-once cadence
  **matches** our EOD resolution well.
- **Honest floor / caveats:** (a) it decomposes into *covered call + short put*, both already
  well-studied, so the test is really "does adding the naked put to a covered call improve risk-adjusted
  return, or just add left-tail?" (b) Must use **total-return** (dividends matter on SCHD-type names);
  (c) early-assignment-around-ex-div on ITM calls can't be modeled precisely at EOD — mark at mid,
  settle intrinsic; (d) the interesting question is **drawdown behavior**, so any test must include a
  bear window (2018-Q4, 2020, 2022), not just the bull sample he ran it in.
- **NOT testable:** the **/MES futures double-put variant** (the 75% headline) — **futures options are
  not in our table** — and any discretionary "wait for recovery / stop selling calls on a big drop"
  judgment.

## Open questions / next step

- Does adding the short put to a plain covered call improve Sharpe, or merely amplify the left tail?
  A/B the two on the same names/period. This is the whole ballgame and is directly testable.
- What is the realized return through a **bear** (2018-Q4, 2020, 2022) on SCHD/SPY, net of the capped
  upside — does the covered strangle beat, or lag, simple buy-and-hold once the right tail is
  surrendered and the left tail is doubled?
- What is an actual win rate / ROC for the covered strangle (he gave none)?
- **Next step (on command only):** backtest the skeleton under `backtests/covered_strangle_kaminsky/`
  on SPY/QQQ/SCHD — long 100 sh + short 0.15Δ 1-mo call + short ~0.20–0.30Δ 1-mo CSP, roll monthly,
  double on put assignment — vs (a) plain covered call and (b) buy-and-hold, total-return, across a
  full cycle including 2022. The /MES variant is out of scope (no futures options data).

# Option Alpha: "GEX Day Trading Results ($1K Per Day Goal)" (Jack Slocum, 2026-03-16, 19:35)

_Reviewed 2026-09-23. It's a solo midday screen-share. He shows SPX gamma-exposure charts on the Option Alpha platform,
two live trades from that morning, a month-by-month P&L-per-day log, a post-mortem of a tilt episode (Mar 5–6), and
three automated bots. He places one more trade on camera. The transcript (`en-orig` auto-captions) and `meta.json` are
in this folder. ⚠ The captions garble several dollar figures in the Mar 6 butterfly segment ("9,700 credit", "$9,800
credit on a $150 risk"). Those numbers are not used below._

⚠ **Provenance.** Option Alpha sells the automation platform used in the video. The GEX tool, the bots and the "WiFly"
community bot linked in the description are all its products. The video is a platform demo as well as a trading
journal.

## Verdict: 2 / 5

He deserves credit for candour. He shows a losing month, admits the P&L is falling each month, and gives an honest
account of going on tilt (a progression-sized bot he forgot about → revenge trades → holding for max profit).

The strategy itself does not hold up. **The GEX part is the "big-gamma strike is a magnet" idea, and that is the half
of our GEX study that came back NULL.** His entries are short-horizon directional debit spreads that bet on reversion
to the largest gamma/OI strike, plus iron butterflies placed to pin at max-OI strikes on the first Friday of the month.
The half of GEX that passed for us (negative gamma → more realised volatility beyond VIX; positive gamma → sell ATM
1-day premium) is not in any trade he shows. The one place it could apply is his WiFly 1-DTE short-fly bot, which he
runs *unfiltered*, and he says it has been flat or down for long stretches. That is consistent with our unfiltered fly
at 0.0%.

The results can't be audited as GEX results. They are whole-account P&L per day, mixing discretionary GEX trades with
at least four bots, and the per-day figure goes $1,194 → $524 → $113.

## RESULTS AUDIT

| item | what the video actually shows |
|---|---|
| Period | Calendar 2026 to date: Jan 1 → Mar 16 (~50 sessions). **Forward, not a backtest.** |
| Live or paper | Stated as "my own personal trades", with a live fill on camera ($2.25, 4 contracts). Treated as live, but **no broker statement is shown**. The P&L comes from the platform's own trade log |
| Headline numbers | Goal $1,000/day on a **$50,000** start ($50k → $250k in a year). **P&L per trading day: Jan $1,194, Feb $524, Mar-to-date $113 (this includes the $1,200 win that morning), YTD $681.** Implied YTD ≈ $681 × ~50 ≈ **+$34k on $50k (~68%) in 2.5 months**. The monthly figures are consistent with that: 1,194×20 + 524×19 + 113×11 ≈ $35k |
| Trend | **Monotone decay**: −56% Jan→Feb, −78% Feb→Mar. He attributes March to tilt on Mar 5–6 (~−$6,000 on Mar 5 alone, by his account) |
| n trades / win rate | **Not shown** for the GEX trades. No trade count, win rate, average win or loss, or max drawdown for the discretionary book. The only bot record given is the long-put bot: "4 wins, around 111 losses" over ~1.5 years |
| What the P&L includes | **Everything in the account.** Discretionary GEX debit spreads, discretionary iron butterflies, the long-put "long shot" bot, a VIX>25 iron-condor bot with progression sizing, the WiFly 1-DTE 60-wide bot, and a bot in a **$12,367 drawdown**. GEX cannot be separated from the bots. The denominator is the account, not the strategy |
| Sizing | SPX **$5-wide debit verticals**: 10 contracts (first trade, +$1,200); 5 × $2.20 = **$1,100 risk** for a $500 target; 4 × $2.25 = **$900 risk** for a $400 target. So roughly 2% of the $50k per trade, with **targets under 1R** (45–50% of the debit) and no stop other than max loss. Tilt trades: iron condor $520 credit / $1,480 risk, a $570 "scalp", and butterflies with credits in the thousands |
| Fills / commissions | Fills at or near mid (he works the limit $2.35 → $2.20 → filled $2.25). **Commissions and exchange fees are not mentioned.** SPX index-option fees per leg are material on $2 spreads, and we can't tell whether the platform P&L is net of them |
| Expiry | Not stated for the GEX spreads. The pricing and holding times (22 min to ~1 hr) fit 0DTE. The Mar 6 flies were "opened 3 days in advance" and held to the Friday expiry |
| How GEX is computed | **Not disclosed.** The Option Alpha GEX chart shows a per-strike gamma-exposure bar profile plus overlays of **open interest** and **same-day call/put volume**. He can replay "what gamma exposure looked like at that minute", so the profile updates intraday. Open interest doesn't change intraday, so the minute updates must come from spot/greeks (and possibly volume). He quotes a **net sign** ("overall the gamma exposure net was negative"), which implies the standard naive convention (customers long calls/short puts). That is our convention too. **The dealer-positioning assumption is never stated or questioned.** The same-day-volume overlay is the only thing beyond our OI-based GEX. It may catch some 0DTE flow that never shows in OI (our known blind spot) |
| Selection | One midday session and one tilt post-mortem chosen by the presenter. The on-camera trade result is not reported |

**Bottom line on the audit:** this is ~50 sessions of one live account. The mix is not disclosed. Returns fall every
month. There is no per-strategy n, win rate or cost line. It is a diary, not evidence that GEX levels pay.

## What he actually trades (codable spec)

**A. GEX strike-reversion debit spread (discretionary; the core "GEX day trade")**
- Underlying: SPX. Vehicle: $5-wide debit vertical, a put spread when price is above the strike and a call spread
  when below. Short strike at or next to the level. Examples: 6710/6705 put spread with spot 6706; long spread
  "back up to 6700" with spot below 6700.
- Level K*: the strike with the largest gamma-exposure bar in the profile *and* heavy same-day call+put volume (6700
  on 3/16; 6850 on 3/5).
- Trigger: spot trades through K* by roughly 0.1–0.3% (6708 vs 6700). Enter against the move, betting on a return to
  K*. No time-of-day rule; entries at ~9:46, ~10:00, ~10:30, ~12:00 and ~13:00. **No regime gate.** On 3/5 he noted
  negative net GEX but used it as a *direction* cue ("downward momentum"), not as a filter.
- Exit: take profit at a fixed dollar target of roughly 45–50% of the debit (e.g. $2.25 → $3.25). Otherwise hold to
  max loss or expiry. No stop, no time stop.
- Size: 4–10 contracts, ~$900–1,100 risk per trade (~2% of $50k).
- A "value" rationale he gives: the spread is "$3.79 in the money and I paid $2.20". ⚠ That is a misreading. With
  spot between the strikes near expiry, a vertical is worth roughly width × P(finish past the midpoint), not its
  intrinsic value. Paying under intrinsic is the normal price of a coin-flip vertical, not a discount.

**B. First-Friday pin butterflies (discretionary)**: short iron butterflies centred on the strikes with the largest
open interest (10.8k, 6.4k, 11k contracts) on the first Friday of the month, opened ~3 days ahead and held for the pin.
They lost when he refused to take early profit.

**C. Bots (automated, not GEX)**: a long-put lottery bot (4W/~111L); a VIX>25 iron condor with progression sizing
(martingale-style, which is how it misfired); WiFly, a 1-DTE, 60-wide SPX fly that sells overnight vol ("overnight
volatility overstated"), flat/down Oct 2024→May 2025 and again since Oct 2025; and one unnamed bot in a $12,367
drawdown.

## Does he use the half of GEX that passed, or the half that failed?

**He uses the half that failed.**

Our study (`gex_regime_pin_2026-09-21.md`, pre-registered, SPY 3,985 days 2010→2026-02, naive OI×γ from the prior
close) found:
- **Regime PASS:** negative-GEX days show **+8.1% realised vol beyond log VIX(t−1) + log RV(t−1), NW t 7.7**, with
  both halves positive (+6.5% t 4.6 / +9.5% t 5.9); QQQ +4.0% t 4.1. It is a volatility effect with no direction.
- **Momentum:** first 30 min → last 30 min × NEG gave +0.057, t 2.0. **UNDERPOWERED.**
- **Pin:** FAIL as registered (−5.4 bps, t −4.2, from a control biased toward ATM). The distance-matched
  mirror-strike diagnostic was **+0.6 bps, t 0.3 on SPY expiry days, and no cell above |t| 1.6: no magnet at the
  largest-gamma strike.**

The money in the passing half came from **selling ATM 1-day SPY premium on POSITIVE-gamma days**:
- straddle +13.7% of credit, t 5.6;
- 2× iron fly +5.8% on max risk, t 3.4;
- the same fly every day 0.0%, so the gamma filter is the whole edge.

Buying premium on negative-gamma days **FAILS** (−0.05%; the extra vol is priced, realised/implied 1.01).

His playbook maps onto that as follows:
- A (reversion to the big-gamma strike) is the magnet claim.
- B (pin flies at max-OI strikes) is the pin claim, stated directly.
- The only regime use (3/5) turns the sign into a **direction**, which our regime test says it does not give.

Nothing he runs conditions on the sign in the way that paid for us.

⚠ **False-negative check (required after a null):** our pin test measures the **open → close** move toward K* from the
*prior close's* GEX. His claim is narrower: after an *intraday overshoot* through K*, price comes back **within about
an hour**. Our daily test does not directly refute that. It is the "creator patterns have no fixed timeframe" case, so
it goes in the queue below rather than being marked contradicted. The priors are still poor. Every intraday price
trigger we have tested ≈ a random minute (Stage A: 11,227 alerts, every intraday arm within ±0.03R of a random later
minute), and his targets under 1R need a high hit rate to pay after SPX fees.

## Claim-by-claim

| @ | Claim | Our evidence |
|---|---|---|
| 00:10 | A big gamma-exposure block at 6700, with heavy OI and daily volume there, means price will come back to it; he faded a move to 6708 and made $1,200 in ~1 hr | ❌ **The magnet claim: NULL at the daily horizon.** `gex_regime_pin_2026-09-21.md`: mirror-strike diagnostic SPY expiry days +0.6 bps (t 0.3), non-expiry −1.7 (t −0.8); no half above \|t\| 1.6. The intraday "overshoot → revert within 1 hr" version is **untested** (see below). One winner, no denominator |
| 01:40 | Second entry: a 6710/6705 put spread "$3.79 in the money" for $2.20 is "a great price" | ⚠ **Pricing misread.** Near expiry with spot inside the spread, fair value ≈ width × P(finish below ~6707.5), about $2.2–2.5 here. It is not a discount to intrinsic. It is a ~50/50 bet sized at ~1R risk for a 0.45R target |
| 03:07 | $1,000/day goal on $50k; Jan $1,194/day, Feb $524, Mar $113, YTD $681 | **Whole-account P&L, not the GEX strategy.** It mixes ≥4 bots. There is no n, win rate or cost line, and it declines every month. ~50 sessions is far below what an intraday edge needs. Our intraday studies need thousands of events before \|t\| ≥ 3 is meaningful |
| 04:35 | On 3/5 net GEX was negative, "a lot of downward momentum", so long put spread toward 6850 | ⚠ **Regime used as direction; ours is volatility only.** NEG → +8.1% RV beyond VIX (t 7.7) says **nothing about direction**. The directional cousin (momentum × NEG) is t 2.0, UNDERPOWERED. And this trade was placed by his long-put bot, not by GEX |
| 04:57 | Long-put "long shot" bot: ~4 wins / ~111 losses in 1.5 yrs, "hits a really big win every once in a while" | **Lottery profile; same family as our long-premium nulls.** 0DTE long strangle EOD floor −26%/trade (Theta Profits KB); 1-DTE long straddle ≈ −30% of premium at every exit (`one_day_straddle_study.md`); long straddle on negative-gamma days −0.05% (extra vol already priced). No P&L is shown for the bot |
| 06:40 | VIX>25 iron-condor bot with "progression" sizing (bigger after 2 wins) misfired after months idle | ✅ **His own lesson is right.** Progression sizing on independent trades adds risk without edge. Our size-lever work says the lever is exclusion, not scaling up (+0.29R OOS). The unconditional high-VIX condor question is closest to our certified bearish-high-IV index put sale (SPY bull put t 6.07, SPX condor t 5.21, one bet), which has a different structure and entry |
| 08:40–11:30 | Tilt: revenge trades, then holding winners for max profit ($1,500 available → −$1,900 max loss), ~−$6k in a day | ✅ **Honest and consistent with our findings**: same-day revenge cycles are the book's largest measured leak (278 same-day cycles, −$8.3k at 19% win). ⚠ But "take the profit that was there" is not supported by our exit work either. Early profit-taking and trims all cost money in our profit-lock study. The failure was sizing and state, not the exit rule |
| 10:03 | First-Friday expiry has very large OI at a few strikes, so iron butterflies centred there will pin | ❌ **Pin claim: NULL.** Mirror-strike diagnostic on SPY expiry days +0.6 bps, t 0.3. The ATM 1-day fly that does pay for us is centred **ATM on positive-gamma days**, not at the max-OI strike, and the same fly every day = 0.0% |
| 14:03 | GEX day trading is hard to automate "just yet" | ⚠ Telling. If the rule can't be written down, it can't be tested, and his results can't be separated from discretion. The spec above is our best reconstruction |
| 15:30–17:40 | Live on camera: price is below 6700 with heavy put+call volume there, so buy a spread for a bounce back above 6700: 4 × $2.25 = $900 risk, TP +$400 | ❌/untested, as at 00:10. A target at 0.44R with no stop needs a hit rate above ~70% before fees. Result not reported |
| 17:50 | "Hoping my gamma-exposure trades make up for" the bot's $12,367 drawdown | Neither leg has shown an edge, so this is hope, not a hedge |
| 18:20 | WiFly (1-DTE, 60-wide SPX fly) sells overstated overnight vol; streaky, flat/down Oct 2024→May 2025 and since Oct 2025; pays after vol contracts following a volatile period | ⭐ **This is the one place our passing half applies, and he doesn't use it.** SPY 1-day ATM fly, prior close → next-day expiry: **the same fly every day = 0.0%**, while positive-gamma days only give **+5.8% on max risk, t 3.4** (2× implied-move wings), and negative-gamma days −5.4% (t −3.1). The QQQ replication failed its bar (t 2.55) but gamma still sorts it (POS +5.24 vs NEG −6.67). An unfiltered 1-DTE short fly going flat for long stretches is what our data predicts. ⚠ Caveats: SPX vs SPY; his wings are fixed 60-point, ours are 2× the implied move; the 1× wing version failed (t 2.0). "Waits for vol to contract after a spike" is the post-shock premium idea, which FAILED against VIX-matched days |

## What I would take

1. **Nothing for the book from the GEX day trades.** Their mechanism is the pin/magnet half we found NULL, and the
   record can't be separated from four bots.
2. **One confirmation of our own filter.** An unfiltered 1-DTE short fly (WiFly) grinding flat for months is what "same
   fly every day = 0.0%" predicts. Our positive-gamma gate is the part that paid. This is not new evidence, only
   consistent with it.
3. **Two behavioural lessons, both already our rules:** never use progression or martingale sizing on independent
   trades, and don't size up to recover a loss (the same-day round-trip leak). His Mar 5 account is a clean worked
   example.
4. **A pricing warning:** "paid less than intrinsic" on a near-expiry vertical isn't value. Price the payoff
   distribution, not the intrinsic value.

## Not tested, could be

1. **Intraday GEX-strike reversion (the part our daily pin test doesn't cover).** Underlying only.
   - Data: SPY 1-min (`data/cache/intraday_hist/SPY_1min.parquet`, 2007→2026-09-17) and per-strike OI×γ
     (`data/cache/gex/SPY_gex_strikes.parquet`, v3 complete 2010→2026-02).
   - K* = the largest-|GEX| strike within ±1% of the open, from the prior close.
   - Event = the first cross of K* by ≥ d (pre-registered, ATR-normalised, e.g. 0.15 × 1-min-ATR-scaled daily range)
     between 09:45 and 14:30.
   - Outcome = P(touch K* within 60 min) and the signed return toward K* at +30/+60 min.
   - **Control = distance-matched**: the mirror strike on the other side of spot, crossed by the same d in the same
     session (the lesson from the biased pin control). Also a random-minute control in the same session (the Stage A
     standard).
   - Split by GEX sign; bar |t| ≥ 3, both halves, per-year.
   - ~½ day on the existing caches. Prior: low.
   - **The option P&L cannot be tested at real fills**:
     - `options_daily_v3` is daily EOD only;
     - we have **no intraday SPY/SPX option bid/ask** (the only minute quotes are the paused 4-expiry GOOG pilot,
       Aug 2026);
     - SPX 1-min underlying isn't cached (SPY is the proxy);
     - 0DTE OI never shows in v3, and same-day strike volume in v3 is end-of-day, so his volume overlay can't be
       reconstructed intraday.
   - A model-priced debit-spread P&L would be mid-priced and would count as an upper bound only. Run the underlying
     test first; if it fails, stop.
2. **Unfiltered vs gamma-gated wide 1-DTE fly (WiFly-style).**
   - Re-run `run_gex_spy_ironfly.py` with a fixed wide wing of ~0.9% of spot (≈ SPX 60 points), in addition to the 2×
     implied-move wing. The aim is to check that his structure, not just ours, carries the gamma sort.
   - One pre-registered extra cell, charged to the GEX family.
   - < 1 hr on the cached quote pull.
   - Would only matter for anyone running WiFly. Low priority because our fly is already in forward paper trade.

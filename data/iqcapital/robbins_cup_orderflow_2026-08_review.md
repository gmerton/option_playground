# IQCapital — "Trading WORLD CHAMPION Reveals the Orderflow Strategy That Won the Robbins Cup" — reviewed 2026-09-20

Video: https://www.youtube.com/watch?v=PL7LKUsCgIQ (58:00, uploaded 2026-08-11). Guest: Chris Creamer, 26, winner of
the July micro day-trading division of the Robbins World Cup (100% in the month, per the host; not independently
verified). Captions: yt-dlp auto-subs, clean. Transcript ~12.4k words.

**Score: 2.5/5.** The most coherent intraday process this KB has reviewed: a stated mechanism, explicit invalidation
and a real risk process. The evidence behind it is one month of competition P&L plus self-reported stats. The part
that decides entries (reading footprint candles) is discretionary and can't be tested with our data. The channel is a
prop firm that sells challenges ($9 for a 50K futures eval, mid-video ad), so the video is marketing.

## The method (MNQ futures, first 90 minutes of the New York session, 5-minute execution)

1. **Environment**, set before the open. Higher-timeframe structure (1h/4h): is value migrating up, down or
   sideways? Plus the **gamma regime** from *naive* GEX on QQQ/NDX (Tanuki Trade). In positive gamma, dealers sell
   rips and buy dips, so volatility is damped and breakouts fail. In negative gamma, dealers chase, so volatility is
   amplified. He notes the call wall, put wall and gamma-flip level but doesn't trade off them.
2. **Location.** Volume-profile value area. With the trend, buy only at a "discount": below the value-area low AND
   inside a 0.705 / 0.786 / 0.886 Fibonacci pullback zone that sits outside value. The zone needs a swing point first.
   **Below 0.886 the idea is dead.** Low-volume nodes / fast "inefficient" moves are preferred locations.
3. **Confirmation** (footprint charts: bid×ask volume + delta per price level). Absorption: heavy negative delta
   and the candle's point of control at the extreme of the lower wick, with no price progress ("effort without
   result"). Then the balance shifts: ≥ 400% ask imbalances light up. He waits for **a second seller push that fails
   higher**, then goes long. Stop beyond the failed sellers.
4. **Management.** Target swing highs/lows (resting orders) or the POC. If buyers can't reclaim the value area, move
   to breakeven or cut. Trail behind continued buyer aggression. Typical outcome 1.5–2R.

**Filters / process:** no trade when MNQ volume is < 20,000 contracts per 5-min bar (participation gone, lunch).
Hard shutoff ~90 minutes after the open (his own data showed trades getting "dramatically worse" after that). Stop
after 2 consecutive losses. 0–2 trades a day. A/B/C "game" sessions graded on execution, not P&L. "Bad loss" =
anticipating without confirmation, even when it wins.

**Claimed stats:** win rate 60–65%, profit factor ~1.8, 1.5–2R. ⚠ These don't fully fit together: a 62.5% win rate
at 1.5R per win implies PF ≈ 2.5. PF 1.8 implies the average win is ≈ 1.1R, which is plausible once breakevens and
trailed exits are included. That's about +0.3R per trade if true.

## Against our evidence

| his claim | what we've measured | read |
|---|---|---|
| Buy location (discount in a value-up structure), not the breakout | **We select well, enter badly** (2026-09-20): breakout entries are 2.6 ADR worse than a later entry; the retrace entry beats the breakout in 6/6 cells, but t 0.48 | **Agrees in direction.** Our version is PARKED for lack of power, not refuted |
| Confirmation = a failed push then a reclaim (effort vs result) | **Stage A**: our UR (undercut & reclaim → VWAP) and ORB triggers ≈ a random minute (±0.03R, 11,227 fires); the alert funnel adds nothing | His trigger belongs to the same family as UR, with footprint delta replacing VWAP. **Our price-only version of this family has no edge.** Whether aggressor-side data rescues it can't be tested without tick data |
| Positive gamma → failed breakouts; negative gamma → trend/amplify | the intraday momentum (noise-band) paper we replicated uses exactly this mechanism (dealer gamma hedging) | **Testable with data we have**: naive GEX from `options_daily_v3` OI × gamma (to ~Jul 2026) against QQQ 1-min 2007→ |
| Only the first 90 min; hard shutoff; skip low participation | exit-timing + journal: same-day round trips −$8.3k; D-grade days 82 fills avg −$169 vs A-grade 39 fills +$1,752 | **Agrees.** Fewer decisions is the one intraday lesson every source and our own book share |
| Stop after 2 losses in a row | Cameron's "80% chance of doubling the loss after breaching max loss" is queued (Breitstein test 1) on the journal | **Testable on your journal**; fold it into that test |
| 1.5R targets | chosen to fit prop-eval math (drawdown $2k / target $3k = 1.5), in his own words | a rule for passing evals, not for maximising expectancy. Ignore for our book |

## What's worth taking

1. **The GEX-regime claim is the one testable, mechanistic idea here, and it belongs in the parked order-flow row
   (b).** Test: compute naive dealer gamma for SPY/QQQ each morning from v3 OI × gamma (dealers assumed short puts /
   long calls: the naive convention) and check whether its sign predicts (i) the day's range vs ADR, (ii) whether an
   opening-range breakout follows through or fails, and (iii) noise-band returns. Controls: the same days by VIX
   level, since GEX sign largely tracks the VIX regime, so it must beat VIX. About 1 day.
2. **"Two losses in a row → stop" and a hard time shutoff:** add both to the queued journal test (Breitstein test 1).
3. **"Bad loss = entered without confirmation, even if it won":** this is your A/B/C report card. Nothing new, but the
   same conclusion from someone with P&L on the line.

## What's NOT worth taking

- **A one-month competition win is not evidence.** Competitions reward maximum variance, and he says he is
  "extremely aggressive in evaluations". Across many entrants, someone makes 100% in a month by chance.
- **The footprint confirmation** (absorption, 400% imbalances, second failure) is discretionary pattern-reading with
  no rule precise enough to backtest, and we have no historical aggressor-side data (Tradier = prints only; no L2).
  Buying MNQ tick data (e.g. Databento) to test a discretionary read would be expensive and still wouldn't settle it.
- **Fibonacci 0.705/0.786/0.886:** no mechanism, and the zone is doing the work that "a pullback" does.
- It's MNQ futures, outside our instrument set. The transferable parts are the regime idea and the process rules.

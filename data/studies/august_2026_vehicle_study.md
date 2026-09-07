# August 2026 — would a different long vehicle have helped?

*2026-09-06. Follow-up to `august_2026_luk_tito_lens.md`. Question: for the same long entries and exits, would a long call, a short put, or a put credit spread have improved risk/reward over buying stock?*

Two sources of evidence. First, the book's own August option trades, placed under the same entry discipline as the stock trades. Second, every closed August long-stock trade (166) repriced as three option structures at its actual entry and exit prices and dates, using each name's at-the-money implied vol backed out from that day's option prints in `silver.options_daily_v3` (bid/ask and greeks are not populated after mid-July; `last` with volume is). Structures: ATM call nearest 30 DTE, short put at 30 delta same expiry, 30/15-delta put credit spread. Marks are Black-Scholes at entry (entry-day IV) and exit (exit-day IV), so IV change over the hold is included; slippage of half a 3% (calls) or 5% (puts) spread each way. Same-day trades are priced as pure delta moves. Scripts: session scratchpad `vehicle_real.py`, chains in `aug_chains.parquet`.

## 1. The book's own option trades in August (closed, long side)

| Vehicle | n | P&L | win | median hold | median strike / spot | median DTE |
|---|---|---|---|---|---|---|
| Long stock | 166 | −$2,406 | 22% | 0 days | | |
| Long call | 104 | −$3,101 | 23% | 1 day | 1.09 (9% OTM) | 22 |
| Short put | 26 | −$2 | 58% | 4 days | 0.90 (10% OTM) | 31 |

Long calls by strike: the only bucket that made money was 0 to 5% OTM (26 trades, +$728, 35% win). 5 to 15% OTM lost $1,245 and more than 15% OTM lost $1,857 at an 18% win rate. By tenor: under 7 DTE made +$1,221 at 38% win (gamma on the day-trades), 7 to 45 DTE lost $3,271. The short puts broke even at a 58% win rate despite 46% of them being on extended entries and most classified as fighting the trend; the one CLS earnings gap (−$992) offset the other 25.

## 2. Repricing the 166 stock trades (165 priced)

Per 100 shares versus one contract, identical entry and exit:

| Vehicle | total | win | worst | best | capital at risk (median) | P&L per $ risked, mean |
|---|---|---|---|---|---|---|
| Stock, risk = 2% stop | −$13,665 | 25% | −$4,432 | +$9,992 | $301 | −14% |
| ATM 30-DTE call, risk = premium | −$23,888 | 15% | −$3,269 | +$5,590 | $1,157 | −5% |
| Short 30-delta put, stopped at 2× credit | −$5,857 | 23% | −$864 | +$2,486 | $1,175 | −2% |
| Put spread 30/15 delta, risk = width − credit | −$4,525 | 20% | −$617 | +$1,347 | $907 | −2% |

Sized to the same dollar risk per trade as the stock's 2% stop (so roughly 0.2 to 0.3 contracts per 100 shares):

| Vehicle | total | win | worst | best |
|---|---|---|---|---|
| Stock | −$13,665 | 25% | −$4,432 | +$9,992 |
| Call | −$5,649 | 15% | −$874 | +$1,241 |
| Short put | −$1,227 | 23% | −$226 | +$520 |
| Put spread | −$1,335 | 20% | −$206 | +$378 |

By hold length (per contract):

| Hold | n | stock | call | short put | put spread |
|---|---|---|---|---|---|
| same day | 85 | −$14,310 (14% win) | −$12,088 (6%) | −$8,749 (1%) | −$4,741 (1%) |
| 1 to 3 days | 42 | +$415 (19%) | −$4,633 (17%) | +$122 (24%) | −$552 (17%) |
| 4+ days | 38 | +$231 (55%) | −$7,167 (32%) | **+$2,770 (71%)** | +$768 (66%) |

Extended entries: stock −$13,026, call −$17,422, short put −$2,743, spread −$2,466. Not extended: stock −$639, call −$6,466, short put −$3,115, spread −$2,059.

## 3. Reading

- **No vehicle rescues the entries.** Every structure lost on the same trades. The underlying moved a median −1.1% from entry to exit and 32% of trades moved less than 1% either way. Options cannot make money on that.
- **Long calls are the worst vehicle for this book**, on the book's own trades and in the repricing. Median ATM IV at entry was 75%, so a 30-DTE ATM call cost 8.7% of notional, and the median hold was zero days. The 15% win rate is the stock's 25% minus every trade that was flat or slightly up and got eaten by the spread and a day of theta. The book's own calls were struck 9% OTM at 22 DTE, which is worse still. The only call variant that worked was 0 to 5% OTM held under a week on a name that moved, which is a gamma trade, not a swing vehicle.
- **Short puts and put spreads cut the loss by 60 to 70% at equal risk**, and they are the only structure that was positive on the trades held 4 days or more (71% win on the short put). That is the arithmetic of a book whose entries are mostly flat-to-slightly-down: a 30-delta put 8% below spot survives a −2% drift and collects the 75% IV. It also caps the two ways the stock book got hurt: the worst single trade drops from −$4,432 (MU) to −$864, and 82 stopped-through losers become bounded losses.
- **But the short put gives away the winners.** STX +$9,992 on stock became +$2,486 on the put; SOLT +$1,650 became +$207. Across the 15 trades where the stock moved more than 5%, stock made $28,935, the call $15,407, the short put $7,214. If the entry problem is fixed and the book starts holding through the moves, the short put becomes the wrong vehicle again.
- **The put spread is the short put with a seatbelt**: nearly the same P&L on these trades, half the capital, no gap tail (CLS), and the risk is defined the way Luk sizes trades, from a fixed max loss.

## 4. Answer

For the August book as it was actually traded, yes: a 30-delta put credit spread or short put on the same entries would have lost a fraction of what stock lost, because the entries were extended, mostly flat over the hold, and often stopped late. That is a statement about the book's entry quality, not a general edge in selling puts.

The vehicle decision follows the entry decision:
- Extended or uncertain entry, or a name with IV above ~60%: sell the put spread. Bounded risk, the high IV works for you, and a −2% drift still pays.
- Clean pullback into the rising EMAs, IV moderate, you intend to hold through the 9 EMA: buy stock (or slightly ITM calls with 45+ DTE if you want the convexity). This is the only setup where the +5% tail exists, and the short put throws it away.
- Never the book's default call: 9% OTM, 3 weeks out, held a day. That vehicle lost in every configuration tested.

## Caveats

Marks are model prices anchored to print-implied ATM vols, not executable quotes; skew is ignored (OTM puts would have carried more premium than the ATM vol implies, which flatters the call comparison and understates the put credits slightly). Same-day trades are delta-only. Stock risk is set at a notional 2% stop, though the actual book often lost more than that; the risk-equalized table is therefore generous to stock. One month, 165 trades, one trader's entries.

# August 2026 trades through the Martin Luk / Tito Adhikary lens

*2026-09-05. Companion to `august_2026_retrospective.md`. Every flat-to-flat trade cycle opened 8/1–8/31 (from `journal_trades` via `reconstruct_trade_cycles()`) scored at its entry session against the two rulebooks in `data/martin_luk/philosophy/principles.md` and `tito_selection_playbook.md`. Script: `run_trade_lens.py --start 2026-08-01 --end 2026-08-31`; per-trade table: `august_2026_luk_tito_lens_trades.csv`. Prices: yfinance adjusted daily bars; features use only sessions before the entry, plus the entry day's own bar. Option trades are scored on the underlying's chart.*

## Scope

| | n | P&L |
|---|---|---|
| All August cycles | 548 | +$1,125 |
| Multi-leg structures opened at one timestamp (straddles, spreads, condors) | 132 | +$4,306 |
| Directional single-leg trades scored below | 411 | −$3,181 |
| of which long side | 308 | −$5,581 |
| of which short side | 103 | +$2,400 |

The systematic option book made money. The discretionary directional book lost it, and the long side is where the loss lives.

## 1. Entry location — the extension finding, quantified

Long-side trades bucketed by how far the entry was above the 21 EMA, in units of the stock's own 20-day ADR:

| Distance above 21 EMA | n | P&L | win rate | avg |
|---|---|---|---|---|
| at or below the 21 EMA | 59 | +$435 | 31% | +$7 |
| 0 to 1 ADR | 107 | −$133 | 24% | −$1 |
| **1 to 2 ADR** | **81** | **−$4,569** | 22% | −$56 |
| 2 to 3 ADR | 33 | −$702 | 21% | −$21 |
| 3 to 5 ADR | 22 | −$771 | 18% | −$35 |
| over 5 ADR | 6 | +$160 | 33% | +$27 |

Luk's line is "buy at the EMAs, skip if more than ~3% above the ideal point." Read in ADR terms the book's edge sits inside one ADR of the 21 EMA and dies past it. The 1-to-2 ADR band is the biggest hole: it looks "not that extended" on a chart and it is where the money went. Flagging entries as extended (more than 2 ADR over the 21 EMA or more than 5% over the 9 EMA): 122 trades, −$6,177, 20% win. Not extended: 186 trades, +$596, 27% win.

Other Luk entry flags, long side:

| Flag | n | P&L | win |
|---|---|---|---|
| Bought a ≥3% gap-up | 57 | −$4,146 | 21% |
| No gap | 251 | −$1,435 | 25% |
| 9>21>50 EMA stack up | 125 | −$439 | 28% |
| Stack not up (buying below or through falling EMAs) | 183 | −$5,142 | 22% |
| Entered in the first 30 minutes | 48 | +$371 | 19% |
| Entered after 30 minutes | 260 | −$5,952 | 25% |
| SPY above its 21 EMA at entry | 288 | −$4,785 | 25% |

Two of his rules bite hard (extension, gap-ups, stack). One does not: the "sit out the first 30 minutes" rule was not the leak. Neither was index context. Almost every entry was made with SPY above its 21 EMA.

## 2. Setup classes

| Class (long side unless noted) | n | P&L | win |
|---|---|---|---|
| Fight the trend: long below falling EMAs | 85 | −$3,823 | 19% |
| Extended chase | 64 | −$1,193 | 25% |
| Gap chase (bought a ≥3% gap in the first hour) | 7 | −$1,023 | 14% |
| Luk pullback into rising EMAs | 59 | −$610 | 27% |
| Uptrend, no defined trigger | 19 | −$170 | 32% |
| Tito A: base breakout, stacked | 14 | +$382 | 14% |
| Tito B: earnings/EP breakout, day-after thrust above the pivot | 4 | +$496 | 75% |
| No setup (mixed EMAs) | 97 | +$2,462 | 34% |
| Short a stacked uptrend (Luk says don't) | 48 | +$614 | 44% |
| Luk short: bounce into declining EMAs | 13 | −$295 | 31% |

Three readings. First, the largest single class is "long below falling EMAs": 85 trades, mostly semis and AI hardware after the sector topped on 8/17, plus dip-buys in names already broken. Luk calls this the laggard's tricky bounce and says his younger self got stopped on it "100% of the time." Second, the rule-compliant setups did not make money either, they just lost less. Luk pullbacks were 27% winners at −$10 each. The month was hostile to the style (see the retrospective), and the compliant trades were still cut in a day (below). Third, the short book was profitable precisely where Luk says not to short, into stacked uptrends, because the second half of August rolled those over. That is regime luck, not a repeatable edge.

## 3. Universe and theme

Tito's first filter is a history of big moves; Luk's is hottest theme, then highest ADR, then liquidity. On ADR and liquidity the book was fine: 231 of 308 long entries were in names with ADR ≥ 4% and 302 of 308 traded over $100M a day. The failure was theme.

| Theme | n | P&L | win | Aug return of the group |
|---|---|---|---|---|
| AI hardware / optical (AAOI, COHR, HPE, DELL, GLW, CIEN, ALAB, CRDO, DRAM) | 93 | −$3,048 | 24% | hardware +9%, but semis peaked 8/17 |
| Semis (INTC, MRVL, MU, AMD, LRCX, SOXL) | 82 | −$2,560 | 33% | +3% (first half +9%, second half −5%) |
| Software | 80 | −$431 | 32% | +13% |
| Crypto (BMNR, CRCL, IBIT, ETHA, HUT, MSTR) | 28 | **+$5,174** | 50% | +25%, all after 8/14 |
| Biotech / health | 12 | +$325 | 42% | +5 to +24% |
| Metals / energy | 4 | +$383 | 25% | +7 to +39% |

175 of 411 directional trades were in the one group that round-tripped. 28 were in the group that led, and those 28 made more than the whole book lost. Luk would have had you in crypto, software, gold, and biotech by the second week. The repeat-traded names tell the same story: HPE 14 cycles for −$971, INTC 10 cycles at a 10% win rate, FCEL 7 cycles with no winner, AMZN and CRWV 6 each with no winner, MDB 6 cycles entered a median 4.3 ADR above the 21 EMA.

## 4. Holding period and exits

| | n | P&L |
|---|---|---|
| Same-day round trips (long side, closed) | 132 | **−$7,884** |
| Multi-day holds | 164 | +$2,375 |

Tito's own log says sub-10-minute trades are his one negative-expectancy bucket, at −$26 a trade as the deliberate cost of cutting fast. Here the same-day bucket ran −$60 a trade and was 45% of all long-side trades. This is not fast loss-cutting, it is a day-trading book that Tito would say has no tail: his 4+ hour trades are 82% of his profit.

Exit versus the 9 EMA rule (long side, closed): 198 of 296 trades were exited before the stock ever closed below its 9 EMA, at a median hold of zero days. Had they instead been held to that first close-break the median outcome was −2.6%, so the exits were not the problem. The entries were. The 22 stock winners that were sold before any 9 EMA break made +$6,483 as executed and would have made only +$910 held to the break: selling into strength, which Luk endorses, was done well. The exception is the four winners whose 9 EMA never broke by 9/4 (BMNR, CRCL, FCX class): +$2,537 as executed, +$8,712 marked to 9/4. Tito's "hang tight on the daily close, 20 EMA never breaks on a real winner" is the rule that would have paid, on the handful of trades that had legs.

Stop discipline: 82 of 220 long-side losers went more than 2% against entry on a close basis before being exited. Those 82 trades lost $13,032, more than double the book's net long-side loss. For stock longs, the median loss was 1.31% of notional and the median win 2.83%, a 3.1 payoff ratio, which at a 21% win rate is still negative expectancy. Luk's arithmetic (0.3% risk, stop ≤ 2%, size from the stop) only works if the stop is honored: capping the 40 stock-long losers that blew through 2% at exactly 2% turns the stock-long book from −$2,406 to +$1,074.

## 5. Counterfactuals (closed long-side trades, n=296, actual −$5,509)

| Rule applied to the actual August trades | trades kept | P&L | win |
|---|---|---|---|
| Luk: skip extended entries | 179 | +$667 | 28% |
| Luk: skip extended and skip ≥3% gap-ups | 169 | +$1,209 | 29% |
| Luk: only stacked, not extended, no gap | 75 | +$131 | 31% |
| Tito: big movers with a defined A/B/pullback trigger only | 47 | +$337 | 32% |
| Drop same-day round trips | 164 | +$2,375 | 38% |
| **Drop same-day round trips and skip extended** | **92** | **+$5,625** | **45%** |
| Luk 2% stop cap on stock-long losers | 166 | +$1,074 (from −$2,406) | |

These are not additive and they are in-sample, but the direction is unambiguous. The two filters that matter most are not about setup recognition at all: hold the trade past the day you put it on, and do not buy more than one ADR above the 21 EMA.

## 6. What each of them would say

**Luk:** the entries were in the right kind of names (fast, liquid) in the wrong group at the wrong location. Buy the first pullback into the rising 9/21 in the hottest theme, place the stop before the fill and never widen it, size from the stop. The book did the opposite on all three: bought strength 1 to 2 ADR out, in the group that had already run, and let 82 losers run past 2%. The one thing he would not criticize is the exits on winners.

**Tito:** the universe was right (big movers) but the trades had no archetype. Only 18 of 308 longs match his A or B signature, and his B trades (day-after-catalyst, pivot held) were the best class in the book at 75% winners. 132 same-day round trips is a scalping book, and his own numbers say scalps are the drag, not the profit. On the four trades that were real winners the daily close never broke the 9 EMA and the book sold them in a day. Manage on the daily close and stop watching the intraday tape.

## Caveats

One month, small per-class counts, features from daily bars only (intraday extension and stop placement are invisible here). The setup classifier is a heuristic on EMA geometry and will misfile edge cases (an ETF breakout after adjusted data, a laggard turn that August happened to pay). The counterfactuals assume the skipped trades would not have been replaced by others.

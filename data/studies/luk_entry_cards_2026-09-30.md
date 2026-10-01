# Martin Luk entry cards: what he says about stop, size and trigger (2026-09-30)

**Data:** `data/martin_luk/trades/entry_cards.jsonl`, 113 cards, one per clean entry in his trade log (the 64 rows
still open on the clarification worklist are not carded). Built by `build_luk_entry_cards.py`.

**How they were made.** Each entry's stream transcript was read in full and coded from his words only: no prices, no
charts, no outcomes. Every coded field carries a verbatim quote with its timestamp. All 487 quotes were machine-checked
against the transcripts (0 failures), and I read the quotes behind every card that carries a number. Coder confidence:
34 high, 69 medium, 10 low.

## What the cards show

**1. He rarely states stop or size on the entry itself.** 23 of 113 cards carry any number. A stop location is named
on 8, a stop distance on 8, account risk on 17, position size on 5. Another ~27 have only words ("really tight",
"half size", "ran out of buying power"). Anyone copying his entries from the streams is not being told the stop.

**2. When he does state them, the numbers are consistent.**
| | stated values | median |
|---|---|---|
| stop distance (8) | 1.0, 1.0, 1.0, 1.2, 2.0, 2.0, 2.0, 2.5% | 1.6% |
| account risk per trade (17) | 0.1 to 0.5%, one accidental 1.0% from slippage | 0.3% |
| position size (5) | 25, 25, 25% (one crypto basket), and 15% / 10% when out of buying power | |

Where stop and risk are both stated, the implied position is 20-30% of the account (NBIS 1% / 0.2%, AAOI <1% / 0.2%,
PATH 1% / 0.3%, SKHY 2% / 0.5%), matching the sizes he states directly. Account-level remarks left in the notes
agree: "200% long", positions capped around 25-35%, and "if I get stopped out on all positions today ... .3% each, so
around 4%" (about 13 positions).

**3. His triggers are intraday.** Of 51 entries with a stated timeframe, 88% are 1- to 60-minute (5m 17, 1m 12,
15m 9, 60m 7). Stated long triggers (56): intraday range or candle breakout 39%, pullback to an EMA 16%, opening-range
breakout 9%, reclaim or failed breakdown 7%, pullback to anchored VWAP 7%. Stated short triggers (33): 79% are a bounce
into resistance. This is what the picks test could not see: it scored his names at the close.

**4. Stop-outs are routine and he re-enters.** 45 cards have an outcome stated later in the same stream; 30 of those
mention a stop. Several cards are a second, third or fourth attempt at the same name that day (CAR four attempts, AAOI
"last try", SPCX third try).

## What this means for the goal
His return is not coming from a 20-session hold on better names (picks test: +6.5% vs our +5.1%). The cards say it
comes from **position size bought with a very tight stop**: a 1-2% stop on a stock with a 6.5% daily range is about
0.2-0.3 of one day's range, which is what lets 0.3% of risk carry a 25% position and the book run at about 200%.

That is the opposite of the house rule here (stops under ~0.5 ADR get widened and sized down, because resting tight
stops intraday were measured to lose). So the testable question is narrow: **at his kind of entry (an intraday candle
breakout after a pullback, stop at the bar low or the day low), how often does a 0.2-0.3 ADR stop survive, and what do
the survivors pay?** ⚠ The ledger's prior is negative: Stage A priced intraday triggers at about a random later
minute, and the daily-bar version of his pullback entry failed. The intraday version has not been run. Our
single-name 1-minute data starts 2026-02 (about 160 names a day), so it would be a seven-month test.

## Problems found in the trade log (for the clarification worklist)
| entry | problem |
|---|---|
| CIFR 2026-08-13 @61:21 | a viewer's question read aloud; not his trade |
| INTC 2026-07-15 @122:10 | probably a viewer's trade ("I got intel on 13 of July"); he answers in the second person |
| AFRM 2026-08-12 @91:29 | agreeing with a viewer; not clearly his own fill |
| AVGO 2026-03-05 @06:10 | logged long, the transcript reads as a short |
| QQQ 2026-04-07 | "Q" looks like an individual stock, not QQQ |
| ARKK 2026-03-12 @37:15 | may be an intention, not an entry |
| LYFT 2026-03-13 | caption says "light"; LITE cannot be excluded |
| TSLA 2026-09-16 | given as a Q&A example; trade date not stated |
| MSTR, COIN 2026-04-06 | the "three crypto positions" are never named in that stream; only BMNR is |
| HOOD (batch 1) | the logged "~1.5% stop" belongs to a different stock he had not entered |

The first three would come out of the picks test; AVGO would flip sign. None of this was applied to the log: the
worklist is being edited by Gabe, so these are listed here instead.

# Ariel Hernandez trade log: built from every public recap (2026-10-01)

**Data:** `data/ariel_hernandez/trades/observed_trades.jsonl`, 3,682 rows from 351 videos (349 public recaps and
stream-style videos from the channel's Videos tab, plus a 2-stream premarket pilot), sessions 2025-04-16 -> 2026-09-30.
Homework page: `data/ariel_hernandez/ambiguous_tickers.md`. Brief: `data/ariel_hernandez/trades/EXTRACTION_BRIEF.md`.

**How it was made.** Transcripts via `ingest_ariel_channel.py` (all 349 public recaps and 325 of 328 premarket
streams are on disk). Each recap was read in full by an extraction agent working from the transcript only, logging
HIS OWN actions with a verbatim quote per row. `check_extract_quotes.py` finds every one of the 3,682 quotes in its
transcript (0 failures) and I read a random sample by hand. Waves 1-2 (109 recaps, Apr-Sep 2026) ran on Fable, waves
3-7 (240 recaps, Apr 2025 - Mar 2026 plus leftovers) on Opus; the Opus waves show no drop in quality (8.2 live rows
per recap vs 6.7, inferred 5.5% vs 7.9%, unresolved tickers about 4% in both).

## What is in it
| | |
|---|---|
| rows | 3,682 (2,393 live, 1,289 retrospective retellings; 232 marked inferred) |
| live opening rows | 633, of which 561 dated -> **420 distinct dated opens** (285 long, 134 short) |
| closed the same day | **173 of the 420** (41%): "tried it, didn't close well enough to keep" |
| stated on opening rows | a trigger on 61%, a size on 34%, a stop on 23% |
| unresolved tickers | 174 rows; 58 of them are one position captioned "ARC" |

- **Retrospective rows are flagged, not dropped.** Monthly, quarterly and yearly review videos (Oct 2025, Nov 2025,
  2025 year, Jan / Feb / Mar 2026, Q2 2026) and chart walk-throughs retell trades already reported; several are
  hand-picked. Score only `is_retrospective == false`, and de-duplicate on (ticker, direction, fill_date): the same
  trade is often told in two or three videos.
- **Most-traded names (distinct opens):** RKLB 17, RGTI 13, NBIS 12, AXTI 12, DELL 11, TSLA 11, NVDA 10, SNDK 10.
- **Vehicles:** SQQQ (33 rows), TQQQ (21), NUGT (12), SOXL (10), TNA (9). Leveraged products are logged on the
  underlying with the product in `vehicle`; an inverse product held long is logged as short the underlying.
- **His book swings between sides.** Share of new opens that were long, by month: 85% in Dec 2025, 43% in Nov 2025
  and Mar 2026, 52% in Feb 2026, 89% in Sep 2026. Activity swings too: 48 opens in Apr 2026, 6 in Jul 2026.

## What he says he makes (his own statements, unaudited; captions can garble numbers)
| period | stated | his stats |
|---|---|---|
| 2025 YTD at 21 May | "up close to 20%" on about $4M | |
| 26 Jun 2025, one trade | about $500K | 60,000 shares of OST short at $9.11, covered $0.70-0.83; "made the month" |
| October 2025 | +$596,435 | 10 winners, 28 losers (26%); an 11-trade losing streak cost about 1.5% of the account; one NUGT short made it back |
| November 2025 | +$531,501 | "10 winners, 18 losses" |
| December 2025 | (not in the title) | 6 wins, 23 losses, 29 trades, 20% win rate |
| 2025, full year | $7.2 million (title) | losses kept to "0.1, 0.2, 0.3%" of the portfolio |
| January 2026 | $1,322,669 | 48 trades; biggest loss in 12 months (SILJ) about 1% of the portfolio; biggest win SLV |
| February 2026 | $131,534 | "almost 50 trades" |
| March 2026 | $1,031,358 | the outlier was an AXTI short |
| Q2 2026 | (no figure found) | expects to lose 65-70% of trades; "65% according to my stats" |

Taken at face value, 20% by late May and $7.2M for the year on a ~$4M account is roughly 180% for 2025, most of it
after May. None of this is verified.

## How he says he does it (from the review videos)
- Starter positions of 3-5% of the account; adds only when right, building toward 8, 10, 15, 20%. Larger (10%+)
  starters coming off a market correction, smaller when he is trading poorly.
- Losers go the same day on average, usually on a weak close; loss per trade 0.1-0.3% of the account.
- Win rate 20-40% by his own numbers; the month is made by one or two outliers (OST, NUGT, AXTI, SLV).

**Against Luk's cards:** both keep the loss per trade to about 0.1-0.3% of the account and both win a minority of
trades. They get size differently. Luk buys a 20-30% position against a 1-2% intraday stop. Ariel starts at 3-5%,
cuts on the close, and pyramids the ones that work. Both lean on shorts and on standing aside for stretches.

## Open items
- **Decodes to confirm** (not applied): "ARC" (58 rows) is ARKK in several transcripts ("Cathie's holdings", "I own
  Ark"); "GRR" (9) probably GRRR; "NQ" / "OQ" (8) probably IONQ; "QBT" (7) QBTS or QUBT; "DocuSign" / "Dock" (5+)
  DOCN or DOCU; "Enphase" (5) may be NBIS misheard.
- **Not included:** the 30 members-only watchlist videos (7 captured earlier, not extracted) and the 325 premarket
  streams. A 2-stream pilot found 13 own-trade rows of which 2 were fresh, both already covered by the prior day's
  recap, so the streams look redundant except on dates with no recap.
- **Not built yet:** journal pages, entry cards, and any scoring against prices.

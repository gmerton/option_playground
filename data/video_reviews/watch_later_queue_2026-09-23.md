# Watch Later triage — 2026-09-23

Source: YouTube Watch Later (1,405 videos, 1,366 visible). Trading content = positions #1–~430 plus ~12
value-investing clips further down; everything else (dating, StarCraft, fitness, real estate, poker) ignored.
**31 WL videos already live in a KB** (matched by video ID across `data/*/`): #4 14 15 31 54 61 67 74 79 83 89
102 113 130 135 137 147 151 192 204 214 240 256 286 289 305 313 317 333 343 413.

Ranking rule: a video ranks high if it (a) supplies the spec for something already queued in TEST_INDEX §10,
(b) comes with an audited/verified record, or (c) bears on the live book (entry quality, stops, the
straddle/bull-put pair, the certified index put sale, GEX). Channels whose claims have repeatedly failed
here rank low regardless of title.

## Tier 1 — analyze next

| # | channel | title | id | why |
|---|---|---|---|---|
| 78 | Qullamaggie | My setups, methodology, and how to build trading mastery | KciAjkEFA6s | No Qullamaggie KB yet, though the house breakout/EP/ADR stack is his. Primary source for the **queued partial-then-trail exit** (§10) and his ORH entry / LOD stop, i.e. the "we select well, enter badly" question |
| 114 | Qullamaggie | THE best daytrading setup. | io4TknSgkUk | same KB, his own words on the intraday entry |
| 72 | Qullamaggie | Studying historical stock moves over the weekend | zxqFTq59gZU | same KB, selection process (our strong side) |
| 213 | Chat With Traders | Breakouts, Home Runs & Exponential Returns · Kullamägi | K0F73Sq90j0 | long-form interview, same KB |
| 203 | TraderLion | The Perfect VCP Trading Setup with Mark Minervini | M_tD6X0CSOI | **VCP is queued and has never been tested** (§10); `traderlion/setups/minervini_vcp_low_risk_entry.md` exists, but check it pins down a codable contraction definition |
| 33 | KINFO | $10,000,000 Verified Day Trader: core patterns, process & live trades | 8IRs-5yN7vE | broker-verified record (better provenance than usual); KINFO precedent in `video_reviews/kinfo_malik_tqqq` |
| 355 | neurotrader | Permutation tests and trading strategy development with Python | NLBXgSmRBgU | METHOD: permutation/Monte-Carlo nulls fit next to the queued parameter-neighbourhood robustness upgrade |
| 141 | Option Alpha | GEX Day Trading Results ($1K Per Day Goal) | O2vTwL4R6kI | GEX regime is one of the few PASSes (SPY t 7.7); a published results log using it |

## Tier 2 — testable patterns, champion records

| # | channel | title | id | note |
|---|---|---|---|---|
| 146, 155 | TraderLion | Leif Soreide high tight flags (90%+ winners / +222% in 27 days) | mpe2_FCfpRg, rdmjsbDVuoU | HTF has never been tested; a daily pattern, so ~20 lines in `pattern_test` |
| 207 | TraderLion | The Wedge Pop setup (Oliver Kell) | fYxSQvuwOQc | never tested; USIC champion |
| 209, 212, 196 | Norm Zadeh / TraderLion | USIC champions Christian Flanders, J Law | ecmHzX-6x8g, D21SgKhgv2E, 6aOnCK1gv2w | audited contest records |
| 234 | Nichol Hermel | Black swan hedges: deep OTM puts | HC6GKtqNZHc | a tail overlay for the certified index put sale, priced from v3 |
| 77 | tastylive | 539 zero-DTE iron condors, PDT rule cost $166/trade | UIxluRMfh80 | their own study with numbers, reproducible on v3 |
| 29, 30 | Trading Steady / Raghee Horner | ORB breakout + pullback backtest; why ORB fails | ZF8uKPqAu8M, T06ayy3-zs8 | ORB has been tested here 12 times; use only as a **false-negative check** against today's ORB-retest result |
| 19 | Chat With Traders | Peter Brandt on risk management | bIi6YzPt9bE | stops/sizing; compare with the size-lever finding |
| 32 | Jack Corsellis | the one change that improves Qullamaggie breakout win rate | zZls8f2At9k | fold into the Qullamaggie KB |
| 163 | Deepvue | Early breakouts with the RMV indicator | dDAoAjyYI2I | a volatility-compression gate; compare with `vol_compression.py` |

## Tier 3 — method / theory (read, don't test)
- #295 Euan Sinclair, volatility (LAiGKUIlwSo); #263 Sinclair, retail vs institutional (EjD6KPo3OZs); #300 Meldrum, IV skew/term structure. The VRP is already measured directly, so these add framing, not tests.
- #257 Paolucci, why your backtests are wrong (w-EbZ6Xct_E); #231 luck vs skill; #26 IRONCLAD coded Tori Trades (2T-1REPS-Qk); #21 Unbiased Trading $1,000-book test (DpPLqjdRizs): audit their method only.
- #92 / #157 / #199 Brian Shannon AVWAP: **AVWAP already tested NULL** as a trigger and as a trailing exit. Only worth it if he specifies a different anchor rule.

## Deprioritized, with reasons
- **Unprocessed TheOneLanceB uploads** (#113 scalping, #116, #123, #139, #153, #154, #150): the Lance KB is a channel ingest (39/145). Leave them in that queue; Stage A says intraday triggers have no edge.
- **Options With Davis (~40), Theta Profits remainder (~25), tastylive income (~30), SMB options-income (~25), OptionsPlay, Cashflow Academy, Options With Ravish/Ryan**: all of these channels have KBs at ≤2.5/5, and their core premise (short-premium income, calendars) is already contradicted after costs.
- **Tom Sosnoff lifestyle clips** (#18 23 60 90): covered by the More Tom KB.
- **Value investing** (Buffett / Munger / Pabrai / Lynch, ~20): not in this desk's scope.
- **Psychology / motivation** (#7 37 45 25 162 148 …): not testable.

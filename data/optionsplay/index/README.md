# OptionsPlay channel index: prioritised for review (2026-09-24)

Built the same way as `data/tastylive/index/`. Source: `@OptionsPlay`, flat-listed with yt-dlp (metadata only,
no transcripts). Presenter is mostly Tony Zhang; guests include Tom Sosnoff (10+ sessions), Brian Overby, Rick
Bensignor and Prakash Vijayanath.

- `playlists_raw.tsv`: the 26 playlists.
- `playlist_videos_raw.csv`: 341 playlist entries.
- `channel_tabs_raw.tsv`: the channel's **videos (279) / streams (30) / shorts (331)** tabs, newest first.
- **`video_index.csv`: 827 unique videos** (640 from the tabs plus 187 that exist only in playlists), scored and
  sorted: `video_id, title, duration, tab, channel_rank, playlists, reviewed, score`. `channel_rank` 1 is the
  newest in its tab.
- `build_index.py` rebuilds `video_index.csv` from the three raw files.

**Coverage.** Unlike tastylive, the tabs were listed in full, so the ~100-entry playlist cap doesn't apply. Uploads
run from 2017 (webinar recordings) to 2026-09-19. ⚠ The flat listing has **no upload dates**. Dates below were
fetched per video for the shortlisted videos only. For the rest, use `channel_rank` as a proxy.

**What the catalogue is.** Roughly:
- 331 shorts (clips, skip);
- ~150 dated market outlooks, 2020–2022 and 2026 (skip);
- platform walkthroughs, beginner courses and AI/ChatGPT sessions (skip);
- a core of ~40 strategy webinars.

`jmD1S47yjjA`, `nTqAK_mXX6E`, `ITjKK9fbayw` and `4zwgKjj8-fk` are 2.5–3.3 h compilations of Growth Lab series whose
parts are also listed individually. Review the parts, not the compilation.

**Scoring (heuristic, for triage only; the tiers below are hand-curated and override it):**
- +4 for Sosnoff, credit spreads, premium, condors, strangles and straddles.
- +3 for put selling, the wheel, covered calls, earnings, 0DTE, backtests, volatility, liquidity, breakouts and
  trade management.
- −3 for outlooks and macro, AI, platform, and beginner/explainer titles.
- −2 for weekly idea lists.
- −4 for anything under 2 min.

**Already reviewed (4):** `pQlGgcyrUoQ` (Sosnoff, 3/5), `YfrZT_kTo_4` (three filters, **3.5/5**, credit/width
PASS), `iXOULnIGEKk` (selling winners early, 2.5/5), `lV8Jkl37h4M` (what volatility is telling you, 2.5/5). See
`../README.md`.

## Priority tiers

### Tier 1: selecting what to sell premium on, checkable against our real-fill results
This is the direct continuation of the question "how do they pick names to sell vol on?". OptionsPlay's answer
(direction first, then liquidity, then rank by premium-to-width) is the one creator selection rule that has passed
on our quotes.

| video | date | title | our nearest result |
|---|---|---|---|
| bk9Co7V6AI4 | 2020-10-08 | Finding the Optimal Credit Spreads | the credit/width ranker's origin; PASS +8.57pp t 3.74, within-date t 4.15 |
| gUOWa-i4R70 | 2022-02-10 | How to Trade Credit Spreads for An EDGE | same; check whether the "edge" is credit/width or POP (POP is not an edge, doctrine rule 14) |
| wG0yvxmDuXI | 2026-09-19 | Why the Options Market Is Always Wrong About Volatility | VRP panel: 10d +1.75vp t 8.93; 30d only t 2.08 |
| jLUPi1Im9cw | 2026-04-11 | Stop Buying Options. Get Paid to Wait Instead. | paid-to-wait: ungated −3.3% net, IV≥60th +5.7% (t 2.29, not certified) |
| VSLc-kHxFlw | 2026-08-01 | How to Screen Both Legs of the Wheel Before You Trade | ⭐ per-name selection for put sales; BCI CSP = stock minus costs |
| n1T3PUyS4uQ | 2025-02-17 | How to Choose the BEST Stocks for Covered Calls Trading | ⭐ per-name selection; IV rank NULL per name (zivr t −1.25) |
| Uvk_no85Yj4 | 2026-02-15 | How to Trade Credit Spreads After Earnings | earnings vol premium −0.43% at the bid; post-catalyst entry NULL |
| 2VzqGw2_ZFs | 2018-09-16 | Credit Spread Income Strategy w/ NDX Weekly Index Options | the certified cell is an index put sale, but only bearish-high-IV |
| 5IvhBIQVujs | 2022-10-07 | Generating Income with Index Options using Iron Condors (8 min) | SPX condor bearish-high-IV t 5.21; ETF condor call side t 0.6 |
| m2-bo0kxMu0 | 2025-05-04 | How to Manage Losing Credit Spread | roll test: stop is a cost (−9.51pp), re-entry NULL |
| p477UMpfVxI | 2021-03-19 | Lose MORE than your Max Loss on a Credit Spread (7 min) | assignment/pin mechanics; likely no test |

### Tier 2: Sosnoff on OptionsPlay (extends `data/tastylive/sosnoff_doctrine.md`)
| video | date | title |
|---|---|---|
| e2y8LUTMOsI | 2025-03-30 | How to Master Options for Volatile Markets with Tom Sosnoff (CHEAT SHEET) |
| QBcDJ_h4NjU | 2024-12-15 | Some of The BEST 0DTE Strategies for Profit with Tom Sosnoff |
| ongdu7qgLnc | 2024-07-14 | TOP Options Trading Strategies with Tom Sosnoff |
| OT-lCh3PdTw | 2021-12-14 | How to Master Futures: Small Futures with Tom Sosnoff |
| KHVQjrq8lgw | 2021-09-23 | The BEST Advanced Options Strategies with Tom Sosnoff |
| DflH0AUVETQ | 2021-03-17 | Tom Sosnoff: Introduction to Small Futures |
| x9-W5gZj5gI | 2021-01-12 | Tom Sosnoff: Options Trading Strategies You MUST Know |
| VFZxl7rfDIw | 2020-11-13 | Market Analysis With Tom Sosnoff |
| k_kbWpHpwi0 | 2020-08-25 | The Optimal Options Strategy Guide with Tony Zhang & Tom Sosnoff |
| jt7mjlU1whk | 2020-06-18 | Market Outlook & Options Questions with Tom Sosnoff |

The futures pair (OT-lCh3PdTw, DflH0AUVETQ) is the one arena the doctrine review calls untested. Expect
philosophy, not numbers.

### Tier 3: 0DTE and short-dated (our lens: the 1-day fly pays only on positive dealer gamma, t 3.4)
7t2EROvIVSg (2024-10-20, "The #1 Backtested Strategy for 0 DTE") · yCAYvRwSscI (2025-07-13, butterfly 0DTE
showdown) · zAxXwa_puLw (2025-06-29, 0DTE gamma pricing) · t5fx2AYdty0 (2025-06-01, 0DTE credit spreads) ·
N_HnKpwox1I (2025-05-16, buying vs selling 0DTE). Most can't be priced on our EOD data (see UIxluRMfh80 in the
tastylive KB). Review 7t2EROvIVSg first, since it claims a backtest.

### Tier 4: the equity book (selection and entry, our core question)
2H1z0vauisg (2026-07-11, Early Breakout Detector) · 9VylBGWJVT8 (2026-04-20, spotting leading stocks early) ·
DqtBkL1qalU (2026-06-20, cutting winners too early; sibling of reviewed iXOULnIGEKk) · ZS_hzRzJz9M (2026-02-18,
high-probability trend following) · yLQt8UZNS8Q (2026-07-18, the few earnings setups worth trading) ·
3VVjDDJvu2s / RokhF9v62HE (2025-05-02 / 2025-07-20, "algorithm to trade earnings"). Our priors:
- control beats the breakout signal (the entry is the leak);
- PEAD NULL;
- post-catalyst entry NULL.

### Tier 5: hedging (our lens: tail overlay WL-5f NULL, 5Δ same-expiry −100% every trade)
uT_CZY7SdSE (2026-02-08, protect investments at zero cost, i.e. collars) · d7iqTz7m9es (2021-09-14, 7 min, "Index
Options Strategies Backtested") · NrIvJ0F4i6M (2021-01-28, selling straddles and strangles).

## Suggested review order
1. Tier 1 as one batch of 11 (one KB, one ledger cross-check). It answers the stock-selection question directly.
2. Then the 3 most recent Sosnoff sessions from Tier 2.
3. Then decide on Tiers 3–4.

Captions come down with yt-dlp. ⚠ Check `--list-subs` for `en-orig` first (see the caption trap in `../README.md`).

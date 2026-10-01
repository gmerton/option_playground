# Quantified Strategies channel triage: what is worth testing (2026-09-30)

**Scope.** 321 long videos and 315 shorts listed. 40 transcripts read in full (every video whose title touched an axis
the ledger lacks, plus samples of the main family); the other 281 long videos were triaged by title only, and the shorts
not at all. Nothing here was run. Power figures are arithmetic from the creator's own claimed means and typical daily
volatility, not measurements.

**What the channel is.** About a third of the long videos (114 by title) are one template: an oversold reading on
SPY/QQQ (RSI, Williams %R, IBS, CCI, stochastic, CMO, 5-day low, down Monday, VIX spike) plus the "QS exit" (sell after
a close above the prior day's high), no stop. 39 are calendar effects. The rest are paper summaries, rotation
portfolios, education and biography. Several of the best-sounding rules are members-only and not stated.

## Worth testing, in order

### 1. The dip family, settled with one rule (existing queue row, promote)
- **Not new:** TEST_INDEX section 10, "Daily ETF mean reversion (RSI/Keltner) benchmarked against buy-and-hold",
  PARKED low priority 2026-09-22, never run.
- **Why now:** the Darvas test built the control this family needs. Any-day SPY entry with the QS exit wins 69.5% and
  averages +0.283% (QQQ +0.416%). The channel claims +0.82% (SPY, Williams %R(7) < -95, 288 trades) and +0.95% (QQQ,
  Williams %R(5) < -90, 361 trades), roughly 0.5pp above that baseline. The Darvas ablation points the same way from
  the other side: plain breakout days were worse than other days (-0.180pp, t -3.60, exploratory).
- **Design:** ONE pre-registered rule with no parameter freedom, chosen because the channel says it was published in
  2012: buy the close on a 5-day low, sell on a close above the prior high or after 5 days (video `UkoTdKV65yk`), or
  Turnaround Tuesday (`SjAVW7jgwuQ`, also "2012"). Primary on 2013 -> 2026 only (after their publication), SPY, QQQ as
  the second cell. Controls: any-day entry with the same exit, the random-entry null from `run_darvas_spy.py`, and
  exposure-matched buy-and-hold. Discovery bar (creator claim).
- **Watch for:** their own numbers decay (Williams %R + filters: PF 5.4 / 8.6 / 2.1 by era, average trade 0.49% in
  2017-26); dips cluster in high-volatility periods, so a per-trade edge may be a volatility premium. Rough power: a
  0.5pp gap on ~2% per-trade dispersion and ~290 trades is t ~4 on the full sample, about half that on 2013+.
- **Cost:** local, under an hour (`data/cache/index_daily_ftd.parquet`).

### 2. TLT month-end long, early-month short (new axis)
- **Claim** (`pgZaqAC7_ks`): buy TLT on the fourth-last trading day of the month, sell the last day's close: +0.35% per
  trade, 4%/yr at 11% exposure. Short from month-end to the seventh trading day: +0.45% per trade. Combined 9%/yr vs
  ~4% buy-and-hold, 23 years, 3 bp costs. "Published several years ago and has continued to perform."
- **Why new:** no bond-calendar row in the ledger. Turn-of-month in SPY/QQQ was NULL (2026-09-24), and they say the
  same rule loses on the S&P. There is a flow story (month-end index extension buying by bond funds).
- **Design:** yfinance TLT total return 2002 ->; primary = long window vs all other 4-day windows, HAC t; short leg
  second; split at the original publication date (to be found on their site); per-year. Rough power: 0.35% on ~1.8%
  window dispersion, ~280 months, t ~3.
- **Cost:** local, under an hour. Uncorrelated with the equity book, which is its appeal.

### 3. Third-Friday (monthly expiration) open-to-close short in SPY/QQQ (new axis)
- **Claim** (`gf2L_MNznmk`, `VpiNOEPbgss`): index derivatives settle on the third-Friday opening prices, the open is
  bid up and fades by noon. Short the open, cover the close: +0.23% (QQQ), +0.15% (SPY), 58% winners, 25 years.
  Secondary: OPEX week long (Monday open to Friday open) +0.4%, "last years have been poor".
- **Why new:** no expiration-calendar test in the ledger; it is a dealer-flow effect, the one mechanism family
  certified here (GEX regime). The video paraphrases a paper without naming it (I believe Baltussen, Terstegge and
  Whelan, "The Derivative Payoff Bias"; unverified).
- **Design:** daily open/close 1993 -> for the claim; SPY/QQQ 1-min 2007 -> for the open-to-noon shape. Control = the
  other Fridays of the same month (holds the weekday fixed). Rough power: 0.15-0.23% on ~0.9-1.3% intraday dispersion,
  ~400 third Fridays, t ~3, borderline.
- **Honest size:** 12 trades a year at ~0.2% is 2-3% a year on the notional. Mechanism value more than income.

## New axis, but blocked or weak
| video | claim | why not now |
|---|---|---|
| `fobD-iiaFbI` Stocks-in-play ORB (Zarattini et al.) | 5-min ORB on the top 20 names by opening relative volume, 2016-23, 41.6%/yr, Sharpe 2.81 | Needs the whole universe ranked each morning. Our 1-min cache is ~160 pre-selected names a day from 2026-02, so the ranking cannot be reproduced. Existing ORB nulls (ORB9 INVERTED vs a random minute, index ORB NULL) did not use this filter |
| `tc0kY_mAQr0` End-of-day reversal (Baltussen, Da, Soebhag) | intraday losers bounce in the last 30 minutes, 0.24%/day decile spread, 1993-2019, weaker since 2010, costs take ~40% | Same data limit; strongest in small/mid caps; two crossings of the spread for a 30-minute hold |
| `cpWJpEMrv4g` Intraday periodicity | the same half-hour repeats its return across days | Same data limit; no stated rule |
| `0ECgRZQgnZg` Wei and Yang, short-term momentum and reversal in large stocks | large-cap low-volatility names reverse, high-volatility names continue, 1964-2009 | Testable monthly on chain_spot (survivorship-free). A paper summary with no rule; moderate prior. Only worth it as a refinement of the certified 12-1 sleeve |
| `qL9gnzI5Akc` Closed-end fund premium/discount | RSI(2) of price/NAV on ETG, +0.48% per trade | One fund; needs NAV history; CEF spreads are the size of the edge |

## Not worth testing (already answered, or cannot clear the bar)
- **Rotation and allocation** (SPY + GLD/TLT ratio `PUIicr8b1ck`; SPY/TLT and SPY/GLD 3-month dual momentum, GEM
  `_QN7zq1-elU`; SPY/GLD 12-month average, SPY/EFA/EEM `k_CpZTWaKkA`; TQQQ/BTAL `NdnJX4kjPQM`; TQQQ/TMF `pSUt2Hnezps`):
  ~20 years of monthly data with a chosen lookback cannot reach t 3. Ledger: multi-asset TSMOM RETRACTED against the
  same assets held long (-0.13%/mo, t -1.43); TQQQ lab FAIL. Their own GEM re-test earns 6.1%/yr after publication.
- **Zarattini and Antonacci, "A Century of Profitable Industry Trends"** (`-bg_xbCSgtE`): the paper's own ETF version
  has Sharpe 0.61 vs 0.59 for the market. Ledger: house breakout on 31 sector ETFs NULL, TSMOM row above.
- **Overnight SPY** (`obY8l6-sTnY`, `_XVib3RF9sU`): +3.6 bp a weekday night gross; a nightly round trip costs most of
  it. Ledger: single-name overnight persistence PARKED on costs and an open-print bias. Their "3 down closes" and
  RSI(2) overnight rules are the dip family.
- **VIX rules** (`SoqRHI5ldXs`): VIX above its 20-day average, +0.05% vs +0.03% next day; the Bollinger and 20-day-high
  rules use the QS exit, so they are the dip family; the best one is members-only.
- **TLT trend as an SPY switch** (`ro4ck8Z1rYw`, `Dw1pit-dC8Y`): 8.85% vs 0.86%/yr by TLT above/below its 15-day
  average, 2003 ->, picked from 20 averages. About t 1.8 on their own numbers. Ledger: rates-regime tests NULL.
- **Calendar trivia** (turn of month, holidays, Santa, months, weekdays, moon): turn-of-month NULL after publication
  (2026-09-24); the rest have a few hundred observations at most and no mechanism.
- **Short interest, insiders, small caps, 52-week high, January:** each has a ledger row.
- **Stops** (`1YJSX6LtX2o`): "a stop makes a mean-reversion strategy worse" agrees with the ledger on stop execution;
  nothing new to test.

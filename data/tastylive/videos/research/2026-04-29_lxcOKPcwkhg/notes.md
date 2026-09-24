# tastylive / Options Math Check: "The Market Crashed 3 Times in 5 Years. Each Time the VIX Futures Curve Warned You First." (2026-04-29, 12:17)

_Reviewed 2026-09-23 for the Sosnoff "sell vol when it's high" wave. One host, solo, on the tastytrade platform: a
CAPE-ratio intro, a live look at the VX futures watchlist, then SPX/NDX probability-of-ITM reads for May-Dec.
Transcript (`en-orig` auto-captions) in this folder. There is **no study**: no sample, no table, no statistic._

## Verdict: 1.5 / 5

**The title claims a lead ("warned you first"). The transcript claims only coincidence.** What the host actually
says (02:07-02:11) is that in COVID, the 2025 tariff selloff and the 2026 war selloff "where the market was selling
off, the vol futures were in backwardation". That is backwardation *during* a selloff, which is close to a
definition: VIX spikes when the index falls, and the front of the curve moves the most. His operative rule
(04:27-05:22) is the necessary-condition form: "I just don't see a situation where we get down 30, 40% in the S&P
500 without the vol curve being backwardated", so stay long-drift "until this vol futures curve goes into
backwardation".

Three events, recalled from memory ("like a five or six-point backwardation, if I remember correctly"), no false
positive rate, no lead time. It scores above 1 only because the necessary-condition claim is true in our data and
the term-structure axis itself is one the ledger has not tested (see "Not tested, could be").

## Data audit

| item | what the video gives |
|---|---|
| sample | 3 selloffs: COVID 2020, tariffs 2025, "the war" 2026 (02:01-02:06) |
| period | "the last couple of years" (04:36); title says 5 years |
| n | 3 events; **no count of backwardation episodes that were NOT followed by a crash** |
| rule | contango = complacency, drift up; flat/backwardated = the door is open to a 20-40% selloff |
| fills / costs | n/a (no trade is simulated) |
| control | none: no false-positive rate, no comparison with the VIX level alone |
| tail shown? | n/a |
| significance | none |
| selection | the three events were chosen because they were selloffs, so the "signal" is scored only where it fired |

## Their numbers (transcribed)

| @ | number |
|---|---|
| 00:21 | CAPE long-term average ~17; today **40.66**, "8% below the all-time high" |
| 00:56 | Mag 7 ~**33%** of the S&P 500 |
| 02:18-02:39 | backwardation size: COVID "like a **15-point**" (largest he's seen); 2025 tariffs "like a **five or six-point**"; 2026 war "pretty muted" |
| 03:32-03:35 | VX curve on the day: K (May) **20.28**, M (Jun) **21.16**, high **20.95** in V; "full contango", "kind of flat" |
| 07:04-07:14 | SPX IV **18%**; NDX **26% / 22%**, the 26% over the 30th-1st (Mag 7 earnings week) |
| 08:12-08:57 | NDX 27,288: −3,000 pts (24,200) **5%** ITM / **10%** touch over 18 days; the put **35** pts vs the call **6** |
| 09:15-09:40 | Dec: 24,200 and 30,000 each **~30%** ITM; call **988** vs put **844** ("upside skew in NDX") |
| 09:50-10:32 | SPX Dec 7,700 call **33%**, **196**; 6,600 put **~30%**, **205** |

## Verification run for this review (descriptive, not a test)

yfinance `^GSPC`, `^VIX`, `^VIX3M`, 2006-07-17 → 2026-09-23 (5,078 sessions). Backwardation proxy = VIX / VIX3M ≥ 1
(the spot term structure; VX futures per-contract settles only exist from 2013, see below). Drawdown episodes =
S&P 500 close ≥10% below its running peak, measured peak → trough before a new high (so 2010 and 2011 sit inside the
2007-13 episode).

| episode (peak → trough) | max DD | first VIX/VIX3M ≥ 1 | S&P already down by then | backwardated days peak→trough |
|---|---|---|---|---|
| 2007-10-09 → 2009-03-09 | −56.8% | 2007-10-22 | −3.8% | 153 / 356 |
| 2015-05-21 → 2016-02-11 | −14.2% | 2015-06-29 | −3.4% | 25 / 184 |
| 2018-01-26 → 2018-02-08 | −10.2% | 2018-02-02 | −3.9% | 5 / 10 |
| 2018-09-20 → 2018-12-24 | −19.8% | 2018-10-10 | −4.9% | 27 / 66 |
| 2020-02-19 → 2020-03-23 | −33.9% | 2020-02-24 | −4.7% | 21 / 24 |
| 2022-01-03 → 2022-10-12 | −25.4% | 2022-01-26 | −9.3% | 14 / 196 |
| 2025-02-19 → 2025-04-08 | −18.9% | 2025-03-03 | −4.8% | 15 / 35 |

- **The necessary condition holds: 7 of 7 ≥10% drawdowns since 2006 had backwardated days.** So does his weaker
  "no 30-40% selloff without it".
- **It never warned first.** In every episode the curve inverted only after the index was already down 3.4-9.3%.
  It's an early alarm, not a forecast. The 2026 war selloff is below the 10% line: max DD −9.1%, VIX/VIX3M peaked at
  just +1.93 pts (2026-03-06), 11 backwardated days. That matches his "muted".
- Magnitudes: VIX − VIX3M peaked at **+18.2** (2020-03-12) and **+10.8** (2025-04-08). The spot curve is steeper
  than the futures curve he recalls (15 / 5-6); consistent in rank.
- **False positives are the missing half.** 10.9% of sessions are backwardated. There are 152 separate backwardation
  starts (many are 1-day flickers). After a start, a further ≥10% fall within 63 sessions happened **25%** of the
  time, vs **15.2%** from any date. That isn't VIX-matched, so it may be nothing beyond the VIX level (the skew
  precedent).

## Claim-by-claim

| @ | claim | our evidence |
|---|---|---|
| title | the VX curve "warned you first" before three crashes | ❌ **Not as a lead.** Verification above: first inversion came after a 3.4-9.3% decline, 7 of 7 episodes. Coincident alarm |
| 02:07 | all three selloffs had vol futures in backwardation | ✅ True, and true of all 7 ≥10% drawdowns since 2006 (VIX/VIX3M proxy). Near-definitional |
| 04:27 / 05:18 | no 20-40% S&P decline without backwardation, so stay long until it inverts | **NEW: untested as a rule.** Necessary-not-sufficient holds in-sample, but the question that matters is **information beyond the VIX level**, and the ledger's closest analogue failed exactly there: SPY 25Δ skew Q5−Q1 +1.72%/21d, t 1.44, "skew adds nothing beyond the VIX level" (vol t −1.22 vs vix_pct t +6.54), TEST_INDEX §9 skew row |
| 04:08 | the more complacent the market, the more contango; big daily moves flatten or invert it | ✅ Descriptive. Ledger adjacent: negative dealer gamma = +8.1% realised vol beyond VIX (t 7.7, §7 GEX row). Term structure itself has no row |
| 06:00 | markets make more V-bottoms now than slow bear markets | Untested as stated; our FTD/regime-timing work (NULL ×5) says the V can't be timed from the index |
| 06:46 | to avoid single-name earnings, trade SPX/NDX, whose IV bump is small | ✅ Consistent with the companion earnings-season video (index IV barely moves) and with our liquidity gate. Not a trade |
| 08:12-10:32 | probability-of-ITM reads and call-vs-put premium comparisons (NDX upside "skew") | Model-implied probabilities from today's IV, not forecasts. The Dec call > put in NDX is mostly **carry** (forward above spot); he says so at 09:43. No evidence either way |
| 00:40 | high CAPE → weak 10-20 year returns, not a timing tool | Out of scope (no ledger row; decade horizon) |

## "Sell high vol": index-after-stress, per-name, or neither?

**Neither directly. It's a risk-off signal for *long* equity, not a vol-selling rule.** But it bears on the index
cell: backwardation is what the curve looks like **inside** our certified bearish-high-IV put-sale bucket. **20 of
its 75 recorded entries** (13 distinct months) were backwardated at entry (VIX/VIX3M ≥ 1). That refines rather
than overturns our reading. The certified trade *already* sells into backwardated stress, and it certifies anyway
(SPY t 6.07). Whether it should wait for the curve to re-normalise is the open question below, and it's
underpowered.

## What I would take

1. **VIX/VIX3M ≥ 1 as a descriptive "stress is live" flag on the desk** (not a trade trigger): it co-occurs with
   every ≥10% drawdown, it's free (`^VIX3M` on yfinance since 2006), and it tells you that you are inside the
   regime where our certified bucket lives and the long-equity book's stops fire.
2. **Don't read it as a lead.** On our data it inverts after the first 3-9% of the fall.

## Not tested, could be

**What makes it new:** the ledger's term-structure rows are all about *option-implied forward vol on the
underlying*: VRP panel fwd 30→90 absent (t 1.45), FVR doesn't sort; FVR ≥1.20 gates the long single-name straddle;
the earnings `ts_slope` gate passes 90%. None uses the **VIX futures / VIX3M curve as an index regime signal**.

1. **Term-structure inversion vs the VIX level (the skew-test design, one new regressor).**
   - Pre-register: forward 21d S&P return, forward 21d max drawdown and forward 21d realised vol, regressed on
     `bw = VIX/VIX3M ≥ 1` (and the continuous ratio) **plus vix_pct**, NW-corrected at the overlap lag.
   - Bar: |t| ≥ 3 on the `bw` coefficient, both halves the same sign.
   - Exploratory: VX1 − VX2 from CBOE settles (2013+) as the direct version of his curve.
   - Effort **~2-3 h, local.** `run_skew_signal.py` is the template.
   - Data: `^VIX`, `^VIX3M` (2006-07+, 5,078 days), `^VIX9D` (2011+), `^VIX6M` (2008+), `^VVIX` (2007+) all load from
     yfinance. **VX futures:** yfinance has no `VX=F`. The CBOE CDN serves per-contract daily settles at
     `cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_<expiry>.csv`: HTTP 200 for 2013+
     expiries, **403 for 2008-2012**. Early 2013 files carry Settle = 0 on some rows, so use Close.
   - No option fills needed: this is a signal test. It only earns a real-fill stage-two test if it clears.
   - Prior: **low**. The skew test is the precedent, and backwardation is largely a function of the VIX level.
2. **Inside the certified bucket: enter while backwardated vs wait for re-normalisation.** This is doctrine
   candidate #3, already listed.
   - ⚠ **I peeked while checking power** (`data/studies/logs/spy_tail_overlay_trades.csv` × VIX/VIX3M):
     backwardated entries n 20 mean roc_net **+0.5%** vs contango n 55 **+9.0%**, but **medians are equal (+11.4% vs
     +10.6%)**. The whole gap is the two max-loss trades (2018-12-07, 2020-03-06).
   - That's 2 trades: **UNDERPOWERED**, and the 75 SPY trades are now **contaminated** for a pre-registered test.
   - Any test must run on a held-out sample: the SPX condor 2010-2017 leg, or QQQ/IWM bearish-high-IV entries.

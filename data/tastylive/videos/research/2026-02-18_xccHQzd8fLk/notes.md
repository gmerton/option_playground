# tastylive / Options Jive: "Why 21 DTE May Change How You Manage Options" (2026-02-18, 8:19)

_Reviewed 2026-09-24 for the Sosnoff-doctrine batch (Tier 1), after the FIX-1 re-run of our 21-DTE study. Two hosts
discussing research slides. This is "part two" of a morning strangle study that isn't in this folder. Transcript
(`en-orig` auto-captions) in this folder. The slides aren't in the transcript and **not one numeric result is
spoken**. Every number below is a study parameter, not a finding._

## Verdict: 1.5 / 5

The design is the right one to ask about: **the same short-premium trade under three exits** (hold to expiry, take
50% of max profit, close at 21 DTE), compared on mean daily return and on daily P&L volatility, at two sizes. It's
also honest about the trade-off. It never claims 21 DTE earns more. The final takeaway splits the jobs: "21 DTE
... control volatility, and managing winners provide stronger returns in bull markets" (07:33–07:48). That's
closer to our ledger than the sibling videos get.

What caps it:

- **No numbers.** Every result is "a couple of ticks" (02:14), "way higher" (05:09), "2% plus move in your average
  daily" (07:16). There's no period, no n, no fills, no t, and no absolute P&L for any arm.
- **"Basically similar daily return" (03:13) is the claim that matters, and on our data it's false.** The 21-DTE
  close earns less than holding, per trade and per day at risk (below). The volatility cut is real. It is paid for,
  and the video says it's free.
- **The capital-allocation result looks impossible as stated.** Going from 25% to 35% of capital scales every arm's
  P&L by 1.4× if the trade set is unchanged. So the volatility of every arm, 21 DTE included, should rise by the
  same 40%. "21 DTE stayed the same" (01:55) can only come from a changed trade set (more overlapping positions?)
  or a changed denominator, and the video doesn't say which.
- **Their own caveat is the selection problem.** "Thanks to the decade-long bull market ... managing winners ...
  outperformed" (02:56). Naked SPY puts in a bull sample, with no stock or delta-matched control, can't separate
  the exit rule from beta.

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY (puts). The morning companion study used 1-SD strangles, underlying not stated here |
| period | **not stated** ("decade-long bull market", 02:56, suggests roughly the 2010s) |
| n | **not stated** |
| entry rule | sell a **20Δ SPY put at 45 DTE** (01:17). Entry frequency and IV filter not stated |
| management | three arms: **hold to expiry / take 50% of max profit / exit at 21 DTE** (01:23–01:30). Two sizes: **25% and 35%** of capital committed (04:41) |
| fills | none stated. Channel disclaimer: "Performance is not presented net of all commissions, fees, and expenses." Likely mid |
| control | the three exits against each other (the right comparison for an exit rule). **No control for the trade itself**: no buy-and-hold, no delta-matched stock |
| win rate / avg / tail | none. Metrics are "average daily return" and "standard deviation" of daily P&L, spoken only qualitatively |
| significance | none |
| selection | SPY in a bull sample, named as such (02:56, 03:55). Naked puts in that window are a long-beta trade |

## Numbers as spoken

| @ | number |
|---|---|
| 00:33–00:37 | companion strangle study: capital allocation **25% → 35%** |
| 01:17–01:30 | **20Δ SPY puts, 45 DTE**, three arms: hold / 50% of max profit / exit at 21 DTE |
| 01:35–01:55 | at 21 DTE, strangle and put volatility are "similar"; the other arms "saw an increase" going from strangles to puts |
| 02:14 | "a couple of ticks" more volatility on the put (unquantified) |
| 03:13–03:18 | 21 DTE vs the others: "basically similar daily return, but the ... standard deviation ... is a whole lot less" |
| 04:41–04:43 | committed capital **25% → 35%** on the puts |
| 05:07–05:09 | vol increase at 35% for hold / 50%: "a little bit higher ... way higher actually" |
| 07:13–07:16 | 50% arm at 35%: "**2% plus** move in your average daily" (the only magnitude spoken, and unclear whether it's the return or its sd) |
| 05:25 / 05:53 | "volatility up around 50 cents ... 2140", "hanging in there 46": live market chatter, not study numbers |

## Claim by claim

Ledger row: **21-DTE management on a 45 DTE / 20Δ short strangle**, TEST_INDEX §1, re-run 2026-09-24 after FIX-1.
Primary artefacts read: `data/studies/exit_21dte_2026-09-23_fixed.csv` (14,367 strangles, 44 names, 2018–2026,
sell bid / buy ask) and `data/studies/logs/exit_21dte_fixed.log`. Units are per share. It's a **strangle** panel and
the video is a **put**, so it's the nearest cell, not a replication.

| @ | claim | our evidence |
|---|---|---|
| 03:04 / 07:33 | Exiting at 21 DTE is the most effective way to control P&L volatility | ✅ **Agrees.** Log: sd **$9.33 vs $17.09**, worst **−$291 vs −$617**, worst 1% **−$23 vs −$46**. Exploratory check below: it survives credit-normalisation and a monthly book, though it barely moves the worst month in dollars. |
| 03:13 | ...at "basically similar daily return" | ⛔ **Contradicted.** 21-DTE close − hold **−$0.52/share, month-clustered t −2.42**, halves −0.63 / −0.40 (NULL on return, leaning INVERTED). Hold **+$0.23 (74% win)**, 21-DTE **−$0.29 (64% win)**. Per calendar day at risk (exploratory): **+$0.0055 vs −$0.0076**, so the shorter holding period doesn't rescue it. SPY-only subset (exploratory, n 400 overlapping weekly entries): hold +$1.09, 21-DTE +$0.31, diff −$0.78, t −1.81. Same sign, smaller. Mechanism (log and doctrine row 21): the early close pays a second round trip, and at mid that cost is invisible. |
| 02:56 / 07:46 | Taking 50% of max profit gives the best returns in a bull market | **UNTESTED by us.** Sosnoff doctrine row 22: "the 50%-take arm of the queued 21-DTE design was never run". Adjacent: the ungated SPY 45-DTE 50%-take put spread is only **t 1.2** monthly (Freedom Income row, TEST_INDEX). Their own qualifier ("in bull markets") is the confound. A short put in a rising sample is long beta, and there's no stock control. |
| 01:55 / 05:51 | Raising committed capital 25% → 35% raises vol for hold and 50% but not for 21 DTE | ⚠ **Not coherent as stated.** With a fixed trade set, P&L is linear in size, so every arm's vol scales by 1.4×. Our data can't test it. What we can say: the 21-DTE arm's *lower* sd means the same % sizing produces a smaller absolute swing. That's a level difference, not a different slope. |
| 04:20–04:29 | Being mechanical at 21 DTE stops emotional exits | Behavioural, untestable. It sits badly with our exit ledger, though: a mechanical early exit is still an early exit, and every loser-removing exit we've tested INVERTED (TEST_INDEX §10, 21-DTE queue row). The 21-DTE rule is the one exception that isn't negative on risk, and it's still negative on return. |
| 02:00 | Naked puts should show lower vol than strangles, "but not as much as you would think" | Descriptive, not checked (we have no put-only 21-DTE arm). Unsurprising: in a skewed index the put leg carries most of a strangle's tail. |

### Exploratory check (local, fixed CSV only; no ledger row)

`.venv/bin/python3` on `exit_21dte_2026-09-23_fixed.csv`. Descriptive, not pre-registered. Question: does the risk
cut survive once we stop measuring in raw per-share dollars, which let high-priced names dominate?

| cut | hold (A) | 21-DTE (B) |
|---|---|---|
| per-trade mean / sd ($/share) | +0.231 / 17.09 | −0.294 / 9.33 |
| mean per calendar day held ($/share) | +0.0055 (median 42 days) | −0.0076 (median 21 days) |
| P&L ÷ credit, credit ≥ $0.50 (n 12,779): mean / sd / p1 | +0.016 / 2.68 / −8.6 | −0.153 / 1.59 / −6.1 |
| monthly book, P&L ÷ credit, credit ≥ $0.50: mean / sd / worst month | −0.010 / 1.13 / −9.4 | −0.169 / 0.75 / −6.9 |
| monthly book, $ sum across names: sd / worst month | 512 / −2,743 | 318 / −2,486 |
| months with a losing book (all trades, P&L ÷ credit) | 39 / 97 | 71 / 97 |

Reading: the variance cut is robust (about 0.6× per trade, 0.67× on a monthly book). **The worst dollar month is
cut by only ~9%**, because a crash inside the first 24 days hits both arms. The return cost shows up in every cut,
and the 21-DTE book loses in 71 of 97 months against 39 for hold. Credit-normalised figures without a credit floor
are dominated by tiny-credit tails (UVXY-type names) and aren't reported. By year, B's mean sits below A's in
every full year except 2020 (tie, −1.43 vs −1.44) and 2023 (≈ tie).

## What I would take

1. **The framing, not the evidence:** 21 DTE is a volatility-control rule, and managing winners is the return
   rule. That split matches our ledger on the first half. The second half is untested.
2. **A correction to relay:** "similar return, less volatility" is the claim tastylive's mid-priced studies
   produce. At real fills the 21-DTE close earns **less** than holding (−$0.52/share, t −2.42). It's a risk
   purchase with a price.

## Not tested, could be

Specs only. Nothing queued.

- **The 50%-take arm on the existing harness** (doctrine row 22, already named in `sosnoff_doctrine.md` next-tests
  item 2). This video adds nothing to that spec except the prior. Their bull-market qualifier says to report it
  per year and against a stock/delta-matched control, not just against hold.
- **Put-only version of the 21-DTE study on SPY**: 20Δ / 45 DTE naked put, arms hold / 21-DTE / 50%, from
  `data/cache/SPY_puts_v3_2018_2026.parquet` (v3, so zero-bid rows survive; recover spot from the chain since strikes
  are RAW). Would replicate the video's exact cell at real fills. Low value: the strangle panel's SPY subset already
  shows the same sign (−$0.78, t −1.81), and a single-name-free SPY put test has ~97 independent months at best.
- **The capital-allocation claim** is not testable as a claim, because size scales linearly. The testable version
  is concurrency: does a 21-DTE book, which frees capital after ~24 days, carry a different drawdown at equal
  average buying-power use than a hold book? That's a portfolio simulation on the existing CSV plus a
  buying-power model we don't have. Not worth building for this video.

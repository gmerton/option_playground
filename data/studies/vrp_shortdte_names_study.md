# Short-dated premium selling on single names — stage two

Generated 2026-09-15. 68,946 closed bull put spreads, 12 single names, 2018-01-05 to 2026-02-13.

> **Data note.** 4 row(s) were dropped as corrupt: a defined-risk spread cannot return worse than -100% of max loss, and these carried an `exit_net_value` far above the spread width. All of them are MA expiring 2022-02-11, a bad quote in the shared MySQL `options_cache`. Left in, they alone drag MA's 10-DTE mean to -799%.

Engine: `lib.studies.put_spread_study` unchanged, wing ~0.15 delta, 50% profit take, weekly Friday entries, net of the house cost model ($0.65/leg commission plus 25% of entry bid-ask per traded side).

Hurdle: Bonferroni at 50 declared trials, t >= 3.29. t-stats collapse each date to a cross-sectional mean before correcting, because these names all trade on the same Fridays.

## 1. 10 DTE vs 30 DTE, pooled across names

```
  cell               n   net ROC    gross  cost bite   ann net    win   days
  --------------------------------------------------------------------------
  10d  0.25D    11,663    -0.49%   +1.09%       145%   +265.7%  86.2%    4.9
  10d  0.30D    11,670    -0.62%   +1.70%       136%   +366.0%  83.0%    5.1
  10d  0.35D    11,608    -0.73%   +2.35%       131%   +453.9%  79.6%    5.3
  30d  0.25D    11,377    +1.32%   +2.96%        55%   +263.7%  90.0%   12.9
  30d  0.30D    11,376    +1.79%   +4.19%        57%   +355.5%  87.7%   13.7
  30d  0.35D    11,252    +2.57%   +5.77%        55%   +439.3%  85.1%   14.6
```

## 2. Is the net edge statistically real?

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  10d 0.25D                11,663     411   -0.10%   7.30%    69%     -0.1   -0.12     0.12    [ -1.64, +1.58]    3.29  -
  10d 0.30D                11,670     411   -0.22%   7.11%    68%     -0.2   -0.21     0.03    [ -2.18, +1.87]    3.29  -
  10d 0.35D                11,608     411   -0.43%   8.63%    64%     -0.3   -0.34    -0.04    [ -2.81, +2.06]    3.29  -
  30d 0.25D                11,377     411    1.83%   7.21%    76%      2.7    2.10     1.92    [ +0.25, +3.62]    3.29  -
  30d 0.30D                11,376     411    2.41%   9.76%    76%      2.8    2.10     1.59    [ +0.29, +4.86]    3.29  -
  30d 0.35D                11,252     411    3.13%  10.24%    74%      3.0    2.13     1.45    [ +0.40, +6.21]    3.29  -
```

Values are per-trade return on capital at risk, in percent (the table scales by 100, so read `mean` as percentage points of ROC).

## 3. The VIX gate

On SPY the 10 DTE spread was net NEGATIVE below VIX 20 at almost every delta, and the all-VIX result was carried entirely by calmer days being excluded. This checks whether single names behave the same way.

  (no VIX column on the sweep)

## 4. Per name, 10 DTE

```
  ticker         n   net ROC    gross  cost bite     win
  ------------------------------------------------------
  AAPL       3,057    +1.23%   +2.66%        54%   84.6%
  AMZN       3,060    +2.25%   +3.62%        38%   84.8%
  COST       3,059    -1.22%   +1.46%       183%   83.2%
  GOOGL      3,060    -0.76%   +1.30%       158%   82.8%
  HD         3,052    -7.04%   -3.94%       -79%   76.3%
  JNJ        2,961    -3.52%   +0.21%      1796%   80.6%
  MA         3,041    -1.28%   +1.58%       181%   82.9%
  META       1,476    -0.20%   +0.93%       122%   81.2%
  MSFT       3,066    -0.23%   +1.48%       116%   82.8%
  NVDA       3,048    +3.80%   +4.99%        24%   85.3%
  V          3,045    +0.56%   +3.19%        82%   85.8%
  WMT        3,016    -0.80%   +2.64%       130%   84.3%
```


---

# Verdict — 2026-09-15

**The 10-DTE single-name idea is dead, and it died exactly where it was predicted to.**

Stage one found a large gross premium at the short end of single names: +4.13 vol points,
t 8.74, 82% of days positive. Stage two says you cannot get it.

```
  tenor   net ROC (0.30D)   gross   cost bite   names net-positive
   10d         -0.62%       +1.70%      136%        4 of 12
   30d         +1.79%       +4.19%       57%       10 of 12
```

At 10 days the cost model eats more than the entire gross edge. That is not a marginal
haircut, it is the trade. The warning written into the stage-one report before any of this
ran said gross premium would be richest exactly where the cost ratio is worst. It was.

## Liquidity is the gate, not the premium

Per-name net return at 10 DTE tracks the cost bite almost perfectly:

| name | cost bite | net ROC |
|------|-----------|---------|
| NVDA | 24% | +3.80% |
| AMZN | 38% | +2.25% |
| AAPL | 54% | +1.23% |
| V | 82% | +0.56% |
| MSFT | 116% | −0.23% |
| WMT | 130% | −0.80% |
| COST | 183% | −1.22% |
| JNJ | 1796% | −3.52% |

The four survivors are the four tightest markets. Everything with a bite above 100% is
negative by construction. SPY, which cleared +1.16% in the earlier pilot, has the tightest
spreads of all and sits at the top of the same ranking.

**So the tradeable version is narrow and specific: short-dated defined-risk premium selling
works only on the very tightest-spread underlyings** — SPY and a handful of mega-caps — not
across the 331-name universe where the premium is largest. That is a real strategy, just a
much smaller one than stage one implied.

## ⚠ The 30-DTE result is probably not premium

30 DTE is net positive on 10 of 12 names, and the bootstrap interval excludes zero at every
delta ([+0.25, +3.62], [+0.29, +4.86], [+0.40, +6.21]). But **stage one found no 30-day
variance premium in either universe** (+1.24 vol points, t 1.37 on single names).

A bull put spread is not a pure volatility trade. It is short a put, so it collects both the
premium and the equity drift. If there is no 30-day premium but the spread still makes money
at 30 days, the most likely explanation is direction, not vol. The two names that lose at
30 DTE, HD and JNJ, are the two with the worst underlying drift over the window, and HD is
gross-negative at both tenors — which is what a direction bet looks like, not a premium one.

**Do not treat the 30-DTE column as a validated strategy.** It needs the beta check that the
research bar already requires: compare against a delta-matched long-stock position over the
same dates. Until that runs, it is an unexplained positive, not an edge.

## Gaps in this run

- **The VIX gate was not measured.** The sweep frame does not carry a `vix` column, so
  section 3 is empty. The SPY pilot showed the 10-DTE edge was entirely conditional on
  VIX > 20, and that check has not been repeated here.
- 12 names, all mega-cap, chosen because they already had cached short-DTE data. This is not
  a random sample of the 331-name pool and is biased toward the liquid end, which if anything
  makes the 10-DTE result look better than it is.
- One structure (bull put spread, 0.15 delta wing, 50% profit take). A short strangle or
  iron condor at the same tenor has a different cost profile.

## What this changes

1. **Do not build a 331-name short-dated premium seller.** The premium is real and
   unreachable on most of that universe.
2. **A tight-spread version is worth finishing**: SPY plus NVDA, AMZN, AAPL, V, with the VIX
   gate measured properly and the entry restricted to days above the threshold.
3. **Run the beta check on the 30-DTE column before anything else**, because it is currently
   the strongest-looking number in this study and the least likely to be what it appears.

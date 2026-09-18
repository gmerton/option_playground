# Reconciling the long straddle with the variance risk premium

Generated 2026-09-15. 128,447 straddle trades matched to an independent implied-vol measurement and to realized vol over each trade's own horizon. 317 tickers, 2018-01-05 to 2026-02-20.

Hurdle: Bonferroni at 50 declared trials, t >= 3.29.

## 1. Does the 10-day premium transfer to single names?

The ETF panel found +1.75 vol points at 10 days. Index implied vol carries a correlation premium that single stocks do not, so this is the first thing to check before calling anything a contradiction.

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  single names 10d        417,022   2,093    4.13%   5.16%    82%     20.3    8.74     7.68    [ +3.17, +4.92]    3.29  YES
  single names 30d        455,347   2,093    1.24%   3.03%    71%      5.3    1.37     1.19    [ -0.69, +2.73]    3.29  -
```

## 2. Straddle outcome by the premium it actually faced

`premium = implied at entry - realized over the trade's own horizon`. Positive means the straddle bought vol that turned out expensive. If the straddle is a premium trade, its returns should fall monotonically across these buckets.

> **LOOK-AHEAD BY CONSTRUCTION — this is a diagnostic, not a signal.** The premium is measured over the same forward window that determines the straddle's payoff, so sorting trades by it is partly sorting them by their own outcome. A monotonic table here answers *what kind of trade the straddle is*. It cannot be traded, because the premium is unknown at entry. Section 3 is the one that uses entry-time information.

```
  bucket                               n   med ROC  mean ROC(w)  mean ROC(raw)    win  mean prem
  ----------------------------------------------------------------------------------------------
  prem -8.765..-0.066             25,690     49.3%        60.5%         461.8%    67%    -22.73%
  prem -0.066..+0.009             25,689      1.6%        11.6%         378.5%    51%     -2.42%
  prem +0.009..+0.060             25,689    -18.7%        -9.4%         305.0%    40%      3.47%
  prem +0.060..+0.125             25,689    -32.7%       -23.9%        1154.7%    30%      8.95%
  prem +0.125..+3.232             25,690    -46.5%       -37.8%        1486.0%    19%     23.83%
```

## 3. What does the existing IV-percentile gate select?

The playbook gate buys when own IV percentile is LOW. If that gate is the edge, low percentile should line up with a negative premium.

```
  bucket                               n   med ROC  mean ROC(w)  mean ROC(raw)    win  mean prem
  ----------------------------------------------------------------------------------------------
  ivpct +0.003..+0.104            24,652    -16.5%         1.7%         592.8%    42%      1.07%
  ivpct +0.104..+0.310            24,688    -16.9%        -0.4%         269.9%    42%      2.02%
  ivpct +0.310..+0.548            24,941    -17.6%        -0.1%         899.8%    41%      2.20%
  ivpct +0.548..+0.778            24,574    -17.5%         0.5%         723.4%    42%      2.80%
  ivpct +0.778..+1.000            24,402    -20.4%        -2.3%         327.6%    40%      3.28%
```

## 4. Convexity check

A straddle pays on the TERMINAL move; realized vol sums DAILY squared moves. If the edge is convexity, straddle returns should track the terminal move relative to implied far better than they track the premium.

```
  Spearman rank correlation of winsorized straddle ROC with:
    premium (iv - rv_fwd)   -0.387   <- negative if it is a premium trade
    realized vol (rv_fwd)   +0.230
    implied at entry (iv)   -0.026
```

## 5. Is the premium spread real, or date-clustered noise?

> Same look-ahead caveat as section 2. This asks whether the premium-to-payoff link survives pairing by date (so it is not just a few violent days), not whether it can be traded.

```
  cheapest-premium quintile minus richest, same dates only
    paired dates      411
    mean ROC gap      +95.33 pp
    t (Newey-West)    +39.26    hurdle 3.29
    bootstrap 95% CI  [+91.31, +100.47] pp
    verdict           REAL
```


---

# Verdict — 2026-09-15

All three escape routes are closed, and the answer points at the opposite side of the
trade we currently hold.

## A. "The premium does not transfer to single names" — REJECTED

| universe | 10d premium | t_NW | dates positive |
|----------|-------------|------|----------------|
| 10 ETFs  | +1.75 vol pts | 8.93 | 75% |
| 331 single names | **+4.13 vol pts** | 8.74 | **82%** |

It does not merely transfer. It is **2.4x larger** on single names. At 30 days it is
+1.24 with t 1.37, the same nothing we saw on ETFs. The premium is a short-dated effect
and it is strongest exactly where the straddle trades.

It is also not just earnings. Split by own-IV percentile it is positive in every quintile,
rising from +2.52 (lowest IV) to +6.62 (highest), with 66-69% of days positive throughout.
Event risk makes it bigger; it does not create it.

## B. "The edge is the entry gate" — REJECTED

The playbook buys when own IV percentile is low. Across percentile quintiles the straddle's
outcome is **flat**: median ROC between -16.5% and -20.4%, win rate between 40% and 42%, in
every bucket. The gate does not sort outcomes. Implied vol at entry has a Spearman
correlation with returns of -0.026, which is nothing.

## C. "The edge is convexity, not premium" — REJECTED as the main effect

Sorted by the premium it actually faced, the straddle is cleanly monotonic: the cheapest
quintile returns a median +49.3% with a 67% win rate, the richest -46.5% with a 19% win
rate. Spearman correlation with the premium is -0.387. It is a premium trade, and it is on
the losing side of one. (That sort uses look-ahead and is a diagnostic only — see section 2.)

## The finding that matters most

Equal-dollar across 128,447 trades:

```
  top 0.1% of trades (128 of 128,447)   contribute  99.9% of the total return
  mean ROC, all trades                  +757%   <- inflated by one corrupt row (+10,526,214%)
  mean ROC excluding top 0.1%           +0.57%
  mean ROC excluding top 1%             -2.61%
  median ROC                            -17.6%
  win rate                              41.5%
```

**The long straddle's entire expectancy lives in 128 trades.** Remove one trade in a
thousand and it is a coin flip; remove one in a hundred and it is negative. That is a
lottery-ticket profile, not a carry profile, and it is extremely sensitive to whether the
tail is actually held and to position sizing.

This does **not** prove the playbook's +4.1%/trade wrong. That figure came from a gated
subset with its own filters and a cost model, and is a mean of a right-skewed distribution,
which median -17.6% does not contradict. But tail concentration is a property of the payoff
shape, not of the gate, so it survives any gating and is a live risk to how the strategy is
sized.

## What to attack first

**Short-dated, defined-risk premium selling on the single-name universe.**

The reasoning in one line: the premium is +4.13 vol points at 7-14 days on 331 names with
82% of days positive, we are currently positioned against it, and the gate we thought was
picking our spots is not picking anything.

Naked short is not the answer. The same 128 trades that carry the long straddle would
destroy a naked short seller — the sell side's raw mean is -757%. The structure has to cap
the tail:

```
  long straddle, ex-top-1%     -2.61%   (what we own)
  short straddle, ex-top-1%    +2.61%   (gross, but the tail is unbounded)
  short straddle, median       +17.6%   (the carry the defined-risk version is reaching for)
```

A bought wing converts that unbounded tail into a known maximum loss while keeping most of
the carry. That is the stage-two question, and it is a parameter change to an engine that
already exists and is already audited: `lib.studies.put_spread_study` at `--dte 10` instead
of the book's 20-45, with `lib.studies.costs` applied.

The honest risk going in: short-dated options have the worst cost ratio in the book, small
premium against a bid-ask that does not shrink proportionally. Stage one says the gross
edge is real and large. Only stage two decides whether any of it survives the fill.

---

# Stage-two pilot — SPY bull put spreads, 10 DTE vs 30 DTE (2026-09-15)

`run_put_spreads.py --ticker SPY --dte {10,30} --dte-tol 4 --spread 0.25`, weekly Friday
entries, 50% profit take, wing ~0.15 delta, ~410 closed trades each, net of the house cost
model ($0.65/leg commission plus 25% of entry bid-ask per traded side).

Net ROC per trade, all-VIX column:

| short delta | 10 DTE | 30 DTE |
|-------------|--------|--------|
| 0.20 | +0.82% | +1.33% |
| 0.25 | +0.94% | +1.05% |
| 0.30 | +0.65% | +1.14% |
| 0.35 | **+1.16%** | +1.10% |
| 0.40 | +0.77% | +1.72% |

**Short-dated selling survives costs.** At matched 0.35 delta the two tenors earn almost the
same per trade, +1.16% against +1.10%, but the 10-DTE version holds capital one third as
long. On the annualized column that is roughly +703% gross against +371%, and after
applying each tenor's own cost haircut (50% at 10 DTE, 61% at 30 DTE) short-dated still
leads by about 1.5x.

**The predicted cost problem is real but not fatal.** Costs take half the gross ROC at 10
DTE against 39% at 30 DTE. Exactly the direction stage one warned about, smaller than
feared.

**⚠ The edge is conditional on VIX, not unconditional.** In the VIX<20 column the 10-DTE
spread is net NEGATIVE at almost every delta (-0.05%, -0.49%, -0.90%, -0.61%, -1.03%). The
all-VIX result is carried entirely by days above 20. This matches stage one, where the
premium was smallest in the calmest regime. Any live version needs a VIX gate, and that gate
is the difference between a strategy and a slow bleed.

## What this pilot is not

One ticker, one structure, one profit-take rule. SPY is an ETF, and the +4.13 vol point
premium that motivated this is on **single names**, which have not been through stage two at
all. The next run is the same engine on the cached single names with short-DTE coverage
(AMZN, GOOGL, NVDA, MSFT, COST already in `options_cache`), then a decision on whether the
single-name premium survives their wider spreads.

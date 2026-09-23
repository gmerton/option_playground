# ORB retest vs ORB break — the Fit Mom Trader remedy (2026-09-23)

**Verdict: FAILS as a strategy · ⭐ but the first intraday arm in this book to beat a random-minute
control on the events where it fires.** Pre-registered in `run_orb_retest_vs_break.py` before the run.
Trades: `orb_retest_vs_break_2026-09-23.csv`. Claim source:
[fit_mom_trader review](../fit_mom_trader/2026-07-24_orb_mistakes_review.md) (3/5).

## The claim

Do not trade the opening-range break — retail buy-stops sit at the obvious level and get swept. Trade the
**retest**: the pullback to the anchored VWAP or the 50% midpoint of the opening range. She accepts the
cost verbally ("you'll miss some fast moves") and never quantifies it, but asserts a backtest exists:
*"the number of times you avoid the loss exceeds the number of gains."* **That is the claim tested here.**

Our own ORB9 break entry is already known to be **INVERTED** (−0.425pp vs a random minute, t −8.50), so
beating the break is a low bar. The real question is whether the retest beats doing nothing in
particular, which no intraday arm here has ever managed.

## Method

1,411 curated ORB9 alerts, 152 sessions, 1-minute bars. Same name-day, same **0.6 ADR stop** (the live
floor), all held to the session close — only the **entry minute** differs. Retest capped at **60 minutes**
after the break. Random control = 3 draws from 09:45–12:00, averaged.

## Result

| | VWAP retest | midpoint retest |
|---|---:|---:|
| fires on | **39.1%** (551) | **14.4%** (203) |
| **when it fires** — retest | +0.321% | +0.219% |
| …vs BREAK | −1.076% → **+1.396pp, t +14.98** | −2.403% → **+2.622pp, t +10.88** |
| …vs RANDOM minute | −0.003% → **+0.324pp, t +4.45** | −0.356% → **+0.576pp, t +6.68** |
| on days it **never** comes back, BREAK earned | **+1.264%** | +0.813% |
| **STRATEGY** (no-retest = no trade, 0%) | +0.125% | +0.032% |
| …vs BREAK +0.351% | −0.225pp, t −0.57 | −0.319pp, t −0.62 |
| …vs RANDOM +0.726% | **−0.601pp, t −5.56** | **−0.695pp, t −4.92** |

**PRE-REGISTERED PASS: NO**, on the strategy view — the declared test.

## ⭐ What is genuinely new: the conditional result

On the events where the retest fires, it beats a **random minute in the same name-day** by +0.32pp
(VWAP, t 4.45) and +0.58pp (midpoint, t 6.68). **Nothing intraday in this book has done that.** Stage A
priced every intraday arm at −0.10 to −0.13R and indistinguishable from a random later minute; ORB9's own
break entry came in at −0.425pp against the same control the same day. Her entry is the exception.

Note *which* days those are: on retest days the break earned **−1.076%** and even a random minute earned
**−0.003%**. These are the bad days, and the retest converts them to +0.321%. That is a real effect, and
it is exactly the mechanism she describes — the sweep happens, price comes back, and the pullback is where
the trade actually was.

## ⚠ Why it still fails, and why her asserted backtest is wrong

**The days that never come back are the good days.** The break earned **+1.264%** on precisely the 860
sessions where no VWAP retest appeared. Waiting forfeits all of them. Netted over the full population:

* trade every break → **+0.351%**
* trade a random minute every day → **+0.726%**
* wait for the retest → **+0.125%** per opportunity

Her claim is that the losses avoided exceed the gains missed. **On this data the reverse holds**, and by a
wide margin — the forfeited runaways are worth roughly 3–10× the salvaged failures.

⚠ **One honest alternative reading.** Per *opportunity* the retest loses; per *trade actually taken* it
wins (+0.321% vs −0.003% for a random minute on the same days). The retest deploys capital on 39% of
occasions. If capital — not opportunity — is the binding constraint, the ranking flips. That does not
rescue the claim as stated, which is about avoided losses versus missed gains, but it is the version of
her argument that survives.

## What this does and does not establish

* **Settled:** waiting for the retest is not a better ORB *strategy* on our equity intraday panel. Both
  definitions lose to the break and lose badly to a random minute.
* ⭐ **Not a null:** the conditional entry-quality effect is real and significant, and it is the first
  intraday thing here to clear a random-minute control. Worth remembering when any future intraday work
  needs a benchmark that is not hopeless.
* ⚠ **Scope:** she trades NQ futures; this is equities. Her mechanism transfers, her instrument does not.
* ⚠ The 60-minute retest cap and the 0.6 ADR stop are fixed parameters, deliberately not swept.

## ⛔ Data note — the cached `vwap` column is PER-BAR, not session-cumulative

`data/cache/intraday_1min/*.parquet` carries a `vwap` column that is **byte-identical to `price` on every
bar** (verified 2026-09-23). It is that minute's own VWAP, not the running session VWAP.

The first cut of this study used it directly, and the tell was immediate and loud: the "pullback to VWAP"
fired on **100.0% of breaks**, because `close <= per-bar vwap` is near a coin flip each minute. A
100% fire rate is not a setup. Session VWAP must be rebuilt as `cumsum(price × volume) / cumsum(volume)`.

⚠ My first diagnosis of that 100% was **also wrong** — I blamed a missing time limit, added a 60-minute
cap, and the rate stayed at 100%. Only then did I check the column.

**No production impact.** `src/lib/alerts/bars.py:49` computes session VWAP correctly from cumulative
price×volume for the live detectors, and `src/lib/studies/pattern_test.py:259` already rebuilds it with
the same cumsum. The precedent existed and should have been followed.

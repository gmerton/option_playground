# Review — KINFO: "This Trader Made +$700K in 6 MONTHS" (Malik, TQQQ/SQQQ systematic)

**Video:** [`pBS5vrqrUjk`](https://www.youtube.com/watch?v=pBS5vrqrUjk) · KINFO · 2025-09-11 · 52:36 · 604k views
**Reviewed:** 2026-07-27 · verification script: `carter_mastering_the_trade/backtests/risk_architecture/check_tqqq_claim.py`

> ## Verdict: **limited promise — 1.5/5.** The methodology is the most testable thing we've
> reviewed and the verified live record is real, but every headline number fails checking, and
> the live result **underperforms simply buying and holding the ETF he trades.**

---

## Who / what

Malik, a software engineer (Microsoft, Salesforce, 20 yrs), trading since ~2016, "consistently
profitable since 2022." Fully automated, **7 sub-strategies** (trend-following + mean reversion,
long and short), low frequency (1–2 trades/week), position-held-for-months style. He trades
**only TQQQ and SQQQ** — the 3× long and 3× short NASDAQ-100 ETFs. Wrote his own backtest/execution
engine ("White Light"). Sells signals on Collective2 (~$50k of subscriber capital following).

**Stated live result: ~40%/yr over ~3 years, with 30–33% max drawdown.**
**Stated backtest: 80%/yr from 1985**, vs QQQ buy-and-hold ~12%.

## What's genuinely good — and it's not nothing

1. **KINFO verification is brokerage-linked.** The $700k is very likely real money actually made.
   That alone puts him above almost everything else reviewed in this repo.
2. **He corrects the clickbait himself.** The "+$700K in 6 months" is an artifact of Kinfo booking
   profit on *closed* positions — he held those positions for two to three years. The host hypes
   it; Malik explains the accounting unprompted.
3. **Fully mechanical ⇒ falsifiable.** Unlike Luk/Breitstein/Qullamaggie, there is no discretionary
   joint. This is the rare case where the strategy family can actually be tested.
4. **He names his weakness** — sideways markets — and doesn't claim it works everywhere.
5. **"Most of the technical analysis… when I actually backtested it, none of it worked."**
   Independently consistent with this repo's own results.

## ⚠ Why the numbers don't survive checking

### 1. 80%/yr for 40 years is arithmetically impossible

$10,000 at 80%/yr for 40 years = **$162 trillion**, larger than world equity market cap. This is
not a close call or a modelling quibble — any backtest producing it is broken. It is the single
fastest disqualifier available and needs no data to apply.

### 2. ~60% of the backtest is synthetic, in exactly the place synthesis is most dangerous

**TQQQ and SQQQ both launched in February 2010.** Everything before that — including the dot-com
crash and 2008, the two events he cites as proof of robustness — is simulated from the NDX index.

Leveraged ETFs reset daily, so they are *not* 3× the index over any period longer than a day. Drag
is roughly (L²−L)/2 × σ², which at the ~50% realised volatility NDX ran in 2000–02 is on the order
of **75%/yr**. A naive 3× simulation that misses this produces spectacular fictional returns
precisely during the periods he showcases.

### 3. The rule he demonstrates on screen doesn't do what he says

He shows: long 100% TQQQ when price is above the 50-day and 250-day MAs; shorts and mean-reversion
sub-strategies take over when the trend breaks. Reconstructed on NDX 1985–2026, traded next-close
(no look-ahead), with expense ratio, financing on the borrowed 2× notional at the **actual
time-varying T-bill rate**, and 5 bp per switch:

| | CAGR | max DD | MAR |
|---|---:|---:|---:|
| **Naive 3× (zero costs)** — what a careless backtest shows | **+2.19%** | −98.1% | 0.02 |
| **Modelled 3×** (expense + financing + slippage) | **−4.68%** | −99.3% | −0.05 |
| Buy & hold synthetic TQQQ | +12.97% | −100.0% | 0.13 |
| NDX index (price only) | +14.53% | −82.9% | 0.18 |

Even the **zero-cost** version returns 2.2%/yr, not 80%. Whipsaw in a 3× vehicle is devastating.

### 4. The dot-com claim inverts

He claims **+200% in 2000 and +152% in 2001**. The reconstruction:

| year | modelled | naive |
|---|---:|---:|
| 1999 | +136.7% | +163.3% |
| **2000** | **−49.2%** | −43.3% |
| **2001** | **−50.7%** | −47.4% |

⚠ **Fairness caveat, and it matters:** this is *my* two-state reconstruction, not his seven-strategy
ensemble. He is explicit that the shorts come from separate mean-reversion sub-strategies and that
the MA rule was illustrating the *long* entry only. So this does **not** prove his system loses
money in 2000 — it proves the rule he *demonstrated on camera* does, and that the gap between the
demo and the claim is very large.

### 5. ⚠ 300–350 strategies tested, 7 kept

> "I have backtested almost **300 to 350 strategies**, only seven of them [survived]."

The host presents this as diligence. It is the **single strongest reason to distrust every
backtested number in the video.** Searching 350 specifications over one 40-year path and keeping
the best 7 guarantees the survivors' performance is selection-biased upward; this is the standard
multiple-testing problem, and it is why the serious literature demands far higher significance
bars for mined strategies. No walk-forward, no held-out period, and no deflation for the number of
trials is mentioned anywhere in 52 minutes.

### 6. The live record loses to buy-and-hold of the thing he trades

His stated live window (~Sep 2022 → Sep 2025), which **begins essentially at the bear-market
bottom** — the most favourable possible start for a long-biased NASDAQ strategy:

| | CAGR | max DD | MAR |
|---|---:|---:|---:|
| **His stated result** | **~40%** | ~30–33% | **~1.2** |
| **TQQQ, just buy and hold** | **+52.4%** | −58.0% | 0.90 |
| QQQ, just buy and hold | +25.5% | −22.8% | **1.12** |
| NDX | +24.8% | −22.9% | 1.08 |

**He earned less than holding TQQQ (40% vs 52%), and his risk-adjusted result (~1.2) barely
exceeds simply owning QQQ (1.12).** Three years of automation, seven sub-strategies and 350
backtests to roughly match a buy-and-hold of the unlevered index on MAR.

## Method notes on my own check

- The simulator was validated against real TQQQ 2010–2026: it produces 211× vs the actual 322×
  (ratio 0.66). **My model is still ~2.7%/yr too harsh** — probably FIN_SPREAD and using 0.95%
  rather than TQQQ's 0.84% expense ratio. So the strategy table above is, if anything,
  conservative against him; correcting it would not move a −4.7% CAGR anywhere near +80%.
- First pass used a flat 3% risk-free rate, which badly mispriced the ZIRP decade and biased
  results against any levered strategy. Rerun with the actual ^IRX 13-week bill series.
- No look-ahead: signal computed on close *t*, position applied from close *t+1*.

## Does it have promise?

**The instrument choice is the problem, not the method.** Automated, low-frequency, regime-aware,
tested across many market environments — that is exactly the methodology this repo values, and it
is the reason his live drawdown (−33%) is so much better than TQQQ's (−58%). The trend filter *is*
doing real work.

But 3× daily-reset ETFs are a known trap: they convert whipsaw directly into permanent capital
loss, and they make backtests look brilliant precisely where they are least trustworthy.

**Two things worth taking:**

1. ⭐ **The idea is directly testable here, and cheaply.** This repo's largest single finding is
   that a market-regime gate halves drawdown and triples MAR
   ([`REGIME.md`](../carter_mastering_the_trade/backtests/risk_architecture/REGIME.md)). A
   regime-gated levered index strategy is the natural application of that result, and the harness
   already exists. Worth an afternoon — with **modest leverage (1.5–2×) rather than 3×**, which is
   where the whipsaw math stops being ruinous.
2. **The multiple-testing lesson cuts at us too.** 350 strategies → 7 survivors is what this repo
   would produce if it stopped reporting the nulls. Every failed test recorded in
   `carter_mastering_the_trade/` is what keeps our surviving results meaningful. Worth being
   explicit about that in future write-ups.

**Do not follow the signals**, and treat the 80%/yr and dot-com figures as disqualified.

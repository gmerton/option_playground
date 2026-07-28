# TQQQ/SQQQ Lab — can a rule on these two ETFs be consistently profitable?

**Run:** 2026-07-27 · `build_tqqq_lab.py` + `build_tqqq_lab_v2.py` · prompted by the
[KINFO/Malik review](../../video_reviews/kinfo_malik_tqqq_2025-09-11.md)

**Protocol (the point of the exercise):** he tested 300–350 rules and kept 7. Here: **~20
pre-specified, mechanism-justified, untuned rules**, every one reported in **three disjoint
periods** (synthetic 1985–2009, real 2010–2017, real 2018–2026), nothing selected after the fact.

**Two modelling fixes he got wrong:** real TQQQ prices already contain the expense ratio and
financing, so costs are charged only on the synthetic pre-2010 series (slippage only on real
data); and the synthetic series is **calibrated** to actual TQQQ rather than assumed.

---

## Bottom line

> **"Consistently profitable" — no.** Nothing beat buy-and-hold QQQ on *year-consistency*: every
> gated rule had 3–5 losing years out of 17; plain QQQ had **2**.
>
> **"Reasonable" — yes, one configuration.** Long-only, 200-day-gated, ~1.5× exposure (50% TQQQ),
> **no SQQQ**. It's a modest improvement on buy-and-hold and a large one in genuine bear markets.
>
> **But the leverage buys no alpha.** That's the finding that matters most.

## 1. ⭐ The decisive control: leverage adds nothing risk-adjusted

Same 200-day timing rule, unlevered QQQ vs 3× TQQQ. Sharpe is volatility-normalised, so if it
doesn't improve, the leverage is contributing size and drag — not edge.

| period | QQQ gate Sharpe | TQQQ gate Sharpe | **Δ from 3× leverage** |
|---|---:|---:|---:|
| Synthetic 1985–2009 | 0.58 | 0.55 | **−0.02** |
| Real 2010–2017 | 0.81 | 0.82 | **+0.00** |
| Real 2018–2026 | 0.95 | 0.86 | **−0.10** |

Flat to negative in all three. The vol-target sweep says the same thing from another angle — MAR
falls monotonically as the target rises (15% → 0.78, 20% → 0.75, 25% → 0.70, 30% → 0.68,
35% → 0.65), i.e. *less leverage is better risk-adjusted*, all the way down.

⟹ **TQQQ is a position-sizing decision, not a strategy.** Anyone using it should size it as
leverage they've consciously chosen, not as an edge.

## 2. ⚠ Drop SQQQ entirely — it was the worst component in every period

| period | MA200 long-only | MA200 long/short (adds SQQQ) |
|---|---:|---:|
| Synthetic 1985–2009 | +16.2% CAGR | **−17.0%** |
| Real 2010–2017 | +27.9% | **−1.1%** |
| Real 2018–2026 | +35.8% | **+7.9%** |

**9 losing years out of 17**, worst of anything tested. The mechanism is structural, not bad luck:
NDX has positive drift, so a −3× product fights *both* the drift *and* the volatility drag. SQQQ
has lost >99.9% since inception. Malik trades it; this is very likely a large part of why his live
result trailed buy-and-hold TQQQ.

## 3. The 200-day gate is real, and it replicates

Consistent with this repo's largest prior finding ([`REGIME.md`](../../carter_mastering_the_trade/backtests/risk_architecture/REGIME.md)),
now confirmed on a different instrument and a different era:

| | buy&hold QQQ | QQQ + MA200 gate |
|---|---:|---:|
| Synthetic 1985–2009 (dot-com) | **−1.28%** CAGR, −83.0% DD | **+9.66%** CAGR, −59.3% DD |
| Real 2018–2026 | 19.57%, −35.1%, MAR 0.56 | 16.24%, **−22.0%**, **MAR 0.74** |
| 2022 alone | **−33.2%** | **−18.7%** |

It gives up return in mild chop and saves you in real bear markets. That is the whole trade.

## 4. ⚠ Where "consistency" fails, and why

Losing calendar years, 2010–2026 (17 years):

| rule | losing years |
|---|---:|
| **buy & hold QQQ** | **2** |
| MA200 gate (any leverage) | 4 |
| vol-targeted 25% | 4 |
| 50% TQQQ + gate | 4 |
| vol-target + low-vol gate | 5 |

The gates lose in **mild-chop years** — 2011 (QQQ +1.9%, gate −11.8%), 2016 (QQQ +9.4%, gate
−0.5%), 2015 — because they churn around the line while the index grinds sideways-to-up.

**The whipsaw fixes don't replicate.** Tested hysteresis buffers (1/2/3/5%) and monthly
rebalancing. The best buffer size *flips across periods*: 5% in the synthetic era, 0% in 2010–17,
1% in 2018–26. **That pattern is noise, not signal** — and selecting the buffer that wins overall
would be exactly the mistake this study was built to avoid. Reported and rejected.

## 5. The configuration I'd actually defend

**Long-only, 200-day gate on NDX, 50% TQQQ (~1.5× effective), no SQQQ, no buffer.**

| | CAGR | max DD | MAR | Sharpe |
|---|---:|---:|---:|---:|
| buy & hold QQQ, 2018–26 | 19.57% | −35.1% | 0.56 | 0.87 |
| **this rule, 2018–26** | **20.58%** | **−31.4%** | **0.66** | 0.86 |
| buy & hold TQQQ, 2018–26 | 33.01% | −81.7% | 0.40 | 0.76 |

Slightly better return than QQQ with a slightly smaller drawdown, and far better than holding
TQQQ. It trades ~4×/yr. Dial the TQQQ fraction up for more return at proportional risk — that is
the honest lever, and it is *not* free.

⚠ **Be clear-eyed about what it is:** scaled beta with a timing overlay. It has no alpha over the
unlevered gated version, it still loses ~26% in 2022 and ~17% in 2011, and it underperforms plain
QQQ in quiet up-years.

## 6. Limitations

- **Three periods, one instrument, one index.** NDX 1985–2026 is a single path; the 200-day gate's
  value here rests heavily on two events (dot-com, 2022).
- **The synthetic era is synthetic.** Calibrated to real TQQQ, but SQQQ/TQQQ did not exist before
  2010 and the drag constant is assumed stable across regimes — it isn't; it scales with rates.
- **Slippage 5 bp/switch, no tax.** Low-turnover rules survive this; the 15% vol-target
  (137 trades/yr) probably does not.
- **NDX is not investable** — the gate is computed on the index and traded via ETFs. Minor, but it
  is a small look-ahead in liquidity terms.
- No test of what happens if the NASDAQ's 40-year uptrend doesn't repeat. Every long-only result
  here is conditional on that.

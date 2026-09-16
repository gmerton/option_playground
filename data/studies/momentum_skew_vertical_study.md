# Momentum-skew verticals — oquants strategy #3, tested on real quotes (2026-09-16)

**Their rule.** Skew = (ATM IV − 25Δ IV)/ATM IV per wing; when its z-score ≤ −1.5 *and* momentum agrees (CS decile
≥8 / ≤3, TSMOM sign, relative momentum vs SPY), buy the 45-60Δ option and sell the 10-25Δ wing on the same expiry,
7-21 DTE, hold to expiry, close before earnings. **Claimed +23% mean return on debit at a 32% win rate** — from a
geometric Brownian motion simulation on one name, which assumes the lognormal distribution their own thesis says is
wrong (review: `data/oquants/posts/momentum-skew-strategy.md`).

**This test.** 249 liquid-option names in the straddle pool that also have price history, 2019-01 → 2026-02 (v3
loses bid/ask in March 2026). Signal expiry = nearest 14 DTE; skew z-scored against each ticker's own trailing 252
days (min 120). Momentum from `liquid_panel_2019.parquet`: 126-day return, its cross-sectional decile, sign, and
ratio to SPY. Entry priced at mid + 25% of the bid-ask + $0.0065/share per leg. **Settlement at intrinsic from a
put-call-parity spot on the same unadjusted basis as the strikes** — no adjusted price feed, no chain lookup after
entry. 668,834 priced verticals; 9,566 pass their full rule. Scripts: `run_skew_vertical_pull.py`,
`run_skew_vertical_sim.py`; data `data/cache/skew_vertical/`.

## The gates do separate — but almost all of it is the call wing

| cell | n | mean ROC on debit | median | win | halves | per-trade t |
|---|---|---|---|---|---|---|
| ungated, all verticals | 668,834 | −4.1% | −83.9% | 38% | −5.4 / −2.8 | −26.2 |
| skew z ≤ −1.5 only | 44,461 | −2.2% | −92.5% | 36% | −2.5 / −2.0 | −2.3 |
| momentum only | 139,629 | −0.5% | −80.2% | 39% | −3.1 / +1.3 | −1.2 |
| skew + momentum | 10,772 | +7.7% | −77.9% | 39% | +7.0 / +8.0 | 2.3 |
| **their full rule** | 9,566 | **+8.8%** | −75.3% | 39% | +7.3 / +9.7 | 2.4 |
| their full rule, **call wing** | 6,601 | **+17.7%** | −55.9% | 42% | +3.7 / +23.8 | 3.4 |
| their full rule, **put wing** | 2,965 | **−11.0%** | −100% | 34% | +12.2 / −33.0 | −4.8 |

## The skew premium is real, measured properly

Conditioning on what the underlying actually did over the hold isolates the pricing effect from the directional one.
The gate does **not** pick names that go up more (gated call trades saw +0.88% vs +1.03% for the control), but given
the *same* move it converts it into more profit, because the richer wing you sold lowers the debit:

| underlying move over the hold | gated ROC | control ROC | gate worth |
|---|---|---|---|
| < −5% | −99.9% | −100.0% | +0.1pp |
| −5 to 0% | −98.7% | −99.1% | +0.4pp |
| 0 to +5% | +31.1% | +22.3% | +8.8pp |
| +5 to +10% | +171.8% | +149.0% | +22.7pp |
| > +10% | +295.1% | +198.7% | +96.4pp |

Weighted, **the gate is worth +15.3pp conditional on the move**. The skew decile table agrees and is monotone-ish:
steepest decile +10.3% vs flattest +5.8%. So the thesis is sound — the wing really is overpriced, and selling it
really does raise the payoff per unit of move.

## It is still not tradable

- **Monthly-mean t = 0.1** over 71 months, 55% of months positive. The per-trade t of 3.4 is an illusion: 6,601
  trades cluster into 71 months and are heavily correlated within them. At the month level there is no edge.
- **The mean is 66 trades.** The top 1% of the gated call cell contributes **52%** of total ROC; the top 5%
  contributes 115%, i.e. the other 95% lose money together. Excluding the top 1% the mean falls from +17.7% to +8.6%.
  The median trade is **−55.9%**.
- **One name and one year carry it.** WDC alone averages +427% over 91 trades. Gated-minus-control by year on the
  call wing: +7.2, −8.4, −3.7, −27.1, +13.3, +0.4, **+45.2**, −15.9 — positive in 4 of 8 years, and excluding 2025
  the gate is worth +3.2pp.
- **The ungated control is the more robust trade.** Buying a 52Δ call and selling a 17Δ call on this universe,
  unconditionally, made +6.8% per trade with monthly t 1.9, 62% of months positive, and compounds to 2.36×. The
  gated version compounds to zero at equal weight because one month is a total loss. (At their stated 0.5-2% per
  position that is a sleeve drawdown, not ruin — but the ranking is what matters.)
- **The put wing loses**, −11.0% with the second half at −33.0%. A rule that only works on one side in a bull sample
  is a directional bet wearing a relative-value label — which their own drift sensitivity already hinted at.

## Verdict

**Mechanism confirmed, strategy not.** The skewness premium they describe is measurable and worth ~15pp per unit of
move, which is a genuine finding and more than the vendor established with a lognormal simulation. But the realized
edge does not survive month-level aggregation, is concentrated in a handful of trades, one ticker and one year, works
only on the call side of a bull sample, and loses to the ungated version of the same structure on every robustness
measure. Conviction stays **2/5**. Not a candidate for capital.

**Methodological note.** The per-trade vs monthly t gap here is the same family of error as the calendar study's
truncation: a statistic that looks decisive because the unit of observation is wrong. Overlapping option trades
within a month are not independent draws. Report the monthly-mean t alongside the per-trade t in every future
options study.

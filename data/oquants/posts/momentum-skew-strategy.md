# Momentum-Skew Strategy (posted 2025-09-17) — video `6I5a3QQX4y0`

**Thesis.** Two premia in one debit vertical. (1) Skewness premium: OTM wings (hedgers' puts, speculators' calls) are rich, so the short leg sells expensive convexity. (2) Momentum: the long leg rides continuation. Framed as a relative-value spread: buy fair or cheap ATM vol, sell rich wing vol.

**Signals.** Skew = (ATM IV − 25Δ IV) / ATM IV per wing; **z-score ≤ −1.5** vs its own history (more negative = steeper). Momentum in the skew's direction: cross-sectional decile **≥8** (call-skew longs) or **≤3** (put-skew bears), time-series momentum sign, relative momentum vs S&P (>1 / <1). Liquidity ≥5k contracts/day (≥20k for easy fills). Strike check: short-leg IV ≫ RV; long-leg ATM IV ≈ or < RV.

**Trade.** Bullish: buy 45-60Δ call, sell 10-25Δ call. Bearish: mirror with puts. 10-20 DTE (video: 5-15). Payoff typically 5:1 to 10:1. Price several combinations and take the best reward/risk. Variant: a **1-3-2 ratio fly** (buy 1 ATM, sell 3 at 20-30Δ, buy 2 further; first strike gap = 2× second) for moderate momentum (decile 7-8 / 3-4); pays 20-30× at a pin but loses on overshoot. Size 0.5-2% per trade. Hold to just before expiry; take ≥90% of max early; let worthless spreads expire; **close before any earnings inside the life** unless you have an earnings view.

**Evidence.** A GBM simulation on AMC (7/22): +23% expected return on debit, **32% win rate**, and still ~breakeven at −50% annual drift. Member trades QUBT/SBET/MP/QS returned +160% to +400% (cherry-picked winners). Low win rate, expect long losing streaks.

**Our cross-check.** Maps directly onto Gabe's momentum universe (quantum, SPCX-type names) and our August vehicle study (put spreads cut loss 60-70% at equal risk but forfeit +5% winners; calls were the worst vehicle). Test idea: a 25Δ skew z-score panel from options_daily_v3 (greeks through ~2026-05) × our momentum ranks → 10-20 DTE vertical P&L with costs. Their momentum definitions are generic; our Minervini / RS stack could substitute.

## Evidence review (2026-09-16) — the simulation contradicts the strategy's own premise

**Conviction 2 / 5 · Risk 4 / 10 per trade (defined debit) · Tested by us: NO (but cheaply testable — see below).**

The mechanics are sound and the economic thesis is real: the skewness premium is a documented phenomenon, and a
debit vertical that buys near-ATM vol and sells wing vol is a clean way to express it. The problem is the evidence.

**The circularity.** The video opens by showing that real SPY log returns are negatively skewed and leptokurtic —
fatter tails and a sharper peak than a normal distribution — and argues the wings are rich *because* the risk-neutral
distribution overstates tail probabilities relative to reality. It then evaluates the trade with a **geometric
Brownian motion simulation** at a single forecast vol, i.e. under the lognormal distribution it has just said is
wrong. Under a constant-vol lognormal assumption, any option priced on a volatility smile is mechanically
"overpriced," so the +23% expected return on debit is definitionally the size of the smile, not evidence that the
smile is exploitable. The measured premium is an artifact of the model choice.

**The bias has a direction, and it flatters them.** Against reality, GBM understates large down moves (the fatter
left tail), each of which is a total loss of the debit. It also understates large up moves, but those are capped at
the spread width, so the benefit is bounded while the cost is not. Negative skew means the miss is net unfavourable.
So the true expectancy is below the simulated +23%, by an unknown amount.

**Direction is doing work they disclaim.** They call it "non-directional relative value," then run a drift sensitivity
and report that "adding a modest positive bias significantly boosts both return and probability of success" — with
the aside "I know we said direction doesn't matter, but…". A long call vertical gated on positive momentum is a
bullish position; the momentum filter is not a neutrality device.

**Other evidence gaps.** One name (AMC, 2025-07-22) for the simulation. The member trades cited at +160% to +400%
(QUBT, SBET, MP, QS) are selected winners with no denominator. A 32% win rate means long losing streaks are normal,
which is a sizing and psychology problem, not a flaw — but it makes the absent track record matter more.

**Note on the title.** "10x vertical spreads" cannot come from an uncapped move: max profit is the strike width minus
the debit. The 10x is a cheap debit relative to a wide spread, i.e. buying a low-probability structure, not catching
an outsized move.

## Why this one IS worth testing (unlike the forward-factor claim)

It needs only machinery we have, and the data reaches far enough:
- **Skew z-score** = (ATM IV − 25Δ IV)/ATM IV per wing, z-scored against its own history — needs per-strike IV and
  delta from `options_daily_v3`, present through **mid-May 2026** (verified 2026-09-16).
- **Vertical P&L with the house cost model** — needs bid/ask, which ends **March 2026** (verified same day). So a
  clean backtest runs 2018 → Feb 2026, the same window as our other engines.
- **Momentum ranks** — substitute our own (Minervini / RS stack, `project_topdown_swing_pipeline`) for their generic
  cross-sectional deciles.
No ex-earnings IV model is required (they close before earnings anyway), which is the thing that stopped the
forward-factor replication.

⚠ **Apply the erratum lesson.** Pull the strike window wide enough to cover the largest plausible move over a 10–20
DTE hold and do not delta-filter the pull; settle the spread at intrinsic from the underlying close. A vertical's
loss is capped, so truncation cannot produce the calendar study's unbounded error — but it can still hide total
losses, which is exactly the cell that decides a 32%-win-rate strategy.


## TESTED 2026-09-16 on real quotes — mechanism confirmed, strategy rejected

Full write-up: `data/studies/momentum_skew_vertical_study.md`. 249 liquid names, 2019→Feb 2026, 668,834 priced verticals, 9,566 through their full rule, house cost model, intrinsic settlement off a parity spot.

**Their rule earns +8.8% per trade pooled (+17.7% call wing, −11.0% put wing) at a 39% win rate, vs −4.1% ungated.** The skew premium is REAL: conditional on the same underlying move the gate is worth **+15.3pp**, and the gate does not pick names that move more (+0.88% vs +1.03%), so it is a pricing effect, not direction. The skew decile is monotone-ish (+10.3% steepest vs +5.8% flattest).

**But it is not tradable.** Monthly-mean t **0.1** over 71 months (the per-trade t of 3.4 treats 6,601 clustered, overlapping trades as independent); the top 1% of trades supply 52% of total ROC and the other 95% lose money together; median trade −55.9%; WDC alone averages +427% over 91 trades; gated-minus-control is positive in 4 of 8 years and worth only +3.2pp excluding 2025. **The UNGATED control is better behaved** — +6.8%/trade, monthly t 1.9, 62% of months positive, compounds 2.36×. Conviction stays 2/5.

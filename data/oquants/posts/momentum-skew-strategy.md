# Momentum-Skew Strategy (posted 2025-09-17) — video `6I5a3QQX4y0`

**Thesis.** Two premia in one debit vertical. (1) Skewness premium: OTM wings (hedgers' puts, speculators' calls) are rich, so the short leg sells expensive convexity. (2) Momentum: the long leg rides continuation. Framed as a relative-value spread: buy fair or cheap ATM vol, sell rich wing vol.

**Signals.** Skew = (ATM IV − 25Δ IV) / ATM IV per wing; **z-score ≤ −1.5** vs its own history (more negative = steeper). Momentum in the skew's direction: cross-sectional decile **≥8** (call-skew longs) or **≤3** (put-skew bears), time-series momentum sign, relative momentum vs S&P (>1 / <1). Liquidity ≥5k contracts/day (≥20k for easy fills). Strike check: short-leg IV ≫ RV; long-leg ATM IV ≈ or < RV.

**Trade.** Bullish: buy 45-60Δ call, sell 10-25Δ call. Bearish: mirror with puts. 10-20 DTE (video: 5-15). Payoff typically 5:1 to 10:1. Price several combinations and take the best reward/risk. Variant: a **1-3-2 ratio fly** (buy 1 ATM, sell 3 at 20-30Δ, buy 2 further; first strike gap = 2× second) for moderate momentum (decile 7-8 / 3-4); pays 20-30× at a pin but loses on overshoot. Size 0.5-2% per trade. Hold to just before expiry; take ≥90% of max early; let worthless spreads expire; **close before any earnings inside the life** unless you have an earnings view.

**Evidence.** A GBM simulation on AMC (7/22): +23% expected return on debit, **32% win rate**, and still ~breakeven at −50% annual drift. Member trades QUBT/SBET/MP/QS returned +160% to +400% (cherry-picked winners). Low win rate, expect long losing streaks.

**Our cross-check.** Maps directly onto Gabe's momentum universe (quantum, SPCX-type names) and our August vehicle study (put spreads cut loss 60-70% at equal risk but forfeit +5% winners; calls were the worst vehicle). Test idea: a 25Δ skew z-score panel from options_daily_v3 (greeks through ~2026-05) × our momentum ranks → 10-20 DTE vertical P&L with costs. Their momentum definitions are generic; our Minervini / RS stack could substitute.

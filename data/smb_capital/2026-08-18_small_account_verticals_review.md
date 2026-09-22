# Review: "How to Grow a Small Options Account (quickly)" (SMB Capital, Nick, 2026-08-18, KAapuE02EOw) — 2/5

Reviewed 2026-09-21. 13:38, public; ends with a pitch for SMB's free options workshop (optionsclass.com).
Transcript: `videos/education/2026-08-18_KAapuE02EOw/`.

## What it says

1. Small accounts fail from uncontrolled risk, not bad calls: protect capital first, don't size up because the
   account is small.
2. Vertical spreads = defined max loss and gain, capital-efficient, repeatable. Bull put 100/95 for $1: risk $400,
   break-even $99.
3. **Same delta ≠ same risk.** A 20Δ short put at 0 DTE is 47 SPX points out; at 29 DTE it's 302 points out
   (7100). Worked example, 10 contracts, 25-wide: 0 DTE gamma −1.81, down ~10% on a 10-point move; 30 DTE gamma −0.04
   (~40× less), down < 2% on the same move. So go further out in time to protect capital.
4. Capital efficiency lets a small account run many spreads across stocks, sectors and expiries: "more trades means
   probability has more room to work in your favor."
5. Four mistakes: too close to expiration, chasing premium near the money, strikes by feel instead of probability,
   treating high probability as certainty.

No track record, no backtest. The title says "quickly"; the content says the opposite (go slow, protect capital).

## Against our evidence

| Claim | Our evidence | Verdict |
|---|---|---|
| Define risk, size small, protect capital | Size-lever study: the lever is exclusion + fixed small size, not bigger bets; breakout book is bimodal and uncallable at entry → fixed small sizing | **Agrees** |
| Gamma: 0 DTE vs 30 DTE | Mechanically correct. But "down 10% vs 2% on a 10-point move" compares an instantaneous move; the 30-day spread is exposed to 30 days of moves (distance ∝ √T, which is why the same 20Δ sits 6× further out). Risk per unit of TIME isn't lower, it's spread out | **Correct but misleading** |
| "Probability works in your favor" with 20Δ credit spreads | Delta ≈ the risk-neutral probability, so an 80% win rate is priced in, not an edge (super bull call spread review: cost/width IS the probability). Paid-to-wait study: the generic put-spread rule was **−3.3% net**; it turned positive (+5.7%, 78% win) only with an IV ≥ 60th-percentile gate. SPY 10-DTE defined-risk selling +1.16%/trade but **negative when VIX < 20**; single-name 10-DTE selling net negative after costs | **Contradicted as stated**: win rate ≠ expectancy; an edge needs a gate |
| Many spreads across names = diversification | Our bull-put book: 3,377 spreads = **53 independent dates**; credit spreads fail together in a selloff | **Contradicted**: more trades ≠ more independent bets |
| Mistake 2, "chasing premium" near the money | Closer strikes collect more premium for more risk; both priced. Untested here | Neutral |

## Score: 2/5

Accurate mechanics and good risk hygiene (defined loss, small size, respect gamma near expiry), better than most
channel content. It loses points for presenting the credit spread's high win rate as an edge that "probability" will
deliver, and for the diversification claim, both of which our data contradicts, and for a clickbait title over a
workshop funnel. Nothing new to test.

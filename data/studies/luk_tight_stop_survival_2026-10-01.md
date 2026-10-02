# Luk-style tight-stop entries: survival and payoff (2026-10-01)

**Verdict: NULL (no edge), and tightly bounded.** At his entry, an intraday turn after a pullback into the rising
EMAs with a stop at the session low, the trade earns exactly its market exposure: **TIGHT minus BETA +0.003pp per
trade, t +0.02, over 13,410 entries on 473 dates.** The pre-registration's wording puts any result below the MDE
in the UNDERPOWERED bucket. Here the MDE is only 0.38pp per trade, so any edge larger than that is ruled out. Script
`run_luk_tight_stop_survival.py` (pre-registered 2026-09-30, amended before scoring 8837af6), ran on ECS Fargate in
2 minutes. Log `logs/luk_tight_stop_survival.log`, trades `logs/luk_tight_stop_survival_trades.csv`.

Sample: 674 liquid names passed the daily gate (ADR >= 4%, ADDV >= $100M, price above a rising 50/150 EMA stack),
620 produced entries, 2024-10-02 -> 2026-08-26. Median stop distance 1.10%, which is **0.17 ADR**, his kind of stop
(he states 1-2.5%, median 1.6%). The house disaster width, 1 ADR, is 5.6%.

## Results (net of 10 bp/side, entry-date cluster means)
| cell | mean | t | read |
|---|---|---|---|
| **PRIMARY: TIGHT - BETA** | **+0.003pp** | **+0.02** | halves +0.36 / -0.38, quarters positive 2/8 -> NOT MET |
| S1 TIGHT - RANDOM later minute (same stop %) | +0.10pp | +0.97 | the turn adds nothing over a random later minute |
| S2 TIGHT - WIDE (1 ADR stop) | -0.23pp | -1.60 | the tight stop costs a little per dollar, not significant |
| S3a QQQ gate ON - OFF | +0.27pp | +0.95 | standing aside in a weak tape: right sign, not significant |
| S3b his LONG weeks - SHORT weeks | -0.18pp | -0.96 | his own stance does not separate good weeks |

Raw per trade: TIGHT -0.005% (13% winners), WIDE +0.03% (31%), RANDOM +0.02%, BETA +0.23%. By year, TIGHT
+0.73 / +0.26 / -0.32% for 2024 / 2025 / 2026.

## Survival (descriptive)
- **59% are stopped the same day, 83% within 3 sessions, 86% eventually.** Median hold 0 sessions.
- R: median -1.0, mean +0.19. 5.3% of trades reach 5R and 3.1% reach 10R, but those tails do not cover the
  stop-outs plus costs.
- Re-entries after a same-day stop (10,896): net -0.20% per trade, 69% stopped again the same day. Trying again
  makes it worse.

## Account simulation (a simulation, not the test: 0.3% risk, position = min(0.3%/stop, 30%), 200% gross cap)
| | total 2024-10 -> 2026-09 | max drawdown |
|---|---|---|
| TIGHT, all days | +16.6% | -48.7% |
| WIDE, all days | +63.9% | -43.5% |
| TIGHT, QQQ gate ON only | +103.7% | -37.9% |
| WIDE, gate ON only | +73.0% | -26.9% |
The gated TIGHT book reaching +104% is the leverage arithmetic (25-30% positions, up to 200% gross) applied to a
strong tape on a survivor-biased universe. The per-trade test says the entries carry beta and nothing else (S3a
t 0.95), so that number is levered exposure, not an edge.

## Reading against the goal
- Look 2 of the picks test said his SELECTION at the close is level with ours (t -0.07). This test says his
  mechanical ENTRY and STOP add nothing beyond exposure either. Both components of the Luk method that can be coded
  have now been tested, and neither carries an edge.
- What remains is what no rule here captures: his discretionary choice of which pullback to take, sizing up on
  conviction, and his trailing and selling into strength. That is not testable from what we have, and his stated
  P&L cannot be verified.
- ⚠ Limits: one tape (2024-10 -> 2026-09), today's liquid universe (flatters levels, not arm differences), a
  mechanical reading of a discretionary entry, and no partial sales or trailing (both his, both discretionary).

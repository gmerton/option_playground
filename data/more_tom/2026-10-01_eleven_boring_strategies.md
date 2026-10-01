# Tom Sosnoff: "11 'Boring' Trading Strategies the Top 1% of Retail Traders Use"

- Video: https://www.youtube.com/watch?v=Z__VENA80Bo (channel `@SosnoffonMoney`, not the `@Lossdog` clip channel)
- Reviewed 2026-10-01 from auto-captions (3.4k words, scripted monologue). No backtest, no sample size, no P&L shown.
- **Score: 2/5. No new test.** Every rule with a number has already been tested here; the four untested
  structures are recombinations of tested legs, and the family as a whole is off-goal (small-positive premium
  selling, not the triple-digit target set 2026-09-30).

## Claim ledger

| # | His rule | Our evidence | Verdict |
|---|---|---|---|
| 1 | Short put 16-22d, 35-50 DTE, POP>80%, 50% take, beaten-down names, IVR>=30 | Single-name put = stock at delta minus costs (BCI FAIL); IVR selector CONTRADICTED (zivr t -1.25, TEST_INDEX "IV rank vs credit/width"); buying deep drawdowns in a healthy tape is vetoed (crash-leader study); index put: always-on 45-DTE 12d edge IS the stress regime (complement t 1.73) | CONTRADICTED (selection), partly AGREES (index, stress only) |
| 2 | Jade lizard (put + call spread, credit > call width), ~40 DTE | Not tested as named. Put leg = #1; call-spread leg = #6 | UNTESTED, legs answered |
| 3 | Covered call 25-30d, 40-60 DTE, cheap high-IV stocks | BCI covered calls / CSPs vs stock at same delta: FAIL | CONTRADICTED |
| 4 | Short put spread, credit 30-35% of width | OptionsPlay spec vs delta-matched stock -2.68pp (t -2.21); credit/width as a RANKING passes (borderline) | CONTRADICTED as a strategy; cw ranking AGREES |
| 5 | Put ratio 1x2 for a credit | Not tested. Naked-put tail with a debit long; same bet as #1 | UNTESTED, no new axis |
| 6 | Short call spreads "trade rich because of call skew" | Equity skew is put-side; ETF bear calls/condor call side FAIL (t 0.6); UVXY bear call FAIL after costs | CONTRADICTED |
| 7 | Broken-wing butterfly (calls) for a credit | Not tested | UNTESTED |
| 8 | Unbalanced condor (wider call side) | Not tested; rests on claim 6 | UNTESTED, premise contradicted |
| 9 | Iron condor, 30-40% of width, high IVR | ETF condor +0.36%/trade t 0.6; IVR NULL | CONTRADICTED |
| 10 | 16-20d short strangle, 45 DTE, 50% take, roll untested side ("#1, >70% of profits") | SPY strangle vs short put EQUIVALENT, leans worse (t -1.74); 21-DTE management PASS RETRACTED (t -2.42); single-name hold +$0.23/share | NOT BETTER than a short put |
| 11 | Vol mean-reverts, price does not; prefer short vol | VRP panel +1.75vp t 8.93, 17/17 yrs | AGREES (already in hand) |

## What it adds
Nothing testable that is new. The one factual premise that would justify claims 6-8 (calls trade rich vs
puts) is backwards for equities. The 70% attribution is self-reported and unauditable.

# OptionsPlay — "What Volatility Is Actually Telling You" (Tony Zhang, 2026-09-11, 56 min)

_Reviewed 2026-09-22. Growth Lab week 3 of 4. Webinar + platform demo + Q&A. Transcript in this folder._

## Verdict: 2.5 / 5

The **descriptive** half is correct and matches our own measurements — this is the clearest short statement of the
variance risk premium and vol mean-reversion I have reviewed here. The **prescriptive** half is the usual retail
gap: every rule is argued at the mid, with no cost model, no test statistic, no sample, and no control. One of its
headline recommendations (express a directional view as a debit spread rather than an outright option) is
**contradicted by our own test at real fills**. It is also, structurally, an ad: the strike selection, the
"OptionsPlay score" and the strategy matrix all resolve to "the platform already does this for you".

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 04:26 | Implied vol has exceeded realised since 1990 (ex-2008) — the variance risk premium | ✅ **Reproduced.** Our VRP panel: 10-day premium **+1.75 vol points, t 8.93, 17/17 years**; single-name +4.13vp. He states it correctly and without exaggeration |
| 05:57 | "Therefore there is a statistical edge in selling premium over buying" | ⚠ **The gap is real, the edge often isn't.** At MID yes; at fills frequently not: earnings vol premium +0.601% at mid → **−0.428% at the bid** (costs 171% of gross); short-dated single-name selling FAIL (costs 136% of gross); BCI cash-secured puts = stock at the same delta minus costs. 2026-09-22: 13 of our own screener spreads went from +3.8…+13.4% gross to −5.1…+5.9% net, **0 of 13 significant**. He never mentions the spread |
| 07:37 | Vol is mean-reverting; extremes are the opportunity | ✅ Consistent with our straddle gate: **IV percentile ≤30 is what carries the long straddle** (both gates +4.14%/trade vs +1.3% for the FVR-only superset) |
| 11:49 | VIX spikes mark market bottoms; he calls the prior day's low a bottom | ⚠ **Narrative, one episode, no test.** Our index-timing work (FTD as a regime switch) is NULL, and nothing we tested forecasts the paying months. Note the mechanism he skips: our GEX study shows negative dealer gamma = +8% realised vol beyond VIX (t 7.7) — the vol spike is often the *cause*, not a bottom signal |
| 14:08 | The CBOE skew index reads where directional demand is (95th pct into FOMC = crash protection bid) | **Untested here.** We compute 25-delta skew in the credit-spread finder but never tested it as a signal; the one adjacent test, oquants' momentum-skew verticals, FAILED. Testable and cheap |
| 19:51 | IV rank as the single-stock VIX; **33 = the cheap/rich line**, 25–35 = no-edge band | ✅ Same neighbourhood as our own gate (IV percentile ≤30). He is honest that the threshold is not science |
| 32:11 | **The matrix:** bullish + low IV → debit call spread · bullish + high IV → put credit spread · bearish + low IV → debit put spread · bearish + high IV → call credit spread | **Mixed, and the two we tested go against him.** Bullish + high IV → put credit spread is our ONE certified equity-option cell — but only after a selloff (SPY bull put bearish-high-IV t 6.07, SPX condor t 5.21); the bullish-**low**-IV version is −4.8% month-weighted (t −0.87). Bearish + high IV → **call credit spread: the ETF condor call side FAIL, and 2026-09-22 UVXY (−3.5%/trade, t −2.65) and UVIX (−8.8%, t −2.81) are exactly this trade, net-negative.** Bullish + low IV → debit call spread: our August vehicle study ranked the 30Δ/15Δ debit call spread the **worst** vehicle risk-equalised |
| 33:20 | Pick strikes by delta/probability, not by a fixed % OTM, for consistency across vol regimes | ✅ Mechanically right — a delta-constant rule holds the assignment rate steady where a fixed-% rule does not. It is a **variance** argument, not an edge argument, and he presents it as both |
| 38:25 | **The 110/95 put spread costs $536 vs $640 outright → 180% vs 135% return if right, so prefer the spread** | ❌ **Contradicted at real fills.** Our event-convexity spread test: capping costs only −2.0pp (t −0.45, the cap binds 1.7% of the time) but the second leg's **friction costs −27.1pp (t −5.51)**. He compares two mid prices; the short wing is the cheapest-to-quote, widest-relative-spread leg in the structure. His own arithmetic also flatters the spread by quoting % return on a smaller base |
| 40:18 | Buying the 220 wing cuts risk from $20k to $1.5k "without spending much" | Trivially true (that is what defining risk means) and fine, but the framing hides that the credit shrinks too; ROC, not risk, is the comparison |
| 50:02 | Diagonals: buy a ~70Δ 60–90 DTE call, sell short-dated premium against it, roll | **Untested by us for stocks.** Our calendar/diagonal path study found no edge on ETFs and −8 to −18% on stocks; Ravish's double diagonal is the one variant that tested better than its double calendar |
| 47:19 | An OptionsPlay **MCP server** is in UAT, production "in coming weeks" — screener, trend, strategy selection | Worth a look when it ships, with the TradingView lesson applied: that one is a research layer only (no chains, no L2), and its news cap made it useless for backtests |

## What I would take

1. **Nothing to adopt.** Everything correct here we already measure directly (VRP panel, IV-percentile gate), and we
   measure it better, because we price the spread.
2. **One framing worth borrowing:** "if you buy options you are fighting a headwind, so be selective." That is the
   honest version of our own finding that the long straddle only works behind the IV-percentile gate.
3. **The contrast is instructive:** his whole session would rank strategies by expected value at mid. Our 2026-09-22
   sweep is the counterexample — *the spread, not the signal, decided 13 of 13 outcomes*, and it is the reason the
   screener's filler layer got retired.

## Tests run 2026-09-22 (both from this video)

- **Skew as a signal (@14:08): NULL.** `run_skew_signal.py`, SPY 25-delta skew at ~30 DTE, 1,796 sessions.
  Forward 21d Q5−Q1 +1.72% (NW t 1.44); 10d and 5d weaker; forward realised vol +8.2pp (t 2.06) but +15.7 / +1.0
  across halves, and skew adds **nothing** beyond the VIX level in a joint regression (t 1.23 return / −1.22 vol,
  vs vix_pct t +6.54). His "95th-percentile skew into FOMC" reading is interpretation, not signal.
- **IV rank as a vehicle chooser (@32:11): NULL for his flip.** `run_ivrank_vehicle.py`, 4,742 paired entries on
  18 liquid names at real fills. The flip has the right sign but t 0.68 (DiD +15.4pp bullish, halves +38.3 / +8.3).
  Sideways finding: per dollar at risk the call debit spread beat the put credit spread in *every* IV-rank tercile
  in this 2019–26 bull sample — which is not his rule either, and cuts against our own "calls are the worst
  vehicle" note (that one was dollar-equalised, mid-priced, n 93).
- ⚠ Both runs re-taught the same lesson: the first vehicle run printed −38% on bull puts because panel closes are
  split-adjusted while v3 strikes are raw. Spot is now recovered from the chain (delta → d1 → S).

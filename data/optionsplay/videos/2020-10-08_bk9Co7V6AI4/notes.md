# OptionsPlay: "Finding the Optimal Credit Spreads" (Tony Zhang, 2020-10-08, 73 min)

_Reviewed 2026-09-24. Members' education webinar, about 45 min of slides and then a live demo of the Credit Spread
Opportunity Report, followed by Q&A. Transcript in this folder (auto `en-orig`)._

## Verdict: 3 / 5. This is where the credit/width ranker comes from, but the rule he gives is not the rule we tested

This is the earliest full statement of the OptionsPlay credit-spread process: filter for liquidity, require credit
≥ 1/3 of the width, align with a directional signal, then sort by credit/width. The part we tested
(`run_premium_to_width.py`) holds up on our data. It is only one piece of his rule, though, applied to a different
structure. His other pieces fare worse. The IV-rank advice and the 2×-credit stop are both contradicted by our
fills, and the "backtesting" he mentions three times is never shown: no n, no costs, no t. Orders are worked from the
mid (53:00, 68:03). That scores lower than the 2026-07-25 video (3.5), which is the same filter with the bad parts
removed.

## His selection rule (36:01–39:00, 28:02–31:01)

1. **Liquidity first.** Of about 4,200 optionable names, 100–200 a day pass; "filter out 95% of the names through
   liquidity".
2. **Credit ≥ 33% of width** as a hard floor ("never risk more than two to one"). With his structure he usually
   gets **~40%**.
3. **Directional signal**: a reversal, meaning support/resistance, overbought/oversold on RSI or CCI, or a range.
   A bullish signal means a bull put; a bearish signal means a bear call.
4. **Sort by credit/width**, top of the list first. IV rank and next-earnings date are shown as side columns.
5. **Structure: sell the 50Δ (ATM), buy the 25Δ, ~45 DTE** (±7 days). His contrast is with Sosnoff's 35Δ/20Δ
   (quoted as 35/25 at 29:01).
6. **Exits, whichever comes first:** 50% of max gain; a loss of 100% of the credit (spread worth 2× the credit);
   or 21 DTE. Roll winners at 21 DTE and never roll losers.

## Does his 2020 ranker match the rule we tested? Partly. It shares the sort variable and differs on four axes

| axis | his 2020 rule | `run_premium_to_width.py` (ARM A) | consequence |
|---|---|---|---|
| sort variable | credit / width | credit / width, at a real fill (short bid − long ask − commissions) | **same**. Ours is stricter because his is read at the mid |
| **how it is applied** | **absolute floor ≥ 0.33**, then sort | **relative quintiles** within a fixed structure | ⚠ **At 30Δ/20Δ his floor is almost never reachable.** From the primary CSV: ARM A credit/width median ≈ 0.20, top-quintile mean 0.252, and **only 5 of 7,019 spreads (0.07%) reach 0.33**. Across all 27,404 spreads the 99th percentile is 0.284. His floor was set for a near-ATM short. At our geometry it would reject the whole test sample, including the top quintile that earned +4.07% |
| **short strike** | **50Δ (ATM)**, long 25Δ, net ~25Δ | 30Δ short, 20Δ long, net ~10Δ | a different structure, about 2.5× more directional |
| tenor | ~45 DTE | expiry nearest 30 DTE (the cache only holds 25–40 DTE) | different |
| exit | 50% take / 2×-credit stop / 21 DTE | held to expiry | different, and our ledger rejects his stop (see below) |
| direction gate | technical reversal, bull puts **and** bear calls | none, bull puts only, 20 liquid names | the call side is untested at cw; on ETFs the call side FAILs |

**So the tested rule is the cross-sectional cw sort, not his rule.** The quintile sort works (top − bottom +8.57pp,
month-clustered t 3.74; I recomputed +8.54pp, t 3.73 from the CSV). Its mechanism is geometry-independent: it ranks
names by how rich their options are (entry IV 0.25 → 0.48 across quintiles). There is therefore a reasonable prior
that it transfers to his 50Δ/25Δ structure. **The piece that is NOT tested is his absolute 0.33 floor at an ATM
short,** together with whether the 50Δ/25Δ geometry is better or worse than 30Δ/20Δ after costs. That is a new
axis (see the test candidate below). **His exit rule is not new.** It is already answered, and against him.

## Claims against our ledger

| @ | Claim | Tag | Our evidence (source) |
|---|---|---|---|
| 05:01–08:01 | Delta, not vega, is the biggest exposure; IV level should not decide credit-vs-debit alone | **AGREES** | The cw play loses to **delta-matched stock by −2.43pp** (TEST_INDEX §1 cw-play row, `cw_play_2026-09-22.csv`): the put spread is stock exposure with the upside cut off. His framing is right, and it cuts harder than he lets it |
| 14:01–16:00, 19:02 | Credit as a % of width is the thing to maximise, because every cent of credit is a cent less risk | **PARTIAL** | Across names ✅: `premium_to_width_2026-09-22.csv` ARM A Q1 −2.91% → Q5 +4.07% net ROC. **Within a name ❌**: ARM B (same name-date, only the wing moves) is non-monotone, and wings wider than 0.20Δ are flat (+2.66 / +3.10 / +2.98 for the 0.20 / 0.15 / 0.10Δ wing; narrowest 0.25Δ wing −0.04%). Maximising cw by choosing your own strikes buys nothing. It only informs when it varies across names |
| 22:01 | IV rank > 30 is high, > 50 extreme; > 50 "has a much higher probability of better returns" | **CONTRADICTED** | `ivrank_vs_cw_2026-09-22.md` l.28–29: joint fit zivr **−1.89pp (t −1.25)**, within-date +0.25 (t 0.22); IV-rank quintiles non-monotone and backwards (the lowest ivr earned most). cw wins in the same regression (t 2.81 / within-date 4.01). Doctrine scorecard C1 |
| 22:01–23:00 | Sell credit spreads at reversal points (overbought/oversold, S/R) | **PARTIAL** | Bull-put side: `rsi_conditioning_study_2026-09-16.md` §A, 20 ETFs 45 DTE: RSI<40 +3.88pp pooled (t 2.21) → **+1.21pp controlling for VIX (t 0.69)**, and **−0.23pp within-week**. "Oversold" is a VIX proxy. The certified index cell (bearish-high-IV SPY bull put, t 6.07) is the stress-state version. Bear-call side: ETF call side FAIL (TEST_INDEX §1, `etf_condor_call_side_2026-09-16.md`) |
| 28:02 | "The difference in performance between each [credit-spread choice] is generally relatively low" | **AGREES within a name** | ARM B: realised win rate tracks the break-even win rate within 0.5–3pp; flat past the 0.20Δ wing. Sosnoff says the same (doctrine rule 15, PARTIAL: wrong across names) |
| 29:01 / 61:00 | Sell 50Δ / buy 25Δ at 45 DTE; ~67% POP, ~40% of width | **UNTESTED** at this geometry | The chain cache behind ARM A holds only 0.10–0.40Δ and 25–40 DTE (`ivrank_vehicle_chains.parquet`), so a new pull is needed. The nearest index evidence is QQQ bullish-low-IV 0.45/0.35, **−4.8% month-weighted, t −0.87** (TEST_INDEX §0 Tier A/B) |
| 30:01 | Collect at least 1/3 of the width | **UNTESTED as a floor** | See the table above: 0.07% of our 30/20 sample clears it |
| 31:01–34:00 | Exit at 50% of max gain, **or a loss equal to the credit (spread at 2×)**, or 21 DTE | **CONTRADICTED on the stop, NULL on the take at real fills (was AGREES), 21-DTE AGREES on risk only (NULL on return, leaning INVERTED)** | `etf_put_spread_study.md` §2: 50% take **bundled with the 2× stop = −4.3%/trade (t −5.4)**, negative in both halves. `etf_put_spread_exit_rule_2026-09-16.md`: 50% take with no stop = **+5.70%/trade, monthly t 3.13** (after the ceiling-filter erratum) ⚠ *corrected 2026-09-24: the +5.70% was GROSS and came from `options_cache`, which drops zero-bid quotes and so flatters take-profit fills. On unfiltered v3 at house fills the 50% take is **−2.78%/trade** (hold −1.37%); take − hold −1.42pp, t −1.77 → NULL (`putspread_exit_capital_time_2026-09-24.md`)*. The stop is what destroys it. (⚠ The certified SPX condor does run a 50%/2× rule, t 5.21, but with no stop/no-stop comparison on file; the certified SPY bull put runs no stop.) 21 DTE: the §1 21-DTE row was re-run 2026-09-24 (FIX-1, the original dropped worthless-expiry winners): on 45-DTE 20Δ strangles 21-DTE close − hold **−$0.52/share, month-clustered t −2.42** (halves −0.63/−0.40; hold +$0.23, 74% win; 21-DTE −$0.29, 64% win) → PASS: NO; it cuts risk only (sd $9.33 vs $17.09, worst −$291 vs −$617) |
| 34:00 | Never roll a loser; roll winners at 21 DTE | **UNTESTED** for spreads | Adjacent: the straddle "roll at −50%" row, where 69.8% of breaches were better held (TEST_INDEX §2) |
| 35:00 | Gamma risk outweighs theta in the last 2–3 weeks | **PARTIAL** (true of risk, not return) | Re-run 2026-09-24 (FIX-1): exiting at 21 DTE cuts the tail (sd $9.33 vs $17.09, worst −$291 vs −$617) but earns less than holding through the last 3 weeks (−$0.52/share, t −2.42). Note that the certified SPY bull put is **entered at 20 DTE** (50% take, no stop, t 6.07), i.e. entirely inside the window he says to avoid. That argues against the rule as a universal one |
| 39:00 | Avoid selling into earnings | **AGREES in direction** | Earnings vol premium +0.601% at mid, **−0.428% at the bid** (TEST_INDEX §9) |
| 40:02 | Don't use the report after hours: spreads widen, "funky premiums that are not executable" | **AGREES** | The same reason we price at the bid/ask: 13 of 13 screener spreads collapsed gross → net on 2026-09-22 (TEST_INDEX §1 Tier C row) |
| 57:02 | Delta is "crazy accurate" as a probability of expiring ITM (backtested to 2007) | **PARTIAL** | Close but biased, and the bias is the premium: realised vol beats implied only 25% (10d) / 29% (30d) of the time (doctrine rule 12, `vrp_panel_study.md`). A 30Δ put expires ITM less often than 30% |
| 64:01–67:02 | Far-OTM 98–99% POP spreads are "picking up pennies in front of a freight train" | **AGREES** | Doctrine rule 14 (POP is a dial, not an edge). The cw quintiles' win rate *falls* 79.6 → 75.7% as net ROC rises |
| 68:03 | Weeklies are as liquid as monthlies; low OI ≠ illiquid; fill at mid | **PARTIAL** | OI is not a signal (doctrine rule 7, AGREES). "Fill at the mid" is not our model: the house model assumes 25% of the quoted spread, and the cw test sold at the bid and bought at the ask |

## Discrepancies found in our own docs (primary artefacts checked 2026-09-24)

1. ⚠ **TEST_INDEX §1 (premium-to-width row) says "PASS (borderline)", but the script's own pre-registration says NO.**
   `run_premium_to_width.py` l.24–26 pre-registers PASS as *ARM A t ≥ 2 with both halves agreeing* **AND** *ARM B net
   ROC monotone in credit/width*. ARM B is not monotone (0.10Δ +2.98 / 0.15Δ +3.10 / 0.20Δ +2.66 / 0.25Δ −0.04). So
   the script prints "PRE-REGISTERED PASS: NO → risk coordinate". The ledger reports ARM A as the pass and ARM B as a
   caveat. The reading is defensible, since ARM B tests a different question (within-name dialling), but it is a
   post-hoc re-scoping of a pre-registered conjunction and should say so.
2. The script docstring says "18-name … 2019-10 → 2026-01". The CSV has **20 names, 2018-01-05 → 2026-01-23**, which
   matches the TEST_INDEX row. The docstring is stale.
3. **The within-date figure (+7.64pp, t 4.15) is not produced by `run_premium_to_width.py`.** The script has no
   within-date step, and there is no log. Two reconstructions from the CSV bracket it: within-date cw rank top vs
   bottom 20% = +8.32pp (t 4.50); date-demeaned ROC on pooled quintiles = +5.61pp (t 2.67). The sign and
   significance are robust, but the exact number has no primary artefact. The independent replication in
   `ivrank_vs_cw_2026-09-22.md` (within-date zcw t +4.01) is the citable one.
4. Rounding: Q1 net ROC is −2.91% from the CSV vs −2.96% published, and top − bottom is +8.54 (t 3.73) vs +8.57
   (t 3.74). Immaterial.

## What's new / test candidates

1. **NEW: credit/width at his own geometry, 50Δ/25Δ ~45 DTE, with his absolute 0.33 floor.** Nothing in TEST_INDEX
   touches it. Every cw row (premium-to-width, cw rescue, cw play, cw on certified, ivrank vs cw) is 30Δ/20Δ or
   index 25Δ/15Δ, ~30 DTE, held to expiry. Question: on the same 20 names and Fridays, does (a) the cw quintile sort
   replicate at 50Δ/25Δ, and (b) does "cw ≥ 0.33" add anything beyond the rank? Primary: the top − bottom quintile at
   50/25, month-clustered, both halves. **Control: delta-matched stock.** At net ~25Δ it matters even more than at
   30/20, where the play already lost −2.43pp to its delta. Hold to expiry and add a 50%-take/no-stop arm; do not
   test his 2× stop, which is already answered. Prior: (a) replicates, because the mechanism is entry IV; (b) is
   nothing beyond rank. The likely finding is that ATM geometry is more beta and more friction for the same
   ranking. ⚠ It needs a new v3 chain pull (0.20–0.55Δ, 38–52 DTE), which is an Athena job, so **ask Gabe before
   running it**.
2. **Not new, don't re-test:** IV rank as a sort (ivrank-vs-cw row), oversold entry (RSI row, a VIX proxy), the
   2×-credit stop (ETF put-spread rows), POP (doctrine rule 14), earnings avoidance (§9).
3. **Answered, not new:** the 21-DTE leg of his exit — [FIX-1] done 2026-09-24: risk reducer only, NULL/leaning INVERTED on return (TEST_INDEX §1).

## ✅ Test run 2026-09-24: NULL, negative sign
`run_optionsplay_spec.py` → [`optionsplay_spec_2026-09-24.md`](../../../studies/optionsplay_spec_2026-09-24.md). His exact spec (50Δ/25Δ, ~45 DTE, cw ≥ 0.33) earns +9.45% on capital but **−2.68pp vs the stock held at the same net delta (month-weighted t −2.21)**, negative in 7 of 8 years. The floor and the quintile sort select high-beta names; the option structure adds nothing.

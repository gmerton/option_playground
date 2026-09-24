# OptionsPlay — "How to Trade Credit Spreads After Earnings" (Brian Overby, 2026-02-15, 30 min)

_Reviewed 2026-09-24. Growth Lab session, presented by **Brian Overby** (senior strategist; not Tony Zhang). Platform demo
plus two Q&A answers, and the rest of the Q&A is members-only. Three worked trades (BRK.B, JPM, TER), all
priced at the **mid**. No backtest, no win rate, no sample and no statistic. Transcript in this folder._

## Verdict: 2 / 5

He inherits the one good OptionsPlay rule, **credit ≥ ~33% of width** (the filter behind our 3.5/5 review,
[YfrZT_kTo_4](../2026-07-25_YfrZT_kTo_4/notes.md)). What the title adds is **timing**: sell the bull put only
**after** the print, on a name at or near highs that "had a solid report and sold off a bit". That timing half
is **contradicted twice by our ledger**. Selling **through** earnings earned more, not less, and buying the
post-earnings dip in a good reporter is no better than a random entry in the same name that month. There is also
a structural conflict he doesn't see: the print is when the name's IV collapses, so "sell after earnings" means
selling the name's cheapest premium, which is the low-credit/width bucket that his own rule rejects. In the demo
he applies that rule loosely, taking 28–32% as "close enough", and quotes 40% on a ~26Δ leg, which cannot be
filled at a real price (see the 06:31 row).

**His selection rule in one line:** a platform trend-following momentum signal (CCI "dip in a bullish trend",
counter-trend names dropped) → a name that has just reported, ideally near a 52-week high after a small post-print
selloff → a high-IV name ("not utilities") → a ~45-DTE bull put with its expiry **before the next print**, short
leg near the money with a ~22Δ target, and credit ≥ ~33% of width at the mid. Otherwise, switch to a bull call debit spread.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 01:03 / 02:52 / 04:23 | **Sell credit spreads after the print, not through it**; the event is the risk, and after it "you have a little bit more predictability" | ❌ **CONTRADICTED as a return claim.** BCI test of exactly this rule on short puts (`bci_csp_study_2026-09-17.md` §3, 326 names, 2018–26, real bid/ask): 0.30Δ weeklies with **earnings in the window +0.26% vs +0.05% earnings-clear**. Within-week, the through-earnings sellers earned **+0.19pp, t +3.6**, and the monthly tenor agrees in sign (t +2.3). This is not beyond direction (excess t +1.3), and the tail is worse (worst 1% −22.3% vs −17.8%). So **avoiding the print is a risk preference, not an edge**. ⚠ That was tested on naked puts, not on spreads |
| 03:12 | Don't sell spreads on low-IV names (utilities), because "you don't get anything" | ✅ **AGREES, in the cross-sectional form.** At a fixed 30Δ/20Δ, the cheapest credit/width quintile loses **−2.96% net**, and the richest quintile makes **+4.07%** (top−bottom +8.57pp, t 3.74; within-date +7.64pp, t 4.15), with entry IV rising 0.25 → 0.48 across the quintiles (`premium_to_width_2026-09-22.csv`, TEST_INDEX row 277). ⚠ Not in the IV-rank form: IV rank per name is NULL (zivr −1.89pp, t −1.25, `ivrank_vs_cw_2026-09-22.md`) |
| 03:12 vs 01:03 (implicit) | Sell after earnings **and** want high IV | ⚠ **Internally inconsistent, by our own measurements.** Single-name **front-expiry** ATM IV rises **+40 to +57 vol points** into the print (smaller at a 45-DTE tenor, which we have not measured) (`earnings_ramp_2026-09-20.md`), and that ramp is what collapses on the print. The session after earnings is structurally the name's **low-IV** state. So his timing rule steers him into the bucket his premium rule rejects. His own demo shows this: BRK.B fails the 33% floor (26%, 30%), and TER passes only after a fresh post-print selloff |
| 04:37–04:55 | 45 DTE by default. Go to ~30 DTE when that is what keeps the expiry before the next print | **UNTESTED as a tenor choice.** Our credit/width test is ~28 DTE and the ETF bull put roster is 45 DTE. We have not compared the two on single names. The earnings-clear half is the BCI row above |
| 06:31–06:51 | **"Tony's rule": credit ≥ ~33% of width, ~40% is good, 50% is rare** | ✅ **The ranking PASSES** (row 277, above; borderline under the ledger correction, SUPPORTED not CONFIRMED). ⚠ **The floor, used as a hard rule at his ~22Δ, rejects almost everything at a real fill.** At a 0.30Δ short leg, real-fill credit/width is **≥ 0.33 on 0.07% of 30Δ/20Δ spreads** (median 0.20, 99th percentile 0.28), and at most 0.19% at any wing (`premium_to_width_2026-09-22.csv`, 27,404 spreads). At fair prices credit/width is bounded by roughly the short leg's ITM probability, so a 33% credit needs a short near the money (his BRK.B 500 short) or a quote at the **mid of a wide market**. The rule works as a **cross-sectional rank**, which is how we adopted it. As a fixed floor it acts as a filter on how wide the market's spreads are |
| 08:57–09:40 | Start from the platform's CCI trend-following signals. Drop counter-trend ("falling knives") and illiquid names | Liquidity: ✅ AGREES (our biggest cost finding. Spread predicts outcomes, R² 0.153 vs 0.027 for premium). The CCI signal itself is untested. It belongs to the pullback-in-uptrend family, which FAILS vs the breakout on daily bars (`pullback_entry_study_2026-09-17.md`, +1.2–2.4%/trade, t ≤ 1.4). A directional signal alone does not rescue the structure: the bullish-low-IV bull put is −4.8% month-weighted (t −0.87) |
| 15:51–18:11 | **"Earnings beat" watch list: a strong report, but the stock sold off a bit** → a bullish setup | ❌ **NULL on our data.** The good-reaction drift entry is +0.27R vs a same-name control of +0.25R (edge +0.02). The delayed-bump version is **−0.47R vs control** (`delayed_earnings_2026-09-18.md`). The catalyst-gated retrace entry is also NULL: DR-EP −0.067R (t 0.21), which is worse than the same rule with no catalyst gate (`drep_catalyst_retrace_2026-09-22.md`). Post-print names are no better than a random entry in the same name that month |
| 21:38–22:32 | TER: new high, pulled back, 20/50/200 MAs stacked → sell a bull put | Same family as the row above. Our selection side is fine ("we select well"), but a pullback entry on a leader is worse than the breakout entry. Also, at 40% of width on a "26 delta" (24:17) he is either quoting the long leg's delta or quoting a mid inside a wide market. He says so himself at 25:08 |
| 12:54–15:47 | BRK.B fails the 33% floor, so **switch to a bull call debit spread** (~1:2 risk:reward) | **PARTIAL.** A credit/width-driven vehicle switch was not tested as such. Its nearest relative, IV rank as the vehicle chooser, is **NULL** (t 0.68, `run_ivrank_vehicle.py`). Per dollar at risk, the call debit spread beat the put credit spread in every IV-rank tercile (2019–26 bull sample), and it beats delta-matched stock by +$97/contract (t 2.29, not adopted). So the switch doesn't hurt, but nothing shows it helps |
| 25:08–25:48 | Work the **mid**; a spread gives the market maker their hedge, **"so you should get that benefit"**, i.e. fills near the mid | **UNTESTED, and it is the assumption his whole demo rests on.** Our cost model charges **25% of each leg's quoted bid-ask**, and that figure was **copied from one study, never calibrated** (`src/lib/studies/costs.py` docstring). The credit/width test was more pessimistic still: it paid the full spread (short bid − long ask). No study has measured whether multi-leg orders actually fill closer to the mid than the per-leg charge assumes. See test candidate 1 |
| 27:25–28:21 | Deltas differ across platforms by model, so don't over-read 63 vs 69 | ✅ Fair. For us, this is the RAW-vs-adjusted spot problem: recover spot from the chain before trusting a delta (`src/lib/studies/chain_spot.py`) |

## What's new / test candidates

1. **⭐ Calibrate the slippage assumption from real multi-leg fills (METHOD, cost realism, new axis).** His whole
   demo assumes spreads fill near the mid. Our model charges 25% of each leg's bid-ask, and that number has never been checked. The
   question is whether Gabe's actual IBKR multi-leg option fills (Flex confirms, query 1415008), compared with the
   NBBO mid of both legs at `trade_datetime` (Tradier intraday), land nearer the mid than 25%-per-leg. The journal
   is **admissible for cost realism**, which is exactly this use, and never for selection. This is a small local job:
   Flex data is already pulled, plus one Tradier quote lookup per fill. It moves every net number in the ledger in one direction,
   so it matters more than any single strategy test. ⚠ Check first that nothing under `lib/journal/` already
   computes fill-vs-mid. I found no study doc that does.
2. **Post-earnings timing on the credit/width bull put (new axis, a zero-pull re-cut).** Tag each of the 15
   single names' spreads in `premium_to_width_2026-09-22.csv` using `data/cache/earnings_yf.parquet`: (a) a print
   inside entry→expiry, (b) entry 1–10 sessions after a print with none inside, (c) everything else. Compare net
   ROC **within credit/width quintile**, so that we test the **timing** and not the IV level. The BCI row answers
   "through vs clear" for naked puts only. This asks whether his after-the-print window is a better or worse place
   to sell the **spread** at the same richness. It is not the §10 row 348 "post-news put spread under the gap low"
   (unscheduled news, 7–20 DTE). Pre-register before running. Low prior: the IV crush predicts (b) sits in
   low-cw quintiles, and the within-quintile comparison is what separates the two.
3. **Nothing else.** The post-print dip entry is answered by `delayed_earnings` / DR-EP (NULL), IV rank by
   `ivrank_vs_cw` (NULL), and the 33% rule by row 277 (PASS as a rank).

## Discrepancies found in our own docs while checking

- **TEST_INDEX §10 row 347** ("Post-catalyst entry: first flag / first pullback") still reads **"queued"**, but
  the memory catalyst queue and row 144 (DR-EP, 2026-09-22) record the post-catalyst entry as **CLOSED, NULL**.
  DR-EP tested the (a) arm (first close above the post-catalyst high after a give-back). The (b) arm (first close
  near the rising 10/21 EMA) is only covered indirectly, by the pullback-entry FAIL. Mark (a) done and decide whether (b) is still open.
- **`run_premium_to_width.py` docstring** says "18-name ... 2019-10 → 2026-01". The output CSV actually has **20
  names, 2018-01-05 → 2026-01-23, 395 Fridays**. TEST_INDEX row 277 (20 names, 395 Fridays) matches the CSV, so the docstring is the stale one.

# OptionsPlay: "How to Screen Both Legs of the Wheel Before You Trade" (Tony Zhang, 2026-08-01, 45 min)

_Reviewed 2026-09-24. Growth Lab week 4 of 4. About 40 minutes of platform demo and no Q&A (members only). Transcript in this folder._

## Verdict: 2 / 5. The wheel sold as "a limit order that pays you", and our ledger already has the answer

The selection rule is simple and stated clearly: **pick a watchlist (undervalued / outperformers / earnings / your
own), then rank the platform's short-put ideas by annualised yield and take the top names you would be happy to
own.** Strikes sit near the money on purpose ("you want a high probability of acquiring the shares"), about 29
days out. The covered-call leg does the same thing, restricted to names you already hold.

Every number is a headline yield at the quoted price (mid, or the platform's price). There are no costs, no
assignment rate, no sample and no benchmark. The central framing, "same obligation as a limit order, but you get
paid", is the claim our BCI study tested directly. It **fails**: the payment is the price of the left tail you
give up, and after costs you keep less than the stock at the same delta would have earned.

## His selection rule, and the claims

| @ | Claim | Our evidence |
|---|---|---|
| 07:38 | **Median annualised CSP yield on his ~800-name screen is 56%.** Covered calls about 10% | ❌ **Headline yield is not return.** BCI study, 326 names, 2018 to 2026-02, real fills (mid minus a quarter of the spread): the weekly put **collects 0.74%/wk and keeps +0.03%/trade**. Assignments (22% of weeks) and the tail take the rest. As a compounded book it returns **+1.2% CAGR, versus +10.5% for SPY** (`data/studies/bci_csp_study_2026-09-17.md` §1). Annualising a 29-day yield is the error he warns against at 19:00 and then quotes anyway |
| 21:23–22:30 | **A CSP has the same obligations as a limit order, but pays you.** Use it instead of limit orders | ❌ **Contradicted.** The limit order has no cap on the upside and the put does. On like-for-like exposure the put **loses to the stock at the same delta** at every tenor and strike: W 0.30Δ excess **−0.06% (t −1.8)**, M 0.30Δ **−0.20% (t −1.4)**, and **t −4.2 at bid fills** (bci §1). A follow-up (`csp_vs_stopped_stock_2026-09-23.md`, 201,849 trades) finds that **the unstopped stock at the same delta beats the put** on return (+0.49 vs +0.36) and on the tail (worst 1% −16.9 vs −41.0). On risk the put is the worst of the arms. It takes no position on whether a limit order beats a market order |
| 11:49, 17:54 | Sell puts only on stocks you want to own. Screen with the "outperformers" or "undervalued" watchlist | ⚠ **A preference, not an edge.** Our mechanical version of a trend + relative-strength screen (BCI: EMA trend, MACD, stochastic, 63-day return beats SPY, IV 30–60%, earnings clear) **adds nothing**: within-week put −0.03 (t −0.5), excess −0.00 (t −0.1). Monthly it is worse: worst 1% −51% vs −39%, and −1.3%/trade in 2022 while the pool made +0.15%. Momentum screens concentrate the book in the names that fall hardest when the market de-rates (bci §2). Down-day RS as a selection filter is **INVERTED**, −3.51pp at 63d, t −3.33 (TEST_INDEX §4) |
| 14:14, 26:02 | **Rank candidates by annualised yield**, and go down the list from the top | **UNTESTED in this form, but see the next section.** At a fixed near-ATM strike and tenor, yield on collateral tracks the name's *absolute* IV. That is the same axis as the credit/width ranker that passed on bull puts: +8.57pp, t 3.74; within-date +7.64pp, t 4.15; corr(cw, iv) +0.474 (`ivrank_vs_cw_2026-09-22.md`). We have never run it on naked CSPs against a delta-matched stock control. A fixed IV *band* (30–60%) did nothing in BCI |
| 22:59 | Sell near the money (not further OTM) because the goal is to be assigned | **PARTIAL.** Consistent with our mechanism: a short put is a lower-beta long, so choosing the strike is choosing a delta. It is not a source of premium. BCI his-rule (~0.25–0.33Δ) and 0.30Δ strikes both come out at stock-at-delta minus costs |
| 24:13 | Blackstone: one month of put income ≈ a year of dividend (3.3% in 29 days vs 3.84%/yr) | ❌ **Category error.** The dividend is not exposed to a left tail. The put premium is paid in exchange for one. The M 0.30Δ put's worst 1% is **−41%** (bci §1) |
| 29:59–30:28 | **A covered call adds no risk** because you already own the stock | ⚠ **PARTIAL.** It adds no downside, but it sells the right tail. Measured on the PMCC: **p90 148 → 71, p99 298 → 135**, and "the shorts get run over" (`pmcc_study_2026-09-23.md`). BCI: an ITM covered call is the same trade as the CSP by put-call parity, so it inherits the CSP's FAIL |
| 32:02 | Filter to very liquid (282 names) or somewhat liquid (843) | ✅ **AGREES** with our strongest cost finding. Bid fills turn the CSP clearly negative (t −4.2). Credit/width only discriminates inside a liquid universe (`cw_rescue` §1: 2 of 15 junk-name spreads rescued) |
| 33:07 | MSFT covered call is the best-yielding today *because IV jumped after a +16% day* | ⚠ **AGAINST "it just spiked"**. Post-shock premium versus VIX-matched days: 10d −10.8pp (t −1.8), and **after UP shocks −20.7pp (t −2.1)** (`sosnoff_doctrine.md` scorecard A5). Evidence is index-level only |

## What's new / test candidates

1. **Nothing to adopt.** The wheel is `bci_csp_study` (FAIL) and `csp_vs_stopped_stock` (NULL). Already-answered
   rows: TEST_INDEX §1 "BCI cash-secured puts / covered calls", §0 "CSP vs STOPPED stock", Options With Ryan
   "Som" row (same 4%/mo wheel claim, 1/5).
2. ⭐ **One genuinely new axis: yield rank as a cross-sectional CSP selector.** Credit/width passed as a
   cross-sectional chooser on *bull put spreads*, measured as ROC. BCI tested CSPs against the stock only at fixed
   yield targets or IV bands. Nobody has asked whether the **top yield quintile within the same week**
   (at 0.30Δ, 28 DTE) beats its **delta-matched stock**, which is what his "rank by yield" claims. The risk to
   rule out is that high yield just picks high-beta names and wins in up tapes (see the 2022 BCI row), so the
   control must be delta-matched stock, not raw ROC. Cheap and local: the BCI chain cache
   (`data/cache/bci_csp/chain_*.parquet`) already carries per-trade `iv`, `atm_iv`, `sellpx`, `csp`, `stock_d` and
   `excess` (checked 2026-09-24), so the test is a re-sort of that cache, with no Athena pull.
   Prior: low to moderate. At the bid the whole pool is negative, and C4 in the scorecard shows the richest
   earnings premium *inverts* at fills.

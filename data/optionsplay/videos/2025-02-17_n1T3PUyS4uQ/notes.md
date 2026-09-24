# OptionsPlay: "How to Choose the BEST Stocks for Covered Calls Trading" (Tony Zhang, 2025-02-17, 69 min)

_Reviewed 2026-09-24. Members-only session, later posted publicly: about 47 minutes of method and platform demo, then 22 minutes of Q&A. Transcript in this folder._

## Verdict: 2.5 / 5. The two option-mechanics claims agree with our data. The stock selection, which is the actual topic, doesn't hold up

The title question gets a clear, mechanical answer. **Stock:** a 1-month and 6-month triple-MA trend, both
bullish, plus a 1–10 relative-strength score against the S&P that is high. Two archetypes qualify: "strong
bullish" (trend + RS) and "bullish turnaround" (RS still low, trend just turned). **Screen:** very liquid only,
**high IV rank only**, then rank by covered-call yield. **Strike:** **10Δ, about 45 DTE**, "our research clearly
shows" it beats 20Δ and 30Δ. **Earnings:** don't avoid them, "we've back-tested that there's no difference".

The two things he calls back-tested (low-delta strikes, trading through earnings) both line up with what our
own data implies. Both are mechanism claims, and his "research" is never shown. The part that is supposed to
select the stock (trend + RS, high IV rank, rank by yield) is contradicted or unsupported by our tests. Every
yield is annualised, per trade, at the quoted price, with no costs or n.

## Claims against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 01:37 | The primary reason to sell covered calls is to own a stock that **beats the market**, or else buy an index fund | ✅ **AGREES, and it matters more than he lets on.** A covered call is the stock at a lower delta, minus costs. The ITM CC and the CSP are the same trade by parity, and both earn stock-at-same-delta minus costs (`bci_csp_study_2026-09-17.md` §1, Verdict). So all of the return is the stock selection, and the option only subtracts |
| 07:58–16:14 | **Trend + relative strength** (1m/6m triple-MA trend, RS score 1–10 vs SPY) give "a directional edge" | ❌ / ⚠ **Not supported where we have tested it.** Mechanical trend + RS filter on BCI puts adds **nothing** (within-week excess −0.00, t −0.1) and is **worse in 2022** (−1.3%/trade vs +0.15% pool) (bci §2). Down-day RS selection **INVERTED** −3.51pp at 63d, t −3.33 (TEST_INDEX §4). Our Trend Template is the **weakest of 5 universes** (TT +0.56, t 1.3; universe test §4). His exact score is proprietary, so it is untestable as stated |
| 17:40–20:04 | **Bullish turnaround** (weak RS, trend just turned up, e.g. SMCI after −80%) is where the home runs are | ⚠ **AGAINST in a healthy tape.** Buying deep drawdowns is a regime bet, not selection. In a healthy tape the median trade underperforms by **−20% over a year** (`crash_leader_reversion_study.md`; memory veto "never buy deep drawdowns in a healthy tape"). His confirmation-first version (higher low + breakout) is the reclaim variant that TEST_INDEX §10 still has queued, untested |
| 25:13 | Filter to **high IV rank** "to capture higher premiums" | ❌ **Contradicted for per-name selection.** IV rank vs credit/width on 6,419 single-name bull puts: **zivr −1.89pp (t −1.25)**, within-date +0.25 (t 0.22). Quintiles are non-monotone and run **backwards**: the lowest ivr earned most (`ivrank_vs_cw_2026-09-22.md`). IV rank is own-history-relative, so it has no common cross-sectional scale. The short-straddle mirror is also against: selling at IVpct ≤ 30 is significantly negative, and ≥ 85 has a CI through 0 (`sosnoff_doctrine.md` C2) |
| 25:43 | Then **rank by yield** | **UNTESTED on covered calls / CSPs.** On bull puts the absolute-richness sort (credit/width) passes, +8.57pp t 3.74, and works best in the *lowest*-ivr column. So his two filters pull against each other: the IV-rank filter throws away the low-ivr names where the yield-style sort works best. See the test candidate in `2026-08-01_VSLc-kHxFlw/notes.md` |
| 42:29–44:11 | **Sell the 10Δ, ~45 DTE call**, not 20Δ or 30Δ: you give up $4 of upside for $0.50 of premium | ✅ **PARTIAL, and the mechanism agrees.** If the option is stock-at-delta minus costs (bci), a 10Δ CC leaves ~0.90 delta and a 30Δ leaves ~0.70. In a rising sample the higher delta wins, which is a **beta** statement, not a premium edge. The PMCC run found the same thing directly: the short calls get run over, credits $4,572 vs buybacks $5,634 per cycle-set, and the damage is concentrated in up years (`pmcc_study_2026-09-23.md`). The 10Δ vs 30Δ covered call itself is untested here. ⚠ At 10Δ the quoted spread is the largest fraction of the premium, and he prices none of it |
| 62:27 | **Don't avoid earnings**: "we back-tested, no difference", because delta-based strikes move out and the premium is higher | ✅ **AGREES, and our data is if anything stronger.** BCI W 0.30Δ: earnings in window **+0.26%/trade vs +0.05%** clear; within-week **+0.19pp, t +3.60** (verified in `bci_csp_study_2026-09-17.log` l.71). Not beyond direction (excess t +1.3), and the tail is worse (−22% vs −18%). "The rule is a risk preference, not a return edge." Same conclusion he reaches |
| 28:22 | Outperforming stocks have a better probability of beating earnings | **UNTESTED as stated.** PEAD on the actual surprise is NULL (TEST_INDEX §9); nothing conditions the beat rate on RS |
| 63:55 | 45 DTE maximises theta per unit of gamma; manage at 14–21 DTE (other strategies) | **Risk yes, return no.** The 21-DTE strangle test, re-run 2026-09-24 after [FIX-1] (the original dropped its worthless-expiry winners; TEST_INDEX §1): 21-DTE close − hold **−$0.52/share, month-clustered t −2.42** (halves −0.63/−0.40; hold +$0.23, 74% win; 21-DTE −$0.29, 64% win) → PASS: NO; it cuts risk only (sd $9.33 vs $17.09, worst −$291 vs −$617) |
| 45:55–46:23 | A covered call is "the only strategy that doesn't add risk" | ⚠ **PARTIAL.** True for the downside, but it sells the right tail: PMCC p90 148 → 71, p99 298 → 135 |
| 49:54 | UPS (RS 2, bearish trend): sell the stock rather than overwrite it | Consistent with his framework and with ours (stock selection is the whole return). Not a test |
| 21:04 | Consistent application of a fixed indicator set matters more than the indicator | ✅ Method point. It matches our pre-registration discipline. Not testable |

## What's new / test candidates

1. **No new stock-selection test.** Trend + RS (bci §2, down-day RS §4, Trend Template universe test §4) and IV rank
   (`ivrank_vs_cw`) are already answered, and bullish turnaround is `crash_leader` plus the queued reclaim test (§10).
2. **Covered-call strike (10Δ vs 30Δ, 45 DTE) against the stock alone.** This is a real gap: the CC side has only
   been tested ITM (BCI) and as a PMCC. But our mechanism already predicts the answer (delta minus costs, so in a
   bull sample the lowest delta wins by being mostly stock). A test would mostly measure beta. **Not worth a slot**
   unless it is run as delta-matched excess, where the prediction is roughly 0 minus costs at every delta.
3. The one live axis, yield rank as a cross-sectional selector for CSPs and CCs, is written up in
   `2026-08-01_VSLc-kHxFlw/notes.md`.

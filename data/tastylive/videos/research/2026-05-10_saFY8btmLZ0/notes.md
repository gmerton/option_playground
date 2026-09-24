# tastylive / Market Measures: "Most Options Traders Think Low Delta Strangles Are Safer. 11 Years of Data Says Otherwise." (2026-05-10, 11:51)

_Reviewed 2026-09-23 for the Sosnoff-doctrine batch (Tier 1). The study runs 01:16 to 11:43. Transcript (`en-orig`
auto-captions) in this folder. Only the slide values the host read out are available._

## Verdict: 2.5 / 5 (right conclusion, and the only video in the batch that shows the worst trade)

It does something the other four don't: it **reports the single worst loss as a multiple of credit** (5Δ: **44.2×**,
25Δ: **13×**). It argues the correct thing from it: don't size by probability of profit; size by credit and by tail
per unit of credit. That's our own rule ("a high win rate on a small credit is the signature of the failure mode —
the credit is the cost"), reached independently.

**What holds it back:**

- **The headline return figure excludes the outliers.** "The 25 delta strangle returns **1.16%** of the buying power
  per trade… **without the outliers**… the five deltas… at **0.49%**" (05:24–05:35). The with-outlier return on
  BP is never read out. The only with-outlier figure spoken is for the 5Δ: 31.4% → 18.2% of credit.
- **The management rule is stated two ways:** "managed all at 21 days" (02:06) and "you're managing this at
  **50%**" (04:09). It's unclear which applies, or whether it's first-of-both.
- **The closing arithmetic is wrong.** "5x times 5x on the five delta cuz you have five contracts… five to the fifth
  power" (10:50–10:59). Using their own figures: 5 × 5Δ at ~$2 credit, worst 44.2× credit, is a worst loss of
  **≈ $442** per credit-matched unit. 1 × 25Δ at ~$10, worst 13×, is **≈ $130**. So the credit-matched tail is
  **≈ 3.4× larger**, not 10–15× and not 5⁵. The conclusion survives; the number used to sell it doesn't.
- No n, no fills (channel disclaimer: not net of commissions), no t, no control beyond comparing deltas with each
  other.

## Data audit

| item | what the video gives |
|---|---|
| underlying | not named for the study. Almost certainly SPY; the description's outliers are "COVID, the 2025 crash, and the April 2026 war move". The AMZN prices at 09:53 are a live illustration only |
| period | **2015 → present** (~11 years) |
| n | **not stated** |
| entry rule | strangles at **25Δ, 20Δ, 16Δ, 5Δ**, "sold separately" |
| DTE / management | "managed all at **21 days**" (02:06), also "managing this at **50%**" (04:09); no rolling, no adds ("snapshot of that one trade", 07:44) |
| metrics | avg P&L **% of credit**; the same **before/after outlier moves** (2020, 2025, April 2026); avg P&L **% of buying power**; **worst single loss ÷ credit** |
| fills | **unstated**; channel disclaimer "not presented net of all commissions, fees, and expenses" |
| control | across deltas only; no benchmark |
| win rate / avg / tail | ⭐ **the worst trade is shown** (as a multiple of credit); no drawdown series; no loss count |
| significance | none |
| selection | ⚠ "without outliers" figures are headline; the outlier definition (which trades or dates were removed) isn't given |

## Numbers as spoken

| @ | number |
|---|---|
| 01:58–02:13 | **2015 → present, ~11 years**; **25Δ, 20Δ, 16Δ, 5Δ** strangles, "managed all at 21 days" |
| 03:56–04:05 | without big outlier moves, 5Δ strangles "performed the best, keeping **31%** of the credit" |
| 04:09 | "you're managing this at **50%**" |
| 04:45–04:54 | with outliers included, 5Δ "drops the most from **31.4%** to an **18.2%**" of credit |
| 05:24–05:35 | 25Δ "returns **1.16%** of the buying power per trade… **without the outliers**", 5Δ **0.49%** |
| 05:52–05:58 | "the most bang for your buck when you're selling somewhere between a **20-delta**" (25Δ) |
| 06:59–07:04 | worst single loss: **5Δ = 44.2× credit** |
| 07:19–07:23 | worst single loss: **25Δ = 13× credit** |
| 09:53–10:00 | live AMZN: 5Δ strangle ≈ **$2**, 25Δ ≈ **$10** |
| 10:27–10:31 | 5 × 5Δ to match the credit = "more than twice… like **10 or 15 times** the risk" |
| 10:50–10:59 | "5x times 5x… five to the fifth power" (arithmetic error, see verdict) |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 01:25 / 11:18 | A 95%-POP strangle is not safer; don't size on POP | ✅ **AGREES, and it's one of our hardest-won rules.** 2026-09-22 cost sweep: **UVIX bear call +11.0% / 93% win at mid → −8.8% net / 46% win** (costs ≈ the whole $0.25 credit); 13 screener spreads, gross +3.8…+13.4% → net −5.1…+5.9%, **0 of 13 significant** (`feedback_price_at_real_fills`). Low delta adds a second problem this video doesn't mention: **friction as a share of credit is worst on the smallest credit**, so at real fills the 5Δ is worse than they show, not just riskier. |
| 06:59–07:23 | Worst loss: 5Δ 44.2× credit vs 25Δ 13× (managed, SPY-type) | **Plausible magnitudes against our measurements.** SPY 20Δ 45-DTE strangle in our 21-DTE study (real fills): worst **managed −$51.7/share on ~$5.15 average credit ≈ 10× credit**; worst held −$82.9/share (`exit_21dte_2026-09-23.csv`). Single-name short 7-DTE ATM straddle: worst **−1,193% of credit (≈ 12×)**. SPY 1-day naked straddle worst **−604% of credit**. The mirror image is on our long side: the **5Δ same-expiry SPY put overlay lost −100% on all 75 trades** [WL-5f], so the far wing expires worthless almost always, and when it doesn't the short side loses dozens of credits. That's exactly their 44×. |
| 04:45 | 5Δ keeps 31.4% of credit without outliers, 18.2% with | ✅ **Right shape:** the outlier removes ~42% of the 5Δ's lifetime P&L. No 25Δ with-outlier figure is read out, so the comparison the title needs is missing from the transcript. |
| 05:24 | 25Δ earns 1.16% of BP per trade vs 0.49% for 5Δ | ⚠ **Excludes outliers**, and it's likely at mid. Our nearest: SPY 20Δ managed at 21 DTE, real fills, **−$0.46/share over 2018–2025** and **+$0.225/share (t 1.91) from May 2020** (descriptive slice). The sign depends on whether 2020 is in the sample, and that's precisely the "outlier" they set aside. |
| 05:37 | "Wider strangles collect enough premium to use capital more efficiently" | ✅ **Agrees in spirit** with our only replicated cross-sectional selector: **credit/width** on single-name bull puts, **top−bottom +7.84pp, month-clustered t +3.56**, both halves positive; **IV rank NULL** head to head (zivr −1.89pp, t −1.25). "Pick by credit relative to risk, not by POP or IV rank" is the same lesson. |
| 07:40 | The tail number is one position, no rolling, no adds | Fair and honest framing. It's also the correct way to measure the tail. Our paired 21-DTE design does the same. |
| 10:27–10:59 | 5 × 5Δ carries 10–15× (or 5⁵×) the risk of 1 × 25Δ | ❌ **Arithmetic error.** From their own figures the credit-matched worst case is ≈ **3.4×** (5 × 2 × 44.2 = 442 vs 1 × 10 × 13 = 130). The direction is right; the multiple is inflated. |

## What I would take

1. **Keep their sizing sentence.** "Size on credit received and tail risk per unit of credit, not on probability of
   profit" (11:20). It agrees with our fills rule and with the credit/width selector, and belongs next to "size to the max loss".
2. **The 44× vs 13× worst-case comparison as an illustration** of why the far-OTM strangle is the worst version.
   Our 5Δ-put overlay result (−100% on all 75) is the same fact seen from the buyer's side.
3. **Discount their return-on-BP table.** It excludes the outliers, and the outliers are the whole question for a
   naked short.

## Not tested, could be

- **SPY 45/21 strangle across 5Δ/16Δ/20Δ/25Δ at real fills, with the worst trade ÷ credit and the with/without-2020
  split.**
  - **Data:** puts from `data/cache/SPY_puts_v3_2018_2026.parquet`, calls need a v3 pull (`run_spy_puts_v3_pull.py`
    with `cp='C'`). Friday entries 2018-01 → 2026-03, sell bid / buy ask. Arms: close at first session ≤ 21 DTE,
    and 50%-take-or-21-DTE.
  - **Report per delta:** mean $/share, % of credit, % of Reg-T BP, win%, worst ÷ credit, month-clustered t.
  - **Effort:** ~½ day plus the call pull.
  - ⚠ **Zero-bid trap for 5Δ legs:** a far-OTM winner decays to a zero bid, and `options_cache` drops those rows.
    Pull from v3 directly and run the path-coverage guard (`lib.studies.path_coverage`) or the 5Δ result will be
    flattered.
  - Prior: every delta is ≤ 0 at real fills over 2018–2026 (SPY 20Δ already is), and 5Δ is the most negative after
    costs.
  - **Descriptive, not an edge search. Not queued unless asked.**

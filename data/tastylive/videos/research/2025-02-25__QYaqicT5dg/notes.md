# tastylive: "4-Year SPY Research Reveals Potential IVR Sweet Spot" (2025-02-25, 6 min)

_Reviewed 2026-09-23. Tom Sosnoff and Tony Battista ("Tony and I… on tasty", 01:46) read a research-desk study. The
transcript (`en-orig` auto) is in this folder. The slide tables aren't legible from the captions. Only the per-year
thresholds are read out, and no P&L figures are._

## Verdict: 1.5 / 5

The headline is a **look-ahead artefact**. "The best IVR threshold" is chosen **inside each year, on that year's
results**, then shown next to the same years. Tony says so on air at 05:43 ("it's a look back… kind of like in
hindsight").

Other problems:
- The sample is tiny: one SPY 20Δ strangle per 45-day cycle is ~8 per year, fewer once a threshold filters them.
- The title's "4-year" contradicts the video's "5 years".
- The thresholds jump around from year to year: 13, 0, 30, 8, 15.
- The takeaway ("our 30 across all underlyings makes a lot more sense") doesn't follow from a SPY-only study whose
  best thresholds were mostly *below* 30.

What's worth keeping is a detail: **IVR is computed from the VIX**, so this is a *market-regime* gate on an index. That
is a different object from the single-name IV rank our ledger found NULL. In that form our data partly agrees with it.

## Data audit

| item | what the video gives |
|---|---|
| Underlying | SPY only |
| Period | "5 years of daily option data" (00:55). Per-year results for 2020–2024. **Title says 4** |
| IVR definition | **"we computed the IVR levels using the VIX"** (00:58–01:01). A market vol rank, not SPY's own IV history |
| Structure | 20Δ short strangle, entered "at each 45-day opportunity", **all closed at 21 DTE** |
| Arms | IVR thresholds from 0 (always trade) upward. For each year, the threshold with the best P&L is picked |
| Sample | ~8 cycles a year × 5 years ≈ **40 trades total at threshold 0**, fewer above it. Not stated exactly. "There might only been one or two or three instances" (04:22) |
| Fills / costs | not stated (tastylive convention: mid, no commissions) |
| Compared to | the other thresholds, then "each year's best applied to all 5 years" (03:22) |
| Win vs mean vs tail | "worst loss, bottom of the page, not too bad" (02:58). Values not read out |
| Significance | none |
| Selection | ⛔ **the per-year optimum is selected on the outcome it's evaluated on.** The "applied throughout" slide reuses those selected thresholds on the same 5 years, so it's in-sample too |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 00:32–00:36 | tastylive's house rule: sell premium only when IVR > **30** |
| 02:10–02:16 | 2020 best threshold: IVR ≥ **13** |
| 02:33–02:38 | 2021: **any** (threshold 0, "every single 45 day cycle worked") |
| 02:38–02:41 | 2022: had to be > **30** "to make money" |
| 02:41–02:47 | 2023: > **8**; 2024: > **15** |
| 03:44–03:57 | Applied to all 5 years (thresholds "130, 38 and 15", garbled captions, probably 13 / 30 / 8 / 15): "P&L numbers remained high", ~**4–5× as many trades**, and worst losses lower |
| 05:00–05:24 | Conclusions: higher threshold = "safer year-to-year"; in the best years trade regardless; in hard years wait for IVR > 15 or 30 |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 00:16–00:25 | "Short premium positions generally perform better in high IVR", repeatedly seen | **Depends which IVR.** (a) **Own-history IV rank as a cross-sectional selector on single names: NULL.** TEST_INDEX §1 "IV rank vs credit/width" (6,419 spreads, 20 names, real fills): zivr −1.89pp (t −1.25) in the joint fit, within-date +0.25pp (t 0.22). Its quintiles are **non-monotone, and the lowest-IVR quintile earned most**. (b) **Own IV percentile as a timing gate on index bull puts: a mild VETO**, not an edge (QQQ/IWM, ≥80th percentile = veto). (c) **Market vol level (what this video actually uses): SUPPORTED.** VRP panel 90d premium by VIX: <15 −0.51vp, 15–20 +0.44, 20–25 **+2.53 (t 4.10)**, >25 **+3.45 (t 4.85)**. The one certified short-premium bucket is gated on **VIX ≥ 20** after a selloff (SPY bull put t 6.07, SPX condor t 5.21, one bet). The SPX strangle playbook: "LowIV regimes (VIX < 20) have near-zero or negative ROC across all delta combos." |
| 00:58–01:09 | IVR from the VIX, 20Δ strangles, 45 DTE, closed at 21 DTE | Close to our SPX 45-DTE strangle/condor engine, which is regime-gated on VIX ≥ 20 and uses a 50% take. Ours adds a trend condition (below the 50MA) and skews the put to 30Δ. The **21-DTE close** is our one "certified" management rule (+$1.53/strangle, t 4.26), but that study drops the both-legs-worthless winners (found in this batch), so it needs a re-run |
| 02:10–02:47 | Best threshold per year: 13 / 0 / 30 / 8 / 15 | ⛔ **In-sample optimum per year with ~8 trades.** The spread of values (0 to 30) is what you'd expect from noise over a flat surface. Tony's own "it's a look back" (05:43) is the right verdict. Our ledger rule: never read a best-of-k cell without the charge. Here k = (thresholds tested) × 5 years, with no charge at all |
| 03:22–03:57 | Applying the thresholds to all 5 years keeps P&L high with 4–5× the trades and lower worst losses | ⚠ Still in-sample: the thresholds were picked on these years. More trades at a *lower* threshold means *less* filtering, so "P&L stayed high" argues that the gate barely matters on SPY |
| 04:39–04:46 | "So our threshold of 30 across the board for all underlyings really makes a lot more sense" | ❌ **Non sequitur.** The study's best SPY thresholds were ≤ 15 in 4 of 5 years. For single names, where tastylive applies 30, our head-to-head says own-IVR has no common cross-sectional scale (corr(cw, ivr) only +0.136 vs corr(cw, iv) +0.474). **Credit/width is the selector that works** (top−bottom +7.84pp, t 3.56, both halves). Down the lowest-IVR column cw still sorts 2.51 → 9.83, "where Sosnoff says not to trade" |
| 05:00–05:24 | Higher threshold → safer year to year; wait for IVR 15–30 in hard years | **Directionally consistent with the VIX-level result above.** But "hard years" is only identifiable afterwards. 2022 (IVR > 30 needed) is exactly the year our bearish-high-IV cell earns in (it's ~43% of trades in one year) |

### Reconciling the sweet spot with our IV-rank NULL

**No contradiction. They're different variables.**

| | this video | our NULL |
|---|---|---|
| Rank of | the **VIX** (market vol) | each **name's own** IV history |
| Used as | a **timing gate** on one index | a **cross-sectional sort** across 20 names |
| Structure | SPY 20Δ strangle | single-name 30Δ/20Δ bull put |
| Our evidence on that variable | VRP rises with VIX level (90d t 4.10 / 4.85 at VIX 20–25 / >25); the certified cell is VIX ≥ 20 | ivr t −1.25 (joint), non-monotone quintiles |

The TEST_INDEX row itself says the NULL "says nothing about ivr as a WITHIN-NAME timing gate". The honest reconciliation:
**elevated market vol is where index short premium pays (agrees). Own-history IVR is not a way to choose which name to
sell (our NULL stands). This video's specific per-year thresholds are noise.**

## What I would take

1. **VIX-level gating on an index strangle is consistent with our certified bucket.** That's a confirmation, not new
   information.
2. **The method lesson, stated by the host:** a per-period optimum is hindsight. Use it as a classroom example of best-of-k
   without a charge.
3. **Nothing to adopt.** The certified cell already gates on VIX ≥ 20.

## Not tested, could be

**VIX-rank threshold sweep on the SPY 45-DTE 20Δ strangle, walk-forward, at real fills.**
- **Data:** v3 calls and puts on SPY 2010–2026 (the puts cache covers 2018+ only).
- **Entry:** every Friday (not one per cycle, for power); sell the bid, close at the first session ≤ 21 DTE at the ask.
- **Gate:** VIX IV rank over the trailing 252 days, thresholds {0, 10, 20, 30, 40, 50}.
- **Walk-forward:** pick the threshold on years 1..k and apply it to year k+1. Compare against the fixed-30 rule and
  against always-on. Month-clustered t, both halves, Šidák charge for 6 thresholds.
- **Effort:** ~½ day (the 21-DTE harness already has the exit; add a VIX rank and a loop).
- **Prior:** the gate helps (VRP by VIX is monotone at 90d), and the per-year optimum doesn't persist.
- ⚠ **It overlaps the certified bucket.** Report the cell with the bearish-high-IV dates removed, or it will just
  re-find that bucket.

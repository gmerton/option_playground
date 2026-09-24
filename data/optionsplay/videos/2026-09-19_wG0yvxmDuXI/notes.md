# OptionsPlay — "Why the Options Market Is Always Wrong About Volatility" (Tony Zhang, 2026-09-19, 45 min)

_Reviewed 2026-09-24. ⚠ **This is a re-edit of the 2026-09-11 webinar already reviewed as
[lV8Jkl37h4M](../2026-09-11_lV8Jkl37h4M/notes.md)**: same session, same examples, same numbers. It adds a
cold-open teaser and a members-only outro, and cuts the Q&A (the MCP-server note and the diagonal walk-through).
Timestamps run about 1:55 earlier than lV8's through the body of the talk. Transcript in this folder._

**How the duplicate was established:** a word-level diff of the two transcripts (timestamps stripped). Of 6,875
words here, 198 are not in lV8. They are the 30-second cold open (a repeat of the 02:57 VRP line), caption-spelling
variants ("Crowdstrike"/"Crowd Strike") and the outro. lV8 has 1,725 words not here, which is the Q&A. Nothing
substantive is new.

## Verdict: 2.5 / 5 (unchanged from lV8)

Same score, for the same reasons: the description is right and every rule is priced at the mid, with no cost
model, sample or statistic. **The retitle overclaims.** On our own panel, "always wrong" is wrong at the tenor he
talks about (VIX = 30 days). Re-reading the VRP panel for this retitle also shows that the lV8 notes were **too
generous** on the premium claim (see the first row below). Everything else is already covered in lV8's table and its two follow-up tests
(skew signal NULL, IV rank as a vehicle chooser NULL). I have not repeated those rows here.

## Claims, with what is new relative to lV8

| @ (here) | Claim | Our evidence |
|---|---|---|
| 00:00 / 02:51 | **"The options market always over-estimates future volatility"**; the VRP has been positive since 1990 except briefly in 2008 | ⚠ **PARTIAL, and a correction to our own lV8 note.** lV8 marked this "✅ Reproduced ... without exaggeration" and cited the **10-day** cell. He is talking about the VIX, a **30-day** measure. On our panel (10 ETFs, 2010-01 → 2026-05, NW-corrected, Bonferroni hurdle t ≥ 3.29): **10d +1.75vp, t 8.93, positive on 75% of days** (so realised beats implied 25% of the time). **30d +0.78vp, t 2.08, below the hurdle, positive on 71% of days** (realised wins 29%). At 30d the **annual mean is negative in 3 of 17 years: 2015 −0.09, 2018 −1.11, 2020 −2.57vp**. The median stays positive in every year. So the premium is collected in the typical month and handed back in the tail. That is the opposite of "always", and a mean-positive/tail-negative payoff is exactly what the cost and crash-week rules exist for. Source: `data/studies/vrp_panel_study.md` §1 and §4 ("30d by year") |
| 03:26 | "Therefore there is a statistical edge in selling over buying" | Covered in lV8: the gap is real, but at real fills it is often not an edge (earnings vol premium +0.601% at mid → **−0.428% at the bid**, `earnings_vol_premium_2026-09-20.md`; the generic put spread goes from +3.2% gross to **−3.3% net**, `paid_to_wait_study.md`) |
| 08:11 | Options 360 report compares **implied vs the last 10 days' realised**; "that gap is where sellers have an edge" | **PARTIAL · new here.** Implied minus TRAILING realised is our panel's `vrp_trail`. At 10d the richest quartile earns the most (**Q4 +2.33vp, t 9.01**), but the ordering is **not monotone**: the "cheap" quartile Q1 (+1.83) beats Q2 (+1.50) and Q3 (+1.42). At 30d, Q4 +1.09 (t 2.70) vs Q1 +0.83 (t 1.74), and neither clears the hurdle. The gauge shows the right direction, but it is a weak sort and not a gate. Source: `vrp_panel_study.md` §3 |
| 20:24 / 22:18 / 25:33 | **IV rank < ~33 = options cheap → "at least not at a disadvantage to be a buyer"**; IVR < 10 → buy the outright | **CONTRADICTED on ETFs · new here.** Even the cheapest own-IV-percentile bucket still pays the **seller**: **10d IVpct 0–20 = +1.28vp, t 8.78, 68% positive**. It is the smallest premium of the five buckets, but it is positive and highly significant. At 30d the buckets are flat and non-monotone (0–20 +0.51, 60–80 +0.42). Low IV rank shrinks the buyer's headwind; it does not remove it. The long straddle only becomes positive when a second gate, FVR ≥ 1.2, is added (IVpct ≤ 30 gate, `straddle_ivgate_robust`). On single-name bull puts, IV rank as a selector is **NULL (zivr −1.89pp, t −1.25)** while credit/width wins (`ivrank_vs_cw_2026-09-22.md`) |
| 22:54 | IV mean-reverts to a long-term IV-rank average of "20–35%", so IVR 54 will drift back down | Untested as a forecast of IV rank itself. Note that IV rank is **bounded to a trailing year by construction**, so "mean-reverts to 25–35" partly restates the definition |
| 26:47 | CrowdStrike: IV is high **at an all-time high**, "strange", so sell a bull put | Covered in lV8 (bullish + high IV → put credit spread). Our certified version of this cell is **index, after a selloff**. The bullish-low-IV version is −4.8% month-weighted (t −0.87) |
| 32:44–38:12 | Choose strikes by delta, not a fixed % OTM; Walmart 110/95 put spread $536 vs $640 outright → 180% vs 135% | Covered in lV8. The delta rule is right as a **variance** argument. **"The spread beats the outright" is CONTRADICTED at real fills**: the second leg's friction costs −27.1pp (t −5.51) while the cap costs only −2.0pp |

## What's new / test candidates

1. **Nothing new to test.** The two claims this edit keeps and lV8 did not grade in detail (the trailing-gap
   gauge and "low IVR → buyer not disadvantaged") are both already answered by the VRP panel's §3 conditioning
   tables. I cite them above and am not proposing a re-test.
2. **Correction to carry into lV8's notes and TEST_INDEX row 282:** "VRP reproduced" should read **"reproduced at
   10 days; at the 30-day tenor he cites it is t 2.08 with 3 of 17 negative years"**. The retitle
   ("always wrong") is the version to rebut.
3. **Housekeeping:** mark this video as a duplicate of lV8Jkl37h4M in `data/optionsplay/index/README.md` so the
   tier table doesn't count it as a second source.

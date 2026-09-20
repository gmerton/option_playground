# Does the index-add rebalance auction pop hold, or give it back? (2026-09-20)

**Question.** SNDK closed 9/18 at 1,791.82 after a +3.25% move in the last thirty minutes on 1.98M shares —
11% of the day's volume — while QQQ did +0.31% and its peers +0.3 to +0.8%. That is a rebalance auction, not
a trend close. Gabe is long 4 shares from 1,698.90. Should a position be held through the effective date, or
sold into the index bid? Generalised: **when a name is added to a major index, does the run-up into the
effective date reverse afterwards?**

**Premise correction first.** The trade was entered on the belief that SNDK was joining the Nasdaq-100. It
was not. SNDK joined the **Nasdaq-100 on 2026-04-20** (replacing TEAM) and the **S&P 500 on 2025-11-28**
(replacing IPG), both verified against the index change histories. The 9/18 event was the **S&P 100 add
effective 9/21** (with DELL, PANW, ANET; out: NKE, HONA, SPG, CL), landing on the September quarterly
rebalance. S&P 100 tracking AUM cannot absorb ~$3.5B at a close, so most of that print is most likely
quarterly re-weighting in indices SNDK was already in. That decomposition is inferred, not verified.

**Event set (`data/studies/index_adds_events.csv`).** S&P 500 and Nasdaq-100 change histories parsed
deterministically from wikitext, 2019-01 → 2026-09: 217 raw adds → 191 unique (ticker, effective date) after
dedup and dropping 26 spin-offs with no prior price history → **173** with ≥60 pre-bars and ≥11 post-bars in
`liquid_panel_2019`. 18–25 per year, every year; 111 S&P 500, 62 NDX; 92 distinct calendar dates.
**Anchor = the T-1 close**, the rebalance auction close, which is the decision point.

**The events are real index adds.** Announcement → auction-close run-up **+4.48% mean, +2.48% median,
t 5.28** (n=143 with a dated announcement). At the anchor the added names sit **+0.89 ADR over the 21 EMA**,
35% of them above 1.5 ADR — extended by construction, which is why an unmatched control would rediscover
mean reversion and let us call it an index effect.

**Test (`run_index_add_study.py`).** Plain forward return from the anchor close over +1/+3/+5/+10 sessions —
a drift question, so the R harness does not apply. Three controls, 3 draws each: `post` (same name, random
session in the following 20), `xname` (random eligible other name, same date), `extmatch` (random eligible
name-day matched on extension over the 20 EMA in ADR ±0.25 and on ADR20 ±1pp). t clustered by calendar date.
Pre-registered: T+5 vs `xname`, t ≥ 3, n ≥ 150. Kill: |t| < 2 on every arm.

| hold from the auction close | n | mean | median | win | t (date-clustered) |
|---|---:|---:|---:|---:|---:|
| T+1 | 173 | −0.11% | −0.14% | 47% | 0.38 |
| T+3 | 173 | −0.46% | −0.41% | 45% | −0.37 |
| **T+5** | 173 | **−1.00%** | −1.02% | 40% | **−1.17** |
| T+10 | 173 | −0.74% | −0.42% | 47% | −0.18 |

| edge vs control (pp) / **t on the paired-by-date difference** | post | xname | extmatch |
|---|---:|---:|---:|
| T+1 | −0.07 / **0.24** | −0.04 / **0.28** | −0.05 / **−0.05** |
| T+3 | −0.40 / **−0.50** | −0.19 / **0.24** | −0.43 / **−0.22** |
| **T+5** | −0.99 / **−1.34** | **−0.89 / −0.83** | −0.95 / **−0.55** |
| T+10 | −1.25 / **−1.17** | −1.02 / **−0.39** | −1.07 / **−0.67** |

**Verdict: FAIL — no tradeable index-add reversal.** The pre-registered test returns **t −0.83** against a bar
of 3. The kill criterion (|t| < 2 on every arm) is met on all four horizons against all three controls; the
largest |t| anywhere in the table is 1.34. The direction is consistently negative — about **−1pp at T+5,
40% win rate against ~51% for every control** — so a give-back is the way to bet if forced, but it is
indistinguishable from noise at this sample size.

**Why the null is believable, and what it could have caught.** Date-clustered SE at T+5 is 0.61pp, so the
minimum detectable effect at t=3 is **1.84pp** (1.22pp at t=2). A give-back of the full +4.5% run-up would
have been caught many times over; a 1pp drift cannot be. The result also matches the published finding that
the S&P index effect has decayed toward zero since the 1990s.

**Splits (descriptive, all underpowered).**
- By half: <2023 **+0.08%** at T+5, ≥2023 **−2.13%**. Not negative in both halves — whatever is there is
  recent, which is the shape of a subgroup result, not an effect.
- By index: NDX −1.9% at T+5 (n=62) vs S&P 500 −0.5% (n=111). Worst cell, NDX since 2023: n=31, 16 dates,
  −3.65%, **t −1.51** — still not significant, and it is the cell a fishing expedition would land on.
- By reason: rebalance adds −1.35%, M&A replacements +0.08%.
- **By extension: no gradient** — <0.4 ADR −0.92%, 0.4–1.5 −0.76%, >1.5 ADR −1.20% at T+5. Being extended
  at the auction does not make the give-back worse, which closes the "SNDK is at +2.11 ADR so it is extra
  vulnerable" line.
- Tails: 16% of adds are ≤ −5% at T+5, 12% are ≥ +5%. Two-sided, not a fade.

**What this changes.**
1. **For SNDK: nothing.** The stop package stands — 1,686.50 judged on the close, 1,595 resting, 20-EMA trail
   once it crosses. The lean written into the thesis log on 2026-09-20 ("expect the auction pop to reverse")
   is **not supported** and has been corrected there. Do not sell into Monday on flow logic.
2. **No new rule.** "Index add" is not a reason to buy, hold, fade or size differently.
3. The one durable operational point survives and is mechanical, not statistical: **a rebalance auction close
   is not a trend close.** Use the pre-auction price (~1,740 for SNDK) as the reference when reading the day
   and setting trails, because the last print had a buyer who is now done.

**Caveats.** 173 events, 92 date clusters. 14 adds dropped for not being in the liquid panel (ARM, PDD, SPLK,
SGEN, ANSS, LCID and 8 others) — mildly non-random, 91% coverage. Announcement dates come from the cited
press releases where Wikipedia carries them (143 of 173). Stock-only: no costs, no fills, no options. S&P 100
adds are not in the event set (no public change history), so SNDK's own event type is untested — but S&P 100
tracking AUM is the smallest of the three, so if anything its flow is weaker than what was tested here.

# OptionsPlay — "How the Early Breakout Detector Finds Trends Before They Go Mainstream" (Tony Zhang, 2026-07-11, 55 min)

_Reviewed 2026-09-24. This is the Week 1 Thursday "Growth Lab" replay and a platform demo: the Early Breakout
Detector watch list, sorted by OptionsPlay's relative-strength score, used as the entry point for the
"add to winners" process from the June series ([iXOULnIGEKk](../2026-09-05_iXOULnIGEKk/notes.md) is a sibling).
About 4 minutes (24:10–26:40) are lost to a platform outage on air. Transcript in this folder._

⚠ **This is vendor content.** It opens and closes with the 14-day-trial QR code [03:28, 53:15], and the live Q&A is
for members only. The detector's formula is not disclosed. The one statistical claim, "the underlying research"
[29:28], has no numbers, sample or source.

## Verdict: 2 / 5

- **The detector is a black box**, and what little is said about it points the wrong way. It is a daily market scan for
  "early movers" [06:48] and the watch list is sorted by an RS score. By his description, a **low** score is a stock
  that "has made its way down over the last 3 6 9 12 months" and is starting to turn [16:24, 27:23]. He tells you to
  start your morning with those names. On our data, breakouts in names that are down over six months, or below the 200 SMA, are the **worst** cohort
  we have measured. An exploratory check today (below) finds the lowest-RS decile is also the worst on the modern
  panel.
- **The one research claim is not supported.** He says the best performance comes from the lowest *and* highest RS,
  with the middle worst [29:28]. That U-shape does not appear in 3 of 4 exploratory cells, and the fourth
  (t 2.48, overlap-inflated) does not clear the bar.
- **The process half is the June series again.** It is the add-to-winners rule from iXOULnIGEKk, which our pyramid test found NULL.
  His failure rate ("30–40% just won't work out") is again much lower than ours.
- **The honest parts:** start small, never add to a loser, use defined risk, and expect most trades to be small wins and
  small losses. That is why it scores 2 and not 1.5.

## What the detector computes: everything the transcript pins down

| @ | statement | what it implies |
|---|---|---|
| 06:48–07:30 | "every day ... we're scanning the entire market ... thousands of names ... trying to find the early movers ... We rank those by relative strength" | a daily cross-sectional scan, with the trigger undisclosed. The count varies a lot: 4 names today, "50, 60, 70" on other days [07:30] |
| 09:31–10:53 | The detector is one of six tiers in the Mon/Thu report: early breakout · building outperformance · confirmed outperformance · confirmed underperformance · building underperformance · early breakdown [22:31–23:11]. Tier counts are "down 21 / 26 / 34 from last week" | the tiers are defined in the sibling video [9VylBGWJVT8 @15:39](../2026-04-20_9VylBGWJVT8/notes.md): early = outperforming the S&P on the **short** time frame only, building = two of three, confirmed = all three. **The horizons are never given** |
| 16:24 | Designed for "stocks that perhaps have made its way down over the last 3 6 9 12 months and now is on the verge of ... starting to make its way back" | the "early" tier is a **turnaround-from-drawdown** scan. It is not a trend-continuation scan |
| 27:23–28:04 | "The lower the [RS] the fresher ... stocks that are most beaten down that are just starting to emerge ... have the lowest scores"; 8–10 = "sat sideways ... now breaking out to new all-time highs" | the RS score is a **1–10 bucket of longer-horizon relative strength**. It is evaluated on names that already pass the short-horizon trigger |
| 30:09–33:34 | Example with RS 3: a $1,700 stock that peaked at $2,600 "in June of last year", held $1,600 support for four months, and is "showing some life". Add above $1,900; target the prior high around $2,600 | the name is not said ("I don't know this particular stock"). MELI is in that day's list [35:11] and fits the prices, but that is my inference, not stated |
| 17:45–18:26 | "prior highs form your target price" | the stated reason to prefer low RS: a **structural profit target**. At all-time highs there is none, so you need "fundamentals ... projections" [36:18] |

**In our vocabulary:** a short-horizon relative-strength turn (the name starts beating SPY over the last few weeks)
in a stock with weak 3–12-month relative strength. That is the stock-level version of the rotation study's
**"early turn" rule** (21d RS crosses above 0 while 63d RS < 0). We tested that at the sector level: +0.28pp at 21d
(t 2.55), gone by 63d (−0.15), and it did not hold across eras (`industry_rotation_detection_study.md` §3a).

## Data audit

| claim | stated source | denominator | checkable? |
|---|---|---|---|
| "best performance ... in the lowest RS and the highest RS" [29:28] | "the underlying research" | none | no. Checked exploratorily on our panel below: **not supported** |
| GE: $1,200 → $4,600 with three adds, May 28 → Jun 17 [19:09–21:11] | their own daily-play record | one trade, hand-picked | no fills or sizes. "Robinhood, Micron" are named as other catches [40:24]; no losers are shown |
| "less than 10%" of ideas reach the final target, "roughly 7–8%" have the big moves [33:34] | none | none | no |
| home runs "outweigh your losing trades by a factor of four to five times ... sometimes 7, 8, even 10" [33:34] | "previous sessions last month" | none | no. It is an R-multiple claim with no distribution |
| "30 to 40% of those are just not going to work out" [45:47]; wrong "40, maybe even 50%" [00:00, 46:28] | none | none | against ours, see below |

## Claims against our ledger

| @ | claim | our evidence |
|---|---|---|
| 29:28 | **Early breakouts perform best at the lowest and the highest RS; the middle is worst** | ❌ **Not supported (exploratory, today, see below).** On 6-month RS the U contrast is +0.08pp at 20d (t 0.25) and +0.04pp at 60d (t 0.07). The **bottom decile is the worst cell**: −1.61pp at 20d and **−4.00pp at 60d** (date-mean t −3.39, both halves negative). This agrees with the rotation study's 20-year panel, where RVOL ≥ 1.3 breakouts **below the 200 SMA ran −3.08pp at 21d / −3.32pp at 63d, and those down > 10% over six months −3.34pp at 21d** (§8). Those two cohorts are why the house has the vetoes (§9) |
| 16:24, 27:23 | Start with the lowest-RS names: they are "fresher" and have "huge upside potential" | ❌ **Contradicted, as above.** A related study, done differently: buying deep drawdowns on arrival is a **regime bet, not selection**. It pays in a broken tape and in a healthy one the median is **−20% over 252d** at a 50% drawdown (`crash_leader_reversion_study.md` §4). His examples come in a tape he calls "risk-off" [09:31], which is the only regime where that study's cell is positive. But his trigger is a base breakout, not arrival at the drawdown, so this is supporting context and not the same test |
| 17:45–18:26 | A prior high is a better profit target than a projection | Untested as a target. The nearest evidence goes against fixed exits: trims and profit-locks cost −0.25…−0.33R, and "extended → tighten" INVERTS (TEST_INDEX §4 profit-lock row). A target at the prior high would cap the same right tail the 20-EMA trail exists to keep |
| 13:37–16:24, 43:47–45:07 | **Add at 110, 120, 130** when the platform issues a new signal, but only on a profitable position and never on a loser | ⚠ **Tested 2026-09-22, NULL** (`run_oneil_pyramid_8wk.py`): adds at session 3/5/10 earn +0.30…+0.66R on their own risk (t 0.4–1.5). **No condition beats adding to any still-open trade** (best +0.15R, t 1.25). "Only if profitable" is the endogeneity trap: trades that are up by day 3 finish +3.4R vs +0.35R because of gain already made (TEST_INDEX §4 pyramid row; iXOULnIGEKk notes) |
| 19:09–21:11 | GE: an early-breakout trigger above ~310, then three adds in three weeks, $1,200 → $4,600 | One winner, picked after the fact. It is also a **credit-spread** book: three put credit spreads and one debit spread. Our pyramid test was on stock; the put spread vs the house stock trade on the same breakouts is a separate 2026-09-24 row (TEST_INDEX §1). Not evidence either way |
| 45:47, 00:00 | 30–40% of early breakouts "just won't work out"; you are wrong 40–50% of the time | ❌ **Understated.** The house 20d breakout: **76.4% return to the level** (−0.374R), and only 23.6% hold (+1.273R) (`retrace_entry_2026-09-20.md`, 43,970 breakouts). The in-book precision tier wins **30%**, median −1.08R (`breitstein_tests/precision_tier_control_2026-09-19.md`). His baseball analogy (a .350 hitter) is the right *shape*, since our win rate is about .300. But "wrong 4 in 10" is off by 30pp |
| 42:26–43:06 | Most trades are small wins and small losses plus a few home runs; the home runs pay 4–10× the losers | ✅ **The shape matches.** Our breakout book is right-tail-carried: +0.448R trade-weighted vs −0.007R month-weighted, so the edge lives in the busy breakout months (pyramid row METHOD note). The **multiplier** is unsupported, since no distribution is given |
| 06:08, 25:25 | Social media / TV = late; the detector = early, so you enter "at the ground level" | ⚠ **The early-vs-late framing is the entry-extension finding upside down.** Our breakout entry buys **+0.52 ADR above the prior 20d high vs −2.09 ADR for a random later entry in the same name: 2.6 ADR of price paid**. The later entry wins, and the stop is not the cause, since stop-out rates are identical at 48.4% vs 48.0% (`entry_vs_stop_2026-09-20.md`). "Early" in *trend age* is not the same as a good *entry location*. His early breakouts are still breakouts |
| 37:40–39:01 | LNG / energy is in the early tier but "I don't know that [it's] durable"; fade the rally on a Middle-East view | A **discretionary override of the detector** on air. That is fine as a practice, but it means the published list is not the traded list, and any record of the detector is a record of his vetoes too |
| 36:59–37:40 | At all-time highs, "layer in fundamentals" (measured move plus a valuation check) before chasing | Untested here. Note that the gate-ablation found **within 15% of the 52wk high NULL (+0.12pp, t 0.14)** (`TEST_INDEX` §4, 2026-09-24), so being at the high is neither a veto nor a lever on its own |
| 41:46–42:26 | At highs, use limited-risk structures (debit or credit spreads) | ✅ In principle, as risk hygiene. On cost: the spread-vs-outright claim from lV8Jkl37h4M is CONTRADICTED at real fills (second-leg friction −27.1pp, t −5.51; see the 2026-09-19 notes) |

## Exploratory check run for this review (not pre-registered, not a ledger row)

Script in the session scratchpad only (`rs_ushape.py`), about 2 minutes, local. `liquid_panel_2019`. House breakout =
close > prior 20-session high, ADR ≥ 3, eligible, 2019-10 → 2026-09. RS = cross-sectional percentile of the trailing
126d (his "3–12 months") or 252d return among eligible names on the breakout date. Outcome = forward close-to-close return
minus the same-date mean of eligible names **in the same ADR decile**. t = over per-date bucket means.

| RS lookback / horizon | bottom decile (D1) | D4–D7 | top decile (D10) | **U: (D1+D10) − D4..7, same-date** |
|---|---|---|---|---|
| 126d / 20d | **−1.61pp** (t −1.60; halves −0.45 / −0.78) | −0.65…−0.01 | +0.22 (t 1.31) | **+0.08pp, t 0.25** |
| 126d / 60d | **−4.00pp** (t −3.39; halves −2.89 / −1.88) | −0.35…+1.32 | +1.30 (t 3.31) | **+0.04pp, t 0.07** |
| 252d / 20d | −0.82 (t +0.43, pooled and date-weighted disagree) | −0.60…+0.11 | +0.44 (t 1.38) | +0.76pp, t 2.48, halves +0.51 / +0.94 |
| 252d / 60d | −2.31 (t −1.39) | −0.26…+1.40 | +1.49 (t 2.84) | +0.18pp, t 0.33 |

**Reading.** The shape is monotone-ish (weak at the bottom, better at the top), not a U. The one U-leaning cell is
12-month RS at 20d. It is the best of 4 cells, it does not reach t 3, and its t is inflated. ⚠ **Every t here is
overlap-inflated**: consecutive breakout dates share most of their 20/60-session windows, so the per-date means
are autocorrelated. Read the signs and the shape, not the t against the bar. Survivorship (the panel is names liquid
as of 2026) *flatters* D1, because beaten-down names that later died are missing. So the true bottom-decile figure
is likely worse. The pooled-vs-date-weighted sign disagreement at 252d/20d D1 means that cell is fragile.

## What I would take

1. **Nothing to adopt.** The detector's distinctive choice is to start with the lowest RS, and that is the cohort our
   vetoes (below the 200 SMA, 6-month return < −10%) exist to exclude. Today's exploratory check agrees with them on
   the 2019–26 panel.
2. **Keep the vetoes.** This is the first t-bearing look at them on the modern panel. The rotation study's cohort table
   that created them (§8) reports no t. Today's check is exploratory and overlap-inflated, but it points the same way.
3. **His framing is useful only as a warning.** "Early in the trend" and "a good entry" are different things. The
   first is what he sells. Our data says the second is where the leak is.

## Not tested, could be

### RS-decile U-shape at the breakout, as a confirmatory run (spec only, and low prior; I recommend NOT queuing it)

**Why it is weak.** Today's exploratory check already contradicts the claim in 3 of 4 cells. The bottom end is the
rotation study's vetoed cohort. RS as a selection lever has now failed five ways: group RS INVERTED, down-day RS
INVERTED (−3.51pp at 63d, t −3.33), the weak-tape leaders NULL leaning INVERTED (−0.69pp, t −1.50), the 52wk gate NULL
(t 0.14), and TT c9 RS ≥ 70 UNDERPOWERED (−0.090, t −0.95). Write it up only if Gabe wants the veto certified.

- **Universe / trigger:** `liquid_panel_2009` (the 2010–19 holdout comes free), house breakout, close entry.
- **RS:** 126d return percentile among eligible names, computed at t−1. That is fixed, not swept; 252d is the one
  declared neighbour.
- **Primary:** same-date paired `(D1 + D10) − mean(D4..D7)` of the 20-EMA-trail **% per trade**. Use non-overlapping
  20-session date blocks to fix today's overlap problem, with t clustered by block.
- **Secondary (the veto question, which is the useful one):** D1 vs D4–D7 alone, same date, ADR-matched.
- **Control that holds the confound:** ADR-decile matching on the same date. Report `ext_above_level_ADR` by decile,
  so a D1 result is not just a less- or more-extended entry.
- **Bar:** |t| ≥ 3, both halves the same sign, a per-year table, and Šidák k = 2.
- **Effort:** about an hour on top of `run_vcp_damped_sine.py`'s breakout mask and `pct_trade`.

### Prior-high target exit on beaten-down base breakouts (not specced further)

This is the one mechanically distinct idea in the video: exit at the prior 52-week high rather than trailing. It is
low prior for two reasons. Fixed-level exits cost money in every variant we have run (profit-lock row), and the cohort
it applies to (D1) is the worst entry cohort. A test is only worth writing if a D1 run ever comes back positive.

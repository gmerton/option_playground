# The Adhikary precision tier is a REGIME finding, not a selection finding (2026-09-23)

**Verdict: NULL for the precision tier as a selection layer. YIELD: REFRAME.** Pre-registered in
`run_precision_tier_freeze_forward.py` before the first run. Events: `precision_tier_freeze_forward_2026-09-23.csv`.

The published tier — **ADR 4–7, within 15% of the 52-week high, stack run 5–40 sessions** — reads
+0.67R against +0.16R for the generic archetype-A breakout. This asks whether that is a durable
cross-sectional sort or an artefact of when it was fit.

## ⚠ First: the queued test (TEST_INDEX §286) was not a test

§286 asks for a "precision-tier true OOS" on **2023 + 2025**. Those years are **inside** the
2019-10 → 2026-09 window the tier was fit on, and they are its two best years. Re-running the same panel
on them re-reads in-sample data and can only confirm. It was also mis-keyed: §286 carries `n = 17`, which
belongs to the **archetype-C exhaustion fade** (intraday 0DTE), not to this breakout tier, whose n is
~1,824 events. Both errors are corrected in the index.

## Method — temporal freeze-forward

| window | dates | events | role |
|---|---|---|---|
| FIT | 2019-10-01 → 2022-12-31 | 3,094 | re-derive all three thresholds from scratch, mechanically |
| TEST | 2023-01-01 → 2026-09-18 | 5,116 | apply the frozen bands; never inspected during the fit |

Fit rule declared before running: bucket each lever independently, keep buckets beating the pool mean by
**≥ 0.10R**, take the contiguous span. A lever with no qualifying bucket is **dropped**, not forced.

R = the house process: entry at the signal **close**, stop = that bar's **low with a 2% floor**, exit =
first close through the stop, else first close below the 20 EMA, else 60 sessions.
`R = (exit − entry) / (entry − stop)`. Reported at **cap 10 / cap 20 / uncapped**, because the
2026-09-19 control study showed the verdict slides t 3.9 → t 1.5 across exactly those cells.

## Q1 — the thresholds do not reproduce

Refit on 2019–2022 alone (pool mean R −0.144):

| lever | published | refit on 2019–2022 | recovered? |
|---|---|---|---|
| ADR | 4–7 | **5–7** | ✗ |
| stack run | 5–40 | **5–10** | ✗ |
| off 52wk high | > −15% | **no bucket clears the bar — lever DROPPED** | ✗ |

Not one band is recovered, and one of the three levers does not survive at all. The `off52` buckets in
the fit window run −0.507 / −0.216 / −0.222 / −0.051 — monotone-ish but never clearing the pool by 0.10R.

## Q2 — neither the refit tier nor the published tier certifies

**Refit tier (ADR 5–7, stack 5–10) carried forward into 2023–2026**, n = 198:

| cap | tier meanR | edge vs pool | t | halves |
|---|---:|---:|---:|---|
| 10 | +0.082 | −0.030 | −0.15 | −0.410 / +0.078 |
| 20 | +0.406 | +0.090 | +0.30 | −0.427 / +0.238 |
| none | +0.530 | +0.076 | +0.23 | −0.427 / +0.220 |

No edge at any cap, halves disagree at every cap, 28% win rate, median −1.04R.

**Published tier vs NON-tier archetype-A** (the fair contrast — 1,217 vs 3,899 events):

| window | cap | tier | non-tier | edge | t | halves |
|---|---|---:|---:|---:|---:|---|
| TEST 2023–26 | 10 | +0.319 | −0.052 | +0.139 | +0.92 | −0.152 / +0.242 |
| TEST 2023–26 | 20 | +0.681 | +0.073 | +0.352 | +1.73 | −0.250 / +0.565 |
| TEST 2023–26 | none | +1.144 | +0.099 | +0.817 | **+2.79** | −0.259 / +1.197 |
| **FIT 2019–22** | 10 | +0.006 | −0.291 | **−0.065** | −0.50 | — |
| **FIT 2019–22** | 20 | +0.121 | −0.231 | **−0.020** | −0.14 | — |
| **FIT 2019–22** | none | +0.135 | −0.225 | **−0.010** | −0.07 | — |

⭐ **In 2019–2022 the tier adds nothing** — edge ≈ 0 or negative at every cap. Its entire apparent
selection value appears in 2023+. And even there, **both halves disagree in sign at every cap**, and the
best t (+2.79, uncapped) is below the house bar of 3 and lives entirely in the right tail the cap removes.

## What is actually going on — archetype A by year

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| −0.41 | +0.06 | −0.20 | −0.36 | **+0.17** | **+0.42** | **+0.66** | +0.17 |

Everything breakout-shaped worked 2023–2025 and nothing did 2019–2022. The tier's headline is a
**regime** reading, and the three levers were chosen on a sample dominated by the good years.

## ⚠ Reconciling with the 2026-09-19 control study

That study reported **+0.60R over `xname`** and was read as "selection works." Its control is a random
**eligible name**, not a random **breakout** — so it measures *breakout vs non-breakout*, conflating
(a) being a breakout with (b) being a *precision* breakout. This study isolates (b) and finds it does not
hold. Both results stand; they answer different questions. Nothing here says breakouts don't work in a
breakout regime — it says the precision filter is not the reason.

## What this does and does not establish

* **Settled:** the ADR/off-high/stack precision filter is not a durable cross-sectional sort. Do not size
  on `precision=YES` as though it carried +0.67R of edge. It is a regime tag.
* **Not established:** that archetype A is worthless. The non-tier pool is also positive in 2023+.
* ⚠ **Survivorship is NOT controlled here.** `liquid_panel_2019.parquet` holds names liquid as of 2026, so
  both windows contain only survivors. A freeze-forward controls for *threshold* fitting, not universe
  construction. The survivorship-free version (point-in-time universe from `silver.equity_daily`) was
  queued as the follow-on and is now **moot** — the cheap gate failed first, which is why it ran first.

## This is the fourth independent angle with the same answer

Within-date ranking NULL (t −0.11), the universe test, the Trend-Template ablation (two criteria
logically redundant), and now this. **Mechanical selection does not improve the breakout book.** The
measured leak remains the **entry**, not the screen.

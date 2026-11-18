# Former leaders: a human read of how the top-250 gainers actually moved (2026-11-17)

**Verdict: DESCRIPTIVE, hypothesis-generating only. Nothing here is evidence that a rule selects winners.**
Prompt (Gabe, via Ariel Hernandez): study the charts of past leaders for repeatable entry/exit tactics (EMAs,
volume, pullbacks vs breakouts), daily/weekly, human perspective first; computation later.

- Universe: `data/top_gainers/` (top 250 US gainers over 1Y / 3Y / 5Y to 2026-06-03, commit 4f29579).
  505 of 511 names priced (yfinance adjusted, `run_top_gainers_pull.py`; CNTA, CPRX, ESPR, KORE, LIXT, SSSS missing).
  6 runs dropped because their history starts after the window (WOLF post-reorg, etc.): **728 runs**.
- Scripts: `run_top_gainers_chart_study.py` (per-run stats + charts); trend-phase pass in
  `top_gainers_chart_study_2026-11-17_trend_phase.csv`. Per-run rows: `top_gainers_chart_study_2026-11-17_runs.csv`.
- Charts (24, fixed sample: top 4 + 4 random from ranks 100–250 per list, seed 17): `charts/top_gainers/`.
  16 were read by eye for §1.
- **Repeatable only:** every event is defined on that bar's close: first close at a new 52-week high, close
  below the 21 EMA, weekly close below the 10-week, and so on. "The low" is never an entry.

> ⚠ **Outcome-conditioned by construction.** These names were picked *because* they went up. "Pullbacks held
> the 50" is true of these winners and also of an unknown number of names that then died. This study can say what
> a winner's path looks like and what a rule **costs you on a winner** (missed move, shakeouts, giveback). It
> cannot say a rule finds winners. The population tests that can say so are in the ledger, cited in §4.

---

## 1. What the charts look like (human read)

**Two families, not one.**
- **Trend leaders** (AXTI, SNDK, SPHR, CLS, STRL, STRO): one clean Stage 2. They spend a long time in a base
  under a falling 40-week MA, then cross a **flattening** 40-week. After that, weekly closes ride the 10-week
  for 6–12 months. Daily pullbacks mostly tag the 21 EMA, with a 50-day test once or twice a year. Corrections
  are mostly **sideways in time** rather than deep in price: SNDK Nov–Dec and Mar, SPHR Jan–Mar.
- **Cyclical / multi-wave names** (AAOI, CLSK, FORM, AEHR, YPF, DAVE, NEXT, UMAC): two or three separate
  advances with **40–60% drawdowns** in between, closing below the 40-week. AAOI fell about 60% in 2024.
  FORM went nowhere for four years and made the whole move in 2025–26. A "3-year winner" is usually a
  1-year winner plus noise.

**Launch.** The move almost always starts with price reclaiming a 40-week MA that has stopped falling, after
a long base. The first real leg usually comes with clearly higher volume than the base: CLS Jun-23, DAVE
Jan-24, SNDK Sep-25, FORM Oct-25. AXTI is the exception: its volume arrived months after the move began.

**Tops.** Almost every top is a **climax**: the slope steepens, gaps appear, and price sits far above the
10-week (AXTI May-26, STRL May-26, FORM Apr-26, WOLF, STRO). Then comes the first weekly close below the
10-week, and later a 50-day break on heavy **red** volume (STRL Jul-26, STRO Jun-26). The first exit signal
was rarely the high, but it was always far above where the stock ended up.

**Lower-ranked names (#100–250)** are choppier. UMAC and NEXT made much of their move in a handful of gap
days and chopped around the EMAs in between. EMA rules look far worse on these than on the top-10 names
people remember.

## 2. Numbers across all 728 runs (median [IQR])

### Launch: how much did a repeatable entry miss?
| | 1Y | 3Y | 5Y |
|---|---|---|---|
| start price vs 52w high | −42% [−61, −26] | −26% | −11% |
| sessions to first close at a new 52w high | 67 [31, 127] | 70 | 92 |
| **share of the log move still ahead at the first 52w-high close** | **66%** [52, 82] | 88% | 97% |
| RVOL on that first 52w-high day | 1.86× [1.18, 4.25] | 1.80× | 1.49× |
| share of the move ahead at the first reclaim of a rising 50-day | 89% [64, 97] | 93% | 100% |

On 1Y names, waiting for proof (the first new 52-week-high close) still left **two-thirds** of the move. The
50-day reclaim comes earlier, but nothing here says how often it fails. The ledger says it often does: see §4,
Weinstein H2.

### Trend phase (first 52w-high close → peak): where did pullbacks stop?
Pullback = a close-to-close decline of at least 1.5 ATR from a closing high, ending at the next new closing
high. Each pullback is labelled by the deepest MA its lowest **close** stayed above.

| support at the pullback low | 1Y | 3Y | 5Y |
|---|---|---|---|
| stayed above the 10 EMA | 10% | 7% | 5% |
| **held the 21 EMA** (closed below the 10) | 22% | 18% | 16% |
| **held the 50 SMA** (closed below the 21) | **35%** | 30% | 29% |
| below the 50, held the 200 | 28% | 31% | 32% |
| closed below the 200 | 5% | 14% | 18% |
| median depth | 17% | 15% | 12% |
| pullbacks per run | 4 | 10 | 15 |

**Even on the best 1Y winners, a third of meaningful pullbacks closed below the 50-day.** The 21 EMA held
only about one time in five. A rule that waits at the 21 EMA buys a pullback that then goes lower most of
the time.

### Volume
| | 1Y | 3Y | 5Y |
|---|---|---|---|
| up-day vol ÷ down-day vol (whole run) | 1.22 [1.06, 1.54] | 1.12 | 1.06 |
| RVOL on new-50-day-high closes | 1.24 | 1.20 | 1.12 |
| volume during pullbacks ÷ 50d avg | **1.00** [0.85, 1.17] | 0.99 | 0.99 |

There is an accumulation signature (more volume on up days), but it is modest. **Pullbacks on these winners
were not dry.** They traded at average volume. The textbook "volume dries up on the pullback" is not the
typical path of a top-250 winner.

### Exits: what each trailing rule costs
| | 1Y | 3Y | 5Y |
|---|---|---|---|
| closes crossing below the 21 EMA during the trend phase | 8 | 36 | 68 |
| closes crossing below the 50 SMA | 3 | 18 | 35 |
| **single trip** from the first 52w-high close, share of the move kept: exit on close < 21 EMA | **3%** | 0% | −2% |
| ‥ close < 50 SMA | 15% | 1% | −3% |
| ‥ 2 closes < 50 SMA | 19% | 1% | −3% |
| ‥ weekly close < 10-week | 19% | 0% | −3% |
| ‥ weekly close < 40-week | **50%** | 5% | −4% |
| giveback from the peak at the first close < 21 EMA after it | 15% | 13% | 10% |
| ‥ first close < 50 SMA after the peak | 20% | 17% | 14% |
| peak → today (2026-11-16) | **−50%** [−67, −33] | −44% | −35% |
| max (close − SMA50) ÷ ATR during the run | 7.1 | 7.8 | 7.9 |

Context: SPY −1.4%, QQQ −10.9%, IWM −4.6% over 2026-06-03 → 11-16. The −50% is mostly the names, not the tape.

Multi-year lists: the median 3Y winner made **63%** of its log gain in the final 12 months before its peak,
and the 5Y winner 51%. About **45–48% drew down more than 50%** along the way.

## 3. Answers to the questions

1. **EMA entry points.** No single EMA is "the" line. The 21 EMA held about 1 in 5 meaningful pullbacks and the
   50 about 1 in 3. Pullbacks closing below the 50 were common even on the best names. If a human uses EMAs, the
   repeatable version is **the reclaim, not the touch**: wait for the close back above the 10 or 21 EMA after a
   pullback, with the stop under that pullback's low. A limit order at the line is not repeatable. On a winner
   the line breaks about four times out of five, so the limit fills early and the stop beneath it gets hit
   with it.
2. **Volume.** It matters at the **launch** (first 52w-high day median 1.8× average; the first leg is usually
   on visibly higher volume than the base) and at the **top** (a high-volume red week after a climax). It is a
   weak guide in between: pullbacks were not dry, and the up/down volume ratio is only 1.1–1.2×.
3. **Pullbacks vs breakouts.** Both were present in every winner: 4 to 15 pullbacks and repeated new 50-day
   highs. Once a name was a leader, either entry was available many times. The real problem is the **exit**.
   Every daily trailing rule taken as a one-shot trade kept 3–19% of a 1Y winner's move. Only the weekly
   40-week rule kept half, and it gave back 20%+ from the peak. **On a leader the tactic that matters is
   re-entry:** get stopped out cheaply, then get back in on the next repeatable trigger, either a reclaim of
   the 21 or a new 50-day-high close. Watching Luk and Ariel, that is how they actually trade these names.
4. **Ariel's 4×-ATR-over-the-50 ceiling.** Winners ran to about 7–8× ATR over the 50 at their peak, so the
   ceiling works as a **don't-add / don't-initiate** rule, which is how he states it. Used as an exit, it
   would have cut most of these runs short.
5. **Tops.** Climax, then the first weekly close below the 10-week. The median name then fell another 50% in
   five months. On a former leader, the cost of not exiting is much larger than the cost of exiting early.

## 4. What the ledger already says (do not re-test)
- Pullback entries on leaders vs the breakout: **FAIL** (`pullback_entry_study_2026-09-17.md`). Waiting for the
  20-EMA zone vs the breakout close: **NULL, regime flip**. Waiting won 2010–22 and the breakout won 2023–26
  (TEST_INDEX, `run_breakout_vs_pullback_entry.py`).
- Volume at the pullback low: **NULL 0/12**. High turn-day volume finds lows that hold, but price already
  reflects it. Dry pullbacks hold *less* (`volume_low_signature_2026-09-25.md`). That matches the
  "pullbacks weren't dry" finding above.
- Weinstein Stage 1→2 weekly breakout: **NULL**. The first reclaim of a still-falling 30-week MA is
  **INVERTED** (a fade). The "reclaim of a flattening 40-week" in §1 is what winners did. As a stand-alone
  entry it has already failed on the full population.
- Exits: 20-EMA trail vs profit locks, Qullamaggie's partials, swing-low trail, RS-loss and vol-decay exits: all
  NULL or FAIL against the 20-EMA trail on breakout trades. Those were single-trade tests, though. **None
  measured a re-entry loop on the same name.**

## 5. Candidate hypotheses for the computational phase (new axes only)
1. ~~**Re-entry loop on an established leader**~~ **RUN 2026-11-17: INVERTED** (B1 − A −1.3% to −2.4%, t −3.2 to −9.1; NULL vs hold). Re-entry recovers the move on the 3% that double and costs it on the rest, so §3.3 was outcome conditioning. See `leader_reentry_loop_2026-11-17.md`. Original text: after the first 52w-high close, trade the name repeatedly.
   Exit on a close below the 21 EMA (or 50 SMA), re-enter on the next reclaim / new 50-day-high close. Score
   total capture vs single-trip and vs buy-and-hold, **on the full population of names that made a first 52w
   high**, not on these winners. This is the gap §3.3 points at.
2. **Climax exit** (partly new): sell when (close − SMA50)/ATR ≥ 7 plus a gap or weekly-range expansion, vs the
   20-EMA trail. Check first against the existing extended-first-failure short row (TEST_INDEX, 2026-10-01).
3. **Launch volume gate**: a first 52w-high close on RVOL ≥ 1.5 vs < 1.5, full population. Check against the
   precision-tier RVOL gate ablation (`run_precision_gate_ablation.py`) before running.

Any of these must be run on the point-in-time population (`chain_spot_daily` incl. delisted, or the liquid
panel with its survivorship caveat), never on this list.

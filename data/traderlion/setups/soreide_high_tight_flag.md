# High Tight Flag (HTF) -- Leif Soreide

> **Verdict:** A clean, mostly codable definition of O'Neil's rarest pattern, from a trader who shows some of
> his losers. There is **no evidence**: no base rate, no count, winners-first case studies, and both headline
> numbers ("90%+ winners", "+222% in 27 days") are **absent from the videos**. The management rules he gives
> (scale at 1-3R, sell 100% round numbers, pyramid) are contradicted or NULL here. The one idea on the right side
> of our data is his **early entry inside the flag** (low-volume inside day), which buys below the flag high.
> **Type:** swing · **Instrument:** US equities
> **Conviction:** 1.5/5 · **Risk:** 7/10 (extreme-momentum names, ADR 5-10%, gap risk) · **Tested?** **no**
> **Sources:** [2024-10-09 clip, 12 min](../videos/interviews/2024-10-09_mpe2_FCfpRg/notes.md) ·
> [2024-10-27 podcast, 50 min](../videos/interviews/2024-10-27_rdmjsbDVuoU/notes.md)

---

## 1. Who, and what's being sold

Leif Soreide, billed as 2019 USIC champion (figure, division and size not stated on camera). The podcast is a
promo for his paid **HTF Masterclass** + "model book"; he runs a members' platform; a Deepvue scan carries his
name. He trades alongside the 2024 contest leader (Champion Team Trading). The discretionary layer ("think beyond
the pattern", themes, shakeout grades, dollar levels) is the part held back for the class.

## 2. Mechanics as stated (timestamps: C = 2024-10-09 clip, P = 2024-10-27 podcast)

- **Pole:** >= 90% rise, 100%+ preferred, in <= 8 weeks, measured from the low [C 01:02, C 02:24, C 06:22]. A
  smooth ~45-degree rise; a base inside the pole is "almost a strike against it" [C 06:46]. "Skyscraper" bars in
  the pole [C 09:11]. Not an HTF if the rise from the relevant level is only ~40% [P 15:01].
- **Flag:** 3-5 weeks standard; as short as 7 days; IPOs get half the time rule [C 02:40, C 05:33]. Depth ~25%
  tolerance, a bit more "with a more powerful rise" [C 08:07-08:22]. Volume declines from the pole top to the
  flag low [C 02:55].
- **Rocket base:** a failed HTF that corrects 25-50% and rebuilds over 6-10 weeks [P 13:01].
- **Entry:** (a) the pivot (flag high) on a volume trigger, e.g. 10x RVOL [C 05:03, C 08:36]; (b) preferred:
  **early, on a low-volume inside day** ("dead volume, lowest volume in 10 days") inside the flag, stop under the
  inside-day low [P 10:02, P 26:01-27:01]; "these highs are always sloppy" [P 25:01].
- **Stop:** ~5%, staggered under a prior inside-day low [P 22:44].
- **Management:** scale from ~1R (difficult tape) to ~3R [P 23:00, P 43:40]; sell into +20% (= 4R at a 5% stop)
  [P 27:01]; sell into 100% round numbers [P 37:40]; wind down to <= 25% trailing size [P 39:00]; out on a roll
  under the 50-day [P 36:40].
- **Context:** bull market / his own red-green signal [C 02:17, C 07:55]; price >= $10 preferred, never < $5
  [P 18:40].

## 3. Claimed edge and returns

None stated on camera. "90%+ winners" is the thumbnail's reading of the 90% pole. "+222% in 27 days" is in the
title and description only.

## 4. Objective assessment

- The pattern is selected on the most extreme trailing return in the market. Any test must separate **the flag**
  from **the momentum**. A +90% name breaking out may just be a momentum effect or the house breakout, with the
  flag adding nothing.
- Rare: on a liquid, $5+, $50M-ADDV panel from 2019, the event count could be small. The small caps where HTFs
  cluster are outside the panel.
- The discretionary allowances (IPO halving, "more room with a more powerful rise", "context is key", "if you
  have to argue it's not the best one") mean any single failure can be explained away. Only a fixed pre-registered
  spec can be scored.

## 5. What's genuinely sound

The definition is concrete. He shows losers. Entering early inside the flag lowers the entry price, which is the
only entry direction our data has rewarded. "Best loser" framing is correct for a 30%-win right-tail book.

## 6. Overlap with the existing book

House breakout (close > prior 20d high, ADR >= 3) is the natural comparison; VCP damped sine (NULL) covers
"tightening"; trend smoothness (NULL) covers "smooth pole"; profit-lock and pyramid tests (FAIL/NULL) cover his
management. **The pole requirement and the early inside-day entry are new.**

## 7. Codable spec (daily bars, pre-registerable) -- NOT RUN

Liquid panel (`data/cache/liquid_panel_2019.parquet`, has `volume`), eligibility as of the signal date (ADDV >=
$50M, px >= $5, not suspect), 2019-10 onward. All windows use data up to and including the signal close only.
**Default [discretionary range]**; parameters he states are marked (S), house defaults (H).

| # | Element | Rule | Source |
|---|---|---|---|
| 1 | Pole top | `p` = the session of the highest high in the last 60 sessions (flag window + pole) | (H) |
| 2 | Pole rise | `H_p / min(low[p-40 .. p]) - 1 >= 0.90` **[0.90, 1.00]** (<= 8 weeks = 40 sessions) | (S) C 01:02 |
| 3 | Pole quality | no sub-base inside the pole: no 10-session window within the pole whose high-low span is <= 3 ADR **[on/off]** | (S) C 06:46, threshold (H) |
| 4 | Flag length | sessions since `p`: **10-25** [5-25; 7 per C 05:12] | (S) C 02:40 |
| 5 | Flag depth | `1 - min(low[p+1 .. t]) / H_p <= 0.25` **[0.20, 0.33]** | (S) C 08:07 |
| 6 | Volume dry-up | mean volume over the flag <= **0.6x** [0.5-0.8] mean volume over the pole | (S) C 02:55, ratio (H) |
| 7 | Tightness (optional) | last 5 sessions span <= **2 ADR** [1.5-3] | (S) P 10:02 |
| 8 | Price floor | close >= $10 | (S) P 18:40 |
| **A** | **Trigger: flag breakout (PRIMARY)** | first close > `H_p` with RVOL (volume / 50d mean) >= **1.5** [1.0-3.0]; entry at the close | (S) C 05:03 |
| B | Trigger: early inside-day entry | inside day (high < prior high, low > prior low) with volume = 10-session minimum inside the flag; entry = first close above that inside day's high within 3 sessions; stop = inside-day low | (S) P 26:01 |
| C | Rocket base | as A but depth <= 50% and flag length 30-50 sessions | (S) P 13:01 |

- **Stop:** A = min(low of the last 5 sessions) (flag's final contraction), C = flag low, B as above; judged on
  the close; also report stop/ADR and stop %, floor 0.5% (harness `MIN_RISK`).
- **Exit:** first close < 20 EMA (house) **primary**; arm: first close < 50-day SMA (his rule [P 36:40]); cap 60
  sessions; 0.10% slippage a side. No scale-outs (tested separately; they cost).
- **One signal per name per pole** (the first trigger).

## 8. Pattern_test design (sketch, NOT RUN)

**Question:** does the HTF breakout beat an ordinary breakout on the same day, and does the flag add anything
beyond the pole's momentum?

- **Implementation:** pattern function via `lib.studies.pattern_test.load_panel()` + `daily_signals(hit, stop)`,
  run with `entry_at="close"`, `ledger=True`, for the ledger row. `control="post"` and `"xname"` are run for
  bookkeeping only. **They are not the primary comparison.** The harness `xname` draws a random *eligible name*,
  not a random *breakout* (the 2026-09-19/23 lesson), and `post` is a same-name window after the signal, which the
  VCP retraction showed is outcome-selected.
- **Primary control (custom, as in `run_vcp_damped_sine.py`):** for every HTF signal on date d, all **house
  breakouts on the same date in other names** (close > prior 20d high, ADR >= 3, eligible). Same entry (close),
  same exit rule, **stop for the control = its own entry-day low**. Paired diff = HTF % return - mean control %
  return that date. **Score in percent, not R** (stop definitions differ; house rule 2026-09-23).
- **Secondary control, holding the momentum fixed (the key one for the flag claim):** same-date house breakouts
  in other names whose **40-session return is also >= 90%** but which fail rules 4-6 (no flag). If HTF beats
  generic breakouts but not momentum-matched ones, the flag adds nothing and the result is a momentum effect.
- **Tertiary (within-setup timing):** arm B vs arm A **on the same poles** (both fire on ~some share of poles):
  isolates entry location, the one variable with a measured mechanism (report `ext_above_level` in ADR for each).
- **Same-name control, if any:** only breakouts in the same name ending before the pole starts (`p - 40`),
  never after the signal.
- **Pre-registered bar:** primary = arm A vs same-date house breakouts, % return at the 20-EMA exit.
  Date-clustered |t| >= 3, both chronological halves the same sign, and **per-year signs reported** (halves miss a
  back-half regime). Cells: 3 arms x 2 exits = 6 -> Sidak |t| >= 2.64; the house 3.0 governs.
- **Power gate, before any return is computed:** count arm-A events. If n < ~300 or effective dates < ~150,
  report **UNDERPOWERED** and stop. **Do not loosen rules 2, 4 or 5 after seeing the count.** A larger universe
  (pre-2019, sub-$50M ADDV) would be a separate, pre-registered extension.
- **Prior:** ~70% NULL. The VCP (tightening) failed; the extension mechanism says a breakout from a +90% name buys
  the extended end; the within-date rank test says less-extended candidates are *weaker* at a fixed date, which
  cuts the other way. Arm B beating arm A is the likeliest positive finding.
- **Clean-result check:** outcome conditioning is the first suspect. The pole is measured to the highest high
  *before* the signal, so no post-signal data enters; verify it in code by asserting every window ends <= t.

## 9. Testability

EOD-testable now (daily OHLCV + volume on the liquid panel). Intraday inside-day buy stops need 1-min bars
(cache covers ~2026 only); the daily approximation is arm B.

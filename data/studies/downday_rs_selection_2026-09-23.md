# Down-day relative strength as a selection filter — **INVERTED** (2026-09-23)

**Verdict: INVERTED at 63 days. The filter is negative, with a monotone dose-response.**
Pre-registered in `run_downday_rs_selection.py` before the run (TEST_INDEX §125).
Cells: `downday_rs_selection_2026-09-23.csv`.

## The claim

SMB Capital, *"Revealing My Secret Relative Strength Breakout Strategy"* (reviewed 2026-09-22, **3/5** —
the highest in that cohort). On a genuinely weak tape, names that **refuse to fall** are being
accumulated: institutions work orders over days and use market weakness to fill. *"Weakness in the market
is what makes strength visible."* The filter is flat-or-green while the index flushes, **more than once**,
and near the 52-week high — explicitly not mid-range. He is careful that it is **not an entry**:
*"relative strength on its own is not an entry, it's an alert."* It ranks the watchlist; the trade is
still the first close over resistance.

**Why it was worth running when five angles already say selection cannot be improved:** unlike the five,
this one has a *mechanism* and a precedent at another scale — the rotation study's Part III found
bottom-3-sector, volume-confirmed breakouts at **+5.6pp, t 2.61**. Its process also independently matches
the house process (rank don't buy, close trigger, stop at the day's low, earnings veto).

## Method

| | |
|---|---|
| down day | QQQ closes **≤ −1.5%** — 222 such days |
| RS event | on a down day, a name closes **flat or green** and sits **within 15%** of its 52-week high — 25,929 events |
| dose | count of RS events in the trailing **20 sessions, shifted 1** so the dose is fully known before the entry bar |
| entry | the next **breakout close**: close > prior 20-session high, ADR ≥ 3, eligible — 43,828 breakouts |
| comparison | **within-date** mean forward return, RS-dosed breakouts vs undosed, same pool |

Panel 2019–2026, 1,725 names. Within-date because a down-day filter is mechanically correlated with the
calendar — comparing across dates would measure the regime, not the name.

## ⚠ The first cut was uninterpretable — the control varied two things

The unmatched run returned −1.00pp (21d) and −2.75pp (63d). **Those numbers do not mean what they appear
to**, because the RS definition *bundles* two conditions: held up on down days **and** within 15% of the
52-week high. So the comparison cohort was structurally different:

| at the breakout bar | n | ext21 | **off 52wk high** |
|---|---:|---:|---:|
| dose ≥2 (RS) | 2,796 | +2.69 ADR | **+0.55%** |
| dose == 0 | 36,074 | +2.66 ADR | **−18.25%** |

It was a near-high vs below-high test, not a relative-strength test. ⭐ Note also that **extension is
identical** (+2.69 vs +2.66 ADR) — the leak this book keeps finding is *not* the mechanism here.

## The matched result — both cohorts within 15% of the 52-week high

| horizon | dose | RS | non-RS | **edge** | **t** | halves |
|---|---|---:|---:|---:|---:|---|
| 21d | ≥1 | +0.83% | +1.41% | −0.57pp | −1.45 | −1.12 / −0.11 |
| 21d | ≥2 | −0.38% | +0.40% | −0.78pp | −1.49 | −1.34 / −0.23 |
| 63d | ≥1 | +5.80% | +6.73% | −0.92pp | −1.34 | −0.58 / −1.23 |
| **63d** | **≥2** | **+3.99%** | **+7.50%** | **−3.51pp** | **−3.33** | **−2.81 / −4.33** |

n = 2,796 dosed vs 17,151 matched undosed.

**Clears the house bar (|t| ≥ 3) and the Šidák charge for 16 cells (2.96) — in the negative direction.**

Two features argue it is real rather than noise:
* **Monotone dose-response** — dose ≥1 is −0.92pp, dose ≥2 is −3.51pp. More of the recommended condition,
  worse the outcome. The video specifically asks for **more than once**.
* **It grows with horizon** (−0.78pp → −3.51pp), the shape of a drift effect rather than an isolated cell.

## Mechanism — a hypothesis, not a finding

His logic is that refusing to fall reveals institutions accumulating. The data is consistent with the
accumulation having **already happened**: by the time a name has absorbed several index flushes while
sitting at its highs, the demand has been filled, and the subsequent breakout is bought *after* that
demand rather than alongside it. It is explicitly **not** an extension effect — ext21 matched exactly.

## What this does and does not establish

* **Settled:** down-day relative strength, as specified, is not a positive selection filter on this panel.
  At dose ≥2 / 63d it is **negative at significance**. Do not use it to rank a watchlist long.
* ⚠ **The RVOL prior was wrong.** Pre-registered expectation was "positive, but explained by RVOL". It is
  negative from the start and *more* negative inside the RVOL ≥ 1.8 cohort (−5.27pp at 63d), so volume
  confirmation does not absorb it.
* ⚠ **Not established: that it is a short signal.** −3.5pp over 63 days against a cohort that itself earns
  +7.5% is relative underperformance, not an absolute negative.
* ⚠ **Untested parameter:** the 20-session lookback was fixed and deliberately **not swept** — sweeping
  invites the overfitting that produced the retracted UR band result the same day.
* ⚠ **Survivorship:** the panel is names liquid as of 2026, the standing caveat on every study using it.

## Method note worth carrying

This is the second time in one day that a control turned out to vary the wrong dimension — the first was
the ORB9 name-split control, which moved the *names* when the question was the *trigger*. The rule added
to CLAUDE.md that morning (**name what the control varies**) is what caught this one. Without the matched
re-run, the first cut would have been reported as a −2.75pp null and would have been measuring
52-week-high proximity instead.

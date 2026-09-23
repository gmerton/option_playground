# The intraday alert suite, re-examined (2026-09-23)

**Verdict: ORB9 INVERTED · FBO INVERTED · UR NULL as a trigger.** Four linked tests, all pre-registered.
Scripts: `run_ur_fbo_stop_floor_study.py`, `run_orb9_trigger_control.py` (`KIND=UR` for the UR pass),
`run_ur_vwap_band_sweep.py` (**retracted — see §5**). Data: `ur_fbo_stop_floor_2026-09-23.csv`,
`orb9_trigger_control_2026-09-23.csv`, `ur_trigger_control_2026-09-23.csv`.

Sample throughout: curated watchlist only, 2026-02-02 → 2026-09-10, 153 sessions.
UR n=4,855 · FBO n=3,175 · ORB9 n=1,411.

---

## 1. The question that started it — should UR and FBO get ORB9's stop floor? **NO**

A 0.60-ADR floor was adopted for **ORB9 only** (2026-09-21) after its structural stop proved pathological:
median **0.15 ADR**, 96% under 0.4, and a **73% stop-out rate**. UR and FBO were never re-run.

| | median emitted stop | share < 0.4 ADR | stop-out | best floor helps? |
|---|---:|---:|---:|---|
| ORB9 | **0.15 ADR** | 96% | 73% | **yes — large** |
| UR | 0.33 ADR | 68% | 40% | **no** |
| FBO | **0.50 ADR** | 16% | 22% | **no** |

* **UR** — stops are tight, but flooring them does not help: % return is flat to 0.4 ADR then declines
  (+0.109 → +0.097 at 0.6 → +0.094 at 1.0), and the halves disagree (A +0.160→+0.186, B +0.060→+0.006).
* **FBO** — ⚠ **the premise was wrong.** Its median stop is already 0.50 ADR with only 16% under 0.4. The
  0.48 seen on 2026-09-22 was near its median, not an outlier. It also loses at every width, so the stop
  is not what is wrong with it.

Only ORB9 was ever in the pathological regime. **The floor stays ORB9-only.**

## 2. ⭐ The methodological finding — judge stop widths in PERCENT, not R

Re-checking the live ORB9 floor exposed a trap that nearly fooled me in both directions:

| ORB9 curated (n=1,411) | mean R | t(R) | stop-out | **return %** | **t(%)** |
|---|---:|---:|---:|---:|---:|
| base (0.15 ADR) | **0.431** | 1.90 | 72.6% | 0.187 | 3.01 |
| floor 0.4 | 0.133 | 4.25 | 34.8% | 0.306 | 3.86 |
| **floor 0.6 (live)** | 0.109 | 4.91 | 17.4% | **0.352** | **4.21** |
| floor 1.0 | 0.068 | 4.86 | 5.3% | 0.362 | 4.16 |

**Mean R falls as the floor widens while the actual return nearly doubles.** `R = return ÷ risk`, so
changing the stop changes the denominator — any stop-width comparison scored in R is partly an artefact.
The base R of 0.431 is inflated by tiny denominators, the same unfillable-stop effect that produced 762R
in the precision-tier work. **On the honest column the live 0.60 floor is better supported than the R
column suggested.** It stays.

## 3. ⭐⭐ ORB9 is INVERTED — worse than a random minute in its own window

The name-split control (`universe_study_extra.txt`, n=371) was the wrong control: it varies the **names**,
not the **trigger**, and it was far too small. The right test holds the name-day fixed and moves only the
entry minute. Same 0.6 ADR stop, hold to the session close, 3 control draws averaged:

| | per trade |
|---|---:|
| Random **other** curated name, same minute | **+1.029%** |
| Same name, **random minute** in ORB9's own 09:45–12:00 window | **+0.775%** |
| **ORB9 trigger** | **+0.351%** |

**SIGNAL − POST = −0.425pp, date-clustered t −8.50, both halves agreeing** (−0.440 / −0.407).
vs a random peer name: −0.687pp, t −6.01.

ORB9 fails twice: it picks the **weaker names** that day (0.775 vs 1.029) **and** the **worse minute** in
them (0.351 vs 0.775). The +0.352%/trade that looked strong was the curated watchlist's intraday drift —
the trigger captured less than half of what was available.

⭐ **Mechanism: this is the entry-extension finding in intraday form.** ORB9 buys a break of the
opening-range high, i.e. it buys strength, and therefore enters near the high of the move. Identical in
shape to the daily result where the control beats the breakout signal.

⚠ Honest confound: the random-minute control enters earlier on average, and earlier is better on an
up-drifting day. That **is** the finding — if the name is already chosen, waiting for the break costs you.

## 4. UR is NULL as a trigger — but it is not destructive

Same test, UR's own 09:40–15:00 window:

| | per trade |
|---|---:|
| Random other curated name, same minute | +0.218% |
| Same name, random minute | +0.064% |
| **UR trigger** | +0.097% |

**SIGNAL − POST = +0.033pp, t −0.31, halves disagree** (−0.017 / +0.081) → **NULL**.
vs a random peer name: **−0.121pp, t −4.55**.

So UR ≈ random timing on the same name (unlike ORB9, which destroys value), but still loses to simply
picking another name off the watchlist.

**What UR's apparent edge actually was.** Against the *name* control UR reads +0.148pp at t 3.19 with both
halves positive — the best of the three. That measures **the curated universe**, not the UR pattern. It is
the standing finding restated: *conviction selection is the strategy; the intraday machinery is execution
insurance.* And at +0.109%/trade gross against ~0.05–0.10% round-trip friction, most of it is eaten anyway.

⚠ UR reclaims **VWAP**: armed by a 1-min close 0.10% under it, triggered by a close 0.10% above, after a
flush ≥0.25 ADR, session low before 11:00, a higher low printed, nothing before 09:40.

## 5. ⛔ RETRACTED — the VWAP band sweep was pure look-ahead

`run_ur_vwap_band_sweep.py` swept the reclaim band (−0.20% … +0.40%) and returned a **perfectly monotone
gradient**: −0.20% → +0.523%/trade vs the live +0.10% → +0.214%, "beating" live by +0.321pp at **t 27.8**,
both halves agreeing, three bands clearing every pre-registered gate. **It is invalid.**

Every alert in the sample exists *because* price went on to clear VWAP by +0.10%. A lower band is
therefore only ever evaluated on occasions where the reclaim succeeded:

* **93.7%** of −0.20% entries land **before** the actual trigger
* **84.1%** land **exactly on the arm bar — the low of the dip**

It buys the bottom of a dip already known to recover. The dips that fire a low band and never come back
are structurally absent. The `n` column said so and was read past: low bands keep all 4,855 alerts (a
100% fire rate *by construction*) while +0.40% drops to 1,473.

Same failure as the retracted exhaustion fade — conditioning on the outcome, then trading it. **The tell
was the result itself**: a large, monotone, t-27 effect in a domain where nothing works.

**Testing the band properly** requires re-running the UR detector at each band across all name-days so
each band generates its own alerts *including its failures* — a real build. Not recommended: UR's trigger
has no edge over a random minute, so tuning it is optimising inside noise.

---

## What to do

| | action |
|---|---|
| **FBO** | **Remove.** Negative on curated names (−0.148%/trade, t −3.80), worse than the name control (−0.126pp), both halves. Floors make it worse. |
| **ORB9** | **Do not trade the trigger.** Inverted at t −8.50. The 0.60 floor stays for anything still watched, since it is the better stop. |
| **UR** | **Keep, unfloored**, as an attention cue only. Not an entry edge. |
| the suite | Consistent with the alert-funnel test (alerts add nothing beyond the daily state) and Stage A (every intraday arm ≈ a random later minute). **This closes the UR/FBO stop-floor item.** |

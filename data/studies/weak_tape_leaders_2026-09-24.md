# Stocks that hold up in a weak tape (2026-09-24)

**Question (O'Neil; TEST_INDEX §10, queued 2026-09-20):** when breadth washes out, do the names still near their
52-week high beat the field once breadth recovers? Timely: breadth has been in a washout episode since 2026-09-15.
**Script:** `run_weak_tape_leaders.py` (pre-registration in the docstring). Log `data/studies/logs/weak_tape_leaders.log`,
per-episode table `weak_tape_leaders_2026-09-24.csv`.

**Design.** `liquid_panel_2009`, 2010 → 2026, point-in-time eligible names. Breadth = % of eligible names above the
50 SMA. **Episode** = first close < 35% after breadth was ≥ 45% (60 episodes; one observation each). **STRONG** =
within 10% of the 252-day high that day; control = the rest of the field, **ADR-matched** by band. Entry at that close,
no stop (a state test).

## Result

| | mean excess (pp) | t | % episodes + |
|---|---|---|---|
| **PRIMARY: 40 sessions, ADR-matched** | **−0.69** (median −0.28) | **−1.50** | 48% |
| halves pre-2018 / 2018+ | −0.30 / −1.04 | −0.56 / −1.42 | |
| 20 sessions | −0.35 | −1.02 | 53% |
| 60 sessions | −0.87 | −1.60 | 40% |
| 40 sessions, raw (no ADR match) | −0.91 | −1.38 | |
| every washout day (overlapping, descriptive) | −1.28 | — | |
| WAIT: same names bought when breadth recovers ≥ 50% | −0.65 | washout − wait −0.04 (t −0.10) | |

**FAIL — NULL, leaning INVERTED.** Names that hold up in a washout do **not** beat their ADR peers through the
recovery; if anything they lag, most in the sharp V-recoveries where the beaten-down field snaps back hardest
(2011-12 −5.7, 2016-06 −7.5, 2020-10 −6.4, 2022-06 −8.2). The survivor panel flatters STRONG, so the true figure is
likely a little worse. Buying them *during* the washout vs *after* recovery makes no difference (−0.04pp).

**YIELD MECHANISM.** Relative strength in a washout is not a selection signal at the recovery horizon — the recovery
is led by what fell. This agrees with the group-level RS (INVERTED), down-day RS (INVERTED) and the crash-leader
finding (deep drawdowns pay in a broken tape), and with the gate ablation (52wk-high distance t 0.14). It is the
fourth RS-flavoured selection idea to fail here.

**Today (row marked):** breadth 35.1% on 2026-09-21, in an episode since 2026-09-15, 309 names within 10% of their
high. The test says being one of those 309 is not a reason to prefer a name over its ADR peers for the next ~2 months.

⚠ Data note: `liquid_panel_2009` has only 178 names on 2026-09-22 and 3 on 09-23 (partial update); the script drops
days with < 50% of the usual count.

# VCP as a damped sine wave — 2026-09-23

**Verdict: NULL · YIELD METHOD.** The pre-registered primary cell cleared the bar on paper (+1.36pp vs same-name
house breakouts, t 3.43, both halves positive) and is **RETRACTED as a control artefact**. On every
uncontaminated control, VCP adds nothing to the house breakout.

Script: `run_vcp_damped_sine.py` (pre-registration in its docstring). Log: `data/studies/logs/vcp_damped_sine.log`.
Trades: `data/studies/logs/vcp_damped_sine_N{3,2}_trades.csv`. Diagnostic (post hoc):
`run_vcp_damped_sine_diag.py`.

## Definition (Gabe)

"On the daily chart, look at the distance between local maxima. If the vertical distance decreases, that is VCP —
like a damped sine wave." Mechanised as follows:
- **Swings:** 3-bar fractal swing highs and lows, known 3 bars late (no look-ahead).
- **Contraction depth:** measured from each swing high to the next swing low, as `1 − trough/peak`.
- **VCP:** the last N depths are strictly decreasing, all within 65 sessions.
- **Context:** close > SMA50 > SMA200, ADR ≥ 3%, liquid-eligible.
- **Trigger:** the first close above the last swing high, entered at the close.
- **Stop:** the last trough's low, judged on the close.
- **Exit:** first close below the 20 EMA or through the stop, max 60 sessions, 0.10% slippage per side.

⚠ **Interpretation choice:** "vertical distance" was read as each swing's peak-to-trough amplitude, not the gap
between successive peaks. The two coincide for a textbook VCP (flat highs, rising lows).

## Results

| | N = 3 (PRIMARY) | N = 2 (exploratory) |
|---|---|---|
| signals / names | 1,704 / 688 | 5,317 / 1,035 |
| VCP mean % / trade (t vs 0) | +0.28% (t 0.81) | +0.35% (t 2.06) |
| win rate · median stop | 31% · 9.6% | 33% · 10.4% |
| all house breakouts, same exit (n 42,876) | +0.57% | +0.57% |
| held-the-level share (low never touches the pivot in 20 sessions), VCP vs all breakouts | 13.7% vs 13.3% | 14.7% vs 13.3% |
| **pre-registered paired diff vs same-name breakouts ±60** | +1.36pp, **t 3.43**, halves +0.85/+1.78 | +1.29pp, t 3.60 |
| harness, R, vs `post` (random later session, same name), best arm | edge −0.008 (trail_bar), fails | edge −0.009, fails |
| harness vs `xname` (random other name, same date) | edge −0.035, fails | — |

## Why the pass is retracted — the control was selected by the event

The ±60 same-name window pooled breakouts before and after the VCP signal. Split (N = 3):

| VCP vs … | n | control | diff | t | halves |
|---|---|---|---|---|---|
| same-name breakouts 60 sessions **AFTER** | 1,387 | −2.18% | +3.62pp | **7.69** | +2.40 / +4.62 |
| same-name breakouts 60 sessions **BEFORE** (inside the base) | 1,400 | −0.38% | +0.51pp | 1.52 | +0.10 / +0.83 |
| same-name breakouts 61–125 sessions away | 1,480 | −0.35% | +0.90pp | 2.33 | +0.37 / +1.29 |
| **other names' house breakouts, SAME date** | 1,693 | +0.60% | **−0.37pp** | −0.70 | −0.75 / −0.06 |

The "after" breakouts are selected by the VCP's own outcome. A VCP that worked leaves the name extended, so its
next 20-day highs are late entries (the entry-extension leak). One that failed leaves broken re-tries. That window
alone carries the whole t. Of the controls that hold the confound fixed, the date-matched one is the cleanest
(same day, same regime, same breakout definition): **VCP is 0.37pp *worse*.** The name-far control (+0.90pp,
t 2.33, both halves positive) is the only hint, and it is below the bar and exploratory.

**What VCP had to show, and didn't:**
- **Beat the house breakout.** It doesn't: +0.28% vs +0.57% for all breakouts, −0.37pp against the same date.
- **Raise the held-the-level share.** It doesn't: 13.7% vs 13.3%. The good cohort of the bimodal breakout book
  is no more callable with a damped-sine base than without one.

## Yield (METHOD)

- **A same-name ±N window around a signal is not a neutral control.** The sessions after an event are selected
  by the event's outcome. Use date-matched cross-name controls for the same setup, or same-name windows that
  exclude the trade and its aftermath. This is the 2026-09-19 `month`-control look-ahead in another form.
- A pre-registered PASS reversed within minutes, which is the ⭐ "clean result is a bug" rule working as intended.

## Not tested, could be

- The full Minervini spec (`data/traderlion/setups/minervini_vcp_low_risk_entry.md` §11): volume dry-up, final
  contraction ≤ 1 ADR, depth cap, RVOL gate. Low prior: the geometric core (shrinking swings) adds nothing on its
  own, and the extra filters are the kind of discretionary tightening the size-lever study already found
  adds only by exclusion.

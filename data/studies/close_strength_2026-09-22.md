# Does a weak close degrade the close-entry edge? — 2026-09-22

**Verdict: NULL on the forecast, MECHANICAL on the stop.** Close-in-range carries no information about
the forward move. What it does is set the stop distance, and at the weak end that stop is far too tight
for the name's volatility. `run_close_strength.py`, pre-registered in the docstring.

## Why it was run

Opened by a live position: ZETA entered on the close 2026-09-22 at 30.13, in the bottom 26% of the day's
range (DINO the same day, 20%). [[project_entry_study]] established that buying the daily CLOSE beats
every intraday entry (+5.95% vs ORB/RECLAIM, paired t −1.6..−3.4) but never conditioned on *where in the
day's range* that close landed. The house rule was silent on exactly the case we were in.

## The confound, stated before running

The house stop **is** the day's low, so `cir = (close−low)/(high−low)` **is** the stop distance:
`stop% = (close−low)/close`. A weak close is mechanically a tight stop → small R denominator → |R|
inflated in both tails and a higher stop-out rate. **R is confounded by construction.** This is the trap
named in [[project_entry_extension_finding]] ("the best CLASSIFIER is the worst GATE… predicts
mechanically/near-tautologically"). So three measurements, with the confound-free one deciding.

Pool: house breakout (close > prior 20d high, ADR ≥ 3, eligible), **42,921 signals, 1,455 names,
2019-10 → 2026-09**, close entry.

## (1) Raw forward % return by cir — confound-free, DECIDES

| cir | n | stop% (med) | stop/ADR | r10 | r20 | r60 |
|---|---|---|---|---|---|---|
| 0.00–0.20 | 1,019 | 0.50 | **0.12** | −0.30 | +1.24 | +5.79 |
| 0.20–0.30 | 955 | 1.03 | 0.25 | +0.69 | +1.46 | +5.89 |
| 0.30–0.50 | 3,607 | 1.59 | 0.39 | +0.68 | +1.89 | +5.97 |
| 0.50–0.80 | 14,645 | 2.75 | 0.68 | +0.88 | +1.91 | +5.80 |
| 0.80–1.00 | 22,695 | 4.19 | 1.03 | +0.52 | +1.30 | **+4.70** |

- **Flat, and not monotone** — Spearman rho **−0.80 to −0.90**, i.e. pointing the *wrong* way: the
  strongest closes (cir ≥ 0.8) are the **worst** 60-day cell (+4.70% vs +5.8–6.0% everywhere else).
  Consistent with the extension finding — closing on the high is closing extended.
- Q5−Q1 spread fails at every horizon: r5 t +0.22, r10 t −0.21, r20 t +0.51, r60 t −1.21. Bar was |t| ≥ 3.
- **The ZETA/DINO cut (cir ≤ 0.30, n=1,975) vs the rest:** r10 +0.28pp (t 0.78), r20 +0.22pp (t 0.41),
  r60 +0.21pp (t 0.24). NULL.
- ⚠ Note the raw means mislead: weak-close r5 reads −0.54% vs strong +0.07%, but the **date-clustered**
  difference is +0.08pp (t 0.28). Weak closes cluster on bad market days; within a date there is nothing.

## (2) R with the house day-low stop — the confounded view

| cell | n | ema20 meanR | win% | ctrl | edge |
|---|---|---|---|---|---|
| WEAK close | 8,137 | **−0.449** | 23.2 | −0.323 | −0.125 |
| STRONG close | 8,556 | **−0.020** | 31.2 | +0.021 | −0.040 |

A 0.43R gap — and it is the artifact the pre-registration predicted, not a finding.

## (3) R with a fixed 1-ADR stop — mechanical link broken

| cell | n | ema20 meanR | ctrl | edge |
|---|---|---|---|---|
| WEAK close | 8,570 | **+0.031** | +0.054 | −0.023 |
| STRONG close | 8,571 | **−0.021** | +0.036 | −0.057 |

**The gap reverses and collapses to ~0.05R.** Once the stop is matched, the weak close is not worse — if
anything marginally better. Neither cell beats its control; neither passes the bar.

## How to apply

1. **Do not make close-in-range an entry gate.** It does not forecast the move. A weak close is not a
   reason to skip a setup that passed the gates that do have support (location vs the 21 EMA, the
   stock-level vetoes, SPY > rising 200).
2. **Do treat it as a sizing input.** cir is the stop-distance knob. At cir ≤ 0.2 the day-low stop is
   **0.12 ADR** — inside the noise, and you will be shaken out on breathing rather than invalidation
   (23% win rate). The fix is Breitstein's C1: **widen the stop to the structure and cut size
   proportionally**, same dollar risk, much better cell. Not a tighter stop at full size.
3. This is the **second** instance of the same mechanism on one day — DINO 2026-09-22 was stopped
   intraday at a level above its structural invalidation (day low 105.83, set at 09:37 *before* the
   11:57 entry; close 106.69 never triggered the house stop).

⚠ Limits: the quintile split in (2)/(3) puts "WEAK" at cir ≤ 0.59 — breakouts close near their highs by
construction, so the quintiles do not reach the truly weak tail. The genuinely weak cells (cir ≤ 0.30,
n = 1,975) are only tested in (1), which is where the confound-free answer lives anyway.
⚠ Multiple testing: 68 patterns now in `pattern_ledger.md`; expect ~3.4 to clear by chance.

Related: [[project_entry_study]], [[project_entry_extension_finding]], [[project_size_lever_study]],
[[project_lance_breitstein_kb]].

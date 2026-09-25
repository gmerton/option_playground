# Option-implied single-name SHORT signals (IV smirk, put-call IV spread): 2026-09-25

Script: `run_iv_skew_short.py` (pre-registration in the docstring, committed before the run). New data:
`silver.options_iv_daily` (`run_build_options_iv_daily.py`; 13.0M ticker-days 2010→2026, ~90 s in Athena).
Log: `data/studies/logs/iv_skew_short.log`; table `iv_skew_short_2026-09-25.csv`.

## Verdict: NULL (short) · 0 of 4 cells pass · every short loses money in absolute terms · MECHANISM

Weekly formation, 838 dates 2010-02 → 2026-02, ~56 names/date (top or bottom decile of the liquid optionable
cross-section). Short at the next open, cover at +h. Excess is measured against same-date names in the same
prior-20d-return quintile × ADR tercile. t is month-clustered.

| cell | signal fwd | excess vs matched | t | halves | short P&L after costs |
|---|---|---|---|---|---|
| **SKEW top decile +20 (PRIMARY)** | +1.27% | **+0.06pp** | +0.67 | +0.14 / −0.01 | **−1.55%** (t −4.25) |
| SKEW top decile +5 | +0.33% | +0.02pp | +0.62 | +0.04 / −0.00 | −0.55% |
| CW bottom decile +20 | +1.03% | −0.16pp | −2.60 | +0.05 / **−0.36** | −1.31% |
| CW bottom decile +5 | +0.26% | −0.04pp | −1.53 | +0.01 / −0.08 | −0.48% |

- **SKEW (Xing–Zhang–Zhao) is flat.** Once prior return and volatility are held fixed, a steep smirk adds nothing.
  The decile gradient is noise (D1 −0.12, D10 +0.06, no monotone pattern). The published effect is probably the
  smirk re-finding momentum and volatility, or it lives in the illiquid names this panel excludes (ADDV ≥ $50M).
- **CW (Cremers–Weinbaum) has a post-2018 lean, and it fails the bar.** It is −0.16pp at t −2.60, but the halves
  disagree: 2010–17 is +0.05 and 2018–25 is −0.36, with every year from 2018 to 2025 negative. Even there it is only
  about −0.4pp per 20 days. It is too small to be a short, and too small to be a useful veto on a long book whose
  trades run several percent.
- **The absolute return kills every short cell.** Names with rich puts still rise about 1% in 20 sessions. That is
  the short-universe finding again (weak or feared names drift up); the stock has to actually fall, and none of
  these do.

## What it taught
- **MECHANISM:** on liquid names, option-implied put demand does not predict the price once the price's own recent
  path is controlled for. Together with the put-burst NULL (9/24, volume), neither the level nor the shape of put
  demand is a stock signal here.
- **Reusable data:** `silver.options_iv_daily` (skew, put25/call50 IV, CW spread) is available for any future IV
  study (e.g., IV-rank gates, the Sleeping Giants IV-rank TODO).
- **Not re-testable as-is:** the CW post-2018 lean would need a fresh pre-registered out-of-sample window
  (2026-03 onward, once bid/ask coverage resumes) before it is worth anything.

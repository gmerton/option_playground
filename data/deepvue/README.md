# Deepvue KB

Deepvue is a **charting and screening platform vendor**. Its YouTube channel is product marketing: every video
demonstrates a platform feature, and descriptions carry referral discounts. The indicators it promotes, like
RMV, are **proprietary and undisclosed**, so nothing here can be verified against the vendor's own
implementation. Anything we test is our own reconstruction. Skeptic-default scoring like every KB here.

`videos/<date>_<id>/` holds `transcript.txt` (timestamped auto-captions), `meta.json` and `notes.md`.
⚠ The captions mishear the indicator's name ("R&V", "RMD", "R&B" = RMV).

## Videos

| video | date | verdict |
|---|---|---|
| [How I Find Early Breakouts - The RMV Indicator in Deepvue](videos/2026-03-06_dDAoAjyYI2I/notes.md) | 2026-03-06 | **2/5.** A feature demo with three hand-picked winners, no hit rate, no denominator. He's honest that contraction doesn't predict direction. RMV reconstructs as a **min-max (0–100) normalisation of a short-window range over a 15-bar lookback**, where ≤ 10 = tight. The inner measure isn't disclosed. It's a fast, own-relative "tightest in 3 weeks" flag, a different object from the VCP geometry (NULL 2026-09-23) and from `vol_compression.py` (a 252-day ATR percentile). ⭐ A pre-registerable test is written: RMV as a gate on the house breakout vs **same-date other-name** breakouts, ~2–3 h |

## Standing caveats

- **Vendor incentive:** the product is the screen. A video that makes screening by RMV look productive is
  doing its job whether or not RMV carries edge.
- **Per-chart parameter switching** (RMV15 ↔ RMV5 "after gaps") is look-ahead if copied into a backtest. Fix L in advance.

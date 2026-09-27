# "Quiet falling knife" LEAPs — Sleeping Giants with the coiling gate flipped (2026-09-27)

`run_quiet_knife_leaps.py` (pre-registered in its docstring, committed before the run). Log `logs/quiet_knife_leaps.log`;
per-LEAP table `quiet_knife_leaps_2026-09-27.csv`. Prompted by Gabe's Aug–Sep 2026 IBIT LEAP buys (sleeping ✅, coiling ❌).

Detector swept weekly over the Sleeping Giants universe (77 large caps + sector ETFs + GLD/SLV), 2014-01 → 2025-06,
44,481 point-in-time evaluations. ~0.40Δ / ~315-DTE calls from v3 at real fills (mid ± 25% of spread + commission),
exit at +180 days. Median entry spread 3.4% of mid. 5 split artefacts excluded.

## Verdict: INVERTED — buying cheap LEAPs on quiet, beaten-down large caps loses badly

| arm | n | net ROC mean | median | win | underlying stock, same window |
|---|---|---|---|---|---|
| **LOW** (sleeping + can wake + ≥1.5y base + price ≤ 40% of range) | 66 | **−32.6%** | **−77.3%** | 23% | −0.6% |
| TOP (the original Sleeping Giant, ≥ 80%) | 164 | +47.2% | −23.9% | 43% | +6.6% |
| same-date control (3 random other universe names per LOW episode) | 189 | +39.1% | −24.7% | 42% | +7.2% |

**PRIMARY LOW − same-date control: −70.4pp per episode, t −4.09** (61 dates), median −49.0pp, win 23%, halves −87.3 /
−52.5, **negative in all 11 years with episodes**. Clears the bar in the wrong direction.

## Read
- **The quiet low-in-range names keep lagging:** their stock underperformed the same-date control by −7.7pp (median
  −8.4pp) over the 180 days, and the LEAP turns that into near-total losses (median −77%): time decay plus a stock that
  doesn't wake up. The list reads like a value-trap catalogue: GE 2022, BA 2021–24, NKE 2023–24, PFE 2023–25, INTC 2024,
  DIS 2023–25, FCX/SLB/SLV in their down years.
- **Convexity doesn't rescue it:** 23% win and a handful of big wins (OXY 2017 +415%, COP +262%, GE 2023 +178%) don't
  come close to paying for the rest.
- ⭐ **Side result on the original Sleeping Giants:** TOP +47% mean vs a random-large-cap LEAP +39% on the same
  pipeline and period (not a paired test). Most of SG's "convex edge" looks like the return of owning 0.40Δ LEAPs in
  a bull market; its MARGINAL status stands, if anything weaker.
- ⚠ Survivorship: the universe is today's large caps, which flatters buying low (names that recovered stayed large).
  The result is negative despite that bias.
- Gabe's IBIT trade sits in this losing category. The Aug–Sep 2026 rebound was one favourable draw from a
  distribution with a −77% median. Journal outcomes don't change the verdict (house rule).

## Consequences
- Keep the Sleeping Giants coiling gate (≥ 80% of range). Do NOT relax it toward "quiet and low": the gate is doing
  the work it was designed for.
- Treat "cheap LEAPs on a quiet beaten-down name" as a veto-class setup, alongside the crash-leader veto.

"""Path-coverage guard for any study whose result depends on the PATH, not just the endpoint.

WHY THIS EXISTS
---------------
`run_iv_condor_study.py` reported an IVP-gated 0.25d short strangle at **94-99% win / 86-100% ROC,
including 2020 and 2022**. It was invalid. Median mark coverage was **14.3%**.

The mechanism is worth stating precisely, because "missing data adds noise" is the wrong intuition and
would not have caught it. That study walked the holding window day by day and evaluated its take/stop
triggers ONLY on days where both legs had marks:

    if c_mid is not None and p_mid is not None:     # <-- days without marks are silently skipped
        if net_val <= take_target: return profit_take
        if net_val >= stop_level: return stop_loss
    if cur >= expiry: return settle_at_expiry(...)  # <-- everything else lands here

A trade whose marks are missing therefore never gets the chance to hit its stop. It falls through to
expiry settlement — and for short premium, expiry is win-biased by construction. **Low coverage does not
add noise; it systematically converts path-dependent losses into endpoint wins.** The bias has a sign,
and the sign flatters the seller.

That study already computed `mark_cov` and returned it on every trade. Nobody gated or reported on it.
The data was there; the discipline was not. This module makes the discipline mechanical.

WHEN TO USE IT
--------------
Any study where the answer depends on what happened BETWEEN entry and exit: profit takes, stops, trailing
exits, breach-and-recover, a fixed-date exit such as the 21-DTE rule, barrier touches. If the only thing
that matters is the endpoint, coverage cannot bias you and this is unnecessary.

Short-premium path studies are the highest-risk case in this repo and must not ship without `report()`.

USAGE
-----
    from lib.studies.path_coverage import report, enforce_floor

    resolved, dropped = enforce_floor(trades, "mark_cov", floor=0.60)
    report(trades, cov_col="mark_cov", pnl_col="pnl", floors=(0.0, 0.25, 0.5, 0.75, 0.9))

`report()` prints the block that MUST accompany any headline from a path study: the coverage
distribution, the share excluded at the chosen floor, and — the diagnostic that actually catches the bug
— **the headline recomputed at rising coverage floors**. If the result degrades monotonically as you
demand better data, the edge is a coverage artefact, not an edge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_FLOOR = 0.60
DEFAULT_FLOORS = (0.0, 0.25, 0.50, 0.75, 0.90)


def compute_coverage(marked_days: pd.Series | np.ndarray, total_days: pd.Series | np.ndarray) -> pd.Series:
    """Fraction of the holding window on which every leg had a usable mark. 0 total days -> NaN."""
    m = pd.Series(marked_days, dtype="float64").reset_index(drop=True)
    t = pd.Series(total_days, dtype="float64").reset_index(drop=True)
    return (m / t.replace(0, np.nan)).clip(upper=1.0)


def enforce_floor(df: pd.DataFrame, cov_col: str = "mark_cov",
                  floor: float = DEFAULT_FLOOR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into (resolved, insufficient). A trade below the floor is UNRESOLVED, not a win.

    The point is that an under-covered trade has no defensible outcome — resolving it either way invents
    data. Report `insufficient` as its own bucket; never silently fold it into the result.
    """
    if cov_col not in df.columns:
        raise KeyError(
            f"{cov_col!r} not in the trade frame. A path study must record per-trade mark coverage "
            f"before it can be trusted — see lib.studies.path_coverage."
        )
    cov = pd.to_numeric(df[cov_col], errors="coerce")
    ok = cov >= floor
    return df[ok].copy(), df[~ok].copy()


def sensitivity(df: pd.DataFrame, cov_col: str = "mark_cov", pnl_col: str = "pnl",
                floors: tuple[float, ...] = DEFAULT_FLOORS) -> pd.DataFrame:
    """THE diagnostic: recompute the headline at rising coverage floors.

    A real edge is roughly flat across floors — demanding better data costs you sample, not result. A
    coverage artefact decays monotonically, because the flattering trades are exactly the under-covered
    ones. Read the trend, not any single row.
    """
    cov = pd.to_numeric(df[cov_col], errors="coerce")
    pnl = pd.to_numeric(df[pnl_col], errors="coerce")
    rows = []
    for f in floors:
        keep = cov >= f
        sub = pnl[keep]
        rows.append(dict(floor=f, n=int(keep.sum()), pct_kept=100.0 * keep.mean(),
                         mean=sub.mean(), median=sub.median(),
                         win_pct=100.0 * (sub > 0).mean() if len(sub) else np.nan))
    return pd.DataFrame(rows)


def report(df: pd.DataFrame, cov_col: str = "mark_cov", pnl_col: str = "pnl",
           floor: float = DEFAULT_FLOOR, floors: tuple[float, ...] = DEFAULT_FLOORS,
           label: str = "") -> dict:
    """Print the block that must accompany any path-study headline. Returns a verdict dict."""
    cov = pd.to_numeric(df[cov_col], errors="coerce")
    head = f"PATH-COVERAGE GUARD{(' — ' + label) if label else ''}"
    print("\n" + "=" * 96); print(head); print("=" * 96)
    print(f"  trades {len(df):,}   coverage: median {cov.median():.1%}  mean {cov.mean():.1%}  "
          f"p10 {cov.quantile(0.10):.1%}  p90 {cov.quantile(0.90):.1%}")
    resolved, dropped = enforce_floor(df, cov_col, floor)
    print(f"  floor {floor:.0%} -> {len(resolved):,} resolved, {len(dropped):,} UNRESOLVED "
          f"({100*len(dropped)/max(len(df),1):.1f}% — report as its own bucket, never as wins)")

    s = sensitivity(df, cov_col, pnl_col, floors)
    print("\n  headline vs coverage floor (a real edge is flat here; an artefact decays):")
    print(s.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))

    # Decay detector. Strict monotonicity is the wrong test: the highest floor is always the thinnest
    # bucket, so ordinary noise there defeats it (found by the module's own self-test — a case decaying
    # 0.328 -> -0.618 went undetected because the n=9 top row ticked back up). Judge on the trend across
    # buckets that have enough trades to mean anything, and on the drop from the unfiltered headline to
    # the best-covered adequate bucket.
    MIN_N = 30
    ok = s[(s["n"] >= MIN_N) & s["mean"].notna()]
    decayed = False
    if len(ok) >= 3:
        f = ok["floor"].to_numpy(dtype="float64")
        m = ok["mean"].to_numpy(dtype="float64")
        rank_corr = float(pd.Series(f).corr(pd.Series(m), method="spearman"))
        spread = abs(m[0]) if abs(m[0]) > 1e-9 else 1.0
        drop = (m[0] - m[-1]) / spread          # positive = headline shrinks as coverage improves
        decayed = bool(rank_corr <= -0.8 and drop >= 0.25)
    low = bool(cov.median() < floor)
    verdict = {"median_coverage": float(cov.median()), "unresolved_share": len(dropped) / max(len(df), 1),
               "decays_with_floor": decayed, "median_below_floor": low}

    if low:
        print(f"\n  ⛔ MEDIAN COVERAGE {cov.median():.1%} IS BELOW THE {floor:.0%} FLOOR. The path is mostly "
              f"invisible; any path-dependent exit in this study is unenforced. Do not report a headline.")
    if decayed:
        print("\n  ⛔ THE RESULT DECAYS MONOTONICALLY AS COVERAGE IMPROVES — the signature of a coverage "
              "artefact. The flattering trades are the under-covered ones. This is how the IVP-gated short "
              "strangle printed 94-99% win rates at 14.3% median coverage.")
    if not low and not decayed:
        print("\n  ✓ Coverage is adequate and the headline does not depend on it. Still quote the median "
              "coverage and the unresolved share next to the result.")
    return verdict

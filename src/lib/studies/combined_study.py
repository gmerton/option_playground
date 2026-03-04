"""
Combined UVXY strategy: bear call spread (always) + short put (VIX<20 only).

Entry logic every Friday
------------------------
- Always:       sell 0.50Δ call / buy 0.40Δ call (bear call spread), 20 DTE
- If VIX < 20:  also sell 0.40Δ put, 20 DTE

Both sides use:  spread ≤ 25% filter on short leg, 50% profit take

Capital normalization
---------------------
ROC is computed with an equal-capital allocation:

  combined_roc = 0.5 × spread_roc + 0.5 × put_roc   (weeks with both sides)
  combined_roc = spread_roc                           (call-spread-only weeks)

This answers: "if I split my options budget 50/50 between the two strategies,
what blended ROC do I earn each week?"

In practice this means more call-spread contracts than put contracts per dollar
(spread max_loss << put Reg-T), but the ROC percentages are directly comparable
and portfolio-weightable.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ── Core combiner ─────────────────────────────────────────────────────────────

def combine_strategies(
    put_df: pd.DataFrame,
    spread_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge closed put and call-spread trades on entry_date.

    put_df:    put trades already filtered to target delta / VIX threshold.
               These represent the VIX<20 conditional entries.
    spread_df: call-spread trades already filtered to target delta / wing / All VIX.

    Returns one row per spread entry date.  When a put was also entered
    (VIX<20 that week) both P&Ls are present; otherwise put columns are NaN.
    """
    spreads = spread_df[~spread_df["split_flag"] & ~spread_df["is_open"]].copy()
    puts    = put_df[~put_df["split_flag"]    & ~put_df["is_open"]].copy()

    merged = (
        spreads[[
            "entry_date", "vix_on_entry",
            "net_pnl", "max_loss", "roc", "annualized_roc", "days_held", "is_win",
        ]]
        .rename(columns={
            "net_pnl":        "spread_pnl",
            "max_loss":       "spread_max_loss",
            "roc":            "spread_roc",
            "annualized_roc": "spread_ann_roc",
            "days_held":      "spread_days",
            "is_win":         "spread_win",
        })
        .merge(
            puts[[
                "entry_date", "short_pnl", "margin_reg_t",
                "roc", "annualized_roc", "days_held", "is_win",
            ]].rename(columns={
                "short_pnl":      "put_pnl",
                "margin_reg_t":   "put_margin",
                "roc":            "put_roc",
                "annualized_roc": "put_ann_roc",
                "days_held":      "put_days",
                "is_win":         "put_win",
            }),
            on="entry_date",
            how="left",
        )
    )

    merged["has_put"] = merged["put_pnl"].notna()

    # Equal-capital blended ROC
    merged["combined_roc"] = np.where(
        merged["has_put"],
        0.5 * merged["spread_roc"] + 0.5 * merged["put_roc"],
        merged["spread_roc"],
    )
    merged["combined_ann_roc"] = np.where(
        merged["has_put"],
        0.5 * merged["spread_ann_roc"] + 0.5 * merged["put_ann_roc"],
        merged["spread_ann_roc"],
    )
    # Win = net P&L positive (sum of both sides)
    merged["combined_win"] = (
        merged["spread_pnl"].fillna(0) + merged["put_pnl"].fillna(0)
    ) > 0

    return merged.sort_values("entry_date").reset_index(drop=True)


# ── Summary printing ───────────────────────────────────────────────────────────

def print_combined_summary(
    combined: pd.DataFrame,
    put_delta: float = 0.40,
    short_delta: float = 0.50,
    wing_width: float = 0.10,
    put_vix_max: float = 20.0,
    dte: int = 20,
    ticker: str = "UVXY",
) -> None:
    """Print per-year combined strategy table plus regime and correlation stats."""

    bar = "=" * 82
    print(f"\n{bar}")
    print(f"  {ticker} Combined Strategy — {dte} DTE, 50% profit take, Fridays")
    print(f"  Call Spread : short={short_delta:.2f}Δ / wing={wing_width:.2f}Δ  (All VIX — always enters)")
    print(f"  Short Put   : delta={put_delta:.2f}Δ  (VIX < {put_vix_max:.0f} only)")
    print(f"  Combined ROC: equal-capital blend — 50% call spread / 50% put (when both active)")
    print(bar)

    print(
        f"  {'Year':>4}  {'Spr':>4} {'Put':>4}  "
        f"{'SprROC%':>8}  {'PutROC%':>8}  "
        f"{'CombROC%':>9}  {'CombAnn%':>9}  {'Win%':>5}"
    )
    print("  " + "-" * 74)

    combined = combined.copy()
    combined["_year"] = pd.to_datetime(combined["entry_date"]).dt.year

    for yr, grp in combined.groupby("_year"):
        n_spr  = len(grp)
        n_put  = int(grp["has_put"].sum())
        spr_roc  = grp["spread_roc"].mean() * 100
        put_roc  = grp.loc[grp["has_put"], "put_roc"].mean() * 100 if n_put > 0 else float("nan")
        comb_roc = grp["combined_roc"].mean() * 100
        comb_ann = grp["combined_ann_roc"].mean() * 100
        win_pct  = grp["combined_win"].mean() * 100

        put_str = f"{put_roc:>+8.2f}%" if not np.isnan(put_roc) else f"{'—':>9}"
        print(
            f"  {yr:>4}  {n_spr:>4} {n_put:>4}  "
            f"  {spr_roc:>+6.2f}%  {put_str}  "
            f"  {comb_roc:>+7.2f}%  {comb_ann:>+8.1f}%  {win_pct:>4.1f}%"
        )

    print("  " + "-" * 74)

    # Overall totals
    n_spr  = len(combined)
    n_put  = int(combined["has_put"].sum())
    spr_roc  = combined["spread_roc"].mean() * 100
    put_roc  = combined.loc[combined["has_put"], "put_roc"].mean() * 100
    comb_roc = combined["combined_roc"].mean() * 100
    comb_ann = combined["combined_ann_roc"].mean() * 100
    win_pct  = combined["combined_win"].mean() * 100

    print(
        f"  {'ALL':>4}  {n_spr:>4} {n_put:>4}  "
        f"  {spr_roc:>+6.2f}%  {put_roc:>+8.2f}%  "
        f"  {comb_roc:>+7.2f}%  {comb_ann:>+8.1f}%  {win_pct:>4.1f}%"
    )
    print(bar)

    # ── Regime breakdown ──────────────────────────────────────────────────────
    both      = combined[combined["has_put"]]
    call_only = combined[~combined["has_put"]]

    print(f"\n  Regime breakdown:")
    print(
        f"  Call spread only (VIX ≥ {put_vix_max:.0f}): {len(call_only):>3} weeks  "
        f"avg spread ROC = {call_only['spread_roc'].mean()*100:>+6.2f}%"
    )
    if len(both) > 0:
        print(
            f"  Both sides       (VIX < {put_vix_max:.0f}): {len(both):>3} weeks  "
            f"avg combined ROC = {both['combined_roc'].mean()*100:>+6.2f}%  "
            f"(spread {both['spread_roc'].mean()*100:>+5.2f}%  "
            f"put {both['put_roc'].mean()*100:>+5.2f}%)"
        )

    # ── Joint outcome correlation ─────────────────────────────────────────────
    if len(both) > 0:
        sw = both["spread_win"].fillna(False).astype(bool)
        pw = both["put_win"].fillna(False).astype(bool)
        both_win      = int(( sw &  pw).sum())
        spr_win_only  = int(( sw & ~pw).sum())
        put_win_only  = int((~sw &  pw).sum())
        both_lose     = int((~sw & ~pw).sum())
        n = len(both)

        print(f"\n  Joint outcomes (weeks both sides active, N={n}):")
        print(f"    Both win         : {both_win:>3}  ({both_win/n*100:>4.1f}%)")
        print(f"    Spread win only  : {spr_win_only:>3}  ({spr_win_only/n*100:>4.1f}%)")
        print(f"    Put win only     : {put_win_only:>3}  ({put_win_only/n*100:>4.1f}%)")
        print(f"    Both lose        : {both_lose:>3}  ({both_lose/n*100:>4.1f}%)")

        # Correlation coefficient between the two ROC streams
        corr = both["spread_roc"].corr(both["put_roc"])
        print(f"\n    Spread/put ROC correlation (VIX<20 weeks): {corr:>+.3f}")

    print()

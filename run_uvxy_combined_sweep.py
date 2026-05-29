#!/usr/bin/env python3
"""
UVXY combined strategy sweep — bear call spread × wing width × short put delta.

Sweeps all combinations of:
  - Call spread short delta   (default: 0.30–0.50)
  - Call spread wing width    (default: 0.05, 0.10, 0.15, 0.20)
  - Short put delta           (default: 0.20–0.50, VIX < 20 gate)

For each combo, reports the equal-capital blended ROC matching the playbook
framework:  combined_roc = 0.5×spread_roc + 0.5×put_roc  (when both active)
                         = spread_roc                      (call-spread-only weeks)

Split adjustment: trades spanning any UVXY reverse split are excluded via
UVXY_SPLIT_DATES.  Delta-based matching is scale-invariant by design.

Usage
-----
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \\
    .venv/bin/python3 run_uvxy_combined_sweep.py

  # Custom delta ranges:
  ... run_uvxy_combined_sweep.py --short-deltas 0.40,0.50 --wings 0.10 --put-deltas 0.30,0.40

  # Refresh options cache from Athena:
  ... run_uvxy_combined_sweep.py --refresh

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.straddle_study import UVXY_SPLIT_DATES
from lib.studies.call_spread_study import (
    build_call_spread_trades,
    find_spread_exits,
    compute_spread_metrics,
)
from lib.studies.put_study import (
    build_put_trades,
    find_exits as find_put_exits,
    compute_put_metrics,
    fetch_vix_data,
)

UVXY_START = date(2018, 1, 12)   # post-leverage-change (1.5×)
DTE_TARGET = 20
DTE_TOL    = 5
PUT_VIX_MAX = 20.0               # put gate: only enter when VIX < 20


def _parse_floats(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",")]


def load_data(start: date, end: date, refresh: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load UVXY options cache + VIX data."""
    from lib.mysql_lib import fetch_options_cache
    from lib.studies.straddle_study import sync_options_cache

    sync_options_cache("UVXY", start, force=refresh)

    fetch_end = end + timedelta(days=DTE_TARGET + DTE_TOL + 5)
    print(f"Loading UVXY options from MySQL ({start} → {fetch_end}) ...")
    df_opts = fetch_options_cache("UVXY", start, fetch_end)
    print(f"  {len(df_opts):,} rows loaded.")

    vix_start = start - timedelta(days=5)
    print(f"Fetching VIX ({vix_start} → {end}) ...")
    df_vix = fetch_vix_data(vix_start, end)

    return df_opts, df_vix


def run_sweep(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_deltas: list[float],
    wing_widths: list[float],
    put_deltas: list[float],
    end: date,
    max_spread_pct: float = 0.25,
) -> pd.DataFrame:
    """
    Build trades for every (short_delta, wing_width) and every put_delta,
    then combine each triplet and return a summary DataFrame.
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]

    # ── Pre-build all put variants (one per delta) ──────────────────────────
    print("\nBuilding put trades ...")
    put_cache: dict[float, pd.DataFrame] = {}
    for pd_ in put_deltas:
        positions = build_put_trades(
            df_opts, delta_target=pd_,
            dte_target=DTE_TARGET, dte_tol=DTE_TOL,
            entry_weekday=4, split_dates=UVXY_SPLIT_DATES,
            max_spread_pct=max_spread_pct,
        )
        if positions.empty:
            put_cache[pd_] = pd.DataFrame()
            continue
        positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
        positions = find_put_exits(positions, df_opts)
        positions = compute_put_metrics(positions)
        # VIX < 20 gate
        positions = positions[
            positions["vix_on_entry"].isna() | (positions["vix_on_entry"] < PUT_VIX_MAX)
        ].copy()
        positions = positions[~positions["split_flag"] & ~positions["is_open"]].copy()
        put_cache[pd_] = positions
        print(f"  put delta={pd_:.2f}: {len(positions)} trades (VIX<{PUT_VIX_MAX:.0f})")

    # ── Pre-build all call spread variants ──────────────────────────────────
    print("\nBuilding call spread trades ...")
    spread_cache: dict[tuple[float, float], pd.DataFrame] = {}
    for sd in short_deltas:
        for ww in wing_widths:
            long_delta = sd - ww
            if long_delta <= 0:
                continue
            positions = build_call_spread_trades(
                df_opts, short_delta_target=sd, wing_delta_width=ww,
                dte_target=DTE_TARGET, dte_tol=DTE_TOL,
                entry_weekday=4, split_dates=UVXY_SPLIT_DATES,
                max_spread_pct=max_spread_pct,
            )
            if positions.empty:
                spread_cache[(sd, ww)] = pd.DataFrame()
                continue
            positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
            positions = find_spread_exits(positions, df_opts)
            positions = compute_spread_metrics(positions)
            positions = positions[~positions["split_flag"] & ~positions["is_open"]].copy()
            positions = positions[positions["entry_date"] <= end].copy()
            spread_cache[(sd, ww)] = positions
            print(f"  call spread short={sd:.2f}/wing={ww:.2f}: {len(positions)} trades")

    # ── Combine every triplet ────────────────────────────────────────────────
    print("\nCombining ...")
    rows = []
    for (sd, ww), spreads in spread_cache.items():
        if spreads.empty:
            continue
        for pd_, puts in put_cache.items():
            # Merge: every spread entry gets a put entry if one fired that week
            merged = spreads[["entry_date", "vix_on_entry",
                               "net_pnl", "max_loss", "roc", "annualized_roc",
                               "days_held", "is_win"]].rename(columns={
                "net_pnl": "spread_pnl", "max_loss": "spread_max_loss",
                "roc": "spread_roc", "annualized_roc": "spread_ann_roc",
                "days_held": "spread_days", "is_win": "spread_win",
            })
            if not puts.empty:
                put_side = puts[["entry_date", "short_pnl", "margin_reg_t",
                                  "roc", "annualized_roc", "days_held", "is_win"]].rename(columns={
                    "short_pnl": "put_pnl", "margin_reg_t": "put_margin",
                    "roc": "put_roc", "annualized_roc": "put_ann_roc",
                    "days_held": "put_days", "is_win": "put_win",
                })
                merged = merged.merge(put_side, on="entry_date", how="left")
            else:
                for c in ("put_pnl","put_margin","put_roc","put_ann_roc","put_days","put_win"):
                    merged[c] = float("nan")

            merged["has_put"] = merged["put_pnl"].notna()
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
            merged["combined_win"] = (
                merged["spread_pnl"].fillna(0) + merged["put_pnl"].fillna(0)
            ) > 0

            closed = merged[~merged["combined_roc"].isna()]
            if closed.empty:
                continue

            n_spr   = len(closed)
            n_put   = int(closed["has_put"].sum())
            comb_roc = closed["combined_roc"].mean() * 100
            comb_ann = closed["combined_ann_roc"].mean() * 100
            win_pct  = closed["combined_win"].mean() * 100
            spr_roc  = closed["spread_roc"].mean() * 100
            put_roc  = closed.loc[closed["has_put"], "put_roc"].mean() * 100 if n_put > 0 else float("nan")

            # Per-year worst
            closed["_year"] = pd.to_datetime(closed["entry_date"]).dt.year
            yr_rocs = closed.groupby("_year")["combined_roc"].mean() * 100
            worst_yr_roc  = yr_rocs.min()
            worst_yr      = int(yr_rocs.idxmin())
            both_lose_weeks = int((
                (closed["spread_pnl"].fillna(0) < 0) &
                (closed["put_pnl"].fillna(0) < 0) &
                closed["has_put"]
            ).sum())

            rows.append({
                "short_delta": sd,
                "wing_width":  ww,
                "long_delta":  round(sd - ww, 2),
                "put_delta":   pd_,
                "n_spread":    n_spr,
                "n_put":       n_put,
                "spread_roc":  round(spr_roc, 2),
                "put_roc":     round(put_roc, 2) if not np.isnan(put_roc) else float("nan"),
                "combined_roc":   round(comb_roc, 2),
                "combined_ann":   round(comb_ann, 1),
                "win_pct":        round(win_pct, 1),
                "worst_yr_roc":   round(worst_yr_roc, 2),
                "worst_yr":       worst_yr,
                "both_lose_wks":  both_lose_weeks,
            })

    return pd.DataFrame(rows)


def print_summary(df: pd.DataFrame, top_n: int = 20) -> None:
    if df.empty:
        print("No results.")
        return

    df = df.sort_values("combined_roc", ascending=False).reset_index(drop=True)

    bar = "=" * 108
    print(f"\n{bar}")
    print(f"  UVXY Combined Sweep  —  {DTE_TARGET} DTE, 50% PT, Fridays  |  "
          f"Call spread: all VIX  |  Put: VIX < {PUT_VIX_MAX:.0f}")
    print(f"  Top {top_n} combos by combined ROC (equal-capital blend)")
    print(bar)
    print(f"  {'ShtΔ':>5}  {'WingΔ':>6}  {'LngΔ':>5}  {'PutΔ':>5}  "
          f"{'N_Spr':>6}  {'N_Put':>5}  "
          f"{'SprROC%':>8}  {'PutROC%':>8}  {'CombROC%':>9}  "
          f"{'CombAnn%':>9}  {'Win%':>5}  {'WorstYr':>8}  {'BothLose':>8}")
    print("  " + "-" * 102)

    for _, r in df.head(top_n).iterrows():
        put_roc_str = f"{r['put_roc']:>+7.2f}%" if not np.isnan(r["put_roc"]) else f"{'—':>8}"
        print(
            f"  {r['short_delta']:>5.2f}  {r['wing_width']:>6.2f}  {r['long_delta']:>5.2f}  "
            f"{r['put_delta']:>5.2f}  "
            f"{r['n_spread']:>6.0f}  {r['n_put']:>5.0f}  "
            f"  {r['spread_roc']:>+6.2f}%  {put_roc_str}  "
            f"  {r['combined_roc']:>+7.2f}%  {r['combined_ann']:>+8.1f}%  "
            f"{r['win_pct']:>4.1f}%  "
            f"{r['worst_yr_roc']:>+7.2f}%({r['worst_yr']:.0f})  "
            f"{r['both_lose_wks']:>8.0f}"
        )

    print(bar)

    # Show current playbook params for reference
    playbook = df[
        (df["short_delta"] == 0.50) &
        (df["wing_width"]  == 0.10) &
        (df["put_delta"]   == 0.40)
    ]
    if not playbook.empty:
        r = playbook.iloc[0]
        rank = df.index[
            (df["short_delta"] == 0.50) & (df["wing_width"] == 0.10) & (df["put_delta"] == 0.40)
        ].tolist()
        rank_str = f"#{rank[0]+1}" if rank else "not found"
        print(f"\n  Current playbook (0.50/0.10/0.40): combined ROC={r['combined_roc']:+.2f}%  "
              f"win={r['win_pct']:.1f}%  worst={r['worst_yr_roc']:+.2f}%({r['worst_yr']:.0f})  "
              f"rank {rank_str} of {len(df)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UVXY combined strategy delta sweep",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--short-deltas", type=_parse_floats,
                        default=[0.30, 0.35, 0.40, 0.45, 0.50],
                        help="Call spread short leg deltas")
    parser.add_argument("--wings", type=_parse_floats,
                        default=[0.05, 0.10, 0.15, 0.20],
                        help="Call spread wing widths (delta)")
    parser.add_argument("--put-deltas", type=_parse_floats,
                        default=[0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
                        help="Short put deltas (VIX<20 gate)")
    parser.add_argument("--spread", type=float, default=0.25,
                        help="Max bid-ask/mid on short legs")
    parser.add_argument("--top", type=int, default=20,
                        help="Number of top combos to print")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-sync from Athena")
    args = parser.parse_args()

    end = date.today()
    df_opts, df_vix = load_data(UVXY_START, end, args.refresh)

    results = run_sweep(
        df_opts=df_opts,
        df_vix=df_vix,
        short_deltas=args.short_deltas,
        wing_widths=args.wings,
        put_deltas=args.put_deltas,
        end=end,
        max_spread_pct=args.spread,
    )

    print_summary(results, top_n=args.top)


if __name__ == "__main__":
    main()

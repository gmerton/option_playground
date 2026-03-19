#!/usr/bin/env python3
"""
Per-regime bull put spread delta sweep — with and without 2× stop loss.

Finds the optimal short_delta × wing_width for each of the four 50MA×VIX regimes:
  Bearish_HighIV  — below 50MA + VIX ≥ 20
  Bearish_LowIV   — below 50MA + VIX < 20
  Bullish_HighIV  — above 50MA + VIX ≥ 20
  Bullish_LowIV   — above 50MA + VIX < 20

Exit rules match the live screener: 50% profit take OR optional 2× stop loss.
The sweep runs without any MA/VIX gates, then positions are classified by regime
post-hoc so exit data uses the full options dataset.

Usage:
    AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \\
        PYTHONPATH=src .venv/bin/python3 run_qqq_regime_put_sweep.py [--ticker QQQ] [--no-stop]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from typing import Optional

import pandas as pd

import pathlib

from lib.mysql_lib import fetch_options_cache
from lib.studies.straddle_study import sync_options_cache
from lib.studies.put_study import fetch_vix_data
from lib.studies.put_spread_study import (
    add_ma_column,
    build_put_spread_trades,
    find_put_spread_exits,
    compute_spread_metrics,
)

_CACHE_DIR = pathlib.Path(__file__).resolve().parent / "data" / "cache"

# Per-ticker split date config (add entries as needed)
_SPLIT_DATES: dict[str, list] = {
    "QQQ": [],
    "SPY": [],
}


def _load_stock_cache(ticker: str) -> pd.DataFrame:
    """Load daily close prices from local parquet cache."""
    cache_path = _CACHE_DIR / f"{ticker}_stock.parquet"
    if not cache_path.exists():
        raise FileNotFoundError(f"Stock cache not found: {cache_path}")
    df = pd.read_parquet(cache_path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["close"]      = pd.to_numeric(df["close"], errors="coerce")
    return df.sort_values("trade_date").reset_index(drop=True)


def _load_options_cache(ticker: str, start: "date", fetch_end: "date") -> pd.DataFrame:
    """
    Load options data from local parquet cache if available and up-to-date,
    otherwise fetch from MySQL and save to parquet for future runs.

    Cache is considered stale if it doesn't cover fetch_end - 7 days.
    """
    cache_path = _CACHE_DIR / f"{ticker}_options.parquet"

    # Only load options within a useful DTE window — cuts memory significantly
    max_dte = DTE_TARGET + DTE_TOL + 10

    if cache_path.exists():
        df = pd.read_parquet(cache_path)
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
        cached_max = df["trade_date"].max()
        # Cache is fresh if it has data within the last 30 calendar days
        staleness_threshold = date.today() - timedelta(days=30)
        if cached_max >= staleness_threshold:
            filtered = df[
                (df["trade_date"] >= start)
                & (df["trade_date"] <= fetch_end)
                & (df["dte"] >= 0)
                & (df["dte"] <= max_dte)
            ].reset_index(drop=True)
            print(f"  Loaded {len(filtered):,} rows from parquet cache "
                  f"(max date: {cached_max}, DTE ≤ {max_dte}).")
            return filtered
        print(f"  Parquet cache stale (max date: {cached_max}, threshold: {staleness_threshold}).")
        answer = input("  Refresh from MySQL? This may use ~13 GB RAM. [y/N] ").strip().lower()
        if answer != "y":
            print("  Using stale cache — results may not include the most recent data.")
            filtered = df[
                (df["trade_date"] >= start)
                & (df["trade_date"] <= fetch_end)
                & (df["dte"] >= 0)
                & (df["dte"] <= max_dte)
            ].reset_index(drop=True)
            print(f"  Loaded {len(filtered):,} rows from parquet cache "
                  f"(max date: {cached_max}, DTE ≤ {max_dte}).")
            return filtered
        print("  Refreshing from MySQL ...")
    else:
        print(f"  No parquet cache found, fetching from MySQL (~13 GB RAM) ...")

    df = fetch_options_cache(ticker, start, fetch_end)
    if not df.empty:
        df.to_parquet(cache_path, index=False)
        print(f"  Saved {len(df):,} rows to {cache_path.name}")
    return df


def _parse_args():
    p = argparse.ArgumentParser(description="Per-regime bull put spread delta sweep")
    p.add_argument("--ticker",   default="QQQ", help="Underlying ticker (default: QQQ)")
    p.add_argument("--no-stop",  action="store_true", help="Disable 2× stop loss (default: use stop)")
    p.add_argument("--dte",      type=int, default=20, help="Target DTE (default: 20)")
    return p.parse_args()


# ── Config ────────────────────────────────────────────────────────────────────

# These are overridden by CLI args in main(); kept here for module-level references
TICKER        = "QQQ"
START         = date(2018, 1, 1)
END           = date.today()
DTE_TARGET    = 20
DTE_TOL       = 5
PROFIT_TAKE   = 0.50
STOP_MULTIPLE = 2.0      # overridden by --no-stop flag
VIX_SPLIT     = 20.0
MA_DAYS       = 50
SPLIT_DATES   = []

SHORT_DELTAS  = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
WING_WIDTHS   = [0.05, 0.10, 0.15, 0.20]

REGIMES = [
    ("Bearish_HighIV", "below 50MA + VIX≥20"),
    ("Bearish_LowIV",  "below 50MA + VIX<20"),
    ("Bullish_HighIV", "above 50MA + VIX≥20"),
    ("Bullish_LowIV",  "above 50MA + VIX<20"),
]


# ── Regime classifier ─────────────────────────────────────────────────────────

def assign_regime(row) -> str:
    ma  = row["ma_ratio_50"]
    vix = row["vix_on_entry"]
    if pd.isna(ma) or pd.isna(vix):
        return "Unknown"
    above_ma = ma  >= 1.0
    high_iv  = vix >= VIX_SPLIT
    if not above_ma and high_iv:
        return "Bearish_HighIV"
    if not above_ma and not high_iv:
        return "Bearish_LowIV"
    if above_ma and high_iv:
        return "Bullish_HighIV"
    return "Bullish_LowIV"


# ── Custom sweep with stop loss ───────────────────────────────────────────────

def run_sweep_with_stop(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    stock_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Run the put spread sweep for all (short_delta, wing_width) pairs.
    Uses 50% profit take + 2× stop loss. Returns combined DataFrame with
    regime classification on every row.
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    all_results = []

    for short_delta in SHORT_DELTAS:
        for wing_width in WING_WIDTHS:
            long_delta = short_delta - wing_width
            if long_delta < 0.05:
                continue
            print(
                f"  short={short_delta:.2f}  wing={wing_width:.2f}"
                f"  (long≈{long_delta:.2f}) ...",
                end=" ", flush=True,
            )

            positions = build_put_spread_trades(
                df_opts,
                short_delta_target=short_delta,
                wing_delta_width=wing_width,
                dte_target=DTE_TARGET,
                dte_tol=DTE_TOL,
                entry_weekday=4,
                split_dates=SPLIT_DATES,
                max_delta_err=0.08,
                max_spread_pct=None,
            )
            if positions.empty:
                print("no entries.")
                continue

            # Attach VIX and 50-day MA
            positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
            positions = add_ma_column(positions, stock_df, MA_DAYS)

            # Exit with both profit take and stop loss
            positions = find_put_spread_exits(
                positions, df_opts,
                profit_take_pct=PROFIT_TAKE,
                stop_multiple=STOP_MULTIPLE,
            )
            positions = compute_spread_metrics(positions)

            # Tag each row with delta combo
            positions["short_delta_target"] = short_delta
            positions["wing_delta_width"]   = wing_width

            n = len(positions[~positions["split_flag"] & ~positions["is_open"]])
            print(f"{n} trades.")
            all_results.append(positions)

    if not all_results:
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)
    combined = combined[combined["entry_date"] <= END].reset_index(drop=True)

    # Assign regime
    combined["regime"] = combined.apply(assign_regime, axis=1)
    return combined


# ── Stats helper ──────────────────────────────────────────────────────────────

def _stats(grp: pd.DataFrame) -> Optional[dict]:
    closed = grp[~grp["is_open"] & ~grp["split_flag"] & (grp["regime"] != "Unknown")]
    if closed.empty:
        return None
    n        = len(closed)
    n_stop   = (closed["exit_type"] == "stop").sum()
    n_early  = (closed["exit_type"] == "early").sum()
    return {
        "n":        n,
        "n_stop":   n_stop,
        "win_pct":  closed["is_win"].mean() * 100,
        "roc":      closed["roc"].mean() * 100,
        "ann_roc":  closed["annualized_roc"].mean() * 100,
        "sum_roc":  closed["roc"].sum() * 100,
        "crd_pct":  closed["credit_pct_of_width"].mean() * 100,
        "stop_pct": n_stop / n * 100,
        "take_pct": n_early / n * 100,
    }


# ── Printing ──────────────────────────────────────────────────────────────────

def print_regime_sweep(sweep: pd.DataFrame) -> None:
    bar = "=" * 96

    # Count unique weeks per regime (proxy: first delta combo)
    regime_weeks: dict[str, int] = {}
    base = sweep[
        (sweep["short_delta_target"] == 0.35)
        & (sweep["wing_delta_width"] == 0.10)
        & ~sweep["is_open"] & ~sweep["split_flag"]
        & (sweep["regime"] != "Unknown")
    ]
    for rname, _ in REGIMES:
        regime_weeks[rname] = base[base["regime"] == rname]["entry_date"].nunique()

    print(f"\n{bar}")
    print(f"  {TICKER} Per-Regime Bull Put Spread Delta Sweep  ·  {"WITH 2× stop loss" if STOP_MULTIPLE else "NO stop loss"}")
    print(f"  {DTE_TARGET} DTE  ·  50% take / {"2× stop" if STOP_MULTIPLE else "NO stop"}  ·  50-day MA × VIX {VIX_SPLIT:.0f}")
    print(bar)

    for wing_width in WING_WIDTHS:
        print(f"\n{'─'*96}")
        print(f"  WING = {wing_width:.2f}Δ")
        print(f"{'─'*96}")
        print(
            f"  {'Regime':<20}  {'ShortΔ':>7}  {'N':>4}  "
            f"{'Win%':>5}  {'Stop%':>5}  {'ROC%':>6}  {'AnnROC':>7}  {'SumROC':>7}  {'Crd%':>4}"
        )
        print("  " + "─" * 68)

        for regime_name, regime_desc in REGIMES:
            n_weeks = regime_weeks.get(regime_name, "?")
            print(f"\n  ── {regime_name}  ({regime_desc})  ·  ~{n_weeks} wks ──")
            best_roc = -999.0

            for short_delta in SHORT_DELTAS:
                long_delta = short_delta - wing_width
                if long_delta < 0.05:
                    continue

                sub = sweep[
                    (sweep["short_delta_target"] == short_delta)
                    & (sweep["wing_delta_width"]  == wing_width)
                    & (sweep["regime"] == regime_name)
                ]
                st = _stats(sub)
                if st is None:
                    continue

                marker = " ◄ BEST" if st["roc"] > best_roc else ""
                if st["roc"] > best_roc:
                    best_roc = st["roc"]

                print(
                    f"  {' ':20}  {short_delta:>7.2f}  {st['n']:>4}  "
                    f"{st['win_pct']:>4.1f}%  {st['stop_pct']:>4.1f}%"
                    f"  {st['roc']:>+5.2f}%  {st['ann_roc']:>+6.1f}%  {st['sum_roc']:>+7.1f}"
                    f"  {st['crd_pct']:>3.0f}%{marker}"
                )

    # ── Best combo per regime summary ─────────────────────────────────────────
    print(f"\n{bar}")
    print(f"  BEST COMBO PER REGIME  (by avg AnnROC, {"with 2× stop" if STOP_MULTIPLE else "no stop"})")
    print(f"  {'Regime':<20}  {'ShortΔ':>7}  {'Wing':>6}  {'N':>4}  "
          f"{'Win%':>5}  {'ROC%':>6}  {'AnnROC':>7}  {'SumROC':>7}  {'Crd%':>4}")
    print("  " + "─" * 84)

    for regime_name, regime_desc in REGIMES:
        n_weeks = regime_weeks.get(regime_name, "?")
        best_val = -999.0
        best = None

        for short_delta in SHORT_DELTAS:
            for wing_width in WING_WIDTHS:
                if short_delta - wing_width < 0.05:
                    continue
                sub = sweep[
                    (sweep["short_delta_target"] == short_delta)
                    & (sweep["wing_delta_width"]  == wing_width)
                    & (sweep["regime"] == regime_name)
                ]
                st = _stats(sub)
                if st and st["ann_roc"] > best_val:
                    best_val = st["ann_roc"]
                    best = (short_delta, wing_width, st)

        if best:
            sd, ww, st = best
            print(
                f"  {regime_name:<20}  {sd:>7.2f}  {ww:>6.2f}  {st['n']:>4}  "
                f"{st['win_pct']:>4.1f}%"
                f"  {st['roc']:>+5.2f}%  {st['ann_roc']:>+6.1f}%  {st['sum_roc']:>+7.1f}"
                f"  {st['crd_pct']:>3.0f}%  ({regime_desc}, ~{n_weeks} wks)"
            )
        else:
            print(f"  {regime_name:<20}  —")

    # Current screener combo for reference
    print(f"\n  Reference — current screener strikes (0.10Δ wing), all regimes")
    print(f"  {'Regime':<20}  {'ShortΔ':>7}  {'Wing':>6}  {'N':>4}  "
          f"{'Win%':>5}  {'ROC%':>6}  {'AnnROC':>7}  {'SumROC':>7}  {'Crd%':>4}")
    print("  " + "─" * 84)
    _ref = {
        "Bearish_HighIV": (0.25, 0.10),
        "Bearish_LowIV":  (0.35, 0.10),
        "Bullish_HighIV": (0.45, 0.10),
        "Bullish_LowIV":  (0.45, 0.10),
    }
    for regime_name, regime_desc in REGIMES:
        sd, ww = _ref.get(regime_name, (0.35, 0.10))
        sub = sweep[
            (sweep["short_delta_target"] == sd)
            & (sweep["wing_delta_width"]  == ww)
            & (sweep["regime"] == regime_name)
        ]
        st = _stats(sub)
        if st:
            print(
                f"  {regime_name:<20}  {sd:>7.2f}  {ww:>6.2f}  {st['n']:>4}  "
                f"{st['win_pct']:>4.1f}%"
                f"  {st['roc']:>+5.2f}%  {st['ann_roc']:>+6.1f}%  {st['sum_roc']:>+7.1f}"
                f"  {st['crd_pct']:>3.0f}%"
            )
    print(bar)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    global TICKER, STOP_MULTIPLE, SPLIT_DATES, DTE_TARGET, DTE_TOL

    args = _parse_args()
    TICKER        = args.ticker.upper()
    STOP_MULTIPLE = None if args.no_stop else 2.0
    SPLIT_DATES   = _SPLIT_DATES.get(TICKER, [])
    DTE_TARGET    = args.dte
    DTE_TOL       = max(5, args.dte // 4)  # scale tolerance with DTE

    sync_options_cache(TICKER, START)

    vix_start = START - timedelta(days=5)
    print(f"Fetching VIX data ({vix_start} → {END}) ...")
    df_vix = fetch_vix_data(vix_start, END)
    if df_vix.empty:
        print("WARNING: no VIX data.")

    fetch_end = END + timedelta(days=DTE_TARGET + DTE_TOL + 5)
    print(f"Loading {TICKER} options ({START} → {fetch_end}) ...")
    df_opts = _load_options_cache(TICKER, START, fetch_end)
    if df_opts.empty:
        print("No options data. Aborting.")
        sys.exit(1)
    print(f"  {len(df_opts):,} rows ready.")

    print(f"Loading {TICKER} stock price cache for {MA_DAYS}-day MA ...")
    stock_df = _load_stock_cache(TICKER)
    if stock_df.empty:
        print("ERROR: no stock data.")
        sys.exit(1)
    print(f"  {len(stock_df):,} daily rows ({stock_df['trade_date'].min()} → {stock_df['trade_date'].max()})")

    stop_label = "NO stop" if STOP_MULTIPLE is None else f"{STOP_MULTIPLE:.0f}× stop"
    print(f"\nRunning sweep: {len(SHORT_DELTAS)} short deltas × {len(WING_WIDTHS)} wings  [50% take / {stop_label}] ...")
    sweep = run_sweep_with_stop(df_opts, df_vix, stock_df)
    if sweep.empty:
        print("No trades found.")
        sys.exit(1)

    print(f"Total positions: {len(sweep):,}")
    print_regime_sweep(sweep)


if __name__ == "__main__":
    main()

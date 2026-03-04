"""
Short call backtest engine with delta sweep and VIX regime filter.

Strategy
--------
- Sell an OTM (or ATM) call on entry day (Friday) at a target delta
- Hold until the earlier of:
    (a) call mid falls to ≤ (1 - profit_take_pct) × entry_mid  [profit take]
    (b) expiry (settle at intrinsic value from daily last price)
- Apply optional VIX threshold filter: skip entries when VIX >= threshold

Sweep
-----
Run simultaneously across:
  delta_targets  e.g. [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
  vix_thresholds e.g. [None, 30, 25, 20]   (None = no filter / baseline)

UVXY structural note
--------------------
UVXY has a downward structural drift (VIX futures roll cost + leverage decay),
which is favourable for call sellers — the underlying tends to move toward and
through OTM call strikes expiring worthless.  The tail risk is the opposite of
the put study: a sudden VIX spike drives UVXY sharply higher, putting short
calls deeply in the money.  The VIX filter attempts to avoid the highest-risk
entry regimes, but cannot fully protect against sudden spike events.

Capital / Margin
----------------
Reg T naked call: (0.20 × strike × 100) + (entry_mid × 100)
Same convention as the put study, using the short strike as the underlying proxy.

Data sources
------------
- Options data:  MySQL options_cache (synced from Athena by straddle_study.sync_options_cache)
- VIX data:      Tradier VIX daily close, cached to data/cache/vix_daily.parquet

Shared utilities
----------------
Imports fetch_vix_data and find_exits from put_study — those functions are
option-type agnostic once entry_mid_col and cp are parameterised.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.put_study import fetch_vix_data
from lib.studies.put_study import find_exits as _find_exits


# ── Entry construction ────────────────────────────────────────────────────────

def build_call_trades(
    df: pd.DataFrame,
    delta_target: float,
    dte_target: int = 30,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
) -> pd.DataFrame:
    """
    Find short call entries from the options cache.

    delta_target is the UNSIGNED call delta (e.g. 0.30 selects calls with
    delta ≈ +0.30).  Call deltas in the cache are positive.

    max_spread_pct: if set, skip entries where (ask - bid) / mid > threshold.
    """
    split_dates = split_dates or []
    df = df.copy()

    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    td_dt = pd.to_datetime(df["trade_date"])

    mask = (
        (td_dt.dt.dayofweek == entry_weekday)
        & (df["dte"] >= dte_target - dte_tol)
        & (df["dte"] <= dte_target + dte_tol)
        & (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["cp"] == "C")
        & (df["delta"].notna())
    )
    calls = df[mask].copy()

    # Spread filter
    if max_spread_pct is not None:
        calls["_spread_pct"] = (calls["ask"] - calls["bid"]) / calls["mid"]
        calls = calls[calls["_spread_pct"] <= max_spread_pct]

    # Call delta is positive; target delta_target directly
    calls["_delta_err"] = (calls["delta"] - delta_target).abs()
    calls = calls[calls["_delta_err"] <= max_delta_err]
    if calls.empty:
        return pd.DataFrame()

    # Best call per (trade_date, expiry): closest delta
    calls = calls.sort_values(["trade_date", "expiry", "_delta_err"])
    calls = calls.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    # Best expiry per trade_date: DTE closest to target
    calls["_dte_err"] = (calls["dte"] - dte_target).abs()
    calls = calls.sort_values(["trade_date", "_dte_err"])
    calls = calls.drop_duplicates(subset=["trade_date"], keep="first")

    calls = calls.rename(columns={
        "trade_date": "entry_date",
        "dte":        "actual_dte",
        "mid":        "call_entry_mid",
        "bid":        "call_entry_bid",
        "ask":        "call_entry_ask",
        "delta":      "call_entry_delta",
    })[[
        "entry_date", "expiry", "actual_dte", "strike",
        "call_entry_mid", "call_entry_bid", "call_entry_ask", "call_entry_delta",
    ]]

    # Split flag
    def _spans(entry_d: date, exp_d: date) -> bool:
        return any(entry_d < sd <= exp_d for sd in split_dates)

    calls["split_flag"] = [
        _spans(r.entry_date, r.expiry)
        for r in calls.itertuples(index=False)
    ]

    return calls.sort_values("entry_date").reset_index(drop=True)


def find_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_take_pct: float = 0.50,
) -> pd.DataFrame:
    """Wrapper around put_study.find_exits using call column names."""
    return _find_exits(
        positions,
        df_opts,
        profit_take_pct=profit_take_pct,
        entry_mid_col="call_entry_mid",
        cp="C",
    )


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_call_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add P&L and risk-adjusted return columns.

    short_pnl       (call_entry_mid - exit_price) × 100  (positive = profit)
    short_pnl_worst (call_entry_bid  - exit_price) × 100
    pnl_pct         short_pnl / (call_entry_mid × 100)
    margin_reg_t    (0.20 × strike × 100) + (call_entry_mid × 100)
    roc             short_pnl / margin_reg_t
    annualized_roc  roc × 365 / days_held
    breakeven_pct   call_entry_mid / strike  (how far above strike to break even)
    is_win          short_pnl > 0
    is_open         missing exit data
    """
    df = df.copy()
    df["short_pnl"]       = (df["call_entry_mid"] - df["exit_price"]) * 100
    df["short_pnl_worst"] = (df["call_entry_bid"]  - df["exit_price"]) * 100
    df["pnl_pct"]         = df["short_pnl"]       / (df["call_entry_mid"] * 100)
    df["pnl_pct_worst"]   = df["short_pnl_worst"] / (
        df["call_entry_bid"].replace(0, float("nan")) * 100
    )
    df["margin_reg_t"]    = (0.20 * df["strike"] * 100) + (df["call_entry_mid"] * 100)
    df["roc"]             = df["short_pnl"] / df["margin_reg_t"]
    df["annualized_roc"]  = df["roc"] * 365 / df["days_held"].clip(lower=1)
    df["breakeven_pct"]   = df["call_entry_mid"] / df["strike"]
    df["is_win"]          = df["short_pnl"] > 0
    df["is_open"]         = df["missing_exit_data"].fillna(False)
    return df


# ── Sweep orchestrator ────────────────────────────────────────────────────────

def run_call_delta_sweep(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 30,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    profit_take_pct: float = 0.50,
) -> pd.DataFrame:
    """
    Run the call study across all (delta_target, vix_threshold) combinations.

    Returns a combined DataFrame with columns 'delta_target' and 'vix_threshold'
    added.  vix_threshold is stored as float (NaN = no filter / baseline).
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    all_results = []

    for delta_target in delta_targets:
        print(f"  delta={delta_target:.2f} ...", end=" ", flush=True)
        positions = build_call_trades(
            df_opts,
            delta_target=delta_target,
            dte_target=dte_target,
            dte_tol=dte_tol,
            entry_weekday=entry_weekday,
            split_dates=split_dates,
            max_delta_err=max_delta_err,
            max_spread_pct=max_spread_pct,
        )
        if positions.empty:
            print("no entries found.")
            continue

        positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
        positions = find_exits(positions, df_opts, profit_take_pct=profit_take_pct)
        positions = compute_call_metrics(positions)

        for vix_thresh in vix_thresholds:
            if vix_thresh is None:
                filtered = positions.copy()
                label = float("nan")
            else:
                filtered = positions[
                    positions["vix_on_entry"].isna()
                    | (positions["vix_on_entry"] < vix_thresh)
                ].copy()
                label = float(vix_thresh)

            filtered["delta_target"]  = delta_target
            filtered["vix_threshold"] = label
            all_results.append(filtered)

        n = len(positions[~positions["split_flag"] & ~positions["is_open"]])
        print(f"{n} trades.")

    if not all_results:
        return pd.DataFrame()
    return pd.concat(all_results, ignore_index=True)


# ── Summary printing ──────────────────────────────────────────────────────────

def print_call_sweep_summary(
    sweep_df: pd.DataFrame,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 30,
    profit_take_pct: float = 0.50,
) -> None:
    """Print a pivot-style summary table for the call sweep."""
    import math

    def _label(v) -> str:
        return "All VIX" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"VIX<{int(v)}"

    def _stats(grp: pd.DataFrame) -> dict:
        closed = grp[~grp["is_open"] & ~grp["split_flag"]]
        if closed.empty:
            return {}
        n       = len(closed)
        wins    = closed["is_win"].sum()
        n_early = (closed["exit_type"] == "early").sum()
        return {
            "n":        n,
            "n_early":  n_early,
            "win_pct":  wins / n * 100,
            "pnl_pct":  closed["pnl_pct"].mean() * 100,
            "roc":      closed["roc"].mean() * 100,
            "ann_roc":  closed["annualized_roc"].mean() * 100,
        }

    width = 80
    bar   = "=" * width
    print(f"\n{bar}")
    print(f"  UVXY Short Call Sweep — {dte_target} DTE  "
          f"({int(profit_take_pct*100)}% profit take, Fridays)")
    print(bar)

    thresh_labels = [_label(v) for v in vix_thresholds]

    hdr1 = f"  {'Delta':>6}"
    hdr2 = f"  {'':>6}"
    for lbl in thresh_labels:
        hdr1 += f"  {lbl:^30}"
        hdr2 += f"  {'N(E%)':>5} {'Win%':>5} {'Pnl%':>6} {'ROC%':>6} {'AnnROC%':>8}"
    print(hdr1)
    print(hdr2)
    print("  " + "-" * (width - 2))

    for delta in delta_targets:
        row = f"  {delta:>6.2f}"
        for vt in vix_thresholds:
            sub = sweep_df[
                (sweep_df["delta_target"] == delta)
                & (
                    (sweep_df["vix_threshold"].isna() & (vt is None))
                    | (sweep_df["vix_threshold"] == (float(vt) if vt is not None else float("nan")))
                )
            ]
            st = _stats(sub)
            if st:
                early_pct = st["n_early"] / st["n"] * 100
                row += (
                    f"  {st['n']:>3}({early_pct:>2.0f}%)"
                    f" {st['win_pct']:>4.1f}%"
                    f" {st['pnl_pct']:>+5.1f}%"
                    f" {st['roc']:>+5.2f}%"
                    f" {st['ann_roc']:>+7.1f}%"
                )
            else:
                row += f"  {'—':^30}"
        print(row)

    print("  " + "-" * (width - 2))
    print(f"  N = closed trades (split-spanning excluded)  "
          f"E% = % that hit {int(profit_take_pct*100)}% profit take")
    print(f"{bar}\n")


def print_call_year_detail(
    sweep_df: pd.DataFrame,
    delta_target: float,
    vix_threshold: Optional[float] = None,
) -> None:
    """Print the per-year breakdown for one (delta, vix_threshold) combo."""
    import math

    vt_label = (
        "All VIX" if (vix_threshold is None or math.isnan(float(vix_threshold or 0)))
        else f"VIX<{int(vix_threshold)}"
    )
    sub = sweep_df[
        (sweep_df["delta_target"] == delta_target)
        & (
            (sweep_df["vix_threshold"].isna() & (vix_threshold is None))
            | (sweep_df["vix_threshold"] == float(vix_threshold or float("nan")))
        )
    ].copy()
    closed = sub[~sub["is_open"] & ~sub["split_flag"]].copy()
    if closed.empty:
        print("No data.")
        return

    print(f"\n  delta={delta_target:.2f}  {vt_label}  — per-year")
    print(f"  {'Year':>4}  {'N':>3}  {'E%':>4}  {'Win%':>5}  {'Pnl%':>6}  "
          f"{'ROC%':>6}  {'AnnROC%':>8}  {'AvgDays':>7}")
    print("  " + "-" * 58)

    closed["_year"] = pd.to_datetime(closed["entry_date"]).dt.year
    for yr, grp in closed.groupby("_year"):
        n       = len(grp)
        wins    = grp["is_win"].sum()
        n_early = (grp["exit_type"] == "early").sum()
        print(
            f"  {yr:>4}  {n:>3}  {n_early/n*100:>3.0f}%"
            f"  {wins/n*100:>4.1f}%"
            f"  {grp['pnl_pct'].mean()*100:>+5.1f}%"
            f"  {grp['roc'].mean()*100:>+5.2f}%"
            f"  {grp['annualized_roc'].mean()*100:>+7.1f}%"
            f"  {grp['days_held'].mean():>7.1f}"
        )
    print()


# ── Top-level runner ──────────────────────────────────────────────────────────

def run_call_study(
    ticker: str,
    start: date,
    end: date,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 30,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    profit_take_pct: float = 0.50,
    output_csv: Optional[str] = None,
    force_sync: bool = False,
    detail_delta: Optional[float] = None,
    detail_vix: Optional[float] = None,
) -> pd.DataFrame:
    """
    Full pipeline: sync options_cache → VIX fetch → load → sweep → print → CSV.
    """
    from lib.mysql_lib import fetch_options_cache
    from lib.studies.straddle_study import sync_options_cache

    # 1. Sync options cache
    sync_options_cache(ticker, start, force=force_sync)

    # 2. Fetch VIX
    vix_start = start - timedelta(days=5)
    print(f"Fetching VIX data ({vix_start} → {end}) ...")
    df_vix = fetch_vix_data(vix_start, end)
    if df_vix.empty:
        print("WARNING: no VIX data — VIX filters will be skipped.")

    # 3. Load options from MySQL
    fetch_end = end + timedelta(days=dte_target + dte_tol + 5)
    print(f"Loading {ticker} options from MySQL ({start} → {fetch_end}) ...")
    df_opts = fetch_options_cache(ticker, start, fetch_end)
    if df_opts.empty:
        print("No options data found. Aborting.")
        return pd.DataFrame()
    print(f"  {len(df_opts):,} rows loaded.")

    # 4. Run sweep
    print(f"\nRunning call delta sweep: {delta_targets}")
    sweep = run_call_delta_sweep(
        df_opts=df_opts,
        df_vix=df_vix,
        delta_targets=delta_targets,
        vix_thresholds=vix_thresholds,
        dte_target=dte_target,
        dte_tol=dte_tol,
        entry_weekday=entry_weekday,
        split_dates=split_dates,
        max_delta_err=max_delta_err,
        max_spread_pct=max_spread_pct,
        profit_take_pct=profit_take_pct,
    )

    if not sweep.empty:
        sweep = sweep[sweep["entry_date"] <= end].reset_index(drop=True)

    if sweep.empty:
        print("No trades found.")
        return pd.DataFrame()

    # 5. Print summary
    print_call_sweep_summary(sweep, delta_targets, vix_thresholds, dte_target, profit_take_pct)

    # 6. Optional per-year detail
    if detail_delta is not None:
        print_call_year_detail(sweep, detail_delta, detail_vix)

    # 7. CSV
    if output_csv:
        col_order = [
            "delta_target", "vix_threshold",
            "entry_date", "expiry", "actual_dte", "strike",
            "call_entry_delta", "call_entry_mid", "call_entry_bid",
            "vix_on_entry",
            "exit_date", "exit_price", "exit_type", "days_held",
            "short_pnl", "short_pnl_worst",
            "pnl_pct", "pnl_pct_worst",
            "margin_reg_t", "roc", "annualized_roc", "breakeven_pct",
            "is_win", "is_open", "split_flag", "missing_exit_data",
        ]
        save_cols = [c for c in col_order if c in sweep.columns]
        sweep[save_cols].to_csv(output_csv, index=False)
        print(f"Saved {len(sweep)} rows to {output_csv}")

    return sweep

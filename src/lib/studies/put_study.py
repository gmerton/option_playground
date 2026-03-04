"""
Short put backtest engine with delta sweep and VIX regime filter.

Strategy
--------
- Sell an OTM put on entry day (Friday) at a target delta
- Hold until the earlier of:
    (a) put mid falls to ≤ (1 - profit_take_pct) × entry_mid  [profit take]
    (b) expiry (settle at intrinsic value from daily last price)
- Apply optional VIX threshold filter: skip entries when VIX >= threshold

Sweep
-----
Run simultaneously across:
  delta_targets  e.g. [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
  vix_thresholds e.g. [None, 30, 25, 20]   (None = no filter / baseline)

Capital / Margin
----------------
Reg T naked put: (0.20 × strike × 100) + (entry_mid × 100)
Using ATM put strike as the underlying price proxy.

Data sources
------------
- Options data:  MySQL options_cache (synced from Athena by straddle_study.sync_options_cache)
- VIX data:      yfinance ^VIX, cached to data/cache/vix_daily.parquet

Usage
-----
  PYTHONPATH=src python run_uvxy_puts.py
  PYTHONPATH=src python run_uvxy_puts.py --dte 30 --profit-take 0.50
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VIX_CACHE  = _REPO_ROOT / "data" / "cache" / "vix_daily.parquet"

# ── VIX data ──────────────────────────────────────────────────────────────────

def fetch_vix_data(
    start: date,
    end: date,
    *,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetch daily VIX closes via Tradier ($VIX.X) and cache to data/cache/vix_daily.parquet.

    Returns a DataFrame with columns: trade_date (date), vix_close (float).
    Incremental: only re-downloads if the cache is stale (> 2 days old).
    """
    import asyncio
    import os
    from lib.tradier.tradier_client_wrapper import TradierClient
    from lib.tradier.get_daily_history import get_daily_history

    today = date.today()

    if _VIX_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(_VIX_CACHE)
        cached["trade_date"] = pd.to_datetime(cached["trade_date"]).dt.date
        max_d = cached["trade_date"].max()
        if max_d >= today - timedelta(days=2):
            mask = (cached["trade_date"] >= start) & (cached["trade_date"] <= end)
            return cached[mask].reset_index(drop=True)
        # Incremental: fetch from max_d+1
        fetch_start = max_d + timedelta(days=1)
        print(f"VIX cache: extending from {fetch_start} → {today} ...")
    else:
        fetch_start = start
        cached = pd.DataFrame(columns=["trade_date", "vix_close"])
        print(f"VIX cache: fetching {fetch_start} → {today} ...")

    api_key = os.environ["TRADIER_API_KEY"]

    async def _fetch():
        async with TradierClient(api_key=api_key) as client:
            return await get_daily_history("VIX", fetch_start, today, client=client)

    raw = asyncio.run(_fetch())

    if raw is None or raw.empty:
        print("  No VIX data returned from Tradier.")
    else:
        new_rows = raw[["close"]].copy()
        new_rows.columns = ["vix_close"]
        new_rows.index = pd.to_datetime(new_rows.index).date
        new_rows.index.name = "trade_date"
        new_rows = new_rows.reset_index()
        new_rows["trade_date"] = pd.to_datetime(new_rows["trade_date"]).dt.date
        new_rows["vix_close"]  = pd.to_numeric(new_rows["vix_close"], errors="coerce")

        combined = pd.concat([cached, new_rows], ignore_index=True)
        combined = combined.drop_duplicates(subset=["trade_date"], keep="last")
        combined = combined.sort_values("trade_date").reset_index(drop=True)
        _VIX_CACHE.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(_VIX_CACHE, index=False)
        print(f"  VIX cache updated: {len(combined)} rows.")
        cached = combined

    mask = (cached["trade_date"] >= start) & (cached["trade_date"] <= end)
    return cached[mask].reset_index(drop=True)


# ── Entry construction ────────────────────────────────────────────────────────

def build_put_trades(
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
    Find short put entries from the options cache.

    delta_target is the UNSIGNED put delta (e.g. 0.20 selects puts with
    delta ≈ -0.20).  Filtering uses ABS(delta - (-delta_target)) ≤ max_delta_err.

    max_spread_pct: if set, skip entries where (ask - bid) / mid > threshold.
    e.g. 0.25 means the spread must be ≤ 25% of mid to be considered tradeable.

    Returns one row per entry date with put entry info.
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
        & (df["cp"] == "P")
        & (df["delta"].notna())
    )
    puts = df[mask].copy()

    # Spread filter
    if max_spread_pct is not None:
        puts["_spread_pct"] = (puts["ask"] - puts["bid"]) / puts["mid"]
        puts = puts[puts["_spread_pct"] <= max_spread_pct]

    # delta for puts is negative; target -delta_target
    puts["_delta_err"] = (puts["delta"] - (-delta_target)).abs()
    puts = puts[puts["_delta_err"] <= max_delta_err]
    if puts.empty:
        return pd.DataFrame()

    # Best put per (trade_date, expiry): closest delta
    puts = puts.sort_values(["trade_date", "expiry", "_delta_err"])
    puts = puts.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    # Best expiry per trade_date: DTE closest to target
    puts["_dte_err"] = (puts["dte"] - dte_target).abs()
    puts = puts.sort_values(["trade_date", "_dte_err"])
    puts = puts.drop_duplicates(subset=["trade_date"], keep="first")

    puts = puts.rename(columns={
        "trade_date": "entry_date",
        "dte":        "actual_dte",
        "mid":        "put_entry_mid",
        "bid":        "put_entry_bid",
        "ask":        "put_entry_ask",
        "delta":      "put_entry_delta",
    })[[
        "entry_date", "expiry", "actual_dte", "strike",
        "put_entry_mid", "put_entry_bid", "put_entry_ask", "put_entry_delta",
    ]]

    # Split flag
    def _spans(entry_d: date, exp_d: date) -> bool:
        return any(entry_d < sd <= exp_d for sd in split_dates)

    puts["split_flag"] = [
        _spans(r.entry_date, r.expiry)
        for r in puts.itertuples(index=False)
    ]

    return puts.sort_values("entry_date").reset_index(drop=True)


# ── Early exit scanner ────────────────────────────────────────────────────────

def find_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_take_pct: float = 0.50,
    entry_mid_col: str = "put_entry_mid",
    cp: str = "P",
) -> pd.DataFrame:
    """
    For each position find the exit date/price:
      - Earliest trading day (after entry) where option mid ≤ (1-profit_take_pct) × entry_mid
      - Or expiry day if the trigger never fires

    entry_mid_col: column in positions holding the entry mid price (default "put_entry_mid").
    cp: option type to look up daily marks for ("P" or "C").

    Returns positions DataFrame with added columns:
      exit_date, exit_price, days_held, exit_type ('early' | 'expiry' | 'missing')
    """
    if positions.empty:
        for c in ("exit_date", "exit_price", "days_held", "exit_type"):
            positions[c] = None
        return positions

    # Daily marks from options cache for the relevant option type
    marks = (
        df_opts[df_opts["cp"] == cp]
        [["trade_date", "expiry", "strike", "mid", "last", "bid"]]
        .rename(columns={
            "trade_date": "mark_date",
            "mid":        "mark_mid",
            "last":       "mark_last",
            "bid":        "mark_bid",
        })
        .copy()
    )
    # Restrict to (expiry, strike) combos present in positions
    pos_keys = positions[["expiry", "strike"]].drop_duplicates()
    put_marks = marks.merge(pos_keys, on=["expiry", "strike"], how="inner")

    # Cross-join positions × daily marks, filtered to holding window
    merged = positions.merge(put_marks, on=["expiry", "strike"], how="left")
    merged = merged[
        (merged["mark_date"] > merged["entry_date"])
        & (merged["mark_date"] <= merged["expiry"])
    ]

    # Profit-take trigger (on mid price)
    profit_target = merged[entry_mid_col] * (1.0 - profit_take_pct)
    merged["_early"]       = merged["mark_mid"] <= profit_target
    merged["_is_expiry"]   = merged["mark_date"] == merged["expiry"]
    merged["_is_exit"]     = merged["_early"] | merged["_is_expiry"]

    # Earliest exit per position
    exits = (
        merged[merged["_is_exit"]]
        .sort_values(["entry_date", "expiry", "strike", "mark_date"])
        .drop_duplicates(subset=["entry_date", "expiry", "strike"], keep="first")
        .copy()
    )

    # Exit price: mid for early exit, prefer last then mid at expiry (vectorized)
    import numpy as np
    at_expiry_only = exits["_is_expiry"] & ~exits["_early"]
    last_val = exits["mark_last"].where(
        pd.notna(exits["mark_last"]) & (exits["mark_last"] > 0),
        other=exits["mark_mid"],
    ).fillna(0.0).clip(lower=0.0)
    early_val = exits["mark_mid"].fillna(0.0).clip(lower=0.0)
    exits["exit_price"] = np.where(at_expiry_only, last_val, early_val)
    exits["days_held"]  = (
        pd.to_datetime(exits["mark_date"]) - pd.to_datetime(exits["entry_date"])
    ).dt.days
    exits["exit_type"]  = exits.apply(
        lambda r: "early" if r["_early"] and not r["_is_expiry"]
                  else ("early" if r["_early"] and r["_is_expiry"] else "expiry"),
        axis=1,
    )
    exits = exits.rename(columns={"mark_date": "exit_date"})

    result = positions.merge(
        exits[["entry_date", "expiry", "strike", "exit_date", "exit_price",
               "days_held", "exit_type"]],
        on=["entry_date", "expiry", "strike"],
        how="left",
    )
    result["missing_exit_data"] = result["exit_date"].isna()
    result["exit_price"] = result["exit_price"].fillna(0.0)
    result["days_held"]  = result["days_held"].fillna(result["actual_dte"]).astype(int)
    result["exit_type"]  = result["exit_type"].fillna("missing")

    return result


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_put_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add P&L and risk-adjusted return columns.

    short_pnl       (entry_mid - exit_price) × 100  ($, positive = profit)
    pnl_pct         short_pnl / (entry_mid × 100)
    margin_reg_t    (0.20 × strike × 100) + (entry_mid × 100)
    roc             short_pnl / margin_reg_t
    annualized_roc  roc × 365 / days_held
    breakeven_pct   entry_mid / strike
    is_win          short_pnl > 0
    is_open         missing_exit_data
    """
    df = df.copy()
    df["short_pnl"]      = (df["put_entry_mid"] - df["exit_price"]) * 100
    df["short_pnl_worst"]= (df["put_entry_bid"] - df["exit_price"]) * 100
    df["pnl_pct"]        = df["short_pnl"]       / (df["put_entry_mid"] * 100)
    df["pnl_pct_worst"]  = df["short_pnl_worst"] / (df["put_entry_bid"].replace(0, float("nan")) * 100)
    df["margin_reg_t"]   = (0.20 * df["strike"] * 100) + (df["put_entry_mid"] * 100)
    df["roc"]            = df["short_pnl"] / df["margin_reg_t"]
    df["annualized_roc"] = df["roc"] * 365 / df["days_held"].clip(lower=1)
    df["breakeven_pct"]  = df["put_entry_mid"] / df["strike"]
    df["is_win"]         = df["short_pnl"] > 0
    df["is_open"]        = df["missing_exit_data"].fillna(False)
    return df


# ── Sweep orchestrator ────────────────────────────────────────────────────────

def run_delta_sweep(
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
    Run the put study across all (delta_target, vix_threshold) combinations.

    Returns a combined DataFrame with columns 'delta_target' and 'vix_threshold'
    added.  vix_threshold is stored as float (NaN = no filter / baseline).
    """
    # Normalise VIX lookup: trade_date → vix_close
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]

    all_results = []

    for delta_target in delta_targets:
        print(f"  delta={delta_target:.2f} ...", end=" ", flush=True)
        positions = build_put_trades(
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

        # Add VIX on each entry date
        positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)

        # Find exits once (reused across VIX threshold variants)
        positions = find_exits(positions, df_opts, profit_take_pct=profit_take_pct)
        positions = compute_put_metrics(positions)

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

            filtered["delta_target"]   = delta_target
            filtered["vix_threshold"]  = label
            all_results.append(filtered)

        n = len(positions[~positions["split_flag"] & ~positions["is_open"]])
        print(f"{n} trades.")

    if not all_results:
        return pd.DataFrame()
    return pd.concat(all_results, ignore_index=True)


# ── Summary printing ──────────────────────────────────────────────────────────

def print_sweep_summary(
    sweep_df: pd.DataFrame,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 30,
    profit_take_pct: float = 0.50,
    ticker: str = "UVXY",
) -> None:
    """
    Print a pivot-style summary table:
      rows    = delta targets
      columns = one block per VIX threshold
    """
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
            "n":          n,
            "n_early":    n_early,
            "win_pct":    wins / n * 100,
            "pnl_pct":    closed["pnl_pct"].mean() * 100,
            "roc":        closed["roc"].mean() * 100,
            "ann_roc":    closed["annualized_roc"].mean() * 100,
            "avg_days":   closed["days_held"].mean(),
            "bkev_pct":   closed["breakeven_pct"].mean() * 100,
        }

    width = 80
    bar   = "=" * width

    print(f"\n{bar}")
    print(f"  {ticker} Short Put Sweep — {dte_target} DTE  "
          f"({int(profit_take_pct*100)}% profit take, Fridays)")
    print(bar)

    thresh_labels = [_label(v) for v in vix_thresholds]

    # Header
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
            label = _label(vt)
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


# ── Per-year detail for a single (delta, vix_threshold) ──────────────────────

def print_year_detail(
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

def run_put_study(
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
    Full pipeline: sync options_cache → fetch → sweep → print → CSV.

    detail_delta / detail_vix: if set, also print per-year breakdown for that combo.
    max_spread_pct: if set, skip entries where (ask-bid)/mid > threshold.
    """
    from lib.mysql_lib import fetch_options_cache
    from lib.studies.straddle_study import sync_options_cache

    # 1. Sync options cache
    sync_options_cache(ticker, start, force=force_sync)

    # 2. Fetch VIX
    vix_start = start - timedelta(days=5)   # small buffer for weekend alignment
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
    print(f"\nRunning delta sweep: {delta_targets}")
    sweep = run_delta_sweep(
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

    # Trim to study end date
    if not sweep.empty:
        sweep = sweep[sweep["entry_date"] <= end].reset_index(drop=True)

    if sweep.empty:
        print("No trades found.")
        return pd.DataFrame()

    # 5. Print summary
    print_sweep_summary(sweep, delta_targets, vix_thresholds, dte_target, profit_take_pct, ticker=ticker)

    # 6. Optional per-year detail
    if detail_delta is not None:
        print_year_detail(sweep, detail_delta, detail_vix)

    # 7. CSV
    if output_csv:
        col_order = [
            "delta_target", "vix_threshold",
            "entry_date", "expiry", "actual_dte", "strike",
            "put_entry_delta", "put_entry_mid", "put_entry_bid",
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

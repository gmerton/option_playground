"""
Bull put spread backtest engine — short delta × wing width × VIX regime sweep.

Strategy
--------
- Sell a put at short_delta_target (Friday, target DTE)  ← higher strike, more premium
- Buy a put at (short_delta_target - wing_delta_width)   ← lower strike, less premium
- Hold until the earlier of:
    (a) net spread value ≤ (1 - profit_take_pct) × net_credit_mid  [profit take]
    (b) expiry (settle at intrinsic net value of both legs)
- Apply optional VIX threshold filter: skip entries when VIX >= threshold

Delta sign convention
---------------------
Puts have negative deltas in the MySQL cache (e.g. -0.25 for a 0.25Δ put).
All public APIs use UNSIGNED targets (e.g. short_delta_target=0.25); internally
we compare against -short_delta_target.

Sweep dimensions
----------------
  short_delta_targets  e.g. [0.20, 0.25, 0.30, 0.35]
  wing_delta_widths    e.g. [0.05, 0.10, 0.15]
  vix_thresholds       e.g. [None, 30, 25, 20]   (None = no filter / baseline)

Capital / Margin
----------------
Max loss: (spread_width - net_credit_mid) × 100
  where spread_width = short_strike - long_strike (in dollars)
This is how brokers actually margin credit spreads (defined-risk).

Key metrics
-----------
credit_pct_of_width = net_credit_mid / spread_width   (premium as % of max risk)
roc                 = net_pnl / max_loss              (return on capital at risk)
annualized_roc      = roc × 365 / days_held

Data sources
------------
- Options data:  MySQL options_cache (synced from Athena by straddle_study.sync_options_cache)
- VIX data:      Tradier VIX daily close, cached to data/cache/vix_daily.parquet
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.put_study import fetch_vix_data


# ── Entry construction ─────────────────────────────────────────────────────────

def build_put_spread_trades(
    df: pd.DataFrame,
    short_delta_target: float,
    wing_delta_width: float,
    dte_target: int = 20,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
) -> pd.DataFrame:
    """
    Find bull put spread entries from the options cache.

    short_delta_target: unsigned put delta for the short leg (e.g. 0.25).
                        Internally compared against -short_delta_target because puts
                        have negative deltas in the cache.
    wing_delta_width:   delta separation between legs (e.g. 0.10).
                        → long put target delta = short_delta_target - wing_delta_width
                        → long put strike is lower (less OTM) than short put strike.

    max_spread_pct: bid-ask filter applied to the short leg (ask-bid)/mid ≤ threshold.
    max_delta_err:  used for both legs independently (unsigned distance from target).

    short_strike > long_strike (short put has higher strike = more premium).
    Returns one row per entry with both legs joined.
    """
    split_dates = split_dates or []
    df = df.copy()

    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    td_dt = pd.to_datetime(df["trade_date"])
    long_delta_target = short_delta_target - wing_delta_width

    # Base filter: puts on entry day within DTE range with valid quotes
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

    # ── Short leg ──────────────────────────────────────────────────────────────
    if max_spread_pct is not None:
        puts["_spread_pct"] = (puts["ask"] - puts["bid"]) / puts["mid"]
        short_pool = puts[puts["_spread_pct"] <= max_spread_pct].copy()
    else:
        short_pool = puts.copy()

    # Puts have negative deltas; compare abs(delta - (-short_delta_target))
    short_pool["_delta_err"] = (short_pool["delta"] - (-short_delta_target)).abs()
    short_pool = short_pool[short_pool["_delta_err"] <= max_delta_err]
    if short_pool.empty:
        return pd.DataFrame()

    # Best short per (trade_date, expiry): closest delta
    short_pool = short_pool.sort_values(["trade_date", "expiry", "_delta_err"])
    short_pool = short_pool.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    # Best expiry per trade_date: DTE closest to target
    short_pool["_dte_err"] = (short_pool["dte"] - dte_target).abs()
    short_pool = short_pool.sort_values(["trade_date", "_dte_err"])
    short_pool = short_pool.drop_duplicates(subset=["trade_date"], keep="first")

    short_leg = short_pool.rename(columns={
        "trade_date": "entry_date",
        "dte":        "actual_dte",
        "mid":        "short_mid",
        "bid":        "short_bid",
        "ask":        "short_ask",
        "delta":      "short_delta",
        "strike":     "short_strike",
    })[["entry_date", "expiry", "actual_dte",
        "short_strike", "short_mid", "short_bid", "short_ask", "short_delta"]]

    # ── Long leg ───────────────────────────────────────────────────────────────
    # Use the same date/expiry pool (no spread filter on long leg)
    long_pool = puts.copy()
    long_pool["_long_delta_err"] = (long_pool["delta"] - (-long_delta_target)).abs()
    long_pool = long_pool[long_pool["_long_delta_err"] <= max_delta_err]
    if long_pool.empty:
        return pd.DataFrame()

    # Best long per (trade_date, expiry): closest delta
    long_pool = long_pool.sort_values(["trade_date", "expiry", "_long_delta_err"])
    long_pool = long_pool.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    long_leg = long_pool.rename(columns={
        "trade_date": "entry_date",
        "mid":        "long_mid",
        "bid":        "long_bid",
        "ask":        "long_ask",
        "delta":      "long_delta",
        "strike":     "long_strike",
    })[["entry_date", "expiry",
        "long_strike", "long_mid", "long_bid", "long_ask", "long_delta"]]

    # ── Join legs ──────────────────────────────────────────────────────────────
    spreads = short_leg.merge(long_leg, on=["entry_date", "expiry"], how="inner")

    # Bull put spread: short_strike > long_strike (short put has higher strike)
    spreads = spreads[spreads["short_strike"] > spreads["long_strike"]].copy()
    if spreads.empty:
        return pd.DataFrame()

    # Net credit
    spreads["net_credit_mid"]   = spreads["short_mid"] - spreads["long_mid"]
    spreads["net_credit_worst"] = spreads["short_bid"] - spreads["long_ask"]

    # Must receive a positive credit
    spreads = spreads[spreads["net_credit_mid"] > 0].copy()
    if spreads.empty:
        return pd.DataFrame()

    # Spread geometry
    spreads["spread_width"]        = spreads["short_strike"] - spreads["long_strike"]
    spreads["max_loss"]            = (spreads["spread_width"] - spreads["net_credit_mid"]) * 100
    spreads["credit_pct_of_width"] = spreads["net_credit_mid"] / spreads["spread_width"]

    # Split flag
    def _spans(entry_d: date, exp_d: date) -> bool:
        return any(entry_d < sd <= exp_d for sd in split_dates)

    spreads["split_flag"] = [
        _spans(r.entry_date, r.expiry)
        for r in spreads.itertuples(index=False)
    ]

    return spreads.sort_values("entry_date").reset_index(drop=True)


# ── Exit scanner ────────────────────────────────────────────────────────────────

def find_put_spread_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_take_pct: float = 0.50,
    stop_multiple: Optional[float] = None,
) -> pd.DataFrame:
    """
    For each spread position, find the exit date and net spread value.

    Exit when daily (short_mark_mid - long_mark_mid) ≤ (1 - profit_take_pct) × net_credit_mid,
    or at expiry using last/mid prices for each leg.

    stop_multiple: if set, also exit when net_value ≥ stop_multiple × net_credit_mid.

    Returns positions with added: exit_date, exit_net_value, days_held, exit_type.
    exit_type: 'early' (profit take) | 'stop' (stop-loss) | 'expiry' | 'missing'
    """
    if positions.empty:
        for c in ("exit_date", "exit_net_value", "days_held", "exit_type"):
            positions[c] = None
        return positions

    # All put daily marks
    put_marks = (
        df_opts[df_opts["cp"] == "P"]
        [["trade_date", "expiry", "strike", "mid", "last"]]
        .rename(columns={
            "trade_date": "mark_date",
            "mid":        "mark_mid",
            "last":       "mark_last",
        })
        .copy()
    )

    # Restrict to (expiry, strike) combos present as either leg
    short_keys = (
        positions[["expiry", "short_strike"]]
        .rename(columns={"short_strike": "strike"})
        .drop_duplicates()
    )
    long_keys = (
        positions[["expiry", "long_strike"]]
        .rename(columns={"long_strike": "strike"})
        .drop_duplicates()
    )
    all_keys = pd.concat([short_keys, long_keys]).drop_duplicates()
    relevant = put_marks.merge(all_keys, on=["expiry", "strike"], how="inner")

    short_marks = relevant.rename(columns={
        "strike":    "short_strike",
        "mark_mid":  "short_mark_mid",
        "mark_last": "short_mark_last",
    })[["mark_date", "expiry", "short_strike", "short_mark_mid", "short_mark_last"]]

    long_marks = relevant.rename(columns={
        "strike":    "long_strike",
        "mark_mid":  "long_mark_mid",
        "mark_last": "long_mark_last",
    })[["mark_date", "expiry", "long_strike", "long_mark_mid", "long_mark_last"]]

    # Merge positions × short leg daily marks
    merged = positions.merge(
        short_marks,
        on=["expiry", "short_strike"],
        how="left",
    )
    # Merge × long leg marks on the same mark_date
    merged = merged.merge(
        long_marks,
        on=["expiry", "long_strike", "mark_date"],
        how="left",
    )

    # Filter to holding window
    merged = merged[
        (merged["mark_date"] > merged["entry_date"])
        & (merged["mark_date"] <= merged["expiry"])
    ]

    # Drop rows where either leg mark is missing
    merged = merged.dropna(subset=["short_mark_mid", "long_mark_mid"])

    # Daily net spread value (cost to close the spread)
    merged["net_value"] = merged["short_mark_mid"] - merged["long_mark_mid"]

    # Profit-take trigger
    profit_target        = merged["net_credit_mid"] * (1.0 - profit_take_pct)
    merged["_early"]     = merged["net_value"] <= profit_target
    # Stop-loss trigger
    if stop_multiple is not None:
        stop_threshold   = merged["net_credit_mid"] * stop_multiple
        merged["_stop"]  = merged["net_value"] >= stop_threshold
    else:
        merged["_stop"]  = False
    merged["_is_expiry"] = merged["mark_date"] == merged["expiry"]
    merged["_is_exit"]   = merged["_early"] | merged["_is_expiry"] | merged["_stop"]

    exits = (
        merged[merged["_is_exit"]]
        .sort_values(["entry_date", "expiry", "short_strike", "long_strike", "mark_date"])
        .drop_duplicates(subset=["entry_date", "expiry", "short_strike", "long_strike"], keep="first")
        .copy()
    )

    # Exit net value: at early exit use mid; at expiry prefer last (intrinsic)
    at_expiry_only = exits["_is_expiry"] & ~exits["_early"]

    short_last = exits["short_mark_last"].where(
        pd.notna(exits["short_mark_last"]) & (exits["short_mark_last"] >= 0),
        other=exits["short_mark_mid"],
    ).fillna(0.0).clip(lower=0.0)
    long_last = exits["long_mark_last"].where(
        pd.notna(exits["long_mark_last"]) & (exits["long_mark_last"] >= 0),
        other=exits["long_mark_mid"],
    ).fillna(0.0).clip(lower=0.0)

    short_early = exits["short_mark_mid"].fillna(0.0).clip(lower=0.0)
    long_early  = exits["long_mark_mid"].fillna(0.0).clip(lower=0.0)

    exits["exit_net_value"] = np.where(
        at_expiry_only,
        short_last  - long_last,
        short_early - long_early,
    )
    exits["days_held"] = (
        pd.to_datetime(exits["mark_date"]) - pd.to_datetime(exits["entry_date"])
    ).dt.days
    exits["exit_type"] = exits.apply(
        lambda r: "early" if r["_early"] else ("stop" if r["_stop"] else "expiry"),
        axis=1,
    )
    exits = exits.rename(columns={"mark_date": "exit_date"})

    result = positions.merge(
        exits[["entry_date", "expiry", "short_strike", "long_strike",
               "exit_date", "exit_net_value", "days_held", "exit_type"]],
        on=["entry_date", "expiry", "short_strike", "long_strike"],
        how="left",
    )
    result["missing_exit_data"] = result["exit_date"].isna()
    # If no exit found: assume max loss (worst-case fill for missing data)
    result["exit_net_value"] = result["exit_net_value"].fillna(result["spread_width"])
    result["days_held"]      = result["days_held"].fillna(result["actual_dte"]).astype(int)
    result["exit_type"]      = result["exit_type"].fillna("missing")

    return result


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_spread_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add P&L and risk-adjusted return columns.

    net_pnl         (net_credit_mid - exit_net_value) × 100   (positive = profit)
    net_pnl_worst   (net_credit_worst - exit_net_value) × 100
    pnl_pct         net_pnl / (net_credit_mid × 100)          (% of premium collected)
    roc             net_pnl / max_loss                         (return on capital at risk)
    annualized_roc  roc × 365 / days_held
    is_win          net_pnl > 0
    """
    df = df.copy()
    df["net_pnl"]        = (df["net_credit_mid"]  - df["exit_net_value"]) * 100
    df["net_pnl_worst"]  = (df["net_credit_worst"] - df["exit_net_value"]) * 100
    df["pnl_pct"]        = df["net_pnl"] / (df["net_credit_mid"] * 100)
    df["roc"]            = df["net_pnl"] / df["max_loss"].clip(lower=0.01)
    df["annualized_roc"] = df["roc"] * 365 / df["days_held"].clip(lower=1)
    df["is_win"]         = df["net_pnl"] > 0
    df["is_open"]        = df["missing_exit_data"].fillna(False)
    return df


# ── Sweep orchestrator ─────────────────────────────────────────────────────────

def run_spread_delta_sweep(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_delta_targets: list[float],
    wing_delta_widths: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 20,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    profit_take_pct: float = 0.50,
) -> pd.DataFrame:
    """
    Run the put spread study across all (short_delta, wing_width, vix_threshold) combos.

    Returns a combined DataFrame with columns:
      short_delta_target, wing_delta_width, vix_threshold
    vix_threshold stored as float (NaN = no filter / baseline).
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    all_results = []

    for short_delta in short_delta_targets:
        for wing_width in wing_delta_widths:
            long_delta = short_delta - wing_width
            print(
                f"  short={short_delta:.2f}  wing={wing_width:.2f}"
                f"  (long≈{long_delta:.2f}) ...",
                end=" ", flush=True,
            )
            positions = build_put_spread_trades(
                df_opts,
                short_delta_target=short_delta,
                wing_delta_width=wing_width,
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
            positions = find_put_spread_exits(positions, df_opts, profit_take_pct=profit_take_pct)
            positions = compute_spread_metrics(positions)

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

                filtered["short_delta_target"] = short_delta
                filtered["wing_delta_width"]   = wing_width
                filtered["vix_threshold"]      = label
                all_results.append(filtered)

            n = len(positions[~positions["split_flag"] & ~positions["is_open"]])
            print(f"{n} trades.")

    if not all_results:
        return pd.DataFrame()
    return pd.concat(all_results, ignore_index=True)


# ── Summary printing ────────────────────────────────────────────────────────────

def print_spread_sweep_summary(
    sweep_df: pd.DataFrame,
    short_delta_targets: list[float],
    wing_delta_widths: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 20,
    profit_take_pct: float = 0.50,
    ticker: str = "GLD",
) -> None:
    """
    Print one summary table per wing_width.
    Rows = short_delta, columns = VIX threshold blocks.
    """
    import math

    def _vix_label(v) -> str:
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
            "credit_pct": closed["credit_pct_of_width"].mean() * 100,
        }

    width = 84
    bar   = "=" * width

    for wing_width in wing_delta_widths:
        print(f"\n{bar}")
        print(
            f"  {ticker} Bull Put Spread — {dte_target} DTE  "
            f"({int(profit_take_pct*100)}% profit take, Fridays)  "
            f"Wing ≈ {wing_width:.2f}Δ"
        )
        print(bar)

        thresh_labels = [_vix_label(v) for v in vix_thresholds]
        hdr1 = f"  {'ShortΔ':>7}"
        hdr2 = f"  {'':>7}"
        for lbl in thresh_labels:
            hdr1 += f"  {lbl:^33}"
            hdr2 += f"  {'N(E%)':>5} {'Win%':>5} {'Pnl%':>6} {'ROC%':>6} {'AnnROC%':>8} {'Crd%':>4}"
        print(hdr1)
        print(hdr2)
        print("  " + "-" * (width - 2))

        for short_delta in short_delta_targets:
            row = f"  {short_delta:>7.2f}"
            for vt in vix_thresholds:
                sub = sweep_df[
                    (sweep_df["short_delta_target"] == short_delta)
                    & (sweep_df["wing_delta_width"] == wing_width)
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
                        f" {st['credit_pct']:>3.0f}%"
                    )
                else:
                    row += f"  {'—':^33}"
            print(row)

        print("  " + "-" * (width - 2))
        print(
            f"  N = closed trades (split-spanning excluded)  "
            f"E% = {int(profit_take_pct*100)}% profit take  "
            f"Crd% = net_credit/spread_width"
        )
        print(bar)


def print_spread_year_detail(
    sweep_df: pd.DataFrame,
    short_delta: float,
    wing_width: float,
    vix_threshold: Optional[float] = None,
) -> None:
    """Print per-year breakdown for one (short_delta, wing_width, vix_threshold) combo."""
    import math

    vt_label = (
        "All VIX"
        if (vix_threshold is None or math.isnan(float(vix_threshold or 0)))
        else f"VIX<{int(vix_threshold)}"
    )
    sub = sweep_df[
        (sweep_df["short_delta_target"] == short_delta)
        & (sweep_df["wing_delta_width"] == wing_width)
        & (
            (sweep_df["vix_threshold"].isna() & (vix_threshold is None))
            | (sweep_df["vix_threshold"] == float(vix_threshold or float("nan")))
        )
    ].copy()
    closed = sub[~sub["is_open"] & ~sub["split_flag"]].copy()
    if closed.empty:
        print("No data.")
        return

    long_delta = short_delta - wing_width
    print(
        f"\n  short={short_delta:.2f}  wing={wing_width:.2f}"
        f"  (long≈{long_delta:.2f})  {vt_label}  — per-year"
    )
    print(
        f"  {'Year':>4}  {'N':>3}  {'E%':>4}  {'Win%':>5}  {'Pnl%':>6}  "
        f"{'ROC%':>6}  {'AnnROC%':>8}  {'AvgDays':>7}  {'Crd%':>5}"
    )
    print("  " + "-" * 68)

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
            f"  {grp['credit_pct_of_width'].mean()*100:>4.0f}%"
        )
    print()


# ── Top-level runner ────────────────────────────────────────────────────────────

def run_put_spread_study(
    ticker: str,
    start: date,
    end: date,
    short_delta_targets: list[float],
    wing_delta_widths: list[float],
    vix_thresholds: list[Optional[float]],
    dte_target: int = 20,
    dte_tol: int = 5,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    profit_take_pct: float = 0.50,
    output_csv: Optional[str] = None,
    force_sync: bool = False,
    detail_short_delta: Optional[float] = None,
    detail_wing_width: Optional[float] = None,
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
    print(
        f"\nRunning put spread sweep:"
        f" short_deltas={short_delta_targets}"
        f" wing_widths={wing_delta_widths}"
    )
    sweep = run_spread_delta_sweep(
        df_opts=df_opts,
        df_vix=df_vix,
        short_delta_targets=short_delta_targets,
        wing_delta_widths=wing_delta_widths,
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
    print_spread_sweep_summary(
        sweep, short_delta_targets, wing_delta_widths, vix_thresholds,
        dte_target, profit_take_pct, ticker=ticker,
    )

    # 6. Optional per-year detail
    if detail_short_delta is not None and detail_wing_width is not None:
        print_spread_year_detail(sweep, detail_short_delta, detail_wing_width, detail_vix)

    # 7. CSV
    if output_csv:
        col_order = [
            "short_delta_target", "wing_delta_width", "vix_threshold",
            "entry_date", "expiry", "actual_dte",
            "short_strike", "long_strike", "spread_width",
            "short_delta", "long_delta",
            "short_mid", "short_bid", "net_credit_mid", "net_credit_worst",
            "credit_pct_of_width", "max_loss",
            "vix_on_entry",
            "exit_date", "exit_net_value", "exit_type", "days_held",
            "net_pnl", "net_pnl_worst",
            "pnl_pct", "roc", "annualized_roc",
            "is_win", "is_open", "split_flag", "missing_exit_data",
        ]
        save_cols = [c for c in col_order if c in sweep.columns]
        sweep[save_cols].to_csv(output_csv, index=False)
        print(f"Saved {len(sweep)} rows to {output_csv}")

    return sweep

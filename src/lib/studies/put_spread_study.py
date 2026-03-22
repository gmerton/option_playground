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
- Apply optional MA trend filter: skip entries when spot < N-day MA

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
- Stock prices:  Tradier daily close, cached to data/cache/{ticker}_stock.parquet
"""

from __future__ import annotations

import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.commons.bs import implied_vol as _bs_implied_vol
from lib.studies.put_study import fetch_vix_data

_REPO_ROOT   = pathlib.Path(__file__).resolve().parents[3]
_CACHE_DIR   = _REPO_ROOT / "data" / "cache"


# ── Stock price / MA helpers ───────────────────────────────────────────────────

def fetch_stock_history(ticker: str, start: date, end: date) -> pd.DataFrame:
    """
    Fetch daily close prices for ticker via Tradier, cached to
    data/cache/{ticker}_stock.parquet.

    Returns DataFrame with columns: trade_date (date), close (float).
    Incremental: only fetches dates not already in the cache.
    start is padded by 120 days so MA warmup is available.
    """
    import asyncio
    import os
    from lib.tradier.tradier_client_wrapper import TradierClient
    from lib.tradier.get_daily_history import get_daily_history

    cache_path = _CACHE_DIR / f"{ticker}_stock.parquet"
    need_start = start - timedelta(days=120)   # MA warmup buffer
    today      = date.today()

    if cache_path.exists():
        cached = pd.read_parquet(cache_path)
        cached["trade_date"] = pd.to_datetime(cached["trade_date"]).dt.date
        max_cached = cached["trade_date"].max()
        if max_cached >= today - timedelta(days=2) and cached["trade_date"].min() <= need_start:
            mask = cached["trade_date"] <= end
            return cached[mask].reset_index(drop=True)
        fetch_start = max_cached + timedelta(days=1)
        print(f"Stock cache ({ticker}): extending from {fetch_start} → {today} ...")
    else:
        cached     = pd.DataFrame(columns=["trade_date", "close"])
        fetch_start = need_start
        print(f"Stock cache ({ticker}): fetching {fetch_start} → {today} ...")

    api_key = os.environ.get("TRADIER_API_KEY", "")
    if not api_key:
        print(f"  WARNING: TRADIER_API_KEY not set — cannot fetch stock history for {ticker}")
        return cached

    async def _fetch():
        async with TradierClient(api_key=api_key) as client:
            return await get_daily_history(ticker, fetch_start, today, client=client)

    raw = asyncio.run(_fetch())

    if raw is None or raw.empty:
        print(f"  No data returned from Tradier for {ticker}.")
    else:
        new_rows = raw[["close"]].copy()
        new_rows.index = pd.to_datetime(new_rows.index).date
        new_rows.index.name = "trade_date"
        new_rows = new_rows.reset_index()
        new_rows["trade_date"] = pd.to_datetime(new_rows["trade_date"]).dt.date
        new_rows["close"]      = pd.to_numeric(new_rows["close"], errors="coerce")

        combined = pd.concat([cached, new_rows], ignore_index=True)
        combined = combined.drop_duplicates(subset=["trade_date"], keep="last")
        combined = combined.sort_values("trade_date").reset_index(drop=True)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(cache_path, index=False)
        cached = combined

    mask = cached["trade_date"] <= end
    return cached[mask].reset_index(drop=True)


def add_ma_column(
    positions: pd.DataFrame,
    stock_df: pd.DataFrame,
    ma_days: int = 50,
) -> pd.DataFrame:
    """
    Add ma_ratio_N column (float) to positions DataFrame.
    ma_ratio = spot_close / rolling_MA — values > 1.0 mean spot is above the MA.
    Entries where the MA cannot be computed (warmup) get NaN.
    """
    col_name = f"ma_ratio_{ma_days}"
    df = stock_df.sort_values("trade_date").copy()
    df["_ma"]       = df["close"].rolling(ma_days, min_periods=ma_days).mean()
    df["_ma_ratio"] = df["close"] / df["_ma"]
    ratio_map = df.set_index("trade_date")["_ma_ratio"].to_dict()

    pos = positions.copy()
    pos[col_name] = pos["entry_date"].map(ratio_map)
    return pos


def print_ma_filter_comparison(
    sweep_df: pd.DataFrame,
    short_delta: float,
    wing_width: float,
    vix_threshold: Optional[float] = None,
    ma_days: int = 50,
    ratio_thresholds: Optional[list] = None,
) -> None:
    """
    Print spot/MA{ma_days} ratio analysis for a specific (short_delta, wing, vix) combo.

    Two tables:
    1. Threshold sweep — require ratio >= X (like fwd_vol_factor sweep).
       Answers: "what happens if we only enter when spot/MA >= X?"
    2. Bucket breakdown — performance by ratio range.
       Answers: "where do the losses actually live?"
    """
    import math

    col_name = f"ma_ratio_{ma_days}"
    if col_name not in sweep_df.columns:
        print(f"  No {col_name} column — run with --ma-filter {ma_days}.")
        return

    if ratio_thresholds is None:
        ratio_thresholds = [None, 1.10, 1.05, 1.00, 0.97, 0.95, 0.90]

    vt_label = (
        "All VIX"
        if (vix_threshold is None or (isinstance(vix_threshold, float) and math.isnan(vix_threshold)))
        else f"VIX<{int(vix_threshold)}"
    )

    sub = sweep_df[
        (sweep_df["short_delta_target"] == short_delta)
        & (sweep_df["wing_delta_width"]  == wing_width)
        & (
            (sweep_df["vix_threshold"].isna() & (vix_threshold is None))
            | (sweep_df["vix_threshold"] == float(vix_threshold or float("nan")))
        )
    ].copy()
    closed = sub[~sub["is_open"] & ~sub["split_flag"]].copy()
    if closed.empty:
        print("  No data.")
        return

    base_n   = len(closed)
    avg_ratio = closed[col_name].mean()
    nan_count = closed[col_name].isna().sum()

    print(f"\n  spot/MA{ma_days} Ratio Filter  ·  short={short_delta:.2f}  wing={wing_width:.2f}  {vt_label}")
    print(f"  ratio = spot_close / MA{ma_days}  |  >1.0 = spot above MA (uptrend); <1.0 = spot below MA (downtrend)")
    print(f"  Overall avg ratio: {avg_ratio:.3f}  |  NaN entries (warmup): {nan_count}")

    # ── Table 1: Threshold sweep (require ratio >= X) ──────────────────────────
    print(f"\n  Threshold sweep (require ratio ≥ X to enter):")
    print(f"  {'min ratio':>10}  {'N':>4}  {'Skip%':>6}  {'Win%':>5}  {'ROC%':>6}  {'AnnROC%':>8}  {'AvgRatio':>9}")
    print("  " + "─" * 64)

    for thr in ratio_thresholds:
        if thr is None:
            grp   = closed
            label = "  (no filter)"
        else:
            grp   = closed[closed[col_name].isna() | (closed[col_name] >= thr)]
            label = f"  ≥ {thr:.2f}      "

        n = len(grp)
        if n == 0:
            print(f"  {label:>10}  {0:>4}  {'—':>6}")
            continue
        skip_pct  = (base_n - n) / base_n * 100
        win_pct   = grp["is_win"].mean() * 100
        roc       = grp["roc"].mean() * 100
        ann_roc   = grp["annualized_roc"].mean() * 100
        avg_r     = grp[col_name].mean()
        print(
            f"  {label:>10}  {n:>4}  {skip_pct:>5.1f}%  {win_pct:>4.1f}%"
            f"  {roc:>+5.2f}%  {ann_roc:>+7.1f}%  {avg_r:>9.3f}"
        )

    # ── Table 2: Bucket breakdown ──────────────────────────────────────────────
    buckets = [
        (1.10, None,  "≥ 1.10"),
        (1.05, 1.10,  "1.05 – 1.10"),
        (1.00, 1.05,  "1.00 – 1.05"),
        (0.97, 1.00,  "0.97 – 1.00"),
        (0.95, 0.97,  "0.95 – 0.97"),
        (0.90, 0.95,  "0.90 – 0.95"),
        (None, 0.90,  "< 0.90"),
    ]

    print(f"\n  Performance by ratio bucket:")
    print(f"  {'Ratio range':>14}  {'N':>4}  {'Pct%':>5}  {'Win%':>5}  {'ROC%':>6}  {'AnnROC%':>8}  {'AvgRatio':>9}")
    print("  " + "─" * 68)

    for lo, hi, label in buckets:
        mask = pd.Series([True] * len(closed), index=closed.index)
        if lo is not None:
            mask &= closed[col_name] >= lo
        if hi is not None:
            mask &= closed[col_name] < hi
        grp = closed[mask]
        n   = len(grp)
        if n == 0:
            print(f"  {label:>14}  {0:>4}")
            continue
        pct_of_total = n / base_n * 100
        win_pct      = grp["is_win"].mean() * 100
        roc          = grp["roc"].mean() * 100
        ann_roc      = grp["annualized_roc"].mean() * 100
        avg_r        = grp[col_name].mean()
        print(
            f"  {label:>14}  {n:>4}  {pct_of_total:>4.1f}%  {win_pct:>4.1f}%"
            f"  {roc:>+5.2f}%  {ann_roc:>+7.1f}%  {avg_r:>9.3f}"
        )
    print()


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
    ann_target: Optional[float] = None,
) -> pd.DataFrame:
    """
    For each spread position, find the exit date and net spread value.

    Exit when daily (short_mark_mid - long_mark_mid) ≤ (1 - profit_take_pct) × net_credit_mid,
    or at expiry using last/mid prices for each leg.

    stop_multiple: if set, also exit when net_value ≥ stop_multiple × net_credit_mid.
    ann_target: if set (e.g. 1.0 = 100%), overrides profit_take_pct with an annualized ROC target.
      Exit when (pnl_now / margin) * (365 / days_held) >= ann_target.

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
    if ann_target is not None and ann_target > 0:
        merged["_days_held"] = (
            pd.to_datetime(merged["mark_date"]) - pd.to_datetime(merged["entry_date"])
        ).dt.days.clip(lower=1)
        merged["_pnl_now"] = merged["net_credit_mid"] - merged["net_value"]
        merged["_margin"]  = (merged["short_strike"] - merged["long_strike"] - merged["net_credit_mid"]).clip(lower=0.01)
        merged["_early"]   = (
            (merged["_pnl_now"] / merged["_margin"]) * (365.0 / merged["_days_held"])
        ) >= ann_target
    else:
        profit_target    = merged["net_credit_mid"] * (1.0 - profit_take_pct)
        merged["_early"] = merged["net_value"] <= profit_target
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


# ── Forward volatility ────────────────────────────────────────────────────────

def _leg_iv(mid: float, strike: float, dte_days: int, r: float = 0.04) -> Optional[float]:
    """BS implied vol for a put leg using S ≈ K (ATM approximation)."""
    T = dte_days / 365.0
    if T <= 0 or mid <= 0 or strike <= 0:
        return None
    return _bs_implied_vol(price=mid, S=strike, K=strike, T=T, r=r, q=0.0, opt_type="put")


def enrich_put_spreads_with_fwd_vol(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    r: float = 0.04,
    min_gap: int = 15,
    max_gap: int = 60,
) -> pd.DataFrame:
    """
    Add forward vol metrics to put spread positions.

    Uses ATM puts at (entry_date, spread_expiry) → near_iv, then finds the next
    available expiry min_gap–max_gap days later → far_iv. Computes sigma_fwd and
    fwd_vol_factor via variance decomposition.

    Added columns: near_iv, far_iv, sigma_fwd, fwd_vol_factor
      fwd_vol_factor < 1: market expects vol to FALL → favorable for short puts
      fwd_vol_factor > 1: market expects vol to RISE → unfavorable
      NaN: extreme backwardation (forward variance < 0) or missing data
    """
    if positions.empty:
        for col in ("near_iv", "far_iv", "sigma_fwd", "fwd_vol_factor"):
            positions[col] = np.nan
        return positions

    puts = df_opts[df_opts["cp"] == "P"].copy()
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(puts[col]):
            puts[col] = puts[col].dt.date

    puts = puts[puts["delta"].notna() & (puts["mid"] > 0)].copy()
    puts["_delta_dist"] = (puts["delta"] - (-0.50)).abs()
    puts_atm = (
        puts.sort_values(["trade_date", "expiry", "_delta_dist"])
        .drop_duplicates(subset=["trade_date", "expiry"], keep="first")
        [["trade_date", "expiry", "strike", "mid", "dte"]]
        .copy()
    )
    puts_atm["trade_date"] = puts_atm["trade_date"].apply(
        lambda x: x if isinstance(x, date) else x.date()
    )
    puts_atm["expiry"] = puts_atm["expiry"].apply(
        lambda x: x if isinstance(x, date) else x.date()
    )
    lookup = puts_atm.set_index(["trade_date", "expiry"])

    expiries_by_date = (
        puts_atm.groupby("trade_date")["expiry"]
        .apply(lambda s: sorted(s.unique()))
        .to_dict()
    )

    near_ivs, far_ivs, sigmas_fwd, factors = [], [], [], []

    for _, row in positions.iterrows():
        entry_date  = row["entry_date"]
        near_expiry = row["expiry"]
        if isinstance(near_expiry, str):
            near_expiry = date.fromisoformat(near_expiry)
        if isinstance(entry_date, str):
            entry_date = date.fromisoformat(entry_date)

        s_iv = l_iv = sigma_fwd = factor = None

        near_key = (entry_date, near_expiry)
        if near_key in lookup.index:
            nr = lookup.loc[near_key]
            s_iv = _leg_iv(nr["mid"], nr["strike"], int(nr["dte"]), r)

            if s_iv:
                for far_exp in expiries_by_date.get(entry_date, []):
                    gap = (pd.Timestamp(far_exp) - pd.Timestamp(near_expiry)).days
                    if min_gap <= gap <= max_gap:
                        far_key = (entry_date, far_exp)
                        if far_key in lookup.index:
                            fr = lookup.loc[far_key]
                            l_iv = _leg_iv(fr["mid"], fr["strike"], int(fr["dte"]), r)
                            if l_iv:
                                T1 = nr["dte"] / 365.0
                                T2 = fr["dte"] / 365.0
                                dT = T2 - T1
                                if dT > 0:
                                    var_fwd = (l_iv**2 * T2 - s_iv**2 * T1) / dT
                                    if var_fwd > 0:
                                        sigma_fwd = var_fwd ** 0.5
                                        factor    = sigma_fwd / s_iv
                        break

        near_ivs.append(s_iv)
        far_ivs.append(l_iv)
        sigmas_fwd.append(sigma_fwd)
        factors.append(factor)

    pos = positions.copy()
    pos["near_iv"]        = near_ivs
    pos["far_iv"]         = far_ivs
    pos["sigma_fwd"]      = sigmas_fwd
    pos["fwd_vol_factor"] = factors
    return pos


def print_fwd_vol_factor_sweep(
    sweep_df: pd.DataFrame,
    short_delta: float,
    wing_width: float,
    vix_threshold: Optional[float] = None,
    fwd_vol_thresholds: Optional[list] = None,
) -> None:
    """
    Print effect of a max-fwd_vol_factor filter on put spread performance.

    fwd_vol_factor = sigma_fwd / near_iv
      < 1: market expects vol to FALL → favorable for short puts (enter)
      > 1: market expects vol to RISE → unfavorable (consider skipping)
      NaN: extreme backwardation or missing far expiry → always included
    """
    import math

    if fwd_vol_thresholds is None:
        fwd_vol_thresholds = [None, 1.30, 1.20, 1.10, 1.00, 0.90, 0.80]

    def _vix_label(v) -> str:
        return "All VIX" if (v is None or (isinstance(v, float) and math.isnan(float(v or 0)))) else f"VIX<{int(v)}"

    sub = sweep_df[
        (sweep_df["short_delta_target"] == short_delta)
        & (sweep_df["wing_delta_width"]  == wing_width)
    ].copy()
    if vix_threshold is not None:
        sub = sub[sub["vix_threshold"] == float(vix_threshold)]
    else:
        sub = sub[sub["vix_threshold"].isna()]

    closed_base = sub[~sub["is_open"] & ~sub["split_flag"]]
    if closed_base.empty:
        print("  No data.")
        return

    vix_lbl    = _vix_label(vix_threshold)
    base_n     = len(closed_base)
    avg_factor = closed_base["fwd_vol_factor"].mean()
    nan_count  = closed_base["fwd_vol_factor"].isna().sum()

    print(f"\n  Forward Vol Factor Filter  ·  short={short_delta:.2f}  wing={wing_width:.2f}  {vix_lbl}")
    print(f"  fwd_vol_factor = sigma_fwd / near_iv  |  <1.0 = vol expected to fall (favorable for short puts)")
    print(f"  Overall avg factor: {avg_factor:.3f}  |  NaN entries: {nan_count}")
    print(f"  {'max factor':>12}  {'N':>4}  {'Skip%':>6}  {'Win%':>5}  {'ROC%':>6}  {'AnnROC%':>8}  {'AvgFactor':>9}")
    print("  " + "-" * 68)

    for thr in fwd_vol_thresholds:
        if thr is None:
            grp   = closed_base
            label = "  (no filter)"
        else:
            grp   = closed_base[
                closed_base["fwd_vol_factor"].isna() | (closed_base["fwd_vol_factor"] <= thr)
            ]
            label = f"  ≤ {thr:.2f}      "

        n = len(grp)
        if n == 0:
            print(f"  {label:>12}  {n:>4}  {'—':>6}")
            continue

        skip_pct = (base_n - n) / base_n * 100
        win_pct  = grp["is_win"].mean() * 100
        roc      = grp["roc"].mean() * 100
        ann_roc  = grp["annualized_roc"].mean() * 100
        avg_f    = grp["fwd_vol_factor"].mean()
        print(
            f"  {label:>12}  {n:>4}  {skip_pct:>5.1f}%  {win_pct:>4.1f}%"
            f"  {roc:>+5.2f}%  {ann_roc:>+7.1f}%  {avg_f:>9.3f}"
        )
    print()


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
    ann_target: Optional[float] = None,
    max_fwd_vol_factor: Optional[float] = None,
    stock_df: Optional[pd.DataFrame] = None,
    ma_filter_days: Optional[int] = None,
    ma_thresholds: Optional[list] = None,
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
            positions = enrich_put_spreads_with_fwd_vol(positions, df_opts)

            if stock_df is not None and ma_filter_days is not None:
                positions = add_ma_column(positions, stock_df, ma_filter_days)

            # Add MA columns for all requested sweep thresholds
            if stock_df is not None and ma_thresholds:
                for _ma_days in [d for d in ma_thresholds if d is not None]:
                    positions = add_ma_column(positions, stock_df, _ma_days)

            if max_fwd_vol_factor is not None:
                positions = positions[
                    positions["fwd_vol_factor"].isna()
                    | (positions["fwd_vol_factor"] <= max_fwd_vol_factor)
                ]
            if positions.empty:
                print("no entries after fwd_vol_factor filter.")
                continue

            positions = find_put_spread_exits(positions, df_opts, profit_take_pct=profit_take_pct, ann_target=ann_target)
            positions = compute_spread_metrics(positions)

            _ma_sweep = ma_thresholds if ma_thresholds is not None else [None]
            for ma_thresh in _ma_sweep:
                if ma_thresh is not None:
                    _col = f"ma_ratio_{ma_thresh}"
                    ma_pos = (
                        positions[positions[_col].isna() | (positions[_col] >= 1.0)].copy()
                        if _col in positions.columns
                        else positions.copy()
                    )
                else:
                    ma_pos = positions.copy()

                for vix_thresh in vix_thresholds:
                    if vix_thresh is None:
                        filtered = ma_pos.copy()
                        vix_label = float("nan")
                    else:
                        filtered = ma_pos[
                            ma_pos["vix_on_entry"].isna()
                            | (ma_pos["vix_on_entry"] < vix_thresh)
                        ].copy()
                        vix_label = float(vix_thresh)

                    filtered["short_delta_target"] = short_delta
                    filtered["wing_delta_width"]   = wing_width
                    filtered["vix_threshold"]      = vix_label
                    filtered["ma_threshold"]       = float("nan") if ma_thresh is None else float(ma_thresh)
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
    ma_thresholds: Optional[list] = None,
    entry_weekday: int = 4,
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

    _day_name = {0: "Mondays", 1: "Tuesdays", 2: "Wednesdays", 3: "Thursdays", 4: "Fridays"}.get(entry_weekday, f"weekday={entry_weekday}")
    _ma_sweep = ma_thresholds if ma_thresholds is not None else [None]

    for ma_thresh in _ma_sweep:
        if "ma_threshold" in sweep_df.columns:
            if ma_thresh is None:
                ma_df = sweep_df[sweep_df["ma_threshold"].isna()].copy()
            else:
                ma_df = sweep_df[sweep_df["ma_threshold"] == float(ma_thresh)].copy()
        else:
            ma_df = sweep_df.copy()

        ma_label = "" if ma_thresh is None else f"  [spot > {ma_thresh}-day MA]"

        for wing_width in wing_delta_widths:
            print(f"\n{bar}")
            print(
                f"  {ticker} Bull Put Spread — {dte_target} DTE  "
                f"({int(profit_take_pct*100)}% profit take, {_day_name})"
                f"  Wing ≈ {wing_width:.2f}Δ{ma_label}"
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
                    sub = ma_df[
                        (ma_df["short_delta_target"] == short_delta)
                        & (ma_df["wing_delta_width"] == wing_width)
                        & (
                            (ma_df["vix_threshold"].isna() & (vt is None))
                            | (ma_df["vix_threshold"] == (float(vt) if vt is not None else float("nan")))
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
    ann_target: Optional[float] = None,
    output_csv: Optional[str] = None,
    force_sync: bool = False,
    detail_short_delta: Optional[float] = None,
    detail_wing_width: Optional[float] = None,
    detail_vix: Optional[float] = None,
    fwd_vol_thresholds: Optional[list] = None,
    max_fwd_vol_factor: Optional[float] = None,
    ma_filter_days: Optional[int] = None,
    ma_thresholds: Optional[list] = None,
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

    # 4. Stock price history (for MA filter)
    stock_df: Optional[pd.DataFrame] = None
    _needs_stock = ma_filter_days is not None or (ma_thresholds and any(d is not None for d in ma_thresholds))
    if _needs_stock:
        _ma_desc = ", ".join(str(d) for d in ([ma_filter_days] if ma_filter_days else []) + [d for d in (ma_thresholds or []) if d is not None])
        print(f"Fetching {ticker} daily price history for MA filter(s): {_ma_desc} ...")
        stock_df = fetch_stock_history(ticker, start, end)
        if stock_df.empty:
            print("  WARNING: no stock price data — MA filter will be skipped.")
            stock_df = None

    # 5. Run sweep
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
        ann_target=ann_target,
        max_fwd_vol_factor=max_fwd_vol_factor,
        stock_df=stock_df,
        ma_filter_days=ma_filter_days,
        ma_thresholds=ma_thresholds,
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
        ma_thresholds=ma_thresholds, entry_weekday=entry_weekday,
    )

    # 6. Optional per-year detail + fwd vol factor sweep + MA filter comparison
    if detail_short_delta is not None and detail_wing_width is not None:
        print_spread_year_detail(sweep, detail_short_delta, detail_wing_width, detail_vix)
        if "fwd_vol_factor" in sweep.columns:
            print_fwd_vol_factor_sweep(
                sweep, detail_short_delta, detail_wing_width, detail_vix,
                fwd_vol_thresholds,
            )
        if ma_filter_days is not None:
            print_ma_filter_comparison(
                sweep, detail_short_delta, detail_wing_width, detail_vix, ma_filter_days,
            )

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
            "near_iv", "far_iv", "sigma_fwd", "fwd_vol_factor",
            "exit_date", "exit_net_value", "exit_type", "days_held",
            "net_pnl", "net_pnl_worst",
            "pnl_pct", "roc", "annualized_roc",
            "is_win", "is_open", "split_flag", "missing_exit_data",
        ]
        save_cols = [c for c in col_order if c in sweep.columns]
        sweep[save_cols].to_csv(output_csv, index=False)
        print(f"Saved {len(sweep)} rows to {output_csv}")

    return sweep

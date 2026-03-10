"""
Put calendar spread backtest engine — short ATM put (near expiry) + long put (far expiry)
at the same strike.  Sweep across delta targets and VIX regime filters.

Strategy
--------
Long put calendar (net debit):
  - Sell a put at the short expiry (~20 DTE)
  - Buy a put at the long expiry (~27 DTE) at the EXACT SAME STRIKE
  - Hold until the short leg expires
  - On short expiry day, close the long leg at market (still has ~7 DTE remaining)

P&L per share:
  (short_entry_mid - short_exit_mid) + (long_exit_mid - long_entry_mid)

ROC = net_pnl / net_debit   where net_debit = long_entry_mid - short_entry_mid

Profitable when UVXY stays near the strike at short expiry (short decays to zero while
long retains most of its time value).  Loses when UVXY makes a large move in either
direction — the calendar collapses toward intrinsic parity on both legs.

Sweep
-----
  delta_targets   e.g. [0.40, 0.45, 0.50]   (unsigned; ATM = 0.50)
  vix_thresholds  e.g. [None, 30, 25, 20]    (None = no filter; numeric = skip when VIX ≥ threshold)

Data sources
------------
- Options data:  MySQL options_cache (synced from Athena by straddle_study.sync_options_cache)
- VIX data:      Tradier VIX daily close, cached to data/cache/vix_daily.parquet

Usage
-----
  PYTHONPATH=src python run_calendar.py --ticker UVXY --spread 0.25
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.commons.bs import implied_vol as _bs_implied_vol
from lib.studies.put_study import fetch_vix_data


# ── Entry construction ─────────────────────────────────────────────────────────

def build_calendar_trades(
    df: pd.DataFrame,
    delta_target: float,
    short_dte_target: int = 20,
    long_dte_target: int = 27,
    dte_tol: int = 5,
    gap_tol: int = 5,
    min_gap: Optional[int] = None,
    max_gap: Optional[int] = None,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
) -> pd.DataFrame:
    """
    Find put calendar spread entries from the options cache.

    delta_target:      unsigned put delta for the short (near) leg. e.g. 0.50 = ATM
    short_dte_target:  target DTE for the short leg (e.g. 20)
    long_dte_target:   target DTE for the long leg (e.g. 27)
    dte_tol:           ±tolerance around short_dte_target for the short leg selection
    gap_tol:           ±tolerance in days for matching long_dte_target

    min_gap / max_gap: if provided, override long_dte_target+gap_tol and instead select
                       the next available expiry with gap in [min_gap, max_gap] days.
                       This naturally picks the next standard monthly expiry.
    max_spread_pct:    if set, skip entries where (ask-bid)/mid > threshold on short leg
    max_delta_err:     max |actual_delta - (-delta_target)| for the short leg

    Long leg is matched by same STRIKE (not by delta).

    Returns one row per entry date with both legs joined.
    """
    split_dates = split_dates or []
    df = df.copy()

    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    td_dt = pd.to_datetime(df["trade_date"])

    # ── Short (near) leg ───────────────────────────────────────────────────────
    short_mask = (
        (td_dt.dt.dayofweek == entry_weekday)
        & (df["dte"] >= short_dte_target - dte_tol)
        & (df["dte"] <= short_dte_target + dte_tol)
        & (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["cp"] == "P")
        & (df["delta"].notna())
    )
    short_pool = df[short_mask].copy()

    if max_spread_pct is not None:
        short_pool["_spread_pct"] = (short_pool["ask"] - short_pool["bid"]) / short_pool["mid"]
        short_pool = short_pool[short_pool["_spread_pct"] <= max_spread_pct]

    # Delta filter: puts stored as negative; target = -delta_target
    short_pool["_delta_err"] = (short_pool["delta"] - (-delta_target)).abs()
    short_pool = short_pool[short_pool["_delta_err"] <= max_delta_err]
    if short_pool.empty:
        return pd.DataFrame()

    # Best per (trade_date, expiry): closest delta
    short_pool = short_pool.sort_values(["trade_date", "expiry", "_delta_err"])
    short_pool = short_pool.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    # Best expiry per trade_date: DTE closest to short_dte_target
    short_pool["_dte_err"] = (short_pool["dte"] - short_dte_target).abs()
    short_pool = short_pool.sort_values(["trade_date", "_dte_err"])
    short_pool = short_pool.drop_duplicates(subset=["trade_date"], keep="first")

    short_leg = short_pool.rename(columns={
        "trade_date": "entry_date",
        "expiry":     "short_expiry",
        "dte":        "short_actual_dte",
        "strike":     "strike",
        "mid":        "short_entry_mid",
        "bid":        "short_entry_bid",
        "ask":        "short_entry_ask",
        "delta":      "short_entry_delta",
    })[[
        "entry_date", "short_expiry", "short_actual_dte", "strike",
        "short_entry_mid", "short_entry_bid", "short_entry_ask", "short_entry_delta",
    ]]

    # ── Long (far) leg ─────────────────────────────────────────────────────────
    if min_gap is not None:
        _max_gap = max_gap if max_gap is not None else min_gap + 35
        long_dte_lo, long_dte_hi = min_gap, _max_gap
    else:
        long_dte_lo = long_dte_target - gap_tol
        long_dte_hi = long_dte_target + gap_tol

    long_mask = (
        (td_dt.dt.dayofweek == entry_weekday)
        & (df["dte"] >= long_dte_lo)
        & (df["dte"] <= long_dte_hi)
        & (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["cp"] == "P")
        & (df["delta"].notna())
    )
    long_pool = df[long_mask].copy()
    long_pool = long_pool.rename(columns={
        "trade_date": "entry_date",
        "expiry":     "long_expiry",
        "dte":        "long_actual_dte",
        "strike":     "strike",
        "mid":        "long_entry_mid",
        "bid":        "long_entry_bid",
        "ask":        "long_entry_ask",
        "delta":      "long_entry_delta",
    })

    # Join on (entry_date, strike)
    merged = short_leg.merge(
        long_pool[[
            "entry_date", "long_expiry", "long_actual_dte", "strike",
            "long_entry_mid", "long_entry_bid", "long_entry_ask", "long_entry_delta",
        ]],
        on=["entry_date", "strike"],
        how="inner",
    )

    # Long expiry must be strictly after short expiry (different expiry dates)
    merged = merged[merged["long_expiry"] > merged["short_expiry"]].copy()
    if merged.empty:
        return pd.DataFrame()

    # Among valid long legs: next-expiry mode → pick smallest gap; target mode → closest to target
    if min_gap is not None:
        merged = merged.sort_values(["entry_date", "long_actual_dte"])
    else:
        merged["_long_dte_err"] = (merged["long_actual_dte"] - long_dte_target).abs()
        merged = merged.sort_values(["entry_date", "_long_dte_err"])
    merged = merged.drop_duplicates(subset=["entry_date"], keep="first")

    # Net debit: cost to enter the calendar (long > short for a long calendar)
    merged["net_debit"] = merged["long_entry_mid"] - merged["short_entry_mid"]

    # Must be a positive debit (long leg costs more than short leg premium)
    merged = merged[merged["net_debit"] > 0].copy()

    # IV term structure ratio: near_iv_proxy / far_iv_proxy
    # iv_proxy = mid / sqrt(dte/365) — proportional to IV for near-ATM options
    # ratio > 1.0 → near-term IV elevated (backwardation) → favorable calendar entry
    # ratio < 1.0 → far-term IV elevated (contango) → unfavorable
    merged["iv_ratio"] = (
        (merged["short_entry_mid"] / np.sqrt(merged["short_actual_dte"] / 365))
        / (merged["long_entry_mid"] / np.sqrt(merged["long_actual_dte"] / 365))
    )
    if merged.empty:
        return pd.DataFrame()

    # Days held = entry_date → short_expiry (we hold until short expires)
    merged["days_held_entry"] = (
        pd.to_datetime(merged["short_expiry"]) - pd.to_datetime(merged["entry_date"])
    ).dt.days

    # Split flag: exclude positions spanning any split date
    def _spans(entry_d: date, long_exp: date) -> bool:
        return any(entry_d < sd <= long_exp for sd in split_dates)

    merged["split_flag"] = [
        _spans(r.entry_date, r.long_expiry)
        for r in merged.itertuples(index=False)
    ]

    return merged.sort_values("entry_date").reset_index(drop=True)


# ── Exit scanner ───────────────────────────────────────────────────────────────

def find_calendar_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_target_roc: Optional[float] = None,
) -> pd.DataFrame:
    """
    For each calendar position, find the exit — either an early profit-take or hold to short expiry.

    profit_target_roc: if set (e.g. 0.50 = 50% ROC), scan daily for the first day where
      spread_value = (long_mid - short_mid) >= net_debit * (1 + profit_target_roc).
      If triggered, exit early on that date. Otherwise fall through to hold-to-expiry.

    Hold-to-expiry exit:
      Short leg: `last` price on short_expiry day (settlement/intrinsic), fallback to `mid`. Clip ≥ 0.
      Long leg:  `mid` price on short_expiry day (~gap DTE remaining).
      Date tolerance: ±3 calendar days for holidays/gaps.

    Adds columns:
      short_exit_mid    — exit value of short leg
      long_exit_mid     — exit value of long leg
      exit_date         — actual exit date
      exit_type         — "profit_take" | "expiry"
      exit_found        — True if both legs had exit data
      short_expired_otm — True if short put expired worthless (only meaningful for expiry exits)
    """
    if positions.empty:
        for c in ("short_exit_mid", "long_exit_mid", "exit_date", "exit_type", "exit_found", "short_expired_otm"):
            positions[c] = None
        return positions

    puts = df_opts[df_opts["cp"] == "P"][
        ["trade_date", "expiry", "strike", "mid", "last"]
    ].copy()

    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(puts[col]):
            puts[col] = puts[col].dt.date

    early_exits = pd.DataFrame()  # entry_date → early exit info

    # ── Daily profit-take scan ──────────────────────────────────────────────────
    if profit_target_roc is not None:
        short_daily = puts.rename(columns={
            "expiry":     "short_expiry",
            "trade_date": "scan_date",
            "mid":        "_s_mid",
        })
        long_daily = puts.rename(columns={
            "expiry":     "long_expiry",
            "trade_date": "scan_date",
            "mid":        "_l_mid",
        })

        # Merge positions with daily short leg marks
        scan = positions[["entry_date", "short_expiry", "long_expiry", "strike", "net_debit"]].merge(
            short_daily[["short_expiry", "strike", "scan_date", "_s_mid"]],
            on=["short_expiry", "strike"],
            how="left",
        )
        # Filter to dates strictly after entry and on/before short_expiry
        scan = scan[
            (pd.to_datetime(scan["scan_date"]) > pd.to_datetime(scan["entry_date"]))
            & (pd.to_datetime(scan["scan_date"]) <= pd.to_datetime(scan["short_expiry"]))
        ]
        # Add long leg daily marks on the same scan_date
        scan = scan.merge(
            long_daily[["long_expiry", "strike", "scan_date", "_l_mid"]],
            on=["long_expiry", "strike", "scan_date"],
            how="left",
        )
        scan["_spread_value"] = (
            pd.to_numeric(scan["_l_mid"], errors="coerce").fillna(0.0)
            - pd.to_numeric(scan["_s_mid"], errors="coerce").fillna(0.0)
        )
        threshold = scan["net_debit"] * (1 + profit_target_roc)
        triggered = scan[scan["_spread_value"] >= threshold].copy()

        if not triggered.empty:
            triggered = triggered.sort_values("scan_date")
            triggered = triggered.drop_duplicates(subset=["entry_date"], keep="first")
            early_exits = triggered[["entry_date", "scan_date", "_s_mid", "_l_mid"]].rename(columns={
                "scan_date": "exit_date",
                "_s_mid":    "short_exit_mid",
                "_l_mid":    "long_exit_mid",
            })
            early_exits["exit_type"]         = "profit_take"
            early_exits["exit_found"]        = True
            early_exits["short_expired_otm"] = False

    # ── Expiry exit (for positions without early exit) ──────────────────────────
    if early_exits.empty:
        expiry_positions = positions
    else:
        expiry_positions = positions[~positions["entry_date"].isin(early_exits["entry_date"])]

    expiry_result = pd.DataFrame()
    if not expiry_positions.empty:
        short_marks = puts.rename(columns={
            "expiry":     "short_expiry",
            "trade_date": "_short_mark_date",
            "mid":        "_short_mid",
            "last":       "_short_last",
        })
        m_short = expiry_positions[["entry_date", "short_expiry", "strike"]].merge(
            short_marks[["short_expiry", "strike", "_short_mark_date", "_short_mid", "_short_last"]],
            on=["short_expiry", "strike"],
            how="left",
        )
        m_short["_days_before"] = (
            pd.to_datetime(m_short["short_expiry"]) - pd.to_datetime(m_short["_short_mark_date"])
        ).dt.days
        m_short = m_short[(m_short["_days_before"] >= 0) & (m_short["_days_before"] <= 3)]
        m_short = m_short.sort_values(["entry_date", "_days_before"])
        m_short = m_short.drop_duplicates(subset=["entry_date"], keep="first")

        long_marks = puts.rename(columns={
            "expiry":     "long_expiry",
            "trade_date": "_long_mark_date",
            "mid":        "_long_mid",
        })
        m_long = expiry_positions[["entry_date", "short_expiry", "long_expiry", "strike"]].merge(
            long_marks[["long_expiry", "strike", "_long_mark_date", "_long_mid"]],
            on=["long_expiry", "strike"],
            how="left",
        )
        m_long["_days_diff"] = (
            pd.to_datetime(m_long["_long_mark_date"]) - pd.to_datetime(m_long["short_expiry"])
        ).dt.days.abs()
        m_long = m_long[m_long["_days_diff"] <= 3]
        m_long = m_long.sort_values(["entry_date", "_days_diff"])
        m_long = m_long.drop_duplicates(subset=["entry_date"], keep="first")

        expiry_result = expiry_positions.merge(
            m_short[["entry_date", "_short_mid", "_short_last"]], on="entry_date", how="left"
        ).merge(
            m_long[["entry_date", "_long_mid"]], on="entry_date", how="left"
        )
        expiry_result["short_exit_mid"] = np.where(
            pd.notna(expiry_result["_short_last"])
            & (pd.to_numeric(expiry_result["_short_last"], errors="coerce") >= 0),
            expiry_result["_short_last"],
            expiry_result["_short_mid"],
        )
        expiry_result["short_exit_mid"] = (
            pd.to_numeric(expiry_result["short_exit_mid"], errors="coerce").fillna(0.0).clip(lower=0.0)
        )
        expiry_result["long_exit_mid"] = (
            pd.to_numeric(expiry_result["_long_mid"], errors="coerce").fillna(0.0).clip(lower=0.0)
        )
        expiry_result["exit_date"]         = expiry_result["short_expiry"]
        expiry_result["exit_type"]         = "expiry"
        expiry_result["exit_found"]        = expiry_result["_short_mid"].notna() & expiry_result["_long_mid"].notna()
        expiry_result["short_expired_otm"] = expiry_result["short_exit_mid"] <= 0.01
        expiry_result = expiry_result.drop(columns=["_short_mid", "_short_last", "_long_mid"], errors="ignore")

    # ── Combine early exits with expiry exits ───────────────────────────────────
    if early_exits.empty:
        return expiry_result

    result = pd.concat(
        [expiry_result, positions[positions["entry_date"].isin(early_exits["entry_date"])].merge(
            early_exits, on="entry_date", how="left"
        )],
        ignore_index=True,
    ).sort_values("entry_date").reset_index(drop=True)

    return result


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_calendar_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute P&L and risk metrics.

    net_pnl         (short_entry_mid - short_exit_mid) + (long_exit_mid - long_entry_mid)
                    per share; positive = profit
    roc             net_pnl / net_debit   (return on cost basis)
    annualized_roc  roc × 365 / days_held
    is_win          net_pnl > 0
    is_open         exit_found == False (no exit data — excluded from stats)
    """
    df = df.copy()
    df["short_pnl"]      = df["short_entry_mid"] - df["short_exit_mid"]  # per share
    df["long_pnl"]       = df["long_exit_mid"]   - df["long_entry_mid"]  # per share
    df["net_pnl"]        = df["short_pnl"] + df["long_pnl"]
    # Use actual exit_date if available (early profit-take), else fall back to days_held_entry
    if "exit_date" in df.columns and "entry_date" in df.columns:
        actual_days = (
            pd.to_datetime(df["exit_date"]) - pd.to_datetime(df["entry_date"])
        ).dt.days
        df["days_held"] = actual_days.where(actual_days > 0, df["days_held_entry"])
    else:
        df["days_held"] = df["days_held_entry"]
    df["roc"]            = df["net_pnl"] / df["net_debit"].clip(lower=0.001)
    df["annualized_roc"] = df["roc"] * 365 / df["days_held"].clip(lower=1)
    df["is_win"]         = df["net_pnl"] > 0
    df["is_open"]        = ~df["exit_found"].fillna(False)
    return df


# ── Forward volatility ────────────────────────────────────────────────────────

def _leg_iv(mid: float, strike: float, dte_days: int, r: float = 0.04) -> Optional[float]:
    """
    Compute implied vol for one put leg using Black-Scholes.

    Uses S ≈ K (ATM approximation). Valid for near-ATM options (delta 0.40–0.50),
    which is exactly our selection range. This avoids needing historical stock
    prices, which are tricky to align with split-adjusted data for tickers like UVXY.
    Any systematic bias from S≈K cancels in the fwd_vol_factor ratio.
    """
    T = dte_days / 365.0
    if T <= 0 or mid <= 0 or strike <= 0:
        return None
    return _bs_implied_vol(price=mid, S=strike, K=strike, T=T, r=r, q=0.0, opt_type="put")


def enrich_with_forward_vol(positions: pd.DataFrame, r: float = 0.04) -> pd.DataFrame:
    """
    Add true forward volatility metrics to calendar positions.

    All legs are puts at the same strike. Uses S ≈ K (ATM approximation).

    Added columns:
      short_iv        — BS implied vol of the near leg at entry
      long_iv         — BS implied vol of the far leg at entry
      sigma_fwd       — implied vol for the forward window T1→T2
      fwd_vol_factor  — sigma_fwd / short_iv
                        < 1: market expects vol to fall in fwd window → favorable
                        > 1: market expects vol to rise → unfavorable
                        NaN: extreme backwardation (variance formula goes negative)
    """
    if positions.empty:
        for col in ("short_iv", "long_iv", "sigma_fwd", "fwd_vol_factor"):
            positions[col] = np.nan
        return positions

    short_ivs, long_ivs, sigmas_fwd, factors = [], [], [], []

    for _, row in positions.iterrows():
        s_iv = _leg_iv(row["short_entry_mid"], row["strike"], int(row["short_actual_dte"]), r)
        l_iv = _leg_iv(row["long_entry_mid"],  row["strike"], int(row["long_actual_dte"]),  r)

        sigma_fwd = None
        factor    = None

        if s_iv and l_iv and s_iv > 0 and l_iv > 0:
            T1 = row["short_actual_dte"] / 365.0
            T2 = row["long_actual_dte"]  / 365.0
            dT = T2 - T1
            if dT > 0:
                var_fwd = (l_iv**2 * T2 - s_iv**2 * T1) / dT
                if var_fwd > 0:
                    sigma_fwd = var_fwd ** 0.5
                    factor    = sigma_fwd / s_iv
                # var_fwd <= 0: extreme backwardation — forward variance undefined;
                # leave sigma_fwd/factor as None (NaN in the DataFrame)

        short_ivs.append(s_iv)
        long_ivs.append(l_iv)
        sigmas_fwd.append(sigma_fwd)
        factors.append(factor)

    pos = positions.copy()
    pos["short_iv"]       = short_ivs
    pos["long_iv"]        = long_ivs
    pos["sigma_fwd"]      = sigmas_fwd
    pos["fwd_vol_factor"] = factors
    return pos


# ── Sweep orchestrator ─────────────────────────────────────────────────────────

def run_calendar_delta_sweep(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    short_dte_target: int = 20,
    long_dte_target: int = 27,
    dte_tol: int = 5,
    gap_tol: int = 5,
    min_gap: Optional[int] = None,
    max_gap: Optional[int] = None,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    profit_target_roc: Optional[float] = None,
    min_iv_ratio: Optional[float] = None,
    max_fwd_vol_factor: Optional[float] = None,
) -> pd.DataFrame:
    """
    Run the calendar study across all (delta_target, vix_threshold) combinations.

    Returns a combined DataFrame with columns 'delta_target' and 'vix_threshold' added.
    vix_threshold stored as float (NaN = no filter / baseline).
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    all_results = []

    for delta_target in delta_targets:
        print(f"  delta={delta_target:.2f} ...", end=" ", flush=True)
        positions = build_calendar_trades(
            df_opts,
            delta_target=delta_target,
            short_dte_target=short_dte_target,
            long_dte_target=long_dte_target,
            dte_tol=dte_tol,
            gap_tol=gap_tol,
            min_gap=min_gap,
            max_gap=max_gap,
            entry_weekday=entry_weekday,
            split_dates=split_dates,
            max_delta_err=max_delta_err,
            max_spread_pct=max_spread_pct,
        )
        if positions.empty:
            print("no entries found.")
            continue

        positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
        positions = enrich_with_forward_vol(positions)

        if min_iv_ratio is not None:
            positions = positions[positions["iv_ratio"] >= min_iv_ratio]
        if max_fwd_vol_factor is not None:
            positions = positions[
                positions["fwd_vol_factor"].isna() | (positions["fwd_vol_factor"] <= max_fwd_vol_factor)
            ]
        if positions.empty:
            print("no entries after filters.")
            continue
        positions = find_calendar_exits(positions, df_opts, profit_target_roc=profit_target_roc)
        positions = compute_calendar_metrics(positions)

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


# ── Summary printing ────────────────────────────────────────────────────────────

def print_calendar_summary(
    sweep_df: pd.DataFrame,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    short_dte_target: int = 20,
    long_dte_target: int = 27,
    min_gap: Optional[int] = None,
    max_gap: Optional[int] = None,
    ticker: str = "UVXY",
) -> None:
    """
    Print a pivot-style summary table.
      rows    = delta targets
      columns = one block per VIX threshold

    Columns per block: N(E%) Win% ROC% AnnROC% OTM%
      N     = number of closed (non-split) trades
      Win%  = % profitable
      ROC%  = mean return on net_debit per trade
      AnnROC% = annualized ROC
      OTM%  = % where short put expired worthless
    """
    import math

    def _vix_label(v) -> str:
        return "All VIX" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"VIX<{int(v)}"

    def _stats(grp: pd.DataFrame) -> dict:
        closed = grp[~grp["is_open"] & ~grp["split_flag"]]
        if closed.empty:
            return {}
        n     = len(closed)
        wins  = closed["is_win"].sum()
        otm   = closed["short_expired_otm"].sum()
        return {
            "n":       n,
            "win_pct": wins / n * 100,
            "roc":     closed["roc"].mean() * 100,
            "ann_roc": closed["annualized_roc"].mean() * 100,
            "otm_pct": otm / n * 100,
            "avg_debit": closed["net_debit"].mean(),
            "avg_days": closed["days_held"].mean(),
        }

    width = 80
    bar   = "=" * width

    if min_gap is not None:
        _max_gap = max_gap if max_gap is not None else min_gap + 35
        long_label = f"next expiry ({min_gap}–{_max_gap}d gap)"
    else:
        long_label = f"{long_dte_target} DTE"
    print(f"\n{bar}")
    print(
        f"  {ticker} Put Calendar Spread — short {short_dte_target} DTE / "
        f"long {long_label}  (hold to short expiry, Fridays)"
    )
    print(bar)

    thresh_labels = [_vix_label(v) for v in vix_thresholds]

    hdr1 = f"  {'Delta':>6}"
    hdr2 = f"  {'':>6}"
    for lbl in thresh_labels:
        hdr1 += f"  {lbl:^33}"
        hdr2 += f"  {'N':>4} {'Win%':>5} {'ROC%':>6} {'AnnROC%':>8} {'OTM%':>5}"
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
                row += (
                    f"  {st['n']:>4}"
                    f" {st['win_pct']:>4.1f}%"
                    f" {st['roc']:>+5.1f}%"
                    f" {st['ann_roc']:>+7.1f}%"
                    f" {st['otm_pct']:>4.0f}%"
                )
            else:
                row += f"  {'—':^33}"
        print(row)

    print("  " + "-" * (width - 2))
    print(
        f"  N = closed trades (split-spanning excluded)  "
        f"OTM% = short put expired worthless"
    )
    print(f"{bar}\n")


def print_calendar_year_detail(
    sweep_df: pd.DataFrame,
    delta_target: float,
    vix_threshold: Optional[float] = None,
) -> None:
    """Print per-year breakdown for one (delta_target, vix_threshold) combo."""
    import math

    vt_label = (
        "All VIX"
        if (vix_threshold is None or math.isnan(float(vix_threshold or 0)))
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
    print(
        f"  {'Year':>4}  {'N':>3}  {'Win%':>5}  {'ROC%':>6}  "
        f"{'AnnROC%':>8}  {'OTM%':>5}  {'AvgDebit':>8}  {'AvgDays':>7}"
    )
    print("  " + "-" * 68)

    closed["_year"] = pd.to_datetime(closed["entry_date"]).dt.year
    for yr, grp in closed.groupby("_year"):
        n    = len(grp)
        wins = grp["is_win"].sum()
        otm  = grp["short_expired_otm"].sum()
        print(
            f"  {yr:>4}  {n:>3}"
            f"  {wins/n*100:>4.1f}%"
            f"  {grp['roc'].mean()*100:>+5.1f}%"
            f"  {grp['annualized_roc'].mean()*100:>+7.1f}%"
            f"  {otm/n*100:>4.0f}%"
            f"  ${grp['net_debit'].mean():>6.2f}"
            f"  {grp['days_held'].mean():>7.1f}"
        )
    print()


# ── IV term structure filter sweep ─────────────────────────────────────────────

def print_iv_ratio_sweep(
    sweep_df: pd.DataFrame,
    delta_target: float,
    vix_threshold: Optional[float] = None,
    iv_ratio_thresholds: Optional[list] = None,
) -> None:
    """
    Print effect of IV term structure filter on calendar performance.

    iv_ratio = (short_entry_mid / sqrt(short_dte/365)) / (long_entry_mid / sqrt(long_dte/365))
    ratio > 1.0: near-term IV elevated (backwardation) → favorable entry
    ratio < 1.0: far-term IV elevated (contango) → unfavorable

    Rows = iv_ratio thresholds (None = no filter, then ascending cutoffs).
    Columns = N, Win%, Avg ROC%, AnnROC%, OTM%, Avg iv_ratio on entry.
    """
    import math

    if iv_ratio_thresholds is None:
        iv_ratio_thresholds = [None, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20]

    def _vix_label(v) -> str:
        return "All VIX" if (v is None or (isinstance(v, float) and math.isnan(float(v or 0)))) else f"VIX<{int(v)}"

    # Filter to the requested (delta, vix_threshold) slice
    sub = sweep_df[sweep_df["delta_target"] == delta_target].copy()
    if vix_threshold is not None:
        sub = sub[sub["vix_threshold"] == float(vix_threshold)]
    else:
        sub = sub[sub["vix_threshold"].isna()]

    closed_base = sub[~sub["is_open"] & ~sub["split_flag"]]
    if closed_base.empty:
        print("  No data.")
        return

    vix_lbl = _vix_label(vix_threshold)
    print(f"\n  IV Term Structure Filter  ·  delta={delta_target:.2f}  {vix_lbl}")
    print(f"  iv_ratio = (short_mid/√short_dte) ÷ (long_mid/√long_dte)  |  >1.0 = backwardation")
    print(f"  {'iv_ratio ≥':>12}  {'N':>4}  {'Skip%':>6}  {'Win%':>5}  {'ROC%':>6}  {'AnnROC%':>8}  {'OTM%':>5}  {'AvgRatio':>8}")
    print("  " + "-" * 68)

    base_n = len(closed_base)
    for thr in iv_ratio_thresholds:
        if thr is None:
            grp = closed_base
            label = "  (no filter)"
        else:
            grp = closed_base[closed_base["iv_ratio"] >= thr]
            label = f"  ≥ {thr:.2f}      "

        n = len(grp)
        if n == 0:
            print(f"  {label:>12}  {n:>4}  {'—':>6}")
            continue
        skip_pct = (base_n - n) / base_n * 100
        win_pct  = grp["is_win"].mean() * 100
        roc      = grp["roc"].mean() * 100
        ann_roc  = grp["annualized_roc"].mean() * 100
        otm_pct  = grp["short_expired_otm"].mean() * 100
        avg_ratio = grp["iv_ratio"].mean()
        print(
            f"  {label:>12}  {n:>4}  {skip_pct:>5.1f}%  {win_pct:>4.1f}%"
            f"  {roc:>+5.1f}%  {ann_roc:>+7.1f}%  {otm_pct:>4.0f}%  {avg_ratio:>8.3f}"
        )
    print()


# ── Forward vol factor sweep ────────────────────────────────────────────────────

def print_fwd_vol_factor_sweep(
    sweep_df: pd.DataFrame,
    delta_target: float,
    vix_threshold: Optional[float] = None,
    fwd_vol_thresholds: Optional[list] = None,
) -> None:
    """
    Print effect of a max-fwd_vol_factor filter on calendar performance.

    fwd_vol_factor = sigma_fwd / short_iv
      < 1.0: market expects vol to FALL in the forward window → favorable (enter)
      > 1.0: market expects vol to RISE → unfavorable (skip)
      NaN:   extreme backwardation (forward variance undefined); always included

    Rows sweep max_fwd_vol_factor thresholds: only enter when factor ≤ threshold.
    Lower threshold = more selective, only the most favorable term structures.
    """
    import math

    if fwd_vol_thresholds is None:
        fwd_vol_thresholds = [None, 1.30, 1.20, 1.10, 1.00, 0.90, 0.80]

    def _vix_label(v) -> str:
        return "All VIX" if (v is None or (isinstance(v, float) and math.isnan(float(v or 0)))) else f"VIX<{int(v)}"

    sub = sweep_df[sweep_df["delta_target"] == delta_target].copy()
    if vix_threshold is not None:
        sub = sub[sub["vix_threshold"] == float(vix_threshold)]
    else:
        sub = sub[sub["vix_threshold"].isna()]

    closed_base = sub[~sub["is_open"] & ~sub["split_flag"]]
    if closed_base.empty:
        print("  No data.")
        return

    vix_lbl  = _vix_label(vix_threshold)
    base_n   = len(closed_base)
    avg_factor = closed_base["fwd_vol_factor"].mean()
    nan_count  = closed_base["fwd_vol_factor"].isna().sum()

    print(f"\n  Forward Vol Factor Filter  ·  delta={delta_target:.2f}  {vix_lbl}")
    print(f"  fwd_vol_factor = sigma_fwd / short_iv  |  <1.0 = vol expected to fall (favorable)")
    print(f"  Overall avg factor: {avg_factor:.3f}  |  NaN entries (extreme backwardation): {nan_count}")
    print(f"  {'max factor':>12}  {'N':>4}  {'Skip%':>6}  {'Win%':>5}  {'ROC%':>6}  {'AnnROC%':>8}  {'OTM%':>5}  {'AvgFactor':>9}")
    print("  " + "-" * 72)

    for thr in fwd_vol_thresholds:
        if thr is None:
            grp   = closed_base
            label = "  (no filter)"
        else:
            # NaN (extreme backwardation) always included — they're the most favorable
            grp   = closed_base[closed_base["fwd_vol_factor"].isna() | (closed_base["fwd_vol_factor"] <= thr)]
            label = f"  ≤ {thr:.2f}      "

        n = len(grp)
        if n == 0:
            print(f"  {label:>12}  {n:>4}  {'—':>6}")
            continue

        skip_pct   = (base_n - n) / base_n * 100
        win_pct    = grp["is_win"].mean() * 100
        roc        = grp["roc"].mean() * 100
        ann_roc    = grp["annualized_roc"].mean() * 100
        otm_pct    = grp["short_expired_otm"].mean() * 100
        avg_f      = grp["fwd_vol_factor"].mean()  # NaN entries excluded from mean automatically
        print(
            f"  {label:>12}  {n:>4}  {skip_pct:>5.1f}%  {win_pct:>4.1f}%"
            f"  {roc:>+5.1f}%  {ann_roc:>+7.1f}%  {otm_pct:>4.0f}%  {avg_f:>9.3f}"
        )
    print()


# ── Top-level runner ────────────────────────────────────────────────────────────

def run_calendar_study(
    ticker: str,
    start: date,
    end: date,
    delta_targets: list[float],
    vix_thresholds: list[Optional[float]],
    short_dte_target: int = 20,
    long_dte_target: int = 27,
    dte_tol: int = 5,
    gap_tol: int = 5,
    min_gap: Optional[int] = None,
    max_gap: Optional[int] = None,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    output_csv: Optional[str] = None,
    force_sync: bool = False,
    detail_delta: Optional[float] = None,
    detail_vix: Optional[float] = None,
    iv_ratio_thresholds: Optional[list] = None,
    fwd_vol_thresholds: Optional[list] = None,
    profit_target_roc: Optional[float] = None,
    min_iv_ratio: Optional[float] = None,
    max_fwd_vol_factor: Optional[float] = None,
) -> pd.DataFrame:
    """
    Full pipeline: sync options_cache → VIX fetch → load → sweep → print → CSV.
    """
    from lib.mysql_lib import fetch_options_cache
    from lib.studies.straddle_study import sync_options_cache

    # 1. Sync options cache (needs exit marks up to long_expiry — fetch extra buffer)
    sync_options_cache(ticker, start, force=force_sync)

    # 2. Fetch VIX
    vix_start = start - timedelta(days=5)
    print(f"Fetching VIX data ({vix_start} → {end}) ...")
    df_vix = fetch_vix_data(vix_start, end)
    if df_vix.empty:
        print("WARNING: no VIX data — VIX filters will be skipped.")

    # 3. Load options from MySQL
    # Fetch extra days for exit marks; use max_gap when set, else long_dte_target + gap_tol
    _fetch_buffer = (max_gap or (long_dte_target + gap_tol)) + 7
    fetch_end = end + timedelta(days=_fetch_buffer)
    print(f"Loading {ticker} options from MySQL ({start} → {fetch_end}) ...")
    df_opts = fetch_options_cache(ticker, start, fetch_end)
    if df_opts.empty:
        print("No options data found. Aborting.")
        return pd.DataFrame()
    print(f"  {len(df_opts):,} rows loaded.")

    # 4. Run sweep
    if min_gap is not None:
        _max_gap = max_gap if max_gap is not None else min_gap + 35
        long_label = f"next expiry ({min_gap}–{_max_gap}d gap)"
    else:
        long_label = f"{long_dte_target} DTE"
    print(
        f"\nRunning calendar spread sweep: delta_targets={delta_targets}  "
        f"short={short_dte_target} DTE / long={long_label}"
    )
    sweep = run_calendar_delta_sweep(
        df_opts=df_opts,
        df_vix=df_vix,
        delta_targets=delta_targets,
        vix_thresholds=vix_thresholds,
        short_dte_target=short_dte_target,
        long_dte_target=long_dte_target,
        dte_tol=dte_tol,
        gap_tol=gap_tol,
        min_gap=min_gap,
        max_gap=max_gap,
        entry_weekday=entry_weekday,
        split_dates=split_dates,
        max_delta_err=max_delta_err,
        max_spread_pct=max_spread_pct,
        profit_target_roc=profit_target_roc,
        min_iv_ratio=min_iv_ratio,
        max_fwd_vol_factor=max_fwd_vol_factor,
    )

    if not sweep.empty:
        sweep = sweep[sweep["entry_date"] <= end].reset_index(drop=True)

    if sweep.empty:
        print("No trades found.")
        return pd.DataFrame()

    # 5. Print summary
    print_calendar_summary(
        sweep, delta_targets, vix_thresholds,
        short_dte_target=short_dte_target,
        long_dte_target=long_dte_target,
        min_gap=min_gap,
        max_gap=max_gap,
        ticker=ticker,
    )

    # 6. Optional per-year detail + IV ratio sweep
    if detail_delta is not None:
        print_calendar_year_detail(sweep, detail_delta, detail_vix)
        print_iv_ratio_sweep(sweep, detail_delta, detail_vix, iv_ratio_thresholds)
        print_fwd_vol_factor_sweep(sweep, detail_delta, detail_vix, fwd_vol_thresholds)

    # 7. CSV
    if output_csv:
        col_order = [
            "delta_target", "vix_threshold",
            "entry_date", "short_expiry", "long_expiry",
            "short_actual_dte", "long_actual_dte", "strike",
            "short_entry_delta",
            "short_entry_mid", "short_entry_bid",
            "long_entry_mid", "long_entry_bid",
            "net_debit",
            "iv_ratio",
            "short_iv",
            "long_iv",
            "sigma_fwd",
            "fwd_vol_factor",
            "vix_on_entry",
            "exit_date", "short_exit_mid", "long_exit_mid",
            "short_expired_otm", "exit_found",
            "short_pnl", "long_pnl", "net_pnl",
            "days_held", "roc", "annualized_roc",
            "is_win", "is_open", "split_flag",
        ]
        save_cols = [c for c in col_order if c in sweep.columns]
        sweep[save_cols].to_csv(output_csv, index=False)
        print(f"Saved {len(sweep)} rows to {output_csv}")

    return sweep

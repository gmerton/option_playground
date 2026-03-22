"""
Double calendar spread backtest engine.

Structure (net debit)
---------------------
  Sell OTM put  at short_expiry  (~10-15 DTE)     short_put_strike  (delta ≈ -delta_target)
  Buy  OTM put  at long_expiry   (short + ~7 DTE)  same strike
  Sell OTM call at short_expiry                    short_call_strike (delta ≈ +delta_target)
  Buy  OTM call at long_expiry                     same strike

Entry: Friday.
Long leg strike is matched to the short leg strike (same-strike calendar on each side).

P&L per share:
  put_pnl  = (short_put_entry  - short_put_exit)  + (long_put_exit  - long_put_entry)
  call_pnl = (short_call_entry - short_call_exit) + (long_call_exit - long_call_entry)
  net_pnl  = put_pnl + call_pnl
  ROC      = net_pnl / net_debit

Exit: hold to short expiry, then close long legs at mid.
      Optional early profit-take: exit when combined spread value ≥ net_debit × (1 + target).

Data source: data/cache/{ticker}_options.parquet
  Columns: trade_date, expiry, cp, strike, bid, ask, last, mid, delta, dte
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import numpy as np
import pandas as pd


# ── Entry construction ─────────────────────────────────────────────────────────

def build_double_calendar_trades(
    df: pd.DataFrame,
    delta_target: float = 0.20,
    short_dte_target: int = 12,
    short_dte_tol: int = 3,
    gap_days: int = 7,
    gap_tol: int = 2,
    entry_weekday: int = 4,
    max_delta_err: float = 0.08,
    max_spread_pct: Optional[float] = None,
    put_delta_target: Optional[float] = None,
    call_delta_target: Optional[float] = None,
) -> pd.DataFrame:
    """
    Find double calendar entries from an options parquet DataFrame.

    delta_target: unsigned delta for both OTM legs (e.g. 0.25). Used for both
      sides unless put_delta_target / call_delta_target are specified.
    put_delta_target:  if set, overrides delta_target for the put side.
    call_delta_target: if set, overrides delta_target for the call side.
      Put side:  delta ≈ -put_delta_target   (OTM put below spot)
      Call side: delta ≈ +call_delta_target  (OTM call above spot)

    Short legs: Friday, DTE in [short_dte_target - short_dte_tol, + short_dte_tol].
    Long legs:  same Friday, DTE ≈ short_actual_dte + gap_days (±gap_tol), same strike.

    Returns one row per entry date. Rows where any of the 4 legs can't be matched are dropped.
    """
    df = df.copy()
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    # Resolve effective per-side delta targets
    _put_delta  = put_delta_target  if put_delta_target  is not None else delta_target
    _call_delta = call_delta_target if call_delta_target is not None else delta_target

    entry_dates = (
        pd.to_datetime(df["trade_date"]).dt.dayofweek == entry_weekday
    )
    short_dte_lo = short_dte_target - short_dte_tol
    short_dte_hi = short_dte_target + short_dte_tol

    puts  = df[df["cp"] == "P"].copy()
    calls = df[df["cp"] == "C"].copy()

    # ── Step 1: find short put leg ─────────────────────────────────────────────
    sp_mask = (
        entry_dates
        & (df["cp"] == "P")
        & (df["dte"] >= short_dte_lo) & (df["dte"] <= short_dte_hi)
        & (df["bid"] > 0) & (df["ask"] > 0) & (df["delta"].notna())
    )
    sp_pool = df[sp_mask].copy()
    if max_spread_pct is not None:
        sp_pool = sp_pool[
            (sp_pool["ask"] - sp_pool["bid"]) / sp_pool["mid"].clip(lower=0.001)
            <= max_spread_pct
        ]
    sp_pool["_derr"] = (sp_pool["delta"] - (-_put_delta)).abs()
    sp_pool = sp_pool[sp_pool["_derr"] <= max_delta_err]
    sp_pool["_dte_err"] = (sp_pool["dte"] - short_dte_target).abs()
    sp_pool = sp_pool.sort_values(["trade_date", "_dte_err", "_derr"])
    sp_pool = sp_pool.drop_duplicates(subset=["trade_date"], keep="first")
    sp_pool = sp_pool.rename(columns={
        "trade_date": "entry_date", "expiry": "short_expiry",
        "dte": "short_actual_dte", "strike": "sp_strike",
        "mid": "sp_mid", "bid": "sp_bid", "ask": "sp_ask", "delta": "sp_delta",
    })[["entry_date", "short_expiry", "short_actual_dte",
        "sp_strike", "sp_mid", "sp_bid", "sp_ask", "sp_delta"]]

    # ── Step 2: find short call leg (same expiry as short put) ─────────────────
    sc_mask = (
        entry_dates
        & (df["cp"] == "C")
        & (df["dte"] >= short_dte_lo) & (df["dte"] <= short_dte_hi)
        & (df["bid"] > 0) & (df["ask"] > 0) & (df["delta"].notna())
    )
    sc_pool = df[sc_mask].copy()
    if max_spread_pct is not None:
        sc_pool = sc_pool[
            (sc_pool["ask"] - sc_pool["bid"]) / sc_pool["mid"].clip(lower=0.001)
            <= max_spread_pct
        ]
    sc_pool["_derr"] = (sc_pool["delta"] - _call_delta).abs()
    sc_pool = sc_pool[sc_pool["_derr"] <= max_delta_err]
    # Must match the same short_expiry as the put
    sc_pool = sc_pool.rename(columns={"trade_date": "entry_date", "expiry": "_sc_expiry"})
    sc_pool = sc_pool.merge(
        sp_pool[["entry_date", "short_expiry"]],
        on="entry_date", how="inner",
    )
    sc_pool = sc_pool[sc_pool["_sc_expiry"] == sc_pool["short_expiry"]].copy()
    sc_pool = sc_pool.sort_values(["entry_date", "_derr"])
    sc_pool = sc_pool.drop_duplicates(subset=["entry_date"], keep="first")
    sc_pool = sc_pool.rename(columns={
        "strike": "sc_strike", "mid": "sc_mid",
        "bid": "sc_bid", "ask": "sc_ask", "delta": "sc_delta",
    })[["entry_date", "sc_strike", "sc_mid", "sc_bid", "sc_ask", "sc_delta"]]

    # ── Step 3: long put leg (same strike as short put, long_expiry) ───────────
    # long_dte in [short_actual_dte + gap_days - gap_tol, + gap_tol]
    lp_entry = pd.to_datetime(puts["trade_date"]).dt.dayofweek == entry_weekday
    lp_pool = puts[
        lp_entry & (puts["bid"] > 0) & (puts["ask"] > 0)
    ].rename(columns={"trade_date": "entry_date", "expiry": "long_expiry",
                      "dte": "long_actual_dte", "strike": "_lp_strike",
                      "mid": "lp_mid", "bid": "lp_bid", "ask": "lp_ask", "delta": "lp_delta"})
    # Join to short put to get the target strike and short_actual_dte
    lp_pool = lp_pool.merge(
        sp_pool[["entry_date", "short_expiry", "short_actual_dte", "sp_strike"]],
        on="entry_date", how="inner",
    )
    lp_pool = lp_pool[
        (lp_pool["long_expiry"] > lp_pool["short_expiry"])
        & (lp_pool["_lp_strike"] == lp_pool["sp_strike"])
    ].copy()
    lp_pool["_gap"] = lp_pool["long_actual_dte"] - lp_pool["short_actual_dte"]
    lp_pool = lp_pool[
        (lp_pool["_gap"] >= gap_days - gap_tol)
        & (lp_pool["_gap"] <= gap_days + gap_tol)
    ]
    lp_pool = lp_pool.sort_values(["entry_date", "_gap"])
    lp_pool = lp_pool.drop_duplicates(subset=["entry_date"], keep="first")
    lp_pool = lp_pool.rename(columns={"_lp_strike": "lp_strike"})[
        ["entry_date", "long_expiry", "long_actual_dte",
         "lp_strike", "lp_mid", "lp_bid", "lp_ask", "lp_delta"]
    ]

    # ── Step 4: long call leg (same strike as short call, long_expiry) ─────────
    lc_entry = pd.to_datetime(calls["trade_date"]).dt.dayofweek == entry_weekday
    lc_pool = calls[
        lc_entry & (calls["bid"] > 0) & (calls["ask"] > 0)
    ].rename(columns={"trade_date": "entry_date", "expiry": "_lc_expiry",
                      "dte": "_lc_dte", "strike": "_lc_strike",
                      "mid": "lc_mid", "bid": "lc_bid", "ask": "lc_ask", "delta": "lc_delta"})
    # Join sc and lp to get call strike and long_expiry
    lc_pool = lc_pool.merge(
        sc_pool[["entry_date", "sc_strike"]],
        on="entry_date", how="inner",
    ).merge(
        lp_pool[["entry_date", "long_expiry"]],
        on="entry_date", how="inner",
    )
    lc_pool = lc_pool[
        (lc_pool["_lc_expiry"] == lc_pool["long_expiry"])
        & (lc_pool["_lc_strike"] == lc_pool["sc_strike"])
    ].copy()
    lc_pool = lc_pool.sort_values("entry_date")
    lc_pool = lc_pool.drop_duplicates(subset=["entry_date"], keep="first")
    lc_pool = lc_pool.rename(columns={"_lc_strike": "lc_strike"})[
        ["entry_date", "lc_strike", "lc_mid", "lc_bid", "lc_ask", "lc_delta"]
    ]

    # ── Combine all 4 legs ──────────────────────────────────────────────────────
    result = (
        sp_pool
        .merge(sc_pool, on="entry_date", how="inner")
        .merge(lp_pool, on="entry_date", how="inner")
        .merge(lc_pool, on="entry_date", how="inner")
    )

    result["put_debit"]  = result["lp_mid"] - result["sp_mid"]
    result["call_debit"] = result["lc_mid"] - result["sc_mid"]
    result["net_debit"]  = result["put_debit"] + result["call_debit"]

    result = result[
        (result["put_debit"]  > 0)
        & (result["call_debit"] > 0)
        & (result["net_debit"]  > 0)
    ].copy()

    result["days_held_entry"] = (
        pd.to_datetime(result["short_expiry"]) - pd.to_datetime(result["entry_date"])
    ).dt.days

    # IV ratio proxy (put side, near / far): backwardation > 1 = favorable
    result["iv_ratio"] = (
        (result["sp_mid"] / np.sqrt(result["short_actual_dte"] / 365))
        / (result["lp_mid"] / np.sqrt(result["long_actual_dte"] / 365))
    )
    # Store effective deltas used
    result["put_delta_used"]  = _put_delta
    result["call_delta_used"] = _call_delta

    return result.sort_values("entry_date").reset_index(drop=True)


# ── Exit scanner ───────────────────────────────────────────────────────────────

def find_double_calendar_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_target_roc: Optional[float] = None,
) -> pd.DataFrame:
    """
    Find exit prices for each double calendar position.

    profit_target_roc: if set, scan daily; exit when combined spread value ≥ net_debit × (1 + target).
    Hold-to-expiry:    short legs settle at last/mid on short_expiry; long legs closed at mid.
    """
    if positions.empty:
        return positions

    df = df_opts.copy()
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    puts  = df[df["cp"] == "P"][["trade_date", "expiry", "strike", "mid", "last"]].copy()
    calls = df[df["cp"] == "C"][["trade_date", "expiry", "strike", "mid", "last"]].copy()

    early_exits = pd.DataFrame()

    # ── Daily profit-take scan ──────────────────────────────────────────────────
    if profit_target_roc is not None:
        # Build daily marks for all 4 legs, keyed by (expiry, strike, scan_date)
        sp_daily = puts.rename(columns={"trade_date": "scan_date", "expiry": "short_expiry",
                                        "strike": "sp_strike", "mid": "_sp_mid"})[
            ["scan_date", "short_expiry", "sp_strike", "_sp_mid"]]
        lp_daily = puts.rename(columns={"trade_date": "scan_date", "expiry": "long_expiry",
                                        "strike": "lp_strike", "mid": "_lp_mid"})[
            ["scan_date", "long_expiry", "lp_strike", "_lp_mid"]]
        sc_daily = calls.rename(columns={"trade_date": "scan_date", "expiry": "short_expiry",
                                         "strike": "sc_strike", "mid": "_sc_mid"})[
            ["scan_date", "short_expiry", "sc_strike", "_sc_mid"]]
        lc_daily = calls.rename(columns={"trade_date": "scan_date", "expiry": "long_expiry",
                                         "strike": "lc_strike", "mid": "_lc_mid"})[
            ["scan_date", "long_expiry", "lc_strike", "_lc_mid"]]

        pos_cols = ["entry_date", "short_expiry", "long_expiry",
                    "sp_strike", "lp_strike", "sc_strike", "lc_strike", "net_debit"]
        scan = positions[pos_cols].merge(sp_daily, on=["short_expiry", "sp_strike"], how="left")
        scan = scan.merge(lp_daily, on=["long_expiry", "lp_strike", "scan_date"], how="left")
        scan = scan.merge(sc_daily, on=["short_expiry", "sc_strike", "scan_date"], how="left")
        scan = scan.merge(lc_daily, on=["long_expiry", "lc_strike", "scan_date"], how="left")

        scan = scan[
            (pd.to_datetime(scan["scan_date"]) > pd.to_datetime(scan["entry_date"]))
            & (pd.to_datetime(scan["scan_date"]) <= pd.to_datetime(scan["short_expiry"]))
        ]
        for c in ["_sp_mid", "_lp_mid", "_sc_mid", "_lc_mid"]:
            scan[c] = pd.to_numeric(scan[c], errors="coerce").fillna(0.0)
        scan["_val"] = scan["_lp_mid"] - scan["_sp_mid"] + scan["_lc_mid"] - scan["_sc_mid"]

        triggered = scan[scan["_val"] >= scan["net_debit"] * (1 + profit_target_roc)].copy()
        if not triggered.empty:
            triggered = triggered.sort_values("scan_date").drop_duplicates("entry_date", keep="first")
            early_exits = triggered.rename(columns={
                "scan_date": "exit_date",
                "_sp_mid": "sp_exit_mid", "_lp_mid": "lp_exit_mid",
                "_sc_mid": "sc_exit_mid", "_lc_mid": "lc_exit_mid",
            })[["entry_date", "exit_date",
                "sp_exit_mid", "lp_exit_mid", "sc_exit_mid", "lc_exit_mid"]].copy()
            early_exits["exit_type"]  = "profit_take"
            early_exits["exit_found"] = True

    # ── Expiry exit ─────────────────────────────────────────────────────────────
    expiry_positions = (
        positions[~positions["entry_date"].isin(early_exits["entry_date"])]
        if not early_exits.empty else positions
    )

    expiry_result = pd.DataFrame()
    if not expiry_positions.empty:
        ep = expiry_positions.copy()

        def mark_at_expiry(opt_df, expiry_col, strike_col, mid_out, last_out=None):
            """Get the last available mark on or just before short_expiry."""
            marks = opt_df.rename(columns={
                "trade_date": "_mdate",
                "expiry":     expiry_col,
                "strike":     strike_col,
                "mid":        "_mid",
                "last":       "_last",
            })
            # Build position subset — avoid duplicating expiry_col if it equals short_expiry
            pos_cols = ["entry_date", "short_expiry", strike_col]
            if expiry_col != "short_expiry":
                pos_cols.insert(2, expiry_col)
            m = ep[pos_cols].merge(
                marks[[expiry_col, strike_col, "_mdate", "_mid", "_last"]],
                on=[expiry_col, strike_col], how="left",
            )
            m["_dd"] = (
                pd.to_datetime(m["_mdate"]) - pd.to_datetime(m["short_expiry"])
            ).dt.days.abs()
            m = m[m["_dd"] <= 3].sort_values(["entry_date", "_dd"])
            m = m.drop_duplicates("entry_date", keep="first")
            m = m.rename(columns={"_mid": mid_out})
            if last_out:
                m = m.rename(columns={"_last": last_out})
                return m[["entry_date", mid_out, last_out]]
            return m[["entry_date", mid_out]]

        sp_m  = mark_at_expiry(puts,  "short_expiry", "sp_strike", "sp_exit_mid",  "sp_exit_last")
        sc_m  = mark_at_expiry(calls, "short_expiry", "sc_strike", "sc_exit_mid",  "sc_exit_last")
        lp_m  = mark_at_expiry(puts,  "long_expiry",  "lp_strike", "lp_exit_mid")
        lc_m  = mark_at_expiry(calls, "long_expiry",  "lc_strike", "lc_exit_mid")

        expiry_result = ep.copy()
        for m_df in [sp_m, sc_m, lp_m, lc_m]:
            expiry_result = expiry_result.merge(m_df, on="entry_date", how="left")

        # Short legs: prefer last (settlement), fallback to mid, clip ≥ 0
        for mid_col, last_col in [("sp_exit_mid", "sp_exit_last"), ("sc_exit_mid", "sc_exit_last")]:
            last_val = pd.to_numeric(expiry_result[last_col], errors="coerce")
            mid_val  = pd.to_numeric(expiry_result[mid_col],  errors="coerce")
            expiry_result[mid_col] = np.where(
                last_val.notna() & (last_val >= 0), last_val, mid_val
            )
            expiry_result[mid_col] = expiry_result[mid_col].fillna(0.0).clip(lower=0.0)

        for mid_col in ["lp_exit_mid", "lc_exit_mid"]:
            expiry_result[mid_col] = pd.to_numeric(
                expiry_result[mid_col], errors="coerce"
            ).fillna(0.0).clip(lower=0.0)

        expiry_result["exit_date"]  = expiry_result["short_expiry"]
        expiry_result["exit_type"]  = "expiry"
        expiry_result["exit_found"] = (
            expiry_result["sp_exit_mid"].notna()
            & expiry_result["lp_exit_mid"].notna()
            & expiry_result["sc_exit_mid"].notna()
            & expiry_result["lc_exit_mid"].notna()
        )

    # ── Combine ─────────────────────────────────────────────────────────────────
    if early_exits.empty:
        return expiry_result

    early_merged = positions[
        positions["entry_date"].isin(early_exits["entry_date"])
    ].merge(early_exits, on="entry_date", how="left")

    return pd.concat(
        [expiry_result, early_merged], ignore_index=True
    ).sort_values("entry_date").reset_index(drop=True)


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_double_calendar_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute P&L and ROC for each double calendar trade."""
    df = df.copy()
    df["put_pnl"]  = (df["sp_mid"] - df["sp_exit_mid"]) + (df["lp_exit_mid"] - df["lp_mid"])
    df["call_pnl"] = (df["sc_mid"] - df["sc_exit_mid"]) + (df["lc_exit_mid"] - df["lc_mid"])
    df["net_pnl"]  = df["put_pnl"] + df["call_pnl"]

    actual_days = (
        pd.to_datetime(df["exit_date"]) - pd.to_datetime(df["entry_date"])
    ).dt.days
    df["days_held"]      = actual_days.where(actual_days > 0, df["days_held_entry"])
    df["roc"]            = df["net_pnl"] / df["net_debit"].clip(lower=0.001)
    df["annualized_roc"] = df["roc"] * 365 / df["days_held"].clip(lower=1)
    df["is_win"]         = df["net_pnl"] > 0
    df["is_open"]        = ~df["exit_found"].fillna(False)
    return df

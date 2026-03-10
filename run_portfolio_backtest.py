#!/usr/bin/env python3
"""
Portfolio backtest — simulate all confirmed strategies for a given year.

Rules
-----
  - Sharpe-weighted capital allocation (from strategy_registry)
  - Max 2 concurrent open positions per strategy (skip entry if already at limit)
  - All confirmed parameters: delta targets, DTE, VIX filters, profit-take rules
  - VIX and iv_ratio filters applied as in the playbooks
  - UVXY combined: call spread + short put share total UVXY allocation 50/50
  - Naked UVXY short put sized using short_strike × 100 as max-loss proxy

Output
------
  - Per-trade ledger (CSV optional)
  - Strategy summary: N, win%, avg pnl$, total pnl$, ROC% on allocation
  - Monthly P&L table
  - Full-year portfolio summary

Usage
-----
    AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx \\
    PYTHONPATH=src python run_portfolio_backtest.py --year 2025 --capital 100000 --risk-pct 0.20

    # Save detailed trade ledger:
    PYTHONPATH=src python run_portfolio_backtest.py --year 2025 --capital 100000 --ledger-csv backtest_2025.csv
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.strategy_registry import STRATEGY_MAP
from lib.studies.put_spread_study import (
    build_put_spread_trades, find_put_spread_exits,
    compute_spread_metrics as _compute_put_metrics,
)
from lib.studies.call_spread_study import (
    build_call_spread_trades, find_spread_exits,
    compute_spread_metrics as _compute_call_metrics,
)
from lib.studies.calendar_study import (
    build_calendar_trades, find_calendar_exits, compute_calendar_metrics,
    enrich_with_forward_vol,
)
from lib.studies.put_study import fetch_vix_data
from lib.mysql_lib import fetch_options_cache
from lib.studies.straddle_study import sync_options_cache, UVXY_SPLIT_DATES

MAX_SPREAD_PCT = 0.25
MAX_DELTA_ERR  = 0.08
MAX_CONCURRENT = 2


# ── Strategy configuration ─────────────────────────────────────────────────────
#
# type:           put_spread | call_spread | calendar | naked_put
# vix_min/max:    VIX filter (None = no bound).  vix_min=20 → enter when VIX ≥ 20
# alloc_key:      key into strategy_registry STRATEGY_MAP for Sharpe lookup
# alloc_frac:     fraction of that alloc_key's total dollars allocated to THIS sub-strategy
# avg_concurrent: typical open positions simultaneously (used to size each entry)
# split_dates:    reverse-split dates for this ticker

STRATEGY_CONFIGS = [
    {
        "name":           "UVXY Bear Call Spread",
        "type":           "call_spread",
        "ticker":         "UVXY",
        "short_delta":    0.50, "wing": 0.10,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "UVXY combined", "alloc_frac": 0.50, "avg_concurrent": 2,
        "split_dates":    UVXY_SPLIT_DATES,
    },
    {
        "name":           "UVXY Short Put",
        "type":           "naked_put",
        "ticker":         "UVXY",
        "short_delta":    0.40,
        "dte_target":     20,
        "vix_min":        None, "vix_max": 20,
        "profit_take":    0.50,
        "alloc_key":      "UVXY combined", "alloc_frac": 0.50, "avg_concurrent": 1,
        "split_dates":    UVXY_SPLIT_DATES,
    },
    {
        "name":           "TLT Bear Call Spread",
        "type":           "call_spread",
        "ticker":         "TLT",
        "short_delta":    0.35, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        20, "vix_max": None,
        "profit_take":    0.70,
        "alloc_key":      "TLT calls", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "GLD Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "GLD",
        "short_delta":    0.30, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        None, "vix_max": 25,
        "profit_take":    0.50,
        "alloc_key":      "GLD puts", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "GLD Put Calendar",
        "type":           "calendar",
        "ticker":         "GLD",
        "delta_target":   0.50,
        "dte_target":     20,
        "min_gap":        25, "max_gap": 50,
        "min_iv_ratio":   1.0,
        "max_fwd_vol":    None,            # no fwd_vol filter for GLD
        "profit_take":    0.25,
        "vix_min":        None, "vix_max": None,
        "alloc_key":      "GLD calendar", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "XLU Put Calendar",
        "type":           "calendar",
        "ticker":         "XLU",
        "delta_target":   0.50,
        "dte_target":     20,
        "min_gap":        25, "max_gap": 50,
        "min_iv_ratio":   1.0,
        "max_fwd_vol":    0.90,            # fwd_vol_factor ≤ 0.90 per playbook
        "profit_take":    0.25,
        "vix_min":        None, "vix_max": None,
        "alloc_key":      "XLU calendar", "alloc_frac": 1.0, "avg_concurrent": 1,
        "split_dates":    [],
    },
    {
        "name":           "XLV Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "XLV",
        "short_delta":    0.25, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "XLV puts", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "USO Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "USO",
        "short_delta":    0.25, "wing": 0.05,
        "dte_target":     30,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "USO puts", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "XLF Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "XLF",
        "short_delta":    0.35, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "XLF puts", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "INDA Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "INDA",
        "short_delta":    0.25, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "INDA puts", "alloc_frac": 1.0, "avg_concurrent": 1,
        "split_dates":    [],
    },
    {
        "name":           "ASHR Bull Put Spread",
        "type":           "put_spread",
        "ticker":         "ASHR",
        "short_delta":    0.25, "wing": 0.05,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "ASHR puts", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
    {
        "name":           "ASHR Bear Call Spread",
        "type":           "call_spread",
        "ticker":         "ASHR",
        "short_delta":    0.20, "wing": 0.10,
        "dte_target":     20,
        "vix_min":        None, "vix_max": None,
        "profit_take":    0.50,
        "alloc_key":      "ASHR calls", "alloc_frac": 1.0, "avg_concurrent": 2,
        "split_dates":    [],
    },
]


# ── Naked short put helpers ────────────────────────────────────────────────────

def _build_naked_put_trades(
    df_opts: pd.DataFrame,
    short_delta_target: float = 0.40,
    dte_target: int = 20,
    dte_tol: int = 5,
    split_dates: Optional[list] = None,
) -> pd.DataFrame:
    """Find naked short put entries. One row per Friday, best delta match."""
    split_dates = split_dates or []
    df = df_opts.copy()
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    td_dt = pd.to_datetime(df["trade_date"])
    mask = (
        (td_dt.dt.dayofweek == 4)
        & (df["dte"] >= dte_target - dte_tol)
        & (df["dte"] <= dte_target + dte_tol)
        & (df["bid"] > 0) & (df["ask"] > 0)
        & (df["cp"] == "P") & (df["delta"].notna())
    )
    puts = df[mask].copy()

    # Bid-ask filter
    puts["_sp"] = (puts["ask"] - puts["bid"]) / puts["mid"]
    puts = puts[puts["_sp"] <= MAX_SPREAD_PCT]

    # Delta filter (puts have negative delta; compare against -target)
    puts["_delta_err"] = (puts["delta"] - (-short_delta_target)).abs()
    puts = puts[puts["_delta_err"] <= MAX_DELTA_ERR]
    if puts.empty:
        return pd.DataFrame()

    puts = puts.sort_values(["trade_date", "expiry", "_delta_err"])
    puts = puts.drop_duplicates(subset=["trade_date", "expiry"], keep="first")
    puts["_dte_err"] = (puts["dte"] - dte_target).abs()
    puts = puts.sort_values(["trade_date", "_dte_err"])
    puts = puts.drop_duplicates(subset=["trade_date"], keep="first")

    result = puts.rename(columns={
        "trade_date": "entry_date", "dte": "actual_dte",
        "mid": "short_mid", "bid": "short_bid", "ask": "short_ask",
        "delta": "short_delta", "strike": "short_strike",
    })[["entry_date", "expiry", "actual_dte",
        "short_strike", "short_mid", "short_bid", "short_ask", "short_delta"]]

    def _spans(entry_d: date, exp_d: date) -> bool:
        return any(entry_d < sd <= exp_d for sd in split_dates)

    result["split_flag"] = [_spans(r.entry_date, r.expiry) for r in result.itertuples(index=False)]
    return result.sort_values("entry_date").reset_index(drop=True)


def _find_naked_put_exits(
    positions: pd.DataFrame,
    df_opts: pd.DataFrame,
    profit_take_pct: float = 0.50,
) -> pd.DataFrame:
    """Find exit for each naked short put: profit take or expiry."""
    if positions.empty:
        return positions

    put_marks = (
        df_opts[df_opts["cp"] == "P"]
        [["trade_date", "expiry", "strike", "mid", "last"]]
        .rename(columns={"trade_date": "mark_date", "mid": "mark_mid", "last": "mark_last"})
        .copy()
    )
    for col in ("mark_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(put_marks[col]):
            put_marks[col] = put_marks[col].dt.date

    keys = (positions[["expiry", "short_strike"]]
            .rename(columns={"short_strike": "strike"}).drop_duplicates())
    relevant = (put_marks.merge(keys, on=["expiry", "strike"], how="inner")
                .rename(columns={"strike": "short_strike",
                                  "mark_mid": "short_mark_mid",
                                  "mark_last": "short_mark_last"}))

    merged = positions.merge(
        relevant[["mark_date", "expiry", "short_strike", "short_mark_mid", "short_mark_last"]],
        on=["expiry", "short_strike"], how="left",
    )
    for col in ("entry_date", "expiry", "mark_date"):
        merged[col] = pd.to_datetime(merged[col]).dt.date

    merged = merged[
        (merged["mark_date"] > merged["entry_date"])
        & (merged["mark_date"] <= merged["expiry"])
    ].dropna(subset=["short_mark_mid"])

    profit_target = merged["short_mid"] * (1.0 - profit_take_pct)
    merged["_early"]    = merged["short_mark_mid"] <= profit_target
    merged["_is_expiry"] = merged["mark_date"] == merged["expiry"]
    merged["_is_exit"]   = merged["_early"] | merged["_is_expiry"]

    exits = (
        merged[merged["_is_exit"]]
        .sort_values(["entry_date", "expiry", "short_strike", "mark_date"])
        .drop_duplicates(subset=["entry_date", "expiry", "short_strike"], keep="first")
        .copy()
    )

    at_expiry_only = exits["_is_expiry"] & ~exits["_early"]
    short_last = exits["short_mark_last"].where(
        pd.notna(exits["short_mark_last"]) & (exits["short_mark_last"] >= 0),
        other=exits["short_mark_mid"],
    ).fillna(0.0).clip(lower=0.0)
    short_early = exits["short_mark_mid"].fillna(0.0).clip(lower=0.0)

    exits["exit_net_value"] = np.where(at_expiry_only, short_last, short_early)
    exits["days_held"] = (
        pd.to_datetime(exits["mark_date"]) - pd.to_datetime(exits["entry_date"])
    ).dt.days
    exits["exit_type"] = exits.apply(
        lambda r: "early" if r["_early"] else "expiry", axis=1
    )
    exits = exits.rename(columns={"mark_date": "exit_date"})

    result = positions.merge(
        exits[["entry_date", "expiry", "short_strike",
               "exit_date", "exit_net_value", "days_held", "exit_type"]],
        on=["entry_date", "expiry", "short_strike"], how="left",
    )
    result["missing_exit_data"] = result["exit_date"].isna()
    result["exit_net_value"] = result["exit_net_value"].fillna(result["short_strike"])
    result["days_held"]      = result["days_held"].fillna(result["actual_dte"]).astype(int)
    result["exit_type"]      = result["exit_type"].fillna("missing")
    result["net_pnl"]        = (result["short_mid"] - result["exit_net_value"]) * 100
    result["max_loss"]       = result["short_strike"] * 100   # sizing proxy (underlying → 0)
    result["roc"]            = result["net_pnl"] / result["max_loss"].clip(lower=0.01)
    result["is_win"]         = result["net_pnl"] > 0
    result["is_open"]        = result["missing_exit_data"]
    return result


# ── VIX filter ────────────────────────────────────────────────────────────────

def _apply_vix_filter(
    trades: pd.DataFrame,
    vix_lookup: pd.Series,
    vix_min: Optional[float],
    vix_max: Optional[float],
) -> pd.DataFrame:
    if "vix_on_entry" not in trades.columns:
        trades = trades.copy()
        trades["vix_on_entry"] = trades["entry_date"].map(vix_lookup)
    if vix_min is not None:
        trades = trades[trades["vix_on_entry"].isna() | (trades["vix_on_entry"] >= vix_min)]
    if vix_max is not None:
        trades = trades[trades["vix_on_entry"].isna() | (trades["vix_on_entry"] < vix_max)]
    return trades


# ── Concurrent position limit ─────────────────────────────────────────────────

def _apply_concurrent_limit(trades: pd.DataFrame, max_concurrent: int = 2) -> pd.DataFrame:
    """
    Enforce max_concurrent open positions per strategy, processing entries in date order.

    A position opened on date D with exit_date E is counted as open on any date F where
    D < F and exit_date > F (strictly: it closes on exit_date so it's gone by then).
    """
    if trades.empty:
        return trades

    # Ensure exit_date is available
    if "exit_date" not in trades.columns:
        return trades

    accepted: list[dict] = []
    for row in trades.sort_values("entry_date").itertuples(index=False):
        friday = row.entry_date
        open_count = sum(
            1 for t in accepted
            if t["entry_date"] < friday and t["exit_date"] > friday
        )
        if open_count < max_concurrent:
            accepted.append({
                "entry_date": friday,
                "exit_date":  row.exit_date,
            })

    if not accepted:
        return trades.iloc[:0]

    accepted_dates = {t["entry_date"] for t in accepted}
    return trades[trades["entry_date"].isin(accepted_dates)].copy()


# ── Allocation sizing ──────────────────────────────────────────────────────────

def _compute_allocation(
    total_capital: float,
    risk_pct: float,
) -> dict[str, float]:
    """
    Compute Sharpe-weighted dollar allocation per alloc_key.
    Returns {alloc_key: dollars_allocated}.
    """
    # Collect unique alloc_keys from configs
    keys = list(dict.fromkeys(c["alloc_key"] for c in STRATEGY_CONFIGS))
    sharpes = {k: max(STRATEGY_MAP[k].sharpe_annual, 0.01) if k in STRATEGY_MAP else 0.01
               for k in keys}
    total_sharpe = sum(sharpes.values())
    total_risk = total_capital * risk_pct
    return {k: total_risk * sh / total_sharpe for k, sh in sharpes.items()}


# ── Build trades for one strategy ──────────────────────────────────────────────

def _build_strategy_trades(
    cfg: dict,
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Build, filter (VIX + iv_ratio + fwd_vol), and find exits for one strategy."""
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    stype = cfg["type"]
    split_dates = cfg.get("split_dates", [])
    dte = cfg["dte_target"]
    profit_take = cfg["profit_take"]

    if stype == "put_spread":
        trades = build_put_spread_trades(
            df_opts, short_delta_target=cfg["short_delta"],
            wing_delta_width=cfg["wing"], dte_target=dte,
            split_dates=split_dates, max_spread_pct=MAX_SPREAD_PCT,
        )
        if trades.empty:
            return pd.DataFrame()
        trades["vix_on_entry"] = trades["entry_date"].map(vix_lookup)
        trades = _apply_vix_filter(trades, vix_lookup, cfg["vix_min"], cfg["vix_max"])
        # Restrict to year range (entry only)
        trades = trades[(trades["entry_date"] >= start) & (trades["entry_date"] <= end)]
        if trades.empty:
            return pd.DataFrame()
        trades = find_put_spread_exits(trades, df_opts, profit_take_pct=profit_take)
        trades = _compute_put_metrics(trades)
        trades["max_loss"] = trades["max_loss"]   # already (spread_width - credit) × 100

    elif stype == "call_spread":
        trades = build_call_spread_trades(
            df_opts, short_delta_target=cfg["short_delta"],
            wing_delta_width=cfg["wing"], dte_target=dte,
            split_dates=split_dates, max_spread_pct=MAX_SPREAD_PCT,
        )
        if trades.empty:
            return pd.DataFrame()
        trades["vix_on_entry"] = trades["entry_date"].map(vix_lookup)
        trades = _apply_vix_filter(trades, vix_lookup, cfg["vix_min"], cfg["vix_max"])
        trades = trades[(trades["entry_date"] >= start) & (trades["entry_date"] <= end)]
        if trades.empty:
            return pd.DataFrame()
        trades = find_spread_exits(trades, df_opts, profit_take_pct=profit_take)
        trades = _compute_call_metrics(trades)
        trades["max_loss"] = trades["max_loss"]

    elif stype == "naked_put":
        trades = _build_naked_put_trades(
            df_opts, short_delta_target=cfg["short_delta"],
            dte_target=dte, split_dates=split_dates,
        )
        if trades.empty:
            return pd.DataFrame()
        trades["vix_on_entry"] = trades["entry_date"].map(vix_lookup)
        trades = _apply_vix_filter(trades, vix_lookup, cfg["vix_min"], cfg["vix_max"])
        trades = trades[(trades["entry_date"] >= start) & (trades["entry_date"] <= end)]
        if trades.empty:
            return pd.DataFrame()
        trades = _find_naked_put_exits(trades, df_opts, profit_take_pct=profit_take)

    elif stype == "calendar":
        trades = build_calendar_trades(
            df_opts, delta_target=cfg["delta_target"],
            short_dte_target=dte, dte_tol=5,
            min_gap=cfg["min_gap"], max_gap=cfg["max_gap"],
            split_dates=split_dates, max_spread_pct=MAX_SPREAD_PCT,
        )
        if trades.empty:
            return pd.DataFrame()
        trades["vix_on_entry"] = trades["entry_date"].map(vix_lookup)
        trades = _apply_vix_filter(trades, vix_lookup, cfg["vix_min"], cfg["vix_max"])
        # iv_ratio filter
        if cfg.get("min_iv_ratio") is not None:
            trades = trades[trades["iv_ratio"] >= cfg["min_iv_ratio"]]
        # fwd_vol filter (XLU: ≤ 0.90)
        max_fwd = cfg.get("max_fwd_vol")
        if max_fwd is not None:
            trades = enrich_with_forward_vol(trades)
            trades = trades[trades["fwd_vol_factor"].isna() | (trades["fwd_vol_factor"] <= max_fwd)]
        trades = trades[(trades["entry_date"] >= start) & (trades["entry_date"] <= end)]
        if trades.empty:
            return pd.DataFrame()
        trades = find_calendar_exits(trades, df_opts, profit_target_roc=profit_take)
        trades = compute_calendar_metrics(trades)
        # Standardize: max_loss = net_debit × 100; exit_date and net_pnl already computed
        trades["max_loss"] = trades["net_debit"] * 100
        if "exit_date" not in trades.columns:
            trades["exit_date"] = trades["short_expiry"]

    else:
        raise ValueError(f"Unknown type: {stype}")

    # Standardize exit_date type
    if "exit_date" in trades.columns:
        trades["exit_date"] = pd.to_datetime(trades["exit_date"]).dt.date

    return trades


# ── VIX emergency exit ────────────────────────────────────────────────────────

def _apply_vix_emergency_exit(
    trades: pd.DataFrame,
    stype: str,
    df_opts: pd.DataFrame,
    vix_lookup: pd.Series,
    threshold: float,
) -> pd.DataFrame:
    """
    For trades where VIX crosses `threshold` between entry and original exit,
    force-close on the first spike day using actual option marks.
    Trades with no available marks on the spike day are left unchanged.
    """
    if trades.empty:
        return trades

    cp = "C" if stype == "call_spread" else "P"

    spike_dates = set(d for d, v in vix_lookup.items() if v >= threshold)
    if not spike_dates:
        return trades

    # Build mark lookup: (trade_date, expiry, strike, cp) → mid
    opts = df_opts.copy()
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(opts[col]):
            opts[col] = opts[col].dt.date
        else:
            opts[col] = pd.to_datetime(opts[col]).dt.date
    mark_lkp: dict = {}
    for r in opts.itertuples(index=False):
        key = (r.trade_date, r.expiry, r.strike, r.cp)
        if key not in mark_lkp and r.mid:
            mark_lkp[key] = float(r.mid)

    rows = []
    for row in trades.itertuples(index=False):
        rd = row._asdict()
        entry_d  = rd["entry_date"]
        orig_exit = rd.get("exit_date") or rd.get("short_expiry")
        if orig_exit is None:
            rows.append(rd)
            continue
        if not isinstance(entry_d, date):
            entry_d  = pd.to_datetime(entry_d).date()
        if not isinstance(orig_exit, date):
            orig_exit = pd.to_datetime(orig_exit).date()

        emerg = min(
            (d for d in spike_dates if entry_d < d < orig_exit),
            default=None,
        )
        if emerg is None:
            rows.append(rd)
            continue

        # Compute new P&L from marks on emergency date
        new_pnl: Optional[float] = None

        if stype in ("put_spread", "call_spread"):
            expiry = rd["expiry"]
            if not isinstance(expiry, date):
                expiry = pd.to_datetime(expiry).date()
            s_mid = mark_lkp.get((emerg, expiry, rd["short_strike"], cp))
            l_mid = mark_lkp.get((emerg, expiry, rd["long_strike"], cp))
            if s_mid is not None and l_mid is not None:
                spread_val = max(s_mid - l_mid, 0.0)
                new_pnl = (rd["net_credit_mid"] - spread_val) * 100
                rd["exit_net_value"] = spread_val

        elif stype == "naked_put":
            expiry = rd["expiry"]
            if not isinstance(expiry, date):
                expiry = pd.to_datetime(expiry).date()
            s_mid = mark_lkp.get((emerg, expiry, rd["short_strike"], "P"))
            if s_mid is not None:
                new_pnl = (rd["short_mid"] - s_mid) * 100
                rd["exit_net_value"] = s_mid

        elif stype == "calendar":
            s_exp = rd["short_expiry"]
            l_exp = rd["long_expiry"]
            strike = rd["strike"]
            if not isinstance(s_exp, date):
                s_exp = pd.to_datetime(s_exp).date()
            if not isinstance(l_exp, date):
                l_exp = pd.to_datetime(l_exp).date()
            s_mid = mark_lkp.get((emerg, s_exp, strike, "P"))
            l_mid = mark_lkp.get((emerg, l_exp, strike, "P"))
            if s_mid is not None and l_mid is not None:
                cal_val = max(l_mid - s_mid, 0.0)
                new_pnl = (cal_val - rd["net_debit"]) * 100

        if new_pnl is None:
            rows.append(rd)  # marks not available — leave unchanged
            continue

        max_loss = float(rd.get("max_loss") or (rd.get("net_debit", 1.0) * 100))
        rd.update({
            "exit_date": emerg,
            "exit_type": f"vix_gate_{threshold:.0f}",
            "days_held": (emerg - entry_d).days,
            "net_pnl":   new_pnl,
            "is_win":    new_pnl > 0,
            "roc":       new_pnl / max(max_loss, 0.01),
        })
        rows.append(rd)

    return pd.DataFrame(rows)


# ── Main simulation ─────────────────────────────────────────────────────────────

def run_backtest(
    year: int,
    total_capital: float = 100_000.0,
    risk_pct: float = 0.20,
    ledger_csv: Optional[str] = None,
    force_sync: bool = False,
    vix_exit_threshold: Optional[float] = None,
    verbose: bool = True,
    opts_by_ticker: Optional[dict] = None,
    df_vix: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    start = date(year, 1, 1)
    end   = date(year, 12, 31)
    fetch_end = end + timedelta(days=40)

    total_risk = total_capital * risk_pct
    alloc_by_key = _compute_allocation(total_capital, risk_pct)

    gate_label = f"VIX≥{vix_exit_threshold:.0f} exit" if vix_exit_threshold else "Baseline"

    if verbose:
        print(f"\n{'═' * 72}")
        print(f"  PORTFOLIO BACKTEST  ·  {year}  ·  {gate_label}  ·  "
              f"${total_capital:,.0f} capital  ·  {risk_pct*100:.0f}% risk = ${total_risk:,.0f}")
        print(f"{'═' * 72}")
        print(f"\n  Sharpe-weighted allocations:")
        for akey, dollars in sorted(alloc_by_key.items(), key=lambda x: -x[1]):
            sh = STRATEGY_MAP[akey].sharpe_annual if akey in STRATEGY_MAP else 0.0
            print(f"    {akey:<26}  Sharpe {sh:.3f}  →  ${dollars:,.0f}")

    # ── Load VIX data (if not pre-supplied) ───────────────────────────────────
    if df_vix is None:
        if verbose:
            print(f"\n  Loading VIX data ...")
        df_vix = fetch_vix_data(start - timedelta(days=5), end)
        if df_vix.empty and verbose:
            print("  WARNING: no VIX data — VIX filters will be skipped.")
    vix_lookup = df_vix.set_index("trade_date")["vix_close"] if not df_vix.empty else pd.Series(dtype=float)

    # ── Sync and load options data per unique ticker (if not pre-supplied) ────
    if opts_by_ticker is None:
        unique_tickers = list(dict.fromkeys(c["ticker"] for c in STRATEGY_CONFIGS))
        opts_by_ticker = {}
        for ticker in unique_tickers:
            if verbose:
                print(f"  Syncing {ticker} options cache ...")
            sync_options_cache(ticker, start, force=force_sync)
            df_opts_t = fetch_options_cache(ticker, start, fetch_end)
            if verbose:
                print(f"    {len(df_opts_t):,} rows loaded.")
            opts_by_ticker[ticker] = df_opts_t

    # ── Build and simulate each strategy ──────────────────────────────────────
    all_ledger_rows: list[dict] = []

    if verbose:
        print(f"\n  Building trades ...")

    for cfg in STRATEGY_CONFIGS:
        name   = cfg["name"]
        ticker = cfg["ticker"]
        akey   = cfg["alloc_key"]
        frac   = cfg["alloc_frac"]
        concur = cfg["avg_concurrent"]

        strategy_alloc = alloc_by_key.get(akey, 0.0) * frac
        risk_per_position = strategy_alloc / max(concur, 1)

        df_opts = opts_by_ticker.get(ticker, pd.DataFrame())
        if df_opts.empty:
            if verbose:
                print(f"  {name}: no options data.")
            continue

        # Build all candidate trades (no concurrent limit yet)
        trades = _build_strategy_trades(cfg, df_opts, df_vix, start, end)
        if trades.empty:
            if verbose:
                print(f"  {name}: no trades found.")
            continue

        # Exclude split-spanning and missing-exit trades
        if "split_flag" in trades.columns:
            trades = trades[~trades["split_flag"]]
        if "is_open" in trades.columns:
            trades = trades[~trades["is_open"]]

        n_candidate = len(trades)

        # Apply VIX emergency exit (before concurrent limit — exit_date may change)
        if vix_exit_threshold is not None:
            trades = _apply_vix_emergency_exit(
                trades, cfg["type"], df_opts, vix_lookup, vix_exit_threshold,
            )

        # Apply concurrent position limit
        trades_sim = _apply_concurrent_limit(trades, max_concurrent=MAX_CONCURRENT)
        n_entered = len(trades_sim)

        if trades_sim.empty:
            if verbose:
                print(f"  {name}: {n_candidate} candidates, 0 entered after concurrent limit.")
            continue

        if verbose:
            gate_suffix = f"  [{vix_exit_threshold:.0f} gate]" if vix_exit_threshold else ""
            print(f"  {name}: {n_candidate} candidates → {n_entered} entered{gate_suffix}")

        # Compute contract count and dollar P&L per trade
        for row in trades_sim.itertuples(index=False):
            mlpc = float(getattr(row, "max_loss", 0.0))
            if mlpc <= 0:
                mlpc = 100.0  # safety fallback
            contracts = max(1, int(risk_per_position / mlpc))

            net_pnl_1ct = float(getattr(row, "net_pnl", 0.0))  # per 1 contract (× 100 already)
            pnl_dollars = net_pnl_1ct * contracts
            roc_pct = float(getattr(row, "roc", 0.0)) * 100

            entry_date = row.entry_date
            exit_date  = getattr(row, "exit_date", None)
            exit_type  = getattr(row, "exit_type", "?")
            is_win     = bool(getattr(row, "is_win", pnl_dollars > 0))
            days_held  = int(getattr(row, "days_held", 0))

            # VIX on entry
            vix_val = float(vix_lookup.get(entry_date, float("nan"))) if not vix_lookup.empty else float("nan")

            all_ledger_rows.append({
                "strategy":      name,
                "alloc_key":     akey,
                "ticker":        ticker,
                "entry_date":    entry_date,
                "exit_date":     exit_date,
                "days_held":     days_held,
                "exit_type":     exit_type,
                "contracts":     contracts,
                "risk_per_pos":  risk_per_position,
                "mlpc":          mlpc,
                "net_pnl_1ct":   net_pnl_1ct,
                "pnl_dollars":   pnl_dollars,
                "roc_pct":       roc_pct,
                "is_win":        is_win,
                "vix_on_entry":  vix_val,
            })

    if not all_ledger_rows:
        if verbose:
            print("\n  No trades generated. Check data sync.")
        return pd.DataFrame()

    ledger = pd.DataFrame(all_ledger_rows)
    ledger["exit_month"] = pd.to_datetime(ledger["exit_date"]).dt.to_period("M")

    # ── Save CSV ──────────────────────────────────────────────────────────────
    if ledger_csv:
        ledger.to_csv(ledger_csv, index=False)
        if verbose:
            print(f"\n  Ledger saved to {ledger_csv}")

    if not verbose:
        return ledger

    # ── Strategy summary ──────────────────────────────────────────────────────
    W = 100
    total_pnl = 0.0
    print(f"\n{'═' * W}")
    print(f"  STRATEGY SUMMARY  ·  {year}  ·  {gate_label}")
    print(f"{'═' * W}")
    print(f"  {'Strategy':<28}  {'N':>3}  {'Win%':>5}  {'AvgPnl$':>8}  "
          f"{'TotalPnl$':>10}  {'ROC%':>6}  {'AvgCts':>6}  Alloc$")
    print(f"  {'-' * (W - 2)}")

    for cfg in STRATEGY_CONFIGS:
        name = cfg["name"]
        sub = ledger[ledger["strategy"] == name]
        if sub.empty:
            print(f"  {name:<28}  {'—':>3}")
            continue
        n        = len(sub)
        wins     = sub["is_win"].sum()
        win_pct  = wins / n * 100
        avg_pnl  = sub["pnl_dollars"].mean()
        tot_pnl  = sub["pnl_dollars"].sum()
        avg_roc  = sub["roc_pct"].mean()
        avg_cts  = sub["contracts"].mean()
        alloc    = alloc_by_key.get(cfg["alloc_key"], 0.0) * cfg["alloc_frac"]
        total_pnl += tot_pnl

        print(f"  {name:<28}  {n:>3}  {win_pct:>4.1f}%  "
              f"  {avg_pnl:>+7.0f}  {tot_pnl:>+10.0f}  {avg_roc:>+5.1f}%  "
              f"  {avg_cts:>5.1f}  ${alloc:,.0f}")

    print(f"  {'-' * (W - 2)}")
    total_roi = total_pnl / total_risk * 100
    print(f"  {'TOTAL':<28}  {len(ledger):>3}  "
          f"  {'':>5}  {'':>8}  {total_pnl:>+10.0f}  {total_roi:>+5.1f}%  "
          f"        ${total_risk:,.0f}")
    print(f"{'═' * W}\n")

    # ── Monthly P&L ───────────────────────────────────────────────────────────
    print(f"{'═' * W}")
    print(f"  MONTHLY P&L  ·  {year}  ·  {gate_label}")
    print(f"{'═' * W}")
    print(f"  {'Month':<10}  {'N':>3}  {'Win%':>5}  {'P&L $':>9}  {'Cum P&L $':>10}  Active strategies")
    print(f"  {'-' * (W - 2)}")

    cum_pnl = 0.0
    for period, grp in ledger.groupby("exit_month"):
        n       = len(grp)
        wins    = grp["is_win"].sum()
        win_pct = wins / n * 100 if n > 0 else 0
        mpnl    = grp["pnl_dollars"].sum()
        cum_pnl += mpnl
        strats  = ", ".join(sorted(grp["strategy"].unique()))
        strats_short = strats[:42] + "..." if len(strats) > 45 else strats
        print(f"  {str(period):<10}  {n:>3}  {win_pct:>4.1f}%  "
              f"  {mpnl:>+8.0f}  {cum_pnl:>+9.0f}  {strats_short}")

    print(f"  {'-' * (W - 2)}")
    print(f"  {'YEAR TOTAL':<10}  {len(ledger):>3}  "
          f"{ledger['is_win'].mean()*100:>4.1f}%  "
          f"  {total_pnl:>+8.0f}  {total_pnl:>+9.0f}")
    print(f"{'═' * W}\n")

    # ── Full-year summary ──────────────────────────────────────────────────────
    print(f"{'═' * W}")
    print(f"  FULL-YEAR SUMMARY  ·  {year}  ·  {gate_label}")
    print(f"{'═' * W}")
    print(f"  Portfolio: ${total_capital:,.0f}  ·  Risk budget: ${total_risk:,.0f}  ({risk_pct*100:.0f}%)")
    print(f"  Strategies active: {ledger['strategy'].nunique()} / {len(STRATEGY_CONFIGS)}")
    print(f"  Total trades:      {len(ledger)}")
    print(f"  Win rate:          {ledger['is_win'].mean()*100:.1f}%")
    print(f"  Total P&L $:       {total_pnl:+,.0f}")
    print(f"  ROI on risk budget:{total_roi:+.1f}%")
    print(f"  ROI on portfolio:  {total_pnl/total_capital*100:+.1f}%")
    print(f"  Avg P&L per trade: ${ledger['pnl_dollars'].mean():+.0f}")

    monthly = ledger.groupby("exit_month")["pnl_dollars"].sum()
    if not monthly.empty:
        best  = monthly.idxmax()
        worst = monthly.idxmin()
        print(f"  Best month:        {best} (${monthly[best]:+,.0f})")
        print(f"  Worst month:       {worst} (${monthly[worst]:+,.0f})")
    print(f"{'═' * W}\n")

    return ledger


# ── Scenario comparison ────────────────────────────────────────────────────────

def run_scenarios(
    year: int,
    total_capital: float = 100_000.0,
    risk_pct: float = 0.20,
    force_sync: bool = False,
    thresholds: Optional[list] = None,
) -> None:
    """
    Run the portfolio backtest under multiple VIX emergency-exit scenarios and
    print a side-by-side comparison.  Data is loaded once and shared across runs.
    """
    if thresholds is None:
        thresholds = [None, 30, 35, 40]

    start     = date(year, 1, 1)
    end       = date(year, 12, 31)
    fetch_end = end + timedelta(days=40)
    total_risk = total_capital * risk_pct

    print(f"\n  Loading data for scenario analysis  ·  {year} ...")

    df_vix = fetch_vix_data(start - timedelta(days=5), end)
    vix_lookup = df_vix.set_index("trade_date")["vix_close"] if not df_vix.empty else pd.Series(dtype=float)

    unique_tickers = list(dict.fromkeys(c["ticker"] for c in STRATEGY_CONFIGS))
    opts_by_ticker: dict[str, pd.DataFrame] = {}
    for ticker in unique_tickers:
        print(f"  Syncing {ticker} ...")
        sync_options_cache(ticker, start, force=force_sync)
        opts_by_ticker[ticker] = fetch_options_cache(ticker, start, fetch_end)

    print(f"  Data ready. Running {len(thresholds)} scenarios ...\n")

    results: list[dict] = []
    april_period = pd.Period(f"{year}-04", "M")

    for thresh in thresholds:
        label = f"VIX≥{thresh:.0f} exit" if thresh else "Baseline"
        ledger = run_backtest(
            year=year,
            total_capital=total_capital,
            risk_pct=risk_pct,
            vix_exit_threshold=thresh,
            verbose=False,
            opts_by_ticker=opts_by_ticker,
            df_vix=df_vix,
        )
        if ledger.empty:
            continue

        total_pnl = ledger["pnl_dollars"].sum()
        win_rate  = ledger["is_win"].mean() * 100
        n         = len(ledger)
        forced    = len(ledger[ledger["exit_type"].str.startswith("vix_gate", na=False)]) if thresh else 0

        april_pnl = (
            ledger[ledger["exit_month"] == april_period]["pnl_dollars"].sum()
            if april_period in ledger["exit_month"].values else 0.0
        )
        results.append({
            "label":     label,
            "n":         n,
            "win_rate":  win_rate,
            "total_pnl": total_pnl,
            "roi_pct":   total_pnl / total_risk * 100,
            "april_pnl": april_pnl,
            "forced_exits": forced,
        })

    # ── Print comparison ──────────────────────────────────────────────────────
    W = 90
    print(f"\n{'═' * W}")
    print(f"  SCENARIO COMPARISON  ·  {year}  ·  ${total_capital:,.0f} capital  ·  {risk_pct*100:.0f}% risk")
    print(f"{'═' * W}")
    print(f"  {'Scenario':<22}  {'N':>3}  {'Win%':>5}  {'P&L $':>9}  {'ROI%':>6}  {'Apr P&L':>9}  {'Forced':>7}")
    print(f"  {'-' * (W - 2)}")
    for r in results:
        forced_str = f"{r['forced_exits']:>3}" if r['forced_exits'] > 0 else "   —"
        print(f"  {r['label']:<22}  {r['n']:>3}  {r['win_rate']:>4.1f}%  "
              f"  {r['total_pnl']:>+8.0f}  {r['roi_pct']:>+5.1f}%  "
              f"  {r['april_pnl']:>+8.0f}  {forced_str:>7}")
    print(f"  {'-' * (W - 2)}")
    if len(results) > 1:
        base = results[0]["total_pnl"]
        print(f"\n  P&L vs baseline:")
        for r in results[1:]:
            delta = r["total_pnl"] - base
            print(f"    {r['label']:<22}  {delta:>+8.0f}  ({delta/total_capital*100:>+.1f}% of capital)")
    print(f"{'═' * W}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Portfolio backtest — confirmed strategies with Sharpe-weighted allocation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--year", type=int, default=2025,
                        help="Backtest year")
    parser.add_argument("--capital", type=float, default=100_000,
                        help="Portfolio size in dollars")
    parser.add_argument("--risk-pct", type=float, default=0.20,
                        help="Fraction of capital to risk (e.g. 0.20 = 20%%)")
    parser.add_argument("--ledger-csv", type=str, default=None,
                        help="Save per-trade ledger to this CSV path")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-sync of options cache from Athena")
    parser.add_argument("--vix-exit", type=float, default=None, metavar="N",
                        help="Close open positions when VIX reaches N (e.g. 30, 35, 40)")
    parser.add_argument("--scenarios", action="store_true",
                        help="Run baseline + VIX-exit at 30/35/40 and compare (loads data once)")
    args = parser.parse_args()

    if args.scenarios:
        run_scenarios(
            year=args.year,
            total_capital=args.capital,
            risk_pct=args.risk_pct,
            force_sync=args.refresh,
        )
    else:
        run_backtest(
            year=args.year,
            total_capital=args.capital,
            risk_pct=args.risk_pct,
            ledger_csv=args.ledger_csv,
            force_sync=args.refresh,
            vix_exit_threshold=args.vix_exit,
        )


if __name__ == "__main__":
    main()

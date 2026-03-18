#!/usr/bin/env python3
"""
TLT Naked Short Call backtest.

Strategy:
  - Every Friday, sell the TLT call nearest to target_delta at ~target_dte DTE.
  - Hold until:
      (a) daily mid ≤ entry_credit × (1 - profit_take): close for profit
      (b) expiry: if OTM → keep full credit; if ITM → loss = strike - TLT_close - credit
  - Optional VIX ≥ min_vix filter.

Sweep: short_delta × profit_take × vix_filter

Usage:
  PYTHONPATH=src python run_tlt_naked_calls.py

Requires: MYSQL_PASSWORD
"""
from __future__ import annotations

import os
import pathlib
from datetime import date, timedelta

import pandas as pd

from lib.mysql_lib import _get_engine

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_DELTAS  = [0.20, 0.25, 0.30, 0.35, 0.40]
PROFIT_TAKES   = [0.50, 0.70]
VIX_MINS       = [None, 20, 25]          # None = no filter; 20 = only when VIX ≥ 20
DTE_TARGET     = 20
DTE_TOL        = 5
MAX_DELTA_ERR  = 0.08
START_DATE     = date(2018, 1, 1)
END_DATE       = date(2026, 3, 14)       # last full Friday before today


# ── Data loading ──────────────────────────────────────────────────────────────

def load_tlt_calls() -> pd.DataFrame:
    sql = f"""
        SELECT trade_date, expiry, strike, mid, delta
        FROM options_cache
        WHERE ticker = 'TLT'
          AND cp     = 'C'
          AND trade_date >= '{START_DATE}'
          AND trade_date <= '{END_DATE}'
          AND mid > 0
          AND delta > 0
        ORDER BY trade_date, expiry, strike
    """
    df = pd.read_sql(sql, _get_engine())
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].astype(float)
    df["dte"]        = (df["expiry"] - df["trade_date"]).apply(lambda d: d.days)
    return df


def load_stock() -> dict[date, float]:
    path = _CACHE_DIR / "TLT_stock.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Stock cache not found: {path}")
    df = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return dict(zip(df["trade_date"], df["close"].astype(float)))


def load_vix() -> dict[date, float]:
    path = _CACHE_DIR / "vix_daily.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col = "close" if "close" in df.columns else df.columns[-1]
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Entry selection ───────────────────────────────────────────────────────────

def find_entry(
    calls_on_date: pd.DataFrame,
    target_delta: float,
    dte_target: int = DTE_TARGET,
    dte_tol: int = DTE_TOL,
) -> pd.Series | None:
    """Find best expiry + strike for the target delta / DTE."""
    window = calls_on_date[
        (calls_on_date["dte"] >= dte_target - dte_tol) &
        (calls_on_date["dte"] <= dte_target + dte_tol)
    ]
    if window.empty:
        return None
    # pick expiry closest to dte_target
    best_exp = window.iloc[(window["dte"] - dte_target).abs().argsort()[:1]]["expiry"].iloc[0]
    candidates = window[window["expiry"] == best_exp].copy()
    candidates["_derr"] = (candidates["delta"] - target_delta).abs()
    candidates = candidates[candidates["_derr"] <= MAX_DELTA_ERR]
    if candidates.empty:
        return None
    return candidates.loc[candidates["_derr"].idxmin()]


# ── P&L simulation ────────────────────────────────────────────────────────────

def simulate_naked_call(
    entry_date: date,
    expiry: date,
    strike: float,
    entry_credit: float,
    profit_take_pct: float,
    daily_map: dict,          # (trade_date, expiry, strike) → mid
    stock_map: dict[date, float],
) -> dict:
    """
    Simulate one naked short call position.
    Returns dict with pnl_per_shr, exit_type, days_held, exit_date.
    """
    take_target = entry_credit * (1.0 - profit_take_pct)
    current_date = entry_date + timedelta(days=1)

    while current_date <= expiry:
        # daily mid for this contract
        mid = daily_map.get((current_date, expiry, strike))
        if mid is not None:
            if mid <= take_target:
                pnl = entry_credit - mid
                return dict(pnl=pnl, exit_type="profit_take",
                            days_held=(current_date - entry_date).days,
                            exit_date=current_date)
            if current_date == expiry:
                # settle at intrinsic
                spot = stock_map.get(expiry)
                if spot is None:
                    spot = stock_map.get(current_date, strike)  # fallback
                intrinsic = max(0.0, spot - strike)
                pnl = entry_credit - intrinsic
                etype = "expiry_win" if intrinsic == 0 else "expiry_loss"
                return dict(pnl=pnl, exit_type=etype,
                            days_held=(expiry - entry_date).days,
                            exit_date=expiry)
        current_date += timedelta(days=1)

    # no data after entry — use stock price at expiry
    spot = stock_map.get(expiry, strike)
    intrinsic = max(0.0, spot - strike)
    pnl = entry_credit - intrinsic
    etype = "expiry_win" if intrinsic == 0 else "expiry_loss"
    return dict(pnl=pnl, exit_type=etype,
                days_held=(expiry - entry_date).days,
                exit_date=expiry)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading TLT call data from MySQL...")
    calls = load_tlt_calls()
    print(f"  {len(calls):,} rows  ({calls['trade_date'].min()} → {calls['trade_date'].max()})")

    stock_map = load_stock()
    vix_map   = load_vix()

    # Build daily lookup: (trade_date, expiry, strike) → mid
    daily_map = {
        (row.trade_date, row.expiry, row.strike): row.mid
        for row in calls.itertuples(index=False)
    }

    # Entry dates: all Fridays (weekday==4) in range
    entry_dates = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    calls_by_date = {d: grp for d, grp in calls.groupby("trade_date")}

    results = []
    for target_delta in TARGET_DELTAS:
        for profit_take in PROFIT_TAKES:
            for vix_min in VIX_MINS:
                for edate in entry_dates:
                    # VIX filter
                    vix = vix_map.get(edate)
                    if vix_min is not None and (vix is None or vix < vix_min):
                        continue

                    day_calls = calls_by_date.get(edate)
                    if day_calls is None or day_calls.empty:
                        continue

                    entry = find_entry(day_calls, target_delta)
                    if entry is None:
                        continue

                    sim = simulate_naked_call(
                        entry_date    = edate,
                        expiry        = entry["expiry"],
                        strike        = entry["strike"],
                        entry_credit  = entry["mid"],
                        profit_take_pct = profit_take,
                        daily_map     = daily_map,
                        stock_map     = stock_map,
                    )

                    results.append({
                        "target_delta":  target_delta,
                        "profit_take":   profit_take,
                        "vix_min":       vix_min if vix_min else 0,
                        "entry_date":    edate,
                        "expiry":        entry["expiry"],
                        "strike":        entry["strike"],
                        "entry_delta":   entry["delta"],
                        "entry_credit":  entry["mid"],
                        "vix":           vix,
                        **sim,
                    })

    df = pd.DataFrame(results)
    df["year"] = pd.to_datetime(df["entry_date"]).dt.year

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "═" * 76)
    print("  TLT NAKED SHORT CALL — BACKTEST  ·  2018–2026  ·  ~20 DTE")
    print("═" * 76)

    for profit_take in PROFIT_TAKES:
        print(f"\n  Profit Take: {int(profit_take*100)}%")
        print(f"  {'Delta':>6}  {'VIX≥':>5}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  "
              f"{'AvgPnL':>7}  {'AvgROC%':>8}  {'MaxLoss':>8}  {'SumPnL':>8}")
        print("  " + "-" * 72)

        for vix_min in VIX_MINS:
            vix_val = vix_min if vix_min else 0
            for target_delta in TARGET_DELTAS:
                sub = df[
                    (df["target_delta"] == target_delta) &
                    (df["profit_take"]  == profit_take) &
                    (df["vix_min"]      == vix_val)
                ]
                if sub.empty:
                    continue
                n        = len(sub)
                wins     = (sub["pnl"] > 0).sum()
                win_pct  = wins / n * 100
                avg_cr   = sub["entry_credit"].mean()
                avg_pnl  = sub["pnl"].mean()
                # ROC: pnl as % of entry credit (income-on-income return)
                avg_roc  = (sub["pnl"] / sub["entry_credit"]).mean() * 100
                max_loss = sub["pnl"].min()
                sum_pnl  = sub["pnl"].sum()
                vix_lbl  = f"{vix_min}" if vix_min else "All"

                print(f"  {target_delta:>6.2f}  {vix_lbl:>5}  {n:>4}  "
                      f"{win_pct:>5.1f}%  ${avg_cr:>6.3f}  ${avg_pnl:>6.3f}  "
                      f"{avg_roc:>7.1f}%  ${max_loss:>7.3f}  ${sum_pnl:>7.3f}")
            print()

    # ── Per-year breakdown for best combos ───────────────────────────────────
    print("\n" + "═" * 76)
    print("  PER-YEAR BREAKDOWN  ·  0.35Δ  ·  50% take  ·  All VIX vs VIX≥20")
    print("═" * 76)

    for vix_min, lbl in [(0, "All VIX"), (20, "VIX≥20")]:
        sub = df[
            (df["target_delta"] == 0.35) &
            (df["profit_take"]  == 0.50) &
            (df["vix_min"]      == vix_min)
        ]
        if sub.empty:
            continue
        print(f"\n  {lbl}")
        print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  {'AvgPnL':>7}  {'SumPnL':>8}")
        print("  " + "-" * 50)
        for yr, grp in sub.groupby("year"):
            n       = len(grp)
            wins    = (grp["pnl"] > 0).sum()
            avg_cr  = grp["entry_credit"].mean()
            avg_pnl = grp["pnl"].mean()
            sum_pnl = grp["pnl"].sum()
            print(f"  {yr:>6}  {n:>4}  {wins/n*100:>5.1f}%  ${avg_cr:>6.3f}  "
                  f"${avg_pnl:>6.3f}  ${sum_pnl:>7.3f}")
        tot = sub
        print(f"  {'TOTAL':>6}  {len(tot):>4}  {(tot['pnl']>0).mean()*100:>5.1f}%  "
              f"${tot['entry_credit'].mean():>6.3f}  ${tot['pnl'].mean():>6.3f}  "
              f"${tot['pnl'].sum():>7.3f}")


if __name__ == "__main__":
    main()

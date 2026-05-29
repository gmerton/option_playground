#!/usr/bin/env python3
"""
Compounding simulation for any ticker.

Starting with a fixed capital allocation, enter every other Friday using the
playbook parameters.  Profits and losses are rolled back into the strategy
capital each trade.

Capital model (equal-capital blend):
  Both sides active (VIX < put_vix_max):  50% to call spread, 50% to put
  Call spread only (VIX >= put_vix_max):  100% to call spread

Dollar P&L per leg = allocated_capital × ROC
  Call spread ROC = net_pnl / max_loss          (defined-risk denominator)
  Put ROC        = short_pnl / margin_reg_t     (Reg T denominator)

Usage
-----
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \\
    .venv/bin/python3 run_compound_sim.py --ticker UVXY

  # Custom parameters:
  ... --ticker UVXY --start 2021-01-01 --capital 1000 --short-delta 0.50 --wing 0.10 --put-delta 0.40

  # No VIX gate on the put leg:
  ... --put-vix-max 100

  # ATM straddle mode (holds to expiry):
  ... --ticker UVXY --straddle
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.straddle_study import (
    build_straddle_trades,
    compute_metrics as compute_straddle_metrics,
)
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
from lib.studies.ticker_config import TICKER_CONFIG
from lib.studies.put_spread_study import (
    build_put_spread_trades,
    find_put_spread_exits,
    compute_spread_metrics as compute_put_spread_metrics,
)

DTE_TARGET  = 20
DTE_TOL     = 5


def _parse_date(s: str) -> date:
    from datetime import datetime
    return datetime.strptime(s, "%Y-%m-%d").date()


def _add_hedge_call(
    spreads: pd.DataFrame,
    df_opts: pd.DataFrame,
    hedge_delta: float,
) -> pd.DataFrame:
    """
    For each spread position, buy a long call at hedge_delta at the same expiry.
    Exits on the same date as the spread (exit_date column).

    Adds columns: hedge_strike, hedge_entry_mid, hedge_exit_mid, hedge_pnl ($).
    hedge_pnl > 0 means the hedge profited (UVXY spiked hard past the hedge strike).
    """
    calls = df_opts[df_opts["cp"] == "C"].copy()

    # Fast lookup: (trade_date, expiry, strike) -> mid
    price_idx = calls.set_index(["trade_date", "expiry", "strike"])["mid"]

    rows = []
    for _, pos in spreads.iterrows():
        entry_date = pos["entry_date"]
        expiry     = pos["expiry"]
        exit_date  = pos.get("exit_date", expiry)
        if pd.isna(exit_date):
            exit_date = expiry

        # Find closest-delta call at entry
        entry_chain = calls[
            (calls["trade_date"] == entry_date) &
            (calls["expiry"]     == expiry)
        ]
        if entry_chain.empty:
            rows.append({"entry_date": entry_date, "hedge_pnl": 0.0,
                         "hedge_entry_mid": 0.0, "hedge_strike": np.nan})
            continue

        best = entry_chain.iloc[
            (entry_chain["delta"].abs() - hedge_delta).abs().argmin()
        ]
        h_strike    = best["strike"]
        h_entry_mid = float(best["mid"])

        # Exit price: same strike at exit_date (or expiry if missing)
        try:
            h_exit_mid = float(price_idx.loc[(exit_date, expiry, h_strike)])
        except KeyError:
            try:
                h_exit_mid = float(price_idx.loc[(expiry, expiry, h_strike)])
            except KeyError:
                h_exit_mid = 0.0  # expired worthless

        hedge_pnl = (h_exit_mid - h_entry_mid) * 100  # long call, $ per contract

        rows.append({
            "entry_date":      entry_date,
            "hedge_strike":    h_strike,
            "hedge_entry_mid": round(h_entry_mid, 4),
            "hedge_exit_mid":  round(h_exit_mid, 4),
            "hedge_pnl":       round(hedge_pnl, 4),
        })

    hedge_df = pd.DataFrame(rows)
    if hedge_df.empty:
        spreads["hedge_pnl"]       = 0.0
        spreads["hedge_entry_mid"] = 0.0
        spreads["hedge_strike"]    = np.nan
        return spreads
    return spreads.merge(
        hedge_df[["entry_date", "hedge_strike", "hedge_entry_mid", "hedge_exit_mid", "hedge_pnl"]],
        on="entry_date", how="left",
    )


def build_combined_trades(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_delta: float,
    wing_width: float,
    put_delta: float,
    start: date,
    end: date,
    split_dates: list,
    put_vix_max: Optional[float] = None,
    hedge_delta: Optional[float] = None,
    max_spread_pct: float = 0.25,
) -> pd.DataFrame:
    """
    Build the full combined trade table for the given parameters.
    Returns one row per spread entry date with put columns (NaN when not active).
    put_vix_max: if set, only enter the put leg when VIX < put_vix_max.
    hedge_delta: if set, buy a long call at this delta each entry to cap tail losses.
                 The hedge P&L is folded into spread_pnl and spread_roc.
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]

    # ── Call spreads (all VIX, every Friday) ─────────────────────────────────
    spreads = build_call_spread_trades(
        df_opts, short_delta_target=short_delta, wing_delta_width=wing_width,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL,
        entry_weekday=4, split_dates=split_dates,
        max_spread_pct=max_spread_pct,
    )
    spreads["vix_on_entry"] = spreads["entry_date"].map(vix_lookup)
    spreads = find_spread_exits(spreads, df_opts)
    spreads = compute_spread_metrics(spreads)
    spreads = spreads[~spreads["split_flag"] & ~spreads["is_open"]].copy()
    spreads = spreads[
        (spreads["entry_date"] >= start) & (spreads["entry_date"] <= end)
    ].copy()

    # ── Hedge call (optional) ─────────────────────────────────────────────────
    if hedge_delta is not None:
        spreads = _add_hedge_call(spreads, df_opts, hedge_delta)
        # Fold hedge P&L into the spread metrics (same denominator: max_loss)
        spreads["net_pnl"] = spreads["net_pnl"] + spreads["hedge_pnl"].fillna(0)
        spreads["roc"]     = spreads["net_pnl"] / spreads["max_loss"]

    # ── Puts (optional VIX gate, every Friday) ────────────────────────────────
    puts = build_put_trades(
        df_opts, delta_target=put_delta,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL,
        entry_weekday=4, split_dates=split_dates,
        max_spread_pct=max_spread_pct,
    )
    puts["vix_on_entry"] = puts["entry_date"].map(vix_lookup)
    puts = find_put_exits(puts, df_opts)
    puts = compute_put_metrics(puts)
    puts = puts[~puts["split_flag"] & ~puts["is_open"]].copy()
    # VIX gate (skip if put_vix_max is None)
    if put_vix_max is not None:
        puts = puts[
            puts["vix_on_entry"].isna() | (puts["vix_on_entry"] < put_vix_max)
        ].copy()
    puts = puts[
        (puts["entry_date"] >= start) & (puts["entry_date"] <= end)
    ].copy()

    # ── Merge ─────────────────────────────────────────────────────────────────
    spread_cols = ["entry_date", "vix_on_entry",
                   "net_pnl", "max_loss", "roc", "days_held", "is_win",
                   "exit_type", "expiry"]
    if hedge_delta is not None and "hedge_entry_mid" in spreads.columns:
        spread_cols += ["hedge_entry_mid", "hedge_strike"]
    merged = spreads[spread_cols].rename(columns={
        "net_pnl": "spread_pnl",
        "max_loss": "spread_max_loss",
        "roc": "spread_roc",
        "days_held": "spread_days",
        "is_win": "spread_win",
        "exit_type": "spread_exit",
    })

    put_cols = puts[[
        "entry_date", "short_pnl", "margin_reg_t", "roc", "days_held", "is_win", "exit_type",
    ]].rename(columns={
        "short_pnl": "put_pnl",
        "margin_reg_t": "put_margin",
        "roc": "put_roc",
        "days_held": "put_days",
        "is_win": "put_win",
        "exit_type": "put_exit",
    })

    combined = merged.merge(put_cols, on="entry_date", how="left")
    combined["has_put"] = combined["put_roc"].notna()
    combined = combined.sort_values("entry_date").reset_index(drop=True)
    return combined


def build_straddle_trade_table(
    df_opts: pd.DataFrame,
    start: date,
    end: date,
    split_dates: list,
    hedge_delta: Optional[float] = None,
) -> pd.DataFrame:
    """Build ATM straddle trades (all regimes, no VIX filter, holds to expiry).
    hedge_delta: if set, buy a long call at this delta each entry; P&L folded into roc.
    """
    trades = build_straddle_trades(
        df_opts,
        dte_target=DTE_TARGET,
        dte_tol=DTE_TOL,
        call_delta=0.50,
        entry_weekday=4,
        split_dates=split_dates,
    )
    trades = compute_straddle_metrics(trades)
    trades = trades[~trades["split_flag"] & ~trades["is_open"]].copy()
    trades = trades[
        (trades["entry_date"] >= start) & (trades["entry_date"] <= end)
    ].copy()

    if hedge_delta is not None:
        # Straddle holds to expiry: _add_hedge_call falls back to expiry when no exit_date
        trades = _add_hedge_call(trades, df_opts, hedge_delta)
        trades["short_pnl_mid"] = trades["short_pnl_mid"] + trades["hedge_pnl"].fillna(0)
        trades["roc"]           = trades["short_pnl_mid"] / trades["margin_reg_t"]

    cols = ["entry_date", "roc", "margin_reg_t",
            "entry_premium_mid", "strike", "short_pnl_mid",
            "is_win", "actual_dte"]
    if hedge_delta is not None and "hedge_entry_mid" in trades.columns:
        cols += ["hedge_entry_mid", "hedge_strike"]
    return trades[cols].sort_values("entry_date").reset_index(drop=True)


def select_biweekly(df: pd.DataFrame, first_date: date) -> pd.DataFrame:
    """
    Select every-other-Friday entries starting from the first available
    entry date >= first_date.
    """
    dates = sorted(df["entry_date"].unique())
    # First entry on or after first_date
    eligible = [d for d in dates if d >= first_date]
    if not eligible:
        return pd.DataFrame()
    anchor = eligible[0]
    selected = []
    last_picked = None
    for d in eligible:
        if last_picked is None:
            selected.append(d)
            last_picked = d
        else:
            # Pick if >= 12 days since last (bi-weekly = ~14 days, allow some tolerance)
            if (d - last_picked).days >= 12:
                selected.append(d)
                last_picked = d
    return df[df["entry_date"].isin(selected)].copy()


def run_simulation(
    trades: pd.DataFrame,
    initial_capital: float,
    risk_pct: float = 0.50,
) -> pd.DataFrame:
    """
    Compound simulation: each trade deploys risk_pct of current capital.
    When both legs active, that allocation is split 50/50 between spread and put.
    When call-spread-only, the full risk_pct goes to the spread.

    risk_pct=0.50 matches the playbook: budget supports 2 concurrent 20-DTE
    positions, so each new entry uses half the strategy capital.
    """
    capital = initial_capital
    rows = []

    for _, t in trades.iterrows():
        entry_alloc = capital * risk_pct
        if t["has_put"]:
            spread_alloc = entry_alloc * 0.50
            put_alloc    = entry_alloc * 0.50
        else:
            spread_alloc = entry_alloc
            put_alloc    = 0.0

        spread_dollar = spread_alloc * t["spread_roc"]
        put_dollar    = put_alloc    * t["put_roc"] if t["has_put"] else 0.0
        total_pnl     = spread_dollar + put_dollar

        rows.append({
            "entry_date":   t["entry_date"],
            "vix":          round(t["vix_on_entry"], 1) if pd.notna(t["vix_on_entry"]) else None,
            "has_put":      t["has_put"],
            "spread_alloc": round(spread_alloc, 2),
            "put_alloc":    round(put_alloc, 2),
            "spread_roc":   round(t["spread_roc"] * 100, 2),
            "put_roc":      round(t["put_roc"] * 100, 2) if t["has_put"] else None,
            "spread_$pnl":  round(spread_dollar, 2),
            "put_$pnl":     round(put_dollar, 2),
            "trade_$pnl":   round(total_pnl, 2),
            "capital_end":  round(capital + total_pnl, 2),
        })

        capital += total_pnl

    return pd.DataFrame(rows)


def run_straddle_simulation(
    trades: pd.DataFrame,
    initial_capital: float,
    risk_pct: float = 0.50,
) -> pd.DataFrame:
    """Compound simulation for the ATM straddle (holds to expiry, all regimes)."""
    capital = initial_capital
    rows = []
    for _, t in trades.iterrows():
        alloc     = capital * risk_pct
        dollar_pnl = alloc * t["roc"]
        capital   += dollar_pnl
        rows.append({
            "entry_date":  t["entry_date"],
            "strike":      t["strike"],
            "premium":     round(t["entry_premium_mid"], 2),
            "alloc":       round(alloc, 2),
            "roc":         round(t["roc"] * 100, 2),
            "trade_$pnl":  round(dollar_pnl, 2),
            "capital_end": round(capital, 2),
            "is_win":      t["is_win"],
        })
    return pd.DataFrame(rows)


def print_straddle_simulation(sim: pd.DataFrame, initial_capital: float,
                               ticker: str = "UVXY",
                               hedge_delta: Optional[float] = None,
                               risk_pct: float = 0.50) -> None:
    final      = sim["capital_end"].iloc[-1]
    total_gain = final - initial_capital
    total_ret  = (final / initial_capital - 1) * 100
    n_trades   = len(sim)
    n_years    = (sim["entry_date"].iloc[-1] - sim["entry_date"].iloc[0]).days / 365.25
    cagr       = ((final / initial_capital) ** (1 / n_years) - 1) * 100 if n_years > 0 and final > 0 else -100
    win_pct    = sim["is_win"].mean() * 100
    worst      = sim["trade_$pnl"].min()
    worst_date = sim.loc[sim["trade_$pnl"].idxmin(), "entry_date"]
    best       = sim["trade_$pnl"].max()
    best_date  = sim.loc[sim["trade_$pnl"].idxmax(), "entry_date"]

    capital_series = pd.concat([pd.Series([initial_capital]), sim["capital_end"]]).reset_index(drop=True)
    rolling_max    = capital_series.cummax()
    drawdown       = (capital_series - rolling_max) / rolling_max * 100
    max_dd         = drawdown.min()

    sim["year"] = pd.to_datetime(sim["entry_date"]).dt.year

    hedge_str = f" + long {hedge_delta:.2f}Δ call" if hedge_delta is not None else ""
    bar = "=" * 80
    print(f"\n{bar}")
    print(f"  {ticker} ATM Short Straddle{hedge_str} — Compounding Simulation")
    print(f"  All regimes (no VIX filter)  |  20 DTE  |  Hold to expiry  |  "
          f"Risk/entry: {risk_pct*100:.0f}%  |  Starting capital: ${initial_capital:,.2f}")
    print(bar)

    print(f"\n  {'Entry Date':<14} {'Strike':>7}  {'Premium':>8}  "
          f"{'Alloc':>10}  {'ROC%':>8}  {'Trade$PnL':>10}  {'Capital':>10}")
    print("  " + "-" * 76)

    for _, r in sim.iterrows():
        print(
            f"  {str(r['entry_date']):<14} {r['strike']:>7.2f}  ${r['premium']:>7.2f}  "
            f"${r['alloc']:>9,.2f}  {r['roc']:>+7.2f}%  "
            f"${r['trade_$pnl']:>+9,.2f}  ${r['capital_end']:>9,.2f}"
        )

    print("  " + "-" * 76)
    print(f"\n{bar}")
    print(f"  SUMMARY")
    print(bar)
    print(f"  Initial capital:  ${initial_capital:>10,.2f}")
    print(f"  Final capital:    ${final:>10,.2f}")
    print(f"  Total gain:       ${total_gain:>+10,.2f}  ({total_ret:>+.1f}%)")
    print(f"  CAGR:             {cagr:>+.1f}%  over {n_years:.1f} years")
    print(f"  Trades:           {n_trades}  ({win_pct:.1f}% wins)")
    print(f"  Max drawdown:     {max_dd:.1f}%")
    print(f"  Worst trade:      ${worst:>+,.2f}  ({str(worst_date)})")
    print(f"  Best trade:       ${best:>+,.2f}  ({str(best_date)})")

    print(f"\n  {'Year':>4}  {'Trades':>6}  {'Start$':>9}  {'End$':>9}  "
          f"{'Gain$':>9}  {'Ret%':>6}  {'Wins%':>6}")
    print("  " + "-" * 62)
    cap_start = initial_capital
    for yr, grp in sim.groupby("year"):
        cap_end = grp["capital_end"].iloc[-1]
        gain    = cap_end - cap_start
        ret     = gain / cap_start * 100 if cap_start != 0 else float("nan")
        wins    = grp["is_win"].mean() * 100
        print(f"  {yr:>4}  {len(grp):>6}  ${cap_start:>8,.2f}  ${cap_end:>8,.2f}  "
              f"${gain:>+8,.2f}  {ret:>+5.1f}%  {wins:>5.1f}%")
        cap_start = cap_end
    print(bar)


def print_simulation(sim: pd.DataFrame, initial_capital: float,
                     short_delta: float, wing_width: float, put_delta: float,
                     ticker: str = "UVXY",
                     put_vix_max: Optional[float] = None,
                     hedge_delta: Optional[float] = None,
                     risk_pct: float = 0.50) -> None:
    final   = sim["capital_end"].iloc[-1]
    total_gain = final - initial_capital
    total_ret  = (final / initial_capital - 1) * 100
    n_trades   = len(sim)
    n_years    = (sim["entry_date"].iloc[-1] - sim["entry_date"].iloc[0]).days / 365.25
    cagr       = ((final / initial_capital) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
    win_pct    = (sim["trade_$pnl"] > 0).mean() * 100
    worst      = sim["trade_$pnl"].min()
    worst_date = sim.loc[sim["trade_$pnl"].idxmin(), "entry_date"]
    best       = sim["trade_$pnl"].max()
    best_date  = sim.loc[sim["trade_$pnl"].idxmax(), "entry_date"]

    # Max drawdown on capital_end series
    capital_series = pd.concat([
        pd.Series([initial_capital]),
        sim["capital_end"],
    ]).reset_index(drop=True)
    rolling_max = capital_series.cummax()
    drawdown    = (capital_series - rolling_max) / rolling_max * 100
    max_dd      = drawdown.min()

    # Per-year summary
    sim["year"] = pd.to_datetime(sim["entry_date"]).dt.year

    vix_gate_str  = f"VIX<{put_vix_max:.0f}" if put_vix_max is not None else "no VIX gate"
    hedge_str     = f" + long {hedge_delta:.2f}Δ call hedge" if hedge_delta is not None else ""
    bar = "=" * 80
    print(f"\n{bar}")
    print(f"  {ticker} Compounding Simulation")
    print(f"  Call spread: short={short_delta:.2f}Δ / wing={wing_width:.2f}Δ{hedge_str}  |  "
          f"Put: {put_delta:.2f}Δ ({vix_gate_str})")
    print(f"  Bi-weekly Fridays  |  20 DTE  |  50% PT  |  "
          f"Risk/entry: {risk_pct*100:.0f}%  |  Starting capital: ${initial_capital:,.2f}")
    print(bar)

    print(f"\n  {'Entry Date':<14} {'VIX':>5}  {'Put':>3}  "
          f"{'SprAlloc':>9}  {'PutAlloc':>9}  "
          f"{'SprROC%':>8}  {'PutROC%':>8}  "
          f"{'Trade$PnL':>10}  {'Capital':>10}")
    print("  " + "-" * 90)

    for _, r in sim.iterrows():
        put_alloc_str = f"${r['put_alloc']:>8,.2f}" if r["has_put"] else f"{'—':>9}"
        put_roc_str   = f"{r['put_roc']:>+7.2f}%" if r["put_roc"] is not None else f"{'—':>8}"
        pnl_str = f"${r['trade_$pnl']:>+9,.2f}"
        print(
            f"  {str(r['entry_date']):<14} {r['vix']:>5.1f}  "
            f"{'Y' if r['has_put'] else 'N':>3}  "
            f"${r['spread_alloc']:>8,.2f}  {put_alloc_str}  "
            f"  {r['spread_roc']:>+6.2f}%  {put_roc_str}  "
            f"  {pnl_str}  ${r['capital_end']:>9,.2f}"
        )

    print("  " + "-" * 90)

    print(f"\n{bar}")
    print(f"  SUMMARY")
    print(bar)
    print(f"  Initial capital:  ${initial_capital:>10,.2f}")
    print(f"  Final capital:    ${final:>10,.2f}")
    print(f"  Total gain:       ${total_gain:>+10,.2f}  ({total_ret:>+.1f}%)")
    print(f"  CAGR:             {cagr:>+.1f}%  over {n_years:.1f} years")
    print(f"  Trades:           {n_trades}  ({win_pct:.1f}% wins)")
    print(f"  Max drawdown:     {max_dd:.1f}%")
    print(f"  Worst trade:      ${worst:>+,.2f}  ({str(worst_date)})")
    print(f"  Best trade:       ${best:>+,.2f}  ({str(best_date)})")

    print(f"\n  {'Year':>4}  {'Trades':>6}  {'Start$':>9}  {'End$':>9}  "
          f"{'Gain$':>9}  {'Ret%':>6}  {'Wins%':>6}")
    print("  " + "-" * 62)
    cap_start = initial_capital
    for yr, grp in sim.groupby("year"):
        cap_end = grp["capital_end"].iloc[-1]
        gain    = cap_end - cap_start
        ret     = gain / cap_start * 100
        wins    = (grp["trade_$pnl"] > 0).mean() * 100
        print(f"  {yr:>4}  {len(grp):>6}  ${cap_start:>8,.2f}  ${cap_end:>8,.2f}  "
              f"${gain:>+8,.2f}  {ret:>+5.1f}%  {wins:>5.1f}%")
        cap_start = cap_end
    print(bar)


# ── Iron condor ───────────────────────────────────────────────────────────────

def _compute_vrp_series(
    ticker: str,
    entry_dates: list,
    df_opts: pd.DataFrame,
    rv_window: int = 20,
) -> pd.DataFrame:
    """
    For each entry date compute:
      rv20:   trailing 20-day realised vol (annualised)
      iv_atm: ATM straddle implied vol via Brenner-Subrahmanyam:
                σ ≈ straddle_mid / (0.7979 × K × √(T))
      vrp:    iv_atm − rv20  (positive = market overpricing actual moves)
    """
    import yfinance as yf

    fetch_start = min(entry_dates) - timedelta(days=rv_window * 3)
    fetch_end   = max(entry_dates) + timedelta(days=2)
    hist = yf.download(ticker, start=fetch_start, end=fetch_end,
                       auto_adjust=True, progress=False)
    if hist.empty:
        raise RuntimeError(f"yfinance returned no price history for {ticker}")

    closes   = hist["Close"].squeeze()
    log_rets = np.log(closes / closes.shift(1)).dropna()

    rows = []
    for entry_date in entry_dates:
        # ── RV20 ──────────────────────────────────────────────────────────────
        past = log_rets[log_rets.index.date < entry_date].tail(rv_window)
        rv20 = float(past.std() * np.sqrt(252)) if len(past) >= rv_window else np.nan

        # ── ATM straddle IV at ~DTE_TARGET ────────────────────────────────────
        day_opts = df_opts[
            (df_opts["trade_date"] == entry_date) &
            df_opts["dte"].between(DTE_TARGET - DTE_TOL, DTE_TARGET + DTE_TOL)
        ]
        calls = day_opts[day_opts["cp"] == "C"]
        puts  = day_opts[day_opts["cp"] == "P"]
        iv_atm = np.nan

        if not calls.empty and not puts.empty:
            # ATM call: delta closest to 0.50 (calls store positive delta)
            atm_call   = calls.iloc[(calls["delta"] - 0.50).abs().argmin()]
            k, expiry  = atm_call["strike"], atm_call["expiry"]
            dte_days   = int(atm_call["dte"])

            # Matching put at same expiry + strike (or nearest strike)
            ep = puts[puts["expiry"] == expiry]
            if not ep.empty:
                match_put = ep.iloc[(ep["strike"] - k).abs().argmin()]
                straddle  = float(atm_call["mid"]) + float(match_put["mid"])
                T = dte_days / 252.0
                if T > 0 and k > 0 and straddle > 0:
                    iv_atm = straddle / (0.7979 * k * np.sqrt(T))

        vrp = float(iv_atm - rv20) if not (np.isnan(iv_atm) or np.isnan(rv20)) else np.nan
        rows.append({
            "entry_date": entry_date,
            "rv20":   round(rv20,   4) if not np.isnan(rv20)   else np.nan,
            "iv_atm": round(iv_atm, 4) if not np.isnan(iv_atm) else np.nan,
            "vrp":    round(vrp,    4) if not np.isnan(vrp)    else np.nan,
        })
    return pd.DataFrame(rows)


def build_ic_trades(
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_delta: float,
    wing_width: float,
    start: date,
    end: date,
    split_dates: list,
    ticker: str = "",
    vrp_min: Optional[float] = None,
    max_spread_pct: float = 0.25,
) -> pd.DataFrame:
    """
    Build iron condor trades: symmetric bear call spread + bull put spread.
    Both legs fire every entry (no VIX gate).
    vrp_min: if set, only enter when iv_atm - rv20 >= vrp_min.
    """
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]

    # ── Bear call spread ──────────────────────────────────────────────────────
    calls = build_call_spread_trades(
        df_opts, short_delta_target=short_delta, wing_delta_width=wing_width,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL,
        entry_weekday=4, split_dates=split_dates,
        max_spread_pct=max_spread_pct,
    )
    calls["vix_on_entry"] = calls["entry_date"].map(vix_lookup)
    calls = find_spread_exits(calls, df_opts)
    calls = compute_spread_metrics(calls)
    calls = calls[~calls["split_flag"] & ~calls["is_open"]].copy()
    calls = calls[(calls["entry_date"] >= start) & (calls["entry_date"] <= end)].copy()
    # Defined-risk spread: max win = full credit kept; cap ROC at net_credit_mid/max_loss
    calls["_roc_max"] = (calls["net_credit_mid"] * 100) / calls["max_loss"].clip(lower=0.01)
    bad_calls = (calls["roc"] > calls["_roc_max"] + 1e-6).sum()
    if bad_calls:
        print(f"  WARNING: {bad_calls} call spread row(s) with ROC > theoretical max (bad data) — capped.")
    calls["roc"] = calls[["roc", "_roc_max"]].min(axis=1)
    calls = calls.drop(columns=["_roc_max"])

    # ── Bull put spread ───────────────────────────────────────────────────────
    puts = build_put_spread_trades(
        df_opts, short_delta_target=short_delta, wing_delta_width=wing_width,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL,
        entry_weekday=4, split_dates=split_dates,
        max_spread_pct=max_spread_pct,
    )
    puts = find_put_spread_exits(puts, df_opts)
    puts = compute_put_spread_metrics(puts)
    puts = puts[~puts["split_flag"] & ~puts["is_open"]].copy()
    puts = puts[(puts["entry_date"] >= start) & (puts["entry_date"] <= end)].copy()
    # Same cap for put spreads
    puts["_roc_max"] = (puts["net_credit_mid"] * 100) / puts["max_loss"].clip(lower=0.01)
    bad_puts = (puts["roc"] > puts["_roc_max"] + 1e-6).sum()
    if bad_puts:
        print(f"  WARNING: {bad_puts} put spread row(s) with ROC > theoretical max (bad data) — capped.")
    puts["roc"] = puts[["roc", "_roc_max"]].min(axis=1)
    puts = puts.drop(columns=["_roc_max"])

    # ── Merge (inner: only weeks where both legs were found) ──────────────────
    call_cols = calls[["entry_date", "vix_on_entry",
                        "net_pnl", "max_loss", "roc", "days_held", "is_win", "exit_type"]].rename(columns={
        "net_pnl": "call_pnl", "max_loss": "call_max_loss", "roc": "call_roc",
        "days_held": "call_days", "is_win": "call_win", "exit_type": "call_exit",
    })
    put_cols = puts[["entry_date", "net_pnl", "max_loss", "roc",
                     "days_held", "is_win", "exit_type"]].rename(columns={
        "net_pnl": "put_pnl", "max_loss": "put_max_loss", "roc": "put_roc",
        "days_held": "put_days", "is_win": "put_win", "exit_type": "put_exit",
    })

    combined = call_cols.merge(put_cols, on="entry_date", how="inner")
    combined["combined_roc"] = 0.5 * combined["call_roc"] + 0.5 * combined["put_roc"]
    combined = combined.sort_values("entry_date").reset_index(drop=True)

    # ── VRP gate ──────────────────────────────────────────────────────────────
    if vrp_min is not None and ticker:
        print(f"  Computing VRP for {len(combined)} candidate entries ...")
        vrp_df  = _compute_vrp_series(ticker, combined["entry_date"].tolist(), df_opts)
        combined = combined.merge(vrp_df, on="entry_date", how="left")
        n_before = len(combined)
        combined = combined[
            combined["vrp"].isna() | (combined["vrp"] >= vrp_min)
        ].copy()
        n_skipped = n_before - len(combined)
        print(f"  VRP gate (≥{vrp_min:+.2f}): skipped {n_skipped} of {n_before} entries "
              f"({n_skipped/n_before*100:.0f}%)")
    else:
        combined["rv20"]   = np.nan
        combined["iv_atm"] = np.nan
        combined["vrp"]    = np.nan

    return combined.reset_index(drop=True)


def run_ic_simulation(
    trades: pd.DataFrame,
    initial_capital: float,
    risk_pct: float = 0.50,
) -> pd.DataFrame:
    """Compound simulation for an iron condor (50% to call spread, 50% to put spread)."""
    capital = initial_capital
    rows = []
    for _, t in trades.iterrows():
        entry_alloc  = capital * risk_pct
        call_alloc   = entry_alloc * 0.50
        put_alloc    = entry_alloc * 0.50
        call_dollar  = call_alloc * t["call_roc"]
        put_dollar   = put_alloc  * t["put_roc"]
        total_pnl    = call_dollar + put_dollar
        rows.append({
            "entry_date":   t["entry_date"],
            "vix":          round(t["vix_on_entry"], 1) if pd.notna(t["vix_on_entry"]) else None,
            "rv20":         round(t["rv20"]   * 100, 1) if pd.notna(t.get("rv20"))   else None,
            "iv_atm":       round(t["iv_atm"] * 100, 1) if pd.notna(t.get("iv_atm")) else None,
            "vrp":          round(t["vrp"]    * 100, 1) if pd.notna(t.get("vrp"))    else None,
            "call_alloc":   round(call_alloc, 2),
            "put_alloc":    round(put_alloc, 2),
            "call_roc":     round(t["call_roc"] * 100, 2),
            "put_roc":      round(t["put_roc"] * 100, 2),
            "call_$pnl":    round(call_dollar, 2),
            "put_$pnl":     round(put_dollar, 2),
            "trade_$pnl":   round(total_pnl, 2),
            "capital_end":  round(capital + total_pnl, 2),
            "is_win":       total_pnl > 0,
        })
        capital += total_pnl
    return pd.DataFrame(rows)


def print_ic_simulation(sim: pd.DataFrame, initial_capital: float,
                        ticker: str, short_delta: float, wing_width: float,
                        vrp_min: Optional[float] = None,
                        risk_pct: float = 0.50) -> None:
    final      = sim["capital_end"].iloc[-1]
    total_gain = final - initial_capital
    total_ret  = (final / initial_capital - 1) * 100
    n_trades   = len(sim)
    n_years    = (sim["entry_date"].iloc[-1] - sim["entry_date"].iloc[0]).days / 365.25
    cagr       = ((final / initial_capital) ** (1 / n_years) - 1) * 100 if n_years > 0 and final > 0 else -100
    win_pct    = sim["is_win"].mean() * 100
    worst      = sim["trade_$pnl"].min()
    worst_date = sim.loc[sim["trade_$pnl"].idxmin(), "entry_date"]
    best       = sim["trade_$pnl"].max()
    best_date  = sim.loc[sim["trade_$pnl"].idxmax(), "entry_date"]

    capital_series = pd.concat([pd.Series([initial_capital]), sim["capital_end"]]).reset_index(drop=True)
    rolling_max    = capital_series.cummax()
    drawdown       = (capital_series - rolling_max) / rolling_max * 100
    max_dd         = drawdown.min()

    long_delta  = round(short_delta - wing_width, 2)
    has_vrp     = sim["vrp"].notna().any()
    vrp_str     = f"  VRP≥{vrp_min:+.2f}" if vrp_min is not None else ""
    bar = "=" * (118 if has_vrp else 100)
    print(f"\n{bar}")
    print(f"  {ticker} Iron Condor — Compounding Simulation")
    print(f"  {long_delta:.2f}Δ / {short_delta:.2f}Δ call spread  +  {short_delta:.2f}Δ / {long_delta:.2f}Δ put spread  |  "
          f"{DTE_TARGET} DTE  |  50% PT{vrp_str}  |  Risk/entry: {risk_pct*100:.0f}%  |  Capital: ${initial_capital:,.2f}")
    print(bar)

    if has_vrp:
        print(f"\n  {'Entry Date':<14} {'VIX':>5}  {'RV20%':>6}  {'IV%':>6}  {'VRP%':>6}  "
              f"{'CallAlloc':>10}  {'PutAlloc':>10}  "
              f"{'CallROC%':>9}  {'PutROC%':>9}  {'Call$PnL':>9}  {'Put$PnL':>9}  "
              f"{'Trade$PnL':>10}  {'Capital':>10}")
        print("  " + "-" * 120)
    else:
        print(f"\n  {'Entry Date':<14} {'VIX':>5}  {'CallAlloc':>10}  {'PutAlloc':>10}  "
              f"{'CallROC%':>9}  {'PutROC%':>9}  {'Call$PnL':>9}  {'Put$PnL':>9}  "
              f"{'Trade$PnL':>10}  {'Capital':>10}")
        print("  " + "-" * 104)

    for _, r in sim.iterrows():
        vix_str = f"{r['vix']:>5.1f}" if r["vix"] is not None else f"{'—':>5}"
        if has_vrp:
            rv_str  = f"{r['rv20']:>5.1f}%" if r["rv20"]   is not None else f"{'—':>6}"
            iv_str  = f"{r['iv_atm']:>5.1f}%" if r["iv_atm"] is not None else f"{'—':>6}"
            vrp_val = f"{r['vrp']:>+5.1f}%" if r["vrp"]    is not None else f"{'—':>6}"
            print(
                f"  {str(r['entry_date']):<14} {vix_str}  {rv_str}  {iv_str}  {vrp_val}  "
                f"${r['call_alloc']:>9,.2f}  ${r['put_alloc']:>9,.2f}  "
                f"  {r['call_roc']:>+7.2f}%  {r['put_roc']:>+7.2f}%  "
                f"${r['call_$pnl']:>+8,.2f}  ${r['put_$pnl']:>+8,.2f}  "
                f"  ${r['trade_$pnl']:>+8,.2f}  ${r['capital_end']:>9,.2f}"
            )
        else:
            print(
                f"  {str(r['entry_date']):<14} {vix_str}  "
                f"${r['call_alloc']:>9,.2f}  ${r['put_alloc']:>9,.2f}  "
                f"  {r['call_roc']:>+7.2f}%  {r['put_roc']:>+7.2f}%  "
                f"${r['call_$pnl']:>+8,.2f}  ${r['put_$pnl']:>+8,.2f}  "
                f"  ${r['trade_$pnl']:>+8,.2f}  ${r['capital_end']:>9,.2f}"
            )

    print("  " + "-" * 104)
    print(f"\n{bar}")
    print(f"  SUMMARY")
    print(bar)
    print(f"  Initial capital:  ${initial_capital:>10,.2f}")
    print(f"  Final capital:    ${final:>10,.2f}")
    print(f"  Total gain:       ${total_gain:>+10,.2f}  ({total_ret:>+.1f}%)")
    print(f"  CAGR:             {cagr:>+.1f}%  over {n_years:.1f} years")
    print(f"  Trades:           {n_trades}  ({win_pct:.1f}% wins)")
    print(f"  Max drawdown:     {max_dd:.1f}%")
    print(f"  Worst trade:      ${worst:>+,.2f}  ({str(worst_date)})")
    print(f"  Best trade:       ${best:>+,.2f}  ({str(best_date)})")

    sim = sim.copy()
    sim["year"] = pd.to_datetime(sim["entry_date"]).dt.year
    print(f"\n  {'Year':>4}  {'Trades':>6}  {'Start$':>9}  {'End$':>9}  "
          f"{'Gain$':>9}  {'Ret%':>6}  {'Wins%':>6}")
    print("  " + "-" * 62)
    cap_start = initial_capital
    for yr, grp in sim.groupby("year"):
        cap_end = grp["capital_end"].iloc[-1]
        gain    = cap_end - cap_start
        ret     = gain / cap_start * 100 if cap_start != 0 else float("nan")
        wins    = grp["is_win"].mean() * 100
        print(f"  {yr:>4}  {len(grp):>6}  ${cap_start:>8,.2f}  ${cap_end:>8,.2f}  "
              f"${gain:>+8,.2f}  {ret:>+5.1f}%  {wins:>5.1f}%")
        cap_start = cap_end
    print(bar)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compounding simulation for any ticker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ticker",      type=str.upper,   default="UVXY",
                        help="Ticker symbol (must exist in TICKER_CONFIG or supply --start)")
    parser.add_argument("--start",       type=_parse_date, default=None,
                        help="Simulation start date (default: ticker's configured start)")
    parser.add_argument("--end",         type=_parse_date, default=date(2026, 1, 1))
    parser.add_argument("--capital",     type=float,       default=1000.0)
    parser.add_argument("--short-delta", type=float,       default=0.50)
    parser.add_argument("--wing",        type=float,       default=0.10)
    parser.add_argument("--put-delta",   type=float,       default=0.40)
    parser.add_argument("--put-vix-max",  type=float,       default=None,
                        help="Only enter put leg when VIX < this value. "
                             "Default: 20.0 for UVXY, no gate for all other tickers.")
    parser.add_argument("--hedge-delta", type=float,       default=None,
                        help="Buy a long call at this delta each entry to cap tail losses "
                             "(e.g. 0.10). Cost is folded into spread ROC. "
                             "Default: no hedge.")
    parser.add_argument("--dte",         type=int,         default=20,
                        help="Target DTE for entry (default: 20)")
    parser.add_argument("--spread",      type=float,       default=0.25)
    parser.add_argument("--risk-pct",    type=float,       default=None,
                        help="Fraction of current capital deployed per trade entry. "
                             "Default: 0.50 for bi-weekly, 0.25 for --weekly "
                             "(keeps total exposure comparable across entry frequencies).")
    parser.add_argument("--straddle",    action="store_true",
                        help="Run ATM straddle mode (all regimes, holds to expiry) "
                             "instead of the default call-spread + put combined strategy")
    parser.add_argument("--ic",          action="store_true",
                        help="Run iron condor mode: symmetric bear call + bull put spread, "
                             "both legs every entry, 50/50 capital split")
    parser.add_argument("--vrp-min",     type=float,       default=None,
                        help="IC only: minimum VRP (iv_atm - rv20) to enter, e.g. 0.0. "
                             "Default: no gate.")
    parser.add_argument("--weekly",      action="store_true",
                        help="Enter every Friday instead of every other Friday. "
                             "Automatically halves --risk-pct to maintain comparable exposure "
                             "unless --risk-pct is set explicitly.")
    parser.add_argument("--refresh",     action="store_true")
    args = parser.parse_args()

    # ── Override DTE ─────────────────────────────────────────────────────────
    global DTE_TARGET
    DTE_TARGET = args.dte

    # ── Resolve risk_pct (weekly halves default exposure) ────────────────────
    if args.risk_pct is not None:
        risk_pct = args.risk_pct
    else:
        risk_pct = 0.25 if args.weekly else 0.50

    # ── Resolve ticker config ─────────────────────────────────────────────────
    ticker = args.ticker
    cfg = TICKER_CONFIG.get(ticker, {})
    split_dates = cfg.get("split_dates", [])

    if args.start is not None:
        sim_start = args.start
    elif cfg:
        sim_start = cfg["start"]
    else:
        parser.error(f"Ticker {ticker!r} not found in TICKER_CONFIG. "
                     f"Provide --start to specify the data start date.")

    # Default VIX gate: 20.0 for UVXY, none for everything else
    put_vix_max = args.put_vix_max
    if put_vix_max is None and ticker == "UVXY":
        put_vix_max = 20.0

    from lib.mysql_lib import fetch_options_cache
    from lib.studies.straddle_study import sync_options_cache

    end_fetch = args.end + timedelta(days=DTE_TARGET + DTE_TOL + 5)
    sync_options_cache(ticker, sim_start, force=args.refresh)

    print(f"Loading {ticker} options from MySQL ({sim_start} → {end_fetch}) ...")
    df_opts = fetch_options_cache(ticker, sim_start, end_fetch)
    print(f"  {len(df_opts):,} rows loaded.")

    print(f"\nBuilding trades ({sim_start} → {args.end}) ...")

    if args.ic:
        df_vix = fetch_vix_data(sim_start - timedelta(days=5), args.end)
        all_trades = build_ic_trades(
            df_opts=df_opts,
            df_vix=df_vix,
            short_delta=args.short_delta,
            wing_width=args.wing,
            start=sim_start,
            end=args.end,
            split_dates=split_dates,
            ticker=ticker,
            vrp_min=args.vrp_min,
            max_spread_pct=args.spread,
        )
        freq_label = "weekly" if args.weekly else "bi-weekly"
        print(f"  {len(all_trades)} total Fridays in range.")
        trades = all_trades if args.weekly else select_biweekly(all_trades, sim_start)
        print(f"  {len(trades)} {freq_label} entries selected  (risk/entry: {risk_pct*100:.0f}%).")
        sim = run_ic_simulation(trades, args.capital, risk_pct=risk_pct)
        print_ic_simulation(sim, args.capital, ticker=ticker,
                            short_delta=args.short_delta, wing_width=args.wing,
                            vrp_min=args.vrp_min, risk_pct=risk_pct)
    elif args.straddle:
        all_trades = build_straddle_trade_table(df_opts, sim_start, args.end,
                                                split_dates=split_dates,
                                                hedge_delta=args.hedge_delta)
        freq_label = "weekly" if args.weekly else "bi-weekly"
        print(f"  {len(all_trades)} total Fridays in range.")
        trades = all_trades if args.weekly else select_biweekly(all_trades, sim_start)
        print(f"  {len(trades)} {freq_label} entries selected  (risk/entry: {risk_pct*100:.0f}%).")
        sim = run_straddle_simulation(trades, args.capital, risk_pct=risk_pct)
        print_straddle_simulation(sim, args.capital, ticker=ticker,
                                  hedge_delta=args.hedge_delta, risk_pct=risk_pct)
    else:
        df_vix = fetch_vix_data(sim_start - timedelta(days=5), args.end)
        all_trades = build_combined_trades(
            df_opts=df_opts,
            df_vix=df_vix,
            short_delta=args.short_delta,
            wing_width=args.wing,
            put_delta=args.put_delta,
            start=sim_start,
            end=args.end,
            split_dates=split_dates,
            put_vix_max=put_vix_max,
            hedge_delta=args.hedge_delta,
            max_spread_pct=args.spread,
        )
        freq_label = "weekly" if args.weekly else "bi-weekly"
        print(f"  {len(all_trades)} total Fridays in range.")
        trades = all_trades if args.weekly else select_biweekly(all_trades, sim_start)
        print(f"  {len(trades)} {freq_label} entries selected  (risk/entry: {risk_pct*100:.0f}%).")
        sim = run_simulation(trades, args.capital, risk_pct=risk_pct)
        print_simulation(sim, args.capital, args.short_delta, args.wing, args.put_delta,
                         ticker=ticker, put_vix_max=put_vix_max,
                         hedge_delta=args.hedge_delta, risk_pct=risk_pct)


if __name__ == "__main__":
    main()

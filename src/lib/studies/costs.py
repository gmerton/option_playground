"""
Transaction-cost model for the option backtests (added 2026-09-08, playbook review).

Copied from data/theta_profits/backtests/dc_time_machine/run_gated_confirm.py, the one study
that modeled costs and turned tight-gap calendars net-negative:

  commission = $0.0065 per share per leg per side  ($0.65/contract, IBKR Pro tier)
  slippage   = 25% of the leg's quoted bid-ask, paid on entry AND on any exit that trades
               (a leg that settles at expiry pays no exit slippage and no exit commission)

Exit bid-ask is not stored by the studies, so the entry bid-ask is used as the exit proxy.
Everything is per share; multiply by 100 for per-contract dollars.
"""
from __future__ import annotations
import numpy as np, pandas as pd

COMMISSION_PER_LEG = 0.0065
SLIPPAGE_FRAC = 0.25


def leg_cost(ba_entry: pd.Series, traded_exit: pd.Series) -> pd.Series:
    """Per-share cost of one leg: entry commission+slippage, plus the same again if the exit trades."""
    ba = pd.to_numeric(ba_entry, errors="coerce").fillna(0.0).clip(lower=0.0)
    sides = 1.0 + traded_exit.astype(float)
    return sides * (COMMISSION_PER_LEG + SLIPPAGE_FRAC * ba)


def add_spread_costs(df: pd.DataFrame, short_bid="short_bid", short_ask="short_ask", long_bid="long_bid", long_ask="long_ask",
                     exit_type="exit_type", expiry_types=("expiry",), pnl_col="net_pnl", capital_col="max_loss", per_contract=True) -> pd.DataFrame:
    """Two-leg spread: both legs trade at entry; both trade at exit unless the exit is at expiry."""
    df = df.copy()
    traded = ~df[exit_type].isin(expiry_types)
    cost = leg_cost(df[short_ask] - df[short_bid], traded) + leg_cost(df[long_ask] - df[long_bid], traded)
    df["cost_per_share"] = cost
    mult = 100.0 if per_contract else 1.0
    df["net_pnl_net"] = df[pnl_col] - cost * mult
    df["roc_net"] = df["net_pnl_net"] / df[capital_col].clip(lower=0.01 if per_contract else 0.001)
    df["is_win_net"] = df["net_pnl_net"] > 0
    return df


def add_calendar_costs(df: pd.DataFrame, exit_type="exit_type") -> pd.DataFrame:
    """Long calendar (per share): short leg settles at expiry (no exit cost) unless closed early; long leg always trades out."""
    df = df.copy()
    early = df[exit_type].astype(str).ne("expiry")
    cost = leg_cost(df["short_entry_ask"] - df["short_entry_bid"], early) + leg_cost(df["long_entry_ask"] - df["long_entry_bid"], pd.Series(True, index=df.index))
    df["cost_per_share"] = cost
    df["net_pnl_net"] = df["net_pnl"] - cost
    df["roc_net"] = df["net_pnl_net"] / df["net_debit"].clip(lower=0.001)
    df["is_win_net"] = df["net_pnl_net"] > 0
    return df


def sim_cost(ba_legs_entry, n_legs_traded_exit: int, n_legs: int) -> float:
    """Scalar version for the loop-based regime engines: per-share cost given entry bid-asks per leg."""
    entry = sum(COMMISSION_PER_LEG + SLIPPAGE_FRAC * max(0.0, float(b)) for b in ba_legs_entry)
    exit_ = 0.0
    if n_legs_traded_exit:
        bas = sorted((max(0.0, float(b)) for b in ba_legs_entry), reverse=True)[:n_legs_traded_exit]
        exit_ = sum(COMMISSION_PER_LEG + SLIPPAGE_FRAC * b for b in bas)
    return entry + exit_

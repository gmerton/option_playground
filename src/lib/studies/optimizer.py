"""
Bayesian optimizer for the UVXY combined strategy using Optuna (TPE).

Walk-forward design
-------------------
- Training window  : 2018-01-12 → train_end_year-12-31  (default: 2022)
- Validation window: val_start_year-01-01 → latest       (default: 2023)

Objective (training set only)
------------------------------
Sharpe = mean(combined_roc) / std(combined_roc)  per-trade, training set.
combined_roc = equal-capital blend of spread ROC and put ROC (same as combined_study.py).

Parameters searched
-------------------
  short_delta    [0.30, 0.55] step 0.05  — call spread short leg
  wing_width     [0.05, 0.25] step 0.05  — call spread wing (long leg offset)
  put_delta      [0.10, 0.45] step 0.05  — short put delta
  profit_take_pct[0.30, 0.70] step 0.05  — profit take threshold
  max_spread_pct [0.15, 0.40] step 0.05  — max bid-ask spread (short legs)
  put_vix_max    [15,   35]   step 5     — max VIX to enter put
  call_vix_min   [0,    25]   step 5     — min VIX to enter call spread (0 = no floor)

Fixed (consistent with prior studies)
--------------------------------------
  dte      = 20 (configurable via CLI)
  dte_tol  = 5
  weekday  = Friday
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from lib.studies.call_spread_study import (
    build_call_spread_trades,
    find_spread_exits,
    compute_spread_metrics,
)
from lib.studies.put_study import (
    build_put_trades,
    find_exits as find_put_exits,
    compute_put_metrics,
)
from lib.studies.combined_study import combine_strategies


# ── Single trial runner ────────────────────────────────────────────────────────

def run_trial(
    df_calls: pd.DataFrame,
    df_puts: pd.DataFrame,
    vix_lookup: pd.Series,
    short_delta: float,
    wing_width: float,
    put_delta: float,
    profit_take_pct: float,
    max_spread_pct: float,
    put_vix_max: float,
    call_vix_min: float,
    dte: int = 20,
    dte_tol: int = 5,
    min_spread_trades: int = 10,
    min_put_trades: int = 5,
    split_dates: list = [],
) -> Optional[pd.DataFrame]:
    """
    Run one parameter combination. Returns the combined trades DataFrame or None
    if insufficient trades are found.

    df_calls / df_puts: pre-filtered to cp=="C" / cp=="P" for efficiency.
    vix_lookup: trade_date → vix_close Series.
    """
    # ── Call spread ────────────────────────────────────────────────────────────
    spread_pos = build_call_spread_trades(
        df_calls,
        short_delta_target=short_delta,
        wing_delta_width=wing_width,
        dte_target=dte,
        dte_tol=dte_tol,
        entry_weekday=4,
        split_dates=split_dates,
        max_delta_err=0.08,
        max_spread_pct=max_spread_pct,
    )
    if len(spread_pos) < min_spread_trades:
        return None

    spread_pos["vix_on_entry"] = spread_pos["entry_date"].map(vix_lookup)

    # Optional VIX floor for call spread
    if call_vix_min > 0:
        spread_pos = spread_pos[
            spread_pos["vix_on_entry"].isna()
            | (spread_pos["vix_on_entry"] >= call_vix_min)
        ]
    if len(spread_pos) < min_spread_trades:
        return None

    spread_pos = find_spread_exits(spread_pos, df_calls, profit_take_pct=profit_take_pct)
    spread_pos = compute_spread_metrics(spread_pos)

    # ── Short put ──────────────────────────────────────────────────────────────
    put_pos = build_put_trades(
        df_puts,
        delta_target=put_delta,
        dte_target=dte,
        dte_tol=dte_tol,
        entry_weekday=4,
        split_dates=split_dates,
        max_delta_err=0.08,
        max_spread_pct=max_spread_pct,
    )
    if len(put_pos) < min_put_trades:
        return None

    put_pos["vix_on_entry"] = put_pos["entry_date"].map(vix_lookup)
    put_pos = put_pos[
        put_pos["vix_on_entry"].isna()
        | (put_pos["vix_on_entry"] < put_vix_max)
    ]
    if len(put_pos) < min_put_trades:
        return None

    put_pos = find_put_exits(
        put_pos, df_puts,
        profit_take_pct=profit_take_pct,
        entry_mid_col="put_entry_mid",
        cp="P",
    )
    put_pos = compute_put_metrics(put_pos)

    # ── Combine ────────────────────────────────────────────────────────────────
    return combine_strategies(put_pos, spread_pos)


# ── Objective factory ──────────────────────────────────────────────────────────

def make_objective(
    df_calls: pd.DataFrame,
    df_puts: pd.DataFrame,
    vix_lookup: pd.Series,
    train_end_year: int = 2022,
    objective_metric: str = "sharpe",
    dte: int = 20,
    split_dates: list = [],
    # Optuna search bounds — (low, high) tuples, step=0.05 for deltas/fractions,
    # step=5.0 for VIX values. Defaults match the original UVXY study bounds.
    opt_short_delta:  tuple = (0.30, 0.55),  # call spread short leg delta
    opt_wing_width:   tuple = (0.05, 0.25),  # call spread wing width
    opt_put_delta:    tuple = (0.10, 0.45),  # short put delta
    opt_profit_take:  tuple = (0.30, 0.70),  # profit-take fraction of initial credit
    opt_max_spread:   tuple = (0.15, 0.40),  # max bid-ask spread on short leg (frac of mid)
    opt_put_vix_max:  tuple = (15.0, 35.0),  # max VIX to enter a short put
    opt_call_vix_min: tuple = (0.0,  25.0),  # min VIX to enter a call spread (0 = always)
):
    """
    Returns an Optuna objective function that trains on data ≤ train_end_year.

    objective_metric options:
      "sharpe"   — mean(roc) / std(roc)               [default]
      "sortino"  — mean(roc) / downside_std(roc)
      "mean_roc" — mean(roc)  [no variance penalty, overfits more]
    """

    def objective(trial):
        short_delta     = trial.suggest_float("short_delta",     *opt_short_delta,  step=0.05)
        wing_width      = trial.suggest_float("wing_width",      *opt_wing_width,   step=0.05)
        put_delta       = trial.suggest_float("put_delta",       *opt_put_delta,    step=0.05)
        profit_take_pct = trial.suggest_float("profit_take_pct", *opt_profit_take,  step=0.05)
        max_spread_pct  = trial.suggest_float("max_spread_pct",  *opt_max_spread,   step=0.05)
        put_vix_max     = trial.suggest_float("put_vix_max",     *opt_put_vix_max,  step=5.0)
        call_vix_min    = trial.suggest_float("call_vix_min",    *opt_call_vix_min, step=5.0)

        combined = run_trial(
            df_calls, df_puts, vix_lookup,
            short_delta=short_delta,
            wing_width=wing_width,
            put_delta=put_delta,
            profit_take_pct=profit_take_pct,
            max_spread_pct=max_spread_pct,
            put_vix_max=put_vix_max,
            call_vix_min=call_vix_min,
            dte=dte,
            split_dates=split_dates,
        )
        if combined is None:
            return float("-inf")

        years = pd.to_datetime(combined["entry_date"]).dt.year
        train = combined[years <= train_end_year]["combined_roc"].dropna()
        train_years = years[years <= train_end_year]

        # Require sufficient trades AND coverage across most training years.
        # Without these guards the optimizer cherry-picks sparse high-VIX periods
        # (e.g. call_vix_min=25 → 52 training trades, Sharpe 3.0 but useless OOS).
        if len(train) < 100 or train.std() == 0:
            return float("-inf")
        if train_years.nunique() < 4:
            return float("-inf")

        if objective_metric == "sharpe":
            return float(train.mean() / train.std())
        elif objective_metric == "sortino":
            downside = train[train < 0]
            dstd = downside.std() if len(downside) > 1 else train.std()
            return float(train.mean() / dstd) if dstd > 0 else float("-inf")
        else:  # mean_roc
            return float(train.mean())

    return objective


# ── Evaluation reporter ────────────────────────────────────────────────────────

def evaluate_params(
    df_calls: pd.DataFrame,
    df_puts: pd.DataFrame,
    vix_lookup: pd.Series,
    params: dict,
    train_end_year: int = 2022,
    val_start_year: int = 2023,
    dte: int = 20,
    split_dates: list = [],
) -> None:
    """Run best params and print per-year breakdown split by train / validation."""
    combined = run_trial(
        df_calls, df_puts, vix_lookup,
        short_delta=params["short_delta"],
        wing_width=params["wing_width"],
        put_delta=params["put_delta"],
        profit_take_pct=params["profit_take_pct"],
        max_spread_pct=params["max_spread_pct"],
        put_vix_max=params["put_vix_max"],
        call_vix_min=params["call_vix_min"],
        dte=dte,
        split_dates=split_dates,
    )
    if combined is None:
        print("No trades found with best parameters.")
        return

    combined = combined.copy()
    combined["_year"] = pd.to_datetime(combined["entry_date"]).dt.year

    bar = "=" * 80
    print(f"\n{bar}")
    print("  Best Parameters:")
    for k, v in sorted(params.items()):
        print(f"    {k:<20} = {v}")
    print(bar)

    print(
        f"\n  {'Year':>4}  {'N':>4}  {'SprROC%':>8}  {'PutROC%':>8}  "
        f"{'CombROC%':>9}  {'Sharpe':>7}  {'Tag':>5}"
    )
    print("  " + "-" * 68)

    for yr, grp in combined.groupby("_year"):
        n       = len(grp)
        spr_roc = grp["spread_roc"].mean() * 100
        n_put   = grp["has_put"].sum()
        put_roc = grp.loc[grp["has_put"], "put_roc"].mean() * 100 if n_put > 0 else float("nan")
        croc    = grp["combined_roc"].mean() * 100
        roc_s   = grp["combined_roc"]
        sharpe  = roc_s.mean() / roc_s.std() if len(roc_s) > 1 and roc_s.std() > 0 else float("nan")
        tag     = "VAL  ←" if yr >= val_start_year else "train"
        put_str = f"{put_roc:>+8.2f}%" if not np.isnan(put_roc) else f"{'—':>9}"
        print(
            f"  {yr:>4}  {n:>4}  {spr_roc:>+7.2f}%  {put_str}  "
            f"  {croc:>+7.2f}%  {sharpe:>+6.3f}  {tag}"
        )

    print("  " + "-" * 68)

    for label, mask in [
        ("TRAIN", combined["_year"] <= train_end_year),
        ("VAL",   combined["_year"] >= val_start_year),
    ]:
        grp = combined[mask]
        if grp.empty:
            continue
        n       = len(grp)
        spr_roc = grp["spread_roc"].mean() * 100
        n_put   = grp["has_put"].sum()
        put_roc = grp.loc[grp["has_put"], "put_roc"].mean() * 100 if n_put > 0 else float("nan")
        croc    = grp["combined_roc"].mean() * 100
        roc_s   = grp["combined_roc"]
        sharpe  = roc_s.mean() / roc_s.std() if len(roc_s) > 1 and roc_s.std() > 0 else float("nan")
        put_str = f"{put_roc:>+8.2f}%" if not np.isnan(put_roc) else f"{'—':>9}"
        print(
            f"  {label:>4}  {n:>4}  {spr_roc:>+7.2f}%  {put_str}  "
            f"  {croc:>+7.2f}%  {sharpe:>+6.3f}"
        )
    print(bar)

#!/usr/bin/env python3
"""
Generic Optuna Bayesian optimizer for the combined strategy (bear call spread +
short put).

Per-ticker optimizer search bounds and start dates are loaded from TICKER_CONFIG
in src/lib/studies/ticker_config.py.  The walk-forward design is the same for
all tickers: train on data ≤ train_end_year, validate on data ≥ val_start_year.

Usage
-----
# Default: 200 trials, Sharpe objective, train ≤ 2022, validate ≥ 2023:
  PYTHONPATH=src python run_optimizer.py --ticker UVXY
  PYTHONPATH=src python run_optimizer.py --ticker TLT

# Quick test with 50 trials:
  PYTHONPATH=src python run_optimizer.py --ticker TLT --trials 50

# Sortino objective (penalises downside variance more than Sharpe):
  PYTHONPATH=src python run_optimizer.py --ticker TLT --objective sortino

# Different train/val split:
  PYTHONPATH=src python run_optimizer.py --ticker TLT --train-end 2021 --val-start 2022

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

import argparse
from datetime import date, timedelta

import optuna
import pandas as pd

from lib.mysql_lib import fetch_options_cache
from lib.studies.put_study import fetch_vix_data
from lib.studies.straddle_study import sync_options_cache
from lib.studies.optimizer import make_objective, evaluate_params
from lib.studies.ticker_config import TICKER_CONFIG


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optuna optimizer for the generic combined strategy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ticker", required=True,
        choices=sorted(TICKER_CONFIG),
        help="Underlying ticker (must exist in TICKER_CONFIG)",
    )
    parser.add_argument(
        "--trials", type=int, default=200,
        help="Number of Optuna trials",
    )
    parser.add_argument(
        "--train-end", type=int, default=2022,
        help="Last year included in training set (inclusive)",
    )
    parser.add_argument(
        "--val-start", type=int, default=2023,
        help="First year of validation (out-of-sample) set",
    )
    parser.add_argument(
        "--dte", type=int, default=20,
        help="Target DTE for all entries",
    )
    parser.add_argument(
        "--objective", default="sharpe",
        choices=["sharpe", "sortino", "mean_roc"],
        help="Training objective metric: sharpe (mean/std), sortino (mean/downside_std), "
             "or mean_roc (no variance penalty — overfits more)",
    )
    parser.add_argument(
        "--top-n", type=int, default=5,
        help="Number of top trials to display in the summary table",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force Athena re-sync of options cache before running",
    )
    args = parser.parse_args()

    cfg = TICKER_CONFIG[args.ticker]
    end = date.today()

    # ── Load data (once; shared across all Optuna trials) ─────────────────────
    print(f"Syncing {args.ticker} options cache...")
    sync_options_cache(args.ticker, cfg["start"], force=args.refresh)

    fetch_end = end + timedelta(days=args.dte + 10)
    print(f"Loading options from MySQL ({cfg['start']} → {fetch_end}) ...")
    df_opts = fetch_options_cache(args.ticker, cfg["start"], fetch_end)
    print(f"  {len(df_opts):,} rows loaded.")

    print("Fetching VIX data ...")
    df_vix = fetch_vix_data(cfg["start"] - timedelta(days=5), end)

    # Pre-split by option type — avoids repeated filtering inside every trial,
    # which matters at 200 trials × potentially thousands of rows each.
    df_calls   = df_opts[df_opts["cp"] == "C"].copy()
    df_puts    = df_opts[df_opts["cp"] == "P"].copy()
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    print(f"  {len(df_calls):,} call rows  |  {len(df_puts):,} put rows\n")

    # ── Optuna study ──────────────────────────────────────────────────────────
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    sampler = optuna.samplers.TPESampler(seed=42)
    study   = optuna.create_study(direction="maximize", sampler=sampler)

    objective = make_objective(
        df_calls, df_puts, vix_lookup,
        train_end_year=args.train_end,
        objective_metric=args.objective,
        dte=args.dte,
        split_dates=cfg["split_dates"],
        # Pass per-ticker search bounds from the config.
        opt_short_delta=cfg["opt_short_delta"],
        opt_wing_width=cfg["opt_wing_width"],
        opt_put_delta=cfg["opt_put_delta"],
        opt_profit_take=cfg["opt_profit_take"],
        opt_max_spread=cfg["opt_max_spread"],
        opt_put_vix_max=cfg["opt_put_vix_max"],
        opt_call_vix_min=cfg["opt_call_vix_min"],
    )

    print(
        f"Running {args.trials} trials  "
        f"(ticker={args.ticker}, objective={args.objective}, "
        f"train ≤ {args.train_end}, val ≥ {args.val_start})"
    )

    def _progress(study, trial):
        if (trial.number + 1) % 25 == 0:
            best = study.best_value
            print(f"  trial {trial.number+1:>4}/{args.trials}  best {args.objective} = {best:.4f}")

    study.optimize(objective, n_trials=args.trials, callbacks=[_progress])

    best_trial = study.best_trial
    print(f"\nBest trial #{best_trial.number}: {args.objective} = {best_trial.value:.4f}")

    # ── Evaluate best params on full train + validation windows ───────────────
    evaluate_params(
        df_calls, df_puts, vix_lookup,
        params=best_trial.params,
        train_end_year=args.train_end,
        val_start_year=args.val_start,
        dte=args.dte,
        split_dates=cfg["split_dates"],
    )

    # ── Top-N trials summary table ─────────────────────────────────────────────
    trials_df = study.trials_dataframe()
    param_cols = [c for c in trials_df.columns if c.startswith("params_")]
    top = (
        trials_df[trials_df["value"] > float("-inf")]
        .nlargest(args.top_n, "value")
        [["number", "value"] + param_cols]
        .rename(columns=lambda c: c.replace("params_", ""))
    )
    print(f"\nTop {args.top_n} trials:")
    print(top.to_string(index=False, float_format="{:.3f}".format))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Long Straddle — multi-feature walk-forward model.

Trains a logistic regression (baseline) and LightGBM classifier to predict
P(win) for a 10-DTE ATM long straddle held to expiry.

Features
--------
  fvr_put_30_90   forward vol ratio (contango → buyer edge)
  ivr_30          IV percentile rank (low IVR → cheap options)
  iv_put_30       raw IV level
  premium_pct     straddle cost / ATM strike (normalized premium)
  dte             actual days to expiry at entry
  vix             VIX level on entry date
  vix_ivr         VIX percentile rank (rolling 252d)
  above_50ma      is underlying above 50-day MA?
  rv20            20-day realized vol (annualized)
  vrp             iv_put_30 - rv20 (vol risk premium; negative = buyer edge)

Walk-forward folds (expanding window)
--------------------------------------
  Train 2018–2020 → Test 2021
  Train 2018–2021 → Test 2022
  Train 2018–2022 → Test 2023
  Train 2018–2023 → Test 2024
  Train 2018–2024 → Test 2025

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_long_straddle_model.py

  # Skip all data loading — use cached feature matrix:
  ... run_long_straddle_model.py --use-cache

  # Rebuild all caches from scratch:
  ... run_long_straddle_model.py --rebuild-cache

  # Save predictions to CSV:
  ... run_long_straddle_model.py --csv

Caches (auto-updated incrementally each run)
--------------------------------------------
  data/cache/fvr_daily.parquet         FVR + IV from silver.fwd_vol_daily
  data/cache/vix.parquet               Daily VIX + rolling IVR
  data/cache/price_features.parquet    Per-ticker 50MA, RV20, momentum
  data/cache/long_straddle_features.parquet  Assembled feature matrix

Requires: AWS_PROFILE=clarinut-gmerton, MYSQL_PASSWORD=cthekb23
"""

from __future__ import annotations

import argparse
import os
import warnings
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lib.mysql_lib import _get_engine
from lib.studies.iron_fly_features import (
    build_feature_matrix,
    fetch_price_features,
    fetch_vix,
    load_fvr_cached,
    load_feature_matrix,
    save_feature_matrix,
)
from run_long_straddle_study import (
    assemble_long_straddle,
    compute_roc_buyer,
    load_all_legs,
    OOS_START,
)

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_START = date(2018, 1, 1)
PRICE_START   = date(2017, 1, 1)   # extra lookback for MA/RV warmup
TARGET        = "win"

FEATURES = [
    "fvr_put_30_90",
    "ivr_30",
    "iv_put_30",
    "premium_pct",
    "dte",
    "vix",
    "vix_ivr",
    "above_50ma",
    "rv20",
    "vrp",
]

# Walk-forward test years
WF_TEST_YEARS = [2021, 2022, 2023, 2024, 2025]


# ── Model helpers ─────────────────────────────────────────────────────────────

def _get_lgbm():
    """Return LGBMClassifier if available, else GradientBoostingClassifier."""
    try:
        from lightgbm import LGBMClassifier
        return LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=30,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=42,
            verbose=-1,
        )
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        print("  [model] lightgbm not found — using GradientBoostingClassifier")
        return GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=4,
            min_samples_leaf=30, subsample=0.8, random_state=42,
        )


def _logreg_pipeline():
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
        ("model",  LogisticRegression(C=0.1, max_iter=1000, random_state=42)),
    ])


def _lgbm_pipeline(feature_cols):
    """LightGBM with median imputation (LGBM handles NaN natively but pipeline is cleaner)."""
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model",  _get_lgbm()),
    ])


# ── Walk-forward evaluation ───────────────────────────────────────────────────

def walk_forward(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """
    Expanding-window walk-forward evaluation.

    For each test year in WF_TEST_YEARS:
      - Train on all data before Jan 1 of test year
      - Predict on test year data
      - Compute AUC, win rate at various thresholds

    Returns DataFrame with all predictions appended.
    """
    all_preds = []

    for test_year in WF_TEST_YEARS:
        train_end = date(test_year - 1, 12, 31)
        test_start = date(test_year, 1, 1)
        test_end   = date(test_year, 12, 31)

        train = df[df["entry_date"] <= train_end].copy()
        test  = df[(df["entry_date"] >= test_start) & (df["entry_date"] <= test_end)].copy()

        if len(train) < 500 or len(test) < 50:
            print(f"  [{test_year}] skipped — train={len(train)}, test={len(test)}")
            continue

        X_train = train[feature_cols].values.astype(float)
        y_train = train[TARGET].values.astype(int)
        X_test  = test[feature_cols].values.astype(float)
        y_test  = test[TARGET].values.astype(int)

        # ── Logistic regression ───────────────────────────────────────────────
        lr = _logreg_pipeline()
        lr.fit(X_train, y_train)
        prob_lr = lr.predict_proba(X_test)[:, 1]
        auc_lr  = roc_auc_score(y_test, prob_lr) if len(np.unique(y_test)) > 1 else float("nan")

        # ── LightGBM ──────────────────────────────────────────────────────────
        lgbm = _lgbm_pipeline(feature_cols)
        lgbm.fit(X_train, y_train)
        prob_lgbm = lgbm.predict_proba(X_test)[:, 1]
        auc_lgbm  = roc_auc_score(y_test, prob_lgbm) if len(np.unique(y_test)) > 1 else float("nan")

        test = test.copy()
        test["prob_lr"]   = prob_lr
        test["prob_lgbm"] = prob_lgbm
        test["test_year"] = test_year

        n_pos = y_test.sum()
        print(f"\n  [{test_year}]  train={len(train):,}  test={len(test):,}  "
              f"base_win={n_pos/len(y_test)*100:.1f}%")
        print(f"    LogReg  AUC={auc_lr:.4f}")
        print(f"    LGBM    AUC={auc_lgbm:.4f}")

        all_preds.append(test)

    if not all_preds:
        return pd.DataFrame()
    return pd.concat(all_preds, ignore_index=True)


# ── Threshold analysis ────────────────────────────────────────────────────────

def threshold_analysis(preds: pd.DataFrame, prob_col: str, model_label: str) -> None:
    """
    For each probability threshold, show: N trades, win rate, avg ROC,
    improvement vs baseline, and fraction of universe selected.
    """
    total = len(preds)
    base_win = preds[TARGET].mean()
    base_roc = preds["roc"].mean()

    print(f"\n  Threshold analysis — {model_label}")
    print(f"  Baseline: N={total:,}  win={base_win*100:.1f}%  avg_roc={base_roc:+.2f}%")
    print(f"  {'Threshold':>10}  {'N':>6}  {'%universe':>10}  {'Win%':>7}  "
          f"{'Avg ROC%':>9}  {'Δwin pp':>8}  {'Δroc pp':>8}")
    print(f"  {'-'*68}")

    for thresh in [0.45, 0.50, 0.52, 0.55, 0.58, 0.60, 0.65]:
        sub = preds[preds[prob_col] >= thresh]
        if len(sub) < 10:
            continue
        w   = sub[TARGET].mean()
        r   = sub["roc"].mean()
        pct = len(sub) / total * 100
        print(f"  {thresh:>10.2f}  {len(sub):>6,}  {pct:>9.1f}%  "
              f"{w*100:>6.1f}%  {r:>+9.2f}%  "
              f"{(w-base_win)*100:>+7.1f}  {(r-base_roc):>+7.2f}")


# ── Feature importance ────────────────────────────────────────────────────────

def print_feature_importance(df: pd.DataFrame, feature_cols: list[str]) -> None:
    """Train final model on all data and print feature importances."""
    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        return

    X = df[feature_cols].values.astype(float)
    y = df[TARGET].values.astype(int)

    imp = SimpleImputer(strategy="median")
    X_imp = imp.fit_transform(X)

    lgbm = LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=31,
        min_child_samples=30, subsample=0.8, colsample_bytree=0.8,
        reg_lambda=1.0, random_state=42, verbose=-1,
    )
    lgbm.fit(X_imp, y)

    importances = lgbm.feature_importances_
    order = np.argsort(importances)[::-1]

    print(f"\n  Feature importance (LGBM — trained on all data):")
    print(f"  {'Feature':<18}  {'Importance':>12}")
    print(f"  {'-'*34}")
    for idx in order:
        print(f"  {feature_cols[idx]:<18}  {importances[idx]:>12,}")


# ── Per-year summary ──────────────────────────────────────────────────────────

def per_year_summary(preds: pd.DataFrame, prob_col: str, threshold: float) -> None:
    print(f"\n  Per-year OOS summary (threshold={threshold}, {prob_col}):")
    print(f"  {'Year':>6}  {'N_all':>6}  {'N_sel':>6}  {'Base win%':>10}  "
          f"{'Sel win%':>9}  {'Base ROC%':>10}  {'Sel ROC%':>9}")
    print(f"  {'-'*68}")
    for yr, grp in preds.groupby("test_year"):
        sel  = grp[grp[prob_col] >= threshold]
        bw   = grp[TARGET].mean()
        br   = grp["roc"].mean()
        sw   = sel[TARGET].mean() if len(sel) else float("nan")
        sr   = sel["roc"].mean()  if len(sel) else float("nan")
        print(f"  {int(yr):>6}  {len(grp):>6,}  {len(sel):>6,}  "
              f"{bw*100:>9.1f}%  {sw*100:>8.1f}%  "
              f"{br:>+9.2f}%  {sr:>+8.2f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Long straddle walk-forward model")
    parser.add_argument("--tickers",        nargs="+", default=None)
    parser.add_argument("--ticker-file",    type=str,  default=None)
    parser.add_argument("--start",          type=str,  default=None)
    parser.add_argument("--end",            type=str,  default=None)
    parser.add_argument("--use-cache",      action="store_true",
                        help="Skip all data loading — use cached feature matrix")
    parser.add_argument("--rebuild-cache",  action="store_true",
                        help="Force re-download of all external data (FVR, VIX, prices)")
    parser.add_argument("--csv",            action="store_true",
                        help="Save prediction DataFrame to long_straddle_preds.csv")
    args = parser.parse_args()

    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [l.strip() for l in f if l.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        os.environ.setdefault("MYSQL_PASSWORD", "cthekb23")
        tickers = pd.read_sql(
            "SELECT DISTINCT ticker FROM study_summary WHERE study_id=12 ORDER BY ticker",
            _get_engine(),
        )["ticker"].tolist()

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end   = date.fromisoformat(args.end)   if args.end   else date.today()

    force = args.rebuild_cache

    print(f"Long Straddle Walk-Forward Model")
    print(f"  tickers    : {len(tickers)}")
    print(f"  date range : {start} → {end}")
    print(f"  features   : {FEATURES}")
    print(f"  target     : {TARGET}  (roc > 0)")
    print(f"  use_cache  : {args.use_cache}  |  rebuild_cache: {force}")

    # ── Fast path: load cached feature matrix ────────────────────────────────
    if args.use_cache:
        df = load_feature_matrix()
        if df is None:
            print("No cached feature matrix found — run without --use-cache first.")
            return
        print(f"  Baseline win rate: {df[TARGET].mean()*100:.1f}%  "
              f"avg ROC: {df['roc'].mean():+.2f}%")
    else:
        # ── Step 1: Load option legs ──────────────────────────────────────────
        print(f"\n--- Step 1: Load option legs from cache ---")
        legs = load_all_legs(tickers, start, end)
        if legs.empty:
            print("No data. Exiting.")
            return

        # ── Step 2: Assemble straddles + P&L ─────────────────────────────────
        print(f"\n--- Step 2: Assemble long straddles ---")
        raw    = assemble_long_straddle(legs)
        trades = compute_roc_buyer(raw)
        print(f"  {len(trades):,} trades  ({trades['ticker'].nunique():,} tickers)")
        print(f"  Baseline win rate: {trades[TARGET].mean()*100:.1f}%  "
              f"avg ROC: {trades['roc'].mean():+.2f}%")

        # ── Step 3: Load FVR (cached) ─────────────────────────────────────────
        print(f"\n--- Step 3: Load FVR + IV data (cached) ---")
        fvr = load_fvr_cached(tickers, start, end, force_refresh=force)

        # ── Step 4: Load VIX (cached) ─────────────────────────────────────────
        print(f"\n--- Step 4: Fetch VIX (cached) ---")
        vix = fetch_vix(start, end, force_refresh=force)
        if not vix.empty:
            print(f"  {len(vix):,} VIX rows  ({vix['date'].min()} → {vix['date'].max()})")

        # ── Step 5: Load price features (cached) ─────────────────────────────
        print(f"\n--- Step 5: Fetch price features (cached) ---")
        price_df = fetch_price_features(tickers, start, end, force_refresh=force)
        if not price_df.empty:
            print(f"  {len(price_df):,} price rows  ({price_df['ticker'].nunique():,} tickers)")

        # ── Step 6: Build + cache feature matrix ──────────────────────────────
        print(f"\n--- Step 6: Build feature matrix ---")
        df = build_feature_matrix(trades, fvr, vix, price_df)
        save_feature_matrix(df)

    available_features = [f for f in FEATURES if f in df.columns]
    missing_features   = [f for f in FEATURES if f not in df.columns]
    if missing_features:
        print(f"  Warning: missing features (will be skipped): {missing_features}")

    # Coverage report
    for feat in available_features:
        n_valid = df[feat].notna().sum()
        print(f"  {feat:<18}: {n_valid:>7,} / {len(df):,} valid ({n_valid/len(df)*100:.0f}%)")

    # Drop rows with no useful features at all
    df_model = df.dropna(subset=available_features, how="all").copy()
    print(f"\n  Model dataset: {len(df_model):,} rows  "
          f"({df_model['ticker'].nunique():,} tickers)  "
          f"win rate={df_model[TARGET].mean()*100:.1f}%")

    # ── Step 7: Walk-forward evaluation ───────────────────────────────────────
    print(f"\n--- Step 7: Walk-forward evaluation ---")
    print(f"  Folds: train 2018→N-1, test year N  for N in {WF_TEST_YEARS}")

    preds = walk_forward(df_model, available_features)

    if preds.empty:
        print("No predictions generated.")
        return

    # ── Step 8: Threshold analysis ────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  RESULTS — {len(preds):,} OOS predictions ({preds['test_year'].nunique()} years)")
    print(f"{'='*70}")

    for prob_col, label in [("prob_lr", "LogReg"), ("prob_lgbm", "LGBM")]:
        if prob_col not in preds.columns:
            continue
        threshold_analysis(preds, prob_col, label)

    # ── Step 9: Per-year breakdown ────────────────────────────────────────────
    for prob_col, label in [("prob_lr", "LogReg"), ("prob_lgbm", "LGBM")]:
        if prob_col not in preds.columns:
            continue
        per_year_summary(preds, prob_col, threshold=0.55)

    # ── Step 10: Feature importance ───────────────────────────────────────────
    print_feature_importance(df_model, available_features)

    if args.csv:
        out_cols = ["ticker", "entry_date", "expiry", "atm_strike", "cost",
                    "payout", "profit", "roc", "win", "test_year",
                    "prob_lr", "prob_lgbm"] + available_features
        out_cols = [c for c in out_cols if c in preds.columns]
        preds[out_cols].to_csv("long_straddle_preds.csv", index=False)
        print(f"\n  Predictions saved → long_straddle_preds.csv")


if __name__ == "__main__":
    main()

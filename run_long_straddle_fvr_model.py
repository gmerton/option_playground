#!/usr/bin/env python3
"""
Train/test evaluation of the single-variable model:

    ret_pct_long  ~  fvr_put_30_90        (flat-forward ratio, 30->90d)

Reads the dataset produced by run_long_straddle_fvr_regression.py --csv so the
split can be re-run without re-querying Athena.

Split design
------------
CHRONOLOGICAL, not random.  A random split leaks: entries are weekly and the
universe is ~86 correlated large-caps, so the same Friday vol shock would appear
in both sets and the test score would be inflated.  Train is everything before
--split-date; test is everything on/after.

PURGE: a trade entered before the split date settles ~10 days later, which can
straddle the boundary.  Train rows whose EXPIRY falls on/after the split date
are dropped so no training label depends on post-split price action.

What is reported
----------------
  1. Train fit          - slope/intercept, R^2, clustered SE (the fitted model)
  2. Test performance   - the TRAIN model applied to unseen data:
                          OOS R^2 vs the train-mean baseline (Campbell-Thompson),
                          plus test-set Spearman (does the ordering survive?)
  3. Test-refit         - slope refit on test, purely to see if the coefficient
                          is stable or flips sign
  4. Economic test      - bucket edges fixed on TRAIN, applied to TEST.
                          For a low-R^2 regime signal this matters more than R^2.
  5. Universe drift     - tickers that exist in only one of the two periods.

Usage
-----
  PYTHONPATH=src .venv/bin/python3 run_long_straddle_fvr_model.py
  PYTHONPATH=src .venv/bin/python3 run_long_straddle_fvr_model.py --split-date 2023-01-01
  PYTHONPATH=src .venv/bin/python3 run_long_straddle_fvr_model.py --common-tickers-only
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy import stats

IN_CSV   = "long_straddle_fvr_data.csv"
FVR_COL  = "fvr_put_30_90"
Y_COL    = "ret_pct_long"
BUCKETS  = [0, 0.80, 0.90, 1.00, 1.10, 1.20, np.inf]
BLABELS  = ["<0.80", "0.80-0.90", "0.90-1.00", "1.00-1.10", "1.10-1.20", ">=1.20"]


def _sig(p: float) -> str:
    return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))


# ── Fitting ───────────────────────────────────────────────────────────────────

def fit_ols(df: pd.DataFrame) -> dict:
    """OLS with intercept; SEs clustered by entry_date (CR0 sandwich)."""
    x = df[FVR_COL].to_numpy(dtype=float)
    y = df[Y_COL].to_numpy(dtype=float)
    n = len(df)
    X = np.column_stack([np.ones(n), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    sigma2 = (resid @ resid) / (n - 2)
    se_naive = float(np.sqrt(np.diag(sigma2 * XtX_inv))[1])

    groups = pd.Series(df["entry_date"].to_numpy()).factorize()[0]
    n_cl = int(groups.max() + 1)
    meat = np.zeros((2, 2))
    for g in range(n_cl):
        m = groups == g
        s = X[m].T @ resid[m]
        meat += np.outer(s, s)
    V = XtX_inv @ meat @ XtX_inv * (n_cl / (n_cl - 1)) * ((n - 1) / (n - 2))
    se_cl = float(np.sqrt(np.diag(V))[1])

    r, _ = stats.pearsonr(x, y)
    rho, p_rho = stats.spearmanr(x, y)
    t_cl = beta[1] / se_cl
    return {
        "n": n, "n_clusters": n_cl,
        "intercept": float(beta[0]), "slope": float(beta[1]),
        "se_naive": se_naive, "se_clustered": se_cl,
        "t_naive": beta[1] / se_naive, "t_clustered": t_cl,
        "p_clustered": float(2 * stats.t.sf(abs(t_cl), n_cl - 1)),
        "r2": r ** 2, "spearman_r": rho, "p_spearman": p_rho,
    }


def evaluate_oos(model: dict, test: pd.DataFrame, train_mean: float) -> dict:
    """Apply the train-fitted model to the test set."""
    x = test[FVR_COL].to_numpy(dtype=float)
    y = test[Y_COL].to_numpy(dtype=float)
    pred = model["intercept"] + model["slope"] * x

    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - train_mean) ** 2))   # baseline = train mean
    r2_oos = 1 - ss_res / ss_tot

    rho, p_rho = stats.spearmanr(x, y)
    return {
        "n": len(test),
        "r2_oos": r2_oos,
        "rmse": float(np.sqrt(ss_res / len(test))),
        "rmse_baseline": float(np.sqrt(ss_tot / len(test))),
        "spearman_r": rho, "p_spearman": p_rho,
        "mean_actual": float(y.mean()),
        "mean_pred": float(pred.mean()),
    }


def buckets(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["b"] = pd.cut(d[FVR_COL], bins=BUCKETS, labels=BLABELS)
    return (
        d.groupby("b", observed=True)
        .agg(n=(Y_COL, "count"), mean=(Y_COL, "mean"), median=(Y_COL, "median"),
             win=(Y_COL, lambda s: (s > 0).mean() * 100))
        .reset_index()
    )


# ── Printing ──────────────────────────────────────────────────────────────────

def print_fit(res: dict, label: str) -> None:
    print(f"\n  {label}")
    print(f"    n={res['n']:,} ({res['n_clusters']:,} dates)   "
          f"intercept={res['intercept']:+.3f}   slope={res['slope']:+.3f}")
    print(f"    R^2={res['r2']:.5f}   Spearman rho={res['spearman_r']:+.4f} "
          f"[{_sig(res['p_spearman'])}]")
    print(f"    SE naive={res['se_naive']:.3f} (t={res['t_naive']:+.2f})   "
          f"SE clustered={res['se_clustered']:.3f} (t={res['t_clustered']:+.2f}, "
          f"p={res['p_clustered']:.3g} [{_sig(res['p_clustered'])}])")


def print_buckets(bt: pd.DataFrame, bs: pd.DataFrame) -> None:
    print(f"\n  {'FVR bucket':<12} | {'TRAIN':^30} | {'TEST':^30}")
    print(f"  {'':12} | {'n':>6}{'mean%':>9}{'med%':>8}{'win%':>7} | "
          f"{'n':>6}{'mean%':>9}{'med%':>8}{'win%':>7}")
    print(f"  {'-'*12}-+-{'-'*30}-+-{'-'*30}")
    for lb in BLABELS:
        rt = bt[bt["b"] == lb]
        rs = bs[bs["b"] == lb]
        def fmt(r):
            if not len(r):
                return f"{'-':>6}{'-':>9}{'-':>8}{'-':>7}"
            r = r.iloc[0]
            return f"{int(r['n']):>6}{r['mean']:>+9.2f}{r['median']:>+8.2f}{r['win']:>6.1f}%"
        print(f"  {lb:<12} | {fmt(rt)} | {fmt(rs)}")

    def spread(b):
        lo = b[b["b"] == "<0.80"]["mean"].values
        hi = b[b["b"] == ">=1.20"]["mean"].values
        return float(lo[0] - hi[0]) if len(lo) and len(hi) else float("nan")
    print(f"  {'-'*12}-+-{'-'*30}-+-{'-'*30}")
    print(f"  {'<0.80 minus >=1.20 spread':<28}   TRAIN {spread(bt):+.2f}pp"
          f"      TEST {spread(bs):+.2f}pp")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Train/test split for FVR -> long straddle")
    ap.add_argument("--csv", default=IN_CSV)
    ap.add_argument("--split-date", default=None,
                    help="Test set starts here. Default: date giving ~70%% train.")
    ap.add_argument("--purge-days", type=int, default=0,
                    help="Extra buffer beyond expiry-based purge (default 0)")
    ap.add_argument("--common-tickers-only", action="store_true",
                    help="Restrict to tickers present in BOTH periods (removes IPO drift)")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, parse_dates=["entry_date", "expiry"])
    df["entry_date"] = df["entry_date"].dt.date
    df["expiry"] = df["expiry"].dt.date
    df = df.dropna(subset=[FVR_COL, Y_COL])
    print(f"Loaded {len(df):,} observations, {df['ticker'].nunique()} tickers, "
          f"{df['entry_date'].min()} -> {df['entry_date'].max()}")

    # ── Split point ──────────────────────────────────────────────────────────
    if args.split_date:
        split = date.fromisoformat(args.split_date)
    else:
        split = pd.Series(sorted(df["entry_date"])).quantile(0.70, interpolation="nearest")
    print(f"\n{'='*72}")
    print(f"  CHRONOLOGICAL SPLIT at {split}   (random split would leak: weekly")
    print(f"  entries across 86 correlated names share market-wide vol shocks)")
    print(f"{'='*72}")

    purge_cut = split + timedelta(days=args.purge_days)
    train = df[(df["entry_date"] < split) & (df["expiry"] < purge_cut)].copy()
    dropped = len(df[df["entry_date"] < split]) - len(train)
    test = df[df["entry_date"] >= split].copy()
    print(f"  TRAIN : {len(train):>6,} obs  {train['entry_date'].min()} -> "
          f"{train['entry_date'].max()}  ({train['ticker'].nunique()} tickers)")
    print(f"  TEST  : {len(test):>6,} obs  {test['entry_date'].min()} -> "
          f"{test['entry_date'].max()}  ({test['ticker'].nunique()} tickers)")
    print(f"  purged {dropped} train rows whose expiry crossed the split boundary")

    # ── Universe drift ───────────────────────────────────────────────────────
    tr_t, te_t = set(train["ticker"]), set(test["ticker"])
    only_test  = sorted(te_t - tr_t)
    only_train = sorted(tr_t - te_t)
    if only_test:
        print(f"\n  TEST-ONLY tickers ({len(only_test)}): {', '.join(only_test)}")
        print(f"    (recent IPOs - the test universe is not the train universe)")
    if only_train:
        print(f"  TRAIN-ONLY tickers ({len(only_train)}): {', '.join(only_train)}")

    if args.common_tickers_only:
        common = tr_t & te_t
        train = train[train["ticker"].isin(common)]
        test = test[test["ticker"].isin(common)]
        print(f"\n  [--common-tickers-only] restricted to {len(common)} shared tickers: "
              f"train={len(train):,}  test={len(test):,}")

    # ── Fit on train, evaluate on test ───────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  MODEL:  {Y_COL} ~ a + b * {FVR_COL}")
    print(f"{'='*72}")
    m_train = fit_ols(train)
    print_fit(m_train, "TRAIN FIT (this is the model)")

    train_mean = float(train[Y_COL].mean())
    oos = evaluate_oos(m_train, test, train_mean)
    print(f"\n  TEST PERFORMANCE (train model applied to unseen data)")
    print(f"    n={oos['n']:,}")
    print(f"    OOS R^2 vs train-mean baseline : {oos['r2_oos']:+.5f}")
    print(f"    RMSE  model={oos['rmse']:.2f}   baseline={oos['rmse_baseline']:.2f}")
    print(f"    Test Spearman rho              : {oos['spearman_r']:+.4f} "
          f"[{_sig(oos['p_spearman'])}]   <- does the ORDERING survive?")
    print(f"    mean actual={oos['mean_actual']:+.2f}%   "
          f"mean predicted={oos['mean_pred']:+.2f}%")

    m_test = fit_ols(test)
    print_fit(m_test, "TEST REFIT (coefficient stability check, not a score)")
    stable = (np.sign(m_train["slope"]) == np.sign(m_test["slope"]))
    print(f"    -> slope sign {'HELD' if stable else 'FLIPPED'} out of sample "
          f"({m_train['slope']:+.2f} -> {m_test['slope']:+.2f})")

    # ── Economic test ────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  ECONOMIC TEST - bucket edges fixed a priori, applied to both sets")
    print(f"{'='*72}")
    print_buckets(buckets(train), buckets(test))

    print(f"\n  For a regime signal, the bucket spread holding sign and rough")
    print(f"  magnitude out of sample matters more than OOS R^2, which will sit")
    print(f"  near zero by construction on single-name option returns.")


if __name__ == "__main__":
    main()

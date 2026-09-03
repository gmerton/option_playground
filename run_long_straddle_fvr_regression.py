#!/usr/bin/env python3
"""
Flat-Forward Ratio (30→90d) → LONG 10-DTE Straddle Return — single-variable OLS.

X : fvr_put_30_90 on the entry date
      = sigma_fwd(30->90) / iv_put_30, where
        sigma_fwd = sqrt( (iv90^2 * T90 - iv30^2 * T30) / (T90 - T30) )
      i.e. the flat-forward ratio: forward vol over the 30->90 stub, divided by
      the 30d spot-starting vol.  < 1 = backwardation, > 1 = contango.

Y : ret_pct_long = (payout - entry_premium) / entry_premium * 100
      Long ATM straddle, entered Friday at ~10 DTE, held to expiry.
      Floored at -100% (both legs expire worthless); upside unbounded.

This is the buy-side mirror of run_fvr_straddle_regression.py, which scores the
same trade as `profit_pct_seller`.  Two deliberate differences:

  1. Outlier handling.  The seller study DROPS rows outside p1/p99.  For a long
     straddle the right tail IS the payoff, so trimming it removes the thing
     being measured.  Untrimmed is the headline here; the trimmed fit is
     reported alongside purely as a sensitivity check.

  2. Inference.  Entries are weekly and the universe is ~86 highly correlated
     large-caps, so on any given Friday all names share one market-wide vol
     shock.  Naive OLS standard errors treat those as independent and overstate
     significance badly.  Standard errors clustered by entry_date are reported
     as the primary inference.

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \\
      run_long_straddle_fvr_regression.py \\
      --ticker-file data/watchlist/liquid_straddle_universe.txt --csv
"""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

# Reuse the vetted Athena straddle query + FVR loader from the seller study.
from run_fvr_straddle_regression import (
    BATCH_SIZE,
    DEFAULT_START,
    DTE_TARGET,
    DTE_TOL,
    fetch_straddle_batch,
    load_fvr,
)

FVR_COL      = "fvr_put_30_90"
Y_COL        = "ret_pct_long"
MIN_TICKER_N = 15
OUT_CSV      = "long_straddle_fvr_data.csv"


# ── P&L ───────────────────────────────────────────────────────────────────────

def compute_long_pnl(straddle_df: pd.DataFrame, fvr_df: pd.DataFrame) -> pd.DataFrame:
    """Merge straddle entries with FVR on (ticker, entry_date); add long-side return."""
    if straddle_df.empty or fvr_df.empty:
        return pd.DataFrame()

    merged = straddle_df.merge(
        fvr_df.rename(columns={"trade_date": "entry_date"}),
        on=["ticker", "entry_date"],
        how="inner",
    )
    if merged.empty:
        return merged

    merged = merged.dropna(subset=["payout", FVR_COL])
    merged = merged[merged["entry_premium"] > 0]
    merged[Y_COL] = (
        (merged["payout"] - merged["entry_premium"]) / merged["entry_premium"] * 100
    )
    return merged


# ── Regression ────────────────────────────────────────────────────────────────

def ols_with_clustered_se(df: pd.DataFrame) -> dict:
    """
    OLS of Y on FVR with an intercept.  Reports both naive (iid) and
    entry_date-clustered standard errors via the CR0 sandwich estimator.
    """
    sub = df.dropna(subset=[FVR_COL, Y_COL])
    x = sub[FVR_COL].to_numpy(dtype=float)
    y = sub[Y_COL].to_numpy(dtype=float)
    n = len(sub)

    X = np.column_stack([np.ones(n), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    # Naive (iid) SE
    sigma2 = (resid @ resid) / (n - 2)
    se_naive = np.sqrt(np.diag(sigma2 * XtX_inv))

    # Cluster-robust by entry_date
    groups = pd.Series(sub["entry_date"].to_numpy()).factorize()[0]
    n_clusters = groups.max() + 1
    meat = np.zeros((2, 2))
    for g in range(n_clusters):
        m = groups == g
        Xg, ug = X[m], resid[m]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    dof_adj = (n_clusters / (n_clusters - 1)) * ((n - 1) / (n - 2))
    V_cl = XtX_inv @ meat @ XtX_inv * dof_adj
    se_cl = np.sqrt(np.diag(V_cl))

    t_naive = beta[1] / se_naive[1]
    t_cl    = beta[1] / se_cl[1]
    r, p_pearson = stats.pearsonr(x, y)
    rho, p_spearman = stats.spearmanr(x, y)

    return {
        "n": n,
        "n_clusters": int(n_clusters),
        "intercept": beta[0],
        "slope": beta[1],
        "se_naive": se_naive[1],
        "se_clustered": se_cl[1],
        "t_naive": t_naive,
        "t_clustered": t_cl,
        "p_naive": 2 * stats.t.sf(abs(t_naive), n - 2),
        "p_clustered": 2 * stats.t.sf(abs(t_cl), n_clusters - 1),
        "r2": r ** 2,
        "pearson_r": r,
        "p_pearson": p_pearson,
        "spearman_r": rho,
        "p_spearman": p_spearman,
    }


def bucket_analysis(df: pd.DataFrame) -> pd.DataFrame:
    bins   = [0, 0.80, 0.90, 1.00, 1.10, 1.20, np.inf]
    labels = ["<0.80", "0.80-0.90", "0.90-1.00", "1.00-1.10", "1.10-1.20", ">=1.20"]
    d = df.dropna(subset=[FVR_COL]).copy()
    d["fvr_bucket"] = pd.cut(d[FVR_COL], bins=bins, labels=labels)
    return (
        d.groupby("fvr_bucket", observed=True)
        .agg(
            n         =(Y_COL, "count"),
            mean_ret  =(Y_COL, "mean"),
            median_ret=(Y_COL, "median"),
            win_rate  =(Y_COL, lambda s: (s > 0).mean() * 100),
            p90_ret   =(Y_COL, lambda s: s.quantile(0.90)),
            std_ret   =(Y_COL, "std"),
        )
        .reset_index()
    )


def per_ticker_corr(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sub = df.dropna(subset=[FVR_COL, Y_COL])
    for ticker, grp in sub.groupby("ticker"):
        if len(grp) < MIN_TICKER_N:
            continue
        rho, p = stats.spearmanr(grp[FVR_COL], grp[Y_COL])
        rows.append({
            "ticker": ticker,
            "n": len(grp),
            "spearman_r": round(float(rho), 4),
            "p_value": round(float(p), 4),
            "mean_ret_pct": round(grp[Y_COL].mean(), 2),
        })
    return pd.DataFrame(rows).sort_values("spearman_r")


# ── Printing ──────────────────────────────────────────────────────────────────

def _sig(p: float) -> str:
    return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))


def print_regression(res: dict, label: str) -> None:
    print(f"\n{'='*68}")
    print(f"  OLS: {Y_COL} ~ {FVR_COL}   [{label}]")
    print(f"{'='*68}")
    print(f"  N observations   : {res['n']:,}   ({res['n_clusters']:,} distinct entry dates)")
    print(f"  Intercept        : {res['intercept']:+.4f}")
    print(f"  Slope (beta)     : {res['slope']:+.4f}")
    print(f"  R^2              : {res['r2']:.5f}")
    print(f"  Pearson r        : {res['pearson_r']:+.4f}")
    print(f"  Spearman rho     : {res['spearman_r']:+.4f}  [{_sig(res['p_spearman'])}]")
    print(f"  {'-'*64}")
    print(f"  {'inference':<22}{'SE':>12}{'t':>10}{'p':>14}")
    print(f"  {'naive (iid)':<22}{res['se_naive']:>12.4f}{res['t_naive']:>10.2f}"
          f"{res['p_naive']:>14.3e}  [{_sig(res['p_naive'])}]")
    print(f"  {'clustered by date':<22}{res['se_clustered']:>12.4f}{res['t_clustered']:>10.2f}"
          f"{res['p_clustered']:>14.3e}  [{_sig(res['p_clustered'])}]")
    print(f"  {'-'*64}")
    print(f"  Clustered SE is the one to trust: weekly entries across ~86")
    print(f"  correlated large-caps are not independent observations.")
    d = "higher FVR (contango) -> HIGHER long-straddle return" if res["slope"] > 0 \
        else "higher FVR (contango) -> LOWER long-straddle return"
    print(f"  Direction: {d}")


def print_buckets(bkt: pd.DataFrame, label: str) -> None:
    print(f"\n{'='*68}")
    print(f"  LONG STRADDLE RETURN BY FLAT-FORWARD-RATIO BUCKET  [{label}]")
    print(f"{'='*68}")
    print(f"  {'FVR bucket':<12}{'N':>7}{'Mean%':>9}{'Median%':>9}{'Win%':>8}{'p90%':>9}{'Std':>9}")
    print(f"  {'-'*63}")
    for _, r in bkt.iterrows():
        print(f"  {str(r['fvr_bucket']):<12}{int(r['n']):>7}{r['mean_ret']:>+9.2f}"
              f"{r['median_ret']:>+9.2f}{r['win_rate']:>7.1f}%{r['p90_ret']:>+9.1f}"
              f"{r['std_ret']:>9.1f}")


def print_per_ticker(corr: pd.DataFrame, top_n: int = 15) -> None:
    print(f"\n{'='*68}")
    print(f"  PER-TICKER SPEARMAN rho  (FVR vs long-straddle return, n>={MIN_TICKER_N})")
    print(f"{'='*68}")
    n_neg = (corr["spearman_r"] < 0).sum()
    print(f"  Tickers qualifying: {len(corr)}   negative rho: {n_neg} "
          f"({n_neg/len(corr)*100:.1f}%)   positive rho: {len(corr)-n_neg}")
    sig_neg = ((corr["spearman_r"] < 0) & (corr["p_value"] < 0.05)).sum()
    sig_pos = ((corr["spearman_r"] > 0) & (corr["p_value"] < 0.05)).sum()
    print(f"  Significant at p<0.05:  {sig_neg} negative  vs  {sig_pos} positive")
    print(f"\n  --- Most NEGATIVE rho ---")
    for _, r in corr.head(top_n).iterrows():
        print(f"    {r['ticker']:<8} rho={r['spearman_r']:+.3f}{_sig(r['p_value']):<4} "
              f"n={int(r['n']):>4}  mean_ret={r['mean_ret_pct']:+.1f}%")
    print(f"\n  --- Most POSITIVE rho ---")
    for _, r in corr.tail(top_n).iloc[::-1].iterrows():
        print(f"    {r['ticker']:<8} rho={r['spearman_r']:+.3f}{_sig(r['p_value']):<4} "
              f"n={int(r['n']):>4}  mean_ret={r['mean_ret_pct']:+.1f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Flat-forward ratio -> long 10-DTE straddle return")
    ap.add_argument("--tickers", nargs="+", default=None)
    ap.add_argument("--ticker-file", type=str, default=None)
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--end", type=str, default=None)
    ap.add_argument("--csv", action="store_true", help=f"save merged dataset to {OUT_CSV}")
    args = ap.parse_args()

    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [l.strip().upper() for l in f if l.strip()]
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        ap.error("supply --tickers or --ticker-file")

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end   = date.fromisoformat(args.end)   if args.end   else date.today()

    print("Flat-Forward Ratio (30->90d) -> LONG 10-DTE Straddle Return")
    print(f"  tickers    : {len(tickers)}")
    print(f"  date range : {start} -> {end}")
    print(f"  entry      : Friday, ~{DTE_TARGET} DTE (+/-{DTE_TOL}), ATM straddle, BUY")
    print(f"  exit       : hold to expiry")

    frames: list[pd.DataFrame] = []
    n_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]
        print(f"\n[batch {i//BATCH_SIZE + 1}/{n_batches}] {batch[0]}...{batch[-1]}",
              end="  ", flush=True)
        sdf = fetch_straddle_batch(batch, start, end)
        if sdf.empty:
            print("-> 0 straddle entries")
            continue
        fdf = load_fvr(batch, start, end)
        merged = compute_long_pnl(sdf, fdf)
        print(f"-> {len(sdf):,} straddles, {len(merged):,} with FVR match")
        if len(merged):
            frames.append(merged)

    if not frames:
        print("\nNo data. Check tickers / date range.")
        return

    df = pd.concat(frames, ignore_index=True)

    print(f"\n{'='*68}")
    print(f"  DATASET")
    print(f"{'='*68}")
    print(f"  Observations     : {len(df):,}")
    print(f"  Tickers with data: {df['ticker'].nunique()} of {len(tickers)} requested")
    absent = sorted(set(tickers) - set(df["ticker"]))
    if absent:
        print(f"  NO DATA          : {', '.join(absent)}")
    print(f"  Date range       : {df['entry_date'].min()} -> {df['entry_date'].max()}")
    print(f"  Mean DTE         : {df['dte'].mean():.1f}")
    print(f"  Mean premium     : ${df['entry_premium'].mean():.2f}/shr")
    print(f"  Mean long return : {df[Y_COL].mean():+.2f}%")
    print(f"  Median long ret  : {df[Y_COL].median():+.2f}%")
    print(f"  Long win rate    : {(df[Y_COL] > 0).mean()*100:.1f}%")
    print(f"  FVR range        : {df[FVR_COL].min():.3f} - {df[FVR_COL].max():.3f} "
          f"(mean {df[FVR_COL].mean():.3f})")

    # Headline: untrimmed.
    res = ols_with_clustered_se(df)
    print_regression(res, "UNTRIMMED - headline")
    print_buckets(bucket_analysis(df), "UNTRIMMED")

    # Sensitivity: p1/p99 trim, matching the seller study's handling.
    lo, hi = df[Y_COL].quantile(0.01), df[Y_COL].quantile(0.99)
    df_t = df[(df[Y_COL] >= lo) & (df[Y_COL] <= hi)].copy()
    print(f"\n\n  [sensitivity] p1/p99 trim removed {len(df)-len(df_t):,} rows "
          f"outside [{lo:+.1f}%, {hi:+.1f}%]")
    print(f"  NOTE: this deletes the long straddle's right tail. Compare, don't rely on it.")
    res_t = ols_with_clustered_se(df_t)
    print_regression(res_t, "p1/p99 TRIMMED - sensitivity only")
    print_buckets(bucket_analysis(df_t), "p1/p99 TRIMMED")

    print_per_ticker(per_ticker_corr(df))

    if args.csv:
        df.to_csv(OUT_CSV, index=False)
        print(f"\n  Dataset saved -> {OUT_CSV}  ({len(df):,} rows)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Iron Butterfly Study — delta sweep + FVR regression

Uses silver.option_legs_settled cache: loads all legs ONCE, then assembles
each wing delta variant locally in pandas (no per-variant Athena queries).

For each wing delta in [0.05, 0.10, 0.15, 0.20]:
  1. Assemble iron butterfly trades from cache (pandas join, instant)
  2. Compute ROC on max-loss basis
  3. Join fvr_put_30_90 from silver.fwd_vol_daily
  4. Normalize ROC per-ticker (z-score) to remove cross-ticker IV differences
  5. Logistic regression: P(win) ~ fvr_put_30_90
  6. OLS regression: normalized_roc ~ fvr_put_30_90
  7. FVR bucket analysis
  8. Walk-forward IS (2018–2022) / OOS (2023+) split

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_iron_butterfly_study.py

  # Single wing delta:
  ... run_iron_butterfly_study.py --wing-deltas 0.10

  # Specific tickers:
  ... run_iron_butterfly_study.py --tickers SPY QQQ AAPL --wing-deltas 0.10 0.15

  # Save CSV per wing delta:
  ... run_iron_butterfly_study.py --csv

Requires: AWS_PROFILE=clarinut-gmerton, MYSQL_PASSWORD=cthekb23
"""

from __future__ import annotations

import argparse
import os
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats
import awswrangler as wr

from lib.mysql_lib import _get_engine
from lib.studies.iron_butterfly_study import (
    assemble_iron_fly,
    compute_roc,
    load_legs_from_cache,
)

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_WING_DELTAS = [0.05, 0.10, 0.15, 0.20]
DEFAULT_START       = date(2018, 1, 1)
OOS_START           = date(2023, 1, 1)
MIN_TICKER_N        = 10
LEG_BATCH_SIZE      = 50    # tickers per cache query (Glue is fast; use large batches)
FVR_BATCH_SIZE      = 100


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_all_legs(
    tickers: list[str],
    start: date,
    end: date,
    batch_size: int = LEG_BATCH_SIZE,
) -> pd.DataFrame:
    """Load all option legs from cache in batches. Returns combined DataFrame."""
    frames = []
    n_batches = (len(tickers) + batch_size - 1) // batch_size
    for i in range(0, len(tickers), batch_size):
        batch     = tickers[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  [legs {batch_num}/{n_batches}] {batch[0]}…{batch[-1]}", flush=True)
        df = load_legs_from_cache(batch, start, end)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    print(f"  → {len(out):,} total legs loaded  "
          f"({out['ticker'].nunique():,} tickers, "
          f"{out['entry_date'].nunique():,} unique entry dates)")
    return out


def load_all_fvr(
    tickers: list[str],
    start: date,
    end: date,
    batch_size: int = FVR_BATCH_SIZE,
) -> pd.DataFrame:
    """Load fvr_put_30_90 from silver.fwd_vol_daily in batches."""
    frames = []
    for i in range(0, len(tickers), batch_size):
        batch     = tickers[i : i + batch_size]
        tickers_sql = ", ".join(f"'{t}'" for t in batch)
        df = wr.athena.read_sql_query(
            sql=f"""
            SELECT ticker, trade_date, fvr_put_30_90
            FROM silver.fwd_vol_daily
            WHERE ticker IN ({tickers_sql})
              AND trade_date >= DATE '{start.isoformat()}'
              AND trade_date <= DATE '{end.isoformat()}'
              AND fvr_put_30_90 > 0
            """,
            database="silver",
            workgroup="dev-v3",
            s3_output="s3://athena-919061006621/",
        )
        if not df.empty:
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"trade_date": "entry_date"})
    print(f"  → {len(out):,} FVR rows  ({out['ticker'].nunique():,} tickers)")
    return out


# ── Per-ticker normalization ──────────────────────────────────────────────────

def normalize_roc(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score ROC within each ticker. Drops tickers with < MIN_TICKER_N trades."""
    out = df.copy()
    out["roc_norm"] = np.nan
    for ticker, grp in out.groupby("ticker"):
        if len(grp) < MIN_TICKER_N:
            continue
        mu, std = grp["roc"].mean(), grp["roc"].std()
        if std > 0:
            out.loc[grp.index, "roc_norm"] = (grp["roc"] - mu) / std
    n_dropped = out["roc_norm"].isna().sum()
    print(f"  [normalize] {len(out) - n_dropped:,} rows normalized  "
          f"({n_dropped:,} dropped — tickers with n < {MIN_TICKER_N})")
    return out.dropna(subset=["roc_norm"])


# ── Regression helpers ────────────────────────────────────────────────────────

def _sig(p: float) -> str:
    return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))


def run_logistic(df: pd.DataFrame, x_col: str = "fvr_put_30_90") -> dict:
    """Logistic regression: P(win) ~ FVR via statsmodels."""
    try:
        import statsmodels.api as sm
        X = sm.add_constant(df[x_col].values.astype(float))
        y = df["win"].values.astype(int)
        model   = sm.Logit(y, X).fit(disp=False)
        coef    = model.params[1]
        pval    = model.pvalues[1]
        mean_fvr = float(df[x_col].mean())
        return {
            "coef":      coef,
            "p_value":   pval,
            "p_at_mean": float(model.predict([[1, mean_fvr]])[0]),
            "p_lo":      float(model.predict([[1, 0.75]])[0]),
            "p_hi":      float(model.predict([[1, 1.35]])[0]),
            "n":         len(df),
        }
    except Exception as e:
        return {"error": str(e), "n": len(df)}


def run_ols_norm(df: pd.DataFrame, x_col: str = "fvr_put_30_90") -> dict:
    """OLS: normalized_roc ~ FVR."""
    x = df[x_col].values.astype(float)
    y = df["roc_norm"].values.astype(float)
    slope, intercept, r, p, se = stats.linregress(x, y)
    rho, p_spearman = stats.spearmanr(x, y)
    return {
        "n": len(df), "slope": slope, "intercept": intercept,
        "pearson_r": r, "r2": r**2, "p_ols": p,
        "spearman_r": rho, "p_spearman": p_spearman,
    }


def bucket_analysis(df: pd.DataFrame, x_col: str = "fvr_put_30_90") -> pd.DataFrame:
    bins   = [0, 0.80, 0.90, 1.00, 1.10, 1.20, np.inf]
    labels = ["<0.80", "0.80–0.90", "0.90–1.00", "1.00–1.10", "1.10–1.20", "≥1.20"]
    tmp = df.copy()
    tmp["fvr_bucket"] = pd.cut(tmp[x_col], bins=bins, labels=labels)
    return (
        tmp.groupby("fvr_bucket", observed=True)
        .agg(
            n          = ("roc", "count"),
            mean_roc   = ("roc", "mean"),
            median_roc = ("roc", "median"),
            win_rate   = ("win", "mean"),
            sharpe     = ("roc", lambda x: x.mean() / x.std() if x.std() > 0 else 0),
        )
        .reset_index()
    )


# ── Per-wing-delta analysis ───────────────────────────────────────────────────

def analyze_wing(df: pd.DataFrame, wing_delta: float, oos_start: date) -> dict:
    label = f"{int(wing_delta*100)}Δ"

    print(f"\n{'='*65}")
    print(f"  WING DELTA: {label}  (N={len(df):,}, tickers={df['ticker'].nunique():,})")
    print(f"{'='*65}")

    sharpe = df["roc"].mean() / df["roc"].std() if df["roc"].std() > 0 else 0
    print(f"\n  Net credit    : ${df['net_credit'].mean():.3f}/shr avg  "
          f"(range ${df['net_credit'].min():.3f}–${df['net_credit'].max():.3f})")
    print(f"  Wing width    : ${df['wing_width'].mean():.2f}/shr avg")
    print(f"  Max loss      : ${df['max_loss'].mean():.2f}/shr avg")
    print(f"  ROC (avg)     : {df['roc'].mean():+.2f}%")
    print(f"  ROC (median)  : {df['roc'].median():+.2f}%")
    print(f"  Win rate      : {df['win'].mean()*100:.1f}%")
    print(f"  Sharpe (ROC)  : {sharpe:.4f}")

    has_fvr = "fvr_put_30_90" in df.columns and df["fvr_put_30_90"].notna().sum() > 50

    if has_fvr:
        fvr_df = df.dropna(subset=["fvr_put_30_90"])
        print(f"  FVR range     : {fvr_df['fvr_put_30_90'].min():.3f}–"
              f"{fvr_df['fvr_put_30_90'].max():.3f}  (mean {fvr_df['fvr_put_30_90'].mean():.3f})")

    df_norm = normalize_roc(df)

    log_res, ols_res = {}, {}
    if has_fvr:
        fvr_norm = df_norm.dropna(subset=["fvr_put_30_90"])

        print(f"\n  --- Logistic regression: P(win) ~ fvr_put_30_90 ---")
        log_res = run_logistic(fvr_df)
        if "error" not in log_res:
            print(f"  Coef (β)       : {log_res['coef']:+.4f}  [{_sig(log_res['p_value'])}]")
            print(f"  p-value        : {log_res['p_value']:.4e}")
            print(f"  P(win|FVR=0.75): {log_res['p_lo']*100:.1f}%  (backwardation)")
            print(f"  P(win|FVR=mean): {log_res['p_at_mean']*100:.1f}%")
            print(f"  P(win|FVR=1.35): {log_res['p_hi']*100:.1f}%  (contango)")
        else:
            print(f"  Error: {log_res['error']}")
            log_res = {}

        print(f"\n  --- OLS: normalized_roc ~ fvr_put_30_90 ---")
        ols_res = run_ols_norm(fvr_norm)
        print(f"  N (normalized) : {ols_res['n']:,}")
        print(f"  Slope (β)      : {ols_res['slope']:+.4f}  [{_sig(ols_res['p_ols'])}]")
        print(f"  R²             : {ols_res['r2']:.4f}")
        print(f"  Spearman ρ     : {ols_res['spearman_r']:+.4f}  [{_sig(ols_res['p_spearman'])}]")

        print(f"\n  --- FVR bucket analysis ---")
        bkt = bucket_analysis(fvr_df)
        print(f"  {'Bucket':<12}  {'N':>6}  {'Mean ROC%':>10}  {'Median%':>9}  {'Win%':>7}  {'Sharpe':>8}")
        print(f"  {'-'*60}")
        for _, row in bkt.iterrows():
            print(f"  {str(row['fvr_bucket']):<12}  {int(row['n']):>6}  "
                  f"{row['mean_roc']:>+10.2f}  {row['median_roc']:>+9.2f}  "
                  f"{row['win_rate']*100:>6.1f}%  {row['sharpe']:>8.4f}")

    print(f"\n  --- Walk-forward: IS (2018–2022) vs OOS (2023+) ---")
    is_df  = df[df["entry_date"] < oos_start]
    oos_df = df[df["entry_date"] >= oos_start]
    for lbl, wf in [("IS ", is_df), ("OOS", oos_df)]:
        if not len(wf):
            continue
        wf_sharpe = wf["roc"].mean() / wf["roc"].std() if wf["roc"].std() > 0 else 0
        print(f"  {lbl}: N={len(wf):>5,}  "
              f"avg_roc={wf['roc'].mean():>+7.2f}%  "
              f"win={wf['win'].mean()*100:.1f}%  "
              f"sharpe={wf_sharpe:.4f}")

    return {
        "wing_delta": wing_delta,
        "n":          len(df),
        "tickers":    df["ticker"].nunique(),
        "avg_roc":    df["roc"].mean(),
        "median_roc": df["roc"].median(),
        "win_rate":   df["win"].mean(),
        "sharpe":     sharpe,
        "spearman_r": ols_res.get("spearman_r", float("nan")),
        "p_spearman": ols_res.get("p_spearman", float("nan")),
        "p_win_lo":   log_res.get("p_lo",       float("nan")),
        "p_win_hi":   log_res.get("p_hi",       float("nan")),
    }


# ── Comparison table ──────────────────────────────────────────────────────────

def print_comparison(summaries: list[dict]) -> None:
    print(f"\n{'='*75}")
    print(f"  WING DELTA COMPARISON SUMMARY")
    print(f"{'='*75}")
    print(f"  {'Delta':<8}  {'N':>7}  {'Tickers':>7}  {'Avg ROC%':>9}  "
          f"{'Win%':>6}  {'Sharpe':>8}  {'Spearman ρ':>12}  {'P(win) bkwd→cntg':>18}")
    print(f"  {'-'*75}")
    for s in summaries:
        label   = f"{int(s['wing_delta']*100)}Δ"
        sig     = _sig(s["p_spearman"])
        p_range = (f"{s['p_win_lo']*100:.1f}% → {s['p_win_hi']*100:.1f}%"
                   if not np.isnan(s["p_win_lo"]) else "N/A")
        print(f"  {label:<8}  {s['n']:>7,}  {s['tickers']:>7,}  "
              f"{s['avg_roc']:>+9.2f}  {s['win_rate']*100:>5.1f}%  "
              f"{s['sharpe']:>8.4f}  "
              f"{s['spearman_r']:>+8.4f} [{sig}]  {p_range:>18}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Iron butterfly study — cache-based delta sweep + FVR regression"
    )
    parser.add_argument("--wing-deltas", nargs="+", type=float,
                        default=DEFAULT_WING_DELTAS,
                        help="Wing delta(s) to test (default: 0.05 0.10 0.15 0.20)")
    parser.add_argument("--tickers",     nargs="+", default=None)
    parser.add_argument("--ticker-file", type=str,  default=None)
    parser.add_argument("--start",       type=str,  default=None)
    parser.add_argument("--end",         type=str,  default=None)
    parser.add_argument("--csv", action="store_true",
                        help="Save merged dataset to iron_fly_<delta>.csv per wing delta")
    args = parser.parse_args()

    # ── Ticker list ───────────────────────────────────────────────────────────
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

    print(f"Iron Butterfly Study — cache-based delta sweep")
    print(f"  tickers    : {len(tickers)}")
    print(f"  date range : {start} → {end}")
    print(f"  wing deltas: {args.wing_deltas}")

    # ── Load legs + FVR once ──────────────────────────────────────────────────
    print(f"\n--- Loading option legs from cache ---")
    legs = load_all_legs(tickers, start, end)
    if legs.empty:
        print("No leg data found. Exiting.")
        return

    print(f"\n--- Loading FVR data ---")
    fvr = load_all_fvr(tickers, start, end)

    # ── Loop wing deltas (all local from here) ────────────────────────────────
    summaries = []

    for wing_delta in args.wing_deltas:
        label = f"{int(wing_delta*100)}Δ"
        print(f"\n{'#'*65}")
        print(f"  Assembling wing delta {label}  (pandas, no Athena)")
        print(f"{'#'*65}")

        raw = assemble_iron_fly(legs, wing_delta)
        if raw.empty:
            print(f"  No trades assembled for {label}. Skipping.")
            continue

        df = compute_roc(raw)
        if df.empty:
            print(f"  No valid trades after P&L compute for {label}. Skipping.")
            continue

        print(f"  Assembled {len(df):,} trades  ({df['ticker'].nunique():,} tickers)")

        # Join FVR
        if not fvr.empty:
            df = df.merge(fvr, on=["ticker", "entry_date"], how="left")
            n_fvr = df["fvr_put_30_90"].notna().sum()
            print(f"  FVR joined: {n_fvr:,} / {len(df):,} trades have FVR")

        if args.csv:
            path = f"iron_fly_{label}.csv"
            df.to_csv(path, index=False)
            print(f"  Dataset saved → {path}")

        summary = analyze_wing(df, wing_delta, OOS_START)
        summaries.append(summary)

    if len(summaries) > 1:
        print_comparison(summaries)

    if summaries:
        best = max(summaries, key=lambda s: s["sharpe"])
        print(f"\n  Best Sharpe: {int(best['wing_delta']*100)}Δ wings  "
              f"(Sharpe={best['sharpe']:.4f}, "
              f"avg_roc={best['avg_roc']:+.2f}%, "
              f"win={best['win_rate']*100:.1f}%)")


if __name__ == "__main__":
    main()

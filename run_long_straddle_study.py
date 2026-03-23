#!/usr/bin/env python3
"""
Long Straddle Study — buyer perspective, hold to expiry.

Structure:
  Buy 1x ATM call (~50Δ)
  Buy 1x ATM put  (~50Δ)  ← same strike, same expiry

P&L:
  cost   = call_mid + put_mid          (debit paid)
  payout = call_last_expiry + put_last_expiry
  profit = payout - cost
  roc    = profit / cost × 100         (positive = buyer profit)
  win    = profit > 0                  (stock moved enough to cover premium)

Entry: Friday, ~10 DTE, |delta - 0.50| ≤ 0.08, bid>0/ask>0/OI>0, BA ≤ 35%
Exit:  Hold to expiry

Uses silver.option_legs_settled cache.

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_long_straddle_study.py
  ... --fvr-min 1.20    # only enter in contango
  ... --csv             # save per-ticker breakdown
"""

from __future__ import annotations

import argparse
import os
from datetime import date

import numpy as np
import pandas as pd
import awswrangler as wr

from lib.mysql_lib import _get_engine
from lib.studies.iron_fly_features import compute_ivr
from lib.studies.iron_butterfly_study import load_legs_from_cache

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_START  = date(2018, 1, 1)
OOS_START      = date(2023, 1, 1)
BODY_DELTA     = 0.50
BODY_TOL       = 0.08
MIN_N          = 15
LEG_BATCH_SIZE = 50
FVR_BATCH_SIZE = 100


# ── Straddle assembly ─────────────────────────────────────────────────────────

def assemble_long_straddle(
    legs: pd.DataFrame,
    body_delta: float = BODY_DELTA,
    body_tol:   float = BODY_TOL,
    min_cost:   float = 0.05,
) -> pd.DataFrame:
    """
    Assemble long straddle trades from pre-loaded leg cache.

    For each (ticker, entry_date, expiry):
      1. Best ATM call: delta closest to +body_delta (within ±body_tol)
      2. Matching put at same strike: delta closest to -body_delta

    Returns DataFrame ready for compute_roc_buyer().
    """
    if legs.empty:
        return pd.DataFrame()

    KEY = ["ticker", "entry_date", "expiry"]

    calls = legs[legs["cp"] == "C"].copy()
    puts  = legs[legs["cp"] == "P"].copy()

    # Best ATM call per (ticker, entry_date, expiry)
    atm_c = calls[
        (calls["delta"] >= body_delta - body_tol) &
        (calls["delta"] <= body_delta + body_tol)
    ].copy()
    atm_c["_err"] = (atm_c["delta"] - body_delta).abs()
    atm_c = (
        atm_c.sort_values("_err")
        .groupby(KEY, sort=False).first().reset_index()
        .rename(columns={
            "strike":      "atm_strike",
            "delta":       "call_delta",
            "mid_entry":   "call_mid",
            "last_expiry": "call_last_exp",
        })
        [KEY + ["atm_strike", "dte", "call_delta", "call_mid", "call_last_exp"]]
    )

    # Matching ATM put at same strike
    atm_p = puts[
        (puts["delta"] >= -(body_delta + body_tol)) &
        (puts["delta"] <= -(body_delta - body_tol))
    ].copy()
    atm_p["_err"] = (atm_p["delta"] + body_delta).abs()
    atm_p = (
        atm_p.sort_values("_err")
        .groupby(KEY + ["strike"], sort=False).first().reset_index()
        .rename(columns={
            "delta":       "put_delta",
            "mid_entry":   "put_mid",
            "last_expiry": "put_last_exp",
        })
        [KEY + ["strike", "put_delta", "put_mid", "put_last_exp"]]
    )

    out = atm_c.merge(
        atm_p.rename(columns={"strike": "atm_strike"}),
        on=KEY + ["atm_strike"],
        how="inner",
    )
    out["cost"]   = out["call_mid"] + out["put_mid"]
    out["payout"] = out["call_last_exp"] + out["put_last_exp"]
    return out[out["cost"] >= min_cost].reset_index(drop=True)


def compute_roc_buyer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute profit and ROC from the buyer's perspective.

    profit = payout - cost
    roc    = profit / cost × 100   (positive = buyer wins)
    win    = profit > 0
    """
    if df.empty:
        return df
    out = df.copy()
    out = out.dropna(subset=["payout", "cost"])
    out = out[out["cost"] > 0]
    out["profit"] = out["payout"] - out["cost"]
    out["roc"]    = out["profit"] / out["cost"] * 100
    out["win"]    = (out["profit"] > 0).astype(int)
    return out.reset_index(drop=True)


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_all_legs(tickers, start, end):
    frames = []
    n = (len(tickers) + LEG_BATCH_SIZE - 1) // LEG_BATCH_SIZE
    for i in range(0, len(tickers), LEG_BATCH_SIZE):
        batch = tickers[i : i + LEG_BATCH_SIZE]
        print(f"  [legs {i//LEG_BATCH_SIZE+1}/{n}] {batch[0]}…{batch[-1]}", flush=True)
        df = load_legs_from_cache(batch, start, end)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    print(f"  → {len(out):,} legs  ({out['ticker'].nunique():,} tickers)")
    return out


def load_all_fvr(tickers, start, end):
    frames = []
    for i in range(0, len(tickers), FVR_BATCH_SIZE):
        batch = tickers[i : i + FVR_BATCH_SIZE]
        tickers_sql = ", ".join(f"'{t}'" for t in batch)
        df = wr.athena.read_sql_query(
            sql=f"""
            SELECT ticker, trade_date, fvr_put_30_90, iv_put_30
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
    out = pd.concat(frames, ignore_index=True).rename(columns={"trade_date": "entry_date"})
    print(f"  → {len(out):,} FVR rows  ({out['ticker'].nunique():,} tickers)")
    return out


# ── Per-ticker analysis ───────────────────────────────────────────────────────

def per_ticker_stats(df: pd.DataFrame, min_n: int = MIN_N) -> pd.DataFrame:
    rows = []
    for ticker, grp in df.groupby("ticker"):
        if len(grp) < min_n:
            continue
        avg = grp["roc"].mean()
        med = grp["roc"].median()
        win = grp["win"].mean()
        std = grp["roc"].std()
        sh  = avg / std if std > 0 else 0
        oos = grp[grp["entry_date"] >= OOS_START]
        rows.append({
            "ticker":       ticker,
            "n":            len(grp),
            "n_oos":        len(oos),
            "avg_roc":      avg,
            "median_roc":   med,
            "win_rate":     win,
            "sharpe":       sh,
            "oos_avg_roc":  oos["roc"].mean()  if len(oos) >= 5 else np.nan,
            "oos_win_rate": oos["win"].mean()  if len(oos) >= 5 else np.nan,
        })
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)


def print_leaderboard(tk: pd.DataFrame, label: str, top_n: int = 40) -> None:
    good = tk[(tk["avg_roc"] > 0) & (tk["win_rate"] > 0.40) & (tk["sharpe"] > 0)]
    print(f"\n  Per-ticker leaderboard — {label}  (n ≥ {MIN_N}, sorted by Sharpe)")
    print(f"  {'Ticker':<8}  {'N':>5}  {'Avg ROC%':>9}  {'Median%':>8}  "
          f"{'Win%':>7}  {'Sharpe':>8}  {'OOS ROC%':>9}  {'OOS Win%':>9}")
    print(f"  {'-'*76}")
    for _, row in tk.head(top_n).iterrows():
        oos_roc = f"{row['oos_avg_roc']:>+9.2f}" if not np.isnan(row["oos_avg_roc"]) else "       N/A"
        oos_win = f"{row['oos_win_rate']*100:>8.1f}%" if not np.isnan(row["oos_win_rate"]) else "      N/A"
        marker  = " ✓" if row["ticker"] in good["ticker"].values else ""
        print(f"  {row['ticker']:<8}  {int(row['n']):>5}  "
              f"{row['avg_roc']:>+9.2f}  {row['median_roc']:>+8.2f}  "
              f"{row['win_rate']*100:>6.1f}%  {row['sharpe']:>8.4f}  "
              f"{oos_roc}  {oos_win}{marker}")
    print(f"\n  Recommended ({len(good)} tickers, avg_roc>0, win>40%, Sharpe>0):")
    print(f"  {', '.join(good['ticker'].tolist())}")


def print_summary(df: pd.DataFrame, label: str) -> None:
    if df.empty:
        print(f"  [{label}] no data")
        return
    sh = df["roc"].mean() / df["roc"].std() if df["roc"].std() > 0 else 0
    is_df  = df[df["entry_date"] <  OOS_START]
    oos_df = df[df["entry_date"] >= OOS_START]
    print(f"  [{label}]")
    print(f"    All : N={len(df):>6,}  tickers={df['ticker'].nunique():>4,}  "
          f"avg_roc={df['roc'].mean():>+7.2f}%  median={df['roc'].median():>+7.2f}%  "
          f"win={df['win'].mean()*100:.1f}%  sharpe={sh:.4f}")
    if len(is_df):
        sh_is = is_df["roc"].mean() / is_df["roc"].std() if is_df["roc"].std() > 0 else 0
        print(f"    IS  : N={len(is_df):>6,}  avg_roc={is_df['roc'].mean():>+7.2f}%  "
              f"win={is_df['win'].mean()*100:.1f}%  sharpe={sh_is:.4f}")
    if len(oos_df):
        sh_oos = oos_df["roc"].mean() / oos_df["roc"].std() if oos_df["roc"].std() > 0 else 0
        print(f"    OOS : N={len(oos_df):>6,}  avg_roc={oos_df['roc'].mean():>+7.2f}%  "
              f"win={oos_df['win'].mean()*100:.1f}%  sharpe={sh_oos:.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Long straddle study — buyer, hold to expiry")
    parser.add_argument("--tickers",     nargs="+", default=None)
    parser.add_argument("--ticker-file", type=str,  default=None)
    parser.add_argument("--start",       type=str,  default=None)
    parser.add_argument("--end",         type=str,  default=None)
    parser.add_argument("--fvr-min",     type=float, default=None,
                        help="Only enter when FVR ≥ this value (e.g. 1.20 = contango filter)")
    parser.add_argument("--csv", action="store_true")
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

    print(f"Long Straddle Study — buyer, hold to expiry")
    print(f"  tickers    : {len(tickers)}")
    print(f"  date range : {start} → {end}")
    print(f"  fvr_min    : {args.fvr_min or 'none (all entries)'}")

    print(f"\n--- Loading option legs ---")
    legs = load_all_legs(tickers, start, end)
    if legs.empty:
        print("No data. Exiting.")
        return

    print(f"\n--- Loading FVR data ---")
    fvr = load_all_fvr(tickers, start, end)

    print(f"\n--- Assembling long straddles ---")
    raw = assemble_long_straddle(legs)
    if raw.empty:
        print("No straddles assembled.")
        return
    df = compute_roc_buyer(raw)
    print(f"  {len(df):,} trades  ({df['ticker'].nunique():,} tickers)")

    # Join FVR + compute IVR
    if not fvr.empty:
        # IVR: percentile rank of iv_put_30 over trailing 252 days per ticker
        ivr_df = compute_ivr(fvr)
        df = df.merge(
            fvr[["ticker", "entry_date", "fvr_put_30_90"]],
            on=["ticker", "entry_date"], how="left",
        )
        df = df.merge(
            ivr_df[["ticker", "entry_date", "ivr_30"]],
            on=["ticker", "entry_date"], how="left",
        )

    print(f"\n{'='*70}")
    print(f"  OVERALL — unfiltered")
    print(f"{'='*70}")
    print_summary(df, "all entries")

    # FVR bucket breakdown
    if "fvr_put_30_90" in df.columns:
        has_fvr = df.dropna(subset=["fvr_put_30_90"])
        bins   = [0, 0.80, 0.90, 1.00, 1.10, 1.20, np.inf]
        labels = ["<0.80", "0.80–0.90", "0.90–1.00", "1.00–1.10", "1.10–1.20", "≥1.20"]
        has_fvr = has_fvr.copy()
        has_fvr["fvr_bucket"] = pd.cut(has_fvr["fvr_put_30_90"], bins=bins, labels=labels)
        bkt = (
            has_fvr.groupby("fvr_bucket", observed=True)
            .agg(n=("roc","count"), avg_roc=("roc","mean"),
                 median_roc=("roc","median"), win_rate=("win","mean"),
                 sharpe=("roc", lambda x: x.mean()/x.std() if x.std()>0 else 0))
            .reset_index()
        )
        print(f"\n  FVR bucket breakdown (buyer perspective):")
        print(f"  {'Bucket':<12}  {'N':>7}  {'Avg ROC%':>9}  {'Median%':>8}  {'Win%':>7}  {'Sharpe':>8}")
        print(f"  {'-'*58}")
        for _, row in bkt.iterrows():
            print(f"  {str(row['fvr_bucket']):<12}  {int(row['n']):>7,}  "
                  f"{row['avg_roc']:>+9.2f}  {row['median_roc']:>+8.2f}  "
                  f"{row['win_rate']*100:>6.1f}%  {row['sharpe']:>8.4f}")

    # Apply FVR filter if requested
    df_filtered = df
    filter_label = "all entries"
    if args.fvr_min is not None and "fvr_put_30_90" in df.columns:
        df_filtered = df.dropna(subset=["fvr_put_30_90"])
        df_filtered = df_filtered[df_filtered["fvr_put_30_90"] >= args.fvr_min]
        filter_label = f"FVR ≥ {args.fvr_min}"
        print(f"\n{'='*70}")
        print(f"  FVR ≥ {args.fvr_min} filter")
        print(f"{'='*70}")
        print_summary(df_filtered, filter_label)

    # Per-ticker leaderboard
    print(f"\n{'='*70}")
    tk = per_ticker_stats(df_filtered)
    print_leaderboard(tk, filter_label)

    if args.csv:
        path = f"long_straddle_tickers{'_fvr' + str(args.fvr_min) if args.fvr_min else ''}.csv"
        tk.to_csv(path, index=False)
        print(f"\n  Per-ticker stats saved → {path}")


if __name__ == "__main__":
    main()

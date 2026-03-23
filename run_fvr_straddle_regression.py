#!/usr/bin/env python3
"""
FVR → Short Straddle P&L Regression Study

Tests whether forward vol ratios measured on the entry date predict the profit
of a 10-DTE short ATM straddle held to expiry.  Compares two intervals:
  - fvr_put_10_30 : 10→30d ratio (matches straddle DTE; hypothesis: stronger signal)
  - fvr_put_30_90 : 30→90d ratio (original study baseline)

Entry  : Friday, ~10 DTE ATM straddle (short call + short put, same strike)
Exit   : hold to expiry; payout = call_last_expiry + put_last_expiry
Y      : profit_pct_seller = (entry_premium − payout) / entry_premium × 100
           100% → straddle expires worthless (full profit for seller)
             0% → break-even
           <  0% → loss for seller

Liquidity filters:
  - bid > 0, ask > 0, open_interest > 0 on entry day, both legs
  - bid-ask spread ≤ 35% of mid per leg
  - |delta ∓ 0.50| ≤ 0.08 per leg
  - entry_premium > 0

Usage
-----
  # Full universe (987 tickers), 2018–today:
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \\
      PYTHONPATH=src .venv/bin/python3 run_fvr_straddle_regression.py

  # Specific tickers:
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \\
      PYTHONPATH=src .venv/bin/python3 run_fvr_straddle_regression.py \\
      --tickers AAPL MSFT NVDA

  # Save full dataset to CSV:
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=cthekb23 \\
      PYTHONPATH=src .venv/bin/python3 run_fvr_straddle_regression.py --csv
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
import awswrangler as wr

from lib.athena_lib import athena
from lib.constants import DB, TABLE
from lib.mysql_lib import _get_engine

# ── Config ────────────────────────────────────────────────────────────────────

DTE_TARGET    = 10
DTE_TOL       = 5       # accept DTE in [5, 15]
DELTA_TOL     = 0.08    # |delta ∓ 0.50| ≤ this
BA_MAX        = 0.35    # max bid-ask spread as fraction of mid
BATCH_SIZE    = 20      # tickers per Athena query
DEFAULT_START = date(2018, 1, 1)
MIN_TICKER_N  = 10      # min observations for per-ticker regression

# ── Athena straddle query ─────────────────────────────────────────────────────

def _straddle_sql(tickers: list[str], start: date, end: date) -> str:
    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    dte_lo = DTE_TARGET - DTE_TOL
    dte_hi = DTE_TARGET + DTE_TOL

    return f"""
    WITH
    -- Step 1: find the best ATM call per (ticker, entry_date) on Fridays
    call_cand AS (
      SELECT
        trade_date AS entry_date,
        expiry, ticker, strike,
        (bid + ask) / 2.0                               AS call_mid,
        delta                                            AS call_delta,
        date_diff('day', trade_date, expiry)             AS dte_val,
        ABS(date_diff('day', trade_date, expiry) - {DTE_TARGET}) AS dte_err
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (
            PARTITION BY ticker, trade_date, strike, expiry
            ORDER BY open_interest DESC NULLS LAST, bid DESC
          ) AS dedup_rn
        FROM "{DB}"."{TABLE}"
        WHERE ticker IN ({tickers_sql})
          AND cp = 'C'
          AND trade_date >= TIMESTAMP '{start.isoformat()} 00:00:00'
          AND trade_date <= TIMESTAMP '{end.isoformat()} 00:00:00'
          AND bid > 0 AND ask > 0 AND open_interest > 0
          AND (ask - bid) / ((ask + bid) / 2.0) <= {BA_MAX}
          AND delta IS NOT NULL
          AND ABS(delta - 0.50) <= {DELTA_TOL}
          AND day_of_week(trade_date) = 5
      ) deduped
      WHERE dedup_rn = 1
        AND date_diff('day', trade_date, expiry) BETWEEN {dte_lo} AND {dte_hi}
    ),
    call_leg AS (
      SELECT entry_date, expiry, ticker, strike, call_mid, call_delta, dte_val
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (
            PARTITION BY ticker, entry_date
            ORDER BY dte_err, ABS(call_delta - 0.50)
          ) AS rn
        FROM call_cand
      ) ranked
      WHERE rn = 1
    ),
    -- Step 2: find put at the SAME strike and expiry as the chosen call
    put_leg AS (
      SELECT o.trade_date AS entry_date, o.expiry, o.ticker, o.strike,
             (o.bid + o.ask) / 2.0 AS put_mid,
             o.delta AS put_delta
      FROM "{DB}"."{TABLE}" o
      JOIN call_leg c
        ON o.ticker     = c.ticker
       AND o.trade_date = c.entry_date
       AND o.expiry     = c.expiry
       AND o.strike     = c.strike
      WHERE o.cp = 'P'
        AND o.bid > 0 AND o.ask > 0
        AND (o.ask - o.bid) / ((o.ask + o.bid) / 2.0) <= {BA_MAX}
        AND ABS(o.delta + 0.50) <= {DELTA_TOL}
    ),
    -- Step 3: combine into straddle entry
    straddle AS (
      SELECT
        c.ticker, c.entry_date, c.expiry, c.strike, c.dte_val AS dte,
        c.call_mid, c.call_delta,
        p.put_mid,  p.put_delta,
        c.call_mid + p.put_mid AS entry_premium
      FROM call_leg c
      JOIN put_leg p
        ON c.ticker = p.ticker AND c.entry_date = p.entry_date
       AND c.expiry = p.expiry AND c.strike = p.strike
      WHERE c.call_mid + p.put_mid > 0
    ),
    -- Step 4: look up settlement prices on expiry date
    call_exp AS (
      SELECT o.ticker, o.expiry, o.strike,
             MAX(COALESCE(o.last, 0)) AS call_last_exp
      FROM "{DB}"."{TABLE}" o
      JOIN straddle s
        ON o.ticker = s.ticker AND o.expiry = s.expiry AND o.strike = s.strike
      WHERE o.cp = 'C'
        AND o.trade_date = o.expiry
      GROUP BY o.ticker, o.expiry, o.strike
    ),
    put_exp AS (
      SELECT o.ticker, o.expiry, o.strike,
             MAX(COALESCE(o.last, 0)) AS put_last_exp
      FROM "{DB}"."{TABLE}" o
      JOIN straddle s
        ON o.ticker = s.ticker AND o.expiry = s.expiry AND o.strike = s.strike
      WHERE o.cp = 'P'
        AND o.trade_date = o.expiry
      GROUP BY o.ticker, o.expiry, o.strike
    )
    SELECT
      s.ticker, s.entry_date, s.expiry, s.strike, s.dte,
      s.call_mid, s.put_mid, s.entry_premium,
      s.call_delta, s.put_delta,
      COALESCE(ce.call_last_exp, 0)                                AS call_last_exp,
      COALESCE(pe.put_last_exp,  0)                                AS put_last_exp,
      COALESCE(ce.call_last_exp, 0) + COALESCE(pe.put_last_exp, 0) AS payout
    FROM straddle s
    LEFT JOIN call_exp ce ON s.ticker = ce.ticker AND s.expiry = ce.expiry AND s.strike = ce.strike
    LEFT JOIN put_exp  pe ON s.ticker = pe.ticker AND s.expiry = pe.expiry AND s.strike = pe.strike
    ORDER BY s.ticker, s.entry_date
    """


def fetch_straddle_batch(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    df = athena(_straddle_sql(tickers, start, end))
    if df.empty:
        return df
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    return df


# ── FVR data from Glue ────────────────────────────────────────────────────────

def load_fvr(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    df = wr.athena.read_sql_query(
        sql=f"""
        SELECT ticker, trade_date, fvr_put_30_90, fvr_put_10_30, iv_put_30, iv_put_10
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
    return df


# ── P&L computation ───────────────────────────────────────────────────────────

def compute_pnl(straddle_df: pd.DataFrame, fvr_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge straddle trades with FVR on (ticker, entry_date) and compute
    profit_pct_seller.  Drops rows missing expiry prices or FVR.
    """
    if straddle_df.empty or fvr_df.empty:
        return pd.DataFrame()

    merged = straddle_df.merge(
        fvr_df.rename(columns={"trade_date": "entry_date"}),
        on=["ticker", "entry_date"],
        how="inner",
    )
    if merged.empty:
        return merged

    # Drop rows where payout is missing (expiry data absent) — LEFT JOIN nulls
    merged = merged.dropna(subset=["payout", "fvr_put_30_90"])
    merged = merged[merged["entry_premium"] > 0]
    # fvr_put_10_30 may be NaN (monthly-only chains) — keep rows, filter per-analysis

    merged["profit_pct_seller"] = (
        (merged["entry_premium"] - merged["payout"]) / merged["entry_premium"] * 100
    )
    return merged


# ── Analysis ──────────────────────────────────────────────────────────────────

def winsorize(df: pd.DataFrame, col: str, lo: float = 0.01, hi: float = 0.99) -> pd.DataFrame:
    """Clip col to [lo, hi] quantiles; return filtered copy."""
    lo_val = df[col].quantile(lo)
    hi_val = df[col].quantile(hi)
    out = df[(df[col] >= lo_val) & (df[col] <= hi_val)].copy()
    n_removed = len(df) - len(out)
    print(f"  [winsorize] removed {n_removed:,} outliers outside "
          f"[{lo_val:+.1f}%, {hi_val:+.1f}%]  ({n_removed/len(df)*100:.1f}% of data)")
    return out


def run_ols(df: pd.DataFrame, fvr_col: str = "fvr_put_30_90") -> dict:
    sub = df.dropna(subset=[fvr_col])
    x = sub[fvr_col].values.astype(float)
    y = sub["profit_pct_seller"].values.astype(float)
    slope, intercept, r, p, se = stats.linregress(x, y)
    rho, p_spearman = stats.spearmanr(x, y)
    return {
        "fvr_col":    fvr_col,
        "n":          len(sub),
        "slope":      slope,
        "intercept":  intercept,
        "pearson_r":  r,
        "r2":         r ** 2,
        "p_value":    p,
        "t_stat":     slope / se if se > 0 else float("nan"),
        "spearman_r": rho,
        "p_spearman": p_spearman,
    }


def bucket_analysis(df: pd.DataFrame, fvr_col: str = "fvr_put_30_90") -> pd.DataFrame:
    bins   = [0, 0.80, 0.90, 1.00, 1.10, 1.20, np.inf]
    labels = ["<0.80", "0.80–0.90", "0.90–1.00", "1.00–1.10", "1.10–1.20", "≥1.20"]
    df = df.dropna(subset=[fvr_col]).copy()
    df["fvr_bucket"] = pd.cut(df[fvr_col], bins=bins, labels=labels)
    agg = (
        df.groupby("fvr_bucket", observed=True)
        .agg(
            n              =("profit_pct_seller", "count"),
            mean_profit_pct=("profit_pct_seller", "mean"),
            median_profit  =("profit_pct_seller", "median"),
            win_rate_pct   =("profit_pct_seller", lambda x: (x > 0).mean() * 100),
            std_profit     =("profit_pct_seller", "std"),
        )
        .reset_index()
    )
    return agg


def per_ticker_corr(df: pd.DataFrame, fvr_col: str = "fvr_put_30_90") -> pd.DataFrame:
    rows = []
    sub = df.dropna(subset=[fvr_col])
    for ticker, grp in sub.groupby("ticker"):
        if len(grp) < MIN_TICKER_N:
            continue
        r, p = stats.pearsonr(grp[fvr_col], grp["profit_pct_seller"])
        rows.append({
            "ticker":    ticker,
            "n":         len(grp),
            "pearson_r": round(r, 4),
            "p_value":   round(p, 4),
            "mean_profit_pct": round(grp["profit_pct_seller"].mean(), 2),
        })
    return pd.DataFrame(rows).sort_values("pearson_r")


# ── Printing ──────────────────────────────────────────────────────────────────

def _sig(p: float) -> str:
    return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))


def print_regression(res: dict) -> None:
    col = res.get("fvr_col", "fvr_put_30_90")
    print(f"\n{'='*60}")
    print(f"  POOLED REGRESSION: profit_pct_seller ~ {col}")
    print(f"  (winsorized p1/p99 dataset)")
    print(f"{'='*60}")
    print(f"  N              : {res['n']:,}")
    print(f"  OLS slope (β)  : {res['slope']:+.4f}  [{_sig(res['p_value'])}]")
    print(f"  OLS intercept  : {res['intercept']:+.4f}")
    print(f"  t-stat         : {res['t_stat']:+.2f}")
    print(f"  p-value (OLS)  : {res['p_value']:.4e}")
    print(f"  Pearson r      : {res['pearson_r']:+.4f}")
    print(f"  R²             : {res['r2']:.4f}")
    print(f"  Spearman ρ     : {res['spearman_r']:+.4f}  [{_sig(res['p_spearman'])}]")
    print(f"  p-value (Spmn) : {res['p_spearman']:.4e}")

    dir_note = ("negative β/ρ: high FVR → less profit for seller "
                "(deep contango signals upcoming vol; sell into backwardation)"
                if res["slope"] < 0 else
                "positive β/ρ: high FVR → more profit for seller "
                "(contango favors selling near-term vol)")
    print(f"\n  Interpretation: {dir_note}")


def print_comparison(res_10_30: dict, res_30_90: dict,
                     bkt_10_30: pd.DataFrame, bkt_30_90: pd.DataFrame) -> None:
    """Side-by-side summary comparing the two FVR intervals."""
    def bucket_spread(bkt: pd.DataFrame) -> float:
        lo = bkt[bkt["fvr_bucket"] == "<0.80"]["mean_profit_pct"].values
        hi = bkt[bkt["fvr_bucket"] == "≥1.20"]["mean_profit_pct"].values
        if len(lo) and len(hi):
            return float(lo[0] - hi[0])
        return float("nan")

    def low_mean(bkt: pd.DataFrame) -> float:
        v = bkt[bkt["fvr_bucket"] == "<0.80"]["mean_profit_pct"].values
        return float(v[0]) if len(v) else float("nan")

    def high_mean(bkt: pd.DataFrame) -> float:
        v = bkt[bkt["fvr_bucket"] == "≥1.20"]["mean_profit_pct"].values
        return float(v[0]) if len(v) else float("nan")

    print(f"\n{'='*65}")
    print(f"  INTERVAL COMPARISON")
    print(f"{'='*65}")
    print(f"  {'Metric':<28}  {'fvr_put_10_30':>14}  {'fvr_put_30_90':>14}")
    print(f"  {'-'*60}")

    def row(label, v1, v2, fmt="{:>14.4f}"):
        f1 = fmt.format(v1) if not (isinstance(v1, float) and (v1 != v1)) else "       N/A    "
        f2 = fmt.format(v2) if not (isinstance(v2, float) and (v2 != v2)) else "       N/A    "
        print(f"  {label:<28}  {f1}  {f2}")

    row("N (observations)", res_10_30["n"], res_30_90["n"], fmt="{:>14,}")
    row("OLS slope (β)", res_10_30["slope"], res_30_90["slope"])
    row("Pearson r", res_10_30["pearson_r"], res_30_90["pearson_r"])
    row("R²", res_10_30["r2"], res_30_90["r2"])
    row("Spearman ρ", res_10_30["spearman_r"], res_30_90["spearman_r"])
    row("p (OLS)", res_10_30["p_value"], res_30_90["p_value"])
    row("p (Spearman)", res_10_30["p_spearman"], res_30_90["p_spearman"])
    row("Low FVR mean% (<0.80)", low_mean(bkt_10_30),  low_mean(bkt_30_90),  fmt="{:>13.1f}%")
    row("High FVR mean% (≥1.20)", high_mean(bkt_10_30), high_mean(bkt_30_90), fmt="{:>13.1f}%")
    row("Bucket spread (pp)", bucket_spread(bkt_10_30), bucket_spread(bkt_30_90), fmt="{:>13.1f}p")
    print(f"  {'-'*60}")
    winner = "fvr_put_10_30" if abs(res_10_30["spearman_r"]) > abs(res_30_90["spearman_r"]) else "fvr_put_30_90"
    print(f"  Stronger Spearman ρ : {winner}")


def print_buckets(bkt: pd.DataFrame, fvr_col: str = "fvr_put_30_90") -> None:
    print(f"\n{'='*60}")
    print(f"  PERFORMANCE BY FVR BUCKET  ({fvr_col})")
    print(f"{'='*60}")
    print(f"  {'FVR bucket':<12}  {'N':>6}  {'Mean%':>8}  {'Median%':>8}  {'Win%':>7}  {'Std':>7}")
    print(f"  {'-'*56}")
    for _, row in bkt.iterrows():
        print(f"  {str(row['fvr_bucket']):<12}  {int(row['n']):>6}  "
              f"{row['mean_profit_pct']:>+8.2f}  {row['median_profit']:>+8.2f}  "
              f"{row['win_rate_pct']:>6.1f}%  {row['std_profit']:>7.2f}")


def print_per_ticker(corr_df: pd.DataFrame, top_n: int = 15) -> None:
    print(f"\n{'='*60}")
    print(f"  PER-TICKER PEARSON r  (FVR vs seller profit_pct)")
    print(f"{'='*60}")
    print(f"  --- Most NEGATIVE r (FVR strongly predicts lower seller profit) ---")
    neg = corr_df[corr_df["pearson_r"] < 0].head(top_n)
    for _, row in neg.iterrows():
        sig = "**" if row["p_value"] < 0.01 else ("*" if row["p_value"] < 0.05 else "")
        print(f"    {row['ticker']:<8}  r={row['pearson_r']:+.3f}{sig}  "
              f"n={row['n']:>4}  mean_profit={row['mean_profit_pct']:+.1f}%")
    print(f"\n  --- Most POSITIVE r ---")
    pos = corr_df[corr_df["pearson_r"] > 0].tail(top_n)
    for _, row in pos.iloc[::-1].iterrows():
        sig = "**" if row["p_value"] < 0.01 else ("*" if row["p_value"] < 0.05 else "")
        print(f"    {row['ticker']:<8}  r={row['pearson_r']:+.3f}{sig}  "
              f"n={row['n']:>4}  mean_profit={row['mean_profit_pct']:+.1f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FVR → 10-DTE short straddle P&L regression"
    )
    parser.add_argument("--tickers", nargs="+", default=None,
                        help="Ticker subset (default: all 987-ticker universe)")
    parser.add_argument("--ticker-file", type=str, default=None,
                        help="File with one ticker per line")
    parser.add_argument("--start", type=str, default=None,
                        help="Start date YYYY-MM-DD (default: 2018-01-01)")
    parser.add_argument("--end", type=str, default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--csv", action="store_true",
                        help="Save full merged dataset to fvr_straddle_data.csv")
    args = parser.parse_args()

    # ── Ticker list ───────────────────────────────────────────────────────────
    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [l.strip() for l in f if l.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        engine = _get_engine()
        import os; os.environ.setdefault("MYSQL_PASSWORD", "cthekb23")
        tickers = pd.read_sql(
            "SELECT DISTINCT ticker FROM study_summary WHERE study_id = 12 ORDER BY ticker",
            engine,
        )["ticker"].tolist()

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end   = date.fromisoformat(args.end)   if args.end   else date.today()

    print(f"FVR → Straddle Regression Study")
    print(f"  tickers   : {len(tickers)}")
    print(f"  date range: {start} → {end}")
    print(f"  entry     : Friday, ~{DTE_TARGET} DTE (±{DTE_TOL}), ATM straddle")
    print(f"  exit      : hold to expiry")

    # ── Fetch and accumulate data ─────────────────────────────────────────────
    all_frames: list[pd.DataFrame] = []
    n_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"\n[batch {batch_num}/{n_batches}] {batch[0]}…{batch[-1]}", end="  ", flush=True)

        straddle_df = fetch_straddle_batch(batch, start, end)
        if straddle_df.empty:
            print("→ 0 straddle entries")
            continue

        fvr_df = load_fvr(batch, start, end)
        merged = compute_pnl(straddle_df, fvr_df)

        n = len(merged)
        print(f"→ {len(straddle_df):,} straddles, {n:,} with FVR match")
        if n > 0:
            all_frames.append(merged)

    if not all_frames:
        print("\nNo data found. Check tickers and date range.")
        return

    df = pd.concat(all_frames, ignore_index=True)

    print(f"\n{'='*60}")
    print(f"  DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"  Total observations : {len(df):,}")
    print(f"  Unique tickers     : {df['ticker'].nunique():,}")
    print(f"  Date range         : {df['entry_date'].min()} → {df['entry_date'].max()}")
    print(f"  Mean entry_premium : ${df['entry_premium'].mean():.3f}/shr")
    print(f"  Mean profit_pct    : {df['profit_pct_seller'].mean():+.2f}%  "
          f"(seller perspective)")
    print(f"  Overall win rate   : {(df['profit_pct_seller'] > 0).mean()*100:.1f}%")
    print(f"  FVR 30-90 range    : {df['fvr_put_30_90'].min():.3f} – "
          f"{df['fvr_put_30_90'].max():.3f}  (mean {df['fvr_put_30_90'].mean():.3f})")
    if "fvr_put_10_30" in df.columns:
        n10 = df["fvr_put_10_30"].notna().sum()
        print(f"  FVR 10-30 range    : {df['fvr_put_10_30'].min():.3f} – "
              f"{df['fvr_put_10_30'].max():.3f}  (mean {df['fvr_put_10_30'].mean():.3f}, "
              f"n={n10:,})")

    # ── Winsorize outliers before regression ─────────────────────────────────
    print(f"\n  Winsorizing profit_pct_seller at p1/p99 to remove stale-data outliers...")
    df_w = winsorize(df, "profit_pct_seller")
    print(f"  Post-winsorize mean  : {df_w['profit_pct_seller'].mean():+.2f}%")
    print(f"  Post-winsorize median: {df_w['profit_pct_seller'].median():+.2f}%")

    has_10_30 = "fvr_put_10_30" in df_w.columns and df_w["fvr_put_10_30"].notna().sum() > 100
    n_with_10_30 = df_w["fvr_put_10_30"].notna().sum() if has_10_30 else 0
    if has_10_30:
        print(f"  Rows with fvr_put_10_30: {n_with_10_30:,} "
              f"({n_with_10_30/len(df_w)*100:.0f}% of winsorized dataset)")

    # ── Regression: 30-90d (baseline) ────────────────────────────────────────
    res_30_90 = run_ols(df_w, fvr_col="fvr_put_30_90")
    print_regression(res_30_90)
    bkt_30_90 = bucket_analysis(df_w, fvr_col="fvr_put_30_90")
    print_buckets(bkt_30_90, fvr_col="fvr_put_30_90")

    # ── Regression: 10-30d (new interval) ────────────────────────────────────
    if has_10_30:
        res_10_30 = run_ols(df_w, fvr_col="fvr_put_10_30")
        print_regression(res_10_30)
        bkt_10_30 = bucket_analysis(df_w, fvr_col="fvr_put_10_30")
        print_buckets(bkt_10_30, fvr_col="fvr_put_10_30")
        print_comparison(res_10_30, res_30_90, bkt_10_30, bkt_30_90)
    else:
        print("\n  NOTE: fvr_put_10_30 not available in dataset — run `run_build_fwd_vol.py --mode full` to populate.")

    # Per-ticker correlations — run for both intervals on raw data
    print(f"\n{'='*60}")
    print(f"  PER-TICKER CORRELATIONS (top 15 each end)")
    print(f"{'='*60}")
    corr_30_90 = per_ticker_corr(df, fvr_col="fvr_put_30_90")
    print(f"\n  --- fvr_put_30_90 ---")
    print_per_ticker(corr_30_90)
    if has_10_30:
        corr_10_30 = per_ticker_corr(df, fvr_col="fvr_put_10_30")
        print(f"\n  --- fvr_put_10_30 ---")
        print_per_ticker(corr_10_30)

    if args.csv:
        out_path = "fvr_straddle_data.csv"
        df.to_csv(out_path, index=False)
        print(f"\n  Full dataset saved → {out_path}")


if __name__ == "__main__":
    main()

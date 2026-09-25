#!/usr/bin/env python3
"""
Grid Structure Lookup Table Builder
====================================
Aggregates the 2M-row grid training dataset into
(ticker, vrp_bin, bullish, high_vix, c_delta_tgt, p_delta_tgt, dte_tgt)
cells and saves mean_roc / win_rate / n_trades per cell.

The screener does a direct lookup into this table — no model needed.

Market state features:
  vrp_bin   — per-ticker VRP (iv_rv_ratio) quintile (1=lowest, 5=highest)
  bullish   — spot > 50-day MA (1=yes, 0=no)
  high_vix  — VIX >= 20 (1=yes, 0=no)

Usage:
  PYTHONPATH=src .venv/bin/python3 run_grid_model.py [--build] [--recommend]

  --build      (Re)build and save the lookup table (default if missing)
  --recommend  Print best structures per ticker given latest cached state
  --min-n N    Minimum trades per cell (default: 10)

Output:
  data/cache/grid_lookup.parquet      — aggregated lookup table
  data/models/grid_vrp_quantiles.pkl  — per-ticker VRP quintile boundaries
"""
from __future__ import annotations

import argparse
import pathlib
import pickle
import warnings
from datetime import date

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_CACHE_DIR   = pathlib.Path("data/cache")
_MODEL_DIR   = pathlib.Path("data/models")
_TRAIN_PATH  = _CACHE_DIR / "grid_training_etf.parquet"
_FEAT_PATH   = _CACHE_DIR / "grid_features_etf.parquet"
_LOOKUP_PATH = _CACHE_DIR / "grid_lookup.parquet"
_QUANT_PATH  = _MODEL_DIR / "grid_vrp_quantiles.pkl"

DEFAULT_MIN_N = 10

STATE_COLS     = ["vrp_bin", "bullish", "high_vix"]
STRUCTURE_COLS = ["c_delta_tgt", "p_delta_tgt", "dte_tgt"]
GROUP_KEYS     = ["ticker"] + STATE_COLS + STRUCTURE_COLS

TRAIN_CUTOFF = 2023
VAL_CUTOFF   = 2024


# ── Market-state binning ───────────────────────────────────────────────────────

def compute_vrp_quantiles(df: pd.DataFrame) -> dict:
    """Per-ticker p99-winsorised VRP quintile boundaries from training data."""
    caps = df.groupby("ticker")["iv_rv_ratio"].quantile(0.99)
    df = df.copy()
    df["_vrp_w"] = df.apply(lambda r: min(r["iv_rv_ratio"], caps[r["ticker"]]), axis=1)
    quantiles = {}
    for ticker, grp in df.groupby("ticker"):
        quantiles[ticker] = grp["_vrp_w"].quantile([0.2, 0.4, 0.6, 0.8]).values
    return quantiles


def bin_vrp(vrp_w: float, q: np.ndarray) -> int:
    if q is None or np.isnan(vrp_w):
        return 3
    b = int(np.searchsorted(q, vrp_w) + 1)
    return max(1, min(5, b))


def add_state_columns(df: pd.DataFrame, vrp_quantiles: dict) -> pd.DataFrame:
    df = df.copy()
    caps = {t: vrp_quantiles[t][3] * 2 for t in vrp_quantiles}
    df["_vrp_w"]  = df.apply(lambda r: min(r["iv_rv_ratio"],
                              caps.get(r["ticker"], r["iv_rv_ratio"])), axis=1)
    df["vrp_bin"] = df.apply(lambda r: bin_vrp(r["_vrp_w"],
                              vrp_quantiles.get(r["ticker"])), axis=1).astype(int)
    df["bullish"]  = (df["spot_50ma"] > 1.0).astype(int)
    df["high_vix"] = (df["vix"] >= 20.0).astype(int)
    df.drop(columns=["_vrp_w"], inplace=True)
    return df


# ── Aggregation ────────────────────────────────────────────────────────────────

def build_lookup(df: pd.DataFrame, min_n: int) -> pd.DataFrame:
    """Aggregate all data to (ticker, state, structure) cells."""
    agg = (
        df.groupby(GROUP_KEYS, observed=True)
        .agg(
            mean_roc = ("roc", "mean"),
            win_rate = ("win", "mean"),
            n_trades = ("roc", "count"),
            std_roc  = ("roc", "std"),
        )
        .reset_index()
    )
    before = len(agg)
    agg = agg[agg["n_trades"] >= min_n].copy()
    print(f"  {len(df):,} trades → {len(agg):,} cells "
          f"(dropped {before - len(agg):,} with n<{min_n})")
    return agg.sort_values(["ticker"] + STATE_COLS + ["mean_roc"],
                            ascending=[True]*4 + [False])


def print_oos_summary(df: pd.DataFrame, lookup: pd.DataFrame) -> None:
    """For each ticker/regime cell, compare train vs OOS mean_roc."""
    tr_agg = (df[df["year"] < TRAIN_CUTOFF]
              .groupby(GROUP_KEYS, observed=True)["roc"].mean()
              .rename("train_roc"))
    oos_agg = (df[df["year"] >= VAL_CUTOFF]
               .groupby(GROUP_KEYS, observed=True)["roc"].mean()
               .rename("oos_roc"))
    merged = tr_agg.reset_index().merge(oos_agg.reset_index(), on=GROUP_KEYS, how="inner")
    if merged.empty:
        return
    corr = np.corrcoef(merged["train_roc"], merged["oos_roc"])[0, 1]
    print(f"  Train vs OOS mean_roc correlation (matched cells): ρ={corr:.3f}  "
          f"n={len(merged):,} cells")


# ── Recommendations (offline, from cached features) ───────────────────────────

def recommend(lookup: pd.DataFrame, vrp_quantiles: dict, min_n: int) -> None:
    feat_df = pd.read_parquet(_FEAT_PATH)
    feat_df["trade_date"] = pd.to_datetime(feat_df["trade_date"]).dt.date

    print(f"\n{'═'*96}")
    print(f"  STRUCTURE RECOMMENDATIONS  (direct lookup, min_n={min_n})")
    print(f"  Source: historical mean_roc for current (ticker, VRP bin, trend, VIX) regime")
    print(f"{'═'*96}")

    for ticker in sorted(feat_df["ticker"].unique()):
        tkr_feat = (feat_df[feat_df["ticker"] == ticker]
                    .dropna(subset=["iv_rv_ratio", "spot_50ma", "vix"])
                    .sort_values("trade_date"))
        if tkr_feat.empty:
            continue
        row = tkr_feat.iloc[-1]

        q = vrp_quantiles.get(ticker)
        vrp = row["iv_rv_ratio"]
        vrp_w = min(vrp, q[3] * 2) if q is not None and not np.isnan(vrp) else vrp
        vrp_b = bin_vrp(vrp_w, q)
        bullish  = int(row["spot_50ma"] > 1.0)
        high_vix = int(row["vix"] >= 20.0)

        cell = lookup[
            (lookup["ticker"]   == ticker) &
            (lookup["vrp_bin"]  == vrp_b) &
            (lookup["bullish"]  == bullish) &
            (lookup["high_vix"] == high_vix)
        ].sort_values("mean_roc", ascending=False)

        state_lbl = (f"VRP-bin={vrp_b}/5  "
                     f"{'Bullish' if bullish else 'Bearish'}  "
                     f"{'HighVIX' if high_vix else 'LowVIX'}")
        print(f"\n  {ticker}  (as of {row['trade_date']})")
        print(f"  VRP={vrp:.2f}  VIX={row['vix']:.1f}  "
              f"Spot/50MA={row['spot_50ma']:.3f}  → {state_lbl}")

        if cell.empty:
            print(f"  No cells with n>={min_n} in this regime")
            continue

        print(f"  {'CallΔ':>6}  {'PutΔ':>5}  {'DTE':>4}  {'MeanROC':>8}  "
              f"{'WinRate':>8}  {'N':>5}  {'StdROC':>7}")
        print(f"  {'─'*60}")
        for _, r in cell.head(5).iterrows():
            std_str = f"{r['std_roc']*100:>6.1f}%" if pd.notna(r.get("std_roc")) else "     —"
            print(f"  {r['c_delta_tgt']:>6.2f}  {r['p_delta_tgt']:>5.2f}  "
                  f"{int(r['dte_tgt']):>4}  {r['mean_roc']*100:>7.1f}%  "
                  f"{r['win_rate']*100:>7.1f}%  {int(r['n_trades']):>5}  {std_str}")


# ── Persistence ────────────────────────────────────────────────────────────────

def save(lookup: pd.DataFrame, vrp_quantiles: dict, min_n: int) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    lookup.to_parquet(_LOOKUP_PATH, index=False)
    with open(_QUANT_PATH, "wb") as f:
        pickle.dump({"vrp_quantiles": vrp_quantiles, "min_n": min_n,
                     "saved_at": date.today().isoformat()}, f)
    print(f"  Saved lookup → {_LOOKUP_PATH}  ({len(lookup):,} cells)")
    print(f"  Saved VRP quantiles → {_QUANT_PATH}")


def load() -> tuple[pd.DataFrame, dict, int]:
    lookup = pd.read_parquet(_LOOKUP_PATH)
    with open(_QUANT_PATH, "rb") as f:
        meta = pickle.load(f)
    print(f"Loaded lookup ({len(lookup):,} cells, saved {meta['saved_at']})")
    return lookup, meta["vrp_quantiles"], meta["min_n"]


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build",     action="store_true")
    parser.add_argument("--recommend", action="store_true")
    parser.add_argument("--no-cache",  action="store_true")
    parser.add_argument("--min-n",     type=int, default=DEFAULT_MIN_N)
    args = parser.parse_args()

    if not args.build and not args.recommend:
        args.build = args.recommend = True

    need_build = args.build or args.no_cache or not _LOOKUP_PATH.exists()

    if need_build:
        print(f"Loading training data from {_TRAIN_PATH} ...")
        df = pd.read_parquet(_TRAIN_PATH)
        print(f"  {len(df):,} rows, {df['ticker'].nunique()} tickers, "
              f"{df['year'].min()}–{df['year'].max()}")
        before = len(df)
        df = df.dropna(subset=["iv_rv_ratio", "rv20", "spot_50ma", "vix"])
        print(f"  Dropped {before - len(df):,} rows with missing key features")

        print("\nComputing VRP quantiles ...")
        vrp_quantiles = compute_vrp_quantiles(df[df["year"] < TRAIN_CUTOFF])

        print("\nBinning market state ...")
        df = add_state_columns(df, vrp_quantiles)

        print(f"\nBuilding lookup table (min_n={args.min_n}) ...")
        lookup = build_lookup(df, args.min_n)

        print("\nOut-of-sample consistency check:")
        print_oos_summary(df, lookup)

        save(lookup, vrp_quantiles, args.min_n)
        print()
    else:
        lookup, vrp_quantiles, _ = load()

    if args.recommend:
        recommend(lookup, vrp_quantiles, args.min_n if need_build else DEFAULT_MIN_N)


if __name__ == "__main__":
    main()

"""
Feature engineering for iron butterfly / straddle models.

Caching
-------
All external data sources are cached to data/cache/ as parquet files.
Re-running any script reuses the cache and only fetches new dates.

  data/cache/vix.parquet             — daily VIX + rolling IVR
  data/cache/price_features.parquet  — per-ticker 50MA, RV20, momentum
  data/cache/fvr_daily.parquet       — FVR + IV data from silver.fwd_vol_daily
"""

from __future__ import annotations

import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import awswrangler as wr

_CACHE_DIR = pathlib.Path("data/cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── IVR (IV percentile rank) ──────────────────────────────────────────────────

def compute_ivr(fvr_df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """
    Compute IVR (IV percentile rank) for each (ticker, entry_date).

    IVR = percentile rank of iv_put_30 among the past `window` trading days
    for the same ticker (strictly before current day — no lookahead).

    Returns DataFrame with columns: ticker, entry_date, ivr_30
    """
    date_col = "entry_date" if "entry_date" in fvr_df.columns else "trade_date"
    df = fvr_df.copy().sort_values(["ticker", date_col]).dropna(subset=["iv_put_30"])

    records = []
    for ticker, grp in df.groupby("ticker"):
        grp  = grp.sort_values(date_col).reset_index(drop=True)
        ivs  = grp["iv_put_30"].values
        dates = grp[date_col].values
        for i in range(len(grp)):
            lo   = max(0, i - window)
            past = ivs[lo:i]
            ivr  = float((past < ivs[i]).sum()) / len(past) * 100 if len(past) >= 20 else float("nan")
            records.append({"ticker": ticker, "entry_date": dates[i], "ivr_30": ivr})

    return pd.DataFrame(records)


# ── FVR local cache ────────────────────────────────────────────────────────────

_FVR_CACHE = _CACHE_DIR / "fvr_daily.parquet"
_FVR_DB    = "silver"
_FVR_TABLE = "fwd_vol_daily"


def load_fvr_cached(
    tickers: list[str],
    start: date,
    end: date,
    batch_size: int = 100,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Load FVR + IV data from local cache, fetching new dates from Athena as needed.

    Cache: data/cache/fvr_daily.parquet
    Columns: ticker, entry_date, fvr_put_30_90, iv_put_30
    """
    cached = pd.DataFrame()
    if _FVR_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(_FVR_CACHE)
        cached["entry_date"] = pd.to_datetime(cached["entry_date"]).dt.date

    # Determine what we still need to fetch
    if not cached.empty:
        cached_tickers  = set(cached["ticker"].unique())
        cache_max_date  = cached["entry_date"].max()
        missing_tickers = [t for t in tickers if t not in cached_tickers]
        fetch_start     = cache_max_date + timedelta(days=1) if not missing_tickers else start
        needs_fetch     = missing_tickers or (cache_max_date < end - timedelta(days=5))
    else:
        missing_tickers = tickers
        fetch_start     = start
        needs_fetch     = True

    if needs_fetch:
        fetch_tickers = tickers if missing_tickers else [t for t in tickers]
        print(f"  [fvr_cache] fetching {len(fetch_tickers)} tickers {fetch_start} → {end} from Athena")
        frames = []
        n = (len(fetch_tickers) + batch_size - 1) // batch_size
        for i in range(0, len(fetch_tickers), batch_size):
            batch = fetch_tickers[i : i + batch_size]
            bn    = i // batch_size + 1
            print(f"  [fvr_cache {bn}/{n}] {batch[0]}…{batch[-1]}", flush=True)
            tickers_sql = ", ".join(f"'{t}'" for t in batch)
            df = wr.athena.read_sql_query(
                sql=f"""
                SELECT ticker, trade_date, fvr_put_30_90, iv_put_30
                FROM {_FVR_DB}.{_FVR_TABLE}
                WHERE ticker IN ({tickers_sql})
                  AND trade_date >= DATE '{fetch_start.isoformat()}'
                  AND trade_date <= DATE '{end.isoformat()}'
                  AND fvr_put_30_90 > 0
                """,
                database=_FVR_DB,
                workgroup="dev-v3",
                s3_output="s3://athena-919061006621/",
            )
            if not df.empty:
                df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
                frames.append(df)

        if frames:
            new_rows = pd.concat(frames, ignore_index=True).rename(
                columns={"trade_date": "entry_date"}
            )
            combined = pd.concat([cached, new_rows], ignore_index=True).drop_duplicates(
                subset=["ticker", "entry_date"]
            )
            combined["entry_date"] = pd.to_datetime(combined["entry_date"])
            combined.to_parquet(_FVR_CACHE, index=False)
            combined["entry_date"] = combined["entry_date"].dt.date
            print(f"  [fvr_cache] {len(combined):,} rows cached → {_FVR_CACHE}")
            cached = combined
        else:
            print("  [fvr_cache] no new rows fetched")

    if cached.empty:
        return pd.DataFrame()

    cached["entry_date"] = pd.to_datetime(cached["entry_date"]).dt.date
    result = cached[
        cached["ticker"].isin(tickers) &
        (cached["entry_date"] >= start) &
        (cached["entry_date"] <= end)
    ].reset_index(drop=True)
    print(f"  [fvr_cache] {len(result):,} rows returned  ({result['ticker'].nunique():,} tickers)")
    return result


# ── VIX cache ─────────────────────────────────────────────────────────────────

_VIX_CACHE = _CACHE_DIR / "vix.parquet"


def fetch_vix(
    start: date,
    end: date,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Load daily VIX + rolling IVR from cache, fetching new dates from yfinance as needed.

    Cache: data/cache/vix.parquet
    Columns: date, vix, vix_ivr
    """
    import yfinance as yf

    cached = pd.DataFrame()
    if _VIX_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(_VIX_CACHE)
        cached["date"] = pd.to_datetime(cached["date"]).dt.date

    lookback_start = start - timedelta(days=400)

    if not cached.empty:
        cache_max = cached["date"].max()
        needs_fetch = cache_max < end - timedelta(days=5)
        fetch_from  = cache_max - timedelta(days=300)  # overlap for IVR recompute
    else:
        needs_fetch = True
        fetch_from  = lookback_start

    if needs_fetch:
        print(f"  [vix_cache] downloading ^VIX {fetch_from} → {end}", flush=True)
        raw = yf.download("^VIX", start=fetch_from, end=end + timedelta(days=1),
                          progress=False, auto_adjust=True)
        if not raw.empty:
            raw = raw[["Close"]].copy()
            raw.index = pd.to_datetime(raw.index).date
            raw.columns = ["vix"]
            raw = raw.sort_index().reset_index().rename(columns={"index": "date"})

            # Merge with existing (keep full history for IVR recompute)
            if not cached.empty:
                full = pd.concat([
                    cached[~cached["date"].isin(raw["date"])],
                    raw,
                ], ignore_index=True).sort_values("date").reset_index(drop=True)
            else:
                full = raw.copy()

            # Recompute rolling VIX IVR on full history
            vix_vals = full["vix"].values
            vix_ivr  = np.full(len(vix_vals), float("nan"))
            for i in range(len(vix_vals)):
                lo   = max(0, i - 252)
                past = vix_vals[lo:i]
                if len(past) >= 20:
                    vix_ivr[i] = float((past < vix_vals[i]).sum()) / len(past) * 100
            full["vix_ivr"] = vix_ivr

            full_save = full.copy()
            full_save["date"] = pd.to_datetime(full_save["date"])
            full_save.to_parquet(_VIX_CACHE, index=False)
            full["date"] = pd.to_datetime(full["date"]).apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )
            print(f"  [vix_cache] {len(full):,} rows cached → {_VIX_CACHE}")
            cached = full

    if cached.empty:
        return pd.DataFrame()

    cached["date"] = pd.to_datetime(cached["date"]).dt.date
    return cached[
        (cached["date"] >= start) & (cached["date"] <= end)
    ].reset_index(drop=True)


# ── Price feature cache ───────────────────────────────────────────────────────

_PRICE_CACHE   = _CACHE_DIR / "price_features.parquet"
_PRICE_LOOKBACK = 400
_RV_WINDOW      = 20
_MA_WINDOW      = 50


def fetch_price_features(
    tickers: list[str],
    start: date,
    end: date,
    force_refresh: bool = False,
    batch_size: int = 50,
) -> pd.DataFrame:
    """
    Load per-(ticker, date) price features from cache, downloading new
    tickers / dates from yfinance as needed.

    Cache: data/cache/price_features.parquet
    Columns: ticker, date, above_50ma, rv20, momentum_21

    The cache stores the FULL history (from 2017) so any date range query
    can be served without re-downloading.
    """
    import yfinance as yf

    cached = pd.DataFrame()
    if _PRICE_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(_PRICE_CACHE)
        cached["date"] = pd.to_datetime(cached["date"]).dt.date

    fetch_from = start - timedelta(days=_PRICE_LOOKBACK)

    if not cached.empty:
        cached_tickers  = set(cached["ticker"].unique())
        cache_max_date  = cached["date"].max()
        missing_tickers = [t for t in tickers if t not in cached_tickers]
        stale           = cache_max_date < end - timedelta(days=5)
        needs_fetch     = bool(missing_tickers) or stale
        # For stale data: re-download last 60 days for all tickers + any missing
        if stale and not missing_tickers:
            fetch_tickers  = tickers
            fetch_from_use = cache_max_date - timedelta(days=60)
        else:
            fetch_tickers  = tickers  # download all to refresh stale dates
            fetch_from_use = fetch_from if missing_tickers else (cache_max_date - timedelta(days=60))
    else:
        missing_tickers = tickers
        fetch_tickers   = tickers
        fetch_from_use  = fetch_from
        needs_fetch     = True

    if needs_fetch:
        print(f"  [price_cache] downloading {len(fetch_tickers)} tickers "
              f"{fetch_from_use} → {end}  "
              f"({len(missing_tickers)} new tickers)", flush=True)

        new_frames = []
        n_batches  = (len(fetch_tickers) + batch_size - 1) // batch_size

        for i in range(0, len(fetch_tickers), batch_size):
            batch = fetch_tickers[i : i + batch_size]
            bn    = i // batch_size + 1
            print(f"  [price_cache {bn}/{n_batches}] {batch[0]}…{batch[-1]}", flush=True)
            try:
                raw = yf.download(
                    batch,
                    start=fetch_from_use,
                    end=end + timedelta(days=1),
                    progress=False, auto_adjust=True, group_by="ticker",
                )
            except Exception as e:
                print(f"    warning: yfinance error — {e}")
                continue

            if raw.empty:
                continue

            if isinstance(raw.columns, pd.MultiIndex):
                # yfinance column level order varies by version
                if "Close" in raw.columns.get_level_values(0):
                    close = raw.xs("Close", axis=1, level=0)
                else:
                    close = raw.xs("Close", axis=1, level=1)
            else:
                close = raw[["Close"]].rename(columns={"Close": batch[0]})

            for ticker in close.columns:
                s = close[ticker].dropna()
                if len(s) < _MA_WINDOW + 5:
                    continue
                s.index  = pd.to_datetime(s.index).date
                s        = s.sort_index()
                prices   = s.values
                dates    = np.array(s.index)
                log_rets = np.concatenate([[float("nan")], np.diff(np.log(np.maximum(prices, 1e-10)))])

                ma50  = np.full(len(prices), float("nan"))
                rv20  = np.full(len(prices), float("nan"))
                mom21 = np.full(len(prices), float("nan"))

                for j in range(len(prices)):
                    if j >= _MA_WINDOW:
                        ma50[j] = prices[j - _MA_WINDOW : j].mean()
                    if j >= _RV_WINDOW:
                        rv20[j] = np.std(log_rets[j - _RV_WINDOW + 1 : j + 1], ddof=1) * math.sqrt(252)
                    if j >= 21:
                        mom21[j] = prices[j] / prices[j - 21] - 1

                df_t = pd.DataFrame({
                    "ticker":      ticker,
                    "date":        dates,
                    "above_50ma":  (prices > ma50).astype(float),
                    "rv20":        rv20,
                    "momentum_21": mom21,
                })
                df_t = df_t.dropna(subset=["rv20"])
                if not df_t.empty:
                    new_frames.append(df_t)

        if new_frames:
            new_rows = pd.concat(new_frames, ignore_index=True)
            # Merge: drop old rows for fetched tickers/dates, append new
            if not cached.empty:
                keep_old = cached[
                    ~(cached["ticker"].isin(fetch_tickers) &
                      (cached["date"] >= fetch_from_use))
                ]
                combined = pd.concat([keep_old, new_rows], ignore_index=True)
            else:
                combined = new_rows
            combined = combined.drop_duplicates(subset=["ticker", "date"])
            combined_save = combined.copy()
            combined_save["date"] = pd.to_datetime(combined_save["date"])
            combined_save.to_parquet(_PRICE_CACHE, index=False)
            combined["date"] = pd.to_datetime(combined["date"]).dt.date
            print(f"  [price_cache] {len(combined):,} rows cached → {_PRICE_CACHE}")
            cached = combined

    if cached.empty:
        return pd.DataFrame()

    cached["date"] = pd.to_datetime(cached["date"]).dt.date
    return cached[
        cached["ticker"].isin(tickers) &
        (cached["date"] >= start) &
        (cached["date"] <= end)
    ].reset_index(drop=True)


# ── Feature matrix assembly ───────────────────────────────────────────────────

_FEAT_CACHE = _CACHE_DIR / "long_straddle_features.parquet"


def build_feature_matrix(
    trades: pd.DataFrame,
    fvr_df: pd.DataFrame,
    vix_df: pd.DataFrame,
    price_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join all features onto a trades DataFrame.

    trades must have: ticker, entry_date, atm_strike, call_mid, put_mid,
                      cost, win, roc

    Returns trades with added feature columns.
    """
    df = trades.copy()
    df["premium_pct"] = df["cost"] / df["atm_strike"]

    if not fvr_df.empty:
        date_col  = "entry_date" if "entry_date" in fvr_df.columns else "trade_date"
        fvr_merge = fvr_df.rename(columns={date_col: "entry_date"})
        fvr_cols  = [c for c in ["ticker", "entry_date", "fvr_put_30_90", "iv_put_30"]
                     if c in fvr_merge.columns]
        df = df.merge(fvr_merge[fvr_cols], on=["ticker", "entry_date"], how="left")
        ivr_df = compute_ivr(fvr_merge)
        df = df.merge(ivr_df[["ticker", "entry_date", "ivr_30"]],
                      on=["ticker", "entry_date"], how="left")

    if not vix_df.empty:
        df = df.merge(
            vix_df.rename(columns={"date": "entry_date"}),
            on="entry_date", how="left",
        )

    if not price_df.empty:
        df = df.merge(
            price_df.rename(columns={"date": "entry_date"}),
            on=["ticker", "entry_date"], how="left",
        )
        if "iv_put_30" in df.columns and "rv20" in df.columns:
            df["vrp"] = df["iv_put_30"] - df["rv20"]

    return df


def save_feature_matrix(df: pd.DataFrame) -> None:
    """Cache assembled feature matrix to data/cache/long_straddle_features.parquet."""
    out = df.copy()
    for col in ["entry_date", "expiry"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col])
    out.to_parquet(_FEAT_CACHE, index=False)
    print(f"  [feat_cache] {len(out):,} rows saved → {_FEAT_CACHE}")


def load_feature_matrix() -> Optional[pd.DataFrame]:
    """Load cached feature matrix. Returns None if cache doesn't exist."""
    if not _FEAT_CACHE.exists():
        return None
    df = pd.read_parquet(_FEAT_CACHE)
    for col in ["entry_date", "expiry"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
    print(f"  [feat_cache] loaded {len(df):,} rows from {_FEAT_CACHE}")
    return df

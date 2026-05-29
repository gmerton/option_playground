#!/usr/bin/env python3
"""
IV Percentile (IVP) Short Strangle Study

For each ticker in a liquid ETF/index universe, enter a short strangle on every
qualifying Friday where the ticker's 30-day IV percentile (IVP) exceeds a
threshold.  IVP = percentile rank of today's iv_put_30 (from FVR cache or
vol-index proxy) within the past 252 trading days for that ticker.

Structure (symmetric strangle):
  Short 0.25Δ call  +  Short 0.25Δ put   (same expiry, ~20 DTE)

Exit: 50% profit take OR 2× credit stop, whichever comes first.
ROC:  pnl / entry_credit  (return on credit collected).

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src \\
    .venv/bin/python3 run_iv_condor_study.py [--refresh] [--all-tickers] [--etf-only]

  --refresh       Force re-query from Athena even if cache exists
  --all-tickers   Use all 206 walkforward tickers (default: 82 core 5-fold)
  --etf-only      Restrict universe to the curated ETF/index list
                  SPY/QQQ/IWM IVP is derived from VIX/VXN/RVX via yfinance
"""
from __future__ import annotations

import argparse
import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

_REPO_ROOT       = pathlib.Path(__file__).parent
_CACHE_DIR       = _REPO_ROOT / "data" / "cache"
_FVR_CACHE       = _CACHE_DIR / "fvr_daily.parquet"
_OPT_CACHE         = _CACHE_DIR / "iv_strangle_options.parquet"
_OPT_CACHE_ETF     = _CACHE_DIR / "iv_strangle_options_etf.parquet"
_MARKS_CACHE       = _CACHE_DIR / "iv_strangle_marks.parquet"
_MARKS_CACHE_ETF   = _CACHE_DIR / "iv_strangle_marks_etf.parquet"
_OPT_CACHE_ETF_STRADDLE   = _CACHE_DIR / "iv_straddle_options_etf.parquet"
_MARKS_CACHE_ETF_STRADDLE = _CACHE_DIR / "iv_straddle_marks_etf.parquet"
_TICKER_CSV        = _REPO_ROOT / "straddle_walkforward_ticker_persistence.csv"

# ── Config ────────────────────────────────────────────────────────────────────
SHORT_DELTA   = 0.25
TARGET_DTE    = 20
DTE_TOL       = 5
DELTA_MIN     = 0.15    # load slightly wider than target for find_option slack
DELTA_MAX     = 0.35
MAX_DELTA_ERR = 0.08

PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0
MIN_COVERAGE  = 0.70   # min fraction of entry Fridays with options data

IVP_LOOKBACK    = 252   # trading days for rolling percentile window
IVP_MIN_PERIODS = 60    # minimum history before IVP is valid

START_DATE = date(2018, 1, 1)   # FVR cache starts 2018-01-02
END_DATE   = date(2026, 3, 21)

IVP_THRESHOLDS = [0, 25, 50, 75]


# ── Ticker universe ───────────────────────────────────────────────────────────

# Curated ETF/index universe with liquid options.
# IVP source: VOL_INDEX_PROXY (yfinance) > FVR cache > skipped.
ETF_UNIVERSE = sorted([
    # Broad equity
    "SPY", "QQQ", "IWM", "DIA",
    # Sector / thematic
    "XLF", "XLE", "XLI", "XLB", "XLU", "XLP",  # XLK removed (neg ROC)
    "SOXX", "SOXL", "IGV",                        # SMH removed (neg ROC)
    "XBI", "XRT", "XOP",
    "GDX", "SILJ", "SLV", "GLD",
    "USO", "UNG", "BOIL",
    "ARKK", "JETS", "MSOS",
    # Leveraged / inverse
    "TQQQ", "UPRO", "TNA",                        # ERX removed (neg ROC, leveraged)
    "UVIX",                                    # VXX/UVXY removed (gap risk, unlimited loss)
    "TSLL", "NVDL", "BITX",
    # International
    "EEM", "EFA", "EWZ", "EWY", "FXI", "FEZ", "KWEB",
    # Fixed income / credit
    "TLT", "IEF", "LQD", "BKLN",                 # HYG removed (neg ROC, gap risk)
    # Crypto proxies
    "IBIT", "ETHA",
    # Other
    "IYR",
])

# Vol-index proxies used for IVP when ticker is not in FVR cache.
VOL_INDEX_PROXY: dict[str, str] = {
    "SPY":  "^VIX",
    "QQQ":  "^VXN",
    "IWM":  "^RVX",
    "TQQQ": "^VXN",   # 3× QQQ → use QQQ vol index

    "UPRO": "^VIX",   # 3× SPY
    "DIA":  "^VIX",   # Dow ETF
}


def load_tickers(all_tickers: bool = False, etf_only: bool = False) -> list[str]:
    """Return the requested ticker universe."""
    if etf_only:
        return ETF_UNIVERSE
    df = pd.read_csv(_TICKER_CSV)
    if not all_tickers:
        df = df[df["n_folds"] == 5]
    return sorted(df["ticker"].tolist())


# ── Options data ──────────────────────────────────────────────────────────────

def pull_from_athena(tickers: list[str]) -> pd.DataFrame:
    from lib.athena_lib import athena
    ticker_list = ", ".join(f"'{t}'" for t in tickers)
    dte_lo, dte_hi = TARGET_DTE - DTE_TOL, TARGET_DTE + DTE_TOL
    print(f"Querying Athena: {len(tickers)} tickers, DTE {dte_lo}–{dte_hi}, "
          f"|Δ| {DELTA_MIN}–{DELTA_MAX} ...")
    sql = f"""
    SELECT
        ticker,
        trade_date,
        expiry,
        strike,
        CAST((bid + ask) / 2.0 AS DOUBLE) AS mid,
        CAST(delta AS DOUBLE)              AS delta,
        cp,
        date_diff('day', trade_date, expiry) AS dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({ticker_list})
      AND trade_date >= TIMESTAMP '{START_DATE} 00:00:00'
      AND trade_date <= TIMESTAMP '{END_DATE} 23:59:59'
      AND bid > 0
      AND delta IS NOT NULL
      AND ABS(delta) BETWEEN {DELTA_MIN} AND {DELTA_MAX}
      AND date_diff('day', trade_date, expiry) BETWEEN {dte_lo} AND {dte_hi}
    ORDER BY ticker, trade_date, expiry, cp, strike
    """
    df = athena(sql)
    print(f"  Athena returned {len(df):,} rows")
    return df


def load_options(tickers: list[str], refresh: bool = False,
                 etf_only: bool = False, straddle: bool = False) -> pd.DataFrame:
    if straddle:
        cache = _OPT_CACHE_ETF_STRADDLE
    elif etf_only:
        cache = _OPT_CACHE_ETF
    else:
        cache = _OPT_CACHE
    if not refresh and cache.exists():
        print(f"Loading options from cache: {cache}")
        df = pd.read_parquet(cache)
        print(f"  {len(df):,} rows, {df['ticker'].nunique()} tickers")
    else:
        df = pull_from_athena(tickers)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache, index=False)
        print(f"  Cached to {cache}")

    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    df["dte"]        = df["dte"].astype(int)
    return df


def pull_marks_for_entries(entries: list[dict],
                           etf_only: bool = False,
                           refresh: bool = False,
                           straddle: bool = False) -> pd.DataFrame:
    """Pass 2: pull all daily marks for the exact (ticker, expiry, strike, cp)
    contracts identified in pass 1.  Uses a temp Glue table JOIN so the query
    is perfectly targeted — no delta filter, no data bloat.

    Returns DataFrame with columns: ticker, trade_date, expiry, strike, cp, mid.
    """
    from lib.constants import (GLUE_CATALOG, S3TABLES_CATALOG, DB, TABLE,
                                TMP_S3_PREFIX, WORKGROUP, S3_OUTPUT)
    import awswrangler as wr
    import uuid

    if straddle:
        cache = _MARKS_CACHE_ETF_STRADDLE
    elif etf_only:
        cache = _MARKS_CACHE_ETF
    else:
        cache = _MARKS_CACHE
    if not refresh and cache.exists():
        print(f"Loading daily marks from cache: {cache}")
        df = pd.read_parquet(cache)
        print(f"  {len(df):,} rows")
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
        return df

    # Build unique contracts table
    contracts: set[tuple] = set()
    for e in entries:
        contracts.add((e["ticker"], e["expiry"], float(e["call_strike"]), "C"))
        contracts.add((e["ticker"], e["expiry"], float(e["put_strike"]),  "P"))

    contracts_df = pd.DataFrame(
        list(contracts), columns=["ticker", "expiry", "strike", "cp"]
    )
    contracts_df["expiry"] = pd.to_datetime(contracts_df["expiry"])
    print(f"Pass 2: pulling daily marks for {len(contracts_df):,} unique contracts "
          f"({contracts_df['ticker'].nunique()} tickers) ...")

    # Write temp Glue table
    tmp_table = f"tmp_strangle_{uuid.uuid4().hex}"
    tmp_path  = TMP_S3_PREFIX.rstrip("/") + f"/{tmp_table}/"
    wr.s3.to_parquet(
        df=contracts_df,
        path=tmp_path,
        dataset=True,
        database=DB,
        table=tmp_table,
        compression="snappy",
        mode="overwrite",
        dtype={"ticker": "string", "expiry": "date",
               "strike": "double", "cp": "string"},
    )

    try:
        sql = f"""
        SELECT
            o.ticker,
            o.trade_date,
            o.expiry,
            o.strike,
            o.cp,
            CAST((o.bid + o.ask) / 2.0 AS DOUBLE) AS mid
        FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
        JOIN "{GLUE_CATALOG}"."{DB}"."{tmp_table}" t
          ON  o.ticker = t.ticker
          AND o.expiry = t.expiry
          AND o.strike = t.strike
          AND o.cp     = t.cp
        WHERE o.bid > 0
          AND o.trade_date >= TIMESTAMP '{START_DATE} 00:00:00'
          AND o.trade_date <= TIMESTAMP '{END_DATE} 23:59:59'
        ORDER BY o.ticker, o.trade_date, o.expiry, o.cp, o.strike
        """
        df = wr.athena.read_sql_query(
            sql=sql,
            database=DB,
            workgroup=WORKGROUP,
            data_source=S3TABLES_CATALOG,
            s3_output=S3_OUTPUT,
            ctas_approach=False,
        )
    finally:
        try:
            wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
        except Exception:
            pass
        try:
            wr.s3.delete_objects(tmp_path)
        except Exception:
            pass

    print(f"  Athena returned {len(df):,} mark rows")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    print(f"  Cached to {cache}")

    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    return df


# ── IVP ───────────────────────────────────────────────────────────────────────

def _rolling_ivp(iv_series: pd.Series) -> pd.Series:
    """Given a daily IV series, return rolling 252-day IVP (0–100) at each date."""
    iv_arr = iv_series.values.astype(float)
    out    = np.full(len(iv_arr), np.nan)
    for i in range(IVP_MIN_PERIODS, len(iv_arr)):
        cur = iv_arr[i]
        if math.isnan(cur):
            continue
        start = max(0, i - IVP_LOOKBACK)
        hist  = iv_arr[start:i]
        hist  = hist[~np.isnan(hist)]
        if len(hist) == 0:
            continue
        out[i] = (hist < cur).sum() / len(hist) * 100.0
    return pd.Series(out, index=iv_series.index)


def load_ivp(tickers: list[str]) -> dict[tuple[str, date], float]:
    """Compute rolling 252-day IVP per (ticker, date).

    Priority:
      1. VOL_INDEX_PROXY  — SPY/QQQ/IWM/… via yfinance (VIX, VXN, RVX)
      2. FVR cache        — iv_put_30 from straddle walkforward build
      3. Skipped          — no IVP, ticker won't fire during simulation

    Returns {(ticker, date): ivp_pct} where ivp_pct is 0.0–100.0.
    """
    ivp_map: dict[tuple[str, date], float] = {}

    # ── Vol-index proxies (SPY, QQQ, IWM, …) ─────────────────────────────────
    proxy_tickers = [t for t in tickers if t in VOL_INDEX_PROXY]
    if proxy_tickers:
        import yfinance as yf
        proxy_syms = sorted(set(VOL_INDEX_PROXY[t] for t in proxy_tickers))
        print(f"Downloading vol-index proxies from yfinance: {proxy_syms} ...")
        raw = yf.download(
            proxy_syms,
            start=str(START_DATE),
            end=str(END_DATE + timedelta(days=5)),
            progress=False,
            auto_adjust=True,
        )
        if isinstance(raw.columns, pd.MultiIndex):
            closes = raw["Close"]
        else:
            closes = raw[["Close"]].rename(columns={"Close": proxy_syms[0]})
        closes.index = pd.to_datetime(closes.index).date

        # Compute IVP per vol-index symbol, then assign to all mapped ETFs
        sym_ivp: dict[str, pd.Series] = {}
        for sym in proxy_syms:
            if sym not in closes.columns:
                print(f"  WARNING: {sym} not found in yfinance download — "
                      f"skipping {[t for t in proxy_tickers if VOL_INDEX_PROXY[t]==sym]}")
                continue
            iv_s = closes[sym].dropna() / 100.0   # VIX in %, convert to decimal
            sym_ivp[sym] = _rolling_ivp(iv_s)

        for tkr in proxy_tickers:
            sym = VOL_INDEX_PROXY[tkr]
            if sym not in sym_ivp:
                continue
            for d, v in sym_ivp[sym].items():
                if not math.isnan(v):
                    ivp_map[(tkr, d)] = v

        n_proxy = sum(1 for k in ivp_map if k[0] in proxy_tickers)
        print(f"  Vol-proxy IVP: {n_proxy:,} entries across "
              f"{len({k[0] for k in ivp_map if k[0] in proxy_tickers})} tickers")

    # ── FVR cache (remaining tickers) ────────────────────────────────────────
    fvr_tickers = [t for t in tickers if t not in VOL_INDEX_PROXY]
    if fvr_tickers:
        print("Computing IVP from FVR cache ...")
        fvr = pd.read_parquet(_FVR_CACHE)
        found = set(fvr["ticker"].unique()) & set(fvr_tickers)
        missing = set(fvr_tickers) - found
        if missing:
            print(f"  Not in FVR cache (will be skipped): {sorted(missing)}")
        fvr = fvr[fvr["ticker"].isin(fvr_tickers)].copy()
        fvr["entry_date"] = pd.to_datetime(fvr["entry_date"]).dt.date
        fvr = fvr.sort_values(["ticker", "entry_date"]).reset_index(drop=True)

        for ticker, grp in fvr.groupby("ticker"):
            iv_s  = grp.set_index("entry_date")["iv_put_30"]
            ivp_s = _rolling_ivp(iv_s)
            for d, v in ivp_s.items():
                if not math.isnan(v):
                    ivp_map[(ticker, d)] = v

    print(f"  IVP total: {len(ivp_map):,} (ticker, date) pairs, "
          f"{len({k[0] for k in ivp_map})} tickers")
    return ivp_map


def fill_ivp_from_options(
    ivp_map: dict,
    tickers: list[str],
    opts_df: pd.DataFrame,
    spot_maps: dict[str, dict],
) -> None:
    """Fill ivp_map in-place for tickers with no FVR/proxy coverage.

    IV proxy = (call_mid + put_mid) / spot at each trade_date, using the same
    SHORT_DELTA and TARGET_DTE as entry logic.  Rolling 252-day percentile gives
    IVP on the same 0–100 scale as other sources.
    """
    covered = {k[0] for k in ivp_map}
    missing = [t for t in tickers if t not in covered]
    if not missing:
        return

    print(f"Computing options-derived IVP for {len(missing)} tickers "
          f"not in FVR cache or vol-proxy ...")

    sub = opts_df[opts_df["ticker"].isin(missing)]
    new_pairs: dict[tuple[str, date], float] = {}

    for ticker, grp in sub.groupby("ticker"):
        spot_map = spot_maps.get(ticker, {})
        daily_iv: dict[date, float] = {}

        for trade_date, day_opts in grp.groupby("trade_date"):
            spot = spot_map.get(trade_date)
            if not spot or spot <= 0:
                continue
            call_row = find_option(day_opts, "C", SHORT_DELTA)
            if call_row is None:
                continue
            put_row = find_option(day_opts, "P", SHORT_DELTA,
                                  expiry=call_row["expiry"])
            if put_row is None:
                continue
            credit = call_row["mid"] + put_row["mid"]
            if credit > 0:
                daily_iv[trade_date] = credit / spot

        if len(daily_iv) < IVP_MIN_PERIODS:
            continue

        iv_s  = pd.Series(daily_iv).sort_index()
        ivp_s = _rolling_ivp(iv_s)
        for d, v in ivp_s.items():
            if not math.isnan(v):
                new_pairs[(ticker, d)] = v

    covered_new = len({k[0] for k in new_pairs})
    print(f"  Added {len(new_pairs):,} (ticker, date) pairs across "
          f"{covered_new} tickers")
    ivp_map.update(new_pairs)


# ── Option finding ────────────────────────────────────────────────────────────

def find_option(
    opts: pd.DataFrame,
    cp: str,
    target_delta: float,
    expiry: Optional[date] = None,
) -> Optional[pd.Series]:
    subset = opts[opts["cp"] == cp]
    if expiry is not None:
        subset = subset[subset["expiry"] == expiry]
    else:
        window = subset[
            (subset["dte"] >= TARGET_DTE - DTE_TOL) &
            (subset["dte"] <= TARGET_DTE + DTE_TOL)
        ]
        if window.empty:
            return None
        best_exp = (
            window.iloc[(window["dte"] - TARGET_DTE).abs().argsort()[:1]]
            ["expiry"].iloc[0]
        )
        subset = subset[subset["expiry"] == best_exp]

    subset = subset.copy()
    subset["_derr"] = (subset["delta"] - target_delta).abs()
    subset = subset[subset["_derr"] <= MAX_DELTA_ERR]
    if subset.empty:
        return None
    return subset.loc[subset["_derr"].idxmin()]


# ── Simulation ────────────────────────────────────────────────────────────────

def _settle_at_expiry(
    credit: float,
    call_strike: float,
    put_strike: float,
    expiry: date,
    daily_map_c: dict,
    daily_map_p: dict,
    spot_map: dict,
) -> float:
    """Compute settlement P&L at expiry.

    For a straddle/strangle at most ONE leg can be ITM at expiry.

    Priority:
      1. Athena option marks on expiry date (bid > 0 → ITM leg has value;
         missing leg → OTM → $0). No yfinance needed — avoids split issues.
      2. yfinance spot fallback only when no marks exist for either leg.
    """
    c_exp = daily_map_c.get((expiry, expiry, call_strike))
    p_exp = daily_map_p.get((expiry, expiry, put_strike))

    if c_exp is not None or p_exp is not None:
        # At least one leg has a mark → the other is OTM ($0).
        # Both present is possible for a wide strangle if spot lands between strikes.
        c_val = c_exp if c_exp is not None else 0.0
        p_val = p_exp if p_exp is not None else 0.0
        return credit - (c_val + p_val)

    # Neither mark found → both bid=0 → both expired worthless → full profit.
    # Exception: if yfinance spot is available and suggests one leg is deep ITM,
    # trust it (handles the rare case where Athena has no data for that expiry date).
    spot = (spot_map.get(expiry) or
            spot_map.get(expiry - timedelta(days=1)) or
            spot_map.get(expiry - timedelta(days=2)))
    if spot is None:
        return credit   # no data at all — assume worthless (conservative win)

    c_int = max(0.0, spot - call_strike)
    p_int = max(0.0, put_strike - spot)
    intrinsic = c_int + p_int

    # Sanity check: if yfinance spot implies intrinsic > 3× credit, it's almost
    # certainly a split-adjustment artifact.  Fall back to full-profit settlement.
    if intrinsic > credit * 3:
        return credit

    return credit - intrinsic

def sim_strangle(
    entry_date:  date,
    expiry:      date,
    call_strike: float,
    put_strike:  float,
    credit:      float,
    daily_map_c: dict,
    daily_map_p: dict,
    spot_map:    dict[date, float],
) -> dict:
    take_target = credit * (1.0 - PROFIT_TAKE)   # 50% of credit remaining
    stop_level  = credit * STOP_MULT              # premium doubles → stop

    mark_days  = 0
    total_days = 0

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        total_days += 1
        c_mid = daily_map_c.get((cur, expiry, call_strike))
        p_mid = daily_map_p.get((cur, expiry, put_strike))

        if c_mid is not None and p_mid is not None:
            mark_days += 1
            net_val = c_mid + p_mid

            if net_val <= take_target:
                return dict(pnl=credit - net_val, exit="profit_take",
                            days=(cur - entry_date).days, exit_date=cur,
                            mark_cov=mark_days / total_days)
            if net_val >= stop_level:
                return dict(pnl=credit - net_val, exit="stop_loss",
                            days=(cur - entry_date).days, exit_date=cur,
                            mark_cov=mark_days / total_days)

        if cur >= expiry:
            cov = mark_days / total_days if total_days else 0.0
            pnl = _settle_at_expiry(
                credit, call_strike, put_strike, expiry,
                daily_map_c, daily_map_p, spot_map,
            )
            return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                        days=(expiry - entry_date).days, exit_date=expiry,
                        mark_cov=cov)

        cur += timedelta(days=1)

    # fallback (loop exited without returning — shouldn't happen)
    cov = mark_days / total_days if total_days else 0.0
    pnl = _settle_at_expiry(
        credit, call_strike, put_strike, expiry,
        daily_map_c, daily_map_p, spot_map,
    )
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry,
                mark_cov=cov)


# ── Reporting ─────────────────────────────────────────────────────────────────

def _roc_stats(sub: pd.DataFrame) -> tuple[float, float, float, float]:
    roc     = (sub["pnl"] / sub["credit"]).mean() * 100
    ann_roc = ((sub["pnl"] / sub["credit"]) * (365 / sub["days"])).mean() * 100
    win_pct = (sub["pnl"] > 0).mean() * 100
    stp_pct = (sub["exit"] == "stop_loss").mean() * 100
    return win_pct, roc, ann_roc, stp_pct


def _ticker_stats_table(sub: pd.DataFrame) -> pd.DataFrame:
    """Return a per-ticker summary DataFrame sorted by avg_roc descending."""
    return (
        sub.groupby("ticker")
        .apply(lambda g: pd.Series({
            "n":        len(g),
            "win_pct":  (g["pnl"] > 0).mean() * 100,
            "avg_roc":  (g["pnl"] / g["credit"]).mean() * 100,
            "ann_roc":  ((g["pnl"] / g["credit"]) * (365 / g["days"])).mean() * 100,
            "avg_days": g["days"].mean(),
            "stop_pct": (g["exit"] == "stop_loss").mean() * 100,
            "mark_cov": g["mark_cov"].mean() * 100,
            "avg_cr":   g["credit"].mean(),
        }), include_groups=False)
        .sort_values("avg_roc", ascending=False)
    )


def _print_ticker_table(stats: pd.DataFrame) -> None:
    print(f"\n  {'Ticker':>6}  {'N':>4}  {'Win%':>6}  {'AvgROC%':>7}  "
          f"{'AnnROC%':>8}  {'AvgDays':>7}  {'Stops%':>6}  {'AvgCr':>6}  {'MarkCov':>7}")
    print("  " + "─" * 76)
    for ticker, row in stats.iterrows():
        print(f"  {ticker:>6}  {row['n']:>4.0f}  {row['win_pct']:>5.1f}%  "
              f"{row['avg_roc']:>6.1f}%  {row['ann_roc']:>7.1f}%  "
              f"{row['avg_days']:>6.1f}d  {row['stop_pct']:>5.1f}%  "
              f"${row['avg_cr']:>4.2f}  {row['mark_cov']:>6.1f}%")


def _print_peryear(sub: pd.DataFrame, ticker: str) -> None:
    print(f"\n  {ticker}")
    print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgROC%':>7}  "
          f"{'AvgCr':>7}  {'AvgDays':>7}  {'Stops':>5}")
    print("  " + "─" * 52)
    for yr, grp in sub.groupby("year"):
        roc = (grp["pnl"] / grp["credit"]).mean() * 100
        print(f"  {yr:>6}  {len(grp):>4}  "
              f"{(grp['pnl']>0).mean()*100:>5.1f}%  "
              f"{roc:>6.1f}%  ${grp['credit'].mean():>5.2f}  "
              f"{grp['days'].mean():>6.1f}d  "
              f"{(grp['exit']=='stop_loss').sum():>5}")
    tot_roc = (sub["pnl"] / sub["credit"]).mean() * 100
    print(f"  {'TOTAL':>6}  {len(sub):>4}  "
          f"{(sub['pnl']>0).mean()*100:>5.1f}%  "
          f"{tot_roc:>6.1f}%  ${sub['credit'].mean():>5.2f}  "
          f"{sub['days'].mean():>6.1f}d  "
          f"{(sub['exit']=='stop_loss').sum():>5}")


def print_results(df: pd.DataFrame, n_tickers: int) -> None:
    sep = "═" * 88

    print(f"\n{sep}")
    structure = (f"Short {SHORT_DELTA:.2f}Δ ATM straddle"
                 if SHORT_DELTA >= 0.45
                 else f"Short {SHORT_DELTA:.2f}Δ call + {SHORT_DELTA:.2f}Δ put strangle")
    print(f"  SHORT {'STRADDLE' if SHORT_DELTA >= 0.45 else 'STRANGLE'} STUDY  ·  BASELINE (no filter)")
    print(f"  Universe: {n_tickers} tickers  ·  ~{TARGET_DTE} DTE  ·  "
          f"{structure}  ·  50% PT / {STOP_MULT}× stop")
    print(f"  ROC = pnl / entry_credit")
    print(sep)

    # ── Baseline: all entries, no filter ─────────────────────────────────────
    win, roc, ann, stp = _roc_stats(df)
    print(f"\n  ALL ENTRIES (no filter):  N={len(df):,}  Win={win:.1f}%  "
          f"AvgROC={roc:.1f}%  AnnROC={ann:.1f}%  Stops={stp:.1f}%\n")

    # ── Baseline per-ticker (no filter) ──────────────────────────────────────
    print(f"{sep}")
    print(f"  BASELINE — ALL TICKERS  ·  No Filter  (sorted by Avg ROC%)")
    print(sep)
    baseline_stats = _ticker_stats_table(df)
    _print_ticker_table(baseline_stats)

    # ── IVP threshold sweep ──────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  IVP THRESHOLD SWEEP")
    print(sep)
    print(f"\n  {'Gate':>10}  {'Tickers':>7}  {'Entries':>7}  {'Win%':>6}  "
          f"{'AvgROC%':>7}  {'AnnROC%':>8}  {'AvgDays':>7}  {'Stops%':>6}")
    print("  " + "─" * 70)
    for threshold in IVP_THRESHOLDS:
        sub = df if threshold == 0 else df[df["ivp"] >= threshold]
        if sub.empty:
            continue
        win, roc, ann, stp = _roc_stats(sub)
        lbl = "All IVP" if threshold == 0 else f"IVP ≥ {threshold}"
        print(f"  {lbl:>10}  {sub['ticker'].nunique():>7}  {len(sub):>7}  "
              f"{win:>5.1f}%  {roc:>6.1f}%  {ann:>7.1f}%  "
              f"{sub['days'].mean():>6.1f}d  {stp:>5.1f}%")

    # ── IVP quartile breakdown ───────────────────────────────────────────────
    print(f"\n  IVP QUARTILE BREAKDOWN  (monotonicity check)\n")
    print(f"  {'Quartile':>18}  {'Entries':>7}  {'Win%':>6}  "
          f"{'AvgROC%':>7}  {'AnnROC%':>8}  {'Stops%':>6}")
    print("  " + "─" * 66)
    for lbl, lo, hi in [
        ("Q1  IVP  0–25",   0,  25),
        ("Q2  IVP 25–50",  25,  50),
        ("Q3  IVP 50–75",  50,  75),
        ("Q4  IVP 75–100", 75, 101),
    ]:
        sub = df[(df["ivp"] >= lo) & (df["ivp"] < hi)]
        if sub.empty:
            continue
        win, roc, ann, stp = _roc_stats(sub)
        print(f"  {lbl:>18}  {len(sub):>7}  {win:>5.1f}%  "
              f"{roc:>6.1f}%  {ann:>7.1f}%  {stp:>5.1f}%")

    # ── Per-ticker at IVP ≥ 50 ────────────────────────────────────────────────
    sub50 = df[df["ivp"] >= 50]
    if not sub50.empty:
        print(f"\n{sep}")
        print(f"  ALL TICKERS  ·  IVP ≥ 50  (sorted by Avg ROC%)")
        print(sep)
        stats50 = _ticker_stats_table(sub50)
        _print_ticker_table(stats50)

    # ── Per-year breakdown for top 5 (no filter) ─────────────────────────────
    top5 = baseline_stats.head(5).index.tolist()
    print(f"\n{sep}")
    print(f"  PER-YEAR  ·  Top 5 tickers  (no filter)")
    print(sep)
    for ticker in top5:
        _print_peryear(df[df["ticker"] == ticker], ticker)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-query from Athena even if cache exists")
    parser.add_argument("--all-tickers", action="store_true",
                        help="Use all 206 walkforward tickers (default: 82 core 5-fold)")
    parser.add_argument("--etf-only", action="store_true",
                        help="Restrict universe to curated ETF/index list")
    parser.add_argument("--min-coverage", type=float, default=MIN_COVERAGE,
                        help=f"Min fraction of entry Fridays with options data "
                             f"(default {MIN_COVERAGE:.0%})")
    parser.add_argument("--save-csv", metavar="PATH",
                        help="Save full trade log (one row per trade) to CSV for "
                             "feature analysis. Default: data/studies/strangle_trades.csv")
    parser.add_argument("--straddle", action="store_true",
                        help="Run ATM short straddle (0.50Δ call+put, same strike) "
                             "instead of 0.25Δ strangle")
    args = parser.parse_args()

    if args.straddle:
        global SHORT_DELTA, DELTA_MIN, DELTA_MAX, MAX_DELTA_ERR
        SHORT_DELTA   = 0.50
        DELTA_MIN     = 0.40
        DELTA_MAX     = 0.60
        MAX_DELTA_ERR = 0.10

    etf_only = args.etf_only
    tickers = load_tickers(all_tickers=args.all_tickers, etf_only=etf_only)
    if etf_only:
        lbl = f"ETF/index universe"
    elif args.all_tickers:
        lbl = "all 206 walkforward tickers"
    else:
        lbl = "82 core 5-fold tickers"
    print(f"Universe: {len(tickers)} tickers ({lbl})")

    opts_df = load_options(tickers, refresh=args.refresh, etf_only=etf_only,
                           straddle=args.straddle)
    ivp_map = load_ivp(tickers)

    # ── Spot prices (for expiry P&L) ─────────────────────────────────────────
    # auto_adjust=False: option strikes in Athena are nominal/unadjusted prices,
    # so the expiry spot must match that scale (no reverse-split inflation).
    print("Downloading spot prices from yfinance ...")
    import yfinance as yf
    raw = yf.download(
        tickers,
        start=str(START_DATE),
        end=str(END_DATE + timedelta(days=5)),
        progress=False,
        auto_adjust=False,
    )
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})
    close.index = pd.to_datetime(close.index).date

    spot_maps: dict[str, dict[date, float]] = {}
    for t in tickers:
        if t in close.columns:
            s = close[t].dropna()
            spot_maps[t] = dict(zip(s.index, s.values.astype(float)))
    print(f"  Spot loaded for {len(spot_maps)} / {len(tickers)} tickers")

    # ── Fill IVP gaps from options data ──────────────────────────────────────
    fill_ivp_from_options(ivp_map, tickers, opts_df, spot_maps)

    # ── Build per-ticker daily lookup maps ───────────────────────────────────
    print("Building option lookup maps ...")
    daily_maps_c: dict[str, dict] = {}
    daily_maps_p: dict[str, dict] = {}
    opts_by_date: dict[str, dict] = {}

    for ticker, grp in opts_df.groupby("ticker"):
        calls = grp[grp["cp"] == "C"]
        puts  = grp[grp["cp"] == "P"]
        daily_maps_c[ticker] = {
            (r.trade_date, r.expiry, r.strike): r.mid
            for r in calls.itertuples(index=False)
        }
        daily_maps_p[ticker] = {
            (r.trade_date, r.expiry, r.strike): r.mid
            for r in puts.itertuples(index=False)
        }
        opts_by_date[ticker] = {d: g for d, g in grp.groupby("trade_date")}
    print(f"  Maps built for {len(daily_maps_c)} tickers")

    # ── Chain coverage filter ─────────────────────────────────────────────────
    entry_dates_all = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]
    coverage = {
        t: sum(1 for d in entry_dates_all if d in opts_by_date.get(t, {})) / len(entry_dates_all)
        for t in tickers
    }
    thin = [t for t, c in coverage.items() if c < args.min_coverage]
    liquid = [t for t, c in coverage.items() if c >= args.min_coverage]

    print(f"\n  Chain coverage (≥{args.min_coverage:.0%} required):")
    for t in sorted(tickers, key=lambda x: -coverage[x]):
        flag = "  ✓" if coverage[t] >= args.min_coverage else "  ✗ dropped"
        print(f"    {t:6s}  {coverage[t]:.1%}{flag}")
    print(f"\n  Kept {len(liquid)} tickers, dropped {len(thin)}: {thin}")

    tickers = liquid

    # ── Simulate ─────────────────────────────────────────────────────────────
    entry_dates = entry_dates_all

    # ── Pass 1: identify entries ──────────────────────────────────────────────
    print(f"\nPass 1: identifying entries across "
          f"{len(entry_dates)} Fridays × {len(tickers)} tickers ...")
    raw_entries  = []
    skipped_ivp  = 0
    skipped_opts = 0

    for edate in entry_dates:
        for ticker in tickers:
            ivp = ivp_map.get((ticker, edate))
            if ivp is None:
                skipped_ivp += 1
                continue

            day_opts = opts_by_date.get(ticker, {}).get(edate)
            if day_opts is None:
                skipped_opts += 1
                continue

            call_row = find_option(day_opts, "C", SHORT_DELTA)
            if call_row is None:
                continue

            if args.straddle:
                # True straddle: put must be at the exact same (ATM) strike
                put_candidates = day_opts[
                    (day_opts["cp"] == "P") &
                    (day_opts["expiry"] == call_row["expiry"]) &
                    (day_opts["strike"] == call_row["strike"])
                ]
                if put_candidates.empty:
                    continue
                put_row = put_candidates.iloc[0]
            else:
                put_row = find_option(day_opts, "P", SHORT_DELTA, expiry=call_row["expiry"])
                if put_row is None:
                    continue
                if put_row["strike"] > call_row["strike"]:
                    continue

            credit = call_row["mid"] + put_row["mid"]
            if credit <= 0:
                continue

            raw_entries.append({
                "ticker":      ticker,
                "edate":       edate,
                "expiry":      call_row["expiry"],
                "call_strike": call_row["strike"],
                "put_strike":  put_row["strike"],
                "credit":      credit,
                "ivp":         ivp,
            })

    print(f"  {len(raw_entries):,} entries identified "
          f"(skipped {skipped_ivp:,} no-IVP, {skipped_opts:,} no-options)")

    # ── Pass 2: pull full daily marks for identified contracts ────────────────
    marks_df = pull_marks_for_entries(raw_entries,
                                      etf_only=etf_only,
                                      refresh=args.refresh,
                                      straddle=args.straddle)

    # Merge pass-2 marks into the daily lookup maps
    print("Merging pass-2 marks into lookup maps ...")
    for ticker, grp in marks_df.groupby("ticker"):
        calls = grp[grp["cp"] == "C"]
        puts  = grp[grp["cp"] == "P"]
        if ticker not in daily_maps_c:
            daily_maps_c[ticker] = {}
            daily_maps_p[ticker] = {}
        daily_maps_c[ticker].update({
            (r.trade_date, r.expiry, r.strike): r.mid
            for r in calls.itertuples(index=False)
        })
        daily_maps_p[ticker].update({
            (r.trade_date, r.expiry, r.strike): r.mid
            for r in puts.itertuples(index=False)
        })
    print(f"  Done — maps enriched with pass-2 marks")

    # ── Simulate ──────────────────────────────────────────────────────────────
    print(f"\nSimulating {len(raw_entries):,} entries ...")
    results = []

    for e in raw_entries:
        ticker = e["ticker"]
        sim = sim_strangle(
            e["edate"],
            e["expiry"],
            e["call_strike"],
            e["put_strike"],
            e["credit"],
            daily_maps_c[ticker],
            daily_maps_p[ticker],
            spot_maps.get(ticker, {}),
        )
        results.append({
            "ticker":   ticker,
            "edate":    e["edate"],
            "year":     e["edate"].year,
            "ivp":      e["ivp"],
            "credit":   e["credit"],
            "mark_cov": sim.pop("mark_cov", 0.0),
            **sim,
        })

    df = pd.DataFrame(results)
    if df.empty:
        print("No results — check ticker list or date range.")
        return

    print(f"  Simulated {len(df):,} strangles across "
          f"{df['ticker'].nunique()} tickers\n")
    print_results(df, len(tickers))

    # ── Save trade log CSV ────────────────────────────────────────────────────
    default_csv = "straddle_trades.csv" if args.straddle else "strangle_trades.csv"
    csv_path = args.save_csv or str(_REPO_ROOT / "data" / "studies" / default_csv)
    out = df[["ticker", "edate", "year", "ivp", "credit", "pnl", "days",
              "exit", "mark_cov"]].copy()
    out["roc"] = out["pnl"] / out["credit"]
    out["win"] = (out["pnl"] > 0).astype(int)
    out.to_csv(csv_path, index=False)
    print(f"\nTrade log saved → {csv_path}  ({len(out):,} rows)")


if __name__ == "__main__":
    main()

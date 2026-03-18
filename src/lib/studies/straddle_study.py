"""
Generic ATM short-straddle backtest engine.

Data flow
---------
  Athena (options_daily_v3)
      └─► sync_options_cache()  ─► MySQL options_cache table
              └─► fetch_options_cache()
                      └─► build_straddle_trades()
                              └─► compute_metrics()
                                      └─► print_summary() / CSV

Design goals
------------
- Ticker-agnostic: pass any ticker + date range.
- Extensible: dte_target, dte_tol, call_delta, entry_weekday are all
  runtime parameters.  The same engine handles different strikes, different
  DTE windows, or non-ATM straddles (e.g. call_delta=0.40/put_delta=0.40).
- Split-aware: pass a list of reverse-split dates; any straddle whose
  holding period spans a split is flagged and excluded from summary stats.
- Reg-T margin tracking: margin = 20% × strike × 100 + premium × 100,
  using the ATM strike as the spot proxy (no Tradier dependency).

Usage
-----
  from lib.studies.straddle_study import run_study, UVXY_SPLIT_DATES
  from datetime import date

  df = run_study(
      ticker="UVXY",
      start=date(2018, 1, 12),
      end=date.today(),
      dte_target=20,
      dte_tol=5,
      call_delta=0.50,
      entry_weekday=4,          # Friday
      split_dates=UVXY_SPLIT_DATES,
      output_csv="uvxy_straddle.csv",
  )
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Optional

import pandas as pd

# ── UVXY split dates within the post-leverage-change window (2018-01-12+) ────

UVXY_SPLIT_DATES: list[date] = [
    date(2018, 9, 18),   # 1:5
    date(2021, 5, 26),   # 1:10
    date(2023, 6, 23),   # 1:10
    date(2024, 4, 11),   # 1:5
    date(2025, 11, 20),  # 1:5
]

TLT_SPLIT_DATES: list[date] = []  # TLT has no reverse splits
GLD_SPLIT_DATES: list[date] = []  # GLD has no reverse splits
XLE_SPLIT_DATES: list[date] = []  # XLE has no reverse splits
XLV_SPLIT_DATES: list[date] = []  # XLV has no reverse splits
XOP_SPLIT_DATES: list[date] = [
    date(2020, 6, 9),   # 1:4 reverse split
]
USO_SPLIT_DATES: list[date] = []  # post-restructuring study window avoids the 2020 break
XLU_SPLIT_DATES: list[date] = []  # XLU has no reverse splits
XLP_SPLIT_DATES: list[date] = []  # XLP has no reverse splits (2019 forward split handled by delta selection)
IWM_SPLIT_DATES: list[date] = []  # IWM has no reverse splits
GDX_SPLIT_DATES: list[date] = []  # GDX has no reverse splits
QQQ_SPLIT_DATES: list[date] = []  # QQQ has no reverse splits
INDA_SPLIT_DATES: list[date] = []  # INDA has no reverse splits

UVIX_SPLIT_DATES: list[date] = [
    date(2023, 10, 11),  # ~1:4 reverse split (strikes ~$10 → ~$40)
    date(2025, 1, 15),   # ~1:4 reverse split (strikes ~$8 → ~$33)
]

TMF_SPLIT_DATES: list[date] = [
    date(2016, 8, 25),   # 1:4 forward split (price ~$116 → ~$29; pre-2018 study window)
    date(2023, 12, 5),   # 1:10 reverse split (price ~$6 → ~$60)
]

EEM_SPLIT_DATES: list[date] = []  # EEM has no splits in the study window
XLF_SPLIT_DATES: list[date] = []  # XLF has no splits in the study window
ASHR_SPLIT_DATES: list[date] = []  # ASHR has no known splits in the study window
FXI_SPLIT_DATES: list[date] = []   # FXI has no known splits in the study window
SOXX_SPLIT_DATES: list[date] = []  # SOXX had a 2:1 forward split 2021-10-13; delta selection handles it naturally

SQQQ_SPLIT_DATES: list[date] = [
    date(2022, 5, 24),  # 1:10 reverse split (QQQ crash lifted SQQQ; post-crash re-base)
    # TODO: verify additional splits from Athena price data; there may be a 2023 split
]

BJ_SPLIT_DATES: list[date] = []    # BJ's Wholesale Club; IPO June 2018, no splits
YINN_SPLIT_DATES: list[date] = [
    date(2021, 9, 21),  # 1:5 reverse split
    # TODO: verify additional splits from Athena price data
]

GEV_SPLIT_DATES:  list[date] = []   # GE Vernova; spun off from GE April 2, 2024 — no splits
CLS_SPLIT_DATES:  list[date] = []   # Celestica; no known splits in study window
FN_SPLIT_DATES:   list[date] = []   # Fabrinet; no known splits in study window
CASY_SPLIT_DATES: list[date] = []   # Casey's General Stores; no known splits in study window

VXX_SPLIT_DATES: list[date] = [
    date(2019, 11, 20),  # 1:4 reverse split
    date(2021, 11,  1),  # 1:4 reverse split
    date(2023,  7, 24),  # 1:4 reverse split
]

UCO_SPLIT_DATES: list[date] = [
    date(2020,  6,  8),  # 1:25 reverse split (COVID oil crash / negative WTI prices)
]

XBI_SPLIT_DATES: list[date] = []  # XBI has no reverse splits

XLK_SPLIT_DATES:  list[date] = []  # Technology Select Sector SPDR; no reverse splits
V_SPLIT_DATES:    list[date] = []  # Visa Inc.; no splits in study window
MA_SPLIT_DATES:   list[date] = []  # Mastercard Inc.; no splits in study window
HD_SPLIT_DATES:   list[date] = []  # Home Depot; no splits in study window

# Low-volatility defensive individual stocks (no reverse splits)
COST_SPLIT_DATES: list[date] = []  # Costco; no splits since 2000 (pre-study window)
WMT_SPLIT_DATES:  list[date] = []  # Walmart; 3:1 forward split 2024-02-26 — delta selection handles it
JNJ_SPLIT_DATES:  list[date] = []  # Johnson & Johnson; no splits in study window

# Broad market + mega-cap individual stocks (forward splits only — delta selection handles naturally)
SPY_SPLIT_DATES:   list[date] = []  # SPY; no reverse splits
AAPL_SPLIT_DATES:  list[date] = []  # AAPL; 4:1 forward split 2020-08-31 — delta selection handles it
MSFT_SPLIT_DATES:  list[date] = []  # MSFT; no splits since 2003
NVDA_SPLIT_DATES:  list[date] = []  # NVDA; 4:1 fwd 2021-07-20, 10:1 fwd 2024-06-10 — delta selection handles it
AMZN_SPLIT_DATES:  list[date] = []  # AMZN; 20:1 forward split 2022-06-06 — delta selection handles it
GOOGL_SPLIT_DATES: list[date] = []  # GOOGL; 20:1 forward split 2022-07-18 — delta selection handles it
META_SPLIT_DATES:  list[date] = []  # META; no splits
IBIT_SPLIT_DATES:  list[date] = []  # iShares Bitcoin Trust ETF; no splits


# ── Athena → MySQL sync ───────────────────────────────────────────────────────

def sync_options_cache(
    ticker: str,
    start: date,
    *,
    force: bool = False,
) -> int:
    """
    Sync near-term options data (DTE 0–65) from Athena into options_cache.

    Incremental by default: only fetches dates after the current max_date.
    Pass force=True to re-fetch everything from *start*.

    Returns the number of rows upserted.
    """
    from lib.athena_lib import athena
    from lib.constants import DB, TABLE
    from lib.mysql_lib import (
        create_options_cache_table,
        get_options_cache_max_date,
        upsert_options_cache,
    )

    create_options_cache_table()

    today = date.today()

    if force:
        fetch_start = start
    else:
        max_date = get_options_cache_max_date(ticker)
        if max_date is not None and max_date >= today - timedelta(days=2):
            print(
                f"options_cache [{ticker}]: already current "
                f"(max_date={max_date}). Pass force=True to re-fetch."
            )
            return 0
        fetch_start = (max_date + timedelta(days=1)) if max_date else start

    if fetch_start > today:
        print(f"options_cache [{ticker}]: nothing to fetch.")
        return 0

    print(f"Syncing {ticker} options from Athena: {fetch_start} → {today} ...")

    # Dedup within Athena before storing.  Include expiry-day rows (DTE=0)
    # without bid/ask filters so we can look up settlement prices.
    sql = f"""
    SELECT
        trade_date,
        expiry,
        cp,
        CAST(strike        AS DOUBLE) AS strike,
        CAST(bid           AS DOUBLE) AS bid,
        CAST(ask           AS DOUBLE) AS ask,
        CAST(last          AS DOUBLE) AS last,
        (CAST(bid AS DOUBLE) + CAST(ask AS DOUBLE)) / 2.0 AS mid,
        CAST(delta         AS DOUBLE) AS delta,
        CAST(open_interest AS BIGINT) AS open_interest,
        CAST(volume        AS BIGINT) AS volume
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY ticker, trade_date, expiry, cp, strike
                ORDER BY open_interest DESC NULLS LAST, bid DESC
            ) AS rn
        FROM "{DB}"."{TABLE}"
        WHERE ticker = '{ticker}'
          AND trade_date >= TIMESTAMP '{fetch_start.isoformat()} 00:00:00'
          AND trade_date <= TIMESTAMP '{today.isoformat()} 00:00:00'
          AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 65
          AND (
              date_diff('day', trade_date, expiry) = 0
              OR (bid > 0 AND ask > 0 AND delta IS NOT NULL)
          )
    ) deduped
    WHERE rn = 1
    ORDER BY trade_date, expiry, cp, strike
    """

    df = athena(sql)
    if df.empty:
        print(f"  No data returned for {ticker} in that range.")
        return 0

    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    # Recompute mid safely (bid or ask may be null on expiry-day rows)
    df["mid"] = (df["bid"].fillna(0) + df["ask"].fillna(0)) / 2
    df.loc[df["bid"].isna() | df["ask"].isna(), "mid"] = None

    n = upsert_options_cache(ticker, df)
    print(f"  Upserted {n:,} rows for {ticker}.")
    return n


# ── Trade construction ────────────────────────────────────────────────────────

def build_straddle_trades(
    df: pd.DataFrame,
    dte_target: int = 20,
    dte_tol: int = 5,
    call_delta: float = 0.50,
    entry_weekday: int = 4,      # 0=Mon … 4=Fri
    split_dates: Optional[list] = None,
    max_call_delta_err: float = 0.10,
) -> pd.DataFrame:
    """
    Construct ATM straddle entry/exit records from an options cache DataFrame.

    Parameters
    ----------
    df              Options cache rows (from fetch_options_cache).
    dte_target      Target days to expiry at entry.
    dte_tol         ±tolerance: only accept expiries within [target-tol, target+tol].
    call_delta      Target call delta (0.50 for ATM).  Put uses the same strike.
    entry_weekday   Python weekday int for entry day (4 = Friday).
    split_dates     List of date objects for reverse splits; straddles whose
                    holding period spans a split are flagged split_flag=True.
    max_call_delta_err  Max |actual_delta - call_delta| for the call leg.
                        The put leg is unconstrained (same-strike logic).

    Returns
    -------
    DataFrame with one row per entered straddle:
      entry_date, expiry, actual_dte, strike,
      call_entry_mid, call_entry_bid, call_entry_delta,
      put_entry_mid,  put_entry_bid,  put_entry_delta,
      call_exit_last, put_exit_last,
      missing_exit_data, split_flag
    """
    split_dates = split_dates or []
    df = df.copy()

    # Normalise dates to Python date objects (in case caller passes timestamps)
    for col in ("trade_date", "expiry"):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date

    td_series = pd.to_datetime(df["trade_date"])

    # ── Entry candidates: calls on entry weekday, DTE in window, liquid ──────
    entry_mask = (
        (td_series.dt.dayofweek == entry_weekday)
        & (df["dte"] >= dte_target - dte_tol)
        & (df["dte"] <= dte_target + dte_tol)
        & (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["cp"] == "C")
        & (df["delta"].notna())
    )
    calls = df[entry_mask].copy()
    calls = calls[(calls["delta"] - call_delta).abs() <= max_call_delta_err]
    if calls.empty:
        return pd.DataFrame()

    # Best call per (trade_date, expiry): closest delta to target
    calls["_delta_err"] = (calls["delta"] - call_delta).abs()
    calls = calls.sort_values(["trade_date", "expiry", "_delta_err"])
    calls = calls.drop_duplicates(subset=["trade_date", "expiry"], keep="first")

    # Best expiry per trade_date: DTE closest to target
    calls["_dte_err"] = (calls["dte"] - dte_target).abs()
    calls = calls.sort_values(["trade_date", "_dte_err"])
    calls = calls.drop_duplicates(subset=["trade_date"], keep="first")

    calls = calls.rename(columns={
        "trade_date": "entry_date",
        "dte":        "actual_dte",
        "mid":        "call_entry_mid",
        "bid":        "call_entry_bid",
        "ask":        "call_entry_ask",
        "delta":      "call_entry_delta",
    })[[
        "entry_date", "expiry", "actual_dte", "strike",
        "call_entry_mid", "call_entry_bid", "call_entry_ask", "call_entry_delta",
    ]]

    # ── Matching put at the same (entry_date, expiry, strike) ─────────────────
    put_mask = (
        (td_series.dt.dayofweek == entry_weekday)
        & (df["dte"] >= dte_target - dte_tol)
        & (df["dte"] <= dte_target + dte_tol)
        & (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["cp"] == "P")
    )
    puts = df[put_mask].copy().rename(columns={
        "trade_date": "entry_date",
        "mid":        "put_entry_mid",
        "bid":        "put_entry_bid",
        "ask":        "put_entry_ask",
        "delta":      "put_entry_delta",
    })[[
        "entry_date", "expiry", "strike",
        "put_entry_mid", "put_entry_bid", "put_entry_ask", "put_entry_delta",
    ]]
    # Keep the row with the highest OI if there are dupes (sort bid desc as proxy)
    puts = puts.sort_values(["entry_date", "expiry", "strike", "put_entry_bid"],
                            ascending=[True, True, True, False])
    puts = puts.drop_duplicates(subset=["entry_date", "expiry", "strike"], keep="first")

    straddles = calls.merge(puts, on=["entry_date", "expiry", "strike"], how="inner")
    if straddles.empty:
        return pd.DataFrame()

    # ── Exit prices: option marks on the expiry date itself ───────────────────
    exits = df[df["trade_date"] == df["expiry"]].copy()

    call_exits = (
        exits[exits["cp"] == "C"]
        .groupby(["expiry", "strike"], as_index=False)
        .agg(call_exit_last=("last", "max"), call_exit_mid=("mid", "max"))
    )
    put_exits = (
        exits[exits["cp"] == "P"]
        .groupby(["expiry", "strike"], as_index=False)
        .agg(put_exit_last=("last", "max"), put_exit_mid=("mid", "max"))
    )

    straddles = straddles.merge(call_exits, on=["expiry", "strike"], how="left")
    straddles = straddles.merge(put_exits,  on=["expiry", "strike"], how="left")

    # Flag entries where neither leg has any exit data (possible missing data or still open)
    straddles["missing_exit_data"] = (
        straddles["call_exit_last"].isna() & straddles["put_exit_last"].isna()
    )

    # Fill remaining NaNs with 0 (leg expired worthless, no last trade recorded)
    for col in ("call_exit_last", "put_exit_last", "call_exit_mid", "put_exit_mid"):
        straddles[col] = straddles[col].fillna(0.0).clip(lower=0)

    # ── Split flag ─────────────────────────────────────────────────────────────
    def _spans_split(entry_d: date, expiry_d: date) -> bool:
        return any(entry_d < sd <= expiry_d for sd in split_dates)

    straddles["split_flag"] = [
        _spans_split(r.entry_date, r.expiry)
        for r in straddles.itertuples(index=False)
    ]

    return straddles.sort_values("entry_date").reset_index(drop=True)


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add P&L and risk-adjusted return columns to a straddle trades DataFrame.

    New columns
    -----------
    entry_premium_mid     call_entry_mid + put_entry_mid           (option points)
    entry_premium_worst   call_entry_bid + put_entry_bid           (option points)
    exit_value            max(call_exit_last, call_exit_mid) +
                          max(put_exit_last,  put_exit_mid)        (option points)
    short_pnl_mid         (entry_premium_mid   - exit_value) × 100  ($)
    short_pnl_worst       (entry_premium_worst - exit_value) × 100  ($)
    pnl_pct_mid           short_pnl_mid   / (entry_premium_mid   × 100)
    pnl_pct_worst         short_pnl_worst / (entry_premium_worst × 100)
    margin_reg_t          (0.20 × strike × 100) + (entry_premium_mid × 100)  ($)
    roc                   short_pnl_mid / margin_reg_t
    annualized_roc        roc × 365 / actual_dte
    breakeven_pct         entry_premium_mid / strike  (max move before loss)
    is_win                short_pnl_mid > 0
    is_open               missing_exit_data == True (position not yet settled)
    """
    df = df.copy()

    df["entry_premium_mid"]   = df["call_entry_mid"] + df["put_entry_mid"]
    df["entry_premium_worst"] = df["call_entry_bid"] + df["put_entry_bid"]

    # Best available exit price per leg: prefer last, then mid
    df["call_exit_value"] = df[["call_exit_last", "call_exit_mid"]].max(axis=1)
    df["put_exit_value"]  = df[["put_exit_last",  "put_exit_mid" ]].max(axis=1)
    df["exit_value"]      = df["call_exit_value"] + df["put_exit_value"]

    # Dollar P&L per contract (multiplier = 100)
    df["short_pnl_mid"]   = (df["entry_premium_mid"]   - df["exit_value"]) * 100
    df["short_pnl_worst"] = (df["entry_premium_worst"] - df["exit_value"]) * 100

    # % of premium retained
    df["pnl_pct_mid"]   = df["short_pnl_mid"]   / (df["entry_premium_mid"]   * 100)
    df["pnl_pct_worst"] = df["short_pnl_worst"] / (df["entry_premium_worst"] * 100)

    # Reg T margin: 20% of notional (using ATM strike as spot proxy) + premium received
    df["margin_reg_t"] = (0.20 * df["strike"] * 100) + (df["entry_premium_mid"] * 100)

    # Return on capital
    df["roc"]            = df["short_pnl_mid"] / df["margin_reg_t"]
    df["annualized_roc"] = df["roc"] * 365 / df["actual_dte"].clip(lower=1)

    # Breakeven: how far spot can move in either direction before the straddle loses
    df["breakeven_pct"] = df["entry_premium_mid"] / df["strike"]

    df["is_win"]  = df["short_pnl_mid"] > 0
    df["is_open"] = df["missing_exit_data"].fillna(False)

    return df


# ── Summary output ────────────────────────────────────────────────────────────

def _agg_stats(grp: pd.DataFrame) -> dict:
    closed = grp[~grp["is_open"] & ~grp["split_flag"]]
    if closed.empty:
        return {}
    n      = len(closed)
    wins   = closed["is_win"].sum()
    return {
        "n":              n,
        "win_rate":       wins / n,
        "avg_pnl":        closed["short_pnl_mid"].mean(),
        "avg_pnl_pct":    closed["pnl_pct_mid"].mean(),
        "avg_margin":     closed["margin_reg_t"].mean(),
        "avg_roc":        closed["roc"].mean(),
        "avg_ann_roc":    closed["annualized_roc"].mean(),
        "avg_bkeven_pct": closed["breakeven_pct"].mean(),
    }


def print_summary(df: pd.DataFrame, ticker: str, dte_target: int = 20) -> None:
    if df.empty:
        print("No results.")
        return

    closed   = df[~df["is_open"] & ~df["split_flag"]]
    open_    = df[df["is_open"]]
    flagged  = df[df["split_flag"]]

    width = 76
    bar   = "=" * width

    print(f"\n{bar}")
    print(f"  ATM Short Straddle — {ticker}  ({dte_target} DTE)")
    if not closed.empty:
        d0 = closed["entry_date"].min()
        d1 = closed["entry_date"].max()
        print(f"  Entry range: {d0} → {d1}")
    print(bar)

    # ── Overall stats ─────────────────────────────────────────────────────────
    st = _agg_stats(df)
    if st:
        print(
            f"  Total closed: {st['n']:3d}   "
            f"Win rate: {st['win_rate']*100:5.1f}%   "
            f"Avg P&L: ${st['avg_pnl']:7.2f}  ({st['avg_pnl_pct']*100:+.1f}%)"
        )
        print(
            f"  Avg margin:  ${st['avg_margin']:7.0f}   "
            f"Avg ROC: {st['avg_roc']*100:+5.2f}%   "
            f"Ann ROC: {st['avg_ann_roc']*100:+6.1f}%   "
            f"Breakeven: {st['avg_bkeven_pct']*100:.1f}%"
        )
    print()

    # ── Per-year breakdown ────────────────────────────────────────────────────
    hdr = (
        f"  {'Year':>4}  {'N':>3}  {'WinR%':>6}  "
        f"{'AvgP&L':>8}  {'P&L%':>6}  "
        f"{'AvgMgn':>8}  {'ROC%':>6}  {'AnnROC%':>8}  {'BkEv%':>6}"
    )
    print(hdr)
    print("  " + "-" * (width - 2))

    closed = closed.copy()
    closed["_year"] = pd.to_datetime(closed["entry_date"]).dt.year
    for yr, grp in closed.groupby("_year"):
        s = _agg_stats(grp)
        if not s:
            continue
        print(
            f"  {yr:>4}  {s['n']:>3}  {s['win_rate']*100:>5.1f}%  "
            f"${s['avg_pnl']:>7.2f}  {s['avg_pnl_pct']*100:>+5.1f}%  "
            f"${s['avg_margin']:>7.0f}  {s['avg_roc']*100:>+5.2f}%  "
            f"{s['avg_ann_roc']*100:>+7.1f}%  {s['avg_bkeven_pct']*100:>5.1f}%"
        )

    print("  " + "-" * (width - 2))

    if not open_.empty:
        open_pnl = open_["short_pnl_mid"].sum()
        print(f"\n  Open (no exit data yet): {len(open_)}  MTM P&L: ${open_pnl:.2f}")

    if not flagged.empty:
        print(
            f"\n  Split-spanning (excluded): {len(flagged)} trades — "
            + ", ".join(str(r.entry_date) for r in flagged.itertuples())
        )

    print(f"{bar}\n")


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_study(
    ticker: str,
    start: date,
    end: date,
    dte_target: int = 20,
    dte_tol: int = 5,
    call_delta: float = 0.50,
    entry_weekday: int = 4,
    split_dates: Optional[list] = None,
    max_call_delta_err: float = 0.10,
    output_csv: Optional[str] = None,
    force_sync: bool = False,
) -> pd.DataFrame:
    """
    Full pipeline: sync → fetch → build trades → metrics → print → CSV.

    Returns the full trades DataFrame (including open and split-flagged rows).
    """
    from lib.mysql_lib import fetch_options_cache

    # 1. Sync options data (Athena → MySQL)
    sync_options_cache(ticker, start, force=force_sync)

    # 2. Fetch from MySQL — extend end by dte_target + dte_tol days so that
    #    exit prices for the last batch of entries are included.
    fetch_end = end + timedelta(days=dte_target + dte_tol + 5)
    print(f"Loading {ticker} options from MySQL ({start} → {fetch_end}) ...")
    df_opts = fetch_options_cache(ticker, start, fetch_end)
    if df_opts.empty:
        print("No options data found. Aborting.")
        return pd.DataFrame()
    print(f"  {len(df_opts):,} rows loaded.")

    # 3. Build entry/exit pairs
    print("Building straddle trades ...")
    trades = build_straddle_trades(
        df_opts,
        dte_target=dte_target,
        dte_tol=dte_tol,
        call_delta=call_delta,
        entry_weekday=entry_weekday,
        split_dates=split_dates,
        max_call_delta_err=max_call_delta_err,
    )
    # Drop entries after the requested study end date
    if not trades.empty:
        trades = trades[trades["entry_date"] <= end].reset_index(drop=True)

    if trades.empty:
        print("No straddle trades could be constructed.")
        return pd.DataFrame()

    # 4. Compute metrics
    trades = compute_metrics(trades)

    # 5. Print summary
    print_summary(trades, ticker, dte_target)

    # 6. Save to CSV
    if output_csv:
        # Column order: key info first, then pricing, then metrics
        col_order = [
            "entry_date", "expiry", "actual_dte", "strike",
            "call_entry_delta", "put_entry_delta",
            "call_entry_mid", "call_entry_bid",
            "put_entry_mid",  "put_entry_bid",
            "entry_premium_mid", "entry_premium_worst",
            "call_exit_last", "put_exit_last", "exit_value",
            "short_pnl_mid", "short_pnl_worst",
            "pnl_pct_mid", "pnl_pct_worst",
            "margin_reg_t", "roc", "annualized_roc", "breakeven_pct",
            "is_win", "is_open", "split_flag", "missing_exit_data",
        ]
        save_cols = [c for c in col_order if c in trades.columns]
        trades[save_cols].to_csv(output_csv, index=False)
        print(f"Saved {len(trades)} rows to {output_csv}")

    return trades

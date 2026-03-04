"""
Delta-hedged ATM straddle backtest.

Strategy
--------
- Entry:   each Friday in the study window
- Structure: sell 30-DTE ATM straddle (call_delta≈0.50, same strike for put)
- Hedge:   delta-neutral at end of each trading day via underlying shares
             hedge_shares = -(call_delta + put_delta) * 100
- Hold:    to expiry (daily P&L is tracked so early-exit variants can be layered in)

Daily P&L
---------
  straddle_pnl = (straddle_mid_prev - straddle_mid_today) * 100   [short]
  hedge_pnl    = hedge_shares_prev * (stock_today - stock_prev)
  daily_pnl    = straddle_pnl + hedge_pnl

At expiry, straddle terminal value = max(S-K, 0) + max(K-S, 0) = |S - K|.

Data / caching
--------------
  data/cache/{ticker}_options.parquet  — Athena option daily marks
  data/cache/{ticker}_stock.parquet    — Tradier underlying closes

Both caches store the full fetched date range.  On subsequent calls with the
same or narrower date range the data is served from disk; a wider range
triggers a re-fetch.  Pass force_refresh=True to always re-fetch.

Usage
-----
  from lib.studies.delta_hedged_straddle import run_study, print_summary
  results = run_study("KWEB", months_back=3)
  print_summary(results, "KWEB")
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Cache location ────────────────────────────────────────────────────────────

# Resolve to repo root regardless of where the script is invoked from
_REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR  = _REPO_ROOT / "data" / "cache"


def _cache_path(ticker: str, kind: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{ticker}_{kind}.parquet"


# ── Data fetchers ─────────────────────────────────────────────────────────────

def fetch_option_data(
    ticker: str,
    start: date,
    end: date,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetch daily option rows for *ticker* over [start, end] from Athena.
    Cached to data/cache/{ticker}_options.parquet.

    Columns returned:
      trade_date, expiry, cp, strike, bid, ask, last, delta,
      open_interest, volume, mid
    """
    cache_file = _cache_path(ticker, "options")

    if cache_file.exists() and not force_refresh:
        df = pd.read_parquet(cache_file)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df["expiry"]     = pd.to_datetime(df["expiry"])
        c_start = df["trade_date"].min()
        c_end   = df["trade_date"].max()
        # Accept the cache if the start is covered AND the end is within 7 days
        # of what's cached (Athena EOD data lags a day or two, so the cached
        # max_date may be slightly before the requested end).
        end_gap = (pd.Timestamp(end) - c_end).days
        if pd.Timestamp(start) >= c_start and end_gap <= 7:
            print(f"Options cache hit ({ticker}): {c_start.date()} – {c_end.date()}")
            mask = (df["trade_date"] >= pd.Timestamp(start)) & \
                   (df["trade_date"] <= pd.Timestamp(end))
            return df[mask].copy()
        print(f"Options cache miss: cached {c_start.date()}–{c_end.date()}, "
              f"need {start}–{end}. Re-fetching...")

    print(f"Fetching option data for {ticker} from Athena ({start} → {end})...")
    from lib.athena_lib import athena
    from lib.constants import DB, TABLE

    # Fetch all near-term options (expiry within 65 days of trade_date) with
    # basic liquidity filters.  65-day window covers any DTE up to ~55 with
    # buffer, so the cache stays useful if the study parameters change.
    sql = f"""
    SELECT
        trade_date,
        expiry,
        cp,
        CAST(strike         AS DOUBLE)  AS strike,
        CAST(bid            AS DOUBLE)  AS bid,
        CAST(ask            AS DOUBLE)  AS ask,
        CAST(last           AS DOUBLE)  AS last,
        CAST(delta          AS DOUBLE)  AS delta,
        CAST(open_interest  AS BIGINT)  AS open_interest,
        CAST(volume         AS BIGINT)  AS volume
    FROM "{DB}"."{TABLE}"
    WHERE ticker = '{ticker}'
      AND trade_date >= TIMESTAMP '{start.isoformat()} 00:00:00'
      AND trade_date <= TIMESTAMP '{end.isoformat()} 00:00:00'
      AND bid   > 0
      AND ask   > 0
      AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) <= 65
    ORDER BY trade_date, expiry, cp, strike
    """
    df = athena(sql)

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["expiry"]     = pd.to_datetime(df["expiry"])
    df["mid"]        = (df["bid"] + df["ask"]) / 2

    print(f"  {len(df):,} rows. Caching to {cache_file.name}")
    df.to_parquet(cache_file, index=False, compression="snappy")
    return df


def fetch_stock_data(
    ticker: str,
    start: date,
    end: date,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV for the underlying from Tradier.
    Cached to data/cache/{ticker}_stock.parquet.
    Index: trade_date (DatetimeIndex); columns: open, high, low, close, volume.
    """
    cache_file = _cache_path(ticker, "stock")

    if cache_file.exists() and not force_refresh:
        df = pd.read_parquet(cache_file)
        df.index = pd.to_datetime(df.index)
        c_start = df.index.min()
        c_end   = df.index.max()
        if pd.Timestamp(start) >= c_start and pd.Timestamp(end) <= c_end:
            print(f"Stock cache hit ({ticker}): {c_start.date()} – {c_end.date()}")
            return df.loc[pd.Timestamp(start):pd.Timestamp(end)].copy()
        print(f"Stock cache miss: cached {c_start.date()}–{c_end.date()}, "
              f"need {start}–{end}. Re-fetching...")

    print(f"Fetching stock data for {ticker} from Tradier ({start} → {end})...")
    from lib.tradier.get_daily_history import get_daily_history
    from lib.tradier.tradier_client_wrapper import TradierClient

    api_key = os.environ["TRADIER_API_KEY"]

    async def _fetch():
        async with TradierClient(api_key=api_key) as client:
            return await get_daily_history(ticker, start, end, client=client)

    df = asyncio.run(_fetch())
    if df is None or df.empty:
        raise RuntimeError(f"No stock data returned for {ticker} from Tradier")

    df.index = pd.to_datetime(df.index)
    df.index.name = "trade_date"
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"  {len(df)} trading days. Caching to {cache_file.name}")
    df.to_parquet(cache_file, compression="snappy")
    return df


# ── Entry / straddle selection ────────────────────────────────────────────────

def find_entry_dates(start: date, end: date, weekday: int = 4) -> list[date]:
    """All dates in [start, end] falling on *weekday* (0=Mon, 4=Fri)."""
    d, result = start, []
    while d <= end:
        if d.weekday() == weekday:
            result.append(d)
        d += timedelta(days=1)
    return result


def select_atm_straddle(
    options_df: pd.DataFrame,
    stock_df: pd.DataFrame,
    entry_date: date,
    dte: int = 30,
) -> Optional[dict]:
    """
    On *entry_date*, find the ATM straddle with expiry closest to *dte* days out.

    ATM = the call whose delta is closest to 0.50 on that expiry; the put leg
    uses the same strike.  Returns None if no valid straddle can be formed.
    """
    entry_ts = pd.Timestamp(entry_date)

    if entry_ts not in stock_df.index:
        return None
    spot = float(stock_df.loc[entry_ts, "close"])

    day_opts = options_df[options_df["trade_date"] == entry_ts]
    if day_opts.empty:
        return None

    # Expiry closest to entry + dte days
    target_expiry = entry_ts + pd.Timedelta(days=dte)
    available     = day_opts["expiry"].unique()
    best_expiry   = min(available, key=lambda e: abs((e - target_expiry).days))

    # Call leg: delta closest to 0.50
    calls = day_opts[(day_opts["expiry"] == best_expiry) & (day_opts["cp"] == "C")].copy()
    if calls.empty:
        return None
    calls["delta_err"] = (calls["delta"] - 0.50).abs()
    atm_call = calls.sort_values("delta_err").iloc[0]
    strike   = float(atm_call["strike"])

    # Put leg: same strike
    puts = day_opts[
        (day_opts["expiry"] == best_expiry) &
        (day_opts["cp"]     == "P") &
        (day_opts["strike"] == strike)
    ]
    if puts.empty:
        return None
    atm_put = puts.iloc[0]

    return {
        "entry_date":        entry_date,
        "expiry":            best_expiry.date(),
        "strike":            strike,
        "actual_dte":        (best_expiry - entry_ts).days,
        "spot_at_entry":     round(spot, 2),
        "call_entry_mid":    round(float(atm_call["mid"]), 4),
        "put_entry_mid":     round(float(atm_put["mid"]), 4),
        "straddle_premium":  round(float(atm_call["mid"]) + float(atm_put["mid"]), 4),
        "call_entry_delta":  round(float(atm_call["delta"]), 4),
        "put_entry_delta":   round(float(atm_put["delta"]), 4),
    }


# ── Position simulation ───────────────────────────────────────────────────────

def simulate_position(
    options_df: pd.DataFrame,
    stock_df: pd.DataFrame,
    entry: dict,
) -> Optional[dict]:
    """
    Simulate a delta-hedged straddle day by day from entry to expiry (or
    last available data date for still-open positions).

    Returns a dict with summary fields plus a 'daily' list of per-day records.
    Returns None if there is insufficient data to run even one day.
    """
    entry_ts   = pd.Timestamp(entry["entry_date"])
    expiry_ts  = pd.Timestamp(entry["expiry"])
    strike     = entry["strike"]
    today_ts   = pd.Timestamp(date.today())

    # Window: entry date through min(expiry, today)
    sim_end = min(expiry_ts, today_ts)
    window  = stock_df.loc[entry_ts:sim_end]
    if len(window) < 2:
        return None

    is_closed = (expiry_ts <= today_ts)

    # Option data for this specific strike + expiry
    pos_opts = options_df[
        (options_df["expiry"]  == expiry_ts) &
        (options_df["strike"]  == strike)
    ].set_index(["trade_date", "cp"])

    # ── Day 0: establish position ─────────────────────────────────────────────
    try:
        call_d0 = pos_opts.loc[(entry_ts, "C")]
        put_d0  = pos_opts.loc[(entry_ts, "P")]
    except KeyError:
        return None

    straddle_mid_prev = float(call_d0["mid"]) + float(put_d0["mid"])
    net_delta_prev    = float(call_d0["delta"]) + float(put_d0["delta"])
    hedge_shares      = -net_delta_prev * 100   # shares held after entry-day close
    prev_stock        = float(window.iloc[0]["close"])

    daily_records = []
    total_pnl     = 0.0
    data_gaps     = 0

    # ── Day 1 → expiry ────────────────────────────────────────────────────────
    for curr_ts, row in window.iloc[1:].iterrows():
        curr_stock     = float(row["close"])
        at_expiry      = (curr_ts >= expiry_ts)

        hedge_pnl = hedge_shares * (curr_stock - prev_stock)

        if at_expiry:
            # Settle at intrinsic value
            straddle_mid_curr = max(curr_stock - strike, 0.0) + max(strike - curr_stock, 0.0)
            curr_call_delta   = 1.0 if curr_stock > strike else 0.0
            curr_put_delta    = -1.0 if curr_stock < strike else 0.0
        else:
            try:
                c = pos_opts.loc[(curr_ts, "C")]
                p = pos_opts.loc[(curr_ts, "P")]
                straddle_mid_curr = float(c["mid"]) + float(p["mid"])
                curr_call_delta   = float(c["delta"])
                curr_put_delta    = float(p["delta"])
            except KeyError:
                # Data gap — carry forward previous mid and delta
                straddle_mid_curr = straddle_mid_prev
                curr_call_delta   = net_delta_prev / 2
                curr_put_delta    = net_delta_prev / 2
                data_gaps += 1

        straddle_pnl  = (straddle_mid_prev - straddle_mid_curr) * 100
        daily_pnl     = straddle_pnl + hedge_pnl
        total_pnl    += daily_pnl

        daily_records.append({
            "date":          curr_ts.date(),
            "stock_close":   round(curr_stock, 4),
            "straddle_mid":  round(straddle_mid_curr, 4),
            "net_delta":     round(curr_call_delta + curr_put_delta, 4),
            "hedge_shares":  round(hedge_shares, 2),
            "straddle_pnl":  round(straddle_pnl, 2),
            "hedge_pnl":     round(hedge_pnl, 2),
            "daily_pnl":     round(daily_pnl, 2),
            "cum_pnl":       round(total_pnl, 2),
        })

        # Rebalance hedge for next day
        net_delta_prev    = curr_call_delta + curr_put_delta
        hedge_shares      = -net_delta_prev * 100
        straddle_mid_prev = straddle_mid_curr
        prev_stock        = curr_stock

        if at_expiry:
            break

    if not daily_records:
        return None

    status = ("WIN" if total_pnl > 0 else "LOSS") if is_closed else "OPEN"

    return {
        "entry_date":       entry["entry_date"],
        "expiry":           entry["expiry"],
        "strike":           strike,
        "actual_dte":       entry["actual_dte"],
        "straddle_premium": entry["straddle_premium"],
        "spot_at_entry":    entry["spot_at_entry"],
        "total_pnl":        round(total_pnl, 2),
        "status":           status,
        "data_gaps":        data_gaps,
        "daily":            daily_records,
    }


# ── Study orchestrator ────────────────────────────────────────────────────────

def run_study(
    ticker: str,
    months_back: int = 3,
    dte: int = 30,
    force_refresh: bool = False,
) -> list[dict]:
    """
    Run the delta-hedged ATM straddle study for *ticker*.

    Returns a list of position dicts (one per weekly entry), each containing:
      entry_date, expiry, strike, straddle_premium, spot_at_entry,
      actual_dte, total_pnl, status ('WIN'|'LOSS'|'OPEN'), data_gaps,
      daily  (list of per-day records for the full simulation window)
    """
    end   = date.today()
    start = end - timedelta(days=months_back * 31)

    options_df = fetch_option_data(ticker, start, end, force_refresh=force_refresh)
    stock_df   = fetch_stock_data(ticker, start, end, force_refresh=force_refresh)

    entry_dates = find_entry_dates(start, end, weekday=4)
    print(f"\n{len(entry_dates)} Friday entries in window {start} → {end}")

    results, skipped = [], 0
    for entry_date in entry_dates:
        entry = select_atm_straddle(options_df, stock_df, entry_date, dte=dte)
        if entry is None:
            skipped += 1
            continue
        pos = simulate_position(options_df, stock_df, entry)
        if pos is None:
            skipped += 1
            continue
        results.append(pos)

    closed = sum(1 for r in results if r["status"] != "OPEN")
    open_  = sum(1 for r in results if r["status"] == "OPEN")
    print(f"  Simulated: {len(results)}  (closed: {closed}, open: {open_})  "
          f"Skipped (no data): {skipped}")
    return results


# ── Output ────────────────────────────────────────────────────────────────────

def print_summary(results: list[dict], ticker: str) -> None:
    if not results:
        print("No results.")
        return

    closed = [r for r in results if r["status"] != "OPEN"]
    open_  = [r for r in results if r["status"] == "OPEN"]

    wins   = sum(1 for r in closed if r["status"] == "WIN")
    total_closed = len(closed)
    total_pnl    = sum(r["total_pnl"] for r in closed)

    print(f"\n{'='*72}")
    print(f"  Delta-Hedged ATM Straddle Study — {ticker}")
    print(f"{'='*72}")
    print(f"  {'Entry':<12} {'Expiry':<12} {'Strike':>7} {'DTE':>4} "
          f"{'Premium':>9} {'Spot':>8} {'P&L':>9}  Status")
    print(f"  {'-'*68}")

    for r in results:
        prem_usd = r["straddle_premium"] * 100
        print(f"  {str(r['entry_date']):<12} {str(r['expiry']):<12} "
              f"{r['strike']:>7.2f} {r['actual_dte']:>4} "
              f"${prem_usd:>7.2f}  "
              f"${r['spot_at_entry']:>7.2f} "
              f"${r['total_pnl']:>8.2f}  {r['status']}")

    print(f"  {'-'*68}")
    if total_closed:
        avg_pnl  = total_pnl / total_closed
        avg_win  = sum(r["total_pnl"] for r in closed if r["status"] == "WIN") / max(wins, 1)
        avg_loss = sum(r["total_pnl"] for r in closed if r["status"] == "LOSS") / max(total_closed - wins, 1)
        avg_prem = sum(r["straddle_premium"] for r in closed) / total_closed * 100
        print(f"  Closed positions:  {total_closed}   "
              f"Win rate: {wins}/{total_closed} = {wins/total_closed*100:.0f}%")
        print(f"  Total P&L: ${total_pnl:.2f}   Avg/trade: ${avg_pnl:.2f}")
        print(f"  Avg premium: ${avg_prem:.2f}   "
              f"Avg winner: ${avg_win:.2f}   Avg loser: ${avg_loss:.2f}")
    if open_:
        open_pnl = sum(r["total_pnl"] for r in open_)
        print(f"  Open positions:    {len(open_)}   "
              f"Current mark-to-market P&L: ${open_pnl:.2f}")
    print(f"{'='*72}\n")

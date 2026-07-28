"""
Minervini Trend Template scan — shared core.

Single source of truth for the full-market daily-bar matrix (Polygon grouped
daily aggregates, incremental) and the Trend Template screen. Imported by:
  - run_minervini_scan.py         (local CLI)
  - lib.interface.refresh_lambda  (nightly cloud refresh)

The day-matrix is four wide DataFrames (date x ticker): close, high, low,
dolvol — persisted as one parquet with hierarchical columns. `pull_matrices`
is incremental: pass `prior` frames and it fetches only missing sessions,
strictly serial at `pace` seconds/call (free Polygon tier ~5 req/min).

`pull_matrices` also returns the day's LONG-format rows (with open/volume/vwap,
which the wide matrix does not store) so callers can append them to the
silver.equity_daily Iceberg table.
"""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Callable, List, Optional, Tuple

import pandas as pd

# NYSE full-closure holidays. Probing these wastes the rate budget and, worse,
# a 429 during the probe reads as a "failed day" that blocks the screen.
MARKET_HOLIDAYS = {
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
    "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
}

LONG_COLS = ["trade_date", "ticker", "open", "high", "low", "close", "volume", "vwap", "dollar_volume"]


def trading_dates(lookback_days: int) -> List[str]:
    end = date.today()
    days = []
    d = end
    while d > end - timedelta(days=lookback_days):
        if d.weekday() < 5 and d.isoformat() not in MARKET_HOLIDAYS:
            days.append(d.isoformat())
        d -= timedelta(days=1)
    return days


def _merge_frames(prior, records):
    """Pivot new (day, ticker, c, h, l, dolvol) records and merge onto prior frames."""
    if not records:
        return prior
    df = pd.DataFrame.from_records(
        records, columns=["date", "ticker", "close", "high", "low", "dolvol"])
    df["date"] = pd.to_datetime(df["date"])
    new = tuple(
        df.pivot(index="date", columns="ticker", values=v).sort_index()
        for v in ("close", "high", "low", "dolvol"))
    if prior is None:
        return new
    merged = []
    for old, n in zip(prior, new):
        m = pd.concat([old, n])
        m = m[~m.index.duplicated(keep="last")].sort_index()
        merged.append(m)
    return tuple(merged)


def pull_matrices(client, universe: set, lookback_days: int, pace: float,
                  prior=None, checkpoint_fn: Optional[Callable] = None,
                  max_days: Optional[int] = None,
                  log: Callable[[str], None] = print):
    """
    Incrementally extend the day-matrix. Returns (frames, failed_days, long_rows)
    where long_rows is a DataFrame (LONG_COLS) of every session fetched this run
    — the feed for silver.equity_daily.

    checkpoint_fn(frames) is called every 25 fetched days so a killed run
    resumes from the last checkpoint. max_days caps this run's fetch count
    (Lambda time budget); leftover days are picked up next run.
    """
    dates = trading_dates(lookback_days)
    have = set()
    if prior is not None:
        have = {d.strftime("%Y-%m-%d") for d in prior[0].index}
    todo = [d for d in dates if d not in have]
    deferred = 0
    if max_days is not None and len(todo) > max_days:
        todo_sorted = sorted(todo, reverse=True)      # newest first
        deferred = len(todo) - max_days
        todo = todo_sorted[:max_days]
    log(f"{len(dates)} trading days in window; {len(have)} cached; pulling {len(todo)} "
        f"at {pace:.1f}s pace (~{len(todo) * pace / 60:.0f} min)"
        + (f"; {deferred} deferred to future runs" if deferred else ""))

    def fetch(day):
        for attempt in range(6):
            try:
                return day, client.get_grouped_daily_aggs(day, adjusted=True)
            except Exception:
                time.sleep(min(2 ** attempt, 60))
        return day, None

    records, long_recs, failed = [], [], []
    for i, d in enumerate(todo):
        day, rows = fetch(d)
        if rows is None:
            failed.append(day)
        else:
            for r in rows:
                if r.ticker in universe and r.close and r.volume:
                    records.append((day, r.ticker, r.close, r.high, r.low,
                                    r.close * r.volume))
                    long_recs.append((day, r.ticker, r.open, r.high, r.low,
                                      r.close, r.volume, getattr(r, "vwap", None),
                                      r.close * r.volume))
        if (i + 1) % 25 == 0:
            prior = _merge_frames(prior, records)
            records = []
            if checkpoint_fn is not None:
                checkpoint_fn(prior)
            log(f"  {i + 1}/{len(todo)} days ({len(failed)} failed) [checkpointed]")
        if i + 1 < len(todo):
            time.sleep(pace)

    frames = _merge_frames(prior, records)
    if frames is None:
        raise RuntimeError("no data pulled and no cache to fall back on")

    cutoff = pd.Timestamp(date.today() - timedelta(days=lookback_days))
    frames = tuple(f[f.index >= cutoff] for f in frames)
    long_rows = pd.DataFrame.from_records(long_recs, columns=LONG_COLS)
    log(f"  matrix: {frames[0].shape[0]} sessions x {frames[0].shape[1]} tickers; "
        f"{len(long_rows)} long rows this run")
    return frames, failed, long_rows


# Cache format: LONG parquet (date, ticker, close, high, low, dolvol). The old
# wide format (~21k MultiIndex columns) segfaults pyarrow inside Lambda; long is
# narrow, standard, and pivots to wide in ~2s of pure pandas on load.

def save_cache(frames, path: str) -> None:
    close, high, low, dolvol = frames
    parts = {"close": close.stack(), "high": high.stack(),
             "low": low.stack(), "dolvol": dolvol.stack()}
    long_df = pd.DataFrame(parts).reset_index()
    long_df.columns = ["date", "ticker", "close", "high", "low", "dolvol"]
    long_df.to_parquet(path, index=False)


def load_cache(path: str):
    store = pd.read_parquet(path)
    if isinstance(store.columns, pd.MultiIndex):      # legacy wide format
        return (store["close"], store["high"], store["low"], store["dolvol"])
    return tuple(
        store.pivot(index="date", columns="ticker", values=v).sort_index()
        for v in ("close", "high", "low", "dolvol"))


def build_table(close, high, low, dolvol, slope_days: int) -> pd.DataFrame:
    def last(s):
        return s.iloc[-1]

    sma50 = close.rolling(50, min_periods=50).mean()
    sma150 = close.rolling(150, min_periods=150).mean()
    sma200 = close.rolling(200, min_periods=200).mean()
    hi252 = high.rolling(252, min_periods=200).max()
    lo252 = low.rolling(252, min_periods=200).min()
    addv = dolvol.rolling(50, min_periods=50).mean()

    price = last(close)
    t = pd.DataFrame(index=close.columns)
    t["price"] = price
    t["sma50"] = last(sma50)
    t["sma150"] = last(sma150)
    t["sma200"] = last(sma200)
    t["sma200_prev"] = sma200.iloc[-1 - slope_days] if len(sma200) > slope_days else float("nan")
    t["hi252"] = last(hi252)
    t["lo252"] = last(lo252)
    t["addv"] = last(addv)

    def ratio(n):
        return close.iloc[-1] / close.iloc[-1 - n] if len(close) > n else pd.Series(index=close.columns, dtype=float)
    rs = 2 * ratio(63) + ratio(126) + ratio(189) + ratio(252)
    t["rs_score"] = rs
    t["rs_pct"] = rs.rank(pct=True) * 100.0
    return t


def screen(t: pd.DataFrame, rs_min: float, addv_min: float) -> pd.DataFrame:
    c = pd.DataFrame(index=t.index)
    c["c1"] = (t.price > t.sma150) & (t.price > t.sma200)
    c["c2"] = t.sma150 > t.sma200
    c["c3"] = t.sma200 > t.sma200_prev
    c["c4"] = (t.sma50 > t.sma150) & (t.sma150 > t.sma200)
    c["c5"] = t.price > t.sma50
    c["c6"] = t.price >= 1.30 * t.lo252
    c["c7"] = t.price >= 0.75 * t.hi252
    c["c8"] = t.rs_pct >= rs_min
    c["cL"] = t.addv > addv_min
    out = t.join(c)
    out["pass_all"] = c.all(axis=1)
    return out

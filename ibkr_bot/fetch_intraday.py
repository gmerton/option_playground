#!/usr/bin/env python3
"""
Pull 1-minute intraday bars for one or more symbols from IBKR and save to CSV.

Exploratory data tool for model-building (not part of the live monitor). Saves
each symbol's RTH 1-min bars for the most recent trading day to
ibkr_bot/data/<SYMBOL>_<YYYY-MM-DD>_1min.csv and prints a quick profile of the
session (open drop, intraday low/high, and the move off the low).

Usage:
  .venv/bin/python3 ibkr_bot/fetch_intraday.py PL
  .venv/bin/python3 ibkr_bot/fetch_intraday.py PL AVGO --days 5
  .venv/bin/python3 ibkr_bot/fetch_intraday.py SMCI --end-date 2024-02-16   # historical session
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from ib_async import Stock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _bars_to_df(bars) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "time": b.date,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "wap": b.average,
            }
            for b in bars
        ]
    )
    df["time"] = pd.to_datetime(df["time"])
    return df


def _profile(sym: str, df: pd.DataFrame) -> None:
    """Print a quick narrative of the session shape."""
    if df.empty:
        print(f"  {sym}: no bars")
        return
    day = df["time"].dt.date.iloc[-1]
    sess = df[df["time"].dt.date == day].reset_index(drop=True)
    o = sess["open"].iloc[0]
    lo_i = sess["low"].idxmin()
    hi_i = sess["high"].idxmax()
    lo = sess["low"].iloc[lo_i]
    hi = sess["high"].iloc[hi_i]
    last = sess["close"].iloc[-1]
    lo_t = sess["time"].iloc[lo_i].strftime("%H:%M")
    hi_t = sess["time"].iloc[hi_i].strftime("%H:%M")
    print(f"  {sym}  {day}  ({len(sess)} bars)")
    print(f"    open {o:.2f}  ->  low {lo:.2f} @ {lo_t} ({(lo/o-1)*100:+.1f}%)"
          f"  ->  high {hi:.2f} @ {hi_t}  ->  close {last:.2f}")
    if hi_i > lo_i:
        print(f"    move off low: {(hi/lo-1)*100:+.1f}% over "
              f"{hi_i - lo_i} min (low precedes high -- the rally you saw)")
    else:
        print(f"    high precedes low (sold off into the close)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--days", type=int, default=1, help="trading days of history")
    ap.add_argument("--end-date", default=None,
                    help="pull the session ENDING on this date (YYYY-MM-DD); "
                         "default = most recent session")
    args = ap.parse_args()
    symbols = [s.upper() for s in args.symbols]

    # IB wants the bar window's END. To capture the full RTH of --end-date, end at
    # that day's close (20:00 UTC ~ 16:00 ET; IB treats the date as the cutoff).
    end_dt = ""
    if args.end_date:
        end_dt = f"{args.end_date.replace('-', '')} 23:59:59 US/Eastern"

    os.makedirs(DATA_DIR, exist_ok=True)
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "13")))
    print(f"OK Connected (paper {ib.managedAccounts()}).\n")

    for sym in symbols:
        contract = Stock(sym, "SMART", "USD")
        if not ib.qualifyContracts(contract):
            print(f"  x {sym}: could not qualify -- skipping")
            continue
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_dt,
            durationStr=f"{args.days} D",
            barSizeSetting="1 min",
            whatToShow="TRADES",
            useRTH=True,
            keepUpToDate=False,
        )
        if not bars:
            print(f"  ! {sym}: no bars returned")
            continue
        df = _bars_to_df(bars)
        day = df["time"].dt.date.iloc[-1]
        out = os.path.join(DATA_DIR, f"{sym}_{day}_1min.csv")
        df.to_csv(out, index=False)
        _profile(sym, df)
        print(f"    saved {len(df)} bars -> {out}\n")

    ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

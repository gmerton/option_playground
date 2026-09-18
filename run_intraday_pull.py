#!/usr/bin/env python3
"""
Long-history 1-minute RTH bars from IBKR, one month per request, resumable (2026-09-17, QQQ intraday project).

IBKR serves 1-min TRADES bars back to the head timestamp (QQQ 1999) at ~10s per month-long request. Each month
lands in data/cache/intraday_hist/<SYM>/<SYM>_<YYYY-MM>.parquet; a finished month is never re-requested, so the
pull can be killed and restarted. `--consolidate` stitches a symbol into data/cache/intraday_hist/<SYM>_1min.parquet
(~35 MB for 2007->today). Bars are split-adjusted by IBKR, not dividend-adjusted (irrelevant intraday). Read-only.

Usage (TWS live 7496):
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src:. .venv/bin/python3 run_intraday_pull.py QQQ SPY TQQQ SQQQ --start 2007-01
"""
from __future__ import annotations
import argparse, os, sys, time
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot"))
from ib_async import Stock, util
from conn import connect_ib

ROOT = "data/cache/intraday_hist"


def consolidate(sym: str) -> None:
    d = os.path.join(ROOT, sym)
    parts = [pd.read_parquet(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".parquet")]
    parts = [p for p in parts if len(p)]
    if not parts:
        return
    df = pd.concat(parts).drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    out = os.path.join(ROOT, f"{sym}_1min.parquet"); df.to_parquet(out, index=False)
    print(f"{sym}: {len(df):,} bars  {df['ts'].iloc[0]} -> {df['ts'].iloc[-1]}  {df['ts'].dt.date.nunique():,} sessions  {os.path.getsize(out)/1e6:.1f} MB", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("symbols", nargs="+"); ap.add_argument("--start", default="2007-01")
    ap.add_argument("--client-id", type=int, default=54); ap.add_argument("--consolidate-only", action="store_true"); a = ap.parse_args()
    if a.consolidate_only:
        for s in a.symbols: consolidate(s.upper())
        return 0
    ib = connect_ib(client_id=a.client_id, timeout=20)
    this_month = pd.Timestamp.today().to_period("M")
    for sym in [s.upper() for s in a.symbols]:
        os.makedirs(os.path.join(ROOT, sym), exist_ok=True)
        c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
        head = pd.Timestamp(ib.reqHeadTimeStamp(c, "TRADES", True, 1)).to_period("M")
        months = pd.period_range(max(pd.Period(a.start, "M"), head), this_month, freq="M")
        for m in months[::-1]:                       # newest first: the recent years are usable early
            f = os.path.join(ROOT, sym, f"{sym}_{m}.parquet")
            if os.path.exists(f) and m != this_month:
                continue
            end = (m.end_time.normalize() + pd.Timedelta(days=1)).strftime("%Y%m%d 00:00:00 US/Eastern")
            t0 = time.time()
            for attempt in range(3):
                try:
                    bars = ib.reqHistoricalData(c, endDateTime=end, durationStr="1 M", barSizeSetting="1 min", whatToShow="TRADES",
                                                useRTH=True, formatDate=1, timeout=180); break
                except Exception as exc:  # noqa: BLE001
                    print(f"  {sym} {m} attempt {attempt+1}: {type(exc).__name__} {exc}", flush=True); time.sleep(30); bars = None
            if bars is None:
                continue
            df = util.df(bars) if bars else pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "average", "barCount"])
            if len(df):
                df["ts"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("US/Eastern").dt.tz_localize(None)
                df = df[df["ts"].dt.to_period("M") == m][["ts", "open", "high", "low", "close", "volume", "average", "barCount"]]
            else:
                df = pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume", "average", "barCount"])
            df.to_parquet(f, index=False)
            print(f"  {sym} {m}: {len(df):,} bars  {time.time()-t0:.0f}s", flush=True)
            time.sleep(max(0.0, 10.5 - (time.time() - t0)))   # IBKR pacing: <= 60 historical requests / 10 min
        consolidate(sym)
    ib.disconnect(); return 0


if __name__ == "__main__":
    sys.exit(main())

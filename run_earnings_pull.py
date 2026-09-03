#!/usr/bin/env python3
"""
Earnings-date pull for the straddle pool → MySQL `earnings_report` (currently empty).

Source: Tradier corporate calendar (`/beta/markets/fundamentals/calendars`).
Chosen after Polygon's Benzinga earnings endpoint returned "not entitled" on the
free-tier key, and SEC EDGAR would require fetching every 8-K to test for Item 2.02.

EXTRACTION NOTES
  * event_type codes are NOT reliable — 7, 9, 10, 12, 13, 14 all appear on earnings
    rows for a single ticker. Filter on the event TEXT containing "earnings".
  * The same quarter often produces several rows (release + conference call), so
    events within 5 days are collapsed to the earliest — the release date is what
    matters for an options position.
  * The feed carries forward ESTIMATES (dates into 2027). Rows after today are kept
    but flagged `is_future`, so backtests can exclude them and the live screener can
    use them.

Usage:
  TRADIER_API_KEY=... MYSQL_PASSWORD=... PYTHONPATH=src:. \\
      .venv/bin/python3 run_earnings_pull.py
  ... --tickers CVS ACHR     # subset
  ... --no-write             # dry run, CSV only
"""
from __future__ import annotations

import argparse
import os
import re
import time
from datetime import date

import pandas as pd
import requests

from lib.mysql_lib import _get_conn

URL = "https://api.tradier.com/beta/markets/fundamentals/calendars"
POOL = "data/watchlist/straddle_pool_323.txt"
BATCH, PAUSE, DEDUPE_DAYS = 25, 0.6, 5
OUT_CSV = "earnings_dates.csv"


def fetch(syms: list[str], hdrs: dict) -> list:
    for attempt in range(3):
        try:
            r = requests.get(URL, headers=hdrs, params={"symbols": ",".join(syms)}, timeout=60)
            if r.status_code == 200:
                return r.json()
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return []


def extract(payload) -> pd.DataFrame:
    rows = []
    for blk in payload if isinstance(payload, list) else []:
        tkr = blk.get("request")
        for res in blk.get("results") or []:
            for e in (res.get("tables") or {}).get("corporate_calendars") or []:
                nm = e.get("event") or ""
                if "earnings" not in nm.lower():
                    continue
                d = str(e.get("begin_date_time") or "")[:10]
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                    continue
                rows.append(dict(ticker=tkr, raw_date=d, event=nm[:250],
                                 date_status=e.get("event_status")))
    return pd.DataFrame(rows)


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multi-row quarters (release + call) to the earliest date."""
    out = []
    for t, g in df.sort_values(["ticker", "raw_date"]).groupby("ticker"):
        last = None
        for r in g.itertuples(index=False):
            dt = pd.Timestamp(r.raw_date)
            if last is None or (dt - last).days > DEDUPE_DAYS:
                out.append(r._asdict()); last = dt
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=None)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    tickers = a.tickers or [l.strip() for l in open(POOL) if l.strip()]
    hdrs = {"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"}
    print(f"pulling earnings for {len(tickers)} tickers, {BATCH}/call")

    frames = []
    nb = (len(tickers) + BATCH - 1) // BATCH
    for i in range(0, len(tickers), BATCH):
        b = tickers[i:i + BATCH]
        df = extract(fetch(b, hdrs))
        got = df.ticker.nunique() if len(df) else 0
        print(f"  [{i//BATCH+1}/{nb}] {b[0]}..{b[-1]} -> {len(df):>5} rows, {got}/{len(b)} tickers")
        if len(df):
            frames.append(df)
        time.sleep(PAUSE)

    if not frames:
        print("no data"); return
    raw = pd.concat(frames, ignore_index=True)
    d = dedupe(raw)
    d["is_future"] = pd.to_datetime(d.raw_date).dt.date > date.today()
    d = d.sort_values(["ticker", "raw_date"]).reset_index(drop=True)
    d.to_csv(OUT_CSV, index=False)

    hist = d[~d.is_future]
    print(f"\n{len(raw):,} raw -> {len(d):,} after dedupe   "
          f"({len(hist):,} historical, {int(d.is_future.sum()):,} future estimates)")
    print(f"  tickers with data : {d.ticker.nunique()} of {len(tickers)}")
    missing = sorted(set(tickers) - set(d.ticker))
    if missing:
        print(f"  NO earnings data  : {len(missing)}  {', '.join(missing[:15])}"
              f"{' ...' if len(missing) > 15 else ''}")
    h18 = hist[hist.raw_date >= "2018-01-01"]
    print(f"  historical 2018+  : {len(h18):,} events, "
          f"{h18.raw_date.min()} -> {h18.raw_date.max()}")
    per = h18.groupby("ticker").size()
    print(f"  events per ticker : median {per.median():.0f}  (expect ~4/yr × years listed)")
    print(f"  saved -> {OUT_CSV}")

    if a.no_write:
        print("  --no-write: MySQL not touched"); return
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM earnings_report")
    cur.executemany(
        "INSERT INTO earnings_report (ticker, raw_date, date_status, fiscal_period) "
        "VALUES (%s, %s, %s, %s)",
        [(r.ticker, r.raw_date, r.date_status, (r.event or "")[:64]) for r in d.itertuples(index=False)])
    conn.commit()
    print(f"  wrote {cur.rowcount if cur.rowcount>0 else len(d):,} rows -> stocks.earnings_report")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()

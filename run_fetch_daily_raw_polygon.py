#!/usr/bin/env python3
"""Fetch UNADJUSTED daily bars from Polygon into data/cache/polygon_daily_raw/<SYM>.parquet.

Unadjusted = prices as quoted on the day, which is what a live post ("SNDK long 1315.18") refers to; the
split-adjusted panels would misfire on any name that split since. Free-tier key: 5 calls/min.

Usage: PYTHONPATH=src python run_fetch_daily_raw_polygon.py --start 2025-04-01 --end 2026-10-22 SYM [SYM ...]
       [--from-actions data/ariel_hernandez/discord/actions.csv] [--force] [--sleep 12.5]
"""
from __future__ import annotations
import argparse, os, time
from pathlib import Path
import pandas as pd, requests

CACHE = Path(__file__).resolve().parent / "data" / "cache" / "polygon_daily_raw"


def fetch(sym: str, start: str, end: str, key: str) -> pd.DataFrame:
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{start}/{end}"
           f"?adjusted=false&sort=asc&limit=50000&apiKey={key}")
    for attempt in range(4):
        r = requests.get(url, timeout=60)
        if r.status_code != 429:
            break
        time.sleep(20 * (attempt + 1))
    j = r.json()
    if j.get("status") not in ("OK", "DELAYED") or not j.get("results"):
        print(f"  ! {sym}: {j.get('status')} {str(j.get('error', ''))[:100]}", flush=True)
        return pd.DataFrame()
    df = pd.DataFrame(j["results"])
    d = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("America/New_York").dt.date
    return pd.DataFrame({"date": d.astype(str), "open": df["o"], "high": df["h"], "low": df["l"],
                         "close": df["c"], "volume": df["v"]})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--from-actions")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sleep", type=float, default=12.5)
    a = ap.parse_args()
    key = os.environ["POLYGON_API_KEY"]
    syms = {s.upper() for s in a.symbols}
    if a.from_actions:
        syms |= set(pd.read_csv(a.from_actions)["ticker"].dropna().str.upper()) - {"?"}
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [s for s in sorted(syms) if a.force or not (CACHE / f"{s}.parquet").exists()]
    print(f"{len(todo)} symbols to fetch ({len(syms) - len(todo)} cached)", flush=True)
    for n, s in enumerate(todo, 1):
        df = fetch(s, a.start, a.end, key)
        if len(df):
            df.to_parquet(CACHE / f"{s}.parquet", index=False)
        print(f"[{n}/{len(todo)}] {s} {len(df)} bars", flush=True)
        time.sleep(a.sleep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Pull FINRA bi-monthly short interest (via Polygon /stocks/v1/short-interest) for ALL tickers, 2017-12 -> today.

One request per settlement date returns every ticker (~19k rows). Settlement dates are discovered from one liquid
ticker's history (SPY) so the calendar comes from the data, not a hand-made schedule.
Output: data/cache/short_interest.parquet  (settlement_date, ticker, short_interest, avg_daily_volume, days_to_cover)
⚠ Short interest is published ~8 business days AFTER the settlement date; any study must lag it to the
publication date, never use it as of settlement_date.

Usage: PYTHONPATH=src .venv/bin/python3 run_short_interest_pull.py   (needs POLYGON_API_KEY from ~/.trading_env)
"""
import os, time, json, urllib.request
import pandas as pd

KEY = os.environ["POLYGON_API_KEY"]
BASE = "https://api.polygon.io/stocks/v1/short-interest"
OUT = "data/cache/short_interest.parquet"


PART = "data/cache/short_interest_parts"          # one parquet per settlement date -> resumable
PAUSE = 12                                         # seconds between bulk requests (the endpoint 429s when rushed)


def get(url):
    import urllib.error
    for i in range(8):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            wait = 60 * (i + 1) if e.code == 429 else 10 * (i + 1)
            print(f"  HTTP {e.code}, waiting {wait}s (try {i + 1}/8)", flush=True); time.sleep(wait)
        except Exception as e:  # noqa: BLE001
            print("  retry", i, type(e).__name__, flush=True); time.sleep(10 * (i + 1))
    raise RuntimeError("request failed")


dates, url = [], f"{BASE}?ticker=SPY&limit=50000&apiKey={KEY}"
while url:
    j = get(url); dates += [r["settlement_date"] for r in j.get("results", [])]
    url = (j["next_url"] + f"&apiKey={KEY}") if j.get("next_url") else None
dates = sorted(set(dates))
print(f"{len(dates)} settlement dates {dates[0]} -> {dates[-1]}", flush=True)
os.makedirs(PART, exist_ok=True)
for k, d in enumerate(dates):
    part = f"{PART}/{d}.parquet"
    if os.path.exists(part):
        continue
    url, rows = f"{BASE}?settlement_date={d}&limit=50000&apiKey={KEY}", []
    while url:
        j = get(url); rows += j.get("results", [])
        url = (j["next_url"] + f"&apiKey={KEY}") if j.get("next_url") else None
        time.sleep(PAUSE)
    pd.DataFrame(rows).to_parquet(part, index=False)
    print(f"  [{k + 1}/{len(dates)}] {d}: {len(rows):,} rows", flush=True)
si = pd.concat([pd.read_parquet(f"{PART}/{d}.parquet") for d in dates], ignore_index=True)
si["settlement_date"] = pd.to_datetime(si.settlement_date)
si = si.drop_duplicates(["settlement_date", "ticker"])
si.to_parquet(OUT, index=False)
print(f"{len(si):,} rows, {si.ticker.nunique():,} tickers -> {OUT}")

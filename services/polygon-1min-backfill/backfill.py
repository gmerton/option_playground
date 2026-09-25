#!/usr/bin/env python3
"""
Polygon 1-minute stock bar BACKFILL -> S3, as a one-off ECS Fargate task (2026-09-25).

Why: the per-name 1-min cache (data/cache/intraday_1min) only reaches back to 2026-02, which caps every intraday
entry study at ~7 months (entry_study_2026-09-17: 2,439 name-days). The Polygon key is FREE tier for stocks: 5 calls
per minute and ~2 years of minute history (2023 returns 403), so a full pull of the liquid universe is ~18k calls,
~3 days of wall clock -- a job that should outlive the laptop.

What it does
  tickers   s3://$BUCKET/$PREFIX/tickers.txt (one symbol per line, priority order)
  per name  calendar chunks of $CHUNK_DAYS between $START and $END; one /v2/aggs .../range/1/minute call per chunk
            (plus next_url pages), regular session 09:30-16:00 ET only, split-ADJUSTED (adjusted=true, matching
            run_fetch_intraday_polygon.py and the local cache schema: index `time` ET-naive; timestamp, price(=vw),
            open, high, low, close, volume, vwap(=vw, PER-BAR, not session VWAP))
  output    s3://$BUCKET/$PREFIX/bars/<SYM>/<SYM>_<chunk_start>_<chunk_end>.parquet (one file per name-chunk; a
            chunk with no data still gets a marker in _done/ so a restart skips it)
  resumable a restart lists _done/ once and skips finished chunks. Safe to re-run any time.
  pacing    >= 12.5 s between calls (5/min); 429 -> backoff. PAUSES 21:45-03:00 ET so it never competes with the
            nightly options-daily-updater (same Polygon key, 22:00 ET, ~4.5 h).

Env: POLYGON_API_KEY (from Secrets Manager), BUCKET, PREFIX, START, END, CHUNK_DAYS (default 70), SLEEP (12.5)
"""
from __future__ import annotations

import io
import os
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import boto3
import pandas as pd
import requests

ET = ZoneInfo("America/New_York")
KEY = os.environ["POLYGON_API_KEY"]
BUCKET = os.environ.get("BUCKET", "gmerton-stock-data")
PREFIX = os.environ.get("PREFIX", "backfill/intraday_1min").rstrip("/")
START = date.fromisoformat(os.environ.get("START", "2024-10-01"))
END = date.fromisoformat(os.environ.get("END", "2026-09-24"))
CHUNK = int(os.environ.get("CHUNK_DAYS", "70"))
SLEEP = float(os.environ.get("SLEEP", "12.5"))
s3 = boto3.client("s3")
_last_call = [0.0]


def log(msg: str) -> None:
    print(f"{datetime.now(ET):%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def pause_window() -> None:
    """Sleep through 21:45-03:00 ET (the nightly options updater shares this key)."""
    now = datetime.now(ET)
    t = now.time()
    if t >= datetime.strptime("21:45", "%H:%M").time() or t < datetime.strptime("03:00", "%H:%M").time():
        resume = (now + timedelta(days=1 if t >= datetime.strptime("21:45", "%H:%M").time() else 0)).replace(
            hour=3, minute=0, second=0, microsecond=0)
        secs = (resume - now).total_seconds()
        log(f"pause window: sleeping {secs/3600:.1f} h until {resume:%Y-%m-%d %H:%M} ET")
        time.sleep(max(0, secs))


def get(url: str) -> dict:
    for attempt in range(8):
        pause_window()
        wait = SLEEP - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            r = requests.get(url, timeout=60)
        except requests.RequestException as e:
            log(f"  net error {e}; retry"); time.sleep(30); continue
        if r.status_code == 429:
            time.sleep(30 * (attempt + 1)); continue
        if r.status_code == 403:
            return {"status": "NOT_AUTHORIZED"}
        try:
            return r.json()
        except ValueError:
            time.sleep(30)
    return {"status": "FAILED"}


def fetch(sym: str, a: date, b: date) -> pd.DataFrame | None:
    url = f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{a}/{b}?adjusted=true&sort=asc&limit=50000&apiKey={KEY}"
    rows = []
    while url:
        j = get(url)
        if j.get("status") not in ("OK", "DELAYED"):
            if j.get("status") in ("NOT_AUTHORIZED", "FAILED"):
                return None                       # not marked done -> retried on the next run
            break
        rows += j.get("results", []) or []
        nxt = j.get("next_url")
        url = f"{nxt}&apiKey={KEY}" if nxt else None
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    t = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert(ET).dt.tz_localize(None)
    df = pd.DataFrame({"timestamp": (df["t"] // 1000).astype("int64").values, "price": df["vw"].values,
                       "open": df["o"].values, "high": df["h"].values, "low": df["l"].values, "close": df["c"].values,
                       "volume": df["v"].astype("int64").values, "vwap": df["vw"].values},
                      index=pd.DatetimeIndex(t.values, name="time"))
    tt = df.index.time
    return df[(tt >= datetime.strptime("09:30", "%H:%M").time()) & (tt < datetime.strptime("16:00", "%H:%M").time())]


def done_set() -> set[str]:
    out, tok = set(), None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=f"{PREFIX}/_done/")
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        out |= {o["Key"].rsplit("/", 1)[1] for o in r.get("Contents", [])}
        if not r.get("IsTruncated"):
            return out
        tok = r["NextContinuationToken"]


def main() -> int:
    tickers = s3.get_object(Bucket=BUCKET, Key=f"{PREFIX}/tickers.txt")["Body"].read().decode().split()
    chunks, a = [], START
    while a <= END:
        b = min(a + timedelta(days=CHUNK - 1), END); chunks.append((a, b)); a = b + timedelta(days=1)
    done = done_set()
    todo = [(s, a, b) for s in tickers for a, b in chunks if f"{s}_{a}" not in done]
    log(f"{len(tickers)} tickers x {len(chunks)} chunks {START}..{END}; {len(done)} done, {len(todo)} to go "
        f"(~{len(todo) * SLEEP / 3600:.0f} h of calls + nightly pauses)")
    t0, n_ok, last_sym = time.time(), 0, None
    for k, (sym, a, b) in enumerate(todo, 1):
        df = fetch(sym, a, b)
        if df is None:
            log(f"  {sym} {a}: not authorized / failed -- left for a re-run"); continue
        if len(df):
            buf = io.BytesIO(); df.to_parquet(buf)
            s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/bars/{sym}/{sym}_{a}_{b}.parquet", Body=buf.getvalue())
        s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/_done/{sym}_{a}", Body=str(len(df)).encode())
        n_ok += 1
        if sym != last_sym and last_sym is not None:
            el = time.time() - t0
            log(f"done {last_sym}  [{k}/{len(todo)} chunks, {el/3600:.1f} h elapsed, ETA {(len(todo)-k) * el / k / 3600:.0f} h]")
        last_sym = sym
    log(f"FINISHED: {n_ok} chunks written this run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

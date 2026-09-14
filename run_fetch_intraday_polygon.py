#!/usr/bin/env python3
"""
Backfill the 1-min bar cache (data/cache/intraday_1min/<SYM>_<date>.parquet, the schema
lib.journal.exit_kind.bars_1min writes from Tradier) from Polygon minute aggregates, so alert
replays (`run_universe_monitor.py --replay`, `run_alert_study.py --replay`) reach past Tradier's
~20-session retention. Regular session only (09:30-16:00 ET). Per-bar vwap = Polygon's `vw`, the
same per-bar meaning Tradier gives, so SymbolBook builds the same cumulative session VWAP.

Free-tier key: 5 calls/min, so ~12.5 s between calls; one call covers ~60 calendar days of a liquid
name (50k-bar page cap incl. extended hours). ~95 names x 6 months ~= 300 calls ~= 65 min.

Usage: PYTHONPATH=src python run_fetch_intraday_polygon.py --start 2026-02-02 --end 2026-08-12 [SYMS...]
       (no SYMS = universe_latest.txt + universe_short.txt + SPY/QQQ + group ETFs)  [--force] [--sleep 12.5]
"""
from __future__ import annotations
import argparse, os, sys, time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd, requests

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data" / "cache" / "intraday_1min"
ET = ZoneInfo("America/New_York")


def universe() -> list[str]:
    wl = REPO / "data" / "watchlist"
    syms = set()
    for f in ("universe_latest.txt", "universe_short.txt"):
        if (wl / f).exists():
            syms |= {l.split("#")[0].strip().upper() for l in (wl / f).read_text().splitlines() if l.split("#")[0].strip()}
    etfs = REPO / "data" / "watchlist" / "group_etfs.csv"
    if etfs.exists():
        for line in etfs.read_text().splitlines():
            if line.strip() and not line.startswith("#") and not line.startswith("group,") and "," in line:
                syms.add(line.split(",", 1)[1].strip().upper())
    return sorted(syms | {"SPY", "QQQ"})


def fetch(sym: str, start: date, end: date, key: str, sleep: float) -> pd.DataFrame:
    url = f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={key}"
    rows = []
    while url:
        for attempt in range(4):
            r = requests.get(url, timeout=60)
            if r.status_code == 429:
                time.sleep(20 * (attempt + 1)); continue
            break
        j = r.json()
        if j.get("status") not in ("OK", "DELAYED"):
            print(f"  ! {sym} {start}..{end}: {j.get('status')} {j.get('error', '')[:100]}"); break
        rows += j.get("results", [])
        url = j.get("next_url"); url = f"{url}&apiKey={key}" if url else None
        time.sleep(sleep)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    t = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert(ET).dt.tz_localize(None)
    df = pd.DataFrame({"timestamp": (df["t"] // 1000).astype("int64").values, "price": df["vw"].values, "open": df["o"].values, "high": df["h"].values,
                       "low": df["l"].values, "close": df["c"].values, "volume": df["v"].astype("int64").values, "vwap": df["vw"].values},
                      index=pd.DatetimeIndex(t.values, name="time"))
    tt = df.index.time
    return df[(tt >= datetime.strptime("09:30", "%H:%M").time()) & (tt < datetime.strptime("16:00", "%H:%M").time())]


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("symbols", nargs="*"); ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--force", action="store_true"); ap.add_argument("--sleep", type=float, default=12.5); ap.add_argument("--chunk-days", type=int, default=60)
    a = ap.parse_args()
    key = os.environ.get("POLYGON_API_KEY")
    if not key:
        print("POLYGON_API_KEY not set"); return 2
    syms = [s.upper() for s in a.symbols] or universe()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    CACHE.mkdir(parents=True, exist_ok=True)
    sessions = [d for d in pd.bdate_range(start, end).date]
    print(f"{len(syms)} symbols x {len(sessions)} weekdays {start}..{end} -> {CACHE}", flush=True)
    t0 = time.time(); calls = 0
    for n, sym in enumerate(syms, 1):
        missing = [d for d in sessions if a.force or not (CACHE / f"{sym}_{d.isoformat()}.parquet").exists()]
        if not missing:
            print(f"[{n}/{len(syms)}] {sym}: cached", flush=True); continue
        lo, hi = min(missing), max(missing); got = 0
        c0 = lo
        while c0 <= hi:
            c1 = min(hi, c0 + timedelta(days=a.chunk_days - 1))
            df = fetch(sym, c0, c1, key, a.sleep); calls += 1
            for d, g in (df.groupby(df.index.date) if len(df) else []):
                if d in missing:
                    g.to_parquet(CACHE / f"{sym}_{d.isoformat()}.parquet"); got += 1
            c0 = c1 + timedelta(days=1)
        # weekdays with no bars (holidays / not listed yet) get an empty file so the replay skips them without refetching
        for d in missing:
            p = CACHE / f"{sym}_{d.isoformat()}.parquet"
            if not p.exists():
                pd.DataFrame().to_parquet(p)
        print(f"[{n}/{len(syms)}] {sym}: {got} sessions written ({len(missing) - got} empty) | {calls} calls, {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

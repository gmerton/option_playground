#!/usr/bin/env python3
"""
Deep, DELISTING-INCLUSIVE equity history backfill from Polygon grouped daily aggregates.

WHY THIS EXISTS
    Every result in RESULTS.md and SELECTION_LIFT.md carries the same caveat: the universe is
    names that still exist and are liquid TODAY, so the panel is survivorship-biased, and the
    bias hits the long-hold momentum tiers hardest — exactly the ones that won. yfinance cannot
    fix this; you can only fetch a ticker you already know about.

    Polygon's grouped-daily endpoint returns EVERY ticker that traded on a given date. Walking
    it day by day reconstructs the panel as it actually looked at the time, including names
    that later delisted, merged, or went to zero. That is the only clean fix.

⚠⚠ REQUIRES A PAID POLYGON PLAN — DO NOT RUN ON THE FREE TIER.
    Verified 2026-07-26: the free key returns, for any date beyond ~2 years back,
        {"status":"NOT_AUTHORIZED", "message":"Attempted to request data past historical
         entitlements. Please upgrade your plan"}
    So a 2006-2026 backfill fails on essentially every call. The nightly refresh works only
    because it stays inside the entitlement window. Check `probe_entitlement()` below before
    launching anything long.

COST
    One API call per trading day, ~5,030 calls for 2006-2026. At the free tier's ~5 req/min
    that is roughly 17 hours (moot until the plan is upgraded). Memory stays flat: rows are
    buffered one month at a time and written straight out.

RESUMABLE
    Completed months are recorded in _manifest.txt and skipped on restart, so a killed or
    interrupted run picks up where it left off. Safe to run repeatedly.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
      data/carter_mastering_the_trade/backtests/risk_architecture/backfill_polygon.py [--pace 12.5]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd
from polygon import RESTClient

sys.path.insert(0, "src")

OUT_DIR = "data/carter_mastering_the_trade/backtests/risk_architecture/polygon_history"
MANIFEST = f"{OUT_DIR}/_manifest.txt"
START, END = date(2006, 1, 1), date(2026, 7, 24)

COLS = ["date", "ticker", "open", "high", "low", "close", "volume"]

# Fixed-date holidays worth skipping outright; observed shifts are not modelled, so a handful
# of dead calls remain. Not worth more precision — Polygon returns empty for them anyway.
def _skip(d: date) -> bool:
    if d.weekday() >= 5:
        return True
    return (d.month, d.day) in {(1, 1), (7, 4), (12, 25)}


def trading_days() -> list[date]:
    out, d = [], START
    while d <= END:
        if not _skip(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def done_months() -> set[str]:
    if not os.path.exists(MANIFEST):
        return set()
    with open(MANIFEST) as fh:
        return {ln.strip() for ln in fh if ln.strip()}


def probe_entitlement(client) -> None:
    """One cheap call against the oldest date needed. Fail loudly rather than spend hours
    discovering the plan does not cover the window."""
    try:
        client.get_grouped_daily_aggs(START.isoformat(), adjusted=True)
    except Exception as e:
        msg = str(e)
        if "NOT_AUTHORIZED" in msg or "entitlement" in msg.lower():
            sys.exit(f"ABORT: Polygon plan does not cover {START}.\n  {msg[:200]}\n"
                     "  A paid plan is required for this backfill.")
        print(f"  probe warning (continuing): {type(e).__name__}: {msg[:120]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pace", type=float, default=12.5,
                    help="seconds between calls; free tier is ~5 req/min")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    client = RESTClient(os.environ["POLYGON_API_KEY"])
    probe_entitlement(client)

    days = trading_days()
    have = done_months()
    months: dict[str, list[date]] = {}
    for d in days:
        months.setdefault(d.strftime("%Y-%m"), []).append(d)
    todo = [m for m in sorted(months) if m not in have]

    ncalls = sum(len(months[m]) for m in todo)
    print(f"{len(days)} trading days, {len(months)} months, {len(have)} already done.",
          flush=True)
    print(f"pulling {len(todo)} months = {ncalls} calls at {args.pace}s "
          f"=> ~{ncalls * args.pace / 3600:.1f} hours", flush=True)

    failed_total = 0
    for mi, m in enumerate(todo, 1):
        rows, failed = [], 0
        for d in months[m]:
            ds = d.isoformat()
            got = None
            for attempt in range(5):
                try:
                    got = client.get_grouped_daily_aggs(ds, adjusted=True)
                    break
                except Exception:
                    time.sleep(min(2 ** attempt, 60))
            if got is None:
                failed += 1
            else:
                for r in got:
                    if r.close and r.volume:
                        rows.append((ds, r.ticker, r.open, r.high, r.low, r.close, r.volume))
            time.sleep(args.pace)

        if rows:
            df = pd.DataFrame.from_records(rows, columns=COLS)
            df["date"] = pd.to_datetime(df["date"])
            for c in ("open", "high", "low", "close"):
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("float64")
            df = df.dropna(subset=["open", "close"])
            df.to_parquet(f"{OUT_DIR}/{m}.parquet", index=False)

        failed_total += failed
        with open(MANIFEST, "a") as fh:
            fh.write(m + "\n")
        print(f"  [{mi:3}/{len(todo)}] {m}: {len(rows):>7,} rows, "
              f"{df.ticker.nunique() if rows else 0:>5} tickers"
              f"{f', {failed} FAILED days' if failed else ''}", flush=True)

    print(f"\ndone. {failed_total} failed days total. parts in {OUT_DIR}")


if __name__ == "__main__":
    main()

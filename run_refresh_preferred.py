#!/usr/bin/env python3
"""
Refresh data/preferred_tickers.txt from the Minervini Trend Template scan.

Per the 2026-07-24 definition: the preferred list IS the set of names currently
passing the full Trend Template (price/EMA structure, 30% off low, within 25%
of high, RS>=70 pctile, ADDV>$200M). This script:

  1. Runs run_minervini_scan.py (incremental Polygon cache top-up + screen).
  2. Unions the pass list with data/preferred_manual_adds.txt (optional
     conviction overlay — names kept regardless of template status).
  3. Archives the outgoing list to data/watchlist/preferred_history/ and
     prints the adds/drops diff.
  4. Writes data/preferred_tickers.txt.
  5. --push: uploads to s3://gmerton-stock-data/breakouts/preferred_tickers.txt
     (the list the LIVE Lambda scan reads at 4:15pm PT next session).

Run (evening, after the close — needs the session's Polygon grouped-daily):
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
        run_refresh_preferred.py            # dry run: writes local, no S3
    ... run_refresh_preferred.py --push     # also update the live S3 copy

Requires: POLYGON_API_KEY (scan), AWS_PROFILE for --push.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
LIST = REPO / "data" / "preferred_tickers.txt"
MANUAL = REPO / "data" / "preferred_manual_adds.txt"
HISTORY = REPO / "data" / "watchlist" / "preferred_history"
SCAN_OUT = REPO / "data" / "cache" / "minervini_pass_latest.txt"
S3_URI = "s3://gmerton-stock-data/breakouts/preferred_tickers.txt"
S3_REGION = "us-west-2"


def read_list(p: Path) -> list[str]:
    if not p.exists():
        return []
    return sorted({ln.strip().upper() for ln in p.read_text().splitlines() if ln.strip()})


def main() -> None:
    ap = argparse.ArgumentParser(description="Refresh preferred_tickers.txt from the Minervini scan")
    ap.add_argument("--push", action="store_true", help="also upload the new list to S3 (live Lambda)")
    ap.add_argument("--skip-scan", action="store_true",
                    help="reuse data/cache/minervini_pass_latest.txt without re-running the scan")
    args = ap.parse_args()

    if not args.skip_scan:
        print("Running Minervini scan (incremental cache top-up)...", flush=True)
        r = subprocess.run(
            [sys.executable, str(REPO / "run_minervini_scan.py"),
             "--out", str(SCAN_OUT), "--no-compare"],
            cwd=REPO)
        if r.returncode != 0:
            sys.exit("Scan failed or matrix incomplete — list NOT refreshed. "
                     "(Re-run; the incremental cache resumes automatically.)")

    passing = read_list(SCAN_OUT)
    if len(passing) < 20:
        sys.exit(f"Only {len(passing)} names passed — refusing to overwrite the list "
                 f"(suspicious scan output at {SCAN_OUT}).")

    manual = read_list(MANUAL)
    new = sorted(set(passing) | set(manual))
    old = read_list(LIST)

    adds = [t for t in new if t not in old]
    drops = [t for t in old if t not in new]

    # archive outgoing list, then write
    HISTORY.mkdir(parents=True, exist_ok=True)
    if old:
        (HISTORY / f"preferred_{date.today()}_prev.txt").write_text("\n".join(old) + "\n")
    LIST.write_text("\n".join(new) + "\n")

    print(f"\n=== preferred_tickers.txt refreshed — {date.today()} ===")
    print(f"  template passers: {len(passing)}  + manual overlay: {len(manual)}  -> list: {len(new)}")
    print(f"  vs previous ({len(old)}):  +{len(adds)} adds, -{len(drops)} drops")
    if adds:
        print(f"  ADDS:  {', '.join(adds)}")
    if drops:
        print(f"  DROPS: {', '.join(drops)}")
    print(f"  outgoing list archived to {HISTORY}/")

    if args.push:
        print(f"\nPushing to {S3_URI} ...", flush=True)
        r = subprocess.run(["aws", "s3", "cp", str(LIST), S3_URI, "--region", S3_REGION])
        if r.returncode != 0:
            sys.exit("S3 push FAILED — local list updated, live Lambda still on the old list.")
        print("Live list updated. Takes effect at the next 4:15pm PT Lambda run.")
    else:
        print("\n(dry run — local file updated, S3 untouched; use --push for the live list)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Stage A, step 1: replay every cached session through the CURRENT long detectors, in parallel.

One rulebook for all sessions (the historical logs mix engine versions). Writes
data/watchlist/logs/{universe_alerts,alerts,alerts_oop}_<date>_replay_stagea*.{log,jsonl}.

Usage: PYTHONPATH=src .venv/bin/python3 run_stage_a_replay.py [--workers 8] [--since 2026-02-02]
"""
from __future__ import annotations
import argparse, re, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BARS = Path("data/cache/intraday_1min")
TAG = "stagea"


def sessions() -> list[str]:
    return sorted({m.group(1) for p in BARS.glob("*.parquet")
                   if (m := re.search(r"_(\d{4}-\d{2}-\d{2})\.parquet$", p.name))})


def symbols() -> list[str]:
    return sorted({p.name.rsplit("_", 1)[0] for p in BARS.glob("*.parquet")})


def one(d: str) -> tuple[str, str]:
    syms = symbols()
    r = subprocess.run([sys.executable, "run_universe_monitor.py", *syms, "--replay", d,
                        "--detectors", "ur,orb9,lvl", "--orb-no-index-gate", "--tag", TAG],
                       capture_output=True, text=True, timeout=900)
    last = [l for l in r.stdout.splitlines() if l.startswith("replay:")]
    return d, (last[-1] if last else (r.stderr.strip().splitlines() or ["no output"])[-1][:120])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--since", default=None)
    a = ap.parse_args()
    ds = [d for d in sessions() if not a.since or d >= a.since]
    print(f"{len(ds)} sessions, {len(symbols())} symbols, {a.workers} workers", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        for i, (d, msg) in enumerate(ex.map(one, ds), 1):
            if i % 20 == 0 or i == len(ds):
                print(f"  [{i}/{len(ds)}] {d}: {msg}", flush=True)
    print("done")


if __name__ == "__main__":
    main()

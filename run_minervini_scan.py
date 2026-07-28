#!/usr/bin/env python3
"""
Minervini Trend Template scan over the full US common-stock universe — local CLI.

Core logic lives in src/lib/minervini/scan.py (shared with the nightly
refresh Lambda). Data source: Polygon grouped-daily aggregates into the
incremental day-matrix cache. The S3 copy maintained by the Lambda is
canonical; sync it down for local research with:

    aws s3 cp s3://gmerton-stock-data/breakouts/minervini_matrix.parquet \
        data/cache/minervini_matrix.parquet

Run:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_minervini_scan.py
    ... run_minervini_scan.py --use-cache          # reuse last pull, retune thresholds
    ... run_minervini_scan.py --out data/watchlist/minervini_YYYY-MM-DD.txt

Requires: POLYGON_API_KEY
"""
from __future__ import annotations

import argparse
import os
from typing import List

import pandas as pd
from polygon import RESTClient

from lib.minervini.scan import (
    build_table,
    load_cache,
    pull_matrices,
    save_cache,
    screen,
)

CACHE = "data/cache/minervini_matrix.parquet"
CS_CACHE = "data/cache/polygon_cs_tickers.txt"
PREFERRED = "data/preferred_tickers.txt"


def common_stock_universe(client: RESTClient, refresh: bool) -> set:
    """Active common stocks (type=CS) per Polygon reference, cached to disk."""
    if not refresh and os.path.exists(CS_CACHE):
        with open(CS_CACHE) as f:
            return {ln.strip() for ln in f if ln.strip()}
    print("Fetching active common-stock universe from Polygon reference...", flush=True)
    syms = set()
    for t in client.list_tickers(market="stocks", type="CS", active=True, limit=1000):
        syms.add(t.ticker)
    os.makedirs(os.path.dirname(CS_CACHE), exist_ok=True)
    with open(CS_CACHE, "w") as f:
        f.write("\n".join(sorted(syms)))
    print(f"  {len(syms)} common stocks", flush=True)
    return syms


# ── reporting ────────────────────────────────────────────────────────────────

COND_LABELS = {
    "c1": "px>150&200MA", "c2": "150>200MA", "c3": "200MA rising", "c4": "50>150>200",
    "c5": "px>50MA", "c6": ">30% off low", "c7": "within 25% hi", "c8": "RS rank",
    "cL": "ADDV>$200M",
}


def load_preferred() -> List[str]:
    if not os.path.exists(PREFERRED):
        return []
    with open(PREFERRED) as f:
        return [ln.strip().upper() for ln in f if ln.strip()]


def report(out: pd.DataFrame, rs_min: float, addv_min: float, compare: bool):
    passing = out[out.pass_all].sort_values("rs_pct", ascending=False)
    print(f"\n{'=' * 70}\nMINERVINI SCAN — {len(passing)} names pass "
          f"(RS≥{rs_min:.0f}, ADDV>${addv_min/1e6:.0f}M)\n{'=' * 70}")
    print(f"{'ticker':<8}{'price':>9}{'RS':>6}{'ADDV$M':>9}{'%off hi':>9}")
    print("-" * 70)
    for tk, r in passing.iterrows():
        off_hi = (r.price / r.hi252 - 1) * 100 if r.hi252 else float("nan")
        print(f"{tk:<8}{r.price:>9.2f}{r.rs_pct:>6.0f}{r.addv/1e6:>9.0f}{off_hi:>8.1f}%")

    if not compare:
        return passing
    pref = load_preferred()
    if not pref:
        return passing
    pset, sset = set(pref), set(passing.index)
    both = pset & sset
    add = sorted(sset - pset)
    drop = [p for p in pref if p not in sset]
    print(f"\n{'=' * 70}\nVALIDATION vs {PREFERRED} ({len(pref)} names)\n{'=' * 70}")
    print(f"  overlap:           {len(both)}/{len(pref)}  ({100*len(both)/len(pref):.0f}% of your list reproduced)")
    print(f"  scan adds (new):   {len(add)}")
    print(f"  your names dropped:{len(drop)}")

    print(f"\n  YOUR NAMES THE SCAN DROPPED — and why (first failing conditions):")
    for p in drop:
        if p not in out.index:
            print(f"     {p:<7} — no Polygon data (delisted / not common stock / illiquid)")
            continue
        r = out.loc[p]
        fails = [COND_LABELS[k] for k in COND_LABELS if not bool(r[k])]
        extra = ""
        if not bool(r["cL"]):
            extra = f"  [ADDV ${r.addv/1e6:.0f}M]" if pd.notna(r.addv) else "  [ADDV n/a]"
        if not bool(r["c8"]) and pd.notna(r.rs_pct):
            extra += f"  [RS {r.rs_pct:.0f}]"
        print(f"     {p:<7} fails: {', '.join(fails)}{extra}")

    print(f"\n  SCAN ADDED (not on your list, ranked by RS):")
    addtbl = passing.loc[[a for a in add]].sort_values("rs_pct", ascending=False)
    for tk, r in addtbl.head(40).iterrows():
        print(f"     {tk:<7} RS {r.rs_pct:>3.0f}  ${r.addv/1e6:>5.0f}M  {r.price:>8.2f}")
    if len(add) > 40:
        print(f"     ... +{len(add)-40} more")
    return passing


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Minervini Trend Template universe scan (Polygon)")
    ap.add_argument("--rs-min", type=float, default=70.0)
    ap.add_argument("--addv-min", type=float, default=200e6, help="min 50d avg daily $ volume")
    ap.add_argument("--slope-days", type=int, default=20, help="200MA must rise over N trading days")
    ap.add_argument("--lookback-days", type=int, default=430, help="calendar days of history to pull")
    ap.add_argument("--pace", type=float, default=12.5,
                    help="seconds between Polygon calls (free tier ~5 req/min -> 12.5)")
    ap.add_argument("--use-cache", action="store_true", help="reuse last pulled matrix")
    ap.add_argument("--refresh-universe", action="store_true", help="re-pull CS ticker list")
    ap.add_argument("--no-compare", action="store_true")
    ap.add_argument("--out", help="write passing tickers (one per line) to this path")
    args = ap.parse_args()

    key = os.environ.get("POLYGON_API_KEY")
    if not key:
        raise SystemExit("Set POLYGON_API_KEY")
    client = RESTClient(key)

    if args.use_cache and os.path.exists(CACHE):
        print(f"Loading cached matrix from {CACHE}", flush=True)
        close, high, low, dolvol = load_cache(CACHE)
    else:
        universe = common_stock_universe(client, args.refresh_universe)
        prior = load_cache(CACHE) if os.path.exists(CACHE) else None
        frames, failed_days, _long = pull_matrices(
            client, universe, args.lookback_days, args.pace, prior=prior,
            checkpoint_fn=lambda fr: save_cache(fr, CACHE))
        close, high, low, dolvol = frames
        save_cache(frames, CACHE)
        from datetime import date
        failed_days = [d for d in failed_days if d != date.today().isoformat()]
        if failed_days:
            raise SystemExit(
                f"Saved {close.shape[0]} sessions, but {len(failed_days)} days still "
                f"failed (e.g. {sorted(failed_days)[:5]}). Re-run to top up; "
                f"skipping the screen on an incomplete matrix.")

    t = build_table(close, high, low, dolvol, args.slope_days)
    out = screen(t, args.rs_min, args.addv_min)
    passing = report(out, args.rs_min, args.addv_min, not args.no_compare)

    if args.out:
        with open(args.out, "w") as f:
            f.write("\n".join(passing.index))
        print(f"\nWrote {len(passing)} tickers -> {args.out}")


if __name__ == "__main__":
    main()

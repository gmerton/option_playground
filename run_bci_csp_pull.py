#!/usr/bin/env python3
"""
Pull candidate short puts for the BCI covered-call / cash-secured-put test
(data/traderlion/setups/bci_covered_calls_cash_secured_puts.md §7).

For every straddle-pool ticker, every Friday 2018 -> 2026-02, two tenors:
  W  expiry 4-10 DTE, nearest 7     (Ellman's weekly)
  M  expiry 21-38 DTE, nearest 28   (his 3-4 week)
and within that expiry, at most four puts (by bid/ask, from silver.options_daily_v3):
  r50  nearest -0.50 delta   -> ATM IV for the 30-60% filter
  r30  nearest -0.30 delta   -> house comparator
  r20  nearest -0.20 delta   -> deeper / "defensive"
  ry   OTM put (delta > -0.45) whose premium yield sellpx/(K - sellpx) is nearest his target:
       0.75%/week (W) or 3% x DTE/30 (M) -- the middle of his 0.5-1%/wk and 2-4%/month ranges
sellpx = mid - 25% of the bid/ask spread (house fill model for a sale).

Bid/ask ends ~2026-03 in v3, so trade dates stop at 2026-02-27. Hold-to-expiry settlement is done in
run_bci_csp_study.py from the underlying close, not from option marks.

Output: data/cache/bci_csp/chain_<year>.parquet   (gitignored)

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_bci_csp_pull.py [--years 2018 2019 ...]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from lib.athena_lib import athena

POOL = "data/watchlist/straddle_pool_323.txt"
OUT = Path("data/cache/bci_csp")
BATCH = 120


def sql(tickers: list[str], y: int) -> str:
    tk = ",".join(f"'{t}'" for t in tickers)
    end = "2026-02-27" if y == 2026 else f"{y}-12-31"
    return f"""
WITH c AS (
  SELECT ticker, trade_date, expiry, strike, bid, ask, delta, (bid_iv + ask_iv) / 2 AS iv, open_interest,
         date_diff('day', trade_date, expiry) AS dte,
         (bid + ask) / 2 - 0.25 * (ask - bid) AS sellpx
  FROM silver.options_daily_v3
  WHERE ticker IN ({tk}) AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{end}'
    AND day_of_week(trade_date) = 5 AND cp = 'P' AND bid > 0 AND ask >= bid
    AND delta BETWEEN -0.60 AND -0.03
    AND date_diff('day', trade_date, expiry) BETWEEN 4 AND 38
),
e AS (
  SELECT ticker, trade_date, expiry, dte,
         CASE WHEN dte BETWEEN 4 AND 10 THEN 'W' WHEN dte BETWEEN 21 AND 38 THEN 'M' END AS tenor
  FROM c GROUP BY ticker, trade_date, expiry, dte
),
er AS (
  SELECT *, row_number() OVER (PARTITION BY ticker, trade_date, tenor
                               ORDER BY abs(dte - CASE tenor WHEN 'W' THEN 7 ELSE 28 END), dte) AS rk
  FROM e WHERE tenor IS NOT NULL
),
x AS (
  SELECT c.*, er.tenor,
         CASE er.tenor WHEN 'W' THEN 0.0075 ELSE 0.03 * c.dte / 30.0 END AS ytarget
  FROM c JOIN er ON c.ticker = er.ticker AND c.trade_date = er.trade_date AND c.expiry = er.expiry AND er.rk = 1
  WHERE c.strike > c.sellpx AND c.sellpx > 0
),
y AS (
  SELECT x.*,
    row_number() OVER (PARTITION BY ticker, trade_date, tenor ORDER BY abs(delta + 0.50)) AS r50,
    row_number() OVER (PARTITION BY ticker, trade_date, tenor ORDER BY abs(delta + 0.30)) AS r30,
    row_number() OVER (PARTITION BY ticker, trade_date, tenor ORDER BY abs(delta + 0.20)) AS r20,
    row_number() OVER (PARTITION BY ticker, trade_date, tenor
                       ORDER BY CASE WHEN delta < -0.45 THEN 1 ELSE 0 END,
                                abs(sellpx / (strike - sellpx) - ytarget)) AS ry
  FROM x
)
SELECT ticker, trade_date, expiry, dte, tenor, strike, bid, ask, sellpx, delta, iv, open_interest, ytarget,
       r50 = 1 AS is50, r30 = 1 AS is30, r20 = 1 AS is20, (ry = 1 AND delta >= -0.45) AS isy
FROM y WHERE r50 = 1 OR r30 = 1 OR r20 = 1 OR ry = 1
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2018, 2027)))
    a = ap.parse_args()
    pool = [l.strip() for l in open(POOL) if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    for y in a.years:
        dest = OUT / f"chain_{y}.parquet"
        if dest.exists():
            print(f"{y}: cached ({dest})"); continue
        t0, frames = time.time(), []
        for i in range(0, len(pool), BATCH):
            frames.append(athena(sql(pool[i:i + BATCH], y)))
        d = pd.concat(frames, ignore_index=True)
        d.to_parquet(dest, index=False)
        print(f"{y}: {len(d):,} rows, {d.ticker.nunique()} tickers, {time.time()-t0:.0f}s -> {dest}", flush=True)


if __name__ == "__main__":
    main()

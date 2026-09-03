#!/usr/bin/env python3
"""
Pull 7-DTE straddles for the WEEKLY-OPTIONABLE candidate pool, for an honest
rebuild of the long-straddle approved list.

Why this pool and not the nominal 987:
  The strategy is a 7-DTE straddle, which requires weekly options. Using
  iv_put_10 availability as the weeklies proxy, only ~323 of the 987 study-universe
  names carry weeklies on >=60% of days. The rest cannot be traded at this tenor
  at all, so including them in qualification was never meaningful.
  Sanity check: 139 of the existing 140 approved names fall inside this pool
  (RVLV is the lone exception at 51% coverage), so the pool restriction re-ranks
  within the same eligible universe rather than redefining it.

Emits: data/watchlist/straddle_pool_323.txt  and  straddle_pool_data.csv
(the CSV is gitignored — regenerate with this script).

Usage:
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. \\
      .venv/bin/python3 run_straddle_pool_pull.py
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import awswrangler as wr

import run_fvr_straddle_regression as R
from run_fvr_straddle_regression import BATCH_SIZE, DEFAULT_START, load_fvr
from lib.mysql_lib import _get_engine

DTE, TOL = 7, 2
MIN_WEEKLY_COV = 60.0
POOL_FILE = Path("data/watchlist/straddle_pool_323.txt")
OUT = "straddle_pool_data.csv"


def build_pool() -> list[str]:
    tk = pd.read_sql(
        "SELECT DISTINCT ticker FROM study_summary WHERE study_id=12 ORDER BY ticker",
        _get_engine())["ticker"].tolist()
    q = ",".join(f"'{t}'" for t in tk)
    d = wr.athena.read_sql_query(
        sql=f"""SELECT ticker, COUNT(*) n,
                       SUM(CASE WHEN iv_put_10 IS NOT NULL THEN 1 ELSE 0 END) n10
                FROM silver.fwd_vol_daily WHERE ticker IN ({q}) GROUP BY ticker""",
        database="silver", workgroup="dev-v3", s3_output="s3://athena-919061006621/")
    d["wk_cov"] = d["n10"] / d["n"] * 100
    pool = sorted(d.loc[d["wk_cov"] >= MIN_WEEKLY_COV, "ticker"])
    POOL_FILE.write_text("\n".join(pool) + "\n")
    print(f"pool: {len(pool)} tickers with >={MIN_WEEKLY_COV:.0f}% weekly coverage "
          f"(of {len(tk)} in study_id=12) -> {POOL_FILE}")
    return pool


def main() -> None:
    pool = build_pool()
    R.DTE_TARGET, R.DTE_TOL = DTE, TOL
    start, end = DEFAULT_START, date.today()
    print(f"pulling {DTE} DTE (+/-{TOL}) straddles, {start} -> {end}")

    frames = []
    nb = (len(pool) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(pool), BATCH_SIZE):
        b = pool[i:i + BATCH_SIZE]
        print(f"  [batch {i//BATCH_SIZE+1}/{nb}] {b[0]}...{b[-1]}", end="  ", flush=True)
        sdf = R.fetch_straddle_batch(b, start, end)
        if sdf.empty:
            print("-> 0"); continue
        fdf = load_fvr(b, start, end)
        m = sdf.merge(fdf.rename(columns={"trade_date": "entry_date"}),
                      on=["ticker", "entry_date"], how="inner")
        m = m.dropna(subset=["payout", "fvr_put_30_90"])
        m = m[m["entry_premium"] > 0]
        m["ret_pct_long"] = (m["payout"] - m["entry_premium"]) / m["entry_premium"] * 100
        print(f"-> {len(m):,}")
        if len(m):
            frames.append(m)

    if not frames:
        print("no data"); return
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"\n{len(df):,} rows, {df.ticker.nunique()} tickers, "
          f"{df.entry_date.min()} -> {df.entry_date.max()}, actual DTE {df.dte.mean():.2f}")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()

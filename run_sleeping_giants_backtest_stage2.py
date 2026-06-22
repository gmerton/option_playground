#!/usr/bin/env python3
"""
Sleeping Giants backtest — STAGE 2: entry resolution.

Reads the episode list from Stage 1 and resolves a concrete LEAP entry for BOTH arms:
  A (coil-and-hold)     — enter on the episode (signal) date.
  B (wait-for-breakout) — walk daily price forward from the signal date until close > R
                          (the resistance at signal time); enter on that breakout date.
                          Episodes that never break out within BREAKOUT_WINDOW are recorded
                          as "no breakout" (a real outcome — dead bases cost nothing here but
                          must be counted when we judge arm B).

For each resolved entry it pulls the actual ~0.40-delta, ~9-12mo LEAP call from Athena
(nearest delta then nearest DTE) and records the entry mid + contract spec.

Output: data/studies/Adhikary/sleeping_giants_entries.csv  (feeds Stage 3 payoff tracking).
This stage validates the entry selection before we spend Athena on forward repricing.
"""
import asyncio
import sys
import os
import uuid
from datetime import date, timedelta
from typing import Optional, List, Dict

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

import pandas as pd
import awswrangler as wr

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import DB, TABLE, S3TABLES_CATALOG, GLUE_CATALOG, TMP_S3_PREFIX

EPISODES_CSV = "data/studies/Adhikary/sleeping_giants_episodes.csv"
OUT_CSV = "data/studies/Adhikary/sleeping_giants_entries.csv"

TARGET_DELTA = 0.40
TARGET_DTE = 315            # ~10.5 months
DTE_MIN, DTE_MAX = 200, 450
BREAKOUT_WINDOW = 180      # trading days to wait for a breakout (arm B)
BREAKOUT_VOL_MULT = 1.0    # require breakout-day volume >= this x 50d avg (1.0 = no extra gate)

T = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'


async def find_breakouts(client: TradierClient, episodes: pd.DataFrame) -> Dict[int, Optional[date]]:
    """For each episode (by index), find the first day close > resistance R after the signal.
    Returns {episode_idx: breakout_date or None}."""
    out: Dict[int, Optional[date]] = {}
    # group by ticker -> one history fetch per ticker
    for ticker, grp in episodes.groupby("ticker"):
        first_dt = pd.to_datetime(grp["date"]).min().date()
        df = await get_daily_history(ticker, first_dt - timedelta(days=10),
                                     date.today(), client=client)
        if df is None or df.empty:
            for idx in grp.index:
                out[idx] = None
            continue
        df = df.reset_index().sort_values("date").reset_index(drop=True)
        df["date"] = pd.to_datetime(df["date"])
        df["vol_avg_50"] = df["volume"].rolling(50, min_periods=1).mean()
        for idx, row in grp.iterrows():
            sig_dt = pd.to_datetime(row["date"])
            R = float(row["resistance"])
            fwd = df[df["date"] > sig_dt].head(BREAKOUT_WINDOW)
            bo = fwd[(fwd["close"] > R) & (fwd["volume"] >= BREAKOUT_VOL_MULT * fwd["vol_avg_50"])]
            out[idx] = bo.iloc[0]["date"].date() if not bo.empty else None
    return out


def write_entry_requests(reqs: pd.DataFrame) -> tuple[str, str]:
    """Write (row_id, ticker, entry_date) temp table to Glue/S3 for the Athena join."""
    table_name = f"tmp_sg_entries_{uuid.uuid4().hex}"
    s3_path = TMP_S3_PREFIX.rstrip("/") + f"/{table_name}/"
    dfw = reqs[["row_id", "ticker", "entry_date"]].copy()
    dfw["entry_date"] = pd.to_datetime(dfw["entry_date"]).dt.date
    dfw["ticker"] = dfw["ticker"].astype(str)
    wr.s3.to_parquet(
        df=dfw, path=s3_path, dataset=True, database=DB, table=table_name,
        compression="snappy", mode="overwrite",
        dtype={"row_id": "bigint", "ticker": "string", "entry_date": "date"},
    )
    return table_name, s3_path


def select_leaps(reqs: pd.DataFrame) -> pd.DataFrame:
    """One Athena query: nearest ~0.40-delta, ~315-DTE call per (row_id)."""
    _ensure_glue_db(DB)
    tmp_table, tmp_path = write_entry_requests(reqs)
    try:
        sql = f"""
        WITH cand AS (
          SELECT
            t.row_id,
            o.trade_date AS entry_date,
            o.expiry,
            o.ticker,
            o.strike,
            o.delta,
            ROUND((o.bid + o.ask) / 2, 3) AS entry_mid,
            o.bid, o.ask, o.open_interest,
            date_diff('day', o.trade_date, o.expiry) AS dte,
            ABS(date_diff('day', o.expiry, date_add('day', {TARGET_DTE}, o.trade_date))) AS dte_err
          FROM {T} o
          JOIN "{GLUE_CATALOG}"."{DB}"."{tmp_table}" t
            ON o.ticker = t.ticker AND o.trade_date = t.entry_date
          WHERE o.cp = 'C'
            AND o.bid > 0 AND o.ask > 0 AND o.delta IS NOT NULL
            AND date_diff('day', o.trade_date, o.expiry) BETWEEN {DTE_MIN} AND {DTE_MAX}
        ),
        ranked AS (
          SELECT *,
            ROW_NUMBER() OVER (
              PARTITION BY row_id
              ORDER BY ABS(delta - {TARGET_DELTA}), dte_err
            ) AS rn
          FROM cand
        )
        SELECT row_id, entry_date, expiry, ticker, strike, delta, entry_mid,
               bid, ask, open_interest, dte
        FROM ranked WHERE rn = 1
        ORDER BY row_id
        """
        df = athena(sql)
    finally:
        try:
            wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
            wr.s3.delete_objects(tmp_path)
        except Exception:
            pass
    for c in ("entry_date", "expiry"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c]).dt.date
    return df


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set"); sys.exit(1)

    episodes = pd.read_csv(EPISODES_CSV)
    episodes["date"] = pd.to_datetime(episodes["date"]).dt.date
    print(f"Loaded {len(episodes)} episodes from {EPISODES_CSV}")

    # --- Arm B: find breakout dates ---
    print("Finding breakout dates (arm B)...")
    async with TradierClient(api_key=api_key) as client:
        breakouts = await find_breakouts(client, episodes)
    n_bo = sum(1 for v in breakouts.values() if v is not None)
    print(f"  Breakouts within {BREAKOUT_WINDOW}td: {n_bo}/{len(episodes)} "
          f"({len(episodes)-n_bo} bases never broke out)")

    # --- Build entry requests for both arms ---
    rows = []
    rid = 0
    for idx, ep in episodes.iterrows():
        # Arm A: coil-and-hold (enter on signal date)
        rows.append({"row_id": rid, "arm": "A", "episode_idx": idx, "ticker": ep["ticker"],
                     "signal_date": ep["date"], "entry_date": ep["date"],
                     "resistance": ep["resistance"]})
        rid += 1
        # Arm B: wait-for-breakout
        bo = breakouts.get(idx)
        if bo is not None:
            rows.append({"row_id": rid, "arm": "B", "episode_idx": idx, "ticker": ep["ticker"],
                         "signal_date": ep["date"], "entry_date": bo,
                         "resistance": ep["resistance"]})
            rid += 1
    reqs = pd.DataFrame(rows)
    print(f"Entry requests: {len(reqs)} ({(reqs['arm']=='A').sum()} A, {(reqs['arm']=='B').sum()} B)")

    # --- Select LEAPs from Athena ---
    print("Selecting ~0.40-delta LEAPs from Athena...")
    leaps = select_leaps(reqs)
    print(f"  Resolved {len(leaps)}/{len(reqs)} entries to a LEAP contract")

    # --- Merge + save ---
    merged = reqs.merge(leaps, on="row_id", suffixes=("", "_leap"), how="left")
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    merged.to_csv(OUT_CSV, index=False)

    resolved = merged.dropna(subset=["entry_mid"])
    print(f"\nResolved entries by arm:")
    print(f"  A: {(resolved['arm']=='A').sum()}/{(reqs['arm']=='A').sum()}")
    print(f"  B: {(resolved['arm']=='B').sum()}/{(reqs['arm']=='B').sum()}")
    print(f"\nSample resolved entries:")
    cols = ["arm", "ticker", "entry_date", "expiry", "strike", "delta", "entry_mid", "dte", "open_interest"]
    print(resolved[cols].head(20).to_string(index=False))
    print(f"\nEntry-price diagnostics (mid):")
    print(f"  median ${resolved['entry_mid'].median():.2f}, "
          f"delta median {resolved['delta'].median():.2f}, dte median {resolved['dte'].median():.0f}")
    print(f"\nWritten -> {OUT_CSV}")
    print("Next (Stage 3): reprice each LEAP forward (horizons + expiry + MFE), aggregate by arm & year.")


if __name__ == "__main__":
    asyncio.run(main())

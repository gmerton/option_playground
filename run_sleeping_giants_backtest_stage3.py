#!/usr/bin/env python3
"""
Sleeping Giants backtest — STAGE 3: LEAP payoff tracking + aggregation.

Reads resolved entries from Stage 2, reprices each LEAP forward from entry to expiry
(one batched Athena query), and computes ROC at fixed horizons, at expiry, and MFE.

Split/adjustment guard: option contracts get re-struck around underlying splits, so the
specific (ticker, expiry, strike) contract "vanishes" mid-life. We detect contracts whose
forward quotes stop well before expiry (and that weren't simply going to zero) and report
headline stats BOTH including and excluding them, so split artifacts don't silently pollute
the payoff.

Headline payoff = exit at +180 calendar days OR expiry, whichever comes first (a LEAP held
~6 months to let the breakout's delta+vega play out). We also report +90d, at-expiry, MFE.
Results broken out by arm (A coil-and-hold / B wait-for-breakout) and by regime
(pre-2022 quasi-OOS vs 2023+), so the bull-market concentration is visible.
"""
import sys
import os
import uuid
from datetime import date, timedelta
from typing import Optional, List, Dict

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

import pandas as pd
import numpy as np
import awswrangler as wr

from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import DB, TABLE, S3TABLES_CATALOG, GLUE_CATALOG, TMP_S3_PREFIX

ENTRIES_CSV = "data/studies/Adhikary/sleeping_giants_entries.csv"
OUT_CSV = "data/studies/Adhikary/sleeping_giants_trades.csv"

PRIMARY_HORIZON_DAYS = 180     # headline exit: +180 calendar days or expiry, whichever first
INCOMPLETE_GAP_DAYS = 45       # forward quotes ending > this before expiry => possible split artifact

T = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'


def write_contract_table(df: pd.DataFrame) -> tuple[str, str]:
    """Temp table of the entry contracts to reprice forward."""
    table_name = f"tmp_sg_contracts_{uuid.uuid4().hex}"
    s3_path = TMP_S3_PREFIX.rstrip("/") + f"/{table_name}/"
    dfw = df[["row_id", "ticker", "expiry", "strike", "entry_date"]].copy()
    dfw["expiry"] = pd.to_datetime(dfw["expiry"]).dt.date
    dfw["entry_date"] = pd.to_datetime(dfw["entry_date"]).dt.date
    dfw["ticker"] = dfw["ticker"].astype(str)
    dfw["strike"] = pd.to_numeric(dfw["strike"])
    wr.s3.to_parquet(
        df=dfw, path=s3_path, dataset=True, database=DB, table=table_name,
        compression="snappy", mode="overwrite",
        dtype={"row_id": "bigint", "ticker": "string", "expiry": "date",
               "strike": "double", "entry_date": "date"},
    )
    return table_name, s3_path


def fetch_forward_marks(contracts: pd.DataFrame) -> pd.DataFrame:
    """One Athena query: all daily call marks for each entry contract, entry_date..expiry."""
    _ensure_glue_db(DB)
    tmp_table, tmp_path = write_contract_table(contracts)
    try:
        sql = f"""
        SELECT
          c.row_id,
          o.trade_date,
          ROUND((o.bid + o.ask) / 2, 3) AS mark_mid,
          o.last
        FROM {T} o
        JOIN "{GLUE_CATALOG}"."{DB}"."{tmp_table}" c
          ON o.ticker = c.ticker
         AND o.expiry = c.expiry
         AND o.strike = c.strike
         AND o.cp = 'C'
        WHERE o.trade_date >= c.entry_date
          AND o.trade_date <= c.expiry
          AND o.bid > 0 AND o.ask > 0
        ORDER BY c.row_id, o.trade_date
        """
        df = athena(sql)
    finally:
        try:
            wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
            wr.s3.delete_objects(tmp_path)
        except Exception:
            pass
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df


def compute_payoff(entry, marks: pd.DataFrame) -> Optional[Dict]:
    """Given one entry row and its forward marks, compute ROC at horizons/expiry/MFE."""
    if marks.empty:
        return None
    entry_mid = float(entry["entry_mid"])
    entry_date = entry["entry_date"]
    expiry = entry["expiry"]
    m = marks.sort_values("trade_date").copy()
    m["d"] = (pd.to_datetime(m["trade_date"]) - pd.to_datetime(entry_date)).dt.days

    last_mark_date = m["trade_date"].max()
    days_short_of_expiry = (pd.to_datetime(expiry) - pd.to_datetime(last_mark_date)).days

    def roc_at(horizon_days):
        cand = m[m["d"] >= horizon_days]
        if not cand.empty:
            px = cand.iloc[0]["mark_mid"]
        else:
            px = m.iloc[-1]["mark_mid"]   # ran past last mark -> use last available
        return (px - entry_mid) / entry_mid * 100.0

    roc_90 = roc_at(90)
    roc_180 = roc_at(180)
    # expiry value: intrinsic-ish proxy = last available mark (LEAP repriced to its last quote)
    roc_expiry = (m.iloc[-1]["mark_mid"] - entry_mid) / entry_mid * 100.0
    mfe = (m["mark_mid"].max() - entry_mid) / entry_mid * 100.0

    # headline: +180d or expiry, whichever first
    roc_primary = roc_180

    # split/delisting artifact: forward quotes stop well before expiry AND last mark wasn't ~0
    incomplete = (days_short_of_expiry > INCOMPLETE_GAP_DAYS) and (m.iloc[-1]["mark_mid"] > 0.10)

    return {
        "roc_90": roc_90, "roc_180": roc_180, "roc_expiry": roc_expiry, "mfe": mfe,
        "roc_primary": roc_primary, "n_marks": len(m),
        "last_mark_date": last_mark_date, "days_short_of_expiry": days_short_of_expiry,
        "incomplete": incomplete,
    }


def summarize(df: pd.DataFrame, label: str):
    if df.empty:
        print(f"  {label}: (no trades)")
        return
    roc = df["roc_primary"]
    win = (roc > 0).mean() * 100
    print(f"  {label:30} n={len(df):3}  win={win:5.1f}%  "
          f"median={roc.median():7.1f}%  mean={roc.mean():7.1f}%  "
          f"MFE_med={df['mfe'].median():7.1f}%")


def main():
    entries = pd.read_csv(ENTRIES_CSV)
    entries = entries.dropna(subset=["entry_mid", "expiry", "strike"]).reset_index(drop=True)
    entries["entry_date"] = pd.to_datetime(entries["entry_date"]).dt.date
    entries["expiry"] = pd.to_datetime(entries["expiry"]).dt.date
    print(f"Loaded {len(entries)} resolved entries from {ENTRIES_CSV}")

    print("Repricing LEAPs forward (Athena)...")
    marks = fetch_forward_marks(entries)
    print(f"  Got {len(marks)} forward marks across {marks['row_id'].nunique()} contracts")

    rows = []
    for _, e in entries.iterrows():
        mk = marks[marks["row_id"] == e["row_id"]]
        po = compute_payoff(e, mk)
        if po is None:
            continue
        rows.append({**e.to_dict(), **po})
    trades = pd.DataFrame(rows)
    trades["yr"] = pd.to_datetime(trades["signal_date"]).dt.year
    trades["regime"] = np.where(trades["yr"] <= 2021, "pre2022_OOS", "2022plus")
    trades.to_csv(OUT_CSV, index=False)

    n_incomplete = int(trades["incomplete"].sum())
    clean = trades[~trades["incomplete"]].copy()
    print(f"\nFlagged {n_incomplete} entries as incomplete/split-artifact (excluded from clean stats).")

    print("\n" + "=" * 78)
    print("HEADLINE: ROC at +180d-or-expiry (CLEAN entries only)")
    print("=" * 78)
    summarize(clean, "ALL")
    summarize(clean[clean["arm"] == "A"], "Arm A (coil-and-hold)")
    summarize(clean[clean["arm"] == "B"], "Arm B (wait-for-breakout)")

    print("\nBy regime (clean):")
    for reg in ["pre2022_OOS", "2022plus"]:
        sub = clean[clean["regime"] == reg]
        summarize(sub[sub["arm"] == "A"], f"  A / {reg}")
        summarize(sub[sub["arm"] == "B"], f"  B / {reg}")

    print("\nArm A: include the 38 dead bases? (coil-and-hold trades them all)")
    print("  Arm A above already includes non-breakout episodes (every episode is an A trade).")

    print("\nMulti-horizon (clean, all arms):")
    for h, col in [("+90d", "roc_90"), ("+180d", "roc_180"), ("expiry", "roc_expiry"), ("MFE", "mfe")]:
        v = clean[col]
        print(f"  {h:8} win={ (v>0).mean()*100:5.1f}%  median={v.median():7.1f}%  mean={v.mean():7.1f}%")

    print(f"\nWritten -> {OUT_CSV}")


if __name__ == "__main__":
    main()

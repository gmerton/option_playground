#!/usr/bin/env python3
"""
Day P&L from IBKR NAV — the authoritative reconciliation.

Compares account NAV at consecutive report dates. This is the broker's own
mark-to-market, which is what we want: reconstructing marks position-by-position
from Tradier quotes proved unreliable for thinly-traded options (a short leg with
a $3.40 bid-ask makes `last` meaningless, and two such positions distorted a whole
day's reconciliation by ~$5.7k on 2026-08-14).

Requires an ACTIVITY Flex query containing "Net Asset Value (NAV) in Base"
(optionally "Change in NAV" and "Open Positions"). This is a SEPARATE query from
the trade-confirm one — Activity and Trade Confirmation are different Flex types
and cannot be combined.

The query id defaults to 1605053 (see flex_client.NAV_QUERY_ID); override with
IBKR_FLEX_NAV_QUERY_ID or --query-id.

Usage:
    IBKR_FLEX_TOKEN=... PYTHONPATH=src .venv/bin/python3 run_nav_report.py
    ... --days 30
    ... --query-id 1234567     # one-off override
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

import pandas as pd

from lib.ibkr.flex_client import NAV_QUERY_ID, fetch_flex_query, parse_flex_xml

NAV_TAGS = ["EquitySummaryByReportDateInBase", "EquitySummaryInBase", "ChangeInNAV"]


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--query-id", default=None)
    a = ap.parse_args()

    qid = a.query_id or NAV_QUERY_ID
    if not qid:
        sys.exit("No NAV query id. Create an Activity Flex query with the "
                 "'Net Asset Value (NAV) in Base' section, then set "
                 "IBKR_FLEX_NAV_QUERY_ID or pass --query-id.")

    # Do NOT pass fd/td. An Activity Flex query with a configured Period rejects
    # an explicit range with "Fail: Statement is not available". Let the query's own
    # Period govern; trim client-side with --days.
    print(f"NAV query {qid} (using the query's configured period)")
    dfs = parse_flex_xml(fetch_flex_query(query_id=qid))
    print(f"sections returned: {list(dfs)}\n")

    nav = next((dfs[t] for t in NAV_TAGS if t in dfs and not dfs[t].empty), None)
    if nav is None:
        sys.exit(f"No NAV section found. Got {list(dfs)}. The query needs "
                 f"'Net Asset Value (NAV) in Base'.")

    datecol = next((c for c in ("reportDate", "toDate", "date") if c in nav.columns), None)
    valcol = next((c for c in ("total", "endingValue", "cash") if c in nav.columns), None)
    if not datecol or not valcol:
        print("Unexpected NAV columns:", list(nav.columns)); sys.exit(1)

    nav = nav[[datecol, valcol]].copy()
    nav.columns = ["report_date", "nav"]
    nav["nav"] = pd.to_numeric(nav.nav, errors="coerce")
    nav = nav.dropna().drop_duplicates("report_date").sort_values("report_date")
    nav["day_pnl"] = nav.nav.diff()
    nav["pct"] = nav.nav.pct_change() * 100
    if a.days:
        nav = nav.tail(a.days + 1)

    print(f"{'report date':<14}{'NAV $':>16}{'day P&L $':>14}{'%':>9}")
    print("-" * 53)
    for r in nav.itertuples(index=False):
        d = f"{r.day_pnl:,.2f}" if pd.notna(r.day_pnl) else "—"
        p = f"{r.pct:+.2f}%" if pd.notna(r.pct) else "—"
        print(f"{str(r.report_date):<14}{r.nav:>16,.2f}{d:>14}{p:>9}")

    if len(nav) >= 2:
        last = nav.iloc[-1]
        print(f"\n  latest session: {last.report_date}   day P&L "
              f"${last.day_pnl:,.2f} ({last.pct:+.2f}%)")

    if "ChangeInNAV" in dfs and not dfs["ChangeInNAV"].empty:
        c = dfs["ChangeInNAV"]
        # One ChangeInNAV row per report date — show the latest session only.
        # Summing every row would silently report a period total instead.
        if "toDate" in c.columns:
            c = c.sort_values("toDate").tail(1)
        row = c.iloc[0]
        label = row.get("toDate", "latest")
        print(f"\n=== IBKR's own Change-in-NAV breakdown — {label} ===")
        skip = {"accountId", "acctAlias", "model", "currency", "fromDate", "toDate"}
        for col, val in row.items():
            if col in skip:
                continue
            v = pd.to_numeric(val, errors="coerce")
            if pd.notna(v) and abs(v) > 0.004:
                print(f"  {col:<32}{v:>14,.2f}")

    nav.to_csv("nav_daily.csv", index=False)
    print(f"\n  saved -> nav_daily.csv")


if __name__ == "__main__":
    main()

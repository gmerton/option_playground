#!/usr/bin/env python3
"""
Generate a daily trade journal draft from the IBKR Flex NAV report.

Pulls the same Activity Flex query used by run_nav_report.py (Open Positions +
Trades sections) and writes a markdown draft to data/journal/<date>.md covering
the whole portfolio for the most recent available session:
  - Opened today (new entries -- for evaluating entries)
  - Closed today (exits -- for evaluating exits; flags same-day round trips)
  - Held, untouched today (no fills at all -- for "should we have closed this?")
  - A raw fills table (overtrading pulse: total fills / unique symbols)
  - An empty Notes section per bucket for the daily journaling conversation

NAV data lands ~1 session behind (see [[project_ibkr_flex_nav]] memory), so
"today's" draft usually reflects yesterday's session until the next morning.

Won't overwrite an existing journal file -- once notes are added by hand,
re-running is a no-op unless --force is passed.

Also persists the same pull to MySQL (journal_nav, journal_trades,
journal_open_positions -- created on first run) so the history is queryable
later, not just readable as markdown. All three upserts are idempotent
(tradeID / (report_date, conid) / report_date), so re-running a day is safe.
Pass --no-db to skip this and only write the markdown.

Usage:
    IBKR_FLEX_TOKEN=... MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_daily_journal.py
    ... --force      # regenerate the markdown even if today's file already exists (drops notes!)
    ... --no-db      # markdown only, skip MySQL

Requires: IBKR_FLEX_TOKEN, MYSQL_PASSWORD.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from lib.ibkr.flex_client import NAV_QUERY_ID, fetch_flex_query, parse_flex_xml
from lib.mysql_lib import (
    create_journal_tables,
    upsert_journal_nav,
    upsert_journal_open_positions,
    upsert_journal_trades,
)

JOURNAL_DIR = Path("data/journal")


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(dtype=float)


def _fmt_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def _trade_key(row) -> str:
    """Group key: option/stock contract identity (conid is the safe key)."""
    return row["conid"]


def build_journal(
    dfs: dict[str, pd.DataFrame], target_date: str | None = None
) -> tuple[str, str, pd.DataFrame, pd.DataFrame, float | None, float | None]:
    """Return (report_date_yyyymmdd, markdown_text, opl, trl, nav, day_pnl).

    opl/trl are the OpenPosition/Trade rows filtered to the target report/trade
    date -- the caller persists these to MySQL alongside writing the markdown.
    target_date: YYYYMMDD string. Defaults to the latest date in the pull (the
    query's "Last 30 Calendar Days" window holds ~22 sessions, so any date in
    that window can be requested without a fresh fetch).
    """
    op = dfs["OpenPosition"]
    tr = dfs["Trade"]
    es = dfs.get("EquitySummaryByReportDateInBase")

    if target_date:
        available = set(op["reportDate"].unique()) | set(tr["tradeDate"].unique())
        if target_date not in available:
            raise ValueError(f"{target_date} not in this pull's window. Available: {sorted(available)}")
        latest_pos_date = latest_trade_date = target_date
    else:
        latest_pos_date = sorted(op["reportDate"].unique())[-1]
        latest_trade_date = sorted(tr["tradeDate"].unique())[-1]
    report_date = max(latest_pos_date, latest_trade_date)

    opl = op[op["reportDate"] == latest_pos_date].copy()
    trl = tr[tr["tradeDate"] == latest_trade_date].copy()
    for c in ("quantity", "tradePrice", "fifoPnlRealized"):
        trl[c] = _num(trl, c)
    for c in ("position", "markPrice", "openPrice", "fifoPnlUnrealized", "positionValue"):
        opl[c] = _num(opl, c)

    # NAV header
    nav_line = ""
    nav_val, day_pnl_val = None, None
    if es is not None and not es.empty:
        es = es.copy()
        es["total"] = _num(es, "total")
        nav = es[["reportDate", "total"]].dropna().drop_duplicates("reportDate").sort_values("reportDate")
        nav["day_pnl"] = nav["total"].diff()
        row = nav[nav["reportDate"] == report_date]
        if not row.empty:
            r = row.iloc[0]
            nav_val, day_pnl_val = r["total"], r["day_pnl"]
            pnl_str = f"${day_pnl_val:,.2f}" if pd.notna(day_pnl_val) else "n/a"
            nav_line = f"NAV: ${nav_val:,.2f}  |  Day P&L: {pnl_str}"

    open_conids = set(opl["conid"])
    trade_conids = set(trl["conid"])

    # Per-conid rollup of today's fills
    def label(cid: str) -> str:
        rows = trl[trl["conid"] == cid]
        r0 = rows.iloc[0]
        return r0["symbol"] if r0["assetCategory"] == "OPT" else r0["symbol"]

    opened, closed, roundtrip = [], [], []
    for cid in trade_conids:
        rows = trl[trl["conid"] == cid]
        # A single fill can be "C;O" (reversal -- closes the existing position and
        # opens a new one the other way in one execution); count it in both buckets.
        o_rows = rows[rows["openCloseIndicator"].isin(["O", "C;O"])]
        c_rows = rows[rows["openCloseIndicator"].isin(["C", "C;O"])]
        has_o, has_c = not o_rows.empty, not c_rows.empty
        still_open = cid in open_conids
        sym = label(cid)
        o_qty = o_rows["quantity"].sum() if has_o else 0
        o_px = (o_rows["tradePrice"] * o_rows["quantity"]).sum() / o_qty if has_o and o_qty else None
        c_qty = c_rows["quantity"].sum() if has_c else 0
        c_pnl = c_rows["fifoPnlRealized"].sum() if has_c else 0
        n_fills = len(rows)
        if has_o and has_c:
            roundtrip.append((sym, n_fills, o_qty, c_qty, c_pnl, still_open))
        elif has_o:
            opened.append((sym, n_fills, o_qty, o_px, still_open))
        elif has_c:
            closed.append((sym, n_fills, c_qty, c_pnl, still_open))

    # Held, untouched today: open positions whose conid had zero fills today
    held = opl[~opl["conid"].isin(trade_conids)].copy()

    lines = []
    lines.append(f"# Trade Journal -- {_fmt_date(report_date)}")
    lines.append("")
    if nav_line:
        lines.append(nav_line)
    lines.append(f"Fills today: {len(trl)}  |  Unique symbols traded: {len(trade_conids)}  |  "
                 f"Open positions: {len(opl)}")
    lines.append("")
    lines.append("_NAV data lands ~1 session behind -- this reflects the most recent available session, "
                 "not necessarily today's calendar date._")
    lines.append("")

    lines.append("## Opened today (new entries)")
    lines.append("")
    if opened:
        lines.append("| Symbol | Fills | Qty | Avg Price | Notes (entry eval) |")
        lines.append("|---|---:|---:|---:|---|")
        for sym, n, qty, px, _so in sorted(opened):
            px_s = f"{px:,.4f}" if px is not None else "n/a"
            lines.append(f"| {sym} | {n} | {qty:g} | {px_s} | |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Closed today (exits)")
    lines.append("")
    if closed:
        lines.append("| Symbol | Fills | Qty | Realized P&L | Notes (exit eval) |")
        lines.append("|---|---:|---:|---:|---|")
        for sym, n, qty, pnl, _so in sorted(closed):
            lines.append(f"| {sym} | {n} | {qty:g} | ${pnl:,.2f} | |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Same-day round trips (opened AND closed today)")
    lines.append("")
    if roundtrip:
        lines.append("| Symbol | Fills | Qty Opened | Qty Closed | Realized P&L | Still open? | Notes |")
        lines.append("|---|---:|---:|---:|---:|---|---|")
        for sym, n, oq, cq, pnl, so in sorted(roundtrip):
            lines.append(f"| {sym} | {n} | {oq:g} | {cq:g} | ${pnl:,.2f} | {'yes' if so else 'no'} | |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Held, untouched today (no fills -- should this have been closed?)")
    lines.append("")
    if not held.empty:
        lines.append("| Symbol | Position | Open Price | Mark | Unrealized P&L | Notes |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for _, r in held.sort_values("symbol").iterrows():
            lines.append(f"| {r['symbol']} | {r['position']:g} | {r['openPrice']:,.4f} | "
                         f"{r['markPrice']:,.4f} | ${r['fifoPnlUnrealized']:,.2f} | |")
    else:
        lines.append("_None -- every open position had activity today._")
    lines.append("")

    lines.append("## Overtrading notes")
    lines.append("")
    lines.append("_Freeform -- flag any symbols with excessive same-day fills, revenge trades, "
                 "size creep, etc._")
    lines.append("")

    lines.append("## General notes")
    lines.append("")
    lines.append("")

    return report_date, "\n".join(lines), opl, trl, nav_val, day_pnl_val


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query-id", default=None)
    ap.add_argument("--date", default=None, help="YYYYMMDD -- backfill a specific session instead of the latest")
    ap.add_argument("--force", action="store_true", help="overwrite an existing journal file")
    ap.add_argument("--no-db", action="store_true", help="skip persisting to MySQL (markdown only)")
    a = ap.parse_args()

    qid = a.query_id or NAV_QUERY_ID
    if not qid:
        sys.exit("No NAV query id. Set IBKR_FLEX_NAV_QUERY_ID or pass --query-id.")

    dfs = parse_flex_xml(fetch_flex_query(query_id=qid))
    missing = [t for t in ("OpenPosition", "Trade") if t not in dfs]
    if missing:
        sys.exit(f"Missing required sections {missing}. Got: {list(dfs)}")

    report_date, md, opl, trl, nav_val, day_pnl_val = build_journal(dfs, target_date=a.date)

    if not a.no_db:
        create_journal_tables()
        upsert_journal_nav(pd.Timestamp(_fmt_date(report_date)).date(), nav_val, day_pnl_val)
        n_pos = upsert_journal_open_positions(opl)
        n_tr = upsert_journal_trades(trl)
        print(f"DB: upserted {n_pos} open positions, {n_tr} trades, NAV row for {_fmt_date(report_date)}")

    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = JOURNAL_DIR / f"{_fmt_date(report_date)}.md"

    if out_path.exists() and not a.force:
        print(f"{out_path} already exists -- leaving it alone (pass --force to regenerate).")
        return

    out_path.write_text(md)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

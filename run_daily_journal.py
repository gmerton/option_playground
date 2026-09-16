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
  - Option campaigns touched today: a spread and everything it was rolled into, as ONE entity
    (lib/journal/campaigns.py; tables journal_campaigns / journal_campaign_trades, rebuilt each run)
  - An empty Notes section per bucket for the daily journaling conversation

Every grid carries the same four sort keys: ticker (split out of the option
symbol), entry date, exit date and P&L -- with entry and exit as SEPARATE date
and price fields. Entry/exit dates come from flat-to-flat cycles in
journal_trades (lib.mysql_lib.reconstruct_trade_cycles), so a position opened
before that table's history starts shows a blank entry date rather than a wrong
one. Markdown tables can't sort, so the same grids are also written to
data/journal/days/<date>.html, where clicking a header re-sorts.

NAV data lands ~1 session behind (see [[project_ibkr_flex_nav]] memory), so
"today's" draft usually reflects yesterday's session until the next morning.

Won't overwrite an existing journal file -- once notes are added by hand,
re-running is a no-op unless --force is passed. (The HTML grids hold no notes,
so they are always rewritten.)

Also persists the same pull to MySQL (journal_nav, journal_trades,
journal_open_positions -- created on first run) so the history is queryable
later, not just readable as markdown. All three upserts are idempotent
(tradeID / (report_date, conid) / report_date), so re-running a day is safe.
Pass --no-db to skip this and only write the markdown -- entry/exit dates for
positions opened on an earlier session need the DB, so they come out blank.

Usage:
    IBKR_FLEX_TOKEN=... MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_daily_journal.py
    ... --force      # regenerate the markdown even if today's file already exists (drops notes!)
    ... --no-db      # markdown only, skip MySQL
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from lib.ibkr.flex_client import NAV_QUERY_ID, fetch_flex_query, parse_flex_xml
from lib.journal.day_page import render_day_page, render_days_index
from lib.mysql_lib import (
    create_journal_tables,
    upsert_journal_nav,
    upsert_journal_open_positions,
    upsert_journal_trades,
)

JOURNAL_DIR = Path("data/journal")
DAYS_DIR = JOURNAL_DIR / "days"


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(dtype=float)


def _fmt_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def _split_symbol(row) -> tuple[str, str]:
    """Ticker and contract as two fields: 'QCOM  261016P00145000' -> ('QCOM', '10/16/26 145P').

    Sorting the raw Flex symbol works by accident (the ticker is a prefix) but
    can't group a name's stock and option legs, and can't be sorted on its own.
    """
    sym = str(row.get("symbol") or "").strip()
    if str(row.get("assetCategory") or "") != "OPT":
        return sym, ""
    ticker = str(row.get("underlyingSymbol") or "").strip() or sym.split(" ")[0]
    exp = str(row.get("expiry") or "").strip()
    exp_s = f"{exp[4:6]}/{exp[6:8]}/{exp[2:4]}" if len(exp) == 8 and exp.isdigit() else exp
    strike = pd.to_numeric(row.get("strike"), errors="coerce")
    pc = str(row.get("putCall") or "").strip()[:1]
    leg = f"{strike:g}{pc}" if pd.notna(strike) else pc
    return ticker, " ".join(p for p in (exp_s, leg) if p)


def _cycles_by_conid(cycles: pd.DataFrame | None, date_iso: str) -> dict[str, dict]:
    """conid -> the flat-to-flat cycle live on `date_iso` (entry/exit dates and prices).

    A repeatedly-traded contract has several cycles; pick the one spanning the
    session (the latest, if a close and a re-open share the date). A contract
    with no cycle spanning it is simply absent -- blank beats a wrong date.
    """
    if cycles is None or cycles.empty:
        return {}
    c = cycles.copy()
    c["conid"] = c["conid"].astype(str)
    c["entry_s"] = c["entry_date"].astype(str)
    c["exit_s"] = c["exit_date"].apply(lambda v: "" if v is None or pd.isna(v) else str(v))
    out: dict[str, dict] = {}
    for cid, g in c.groupby("conid"):
        g = g.sort_values("entry_s")
        live = g[(g["entry_s"] <= date_iso) & ((g["exit_s"] == "") | (g["exit_s"] >= date_iso))]
        if live.empty:
            # No cycle spans the session (the contract's history predates the
            # table, say) -- leave it blank rather than attach an older cycle.
            continue
        pick = live.iloc[-1]
        out[cid] = {
            "entry_date": pick["entry_s"] or None,
            "exit_date": pick["exit_s"] or None,
            "entry_price": None if pd.isna(pick["entry_price"]) else float(pick["entry_price"]),
            "exit_price": None if pd.isna(pick["exit_price"]) else float(pick["exit_price"]),
        }
    return out


def _apply_cycle(row: dict, cyc: dict | None, *, keep_exit: bool = True) -> dict:
    """Fill entry/exit fields from the cycle, keeping any value already computed
    from today's own fills (which is the authoritative one for today's side)."""
    if cyc:
        for k in ("entry_date", "entry_price", "exit_date", "exit_price"):
            if not keep_exit and k.startswith("exit_"):
                continue
            if row.get(k) is None:
                row[k] = cyc.get(k)
    return row


def prepare(dfs: dict[str, pd.DataFrame], target_date: str | None = None) -> dict:
    """Bucket the session's fills and positions. No rendering, no DB.

    Returns a ctx dict: report_date (YYYYMMDD), date_iso, nav, day_pnl, counts,
    opl/trl (the filtered OpenPosition/Trade frames the caller persists), and
    buckets{opened, closed, roundtrip, held} as lists of row dicts.
    target_date: YYYYMMDD. Defaults to the latest date in the pull (the query's
    "Last 30 Calendar Days" window holds ~22 sessions, so any date in that
    window can be requested without a fresh fetch).
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
    date_iso = _fmt_date(report_date)

    opl = op[op["reportDate"] == latest_pos_date].copy()
    trl = tr[tr["tradeDate"] == latest_trade_date].copy()
    for c in ("quantity", "tradePrice", "fifoPnlRealized"):
        trl[c] = _num(trl, c)
    for c in ("position", "markPrice", "openPrice", "fifoPnlUnrealized", "positionValue"):
        opl[c] = _num(opl, c)

    nav_val, day_pnl_val = None, None
    if es is not None and not es.empty:
        es = es.copy()
        es["total"] = _num(es, "total")
        nav = es[["reportDate", "total"]].dropna().drop_duplicates("reportDate").sort_values("reportDate")
        nav["day_pnl"] = nav["total"].diff()
        row = nav[nav["reportDate"] == report_date]
        if not row.empty:
            r = row.iloc[0]
            nav_val = float(r["total"])
            day_pnl_val = None if pd.isna(r["day_pnl"]) else float(r["day_pnl"])

    open_conids = set(opl["conid"])
    trade_conids = set(trl["conid"])

    def _vwap(rows: pd.DataFrame) -> float | None:
        w = rows["quantity"].abs()
        if rows.empty or w.sum() == 0:
            return None
        return float((rows["tradePrice"] * w).sum() / w.sum())

    opened, closed, roundtrip = [], [], []
    for cid in trade_conids:
        rows = trl[trl["conid"] == cid]
        r0 = rows.iloc[0]
        ticker, contract = _split_symbol(r0)
        # A single fill can be "C;O" (reversal -- closes the existing position and
        # opens a new one the other way in one execution); count it in both buckets.
        o_rows = rows[rows["openCloseIndicator"].isin(["O", "C;O"])]
        c_rows = rows[rows["openCloseIndicator"].isin(["C", "C;O"])]
        has_o, has_c = not o_rows.empty, not c_rows.empty
        still_open = cid in open_conids
        # IBKR spreads fifoPnlRealized across BOTH legs of a same-day round trip (MRVL 9/14: +72.27 on the opening
        # sell, +2.36 on the closing buy); only the sum across every fill of the day is the trade's P&L
        pnl = float(rows["fifoPnlRealized"].sum())
        base = {
            "conid": cid, "ticker": ticker, "contract": contract, "symbol": str(r0["symbol"]).strip(),
            "fills": len(rows), "still_open": still_open, "still_open_s": "yes" if still_open else "no",
            "pnl": pnl if abs(pnl) >= 0.005 else None,
            "entry_date": date_iso if has_o else None,
            "entry_price": _vwap(o_rows) if has_o else None,
            "exit_date": date_iso if has_c else None,
            "exit_price": _vwap(c_rows) if has_c else None,
        }
        if has_o and has_c:
            roundtrip.append({**base, "qty_opened": float(o_rows["quantity"].sum()),
                              "qty_closed": float(c_rows["quantity"].sum())})
        elif has_o:
            opened.append({**base, "qty": float(o_rows["quantity"].sum())})
        elif has_c:
            closed.append({**base, "qty": float(c_rows["quantity"].sum())})

    # Held, untouched today: open positions whose conid had zero fills today
    held = []
    for _, r in opl[~opl["conid"].isin(trade_conids)].iterrows():
        ticker, contract = _split_symbol(r)
        unreal = r["fifoPnlUnrealized"]
        held.append({
            "conid": r["conid"], "ticker": ticker, "contract": contract, "symbol": str(r["symbol"]).strip(),
            "qty": float(r["position"]), "mark": None if pd.isna(r["markPrice"]) else float(r["markPrice"]),
            "entry_date": None, "entry_price": None if pd.isna(r["openPrice"]) else float(r["openPrice"]),
            "exit_date": None, "exit_price": None,
            "pnl": None if pd.isna(unreal) else float(unreal),
            "still_open": True, "still_open_s": "yes",
        })

    def _key(r: dict) -> tuple:
        return (r["ticker"], r["contract"])

    return {
        "report_date": report_date, "date_iso": date_iso,
        "nav": nav_val, "day_pnl": day_pnl_val,
        "n_fills": len(trl), "n_symbols": len(trade_conids), "n_positions": len(opl),
        "opl": opl, "trl": trl,
        "buckets": {
            "opened": sorted(opened, key=_key), "closed": sorted(closed, key=_key),
            "roundtrip": sorted(roundtrip, key=_key), "held": sorted(held, key=_key),
        },
    }


def attach_cycles(ctx: dict, cycles: pd.DataFrame | None) -> dict:
    """Fill in entry/exit dates and prices for positions whose cycle began earlier."""
    date_iso = ctx["date_iso"]
    idx = _cycles_by_conid(cycles, date_iso)
    for name, rows in ctx["buckets"].items():
        for r in rows:
            cyc = idx.get(str(r["conid"]))
            # Neither bucket has an opening fill today, so a cycle claiming today
            # as its entry is a truncated one: its real entry predates the table.
            if cyc and name in ("closed", "held") and cyc.get("entry_date") == date_iso:
                cyc = {**cyc, "entry_date": None, "entry_price": None}
            # 'held' has no fills today, so the cycle is the only source; for the
            # traded buckets today's own fills win and the cycle fills the gaps.
            _apply_cycle(r, cyc, keep_exit=(name not in ("opened", "held")))
    if cycles is not None and not cycles.empty:
        ctx["entry_date_floor"] = str(cycles["entry_date"].min())
    return ctx


# ── Markdown rendering ─────────────────────────────────────────────────────────

FIFO_NOTE_MD = (
    "_A realized P&L on an OPENING fill is IBKR re-attributing FIFO P&L to a recently closed cycle in the "
    "same contract, not today's entry making money -- it cancels the offsetting figure booked on that close._"
)


def _md_date(v) -> str:
    return str(v) if v else "—"


def _md_px(v) -> str:
    return f"{v:,.4f}" if v is not None else "—"


def _md_pnl(v) -> str:
    return f"${v:,.2f}" if v is not None else "—"


def render_markdown(ctx: dict) -> str:
    b = ctx["buckets"]
    lines = [f"# Trade Journal -- {ctx['date_iso']}", ""]
    if ctx["nav"] is not None:
        pnl_s = f"${ctx['day_pnl']:,.2f}" if ctx["day_pnl"] is not None else "n/a"
        lines.append(f"NAV: ${ctx['nav']:,.2f}  |  Day P&L: {pnl_s}")
    lines += [
        f"Fills today: {ctx['n_fills']}  |  Unique symbols traded: {ctx['n_symbols']}  |  "
        f"Open positions: {ctx['n_positions']}",
        "",
        "_NAV data lands ~1 session behind -- this reflects the most recent available session, "
        "not necessarily today's calendar date._",
        "",
        f"_Sortable version of these grids (click any header): `data/journal/days/{ctx['date_iso']}.html`._",
        "",
    ]

    floor = ctx.get("entry_date_floor")
    caveat = (f"_Entry dates come from flat-to-flat cycles in `journal_trades`, which starts {floor} -- "
              f"a position opened before then shows an em dash._") if floor else ""

    lines += ["## Opened today (new entries)", ""]
    if b["opened"]:
        lines.append("| Ticker | Contract | Fills | Qty | Entry date | Entry $ | Exit date | Exit $ | P&L | "
                     "Notes (entry eval) |")
        lines.append("|---|---|---:|---:|---|---:|---|---:|---:|---|")
        for r in b["opened"]:
            lines.append(f"| {r['ticker']} | {r['contract']} | {r['fills']} | {r['qty']:g} | "
                         f"{_md_date(r['entry_date'])} | {_md_px(r['entry_price'])} | "
                         f"{_md_date(r['exit_date'])} | {_md_px(r['exit_price'])} | {_md_pnl(r['pnl'])} | |")
        if any(r["pnl"] is not None for r in b["opened"]):
            lines += ["", FIFO_NOTE_MD]
    else:
        lines.append("_None._")
    lines.append("")

    lines += ["## Closed today (exits)", ""]
    if b["closed"]:
        lines.append("| Ticker | Contract | Fills | Qty | Entry date | Entry $ | Exit date | Exit $ | "
                     "Realized P&L | Notes (exit eval) |")
        lines.append("|---|---|---:|---:|---|---:|---|---:|---:|---|")
        for r in b["closed"]:
            lines.append(f"| {r['ticker']} | {r['contract']} | {r['fills']} | {r['qty']:g} | "
                         f"{_md_date(r['entry_date'])} | {_md_px(r['entry_price'])} | "
                         f"{_md_date(r['exit_date'])} | {_md_px(r['exit_price'])} | {_md_pnl(r['pnl'])} | |")
        if caveat:
            lines += ["", caveat]
    else:
        lines.append("_None._")
    lines.append("")

    lines += ["## Same-day round trips (opened AND closed today)", ""]
    if b["roundtrip"]:
        lines.append("| Ticker | Contract | Fills | Qty Opened | Qty Closed | Entry date | Entry $ | "
                     "Exit date | Exit $ | Realized P&L | Still open? | Notes |")
        lines.append("|---|---|---:|---:|---:|---|---:|---|---:|---:|---|---|")
        for r in b["roundtrip"]:
            lines.append(f"| {r['ticker']} | {r['contract']} | {r['fills']} | {r['qty_opened']:g} | "
                         f"{r['qty_closed']:g} | {_md_date(r['entry_date'])} | {_md_px(r['entry_price'])} | "
                         f"{_md_date(r['exit_date'])} | {_md_px(r['exit_price'])} | {_md_pnl(r['pnl'])} | "
                         f"{r['still_open_s']} | |")
    else:
        lines.append("_None._")
    lines.append("")

    lines += ["## Held, untouched today (no fills -- should this have been closed?)", ""]
    if b["held"]:
        lines.append("| Ticker | Contract | Position | Entry date | Entry $ | Exit date | Mark | "
                     "Unrealized P&L | Notes |")
        lines.append("|---|---|---:|---|---:|---|---:|---:|---|")
        for r in b["held"]:
            mark = f"{r['mark']:,.4f}" if r["mark"] is not None else "—"
            lines.append(f"| {r['ticker']} | {r['contract']} | {r['qty']:g} | {_md_date(r['entry_date'])} | "
                         f"{_md_px(r['entry_price'])} | {_md_date(r['exit_date'])} | {mark} | "
                         f"{_md_pnl(r['pnl'])} | |")
        if caveat:
            lines += ["", caveat]
    else:
        lines.append("_None -- every open position had activity today._")
    lines.append("")

    lines += ["## Overtrading notes", "",
              "_Freeform -- flag any symbols with excessive same-day fills, revenge trades, size creep, etc._",
              "", "## General notes", "", ""]
    return "\n".join(lines)


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

    ctx = prepare(dfs, target_date=a.date)
    date_iso = ctx["date_iso"]

    cycles = None
    if not a.no_db:
        create_journal_tables()
        upsert_journal_nav(pd.Timestamp(date_iso).date(), ctx["nav"], ctx["day_pnl"])
        n_pos = upsert_journal_open_positions(ctx["opl"])
        n_tr = upsert_journal_trades(ctx["trl"])
        print(f"DB: upserted {n_pos} open positions, {n_tr} trades, NAV row for {date_iso}")
        # Entry/exit dates need the fill history, and today's fills must already be in it.
        try:
            from lib.mysql_lib import reconstruct_trade_cycles
            cycles = reconstruct_trade_cycles()
        except Exception as exc:  # noqa: BLE001 -- the journal must still be written
            print(f"entry/exit dates skipped: {exc.__class__.__name__}: {exc}")
    else:
        print("--no-db: entry/exit dates for positions opened on an earlier session will be blank")

    attach_cycles(ctx, cycles)
    md = render_markdown(ctx)

    if not a.no_db:
        # option campaigns: rolls chained into one entity (lib/journal/campaigns.py); section goes before the notes
        try:
            from lib.journal.campaigns import journal_section
            sec = journal_section(pd.Timestamp(date_iso).date())
            md = md.replace("## Overtrading notes", sec + "## Overtrading notes", 1)
        except Exception as exc:  # noqa: BLE001 -- the journal must still be written
            print(f"campaign section skipped: {exc.__class__.__name__}: {exc}")

    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    DAYS_DIR.mkdir(parents=True, exist_ok=True)

    # The HTML grids carry no hand-written notes, so they are always rewritten.
    day_html = DAYS_DIR / f"{date_iso}.html"
    day_html.write_text(render_day_page(ctx))
    (DAYS_DIR / "index.html").write_text(render_days_index(DAYS_DIR))
    print(f"Wrote {day_html} (sortable grids)")

    out_path = JOURNAL_DIR / f"{date_iso}.md"
    if out_path.exists() and not a.force:
        print(f"{out_path} already exists -- leaving it alone (pass --force to regenerate).")
        return

    out_path.write_text(md)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

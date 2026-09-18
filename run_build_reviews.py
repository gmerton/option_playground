#!/usr/bin/env python3
"""
Build journal_trade_reviews rows for the trade cycles opened in a date range, from the SAME machinery the
process grade uses -- no prose judgement (feedback: one rubric for alerts + journal). 2026-09-18.

  stock cycle  entry verdict = the rubric grade in journal_entry_grades for that fill (A/B good, C gray_area, F bad);
               exit verdict for a same-day close = lib.journal.exit_kind (INVALIDATION good, NOISE_STOP too_soon,
               DISCRETIONARY gray_area); still open -> n_a + tag open_position; closed later -> gray_area + needs_exit_review.
  option legs  one review per journal_campaigns campaign whose first_date is in range (the structure -- straddle,
               vertical, condor, single leg -- is the unit, not the leg). Entry verdict gray_area with the structure
               named; matched-timestamp legs are tagged systematic. Straddles that appear on that day's straddle
               screen archive (data/watchlist/straddle_screen/straddle_screen_<date>.csv, pass_all) are tagged screen_pick.
Then: apply_pending_notes() (attaches the notes staged before the Flex pull), sync_review_campaigns(), sync_review_tags().
Idempotent per (underlying_symbol, entry_date, symbol): existing rows are left alone.

Usage: MYSQL_PASSWORD=... TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_build_reviews.py --since 2026-09-14 [--until 2026-09-17]
"""
from __future__ import annotations
import argparse, os, warnings
from datetime import date
from pathlib import Path
import pandas as pd
from lib.mysql_lib import (_get_conn, reconstruct_trade_cycles, add_trade_review, apply_pending_notes,
                           sync_review_campaigns, sync_review_tags)
from lib.journal.exit_kind import cycles_from_fills, classify_sync

warnings.filterwarnings("ignore")
VERDICT = {"A": "good", "B": "good", "C": "gray_area", "F": "bad"}
EXIT = {"INVALIDATION": ("good", "same-day exit at the trade's worst price after a pre-entry level broke (invalidation)"),
        "NOISE_STOP": ("too_soon", "same-day exit near the trade's worst price with no pre-entry level broken (noise stop)"),
        "DISCRETIONARY": ("gray_area", "same-day discretionary exit, not at the trade's worst price"),
        "UNKNOWN": ("gray_area", "same-day exit; 1-min bars unavailable to classify")}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--since", required=True); ap.add_argument("--until", default=None); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); since = pd.Timestamp(a.since).date(); until = pd.Timestamp(a.until).date() if a.until else date.today()
    conn = _get_conn()
    existing = pd.read_sql("SELECT underlying_symbol, entry_date, symbol FROM journal_trade_reviews WHERE entry_date BETWEEN %s AND %s", conn, params=[since, until])
    have = set(zip(existing.underlying_symbol, pd.to_datetime(existing.entry_date).dt.date, existing.symbol))
    grades = pd.read_sql("SELECT * FROM journal_entry_grades WHERE trade_date BETWEEN %s AND %s", conn, params=[since, until])
    grades["trade_date"] = pd.to_datetime(grades["trade_date"]).dt.date
    camps = pd.read_sql("SELECT * FROM journal_campaigns WHERE first_date BETWEEN %s AND %s", conn, params=[since, until])
    ctr = pd.read_sql("SELECT ct.campaign_id, t.trade_id, t.symbol, t.trade_datetime, t.quantity, t.buy_sell, t.put_call, t.strike, t.expiry "
                      "FROM journal_campaign_trades ct JOIN journal_trades t ON t.trade_id = ct.trade_id", conn)
    trades = pd.read_sql("SELECT trade_date, underlying_symbol, trade_datetime, buy_sell, quantity, trade_price, asset_category FROM journal_trades WHERE trade_date BETWEEN %s AND %s", conn, params=[since, until])
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    conn.close()

    cyc = reconstruct_trade_cycles(); cyc = cyc[(cyc.entry_date >= since) & (cyc.entry_date <= until)]
    # same-day stock exits, classified from 1-min bars (the same call the process grade makes)
    stk = trades[trades.asset_category == "STK"]; same_day = cycles_from_fills(stk)
    adr_by = {}
    try:
        panel = pd.read_parquet("data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "high", "low"]); panel = panel[panel.date >= "2026-07-01"]
        panel["adr"] = (panel.high / panel.low - 1) * 100; adr_by = panel.groupby("ticker")["adr"].apply(lambda s: s.tail(20).mean()).to_dict()
    except Exception: pass
    kinds = {}
    if same_day and os.environ.get("TRADIER_API_KEY"):
        for r in classify_sync(same_day, adr_by): kinds[(r["date"], r["sym"], pd.Timestamp(r["t_in"]))] = r
    batch = f"batch_{until.isoformat()}"; n_new = 0

    # ---- stock cycles
    for c in cyc[cyc.asset_category == "STK"].itertuples():
        label = f"{c.underlying_symbol} ({'long' if c.first_side == 'LONG' else 'short'} {int(abs(c.max_abs_qty))} @{c.entry_price:.2f})"
        if (c.underlying_symbol, c.entry_date, label) in have: continue
        g = grades[(grades.underlying_symbol == c.underlying_symbol) & (grades.trade_date == c.entry_date) & (grades.side == ("long" if c.first_side == "LONG" else "short"))]
        g = g.sort_values("t_fill").iloc[0] if len(g) else None
        tags = [batch, "rubric_graded"]; ev, er = "gray_area", "no rubric grade found for this fill"
        if g is not None:
            ev = VERDICT.get(g.setup_grade, "gray_area"); er = f"RUBRIC {g.rubric}: setup grade {g.setup_grade} -- {g.grade_why}."
            tags.append(f"setup_{g.setup_grade}")
            if isinstance(g.alert_kind, str) and g.alert_kind:
                er += f" Alert {g.alert_kind} {g.alert_t} @{g.alert_px}: filled {g.slip_adr:+.2f} ADR vs the alert, {g.delay_min:.0f} min after it ({'ok' if g.exec_ok == 1 else 'late/slipped'})."; tags.append("alert_taken")
            else: er += " No same-side alert in the 30 min before the fill."; tags.append("no_alert")
        xv, xr = "n_a", None
        if c.still_open: tags.append("open_position")
        elif c.exit_date == c.entry_date:
            tags.append("same_day_round_trip"); k = None
            for key, r in kinds.items():
                if key[0] == c.entry_date and key[1] == c.underlying_symbol: k = r; break
            xv, xr = EXIT[(k or {}).get("kind", "UNKNOWN")]
            if k and "pnl_pct" in k: xr += f" P&L {k['pnl_pct']:+.2f}%, MFE {k['mfe_pct']:+.2f}%."
            tags.append(f"exit_{(k or {}).get('kind', 'UNKNOWN').lower()}")
        else: xv, xr = "gray_area", f"closed {c.exit_date} after a multi-day hold; exit not yet reviewed"; tags.append("needs_exit_review")
        if not a.dry_run:
            add_trade_review(c.underlying_symbol, label, c.entry_date, None if c.still_open else c.exit_date, conid=int(c.conid), asset_category="STK",
                             entry_verdict=ev, entry_reason=er, exit_verdict=xv, exit_reason=xr, tags=",".join(tags), realized_pnl=None if c.still_open else c.realized_pnl)
        n_new += 1

    # ---- option campaigns (one review per structure)
    screen_dir = Path("data/watchlist/straddle_screen")
    for cp in camps.itertuples():
        legs = ctr[ctr.campaign_id == cp.campaign_id]; d0 = pd.to_datetime(cp.first_date).date()
        label = f"{cp.underlying} ({cp.label})"[:48]
        if (cp.underlying, d0, label) in have: continue
        opening = legs[pd.to_datetime(legs.trade_datetime).dt.date == d0]
        systematic = opening["trade_datetime"].nunique() < opening["symbol"].nunique()      # 2+ legs on one timestamp
        tags = [batch, "option_structure", "systematic_spread_likely" if systematic else "single_leg_or_legged_in"]
        if "straddle" in str(cp.label).lower():
            f = screen_dir / f"straddle_screen_{d0.isoformat()}.csv"
            if f.exists():
                sc = pd.read_csv(f); hit = sc[(sc.tkr == cp.underlying)]
                tags.append("screen_pick" if len(hit) and bool(hit.iloc[0].get("pass_all", False)) else "not_on_screen")
        still_open = str(cp.status).lower() != "closed"
        if still_open: tags.append("open_position")
        er = f"Option structure: {cp.label}; {int(cp.n_fills)} fills, {int(cp.n_rolls)} roll(s), net premium {cp.net_premium:+.2f}. " + \
             ("Legs filled on one timestamp -- systematic signature." if systematic else "Legs filled at different times.")
        if not a.dry_run:
            add_trade_review(cp.underlying, label, d0, None if still_open else pd.to_datetime(cp.last_date).date(), asset_category="OPT",
                             entry_verdict="gray_area", entry_reason=er, exit_verdict="n_a" if still_open else "gray_area",
                             exit_reason=None if still_open else "structure closed; exit not yet reviewed against its playbook", tags=",".join(tags),
                             realized_pnl=None if still_open else cp.realized_pnl)
        n_new += 1
    print(f"reviews written: {n_new}  ({'dry run' if a.dry_run else 'persisted'})")
    if not a.dry_run:
        print("notes attached:", apply_pending_notes()); print("campaign sync:", sync_review_campaigns()); print("tags synced:", sync_review_tags())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

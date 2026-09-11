#!/usr/bin/env python3
"""Process report card, one grade per session, from the journal tables.

Graded on PROCESS, not P&L (Breitstein's 'daily report card' / four-constraints frame,
data/lance_breitstein/notes/four-constraints-and-the-ai-trap.md). Every input is computed
from journal_trades + journal_trade_reviews, so the grade is reproducible and cannot be
argued with after the fact. NAV P&L is shown alongside for context only.

Five components, 100 points, each tied to a rule already on the plan sheet:
  entry quality   30  from journal_entry_grades (lib/journal/entry_grades.py), i.e. the SAME setup rubric the
                      alert monitor uses (lib/alerts/grading.py):
                        setup 20      share of stock entries graded A/B: >=75% -> 20, 50-75% -> 10, else 0
                        execution 10  share of alert-following entries filled <=0.25 ADR worse and <=10 min
                                      after the alert: >=75% -> 10, 50-75% -> 5, else 0 (no alert entries -> 10)
                      Sessions before the alert logs (pre-8/13) fall back to the old prose review verdicts.
  same-day trips  25  stock same-day round trips that were NOT true invalidations (exit at the trade's
                      worst price after a pre-entry level broke = INVALIDATION, not penalized; see
                      lib/journal/exit_kind.py): <=3 full, 4-6 -> 15, 7-10 -> 5, >10 -> 0.
                      Sessions older than Tradier's 1-min retention fall back to the raw count.
  activity        15  fills: <=50 full, 51-80 -> 8, >80 -> 0
  exits           15  exits reviewed 'too_soon': 0 full, 1 -> 10, 2 -> 5, >=3 -> 0
  vehicles        15  stock + option opened same day on one underlying: 0 full, 1-2 -> 8, >=3 -> 0
Grade: A >= 85, B >= 70, C >= 55, else D.

  MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_journal_grades.py [--since YYYY-MM-DD]
Writes data/studies/journal_process_grades.md + data/watchlist/logs/journal_process_grades.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from lib.mysql_lib import _get_conn
from lib.journal.exit_kind import cycles_from_fills, classify_sync
from lib.journal.entry_grades import ALERT_LOGS_START, drop_execution_errors, rebuild as rebuild_entry_grades

SYSTEMATIC = "straddle_screener|systematic_spread_likely|playbook_verified|playbook_deviation|^systematic$|,systematic,|,systematic$"
OUT_MD = Path("data/studies/journal_process_grades.md")
OUT_CSV = Path("data/watchlist/logs/journal_process_grades.csv")




def grade(score: float) -> str:
    return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--since", default=None)
    ap.add_argument("--no-entry-rebuild", action="store_true", help="use journal_entry_grades as stored")
    a = ap.parse_args()
    if not a.no_entry_rebuild:
        print("grading stock entries with the shared setup rubric ...", flush=True)
        rebuild_entry_grades(a.since)
    conn = _get_conn()
    t = pd.read_sql("SELECT trade_date, conid, underlying_symbol, asset_category, open_close, realized_pnl, trade_datetime, buy_sell, quantity, trade_price FROM journal_trades", conn)
    nav = pd.read_sql("SELECT report_date, nav, day_pnl FROM journal_nav", conn)
    rv = pd.read_sql("SELECT underlying_symbol, symbol, entry_date, exit_date, entry_verdict, exit_verdict, tags, realized_pnl FROM journal_trade_reviews", conn)
    eg = pd.read_sql("SELECT trade_date, setup_grade, alert_kind, exec_ok FROM journal_entry_grades", conn)
    eg["trade_date"] = pd.to_datetime(eg["trade_date"]).dt.date
    conn.close()
    t["trade_date"] = pd.to_datetime(t["trade_date"]).dt.date
    t = drop_execution_errors(t)
    rv["entry_date"] = pd.to_datetime(rv["entry_date"]).dt.date
    nav["date"] = pd.to_datetime(nav["report_date"]).dt.date
    sysmask = rv.tags.fillna("").str.contains(SYSTEMATIC, regex=True) | rv.symbol.str.contains("multi-leg|straddle|condor|spread", case=False)
    # exit-kind classification for same-day stock cycles (needs 1-min bars; ~20 sessions back)
    stk = t[t.asset_category == "STK"]
    cyc = cycles_from_fills(stk)
    adr_by = {}
    if cyc:
        try:
            from lib.alerts.context import load_context
            import asyncio as _a
            syms = sorted({c["sym"] for c in cyc})
            ctx = _a.run(load_context(syms, max(t.trade_date) if hasattr(max(t.trade_date), "year") else date.today()))
            adr_by = {s_: k.adr_pct for s_, k in ctx.items()}
        except Exception as exc:  # noqa: BLE001
            print(f"  (adr context unavailable: {exc.__class__.__name__}; using 3% default)")
        kinds = classify_sync(cyc, adr_by)
    else:
        kinds = []
    kind_df = pd.DataFrame(kinds) if kinds else pd.DataFrame(columns=["date", "sym", "kind"])
    if len(kind_df):
        kind_df["date"] = pd.to_datetime(kind_df["date"]).dt.date
    rows = []
    for d in sorted(t.trade_date.unique()):
        if a.since and str(d) < a.since:
            continue
        x = t[t.trade_date == d]
        opens = x[x.open_close.isin(["O", "C;O"])]; closes = x[x.open_close.isin(["C", "C;O"])]
        rt = set(opens.conid) & set(closes.conid)
        stk_rt = x[(x.conid.isin(rt)) & (x.asset_category == "STK")].underlying_symbol.nunique()
        doubled = int((opens.groupby("underlying_symbol").asset_category.nunique() > 1).sum())
        r = rv[rv.entry_date == d]; disc = r[~sysmask.loc[r.index]]
        good, bad, gray = int((disc.entry_verdict == "good").sum()), int((disc.entry_verdict == "bad").sum()), int(disc.entry_verdict.isin(["gray_area", "gray"]).sum())
        too_soon = int((r.exit_verdict == "too_soon").sum())
        n_disc = good + bad + gray
        pg = good / n_disc if n_disc else None
        e = eg[eg.trade_date == d]
        if str(d) >= ALERT_LOGS_START and len(e):
            ab = int(e.setup_grade.isin(["A", "B"]).sum()); share = ab / len(e)
            s_setup = 20 if share >= 0.75 else 10 if share >= 0.50 else 0
            mt = e[e.alert_kind.notna()]; ok = int((mt.exec_ok == 1).sum())
            s_exec = 10 if not len(mt) else (10 if ok / len(mt) >= 0.75 else 5 if ok / len(mt) >= 0.50 else 0)
            s_entry, entry_src = s_setup + s_exec, "rubric"
            gc = e.setup_grade.value_counts()
            abcf = "/".join(str(int(gc.get(k, 0))) for k in "ABCF"); exec_s = f"{ok}/{len(mt)}"
        else:
            s_entry = 30 if pg is None else (30 if pg >= 0.75 else 15 if pg >= 0.50 else 0)
            entry_src, abcf, exec_s = "prose", "", ""
        kd = kind_df[kind_df["date"] == d] if len(kind_df) else kind_df
        n_inval = int((kd["kind"] == "INVALIDATION").sum()) if len(kd) else 0
        n_noise = int((kd["kind"] == "NOISE_STOP").sum()) if len(kd) else 0
        n_disc = int((kd["kind"] == "DISCRETIONARY").sum()) if len(kd) else 0
        classified = len(kd) and (kd["kind"] != "UNKNOWN").any()
        rt_pen = (n_noise + n_disc) if classified else stk_rt        # penalize only non-invalidation exits when bars exist
        s_rt = 25 if rt_pen <= 3 else 15 if rt_pen <= 6 else 5 if rt_pen <= 10 else 0
        s_act = 15 if len(x) <= 50 else 8 if len(x) <= 80 else 0
        s_exit = 15 if too_soon == 0 else 10 if too_soon == 1 else 5 if too_soon == 2 else 0
        s_veh = 15 if doubled == 0 else 8 if doubled <= 2 else 0
        score = s_entry + s_rt + s_act + s_exit + s_veh
        pnl = nav.loc[nav.date == d, "day_pnl"]
        rows.append(dict(date=d, fills=len(x), symbols=x.underlying_symbol.nunique(), stock_round_trips=stk_rt,
                         rt_invalidation=n_inval, rt_noise_stop=n_noise, rt_discretionary=n_disc, doubled=doubled,
                         disc_entries=good + bad + gray, disc_good=good, disc_bad=bad, too_soon=too_soon,
                         pct_good=round(100 * good / (good + bad + gray), 0) if (good + bad + gray) else None,
                         entry_src=entry_src, entries_ABCF=abcf, exec_ok_of_alert=exec_s, s_entry=s_entry,
                         score=int(score), grade=grade(score), nav_pnl=round(float(pnl.iloc[0]), 0) if len(pnl) else None))
    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True); df.to_csv(OUT_CSV, index=False)
    pd.set_option("display.width", 220); print(df.to_string(index=False))
    g = df.groupby("grade").agg(days=("date", "count"), avg_pnl=("nav_pnl", "mean"), avg_fills=("fills", "mean"), avg_rt=("stock_round_trips", "mean")).round(0)
    print("\nby grade:"); print(g.to_string())
    corr = df[["score", "nav_pnl"]].dropna().corr().iloc[0, 1]
    print(f"\ncorrelation(score, NAV day P&L) = {corr:+.2f} over {df.nav_pnl.notna().sum()} days")
    # markdown
    lines = ["# Journal process grades", "", f"*Generated by `run_journal_grades.py` from `journal_trades` + `journal_trade_reviews`; {len(df)} sessions. "
             "Graded on process, not P&L; NAV P&L shown for context. Rubric in the script docstring. Entry grades use the same setup rubric as the alert monitor (`src/lib/alerts/grading.py`).*", "",
             "| date | grade | score | entry pts | stock entries A/B/C/F (rubric) | exec ok / alert entries | fills | stock round trips (invalidation / noise-stop / discretionary) | doubled | too-soon exits | NAV P&L |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        ent = r.entries_ABCF if r.entry_src == "rubric" else f"prose {r.disc_good}/{r.disc_bad} of {r.disc_entries}"
        lines.append(f"| {r.date} | **{r.grade}** | {r.score} | {r.s_entry}/30 | {ent} | {r.exec_ok_of_alert} | {r.fills} | {r.stock_round_trips} ({r.rt_invalidation} / {r.rt_noise_stop} / {r.rt_discretionary}) | {r.doubled} | {r.too_soon} | {'' if pd.isna(r.nav_pnl) else f'{r.nav_pnl:+,.0f}'} |")
    lines += ["", "## By grade", "", "| grade | days | avg NAV P&L | avg fills | avg stock round trips |", "|---|---|---|---|---|"]
    for gr, r in g.iterrows():
        lines.append(f"| {gr} | {int(r.days)} | {r.avg_pnl:+,.0f} | {r.avg_fills:.0f} | {r.avg_rt:.0f} |")
    lines += ["", f"Correlation between the process score and NAV day P&L: **{corr:+.2f}** over {df.nav_pnl.notna().sum()} days.", ""]
    OUT_MD.write_text("\n".join(lines))
    print(f"\nwrote {OUT_MD} and {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Gabe's own stock trades since the alert logs start: same-day round trips vs held overnight,
split by whether an ALERT triggered the entry.

Question (2026-09-18): our book says "no same-day exits unless the stop is hit" (August: 132 round trips,
-$7.9k), while Tito's log is mostly intraday. Is the same-day exit itself the problem, or is it that our
same-day trades are unplanned?

Method: flat-to-flat cycles from journal_trades (lib.mysql_lib.reconstruct_trade_cycles), stock only, closed
cycles, entry date >= the first session with alert logs (lib.journal.entry_grades.ALERT_LOGS_START). Each
cycle's entry is matched to that day's alert log with the same matcher the journal uses
(entry_grades.grade_day -> alert_kind / setup_grade), so "alert-triggered" means the engine had fired that
symbol, that side, within the match window before the fill.

Reports expectancy per cycle in dollars (realized P&L) and as R where the alert gave a stop.

Usage:
  MYSQL_PASSWORD=... AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_roundtrip_split_study.py
"""
from __future__ import annotations

import warnings
from datetime import date

import pandas as pd

from lib.journal.entry_grades import ALERT_LOGS_START, drop_execution_errors, grade_day
from lib.mysql_lib import _get_engine, reconstruct_trade_cycles

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)


def main() -> None:
    cyc = reconstruct_trade_cycles()
    cyc = cyc[(cyc.asset_category == "STK") & (~cyc.still_open)].copy()
    cyc["entry_date"] = pd.to_datetime(cyc.entry_date)
    cyc["exit_date"] = pd.to_datetime(cyc.exit_date)
    cyc = cyc[cyc.entry_date >= ALERT_LOGS_START]
    cyc["same_day"] = cyc.entry_date == cyc.exit_date
    cyc["held_days"] = (cyc.exit_date - cyc.entry_date).dt.days

    trades = pd.read_sql("SELECT * FROM journal_trades WHERE trade_date >= %s",
                         _get_engine(), params=(ALERT_LOGS_START,))
    trades["trade_date"] = pd.to_datetime(trades.trade_date)
    trades = drop_execution_errors(trades)

    grades = []
    for d, t_day in trades.groupby(trades.trade_date.dt.date):
        try:
            g = grade_day(d, t_day)
        except Exception as exc:                                   # noqa: BLE001 — one bad session must not kill the run
            print(f"  ({d}: grade_day failed, {type(exc).__name__})")
            continue
        if len(g):
            grades.append(g)
    G = pd.concat(grades, ignore_index=True)
    G["entry_date"] = pd.to_datetime(G.trade_date)
    first = (G.sort_values("t_fill").groupby(["underlying_symbol", "entry_date"])
             .agg(alert_kind=("alert_kind", "first"), setup_grade=("setup_grade", "first"),
                  day_state=("day_state", "first"), side=("side", "first")).reset_index())

    m = cyc.merge(first, left_on=["underlying_symbol", "entry_date"],
                  right_on=["underlying_symbol", "entry_date"], how="left")
    m["alerted"] = m.alert_kind.notna()
    m["planned"] = m.alerted & m.setup_grade.isin(["A", "B"])
    print(f"closed stock cycles since {ALERT_LOGS_START}: {len(m)} "
          f"({m.entry_date.min().date()} -> {m.exit_date.max().date()}), "
          f"{m.same_day.sum()} same-day / {(~m.same_day).sum()} held overnight\n")

    def tab(x):
        return dict(n=len(x), total=x.realized_pnl.sum(), mean=x.realized_pnl.mean(),
                    median=x.realized_pnl.median(), win=100 * (x.realized_pnl > 0).mean(),
                    best=x.realized_pnl.max(), worst=x.realized_pnl.min())

    print("=== same-day round trips vs held overnight ===")
    print(pd.DataFrame({("same day" if k else "held overnight"): tab(v)
                        for k, v in m.groupby("same_day")}).T.round(0).to_string())

    print("\n=== split by whether an alert fired the entry ===")
    rows = {}
    for sd, lab in ((True, "same day"), (False, "overnight")):
        for al, lab2 in ((True, "alert"), (False, "no alert")):
            x = m[(m.same_day == sd) & (m.alerted == al)]
            if len(x):
                rows[f"{lab}, {lab2}"] = tab(x)
    print(pd.DataFrame(rows).T.round(0).to_string())

    print("\n=== alert-triggered entries only, by grade ===")
    a = m[m.alerted]
    rows = {}
    for (sd, g), x in a.groupby(["same_day", "setup_grade"]):
        rows[f"{'same day' if sd else 'overnight'}, grade {g}"] = tab(x)
    print(pd.DataFrame(rows).T.round(0).to_string())

    print("\n=== holding period of closed cycles ===")
    b = pd.cut(m.held_days, [-1, 0, 1, 3, 7, 1000], labels=["same day", "1 day", "2-3 d", "4-7 d", "8+ d"])
    print(m.groupby(b, observed=True).apply(lambda x: pd.Series(tab(x))).round(0).to_string())
    m.to_csv("data/studies/roundtrip_split_2026-09-18.csv", index=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Alert study: replay sessions (optional), score every alert, print the gate/filter reports.

  PYTHONPATH=src .venv/bin/python3 run_alert_study.py                      # all replay logs on file
  PYTHONPATH=src .venv/bin/python3 run_alert_study.py --since 2026-08-13 --report daystate
  PYTHONPATH=src .venv/bin/python3 run_alert_study.py --replay 2026-09-11 2026-09-18   # replay, then report
  ... --live            # study the LIVE logs instead of replays
  ... --shown-only      # drop out-of-play alerts (what the monitor actually showed)
  ... --rescore         # re-score everything (scores are cached in logs/alert_study_scores*.csv)

Replays run the CURRENT detector code over the universe (universe_latest.txt + universe_short.txt)
and overwrite that date's replay logs. Tradier keeps ~20 sessions of 1-min bars, so replays only
reach back about a month; scores and bars are cached so older sessions stay studyable.
Harness logic: src/lib/alerts/study.py. Write-ups: data/studies/alert_filter_study_2026-09.md.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from lib.alerts import study

REPO = Path(__file__).resolve().parent


def replay(start: str, end: str) -> None:
    wl = REPO / "data" / "watchlist"
    syms = sorted({s.strip().upper() for f in ("universe_latest.txt", "universe_short.txt") if (wl / f).exists()
                   for s in (wl / f).read_text().splitlines() if s.strip() and not s.startswith("#")})
    d, e = date.fromisoformat(start), date.fromisoformat(end)
    while d <= e:
        if d.weekday() < 5:
            r = subprocess.run([sys.executable, "run_universe_monitor.py", *syms, "--replay", d.isoformat(), "--index-gate"],
                               cwd=REPO, capture_output=True, text=True)
            last = [l for l in r.stdout.splitlines() if l.startswith("replay:")]
            print(f"{d}: rc={r.returncode} {last[0] if last else ''}", flush=True)
        d += timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replay", nargs=2, metavar=("START", "END"), help="replay these sessions first (current code)")
    ap.add_argument("--since", default=None); ap.add_argument("--until", default=None)
    ap.add_argument("--live", action="store_true", help="study the live logs, not the replays")
    ap.add_argument("--shown-only", action="store_true", help="exclude out-of-play alerts")
    ap.add_argument("--report", default="filters,extension,daystate,grades")
    ap.add_argument("--rescore", action="store_true")
    ap.add_argument("--no-day-state", action="store_true", help="skip the daily-state join (no context loads)")
    a = ap.parse_args()
    if a.replay:
        replay(*a.replay)
        a.since, a.until = a.since or a.replay[0], a.until or a.replay[1]
    paths = study.log_paths(a.since, a.until, replay=not a.live)
    df = study.parse_logs(paths)
    if a.shown_only:
        df = df[~df.out_of_play]
    if df.empty:
        print("no alerts in those logs"); return 1
    cache = study.LOGS / f"alert_study_scores{'_live' if a.live else ''}.csv"
    S = study.enrich(study.score_with_cache(df, cache, a.rescore), day_state=not a.no_day_state)
    pd.set_option("display.width", 230)
    days = sorted(S.date.unique())
    print(f"{len(S)} scored alerts, {len(days)} sessions {days[0]} .. {days[-1]} | half A = first {len(days) // 2} sessions"
          f" | {int(S.out_of_play.sum())} out of play | {'live' if a.live else 'replay'} logs")
    reps = {"filters": study.report_filters, "extension": study.report_extension, "daystate": study.report_daystate,
            "grades": study.report_grades}
    for r in a.report.split(","):
        reps[r.strip()](S)
    return 0


if __name__ == "__main__":
    sys.exit(main())

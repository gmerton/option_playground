"""
Upcoming US economic events for position monitoring.

CPI dates are sourced from the official BLS release schedule:
  https://www.bls.gov/schedule/news_release/cpi.htm
  -> update data/bls_cpi_schedule.json each January.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

_BLS_SCHEDULE = Path(__file__).parent.parent.parent / "data" / "bls_cpi_schedule.json"


def _load_cpi_dates() -> list[dict]:
    return json.loads(_BLS_SCHEDULE.read_text())["cpi_releases"]


def get_upcoming_events(lookahead_days: int = 7) -> list[dict]:
    """
    Return upcoming CPI release dates within the next `lookahead_days`.
    Each item: {date, period, label, days_away}
    """
    today = date.today()
    cutoff = today + timedelta(days=lookahead_days)
    events = []
    for entry in _load_cpi_dates():
        d = date.fromisoformat(entry["date"])
        if today <= d <= cutoff:
            events.append({
                "date": d,
                "period": entry["period"],
                "label": "CPI",
                "days_away": (d - today).days,
            })
    return sorted(events, key=lambda e: e["date"])


def print_upcoming_events(lookahead_days: int = 7) -> None:
    """Print a warning banner if a CPI release falls within lookahead_days."""
    events = get_upcoming_events(lookahead_days=lookahead_days)
    if events:
        print("  ⚠️  UPCOMING ECONOMIC EVENTS (next 7 days):")
        for ev in events:
            days_away = ev["days_away"]
            when = "TODAY" if days_away == 0 else ("TOMORROW" if days_away == 1 else f"in {days_away} days")
            print(f"     📅  CPI ({ev['period']})  —  {ev['date']}  ({when})")
        print()

    # Warn when the schedule is about to run out
    all_dates = sorted(date.fromisoformat(e["date"]) for e in _load_cpi_dates())
    last_date = all_dates[-1]
    days_until_last = (last_date - date.today()).days
    if days_until_last <= 30:
        print(f"  🗓️  REMINDER: BLS CPI schedule expires on {last_date} ({days_until_last} days away).")
        print(f"     Update data/bls_cpi_schedule.json with next year's dates from:")
        print(f"     https://www.bls.gov/schedule/news_release/cpi.htm")
        print()

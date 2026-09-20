"""Forward earnings dates: a single rolling snapshot at `data/news/earnings.json`.

Not a per-day file like the news store, because the provider gives a two-point snapshot per symbol
(last release + next), not a series -- so there is nothing to archive per session, only a current
view that a later pull refreshes. `stale_days` exists because a snapshot that was right in August
is wrong once the print has happened, and a silently stale "next" date is worse than no date.

What this is for: the forward question every live screen actually asks -- is there a print between
here and the exit? That covers `run_adhikary_scan.py`'s no-catalyst-gap filter and the double
calendar placement rule (prefer earnings BETWEEN the expiries, tastylive 2026-09-15).

    from lib.news import earnings
    earnings.days_until("SNDK", date(2026, 9, 20))       # -> 10
    earnings.reports_between("SNDK", front_expiry, back_expiry)
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from lib.news.tradingview import EarningsRow

REPO = Path(__file__).resolve().parents[3]
PATH = REPO / "data" / "news" / "earnings.json"
SCHEMA = 1


def save(rows: list[EarningsRow], *, source: str) -> Path:
    """Merge `rows` into the snapshot, keyed by ticker. A later pull overwrites a ticker outright --
    unlike news there is no partial row to preserve."""
    PATH.parent.mkdir(parents=True, exist_ok=True)
    cur = json.loads(PATH.read_text()).get("rows", {}) if PATH.exists() else {}
    now = datetime.now().isoformat(timespec="seconds")
    for r in rows:
        cur[r.ticker] = {**asdict(r), "pulled_at": now}
    PATH.write_text(json.dumps({
        "schema": SCHEMA, "source": source, "pulled_at": now,
        "rows": dict(sorted(cur.items())),
    }, indent=1))
    return PATH


def load() -> dict[str, dict]:
    return json.loads(PATH.read_text()).get("rows", {}) if PATH.exists() else {}


def next_release(ticker: str) -> date | None:
    r = load().get(ticker.upper())
    if not r or not r.get("next_release"):
        return None
    try:
        return date.fromisoformat(r["next_release"])
    except ValueError:
        return None


def days_until(ticker: str, d: date) -> int | None:
    """Sessions-agnostic calendar days to the next print. Negative means the snapshot is stale --
    the date it holds has already passed and needs re-pulling."""
    nxt = next_release(ticker)
    return (nxt - d).days if nxt else None


def reports_between(ticker: str, start: date, end: date) -> bool | None:
    """True/False when a forward date is known, None when it is not. None is NOT False: a caller
    gating on 'no earnings in the window' must treat the unknown case explicitly."""
    nxt = next_release(ticker)
    return None if nxt is None else (start <= nxt <= end)


def stale(ticker: str, d: date) -> bool:
    """The cached next-release date is in the past, so this ticker needs a fresh pull."""
    n = days_until(ticker, d)
    return n is not None and n < 0


def stale_tickers(d: date) -> list[str]:
    return sorted(t for t in load() if stale(t, d))

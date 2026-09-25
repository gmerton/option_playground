"""Assemble the live-alert universe with no hand entry.

Sources (all optional except the preferred list):
  data/preferred_tickers.txt                Trend-Template passers + manual overlay (S3-owned, pulled by the desk)
  open stock positions                      journal_open_positions, newest snapshot (needs MYSQL_PASSWORD)
  data/watchlist/trade_plan_<latest>.md     first column of every markdown table -- only if <= 7 days old
  data/watchlist/alerts_latest.csv          Adhikary scan buy-stop rows
  data/watchlist/monitor_latest.json        breakout-monitor roster
  data/ariel_hernandez/analysis/<latest>_watchlist_scored.md   creator watchlist -- only if <= 7 days old
  data/watchlist/universe_extra.txt         free-form adds (one ticker per line, # comments)
  data/watchlist/universe_exclude.txt       tickers to drop

Writes data/watchlist/universe_latest.txt and returns the sorted list.

2026-09-24: the hand-edited universe_focus.txt was retired. When it existed the monitor streamed ONLY it (+ the
plan), so the evening scans never reached the next session (it was last edited 9/14, the plan 9/09). The universe is
now always the union above; the hand levers are universe_extra.txt (add) and universe_exclude.txt (drop).
"""
from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WL = REPO / "data" / "watchlist"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,5}$")


def _read_lines(p: Path) -> set[str]:
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        t = line.split("#", 1)[0].strip().upper()
        if t and TICKER_RE.match(t):
            out.add(t)
    return out


MAX_AGE_DAYS = 7          # hand-made plans / creator scorecards older than this are stale, not a watchlist


def _fresh(p: Path | None) -> Path | None:
    """p if the YYYY-MM-DD in its name is within MAX_AGE_DAYS, else None."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name) if p else None
    if not m:
        return None
    age = (date.today() - datetime.strptime(m.group(1), "%Y-%m-%d").date()).days
    return p if age <= MAX_AGE_DAYS else None


def latest_plan() -> Path | None:
    plans = sorted(WL.glob("trade_plan_*.md"))
    return _fresh(plans[-1]) if plans else None


def holding_tickers() -> set[str]:
    """Stock positions in the newest journal_open_positions snapshot. Empty if MySQL is unreachable."""
    try:
        from lib.mysql_lib import _get_conn
        conn = _get_conn()          # keep a reference: the cursor only holds a weak one to its connection
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT symbol FROM journal_open_positions WHERE asset_category = 'STK' AND "
                    "report_date = (SELECT MAX(report_date) FROM journal_open_positions)")
        out = {r[0].upper() for r in cur.fetchall() if r[0] and TICKER_RE.match(r[0].upper())}
        conn.close()
        return out
    except Exception:  # noqa: BLE001 -- no DB (e.g. no MYSQL_PASSWORD) must not stop the monitor
        return set()


def plan_tickers(p: Path | None) -> set[str]:
    """First cell of every markdown table row, minus header/separator rows.
    Cells like 'GLW (add only)' contribute the leading token."""
    if p is None or not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        if line.startswith("|"):
            cell = line.split("|")[1].strip()
            tok = cell.split()[0].strip("*`") if cell else ""
        elif line.lstrip().startswith("- **"):        # position/management bullets: "- **DINO** long ..."
            tok = line.lstrip()[4:].split("*")[0].split()[0] if line.lstrip()[4:].strip() else ""
        else:
            continue
        if tok and tok.lower() not in ("name", "---", "ticker") and TICKER_RE.match(tok):
            out.add(tok)
    return out


def scan_tickers() -> set[str]:
    p = WL / "alerts_latest.csv"
    if not p.exists():
        return set()
    with p.open() as fh:
        return {r["ticker"].strip().upper() for r in csv.DictReader(fh) if r.get("ticker")}


def monitor_tickers() -> set[str]:
    p = WL / "monitor_latest.json"
    if not p.exists():
        return set()
    try:
        d = json.loads(p.read_text())
    except json.JSONDecodeError:
        return set()
    return {k.upper() for k in (d.keys() if isinstance(d, dict) else [])}


def creator_tickers() -> set[str]:
    """Tickers from the newest Ariel watchlist scorecard (first column of its tables)."""
    scored = sorted((REPO / "data" / "ariel_hernandez" / "analysis").glob("*_watchlist_scored.md"))
    return plan_tickers(_fresh(scored[-1])) if scored else set()


def build_universe(write: bool = True, full: bool = False) -> tuple[list[str], dict[str, set[str]]]:
    """Union of every source minus universe_exclude.txt. `full` is accepted for backward compatibility and ignored
    (it used to switch from the retired universe_focus.txt to this union)."""
    exclude = _read_lines(WL / "universe_exclude.txt")
    parts = {
        "preferred": _read_lines(REPO / "data" / "preferred_tickers.txt"),
        "holdings": holding_tickers(),
        "plan": plan_tickers(latest_plan()),
        "scan": scan_tickers(),
        "monitor": monitor_tickers(),
        "creator": creator_tickers(),
        "extra": _read_lines(WL / "universe_extra.txt"),
    }
    uni = sorted(set().union(*parts.values()) - exclude)
    if write:
        (WL / "universe_latest.txt").write_text("\n".join(uni) + "\n")
    return uni, parts

if __name__ == "__main__":
    import sys
    u, parts = build_universe(full="--full" in sys.argv)
    for k, v in parts.items():
        print(f"{k:10s} {len(v):4d}")
    print(f"{'universe':10s} {len(u):4d} -> data/watchlist/universe_latest.txt")

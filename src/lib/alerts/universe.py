"""Assemble the live-alert universe with no hand entry.

Sources (all optional except the preferred list):
  data/preferred_tickers.txt                Trend-Template passers + manual overlay
  data/watchlist/trade_plan_<latest>.md     first column of every markdown table
  data/watchlist/alerts_latest.csv          Adhikary scan buy-stop rows
  data/watchlist/monitor_latest.json        breakout-monitor roster
  data/watchlist/universe_extra.txt         free-form adds (one ticker per line, # comments)
  data/watchlist/universe_exclude.txt       tickers to drop

Writes data/watchlist/universe_latest.txt and returns the sorted list.
"""
from __future__ import annotations

import csv
import json
import re
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


def latest_plan() -> Path | None:
    plans = sorted(WL.glob("trade_plan_*.md"))
    return plans[-1] if plans else None


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
    return plan_tickers(scored[-1]) if scored else set()


def build_universe(write: bool = True, full: bool = False) -> tuple[list[str], dict[str, set[str]]]:
    """Default: the curated focus file (if present) + the current plan's table names.
    full=True (or no focus file): union of every source."""
    focus = _read_lines(WL / "universe_focus.txt")
    exclude = _read_lines(WL / "universe_exclude.txt")
    if focus and not full:
        parts = {"focus": focus, "plan": plan_tickers(latest_plan())}
        uni = sorted(set().union(*parts.values()) - exclude)
        if write:
            (WL / "universe_latest.txt").write_text("\n".join(uni) + "\n")
        return uni, parts
    parts = {
        "preferred": _read_lines(REPO / "data" / "preferred_tickers.txt"),
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

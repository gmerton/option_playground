#!/usr/bin/env python3
"""
Merge TradingView MCP payloads into the news + earnings stores.

This script does NOT fetch anything: the MCP server is callable by Claude, not by Python. The
division of labour is therefore:

  1. `--plan`   this script prints exactly which MCP calls to make (resolved EXCHANGE:TICKER
                symbols for news, the batched symbol list for earnings, and any ticker whose
                exchange prefix is not cached yet).
  2.            Claude makes those calls and writes the raw responses to a payload JSON.
  3. `--load`   this script transforms and merges them into data/news/<date>.json (news) and
                data/news/earnings.json (forward earnings snapshot).

Cost asymmetry worth knowing before you plan a pull: earnings takes a LIST of symbols, so the whole
universe is a couple of calls; news is one call per symbol. Pull earnings wide and news narrow --
the trade-plan names and whatever actually moved.

Payload file schema (every key optional except the ones you use):

    {
      "date": "2026-09-18",
      "universe": ["AAPL", "NVDA"],          # every ticker the pull ASKED for, incl. empty results
      "resolve":  {"AAPL": <search-symbols payload>},
      "news":     {"AAPL": <get-news payload>},
      "stories":  [{"url": "<headline link>", "story": "<full body>"}],
      "earnings": [<get-earnings-calendar payload>, ...]
    }

Run (from the repo root):
    PYTHONPATH=src .venv/bin/python3 run_news_pull.py --plan
    PYTHONPATH=src .venv/bin/python3 run_news_pull.py --plan --tickers SNDK,CF,NVDA
    PYTHONPATH=src .venv/bin/python3 run_news_pull.py --load /tmp/payloads.json
    PYTHONPATH=src .venv/bin/python3 run_news_pull.py --show SNDK

Requires: nothing at run time -- no API key, no network. The MCP session is Claude's.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from lib.news import earnings as earn
from lib.news import store, tradingview as tv

REPO = Path(__file__).resolve().parent
DEFAULT_UNIVERSE = REPO / "data" / "watchlist" / "universe_latest.txt"


def _read_universe(p: Path) -> list[str]:
    out = []
    for line in p.read_text().splitlines() if p.exists() else []:
        t = line.split("#", 1)[0].strip().upper()
        if t:
            out.append(t)
    return sorted(set(out))


def cmd_plan(tickers: list[str], d: date) -> int:
    m = tv.load_symbol_map()
    missing = tv.unresolved(tickers, m)
    known = [t for t in tickers if t in m]

    print(f"# news pull plan for {d.isoformat()}  ({len(tickers)} tickers)\n")
    if missing:
        print(f"## 1. resolve {len(missing)} unknown exchange prefix(es) -- search-symbols, then "
              f"put each response under \"resolve\" in the payload file:")
        print("   " + " ".join(missing) + "\n")
    else:
        print("## 1. resolve: nothing -- every ticker has a cached exchange prefix\n")

    print(f"## 2. earnings -- ONE batched get-earnings-calendar call per chunk of symbols:")
    syms = [m[t] for t in known]
    for i in range(0, len(syms), 40):
        print("   " + json.dumps(syms[i:i + 40]))
    if not syms:
        print("   (nothing resolved yet)")

    print(f"\n## 3. news -- one get-news call PER symbol ({len(syms)}); narrow this list by hand "
          f"to the names that matter today:")
    for s in syms:
        print("   " + s)

    stale = earn.stale_tickers(d)
    if stale:
        print(f"\n## note: {len(stale)} cached earnings date(s) are in the past and need a re-pull: "
              + " ".join(stale[:20]) + (" ..." if len(stale) > 20 else ""))
    return 0


def cmd_load(path: Path) -> int:
    pay = json.loads(path.read_text())
    d = date.fromisoformat(pay["date"]) if pay.get("date") else date.today()
    source = pay.get("source", "tradingview-mcp")

    # 1. symbol resolutions first: they are what future plans depend on.
    res = pay.get("resolve") or {}
    if res:
        m = tv.load_symbol_map()
        added, failed = [], []
        for tk, payload in res.items():
            full = tv.resolutions_from_search(payload, tk)
            if full:
                m[tk.upper()] = full
                added.append(f"{tk}->{full}")
            else:
                failed.append(tk)
        tv.save_symbol_map(m)
        print(f"symbols: +{len(added)} resolved" + (f", {len(failed)} with no feed: {' '.join(failed)}" if failed else ""))

    # 2. news
    items: list[tv.NewsItem] = []
    for tk, payload in (pay.get("news") or {}).items():
        got = tv.items_from_news(payload, ticker=tk)
        items.extend(got)
        if len(got) >= tv.HEADLINE_CAP:
            print(f"  note: {tk} hit the {tv.HEADLINE_CAP}-headline cap -- older news is unreachable")
    for s in pay.get("stories") or []:
        tv.attach_story(items, s.get("url", ""), s.get("story", ""))

    universe = [t.upper() for t in (pay.get("universe") or list((pay.get("news") or {}).keys()))]
    if items or universe:
        p = store.save_day(d, items, source=source, universe=universe)
        day = store.load_day(d)
        with_story = sum(1 for i in day if i.story)
        print(f"news:    {len(items)} item(s) merged -> {p.relative_to(REPO)} "
              f"({len(day)} total, {with_story} with full story, {len(store.covered(d))} tickers covered)")

    # 3. earnings
    rows = [r for payload in (pay.get("earnings") or []) for r in tv.rows_from_earnings(payload)]
    if rows:
        p = earn.save(rows, source=source)
        nxt = sum(1 for r in rows if r.next_release)
        print(f"earnings: {len(rows)} row(s) merged -> {p.relative_to(REPO)} ({nxt} with a forward date)")
    return 0


def cmd_show(ticker: str | None, d: date) -> int:
    if ticker:
        t = ticker.upper()
        hits = store.for_ticker(t, d, lookback_days=7)
        nxt, dd = earn.next_release(t), earn.days_until(t, d)
        print(f"{t}  next earnings: {nxt or 'unknown'}" + (f"  ({dd:+d}d)" if dd is not None else ""))
        if not hits:
            covered = t in store.covered(d)
            print("  no news" + (" found in the last 7 days" if covered else " -- never pulled for this date"))
        for i in hits[:15]:
            print(f"  {i.published[:16]}  {'[story] ' if i.story else ''}{i.headline[:100]}"
                  + (f"  ({i.provider})" if i.provider else ""))
        return 0
    day = store.load_day(d)
    rows = earn.load()
    print(f"{d.isoformat()}: {len(day)} news item(s) over {len(store.covered(d))} ticker(s) covered")
    print(f"earnings snapshot: {len(rows)} ticker(s), {len(earn.stale_tickers(d))} stale")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge TradingView MCP payloads into the news stores")
    ap.add_argument("--plan", action="store_true", help="print the MCP calls a pull needs")
    ap.add_argument("--load", metavar="FILE", help="transform + merge a payload JSON")
    ap.add_argument("--show", nargs="?", const="", metavar="TICKER", help="inspect the stores")
    ap.add_argument("--tickers", help="comma-separated list, overrides the universe file")
    ap.add_argument("--universe-file", default=str(DEFAULT_UNIVERSE))
    ap.add_argument("--date", help="ISO date, default today")
    a = ap.parse_args()

    d = date.fromisoformat(a.date) if a.date else date.today()
    if a.load:
        return cmd_load(Path(a.load))
    if a.show is not None:
        return cmd_show(a.show or None, d)
    if a.plan:
        tickers = ([t.strip().upper() for t in a.tickers.split(",") if t.strip()]
                   if a.tickers else _read_universe(Path(a.universe_file)))
        if not tickers:
            print(f"no tickers: {a.universe_file} is missing or empty", file=sys.stderr)
            return 1
        return cmd_plan(tickers, d)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

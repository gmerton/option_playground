"""Source-agnostic news cache: one JSON file per session, `data/news/<YYYY-MM-DD>.json`.

Why a cache and not a client: an MCP server is callable by Claude, not by cron'd Python, so
`start_alerts.sh`, `run_daily_journal.py` and the screeners can never fetch news themselves. The
contract is therefore one-way -- a Claude-driven step writes the day's file, every engine reads it.
Keeping the schema independent of the provider means a TradingView outage (or a better source) is an
adapter change, not a rewrite.

    from lib.news import store
    store.save_day(date(2026, 9, 18), items, source="tradingview-mcp")
    hits = store.for_ticker("SNDK", date(2026, 9, 18), lookback_days=3)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
NEWS_DIR = REPO / "data" / "news"
SCHEMA = 1


@dataclass
class NewsItem:
    ticker: str
    published: str          # ISO 8601, exchange-local (ET) -- the field every consumer sorts on
    headline: str
    url: str = ""
    summary: str = ""
    provider: str = ""      # who wrote it (Reuters, DJ, the company)
    story: str = ""         # full body when pulled; empty when only the headline was taken
    tags: list[str] = field(default_factory=list)

    def key(self) -> tuple[str, str]:
        """Dedup key. URL when there is one -- the same story arrives under slightly different
        headlines from different providers."""
        return (self.ticker.upper(), self.url or self.headline.strip().lower())


def _path(d: date) -> Path:
    return NEWS_DIR / f"{d.isoformat()}.json"


def save_day(d: date, items: list[NewsItem], *, source: str, universe: list[str] | None = None) -> Path:
    """Merge `items` into the day's file. Re-running a pull is safe: existing items are kept and
    matched by key, and a later pull that carries the full story upgrades a headline-only row."""
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(d)
    existing = {i.key(): i for i in load_day(d)}
    for it in items:
        it.ticker = it.ticker.upper()
        prev = existing.get(it.key())
        if prev and not it.story and prev.story:
            it.story = prev.story          # never downgrade a full story to a headline
        existing[it.key()] = it
    prior = json.loads(p.read_text()).get("universe", []) if p.exists() else []
    asked = sorted({*prior, *(u.upper() for u in (universe or [])),
                    *(i.ticker for i in existing.values())})
    p.write_text(json.dumps({
        "schema": SCHEMA, "date": d.isoformat(), "source": source,
        "pulled_at": datetime.now().isoformat(timespec="seconds"),
        "universe": asked,           # every ticker any pull has ASKED for: no news != not looked at
        "items": [asdict(i) for i in sorted(existing.values(), key=lambda x: (x.ticker, x.published))],
    }, indent=1))
    return p


def load_day(d: date) -> list[NewsItem]:
    p = _path(d)
    if not p.exists():
        return []
    raw = json.loads(p.read_text())
    return [NewsItem(**{k: v for k, v in i.items() if k in NewsItem.__annotations__})
            for i in raw.get("items", [])]


def covered(d: date) -> set[str]:
    """Tickers the day's pull looked at, whether or not it found anything."""
    p = _path(d)
    return set(json.loads(p.read_text()).get("universe", [])) if p.exists() else set()


def for_ticker(ticker: str, d: date, *, lookback_days: int = 1) -> list[NewsItem]:
    """Every item for `ticker` on the `lookback_days` files ending at `d`, newest first."""
    t = ticker.upper()
    out = [i for k in range(lookback_days) for i in load_day(d - timedelta(days=k)) if i.ticker == t]
    return sorted(out, key=lambda x: x.published, reverse=True)


def headline_for(ticker: str, d: date, *, lookback_days: int = 1) -> str | None:
    """One line for an alert or a journal row -- the newest headline, or None.
    None means 'nothing found'; use `covered()` to tell that apart from 'never looked'."""
    hits = for_ticker(ticker, d, lookback_days=lookback_days)
    return hits[0].headline if hits else None

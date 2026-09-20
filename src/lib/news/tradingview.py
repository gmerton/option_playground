"""TradingView MCP -> lib.news adapter. Pure transforms: this module never makes a network call.

Why pure: the MCP server is callable by Claude, not by cron'd Python (see store.py). So the division
of labour is fixed -- Claude makes the MCP calls and dumps the raw payloads to a file, this module
turns those payloads into rows, and run_news_pull.py merges them into the stores. Every provider
quirk (EXCHANGE:TICKER symbols, unix-UTC timestamps, the 200-headline cap) lives here, so a second
source later is another adapter rather than a rewrite.

Measured limits of the source, 2026-09-20 -- both constrain what the data may be USED for:

  * News is capped at 200 headlines per symbol -- a hard cap, not a page limit. For an active name
    that is ~36 days (SNDK's 200th reached back to 2026-08-13). There is therefore no usable
    history: news can only be accumulated FORWARD. A rule scored on it today would be scored on
    stories pulled after the outcome was known, which is the hindsight failure the thesis log
    exists to prevent. Treat news as annotation and thesis-log input, never as a gate.

  * The earnings calendar returns two points per symbol -- the last release and the next -- not a
    series across the requested range. It fixes FORWARD coverage ("when is the next print"), not
    the historical backfill gap in the catalyst studies.

  * The exchange prefix must be exact. NYSE:NVDA returns an error telling the caller not to retry
    with alternate prefixes, so guessing is not an option and resolutions are cached in
    data/news/symbol_map.json.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from lib.news.store import NewsItem

REPO = Path(__file__).resolve().parents[3]
NEWS_DIR = REPO / "data" / "news"
SYMBOL_MAP = NEWS_DIR / "symbol_map.json"
ET = ZoneInfo("America/New_York")

HEADLINE_CAP = 200       # provider hard cap per symbol; see module docstring
US_VENUES = {"NASDAQ", "NYSE", "AMEX", "ARCA", "BATS", "CBOE"}


# --- symbols -------------------------------------------------------------------------
def bare_ticker(tv: str) -> str:
    """'NASDAQ:SNDK' -> 'SNDK'. Bare input passes through."""
    return tv.split(":", 1)[-1].strip().upper()


def load_symbol_map() -> dict[str, str]:
    """ticker -> EXCHANGE:TICKER, as resolved by search-symbols and cached."""
    if not SYMBOL_MAP.exists():
        return {}
    raw = json.loads(SYMBOL_MAP.read_text())
    return {k.upper(): v for k, v in raw.get("map", {}).items()}


def save_symbol_map(m: dict[str, str]) -> Path:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    SYMBOL_MAP.write_text(json.dumps({
        "note": "ticker -> EXCHANGE:TICKER for the TradingView MCP. The prefix must be exact; "
                "the provider rejects a wrong one and says not to retry alternates.",
        "updated": datetime.now().isoformat(timespec="seconds"),
        "map": dict(sorted(m.items())),
    }, indent=1))
    return SYMBOL_MAP


def tv_symbol(ticker: str, m: dict[str, str] | None = None) -> str | None:
    return (m if m is not None else load_symbol_map()).get(ticker.upper())


def unresolved(tickers: list[str], m: dict[str, str] | None = None) -> list[str]:
    """Tickers with no cached prefix -- the ones a pull must resolve before it can ask for news."""
    m = m if m is not None else load_symbol_map()
    return sorted({t.upper() for t in tickers} - set(m))


def resolutions_from_search(payload: dict, ticker: str) -> str | None:
    """Pick the EXCHANGE:TICKER out of a search-symbols response.

    The search is fuzzy and returns the same ticker on a dozen venues -- the Swiss line, the Toronto
    and Buenos Aires depositary receipts, a leveraged ETF whose ticker merely resembles it. Ranking
    is therefore explicit: an exact ticker match, on a US equity venue, typed `stock`, wins. Returns
    None when nothing qualifies, which is a real answer -- some names have no TradingView feed.
    """
    want = ticker.upper()
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    rows = data.get("symbols", []) if isinstance(data, dict) else []
    best, best_score = None, -1
    for r in rows:
        if not isinstance(r, dict):
            continue
        sym, exch = r.get("symbol") or "", (r.get("exchange") or "").upper()
        full = sym if ":" in sym else (f"{exch}:{sym}" if exch else sym)
        if ":" not in full or bare_ticker(full) != want:
            continue
        typ = (r.get("type") or "").lower()
        if typ == "dr":                       # depositary receipt: same name, wrong instrument
            continue
        score = (2 if full.split(":", 1)[0].upper() in US_VENUES else 0) + (1 if typ == "stock" else 0)
        if score > best_score:
            best, best_score = full, score
    return best


# --- news ----------------------------------------------------------------------------
def _iso_et(unix: int | float) -> str:
    """Provider timestamps are unix seconds UTC; the store's contract is exchange-local ISO."""
    return datetime.fromtimestamp(float(unix), timezone.utc).astimezone(ET).isoformat(timespec="seconds")


def items_from_news(payload: dict, *, ticker: str | None = None) -> list[NewsItem]:
    """Map one get-news response onto NewsItems.

    `ticker` is the name the pull ASKED for, and is what the row is filed under -- a headline also
    lists relatedSymbols, but filing under those would silently widen the universe beyond what the
    day's file claims to cover. Falls back to the first related symbol only when nothing was passed.
    """
    if not payload.get("success", True):
        return []
    data = payload.get("data", payload)
    out: list[NewsItem] = []
    for h in data.get("headlines", []):
        rel = [bare_ticker(s.get("symbol", "")) for s in h.get("relatedSymbols", []) if s.get("symbol")]
        tk = (ticker or (rel[0] if rel else "")).upper()
        if not tk:
            continue
        tags = []
        if h.get("urgency") == 1:
            tags.append("top")
        if h.get("paywall"):
            tags.append("paywall")          # full story unavailable: headline is all we will ever get
        if len(rel) > 1:
            tags.append("multi-symbol")     # sector/theme piece, not name-specific
        out.append(NewsItem(
            ticker=tk,
            published=_iso_et(h.get("published", 0)),
            headline=(h.get("title") or "").strip(),
            url=h.get("link") or "",
            provider=(h.get("provider") or {}).get("name", "") if isinstance(h.get("provider"), dict) else "",
            story="",
            tags=tags,
        ))
    return out


def story_ids(payload: dict) -> dict[str, str]:
    """url -> story id, for the headlines in one get-news response.

    get-news-story keys on the headline `id` (a urn), NOT the storyPath, and NewsItem has no id
    field -- so the mapping is rebuilt from the payload at pull time rather than stored. Headlines
    tagged `paywall` are skipped: the body is not retrievable, so asking for it only burns a call.
    """
    out = {}
    for h in payload.get("data", payload).get("headlines", []):
        if h.get("paywall") or not h.get("link") or not h.get("id"):
            continue
        out[h["link"]] = h["id"]
    return out


def attach_story(items: list[NewsItem], url: str, story: str) -> list[NewsItem]:
    """Fill the full body on the item matching `url`. save_day never downgrades a story back to a
    headline, so re-pulling is safe."""
    for it in items:
        if it.url == url:
            it.story = (story or "").strip()
    return items


# --- earnings ------------------------------------------------------------------------
@dataclass
class EarningsRow:
    ticker: str
    next_release: str = ""      # ISO date; "" when the provider has no forward date
    last_release: str = ""
    eps_forecast: float | None = None
    revenue_forecast: float | None = None
    name: str = ""


def rows_from_earnings(payload: dict) -> list[EarningsRow]:
    """Map one get-earnings-calendar response. Note this is a two-point snapshot per symbol
    (last + next), not a series -- the requested date range does not produce historical rows."""
    if not payload.get("success", True):
        return []
    data = payload.get("data", payload)
    out = []
    for e in data.get("earnings", []):
        tk = bare_ticker(e.get("symbol") or e.get("name") or "")
        if not tk:
            continue
        out.append(EarningsRow(
            ticker=tk,
            next_release=(e.get("release_next_date") or "")[:10],
            last_release=(e.get("release_date") or "")[:10],
            eps_forecast=e.get("eps_forecast_next_fq"),
            revenue_forecast=e.get("revenue_forecast_next_fq"),
            name=e.get("description") or "",
        ))
    return out


def as_dict(rows: list[EarningsRow]) -> dict[str, dict]:
    return {r.ticker: asdict(r) for r in rows}

"""Durable signal store shared by the monitor and the web UI.

The monitor process writes one row per fired signal; the UI process reads
them to render (and live-append to) the opportunities table. SQLite in WAL
mode lets the two processes share the file with concurrent read/write, and
the table survives the daily Gateway/bot restart (an in-memory list would
not). Pure stdlib -- no extra dependency to carry into the container.

  SIGNAL_DB   override the db path (default: <this dir>/signals.db)
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# A ticker: starts with a letter, up to 10 chars, allows . and - (BRK.B, etc.)
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def normalize_tickers(value) -> list[str]:
    """Whitespace/`,`-split, upper-case, de-dupe (order-preserving), validate.

    Accepts a string ("AAPL msft, nvda") or an iterable of strings. Anything
    that doesn't look like a ticker is dropped silently -- the UI shows the
    accepted result back so a typo is visible rather than fatal.
    """
    parts = value.replace(",", " ").split() if isinstance(value, str) else list(value)
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        t = str(p).strip().upper()
        if t and t not in seen and _TICKER_RE.match(t):
            seen.add(t)
            out.append(t)
    return out


def db_path() -> str:
    return os.environ.get("SIGNAL_DB", os.path.join(HERE, "signals.db"))


def _connect() -> sqlite3.Connection:
    # A short busy timeout absorbs the rare write/write overlap between
    # processes; WAL keeps readers from blocking the writer.
    conn = sqlite3.connect(db_path(), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """Create the table if absent. Safe to call on every process start."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT NOT NULL,   -- ISO local time the signal fired
                session_date TEXT NOT NULL,   -- YYYY-MM-DD (trading session)
                symbol       TEXT NOT NULL,
                pattern      TEXT NOT NULL,   -- EMA | MFR | PHB
                message      TEXT NOT NULL    -- formatted detail line
            )
            """
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )


# --- watchlist settings -----------------------------------------------------
# Keys in `settings`:
#   default_tickers  space-separated editable default list
#   active_tickers   space-separated set the bot actually monitors
#   active_source    "default" | "custom"  (UI state)
#   watchlist_rev    integer bumped on every active-list change (bot polls it)

def _get(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def _set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value),
    )


def _bump_rev(conn: sqlite3.Connection) -> None:
    cur = int(_get(conn, "watchlist_rev", "0") or "0")
    _set(conn, "watchlist_rev", str(cur + 1))


def init_settings(default_seed: list[str]) -> None:
    """Seed the default + active lists on first run only.

    Seed-if-absent (not overwrite) so edits made in the UI survive restarts --
    the stored default is authoritative once it exists; the file/CLI is just
    the initial seed.
    """
    seed = " ".join(normalize_tickers(default_seed))
    with _connect() as conn:
        if not _get(conn, "default_tickers"):
            _set(conn, "default_tickers", seed)
        if not _get(conn, "active_tickers"):
            _set(conn, "active_tickers", _get(conn, "default_tickers"))
            _set(conn, "active_source", "default")
        if not _get(conn, "watchlist_rev"):
            _set(conn, "watchlist_rev", "1")


def get_watchlist() -> dict:
    with _connect() as conn:
        return {
            "default": normalize_tickers(_get(conn, "default_tickers")),
            "active": normalize_tickers(_get(conn, "active_tickers")),
            "source": _get(conn, "active_source", "default"),
            "rev": int(_get(conn, "watchlist_rev", "0") or "0"),
        }


def watchlist_rev() -> int:
    with _connect() as conn:
        return int(_get(conn, "watchlist_rev", "0") or "0")


def set_default_tickers(value) -> list[str]:
    """Edit the default list. If 'default' is the active source, the active
    set follows the edit (and rev bumps so the bot re-subscribes)."""
    tickers = normalize_tickers(value)
    with _connect() as conn:
        _set(conn, "default_tickers", " ".join(tickers))
        if _get(conn, "active_source", "default") == "default":
            _set(conn, "active_tickers", " ".join(tickers))
            _bump_rev(conn)
    return tickers


def use_default() -> list[str]:
    with _connect() as conn:
        tickers = normalize_tickers(_get(conn, "default_tickers"))
        _set(conn, "active_tickers", " ".join(tickers))
        _set(conn, "active_source", "default")
        _bump_rev(conn)
    return tickers


def set_active_custom(value) -> list[str]:
    tickers = normalize_tickers(value)
    with _connect() as conn:
        _set(conn, "active_tickers", " ".join(tickers))
        _set(conn, "active_source", "custom")
        _bump_rev(conn)
    return tickers


def add_signal(symbol: str, pattern: str, message: str,
               ts: datetime | None = None) -> int:
    """Append a fired signal; returns its row id."""
    ts = ts or datetime.now()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO signals (ts, session_date, symbol, pattern, message) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts.strftime("%Y-%m-%d %H:%M:%S"), ts.strftime("%Y-%m-%d"),
             symbol, pattern, message),
        )
        return int(cur.lastrowid)


def recent_signals(limit: int = 200) -> list[dict]:
    """Most-recent-first rows, for the initial page render."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def signals_after(last_id: int) -> list[dict]:
    """Rows newer than last_id, oldest-first, for live SSE append."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM signals WHERE id > ? ORDER BY id ASC", (last_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def max_id() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) AS m FROM signals").fetchone()
    return int(row["m"])

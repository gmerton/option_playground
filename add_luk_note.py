#!/usr/bin/env python3
"""
Add a Martin Luk livestream observation to the notes file.

Usage:
    # Ticker-specific (long or short):
    python add_luk_note.py "BE, PL" "setting up nicely for a long"
    python add_luk_note.py "GLD" "shorted when 15-min bar crossed below 9 EMA" --direction short
    python add_luk_note.py "NVDA" "extended, avoid" --date 2026-03-01

    # General market observation (no ticker):
    python add_luk_note.py --general "Market is rewarding pullback longs and pullback shorts"

Direction is auto-detected from the comment if not specified.
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

NOTES_FILE = Path("data/luk_notes.jsonl")

_SHORT_KEYWORDS = {"short", "shorted", "shorting", "bearish", "put"}


def _detect_direction(comment: str) -> str:
    words = set(re.findall(r"[a-z]+", comment.lower()))
    return "short" if words & _SHORT_KEYWORDS else "long"


def main():
    parser = argparse.ArgumentParser(description="Log a Martin Luk livestream comment")
    parser.add_argument(
        "tickers", nargs="?",
        help="Comma-separated ticker list, e.g. 'BE, PL'. Omit with --general.",
    )
    parser.add_argument("comment", nargs="?", help="Martin Luk's comment")
    parser.add_argument(
        "--general", metavar="COMMENT",
        help="Log a general market observation with no specific ticker",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date of the observation (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--direction",
        choices=["long", "short", "auto"],
        default="auto",
        help="Trade direction (default: auto-detect from comment)",
    )
    args = parser.parse_args()

    # ── General market observation (no ticker) ────────────────────────────────
    if args.general:
        note = {
            "date": args.date,
            "tickers": [],
            "comment": args.general,
            "type": "market_context",
            "analyzed": True,   # nothing to fetch; used as context in synthesis
        }
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with NOTES_FILE.open("a") as f:
            f.write(json.dumps(note) + "\n")
        print(f"Added market context: {args.date} | \"{args.general}\"")
        return

    # ── Ticker-specific observation ───────────────────────────────────────────
    if not args.tickers or not args.comment:
        parser.error("Provide tickers and comment, or use --general for a market-wide note.")

    tickers = [t.strip().upper() for t in re.split(r"[,\s]+", args.tickers) if t.strip()]
    direction = args.direction if args.direction != "auto" else _detect_direction(args.comment)

    note = {
        "date": args.date,
        "tickers": tickers,
        "comment": args.comment,
        "direction": direction,
        "analyzed": False,
    }

    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with NOTES_FILE.open("a") as f:
        f.write(json.dumps(note) + "\n")

    print(f"Added: {args.date} | {direction.upper()} | {', '.join(tickers)} | \"{args.comment}\"")


if __name__ == "__main__":
    main()

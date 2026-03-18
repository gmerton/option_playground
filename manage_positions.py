#!/usr/bin/env python3
"""
Position management CLI — view, close, and add positions.

Usage:
  python manage_positions.py list
  python manage_positions.py close <id>
  python manage_positions.py close <id> --date 2026-03-18

Requires: MYSQL_PASSWORD
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

import pandas as pd

from lib.mysql_lib import _get_conn, _get_engine, close_position, get_open_positions


def cmd_list(args) -> None:
    rows = get_open_positions()
    if not rows:
        print("No open positions.")
        return
    print(f"\n  {'ID':>3}  {'Strategy':<28}  {'Ticker':>6}  {'Contracts':>9}  "
          f"{'Entry':>10}  {'Expiry':>10}  {'Credit':>7}")
    print("  " + "─" * 80)
    for r in rows:
        print(f"  {r['id']:>3}  {r['strategy_name']:<28}  {r['ticker']:>6}  "
              f"{r['contracts']:>9}  {str(r['entry_date']):>10}  "
              f"{str(r['expiry']):>10}  ${r['entry_value']:>6.4f}")
    print()


def cmd_close(args) -> None:
    position_id = args.id
    close_date  = date.fromisoformat(args.date) if args.date else date.today()

    # Confirm the position exists and is open
    df = pd.read_sql(
        f"SELECT id, strategy_name, ticker, status FROM strategy_positions WHERE id={position_id}",
        _get_engine(),
    )

    if df.empty:
        print(f"Error: position id={position_id} not found.")
        sys.exit(1)

    row = df.iloc[0]
    if row["status"] == "closed":
        print(f"Position {position_id} ({row['strategy_name']}) is already closed.")
        sys.exit(0)

    close_position(position_id, close_date)
    print(f"Closed: [{position_id}] {row['strategy_name']} ({row['ticker']})  close_date={close_date}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage strategy positions")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all open positions")

    p_close = sub.add_parser("close", help="Close a position by ID")
    p_close.add_argument("id", type=int, help="Position ID")
    p_close.add_argument("--date", default=None, help="Close date (YYYY-MM-DD), default today")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "close":
        cmd_close(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

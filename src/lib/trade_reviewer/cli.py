"""
Trade Reviewer CLI

Run with:
    PYTHONPATH=src python -m lib.trade_reviewer.cli

Shows recent stock (STK) buys and lets you pick one to review.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal

import mysql.connector


def _get_conn():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.environ["MYSQL_PASSWORD"],
        database="stocks",
    )


def _load_recent_buys(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, trade_date, asset_category, symbol, underlying,
                   buy_sell, quantity, price, amount, net_cash
            FROM trades
            WHERE asset_category = 'STK'
              AND buy_sell = 'BUY'
            ORDER BY trade_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()

    for r in rows:
        for k, v in r.items():
            if isinstance(v, date):
                r[k] = v.isoformat()
            elif isinstance(v, Decimal):
                r[k] = float(v)
    return rows


def _pick_trade(trades: list[dict]) -> dict | None:
    print("\nRecent stock buys:")
    print(f"  {'#':>3}  {'Date':<12} {'Symbol':<8} {'Qty':>6} {'Price':>8}  {'Amount':>10}")
    print("  " + "-" * 55)
    for i, t in enumerate(trades):
        print(
            f"  {i+1:>3}  {t['trade_date']:<12} {t['symbol']:<8} "
            f"{t['quantity']:>6}  ${t['price']:>7.2f}  ${t['amount']:>9.2f}"
        )

    print("\nEnter a number to review, or 'q' to quit: ", end="", flush=True)
    raw = sys.stdin.readline().strip()
    if raw.lower() == "q":
        return None
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(trades):
            return trades[idx]
    except ValueError:
        pass
    print("Invalid selection.")
    return None


def main():
    print("=== Trade Reviewer ===")
    print("Loading recent stock buys...")

    trades = _load_recent_buys()
    if not trades:
        print("No stock buy trades found.")
        return

    trade = _pick_trade(trades)
    if trade is None:
        return

    print(f"\nReviewing: {trade['symbol']} bought on {trade['trade_date']} @ ${trade['price']:.2f}")
    print("Calling Claude Opus — this may take 15-30 seconds...\n")
    print("-" * 60)

    from lib.trade_reviewer.reviewer import review_trade
    analysis = review_trade(trade)

    print(analysis)
    print("-" * 60)


if __name__ == "__main__":
    main()

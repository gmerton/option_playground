#!/usr/bin/env python3
"""Reconstruct the CURRENT open lot's entry date(s) per name from stocks.trades.

A ticker may have been traded in/out repeatedly, so we walk trades chronologically,
track running position, and find the most recent transition from flat(<=0) to long(>0).
The buys from that point form the current position; we report their dates, the weighted
avg entry, and cross-check the ending qty against the live IBKR position.

  MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 scratch_entry_dates.py
"""
import sys
sys.path.insert(0, "src")
from lib.mysql_lib import _get_conn  # noqa: E402

# Review-list names -> current live qty (cross-check)
EXPECT = {"MRNA": 20, "GLW": 30, "CAT": 5, "AMD": 10, "MU": 2,
          "FCEL": 50, "TE": 100, "ENTG": 5, "VSH": 10}


def main():
    conn = _get_conn()
    cur = conn.cursor()
    print(f"{'sym':5s}{'live':>5}{'recon':>6}  opened       most-recent-buy   avg_entry   buys_in_lot")
    print("-" * 86)
    for sym, live in EXPECT.items():
        cur.execute(
            "SELECT trade_date, buy_sell, quantity, price FROM trades "
            "WHERE symbol=%s AND asset_category='STK' ORDER BY trade_date, id", (sym,))
        rows = cur.fetchall()
        if not rows:
            print(f"{sym:5s}{live:>5}     -  (no STK trades found)")
            continue
        pos = 0
        lot_open = None
        lot_buys = []           # (date, qty, price) for current lot
        for tdate, bs, qty, price in rows:
            q = int(qty)
            prev = pos
            pos += q
            if prev <= 0 and pos > 0:        # opened a new long lot
                lot_open = tdate
                lot_buys = [(tdate, q, float(price or 0))]
            elif pos > 0 and q > 0:          # added to existing lot
                lot_buys.append((tdate, q, float(price or 0)))
            elif pos <= 0:                   # flat or flipped short
                lot_open = None
                lot_buys = []
        # weighted avg over buys in the current lot
        tot_q = sum(q for _, q, _ in lot_buys)
        avg = sum(q * p for _, q, p in lot_buys) / tot_q if tot_q else 0
        recent = max((d for d, _, _ in lot_buys), default=None)
        flag = "" if pos == live else f"  <-- recon {pos} != live {live}"
        buys_str = ", ".join(f"{d}:{q}@{p:.2f}" for d, q, p in lot_buys)
        print(f"{sym:5s}{live:>5}{pos:>6}  {str(lot_open):11s}  {str(recent):11s}   {avg:>8.2f}   {buys_str}{flag}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()

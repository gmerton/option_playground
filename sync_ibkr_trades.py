#!/usr/bin/env python3
"""
Fetch IBKR Flex report and upsert trades into MySQL.

Usage:
    PYTHONPATH=src python sync_ibkr_trades.py              # last 5 days (default)
    PYTHONPATH=src python sync_ibkr_trades.py 7            # last N days
    PYTHONPATH=src python sync_ibkr_trades.py 20260101 20260226  # explicit range

Requires: IBKR_FLEX_TOKEN, MYSQL_PASSWORD
"""

import sys
from datetime import date, timedelta

from lib.ibkr.flex_client import fetch_flex_query, parse_flex_xml
from lib.mysql_lib import upsert_trades

# ── Date range ────────────────────────────────────────────────────────────────
if len(sys.argv) == 3:
    from_date, to_date = sys.argv[1], sys.argv[2]
elif len(sys.argv) == 2 and sys.argv[1].isdigit() and len(sys.argv[1]) <= 3:
    days = int(sys.argv[1])
    from_date = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
    to_date   = date.today().strftime("%Y%m%d")
else:
    from_date = (date.today() - timedelta(days=5)).strftime("%Y%m%d")
    to_date   = date.today().strftime("%Y%m%d")

print(f"Date range: {from_date} → {to_date}\n")

# ── Fetch ─────────────────────────────────────────────────────────────────────
xml_text = fetch_flex_query(from_date=from_date, to_date=to_date)

# ── Parse ─────────────────────────────────────────────────────────────────────
dfs = parse_flex_xml(xml_text)
print(f"\nParsed sections: {list(dfs.keys())}")

# ── Upsert ────────────────────────────────────────────────────────────────────
trades_df = dfs.get("Trade") or dfs.get("TradeConfirm")
if trades_df is None or trades_df.empty:
    print("No trade data in this report.")
    sys.exit(0)

section = "Trade" if "Trade" in dfs else "TradeConfirm"
print(f"\nUpserting {len(trades_df)} {section} rows...")
affected = upsert_trades(trades_df)
print(f"Done. Rows affected (new/updated): {affected} of {len(trades_df)}")

# ── Summary ───────────────────────────────────────────────────────────────────
cols = [c for c in ["tradeDate", "symbol", "buySell", "quantity", "price", "assetCategory"] if c in trades_df.columns]
if cols:
    print(f"\n{section} sample (last 10):")
    print(trades_df[cols].tail(10).to_string(index=False))

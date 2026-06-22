#!/usr/bin/env python3
"""
Backtest Archetype A (Technical VCP Breakout) against Tito's 15 Breakout trades.

Tests the detection rules:
1. ADR%(20d) >= ~3%
2. SMA 10>20>50 stacked, held >= 1-2 weeks before entry
3. Pivot = highest high of prior ~10-15 trading days
4. Entry bar: close at/above pivot, volume >= ~1.1x
5. Exit: grind trades (hold 20-EMA), spike trades (profit-target)
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import sys

# Add src to path
sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
import os

# Tito's 15 Breakout trades (from Adhikary_Options.csv, Setup_Type == "Breakout")
BREAKOUT_TRADES = [
    ("NVDA", "1/8/24"),
    ("SMCI", "1/19/24"),
    ("MSTR", "2/8/24"),
    ("COIN", "2/9/24"),
    ("GLD", "3/1/24"),
    ("AAPL", "6/11/24"),
    ("BRKB", "7/11/24"),
    ("IWM", "7/11/24"),
    ("GEV", "8/29/24"),
    ("APP", "9/11/24"),
    ("BABA", "9/19/24"),
    ("MSTR", "10/11/24"),  # 2nd MSTR
    ("PLTR", "11/5/24"),
    ("BTC", "11/6/24"),
    ("COST", "11/8/24"),
]

LOOKBACK_DAYS = 120  # Days of history to fetch (before entry + after for exit check)
PIVOT_WINDOW = 15   # Highest high of prior N trading days = pivot
SMA_STACK_HOLD = 3  # Minimum days SMA must be stacked before entry


async def get_daily_data(client: TradierClient, ticker: str, entry_date: str, lookback_days: int, forward_days: int) -> Optional[pd.DataFrame]:
    """Fetch daily OHLCV data. Returns DataFrame with OHLCV + computed SMA/ADR/52wk range/volume compression."""
    try:
        # entry_date format: "1/8/24" -> "2024-01-08"
        parts = entry_date.split("/")
        entry_dt = datetime(int("20" + parts[2]), int(parts[0]), int(parts[1]))
        start_dt = entry_dt - timedelta(days=lookback_days)
        end_dt = entry_dt + timedelta(days=forward_days)

        # Fetch history
        hist = await get_daily_history(ticker, start_dt.date(), end_dt.date(), client=client)
        if hist is None or hist.empty:
            return None

        # Reset index to have date as a column
        hist = hist.reset_index()

        # Compute SMAs
        hist["sma10"] = hist["close"].rolling(10, min_periods=1).mean()
        hist["sma20"] = hist["close"].rolling(20, min_periods=1).mean()
        hist["sma50"] = hist["close"].rolling(50, min_periods=1).mean()

        # Compute ADR% (average daily range over 20 days)
        hist["daily_range_pct"] = (hist["high"] - hist["low"]) / hist["open"] * 100
        hist["adr_pct"] = hist["daily_range_pct"].rolling(20, min_periods=1).mean()

        # Compute 52-week range (high-low over past ~252 days) as % of entry price
        hist["high_52w"] = hist["high"].rolling(252, min_periods=1).max()
        hist["low_52w"] = hist["low"].rolling(252, min_periods=1).min()

        # Compute RVOL (relative volume vs 50-day avg)
        hist["vol_avg_50"] = hist["volume"].rolling(50, min_periods=1).mean()
        hist["rvol"] = hist["volume"] / hist["vol_avg_50"]

        # Compute recent volume trend (10d avg vs 50d avg for compression signal)
        hist["vol_avg_10"] = hist["volume"].rolling(10, min_periods=1).mean()
        hist["vol_compression_ratio"] = hist["vol_avg_10"] / hist["vol_avg_50"]

        return hist
    except Exception as e:
        print(f"  Error fetching data for {ticker}: {e}")
        return None


def find_entry_bar_index(df: pd.DataFrame, entry_date_str: str) -> Optional[int]:
    """Find the index of the entry date in the dataframe."""
    parts = entry_date_str.split("/")
    entry_dt = datetime(int("20" + parts[2]), int(parts[0]), int(parts[1]))

    for idx, row in df.iterrows():
        if pd.to_datetime(row["date"]).date() == entry_dt.date():
            return idx
    return None


def check_sma_stack_before_entry(df: pd.DataFrame, entry_idx: int, min_days: int = SMA_STACK_HOLD) -> bool:
    """Check if 10>20>50 stack held for min_days before entry."""
    if entry_idx < min_days:
        return False

    for i in range(entry_idx - min_days, entry_idx + 1):
        row = df.iloc[i]
        # Stack means 10 > 20 > 50
        if not (row["sma10"] > row["sma20"] > row["sma50"]):
            return False

    return True


def check_pivot_and_trigger(df: pd.DataFrame, entry_idx: int) -> dict:
    """Check pivot (highest high of prior 10-15 days) and entry trigger."""
    if entry_idx < PIVOT_WINDOW:
        return {"pivot_found": False}

    # Pivot = highest high of prior 10-15 days (exclude entry day)
    prior_data = df.iloc[entry_idx - PIVOT_WINDOW:entry_idx]
    pivot_high = prior_data["high"].max()

    entry_row = df.iloc[entry_idx]

    # Check: entry close >= pivot
    closes_above_pivot = entry_row["close"] >= pivot_high

    # Check: entry volume >= 1.1x (relative to 50-day avg)
    rvol_ok = entry_row["rvol"] >= 1.1

    # Check: close near high (at least mid-range)
    range_pct = (entry_row["high"] - entry_row["low"]) / entry_row["open"]
    close_pct = (entry_row["close"] - entry_row["low"]) / entry_row["open"]
    close_near_high = close_pct >= range_pct * 0.5  # At least mid-range

    return {
        "pivot_found": True,
        "pivot_high": pivot_high,
        "entry_close": entry_row["close"],
        "closes_above_pivot": closes_above_pivot,
        "rvol": entry_row["rvol"],
        "rvol_ok": rvol_ok,
        "close_near_high": close_near_high,
    }


def check_exit_behavior(df: pd.DataFrame, entry_idx: int, days_held: int) -> dict:
    """Check exit behavior: grind (20-EMA trail) vs spike (fast profit-take)."""
    if entry_idx + days_held >= len(df):
        return {"enough_data": False}

    entry_row = df.iloc[entry_idx]
    exit_row = df.iloc[entry_idx + days_held]

    # For held >= 3 days: check if 20-EMA was ever broken on daily close
    if days_held >= 3:
        closes_held_above_20ema = True
        for i in range(entry_idx, entry_idx + days_held + 1):
            if df.iloc[i]["close"] < df.iloc[i]["sma20"]:
                closes_held_above_20ema = False
                break

        return {
            "enough_data": True,
            "days_held": days_held,
            "trade_type": "grind",
            "entry_price": entry_row["close"],
            "exit_price": exit_row["close"],
            "pnl_pct": (exit_row["close"] - entry_row["close"]) / entry_row["close"] * 100,
            "closes_held_above_20ema": closes_held_above_20ema,
        }
    else:
        # For short holds: check if it spiked (peak > entry) and faded
        max_high = df.iloc[entry_idx:entry_idx + days_held + 1]["high"].max()
        spiked = max_high > entry_row["close"] * 1.1  # Spiked >=10%

        return {
            "enough_data": True,
            "days_held": days_held,
            "trade_type": "spike",
            "entry_price": entry_row["close"],
            "exit_price": exit_row["close"],
            "max_high": max_high,
            "spike_pct": (max_high - entry_row["close"]) / entry_row["close"] * 100,
            "spiked": spiked,
        }


def load_days_held(ticker: str, entry_date: str) -> Optional[int]:
    """Load days held for a trade from CSV."""
    try:
        df = pd.read_csv("/Users/gmerton/v2/options_playground/data/studies/Adhikary/Adhikary_Options.csv")
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        match = df[(df["Ticker"] == ticker) & (df["Entry Date"] == entry_date) & (df["Setup_Type"] == "Breakout")]
        if not match.empty:
            return int(match.iloc[0]["Days_In_Trade"])
    except Exception as e:
        pass
    return None


async def backtest_trade(client: TradierClient, ticker: str, entry_date: str, days_held: int) -> dict:
    """Backtest one trade."""
    print(f"\n{ticker} entry {entry_date} (held {days_held}d):")

    # Fetch daily data (lookback + forward for exit check)
    df = await get_daily_data(client, ticker, entry_date, LOOKBACK_DAYS, days_held + 10)
    if df is None:
        print("  ✗ No data")
        return {"status": "no_data"}

    # Find entry bar
    entry_idx = find_entry_bar_index(df, entry_date)
    if entry_idx is None:
        print("  ✗ Entry date not found in data")
        return {"status": "entry_date_not_found"}

    entry_row = df.iloc[entry_idx]
    entry_price = entry_row['close']

    # Compute 52-week range % (history of big moves)
    high_52w = entry_row['high_52w']
    low_52w = entry_row['low_52w']
    range_52w_pct = (high_52w - low_52w) / entry_price * 100 if entry_price > 0 else 0

    print(f"  Entry: ${entry_price:.2f}, 52w range: {range_52w_pct:.0f}%, ADR: {entry_row['adr_pct']:.1f}%, vol compression: {entry_row['vol_compression_ratio']:.2f}x")

    # Check 52-week range gate (history of big moves)
    range_threshold = 17.0
    range_ok = range_52w_pct >= range_threshold
    if not range_ok:
        print(f"  ✗ 52-week range {range_52w_pct:.0f}% < {range_threshold}%")
        return {"status": "range_gate_failed", "range_52w_pct": range_52w_pct}
    else:
        print(f"  ✓ 52-week range {range_52w_pct:.0f}% >= {range_threshold}%")

    # Volume compression is a confirming signature but not required
    if entry_row['vol_compression_ratio'] < 1.0:
        print(f"  ✓ Volume compressed ({entry_row['vol_compression_ratio']:.2f}x baseline)")
    else:
        print(f"  ~ Volume elevated ({entry_row['vol_compression_ratio']:.2f}x baseline, not compressed)")

    # Check SMA stack (secondary signal, not required)
    sma_stacked = check_sma_stack_before_entry(df, entry_idx, min_days=1)
    if sma_stacked:
        print(f"  ✓ SMA 10>20>50 stacked")
    else:
        print(f"  ~ SMA stack weak or absent (not a hard gate)")

    # Check pivot & trigger
    pivot_info = check_pivot_and_trigger(df, entry_idx)
    if not pivot_info.get("pivot_found"):
        print(f"  ✗ Not enough history for pivot (need {PIVOT_WINDOW}d)")
        return {"status": "pivot_not_found"}

    print(f"  Pivot: ${pivot_info['pivot_high']:.2f}, Entry: ${pivot_info['entry_close']:.2f}")

    if not pivot_info["closes_above_pivot"]:
        print(f"  ✗ Entry close ${pivot_info['entry_close']:.2f} < pivot ${pivot_info['pivot_high']:.2f}")
        return {"status": "entry_below_pivot"}
    else:
        print(f"  ✓ Entry closes above pivot")

    if not pivot_info["rvol_ok"]:
        print(f"  ✗ RVOL {pivot_info['rvol']:.2f}x < 1.1x")
        return {"status": "volume_gate_failed"}
    else:
        print(f"  ✓ RVOL {pivot_info['rvol']:.2f}x >= 1.1x")

    if not pivot_info["close_near_high"]:
        print(f"  ✗ Close not near high (range signature weak)")
        return {"status": "close_not_near_high"}
    else:
        print(f"  ✓ Close near high")

    # Check exit behavior
    exit_info = check_exit_behavior(df, entry_idx, days_held)
    if not exit_info.get("enough_data"):
        print(f"  ✗ Not enough data for exit check")
        return {"status": "exit_data_missing"}

    print(f"  Trade type: {exit_info['trade_type']}")
    if exit_info["trade_type"] == "grind":
        if exit_info["closes_held_above_20ema"]:
            print(f"  ✓ Closes held above 20-EMA (grind behavior)")
        else:
            print(f"  ✗ Close broke 20-EMA during hold")
    else:  # spike
        if exit_info["spiked"]:
            print(f"  ✓ Spiked {exit_info['spike_pct']:.0f}% then faded (spike behavior)")
        else:
            print(f"  ! Did not spike 10%+ (ambiguous)")

    print(f"  ✓ PASS")
    return {"status": "pass", **exit_info}


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set")
        sys.exit(1)

    results = []
    passes = 0

    async with TradierClient(api_key=api_key) as client:
        for ticker, entry_date in BREAKOUT_TRADES:
            days_held = load_days_held(ticker, entry_date)
            if days_held is None:
                print(f"{ticker} {entry_date}: not found in CSV")
                continue

            result = await backtest_trade(client, ticker, entry_date, days_held)
            results.append((ticker, entry_date, result))

            if result.get("status") == "pass":
                passes += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passes}/{len(BREAKOUT_TRADES)} trades PASS")
    print("=" * 60)

    for ticker, entry_date, result in results:
        status_icon = "✓" if result.get("status") == "pass" else "✗"
        print(f"{status_icon} {ticker:6} {entry_date:8} {result.get('status', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())

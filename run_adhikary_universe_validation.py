#!/usr/bin/env python3
"""
Universe validation: Run Archetype A detector on S&P 500 + Nasdaq 100.
Reports win rate, ROC, frequency across all 2024 signals.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import sys
import json

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
import os

# Detection rule thresholds (from validation backtest)
RANGE_52W_MIN = 17.0
PIVOT_WINDOW = 15
PIVOT_LOOKBACK_BEFORE = 60
RVOL_MIN = 1.1
ADR_INFO_ONLY = True  # Informational, not a gate

# Tickers to scan (SP500 + Nasdaq 100)
SP500_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "BRK.B", "JNJ",
    "V", "WMT", "JPM", "PG", "MA", "VISA", "HD", "MCD", "DIS", "BA",
    "ORCL", "COST", "NFLX", "CRM", "NKE", "AMEX", "GS", "IBM", "INTC", "QCOM",
    "AMD", "PYPL", "CSCO", "INTU", "ADBE", "AVGO", "MU", "AMAT", "LRCX", "TXN",
    "ISRG", "ASML", "NOW", "SNOW", "DDOG", "CrowdStrike", "CRWD", "ZM", "APP", "COIN",
    "CVX", "XOM", "COP", "MPC", "PSX", "VLO", "EOG", "MRO", "OXY", "DVN",
    "CAT", "DE", "CMI", "KMX", "CMG", "SQ", "DASH", "UBER", "ABNB", "RBLX",
    "PLTR", "SMCI", "MSTR", "RIOT", "MARA", "CLSK", "COIN", "MSTR", "SQ", "SOFI",
    "GLD", "SLV", "USO", "UUP", "TLT", "IWM", "XLV", "XLU", "XLP", "XLE",
    # Add more S&P 500...
]

NASDAQ_TICKERS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "QCOM",
    "COST", "AMD", "CSCO", "INTC", "ADBE", "INTU", "NFLX", "PYPL", "ASML", "AZN",
    "AMAT", "LRCX", "MU", "TXN", "SNPS", "MCHP", "KLAC", "CDNS", "CRWD", "DDOG",
    "SNOW", "ZM", "NOW", "OKTA", "SPLK", "MRVL", "PALO", "NET", "FTNT", "WDAY",
    "DBX", "BOX", "COIN", "MARA", "RIOT", "SMCI", "MSTR", "PLTR", "RBLX", "ABNB",
    "UBER", "DASH", "SOFI", "FVRR", "UPWK", "ROKU", "PINS", "SNAP", "YELP", "TRIP",
    # Add more Nasdaq...
]

# Combine and dedupe
UNIVERSE = list(set(SP500_TICKERS + NASDAQ_TICKERS))[:100]  # Start with 100 for testing


async def get_daily_data(client: TradierClient, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """Fetch daily OHLCV data with computed metrics."""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        hist = await get_daily_history(ticker, start_dt, end_dt, client=client)
        if hist is None or hist.empty:
            return None

        hist = hist.reset_index()

        # Compute SMAs
        hist["sma10"] = hist["close"].rolling(10, min_periods=1).mean()
        hist["sma20"] = hist["close"].rolling(20, min_periods=1).mean()
        hist["sma50"] = hist["close"].rolling(50, min_periods=1).mean()

        # Compute ADR%
        hist["daily_range_pct"] = (hist["high"] - hist["low"]) / hist["open"] * 100
        hist["adr_pct"] = hist["daily_range_pct"].rolling(20, min_periods=1).mean()

        # Compute 52-week range
        hist["high_52w"] = hist["high"].rolling(252, min_periods=1).max()
        hist["low_52w"] = hist["low"].rolling(252, min_periods=1).min()

        # Compute RVOL
        hist["vol_avg_50"] = hist["volume"].rolling(50, min_periods=1).mean()
        hist["rvol"] = hist["volume"] / hist["vol_avg_50"]

        # Compute 20-EMA for exit checking
        hist["ema20"] = hist["close"].ewm(span=20, adjust=False).mean()

        return hist
    except Exception as e:
        return None


def check_range_gate(df: pd.DataFrame, idx: int) -> bool:
    """52-week range >= 17%."""
    row = df.iloc[idx]
    if pd.isna(row['high_52w']) or pd.isna(row['low_52w']):
        return False
    high_52w = row['high_52w']
    low_52w = row['low_52w']
    entry_price = row['close']
    range_pct = (high_52w - low_52w) / entry_price * 100 if entry_price > 0 else 0
    return range_pct >= RANGE_52W_MIN


def check_pivot(df: pd.DataFrame, idx: int) -> Optional[float]:
    """Pivot = highest high of prior 15d. Returns pivot price or None."""
    if idx < PIVOT_WINDOW:
        return None
    prior_data = df.iloc[idx - PIVOT_WINDOW:idx]
    return prior_data["high"].max()


def check_entry_signal(df: pd.DataFrame, idx: int, pivot: float) -> bool:
    """Entry: close >= pivot, RVOL >= 1.1x, close near high."""
    row = df.iloc[idx]

    # Close above pivot
    if row['close'] < pivot:
        return False

    # Volume
    if row['rvol'] < RVOL_MIN:
        return False

    # Close near high (at least mid-range)
    range_pct = (row['high'] - row['low']) / row['open']
    close_pct = (row['close'] - row['low']) / row['open']
    if close_pct < range_pct * 0.5:
        return False

    return True


def check_exit_hold(df: pd.DataFrame, idx: int, hold_days: int) -> bool:
    """Check if 20-EMA was held (grind exit)."""
    if idx + hold_days >= len(df):
        return None  # Not enough data

    for i in range(idx, idx + hold_days + 1):
        if df.iloc[i]['close'] < df.iloc[i]['ema20']:
            return False
    return True


def calculate_trade_return(df: pd.DataFrame, entry_idx: int, hold_days: int) -> Optional[float]:
    """Return % for a hold of N days."""
    if entry_idx + hold_days >= len(df):
        return None

    entry_price = df.iloc[entry_idx]['close']
    exit_price = df.iloc[entry_idx + hold_days]['close']
    return (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else None


async def scan_ticker(client: TradierClient, ticker: str, start_date: str, end_date: str) -> Dict:
    """Scan one ticker for all 2024 signals. Returns {ticker, signals: [list of trades]}."""
    signals = []

    df = await get_daily_data(client, ticker, start_date, end_date)
    if df is None or len(df) < PIVOT_LOOKBACK_BEFORE:
        return {"ticker": ticker, "signals": []}

    for idx in range(PIVOT_LOOKBACK_BEFORE, len(df)):
        # Check range gate
        if not check_range_gate(df, idx):
            continue

        # Check pivot
        pivot = check_pivot(df, idx)
        if pivot is None:
            continue

        # Check entry signal
        if not check_entry_signal(df, idx, pivot):
            continue

        # We have a signal!
        entry_date = df.iloc[idx]['date']
        entry_price = df.iloc[idx]['close']

        # Track a 10-day hold (proxy for grind trade)
        hold_10d = calculate_trade_return(df, idx, 10)
        hold_ema_ok = check_exit_hold(df, idx, 10)

        signals.append({
            "date": entry_date,
            "entry_price": entry_price,
            "hold_10d_return": hold_10d,
            "ema_hold": hold_ema_ok,
        })

    return {"ticker": ticker, "signals": signals}


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set")
        sys.exit(1)

    print(f"Scanning {len(UNIVERSE)} tickers for 2024 Archetype A signals...")
    print(f"Range gate: 52w >= {RANGE_52W_MIN}%")
    print("=" * 60)

    all_signals = []
    success_count = 0

    async with TradierClient(api_key=api_key) as client:
        for i, ticker in enumerate(UNIVERSE):
            result = await scan_ticker(client, ticker, "2024-01-01", "2024-12-31")

            if result["signals"]:
                print(f"{ticker}: {len(result['signals'])} signals")
                all_signals.extend([(ticker, s) for s in result["signals"]])
                success_count += 1

            if (i + 1) % 10 == 0:
                print(f"  ... {i+1}/{len(UNIVERSE)} tickers scanned")

    # Summary stats
    print("\n" + "=" * 60)
    print(f"SUMMARY: {len(all_signals)} signals across {len(UNIVERSE)} tickers")
    print(f"Tickers with signals: {success_count}")

    if all_signals:
        # Win rate (10-day hold)
        wins = sum(1 for _, s in all_signals if s['hold_10d_return'] is not None and s['hold_10d_return'] > 0)
        returns = [s['hold_10d_return'] for _, s in all_signals if s['hold_10d_return'] is not None]

        if returns:
            win_rate = wins / len(returns) * 100 if returns else 0
            avg_return = sum(returns) / len(returns)
            median_return = sorted(returns)[len(returns)//2]

            print(f"Win rate (10d hold): {win_rate:.1f}% ({wins}/{len(returns)})")
            print(f"Avg return: {avg_return:.2f}%")
            print(f"Median return: {median_return:.2f}%")
            print(f"Best: {max(returns):.2f}%")
            print(f"Worst: {min(returns):.2f}%")


if __name__ == "__main__":
    asyncio.run(main())

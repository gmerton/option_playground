#!/usr/bin/env python3
"""
Fade strategy universe validation: Archetype C (Exhaustion) detector.
Screens for climactic reversals on S&P 500 + Nasdaq 100, 2024.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import sys
import os

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

# Detection thresholds (from playbook)
EXTENSION_MIN = 10.0  # % above 10-SMA
HIGH_WINDOW = 15  # Prior N days for new high detection
VOLUME_CLIMACTIC = 2.3  # × 50-day avg
CLOSE_PERCENTILE_MAX = 10  # Bottom 10% of range
ADR_MIN_INFO = 1.5  # Informational gate (for big movers)

# Sample universe (S&P 500 + Nasdaq 100)
UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "BRK.B", "JNJ",
    "V", "WMT", "JPM", "PG", "MA", "VISA", "HD", "MCD", "DIS", "BA",
    "ORCL", "COST", "NFLX", "CRM", "NKE", "AMEX", "GS", "IBM", "INTC", "QCOM",
    "AMD", "PYPL", "CSCO", "INTU", "ADBE", "AVGO", "MU", "AMAT", "LRCX", "TXN",
    "ISRG", "ASML", "NOW", "SNOW", "DDOG", "CRWD", "ZM", "APP", "COIN", "SMCI",
    "MSTR", "PLTR", "RIOT", "MARA", "CLSK", "CVX", "XOM", "COP", "MPC", "PSX",
    "CAT", "DE", "CMI", "KMX", "CMG", "SQ", "DASH", "UBER", "ABNB", "RBLX",
    "GLD", "SLV", "USO", "UUP", "TLT", "IWM", "XLV", "XLU", "XLP", "XLE",
    "FVRR", "UPWK", "ROKU", "PINS", "SNAP", "YELP", "TRIP", "SOFI", "TRIP", "BOX",
    "OKTA", "NET", "WDAY", "CRowdStrike", "DBX", "SPOT", "ETSY", "AFRM", "RBLX", "MRVL",
]


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

        # Compute relative volume
        hist["vol_avg_50"] = hist["volume"].rolling(50, min_periods=1).mean()
        hist["rvol"] = hist["volume"] / hist["vol_avg_50"]

        return hist
    except Exception as e:
        return None


def check_fade_signal(df: pd.DataFrame, idx: int) -> Optional[Dict]:
    """
    Check for exhaustion/fade signal at idx.
    Returns signal dict or None.
    """
    if idx < HIGH_WINDOW + 1:
        return None

    row = df.iloc[idx]
    prev_row = df.iloc[idx - 1]

    # Gate 1: High ADR (big mover)
    if row['adr_pct'] < ADR_MIN_INFO:
        return None

    # Gate 2: Extension above 10-SMA
    sma10 = row['sma10']
    extension_pct = (row['close'] - sma10) / sma10 * 100 if sma10 > 0 else 0
    if extension_pct < EXTENSION_MIN:
        return None

    # Gate 3: New high (last 15d)
    prior_high = df.iloc[idx - HIGH_WINDOW:idx]['high'].max()
    if row['high'] <= prior_high:
        return None  # Not a new high

    # Gate 4: Climactic volume
    if row['rvol'] < VOLUME_CLIMACTIC:
        return None

    # Gate 5: Reversal bar (closes in bottom ~10% of range)
    bar_range = row['high'] - row['low']
    close_from_low = row['close'] - row['low']
    if bar_range == 0:
        return None
    close_percentile = (close_from_low / bar_range) * 100

    if close_percentile > CLOSE_PERCENTILE_MAX:
        return None  # Not a reversal bar

    # Signal found!
    return {
        "date": row['date'],
        "close": row['close'],
        "high": row['high'],
        "low": row['low'],
        "extension_pct": extension_pct,
        "rvol": row['rvol'],
        "close_percentile": close_percentile,
        "adr_pct": row['adr_pct'],
    }


def calculate_next_day_return(df: pd.DataFrame, idx: int) -> Optional[float]:
    """Next-day return (did it fade?)."""
    if idx + 1 >= len(df):
        return None

    entry_close = df.iloc[idx]['close']
    next_close = df.iloc[idx + 1]['close']
    return (next_close - entry_close) / entry_close * 100 if entry_close > 0 else None


async def scan_ticker(client: TradierClient, ticker: str) -> Dict:
    """Scan one ticker for all 2024 fade signals."""
    signals = []

    df = await get_daily_data(client, ticker, "2024-01-01", "2024-12-31")
    if df is None or len(df) < HIGH_WINDOW + 5:
        return {"ticker": ticker, "signals": []}

    for idx in range(HIGH_WINDOW + 1, len(df) - 1):
        signal = check_fade_signal(df, idx)
        if signal is None:
            continue

        # Get next-day return
        next_return = calculate_next_day_return(df, idx)

        signal["next_day_return"] = next_return

        signals.append(signal)

    return {"ticker": ticker, "signals": signals}


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set")
        sys.exit(1)

    print(f"Scanning {len(UNIVERSE)} tickers for 2024 Archetype C (Fade) signals...")
    print(f"Thresholds: Extension >{EXTENSION_MIN}%, Volume >{VOLUME_CLIMACTIC}×, Close <{CLOSE_PERCENTILE_MAX}%ile")
    print("=" * 70)

    all_signals = []
    success_count = 0

    async with TradierClient(api_key=api_key) as client:
        for i, ticker in enumerate(UNIVERSE):
            result = await scan_ticker(client, ticker)

            if result["signals"]:
                print(f"{ticker}: {len(result['signals'])} signals")
                all_signals.extend([(ticker, s) for s in result["signals"]])
                success_count += 1

            if (i + 1) % 10 == 0:
                print(f"  ... {i+1}/{len(UNIVERSE)} tickers scanned")

    # Summary stats
    print("\n" + "=" * 70)
    print(f"SUMMARY: {len(all_signals)} fade signals across {len(UNIVERSE)} tickers")
    print(f"Tickers with signals: {success_count}")

    if all_signals:
        # Next-day return analysis
        returns = [s['next_day_return'] for _, s in all_signals if s['next_day_return'] is not None]

        if returns:
            fades = sum(1 for r in returns if r < 0)  # Stock went down (fade worked)
            fade_rate = fades / len(returns) * 100

            avg_return = sum(returns) / len(returns)
            median_return = sorted(returns)[len(returns) // 2]

            print(f"\nNext-day follow-through:")
            print(f"  Fade rate (next day ↓): {fade_rate:.1f}% ({fades}/{len(returns)})")
            print(f"  Avg next-day return: {avg_return:.2f}%")
            print(f"  Median next-day return: {median_return:.2f}%")
            print(f"  Best: {max(returns):.2f}%")
            print(f"  Worst: {min(returns):.2f}%")
            print(f"\n  (Negative = fade worked; positive = wrong signal)")

        # Signal characteristics
        print(f"\nSignal characteristics:")
        extensions = [s['extension_pct'] for _, s in all_signals]
        rvols = [s['rvol'] for _, s in all_signals]

        print(f"  Avg extension: {sum(extensions)/len(extensions):.1f}%")
        print(f"  Avg RVOL: {sum(rvols)/len(rvols):.2f}×")


if __name__ == "__main__":
    asyncio.run(main())

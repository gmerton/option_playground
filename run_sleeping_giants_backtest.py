#!/usr/bin/env python3
"""
Sleeping Giants backtest — STAGE 1: historical episode sweep.

For each name in the universe, fetch full daily history once, evaluate the five
detector gates point-in-time at weekly snapshots across history, and dedupe
consecutive firing weeks into distinct EPISODES (one entry signal per base, not
one per day). Writes the episode list to CSV for stages 2-3 (entry resolution +
LEAP payoff).

This stage answers: how many trades does the strategy even generate, on which
names and dates? (The gates are tight, so this gates the whole backtest's viability.)

Usage:
  PYTHONPATH=src python run_sleeping_giants_backtest.py [--start 2014-01-01] [--step 5]
"""
import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict

sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')

import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
from lib.sleeping_giants.detector import analyze, to_floats, ATR_PCT_LOOKBACK

# Same sector-diverse large-cap universe as the live scanner.
UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AVGO", "ORCL", "CRM", "ADBE",
    "CSCO", "QCOM", "TXN", "INTC", "IBM", "NFLX", "AMD",
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA",
    "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "BMY", "AMGN",
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY",
    "CAT", "DE", "BA", "HON", "GE", "UPS", "LMT", "RTX",
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "HD", "NKE", "DIS",
    "LIN", "FCX", "NEM", "NEE", "DUK",
    "XLE", "XLF", "XLV", "XLI", "XLK", "XLP", "XLU", "GLD", "SLV",
]

WINDOW_DAYS = 1500          # multi-year lookback slice fed to analyze() per eval date
EPISODE_GAP_DAYS = 60       # firing gap > this many calendar days => a new episode
OUT_CSV = "data/studies/Adhikary/sleeping_giants_episodes.csv"


async def fetch_full_history(client: TradierClient, ticker: str, start: date, end: date):
    """One fetch per ticker: full daily history. Returns DataFrame or None."""
    df = await get_daily_history(ticker, start, end, client=client)
    if df is None or df.empty:
        return None
    df = df.reset_index().sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    return df


def sweep_ticker(ticker: str, df: pd.DataFrame, start_eval: date, step: int) -> List[Dict]:
    """Evaluate the gates point-in-time every `step` trading days; return firing rows."""
    highs = to_floats(df["high"])
    lows = to_floats(df["low"])
    closes = to_floats(df["close"])
    dates = list(df["date"])
    n = len(closes)

    firings: List[Dict] = []
    # Need at least ~half the ATR lookback of history before the first eval.
    first_idx = ATR_PCT_LOOKBACK // 2
    for i in range(first_idx, n, step):
        d_i = dates[i].date()
        if d_i < start_eval:
            continue
        # Point-in-time slice: only bars up to and including i, capped to WINDOW_DAYS span.
        lo_idx = 0
        # cap window by calendar span
        cutoff = dates[i] - pd.Timedelta(days=WINDOW_DAYS)
        # find first index >= cutoff (linear from a small offset is fine; data is modest)
        while lo_idx < i and dates[lo_idx] < cutoff:
            lo_idx += 1
        res = analyze(highs[lo_idx:i + 1], lows[lo_idx:i + 1], closes[lo_idx:i + 1])
        if res is None:
            continue
        if res["is_sleeping_giant"]:
            firings.append({
                "ticker": ticker,
                "date": d_i,
                "close": res["close"],
                "resistance": res["resistance"],
                "pos_in_base": res["pos_in_base"],
                "base_len_yrs": res["base_len_yrs"],
                "atr_rank": res["atr_rank"],
                "multiyr_range_pct": res["multiyr_range_pct"],
            })
    return firings


def dedupe_episodes(firings: List[Dict]) -> List[Dict]:
    """Collapse consecutive firing snapshots into episodes (first firing of each run)."""
    if not firings:
        return []
    firings = sorted(firings, key=lambda r: r["date"])
    episodes = [firings[0]]
    last_date = firings[0]["date"]
    for f in firings[1:]:
        if (f["date"] - last_date).days > EPISODE_GAP_DAYS:
            episodes.append(f)   # gap -> new episode
        last_date = f["date"]
    return episodes


async def main():
    api_key = os.getenv("TRADIER_API_KEY")
    if not api_key:
        print("TRADIER_API_KEY not set")
        sys.exit(1)

    start_eval = date(2014, 1, 1)
    step = 5  # weekly
    if "--start" in sys.argv:
        start_eval = date.fromisoformat(sys.argv[sys.argv.index("--start") + 1])
    if "--step" in sys.argv:
        step = int(sys.argv[sys.argv.index("--step") + 1])

    # Fetch enough history to have a multi-year window before start_eval.
    fetch_start = start_eval - timedelta(days=WINDOW_DAYS + 400)
    fetch_end = date.today()

    print(f"Sleeping Giants backtest — STAGE 1 (episode sweep)")
    print(f"Universe: {len(UNIVERSE)} | eval from {start_eval} | step {step} trading days")
    print(f"History fetch: {fetch_start} -> {fetch_end}")
    print("=" * 70)

    all_episodes: List[Dict] = []
    no_data: List[str] = []

    async with TradierClient(api_key=api_key) as client:
        for idx, ticker in enumerate(UNIVERSE):
            df = await fetch_full_history(client, ticker, fetch_start, fetch_end)
            if df is None or len(df) < ATR_PCT_LOOKBACK // 2:
                no_data.append(ticker)
                continue
            firings = sweep_ticker(ticker, df, start_eval, step)
            episodes = dedupe_episodes(firings)
            if episodes:
                print(f"{ticker:6} {len(firings):4} firing-weeks -> {len(episodes)} episode(s): "
                      f"{', '.join(e['date'].isoformat() for e in episodes)}")
                all_episodes.extend(episodes)
            if (idx + 1) % 15 == 0:
                print(f"  ... {idx+1}/{len(UNIVERSE)} scanned")

    # Write episodes
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    ep_df = pd.DataFrame(all_episodes)
    if not ep_df.empty:
        ep_df = ep_df.sort_values(["date", "ticker"]).reset_index(drop=True)
        ep_df.to_csv(OUT_CSV, index=False)

    print("\n" + "=" * 70)
    print(f"EPISODES: {len(all_episodes)} across {ep_df['ticker'].nunique() if not ep_df.empty else 0} tickers")
    if no_data:
        print(f"No data: {', '.join(no_data)}")
    if not ep_df.empty:
        print(f"\nBy year:")
        ep_df["yr"] = pd.to_datetime(ep_df["date"]).dt.year
        print(ep_df.groupby("yr").size().to_string())
        print(f"\nWritten -> {OUT_CSV}")
        print("\nNext (Stage 2): resolve entries (coil-and-hold A + wait-for-breakout B),")
        print("then pull the ~0.40-delta LEAP per entry from Athena and track payoff.")


if __name__ == "__main__":
    asyncio.run(main())

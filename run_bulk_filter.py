#!/usr/bin/env python3
"""
Filter the February bulk put spread study to identify candidates for deep analysis.

Filter pipeline:
  1. Statistical: n_entries >= 75, ROC > 0, win_rate >= 0.65
  2. Exclude leveraged/inverse ETFs
  3. Exclude already-studied tickers
  4. Rank by win_rate × ROC, take top 150 candidates
  5. Tradier batch quotes: current price >= $15, avg_volume >= 500k
  6. Tradier history: current price > price 3 years ago (structural uptrend)
  7. Tradier options: OI >= 100 on near-20-DTE put chain
  8. Print ranked top 50

Usage:
    PYTHONPATH=src python run_bulk_filter.py

Requires: TRADIER_API_KEY
"""

from __future__ import annotations

import asyncio
import csv
import math
import os
import sys
from datetime import date, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.tradier.tradier_client_wrapper import TradierClient

SUMMARY_CSV = "src/lib/output/put_spread_study_20260222154422.csv"

# ── Already-studied tickers ───────────────────────────────────────────────────
ALREADY_STUDIED = {
    "UVXY", "UVIX", "TLT", "TMF", "GLD", "XLV", "XLF", "SOXX", "SQQQ",
    "YINN", "ASHR", "BJ", "USO", "XLE", "XOP", "IWM", "QQQ", "GDX",
    "EEM", "FXI", "XLU", "XLP", "INDA", "SPY", "IWV", "VOO", "SSO",
}

# ── Known leveraged / inverse ETFs ───────────────────────────────────────────
# Covers 2x/3x equity and volatility products; not exhaustive but catches
# the common ones likely to appear in a broad options universe screen.
LEVERAGED_ETFS = {
    # Equity leverage
    "SQQQ","TQQQ","UPRO","SPXU","SPXL","SPXS","SSO","SDS","QLD","QID",
    "LABU","LABD","SOXL","SOXS","TNA","TZA","UDOW","SDOW","MIDU","MIDZ",
    "NAIL","DRN","DRV","FAS","FAZ","ERX","ERY","GUSH","DRIP","NUGT","DUST",
    "JNUG","JDST","TECL","TECS","FNGU","FNGO","DPST","WANT","HIBL","HIBS",
    "CURE","SICK","DFEN","WEBL","WEBS","RETL","EMTY","ROM","RXL","URE","SRS",
    "DIG","DUG","DDM","DXD","MVV","MZZ","EFO","EFU","EET","EEV","EZJ","EPV",
    # Volatility
    "UVXY","UVIX","VIXY","VXX","SVXY","VIXM","SVIX",
    # Bond leverage
    "TMF","TBF","TBT","TTT","UBT","PST","TBX",
    # Commodity leverage
    "UCO","SCO","BOIL","KOLD","UNG","UGAZ","DGAZ",
    # Inverse
    "PSQ","DOG","SH","MYY","RWM","BITI","SBIT",
}

# ── Filters ───────────────────────────────────────────────────────────────────
MIN_ENTRIES     = 75
MIN_WIN_RATE    = 0.65
MIN_PRICE       = 15.0
MIN_AVG_VOLUME  = 500_000     # shares/day
MIN_OI          = 100         # open interest on the options chain
TREND_YEARS     = 3           # require price now > price N years ago
PRE_FILTER_N    = 150         # candidates to pass to Tradier checks
FINAL_N         = 50          # final ranked output


# ── Step 1: load + statistical filters ───────────────────────────────────────

def load_and_filter() -> list[dict]:
    with open(SUMMARY_CSV) as f:
        rows = list(csv.DictReader(f))

    mid = [r for r in rows if r["pricing"] == "mid"]
    print(f"Loaded {len(mid)} mid-pricing rows")

    # Statistical filters
    filtered = []
    for r in mid:
        n    = int(r["n_entries"])
        roc  = float(r["roc"])
        wr   = float(r["win_rate"])
        if n >= MIN_ENTRIES and roc > 0 and wr >= MIN_WIN_RATE:
            filtered.append(r)
    print(f"After statistical filters (n>={MIN_ENTRIES}, ROC>0, win>={MIN_WIN_RATE:.0%}): {len(filtered)}")

    # Exclude leveraged ETFs and already-studied
    filtered = [r for r in filtered
                if r["ticker"] not in LEVERAGED_ETFS
                and r["ticker"] not in ALREADY_STUDIED]
    print(f"After exclusions: {len(filtered)}")

    # Rank by win_rate × ROC and take top PRE_FILTER_N
    for r in filtered:
        r["score"] = float(r["win_rate"]) * float(r["roc"])
    filtered.sort(key=lambda r: r["score"], reverse=True)

    candidates = filtered[:PRE_FILTER_N]
    print(f"Top {PRE_FILTER_N} candidates by win_rate × ROC:")
    for i, r in enumerate(candidates[:20], 1):
        print(f"  {i:3d}. {r['ticker']:<7} n={r['n_entries']:>4}  "
              f"win={float(r['win_rate']):.1%}  ROC={float(r['roc']):+.3f}  "
              f"score={r['score']:.4f}")
    if len(candidates) > 20:
        print(f"  ... and {len(candidates)-20} more")
    return candidates


# ── Step 2: Tradier batch quote (price + volume) ──────────────────────────────

async def fetch_quotes(client: TradierClient, tickers: list[str]) -> dict[str, dict]:
    """Batch quote up to 500 symbols in one call."""
    results = {}
    chunk_size = 400
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i+chunk_size]
        data = await client.get_json(
            "/markets/quotes",
            params={"symbols": ",".join(chunk), "greeks": "false"},
        )
        quotes = data.get("quotes", {}).get("quote", [])
        if isinstance(quotes, dict):
            quotes = [quotes]
        for q in quotes:
            if isinstance(q, dict):
                results[q["symbol"]] = q
    return results


# ── Step 3: Tradier history (trend check) ─────────────────────────────────────

async def fetch_price_N_years_ago(
    client: TradierClient, ticker: str, years: int = 3
) -> Optional[float]:
    """Return the closing price approximately N years ago (±30 days)."""
    target = date.today() - timedelta(days=365 * years)
    start  = target - timedelta(days=30)
    end    = target + timedelta(days=30)
    try:
        data = await client.get_json(
            f"/markets/history",
            params={
                "symbol": ticker,
                "interval": "monthly",
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )
        history = data.get("history", {})
        if not history:
            return None
        days = history.get("day", [])
        if isinstance(days, dict):
            days = [days]
        if not days:
            return None
        # Take the closest month to the target date
        days.sort(key=lambda d: abs((date.fromisoformat(d["date"]) - target).days))
        return float(days[0]["close"])
    except Exception:
        return None


async def check_trends(client: TradierClient, candidates: list[dict],
                        quotes: dict[str, dict]) -> list[dict]:
    """Add trend info; filter to those where current > N-year-ago price."""

    async def check_one(r: dict) -> Optional[dict]:
        ticker = r["ticker"]
        q = quotes.get(ticker, {})
        current = q.get("last") or q.get("close")
        if current is None:
            return None
        current = float(current)
        old_price = await fetch_price_N_years_ago(client, ticker, TREND_YEARS)
        if old_price is None or old_price <= 0:
            r["trend_pct"] = None
            return r   # can't determine — keep it
        trend_pct = (current - old_price) / old_price * 100
        r["trend_pct"] = trend_pct
        r["current_price"] = current
        return r if trend_pct > 0 else None

    tasks = [check_one(r) for r in candidates]
    results = await asyncio.gather(*tasks)
    passed = [r for r in results if r is not None]
    return passed


# ── Step 4: Tradier options liquidity ─────────────────────────────────────────

async def fetch_options_liquidity(
    client: TradierClient, ticker: str
) -> Optional[float]:
    """
    Return the maximum open interest found on any put in the nearest
    expiration that is 10–35 DTE from today.
    Returns None if no suitable expiration found.
    """
    try:
        today = date.today()
        exp_data = await client.get_json(
            "/markets/options/expirations",
            params={"symbol": ticker, "includeAllRoots": "true", "strikes": "false"},
        )
        expirations = exp_data.get("expirations", {})
        if not expirations:
            return None
        dates = expirations.get("date", [])
        if isinstance(dates, str):
            dates = [dates]
        if not dates:
            return None

        # Find nearest expiry 10–50 DTE
        candidates = []
        for d in dates:
            exp = date.fromisoformat(d)
            dte = (exp - today).days
            if 10 <= dte <= 50:
                candidates.append((dte, d))
        if not candidates:
            return None
        candidates.sort()
        _, target_exp = candidates[0]

        # Pull chain
        chain_data = await client.get_json(
            "/markets/options/chains",
            params={"symbol": ticker, "expiration": target_exp, "greeks": "false"},
        )
        options = chain_data.get("options", {})
        if not options:
            return None
        contracts = options.get("option", [])
        if isinstance(contracts, dict):
            contracts = [contracts]

        # Puts only → max OI
        puts = [c for c in contracts if c.get("option_type") == "put"]
        if not puts:
            return None
        max_oi = max((int(c.get("open_interest") or 0) for c in puts), default=0)
        return float(max_oi)

    except Exception:
        return None


async def check_liquidity(client: TradierClient, candidates: list[dict]) -> list[dict]:
    """Add max_oi; filter to those meeting MIN_OI."""

    async def check_one(r: dict) -> Optional[dict]:
        max_oi = await fetch_options_liquidity(client, r["ticker"])
        r["max_put_oi"] = max_oi
        if max_oi is None:
            return None   # no options found
        return r if max_oi >= MIN_OI else None

    # Throttle to avoid hammering Tradier
    sem = asyncio.Semaphore(10)

    async def sem_check(r: dict) -> Optional[dict]:
        async with sem:
            return await check_one(r)

    tasks = [sem_check(r) for r in candidates]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("ERROR: TRADIER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Step 1: statistical + exclusion filters
    candidates = load_and_filter()
    tickers = [r["ticker"] for r in candidates]

    async with TradierClient(api_key=api_key) as client:

        # Step 2: batch quotes → price + volume filters
        print(f"\nFetching quotes for {len(tickers)} tickers...")
        quotes = await fetch_quotes(client, tickers)

        price_vol_passed = []
        for r in candidates:
            q = quotes.get(r["ticker"], {})
            price = q.get("last") or q.get("close") or 0
            avg_vol = q.get("average_volume") or 0
            try:
                price   = float(price)
                avg_vol = float(avg_vol)
            except (TypeError, ValueError):
                continue
            r["current_price"] = price
            r["avg_volume"]    = avg_vol
            if price >= MIN_PRICE and avg_vol >= MIN_AVG_VOLUME:
                price_vol_passed.append(r)

        print(f"After price >= ${MIN_PRICE} and avg_volume >= {MIN_AVG_VOLUME:,}: "
              f"{len(price_vol_passed)} tickers")

        # Step 3: trend filter
        print(f"\nChecking {TREND_YEARS}-year price trend...")
        trend_passed = await check_trends(client, price_vol_passed, quotes)
        for r in trend_passed:
            tp = r.get("trend_pct")
            tp_s = f"{tp:+.0f}%" if tp is not None else "n/a"
        print(f"After {TREND_YEARS}-year uptrend filter: {len(trend_passed)} tickers")

        # Step 4: options liquidity
        print(f"\nChecking options liquidity (max put OI >= {MIN_OI})...")
        liq_passed = await check_liquidity(client, trend_passed)
        print(f"After options liquidity filter: {len(liq_passed)} tickers")

    # Final ranking and output
    liq_passed.sort(key=lambda r: r["score"], reverse=True)
    final = liq_passed[:FINAL_N]

    print(f"\n{'='*90}")
    print(f"  FINAL TOP {FINAL_N} PUT SPREAD CANDIDATES")
    print(f"  Filters: n>={MIN_ENTRIES} | ROC>0 | win>={MIN_WIN_RATE:.0%} | "
          f"price>=${MIN_PRICE} | ADV>={MIN_AVG_VOLUME//1000}k | "
          f"{TREND_YEARS}yr uptrend | OI>={MIN_OI}")
    print(f"  Ranked by: win_rate × ROC  (from 50-15 bulk study; re-study with standard params)")
    print(f"{'='*90}")
    print(f"{'#':>3}  {'Ticker':<8} {'N':>5}  {'Win%':>6}  {'ROC':>7}  "
          f"{'Score':>7}  {'Price':>7}  {'ADVm':>6}  {'3yr%':>6}  {'MaxOI':>7}")
    print("-"*90)
    for i, r in enumerate(final, 1):
        tp   = r.get("trend_pct")
        tp_s = f"{tp:+.0f}%" if tp is not None else "  n/a"
        oi   = r.get("max_put_oi")
        oi_s = f"{int(oi):,}" if oi is not None else "   n/a"
        adv  = r.get("avg_volume", 0) / 1e6
        print(f"{i:>3}. {r['ticker']:<8} {r['n_entries']:>5}  "
              f"{float(r['win_rate']):>6.1%}  {float(r['roc']):>7.3f}  "
              f"{r['score']:>7.4f}  ${r.get('current_price',0):>6.2f}  "
              f"{adv:>5.1f}m  {tp_s:>6}  {oi_s:>7}")
    print(f"{'='*90}")
    print(f"\nNext step: re-run each with standard params (0.20-0.30Δ, 20 DTE) "
          f"via run_put_spreads.py")


if __name__ == "__main__":
    asyncio.run(main())

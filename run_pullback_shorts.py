#!/usr/bin/env python3
"""
Luk-style pullback-short screen: stocks in real downtrends that have recently
RISEN into their falling EMAs.

Encodes the short-side rules distilled in data/martin_luk/philosophy/principles.md:
  - Structure (required): EMA9 < EMA21, EMA21 declining, intermediate downtrend
    (EMA50 declining or price < SMA50), well off the 52-week high (topped a while
    ago — the "laggard" precondition, not a first pullback in an uptrend).
  - The bounce (required): price was under the 9 EMA within the last 5 sessions
    and has now risen into the declining-EMA zone — either the 9/21 zone or
    within a band of the declining 50.
  - Vetoes/flags (reported, not auto-excluded): a strong reversal candle on the
    last bar ("don't short right after a strong reversal candle"); price above
    a *rising* 50 (wrong context).
  - Vehicle gates: ADR(20), 50d avg dollar volume, min price.

Data: the incremental Polygon day-matrix cache (data/cache/minervini_matrix.parquet,
common stocks only — refresh via run_minervini_scan.py). No API calls.
Timing gate (Luk): only short these bounces when the INDEX/SECTOR has itself
bounced back near its declining EMAs — check SPY/QQQ/SOXX separately before acting.

Run:
    PYTHONPATH=src .venv/bin/python3 run_pullback_shorts.py
    ... --band 2.5 --adr-min 3.0 --addv-min 100e6 --top 30
"""
from __future__ import annotations

import argparse

import pandas as pd

CACHE = "data/cache/minervini_matrix.parquet"


def main() -> None:
    ap = argparse.ArgumentParser(description="Luk-style pullback-short screen")
    ap.add_argument("--band", type=float, default=2.0,
                    help="%% band around the declining 21/50 EMA that counts as 'at' it")
    ap.add_argument("--adr-min", type=float, default=3.0)
    ap.add_argument("--addv-min", type=float, default=200e6)
    ap.add_argument("--price-min", type=float, default=10.0)
    ap.add_argument("--off-high-min", type=float, default=15.0,
                    help="min %% below 52wk high (topped-a-while-ago precondition)")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    from lib.minervini.scan import load_cache
    close, high, low, dolvol = load_cache(CACHE)
    asof = close.index.max().date()

    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    sma50 = close.rolling(50, min_periods=50).mean()
    hi252 = high.rolling(252, min_periods=120).max()
    adr20 = ((high - low) / close * 100).rolling(20, min_periods=20).mean()
    addv = dolvol.rolling(50, min_periods=50).mean()

    c = close.iloc[-1]
    e9, e21, e50 = ema9.iloc[-1], ema21.iloc[-1], ema50.iloc[-1]
    e21_slope = ema21.iloc[-1] - ema21.iloc[-6]        # 5-session slope
    e50_slope = ema50.iloc[-1] - ema50.iloc[-11]       # 10-session slope
    below9_recent = (close.iloc[-6:-1] < ema9.iloc[-6:-1]).any()  # under the 9 within last 5 bars
    low5 = low.iloc[-5:].min()
    bounce_pct = (c / low5 - 1) * 100
    off_hi = (1 - c / hi252.iloc[-1]) * 100
    ret63 = (c / close.iloc[-64] - 1) * 100

    # last-bar candle quality (reversal veto flag)
    h1, l1, o_proxy = high.iloc[-1], low.iloc[-1], close.iloc[-2]  # no opens in cache: prior close as proxy
    rng = (h1 - l1).replace(0, pd.NA)
    close_pos = (c - l1) / rng                       # 1.0 = closed at high of day
    reversal_bar = (close_pos >= 0.75) & (c > o_proxy)

    # structure gates
    stack = (e9 < e21) & (e21_slope < 0)
    downtrend = (e50_slope < 0) | (c < sma50.iloc[-1])
    topped = off_hi >= args.off_high_min

    # the bounce into falling EMAs
    b = args.band / 100
    zone_921 = below9_recent & (c >= e9 * (1 - b)) & (c <= e21 * (1 + b))
    zone_50 = below9_recent & (e50_slope < 0) & ((c - e50).abs() / e50 <= b)
    in_zone = zone_921 | zone_50
    bounced = bounce_pct >= adr20.iloc[-1]           # rose at least ~1 ADR off the 5d low

    # vehicle gates
    vehicle = (adr20.iloc[-1] >= args.adr_min) & (addv.iloc[-1] >= args.addv_min) & (c >= args.price_min)

    mask = stack & downtrend & topped & in_zone & bounced & vehicle
    mask = mask.fillna(False)
    picks = mask[mask].index

    t = pd.DataFrame({
        "price": c[picks].round(2),
        "zone": ["9/21" if zone_921.get(k) else "50" for k in picks],
        "d21%": ((c[picks] / e21[picks] - 1) * 100).round(1),
        "d50%": ((c[picks] / e50[picks] - 1) * 100).round(1),
        "bounce%": bounce_pct[picks].round(1),
        "ADR": adr20.iloc[-1][picks].round(1),
        "offHi%": off_hi[picks].round(0),
        "ret63%": ret63[picks].round(0),
        "ADDV$M": (addv.iloc[-1][picks] / 1e6).round(0),
        "rev_bar": ["⚠" if reversal_bar.get(k) else "" for k in picks],
        "abv50": ["⚠" if c[k] > e50[k] and e50_slope[k] >= 0 else "" for k in picks],
    })
    # rank: laggards first (worst 63d return), then closest under the 21
    t = t.sort_values(["ret63%", "d21%"]).head(args.top)

    print(f"\n=== LUK PULLBACK-SHORT SCREEN — data through {asof} ===")
    print(f"structure: EMA9<EMA21 declining + (EMA50 declining or px<SMA50) + >={args.off_high_min:.0f}% off 52wk high")
    print(f"bounce: under the 9 within 5 bars, risen >=1 ADR off the 5d low into the falling 9/21 zone "
          f"(or +/-{args.band:.1f}% of a falling 50)")
    print(f"vehicle: ADR>={args.adr_min}%, ADDV>=${args.addv_min/1e6:.0f}M, px>=${args.price_min:.0f}   "
          f"({len(picks)} pass; showing {len(t)})")
    print(f"⚠ rev_bar = strong last bar (closed top-25% of range, up) -> Luk veto: wait for rejection")
    print(f"⚠ TIMING GATE: only act when the index/sector has ALSO bounced to its declining EMAs — check separately.\n")
    if len(t):
        print(t.to_string())
    else:
        print("  (no candidates)")


if __name__ == "__main__":
    main()

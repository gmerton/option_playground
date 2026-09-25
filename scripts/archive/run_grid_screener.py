#!/usr/bin/env python3
"""
Live Grid Screener — Lookup Table
===================================
For each ETF in the universe:
  1. Fetch current ATM straddle price from Tradier
  2. Compute RV20 from yfinance closes
  3. Compute live VRP = (straddle_credit/spot * sqrt(252)) / rv20
  4. Bin VRP into trained quintile (vrp_bin)
  5. Look up best structures directly from historical aggregation table
  6. Print ranked output

Usage:
  TRADIER_API_KEY=xxx AWS_PROFILE=clarinut-gmerton PYTHONPATH=src \\
    .venv/bin/python3 run_grid_screener.py [--min-n N] [--ticker SPY]
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import pathlib
import pickle
import warnings
from datetime import date, datetime

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

_LOOKUP_PATH = pathlib.Path("data/cache/grid_lookup.parquet")
_QUANT_PATH  = pathlib.Path("data/models/grid_vrp_quantiles.pkl")

TICKERS = sorted([
    "SPY", "QQQ", "IWM", "DIA",
    "XLF", "XLE", "XLI", "XLB", "XLU", "XLP",
    "XBI", "XRT", "XOP",
    "GDX", "SLV", "GLD",
    "USO", "UNG",
    "TQQQ", "UPRO", "TNA",
    "EEM", "EFA", "EWZ", "EWY", "FXI", "FEZ",
    "TLT", "IEF", "LQD",
    "IYR", "JETS",
])

TARGET_DTE = 15
DTE_TOL    = 5


# ── VRP helpers ───────────────────────────────────────────────────────────────

def compute_rv20(closes: pd.DataFrame, tickers: list[str]) -> dict[str, float]:
    rv = {}
    for t in tickers:
        if t not in closes.columns:
            continue
        s = closes[t].dropna()
        if len(s) < 22:
            continue
        rv[t] = float(np.log(s / s.shift(1)).dropna().tail(20).std() * np.sqrt(252))
    return rv


def compute_live_vrp(current_iv: dict[str, float],
                     rv20_map: dict[str, float]) -> dict[str, float]:
    vrp = {}
    for ticker, iv_raw in current_iv.items():
        rv = rv20_map.get(ticker)
        if rv and rv > 0 and not math.isnan(iv_raw):
            vrp[ticker] = float(iv_raw * np.sqrt(252) / rv)
    return vrp


def bin_vrp(vrp: float, q: np.ndarray) -> int:
    if q is None or math.isnan(vrp):
        return 3
    vrp_w = min(vrp, q[3] * 2)
    return max(1, min(5, int(np.searchsorted(q, vrp_w) + 1)))


# ── Tradier ────────────────────────────────────────────────────────────────────

async def fetch_atm_straddle(ticker: str, spot: float, client) -> float | None:
    from lib.commons.list_expirations import list_expirations
    from lib.commons.list_contracts import list_contracts_for_expiry

    try:
        exps = await list_expirations(ticker, client=client)
    except Exception:
        return None

    today = date.today()
    best_exp, best_err = None, 9999
    for exp_str in exps:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        dte = (exp_date - today).days
        if TARGET_DTE - DTE_TOL <= dte <= TARGET_DTE + DTE_TOL:
            err = abs(dte - TARGET_DTE)
            if err < best_err:
                best_err, best_exp = err, exp_str

    if best_exp is None:
        return None

    try:
        contracts = await list_contracts_for_expiry(
            ticker, best_exp,
            min_strike=spot * 0.80, max_strike=spot * 1.20,
            include_greeks=True, client=client,
        )
    except Exception:
        return None

    if not contracts:
        return None

    strikes = sorted(set(float(c["strike"]) for c in contracts))
    atm = min(strikes, key=lambda s: abs(s - spot))

    call_mid = put_mid = None
    for c in contracts:
        if float(c["strike"]) != atm:
            continue
        bid, ask = c.get("bid") or 0, c.get("ask") or 0
        if bid <= 0 or ask <= 0:
            continue
        mid = (bid + ask) / 2.0
        if c.get("option_type") == "call":
            call_mid = mid
        elif c.get("option_type") == "put":
            put_mid = mid

    if call_mid is None or put_mid is None:
        return None
    return (call_mid + put_mid) / spot if spot > 0 else None


async def fetch_all_straddles(tickers: list[str],
                               spots: dict[str, float]) -> dict[str, float]:
    from lib.tradier.tradier_client_wrapper import TradierClient

    api_key = os.environ.get("TRADIER_API_KEY", "")
    if not api_key:
        raise RuntimeError("TRADIER_API_KEY not set")

    print(f"Fetching live ATM straddles from Tradier for {len(tickers)} tickers ...")
    results = {}
    async with TradierClient(api_key=api_key) as client:
        tasks = {t: fetch_atm_straddle(t, spots.get(t, 0), client)
                 for t in tickers if t in spots}
        done = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for ticker, result in zip(tasks.keys(), done):
            if not isinstance(result, Exception) and result is not None:
                results[ticker] = result

    print(f"  Got straddle prices for {len(results)}/{len(tickers)} tickers")
    return results


# ── Lookup & display ──────────────────────────────────────────────────────────

def lookup_best(lookup: pd.DataFrame, ticker: str, vrp_bin: int,
                bullish: int, high_vix: int, min_n: int,
                top_n: int = 5) -> pd.DataFrame:
    cell = lookup[
        (lookup["ticker"]   == ticker) &
        (lookup["vrp_bin"]  == vrp_bin) &
        (lookup["bullish"]  == bullish) &
        (lookup["high_vix"] == high_vix) &
        (lookup["n_trades"] >= min_n)
    ].sort_values("mean_roc", ascending=False)
    return cell.head(top_n)


async def main_async(filter_ticker: str | None, min_n: int) -> None:
    # Load lookup table + VRP quantiles
    if not _LOOKUP_PATH.exists() or not _QUANT_PATH.exists():
        raise RuntimeError(
            "Lookup table not found. Run: PYTHONPATH=src .venv/bin/python3 run_grid_model.py --build"
        )
    lookup = pd.read_parquet(_LOOKUP_PATH)
    with open(_QUANT_PATH, "rb") as f:
        meta = pickle.load(f)
    vrp_quantiles = meta["vrp_quantiles"]

    tickers = [filter_ticker] if filter_ticker else TICKERS

    # ── Spot + RV20 from yfinance ─────────────────────────────────────────────
    print("Downloading spot prices ...")
    raw = yf.download(tickers + ["^VIX"], period="90d",
                      progress=False, auto_adjust=True)
    closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    closes.index = pd.to_datetime(closes.index).date

    vix_now = float(closes["^VIX"].dropna().iloc[-1])
    high_vix = int(vix_now >= 20.0)

    spots, ma50s = {}, {}
    for t in tickers:
        if t not in closes.columns:
            continue
        s = closes[t].dropna()
        if len(s) < 22:
            continue
        spots[t] = float(s.iloc[-1])
        ma50s[t]  = float(s.tail(50).mean()) if len(s) >= 50 else float("nan")

    rv20_map = compute_rv20(closes, tickers)

    # ── Live straddles → VRP ──────────────────────────────────────────────────
    current_iv = await fetch_all_straddles(tickers, spots)
    vrp_map    = compute_live_vrp(current_iv, rv20_map)

    today = date.today()
    trend  = lambda b: "Bull" if b else "Bear"
    vixlbl = lambda h: "HiVIX" if h else "LoVIX"

    # ── Per-ticker output ─────────────────────────────────────────────────────
    print(f"\n{'═'*100}")
    print(f"  LIVE GRID SCREENER — {today}   VIX={vix_now:.1f}  "
          f"({'HighVIX' if high_vix else 'LowVIX'})   min_n={min_n}")
    print(f"{'═'*100}")

    summary_rows = []

    for ticker in tickers:
        spot = spots.get(ticker)
        ma50 = ma50s.get(ticker)
        if spot is None or ma50 is None or math.isnan(ma50):
            continue

        vrp     = vrp_map.get(ticker, float("nan"))
        q       = vrp_quantiles.get(ticker)
        vrp_bin = bin_vrp(vrp, q) if not math.isnan(vrp) else 3
        bullish = int(spot > ma50)

        best = lookup_best(lookup, ticker, vrp_bin, bullish, high_vix, min_n)

        if best.empty:
            summary_rows.append(dict(ticker=ticker, vrp=vrp, vrp_bin=vrp_bin,
                                     spot_50ma=spot/ma50, bullish=bullish,
                                     best_roc=float("nan"), c_delta=None,
                                     p_delta=None, dte=None, n=0))
            continue

        top = best.iloc[0]
        summary_rows.append(dict(
            ticker=ticker, vrp=vrp, vrp_bin=vrp_bin, spot_50ma=spot/ma50,
            bullish=bullish, best_roc=top["mean_roc"],
            c_delta=top["c_delta_tgt"], p_delta=top["p_delta_tgt"],
            dte=int(top["dte_tgt"]), n=int(top["n_trades"]),
        ))

        vrp_str   = f"{vrp:.2f}" if not math.isnan(vrp) else " n/a"
        state_lbl = f"VRP={vrp_str} (bin {vrp_bin}/5)  {trend(bullish)}/{vixlbl(high_vix)}"
        print(f"\n  {ticker}  —  Spot/50MA={spot/ma50:.3f}  {state_lbl}")
        print(f"  {'CallΔ':>6}  {'PutΔ':>5}  {'DTE':>4}  {'MeanROC':>8}  "
              f"{'WinRate':>8}  {'N':>5}  {'StdROC':>7}")
        print(f"  {'─'*58}")
        for _, r in best.iterrows():
            std_str = f"{r['std_roc']*100:>6.1f}%" if pd.notna(r.get("std_roc")) else "     —"
            marker  = " ◀" if r.name == best.index[0] else ""
            print(f"  {r['c_delta_tgt']:>6.2f}  {r['p_delta_tgt']:>5.2f}  "
                  f"{int(r['dte_tgt']):>4}  {r['mean_roc']*100:>7.1f}%  "
                  f"{r['win_rate']*100:>7.1f}%  {int(r['n_trades']):>5}  "
                  f"{std_str}{marker}")

    # ── Summary ranking ───────────────────────────────────────────────────────
    if not filter_ticker and summary_rows:
        summ = (pd.DataFrame(summary_rows)
                .dropna(subset=["best_roc"])
                .sort_values("best_roc", ascending=False))
        print(f"\n{'═'*100}")
        print(f"  RANKING BY BEST HISTORICAL ROC IN CURRENT REGIME")
        print(f"{'═'*100}")
        print(f"  {'#':>2}  {'Ticker':<6}  {'VRP':>5}  {'Bin':>4}  {'Regime':<14}  "
              f"{'Spot/50MA':>9}  {'Structure':>16}  {'MeanROC':>8}  {'N':>5}")
        print(f"  {'─'*90}")
        for rank, (_, r) in enumerate(summ.iterrows(), 1):
            struct = (f"{r['c_delta']:.2f}C/{r['p_delta']:.2f}P@{int(r['dte'])}d"
                      if r["c_delta"] is not None else "  no data")
            vrp_s  = f"{r['vrp']:.2f}" if not math.isnan(r["vrp"]) else " n/a"
            regime = f"{trend(r['bullish'])}/{vixlbl(high_vix)}"
            print(f"  {rank:>2}  {r['ticker']:<6}  {vrp_s:>5}  {int(r['vrp_bin']):>4}  "
                  f"{regime:<14}  {r['spot_50ma']:>9.3f}  {struct:>16}  "
                  f"{r['best_roc']*100:>7.1f}%  {int(r['n']):>5}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", type=str, default=None,
                        help="Run for a single ticker only")
    parser.add_argument("--min-n", type=int, default=10,
                        help="Minimum historical trades per cell (default: 10)")
    args = parser.parse_args()
    asyncio.run(main_async(
        filter_ticker=args.ticker.upper() if args.ticker else None,
        min_n=args.min_n,
    ))


if __name__ == "__main__":
    main()

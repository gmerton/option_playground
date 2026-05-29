#!/usr/bin/env python3
"""
IV-Crush Far-OTM Strangle Screener
=====================================
Screens commodity and high-vol country ETFs for far-OTM strangle opportunities
where IV is spike-elevated relative to recent realized vol and likely to crush.

Structure: sell far-OTM put + sell far-OTM call, 45–90 DTE
Signal:    VRP (IV/RV20) ≥ threshold AND absolute IV ≥ threshold
           Each leg must have tradeable premium (≥ $0.50, BA ≤ 25%)

Excludes:  Leveraged ETFs

Rationale: High-IV commodity/country ETFs have episodic vol spikes driven by
           identifiable, time-limited catalysts (OPEC, geopolitical, macro events).
           When IV is spike-elevated and the underlying is not in an extreme trend,
           selling far-OTM options captures vega crush as the catalyst resolves.
           This is a vega trade, not a theta trade — profit comes primarily from
           IV compression over days to weeks, not time decay.

Usage:
  TRADIER_API_KEY=xxx AWS_PROFILE=clarinut-gmerton PYTHONPATH=src \\
    .venv/bin/python3 run_iv_crush_screener.py [--ticker USO] [--min-vrp 1.5]
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import warnings
from datetime import date, datetime

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import brentq
from scipy.stats import norm

warnings.filterwarnings("ignore")

# ── Universe ────────────────────────────────────────────────────────────────

UNIVERSE = sorted([
    # Energy
    "USO", "UNG", "XOP", "OIH", "XLE",
    # Metals / commodities
    "GLD", "SLV", "GDX", "GDXJ",
    # Country / EM
    "EWZ", "FXI", "INDA", "EEM", "EWY", "ASHR", "FEZ",
    # Broad equity (included for comparison; lower IV expected)
    "IWM", "DIA",
])

# ── Screening thresholds ────────────────────────────────────────────────────

MIN_VRP          = 1.5    # IV must be ≥ 1.5× recent realized vol
MIN_ABS_IV       = 0.40   # 40% absolute IV floor (below this, far-OTM is worthless)
MIN_LEG_PREMIUM  = 0.50   # Each leg ≥ $0.50 mid
MAX_BA_PCT       = 0.25   # Bid-ask spread ≤ 25% of mid
MIN_DTE          = 45     # Shortest expiry to consider
MAX_DTE          = 90     # Longest expiry to consider
MAX_TREND_DEV    = 0.15   # Skip if spot is > ±15% from 50MA (extreme trend)

# OTM % levels checked for puts and calls (asymmetric — calls can be farther)
PUT_OTM_TARGETS  = [0.25, 0.30, 0.35, 0.40]
CALL_OTM_TARGETS = [0.25, 0.30, 0.35, 0.40, 0.50, 0.60]

ATM_DTE_TARGET   = 30    # DTE used for the IV signal (short-term ATM straddle)
ATM_DTE_TOL      = 8
RATE             = 0.04


# ── Math helpers ────────────────────────────────────────────────────────────

def bs_iv(price: float, S: float, K: float, T: float,
          r: float = RATE, opt_type: str = "C") -> float:
    """Black-Scholes implied vol via Brent's method."""
    def _price(sigma: float) -> float:
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if opt_type == "C":
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    try:
        return float(brentq(lambda s: _price(s) - price, 0.01, 20.0, xtol=1e-5))
    except Exception:
        return float("nan")


def compute_rv(closes: pd.Series, window: int = 20) -> float:
    s = closes.dropna()
    if len(s) < window + 2:
        return float("nan")
    return float(np.log(s / s.shift(1)).dropna().tail(window).std() * np.sqrt(252))


# ── Tradier helpers ─────────────────────────────────────────────────────────

async def _best_expiry(ticker: str, client, min_dte: int, max_dte: int,
                       target_dte: int) -> tuple[str | None, int]:
    from lib.commons.list_expirations import list_expirations
    try:
        exps = await list_expirations(ticker, client=client)
    except Exception:
        return None, 0
    today = date.today()
    best_exp, best_err, best_dte = None, 9999, 0
    for exp_str in exps:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        dte = (exp_date - today).days
        if min_dte <= dte <= max_dte:
            err = abs(dte - target_dte)
            if err < best_err:
                best_err, best_exp, best_dte = err, exp_str, dte
    return best_exp, best_dte


async def fetch_atm_iv(ticker: str, spot: float, client) -> tuple[float, int]:
    """Return (ATM BS IV, DTE) from the nearest ~30 DTE expiry."""
    from lib.commons.list_contracts import list_contracts_for_expiry
    exp_str, dte = await _best_expiry(
        ticker, client,
        min_dte=ATM_DTE_TARGET - ATM_DTE_TOL,
        max_dte=ATM_DTE_TARGET + ATM_DTE_TOL,
        target_dte=ATM_DTE_TARGET,
    )
    if exp_str is None:
        return float("nan"), 0

    T = dte / 365
    try:
        contracts = await list_contracts_for_expiry(
            ticker, exp_str,
            min_strike=spot * 0.85, max_strike=spot * 1.15,
            include_greeks=True, client=client,
        )
    except Exception:
        return float("nan"), 0

    if not contracts:
        return float("nan"), 0

    strikes = sorted(set(float(c["strike"]) for c in contracts))
    atm = min(strikes, key=lambda k: abs(k - spot))

    call_mid = None
    for c in contracts:
        if float(c["strike"]) != atm or c.get("option_type") != "call":
            continue
        bid, ask = c.get("bid") or 0, c.get("ask") or 0
        if bid > 0 and ask > 0:
            call_mid = (bid + ask) / 2
            break

    if call_mid is None:
        return float("nan"), 0

    return bs_iv(call_mid, spot, atm, T, opt_type="C"), dte


async def fetch_far_otm_legs(ticker: str, spot: float, client) -> list[dict]:
    """
    For each valid expiry in [MIN_DTE, MAX_DTE], find all put/call combos
    at PUT_OTM_TARGETS × CALL_OTM_TARGETS that pass premium + BA filters.
    Returns list of qualifying structures sorted by total credit descending.
    """
    from lib.commons.list_expirations import list_expirations
    from lib.commons.list_contracts import list_contracts_for_expiry

    try:
        exps = await list_expirations(ticker, client=client)
    except Exception:
        return []

    today = date.today()
    valid_exps = []
    for exp_str in exps:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        dte = (exp_date - today).days
        if MIN_DTE <= dte <= MAX_DTE:
            valid_exps.append((dte, exp_str))

    results = []
    for dte, exp_str in valid_exps:
        try:
            contracts = await list_contracts_for_expiry(
                ticker, exp_str,
                min_strike=spot * 0.40, max_strike=spot * 1.70,
                include_greeks=True, client=client,
            )
        except Exception:
            continue

        if not contracts:
            continue

        # Index contracts by (strike, type)
        chain: dict[tuple[float, str], dict] = {}
        for c in contracts:
            bid, ask = c.get("bid") or 0, c.get("ask") or 0
            if bid <= 0 or ask <= 0:
                continue
            mid = (bid + ask) / 2
            ba_pct = (ask - bid) / mid
            chain[(float(c["strike"]), c["option_type"])] = {
                "mid": mid, "ba_pct": ba_pct,
                "delta": abs((c.get("greeks") or {}).get("delta") or float("nan")),
            }

        put_strikes  = sorted(k for (k, t) in chain if t == "put"  and k < spot)
        call_strikes = sorted(k for (k, t) in chain if t == "call" and k > spot)

        if not put_strikes or not call_strikes:
            continue

        for p_otm in PUT_OTM_TARGETS:
            p_tgt = spot * (1 - p_otm)
            p_k = min(put_strikes, key=lambda k: abs(k - p_tgt))
            p = chain.get((p_k, "put"))
            if not p or p["mid"] < MIN_LEG_PREMIUM or p["ba_pct"] > MAX_BA_PCT:
                continue

            for c_otm in CALL_OTM_TARGETS:
                c_tgt = spot * (1 + c_otm)
                c_k = min(call_strikes, key=lambda k: abs(k - c_tgt))
                c = chain.get((c_k, "call"))
                if not c or c["mid"] < MIN_LEG_PREMIUM or c["ba_pct"] > MAX_BA_PCT:
                    continue

                results.append({
                    "dte":            dte,
                    "expiry":         exp_str,
                    "put_strike":     p_k,
                    "call_strike":    c_k,
                    "put_otm":        (spot - p_k) / spot,
                    "call_otm":       (c_k - spot) / spot,
                    "put_mid":        p["mid"],
                    "call_mid":       c["mid"],
                    "put_ba":         p["ba_pct"],
                    "call_ba":        c["ba_pct"],
                    "put_delta":      p["delta"],
                    "call_delta":     c["delta"],
                    "total_credit":   p["mid"] + c["mid"],
                })

    return sorted(results, key=lambda r: -r["total_credit"])


# ── Per-ticker screening ─────────────────────────────────────────────────────

async def screen_ticker(ticker: str, spot: float,
                         closes: pd.Series, client) -> dict:
    rv20 = compute_rv(closes, 20)
    rv60 = compute_rv(closes, 60)

    if math.isnan(rv20):
        return {"ticker": ticker, "skip_reason": "insufficient price history"}

    # 50MA trend filter
    s = closes.dropna()
    ma50 = float(s.tail(50).mean()) if len(s) >= 50 else float("nan")
    trend_dev = (spot - ma50) / ma50 if not math.isnan(ma50) else float("nan")
    if not math.isnan(trend_dev) and abs(trend_dev) > MAX_TREND_DEV:
        return {
            "ticker": ticker, "spot": spot, "rv20": rv20,
            "trend_dev": trend_dev,
            "skip_reason": f"extreme trend ({trend_dev:+.1%} vs 50MA)",
        }

    # ATM IV signal
    iv_atm, iv_dte = await fetch_atm_iv(ticker, spot, client)
    if math.isnan(iv_atm):
        return {"ticker": ticker, "skip_reason": "ATM IV unavailable"}

    vrp = iv_atm / rv20

    if vrp < MIN_VRP:
        return {
            "ticker": ticker, "spot": spot, "iv_atm": iv_atm,
            "rv20": rv20, "vrp": vrp, "trend_dev": trend_dev,
            "skip_reason": f"VRP {vrp:.2f}× < {MIN_VRP}× threshold",
        }

    if iv_atm < MIN_ABS_IV:
        return {
            "ticker": ticker, "spot": spot, "iv_atm": iv_atm,
            "rv20": rv20, "vrp": vrp, "trend_dev": trend_dev,
            "skip_reason": f"IV {iv_atm:.1%} < {MIN_ABS_IV:.0%} threshold",
        }

    # Far OTM leg check at 45–90 DTE
    legs = await fetch_far_otm_legs(ticker, spot, client)

    return {
        "ticker":     ticker,
        "spot":       spot,
        "iv_atm":     iv_atm,
        "iv_dte":     iv_dte,
        "rv20":       rv20,
        "rv60":       rv60,
        "vrp":        vrp,
        "trend_dev":  trend_dev,
        "legs":       legs,
        "skip_reason": None if legs else "no qualifying far-OTM legs at 45–90 DTE",
    }


# ── Main ────────────────────────────────────────────────────────────────────

async def main_async(filter_ticker: str | None, min_vrp: float) -> None:
    from lib.tradier.tradier_client_wrapper import TradierClient

    api_key = os.environ.get("TRADIER_API_KEY", "")
    if not api_key:
        raise RuntimeError("TRADIER_API_KEY not set")

    global MIN_VRP
    MIN_VRP = min_vrp

    tickers = [filter_ticker] if filter_ticker else UNIVERSE

    print("Downloading spot prices and history ...")
    raw = yf.download(tickers, period="120d", progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        closes_all = raw["Close"]
    else:
        closes_all = raw[["Close"]]
        closes_all.columns = tickers
    closes_all.index = pd.to_datetime(closes_all.index).date

    spots: dict[str, float] = {}
    for t in tickers:
        if t in closes_all.columns:
            s = closes_all[t].dropna()
            if len(s) >= 22:
                spots[t] = float(s.iloc[-1])

    print(f"Screening {len(spots)} tickers via Tradier ...")
    results: list[dict] = []
    async with TradierClient(api_key=api_key) as client:
        tasks = {
            t: screen_ticker(t, spots[t], closes_all[t], client)
            for t in tickers if t in spots
        }
        done = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for ticker, res in zip(tasks.keys(), done):
            if isinstance(res, Exception):
                results.append({"ticker": ticker, "skip_reason": repr(res)})
            elif res:
                results.append(res)

    # ── Output ───────────────────────────────────────────────────────────────
    today = date.today()
    qualified = [r for r in results if r.get("legs")]
    skipped   = [r for r in results if "legs" not in r or not r["legs"]]

    print(f"\n{'═'*95}")
    print(f"  IV-CRUSH FAR-OTM STRANGLE SCREENER  ·  {today}")
    print(f"  Signal: VRP ≥ {MIN_VRP}×  |  IV ≥ {MIN_ABS_IV:.0%}  |  "
          f"Each leg ≥ ${MIN_LEG_PREMIUM}  |  BA ≤ {MAX_BA_PCT:.0%}  |  DTE {MIN_DTE}–{MAX_DTE}")
    print(f"{'═'*95}")

    if not qualified:
        print("\n  No qualifying tickers today.\n")
    else:
        for r in sorted(qualified, key=lambda x: -x["vrp"]):
            legs = r["legs"]
            print(f"\n  {'━'*85}")
            trend_str = f"{r['trend_dev']:+.1%} vs 50MA" if not math.isnan(r.get("trend_dev", float("nan"))) else ""
            print(f"  {r['ticker']}  spot=${r['spot']:.2f}  "
                  f"IV={r['iv_atm']:.1%} ({r['iv_dte']}DTE ATM)  "
                  f"RV20={r['rv20']:.1%}  RV60={r['rv60']:.1%}  "
                  f"VRP={r['vrp']:.2f}×  {trend_str}")
            print(f"  {'Put K':>8}  {'Call K':>8}  {'DTE':>5}  "
                  f"{'Put OTM':>8}  {'Call OTM':>9}  "
                  f"{'Put Mid':>8}  {'Call Mid':>9}  {'Total Cr':>9}  "
                  f"{'P BA':>6}  {'C BA':>6}")
            print(f"  {'-'*93}")

            # Deduplicate by (put_strike, call_strike, dte), show top 8
            seen: set = set()
            shown = 0
            for leg in legs:
                key = (leg["put_strike"], leg["call_strike"], leg["dte"])
                if key in seen or shown >= 8:
                    continue
                seen.add(key)
                shown += 1
                print(f"  {leg['put_strike']:>8.2f}  {leg['call_strike']:>8.2f}  "
                      f"{leg['dte']:>5}  "
                      f"{leg['put_otm']:>7.1%}  {leg['call_otm']:>8.1%}  "
                      f"${leg['put_mid']:>7.2f}  ${leg['call_mid']:>8.2f}  "
                      f"${leg['total_credit']:>8.2f}  "
                      f"{leg['put_ba']:>5.1%}  {leg['call_ba']:>5.1%}")

    print(f"\n{'─'*95}")
    print(f"  SKIPPED / DID NOT QUALIFY ({len(skipped)}):")
    for r in sorted(skipped, key=lambda x: x["ticker"]):
        iv_str = (f"IV={r['iv_atm']:.1%}  VRP={r['vrp']:.2f}×"
                  if not math.isnan(r.get("iv_atm", float("nan"))) else "")
        print(f"  {r['ticker']:<8}  {iv_str:<25}  {r.get('skip_reason', '')}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker",  type=str,   default=None,
                        help="Run for a single ticker only")
    parser.add_argument("--min-vrp", type=float, default=MIN_VRP,
                        help=f"Minimum VRP threshold (default: {MIN_VRP})")
    args = parser.parse_args()
    asyncio.run(main_async(
        filter_ticker=args.ticker.upper() if args.ticker else None,
        min_vrp=args.min_vrp,
    ))


if __name__ == "__main__":
    main()

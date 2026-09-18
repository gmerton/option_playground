#!/usr/bin/env python3
"""
Friday options screener — checks all confirmed strategies against live
Tradier data and prints a thumbs-up / thumbs-down for each trade.

Usage:
    PYTHONPATH=src python run_friday_screener.py
    PYTHONPATH=src python run_friday_screener.py --date 2026-03-07

Output: per-strategy detail + one-line summary with ENTER / SKIP verdict.

Requires: TRADIER_API_KEY exported in your shell environment.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys
from datetime import timedelta, date
from pathlib import Path
from typing import Optional

import pandas as pd

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_expirations import list_expirations
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.bs import implied_vol as _bs_implied_vol
from lib.studies.strategy_registry import STRATEGY_MAP


# ── Strategy definitions ──────────────────────────────────────────────────────
#
# type "spread":
#   vix_cond:   None          → always enter
#               ("lt",  N)    → enter only when VIX < N
#               ("gte", N)    → enter only when VIX ≥ N
#   long_delta: None          → naked short (no long leg)
#
# type "calendar":
#   min_gap / max_gap         → days between short and long expiry
#   min_iv_ratio              → minimum iv_ratio to enter (1.0 = backwardation only)

STRATEGIES: list[dict] = [
    # ── Spread strategies ─────────────────────────────────────────────────────
    {
        "type":          "spread",
        "name":          "UVXY Bear Call Spread",
        "alloc_key":     "UVXY combined",
        "ticker":        "UVXY",
        "cp":            "call",
        "short_delta":   0.50,
        "long_delta":    0.40,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.50,   # avg=1.34; >1.50 = extreme contango (vol spike loading)
        "note":          "structural decay trade — enter every Friday",
    },
    {
        "type":          "spread",
        "name":          "UVXY Short Put",
        "alloc_key":     "UVXY combined",
        "ticker":        "UVXY",
        "cp":            "put",
        "short_delta":   0.40,
        "long_delta":    None,
        "vix_cond":      ("lt", 20),
        "profit_take":   0.50,
        "fwd_vol_warn":  1.50,   # same underlying as call spread
        "note":          "only when VIX < 20; skip in elevated-fear regimes",
    },
    {
        "type":          "spread",
        "name":          "UVIX Bear Call Spread",
        "alloc_key":     "UVIX calls",
        "ticker":        "UVIX",
        "cp":            "call",
        "short_delta":   0.50,
        "long_delta":    0.40,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.50,   # avg=1.421 (steep contango); >1.50 = extreme
        "note":          "2x VIX decay; enter every Friday; check dollar credit > $0.10",
    },
    {
        "type":          "spread",
        "name":          "TLT Bear Call Spread",
        "alloc_key":     "TLT calls",
        "ticker":        "TLT",
        "cp":            "call",
        "short_delta":   0.35,
        "long_delta":    0.25,
        "vix_cond":      ("gte", 20),
        "profit_take":   0.70,
        "fwd_vol_warn":  1.30,   # avg=1.10; >1.30 = elevated
        "vrp_min":       -2.5,   # skip Q1 (VRP < -2.5 pp): 60.9% win / -4.9% avg ROC
        "note":          "only when VIX ≥ 20 (fear = TLT under pressure)",
    },
    {
        "type":          "spread",
        "name":          "TMF Bear Call Spread",
        "alloc_key":     "TMF calls",
        "ticker":        "TMF",
        "cp":            "call",
        "short_delta":   0.35,
        "long_delta":    0.25,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.101; >1.20 = elevated
        "note":          "3x TLT decay; all VIX; ⚠ watch-list only — 2yr usable history",
    },
    {
        "type":          "spread",
        "name":          "GLD Bull Put Spread",
        "alloc_key":     "GLD puts",
        "ticker":        "GLD",
        "cp":            "put",
        "short_delta":   0.30,
        "long_delta":    0.20,
        "vix_cond":      ("lt", 25),
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.06; >1.20 = elevated (sweet spot ≤1.10)
        "note":          "skip when VIX ≥ 25 (tail-risk events can spike gold both ways)",
    },
    {
        "type":          "spread",
        "name":          "USO Bull Put Spread",
        "alloc_key":     "USO puts",
        "ticker":        "USO",
        "cp":            "put",
        "short_delta":   0.25,
        "long_delta":    0.15,
        "dte_target":    30,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.08; >1.20 = elevated (sweet spot ≤1.10)
        "note":          "oil IV premium — no VIX filter; post-restructuring (Jul 2020+)",
    },
    {
        "type":          "regime_spread",
        "name":          "XLF Regime-Switching",
        "alloc_key":     "XLF regime",
        "ticker":        "XLF",
        "profit_take":   0.50,
        "fwd_vol_warn":  None,
        "note":          "4-regime switch by 50MA×VIX; $21.74 cum 2018-2025",
        "regime_strategies": {
            "Bearish_HighIV": {"structure": "bull_put_spread",  "short_d": 0.35, "long_d": 0.25},
            "Bearish_LowIV":  {"structure": "short_strangle",   "call_d":  0.20, "put_d":  0.25},
            "Bullish_HighIV": {"structure": "short_strangle",   "call_d":  0.35, "put_d":  0.40},
            "Bullish_LowIV":  {"structure": "bear_call_spread", "short_d": 0.35, "long_d": 0.25},
        },
    },
    {
        "type":          "spread",
        "name":          "SOXX Bull Put Spread",
        "alloc_key":     "SOXX puts",
        "ticker":        "SOXX",
        "cp":            "put",
        "short_delta":   0.35,
        "long_delta":    0.25,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.061; no filter needed; >1.20 = flag
        "note":          "semis secular uptrend; no VIX filter; only 1 losing year (2018)",
    },
    {
        "type":          "spread",
        "name":          "INDA Bull Put Spread",
        "alloc_key":     "INDA puts",
        "ticker":        "INDA",
        "cp":            "put",
        "short_delta":   0.25,
        "long_delta":    0.15,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg unknown; thin liquidity (~7/yr)
        "note":          "India growth tailwind — no VIX filter; enforce 25% BA strictly",
    },
    {
        "type":          "spread",
        "name":          "ASHR Bull Put Spread",
        "alloc_key":     "ASHR puts",
        "ticker":        "ASHR",
        "cp":            "put",
        "short_delta":   0.25,
        "long_delta":    0.15,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.074; condor put leg
        "note":          "condor put leg — range-bound China A-shares; no VIX filter",
    },
    {
        "type":          "spread",
        "name":          "SQQQ Bear Call Spread",
        "alloc_key":     "SQQQ calls",
        "ticker":        "SQQQ",
        "cp":            "call",
        "short_delta":   0.50,
        "long_delta":    0.40,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.30,   # avg=1.253; ≤1.30 is a useful light screen
        "note":          "3x inverse QQQ structural decay; all VIX; 2 losing years (2018, 2022)",
    },
    {
        "type":          "regime_spread",
        "name":          "QQQ Regime-Optimized",
        "alloc_key":     "QQQ puts",
        "ticker":        "QQQ",
        "profit_take":   0.50,
        "fwd_vol_warn":  None,
        "note":          "regime-specific deltas + stop rules; reduce to 1.5% when SPY also fires",
        "regime_strategies": {
            # No stop in bearish regimes — whipsaws mean stopped trades often recover
            "Bearish_HighIV": {"structure": "bull_put_spread", "short_d": 0.25, "long_d": 0.15, "stop_multiple": None},
            "Bearish_LowIV":  {"structure": "bull_put_spread", "short_d": 0.35, "long_d": 0.15, "stop_multiple": None},
            # Keep 2× stop in Bullish_HighIV — losers tend to keep going, not recover
            "Bullish_HighIV": {"structure": "bull_put_spread", "short_d": 0.45, "long_d": 0.35, "stop_multiple": 2.0},
            # No stop in Bullish_LowIV — calm market, minor edge vs stop
            "Bullish_LowIV":  {"structure": "bull_put_spread", "short_d": 0.45, "long_d": 0.35, "stop_multiple": None},
        },
    },
    {
        "type":          "spread",
        "name":          "BJ Bull Put Spread",
        "alloc_key":     "BJ puts",
        "ticker":        "BJ",
        "cp":            "put",
        "short_delta":   0.20,
        "long_delta":    0.10,
        "dte_target":    45,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  None,   # monthly-only chain; fwd_vol not computable
        "note":          "monthly-only options; 45 DTE; 94.2% win, 1 losing year (2023)",
    },
    {
        "type":          "spread",
        "name":          "ASHR Bear Call Spread",
        "alloc_key":     "ASHR calls",
        "ticker":        "ASHR",
        "cp":            "call",
        "short_delta":   0.20,
        "long_delta":    0.10,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.137; condor call leg
        "note":          "condor call leg — range-bound China A-shares; no VIX filter",
    },
    {
        "type":          "spread",
        "name":          "GEV Bull Put Spread",
        "alloc_key":     "GEV puts",
        "ticker":        "GEV",
        "cp":            "put",
        "short_delta":   0.25,
        "long_delta":    0.15,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.10,   # avg=1.083; no filter recommended but flag >1.10
        "vrp_min":       -7.83,  # skip Q1 (VRP < -7.83 pp): 70.0% win / +2.2% avg ROC vs 91.4% / +13.7% above
        "note":          "PROVISIONAL (2yr data); power infra/AI tailwind; 94.4% win; 0.10Δ wing",
    },
    {
        "type":          "spread",
        "name":          "CLS Bull Put Spread",
        "alloc_key":     "CLS puts",
        "ticker":        "CLS",
        "cp":            "put",
        "short_delta":   0.25,
        "long_delta":    0.15,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.156; no filter recommended but flag >1.20
        "note":          "PROVISIONAL (2yr data); AI EMS/hyperscaler infra; 93.4% win; 0.10Δ wing",
    },
    {
        "type":          "regime_spread",
        "name":          "XLE Regime-Gated",
        "alloc_key":     "XLE puts",
        "ticker":        "XLE",
        "profit_take":   0.50,
        "fwd_vol_warn":  None,
        "note":          "Bearish_HighIV only (below 50MA + VIX≥20); +35.5% ROC 84.6% win ~9wks/yr",
        "regime_strategies": {
            "Bearish_HighIV": {"structure": "bull_put_spread", "short_d": 0.35, "long_d": 0.25},
            "Bearish_LowIV":  {"structure": "skip"},
            "Bullish_HighIV": {"structure": "skip"},
            "Bullish_LowIV":  {"structure": "skip"},
        },
    },
    {
        "type":          "regime_spread",
        "name":          "SPY Regime-Switching",
        "alloc_key":     "SPY regime",
        "ticker":        "SPY",
        "profit_take":   0.50,
        "fwd_vol_warn":  None,
        "note":          "VIX≥20→bull put spread (no stop); Bear+LowIV→long straddle; Bull+LowIV→skip; reduce to 1.5% when QQQ also fires",
        "regime_strategies": {
            # No stop in either put spread regime — SPY mean-reverts even in high-IV; stop fires then recovers
            "Bearish_HighIV": {"structure": "bull_put_spread", "short_d": 0.25, "long_d": 0.15, "stop_multiple": None},
            "Bearish_LowIV":  {"structure": "long_straddle",   "delta":   0.50},
            "Bullish_HighIV": {"structure": "bull_put_spread", "short_d": 0.45, "long_d": 0.35, "stop_multiple": None},
            "Bullish_LowIV":  {"structure": "skip"},
        },
    },
    {
        "type":          "straddle",
        "name":          "UUP ATM Short Straddle",
        "alloc_key":     "UUP straddle",
        "ticker":        "UUP",
        "profit_take":   0.50,
        "max_ba_pct":    0.35,
        "fwd_vol_warn":  None,
        "note":          "ATM only (OTM illiquid); 73.1% win +17.4% ROC; verify chain in broker",
    },
    {
        "type":          "spread",
        "name":          "XOP Bull Put Spread",
        "alloc_key":     "XOP puts",
        "ticker":        "XOP",
        "cp":            "put",
        "short_delta":   0.35,
        "long_delta":    0.25,
        "dte_target":    60,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # E&P higher beta to crude; flag >1.20
        "note":          "PROVISIONAL; E&P upstream oil/gas; 60 DTE; +5.44% ROC 81.5% win; All VIX",
    },
    # ── Calendar strategies ───────────────────────────────────────────────────
    # RETIRED 2026-09-15 (calendar path study, data/studies/calendar_path_study.md, 5,920 real-bid/ask calendars):
    #   GLD / XLU / XLV / XLP put calendars -- entry bid-ask 18-470% of the debit; hold-to-expiry ROC after costs
    #   GLD -3%, XLV -16/-25%, XLF -22/-24%, XLP -28/-40%, TLT -15% (XLU/XLE: single-digit trade counts). The Sept
    #   review had already found them net-negative on the cost model; the paths confirm it. Kept: the liquid index ETFs.
]

DTE_TARGET     = 20
DTE_TOL        = 5
MAX_DELTA_ERR  = 0.08
MAX_SPREAD_PCT = 0.25   # max (ask-bid)/mid on the short leg

# ── Tier lookup tables ────────────────────────────────────────────────────────

TIER_MAP: dict[str, str] = {
    "UVXY Bear Call Spread":    "C",
    "UVXY Short Put":           "C",
    "UVIX Bear Call Spread":    "C",
    "TLT Bear Call Spread":     "C",
    "TMF Bear Call Spread":     "P",
    "GLD Bull Put Spread":      "C",
    "USO Bull Put Spread":      "C",
    "SOXX Bull Put Spread":     "C",
    "INDA Bull Put Spread":     "A",
    "ASHR Bull Put Spread":     "C",
    "SQQQ Bear Call Spread":    "C",
    "BJ Bull Put Spread":       "B",
    "ASHR Bear Call Spread":    "C",
    "GEV Bull Put Spread":      "P",
    "CLS Bull Put Spread":      "P",
    "UUP ATM Short Straddle":   "C",
    "XOP Bull Put Spread":      "P",
}

# For regime strategies, tier depends on which regime fires
REGIME_TIER_MAP: dict[str, dict[str, str]] = {
    "XLF Regime-Switching": {
        "Bearish_HighIV": "B", "Bearish_LowIV": "C",
        "Bullish_HighIV": "C", "Bullish_LowIV": "C",
    },
    "QQQ Regime-Optimized": {
        "Bearish_HighIV": "B", "Bearish_LowIV": "A",
        "Bullish_HighIV": "A", "Bullish_LowIV": "B",
    },
    "XLE Regime-Gated": {
        "Bearish_HighIV": "A", "Bearish_LowIV": "C",
        "Bullish_HighIV": "C", "Bullish_LowIV": "C",
    },
    "SPY Regime-Switching": {
        "Bearish_HighIV": "B", "Bearish_LowIV": "A",
        "Bullish_HighIV": "B", "Bullish_LowIV": "C",
    },
}


# ── Pure helpers (no I/O) ─────────────────────────────────────────────────────

def _dte(exp_str: str, today: date) -> int:
    return (date.fromisoformat(exp_str) - today).days


def find_target_expiry(
    expirations: list[str], today: date, dte_target: int = DTE_TARGET,
    dte_tol: int = DTE_TOL,
) -> Optional[str]:
    """Closest expiry to dte_target within ±dte_tol; None if none qualify."""
    best: Optional[str] = None
    best_err = dte_tol + 1
    for exp_str in expirations:
        err = abs(_dte(exp_str, today) - dte_target)
        if err <= dte_tol and err < best_err:
            best_err = err
            best = exp_str
    return best


def find_long_expiry(
    expirations: list[str],
    short_exp: str,
    min_gap: int,
    max_gap: int,
) -> Optional[str]:
    """First expiry whose gap from short_exp is in [min_gap, max_gap] days."""
    short_date = date.fromisoformat(short_exp)
    for exp_str in expirations:
        gap = (date.fromisoformat(exp_str) - short_date).days
        if min_gap <= gap <= max_gap:
            return exp_str
    return None


def find_by_delta(
    contracts: list[dict],
    target_unsigned: float,
    cp: str,
    max_err: float = MAX_DELTA_ERR,
) -> Optional[dict]:
    """Contract closest to target delta, within max_err; None if no match."""
    signed_target = target_unsigned if cp == "call" else -target_unsigned
    best: Optional[dict] = None
    best_err = max_err + 1.0
    for c in contracts:
        if c.get("option_type") != cp:
            continue
        delta = (c.get("greeks") or {}).get("delta")
        if delta is None:
            continue
        err = abs(float(delta) - signed_target)
        if err <= max_err and err < best_err:
            best_err = err
            best = c
    return best


def ba_pct(contract: dict) -> Optional[float]:
    """(ask - bid) / mid; None if quotes are absent."""
    bid = contract.get("bid") or 0.0
    ask = contract.get("ask") or 0.0
    if bid <= 0 or ask <= 0:
        return None
    mid = (bid + ask) / 2.0
    return (ask - bid) / mid if mid > 0 else None


def mid_price(contract: dict) -> float:
    bid = contract.get("bid") or 0.0
    ask = contract.get("ask") or 0.0
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    return float(contract.get("last") or 0.0)


def vix_check(vix: float, cond) -> tuple[bool, str]:
    """(passes, description) for the VIX filter."""
    if cond is None:
        return True, "no filter — always enter"
    op, threshold = cond
    if op == "lt":
        ok = vix < threshold
        sym = "<" if ok else "≥"
        return ok, f"VIX {vix:.2f} {sym} {threshold}"
    else:  # "gte"
        ok = vix >= threshold
        sym = "≥" if ok else "<"
        return ok, f"VIX {vix:.2f} {sym} {threshold}"


def fmt_leg(c: dict, label: str, cp: str, target_delta: float) -> str:
    strike = c.get("strike", 0.0)
    bid    = c.get("bid") or 0.0
    ask    = c.get("ask") or 0.0
    m      = mid_price(c)
    delta  = (c.get("greeks") or {}).get("delta")
    sp     = ba_pct(c)
    cp_c   = "C" if cp == "call" else "P"
    sp_str = f"{sp * 100:.1f}%" if sp is not None else " n/a "
    sp_tag = "✓" if sp is not None and sp <= MAX_SPREAD_PCT else "✗"
    d_str  = f"{float(delta):+.3f}" if delta is not None else "  n/a"
    return (
        f"  {label:<6}  {cp_c}"
        f"  ${strike:>7.2f}"
        f"  bid ${bid:>5.2f}  ask ${ask:>5.2f}  mid ${m:>5.2f}"
        f"  Δ {d_str} (tgt {target_delta:.2f})  BA {sp_str:>6} {sp_tag}"
    )


# ── Forward vol factor helpers ────────────────────────────────────────────────

def _put_iv(mid: float, strike: float, dte: int) -> Optional[float]:
    """BS implied vol for a put using S≈K (ATM approximation)."""
    T = dte / 365.0
    if T <= 0 or mid <= 0 or strike <= 0:
        return None
    try:
        return _bs_implied_vol(price=mid, S=strike, K=strike, T=T, r=0.04, q=0.0, opt_type="put")
    except Exception:
        return None


def _atm_put(chain: list[dict]) -> Optional[dict]:
    """Put in chain closest to |Δ| = 0.50 with positive bid."""
    puts = [c for c in chain
            if c.get("option_type") == "put" and (c.get("bid") or 0) > 0]
    if not puts:
        return None
    return min(puts, key=lambda c: abs(
        abs((c.get("greeks") or {}).get("delta") or 0) - 0.50
    ))


def fwd_vol_factor(
    near_chain: list[dict],
    far_chain:  list[dict],
    near_dte:   int,
    far_dte:    int,
) -> Optional[float]:
    """
    Compute fwd_vol_factor = sigma_fwd / near_iv using ATM puts from both chains.
    Returns None  if data is insufficient.
    Returns float("nan") if var_fwd ≤ 0 (extreme backwardation — always favorable).
    """
    np_ = _atm_put(near_chain)
    fp_ = _atm_put(far_chain)
    if np_ is None or fp_ is None:
        return None

    near_iv = _put_iv(mid_price(np_), np_.get("strike", 0.0), near_dte)
    far_iv  = _put_iv(mid_price(fp_), fp_.get("strike", 0.0), far_dte)
    if near_iv is None or far_iv is None or near_iv <= 0:
        return None

    T1, T2 = near_dte / 365.0, far_dte / 365.0
    dT = T2 - T1
    if dT <= 0:
        return None
    var_fwd = (far_iv**2 * T2 - near_iv**2 * T1) / dT
    if var_fwd <= 0:
        return float("nan")  # extreme backwardation
    return (var_fwd ** 0.5) / near_iv


def fmt_fwd_vol(factor: Optional[float], warn_threshold: float) -> str:
    """Format fwd_vol_factor line with contextual warning."""
    if factor is None:
        return "  fwd_vol_factor: n/a  (insufficient chain data)"
    if math.isnan(factor):
        return "  fwd_vol_factor: NaN  (extreme backwardation — most favorable)"
    if factor > 1.50:
        tag = "⚠⚠ HIGH CONTANGO — vol expected to spike in forward window"
    elif factor > warn_threshold:
        tag = f"⚠ elevated (sweet spot ≤{warn_threshold:.2f}) — proceed with awareness"
    else:
        tag = "✓"
    return f"  fwd_vol_factor: {factor:.3f}  {tag}"


# ── MA50 helper for regime classification ────────────────────────────────────

async def refresh_stock_cache(client: TradierClient, ticker: str, today: date) -> None:
    """Bring data/cache/<T>_stock.parquet up to date from Tradier daily history (2026-09-15: QQQ/SPY/XLE caches had
    stopped in March, so every 50MA regime call and RV20 on them was computed on six-month-old closes)."""
    from lib.tradier.get_daily_history import get_daily_history
    path = Path("data") / "cache" / f"{ticker}_stock.parquet"
    try:
        df = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=["trade_date", "close"])
        last = pd.to_datetime(df["trade_date"]).max().date() if len(df) else today - timedelta(days=400)
        if last >= today - timedelta(days=1):
            return
        d = await get_daily_history(ticker, last - timedelta(days=3), today, client=client)
        if d is None or not len(d):
            return
        d = d.reset_index() if "date" not in d.columns else d
        d = d.rename(columns={"index": "date"})
        new = pd.DataFrame({"trade_date": pd.to_datetime(d["date"]).dt.date})
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns and col in d.columns:
                new[col] = d[col].values
        if "close" not in new.columns:
            new["close"] = d["close"].values
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        out = pd.concat([df, new[[c for c in new.columns if c in df.columns or c in ("trade_date", "close")]]], ignore_index=True)
        out = out.drop_duplicates("trade_date", keep="last").sort_values("trade_date")
        out.to_parquet(path, index=False)
        print(f"  (stock cache {ticker}: {last} -> {out.trade_date.max()})")
    except Exception as exc:  # noqa: BLE001 -- a stale cache is better than a crash; the MA line shows the date
        print(f"  (stock cache {ticker}: refresh failed: {type(exc).__name__})")


def get_ma50(ticker: str) -> Optional[float]:
    """Load 50-day simple MA from cached stock parquet. Returns None on any failure."""
    path = Path("data") / "cache" / f"{ticker}_stock.parquet"
    try:
        df = pd.read_parquet(path)
        df = df.sort_values("trade_date")
        if len(df) < 50:
            return None
        return float(df["close"].iloc[-50:].mean())
    except Exception:
        return None


def compute_vrp(
    ticker: str,
    chain:  list[dict],
    expiry: Optional[str],
    today:  date,
) -> Optional[float]:
    """
    Compute VRP = ATM IV30 − RV20 in percentage points.
    Uses cached stock parquet for RV20 and the live option chain for ATM IV.
    Returns None if data is insufficient.
    """
    # RV20 from parquet (21 closes → 20 log returns)
    path = Path("data") / "cache" / f"{ticker}_stock.parquet"
    try:
        df = pd.read_parquet(path)
        df = df.sort_values("trade_date")
        closes = df["close"].tolist()
        if len(closes) < 21:
            return None
        tail = closes[-21:]
        log_rets = [math.log(tail[i + 1] / tail[i]) for i in range(20)]
        mean_lr  = sum(log_rets) / 20
        variance = sum((r - mean_lr) ** 2 for r in log_rets) / 19   # ddof=1
        rv20 = math.sqrt(variance) * math.sqrt(252)
    except Exception:
        return None

    # ATM IV from chain at target expiry
    if not chain or not expiry:
        return None
    dte = _dte(expiry, today)
    if dte <= 0:
        return None
    atm = _atm_put(chain)
    if atm is None:
        return None
    m = mid_price(atm)
    K = atm.get("strike", 0.0)
    T = dte / 365.0
    try:
        iv30 = _bs_implied_vol(price=m, S=K, K=K, T=T, r=0.04, q=0.0, opt_type="put")
    except Exception:
        return None
    if iv30 is None or iv30 <= 0:
        return None

    return (iv30 - rv20) * 100   # percentage points


# Empirical breach odds for a short put strike placed N ADR below spot, leaders 2019-2026, 19-session hold
# (strike-placement backtest 2026-09-18; identical across extension buckets -- only the cushion matters).
_BREACH_TABLE = [(1.0, 33.0), (1.5, 27.0), (1.75, 24.0), (2.0, 21.0), (2.5, 17.0), (3.0, 13.0)]


def _breach_odds(cushion_adr: float) -> float:
    xs = [c for c, _ in _BREACH_TABLE]; ys = [p for _, p in _BREACH_TABLE]
    if cushion_adr <= xs[0]:
        return min(50.0, ys[0] + (xs[0] - cushion_adr) * 18)          # ~42% at 0.5 ADR
    if cushion_adr >= xs[-1]:
        return max(5.0, ys[-1] - (cushion_adr - xs[-1]) * 6)
    for (x0, y0), (x1, y1) in zip(_BREACH_TABLE, _BREACH_TABLE[1:]):
        if x0 <= cushion_adr <= x1:
            return y0 + (y1 - y0) * (cushion_adr - x0) / (x1 - x0)
    return ys[-1]


def price_the_odds(ticker: str, spot: float, short_strike: float, credit: float, width: float, chain: list[dict], expiry: Optional[str], today: date) -> str:
    """One line per credit spread: cushion in ADR -> empirical breach odds -> break-even credit vs the quoted credit,
    plus ATM IV vs RV20. This is the comparison that separated MPC (IV/RV 1.4, 26% of width, ~24% odds) from
    PANW/CRWD (IV/RV 0.78, 26-30%, ~30% odds) on 2026-09-18. Table is from single names; read ETF rows loosely."""
    path = Path("data") / "cache" / f"{ticker}_stock.parquet"
    try:
        df = pd.read_parquet(path).sort_values("trade_date")
        if {"high", "low"} <= set(df.columns) and len(df) >= 21:
            adr = float(((df["high"] / df["low"] - 1) * 100).tail(20).mean())
        else:
            adr = float(pd.Series(df["close"].values).pct_change().abs().tail(20).mean() * 100 * 1.6)   # crude fallback
    except Exception:
        return "  Odds check:  n/a (no stock cache)"
    if not adr or spot <= 0 or width <= 0:
        return "  Odds check:  n/a"
    cushion = (spot / short_strike - 1) * 100 / adr if short_strike < spot else -(short_strike / spot - 1) * 100 / adr
    odds = _breach_odds(max(cushion, 0.01)); be = odds / (100 - odds) * 100
    quoted = credit / width * 100
    tag = "RICH" if quoted >= be * 1.15 else ("THIN" if quoted < be * 0.85 else "FAIR")
    vrp = compute_vrp(ticker, chain, expiry, today)
    ivrv = ""
    if vrp is not None:
        try:
            closes = pd.read_parquet(path).sort_values("trade_date")["close"].tail(21).tolist()
            lr = [math.log(closes[i + 1] / closes[i]) for i in range(20)]; mu = sum(lr) / 20
            rv20 = math.sqrt(sum((r - mu) ** 2 for r in lr) / 19) * math.sqrt(252) * 100
            iv30 = rv20 + vrp; ivrv = f"  |  ATM IV {iv30:.0f}% vs RV20 {rv20:.0f}% (ratio {iv30 / rv20:.2f}{'; implied BELOW realized' if iv30 < rv20 else ''})"
        except Exception:
            ivrv = f"  |  IV - RV {vrp:+.1f} pp"
    return (f"  Odds check:  short strike {cushion:.1f} ADR below spot -> ~{odds:.0f}% breach by expiry (leaders 2019-26) -> break-even credit "
            f"~{be:.0f}% of width; quoted {quoted:.0f}% = {tag}{ivrv}")


# ── Regime-switching screener ─────────────────────────────────────────────────

def screen_regime_spread(
    strat:  dict,
    chain:  list[dict],
    expiry: Optional[str],
    vix:    float,
    today:  date,
    spot:   Optional[float],
    ma50:   Optional[float],
) -> dict:
    """Screen a regime-switching strategy. Classifies 50MA×VIX regime, selects sub-strategy."""
    ticker      = strat["ticker"]
    profit_take = strat["profit_take"]
    lines: list[str] = []

    # 1. Regime classification
    if spot is None or ma50 is None:
        lines.append("  Cannot classify regime: spot or MA50 unavailable")
        return {"enter": False, "lines": lines, "summary": "SKIP  (regime data unavailable)"}

    trend    = "Bullish" if spot > ma50 else "Bearish"
    iv_class = "HighIV"  if vix >= 20   else "LowIV"
    regime   = f"{trend}_{iv_class}"

    lines.append(f"  {ticker} ${spot:.2f} vs 50MA ${ma50:.2f} → {trend}")
    lines.append(f"  VIX {vix:.2f} → {iv_class}")
    lines.append(f"  Regime: {regime}")

    rs_map = strat["regime_strategies"]
    if regime not in rs_map:
        lines.append(f"  No strategy configured for {regime}")
        return {"enter": False, "lines": lines, "summary": f"SKIP  ({regime} — unconfigured)"}

    rs        = rs_map[regime]
    structure = rs["structure"]

    if structure == "skip":
        lines.append(f"  {regime}: no edge in this regime — skip")
        return {"enter": False, "lines": lines, "summary": f"SKIP  ({regime})"}

    # 2. Expiry
    if not expiry:
        lines.append(f"  No expiry within {DTE_TARGET}±{DTE_TOL} DTE")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no valid expiry)"}
    dte = _dte(expiry, today)
    lines.append(f"  Expiry: {expiry}  ({dte} DTE)")

    if not chain:
        lines.append("  No option chain data returned")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)"}

    # 3a. Credit spread (bull put or bear call)
    if structure in ("bull_put_spread", "bear_call_spread"):
        cp      = "put"  if structure == "bull_put_spread" else "call"
        short_d = rs["short_d"]
        long_d  = rs["long_d"]

        short = find_by_delta(chain, short_d, cp)
        if short is None:
            lines.append(f"  Short {short_d:.2f}Δ {cp}: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no short leg)"}
        lines.append(fmt_leg(short, "Short", cp, short_d))

        sp = ba_pct(short)
        if sp is None or sp > MAX_SPREAD_PCT:
            sp_str = f"{sp * 100:.1f}%" if sp is not None else "n/a"
            lines.append(f"  Short leg BA too wide: {sp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (short BA {sp_str})"}

        long = find_by_delta(chain, long_d, cp)
        if long is None:
            lines.append(f"  Long  {long_d:.2f}Δ {cp}: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no long leg)"}
        lines.append(fmt_leg(long, "Long", cp, long_d))

        lsp = ba_pct(long)
        if lsp is None or lsp > MAX_SPREAD_PCT:
            lsp_str = f"{lsp * 100:.1f}%" if lsp is not None else "n/a"
            lines.append(f"  Long leg BA too wide: {lsp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (long BA {lsp_str})"}

        lines.append("")
        short_mid = mid_price(short)
        long_mid  = mid_price(long)
        credit    = short_mid - long_mid
        s_strike  = short.get("strike", 0.0)
        l_strike  = long.get("strike", 0.0)
        width     = (l_strike - s_strike) if cp == "call" else (s_strike - l_strike)

        if credit <= 0 or width <= 0:
            lines.append(f"  Invalid spread — credit ${credit:.3f}  width ${width:.2f}")
            return {"enter": False, "lines": lines, "summary": "SKIP  (invalid spread)"}

        max_loss   = width - credit
        credit_pct = credit / width * 100
        take_at    = credit * (1.0 - profit_take)
        keep       = credit * profit_take
        cp_c       = "C" if cp == "call" else "P"
        s_delta    = (short.get("greeks") or {}).get("delta")
        l_delta    = (long.get("greeks")  or {}).get("delta")
        s_d_str    = f"{abs(float(s_delta)):.2f}Δ" if s_delta is not None else "?Δ"
        l_d_str    = f"{abs(float(l_delta)):.2f}Δ" if l_delta is not None else "?Δ"

        lines.append(f"  Net credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)")
        lines.append(f"  Spread:      ${s_strike:.2f}/${l_strike:.2f}  width ${width:.2f}  credit/width {credit_pct:.1f}%")
        lines.append(f"  Max loss:    ${max_loss:.3f}/shr  (${max_loss * 100:.2f}/contract)")
        if cp == "put":
            lines.append(price_the_odds(strat["ticker"], spot, s_strike, credit, width, chain, expiry, today))
        stop_mult = rs.get("stop_multiple", 2.0)
        lines.append("  Management: HOLD to expiry -- no profit take, no stop (etf_put_spread_study 2026-09-10: 50%-take / 2x-stop = -4.3%/trade, t -5.4; paid_to_wait: closing on the break -8.3% net); size to the max loss")
        if stop_mult is None:
            lines.append(f"  Stop loss:   NONE — hold to profit take or expiry (no stop this regime)"  )
        else:
            lines.append(f"  Stop loss:   close spread at ≥ ${credit * stop_mult:.3f}  ({stop_mult:.0f}× credit)")

        summary = (
            f"{regime}  short ${s_strike:.2f}{cp_c}({s_d_str}) / buy ${l_strike:.2f}{cp_c}({l_d_str})"
            f"   net ${credit:.3f}cr   width ${width:.2f}"
        )
        return {"enter": True, "lines": lines, "summary": summary,
                "max_loss_per_contract": max_loss * 100, "active_regime": regime}

    # 3b. Short strangle
    elif structure == "short_strangle":
        call_d = rs["call_d"]
        put_d  = rs["put_d"]

        short_call = find_by_delta(chain, call_d, "call")
        if short_call is None:
            lines.append(f"  Short {call_d:.2f}Δ call: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no short call)"}
        lines.append(fmt_leg(short_call, "Call", "call", call_d))

        csp = ba_pct(short_call)
        if csp is None or csp > MAX_SPREAD_PCT:
            csp_str = f"{csp * 100:.1f}%" if csp is not None else "n/a"
            lines.append(f"  Call leg BA too wide: {csp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (call BA {csp_str})"}

        short_put = find_by_delta(chain, put_d, "put")
        if short_put is None:
            lines.append(f"  Short {put_d:.2f}Δ put: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no short put)"}
        lines.append(fmt_leg(short_put, "Put", "put", put_d))

        psp = ba_pct(short_put)
        if psp is None or psp > MAX_SPREAD_PCT:
            psp_str = f"{psp * 100:.1f}%" if psp is not None else "n/a"
            lines.append(f"  Put leg BA too wide: {psp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (put BA {psp_str})"}

        lines.append("")
        call_mid = mid_price(short_call)
        put_mid  = mid_price(short_put)
        credit   = call_mid + put_mid
        c_strike = short_call.get("strike", 0.0)
        p_strike = short_put.get("strike", 0.0)

        if credit <= 0:
            lines.append(f"  Invalid strangle — combined credit ${credit:.3f}")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no credit)"}

        take_at = credit * (1.0 - profit_take)
        keep    = credit * profit_take
        c_delta = (short_call.get("greeks") or {}).get("delta")
        p_delta = (short_put.get("greeks")  or {}).get("delta")
        c_d_str = f"{abs(float(c_delta)):.2f}Δ" if c_delta is not None else "?Δ"
        p_d_str = f"{abs(float(p_delta)):.2f}Δ" if p_delta is not None else "?Δ"

        lines.append(f"  Combined credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)")
        lines.append(f"  Strikes:          call ${c_strike:.2f} / put ${p_strike:.2f}")
        lines.append("  Management: HOLD to expiry -- no profit take, no stop (etf_put_spread_study 2026-09-10: 50%-take / 2x-stop = -4.3%/trade, t -5.4; paid_to_wait: closing on the break -8.3% net); size to the max loss")
        lines.append(f"  Stop loss:   close strangle at ≥ ${credit * 2:.3f}  (2× credit)")

        summary = (
            f"{regime}  short ${c_strike:.2f}C({c_d_str}) / short ${p_strike:.2f}P({p_d_str})"
            f"   combined ${credit:.3f}cr"
        )
        return {"enter": True, "lines": lines, "summary": summary,
                "max_loss_per_contract": None, "active_regime": regime}  # naked — undefined max loss

    # 3c. Long straddle (debit — buy ATM call + put)
    elif structure == "long_straddle":
        delta = rs.get("delta", 0.50)

        long_call = find_by_delta(chain, delta, "call")
        if long_call is None:
            lines.append(f"  Long {delta:.2f}Δ call: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no call leg)"}
        lines.append(fmt_leg(long_call, "Call (buy)", "call", delta))

        csp = ba_pct(long_call)
        if csp is None or csp > MAX_SPREAD_PCT:
            csp_str = f"{csp * 100:.1f}%" if csp is not None else "n/a"
            lines.append(f"  Call leg BA too wide: {csp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (call BA {csp_str})"}

        long_put = find_by_delta(chain, delta, "put")
        if long_put is None:
            lines.append(f"  Long {delta:.2f}Δ put: no match within ±{MAX_DELTA_ERR}Δ")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no put leg)"}
        lines.append(fmt_leg(long_put, "Put (buy)", "put", delta))

        psp = ba_pct(long_put)
        if psp is None or psp > MAX_SPREAD_PCT:
            psp_str = f"{psp * 100:.1f}%" if psp is not None else "n/a"
            lines.append(f"  Put leg BA too wide: {psp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines, "summary": f"SKIP  (put BA {psp_str})"}

        lines.append("")
        call_mid = mid_price(long_call)
        put_mid  = mid_price(long_put)
        debit    = call_mid + put_mid
        c_strike = long_call.get("strike", 0.0)
        p_strike = long_put.get("strike", 0.0)

        if debit <= 0:
            lines.append(f"  Invalid straddle — combined debit ${debit:.3f}")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no debit)"}

        take_at  = debit * (1.0 + profit_take)   # close when value rises to +50%
        stop_at  = debit * 0.60                   # stop when value falls to 60% of debit (-40%)
        c_delta  = (long_call.get("greeks") or {}).get("delta")
        p_delta  = (long_put.get("greeks")  or {}).get("delta")
        c_d_str  = f"{abs(float(c_delta)):.2f}Δ" if c_delta is not None else "?Δ"
        p_d_str  = f"{abs(float(p_delta)):.2f}Δ" if p_delta is not None else "?Δ"

        lines.append(f"  Total debit:    ${debit:.3f}/shr  (${debit * 100:.2f}/contract)")
        lines.append(f"  Strikes:        call ${c_strike:.2f} / put ${p_strike:.2f}")
        lines.append(f"  Max loss:       ${debit:.3f}/shr  (${debit * 100:.2f}/contract)  — fully defined")
        lines.append("  Management:     HOLD to expiry; sell a SPIKE into strength (structure >= +100% within days); -50% stop (long_straddle_playbook: no profit cap -- capping at 100% drops Sharpe +0.17 -> -0.04)")
        lines.append(f"  Stop loss:      close when straddle value ≤ ${stop_at:.3f}  (−40% of debit)")

        summary = (
            f"{regime}  buy ${c_strike:.2f}C({c_d_str}) / buy ${p_strike:.2f}P({p_d_str})"
            f"   debit ${debit:.3f}   max loss ${debit * 100:.2f}/contract"
        )
        return {"enter": True, "lines": lines, "summary": summary,
                "max_loss_per_contract": debit * 100, "active_regime": regime}

    lines.append(f"  Unknown structure: {structure}")
    return {"enter": False, "lines": lines, "summary": f"SKIP  (unknown structure)"}


# ── ATM short straddle screener ───────────────────────────────────────────────

def screen_straddle(
    strat:  dict,
    chain:  list[dict],
    expiry: Optional[str],
    today:  date,
) -> dict:
    """Screen an ATM short straddle. Uses strict BA filter (max_ba_pct). Returns enter/lines/summary."""
    profit_take = strat["profit_take"]
    max_ba      = strat.get("max_ba_pct", MAX_SPREAD_PCT)
    lines: list[str] = []

    # 1. Expiry
    if not expiry:
        lines.append(f"  No expiry within {DTE_TARGET}±{DTE_TOL} DTE")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no valid expiry)"}
    dte = _dte(expiry, today)
    lines.append(f"  Expiry: {expiry}  ({dte} DTE)")

    if not chain:
        lines.append("  No option chain data returned")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)"}

    # 2. ATM put (closest to 0.50Δ)
    atm_put = _atm_put(chain)
    if atm_put is None:
        lines.append("  No ATM put with positive bid found")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no ATM put)"}

    strike = atm_put["strike"]

    # 3. Matching call at same strike
    atm_call = next(
        (c for c in chain
         if c.get("option_type") == "call" and c["strike"] == strike and (c.get("bid") or 0) > 0),
        None,
    )
    if atm_call is None:
        lines.append(f"  No call at ATM strike ${strike:.2f} with positive bid")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no ATM call)"}

    # 4. BA checks (strict limit for thinly-traded underlyings)
    put_ba = ba_pct(atm_put)
    if put_ba is None or put_ba > max_ba:
        put_ba_str = f"{put_ba * 100:.1f}%" if put_ba is not None else "n/a"
        lines.append(f"  Put BA too wide: {put_ba_str} > {max_ba * 100:.0f}% (ATM limit for this ticker)")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (put BA {put_ba_str})"}

    call_ba = ba_pct(atm_call)
    if call_ba is None or call_ba > max_ba:
        call_ba_str = f"{call_ba * 100:.1f}%" if call_ba is not None else "n/a"
        lines.append(f"  Call BA too wide: {call_ba_str} > {max_ba * 100:.0f}% (ATM limit for this ticker)")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (call BA {call_ba_str})"}

    # 5. Economics
    put_mid  = mid_price(atm_put)
    call_mid = mid_price(atm_call)
    credit   = put_mid + call_mid

    if credit <= 0:
        lines.append(f"  Combined credit ${credit:.3f} — no edge")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no credit)"}

    take_at = credit * (1.0 - profit_take)
    keep    = credit * profit_take
    p_delta = (atm_put.get("greeks")  or {}).get("delta")
    c_delta = (atm_call.get("greeks") or {}).get("delta")
    p_d_str = f"{abs(float(p_delta)):.2f}Δ" if p_delta is not None else "?Δ"
    c_d_str = f"{abs(float(c_delta)):.2f}Δ" if c_delta is not None else "?Δ"

    lines.append(fmt_leg(atm_put,  "Put",  "put",  0.50))
    lines.append(fmt_leg(atm_call, "Call", "call", 0.50))
    lines.append("")
    lines.append(f"  Combined credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)")
    lines.append(f"  ATM strike:       ${strike:.2f}")
    lines.append("  Management: HOLD to expiry -- no profit take, no stop (etf_put_spread_study 2026-09-10: 50%-take / 2x-stop = -4.3%/trade, t -5.4; paid_to_wait: closing on the break -8.3% net); size to the max loss")
    lines.append(f"  Stop loss:   close straddle at ≥ ${credit * 2:.3f}  (2× credit)")

    summary = (
        f"${strike:.2f} straddle  P({p_d_str}) + C({c_d_str})"
        f"   combined ${credit:.3f}cr"
    )
    return {"enter": True, "lines": lines, "summary": summary,
            "max_loss_per_contract": None}  # stop at 2× credit; no defined max


# ── Per-strategy screening ────────────────────────────────────────────────────

def screen_spread(
    strat:   dict,
    chain:   list[dict],
    expiry:  Optional[str],
    vix:     float,
    today:   date,
) -> dict:
    """Screen a credit spread or naked short strategy. Returns enter/lines/summary."""
    cp          = strat["cp"]
    short_delta = strat["short_delta"]
    long_delta  = strat.get("long_delta")
    profit_take = strat["profit_take"]
    lines: list[str] = []

    # 1. VIX gate
    ok, vix_desc = vix_check(vix, strat["vix_cond"])
    lines.append(f"  {vix_desc}")
    if not ok:
        return {"enter": False, "lines": lines,
                "summary": f"SIT OUT   ({vix_desc})"}

    # 1b. VRP gate (optional; only if vrp_min is configured on the strategy)
    vrp_min = strat.get("vrp_min")
    if vrp_min is not None:
        vrp = compute_vrp(strat["ticker"], chain, expiry, today)
        if vrp is None:
            lines.append(f"  VRP: n/a (data unavailable) — proceeding without filter")
        else:
            lines.append(f"  VRP: {vrp:+.1f} pp  (IV30 − RV20)  filter: VRP ≥ {vrp_min:+.1f} pp")
            if vrp < vrp_min:
                return {"enter": False, "lines": lines,
                        "summary": f"SIT OUT   (VRP {vrp:+.1f} pp < {vrp_min:+.1f} pp — Q1 skip)"}

    # 2. Expiry
    if not expiry:
        lines.append(f"  No expiry within {DTE_TARGET}±{DTE_TOL} DTE")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no valid expiry)"}
    dte = _dte(expiry, today)
    lines.append(f"  Expiry: {expiry}  ({dte} DTE)")

    # 3. Chain guard
    if not chain:
        lines.append("  No option chain data returned")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)"}

    # 4. Short leg
    short = find_by_delta(chain, short_delta, cp)
    if short is None:
        lines.append(
            f"  Short {short_delta:.2f}Δ {cp}:  no match within ±{MAX_DELTA_ERR}Δ"
            f"  (greeks may be unavailable outside market hours)"
        )
        return {"enter": False, "lines": lines, "summary": "SKIP  (no short leg match)"}
    lines.append(fmt_leg(short, "Short", cp, short_delta))

    sp = ba_pct(short)
    if sp is None or sp > MAX_SPREAD_PCT:
        sp_str = f"{sp * 100:.1f}%" if sp is not None else "n/a"
        lines.append(f"  Short leg bid-ask too wide: {sp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines,
                "summary": f"SKIP  (short leg BA {sp_str})"}

    # 5. Long leg (spreads only)
    long: Optional[dict] = None
    if long_delta is not None:
        long = find_by_delta(chain, long_delta, cp)
        if long is None:
            lines.append(
                f"  Long  {long_delta:.2f}Δ {cp}:  no match within ±{MAX_DELTA_ERR}Δ"
            )
            return {"enter": False, "lines": lines, "summary": "SKIP  (no long leg match)"}
        lines.append(fmt_leg(long, "Long", cp, long_delta))

        lsp = ba_pct(long)
        if lsp is None or lsp > MAX_SPREAD_PCT:
            lsp_str = f"{lsp * 100:.1f}%" if lsp is not None else "n/a"
            lines.append(f"  Long leg bid-ask too wide: {lsp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
            return {"enter": False, "lines": lines,
                    "summary": f"SKIP  (long leg BA {lsp_str})"}

    # 6. Economics
    lines.append("")
    short_mid = mid_price(short)

    if long is not None:
        long_mid = mid_price(long)
        credit   = short_mid - long_mid
        s_strike = short.get("strike", 0.0)
        l_strike = long.get("strike", 0.0)
        width = (l_strike - s_strike) if cp == "call" else (s_strike - l_strike)

        if credit <= 0 or width <= 0:
            lines.append(f"  Invalid spread — credit ${credit:.3f}  width ${width:.2f}")
            return {"enter": False, "lines": lines, "summary": "SKIP  (invalid spread)"}

        max_loss   = width - credit
        credit_pct = credit / width * 100
        take_at    = credit * (1.0 - profit_take)
        keep       = credit * profit_take

        lines.append(f"  Net credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)")
        lines.append(f"  Spread:      ${s_strike:.2f}/${l_strike:.2f}  width ${width:.2f}  credit/width {credit_pct:.1f}%")
        lines.append(f"  Max loss:    ${max_loss:.3f}/shr  (${max_loss * 100:.2f}/contract)")
        if cp == "put":
            spot_est = next((float(c.get("underlying_price") or 0) for c in chain if c.get("underlying_price")), None)
            if not spot_est:   # estimate spot from the chain: the put closest to 0.50 delta
                atm = min((c for c in chain if (c.get("greeks") or {}).get("delta") is not None), key=lambda c: abs(abs(float(c["greeks"]["delta"])) - 0.5), default=None)
                spot_est = float(atm["strike"]) if atm else None
            if spot_est:
                lines.append(price_the_odds(strat["ticker"], spot_est, s_strike, credit, width, chain, expiry, today))
        lines.append(
            "  Management: HOLD to expiry -- no profit take, no stop (etf_put_spread_study 2026-09-10; size to the max loss)"
        )
        cp_c       = "C" if cp == "call" else "P"
        s_delta    = (short.get("greeks") or {}).get("delta")
        l_delta    = (long.get("greeks")  or {}).get("delta")
        s_delta_str = f"{abs(float(s_delta)):.2f}Δ" if s_delta is not None else "?Δ"
        l_delta_str = f"{abs(float(l_delta)):.2f}Δ" if l_delta is not None else "?Δ"
        tgt_s_str = f"{short_delta:.2f}Δ"
        tgt_l_str = f"{long_delta:.2f}Δ" if long_delta is not None else "?Δ"
        summary = (
            f"short ${s_strike:.2f}{cp_c}({s_delta_str} tgt {tgt_s_str}) / buy ${l_strike:.2f}{cp_c}({l_delta_str} tgt {tgt_l_str})"
            f"   net ${credit:.3f}cr   width ${width:.2f}"
        )
        max_loss_per_contract = max_loss * 100
    else:
        take_at = short_mid * (1.0 - profit_take)
        keep    = short_mid * profit_take
        strike  = short.get("strike", 0.0)
        lines.append(f"  Premium:     ${short_mid:.3f}/shr  (${short_mid * 100:.2f}/contract)")
        lines.append(
            "  Management: HOLD to expiry -- no profit take, no stop (etf_put_spread_study 2026-09-10; size to the max loss)"
        )
        cp_c       = "C" if cp == "call" else "P"
        s_delta    = (short.get("greeks") or {}).get("delta")
        s_delta_str = f"{abs(float(s_delta)):.2f}Δ" if s_delta is not None else "?Δ"
        summary = f"${strike:.2f}{cp_c}({s_delta_str} tgt {short_delta:.2f}Δ)   premium ${short_mid:.3f}"
        max_loss_per_contract = None  # naked short — undefined max loss

    return {"enter": True, "lines": lines, "summary": summary,
            "max_loss_per_contract": max_loss_per_contract}


def screen_calendar(
    strat:       dict,
    short_chain: list[dict],
    long_chain:  list[dict],
    short_expiry: Optional[str],
    long_expiry:  Optional[str],
    today:        date,
    spot:         Optional[float] = None,
) -> dict:
    """Screen a put calendar spread strategy. Returns enter/lines/summary."""
    min_iv_ratio = strat.get("min_iv_ratio", 1.0)
    profit_take  = strat["profit_take"]
    lines: list[str] = []

    # 1. Expiry pair
    if not short_expiry or not long_expiry:
        lines.append(
            f"  Could not find expiry pair (need ~{DTE_TARGET} DTE short + "
            f"{strat['min_gap']}–{strat['max_gap']}d gap)"
        )
        return {"enter": False, "lines": lines, "summary": "SKIP  (no expiry pair)"}

    short_dte = _dte(short_expiry, today)
    long_dte  = _dte(long_expiry,  today)
    gap       = long_dte - short_dte
    lines.append(f"  Short expiry: {short_expiry} ({short_dte} DTE)")
    lines.append(f"  Long expiry:  {long_expiry} ({long_dte} DTE, gap={gap}d)")

    # 2. Chain guard
    if not short_chain or not long_chain:
        lines.append("  Option chain data unavailable")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)"}

    # 3. Common strikes with positive bid on BOTH expiries
    short_strikes = {
        c["strike"] for c in short_chain
        if c.get("option_type") == "put" and c.get("bid", 0) > 0
    }
    long_strikes = {
        c["strike"] for c in long_chain
        if c.get("option_type") == "put" and c.get("bid", 0) > 0
    }
    common = short_strikes & long_strikes
    if not common:
        lines.append("  No common strikes with positive bid on both expiries")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no common strikes)"}

    # 4. Best ATM put: prefer strike closest to spot among the "ATM zone"
    # (short delta in [0.30, 0.65]); fall back to delta-closest-to-0.50 if spot
    # is unknown or no strike is in the zone. Calendar P/L peaks at strike=spot,
    # so distance-to-spot is the right primary criterion — pure delta-targeting
    # can pick a strike >$1 away from spot when the vol skew is steep.
    short_puts = [
        c for c in short_chain
        if c.get("option_type") == "put"
        and c.get("bid", 0) > 0
        and c["strike"] in common
    ]
    if not short_puts:
        lines.append("  No ATM put in common strikes")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no ATM put)"}

    in_zone = [
        c for c in short_puts
        if 0.30 <= abs((c.get("greeks") or {}).get("delta", 0)) <= 0.65
    ]
    if spot is not None and in_zone:
        best_short = min(in_zone, key=lambda c: abs(c["strike"] - spot))
    else:
        best_short = min(
            short_puts,
            key=lambda c: abs(abs((c.get("greeks") or {}).get("delta", 0)) - 0.50)
        )
    strike = best_short["strike"]

    # 5. Long leg at same strike
    long_matches = [
        c for c in long_chain
        if c.get("option_type") == "put"
        and c["strike"] == strike
        and c.get("bid", 0) > 0
    ]
    if not long_matches:
        lines.append(f"  No ${strike:.2f} put with positive bid on {long_expiry}")
        return {"enter": False, "lines": lines, "summary": "SKIP  (long leg unavailable)"}
    best_long = long_matches[0]

    short_mid = mid_price(best_short)
    long_mid  = mid_price(best_long)
    net_debit = long_mid - short_mid

    if net_debit <= 0:
        lines.append(f"  Net debit ≤ 0 (${net_debit:.3f}) — data issue or deep ITM")
        return {"enter": False, "lines": lines, "summary": "SKIP  (negative debit)"}

    # 6. iv_ratio
    iv_ratio = (
        (short_mid / math.sqrt(short_dte / 365))
        / (long_mid  / math.sqrt(long_dte  / 365))
    )

    # 7. BA spread on both legs
    sp = ba_pct(best_short)
    lp = ba_pct(best_long)

    short_delta = (best_short.get("greeks") or {}).get("delta", 0)
    long_delta  = (best_long.get("greeks")  or {}).get("delta", 0)
    sp_str = f"{sp * 100:.1f}%" if sp is not None else "n/a"
    sp_tag = "✓" if sp is not None and sp <= MAX_SPREAD_PCT else "✗"
    lp_str = f"{lp * 100:.1f}%" if lp is not None else "n/a"
    lp_tag = "✓" if lp is not None and lp <= MAX_SPREAD_PCT else "✗"

    lines.append(f"  Strike: ${strike:.2f}")
    lines.append(
        f"  Short  {short_expiry}"
        f"  bid ${best_short.get('bid', 0):.2f} / ask ${best_short.get('ask', 0):.2f}"
        f"  mid ${short_mid:.2f}  Δ {short_delta:+.3f}"
        f"  BA {sp_str} {sp_tag}"
    )
    lines.append(
        f"  Long   {long_expiry} "
        f"  bid ${best_long.get('bid', 0):.2f} / ask ${best_long.get('ask', 0):.2f}"
        f"  mid ${long_mid:.2f}  Δ {long_delta:+.3f}"
        f"  BA {lp_str} {lp_tag}"
    )
    lines.append("")
    lines.append(f"  Net debit:   ${net_debit:.2f}/share  (${net_debit * 100:.0f}/contract)")
    lines.append(
        f"  iv_ratio:    {iv_ratio:.3f}"
        f"  ({'✓ backwardation' if iv_ratio >= min_iv_ratio else '✗ contango — skip'})"
    )
    if profit_take is None:
        lines.append("  Exit:        HOLD to the short expiry (path study 2026-09-15: every exit rule tested lost to holding)")
    else:
        lines.append(
            f"  Take profit: close when spread ≥ ${net_debit * (1 + profit_take):.2f}/share"
            f"  (+{int(profit_take * 100)}% ROC)"
        )

    # Gate checks
    if sp is None or sp > MAX_SPREAD_PCT:
        lines.append(f"  Short leg BA too wide: {sp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (short BA {sp_str})"}

    if lp is None or lp > MAX_SPREAD_PCT:
        lines.append(f"  Long leg BA too wide: {lp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (long BA {lp_str})"}

    if iv_ratio < min_iv_ratio:
        return {
            "enter": False, "lines": lines,
            "summary": f"SKIP  (iv_ratio {iv_ratio:.3f} < {min_iv_ratio:.2f} — contango)"
        }

    summary = (
        f"${strike:.2f}P calendar  debit ${net_debit:.2f}"
        f"  iv_ratio {iv_ratio:.3f}"
    )
    return {"enter": True, "lines": lines, "summary": summary,
            "max_loss_per_contract": net_debit * 100,
            "long_expiry": long_expiry}


# ── Double calendar screener ──────────────────────────────────────────────────

def screen_double_calendar(
    strat:        dict,
    short_chain:  list[dict],
    long_chain:   list[dict],
    short_expiry: Optional[str],
    long_expiry:  Optional[str],
    vix:          float,
    today:        date,
    spot:         Optional[float],
    ma50:         Optional[float],
) -> dict:
    """
    Screen a regime-gated double calendar spread.

    Structure:
      Short legs: ~12 DTE expiry  (sell put at put_d delta + sell call at call_d delta)
      Long  legs: same strikes (double calendar) or long_widen_pct wider (double diagonal), next weekly (buy them);
                  or, with same_expiry_wings, long_widen_pct wider in the SAME expiry = IRON CONDOR (study step 11)
      Net debit = (long_put_mid - short_put_mid) + (long_call_mid - short_call_mid)   (negative = credit)
      Max risk = net debit + wider wing width (= net debit for the calendar; = width - credit for the condor).
    """
    ticker      = strat["ticker"]
    profit_take = strat["profit_take"]
    lines: list[str] = []

    # 0. 2026-09-16 HOLD: the calendar path study behind the condor / diagonal / double-calendar rules truncated its daily
    #    path after ~2% moves (chain-pull strike window), hiding every loss beyond 3%. Corrected ETF results are ~0
    #    (calendar +3.5 / -2.2, diagonal +2.8 / -2.5, condor +0.8 / -6.6 on 12/19 / 20/27d). Entries print for reference
    #    but are NOT entries until the study is re-run on a clean pull. Set on_hold=False on a strategy to re-enable.
    if strat.get("on_hold", True):
        lines.append("  ⚠ ON HOLD (2026-09-16): the study behind this entry had a path-truncation bug; corrected edge ≈ 0. See calendar_path_study.md erratum.")
        return {"enter": False, "lines": lines, "summary": "SKIP  (ON HOLD -- study erratum 2026-09-16)"}
    # 1. Regime classification
    if spot is None or ma50 is None:
        lines.append("  Cannot classify regime: spot or MA50 unavailable")
        return {"enter": False, "lines": lines, "summary": "SKIP  (regime data unavailable)"}

    trend    = "Bullish" if spot > ma50 else "Bearish"
    iv_class = "HighIV"  if vix >= 20   else "LowIV"
    regime   = f"{trend}_{iv_class}"

    lines.append(f"  {ticker} ${spot:.2f} vs 50MA ${ma50:.2f} → {trend}")
    lines.append(f"  VIX {vix:.2f} → {iv_class}")
    lines.append(f"  Regime: {regime}")

    rs_map = strat["regime_strategies"]
    rs     = rs_map.get(regime, {"exit": "skip"})

    if rs["exit"] == "skip":
        lines.append(f"  {regime}: no double calendar edge in this regime — skip")
        return {"enter": False, "lines": lines, "summary": f"SKIP  ({regime})", "active_regime": regime}

    # 2. Expiry pair (a same-expiry condor only needs the short expiry)
    if strat.get("same_expiry_wings") and short_expiry and not long_expiry:
        long_expiry = short_expiry
    if not short_expiry or not long_expiry:
        lines.append(
            f"  Could not find expiry pair (need ~{strat['dte_target']} DTE short + "
            f"{strat['dc_gap_min']}–{strat['dc_gap_max']}d gap)"
        )
        return {"enter": False, "lines": lines, "summary": "SKIP  (no expiry pair)", "active_regime": regime}

    short_dte = _dte(short_expiry, today)
    long_dte  = _dte(long_expiry, today)
    gap       = long_dte - short_dte
    lines.append(f"  Short expiry: {short_expiry} ({short_dte} DTE)")
    lines.append(f"  Long  expiry: {long_expiry} ({long_dte} DTE, gap={gap}d)")

    if not short_chain or not long_chain:
        lines.append("  Option chain data unavailable")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)", "active_regime": regime}

    put_d  = rs["put_d"]
    call_d = rs["call_d"]

    # 3. Short put leg
    short_put = find_by_delta(short_chain, put_d, "put")
    if short_put is None:
        lines.append(f"  Short {put_d:.2f}Δ put: no match within ±{MAX_DELTA_ERR}Δ")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no short put)", "active_regime": regime}

    pba = ba_pct(short_put)
    if pba is None or pba > MAX_SPREAD_PCT:
        pba_str = f"{pba * 100:.1f}%" if pba is not None else "n/a"
        lines.append(f"  Short put BA too wide: {pba_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (short put BA {pba_str})", "active_regime": regime}

    # 4. Short call leg
    short_call = find_by_delta(short_chain, call_d, "call")
    if short_call is None:
        lines.append(f"  Short {call_d:.2f}Δ call: no match within ±{MAX_DELTA_ERR}Δ")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no short call)", "active_regime": regime}

    cba = ba_pct(short_call)
    if cba is None or cba > MAX_SPREAD_PCT:
        cba_str = f"{cba * 100:.1f}%" if cba is not None else "n/a"
        lines.append(f"  Short call BA too wide: {cba_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (short call BA {cba_str})", "active_regime": regime}

    put_strike  = short_put["strike"]
    call_strike = short_call["strike"]

    # 5/6. Long legs. widen = 0 -> same strikes (double calendar). widen > 0 -> DOUBLE DIAGONAL: long put at the
    # largest long-expiry strike <= Kp x (1 - widen), long call at the smallest >= Kc x (1 + widen)
    # (calendar path study step 7, 2026-09-15: 1% wider beat the calendar on every ticker / regime / 8 of 9 years).
    widen = float(strat.get("long_widen_pct", 0) or 0) / 100.0
    condor = bool(strat.get("same_expiry_wings")) and widen > 0
    if condor:                       # IRON CONDOR: the "long legs" are wings in the SHORT expiry (study step 11)
        long_chain, long_expiry = short_chain, short_expiry
    lp_cands = [c for c in long_chain if c.get("option_type") == "put" and (c.get("bid") or 0) > 0
                and (c["strike"] == put_strike if widen == 0 else c["strike"] <= put_strike * (1 - widen))]
    lc_cands = [c for c in long_chain if c.get("option_type") == "call" and (c.get("bid") or 0) > 0
                and (c["strike"] == call_strike if widen == 0 else c["strike"] >= call_strike * (1 + widen))]
    long_put  = max(lp_cands, key=lambda c: c["strike"]) if lp_cands else None
    long_call = min(lc_cands, key=lambda c: c["strike"]) if lc_cands else None
    if long_put is None:
        lines.append(f"  No long put {'at' if widen == 0 else 'at/below'} ${put_strike * (1 - widen):.2f} with positive bid on {long_expiry}")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no long put)", "active_regime": regime}
    if long_call is None:
        lines.append(f"  No long call {'at' if widen == 0 else 'at/above'} ${call_strike * (1 + widen):.2f} with positive bid on {long_expiry}")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no long call)", "active_regime": regime}
    lp_strike, lc_strike = long_put["strike"], long_call["strike"]
    width_p, width_c = put_strike - lp_strike, lc_strike - call_strike

    # 6b. Long-leg BA gates — same threshold as the short legs. Without this,
    # an illiquid back-month with a 100%+ wide quote sneaks through and the
    # printed mid is fictional.
    lpba = ba_pct(long_put)
    lcba = ba_pct(long_call)
    if lpba is None or lpba > MAX_SPREAD_PCT:
        lpba_str = f"{lpba * 100:.1f}%" if lpba is not None else "n/a"
        lines.append(f"  Long put BA too wide: {lpba_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (long put BA {lpba_str})", "active_regime": regime}
    if lcba is None or lcba > MAX_SPREAD_PCT:
        lcba_str = f"{lcba * 100:.1f}%" if lcba is not None else "n/a"
        lines.append(f"  Long call BA too wide: {lcba_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (long call BA {lcba_str})", "active_regime": regime}

    # 7. Economics
    sp_mid  = mid_price(short_put)
    sc_mid  = mid_price(short_call)
    lp_mid  = mid_price(long_put)
    lc_mid  = mid_price(long_call)
    net_debit = (lp_mid - sp_mid) + (lc_mid - sc_mid)

    max_risk = net_debit + max(width_p, width_c)     # only one wing can be breached at the short expiry
    if condor:
        max_risk = max(width_p, width_c) + net_debit     # net_debit is negative (a credit): width - credit
        if net_debit >= 0:
            lines.append(f"  Condor is not a credit (${net_debit:.3f}) — data issue")
            return {"enter": False, "lines": lines, "summary": "SKIP  (no credit)", "active_regime": regime}
    if widen == 0 and net_debit <= 0:
        lines.append(f"  Net debit ≤ 0 (${net_debit:.3f}) — data issue")
        return {"enter": False, "lines": lines, "summary": "SKIP  (negative debit)", "active_regime": regime}
    if max_risk <= 0.01:
        lines.append(f"  Max risk ≤ 0 (${max_risk:.3f}) — data issue")
        return {"enter": False, "lines": lines, "summary": "SKIP  (bad max risk)", "active_regime": regime}

    sp_delta = (short_put.get("greeks")  or {}).get("delta")
    sc_delta = (short_call.get("greeks") or {}).get("delta")
    sp_d_str = f"{abs(float(sp_delta)):.2f}Δ" if sp_delta is not None else "?Δ"
    sc_d_str = f"{abs(float(sc_delta)):.2f}Δ" if sc_delta is not None else "?Δ"

    pba_str  = f"{pba * 100:.1f}%" if pba is not None else "n/a"
    cba_str  = f"{cba * 100:.1f}%" if cba is not None else "n/a"
    lpba_str = f"{lpba * 100:.1f}%" if lpba is not None else "n/a"
    lcba_str = f"{lcba * 100:.1f}%" if lcba is not None else "n/a"

    lines.append(f"")
    lines.append(
        f"  Short put  ${put_strike:.2f}P  {short_expiry}"
        f"  mid ${sp_mid:.2f}  Δ {sp_d_str}  BA {pba_str}"
    )
    lines.append(
        f"  Long  put  ${lp_strike:.2f}P  {long_expiry}"
        f"  mid ${lp_mid:.2f}  Δ {(long_put.get('greeks') or {}).get('delta', 0):+.3f}"
        f"  BA {lpba_str}"
    )
    lines.append(
        f"  Short call ${call_strike:.2f}C  {short_expiry}"
        f"  mid ${sc_mid:.2f}  Δ {sc_d_str}  BA {cba_str}"
    )
    lines.append(
        f"  Long  call ${lc_strike:.2f}C  {long_expiry}"
        f"  mid ${lc_mid:.2f}  Δ {(long_call.get('greeks') or {}).get('delta', 0):+.3f}"
        f"  BA {lcba_str}"
    )
    lines.append(f"")
    if widen == 0:
        lines.append(f"  Net debit:   ${net_debit:.3f}/shr  (${net_debit * 100:.2f}/contract)")
        lines.append(f"  Max loss:    ${net_debit:.3f}/shr  = net debit paid")
    elif condor:
        lines.append(f"  Structure:   IRON CONDOR, all four legs {short_expiry}, wings {widen * 100:.1f}% of spot (put wing ${width_p:.2f}, call wing ${width_c:.2f})")
        lines.append(f"  Credit:      ${abs(net_debit):.3f}/shr  (${abs(net_debit) * 100:.2f}/contract) = {100 * abs(net_debit) / max_risk:.0f}% of max risk")
        lines.append(f"  Max risk:    ${max_risk:.3f}/shr  (${max_risk * 100:.2f}/contract) = wider wing - credit; SIZE ON THIS")
        lines.append(f"  Breakevens:  ${put_strike + net_debit:.2f} / ${call_strike - net_debit:.2f}  (full credit if {ticker} settles between ${put_strike:.2f} and ${call_strike:.2f})")
    else:
        lines.append(f"  Structure:   DOUBLE DIAGONAL, longs {widen * 100:.1f}% wider (put wing ${width_p:.2f}, call wing ${width_c:.2f})")
        lines.append(f"  Net {'debit' if net_debit >= 0 else 'CREDIT'}:  ${abs(net_debit):.3f}/shr  (${abs(net_debit) * 100:.2f}/contract)")
        lines.append(f"  Max risk:    ${max_risk:.3f}/shr  (${max_risk * 100:.2f}/contract) = net debit + wider wing; SIZE ON THIS")

    if rs["exit"] == "hold":
        lines.append(f"  Exit:        HOLD to expiry -- all four legs settle (every exit rule tested lost to hold; the last day is worth ~10pp)" if condor else
                     f"  Exit:        HOLD to the short expiry -- shorts settle, sell both longs at the close (every exit rule tested lost to hold)")
    else:
        take_at = net_debit * (1.0 + profit_take)
        lines.append(
            f"  Exit:        50% profit take — close when value ≥ ${take_at:.3f}/shr"
            f"  (+{int(profit_take * 100)}% ROC)"
        )

    exit_label = "hold" if rs["exit"] == "hold" else "50%PT"
    summary = (
        f"{regime}  short ${put_strike:.2f}P({sp_d_str})/${call_strike:.2f}C({sc_d_str})"
        + (f"  {'wings' if condor else 'long'} ${lp_strike:.2f}P/${lc_strike:.2f}C{' [IC ' + short_expiry + ']' if condor else ''}" if widen else "")
        + f"  {'debit' if net_debit >= 0 else 'credit'} ${abs(net_debit):.3f}"
        + (f"  max risk ${max_risk:.3f}" if widen else "")
        + f"  [{exit_label}]"
    )
    return {"enter": True, "lines": lines, "summary": summary,
            "max_loss_per_contract": max_risk * 100, "active_regime": regime}


# ── Allocation sizing ─────────────────────────────────────────────────────────

def _print_sizing(
    results: list[tuple[str, dict]],
    total_capital: float,
    risk_pct: float,
) -> None:
    """
    Print contract sizing for all ENTER strategies.

    Primary column: fixed allocation from the $100K portfolio model (registry.portfolio_alloc).
      risk_per_trade = portfolio_alloc / avg_concurrent
      contracts      = risk_per_trade / max_loss_per_contract

    Secondary column: Sharpe-weighted allocation across today's active strategies,
      distributing a total risk budget (total_capital × risk_pct).

    UVXY Bear Call Spread + UVXY Short Put share a single 'UVXY combined' allocation.
    """
    # Collect ENTER results keyed by alloc_key; preserve first-seen order
    entered: dict[str, dict] = {}   # alloc_key → {name, max_loss_per_contract, sub_names}
    strat_meta = {s["name"]: s for s in STRATEGIES}

    for name, result in results:
        if not result["enter"]:
            continue
        strat = strat_meta[name]
        akey  = strat.get("alloc_key", name)
        if akey not in entered:
            entered[akey] = {
                "alloc_key":            akey,
                "sub_names":            [name],
                "max_loss_per_contract": result.get("max_loss_per_contract"),
            }
        else:
            entered[akey]["sub_names"].append(name)
            # For UVXY combined: call spread has defined risk; use that for contracts
            if entered[akey]["max_loss_per_contract"] is None:
                entered[akey]["max_loss_per_contract"] = result.get("max_loss_per_contract")

    if not entered:
        return

    # Look up registry data; collect Sharpes for secondary column
    active_keys = list(entered.keys())
    regs: list[object]   = []
    sharpes: list[float] = []
    missing: list[str]   = []
    for akey in active_keys:
        reg = STRATEGY_MAP.get(akey)
        regs.append(reg)
        if reg is None:
            missing.append(akey)
            sharpes.append(0.01)
        else:
            sharpes.append(max(reg.sharpe_annual, 0.01))

    total_risk   = total_capital * risk_pct
    total_sharpe = sum(sharpes)
    sharpe_alloc = [total_risk * (sh / total_sharpe) for sh in sharpes]

    W = 115
    print("═" * W)
    print(
        f"  CONTRACT SIZING  ·  ${total_capital:,.0f} portfolio  ·  "
        f"{len(active_keys)} active {'strategy' if len(active_keys) == 1 else 'strategies'}"
    )
    print("═" * W)
    print(
        f"  {'Strategy':<24}  {'Alloc':>6}  {'$/trade':>8}  {'Cts':>5}  │  "
        f"{'Sharpe':>6}  {'Sh-wtd $':>9}  {'Sh Cts':>7}  Max loss/ct"
    )
    print(f"  {'(primary: fixed $100K model)':<24}  {'':>6}  {'':>8}  {'':>5}  │  "
          f"{'':>6}  {'(20% risk budget)':>9}")
    print("─" * W)

    fixed_total = 0
    for akey, reg, sh, sa in zip(active_keys, regs, sharpes, sharpe_alloc):
        info = entered[akey]
        sharpe_disp = reg.sharpe_annual if reg else 0.0
        mlpc = info["max_loss_per_contract"]

        # Fixed allocation column (primary)
        if reg and reg.portfolio_alloc > 0:
            alloc_str       = f"${reg.portfolio_alloc:,}"
            risk_per_trade  = reg.risk_per_trade
            risk_str        = f"${risk_per_trade:,}"
            if mlpc and mlpc > 0:
                fixed_cts = int(risk_per_trade / mlpc)
                fixed_cts_str = str(fixed_cts)
            else:
                fixed_cts_str = "—"
            fixed_total += reg.portfolio_alloc
        else:
            alloc_str     = "—"
            risk_str      = "—"
            fixed_cts_str = "—"

        # Sharpe-weighted column (secondary)
        if mlpc and mlpc > 0:
            sh_cts     = int(sa / mlpc)
            mlpc_str   = f"${mlpc:.2f}"
            sh_cts_str = str(sh_cts)
        else:
            mlpc_str   = "undefined (naked)"
            sh_cts_str = "—"

        sub  = ", ".join(info["sub_names"])
        note = f"  ← {sub}" if sub != akey else ""
        print(
            f"  {akey:<24}  {alloc_str:>6}  {risk_str:>8}  {fixed_cts_str:>5}  │  "
            f"{sharpe_disp:>6.3f}  ${sa:>8,.0f}  {sh_cts_str:>7}  {mlpc_str}{note}"
        )

    print("─" * W)
    print(
        f"  {'TOTAL':<24}  ${fixed_total:>5,}  {'':>8}  {'':>5}  │  "
        f"{'':>6}  ${sum(sharpe_alloc):>8,.0f}"
    )
    if missing:
        print(f"\n  NOTE: no registry entry for {missing} — Sharpe floored at 0.01; add to strategy_registry.py")
    print(
        "\n  Fixed model: contracts = (portfolio_alloc / avg_concurrent) / max_loss_per_contract"
        "\n  Sharpe-wtd: distributes 20% of portfolio across today's active strategies by Sharpe ratio"
        "\n  For UVXY combined: risk_per_trade = $2,500 (call spread leg); put runs same $"
        "\n  Always round down contracts; verify fills before sizing up"
    )
    print("═" * W + "\n")


# ── Async fetch helpers ───────────────────────────────────────────────────────

async def _safe_expirations(ticker: str, client: TradierClient) -> list[str]:
    try:
        return await list_expirations(ticker, client=client)
    except Exception as e:
        print(f"  WARNING: expirations fetch failed for {ticker}: {e}", file=sys.stderr)
        return []


async def _safe_chain(
    ticker: str, expiry: Optional[str], client: TradierClient
) -> list[dict]:
    if not expiry:
        return []
    try:
        return await list_contracts_for_expiry(ticker, expiry, client=client)
    except Exception as e:
        print(f"  WARNING: chain fetch failed for {ticker}/{expiry}: {e}", file=sys.stderr)
        return []


async def _safe_spot(ticker: str, client: TradierClient) -> Optional[float]:
    try:
        return await get_underlying_price(ticker, client=client)
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

async def run(today: date, capital: Optional[float] = None, risk_pct: float = 0.20) -> None:
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("ERROR: TRADIER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    W    = 72
    BAR  = "═" * W
    dbar = "─" * W

    if today.weekday() != 4:
        day_name = today.strftime("%A")
        print(f"\n  NOTE: {day_name} is not a Friday. "
              f"Entry signals are calibrated for Friday expiry selection.\n")

    spread_strats        = [s for s in STRATEGIES if s.get("type", "spread") == "spread"]
    calendar_strats      = [s for s in STRATEGIES if s.get("type") == "calendar"]
    regime_strats        = [s for s in STRATEGIES if s.get("type") == "regime_spread"]
    double_cal_strats    = [s for s in STRATEGIES if s.get("type") == "double_calendar"]

    async with TradierClient(api_key=api_key) as client:

        # ── Step 1: fetch VIX, spots, expirations ─────────────────────────────
        unique_tickers = list(dict.fromkeys(s["ticker"] for s in STRATEGIES))

        vix_task   = _safe_spot("VIX", client)
        spot_tasks = [_safe_spot(t, client) for t in unique_tickers]
        exp_tasks  = [_safe_expirations(t, client) for t in unique_tickers]

        vix, *spot_and_exp = await asyncio.gather(
            vix_task, *spot_tasks, *exp_tasks
        )
        spots_list = spot_and_exp[:len(unique_tickers)]
        exps_list  = spot_and_exp[len(unique_tickers):]

        spot_for:        dict[str, Optional[float]] = dict(zip(unique_tickers, spots_list))
        expirations_for: dict[str, list[str]]       = dict(zip(unique_tickers, exps_list))

        # Short expiry per strategy (supports per-strategy dte_target)
        short_expiry_for: dict[str, Optional[str]] = {}
        for strat in STRATEGIES:
            name = strat["name"]
            t    = strat["ticker"]
            dte  = strat.get("dte_target", DTE_TARGET)
            short_expiry_for[name] = find_target_expiry(expirations_for[t], today, dte)

        # Far expiry for fwd_vol_factor on spread strategies (15–60d past short expiry)
        # Calendar strategies reuse their long_expiry; computed below.
        fwd_expiry_for: dict[str, Optional[str]] = {}
        for strat in spread_strats:
            name      = strat["name"]
            t         = strat["ticker"]
            short_exp = short_expiry_for.get(name)
            fwd_expiry_for[name] = (
                find_long_expiry(expirations_for[t], short_exp, min_gap=15, max_gap=60)
                if short_exp else None
            )

        # Long expiry for each calendar ticker (calendars always use DTE_TARGET short leg)
        long_expiry_for: dict[str, Optional[str]] = {}
        for strat in calendar_strats:
            t = strat["ticker"]
            if t not in long_expiry_for:
                short_exp = short_expiry_for.get(strat["name"])
                long_expiry_for[t] = (
                    find_long_expiry(
                        expirations_for[t], short_exp,
                        strat["min_gap"], strat["max_gap"]
                    )
                    if short_exp else None
                )

        # Long expiry for double calendar strategies (keyed by strategy name, not ticker,
        # because multiple DC strats on same ticker could have different gap targets)
        dc_long_expiry_for: dict[str, Optional[str]] = {}
        for strat in double_cal_strats:
            name = strat["name"]
            t    = strat["ticker"]
            short_exp = short_expiry_for.get(name)
            dc_long_expiry_for[name] = (
                find_long_expiry(
                    expirations_for[t], short_exp,
                    strat["dc_gap_min"], strat["dc_gap_max"]
                )
                if short_exp else None
            )

        if vix is None:
            print("ERROR: Could not fetch VIX. Markets may be closed.", file=sys.stderr)
            sys.exit(1)

        # MA50 for regime-switching strategies (cached parquet, refreshed from Tradier first -- it had gone stale)
        ma50_for: dict[str, Optional[float]] = {}
        for t in sorted({strat["ticker"] for strat in STRATEGIES}):
            await refresh_stock_cache(client, t, today)
        for strat in regime_strats + double_cal_strats:
            t = strat["ticker"]
            if t not in ma50_for:
                ma50_for[t] = get_ma50(t)

        # ── Step 2: collect all (ticker, expiry) pairs and fetch in parallel ──
        chain_pairs: list[tuple[str, Optional[str]]] = []
        seen: set = set()
        for s in STRATEGIES:
            t = s["ticker"]
            e = short_expiry_for.get(s["name"])
            if (t, e) not in seen:
                chain_pairs.append((t, e))
                seen.add((t, e))
        for strat in calendar_strats:
            t = strat["ticker"]
            e = long_expiry_for.get(t)
            if (t, e) not in seen:
                chain_pairs.append((t, e))
                seen.add((t, e))
        for strat in double_cal_strats:
            t = strat["ticker"]
            e = dc_long_expiry_for.get(strat["name"])
            if (t, e) not in seen:
                chain_pairs.append((t, e))
                seen.add((t, e))
        # Far expiry chains for fwd_vol_factor on spread strategies
        for strat in spread_strats:
            t = strat["ticker"]
            e = fwd_expiry_for.get(strat["name"])
            if (t, e) not in seen:
                chain_pairs.append((t, e))
                seen.add((t, e))

        chains_raw = await asyncio.gather(
            *[_safe_chain(t, e, client) for t, e in chain_pairs]
        )
        chain_cache: dict[tuple, list[dict]] = {
            pair: ch for pair, ch in zip(chain_pairs, chains_raw)
        }

        # ── Print header ──────────────────────────────────────────────────────
        print(f"\n{BAR}")
        print(f"  FRIDAY OPTIONS SCREENER  ·  {today}  ·  VIX: {vix:.2f}")
        print(f"{BAR}")

        # ── Screen each strategy ──────────────────────────────────────────────
        results: list[tuple[str, dict]] = []

        for strat in STRATEGIES:
            name        = strat["name"]
            ticker      = strat["ticker"]
            strat_type  = strat.get("type", "spread")
            profit_take = strat["profit_take"]

            strat_dte = strat.get("dte_target", DTE_TARGET)

            # Header line
            if strat_type == "calendar":
                header_detail = (
                    f"0.50Δ  {strat_dte}DTE short / {strat['min_gap']}–{strat['max_gap']}d gap"
                    f"  iv_ratio≥{strat['min_iv_ratio']:.2f}  {'HOLD to short expiry' if profit_take is None else f'{int(profit_take * 100)}% take'}"
                )
            elif strat_type == "double_calendar":
                header_detail = (
                    f"double cal 50MA×VIX  {strat_dte}DTE short / "
                    f"{strat['dc_gap_min']}–{strat['dc_gap_max']}d gap"
                )
            elif strat_type == "regime_spread":
                header_detail = (
                    f"regime-switch 50MA×VIX  {strat_dte}DTE  {int(profit_take * 100)}% take"
                )
            elif strat_type == "straddle":
                max_ba = strat.get("max_ba_pct", MAX_SPREAD_PCT)
                header_detail = (
                    f"ATM 0.50Δ straddle  {strat_dte}DTE  BA≤{int(max_ba * 100)}%  {int(profit_take * 100)}% take"
                )
            else:
                sd = strat["short_delta"]
                ld = strat.get("long_delta")
                delta_str = f"{sd:.2f}Δ/{ld:.2f}Δ" if ld else f"{sd:.2f}Δ"
                cond = strat["vix_cond"]
                if cond is None:
                    vix_label = "all VIX"
                elif cond[0] == "lt":
                    vix_label = f"VIX<{cond[1]}"
                else:
                    vix_label = f"VIX≥{cond[1]}"
                header_detail = f"{delta_str}  {strat_dte}DTE  {vix_label}  {int(profit_take * 100)}% take"

            print(f"\n{dbar}")
            print(f"  {name}   [{header_detail}]")
            print(dbar)

            spot = spot_for.get(ticker)
            if spot:
                print(f"  {ticker}: ${spot:.2f}")

            short_exp = short_expiry_for.get(name)

            if strat_type == "calendar":
                long_exp  = long_expiry_for.get(ticker)
                result = screen_calendar(
                    strat,
                    chain_cache.get((ticker, short_exp), []),
                    chain_cache.get((ticker, long_exp),  []),
                    short_exp,
                    long_exp,
                    today,
                    spot_for.get(ticker),
                )
            elif strat_type == "double_calendar":
                long_exp = dc_long_expiry_for.get(name)
                result = screen_double_calendar(
                    strat,
                    chain_cache.get((ticker, short_exp), []),
                    chain_cache.get((ticker, long_exp),  []),
                    short_exp,
                    long_exp,
                    vix,
                    today,
                    spot_for.get(ticker),
                    ma50_for.get(ticker),
                )
                if result.get("enter"):
                    result["display_expiry"]      = short_exp
                    result["display_expiry_long"] = long_exp
            elif strat_type == "regime_spread":
                result = screen_regime_spread(
                    strat,
                    chain_cache.get((ticker, short_exp), []),
                    short_exp,
                    vix,
                    today,
                    spot_for.get(ticker),
                    ma50_for.get(ticker),
                )
            elif strat_type == "straddle":
                result = screen_straddle(
                    strat,
                    chain_cache.get((ticker, short_exp), []),
                    short_exp,
                    today,
                )
            else:
                result = screen_spread(
                    strat,
                    chain_cache.get((ticker, short_exp), []),
                    short_exp,
                    vix,
                    today,
                )

            # Compute fwd_vol_factor (informational — never blocks entry)
            warn_threshold = strat.get("fwd_vol_warn")
            if warn_threshold is not None:
                short_exp = short_expiry_for.get(name)
                near_dte_val = _dte(short_exp, today) if short_exp else 0
                near_ch = chain_cache.get((ticker, short_exp), [])
                if strat_type == "calendar":
                    long_exp = long_expiry_for.get(ticker)
                    far_ch   = chain_cache.get((ticker, long_exp), [])
                    far_dte_val = _dte(long_exp, today) if long_exp else 0
                else:
                    fwd_exp = fwd_expiry_for.get(name)
                    far_ch  = chain_cache.get((ticker, fwd_exp), [])
                    far_dte_val = _dte(fwd_exp, today) if fwd_exp else 0
                factor = fwd_vol_factor(near_ch, far_ch, near_dte_val, far_dte_val)
                result["lines"].append("")
                result["lines"].append(fmt_fwd_vol(factor, warn_threshold))
                result["fwd_vol_factor"] = factor

            # Store expiry/expiries for summary display
            result["display_expiry"] = short_exp
            if strat_type == "calendar" and result.get("long_expiry"):
                result["display_expiry_long"] = result["long_expiry"]

            results.append((name, result))

            for line in result["lines"]:
                print(line)

            verdict = "🟢  ENTER" if result["enter"] else "🔴  SKIP"
            print(f"\n  {verdict}")

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"\n{BAR}")
        print(f"  SUMMARY  ·  {today}  ·  VIX: {vix:.2f}")
        print(f"{BAR}")
        for name, result in results:
            verdict  = "🟢  ENTER" if result["enter"] else "🔴  SKIP "
            factor   = result.get("fwd_vol_factor")
            strat    = next(s for s in STRATEGIES if s["name"] == name)
            warn_thr = strat.get("fwd_vol_warn")
            fwd_tag  = ""
            if factor is not None and warn_thr is not None:
                if math.isnan(factor):
                    fwd_tag = "  [fwd=NaN backwardation]"
                elif factor > 1.50:
                    fwd_tag = f"  [⚠⚠ fwd={factor:.2f} HIGH CONTANGO]"
                elif factor > warn_thr:
                    fwd_tag = f"  [⚠ fwd={factor:.2f} elevated]"
                else:
                    fwd_tag = f"  [fwd={factor:.2f}]"
            if result.get("display_expiry"):
                if result.get("display_expiry_long"):
                    exp_str = f"  exp {result['display_expiry']} / {result['display_expiry_long']}"
                else:
                    exp_str = f"  exp {result['display_expiry']}"
            else:
                exp_str = ""
            # Tier tag
            active_regime = result.get("active_regime")
            if not active_regime and name in REGIME_TIER_MAP:
                # Regime skips embed the regime name in the summary — extract it
                for r in ("Bearish_HighIV", "Bearish_LowIV", "Bullish_HighIV", "Bullish_LowIV"):
                    if r in result.get("summary", ""):
                        active_regime = r
                        break
            if name in REGIME_TIER_MAP and active_regime:
                tier = REGIME_TIER_MAP[name].get(active_regime, "?")
            else:
                tier = TIER_MAP.get(name, "?")
            tier_tag  = f"  [Tier {tier}]"
            date_tag  = f"  [{today}]" if result.get("enter") else ""
            print(f"  {verdict}   {name:<28}  {result['summary']}{exp_str}{fwd_tag}{tier_tag}{date_tag}")
        print(f"{BAR}\n")

        # ── Sizing section (only when --capital is provided) ──────────────────
        if capital is not None:
            _print_sizing(results, capital, risk_pct)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Friday screener — live Tradier checks for all confirmed strategies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        type=lambda s: date.fromisoformat(s),
        default=date.today(),
        help="Trade date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--capital", type=float, default=100_000,
        help="Portfolio size in dollars (default: $100,000)",
    )
    parser.add_argument(
        "--risk-pct", type=float, default=0.20,
        help="Fraction of capital to risk across active strategies (default: 0.20 = 20%%)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.date, capital=args.capital, risk_pct=args.risk_pct))


if __name__ == "__main__":
    main()

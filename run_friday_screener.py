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
from datetime import date
from typing import Optional

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
        "type":          "spread",
        "name":          "XLF Bull Put Spread",
        "alloc_key":     "XLF puts",
        "ticker":        "XLF",
        "cp":            "put",
        "short_delta":   0.35,
        "long_delta":    0.25,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # avg=1.077; sweet spot ≤1.10
        "note":          "financials upward drift — no VIX filter; optional fwd_vol ≤1.10",
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
        "type":          "spread",
        "name":          "XLE Bull Put Spread",
        "alloc_key":     "XLE puts",
        "ticker":        "XLE",
        "cp":            "put",
        "short_delta":   0.30,
        "long_delta":    0.20,
        "dte_target":    60,
        "vix_cond":      None,
        "profit_take":   0.50,
        "fwd_vol_warn":  1.20,   # energy IV elevated in geopolitical/macro stress; flag >1.20
        "note":          "PROVISIONAL; energy sector oil/gas; 60 DTE; +7.18% ROC 88.7% win; All VIX",
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
    {
        "type":          "calendar",
        "name":          "GLD Put Calendar",
        "alloc_key":     "GLD calendar",
        "ticker":        "GLD",
        "min_gap":       25,
        "max_gap":       50,
        "min_iv_ratio":  1.0,
        "profit_take":   0.25,
        "fwd_vol_warn":  1.10,   # avg≈0.95; >1.10 = unfavorable for calendar
        "note":          "backwardation only (iv_ratio ≥ 1.00); ~68% of Fridays eligible",
    },
    {
        "type":          "calendar",
        "name":          "XLU Put Calendar",
        "alloc_key":     "XLU calendar",
        "ticker":        "XLU",
        "min_gap":       25,
        "max_gap":       50,
        "min_iv_ratio":  1.0,
        "profit_take":   0.25,
        "fwd_vol_warn":  1.00,   # avg=0.80; any >1.0 = unfavorable; ≤0.90 is optimal
        "note":          "structurally in backwardation; enter every eligible Friday",
    },
]

DTE_TARGET     = 20
DTE_TOL        = 5
MAX_DELTA_ERR  = 0.08
MAX_SPREAD_PCT = 0.25   # max (ask-bid)/mid on the short leg


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
        lines.append(
            f"  Take profit: close spread at ≤ ${take_at:.3f}"
            f"  (keep {int(profit_take * 100)}% = ${keep:.3f}/shr)"
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
            f"  Take profit: close at ≤ ${take_at:.3f}"
            f"  (keep {int(profit_take * 100)}% = ${keep:.3f}/shr)"
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

    # 4. Best ATM put: closest to 0.50Δ on short leg, from common strikes only
    short_puts = [
        c for c in short_chain
        if c.get("option_type") == "put"
        and c.get("bid", 0) > 0
        and c["strike"] in common
    ]
    if not short_puts:
        lines.append("  No ATM put in common strikes")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no ATM put)"}

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

    # 7. BA spread on short leg
    sp = ba_pct(best_short)

    short_delta = (best_short.get("greeks") or {}).get("delta", 0)
    long_delta  = (best_long.get("greeks")  or {}).get("delta", 0)
    sp_str = f"{sp * 100:.1f}%" if sp is not None else "n/a"
    sp_tag = "✓" if sp is not None and sp <= MAX_SPREAD_PCT else "✗"

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
    )
    lines.append("")
    lines.append(f"  Net debit:   ${net_debit:.2f}/share  (${net_debit * 100:.0f}/contract)")
    lines.append(
        f"  iv_ratio:    {iv_ratio:.3f}"
        f"  ({'✓ backwardation' if iv_ratio >= min_iv_ratio else '✗ contango — skip'})"
    )
    lines.append(
        f"  Take profit: close when spread ≥ ${net_debit * (1 + profit_take):.2f}/share"
        f"  (+{int(profit_take * 100)}% ROC)"
    )

    # Gate checks
    if sp is None or sp > MAX_SPREAD_PCT:
        lines.append(f"  Short leg BA too wide: {sp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (BA {sp_str})"}

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


# ── Allocation sizing ─────────────────────────────────────────────────────────

def _print_sizing(
    results: list[tuple[str, dict]],
    total_capital: float,
    risk_pct: float,
) -> None:
    """
    Print contract sizing for all ENTER strategies using equal-risk and
    Sharpe-weighted allocations from the strategy registry.

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

    # Look up Sharpe from registry; warn if missing
    active_keys = list(entered.keys())
    sharpes: list[float] = []
    missing: list[str]   = []
    for akey in active_keys:
        reg = STRATEGY_MAP.get(akey)
        if reg is None:
            missing.append(akey)
            sharpes.append(0.01)
        else:
            sharpes.append(max(reg.sharpe_annual, 0.01))

    total_risk  = total_capital * risk_pct
    n           = len(active_keys)
    equal_per   = total_risk / n
    total_sharpe = sum(sharpes)
    sharpe_alloc = [total_risk * (sh / total_sharpe) for sh in sharpes]

    W = 108
    print("═" * W)
    print(
        f"  CONTRACT SIZING  ·  ${total_capital:,.0f} portfolio  ·  "
        f"{risk_pct * 100:.0f}% risk budget = ${total_risk:,.0f}  ·  "
        f"{n} active {'strategy' if n == 1 else 'strategies'}"
    )
    print("═" * W)
    print(
        f"  {'Strategy (alloc key)':<26}  {'Sharpe':>6}  {'= Risk $':>9}  "
        f"{'= Cts':>6}  {'Sharpe-wtd $':>12}  {'Sharpe Cts':>10}  Max loss/ct"
    )
    print("─" * W)

    for akey, sh, sa in zip(active_keys, sharpes, sharpe_alloc):
        info = entered[akey]
        reg  = STRATEGY_MAP.get(akey)
        sharpe_disp = reg.sharpe_annual if reg else 0.0
        mlpc = info["max_loss_per_contract"]

        if mlpc is not None and mlpc > 0:
            eq_cts = int(equal_per / mlpc)
            sh_cts = int(sa / mlpc)
            mlpc_str  = f"${mlpc:.2f}"
            eq_cts_str = str(eq_cts)
            sh_cts_str = str(sh_cts)
        else:
            mlpc_str   = "undefined (naked)"
            eq_cts_str = "—"
            sh_cts_str = "—"

        sub = ", ".join(info["sub_names"])
        note = f"  ← {sub}" if sub != akey else ""
        print(
            f"  {akey:<26}  {sharpe_disp:>6.3f}  ${equal_per:>8,.0f}  "
            f"{eq_cts_str:>6}  ${sa:>11,.0f}  {sh_cts_str:>10}  {mlpc_str}{note}"
        )

    print("─" * W)
    print(
        f"  {'TOTAL':<26}  {'':>6}  ${total_risk:>8,.0f}  {'':>6}  "
        f"${sum(sharpe_alloc):>11,.0f}"
    )
    if missing:
        print(f"\n  WARNING: no registry entry for: {missing}  (Sharpe floored at 0.01)")
    print(
        "\n  Contracts = allocation / max_loss_per_contract  (round down; always verify fills)"
        "\n  For UVXY combined: call spread allocation applies; put allocation is half that (50/50 blend)"
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

    spread_strats   = [s for s in STRATEGIES if s.get("type", "spread") == "spread"]
    calendar_strats = [s for s in STRATEGIES if s.get("type") == "calendar"]

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

        if vix is None:
            print("ERROR: Could not fetch VIX. Markets may be closed.", file=sys.stderr)
            sys.exit(1)

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
                    f"  iv_ratio≥{strat['min_iv_ratio']:.2f}  {int(profit_take * 100)}% take"
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
            if result.get("enter") and result.get("display_expiry"):
                if result.get("display_expiry_long"):
                    exp_str = f"  exp {result['display_expiry']} / {result['display_expiry_long']}"
                else:
                    exp_str = f"  exp {result['display_expiry']}"
            else:
                exp_str = ""
            print(f"  {verdict}   {name:<28}  {result['summary']}{exp_str}{fwd_tag}")
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
        "--capital", type=float, default=None,
        help="Portfolio size in dollars — enables contract sizing output",
    )
    parser.add_argument(
        "--risk-pct", type=float, default=0.20,
        help="Fraction of capital to risk across active strategies (default: 0.20 = 20%%)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.date, capital=args.capital, risk_pct=args.risk_pct))


if __name__ == "__main__":
    main()

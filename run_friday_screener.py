#!/usr/bin/env python3
"""
Friday options screener — checks all four confirmed strategies against live
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
import os
import sys
from datetime import date
from typing import Optional

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_expirations import list_expirations
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price


# ── Strategy definitions ──────────────────────────────────────────────────────
#
# vix_cond: None         → always enter
#           ("lt",  N)   → enter only when VIX < N
#           ("gte", N)   → enter only when VIX ≥ N
#
# long_delta: None       → naked short (no long leg)

STRATEGIES: list[dict] = [
    {
        "name":        "UVXY Bear Call Spread",
        "ticker":      "UVXY",
        "cp":          "call",
        "short_delta": 0.50,
        "long_delta":  0.40,
        "vix_cond":    None,
        "profit_take": 0.50,
        "note":        "structural decay trade — enter every Friday",
    },
    {
        "name":        "UVXY Short Put",
        "ticker":      "UVXY",
        "cp":          "put",
        "short_delta": 0.40,
        "long_delta":  None,          # naked put
        "vix_cond":    ("lt", 20),
        "profit_take": 0.50,
        "note":        "only when VIX < 20; skip in elevated-fear regimes",
    },
    {
        "name":        "TLT Bear Call Spread",
        "ticker":      "TLT",
        "cp":          "call",
        "short_delta": 0.35,
        "long_delta":  0.30,
        "vix_cond":    ("gte", 20),
        "profit_take": 0.70,
        "note":        "only when VIX ≥ 20 (fear = TLT under pressure)",
    },
    {
        "name":        "GLD Bull Put Spread",
        "ticker":      "GLD",
        "cp":          "put",
        "short_delta": 0.30,
        "long_delta":  0.25,
        "vix_cond":    ("lt", 25),
        "profit_take": 0.50,
        "note":        "skip when VIX ≥ 25 (tail-risk events can spike gold both ways)",
    },
    {
        "name":        "XLV Bull Put Spread",
        "ticker":      "XLV",
        "cp":          "put",
        "short_delta": 0.25,
        "long_delta":  0.20,
        "vix_cond":    None,
        "profit_take": 0.50,
        "note":        "defensive healthcare — no VIX filter needed",
    },
]

DTE_TARGET     = 20
DTE_TOL        = 5
MAX_DELTA_ERR  = 0.08
MAX_SPREAD_PCT = 0.25   # max (ask-bid)/mid on the short leg


# ── Pure helpers (no I/O) ────────────────────────────────────────────────────

def find_target_expiry(expirations: list[str], today: date) -> Optional[str]:
    """Closest expiry to DTE_TARGET within ±DTE_TOL; None if none qualify."""
    best: Optional[str] = None
    best_err = DTE_TOL + 1
    for exp_str in expirations:
        dte = (date.fromisoformat(exp_str) - today).days
        err = abs(dte - DTE_TARGET)
        if err <= DTE_TOL and err < best_err:
            best_err = err
            best = exp_str
    return best


def find_by_delta(
    contracts: list[dict],
    target_unsigned: float,
    cp: str,
    max_err: float = MAX_DELTA_ERR,
) -> Optional[dict]:
    """Contract closest to target delta, within max_err; None if no match."""
    # Calls have positive delta; puts have negative delta.
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
        f"  {label:<6}  {target_delta:.2f}Δ {cp_c}"
        f"  ${strike:>7.2f}"
        f"  bid ${bid:>5.2f}  ask ${ask:>5.2f}  mid ${m:>5.2f}"
        f"  Δ {d_str}  BA {sp_str:>6} {sp_tag}"
    )


# ── Per-strategy screening ────────────────────────────────────────────────────

def screen_strategy(
    strat:    dict,
    chain:    list[dict],       # full (call + put) chain for this ticker/expiry
    expiry:   Optional[str],
    vix:      float,
    today:    date,
) -> dict:
    """
    Returns:
        enter:   bool
        lines:   list[str]   detail block
        summary: str         one-liner for the summary table
    """
    cp          = strat["cp"]
    short_delta = strat["short_delta"]
    long_delta  = strat.get("long_delta")
    profit_take = strat["profit_take"]
    lines: list[str] = []

    # ── 1. VIX gate ───────────────────────────────────────────────────────────
    ok, vix_desc = vix_check(vix, strat["vix_cond"])
    lines.append(f"  {vix_desc}")
    if not ok:
        return {"enter": False, "lines": lines,
                "summary": f"SIT OUT   ({vix_desc})"}

    # ── 2. Expiry ─────────────────────────────────────────────────────────────
    if not expiry:
        lines.append(f"  No expiry within {DTE_TARGET}±{DTE_TOL} DTE")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no valid expiry)"}
    dte = (date.fromisoformat(expiry) - today).days
    lines.append(f"  Expiry: {expiry}  ({dte} DTE)")

    # ── 3. Chain guard ────────────────────────────────────────────────────────
    if not chain:
        lines.append("  No option chain data returned")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain data)"}

    # ── 4. Short leg ──────────────────────────────────────────────────────────
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

    # ── 5. Long leg (spreads only) ────────────────────────────────────────────
    long: Optional[dict] = None
    if long_delta is not None:
        long = find_by_delta(chain, long_delta, cp)
        if long is None:
            lines.append(
                f"  Long  {long_delta:.2f}Δ {cp}:  no match within ±{MAX_DELTA_ERR}Δ"
            )
            return {"enter": False, "lines": lines, "summary": "SKIP  (no long leg match)"}
        lines.append(fmt_leg(long, "Long", cp, long_delta))

    # ── 6. Economics ──────────────────────────────────────────────────────────
    lines.append("")
    short_mid = mid_price(short)

    if long is not None:
        long_mid = mid_price(long)
        credit   = short_mid - long_mid
        s_strike = short.get("strike", 0.0)
        l_strike = long.get("strike", 0.0)
        # Bear call: long_strike > short_strike  → width = long - short
        # Bull put:  short_strike > long_strike  → width = short - long
        width = (l_strike - s_strike) if cp == "call" else (s_strike - l_strike)

        if credit <= 0 or width <= 0:
            lines.append(f"  Invalid spread — credit ${credit:.3f}  width ${width:.2f}")
            return {"enter": False, "lines": lines, "summary": "SKIP  (invalid spread)"}

        max_loss     = width - credit
        credit_pct   = credit / width * 100
        take_at      = credit * (1.0 - profit_take)
        keep         = credit * profit_take

        lines.append(f"  Net credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)")
        lines.append(f"  Spread:      ${s_strike:.2f}/${l_strike:.2f}  width ${width:.2f}  credit/width {credit_pct:.1f}%")
        lines.append(f"  Max loss:    ${max_loss:.3f}/shr  (${max_loss * 100:.2f}/contract)")
        lines.append(
            f"  Take profit: close spread at ≤ ${take_at:.3f}"
            f"  (keep {int(profit_take * 100)}% = ${keep:.3f}/shr)"
        )
        cp_c    = "C" if cp == "call" else "P"
        summary = (
            f"short ${s_strike:.2f}{cp_c} / buy ${l_strike:.2f}{cp_c}"
            f"   net ${credit:.3f}cr   width ${width:.2f}"
        )
    else:
        # Naked short put
        take_at = short_mid * (1.0 - profit_take)
        keep    = short_mid * profit_take
        strike  = short.get("strike", 0.0)
        lines.append(f"  Premium:     ${short_mid:.3f}/shr  (${short_mid * 100:.2f}/contract)")
        lines.append(
            f"  Take profit: close at ≤ ${take_at:.3f}"
            f"  (keep {int(profit_take * 100)}% = ${keep:.3f}/shr)"
        )
        cp_c    = "C" if cp == "call" else "P"
        summary = f"${strike:.2f}{cp_c}   premium ${short_mid:.3f}"

    return {"enter": True, "lines": lines, "summary": summary}


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


# ── Main ─────────────────────────────────────────────────────────────────────

async def run(today: date) -> None:
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

    async with TradierClient(api_key=api_key) as client:

        # ── Parallel fetch: VIX, spots, expirations ───────────────────────────
        unique_tickers = list(dict.fromkeys(s["ticker"] for s in STRATEGIES))

        vix_task  = _safe_spot("VIX", client)
        spot_tasks = [_safe_spot(t, client) for t in unique_tickers]
        exp_tasks  = [_safe_expirations(t, client) for t in unique_tickers]

        vix, *spot_and_exp = await asyncio.gather(
            vix_task, *spot_tasks, *exp_tasks
        )
        spots_list = spot_and_exp[:len(unique_tickers)]
        exps_list  = spot_and_exp[len(unique_tickers):]

        spot_for:   dict[str, Optional[float]] = dict(zip(unique_tickers, spots_list))
        expiry_for: dict[str, Optional[str]]   = {
            t: find_target_expiry(exps, today)
            for t, exps in zip(unique_tickers, exps_list)
        }

        if vix is None:
            print("ERROR: Could not fetch VIX. Markets may be closed.", file=sys.stderr)
            sys.exit(1)

        # ── Parallel fetch: option chains ─────────────────────────────────────
        chains_list = await asyncio.gather(
            *[_safe_chain(t, expiry_for[t], client) for t in unique_tickers]
        )
        chain_for: dict[str, list[dict]] = dict(zip(unique_tickers, chains_list))

        # ── Print header ──────────────────────────────────────────────────────
        print(f"\n{BAR}")
        print(f"  FRIDAY OPTIONS SCREENER  ·  {today}  ·  VIX: {vix:.2f}")
        print(f"{BAR}")

        # ── Screen each strategy ──────────────────────────────────────────────
        results: list[tuple[str, dict]] = []

        for strat in STRATEGIES:
            name   = strat["name"]
            ticker = strat["ticker"]
            cp     = strat["cp"]
            sd     = strat["short_delta"]
            ld     = strat.get("long_delta")
            pt     = strat["profit_take"]
            cond   = strat["vix_cond"]

            # Build compact header label
            delta_str = f"{sd:.2f}Δ/{ld:.2f}Δ" if ld else f"{sd:.2f}Δ"
            if cond is None:
                vix_label = "all VIX"
            elif cond[0] == "lt":
                vix_label = f"VIX<{cond[1]}"
            else:
                vix_label = f"VIX≥{cond[1]}"

            print(f"\n{dbar}")
            print(
                f"  {name}"
                f"   [{delta_str}  {DTE_TARGET}DTE  {vix_label}  {int(pt * 100)}% take]"
            )
            print(dbar)

            spot = spot_for.get(ticker)
            if spot:
                print(f"  {ticker}: ${spot:.2f}")

            result = screen_strategy(
                strat,
                chain_for.get(ticker, []),
                expiry_for.get(ticker),
                vix,
                today,
            )
            results.append((name, result))

            for line in result["lines"]:
                print(line)

            verdict = "👍  ENTER" if result["enter"] else "👎  SKIP"
            print(f"\n  {verdict}")

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"\n{BAR}")
        print(f"  SUMMARY  ·  {today}  ·  VIX: {vix:.2f}")
        print(f"{BAR}")
        for name, result in results:
            verdict = "👍  ENTER" if result["enter"] else "👎  SKIP "
            print(f"  {verdict}   {name:<28}  {result['summary']}")
        print(f"{BAR}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Friday screener — live Tradier checks for the four confirmed strategies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        type=lambda s: date.fromisoformat(s),
        default=date.today(),
        help="Trade date YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.date))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Position monitor — checks all open strategy positions against live Tradier
quotes and recommends actions (hold, close, expiry approaching).

Usage:
    PYTHONPATH=src python run_position_monitor.py

Requires: TRADIER_API_KEY, MYSQL_PASSWORD
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, timedelta
from typing import Optional

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.mysql_lib import get_open_positions


# ── Quote helpers ─────────────────────────────────────────────────────────────

def _mid(contract: dict) -> Optional[float]:
    bid = contract.get("bid") or 0.0
    ask = contract.get("ask") or 0.0
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    last = contract.get("last") or 0.0
    return float(last) if last else None


def _find_contract(
    chain: list[dict],
    strike: float,
    put_call: str,
) -> Optional[dict]:
    for c in chain:
        if (
            abs(float(c.get("strike", 0)) - strike) < 0.01
            and c.get("option_type", "").lower() == put_call.lower()
        ):
            return c
    return None


async def _fetch_chain(
    ticker: str,
    expiry: date,
    client: TradierClient,
) -> list[dict]:
    try:
        return await list_contracts_for_expiry(
            ticker, expiry.isoformat(), client=client
        )
    except Exception as e:
        print(f"  WARNING: chain fetch failed {ticker}/{expiry}: {e}", file=sys.stderr)
        return []


# ── Action logic ──────────────────────────────────────────────────────────────

def evaluate_position(pos: dict, chains: dict[tuple, list[dict]], today: date) -> dict:
    """
    Returns a dict with:
        action:   'CLOSE' | 'HOLD' | 'EXPIRY_SOON' | 'DATA_ERROR'
        reason:   str
        pnl_pct:  float | None   (% of entry_value recovered/lost)
        detail:   list[str]
    """
    detail: list[str] = []
    ticker       = pos["ticker"]
    position_type = pos["position_type"]
    entry_value  = pos["entry_value"]   # credit (>0) for spreads, debit (<0) for calendars
    pt_pct       = pos["profit_target_pct"]
    contracts    = pos["contracts"]
    expiry       = pos["expiry"]
    legs         = pos["legs"]

    dte = (expiry - today).days
    detail.append(f"  Expiry: {expiry}  ({dte} DTE)")

    # Locate short and long legs
    short_leg = next((l for l in legs if l["leg_role"] == "open_short"), None)
    long_leg  = next((l for l in legs if l["leg_role"] == "open_long"),  None)

    if not short_leg:
        return {"action": "DATA_ERROR", "reason": "no open_short leg found",
                "pnl_pct": None, "detail": detail}

    # Fetch current quotes
    put_call = (short_leg["put_call"] or "P").upper()
    cp_str   = "put" if put_call == "P" else "call"

    short_chain = chains.get((ticker, short_leg["trade_expiry"]), [])
    short_contract = _find_contract(short_chain, short_leg["trade_strike"], cp_str)

    long_contract = None
    if long_leg:
        long_chain = chains.get((ticker, long_leg["trade_expiry"]), [])
        long_contract = _find_contract(long_chain, long_leg["trade_strike"], cp_str)

    short_mid = _mid(short_contract) if short_contract else None
    long_mid  = _mid(long_contract)  if long_contract  else None

    if short_mid is None:
        return {"action": "DATA_ERROR", "reason": "no quote for short leg",
                "pnl_pct": None, "detail": detail}

    # ── Credit spread (bull_put_spread, bear_call_spread) ─────────────────────
    if position_type in ("bull_put_spread", "bear_call_spread"):
        if long_mid is None:
            return {"action": "DATA_ERROR", "reason": "no quote for long leg",
                    "pnl_pct": None, "detail": detail}

        # Current cost to close = buy back short, sell long
        current_spread = short_mid - long_mid   # cost to close (positive = debit to close)
        target_spread  = entry_value * (1.0 - pt_pct)  # close when spread ≤ this
        pnl_per_share  = entry_value - current_spread   # P&L realised if closed now
        pnl_pct        = pnl_per_share / entry_value * 100
        total_pnl      = pnl_per_share * 100 * contracts

        detail.append(f"  Short ${short_leg['trade_strike']:.2f}P  entry ${short_leg['price']:.2f}  current ${short_mid:.2f}")
        detail.append(f"  Long  ${long_leg['trade_strike']:.2f}P  entry ${long_leg['price']:.2f}  current ${long_mid:.2f}")
        detail.append("")
        detail.append(f"  Entry credit:     ${entry_value:.4f}/shr")
        detail.append(f"  Current spread:   ${current_spread:.4f}/shr  (cost to close)")
        detail.append(f"  Profit target:    close when spread ≤ ${target_spread:.4f}  (keep {int(pt_pct*100)}%)")
        detail.append(f"  P&L if closed now: ${pnl_per_share:+.4f}/shr  ({pnl_pct:+.1f}%)  ${total_pnl:+.0f} total ({contracts} contracts)")

        if dte <= 1:
            action = "EXPIRY_SOON"
            reason = f"Expiry tomorrow — close both legs at market"
        elif current_spread <= target_spread:
            action = "CLOSE"
            reason = (
                f"Profit target reached: spread ${current_spread:.4f} ≤ ${target_spread:.4f} "
                f"({pnl_pct:.1f}% ROC)"
            )
        elif dte <= 3:
            action = "EXPIRY_SOON"
            reason = f"Expiry in {dte} days — monitor closely"
        else:
            action = "HOLD"
            reason = (
                f"Spread ${current_spread:.4f} > target ${target_spread:.4f} "
                f"({pnl_pct:+.1f}% ROC so far)"
            )

    # ── Calendar (put_calendar, call_calendar) ────────────────────────────────
    elif position_type in ("put_calendar", "call_calendar"):
        if long_mid is None:
            return {"action": "DATA_ERROR", "reason": "no quote for long leg",
                    "pnl_pct": None, "detail": detail}

        # For a long calendar: current value = long_mid - short_mid
        # entry_value is stored as negative (debit paid) — use abs
        debit       = abs(entry_value)
        current_val = long_mid - short_mid   # current spread value
        target_val  = debit * (1.0 + pt_pct)
        pnl_per_share = current_val - debit
        pnl_pct       = pnl_per_share / debit * 100
        total_pnl     = pnl_per_share * 100 * contracts

        detail.append(f"  Short ${short_leg['trade_strike']:.2f}P {short_leg['trade_expiry']}  entry ${short_leg['price']:.2f}  current ${short_mid:.2f}")
        detail.append(f"  Long  ${long_leg['trade_strike']:.2f}P {long_leg['trade_expiry']}  entry ${long_leg['price']:.2f}  current ${long_mid:.2f}")
        detail.append("")
        detail.append(f"  Entry debit:       ${debit:.4f}/shr")
        detail.append(f"  Current value:     ${current_val:.4f}/shr")
        detail.append(f"  Profit target:     close when value ≥ ${target_val:.4f}  (+{int(pt_pct*100)}% ROC)")
        detail.append(f"  P&L if closed now: ${pnl_per_share:+.4f}/shr  ({pnl_pct:+.1f}%)  ${total_pnl:+.0f} total ({contracts} contracts)")

        if dte <= 1:
            action = "EXPIRY_SOON"
            reason = "Short leg expires tomorrow — close both legs at market"
        elif current_val >= target_val:
            action = "CLOSE"
            reason = (
                f"Profit target reached: value ${current_val:.4f} ≥ ${target_val:.4f} "
                f"(+{pnl_pct:.1f}% ROC)"
            )
        elif dte <= 3:
            action = "EXPIRY_SOON"
            reason = f"Short expiry in {dte} days — monitor closely"
        else:
            action = "HOLD"
            reason = (
                f"Value ${current_val:.4f} < target ${target_val:.4f} "
                f"({pnl_pct:+.1f}% ROC so far)"
            )

    else:
        return {"action": "DATA_ERROR", "reason": f"unknown position_type {position_type}",
                "pnl_pct": None, "detail": detail}

    return {"action": action, "reason": reason, "pnl_pct": pnl_pct, "detail": detail}


# ── Main ──────────────────────────────────────────────────────────────────────

async def run(today: date) -> None:
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("ERROR: TRADIER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    positions = get_open_positions()
    if not positions:
        print("No open positions.")
        return

    W   = 72
    BAR = "═" * W
    bar = "─" * W

    async with TradierClient(api_key=api_key) as client:

        # Collect all (ticker, expiry) pairs needed
        expiry_pairs: set[tuple[str, date]] = set()
        for pos in positions:
            for leg in pos["legs"]:
                expiry_pairs.add((pos["ticker"], leg["trade_expiry"]))

        # Fetch all chains in parallel
        pairs = list(expiry_pairs)
        chains_raw = await asyncio.gather(
            *[_fetch_chain(t, e, client) for t, e in pairs]
        )
        chains: dict[tuple, list[dict]] = {
            pair: ch for pair, ch in zip(pairs, chains_raw)
        }

        # Spot prices
        unique_tickers = list({pos["ticker"] for pos in positions})
        spots_raw = await asyncio.gather(
            *[get_underlying_price(t, client=client) for t in unique_tickers]
        )
        spot_for = dict(zip(unique_tickers, spots_raw))

    print(f"\n{BAR}")
    print(f"  POSITION MONITOR  ·  {today}")
    print(f"{BAR}")

    action_icons = {
        "CLOSE":       "⚠️   CLOSE NOW",
        "EXPIRY_SOON": "⏰  EXPIRY SOON",
        "HOLD":        "✅  HOLD",
        "DATA_ERROR":  "❌  DATA ERROR",
    }

    results = []
    for pos in positions:
        name   = pos["strategy_name"]
        ticker = pos["ticker"]
        spot   = spot_for.get(ticker)

        print(f"\n{bar}")
        spot_str = f"  {ticker}: ${spot:.2f}" if spot else ""
        print(f"  {name}  ·  {pos['contracts']} contract(s)  ·  entered {pos['entry_date']}{spot_str}")
        print(bar)

        result = evaluate_position(pos, chains, today)
        for line in result["detail"]:
            print(line)

        icon = action_icons.get(result["action"], result["action"])
        print(f"\n  {icon}  —  {result['reason']}")
        results.append((name, result))

    # Summary
    print(f"\n{BAR}")
    print(f"  SUMMARY  ·  {today}")
    print(f"{BAR}")
    for name, result in results:
        icon = action_icons.get(result["action"], result["action"])
        pnl_str = f"  ({result['pnl_pct']:+.1f}%)" if result["pnl_pct"] is not None else ""
        print(f"  {icon}   {name:<30}{pnl_str}")
    print(f"{BAR}\n")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Monitor open strategy positions")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    asyncio.run(run(args.date))


if __name__ == "__main__":
    main()

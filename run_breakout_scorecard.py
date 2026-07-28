#!/usr/bin/env python3
"""
Ad-hoc gate scorecard for one or more tickers — no filtering, full picture.

Answers "would today qualify as a breakout?" the scorecard way: every
universe gate with its measured value, threshold, tier (required/optional),
and pass/miss, then the event (pivot / volume confirmation) and the
Potent/Leader classification, with marginal passes flagged.

Usage:
  PYTHONPATH=src python run_breakout_scorecard.py MNST
  PYTHONPATH=src python run_breakout_scorecard.py MNST NVDA --asof 2026-07-15

Requires: TRADIER_API_KEY.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date
from typing import Any, Dict, Optional

from lib.interface.premarket_watchlist import (
    VOL_CONFIRM_MULT,
    score_ticker,
)
from lib.tradier.tradier_client_wrapper import TradierClient

# A pass within this fraction of its threshold is flagged as marginal.
MARGINAL_FRAC = 0.10


def _marginal(value: Optional[float], threshold: float) -> bool:
    return value is not None and threshold <= value < threshold * (1 + MARGINAL_FRAC)


def format_scorecard(r: Dict[str, Any]) -> str:
    lines = [f"\n{r['ticker']}  close ${r['close']:.2f}"]

    lines.append("  UNIVERSE GATES")
    lines.append(f"    {'gate':<12} {'tier':<10} {'threshold':<36} {'value':<44} result")
    for g in r["gates"]:
        val = "--" if g["value"] is None else str(g["value"])
        result = "PASS" if g["passed"] else "MISS"
        if g["gate"] == "adr" and g["passed"] and _marginal(g["value"], 3.5):
            result += " (marginal)"
        lines.append(f"    {g['gate']:<12} {g['tier']:<10} {g['threshold']:<36} {val:<44} {result}")
    opt = ", ".join(r["optional_misses"]) or "none"
    lines.append(f"    -> required: {'PASS' if r['required_pass'] else 'MISS'}   optional misses: {opt}")

    lines.append("  EVENT")
    if r["pivot"] is None:
        lines.append("    no tight base -> no pivot; nothing to break out of")
    else:
        lines.append(f"    pivot ${r['pivot']:.2f}  dist {r['pivot_dist_pct']:+.1f}%  "
                     f"close {'>=' if r['is_breakout'] else '<'} pivot")
        vr = r["vol_ratio"]
        if vr is not None:
            tag = "confirms" if vr >= VOL_CONFIRM_MULT else "light"
            if _marginal(vr, VOL_CONFIRM_MULT):
                tag += " (marginal)"
            lines.append(f"    RVOL {vr:.2f}x vs {VOL_CONFIRM_MULT}x gate -> {tag}")
        if r["breakout_confirmed"]:
            verdict = "CONFIRMED BREAKOUT"
        elif r["is_breakout"]:
            verdict = "broke pivot on light volume"
        else:
            verdict = "no breakout (still in / below base)"
        lines.append(f"    -> {verdict}")

    lines.append("  CLASSIFICATION")
    ema = "yes" if r["ema_lead"] else "no"
    p1 = f"{r['pct_1m']:+.1f}%" if r["pct_1m"] is not None else "--"
    p3 = f"{r['pct_3m']:+.1f}%" if r["pct_3m"] is not None else "--"
    green = "yes" if r["prev_green"] else "no"
    lines.append(f"    ema_lead {ema} | 1M {p1} (Leader >15) | 3M {p3} (Leader >30) | prev green {green}")
    lines.append(f"    -> potent: {'yes' if r['is_potent'] else 'no'}   leader: {'yes' if r['is_leader'] else 'no'}")

    # Overall framing: is a miss about the event or the vehicle?
    if not r["required_pass"]:
        overall = "DISQUALIFIED (required gate miss)"
    elif r["breakout_confirmed"] and r["optional_misses"]:
        overall = f"event CONFIRMED, vehicle caveat ({', '.join(r['optional_misses'])})"
    elif r["breakout_confirmed"]:
        overall = "event CONFIRMED, vehicle clean"
    elif r["optional_misses"]:
        overall = f"no confirmed event; vehicle caveat ({', '.join(r['optional_misses'])})"
    else:
        overall = "no confirmed event; vehicle clean"
    lines.append(f"  VERDICT: {overall}")
    return "\n".join(lines)


async def _run(api_key: str, tickers: list, asof) -> None:
    async with TradierClient(api_key=api_key) as client:
        for t in tickers:
            r = await score_ticker(client, t, asof=asof)
            if r is None:
                print(f"\n{t}: no usable price history (<60 bars or fetch failed)")
            else:
                print(format_scorecard(r))
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Per-gate breakout scorecard")
    ap.add_argument("tickers", nargs="+", help="ticker symbols")
    ap.add_argument("--asof", help="score as of a past completed session, YYYY-MM-DD")
    args = ap.parse_args()

    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("Error: TRADIER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    asof = date.fromisoformat(args.asof) if args.asof else None
    asyncio.run(_run(api_key, [t.upper() for t in args.tickers], asof))


if __name__ == "__main__":
    main()

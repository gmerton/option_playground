#!/usr/bin/env python3
"""
Thursday short-DTE bull put spread screener.

Scans a universe of highly liquid, structurally upward-trending tickers.
For each ticker, enters a bull put spread if:
  1. Spot is above the N-day moving average  (trend filter)
  2. A qualifying 0-5 DTE expiry exists       (Friday or nearest weekly)
  3. A ~0.10Δ short put / ~0.05Δ long put is available with tight bid-ask

Designed to run Thursday morning before market open or at open.

Usage:
    PYTHONPATH=src python run_thursday_screener.py
    PYTHONPATH=src python run_thursday_screener.py --ma 200
    PYTHONPATH=src python run_thursday_screener.py --date 2026-03-12

Requires: TRADIER_API_KEY
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, timedelta
from typing import Optional

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_expirations import list_expirations
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.moving_averages import get_sma


# ── Universe ──────────────────────────────────────────────────────────────────
#
# Backtested 1-DTE bull put spread edge (0.15Δ short / 0.10Δ long, 50% take):
#   COST  +3.93% ROC (20MA)   WMT   +3.57% ROC (20MA)
#   MSFT  +3.26% ROC (none)   META  +3.21% ROC (20MA, critical)
#   HD    +3.39% ROC (50MA)   AAPL  +2.65% ROC (20MA)
# Note: HD edge peaks at 50MA filter (vs 20MA default); use --ma 50 to optimize.
# Excluded: SPY/QQQ (<2% ROC), GLD (different Δ), NVDA/AMZN/GOOGL (negative ROC),
#           V/XLK (<1.5% ROC), JNJ (too thin), BJ (monthly-only — 0 entries at 1 DTE).

UNIVERSE: list[str] = ["AAPL", "COST", "HD", "META", "MSFT", "WMT"]

# Per-ticker MA overrides — backtested optimal filter per name.
# Tickers not listed here use DEFAULT_MA. --ma CLI arg overrides everything.
TICKER_MA: dict[str, int] = {
    "HD":  50,   # peaks at 50MA (+3.39% vs +1.71% at 20MA)
    "WMT": 50,   # peaks at 50MA (+4.10% vs +3.57% at 20MA)
}

# ── Parameters ────────────────────────────────────────────────────────────────

DTE_TARGET      = 1      # target 1 DTE (Thursday → Friday expiry)
DTE_TOL         = 4      # accept 0–5 DTE window
SHORT_DELTA     = 0.15   # target short put delta (unsigned)
WING_DELTA      = 0.05   # wing width in delta terms (long put ≈ SHORT_DELTA - WING_DELTA)
LONG_DELTA      = SHORT_DELTA - WING_DELTA   # 0.10Δ
MAX_DELTA_ERR   = 0.06   # tighter than 20-DTE screener (0.08)
MAX_SPREAD_PCT  = 0.25   # max bid-ask as fraction of mid
PROFIT_TAKE_PCT = 0.50   # 50% profit target
DEFAULT_MA      = 20     # default moving average window for trend filter


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dte(exp_str: str, today: date) -> int:
    return (date.fromisoformat(exp_str) - today).days


def _find_target_expiry(expirations: list[str], today: date) -> Optional[str]:
    """Closest expiry to DTE_TARGET within ±DTE_TOL."""
    best: Optional[str] = None
    best_err = DTE_TOL + 1
    for exp_str in expirations:
        err = abs(_dte(exp_str, today) - DTE_TARGET)
        if err <= DTE_TOL and err < best_err:
            best_err = err
            best = exp_str
    return best


def _find_by_delta(
    contracts: list[dict],
    target_unsigned: float,
    cp: str,
) -> Optional[dict]:
    """Contract closest to target delta within MAX_DELTA_ERR."""
    signed_target = -target_unsigned  # puts have negative delta
    best: Optional[dict] = None
    best_err = MAX_DELTA_ERR + 1.0
    for c in contracts:
        if c.get("option_type") != cp:
            continue
        delta = (c.get("greeks") or {}).get("delta")
        if delta is None:
            continue
        err = abs(float(delta) - signed_target)
        if err <= MAX_DELTA_ERR and err < best_err:
            best_err = err
            best = c
    return best


def _mid(c: dict) -> float:
    bid = c.get("bid") or 0.0
    ask = c.get("ask") or 0.0
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    return float(c.get("last") or 0.0)


def _ba_pct(c: dict) -> Optional[float]:
    bid = c.get("bid") or 0.0
    ask = c.get("ask") or 0.0
    if bid <= 0 or ask <= 0:
        return None
    m = (bid + ask) / 2.0
    return (ask - bid) / m if m > 0 else None


def _fmt_leg(c: dict, label: str, target_delta: float) -> str:
    strike = c.get("strike", 0.0)
    bid    = c.get("bid") or 0.0
    ask    = c.get("ask") or 0.0
    m      = _mid(c)
    delta  = (c.get("greeks") or {}).get("delta")
    sp     = _ba_pct(c)
    sp_str = f"{sp * 100:.1f}%" if sp is not None else " n/a "
    sp_tag = "✓" if sp is not None and sp <= MAX_SPREAD_PCT else "✗"
    d_str  = f"{float(delta):+.3f}" if delta is not None else "  n/a"
    return (
        f"  {label:<6}  P"
        f"  ${strike:>7.2f}"
        f"  bid ${bid:>5.2f}  ask ${ask:>5.2f}  mid ${m:>5.2f}"
        f"  Δ {d_str} (tgt {target_delta:.2f})  BA {sp_str:>6} {sp_tag}"
    )


# ── Per-ticker screening ──────────────────────────────────────────────────────

def _screen_ticker(
    ticker: str,
    spot: float,
    ma_value: Optional[float],
    ma_window: int,
    expirations: list[str],
    chain: list[dict],
    today: date,
) -> dict:
    """
    Returns:
        enter:   bool
        lines:   list[str]   — detail lines for printing
        summary: str         — one-line verdict
        credit:  float|None
        expiry:  str|None
    """
    lines: list[str] = []

    # 1. Trend filter
    if ma_value is None:
        lines.append(f"  Trend: {ma_window}-day MA unavailable (insufficient history)")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (no {ma_window}MA data)",
                "credit": None, "expiry": None}

    above = spot > ma_value
    trend_sym = "✓ above" if above else "✗ below"
    lines.append(
        f"  Trend: spot ${spot:.2f}  {trend_sym}  {ma_window}-day MA ${ma_value:.2f}"
        f"  ({(spot / ma_value - 1) * 100:+.1f}%)"
    )
    if not above:
        return {"enter": False, "lines": lines,
                "summary": f"SKIP  (below {ma_window}MA — no uptrend)", "credit": None, "expiry": None}

    # 2. Expiry
    expiry = _find_target_expiry(expirations, today)
    if not expiry:
        lines.append(f"  No expiry within {DTE_TARGET}±{DTE_TOL} DTE")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no valid expiry)",
                "credit": None, "expiry": None}
    dte = _dte(expiry, today)
    lines.append(f"  Expiry: {expiry}  ({dte} DTE)")

    # 3. Chain guard
    if not chain:
        lines.append("  No option chain data")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no chain)",
                "credit": None, "expiry": None}

    # 4. Short leg (~0.10Δ put)
    short = _find_by_delta(chain, SHORT_DELTA, "put")
    if short is None:
        lines.append(f"  Short {SHORT_DELTA:.2f}Δ put: no match within ±{MAX_DELTA_ERR}Δ")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no short leg)",
                "credit": None, "expiry": None}
    lines.append(_fmt_leg(short, "Short", SHORT_DELTA))

    sp = _ba_pct(short)
    if sp is None or sp > MAX_SPREAD_PCT:
        sp_str = f"{sp * 100:.1f}%" if sp is not None else "n/a"
        lines.append(f"  Short leg bid-ask too wide: {sp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (short BA {sp_str})",
                "credit": None, "expiry": None}

    # 5. Long leg (~0.05Δ put)
    long = _find_by_delta(chain, LONG_DELTA, "put")
    if long is None:
        lines.append(f"  Long  {LONG_DELTA:.2f}Δ put: no match within ±{MAX_DELTA_ERR}Δ")
        return {"enter": False, "lines": lines, "summary": "SKIP  (no long leg)",
                "credit": None, "expiry": None}
    lines.append(_fmt_leg(long, "Long ", LONG_DELTA))

    lsp = _ba_pct(long)
    if lsp is None or lsp > MAX_SPREAD_PCT:
        lsp_str = f"{lsp * 100:.1f}%" if lsp is not None else "n/a"
        lines.append(f"  Long leg bid-ask too wide: {lsp_str} > {MAX_SPREAD_PCT * 100:.0f}%")
        return {"enter": False, "lines": lines, "summary": f"SKIP  (long BA {lsp_str})",
                "credit": None, "expiry": None}

    # 6. Economics
    short_mid = _mid(short)
    long_mid  = _mid(long)
    credit    = short_mid - long_mid
    s_strike  = short.get("strike", 0.0)
    l_strike  = long.get("strike", 0.0)
    width     = s_strike - l_strike   # puts: short strike > long strike

    if credit <= 0 or width <= 0:
        lines.append(f"  Invalid spread — credit ${credit:.3f}  width ${width:.2f}")
        return {"enter": False, "lines": lines, "summary": "SKIP  (invalid spread)",
                "credit": None, "expiry": None}

    max_loss    = width - credit
    credit_pct  = credit / width * 100
    take_at     = credit * (1.0 - PROFIT_TAKE_PCT)
    keep        = credit * PROFIT_TAKE_PCT
    roc_at_take = PROFIT_TAKE_PCT * credit / max_loss * 100

    lines.append("")
    lines.append(f"  Net credit:  ${credit:.3f}/shr  (${credit * 100:.2f}/contract)  credit/width {credit_pct:.1f}%")
    lines.append(f"  Spread:      ${s_strike:.2f}P / ${l_strike:.2f}P  width ${width:.2f}  max loss ${max_loss:.3f}/shr")
    lines.append(
        f"  Take profit: close ≤ ${take_at:.3f}  "
        f"(keep {int(PROFIT_TAKE_PCT * 100)}% = ${keep:.3f}/shr  ROC {roc_at_take:.1f}%)"
    )

    s_delta   = (short.get("greeks") or {}).get("delta")
    l_delta   = (long.get("greeks")  or {}).get("delta")
    sd_str    = f"{abs(float(s_delta)):.2f}Δ" if s_delta is not None else "?Δ"
    ld_str    = f"{abs(float(l_delta)):.2f}Δ" if l_delta is not None else "?Δ"
    summary   = (
        f"short ${s_strike:.2f}P({sd_str}) / buy ${l_strike:.2f}P({ld_str})"
        f"   net ${credit:.3f}cr   width ${width:.2f}   ROC@50% {roc_at_take:.1f}%"
    )

    return {"enter": True, "lines": lines, "summary": summary,
            "credit": credit, "expiry": expiry}


# ── Async fetch helpers ───────────────────────────────────────────────────────

async def _safe_spot(ticker: str, client: TradierClient) -> Optional[float]:
    try:
        return await get_underlying_price(ticker, client=client)
    except Exception:
        return None


async def _safe_expirations(ticker: str, client: TradierClient) -> list[str]:
    try:
        return await list_expirations(ticker, client=client)
    except Exception:
        return []


async def _safe_chain(ticker: str, expiry: str, client: TradierClient) -> list[dict]:
    try:
        return await list_contracts_for_expiry(ticker, expiry, client=client)
    except Exception:
        return []


async def _safe_sma(ticker: str, ma_window: int, client: TradierClient) -> Optional[float]:
    try:
        result = await get_sma(client, ticker)
        if ma_window == 20:
            return result.sma_20
        elif ma_window == 50:
            return result.sma_50
        elif ma_window == 150:
            return result.sma_150
        elif ma_window == 200:
            return result.sma_200
        return result.sma_20
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

async def run(today: date, ma_window: int, override_ma: bool = False) -> None:
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("ERROR: TRADIER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    W   = 76
    BAR = "═" * W
    bar = "─" * W

    async with TradierClient(api_key=api_key) as client:

        # Resolve per-ticker MA windows (--ma-override forces one value for all tickers)
        ticker_ma_windows = (
            {t: ma_window for t in UNIVERSE} if override_ma
            else {t: TICKER_MA.get(t, ma_window) for t in UNIVERSE}
        )

        # Fetch VIX, spots, expirations, and MAs in parallel
        vix_task  = _safe_spot("VIX", client)
        spot_tasks = [_safe_spot(t, client) for t in UNIVERSE]
        exp_tasks  = [_safe_expirations(t, client) for t in UNIVERSE]
        ma_tasks   = [_safe_sma(t, ticker_ma_windows[t], client) for t in UNIVERSE]

        results = await asyncio.gather(
            vix_task,
            *spot_tasks,
            *exp_tasks,
            *ma_tasks,
        )

        n = len(UNIVERSE)
        vix    = results[0]
        spots  = list(results[1      : 1 + n])
        exps   = list(results[1 + n  : 1 + 2*n])
        mas    = list(results[1 + 2*n: 1 + 3*n])

        if vix is None:
            print("WARNING: Could not fetch VIX (markets may be closed).", file=sys.stderr)
            vix = 0.0

        # Fetch chains only for tickers that have a qualifying expiry AND are above MA
        chain_map: dict[str, list[dict]] = {}
        chain_fetch_needed: list[tuple[int, str, str]] = []

        for i, ticker in enumerate(UNIVERSE):
            spot   = spots[i]
            ma_val = mas[i]
            expiry = _find_target_expiry(exps[i], today) if exps[i] else None
            if spot and ma_val and spot > ma_val and expiry:
                chain_fetch_needed.append((i, ticker, expiry))

        if chain_fetch_needed:
            chains_raw = await asyncio.gather(
                *[_safe_chain(t, e, client) for _, t, e in chain_fetch_needed]
            )
            for (i, ticker, expiry), ch in zip(chain_fetch_needed, chains_raw):
                chain_map[ticker] = ch

    # ── Print results ─────────────────────────────────────────────────────────

    print(f"\n{BAR}")
    vix_str = f"{vix:.2f}" if vix else "n/a"
    ma_note = f"default {ma_window}MA" + (
        "  " + "  ".join(f"{t}:{w}MA" for t, w in ticker_ma_windows.items() if w != ma_window)
        if any(w != ma_window for w in ticker_ma_windows.values()) else ""
    )
    print(f"  THURSDAY SHORT-DTE SCREENER  ·  {today}  ·  VIX: {vix_str}")
    print(f"  Bull Put Spread  ·  ~{SHORT_DELTA:.0%}Δ short / ~{LONG_DELTA:.0%}Δ long  ·  "
          f"0–5 DTE  ·  {PROFIT_TAKE_PCT:.0%} profit take  ·  trend: {ma_note}")
    print(f"{BAR}")

    enters: list[tuple[str, dict]] = []
    skips:  list[tuple[str, dict]] = []

    for i, ticker in enumerate(UNIVERSE):
        spot   = spots[i]
        ma_val = mas[i]
        spot_str = f"${spot:.2f}" if spot else "n/a"

        print(f"\n{bar}")
        print(f"  {ticker}  ·  {spot_str}")
        print(bar)

        chain     = chain_map.get(ticker, [])
        t_ma_win  = ticker_ma_windows[ticker]
        result = _screen_ticker(
            ticker=ticker,
            spot=spot or 0.0,
            ma_value=ma_val,
            ma_window=t_ma_win,
            expirations=exps[i],
            chain=chain,
            today=today,
        )

        for line in result["lines"]:
            print(line)

        if result["enter"]:
            print(f"\n  🟢  ENTER   —  {result['summary']}")
            enters.append((ticker, result))
        else:
            print(f"\n  🔴  SKIP    —  {result['summary']}")
            skips.append((ticker, result))

    # ── Summary ───────────────────────────────────────────────────────────────

    print(f"\n{BAR}")
    print(f"  SUMMARY  ·  {today}  ·  VIX {vix_str}  ·  {ma_note}")
    print(f"{BAR}")

    if enters:
        print(f"\n  🟢  ENTER ({len(enters)} signal{'s' if len(enters) != 1 else ''}):\n")
        for ticker, r in enters:
            spot = spots[UNIVERSE.index(ticker)]
            spot_str = f"${spot:.2f}" if spot else ""
            print(f"  {'':2}{ticker:<6}  {spot_str:<8}  {r['summary']}")
            print(f"  {'':10}expiry {r['expiry']}")
    else:
        print("\n  No ENTER signals today.")

    if skips:
        print(f"\n  🔴  SKIP ({len(skips)}):\n")
        for ticker, r in skips:
            print(f"  {'':2}{ticker:<6}  {r['summary']}")

    print(f"\n{BAR}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thursday short-DTE bull put spread screener",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date", type=date.fromisoformat, default=date.today(),
        help="Run date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--ma", type=int, default=DEFAULT_MA, choices=[20, 50, 150, 200],
        help="Moving average window for trend filter (default 20)",
    )
    parser.add_argument(
        "--ma-override", action="store_true",
        help="Force --ma value for all tickers, ignoring per-ticker defaults",
    )
    args = parser.parse_args()
    asyncio.run(run(args.date, args.ma, override_ma=args.ma_override))


if __name__ == "__main__":
    main()

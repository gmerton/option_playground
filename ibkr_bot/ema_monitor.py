#!/usr/bin/env python3
"""
EMA crossover monitor (v1, alert-only).

Watches one or more symbols on live 1-minute bars and notifies you whenever the
9 EMA crosses the 20 EMA. No orders are placed.

Usage:
  .venv/bin/python3 ibkr_bot/ema_monitor.py SPY
  .venv/bin/python3 ibkr_bot/ema_monitor.py SPY AAPL QQQ

Notifies via the terminal (with a bell) and a macOS banner + sound. The first
banner may trigger a one-time macOS permission prompt for your terminal app.
Connects to the paper account via conn.py (IB_PORT default 4002). Ctrl-C stops.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

import pandas as pd
from ib_async import Stock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402

FAST, SLOW = 9, 20
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerts.log")


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _emas(closes: pd.Series) -> tuple[pd.Series, pd.Series]:
    return (
        closes.ewm(span=FAST, adjust=False).mean(),
        closes.ewm(span=SLOW, adjust=False).mean(),
    )


def _session_vwap(bars) -> float | None:
    """Volume-weighted average price over the given bars, using each bar's WAP
    (falls back to the typical price if WAP is missing)."""
    num = den = 0.0
    for b in bars:
        wap = b.average if b.average else (b.high + b.low + b.close) / 3
        num += wap * b.volume
        den += b.volume
    return num / den if den else None


def _cross_at_last(ema_fast: pd.Series, ema_slow: pd.Series) -> str | None:
    """Return 'bull'/'bear' if the spread flipped sign on the final point."""
    if len(ema_fast) < 2:
        return None
    prev = ema_fast.iloc[-2] - ema_slow.iloc[-2]
    cur = ema_fast.iloc[-1] - ema_slow.iloc[-1]
    if prev <= 0 < cur:
        return "bull"
    if prev >= 0 > cur:
        return "bear"
    return None


def _last_cross(closes: pd.Series, times: list) -> tuple[str, object] | None:
    """Scan a series for the most recent crossover (for startup context)."""
    ef, es = _emas(closes)
    spread = ef - es
    for i in range(len(spread) - 1, 0, -1):
        a, b = spread.iloc[i - 1], spread.iloc[i]
        if a != 0 and b != 0 and (a > 0) != (b > 0):
            return ("bull" if b > 0 else "bear", times[i])
    return None


def _fmt_time(d) -> str:
    try:
        return d.strftime("%H:%M")
    except Exception:
        return str(d)


def _notify(symbol: str, direction: str, price: float, vwap: float | None, when: str) -> None:
    word = "ABOVE" if direction == "bull" else "BELOW"
    arrow = "^^" if direction == "bull" else "vv"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if vwap is not None:
        vwap_part = f"VWAP {vwap:.2f} (px {'above' if price > vwap else 'below'})"
    else:
        vwap_part = "VWAP n/a"
    msg = (f"{symbol}: 9 EMA crossed {word} 20 EMA  |  price {price:.2f}  "
           f"{vwap_part}  (bar {when})")
    line = f"[{stamp}]  {arrow} {msg}"
    bar = "=" * 64
    print(f"\a\n{bar}\n  {line}\n{bar}\n", flush=True)
    _log(line)
    _mac_alert(f"{symbol} EMA cross ({direction})", msg)


def _mac_alert(title: str, msg: str) -> None:
    """Persistent macOS dialog (stays until dismissed) plus a sound.

    Fired non-blocking via Popen so the monitor keeps processing bars while the
    dialog is open; each crossover spawns its own dialog, so simultaneous
    crosses stack as separate prompts. System Events hosts the dialog so it
    comes to the front.
    """
    safe_msg = msg.replace("\\", "").replace('"', "'")
    safe_title = title.replace("\\", "").replace('"', "'")
    script = (
        'tell application "System Events" to display dialog '
        f'"{safe_msg}" with title "{safe_title}" '
        'buttons {"Dismiss"} default button "Dismiss" with icon caution'
    )
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Glass.aiff"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _on_bar_update(bars, has_new_bar: bool) -> None:
    # Only act when a bar has just closed; bars[-1] is the new forming bar,
    # bars[-2] is the bar that just finalized.
    if not has_new_bar or len(bars) < SLOW + 2:
        return
    closed_bars = bars[:-1]
    ef, es = _emas(pd.Series([b.close for b in closed_bars]))
    direction = _cross_at_last(ef, es)
    if direction:
        last = bars[-2]
        _notify(bars.contract.symbol, direction, last.close,
                _session_vwap(closed_bars), _fmt_time(last.date))


def main() -> int:
    symbols = [s.upper() for s in sys.argv[1:]]
    if not symbols:
        print("usage: ema_monitor.py SYMBOL [SYMBOL ...]")
        return 1

    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "12")))
    print(f"OK Connected (paper {ib.managedAccounts()}). Monitoring: {', '.join(symbols)}\n")
    _log(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] --- session start: monitoring {', '.join(symbols)} ---")

    for sym in symbols:
        contract = Stock(sym, "SMART", "USD")
        if not ib.qualifyContracts(contract):
            print(f"  x {sym}: could not qualify -- skipping")
            continue
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr="1 D",
            barSizeSetting="1 min",
            whatToShow="TRADES",
            useRTH=True,
            keepUpToDate=True,
        )
        if not bars:
            print(f"  ! {sym}: no bars yet (market closed or no data) -- will alert when live")
        else:
            closes = pd.Series([b.close for b in bars])
            ef, es = _emas(closes)
            rel = "ABOVE (bullish)" if ef.iloc[-1] > es.iloc[-1] else "BELOW (bearish)"
            lc = _last_cross(closes, [b.date for b in bars])
            extra = f"; last cross was {lc[0]} @ {_fmt_time(lc[1])}" if lc else ""
            print(f"  {sym}: 9EMA={ef.iloc[-1]:.3f}  20EMA={es.iloc[-1]:.3f}  "
                  f"-> 9 is {rel}{extra}")
        bars.updateEvent += _on_bar_update

    print("\nWatching for crossovers (live during market hours). Ctrl-C to stop.\n")
    try:
        ib.run()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        if ib.isConnected():
            ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

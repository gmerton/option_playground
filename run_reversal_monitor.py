#!/usr/bin/env python3
"""
Intraday reversal-up-on-volume monitor for the preferred-ticker universe.

Catches the "flush then reverse" (MFR-style) setup: a name that sold off to an
intraday low and is now swinging back UP on elevated volume. Quote-based (Tradier
batch quotes) — no IB Gateway needed. Keeps state between runs so it can tell
"rising vs the last poll", not just a static off-the-low snapshot.

A ticker FIRES when ALL hold:
  1. Real swing low today:   (high - low) / low >= --min-swing      (default 2.5%)
  2. Recovered off the low:  (last - low) / (high - low) >= --recover (default 0.50)
  3. Elevated volume PACE:   today_vol / (avg_daily_vol * frac_of_day) >= --vol (1.5)
  4. Rising since last poll:  last > previous-poll last  (skipped on the first run)
Optional plus (shown, not required): reclaimed the day's open.

Run (market hours; key from ~/.bash_profile):
  source ~/.bash_profile && PYTHONPATH=src .venv/bin/python3 run_reversal_monitor.py
  ... --universe data/preferred_tickers.txt --vol 1.5 --recover 0.5 --min-swing 2.5
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO = Path(__file__).resolve().parent
STATE = REPO / "data" / "watchlist" / "reversal_state.json"
API = "https://api.tradier.com/v1"
ET = ZoneInfo("America/New_York")


def _headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def fetch_quotes(symbols: list[str], key: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(symbols), 100):  # chunk to keep URLs sane
        chunk = symbols[i : i + 100]
        r = requests.get(f"{API}/markets/quotes", params={"symbols": ",".join(chunk)},
                         headers=_headers(key), timeout=20)
        r.raise_for_status()
        q = r.json().get("quotes", {}).get("quote", [])
        if isinstance(q, dict):
            q = [q]
        for item in q:
            out[item["symbol"]] = item
    return out


def fraction_of_session(key: str) -> tuple[float, str]:
    """Fraction of the 9:30–16:00 ET session elapsed, and market state."""
    c = requests.get(f"{API}/markets/clock", headers=_headers(key), timeout=20).json()
    clock = c.get("clock", {})
    now = datetime.fromtimestamp(clock.get("timestamp", 0), ET)
    open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
    total = (close_t - open_t).total_seconds()
    frac = (now - open_t).total_seconds() / total
    return max(0.02, min(1.0, frac)), clock.get("state", "?")


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="data/preferred_tickers.txt")
    ap.add_argument("--vol", type=float, default=1.5, help="min volume pace (today vs avg, day-fraction adjusted)")
    ap.add_argument("--recover", type=float, default=0.50, help="min recovery off low (0=at low, 1=at high)")
    ap.add_argument("--min-swing", type=float, default=2.5, help="min intraday high→low swing %% to qualify as a flush")
    ap.add_argument("--ext-chg", type=float, default=7.0, help="chg%% at/above which a name is 'over-extended' (don't initiate)")
    ap.add_argument("--ext-recover", type=float, default=0.88, help="recovery fraction at/above which it's back near highs = extended")
    args = ap.parse_args()

    key = os.environ.get("TRADIER_API_KEY")
    if not key:
        raise SystemExit("TRADIER_API_KEY not set (source ~/.bash_profile first).")

    symbols = [s.strip().upper() for s in Path(args.universe).read_text().split() if s.strip()]
    frac, mkt_state = fraction_of_session(key)
    quotes = fetch_quotes(symbols, key)
    prev = load_state()
    prev_q = prev.get("quotes", {})

    now_et = datetime.now(ET).strftime("%H:%M:%S ET")
    fires, new_state = [], {}
    for sym, q in quotes.items():
        last = q.get("last")
        hi, lo, op = q.get("high"), q.get("low"), q.get("open")
        vol, avgvol = q.get("volume") or 0, q.get("average_volume") or 0
        if not (last and hi and lo and lo > 0 and hi > lo):
            continue
        new_state[sym] = last
        swing = (hi - lo) / lo * 100
        recovery = (last - lo) / (hi - lo)
        pace = vol / (avgvol * frac) if avgvol else 0.0
        prev_last = prev_q.get(sym)
        rising = (prev_last is None) or (last > prev_last)
        if swing >= args.min_swing and recovery >= args.recover and pace >= args.vol and rising:
            chg = q.get("change_percentage") or 0
            reclaimed_open = op is not None and last >= op
            risk_low = (last - lo) / last * 100  # % down to today's low (a backstop stop)
            extended = chg >= args.ext_chg or recovery >= args.ext_recover
            buy = (not extended) and reclaimed_open and 0.40 <= recovery <= 0.85
            fires.append({
                "sym": sym, "last": last, "chg": chg,
                "swing": swing, "recovery": recovery, "pace": pace,
                "reclaimed_open": reclaimed_open, "risk_low": risk_low,
                "zone": "BUY" if buy else ("EXT" if extended else "·"),
                "delta": (last - prev_last) if prev_last else None,
                "score": recovery * pace,
            })

    fires.sort(key=lambda f: f["score"], reverse=True)
    first_run = not prev_q

    print(f"\n=== REVERSAL MONITOR — {now_et} | market {mkt_state} | "
          f"{len(symbols)} names | session {frac*100:.0f}% elapsed ===")
    if first_run:
        print("(first run — baseline set; 'rising vs last poll' applies from the next run)")
    if not fires:
        print("No reversal-up-on-volume signals right now.")
    else:
        buys = [f for f in fires if f["zone"] == "BUY"]
        print("BUY-NOW candidates (reversing, NOT extended, tight stop available):")
        if buys:
            for f in sorted(buys, key=lambda f: f["score"], reverse=True):
                print(f"  {f['sym']:6} ${f['last']:.2f}  +{f['chg']:.1f}%  off-low {f['recovery']*100:.0f}%  "
                      f"volpace {f['pace']:.1f}x  stop≈day-low (−{f['risk_low']:.1f}%)")
        else:
            print("  (none right now — reversers are either still below their reclaim or already extended)")
        print(f"\n{'SYM':6}{'last':>10}{'chg%':>8}{'swing%':>8}{'off-low':>9}{'volpace':>9}{'Δpoll':>9}{'zone':>6}")
        for f in fires:
            dlt = f"{f['delta']:+.2f}" if f["delta"] is not None else "  —"
            print(f"{f['sym']:6}{f['last']:>10.2f}{f['chg']:>8.1f}{f['swing']:>8.1f}"
                  f"{f['recovery']*100:>8.0f}%{f['pace']:>9.1f}{dlt:>9}{f['zone']:>6}")

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"ts": now_et, "quotes": new_state}, indent=0))


if __name__ == "__main__":
    main()

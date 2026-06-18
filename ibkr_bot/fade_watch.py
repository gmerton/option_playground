#!/usr/bin/env python3
"""
VWAP reclaim-buy signal (alert-only). The premium intraday entry: a name that
BROKE its pivot, FADED below VWAP (shakeout), then RECLAIMED VWAP on volume.
The fade gives you a tight, defined stop (the fade low); the reclaim confirms
demand returned. NO orders -- this is a heads-up.

The signal (all required -- strict, post-breakout shakeouts only):
  1. ELIGIBLE  -- intraday high reached the pivot (20-day high). A reclaim far
                 below the pivot is just a dead-cat, not a buy.
  2. FADED     -- after the break, price traded BELOW VWAP (the shakeout). The
                 lowest low during that fade is tracked = your stop.
  3. RECLAIM   -- a green 1-min bar closes back ABOVE VWAP...
  4. ON VOLUME -- ...with projected EOD volume >= --reclaim-vol x avg (default 1.2).
  -> RECLAIM BUY: buy-stop above the reclaim bar, STOP = fade low, sized by risk.
     Grade A if the fade held above the pivot (breakout intact); B if it dipped
     below the pivot / filled the gap (deeper damage, weaker).

Also keeps two safety alerts:
  FADE (lost VWAP)  -- exit warning for a position you're already holding.
  status table      -- STRONG/HOLDING/FILLING/FILLED, refreshed each minute.

Prior close uses daily_bars_completed() (today's in-progress bar stripped).

Usage:
  .venv/bin/python3 ibkr_bot/fade_watch.py                 # full roster
  .venv/bin/python3 ibkr_bot/fade_watch.py AMD INTC DAL
  .venv/bin/python3 ibkr_bot/fade_watch.py --reclaim-vol 1.5 --account 100000 AMD
Paper account via conn.py. Ctrl-C stops.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import json
from datetime import datetime

import pandas as pd
from ib_async import Stock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from conn import connect_ib, daily_bars_completed  # noqa: E402

LOG_PATH = os.path.join(HERE, "alerts.log")
RTH_MIN = 390
MIN_ELAPSED = 2.0
# defaults overridden by CLI
RECLAIM_VOL = 1.2          # projected-EOD volume multiple required on the reclaim
ACCOUNT = 100000.0
RISK_PCT = 0.75
MAX_NOTIONAL_PCT = 25.0
VWAP_BAND_FRAC = 0.20      # VWAP deadband = this x ADR% (Schmitt trigger -- kills VWAP-dance noise)
VWAP_BAND_FLOOR = 0.10     # ...but never tighter than this % (floor)
MAX_FADE = 2               # cap FADE exit-warnings per name (you only exit once)

# default watch set = the breakout roster (pivot gate filters to real candidates)
DEFAULT = ["AMD", "AMAT", "AMKR", "INTC", "ONTO", "UCTT", "KEYS", "ADI", "FTNT",
           "CRWD", "PANW", "DAL", "UAL", "STT", "FITB", "C", "IBKR", "MS",
           "RVMD", "CVS", "RPRX", "JBHT", "CAT", "ARMK"]

try:
    THEMES = json.load(open(os.path.join(os.path.dirname(HERE), "data", "theme_scores.json")))
except Exception:
    THEMES = {}

STATE: dict[str, dict] = {}
_last_print_min = {"v": None}


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _mac_alert(title: str, msg: str) -> None:
    safe_msg = msg.replace("\\", "").replace('"', "'")
    safe_title = title.replace("\\", "").replace('"', "'")
    script = ('tell application "System Events" to display dialog '
              f'"{safe_msg}" with title "{safe_title}" '
              'buttons {"Dismiss"} default button "Dismiss" with icon caution')
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _buffer(price: float) -> float:
    return max(0.02, round(price * 0.0003, 2))


def _position(entry: float, stop: float, size_mult: float) -> dict:
    dist = entry - stop
    if dist <= 0:
        return {"shares": 0, "risk": 0.0, "notional": 0.0, "capped": False}
    base = ACCOUNT * (RISK_PCT / 100.0)
    raw = int((base * size_mult) / dist)
    cap = int(ACCOUNT * (MAX_NOTIONAL_PCT / 100.0) / entry)
    sh = min(raw, cap)
    return {"shares": sh, "risk": sh * dist, "notional": sh * entry, "capped": raw > cap}


def _session_vwap(bars):
    num = den = 0.0
    for b in bars:
        wap = b.average if b.average else (b.high + b.low + b.close) / 3
        num += wap * b.volume
        den += b.volume
    return num / den if den else None


def _session_stats(closed):
    cum = float(sum(b.volume for b in closed))
    t0, t1 = closed[0].date, closed[-1].date
    elapsed = (t1 - t0).total_seconds() / 60.0 + 1.0
    frac = min(elapsed / RTH_MIN, 1.0)
    return cum, elapsed, frac


def _classify(price, vwap, open_px, prevclose):
    if price <= prevclose:
        return "FILLED"
    if vwap is None:
        return "HOLDING"
    if price < vwap:
        return "FILLING"
    if price >= open_px:
        return "STRONG"
    return "HOLDING"


def _fmt(d):
    return d.strftime("%H:%M") if hasattr(d, "strftime") else str(d)


def _buy_alert(sym, st, entry, stop, grade, pos, pace, vwap, when):
    risk_pct = (entry - stop) / entry * 100
    cap = " [notional-capped]" if pos["capped"] else ""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (f"{sym} [{st['theme']}] RECLAIM BUY ({grade}): faded to {stop:.2f}, "
           f"reclaimed VWAP {vwap:.2f} -> BUY-STOP {entry:.2f}, STOP {stop:.2f} "
           f"(fade low, {risk_pct:.1f}%)  |  BUY ~{pos['shares']} sh = ${pos['notional']:,.0f}, "
           f"risk ${pos['risk']:,.0f} (x{st['size_mult']:.2f}){cap}  |  pace {pace:.2f}x  (bar {when})")
    bar = "=" * 76
    print(f"\a\n{bar}\n  $$ {msg}\n{bar}\n", flush=True)
    _log(f"[{stamp}]  $$ RECLAIM-BUY {msg}")
    _mac_alert(f"{sym} RECLAIM BUY ({grade})", msg)


def _fade_alert(sym, st, price, vwap, when, tag=""):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (f"{sym} [{st['theme']}] FADE -- lost VWAP {vwap:.2f} by >{st['band_pct']:.2f}% band "
           f"(px {price:.2f}). Exit warning if held.{tag}  (bar {when})")
    bar = "-" * 70
    print(f"\a\n{bar}\n  >> {msg}\n{bar}\n", flush=True)
    _log(f"[{stamp}]  >> FADE {msg}")
    _mac_alert(f"{sym} FADE (lost VWAP)", msg)


def _print_table():
    rows = [s for s in STATE.values() if s.get("price") is not None]
    if not rows:
        return
    order = {"STRONG": 0, "HOLDING": 1, "FILLING": 2, "FILLED": 3}
    rows.sort(key=lambda s: (order.get(s["status"], 9), -s["retained"]))
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{stamp}] reclaim-buy watch  (elig=broke pivot, B=faded<VWAP, R=reclaim fired)")
    print(f"  {'SYM':5} {'THEME':13} {'last':>8} {'day%':>6} {'vwapD%':>7} "
          f"{'pace':>5} {'STATUS':8} {'eBR':>4} {'fadeLo':>8}")
    for s in rows:
        flags = ("E" if s["broke_pivot"] else ".") + ("B" if s["below_vwap_seen"] else ".") + \
                ("R" if s["reclaim_fired"] else ".")
        fl = f"{s['fade_low']:.2f}" if s["fade_low"] else "-"
        print(f"  {s['sym']:5} {str(s['theme'])[:13]:13} {s['price']:8.2f} {s['gap']:+6.1f} "
              f"{s['vwap_delta']:+7.1f} {s['pace']:5.2f} {s['status']:8} {flags:>4} {fl:>8}")


def _on_bar_update(bars, has_new_bar: bool) -> None:
    if not has_new_bar or len(bars) < 2:
        return
    sym = bars.contract.symbol
    st = STATE.get(sym)
    if not st:
        return
    closed = bars[:-1]
    last = closed[-1]
    price = float(last.close); bhigh = float(last.high)
    blow = float(last.low); bopen = float(last.open)
    if st["open"] is None:
        st["open"] = float(closed[0].open)
    cum, elapsed, frac = _session_stats(closed)
    if elapsed < MIN_ELAPSED or frac <= 0:
        return
    pace = (cum / frac) / st["avgvol"] if st["avgvol"] else 0.0
    vwap = _session_vwap(closed)
    when = _fmt(last.date)

    # VWAP deadband scaled to the name's own volatility (Schmitt trigger): state
    # flips to "above" only when price clears VWAP+band, to "below" only when it
    # clears VWAP-band. Inside the band the state HOLDS -- so a grinder (C/STT)
    # dancing on the line never re-fires. band = band_pct% of VWAP.
    band = (vwap * st["band_pct"] / 100.0) if vwap else 0.0
    prev_state = st["vwap_state"]
    if vwap is None:
        new_state = prev_state
    elif price >= vwap + band:
        new_state = "above"
    elif price <= vwap - band:
        new_state = "below"
    else:                                   # inside the band -> hold current state
        new_state = prev_state or ("above" if price >= vwap else "below")

    # eligibility: did intraday high reach the pivot?
    if bhigh >= st["pivot"]:
        st["broke_pivot"] = True
    # track the fade low while genuinely below the band
    if st["broke_pivot"] and new_state == "below":
        st["below_vwap_seen"] = True
        st["fade_low"] = blow if st["fade_low"] is None else min(st["fade_low"], blow)

    # table state (display uses raw VWAP)
    gap = price / st["prevclose"] - 1
    denom = st["open"] - st["prevclose"]
    retained = ((price - st["prevclose"]) / denom * 100) if abs(denom) > 1e-9 else 0.0
    st.update({"price": price, "gap": gap * 100, "retained": retained, "pace": pace,
               "vwap_delta": (price / vwap - 1) * 100 if vwap else 0.0,
               "status": _classify(price, vwap, st["open"], st["prevclose"])})

    # alerts fire only on a CONFIRMED band crossing (hysteresis) -- not every wiggle
    if prev_state == "above" and new_state == "below" and st["broke_pivot"]:
        if st["fade_count"] < MAX_FADE:                 # you only exit once -- cap the warnings
            st["fade_count"] += 1
            tag = " [final fade alert]" if st["fade_count"] >= MAX_FADE else ""
            _fade_alert(sym, st, price, vwap, when, tag)
    elif prev_state == "below" and new_state == "above":
        # RECLAIM BUY: cleared back above the band on a green bar, on volume
        if (st["broke_pivot"] and st["below_vwap_seen"] and not st["reclaim_fired"]
                and price > bopen and pace >= RECLAIM_VOL and st["fade_low"] is not None):
            entry = bhigh + _buffer(bhigh)
            stop = st["fade_low"]
            grade = "A" if stop >= st["pivot"] else "B"   # A = breakout level held through the fade
            if entry > stop:
                st["reclaim_fired"] = True
                _buy_alert(sym, st, entry, stop, grade,
                           _position(entry, stop, st["size_mult"]), pace, vwap, when)

    st["vwap_state"] = new_state

    m = last.date.strftime("%Y-%m-%d %H:%M") if hasattr(last.date, "strftime") else str(last.date)
    if _last_print_min["v"] != m:
        _last_print_min["v"] = m
        _print_table()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*", help="subset to watch (default: full roster)")
    ap.add_argument("--reclaim-vol", type=float, default=1.2,
                    help="projected-EOD volume multiple required on the reclaim (default 1.2)")
    ap.add_argument("--account", type=float, default=100000.0)
    ap.add_argument("--risk-pct", type=float, default=0.75)
    ap.add_argument("--max-notional-pct", type=float, default=25.0)
    ap.add_argument("--vwap-band-frac", type=float, default=0.20,
                    help="VWAP deadband as a fraction of ADR%% -- kills VWAP-dance noise (default 0.20)")
    ap.add_argument("--max-fade", type=int, default=2,
                    help="max FADE exit-warnings per name (default 2)")
    args = ap.parse_args()
    global RECLAIM_VOL, ACCOUNT, RISK_PCT, MAX_NOTIONAL_PCT, VWAP_BAND_FRAC, MAX_FADE
    RECLAIM_VOL, ACCOUNT = args.reclaim_vol, args.account
    RISK_PCT, MAX_NOTIONAL_PCT = args.risk_pct, args.max_notional_pct
    VWAP_BAND_FRAC, MAX_FADE = args.vwap_band_frac, args.max_fade

    syms = [s.upper() for s in args.symbols] or DEFAULT
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "22")))
    print(f"OK Connected (paper {ib.managedAccounts()}). Reclaim-buy watch: {', '.join(syms)}")
    print(f"  signal = broke pivot -> faded < VWAP -> green reclaim of VWAP on >= {RECLAIM_VOL}x vol; "
          f"stop = fade low.")
    print(f"  VWAP deadband = {VWAP_BAND_FRAC:.2f} x ADR%% (floor {VWAP_BAND_FLOOR:.2f}%%), "
          f"max {MAX_FADE} fade-warnings/name -- filters the dance.\n")
    _log(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] --- reclaim-buy watch start: {', '.join(syms)} ---")

    for sym in syms:
        c = Stock(sym, "SMART", "USD")
        if not ib.qualifyContracts(c):
            print(f"  x {sym}: could not qualify -- skipping"); continue
        daily = daily_bars_completed(ib, c, "60 D")
        if not daily or len(daily) < 25:
            print(f"  ! {sym}: insufficient daily history -- skipping"); continue
        closes = pd.Series([b.close for b in daily])
        highs = pd.Series([b.high for b in daily])
        lows = pd.Series([b.low for b in daily])
        vols = pd.Series([float(b.volume) for b in daily])
        adr_pct = float(((highs - lows) / closes).tail(20).mean() * 100)
        ts = THEMES.get(sym, {})
        STATE[sym] = {
            "sym": sym, "prevclose": float(closes.iloc[-1]),
            "pivot": float(highs.tail(20).max()), "avgvol": float(vols.tail(50).mean()),
            "adr": adr_pct, "band_pct": max(VWAP_BAND_FLOOR, VWAP_BAND_FRAC * adr_pct),
            "theme": ts.get("theme", "-"), "size_mult": ts.get("size_mult", 1.0),
            "open": None, "broke_pivot": False, "below_vwap_seen": False,
            "fade_low": None, "reclaim_fired": False, "vwap_state": None, "fade_count": 0,
            "price": None, "gap": 0.0, "retained": 0.0, "pace": 0.0,
            "vwap_delta": 0.0, "status": "-",
        }
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 D",
                                    barSizeSetting="1 min", whatToShow="TRADES",
                                    useRTH=True, keepUpToDate=True)
        bars.updateEvent += _on_bar_update

    if not STATE:
        print("No symbols armed."); ib.disconnect(); return 1
    print(f"Watching {len(STATE)} names for RECLAIM BUYs. Ctrl-C to stop.\n")
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

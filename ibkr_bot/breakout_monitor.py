#!/usr/bin/env python3
"""
Breakout entry monitor (alert-only), ADR-adaptive two-stage confirmation.

Watches live 1-minute bars and pings you when a focus-list name breaks out -- but
tuned so you neither buy the first wick nor miss a runaway move. NO orders placed.

Two pings per name (whichever the tape gives you first):
  Ping 1  ARM    -- breakout confirmed; hands you a BUY-STOP at the confirming
                    bar's high + a tick, so the market must keep going to fill you.
  Ping 2  RETEST -- price broke, pulled back to the pivot, and a green bar held it
                    (often the higher-quality entry on the grinders).

Confirmation strength adapts to each name's ADR (computed live):
  GRINDER (ADR < split, e.g. STT/FITB/C): skip the first 5 min (let the opening
          range form), then need 2 consecutive 1-min closes above max(pivot, OR-high),
          above VWAP. Patient -- low-ADR names don't run away, so whipsaw is the risk.
  MOVER   (ADR >= split, e.g. AMD/AMKR/semis): 1 volume-confirmed close above the
          pivot, above VWAP. Fast -- these gap-and-go, so missing it is the risk.
Both require projected EOD volume >= 1.5x avg for Ping 1; VWAP filter on both pings.

Levels are RE-DERIVED at startup from IB daily bars (so they match the live feed):
  trigger = 20-day high (group 1/3) or 5-day high (group 2 early entry)
  stop    = 20-day EMA of closes ; hard invalidation = 10-day low
  adr%    = mean (high-low)/close over 20 sessions ; vol baseline = 50-day mean
Derived levels + grinder/mover mode print at startup -- eyeball vs TC2000.

Usage:
  .venv/bin/python3 ibkr_bot/breakout_monitor.py                 # all configured
  .venv/bin/python3 ibkr_bot/breakout_monitor.py STT JBHT C
  .venv/bin/python3 ibkr_bot/breakout_monitor.py --adr-split 4.5 --vol-mult 1.5

Notifies via terminal bell + macOS banner/sound + alerts.log. Paper account via
conn.py. Ctrl-C stops.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

import pandas as pd
from ib_async import Stock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from conn import connect_ib, daily_bars_completed  # noqa: E402

LOG_PATH = os.path.join(HERE, "alerts.log")
# Canonical S3 location of the bridge the EOD Lambda (preferred-breakout-scan)
# writes after close. `--s3` pulls this; `--watchlist s3://...` overrides it.
DEFAULT_WATCHLIST_S3 = "s3://gmerton-stock-data/breakouts/monitor_latest.json"
WATCHLIST_MAX_AGE_H = 36.0   # warn if the bridge is older than this (missed run?)
RTH_MIN = 390           # 9:30-16:00 ET
MIN_ELAPSED = 2.0       # don't project EOD volume from a near-zero denominator
OR_MIN = 5.0            # opening-range window (grinders sit this out)
RETEST_BAND = 0.002     # a low within 0.2% of the pivot counts as a retest touch

# defaults overridden by CLI in main()
VOL_MULT = 1.5
ADR_SPLIT = 4.5         # ADR% boundary between grinder (<) and mover (>=)
ACCOUNT = 100000.0      # account equity for position sizing
RISK_PCT = 0.75         # base % of equity risked per trade (before theme tilt)
MAX_NOTIONAL_PCT = 25.0 # cap one position's notional at this % of equity

CONFIG = {
    # Group 1 -- coiled at the pivot (20d high)
    "STT":  {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot"},
    "JBHT": {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot; tight 10d"},
    "FITB": {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot"},
    "C":    {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot; p1m strong"},
    "CVS":  {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot; turnaround"},
    "IBKR": {"trigger_lb": 20, "tier": "A", "note": "coiled at pivot"},
    # Group 2 -- Tier A mid-base, alert on the EARLY (5-day) trigger
    "KEYS": {"trigger_lb": 5,  "tier": "A-", "note": "mid-base; early trigger"},
    "CAT":  {"trigger_lb": 5,  "tier": "A-", "note": "mid-base; low ADR"},
    "ADI":  {"trigger_lb": 5,  "tier": "A-", "note": "mid-base; clean semi"},
    "AMD":  {"trigger_lb": 5,  "tier": "A",  "note": "leader, not overextended"},
    "RVMD": {"trigger_lb": 5,  "tier": "A",  "note": "cleanest base; early trigger"},
    # Group 3 -- extended leaders: alert, but stop is wide -- confirm a flag
    "AMKR": {"trigger_lb": 20, "tier": "B", "note": "EXTENDED -- wide stop"},
    "INTC": {"trigger_lb": 20, "tier": "B", "note": "EXTENDED -- wide stop"},
    "ONTO": {"trigger_lb": 20, "tier": "B", "note": "EXTENDED -- wide stop"},
    "AMAT": {"trigger_lb": 20, "tier": "B", "note": "EXTENDED -- most stretched"},
    "UCTT": {"trigger_lb": 20, "tier": "B", "note": "EXTENDED -- most stretched"},
    # Group 4 -- TC2000 tightness-screen adds (2026-06-14)
    "ARMK": {"trigger_lb": 20, "tier": "A", "note": "tightest base; ADR 2.0"},
    "MS":   {"trigger_lb": 20, "tier": "A", "note": "financial leader; RS +26%"},
    "RPRX": {"trigger_lb": 20, "tier": "A", "watch": True,
             "note": "WATCH-ONLY: 3m RS decelerating -- needs strong-vol break"},
    # Group 5 -- new-industry leaders (cyber + airlines, 2026-06-14)
    "FTNT": {"trigger_lb": 20, "tier": "A", "note": "cyber leader; tight base at highs"},
    "DAL":  {"trigger_lb": 20, "tier": "A", "note": "airline leader; cheap-fuel tailwind"},
    "CRWD": {"trigger_lb": 5, "tier": "A-", "watch": True,
             "note": "WATCH-ONLY: cyber, mid-base ~15% to pivot"},
    "PANW": {"trigger_lb": 5, "tier": "A-", "watch": True,
             "note": "WATCH-ONLY: cyber, 6/7 template, mid-base"},
    "UAL":  {"trigger_lb": 5, "tier": "A-", "watch": True,
             "note": "WATCH-ONLY: airline, slightly extended vs 10EMA"},
}

STATE: dict[str, dict] = {}
# theme/narrative tilt, produced by theme_strength.py -> data/theme_scores.json
THEME_SCORES: dict[str, dict] = {}


def _fetch_s3_watchlist(uri: str) -> dict:
    """Pull the CONFIG bridge the EOD Lambda wrote to S3 (s3://bucket/key).

    Warns (but still loads) if the object is older than WATCHLIST_MAX_AGE_H so the
    live alarm never silently runs on a stale scan after a missed/failed run."""
    import boto3  # local import: only needed for the S3 path
    from datetime import timezone

    bucket, _, key = uri[len("s3://"):].partition("/")
    obj = boto3.client("s3").get_object(Bucket=bucket, Key=key)
    age_h = (datetime.now(timezone.utc) - obj["LastModified"]).total_seconds() / 3600.0
    stamp = obj["LastModified"].astimezone().strftime("%Y-%m-%d %H:%M")
    if age_h > WATCHLIST_MAX_AGE_H:
        print(f"  ! WARNING: {uri} is {age_h:.0f}h old (written {stamp}) -- "
              f"the daily scan may not have run. Using it anyway.")
    else:
        print(f"  . bridge written {stamp} ({age_h:.0f}h ago)")
    return json.loads(obj["Body"].read().decode("utf-8"))


def _load_watchlist(path: str) -> dict:
    """Load externally-generated CONFIG entries (from run_preferred_breakouts.py
    or the EOD Lambda's S3 bridge) and merge them into CONFIG. External entries
    override curated ones on key collision so the daily scan stays authoritative
    for the names it surfaces. `path` may be a local file or an s3:// URI.
    Returns the dict of entries merged (empty on missing/invalid source)."""
    try:
        if path.startswith("s3://"):
            entries = _fetch_s3_watchlist(path)
        else:
            with open(path) as fh:
                entries = json.load(fh)
    except Exception as exc:
        print(f"  ! could not load watchlist {path}: {exc}")
        return {}
    merged = {}
    for sym, cfg in entries.items():
        if not isinstance(cfg, dict) or "trigger_lb" not in cfg:
            continue
        cfg.setdefault("tier", "A")
        cfg.setdefault("note", "from daily scan")
        CONFIG[sym.upper()] = cfg
        merged[sym.upper()] = cfg
    return merged


def _load_theme_scores() -> dict:
    """Load the narrative tilt (ticker -> theme/size_mult/priority_mult/catalyst).
    Missing file = neutral (every name treated as 1.0x). Run theme_strength.py to refresh."""
    path = os.path.join(os.path.dirname(HERE), "data", "theme_scores.json")
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return {}


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _mac_alert(title: str, msg: str) -> None:
    safe_msg = msg.replace("\\", "").replace('"', "'")
    safe_title = title.replace("\\", "").replace('"', "'")
    script = (
        'tell application "System Events" to display dialog '
        f'"{safe_msg}" with title "{safe_title}" '
        'buttons {"Dismiss"} default button "Dismiss" with icon caution'
    )
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _buffer(price: float) -> float:
    """A tick-ish buffer above a bar high: 1c floor, ~3bps for pricier names."""
    return max(0.02, round(price * 0.0003, 2))


def _position(entry: float, stop: float, size_mult: float) -> dict:
    """Risk-based share count: base $-risk * theme tilt / stop distance, capped by
    notional. Returns shares, the realized $-risk, notional, and a cap flag."""
    dist = entry - stop
    if dist <= 0:
        return {"shares": 0, "risk": 0.0, "notional": 0.0, "capped": False, "dist": dist}
    base_risk = ACCOUNT * (RISK_PCT / 100.0)
    raw = int((base_risk * size_mult) / dist)
    cap_sh = int(ACCOUNT * (MAX_NOTIONAL_PCT / 100.0) / entry)
    shares = min(raw, cap_sh)
    return {"shares": shares, "risk": shares * dist, "notional": shares * entry,
            "capped": raw > cap_sh, "dist": dist}


def _derive_levels(ib, sym: str, cfg: dict) -> dict | None:
    contract = Stock(sym, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        print(f"  x {sym}: could not qualify -- skipping")
        return None
    daily = daily_bars_completed(ib, contract, "80 D")  # strips today's in-progress bar
    if not daily or len(daily) < 25:
        print(f"  ! {sym}: insufficient daily history -- skipping")
        return None
    closes = pd.Series([b.close for b in daily])
    highs = pd.Series([b.high for b in daily])
    lows = pd.Series([b.low for b in daily])
    vols = pd.Series([b.volume for b in daily])
    lb = cfg["trigger_lb"]
    trigger = float(highs.tail(lb).max())
    stop = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
    hard_stop = float(lows.tail(10).min())
    avg_vol = float(vols.tail(50).mean())
    last = float(closes.iloc[-1])
    adr_pct = float((((highs - lows) / closes).tail(20).mean()) * 100)
    is_mover = adr_pct >= ADR_SPLIT
    ts = THEME_SCORES.get(sym, {})
    risk_pct = (trigger - stop) / trigger * 100 if trigger else 0.0
    return {
        "contract": contract, "trigger": trigger, "stop": stop,
        "hard_stop": hard_stop, "avg_vol": avg_vol, "last_close": last,
        "adr_pct": adr_pct, "is_mover": is_mover, "risk_pct": risk_pct,
        "tier": cfg["tier"], "note": cfg["note"], "trigger_lb": lb,
        "watch": cfg.get("watch", False),
        # narrative tilt (neutral 1.0 if ticker absent from theme_scores.json)
        "theme": ts.get("theme", "-"), "theme_rs": ts.get("theme_rs", 0.0),
        "size_mult": ts.get("size_mult", 1.0),
        "priority_mult": ts.get("priority_mult", 1.0),
        "catalyst": ts.get("catalyst", ""),
        # live state
        "consec_above": 0, "established": False, "or_high": None,
        "ping1_fired": False, "ping2_fired": False, "soft_noted": False,
        "buy_stop": None,
    }


def _session_stats(closed_bars):
    if not closed_bars:
        return 0.0, 0.0, 0.0
    t0, t1 = closed_bars[0].date, closed_bars[-1].date
    elapsed = (t1 - t0).total_seconds() / 60.0 + 1.0
    frac = min(elapsed / RTH_MIN, 1.0)
    cum_vol = float(sum(b.volume for b in closed_bars))
    return cum_vol, elapsed, frac


def _session_vwap(closed_bars):
    num = den = 0.0
    for b in closed_bars:
        wap = b.average if b.average else (b.high + b.low + b.close) / 3
        num += wap * b.volume
        den += b.volume
    return num / den if den else None


def _fmt(d) -> str:
    return d.strftime("%H:%M") if hasattr(d, "strftime") else str(d)


def _fire(sym: str, st: dict, kind: str, price: float, pace: float,
          when: str, headline: str, above_vwap: bool = True) -> None:
    mode = "mover" if st["is_mover"] else "grinder"
    tag = "WATCH " if st.get("watch") else ""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = st["buy_stop"] if (kind == "ARM" and st.get("buy_stop")) else price
    pos = _position(entry, st["stop"], st["size_mult"])
    cap = " [notional-capped]" if pos["capped"] else ""
    size_part = (f"BUY ~{pos['shares']} sh @ {entry:.2f} = ${pos['notional']:,.0f}, "
                 f"risk ${pos['risk']:,.0f} (x{st['size_mult']:.2f} {st['theme']} "
                 f"RS {st['theme_rs']*100:+.0f}%){cap}  |  ")
    msg = (f"{sym} [{st['tier']}/{mode}] {tag}{kind}: {headline}  |  px {price:.2f}, "
           f"{'above' if above_vwap else 'BELOW'} VWAP, pace {pace:.2f}x  |  {size_part}stop {st['stop']:.2f} "
           f"(risk {st['risk_pct']:.1f}%), hard {st['hard_stop']:.2f}  |  "
           f"{st['note']}  (bar {when})")
    bar = "=" * 76
    print(f"\a\n{bar}\n  >> {msg}\n{bar}\n", flush=True)
    _log(f"[{stamp}]  >> {msg}")
    # watch-only names: terminal + log heads-up, but no macOS dialog/sound
    if not st.get("watch"):
        _mac_alert(f"{sym} {kind} ({st['tier']}/{mode})", msg)


def _on_bar_update(bars, has_new_bar: bool) -> None:
    if not has_new_bar or len(bars) < 2:
        return
    sym = bars.contract.symbol
    st = STATE.get(sym)
    if not st or (st["ping1_fired"] and st["ping2_fired"]):
        return
    closed = bars[:-1]                      # drop the still-forming bar
    last = closed[-1]
    price = float(last.close)
    cum_vol, elapsed, frac = _session_stats(closed)
    if elapsed < MIN_ELAPSED or frac <= 0:
        return
    pace = (cum_vol / frac) / st["avg_vol"] if st["avg_vol"] else 0.0
    vwap = _session_vwap(closed)
    above_vwap = (vwap is None) or (price > vwap)
    when = _fmt(last.date)
    grinder = not st["is_mover"]

    # grinders: capture the opening-range high once, then sit out the OR window
    if grinder:
        if st["or_high"] is None and elapsed >= OR_MIN:
            t0 = closed[0].date
            or_bars = [b for b in closed if (b.date - t0).total_seconds() / 60.0 < OR_MIN]
            st["or_high"] = max((float(b.high) for b in or_bars), default=st["trigger"])
        if elapsed < OR_MIN:
            return

    need = 1 if st["is_mover"] else 2
    level = st["trigger"] if st["is_mover"] else max(st["trigger"], st["or_high"] or st["trigger"])
    qualifies = (price >= level) and above_vwap
    st["consec_above"] = st["consec_above"] + 1 if qualifies else 0
    if st["consec_above"] >= need:
        st["established"] = True

    # Ping 1 -- momentum arm (volume-confirmed).
    # Re-validate LIVE conditions (price still >= level AND above VWAP) at fire
    # time -- `established` only latches that the break HAPPENED, so without this
    # the arm could fire on a faded-back bar (below pivot/VWAP) once volume caught up.
    if not st["ping1_fired"] and st["established"] and qualifies and pace >= VOL_MULT:
        bar_high = max(float(b.high) for b in closed[-need:])
        # buy-stop can never sit below the breakout pivot -- a stop under the
        # trigger would fill on weakness, defeating the "must keep going" design.
        st["buy_stop"] = max(bar_high + _buffer(bar_high), st["trigger"])
        st["ping1_fired"] = True
        kept = f"{need} close{'s' if need > 1 else ''} > {level:.2f}"
        _fire(sym, st, "ARM", price, pace, when,
              f"{kept} held -> PLACE BUY-STOP {st['buy_stop']:.2f}", above_vwap)
        return

    # soft heads-up: broke but volume not confirming yet (no dialog, terminal only)
    if not st["ping1_fired"] and st["established"] and not st["soft_noted"]:
        st["soft_noted"] = True
        print(f"  . {sym}: cleared {level:.2f} (px {price:.2f}) but volume light "
              f"-- pace {pace:.2f}x (need {VOL_MULT}x). Watching.", flush=True)

    # Ping 2 -- retest-and-hold (after a break; volume floor relaxed to 1.0x)
    if st["established"] and not st["ping2_fired"]:
        touched = float(last.low) <= st["trigger"] * (1 + RETEST_BAND)
        green_hold = (price >= st["trigger"] and float(last.close) > float(last.open)
                      and above_vwap)
        if touched and green_hold and pace >= 1.0:
            st["ping2_fired"] = True
            _fire(sym, st, "RETEST", price, pace, when,
                  f"pulled back to {st['trigger']:.2f} and held (green bar)", above_vwap)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*", help="subset to watch (default: all configured)")
    ap.add_argument("--vol-mult", type=float, default=1.5,
                    help="projected-volume confirmation multiple for Ping 1 (default 1.5)")
    ap.add_argument("--adr-split", type=float, default=4.5,
                    help="ADR%% boundary: grinder below, mover at/above (default 4.5)")
    ap.add_argument("--account", type=float, default=100000.0,
                    help="account equity for position sizing (default 100000)")
    ap.add_argument("--risk-pct", type=float, default=0.75,
                    help="base %% of equity risked per trade, before theme tilt (default 0.75)")
    ap.add_argument("--max-notional-pct", type=float, default=25.0,
                    help="cap one position's notional at this %% of equity (default 25)")
    ap.add_argument("--watchlist", default=None,
                    help="local path OR s3:// URI of a JSON of CONFIG-shaped entries "
                         "(e.g. data/watchlist/monitor_latest.json from the daily scan); "
                         "merged into CONFIG, and used as the default symbol set")
    ap.add_argument("--s3", action="store_true",
                    help=f"pull the fresh bridge from the EOD Lambda's S3 location "
                         f"({DEFAULT_WATCHLIST_S3}); shorthand for --watchlist <that URI>")
    args = ap.parse_args()

    global VOL_MULT, ADR_SPLIT, ACCOUNT, RISK_PCT, MAX_NOTIONAL_PCT
    VOL_MULT, ADR_SPLIT = args.vol_mult, args.adr_split
    ACCOUNT, RISK_PCT, MAX_NOTIONAL_PCT = args.account, args.risk_pct, args.max_notional_pct

    watch_src = args.watchlist or (DEFAULT_WATCHLIST_S3 if args.s3 else None)
    watch_syms: list[str] = []
    if watch_src:
        merged = _load_watchlist(watch_src)
        watch_syms = list(merged.keys())
        print(f"Loaded watchlist {watch_src}: {len(watch_syms)} names "
              f"({', '.join(watch_syms) or 'none'})")

    # explicit args win; else the watchlist (if given); else the full curated CONFIG
    default_syms = watch_syms if watch_syms else list(CONFIG.keys())
    syms = [s.upper() for s in args.symbols] or default_syms
    syms = [s for s in syms if s in CONFIG]
    if not syms:
        print("No configured symbols matched. Configured:", ", ".join(CONFIG))
        return 1

    global THEME_SCORES
    THEME_SCORES = _load_theme_scores()

    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "14")))
    print(f"OK Connected (paper {ib.managedAccounts()}).")
    print(f"Narrative tilt: {'loaded data/theme_scores.json' if THEME_SCORES else 'NONE (run theme_strength.py) -- neutral 1.0x'}\n")
    _log(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] --- breakout monitor start: {', '.join(syms)} ---")

    for sym in syms:
        st = _derive_levels(ib, sym, CONFIG[sym])
        if st:
            STATE[sym] = st

    # heavy tilt: rank the display by narrative priority (hot themes first)
    ranked = sorted(STATE, key=lambda s: -STATE[s]["priority_mult"])
    base_risk = ACCOUNT * (RISK_PCT / 100.0)
    print(f"Sizing: ${ACCOUNT:,.0f} acct x {RISK_PCT}% = ${base_risk:,.0f} base risk, "
          f"x theme size_mult, notional cap {MAX_NOTIONAL_PCT:.0f}%.")
    print("Derived levels (from IB daily bars -- compare to TC2000); ranked by narrative tilt:")
    print(f"  {'SYM':5} {'tier':4} {'mode':7} {'THEME':15} {'tRS':>5} {'prio':>5} "
          f"{'size':>5} {'ADR%':>5} {'trigger':>9} {'to_go%':>7} {'stop':>9} {'risk%':>6} "
          f"{'sh@trig':>7} {'$risk':>7}")
    for sym in ranked:
        st = STATE[sym]
        to_go = (st["trigger"] / st["last_close"] - 1) * 100
        mode = "MOVER" if st["is_mover"] else "grinder"
        pos = _position(st["trigger"], st["stop"], st["size_mult"])
        capflag = "*" if pos["capped"] else " "
        print(f"  {sym:5} {st['tier']:4} {mode:7} {st['theme'][:15]:15} "
              f"{st['theme_rs']*100:+5.0f} {st['priority_mult']:5.2f} {st['size_mult']:5.2f} "
              f"{st['adr_pct']:5.1f} {st['trigger']:9.2f} {to_go:7.1f} {st['stop']:9.2f} "
              f"{st['risk_pct']:6.1f} {pos['shares']:6d}{capflag} {pos['risk']:7.0f}")

    if not STATE:
        print("\nNo symbols armed. Exiting.")
        ib.disconnect()
        return 1

    grinders = sum(1 for s in STATE.values() if not s["is_mover"])
    movers = len(STATE) - grinders
    print(f"\nArmed {len(STATE)} names ({grinders} grinder / {movers} mover) | "
          f"vol confirm >= {VOL_MULT}x, ADR split {ADR_SPLIT}%. Ctrl-C to stop.")
    print("  grinder = skip 5min OR + 2 closes (or retest); mover = 1 close. "
          "Both: VWAP filter, buy-stop above the bar.\n")
    for sym, st in STATE.items():
        bars = ib.reqHistoricalData(
            st["contract"], endDateTime="", durationStr="1 D",
            barSizeSetting="1 min", whatToShow="TRADES", useRTH=True,
            keepUpToDate=True,
        )
        bars.updateEvent += _on_bar_update

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

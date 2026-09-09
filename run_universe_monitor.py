#!/usr/bin/env python3
"""Universe-wide intraday alert engine (alert-only, desk delivery).

Live:    PYTHONPATH=src .venv/bin/python3 run_universe_monitor.py
         (universe = data/watchlist/universe_latest.txt, rebuilt at start unless --no-rebuild)
Replay:  PYTHONPATH=src .venv/bin/python3 run_universe_monitor.py --replay 2026-09-08 SPCX LITE
         (feeds Tradier 1-min timesales through the same books + detectors)

Detectors: long = UR (undercut & reclaim), ORB9 (opening-range break above the daily 9 EMA);
short = BIR (bounce into a declining MA, first violation of higher lows; short universe only),
FBO (failed breakout of the prior-day high / opening range; every name -- also the exit tell for a long).
Short universe = data/watchlist/universe_short.txt + long-universe names below their 9 and 21 EMA.
Delivery: terminal + data/watchlist/logs/universe_alerts_<date>.log + macOS dialog (--no-dialog),
plus the journal website: data/journal/alerts/<date>.json mirrored to s3://gmerton-trade-journal/alerts/
(read by alerts.html). Live publishes by default (--no-publish to skip); replay publishes only with --publish.
Requires TRADIER_API_KEY.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from lib.alerts.bars import Bar, SymbolBook
from lib.alerts.context import load_context
from lib.alerts.detectors import DETECTORS, INDEX_SYMBOLS, SHORT_KINDS, Alert, IndexState, SymbolState
from lib.alerts.publish import AlertPublisher
from lib.alerts.stream import trades
from lib.alerts.universe import build_universe
from lib.tradier.get_daily_history import get_intraday_bars
from lib.tradier.tradier_client_wrapper import TradierClient

REPO = Path(__file__).resolve().parent
LOGS = REPO / "data" / "watchlist" / "logs"


def _sound() -> None:
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _read_list(p: Path) -> set[str]:
    if not p.exists():
        return set()
    return {l.split("#")[0].strip().upper() for l in p.read_text().splitlines() if l.split("#")[0].strip()}


def _mac_alert(title: str, msg: str) -> None:
    safe_msg = msg.replace("\\", "").replace('"', "'")
    script = ('tell application "System Events" to display dialog '
              f'"{safe_msg}" with title "{title}" buttons {{"Dismiss"}} default button "Dismiss" with icon caution')
    subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def live_session_date() -> date:
    """The session the monitor is (or will be) watching: today in ET, or the next weekday
    when started after the close -- so an evening start never overwrites today's files."""
    now = datetime.now(ZoneInfo("America/New_York"))
    d = now.date()
    if now.time() >= time(16, 5):
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


class Engine:
    def __init__(self, ctx: dict, detectors: list[str], session: date, dialog: bool,
                 publisher: AlertPublisher | None = None, replay: bool = False,
                 sound: bool = False, index_gate: bool = False, short_syms: set[str] | None = None):
        self.ctx = ctx
        self.publisher = publisher
        # BIR runs only on the short universe; FBO runs everywhere (a failed breakout is a fact
        # about the day, and on a long-universe name it doubles as the exit signal); UR/ORB9 only
        # on long-universe names.
        self.short_syms = short_syms or set()
        self.books = {s: SymbolBook(s) for s in ctx}
        for s in INDEX_SYMBOLS:                       # index books: streamed, never detected on
            self.books.setdefault(s, SymbolBook(s))
        self.state = {s: SymbolState() for s in ctx}
        self.detectors = [DETECTORS[d] for d in detectors]
        self.named_detectors = [(d, DETECTORS[d]) for d in detectors]
        self.long_syms: set[str] = set(ctx) - (short_syms or set())
        self.dialog = dialog
        self.sound = sound
        self.index_gate = index_gate
        self.idx = IndexState()
        for s in INDEX_SYMBOLS:
            self.idx.books[s] = self.books[s]
        LOGS.mkdir(parents=True, exist_ok=True)
        self.log = LOGS / f"universe_alerts_{session.isoformat()}{'_replay' if replay else ''}.log"
        self.fired: list[Alert] = []

    def on_closed_bar(self, sym: str, b: Bar) -> None:
        if sym not in self.ctx:                        # SPY/QQQ: state only
            return
        book, ctx, st = self.books[sym], self.ctx[sym], self.state[sym]
        is_short_name = sym in self.short_syms
        for name, det in self.named_detectors:
            if name == "bir" and not is_short_name:
                continue
            if name in ("ur", "orb9") and is_short_name and sym not in self.long_syms:
                continue
            a = det(book, ctx, st, b, self.idx)
            if a is not None:
                self.emit(a)

    def emit(self, a: Alert) -> None:
        a.msg += self.idx.stamp(a.fields, a.t)
        above = a.fields.get("index_above")
        # mirrored gate: longs are gated while SPY is under VWAP, shorts while it is above
        gated = self.index_gate and above is not None and (above is False if a.kind not in SHORT_KINDS else above is True)
        a.fields["gated"] = gated
        self.fired.append(a)
        line = f"[{a.t:%Y-%m-%d %H:%M}] {a.symbol:6s} {a.kind:5s} {'(gated) ' if gated else ''}{a.msg}"
        print(("" if gated else "\a") + line, flush=True)
        with self.log.open("a") as fh:
            fh.write(line + "\n")
        if not gated:
            if self.sound:
                _sound()
            if self.dialog:
                _mac_alert(f"{a.symbol} {a.kind}", a.msg)
        if self.publisher is not None:
            self.publisher.add(a)


async def run_live(args) -> int:
    session = live_session_date()
    if args.symbols:
        universe = [s.upper() for s in args.symbols]
    else:
        universe, parts = build_universe(write=not args.no_rebuild, full=args.full)
        print("universe: " + ", ".join(f"{k}={len(v)}" for k, v in parts.items()) + f" -> {len(universe)} names")
    short_manual = _read_list(REPO / "data" / "watchlist" / "universe_short.txt")
    ctx = await load_context(sorted(set(universe) | short_manual), session)
    short_syms = short_manual | {s for s in universe if s in ctx and ctx[s].bearish}
    if short_syms:
        print(f"short universe ({len(short_syms)}): manual {len(short_manual)} + bearish-stacked from the long list "
              f"{len(short_syms - short_manual)} -> " + " ".join(sorted(short_syms)))
    missing = sorted(set(universe) - set(ctx))
    if missing:
        print(f"  no daily context for {len(missing)}: {' '.join(missing[:20])}{' ...' if len(missing) > 20 else ''}")
    pub = None if args.no_publish else AlertPublisher(session, mode="live", universe_n=len(ctx))
    eng = Engine(ctx, args.detectors.split(","), session, dialog=not args.no_dialog, publisher=pub,
                 sound=args.sound, index_gate=args.index_gate, short_syms=short_syms)
    print(f"[{datetime.now():%H:%M:%S}] streaming {len(ctx)} names + SPY/QQQ | detectors {args.detectors} | log {eng.log}"
          f"{' | publishing to the journal site' if pub else ''}{' | UR index-gated' if args.index_gate else ''}{' | sound on' if args.sound else ''}")
    print("  " + " ".join(sorted(ctx)))
    print("  alerts print here as they fire; a heartbeat line every 5 min shows prints/alerts so far. Ctrl-C to stop.")
    if pub:
        pub.flush()
    counters = {"prints": 0, "last_print": None}

    async def sweeper():
        last_beat = datetime.now()
        while True:
            await asyncio.sleep(5)
            now = datetime.now()
            for sym, book in eng.books.items():
                b = book.flush_if_stale(now)
                if b is not None:
                    eng.on_closed_bar(sym, b)
            if (now - last_beat).total_seconds() >= args.heartbeat * 60:
                last_beat = now
                lp = counters["last_print"].strftime("%H:%M:%S") if counters["last_print"] else "none"
                stale = counters["last_print"] and (now - counters["last_print"]).total_seconds() > 120
                print(f"[{now:%H:%M:%S}] heartbeat: {counters['prints']} prints, last {lp}"
                      f"{'  !! no prints for 2+ min -- stream may be dead' if stale else ''}, "
                      f"{len(eng.fired)} alerts so far", flush=True)

    sweep = asyncio.create_task(sweeper())
    status = asyncio.create_task(pub.status_loop()) if pub else None
    try:
        async for sym, t, px, sz in trades(sorted(set(ctx) | set(INDEX_SYMBOLS))):
            counters["prints"] += 1
            counters["last_print"] = datetime.now()
            if counters["prints"] == 1:
                print(f"[{datetime.now():%H:%M:%S}] first print received ({sym} {px:.2f}) -- stream is live", flush=True)
            if pub:
                pub.note_print(t)
            book = eng.books.get(sym)
            if book is None:
                continue
            closed = book.on_trade(t, px, sz)
            if closed is not None:
                eng.on_closed_bar(sym, closed)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n[{datetime.now():%H:%M:%S}] stopped -- {len(eng.fired)} alerts this session, log {eng.log}")
    finally:
        sweep.cancel()
        if status:
            status.cancel()
        if pub:
            pub.set_state("stopped")
    return 0


async def run_replay(args) -> int:
    session = date.fromisoformat(args.replay)
    syms = [s.upper() for s in args.symbols]
    if not syms:
        print("replay needs symbols"); return 2
    ctx = await load_context(syms, session)
    pub = AlertPublisher(session, mode="replay", universe_n=len(ctx)) if args.publish else None
    # replay: every symbol is eligible for every requested detector (validation mode)
    eng = Engine(ctx, args.detectors.split(","), session, dialog=False, publisher=pub, replay=True,
                 index_gate=args.index_gate, short_syms=set(syms))
    eng.long_syms = set(syms)
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
        for isym in INDEX_SYMBOLS:
            im = await get_intraday_bars(isym, session, interval="1min", client=client)
            if im is not None:
                im = im.copy(); im["vwap"] = (im["close"] * im["volume"]).cumsum() / im["volume"].cumsum()
                eng.idx.series[isym] = im[["close", "vwap"]]
        for sym in syms:
            if sym not in ctx:
                print(f"{sym}: no daily context"); continue
            m = await get_intraday_bars(sym, session, interval="1min", client=client)
            if m is None:
                print(f"{sym}: no intraday bars"); continue
            c = ctx[sym]
            print(f"--- {sym} {session}: prev close {c.prev_close:.2f} PDL {c.prev_low:.2f} 9EMA {c.ema9:.2f} "
                  f"21EMA {c.ema21:.2f} ADR {c.adr_pct:.1f}% avgvol {c.avg_vol20/1e6:.1f}M | {len(m)} bars")
            book = eng.books[sym]
            for t, r in m.iterrows():
                b = Bar(t.to_pydatetime(), float(r.open), float(r.high), float(r.low), float(r.close), float(r.volume), 0.0)
                book.on_bar(b, bar_vwap=float(r.vwap) if "vwap" in r and pd.notna(r.vwap) else None)
                eng.on_closed_bar(sym, b)
            if not [a for a in eng.fired if a.symbol == sym]:
                print(f"    (no alert) session low {book.session_low:.2f}@{book.low_time:%H:%M} "
                      f"open {book.session_open:.2f} high {book.session_high:.2f}")
    if pub:
        pub.set_state("replay complete")
        print(f"published {len(eng.fired)} alerts -> data/journal/alerts/{session}.json + s3")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*", help="explicit symbols (live: overrides the universe)")
    ap.add_argument("--replay", metavar="YYYY-MM-DD", help="replay a past session from Tradier 1-min bars")
    ap.add_argument("--detectors", default="ur,orb9,bir,fbo", help="comma list of ur,orb9 (long) and bir,fbo (short)")
    ap.add_argument("--no-rebuild", action="store_true", help="use universe_latest.txt as-is")
    ap.add_argument("--full", action="store_true", help="preferred-list union instead of universe_focus.txt")
    ap.add_argument("--no-dialog", action="store_true")
    ap.add_argument("--no-publish", action="store_true", help="live: don't write the journal-site JSON / S3")
    ap.add_argument("--heartbeat", type=int, default=5, help="minutes between heartbeat lines (live)")
    ap.add_argument("--sound", action="store_true", help="play the chime on each (ungated) alert, no dialog")
    ap.add_argument("--index-gate", action="store_true", help="mark UR alerts 'gated' while SPY is under its VWAP (no sound/dialog); ORB9 is always index-gated")
    ap.add_argument("--publish", action="store_true", help="replay: also publish the replayed alerts")
    args = ap.parse_args()
    if "TRADIER_API_KEY" not in os.environ:
        print("TRADIER_API_KEY not set"); return 2
    try:
        return asyncio.run(run_replay(args) if args.replay else run_live(args))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

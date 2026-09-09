#!/usr/bin/env python3
"""Universe-wide intraday alert engine (alert-only, desk delivery).

Live:    PYTHONPATH=src .venv/bin/python3 run_universe_monitor.py
         (universe = data/watchlist/universe_latest.txt, rebuilt at start unless --no-rebuild)
Replay:  PYTHONPATH=src .venv/bin/python3 run_universe_monitor.py --replay 2026-09-08 SPCX LITE
         (feeds Tradier 1-min timesales through the same books + detectors)

Detectors: UR (undercut & reclaim), ORB9 (opening-range break above the daily 9 EMA).
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
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from lib.alerts.bars import Bar, SymbolBook
from lib.alerts.context import load_context
from lib.alerts.detectors import DETECTORS, Alert, SymbolState
from lib.alerts.publish import AlertPublisher
from lib.alerts.stream import trades
from lib.alerts.universe import build_universe
from lib.tradier.get_daily_history import get_intraday_bars
from lib.tradier.tradier_client_wrapper import TradierClient

REPO = Path(__file__).resolve().parent
LOGS = REPO / "data" / "watchlist" / "logs"


def _mac_alert(title: str, msg: str) -> None:
    safe_msg = msg.replace("\\", "").replace('"', "'")
    script = ('tell application "System Events" to display dialog '
              f'"{safe_msg}" with title "{title}" buttons {{"Dismiss"}} default button "Dismiss" with icon caution')
    subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Engine:
    def __init__(self, ctx: dict, detectors: list[str], session: date, dialog: bool,
                 publisher: AlertPublisher | None = None):
        self.ctx = ctx
        self.publisher = publisher
        self.books = {s: SymbolBook(s) for s in ctx}
        self.state = {s: SymbolState() for s in ctx}
        self.detectors = [DETECTORS[d] for d in detectors]
        self.dialog = dialog
        LOGS.mkdir(parents=True, exist_ok=True)
        self.log = LOGS / f"universe_alerts_{session.isoformat()}.log"
        self.fired: list[Alert] = []

    def on_closed_bar(self, sym: str, b: Bar) -> None:
        book, ctx, st = self.books[sym], self.ctx[sym], self.state[sym]
        for det in self.detectors:
            a = det(book, ctx, st, b)
            if a is not None:
                self.emit(a)

    def emit(self, a: Alert) -> None:
        self.fired.append(a)
        line = f"[{a.t:%Y-%m-%d %H:%M}] {a.symbol:6s} {a.kind:5s} {a.msg}"
        print(f"\a{line}", flush=True)
        with self.log.open("a") as fh:
            fh.write(line + "\n")
        if self.dialog:
            _mac_alert(f"{a.symbol} {a.kind}", a.msg)
        if self.publisher is not None:
            self.publisher.add(a)


async def run_live(args) -> int:
    session = date.today()
    if args.symbols:
        universe = [s.upper() for s in args.symbols]
    else:
        universe, parts = build_universe(write=not args.no_rebuild, full=args.full)
        print("universe: " + ", ".join(f"{k}={len(v)}" for k, v in parts.items()) + f" -> {len(universe)} names")
    ctx = await load_context(universe, session)
    missing = sorted(set(universe) - set(ctx))
    if missing:
        print(f"  no daily context for {len(missing)}: {' '.join(missing[:20])}{' ...' if len(missing) > 20 else ''}")
    pub = None if args.no_publish else AlertPublisher(session, mode="live", universe_n=len(ctx))
    eng = Engine(ctx, args.detectors.split(","), session, dialog=not args.no_dialog, publisher=pub)
    print(f"[{datetime.now():%H:%M:%S}] streaming {len(ctx)} names | detectors {args.detectors} | log {eng.log}"
          f"{' | publishing to the journal site' if pub else ''}")
    if pub:
        pub.flush()

    async def sweeper():
        while True:
            await asyncio.sleep(5)
            now = datetime.now()
            for sym, book in eng.books.items():
                b = book.flush_if_stale(now)
                if b is not None:
                    eng.on_closed_bar(sym, b)

    sweep = asyncio.create_task(sweeper())
    status = asyncio.create_task(pub.status_loop()) if pub else None
    try:
        async for sym, t, px, sz in trades(list(ctx)):
            if pub:
                pub.note_print(t)
            book = eng.books.get(sym)
            if book is None:
                continue
            closed = book.on_trade(t, px, sz)
            if closed is not None:
                eng.on_closed_bar(sym, closed)
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
    eng = Engine(ctx, args.detectors.split(","), session, dialog=False, publisher=pub)
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
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
    ap.add_argument("--detectors", default="ur,orb9")
    ap.add_argument("--no-rebuild", action="store_true", help="use universe_latest.txt as-is")
    ap.add_argument("--full", action="store_true", help="preferred-list union instead of universe_focus.txt")
    ap.add_argument("--no-dialog", action="store_true")
    ap.add_argument("--no-publish", action="store_true", help="live: don't write the journal-site JSON / S3")
    ap.add_argument("--publish", action="store_true", help="replay: also publish the replayed alerts")
    args = ap.parse_args()
    if "TRADIER_API_KEY" not in os.environ:
        print("TRADIER_API_KEY not set"); return 2
    return asyncio.run(run_replay(args) if args.replay else run_live(args))


if __name__ == "__main__":
    sys.exit(main())

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
Delivery: terminal + data/watchlist/logs/universe_alerts_<date>.log (macOS pop-ups removed 2026-09-10),
plus the journal website: data/journal/alerts/<date>.json mirrored to s3://gmerton-trade-journal/alerts/
(read by alerts.html). Live publishes by default (--no-publish to skip); replay publishes only with --publish.
Requires TRADIER_API_KEY.
"""
from __future__ import annotations

import argparse
import json
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
from lib.alerts.grading import RUBRIC_VERSION, Grade, grade_alert
from lib.alerts.publish import AlertPublisher
from lib.alerts.stream import trades
from lib.alerts.universe import build_universe
from lib.tradier.get_daily_history import get_intraday_bars
from lib.tradier.tradier_client_wrapper import TradierClient

REPO = Path(__file__).resolve().parent
LOGS = REPO / "data" / "watchlist" / "logs"
EXT_UP_SHORT_ADR = 2.0          # a short on a name this far over its 21 EMA needs a red day to count


def _sound() -> None:
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _read_list(p: Path) -> set[str]:
    if not p.exists():
        return set()
    return {l.split("#")[0].strip().upper() for l in p.read_text().splitlines() if l.split("#")[0].strip()}


_TTY = sys.stdout.isatty()


def headline(a: Alert, gated: bool) -> str:
    """Terminal alert line: ticker, LONG/SHORT, entry, stop (risk) first; time, kind and detail after."""
    side = "SHORT" if a.kind in SHORT_KINDS else "LONG"
    risk = abs(a.price - a.stop) / a.price * 100 if a.price else 0.0
    sa = a.fields.get("stop_adr")
    g = a.fields.get("grade")
    head = f"{a.symbol:<6s} {side:<5s} @ {a.price:.2f}  stop {a.stop:.2f} ({risk:.1f}%{f', {sa:.2f} ADR' if sa else ''}){f'  [{g}]' if g else ''}"
    it = a.fields.get("industry_txt")
    tail = f"  | {a.t:%H:%M} {a.kind}{' (gated)' if gated else ''}{f' | {it}' if it else ''} | {a.msg}"
    if _TTY:
        col = "\033[32m" if side == "LONG" else "\033[31m"
        head = ("\033[2m" if gated else "\033[1m") + head.replace(side, col + side + "\033[39m", 1) + "\033[0m"
    return head + tail


def load_group_etfs() -> dict[str, str]:
    """group -> industry ETF (data/watchlist/group_etfs.csv); context on every alert, not graded."""
    p = REPO / "data" / "watchlist" / "group_etfs.csv"
    out: dict[str, str] = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if not line.strip() or line.startswith("#") or line.startswith("group,"):
                continue
            g, e = line.split(",", 1); out[g.strip()] = e.strip().upper()
    return out


def print_industries(eng) -> None:
    """Pre-market line: each industry ETF's daily in-play state (same classifier as the stocks)."""
    rows = []
    for g, etf in sorted(eng.idx.etf_for.items()):
        k = eng.idx.ref_ctx.get(etf) or eng.idx.universe_ctx.get(etf)
        rows.append(f"{g} {etf} ?" if k is None else f"{g} {etf} {getattr(k, 'day_state', '?')} ({getattr(k, 'ext21_close_adr', 0.0):+.1f} ADR vs 21)")
    print("industry ETFs (daily): " + " | ".join(rows))


def print_day_states(ctx: dict) -> None:
    """Pre-market table: which direction each universe name is in play for today (daily chart, prior close)."""
    by: dict[str, list[str]] = {"LONG": [], "SHORT": [], "OUT": []}
    for s, c in sorted(ctx.items()):
        if s in INDEX_SYMBOLS: continue
        by.setdefault(getattr(c, "day_state", "OUT") or "OUT", []).append(s)
    print(f"daily in-play: LONG {len(by['LONG'])} | SHORT {len(by['SHORT'])} | OUT {len(by['OUT'])}")
    for k in ("LONG", "SHORT", "OUT"):
        print(f"  {k:5s} " + " ".join(by.get(k, [])))
    for s, c in sorted(ctx.items()):
        if s not in INDEX_SYMBOLS and getattr(c, "day_state", "") == "SHORT":
            print(f"    {s:6s} {c.day_reason}")


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
    def __init__(self, ctx: dict, detectors: list[str], session: date,
                 publisher: AlertPublisher | None = None, replay: bool = False,
                 sound: bool = False, index_gate: bool = False, short_syms: set[str] | None = None,
                 day_gate: bool = True, tag: str = ""):
        self.ctx = ctx
        self.day_gate = day_gate
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
        self.sound = sound
        self.index_gate = index_gate
        self.idx = IndexState()
        for s in INDEX_SYMBOLS:
            self.idx.books[s] = self.books[s]
        self.idx.universe_books = self.books
        self.idx.universe_ctx = ctx
        gp = REPO / "data" / "watchlist" / "universe_groups.csv"
        if gp.exists():
            for line in gp.read_text().splitlines()[1:]:
                if "," in line:
                    tk, g = line.split(",", 1); self.idx.groups[tk.strip().upper()] = g.strip()
        self.idx.etf_for = load_group_etfs()
        self.ref_etfs = sorted(set(self.idx.etf_for.values()) - set(ctx))   # streamed for context, never detected on
        for s_ in self.ref_etfs:
            self.books.setdefault(s_, SymbolBook(s_)); self.idx.books[s_] = self.books[s_]
        LOGS.mkdir(parents=True, exist_ok=True)
        self.log = LOGS / f"universe_alerts_{session.isoformat()}{'_replay' + (f'_{tag}' if tag else '') if replay else ''}.log"
        # out-of-play alerts (against the daily in-play direction) are never shown or published,
        # only saved here for analysis: a plain log + a JSON-lines file with every field
        self.oop_log = LOGS / f"universe_alerts_{session.isoformat()}{'_replay' + (f'_{tag}' if tag else '') if replay else ''}_oop.log"
        self.oop_jsonl = LOGS / f"alerts_oop_{session.isoformat()}{'_replay' + (f'_{tag}' if tag else '') if replay else ''}.jsonl"
        if replay:
            self.log.write_text("")          # a replay log is one run, not an accumulation
            self.oop_log.write_text(""); self.oop_jsonl.write_text("")
        self.fired: list[Alert] = []
        self.oop: list[Alert] = []

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

    def _save_oop(self, a: Alert) -> None:
        """Out of play: no terminal line, no sound, not published -- saved for analysis only."""
        self.oop.append(a)
        with self.oop_log.open("a") as fh:
            fh.write(f"[{a.t:%Y-%m-%d %H:%M}] {a.symbol:6s} {a.kind:5s} {a.msg}\n")
        rec = {"date": f"{a.t:%Y-%m-%d}", "t": a.t.strftime("%H:%M"), "symbol": a.symbol, "kind": a.kind,
               "price": round(a.price, 2), "stop": round(a.stop, 2), "msg": a.msg, **a.fields}
        with self.oop_jsonl.open("a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")

    def emit(self, a: Alert) -> None:
        a.msg += self.idx.stamp(a.fields, a.t)
        c0 = self.ctx.get(a.symbol)
        if a.fields.get("stop_adr") is None and c0 is not None and c0.adr_pct and a.price:
            a.fields["stop_adr"] = round(abs(a.price - a.stop) / a.price * 100 / c0.adr_pct, 2)   # longs: same risk-in-ADR the shorts carry
        # Display gate = the setup grade (lib/alerts/grading.py) -- the SAME rubric the journal grades entries
        # with: A/B loud, C dimmed, F saved as out of play. The old index-vs-VWAP and group-leader gates are
        # context in the text only: the 20-session study found no stable edge in either (for shorts the index
        # gate pointed the wrong way). --index-gate is kept as a no-op flag.
        gated = False
        # daily in-play gate: an alert only counts in the direction the daily chart allows
        c = self.ctx.get(a.symbol)
        ds = getattr(c, "day_state", "") if c is not None else ""
        a.fields["day_state"], a.fields["day_reason"] = ds, getattr(c, "day_reason", "")
        want = "SHORT" if a.kind in SHORT_KINDS else "LONG"
        if self.day_gate and ds and ds != want:
            gated = True
            a.fields["out_of_play"] = True
        # extended-UP shorts (parabolic / exhaustion) only count once the day is red: short the crack, never the
        # strength. Replay 9/8-9/10 on BNO/USO/BWET/CVI: every short fired inside a green day lost.
        if (self.day_gate and a.kind in SHORT_KINDS and c is not None and getattr(c, "ext21_close_adr", 0.0) >= EXT_UP_SHORT_ADR
                and a.price >= c.prev_close):
            gated = True
            a.fields["out_of_play"] = True
            a.fields["green_day_short"] = True
            a.msg += f" | still GREEN on the day vs prior close {c.prev_close:.2f}: not cracked yet"
        if ds:
            a.msg += f" | day {ds}{' (OUT OF PLAY for this side)' if ds != want else ''}: {a.fields['day_reason']}"
        g = grade_alert(a.kind, a.t.hour * 60 + a.t.minute, ds or None)
        if a.fields.get("green_day_short"):
            g = Grade("F", "extended-up short still green on the day", g.components)
        a.fields.update(grade=g.grade, grade_why=g.why, rubric=RUBRIC_VERSION)
        a.msg += f" | grade {g.grade}: {g.why}"
        if self.day_gate and g.grade == "F":
            a.fields["out_of_play"] = True
        gated = gated or g.grade in ("C", "F")
        a.fields["gated"] = gated
        ind, ind_txt = self.idx.industry(a.symbol, a.t)
        a.fields.update(ind); a.fields["industry_txt"] = ind_txt
        if a.fields.get("out_of_play"):
            self._save_oop(a)
            return
        self.fired.append(a)
        # the log keeps the machine format (the scorers parse it); the terminal leads with what you act on
        line = f"[{a.t:%Y-%m-%d %H:%M}] {a.symbol:6s} {a.kind:5s} {'(gated) ' if gated else ''}{a.msg}{f' | industry: {ind_txt}' if ind_txt else ''}"
        print(("" if gated else "\a") + headline(a, gated), flush=True)
        with self.log.open("a") as fh:
            fh.write(line + "\n")
        if not gated:
            if self.sound:
                _sound()
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
    etfs = set(load_group_etfs().values()); ref_only = etfs - set(universe) - short_manual
    ctx = await load_context(sorted(set(universe) | short_manual | set(INDEX_SYMBOLS) | etfs), session)
    
    short_syms = short_manual | {s for s in universe if s in ctx and (ctx[s].bearish or getattr(ctx[s], "day_state", "") == "SHORT")}
    print_day_states({k: v for k, v in ctx.items() if k not in ref_only})
    if short_syms:
        print(f"short universe ({len(short_syms)}): manual {len(short_manual)} + bearish-stacked from the long list "
              f"{len(short_syms - short_manual)} -> " + " ".join(sorted(short_syms)))
    missing = sorted(set(universe) - set(ctx))
    if missing:
        print(f"  no daily context for {len(missing)}: {' '.join(missing[:20])}{' ...' if len(missing) > 20 else ''}")
    pub = None if args.no_publish else AlertPublisher(session, mode="live", universe_n=len([k for k in ctx if k not in INDEX_SYMBOLS and k not in ref_only]))
    eng = Engine({k: v for k, v in ctx.items() if k not in INDEX_SYMBOLS and k not in ref_only}, args.detectors.split(","), session, publisher=pub,
                 sound=args.sound, index_gate=args.index_gate, short_syms=short_syms, day_gate=not args.no_day_gate)
    eng.idx.prev_close = {s: ctx[s].prev_close for s in INDEX_SYMBOLS if s in ctx}
    eng.idx.ref_ctx = {s: ctx[s] for s in set(INDEX_SYMBOLS) | etfs if s in ctx}
    print_industries(eng)
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
                      f"{len(eng.fired)} alerts so far ({len(eng.oop)} out of play, saved not shown)", flush=True)

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
        print(f"\n[{datetime.now():%H:%M:%S}] stopped -- {len(eng.fired)} alerts this session, log {eng.log}"
              f" | {len(eng.oop)} out-of-play alerts saved to {eng.oop_jsonl.name}")
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
    etfs = set(load_group_etfs().values()); ref_only = etfs - set(syms)
    ctx = await load_context(syms + list(INDEX_SYMBOLS) + sorted(ref_only), session)
    idx_prev = {s: ctx[s].prev_close for s in INDEX_SYMBOLS if s in ctx}
    ref_ctx = {k: v for k, v in ctx.items() if k in INDEX_SYMBOLS or k in etfs}
    ctx = {k: v for k, v in ctx.items() if k not in INDEX_SYMBOLS and k not in ref_only}
    pub = AlertPublisher(session, mode="replay", universe_n=len(ctx)) if args.publish else None
    # replay: every symbol is eligible for every requested detector (validation mode)
    print_day_states(ctx)
    eng = Engine(ctx, args.detectors.split(","), session, publisher=pub, replay=True,
                 index_gate=args.index_gate, short_syms=set(syms), day_gate=not args.no_day_gate, tag=args.tag)
    short_manual = _read_list(REPO / "data" / "watchlist" / "universe_short.txt")
    eng.long_syms = set(syms) - short_manual
    eng.idx.prev_close = idx_prev
    eng.idx.ref_ctx = ref_ctx
    print_industries(eng)
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
        for isym in list(INDEX_SYMBOLS) + sorted(ref_only):
            im = await get_intraday_bars(isym, session, interval="1min", client=client)
            if im is not None:
                im = im.copy(); im["vwap"] = (im["close"] * im["volume"]).cumsum() / im["volume"].cumsum()
                eng.idx.series[isym] = im[["close", "vwap"]]
        frames: dict[str, "pd.DataFrame"] = {}
        for sym in syms:
            if sym not in ctx:
                print(f"{sym}: no daily context"); continue
            m = await get_intraday_bars(sym, session, interval="1min", client=client)
            if m is None:
                print(f"{sym}: no intraday bars"); continue
            c = ctx[sym]
            print(f"--- {sym} {session}: prev close {c.prev_close:.2f} PDL {c.prev_low:.2f} 9EMA {c.ema9:.2f} "
                  f"21EMA {c.ema21:.2f} ADR {c.adr_pct:.1f}% avgvol {c.avg_vol20/1e6:.1f}M | {len(m)} bars")
            frames[sym] = m
        # feed every symbol minute by minute (lockstep) so group / index relative strength sees same-time data
        rows = sorted(((t.to_pydatetime(), sym, r) for sym, m in frames.items() for t, r in m.iterrows()), key=lambda x: (x[0], x[1]))
        for t, sym, r in rows:
            b = Bar(t, float(r.open), float(r.high), float(r.low), float(r.close), float(r.volume), 0.0)
            eng.books[sym].on_bar(b, bar_vwap=float(r.vwap) if "vwap" in r and pd.notna(r.vwap) else None)
            eng.on_closed_bar(sym, b)
        for sym in frames:
            book = eng.books[sym]
            if not [a for a in eng.fired if a.symbol == sym]:
                print(f"    (no alert) {sym} session low {book.session_low:.2f}@{book.low_time:%H:%M} "
                      f"open {book.session_open:.2f} high {book.session_high:.2f}")
    if pub:
        pub.set_state("replay complete")
        print(f"published {len(eng.fired)} alerts -> data/journal/alerts/{session}.json + s3")
    print(f"replay: {len(eng.fired)} alerts shown, {len(eng.oop)} out of play saved to {eng.oop_jsonl}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*", help="explicit symbols (live: overrides the universe)")
    ap.add_argument("--replay", metavar="YYYY-MM-DD", help="replay a past session from Tradier 1-min bars")
    ap.add_argument("--detectors", default="ur,orb9,bir,fbo,para", help="comma list of ur,orb9 (long) and bir,fbo,para (short)")
    ap.add_argument("--tag", default="", help="replay: write logs as universe_alerts_<date>_replay_<tag>*.log (keeps the study's replay logs intact)")
    ap.add_argument("--no-rebuild", action="store_true", help="use universe_latest.txt as-is")
    ap.add_argument("--full", action="store_true", help="preferred-list union instead of universe_focus.txt")
    ap.add_argument("--no-dialog", action="store_true", help=argparse.SUPPRESS)   # deprecated no-op: macOS pop-ups removed 2026-09-10
    ap.add_argument("--no-publish", action="store_true", help="live: don't write the journal-site JSON / S3")
    ap.add_argument("--heartbeat", type=int, default=5, help="minutes between heartbeat lines (live)")
    ap.add_argument("--sound", action="store_true", help="play the chime on each (ungated) alert")
    ap.add_argument("--index-gate", action="store_true", help="no-op since rubric v1 (2026-09-10): the setup grade in lib/alerts/grading.py decides loud / dimmed / out of play")
    ap.add_argument("--publish", action="store_true", help="replay: also publish the replayed alerts")
    ap.add_argument("--no-day-gate", action="store_true", help="don't dim alerts against the daily in-play direction")
    args = ap.parse_args()
    if "TRADIER_API_KEY" not in os.environ:
        print("TRADIER_API_KEY not set"); return 2
    try:
        return asyncio.run(run_replay(args) if args.replay else run_live(args))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

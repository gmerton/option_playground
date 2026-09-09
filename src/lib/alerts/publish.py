"""Publish alerts where the trade-journal website can read them.

Storage = one JSON document per session, written locally to
data/journal/alerts/<date>.json (so deploy_trade_journal.sh keeps it) AND put to
s3://gmerton-trade-journal/alerts/<date>.json with Cache-Control: no-cache, which
the CloudFront distribution (CachingOptimized, min TTL 1s) honours -- the static
alerts.html page polls it without needing an invalidation. alerts/index.json lists
the available dates. A status block (streaming N names, last print time) is
refreshed every STATUS_EVERY seconds so the page can show liveness.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import threading
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LOCAL_DIR = REPO / "data" / "journal" / "alerts"
PAGE_SRC = Path(__file__).with_name("alerts.html")      # versioned here; data/journal is git-ignored
PAGE_DST = REPO / "data" / "journal" / "alerts.html"


def install_page() -> Path:
    """Copy the static alerts page into the site directory (deploy_trade_journal.sh ships it)."""
    PAGE_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PAGE_SRC, PAGE_DST)
    return PAGE_DST
BUCKET = "gmerton-trade-journal"
PREFIX = "alerts/"
STATUS_EVERY = 60


class AlertPublisher:
    def __init__(self, session: date, *, mode: str, universe_n: int, s3: bool = True):
        self.session = session
        self.doc = {"date": session.isoformat(), "mode": mode, "universe_n": universe_n,
                    "generated_at": None, "status": {"state": "starting", "last_print": None, "prints": 0},
                    "alerts": []}
        self._s3 = None
        if s3:
            import boto3  # lazy: replay without --publish never needs it
            self._s3 = boto3.client("s3")
        self._lock = threading.Lock()
        self._dirty = False
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        install_page()
        # never clobber a day that already has alerts (e.g. a restart, or an evening start
        # that used to resolve to today's date): carry the existing alerts forward
        prev = LOCAL_DIR / f"{session.isoformat()}.json"
        if prev.exists():
            try:
                old = json.loads(prev.read_text())
                if old.get("alerts"):
                    self.doc["alerts"] = old["alerts"]
                    self.doc["mode"] = old.get("mode", mode) if mode == "replay" else mode
            except json.JSONDecodeError:
                pass

    # ---- data ------------------------------------------------------------------
    def add(self, a) -> None:
        rec = {"t": a.t.strftime("%H:%M"), "symbol": a.symbol, "kind": a.kind, "price": round(a.price, 2),
               "stop": round(a.stop, 2), "msg": a.msg, **a.fields}
        with self._lock:
            self.doc["alerts"].append(rec)
            self._dirty = True
        self.flush()

    def note_print(self, t: datetime) -> None:
        st = self.doc["status"]
        st["prints"] += 1
        st["last_print"] = t.strftime("%H:%M:%S")
        st["state"] = "streaming"

    def set_state(self, state: str) -> None:
        self.doc["status"]["state"] = state
        self.flush()

    # ---- io ----------------------------------------------------------------------
    def flush(self) -> None:
        self.doc["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = json.dumps(self.doc, indent=1)
        key = f"{self.session.isoformat()}.json"
        (LOCAL_DIR / key).write_text(body)
        dates = sorted({p.stem for p in LOCAL_DIR.glob("*.json") if p.stem[:4].isdigit()}, reverse=True)
        (LOCAL_DIR / "index.json").write_text(json.dumps({"dates": dates}))
        if self._s3 is not None:
            try:
                self._s3.put_object(Bucket=BUCKET, Key=PREFIX + key, Body=body.encode(),
                                    ContentType="application/json", CacheControl="no-cache, max-age=0")
                self._s3.put_object(Bucket=BUCKET, Key=PREFIX + "index.json",
                                    Body=json.dumps({"dates": dates}).encode(),
                                    ContentType="application/json", CacheControl="no-cache, max-age=0")
            except Exception as exc:  # noqa: BLE001 - never let publishing kill the monitor
                print(f"  ! publish: {exc.__class__.__name__}: {exc}", flush=True)

    async def status_loop(self) -> None:
        while True:
            await asyncio.sleep(STATUS_EVERY)
            await asyncio.get_running_loop().run_in_executor(None, self.flush)

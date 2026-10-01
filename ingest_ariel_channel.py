#!/usr/bin/env python3
"""Bulk-ingest Ariel Hernandez's PUBLIC YouTube videos into data/ariel_hernandez/ (transcripts via add_luk_video.py).

  manifest   data/ariel_hernandez/videos/_channel_videos.tsv  (id, tab, title, seconds, availability), refreshed
             from the channel's Videos and Live tabs on every run unless --no-refresh.
  types      Live tab -> premarket ; Videos tab -> recaps ; members-only "Watchlist video" items are SKIPPED (they
             need the Chrome caption interceptor, see the KB README) ; clips under 3 minutes are skipped.
  order      newest first; already-ingested ids (any videos/*/<date>_<id>/) are skipped, so the job is resumable.
  failures   appended to data/ariel_hernandez/videos/_ingest_failures.tsv; 5 failures in a row = back off 5 minutes,
             and stop after 3 such back-offs (YouTube rate limit).

Usage: .venv/bin/python3 ingest_ariel_channel.py [--limit N] [--tab videos|streams] [--no-refresh]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
KB = REPO / "data/ariel_hernandez"
MANIFEST = KB / "videos/_channel_videos.tsv"
FAILS = KB / "videos/_ingest_failures.tsv"
CHANNEL = "https://www.youtube.com/channel/UCn8hF9X6MGDtbTBb6w3JUYA"
YTDLP = Path(sys.executable).parent / "yt-dlp"


def refresh() -> None:
    rows = []
    for tab in ("videos", "streams"):
        out = subprocess.run([str(YTDLP), "--flat-playlist", "--print", "%(id)s\t%(title)s\t%(duration)s\t%(availability)s",
                              f"{CHANNEL}/{tab}"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            p = line.split("\t")
            if len(p) == 4:
                rows.append("\t".join([p[0], tab, p[1].replace("\t", " "), p[2], p[3]]))
    if rows:
        MANIFEST.write_text("id\ttab\ttitle\tseconds\tavailability\n" + "\n".join(rows) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10_000)
    ap.add_argument("--tab", choices=["videos", "streams"])
    ap.add_argument("--no-refresh", action="store_true")
    a = ap.parse_args()
    if not a.no_refresh or not MANIFEST.exists():
        refresh()
    have = {p.name.split("_", 1)[1] for p in (KB / "videos").glob("*/*_*") if p.is_dir()}
    todo = []
    for line in MANIFEST.read_text().splitlines()[1:]:
        vid, tab, title, secs, avail = line.split("\t")
        if vid in have or avail == "subscriber_only" or (a.tab and tab != a.tab):
            continue
        if not secs.replace(".", "").isdigit() or float(secs) < 180:
            continue
        todo.append((vid, "premarket" if tab == "streams" else "recaps", title))
    print(f"{len(have)} ingested, {len(todo)} public videos to do, limit {a.limit}", flush=True)
    done = streak = backoffs = 0
    for vid, typ, title in todo[: a.limit]:
        for lang in ("en-orig", "en"):                       # the "en" track is rate-limited (HTTP 429); en-orig is not
            r = subprocess.run([sys.executable, str(REPO / "add_luk_video.py"), f"https://www.youtube.com/watch?v={vid}",
                                "--kb", "data/ariel_hernandez", "--type", typ, "--lang", lang], capture_output=True, text=True)
            if r.returncode == 0:
                break
        if r.returncode == 0:
            done, streak = done + 1, 0
            print(f"ok   {vid} [{typ}] {title}", flush=True)
        else:
            streak += 1
            msg = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["?"]
            with FAILS.open("a") as f:
                f.write(f"{vid}\t{typ}\t{title}\t{msg[0][:200]}\n")
            print(f"FAIL {vid} [{typ}] {title}: {msg[0][:120]}", flush=True)
            if streak >= 5:
                backoffs += 1
                if backoffs > 3:
                    print("stopping: repeated failures (rate limit?)", flush=True)
                    break
                time.sleep(300)
                streak = 0
        time.sleep(2)
    print(f"done: {done} ingested this run", flush=True)


if __name__ == "__main__":
    main()

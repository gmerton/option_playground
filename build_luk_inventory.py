#!/usr/bin/env python3
"""
Build data/martin_luk/INVENTORY.md — a high-level inventory of every Martin Luk
video in the knowledge base.

Sources:
  - Ingested videos:  data/martin_luk/videos/<type>/<date>_<id>/meta.json  (authoritative)
  - Full channel list: data/martin_luk/videos/livestreams/_channel_streams.tsv (manifest)
  - Video archive:     s3://gmerton-creator-videos/martin_luk/<date>_<id>.mp4 (run_archive_creator_videos.py),
                       listed with AWS_PROFILE=clarinut-gmerton; archived videos missing from the manifest
                       (Videos-tab uploads) get their own rows

Any video on the channel that isn't ingested is flagged. For those, we check whether
captions are even available (a just-ended livestream's auto-captions take time to
generate) so the inventory can say "captions not available" vs. "not ingested".

Run:
    .venv/bin/python3 build_luk_inventory.py
    .venv/bin/python3 build_luk_inventory.py --no-network   # skip caption checks (S3 is still listed)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
KB = REPO / "data" / "martin_luk"
VIDEOS = KB / "videos"
MANIFEST = VIDEOS / "livestreams" / "_channel_streams.tsv"
OUT = KB / "INVENTORY.md"
YTDLP = Path(sys.executable).parent / "yt-dlp"
S3_BUCKET, S3_PREFIX, S3_PROFILE = "gmerton-creator-videos", "martin_luk/", "clarinut-gmerton"

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
_DATE_SUFFIX = re.compile(r"\s*\|\s*(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{4})\s*$")


def parse_title_date(title: str) -> str:
    m = _DATE_SUFFIX.search(title)
    if not m:
        return ""
    d, mon, y = int(m.group(1)), _MONTHS.get(m.group(2)), int(m.group(3))
    return f"{y:04d}-{mon:02d}-{d:02d}" if mon else ""


def clean_title(title: str) -> str:
    return _DATE_SUFFIX.sub("", title).strip()


def has_captions(vid: str) -> bool:
    """True if the video has auto-captions (what our ingest pipeline pulls).

    yt-dlp prints "<id> has no automatic captions" when none exist. Note it does NOT
    reliably print "has no subtitles" — an empty "Available subtitles:" header may
    follow instead — so we key only on the auto-captions message.
    """
    if not YTDLP.exists():
        return False
    # web_embedded avoids the default client's bot-check / 429; require POSITIVE evidence, since a failed
    # call prints neither message and used to be read as "has captions" (2026-10-04).
    out = subprocess.run(
        [str(YTDLP), "--list-subs", "--skip-download", "--ignore-no-formats-error",
         "--extractor-args", "youtube:player_client=web_embedded", vid],
        capture_output=True, text=True,
    ).stdout
    return "Available automatic captions" in out and "has no automatic captions" not in out


def scan_ingested() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for meta_path in VIDEOS.glob("*/*/meta.json"):
        meta = json.loads(meta_path.read_text())
        folder = meta_path.parent
        tpath = folder / "transcript.txt"
        blocks = chars = 0
        if tpath.exists():
            t = tpath.read_text()
            chars = len(t)
            blocks = (t.count("\n\n") + 1) if t.strip() else 0
        out[meta["video_id"]] = {
            "id": meta["video_id"],
            "date": meta.get("stream_date", ""),
            "title": clean_title(meta.get("title", "")),
            "category": folder.parent.name,
            "duration": meta.get("duration", ""),
            "summary": (meta.get("summary", "") or "").strip(),
            "blocks": blocks,
            "chars": chars,
            "folder": str(folder.relative_to(REPO)),
            "status": "ingested",
        }
    return out


def list_s3() -> dict[str, dict]:
    """video_id -> {"uri", "gb", "date"} for every archived mp4; {} (with a warning) if S3 can't be listed."""
    env = {**os.environ, "AWS_PROFILE": os.environ.get("AWS_PROFILE") or S3_PROFILE}
    p = subprocess.run(["aws", "s3api", "list-objects-v2", "--bucket", S3_BUCKET, "--prefix", S3_PREFIX,
                        "--query", "Contents[?ends_with(Key, '.mp4')].[Key,Size]", "--output", "json"],
                       capture_output=True, text=True, env=env)
    if p.returncode != 0:
        print(f"  ! could not list s3://{S3_BUCKET}/{S3_PREFIX}: {p.stderr.strip()[:200]}")
        return {}
    out = {}
    for key, size in json.loads(p.stdout or "null") or []:
        stem = key.rsplit("/", 1)[1][:-4]               # <YYYY-MM-DD>_<id>
        date, vid = stem[:10], stem[11:]
        out[vid] = {"uri": f"s3://{S3_BUCKET}/{key}", "gb": size / 1e9, "date": date}
    return out


def load_manifest() -> list[tuple[str, str]]:
    rows = []
    if MANIFEST.exists():
        for line in MANIFEST.read_text().splitlines():
            if "\t" in line:
                vid, title = line.split("\t", 1)
                rows.append((vid, title))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-network", action="store_true",
                    help="skip yt-dlp caption-availability checks for un-ingested videos")
    args = ap.parse_args()

    ingested = scan_ingested()
    s3 = list_s3()
    manifest = load_manifest()
    manifest_ids = {v for v, _ in manifest}

    rows: list[dict] = []
    for vid, raw_title in manifest:  # manifest is newest-first
        if vid in ingested:
            rows.append(ingested[vid])
            continue
        r = {
            "id": vid, "date": parse_title_date(raw_title), "title": clean_title(raw_title),
            "category": "livestreams", "duration": "", "summary": "",
            "blocks": 0, "chars": 0, "folder": "",
        }
        if args.no_network:
            r["status"] = "not_ingested"
        else:
            print(f"  checking captions for un-ingested {vid} ...")
            r["status"] = "not_ingested" if has_captions(vid) else "no_captions"
        rows.append(r)

    # ingested videos not on the streams manifest (e.g. interviews)
    for vid, r in ingested.items():
        if vid not in manifest_ids:
            rows.append(r)
    # archived videos on neither (Videos-tab uploads)
    seen = {r["id"] for r in rows}
    for vid, o in s3.items():
        if vid not in seen:
            rows.append({"id": vid, "date": o["date"], "title": "", "category": "videos", "duration": "",
                         "summary": "", "blocks": 0, "chars": 0, "folder": "", "status": "not_ingested"})

    n_total = len(rows)
    n_ing = sum(1 for r in rows if r["status"] == "ingested")
    n_nocap = sum(1 for r in rows if r["status"] == "no_captions")
    n_pending = sum(1 for r in rows if r["status"] == "not_ingested")
    n_s3 = sum(1 for r in rows if r["id"] in s3)
    s3_gb = sum(s3[r["id"]]["gb"] for r in rows if r["id"] in s3)

    badge = {
        "ingested": "✅",
        "no_captions": "⚠️ captions not available",
        "not_ingested": "⏳ not ingested",
    }

    lines: list[str] = []
    lines.append("# Martin Luk — Video Inventory\n")
    lines.append("> Generated by `build_luk_inventory.py` — do not edit by hand; rerun to refresh.\n")
    lines.append(
        f"**{n_total}** videos on channel · **{n_ing}** ingested · "
        f"**{n_nocap}** captions unavailable · **{n_pending}** not yet ingested · "
        f"**{n_s3}** archived to `s3://{S3_BUCKET}/{S3_PREFIX}` ({s3_gb:.1f} GB, 720p, Glacier IR)\n"
    )

    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)

    for cat in sorted(by_cat, key=lambda c: (c != "livestreams", c)):
        crows = sorted(by_cat[cat], key=lambda r: r["date"], reverse=True)
        lines.append(f"\n## {cat.capitalize()}  ({len(crows)})\n")
        lines.append("| Date | Title | Status | Duration | Transcript | Folder | S3 video |")
        lines.append("|------|-------|--------|----------|-----------|--------|----------|")
        for r in crows:
            yt = f"https://www.youtube.com/watch?v={r['id']}"
            title = f"[{r['title'] or r['id']}]({yt})"
            status = badge.get(r["status"], r["status"])
            dur = r["duration"] or "—"
            if r["status"] == "ingested" and r["blocks"]:
                tr = f"{r['blocks']} blocks (~{r['chars'] // 1000}k)"
            else:
                tr = "—"
            folder = f"`{r['folder']}`" if r["folder"] else "—"
            vid_s3 = f"`{s3[r['id']]['uri']}`" if r["id"] in s3 else "—"
            lines.append(
                f"| {r['date'] or '—'} | {title} | {status} | {dur} | {tr} | {folder} | {vid_s3} |"
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n✓ wrote {OUT.relative_to(REPO)}")
    print(f"  {n_total} total · {n_ing} ingested · {n_nocap} no-captions · {n_pending} pending · {n_s3} in S3")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Add a Martin Luk YouTube video to the knowledge base.

Given a video URL, this:
  1. Fetches metadata (id, title, upload/stream date, channel, duration) via yt-dlp.
  2. Downloads the English auto-captions (.vtt).
  3. Dedupes the rolling captions and emits a clean [mm:ss]-timestamped transcript.
  4. Scaffolds  data/martin_luk/videos/<stream_date>_<id>/  with:
       transcript.txt   meta.json   notes.md (template)

Usage:
    .venv/bin/python3 add_luk_video.py https://www.youtube.com/watch?v=XXXX
    .venv/bin/python3 add_luk_video.py XXXX               # bare video id works too
    .venv/bin/python3 add_luk_video.py <url> --type interviews
    .venv/bin/python3 add_luk_video.py <url> --lang en --force

Videos are filed under videos/<type>/<stream_date>_<id>/  (default type: livestreams).

Requires yt-dlp (installed in the project .venv). See data/martin_luk/README.md.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
KB = REPO / "data" / "martin_luk"
VIDEOS = KB / "videos"
YTDLP = Path(sys.executable).parent / "yt-dlp"

_TS_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2})\.\d{3} -->")
_TAG_RE = re.compile(r"<[^>]+>")


def _ytdlp(*args: str) -> str:
    if not YTDLP.exists():
        sys.exit(f"yt-dlp not found at {YTDLP}. Install with: {sys.executable} -m pip install yt-dlp")
    out = subprocess.run([str(YTDLP), *args], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"yt-dlp failed:\n{out.stderr.strip()}")
    return out.stdout


def fetch_meta(url: str) -> dict:
    # Use JSON, not a delimiter — titles can contain '|', '\t', etc.
    info = json.loads(_ytdlp("--skip-download", "--dump-single-json", url))
    d = {
        "id": info["id"],
        "title": info.get("title", ""),
        "upload_date": info.get("upload_date", ""),
        "uploader": info.get("uploader", ""),
        "channel_id": info.get("channel_id", ""),
        "duration_string": info.get("duration_string", ""),
    }
    ud = d["upload_date"]  # YYYYMMDD
    d["stream_date"] = f"{ud[0:4]}-{ud[4:6]}-{ud[6:8]}" if len(ud) == 8 else ud
    return d


def fetch_captions(url: str, lang: str, workdir: Path) -> Path:
    _ytdlp(
        "--skip-download", "--write-auto-subs", "--sub-langs", lang,
        "--sub-format", "vtt", "-o", str(workdir / "vid.%(ext)s"), url,
    )
    vtts = list(workdir.glob("*.vtt"))
    if not vtts:
        sys.exit(
            f"No '{lang}' captions found. YouTube auto-captions for a long livestream "
            "can take hours-to-days to generate after it ends — try again later, or "
            "check available languages with:  .venv/bin/yt-dlp --list-subs <URL>"
        )
    return vtts[0]


def clean_vtt(vtt_path: Path) -> str:
    """Dedupe rolling auto-captions -> chunked [mm:ss] transcript text."""
    cues: list[tuple[str, str]] = []
    cur_ts: str | None = None
    for ln in vtt_path.read_text(encoding="utf-8").splitlines():
        m = _TS_RE.match(ln)
        if m:
            h, mn, s = (int(x) for x in m.groups())
            total = h * 3600 + mn * 60 + s
            cur_ts = f"{total // 60:02d}:{total % 60:02d}"
            continue
        if cur_ts is None:
            continue
        txt = _TAG_RE.sub("", ln).strip()
        if txt:
            cues.append((cur_ts, txt))

    # drop lines we've recently emitted (rolling-caption duplicates)
    recent: list[str] = []
    clean: list[tuple[str, str]] = []
    for ts, txt in cues:
        if txt in recent:
            continue
        recent.append(txt)
        if len(recent) > 6:
            recent.pop(0)
        clean.append((ts, txt))

    # group ~5 lines per chunk, label with the chunk's first timestamp
    out: list[str] = []
    chunk: list[str] = []
    chunk_ts: str | None = None
    for ts, txt in clean:
        if chunk_ts is None:
            chunk_ts = ts
        chunk.append(txt)
        if len(chunk) >= 5:
            out.append(f"[{chunk_ts}] " + " ".join(chunk))
            chunk, chunk_ts = [], None
    if chunk:
        out.append(f"[{chunk_ts}] " + " ".join(chunk))

    text = "\n\n".join(out)
    text = html.unescape(text)                 # &gt;&gt; -> >>
    text = text.replace(">> ", " ").replace(">>", "")  # drop speaker carets
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


NOTES_TEMPLATE = """# Supplemental Notes — {date} "{title}" ({vid})

Human-added context not in the audio: on-screen actions, chart annotations, ticker fixes.

## Ticker decoding table (auto-caption fixes)

Auto-captions garble tickers. Conf: ✅ confirmed · \U0001f7e1 likely · ❓ unsure.

| Transcript said | Likely ticker | Conf | Notes |
|-----------------|---------------|------|-------|
|  |  |  |  |

## On-screen actions (inaudible)

- [mm:ss] —

## Other context

-
"""

NOTES_TEMPLATE_GENERIC = """# Supplemental Notes — {date} "{title}" ({vid})

Human-added context not in the audio: on-screen actions, slides, corrections, the
interviewed trader's name/handle, and anything to verify.

## Interviewee

- Name / handle:
- Strategy in one line:

## Corrections & context

- [mm:ss] —
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Add a YouTube video transcript to a knowledge base.")
    ap.add_argument("url", help="YouTube URL or bare video id")
    ap.add_argument("--kb", default="data/martin_luk",
                    help="knowledge-base root, e.g. data/martin_luk or data/theta_profits")
    ap.add_argument("--type", default="livestreams",
                    help="video category subfolder, e.g. livestreams, interviews (default: livestreams)")
    ap.add_argument("--lang", default="en", help="caption language (default: en)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing video folder")
    args = ap.parse_args()
    videos_root = REPO / args.kb / "videos"
    martin_luk = args.kb.rstrip("/").endswith("martin_luk")

    url = args.url
    # Bare 11-char video id -> full URL. (Leading-dash ids like "-5l8H8TBF5s" are
    # normalized in __main__ before argparse, which would otherwise read them as flags.)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        url = f"https://www.youtube.com/watch?v={url}"

    print(f"Fetching metadata for {url} ...")
    meta = fetch_meta(url)
    vid, title, date = meta["id"], meta["title"], meta["stream_date"]
    dest = videos_root / args.type / f"{date}_{vid}"
    if dest.exists() and not args.force:
        sys.exit(f"{dest} already exists. Use --force to overwrite.")

    # Fetch + clean captions BEFORE creating the folder, so a caption failure
    # (e.g. a just-ended livestream whose auto-captions aren't generated yet)
    # leaves nothing behind.
    with tempfile.TemporaryDirectory() as tmp:
        print(f"Downloading {args.lang} auto-captions ...")
        vtt = fetch_captions(url, args.lang, Path(tmp))
        print("Cleaning transcript ...")
        transcript = clean_vtt(vtt)

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "transcript.txt").write_text(transcript, encoding="utf-8")

    meta_json = {
        "video_id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": title,
        "channel": meta["uploader"],
        "channel_id": meta["channel_id"],
        "stream_date": date,
        "duration": meta["duration_string"],
        "summary": "",
        "transcript": {
            "file": "transcript.txt",
            "source": "youtube_auto_captions",
            "lang": args.lang,
            "format": "timestamped_text_mm_ss",
            "tool": "yt-dlp",
            "quality_note": "Auto-generated captions; tickers often mis-transcribed. See notes.md.",
        },
        "supplemental_notes_file": "notes.md",
    }
    (dest / "meta.json").write_text(json.dumps(meta_json, indent=2) + "\n", encoding="utf-8")

    notes = dest / "notes.md"
    if not notes.exists() or args.force:
        tmpl = NOTES_TEMPLATE if martin_luk else NOTES_TEMPLATE_GENERIC
        notes.write_text(tmpl.format(date=date, title=title, vid=vid), encoding="utf-8")

    n_chunks = transcript.count("\n\n") + 1
    print(f"\n✓ {title}  ({date})")
    print(f"  {dest.relative_to(REPO)}/")
    print(f"  transcript.txt  ({n_chunks} blocks, {len(transcript):,} chars)")
    print(f"  meta.json, notes.md")
    nxt = ("fill notes.md ticker table, then distill into philosophy/principles.md"
           if martin_luk else "summarize the strategy into strategies/ (see the KB README)")
    print(f"\nNext: {nxt}")


if __name__ == "__main__":
    # A YouTube id may start with '-' (e.g. "-5l8H8TBF5s"); argparse would treat it as
    # an unknown flag. Normalize a leading-dash bare id to a full URL before parsing.
    sys.argv[1:] = [
        f"https://www.youtube.com/watch?v={a}"
        if re.fullmatch(r"-[A-Za-z0-9_-]{10}", a) else a
        for a in sys.argv[1:]
    ]
    main()

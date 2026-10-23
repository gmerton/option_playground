#!/usr/bin/env python3
"""Archive a creator's YouTube videos (720p mp4 + info.json) to S3, one at a time.

Bucket: s3://gmerton-creator-videos (account clarinut-gmerton, us-west-2, private, SSE-S3), storage class
GLACIER_IR. Key: <creator>/<YYYY-MM-DD>_<video_id>.mp4 (+ .info.json), the same <date>_<id> as the KB folders.

Disk is tight, so each video is downloaded to a temp dir, uploaded, and deleted before the next. Resumable:
a video whose mp4 is already in S3 is skipped. Runs locally on purpose: YouTube blocks most cloud IPs.

Usage: AWS_PROFILE=clarinut-gmerton .venv/bin/python3 run_archive_creator_videos.py \
           --creator martin_luk --channel https://www.youtube.com/@martinlukkt [--tabs streams videos] [--limit N]
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path

BUCKET = "gmerton-creator-videos"
YTDLP = [sys.executable, "-m", "yt_dlp"]
FORMAT = "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/bv*[height<=720]+ba"


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def list_ids(channel, tabs):
    ids = []
    for tab in tabs:
        out = sh(YTDLP + ["--flat-playlist", "--skip-download", "--print", "%(id)s", f"{channel}/{tab}"])
        ids += [l.strip() for l in out.stdout.splitlines() if l.strip()]
    return list(dict.fromkeys(ids))


def in_s3(prefix, vid):
    out = sh(["aws", "s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", f"{prefix}/",
              "--query", f"Contents[?ends_with(Key, '_{vid}.mp4')].Key", "--output", "text"])
    return out.returncode == 0 and out.stdout.strip() not in ("", "None")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creator", required=True)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--tabs", nargs="+", default=["streams", "videos"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sleep", type=float, default=20, help="pause between videos (YouTube 429s)")
    a = ap.parse_args()
    ids = list_ids(a.channel, a.tabs)
    print(f"{len(ids)} videos on {a.channel} ({' '.join(a.tabs)})", flush=True)
    done = failed = skipped = 0
    for n, vid in enumerate(ids[: a.limit] if a.limit else ids, 1):
        if in_s3(a.creator, vid):
            skipped += 1
            continue
        tmp = Path(tempfile.mkdtemp(prefix="vid_"))
        try:
            t0 = time.time()
            r = sh(YTDLP + ["-f", FORMAT, "--merge-output-format", "mp4", "--write-info-json", "--no-progress",
                            "--retries", "10", "-o", str(tmp / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
                            f"https://www.youtube.com/watch?v={vid}"])
            mp4 = next(tmp.glob("*.mp4"), None)
            if r.returncode != 0 or mp4 is None:
                failed += 1
                print(f"[{n}/{len(ids)}] {vid} DOWNLOAD FAILED: {(r.stderr or '').strip().splitlines()[-1:]}", flush=True)
                continue
            info = next(tmp.glob("*.info.json"), None)
            if info:  # keep the useful metadata, drop the huge format/thumbnail lists
                j = json.loads(info.read_text())
                keep = {k: j.get(k) for k in ("id", "title", "upload_date", "duration", "channel", "webpage_url",
                                              "description", "chapters", "live_status", "width", "height")}
                info.write_text(json.dumps(keep, indent=1))
            for f in [mp4] + ([info] if info else []):
                up = sh(["aws", "s3", "cp", str(f), f"s3://{BUCKET}/{a.creator}/{f.name}",
                         "--storage-class", "GLACIER_IR", "--only-show-errors"])
                if up.returncode != 0:
                    raise RuntimeError(up.stderr.strip())
            done += 1
            print(f"[{n}/{len(ids)}] {mp4.name} {mp4.stat().st_size / 1e9:.2f} GB in {time.time() - t0:.0f}s", flush=True)
        except Exception as e:
            failed += 1
            print(f"[{n}/{len(ids)}] {vid} FAILED: {e}", flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        time.sleep(a.sleep)
    print(f"done {done}, already in S3 {skipped}, failed {failed}", flush=True)


if __name__ == "__main__":
    main()

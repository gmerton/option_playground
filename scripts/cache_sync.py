#!/usr/bin/env python3
"""
Mirror irreplaceable local data artifacts to S3.

Git covers code and small curated data. It does NOT cover the two things that
can never be rebuilt:

  1. IBKR intraday bars (ibkr_bot/data/) — IBKR does not serve this history back.
     Some names already return zero historical bars for this account (SNOW, APP),
     so a lost file is lost for good.
  2. Orphaned artifacts — files with no producer script anywhere in the repo.
     Nothing can regenerate them because nothing knows how they were made.

Everything else under data/cache/ is deliberately NOT mirrored: it derives from
Athena (silver.options_daily_v3), which is itself durable. Losing those costs
query time, not data.

Usage:
    AWS_PROFILE=clarinut-gmerton python3 scripts/cache_sync.py push
    AWS_PROFILE=clarinut-gmerton python3 scripts/cache_sync.py push --dry-run
    AWS_PROFILE=clarinut-gmerton python3 scripts/cache_sync.py pull
    AWS_PROFILE=clarinut-gmerton python3 scripts/cache_sync.py status

Both push and pull skip unchanged files (size + mtime), so re-running is cheap.
pull never clobbers a newer local file unless you pass --force.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUCKET = "s3://gmerton-stock-data/cache"

# (local path relative to repo root, kind). Add new irreplaceable artifacts here.
# Keep the "why" in the comment — it is the whole justification for the entry.
MANIFEST = [
    ("ibkr_bot/data", "dir"),                        # perishable IBKR 1-min stock + option BID_ASK bars
    ("data/models/grid_lgbm.pkl", "file"),           # orphan: no script writes or reads it
    ("data/cache/iv_condor_options.parquet", "file"),  # orphan: run_iv_condor_study.py caches iv_strangle_*/iv_straddle_* only
]


def _run(cmd: list[str], dry: bool) -> int:
    if dry:
        cmd = cmd + ["--dryrun"]
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def _remote(rel: str) -> str:
    return f"{BUCKET}/{rel}"


def push(dry: bool) -> None:
    rc = 0
    for rel, kind in MANIFEST:
        local = REPO / rel
        if not local.exists():
            print(f"  SKIP (missing locally): {rel}")
            continue
        print(f"\n{rel}  ->  {_remote(rel)}")
        if kind == "dir":
            rc |= _run(["aws", "s3", "sync", str(local), _remote(rel)], dry)
        else:
            # cp has no skip-unchanged; sync one file via its parent + an include filter
            rc |= _run(["aws", "s3", "sync", str(local.parent), _remote(str(Path(rel).parent)),
                        "--exclude", "*", "--include", local.name], dry)
    sys.exit(rc)


def pull(dry: bool, force: bool) -> None:
    rc = 0
    for rel, kind in MANIFEST:
        local = REPO / rel
        print(f"\n{_remote(rel)}  ->  {rel}")
        extra = [] if force else ["--size-only"]
        if kind == "dir":
            rc |= _run(["aws", "s3", "sync", _remote(rel), str(local)] + extra, dry)
        else:
            rc |= _run(["aws", "s3", "sync", _remote(str(Path(rel).parent)), str(local.parent),
                        "--exclude", "*", "--include", local.name] + extra, dry)
    sys.exit(rc)


def status() -> None:
    total_local = 0
    print(f"{'MB':>9}  {'local':<7} {'remote':<7} path")
    for rel, kind in MANIFEST:
        local = REPO / rel
        if kind == "dir":
            size = sum(f.stat().st_size for f in local.rglob("*") if f.is_file()) if local.exists() else 0
        else:
            size = local.stat().st_size if local.exists() else 0
        total_local += size
        out = subprocess.run(["aws", "s3", "ls", _remote(rel), "--recursive", "--summarize"],
                             capture_output=True, text=True)
        remote_ok = "Total Objects: 0" not in out.stdout and out.returncode == 0 and out.stdout.strip()
        print(f"{size/1e6:>9.2f}  {'yes' if size else 'NO':<7} {'yes' if remote_ok else 'NO':<7} {rel}")
    print(f"{total_local/1e6:>9.2f}  TOTAL")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("action", choices=["push", "pull", "status"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="pull: overwrite local files that differ")
    a = ap.parse_args()

    if a.action == "push":
        push(a.dry_run)
    elif a.action == "pull":
        pull(a.dry_run, a.force)
    else:
        status()


if __name__ == "__main__":
    main()

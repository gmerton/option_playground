#!/usr/bin/env python3
"""
Audit TEST_INDEX against the study documents on disk. Run it after any study lands.

WHY. TEST_INDEX is the file CLAUDE.md tells every session to check before proposing a study, so a result
that never reaches it is invisible — the work gets redone, or worse, a stale queue row gets believed.
Three separate instances turned up on 2026-09-23 alone:
  * The Davis XSP condor was reviewed AND backtested (12 configurations, claim refuted) and had no row.
  * §286 carried an `n = 17` belonging to a different study, and asked for a window inside the fitting
    sample — a queued "test" that was not a test.
  * The alert-suite study written that same afternoon shipped without a row, found by this audit.

CHECKS
  1. ORPHANS   — a study doc with no reference anywhere in TEST_INDEX.
  2. BROKEN    — a TEST_INDEX link pointing at a file that does not exist.
  2b. OVERSIZE — a TRACKED file above MAX_MB. Per-trade dumps rebuild from their committed script, so
     they do not belong in git: ~148MB was staged this way on 2026-08-08 and a 59MB CSV again on
     2026-09-23, the second swept in by `git add -A data/studies`. GitHub warns at 50MB and the repo
     history is already ~950MB.
  3. Playbooks and `*_analysis_summary` are reported separately: §8 covers them generically and they
     carry their own status banners, so they are not expected to have individual rows.
  4. A doc whose head carries a STATUS BANNER (SUPERSEDED / RETIRED / WITHDRAWN / INVALIDATED) is
     reported as CLOSED, not orphaned. That banner is this repo's terminal state for a result that has
     been re-run or killed — the convention the ticker playbooks already use — and it is a deliberate
     act, unlike simply never being indexed.

Exit code 1 if any genuine orphan or broken link is found, so it can gate a commit if ever wanted.

Usage: PYTHONPATH=src .venv/bin/python3 run_index_audit.py
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

S = pathlib.Path(__file__).resolve().parent / "data" / "studies"
IDX = S / "TEST_INDEX.md"
GENERIC = ("playbook", "analysis_summary")          # covered by §8, banner-managed
MAX_MB = 20.0                                       # tracked-file size ceiling
# Reference/process docs that are deliberately NOT test rows; they are linked from CLAUDE.md / HANDOFF.md.
EXEMPT = {"TEST_INDEX.md", "stop_definitions.md", "daily_routine.md",
          "capital_allocation_framework.md", "pattern_ledger.md"}
CLOSED_MARKERS = ("SUPERSEDED", "RETIRED", "WITHDRAWN", "INVALIDATED", "ERRATUM")
SESSION_REVIEW = "review_"          # dated session reviews are notes, not tests


def main() -> int:
    idx = IDX.read_text()
    linked = set(re.findall(r"\]\(([^)]+)\)", idx))
    names = {pathlib.PurePath(l).name for l in linked}

    docs = [p for p in sorted(S.glob("*.md")) if p.name not in EXEMPT]
    unindexed = [p for p in docs if p.name not in names and p.name not in idx]
    generic = [p for p in unindexed if any(g in p.name for g in GENERIC)]
    rest = [p for p in unindexed if p not in generic]
    closed = [p for p in rest
              if any(m in "\n".join(p.read_text().splitlines()[:8]) for m in CLOSED_MARKERS)]
    reviews = [p for p in rest if p not in closed and p.name.startswith(SESSION_REVIEW)]
    orphans = [p for p in rest if p not in closed and p not in reviews]

    broken = []
    for l in sorted(linked):
        if l.startswith(("http", "#", "mailto")):
            continue
        if not (S / l).resolve().exists():
            broken.append(l)

    print(f"TEST_INDEX audit — {len(docs):,} study docs, {len(linked):,} links")
    print(f"  {len(generic)} playbooks/analyses (generic §8 coverage, not expected to have rows)")
    print(f"  {len(closed)} closed by status banner (superseded/retired) — a deliberate terminal state")
    print(f"  {len(reviews)} dated session reviews (notes, not tests)")

    print(f"\nORPHANS — study doc with no TEST_INDEX reference: {len(orphans)}")
    for p in sorted(orphans, key=lambda x: x.stat().st_mtime, reverse=True):
        head = next((l for l in p.read_text().splitlines() if l.startswith("#")), "")
        print(f"  {dt.date.fromtimestamp(p.stat().st_mtime)}  {p.name:<46s} {head[:70]}")

    print(f"\nBROKEN LINKS — row points at a missing file: {len(broken)}")
    for b in broken:
        print(f"  {b}")

    import subprocess
    big = []
    try:
        files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True,
                               cwd=S.parent.parent, check=True).stdout.split("\0")
        for rel in filter(None, files):
            fp = S.parent.parent / rel
            if fp.is_file() and fp.stat().st_size > MAX_MB * 1e6:
                big.append((fp.stat().st_size / 1e6, rel))
    except Exception as e:  # noqa: BLE001 -- not a git checkout, or git missing; skip the check
        print(f"\n(size check skipped: {type(e).__name__})")
    print(f"\nOVERSIZE — tracked files over {MAX_MB:.0f}MB: {len(big)}")
    for mb, rel in sorted(big, reverse=True):
        print(f"  {mb:7.1f} MB  {rel}")

    bad = len(orphans) + len(broken) + len(big)
    print(f"\n{'✓ clean' if not bad else f'⛔ {bad} issue(s)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verify that every trade in a KB's per-video auto_extract.json carries a quote that is verbatim in that video's
transcript, and that its source timestamp exists. Reports; changes nothing.

  .venv/bin/python3 check_extract_quotes.py --kb data/ariel_hernandez
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

norm = lambda s: re.sub(r"[^a-z0-9%.$ ]", "", re.sub(r"\s+", " ", re.sub(r"\[\d+:\d\d\]", " ", s.lower()))).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", required=True)
    a = ap.parse_args()
    nv = nt = bad = nosrc = 0
    for p in sorted(Path(a.kb).glob("videos/*/*/auto_extract.json")):
        d = json.loads(p.read_text())
        t = norm((p.parent / "transcript.txt").read_text())
        nv += 1
        for tr in d.get("observed_trades", []):
            nt += 1
            q = tr.get("quote") or ""
            if len(q.split()) < 5 or norm(q) not in t:
                bad += 1
                print(f"  quote not verbatim: {p.parent.name} {tr.get('ticker')} {tr.get('action')}: {q[:90]!r}")
            if not re.search(r"@\d+:\d\d$", str(tr.get("source", ""))) or not str(tr.get("source", "")).startswith(p.parent.name):
                nosrc += 1
                print(f"  bad source: {p.parent.name} {tr.get('ticker')}: {tr.get('source')!r}")
    print(f"{nv} videos, {nt} trade rows, {bad} quotes not verbatim, {nosrc} bad sources")


if __name__ == "__main__":
    main()

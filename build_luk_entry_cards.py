#!/usr/bin/env python3
"""Merge and VERIFY Martin Luk's entry cards: what he said about stop, size and trigger on each disclosed entry.

Cards are coded from the stream transcripts only (blind to prices and outcomes) for the entries that are clean on the
clarification worklist. Each coded field must carry a verbatim transcript quote; this script checks every quote against
the transcript and blanks nothing itself -- it reports, and marks each card `quotes_verified`.

  .venv/bin/python3 build_luk_entry_cards.py <dir with out_*.json and batch_*.json>
Writes data/martin_luk/trades/entry_cards.jsonl and prints a verification summary.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

OUT = Path("data/martin_luk/trades/entry_cards.jsonl")
norm = lambda s: re.sub(r"[^a-z0-9%.$ ]", "", re.sub(r"\s+", " ", re.sub(r"\[\d+:\d\d\]", " ", s.lower()))).strip()


def main(src: str) -> None:
    # pair cards with entries BY POSITION within each batch: a multi-ticker fix (e.g. the 3-name crypto basket) shares one key
    pairs, problems = [], []
    for f in sorted(glob.glob(f"{src}/batch_*.json")):
        ms = json.load(open(f))
        o = Path(f.replace("batch_", "out_"))
        if not o.exists():
            problems.append(f"no output for {Path(f).name}")
            continue
        cs = json.load(open(o))
        if len(cs) != len(ms) or any(c["key"] != m["key"] for c, m in zip(cs, ms)):
            problems.append(f"{o.name}: {len(cs)} cards for {len(ms)} entries, or keys out of order")
        pairs += [(m, c) for m, c in zip(ms, cs) if c["key"] == m["key"]]
    tcache: dict[str, str] = {}
    nq = bad = 0
    rows = []
    for m, c in pairs:
        t = tcache.setdefault(m["transcript_path"], norm(open(m["transcript_path"]).read()))
        fails = []
        for q in c.get("quotes") or []:
            nq += 1
            if len(q["text"].split()) < 4 or norm(q["text"]) not in t:
                bad += 1
                fails.append(q["text"][:80])
        supported = {q.get("supports") for q in c.get("quotes") or []}
        rows.append({**{k: m[k] for k in ("ticker", "direction", "action", "stream_date", "source")}, **c,
                     "quotes_verified": not fails, "quote_failures": fails, "fields_with_quotes": sorted(x for x in supported if x)})
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"cards {len(rows)} | quotes {nq}, not found verbatim {bad}; cards with any failed quote {sum(not r['quotes_verified'] for r in rows)}")
    for x in problems:
        print("  PROBLEM:", x)


if __name__ == "__main__":
    main(sys.argv[1])

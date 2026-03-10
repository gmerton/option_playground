#!/usr/bin/env python3
"""
Analyze Martin Luk's livestream stock picks to reverse-engineer his methods.

Usage:
    # Analyze all unanalyzed notes
    PYTHONPATH=src python run_luk_analyzer.py

    # Synthesize common patterns across all analyzed notes into screener rules
    PYTHONPATH=src python run_luk_analyzer.py --synthesize

    # Re-analyze all notes (ignores the analyzed flag)
    PYTHONPATH=src python run_luk_analyzer.py --all
"""

import argparse
import json
from pathlib import Path

NOTES_FILE = Path("data/luk_notes.jsonl")
PATTERNS_FILE = Path("data/studies/luk_patterns.md")


def load_notes() -> list[dict]:
    if not NOTES_FILE.exists():
        return []
    notes = []
    with NOTES_FILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                notes.append(json.loads(line))
    return notes


def save_notes(notes: list[dict]):
    with NOTES_FILE.open("w") as f:
        for note in notes:
            f.write(json.dumps(note) + "\n")


def _append_to_patterns(entry: dict, analyses: dict):
    PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    direction = entry.get("direction", "long").upper()
    with PATTERNS_FILE.open("a") as f:
        f.write(f"\n---\n\n")
        f.write(f"## {entry['date']} — {direction} — {', '.join(entry['tickers'])}\n\n")
        f.write(f"**Luk's comment:** \"{entry['comment']}\"\n\n")
        for ticker, analysis in analyses.items():
            f.write(f"### {ticker}\n\n{analysis}\n\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze Martin Luk's livestream picks")
    parser.add_argument(
        "--synthesize", action="store_true",
        help="Synthesize screener rules from all analyzed notes",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Re-analyze all notes, not just unanalyzed ones",
    )
    args = parser.parse_args()

    from lib.trade_reviewer.luk_analyzer import analyze_ticker, synthesize_patterns

    notes = load_notes()
    if not notes:
        print("No notes found. Add some with:")
        print("  python add_luk_note.py \"BE, PL\" \"setting up nicely for a long\"")
        return

    # ── Synthesis mode ────────────────────────────────────────────────────────
    if args.synthesize:
        analyzed = [n for n in notes if n.get("analyzed")]
        if not analyzed:
            print("No analyzed notes yet. Run without --synthesize first.")
            return

        total_tickers = sum(len(n.get("analyses", {})) for n in analyzed)
        print(f"\nSynthesizing patterns from {len(analyzed)} notes ({total_tickers} tickers)...")

        result = synthesize_patterns(analyzed)

        print("\n" + "=" * 60)
        print(result)
        print("=" * 60)

        PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PATTERNS_FILE.open("a") as f:
            f.write(f"\n---\n\n## PATTERN SYNTHESIS\n\n{result}\n\n")

        print(f"\nSaved to {PATTERNS_FILE}")
        return

    # ── Analysis mode ─────────────────────────────────────────────────────────
    to_analyze = notes if args.all else [n for n in notes if not n.get("analyzed")]

    if not to_analyze:
        print("All notes already analyzed.")
        print("  --synthesize  to distill screener rules")
        print("  --all         to re-analyze everything")
        return

    for i, note in enumerate(to_analyze):
        print(f"\n[{i+1}/{len(to_analyze)}] {note['date']} — {', '.join(note['tickers'])}")
        print(f"  \"{note['comment']}\"")

        direction = note.get("direction", "long")
        analyses = {}
        for ticker in note["tickers"]:
            print(f"\n  Analyzing {ticker} ({direction.upper()})...")
            analysis = analyze_ticker(ticker, note["date"], note["comment"], direction=direction)
            analyses[ticker] = analysis
            print(f"\n  {'─'*50}")
            print(f"  {ticker}:")
            for line in analysis.splitlines():
                print(f"    {line}")

        note["analyzed"] = True
        note["analyses"] = analyses
        _append_to_patterns(note, analyses)

    save_notes(notes)
    print(f"\nDone. Patterns saved to {PATTERNS_FILE}")
    print("Run with --synthesize to distill common screening rules.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate the "actionable analysis" + short indexable "actionable verdict" label for trade
reviews in journal_trade_reviews (see [[project_daily_trade_journal]]). For each review, asks
Claude what -- if anything -- could have raised the entry/exit score using ONLY information
knowable at the time; if nothing available then would have scored well, the verdict is "Pass"
("you should have passed on this trade").

By default only processes reviews with actionable_verdict IS NULL (i.e. new reviews since the
last run -- safe to re-run daily after run_daily_journal.py adds new trades). Pass --all to
force-regenerate every review (used once to redo the whole book after a prompt fix).

No-hindsight guarantee: some of the base review system's own exit_reason text is legitimately
retrospective (too_soon/held_too_long verdicts compare the exit to what happened after -- a fine
outcome-grade for the base system, but exactly the "unknown future" this feature must not use).
sanitize() strips those specific forward-looking clauses out of what the model ever sees, and the
system prompt gives explicit per-exit_verdict-category guidance so it doesn't invert advice
direction (e.g. "held_too_long" -> "Tighter Stop", never "Hold Longer").

Usage:
    MYSQL_PASSWORD=... ANTHROPIC_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_generate_actionable_analysis.py
    ... --all              # force-regenerate every review, not just ones missing a verdict
    ... --ids 512,528       # limit to specific review ids (comma-separated)
    ... --dry-run           # print instead of writing to the DB

Requires: MYSQL_PASSWORD, ANTHROPIC_API_KEY. Optional: ANTHROPIC_WORKSPACE_ID (identity-linked
API keys need this -- the server error names it explicitly if it's missing).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re

import anthropic
import pandas as pd

from lib.mysql_lib import _get_conn, get_trade_reviews
from run_trade_review_pages import _row_to_json, _compute_directions

MODEL = "claude-sonnet-4-6"
CONCURRENCY = 6
WORKSPACE_ID = os.environ.get("ANTHROPIC_WORKSPACE_ID", "wrkspc_01VmLM2yMk7xPXJunyzSX12G")

HINDSIGHT_PATTERNS = [
    r"[^.]*\bover the following days?\b[^.]*\.",
    r"[^.]*\bdays? later\b[^.]*\.",
    r"[^.]*\bfollowing (day|days|session|sessions)\b[^.]*\.",
    r"[^.]*\bkept (falling|rising)\b[^.]*\.",
    r"[^.]*\bafterward\b[^.]*\.",
    r"[^.]*\bcontinued [\d.]+% further\b[^.]*\.",
]
_HINDSIGHT_RE = re.compile("|".join(HINDSIGHT_PATTERNS), re.IGNORECASE)


def sanitize(text: str | None) -> str | None:
    """Strip sentences computed from price action AFTER the exit date (see module docstring)."""
    if not text:
        return text
    cleaned = _HINDSIGHT_RE.sub(
        " [redacted: described price action after the exit date -- withheld, do not use or guess at it] ",
        text,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


SYSTEM = """You are auditing a personal options/equity trading journal. For each trade you are given \
the FACTS THAT WERE KNOWABLE AT OR BEFORE THE RELEVANT TIME: entry reasoning (computed at entry), exit \
reasoning (computed at exit, if closed -- already stripped of anything computed from price action AFTER \
the exit date; if you see a "[redacted: ...]" marker, that means forward-looking information was \
deliberately withheld -- do not guess at what it said and do not let it influence your verdict either way), \
tags, direction, dates, realized or unrealized P&L, and for discretionary trades any recorded thesis. Do NOT \
invent or reason from anything that happened after the trade's exit date -- and for a still-open position, \
do not guess at a future outcome; only comment on setup quality and what to watch for using what's given.

Guidance by exit_verdict category (these were computed by the base system, trust what they imply about
WHEN the underlying fact was knowable):
  - "too_soon": graded by comparing the exit to price action after the exit date (now redacted from what
    you see). You have no legitimate basis to say "hold longer" or suggest a trailing stop for these unless
    the review ALSO states a concrete, at-the-time-knowable rule that was violated (e.g. a documented,
    backtested playbook rule against capping profits) -- if there's no such rule cited, the honest verdict
    is usually "No Change" (the exit was reasonable given what was knowable then), not a critique.
  - "held_too_long": graded by an intra-trade peak-to-close comparison WITHIN the holding period, before
    exit -- this IS legitimately at-the-time information (the trader was holding through it in real time),
    so "Tighter Stop" (protect an open gain before it round-trips) is the usual right verdict here, not
    "Hold Longer" (that would make the described failure worse, not fix it).
  - "thesis_broken" / current-status reads on still-open positions: based on today's data, not the future --
    fine to use as-is.

Your job: write a short, concrete "actionable analysis" -- what, if anything, could have been done \
differently using ONLY the given at-the-time information to raise the entry score and/or exit score. If \
nothing available at entry time would have justified a good score, say so plainly (you should have \
passed). Do not fabricate specific technical details (exact price levels, news, indicators) that are not \
present in the given facts -- reason qualitatively from what's given rather than inventing false precision. \
If the entry and exit were already sound, say that plainly and briefly rather than manufacturing a critique.

Respond with STRICT JSON only, no markdown fences: {"verdict": "<label>", "analysis": "<text>"}

"verdict" MUST be exactly one of this fixed vocabulary (reuse one; only use "Other" as a last resort for a \
genuine fit failure):
  Pass, No Change, Enter Earlier, Wait for Pullback, Wait for Confirmation, Tighter Stop, Hold Longer, Size Down, Other

"analysis" style: plain text, a few short paragraphs (no markdown headers/bullets), similar in spirit to:
"VERDICT: ... WHY: ... WHAT WOULD HAVE HELPED: ... EXIT: ..." but adapt naturally -- don't force a section \
that doesn't apply. For a still-open position, replace the EXIT part with a brief CURRENT STATUS note \
instead. For an already-good entry/exit, keep it short and say there's nothing to fix rather than padding. \
Never reference redacted content or speculate about what it might have said."""


def build_user_prompt(r: dict) -> str:
    lines = [
        f"Ticker: {r['underlying']}" + (f" ({r['symbol']})" if r['symbol'] != r['underlying'] else ""),
        f"Asset category: {r.get('assetCategory')}",
        f"Direction: {r.get('direction') or 'unknown'}",
        f"Entry date: {r['entryDate']}",
        f"Exit date: {r['exitDate'] or 'still open (as of the data pull date)'}",
        f"Entry verdict (already scored): {r.get('entryVerdict')}",
        f"Entry reasoning (computed at entry): {sanitize(r.get('entryReason')) or '(none)'}",
    ]
    if r["exitDate"]:
        lines.append(f"Exit verdict (already scored): {r.get('exitVerdict')}")
        lines.append(f"Exit reasoning (computed at exit): {sanitize(r.get('exitReason')) or '(none)'}")
        lines.append(f"Realized P&L: {r.get('realizedPnl')}")
    else:
        lines.append(f"Current-status reasoning: {sanitize(r.get('exitReason')) or '(none)'}")
        lines.append(f"Unrealized P&L (last snapshot): {r.get('realizedPnl')}")
    if r.get("marketContext"):
        lines.append(f"Additional context/thesis: {sanitize(r['marketContext'])}")
    if r.get("tags"):
        lines.append(f"Tags: {', '.join(r['tags'])}")
    return "\n".join(lines)


TAXONOMY = {"Pass", "No Change", "Enter Earlier", "Wait for Pullback", "Wait for Confirmation",
            "Tighter Stop", "Hold Longer", "Size Down", "Other"}


async def process_one(client, sem, r, conn_writer):
    async with sem:
        prompt = build_user_prompt(r)
        for attempt in range(3):
            try:
                resp = await client.messages.create(
                    model=MODEL, max_tokens=700, system=SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                    extra_headers={"anthropic-workspace-id": WORKSPACE_ID},
                )
                text = resp.content[0].text.strip()
                if text.startswith("```"):
                    text = text.strip("`")
                    if text.startswith("json"):
                        text = text[4:]
                data = json.loads(text)
                verdict = data["verdict"].strip()
                if verdict not in TAXONOMY:
                    verdict = "Other"
                analysis = data["analysis"].strip()
                await conn_writer(r["id"], verdict, analysis)
                return True
            except Exception as e:
                if attempt == 2:
                    print(f"  FAILED id={r['id']} {r['underlying']}: {type(e).__name__}: {e}")
                    return False
                await asyncio.sleep(1.5 * (attempt + 1))


async def main(ids: list[int] | None, do_all: bool, dry_run: bool):
    conn = _get_conn()
    df = get_trade_reviews()
    missing_mask = df["actionable_verdict"].isna()
    conn.close()

    rows = [_row_to_json(r) for _, r in df.iterrows()]
    _compute_directions(rows)
    id_to_missing = dict(zip(df["id"], missing_mask))

    todo = rows if do_all else [r for r in rows if id_to_missing.get(r["id"], True)]
    if ids:
        todo = [r for r in todo if r["id"] in ids]
    print(f"{len(todo)} reviews to process" + (" (dry run, no writes)" if dry_run else ""))

    write_conn = None if dry_run else _get_conn()
    write_cur = None if dry_run else write_conn.cursor()
    write_lock = asyncio.Lock()
    done_count = [0]

    async def writer(review_id, verdict, analysis):
        async with write_lock:
            done_count[0] += 1
            if dry_run:
                print(f"--- id={review_id} verdict={verdict} ---\n{analysis}\n")
                return
            write_cur.execute(
                "UPDATE journal_trade_reviews SET actionable_verdict=%s, actionable_analysis=%s, updated_at=NOW() WHERE id=%s",
                (verdict, analysis, review_id),
            )
            write_conn.commit()
            if done_count[0] % 25 == 0:
                print(f"  ...{done_count[0]}/{len(todo)} written")

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*[process_one(client, sem, r, writer) for r in todo])
    if write_cur:
        write_cur.close()
        write_conn.close()

    ok = sum(1 for x in results if x)
    print(f"Done: {ok}/{len(todo)} succeeded, {len(todo) - ok} failed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="force-regenerate every review, not just ones missing a verdict")
    ap.add_argument("--ids", type=str, default=None, help="comma-separated review ids to limit to")
    ap.add_argument("--dry-run", action="store_true", help="print instead of writing to the DB")
    a = ap.parse_args()
    id_list = [int(x) for x in a.ids.split(",")] if a.ids else None
    asyncio.run(main(id_list, a.all, a.dry_run))

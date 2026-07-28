#!/usr/bin/env python3
"""
Aggregate the per-video auto_extract.json files into knowledge-base artifacts:

  trades/observed_trades.jsonl   all observed trades, newest-first
  ambiguous_tickers.md           "homework": every unclear ticker w/ clickable
                                 YouTube timestamp links, grouped by video
  philosophy/principles_raw.jsonl  flattened principles (input for synthesis)

Source of truth: data/martin_luk/videos/<type>/<date>_<id>/auto_extract.json
Run:  .venv/bin/python3 build_luk_extracts.py
"""

from __future__ import annotations

import datetime
import json
import re
from datetime import timedelta
from pathlib import Path

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}


def resolve_fill_date(timing: str, stream_date: str) -> str:
    """Resolve a fill_timing phrase to an ISO date, using real date math.

    stream_date anchors all relative phrases. Returns "" when unresolvable
    (e.g. "last week") so the gap is explicit rather than silently = stream date.
    """
    try:
        s = datetime.date.fromisoformat(stream_date)
    except ValueError:
        return ""
    t = (timing or "").strip().lower()
    if t in ("", "today", "now", "intraday"):
        return stream_date
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        return t
    if t == "yesterday":
        d = s - timedelta(days=1)
        while d.weekday() >= 5:  # back up over the weekend to prior trading day
            d -= timedelta(days=1)
        return d.isoformat()
    if t in _WEEKDAYS:
        d = s - timedelta(days=1)
        for _ in range(7):
            if d.weekday() == _WEEKDAYS[t]:
                return d.isoformat()
            d -= timedelta(days=1)
        return ""
    m = re.match(r"([a-z]{3,9})\s+(\d{1,2})$", t)  # e.g. "december 17"
    if m:
        mon = _MONTHS.get(m.group(1)[:3])
        if mon:
            year = s.year if mon <= s.month else s.year - 1
            try:
                return datetime.date(year, mon, int(m.group(2))).isoformat()
            except ValueError:
                return ""
    return ""

REPO = Path(__file__).resolve().parent
KB = REPO / "data" / "martin_luk"
VIDEOS = KB / "videos"
TRADES_OUT = KB / "trades" / "observed_trades.jsonl"
AMBIG_OUT = KB / "ambiguous_tickers.md"
PRINC_RAW = KB / "philosophy" / "principles_raw.jsonl"

_DATE_SUFFIX = re.compile(r"\s*\|\s*\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s*$")


def clean_title(t: str) -> str:
    return _DATE_SUFFIX.sub("", t).strip()


def mmss_to_secs(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        return 0
    return h * 3600 + m * 60 + s


def md_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def load_all() -> list[dict]:
    extracts = []
    for p in sorted(VIDEOS.glob("*/*/auto_extract.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"  ⚠️  INVALID JSON, skipped: {p.relative_to(REPO)} ({e})")
            continue
        data["_path"] = str(p.parent.relative_to(REPO))
        extracts.append(data)
    return extracts


def main() -> None:
    extracts = load_all()
    extracts.sort(key=lambda d: d.get("date", ""), reverse=True)
    print(f"loaded {len(extracts)} auto_extract.json files")

    # ── observed_trades.jsonl ────────────────────────────────────────────────
    trades = []
    for d in extracts:
        sd = d.get("date", "")
        for t in d.get("observed_trades", []):
            timing = t.get("fill_timing", "")
            t["fill_timing"] = timing
            t["fill_date"] = resolve_fill_date(timing, sd)
            trades.append(t)
    # stable sort: date desc, then ticker
    trades.sort(key=lambda t: (t.get("date", ""), t.get("ticker", "")), reverse=True)
    TRADES_OUT.write_text(
        "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trades),
        encoding="utf-8",
    )

    # ── principles_raw.jsonl ─────────────────────────────────────────────────
    n_princ = 0
    with PRINC_RAW.open("w", encoding="utf-8") as f:
        for d in extracts:
            for pr in d.get("principles", []):
                row = {
                    "video_id": d.get("video_id", ""),
                    "date": d.get("date", ""),
                    "category": pr.get("category", ""),
                    "text": pr.get("text", ""),
                    "timestamp": pr.get("timestamp", ""),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_princ += 1

    # ── ambiguous_tickers.md (homework: tickers + fill dates) ────────────────
    def ts_link(vid: str, ts: str) -> str:
        return f"[{ts}](https://www.youtube.com/watch?v={vid}&t={mmss_to_secs(ts)}s)" if ts else "—"

    def trade_needs_check(t: dict, stream_date: str) -> bool:
        """A trade needs a human glance if its ticker is unresolved, its fill date
        couldn't be resolved, or the fill date was INFERRED to a different day than the
        stream (vs. him stating an explicit date or it being same-session)."""
        if t.get("ticker", "?") == "?":
            return True
        fd = t.get("fill_date", "")
        if not fd:
            return True
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", (t.get("fill_timing", "") or "").strip()):
            return False  # he stated the explicit date
        return fd != stream_date  # inferred a different day → confirm which one

    total_ambig = sum(len(d.get("ambiguous_tickers", [])) for d in extracts)
    n_trade_checks = sum(
        trade_needs_check(t, d.get("date", ""))
        for d in extracts for t in d.get("observed_trades", [])
    )
    vids_amb = [d for d in extracts if d.get("ambiguous_tickers")]
    vids_shown = [d for d in extracts if d.get("ambiguous_tickers") or d.get("observed_trades")]

    lines = ["# Martin Luk — Homework: tickers & trade dates\n"]
    lines.append("> Generated by `build_luk_extracts.py` from per-video `auto_extract.json`.\n")
    lines.append(
        "Two checks per video. **Ambiguous tickers**: spots where the auto-caption garbled a "
        "symbol — click the timestamp, check the chart, confirm the ticker. **Trades**: each "
        "trade with the day it was placed; ⬜ marks rows that need a glance — an unresolved "
        "ticker (`?`), an unresolved fill date, or a date *inferred* to a different day than the "
        "stream (e.g. he said \"Thursday\"). Rows with no ⬜ are same-session or he stated the date.\n"
    )
    lines.append(
        f"**{total_ambig}** ticker flags · **{n_trade_checks}** trades to date-check · "
        f"across **{len(vids_shown)}** videos. Conf: 🟡 likely · ❓ unsure.\n"
    )

    lines.append("## Index — ticker flags by video\n")
    for d in sorted(vids_amb, key=lambda d: len(d["ambiguous_tickers"]), reverse=True):
        anchor = re.sub(r"[^a-z0-9]+", "-",
                        f"{d['date']}--{clean_title(d.get('title',''))}".lower()).strip("-")
        lines.append(
            f"- [{d['date']} — {clean_title(d.get('title',''))}](#{anchor}) "
            f"· {len(d['ambiguous_tickers'])}"
        )
    lines.append("")

    for d in vids_shown:
        vid = d.get("video_id", "")
        sd = d.get("date", "")
        title = clean_title(d.get("title", ""))
        amb = d.get("ambiguous_tickers", [])
        trd = d.get("observed_trades", [])
        lines.append(f"\n## {sd} — {title}\n")
        lines.append(
            f"[▶ watch](https://www.youtube.com/watch?v={vid}) · `{d['_path']}` · "
            f"{len(amb)} ticker flags · {len(trd)} trades\n"
        )

        if amb:
            lines.append("**Ambiguous tickers**\n")
            lines.append("| ✔ | Time | Caption said | Context | Best guess | Conf |")
            lines.append("|---|------|--------------|---------|-----------|------|")
            for a in amb:
                conf = {"confirmed": "✅", "likely": "🟡"}.get(a.get("confidence"), "❓")
                lines.append(
                    f"| ⬜ | {ts_link(vid, a.get('timestamp',''))} "
                    f"| {md_cell(a.get('caption_text',''))} | {md_cell(a.get('context',''))} "
                    f"| {md_cell(a.get('guess','') or '?')} | {conf} |"
                )
            lines.append("")

        if trd:
            lines.append("**Trades** (confirm fill dates)\n")
            lines.append("| ✔ | Time | Ticker | Dir · Action | He said | Fill date |")
            lines.append("|---|------|--------|--------------|---------|-----------|")
            for t in trd:
                src = t.get("source", "")
                ts = src.split("@")[-1] if "@" in src else ""
                check = "⬜" if trade_needs_check(t, sd) else "·"
                tk = md_cell(t.get("ticker", "?"))
                da = f"{t.get('direction','')} · {t.get('action','')}"
                said = md_cell(t.get("fill_timing", "") or "—")
                fd = t.get("fill_date", "") or "_(unresolved)_"
                lines.append(
                    f"| {check} | {ts_link(vid, ts)} | {tk} | {da} | {said} | {fd} |"
                )
            lines.append("")

    AMBIG_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✓ {TRADES_OUT.relative_to(REPO)}  ({len(trades)} trades)")
    print(f"✓ {PRINC_RAW.relative_to(REPO)}  ({n_princ} principles)")
    print(f"✓ {AMBIG_OUT.relative_to(REPO)}  ({total_ambig} ticker flags, "
          f"{n_trade_checks} trade date-checks, {len(vids_shown)} videos)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Home page for the private journal site: data/journal/index.html -- one card per section.
Run by deploy_trade_journal.sh before every sync, so the site root always has it."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from run_trade_review_pages import BASE_CSS

ROOT = Path("data/journal")
SECTIONS = [
    ("trade_reviews.html", "Trade journal", "Every reviewed trade: entry and exit verdicts, the rubric grade, and a chart per trade."),
    ("summary.html", "Performance", "Strategy performance, top and bottom trades, and results by vehicle."),
    ("alerts.html", "Live alerts", "Today's alert monitor feed: setups graded A/B (loud), C (dimmed), with industry context."),
    ("tutorial/qcom/index.html", "Tutorial: QCOM entries", "A flip book of 12 QCOM entries (8/31 to 9/11): judge each setup before you see the verdict."),
    ("tito/index.html", "Tito's best trades", "His 20 curated winners with daily charts, option paths, commentary and the scale-out rule."),
]

CSS = """
 body { padding: 36px 28px 60px; max-width: 880px; margin: 0 auto; }
 h1 { font-size: 24px; margin: 0 0 4px; } .sub { color: var(--muted); font-size: 13px; margin-bottom: 22px; }
 .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; }
 a.card { display: block; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px;
          color: var(--text); text-decoration: none; transition: border-color .15s, box-shadow .15s; }
 a.card:hover { border-color: var(--accent); box-shadow: 0 2px 10px rgba(63,111,216,.12); }
 a.card h2 { font-size: 16px; margin: 0 0 6px; color: var(--accent); } a.card p { margin: 0; font-size: 13px; color: var(--muted); }
 a.card.missing { opacity: .5; pointer-events: none; }
"""


def main() -> int:
    cards = []
    for href, title, desc in SECTIONS:
        ok = (ROOT / href).exists()
        cards.append(f'<a class="card{"" if ok else " missing"}" href="{href}"><h2>{title}</h2><p>{desc}{"" if ok else " (not generated yet)"}</p></a>')
    page = (f"<title>Trading Journal</title>\n<style>{BASE_CSS}{CSS}</style>\n<h1>Trading journal</h1>\n"
            f'<div class="sub">Private site. Updated {datetime.now():%Y-%m-%d %H:%M}.</div>\n<div class="grid">{"".join(cards)}</div>\n')
    (ROOT / "index.html").write_text(page)
    print(f"wrote {ROOT / 'index.html'} ({sum(1 for h, *_ in SECTIONS if (ROOT / h).exists())}/{len(SECTIONS)} sections present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

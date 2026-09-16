"""Sortable HTML rendering of one daily journal (data/journal/days/<date>.html).

The markdown journal stays the surface for hand-written notes; this is the same
four grids, rendered as tables you can re-sort by clicking a header. Gabe
(2026-09-15): "split Entry/Exit into two fields, then make each grid sortable by
TICKER, entry date, exit date and P&L" -- markdown tables can't sort, so the
grids get a second rendering here and the entry/exit columns are added to both.

Every column is clickable; the four asked-for keys are the ones that exist in all
four grids. Blank cells always sort last, whichever direction.

Pure rendering -- the caller (run_daily_journal.py) owns the data.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from lib.journal.sortable import SORT_JS

try:  # the site's shared palette; run_daily_journal.py runs from the repo root
    from run_trade_review_pages import BASE_CSS
except Exception:  # noqa: BLE001 -- keep the page renderable standalone
    BASE_CSS = """
      :root {
        --bg: #f7f8fa; --panel: #ffffff; --border: #e1e4ea; --text: #1a1d24; --muted: #6b7280;
        --good: #157a4d; --bad: #c23b3b; --neutral: #a3690a; --gray: #5b6272; --accent: #3f6fd8;
        --chip-bg: #eef1f6;
      }
      * { box-sizing: border-box; }
      body { margin: 0; background: var(--bg); color: var(--text);
             font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .pnl-pos { color: var(--good); } .pnl-neg { color: var(--bad); }
    """

PAGE_CSS = """
 body { padding: 28px 24px 64px; max-width: 1280px; margin: 0 auto; }
 a { color: var(--accent); }
 h1 { font-size: 23px; margin: 0 0 4px; }
 .sub { color: var(--muted); font-size: 13px; margin-bottom: 6px; }
 .nav { font-size: 12.5px; margin-bottom: 20px; }
 .stats { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 22px; }
 .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
         padding: 8px 14px; font-size: 13px; }
 .stat b { display: block; font-size: 17px; font-weight: 600; }
 h2 { font-size: 16px; margin: 30px 0 4px; }
 .hint { color: var(--muted); font-size: 12px; margin: 0 0 10px; }
 .wrap { overflow-x: auto; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; }
 table { border-collapse: collapse; width: 100%; font-size: 13px; }
 th, td { padding: 7px 11px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }
 th { position: sticky; top: 0; background: var(--chip-bg); font-size: 11.5px; text-transform: uppercase;
      letter-spacing: .03em; color: var(--muted); cursor: pointer; user-select: none; }
 th:hover { color: var(--accent); }
 th .arrow { opacity: .35; font-size: 9px; margin-left: 3px; }
 th.sorted { color: var(--accent); } th.sorted .arrow { opacity: 1; }
 td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
 td.tkr { font-weight: 600; }
 td.sym { color: var(--muted); }
 tbody tr:hover { background: #fafbfd; }
 tbody tr:last-child td { border-bottom: none; }
 .empty { color: var(--muted); font-size: 13px; padding: 12px 2px; }
 .note { color: var(--muted); font-size: 11.5px; margin: 7px 0 0; }
"""


# (label, key, kind) -- kind drives alignment and the sort comparator.
# 'text' sorts lexically, everything else numerically ('date' keys are ISO, so
# lexical and chronological agree; they sort numerically as YYYYMMDD).
COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    "opened": [
        ("Ticker", "ticker", "text"), ("Contract", "contract", "text"),
        ("Fills", "fills", "int"), ("Qty", "qty", "qty"),
        ("Entry date", "entry_date", "date"), ("Entry $", "entry_price", "px"),
        ("Exit date", "exit_date", "date"), ("Exit $", "exit_price", "px"),
        ("P&L", "pnl", "pnl"),
    ],
    "closed": [
        ("Ticker", "ticker", "text"), ("Contract", "contract", "text"),
        ("Fills", "fills", "int"), ("Qty", "qty", "qty"),
        ("Entry date", "entry_date", "date"), ("Entry $", "entry_price", "px"),
        ("Exit date", "exit_date", "date"), ("Exit $", "exit_price", "px"),
        ("Realized P&L", "pnl", "pnl"),
    ],
    "roundtrip": [
        ("Ticker", "ticker", "text"), ("Contract", "contract", "text"),
        ("Fills", "fills", "int"), ("Qty opened", "qty_opened", "qty"), ("Qty closed", "qty_closed", "qty"),
        ("Entry date", "entry_date", "date"), ("Entry $", "entry_price", "px"),
        ("Exit date", "exit_date", "date"), ("Exit $", "exit_price", "px"),
        ("Realized P&L", "pnl", "pnl"), ("Still open?", "still_open_s", "text"),
    ],
    "held": [
        ("Ticker", "ticker", "text"), ("Contract", "contract", "text"),
        ("Position", "qty", "qty"),
        ("Entry date", "entry_date", "date"), ("Entry $", "entry_price", "px"),
        ("Exit date", "exit_date", "date"), ("Mark", "mark", "px"),
        ("Unrealized P&L", "pnl", "pnl"),
    ],
}

SECTIONS = [
    ("opened", "Opened today (new entries)", "Judge the entry."),
    ("closed", "Closed today (exits)", "Judge the exit."),
    ("roundtrip", "Same-day round trips (opened AND closed today)",
     "Opened and closed inside the session -- the overtrading tell."),
    ("held", "Held, untouched today (no fills)", "Should this have been closed?"),
]


def _cell(row: dict, key: str, kind: str) -> str:
    """One <td>: data-v carries the raw sort value, the text carries the display form."""
    v = row.get(key)
    if v is None or v == "":
        return '<td class="num" data-v=""></td>' if kind != "text" else '<td data-v=""></td>'
    if kind == "text":
        cls = "tkr" if key == "ticker" else ("sym" if key == "contract" else "")
        return f'<td class="{cls}" data-v="{escape(str(v))}">{escape(str(v))}</td>'
    if kind == "date":
        return f'<td class="num" data-v="{str(v).replace("-", "")}">{escape(str(v))}</td>'
    if kind == "int":
        return f'<td class="num" data-v="{v}">{v:g}</td>'
    if kind == "qty":
        return f'<td class="num" data-v="{v}">{v:g}</td>'
    if kind == "px":
        return f'<td class="num" data-v="{v}">{v:,.4f}</td>'
    # pnl
    cls = "pnl-pos" if v >= 0 else "pnl-neg"
    sign = "+" if v >= 0 else "−"
    return f'<td class="num" data-v="{v}"><span class="{cls}">{sign}${abs(v):,.2f}</span></td>'


def _grid(kind: str, rows: list[dict]) -> str:
    cols = COLUMNS[kind]
    if not rows:
        return '<div class="empty">None.</div>'
    head = "".join(
        f'<th class="{"num" if k != "text" else ""}">{escape(lbl)}<span class="arrow">▴▾</span></th>'
        for lbl, _key, k in cols
    )
    body = "".join(
        "<tr>" + "".join(_cell(r, key, k) for _lbl, key, k in cols) + "</tr>"
        for r in rows
    )
    return f'<div class="wrap"><table class="grid"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_day_page(ctx: dict) -> str:
    """ctx: date_iso, nav, day_pnl, n_fills, n_symbols, n_positions, buckets{...}, entry_date_floor."""
    d = ctx["date_iso"]
    nav, pnl = ctx.get("nav"), ctx.get("day_pnl")
    stats = [
        ("NAV", f"${nav:,.2f}" if nav is not None else "n/a"),
        ("Day P&L", f"${pnl:,.2f}" if pnl is not None else "n/a"),
        ("Fills", f"{ctx['n_fills']}"),
        ("Symbols traded", f"{ctx['n_symbols']}"),
        ("Open positions", f"{ctx['n_positions']}"),
    ]
    stat_html = "".join(f'<div class="stat">{escape(lbl)}<b>{escape(val)}</b></div>' for lbl, val in stats)

    floor = ctx.get("entry_date_floor")
    caveat = ""
    if floor:
        caveat = (f'<p class="note">Entry dates come from flat-to-flat cycles in <code>journal_trades</code>, '
                  f'which starts {escape(floor)} — a position opened before then shows a blank entry date.</p>')

    parts = [f'<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>Journal {escape(d)}</title>",
             f"<style>{BASE_CSS}{PAGE_CSS}</style>",
             f"<h1>Trade journal — {escape(d)}</h1>",
             '<div class="sub">Click any column header to re-sort. Ticker, entry date, exit date and P&amp;L '
             'are present in every grid.</div>',
             f'<div class="nav"><a href="index.html">All days</a> &middot; <a href="../index.html">Journal home</a> '
             f'&middot; notes live in <code>data/journal/{escape(d)}.md</code></div>',
             f'<div class="stats">{stat_html}</div>']
    for key, title, hint in SECTIONS:
        rows = ctx["buckets"].get(key, [])
        parts.append(f"<h2>{escape(title)} <span style=\"color:var(--muted);font-weight:400\">({len(rows)})</span></h2>")
        parts.append(f'<p class="hint">{escape(hint)}</p>')
        parts.append(_grid(key, rows))
        if rows and key in ("closed", "roundtrip", "held") and caveat:
            parts.append(caveat)
        if key == "opened" and any(r.get("pnl") is not None for r in rows):
            parts.append('<p class="note">A realized P&amp;L on an <em>opening</em> fill is IBKR re-attributing '
                         'FIFO P&amp;L to a recently closed cycle in the same contract, not today\u2019s entry '
                         'making money \u2014 it cancels the offsetting figure booked on that close.</p>')
    parts.append(f'<p class="note">Generated {datetime.now():%Y-%m-%d %H:%M}. A rolled spread is judged on the '
                 f'campaign line in the markdown journal, not on the roll’s closing fill.</p>')
    parts.append(f"<script>{SORT_JS}</script>")
    return "\n".join(parts) + "\n"


def render_days_index(days_dir: Path) -> str:
    """Index of every generated day page, newest first."""
    days = sorted((p.stem for p in days_dir.glob("[0-9]*.html")), reverse=True)
    items = "".join(f'<li><a href="{escape(d)}.html">{escape(d)}</a></li>' for d in days)
    return (f'<meta charset="utf-8">\n<title>Daily journals</title>\n'
            f"<style>{BASE_CSS}{PAGE_CSS} ul {{ line-height: 1.9; padding-left: 18px; }}</style>\n"
            f"<h1>Daily journals</h1>\n"
            f'<div class="sub">Sortable grids per session. {len(days)} day(s).</div>\n'
            f'<div class="nav"><a href="../index.html">Journal home</a></div>\n'
            f"<ul>{items}</ul>\n")

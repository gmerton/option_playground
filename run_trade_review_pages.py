#!/usr/bin/env python3
"""
Generate the trade-review pages: a lightweight index (data/journal/trade_reviews.html,
no chart data -- just the searchable/sortable table) linking out to one small,
self-contained detail page per review (data/journal/trades/<id>_<TICKER>_<date>.html,
each with its own 1-2 charts).

Replaces the single-file run_trade_reviews_page.py, which loaded every review's
full candle data into one ever-growing file and became unresponsive once
Lightweight Charts had ~500+ instances to create on load (see
[[project_daily_trade_journal]]). Splitting into an index + per-trade pages keeps
the index fast at any scale (pure text, no chart data) and makes each trade a
real, bookmarkable file.

Chart data is fetched through lib.journal.price_cache, which caches daily/
intraday OHLCV on disk per symbol (data/cache/journal_daily/,
data/cache/journal_intraday/) -- closed-session data is immutable and cached
forever, so a full regenerate after the first run is mostly cache hits rather
than ~1-2 Tradier calls per review.

Usage:
    MYSQL_PASSWORD=... TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_trade_review_pages.py
    ... --no-charts      # skip Tradier entirely, detail pages get no chart (fast, for text-only iteration)

Requires: MYSQL_PASSWORD, TRADIER_API_KEY.

Each review may also carry a hand-written `actionable_analysis` (free text --
what could have raised the entry/exit score using only information available
at the time, no hindsight) and a short `actionable_verdict` label -- a small,
CONSISTENT vocabulary so it's filterable/indexable on the index page instead
of read one page at a time. Reuse an existing label rather than mint a new one
unless a review genuinely doesn't fit any of these:
  Pass                   -- no entry available then would have scored well; shouldn't have traded it
  No Change              -- already close to optimal given the information at the time
  Enter Earlier          -- right idea, but entry lagged the actual signal
  Wait for Pullback      -- right idea, but chased an extended price instead of waiting for one
  Wait for Confirmation  -- entered before a would-be trigger (breakout hold, reversal candle, etc.) confirmed
  Tighter Stop           -- exit discipline: should have cut the loss sooner
  Hold Longer            -- exit discipline: cut a working trade too early
  Size Down              -- entry/exit were fine, position size was too big for the setup's risk
"""
from __future__ import annotations

import argparse
import asyncio
import calendar
import os
import re
from datetime import date, datetime, timedelta
import json
from pathlib import Path

import pandas as pd

from lib.mysql_lib import _get_conn, get_trade_reviews
from lib.journal.price_cache import get_daily_history_cached, get_intraday_bars_cached
from lib.tradier.tradier_client_wrapper import TradierClient

INDEX_OUT = Path("data/journal/trade_reviews.html")
TRADES_DIR = Path("data/journal/trades")

LIGHTWEIGHT_CHARTS_SCRIPT = (
    '<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>'
)

# ── Shared bits ─────────────────────────────────────────────────────────────

BASE_CSS = """
  :root {
    --bg: #0f1115; --panel: #161922; --border: #262b38; --text: #e6e9f0; --muted: #8b93a7;
    --good: #34c98c; --bad: #ef6b6b; --neutral: #f0b556; --gray: #7d85a3; --accent: #5b8def;
    --chip-bg: #1f2430;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px;
    font-weight: 600; text-transform: uppercase; letter-spacing: .03em; white-space: nowrap;
  }
  .badge-good { background: rgba(52,201,140,.15); color: var(--good); }
  .badge-bad { background: rgba(239,107,107,.15); color: var(--bad); }
  .badge-neutral, .badge-too_soon, .badge-too_late, .badge-held_too_long, .badge-thesis_broken {
    background: rgba(240,181,86,.15); color: var(--neutral);
  }
  .badge-gray_area, .badge-still_valid { background: rgba(125,133,163,.18); color: var(--gray); }
  .badge-n_a { background: rgba(125,133,163,.1); color: var(--muted); }
  .pnl-pos { color: var(--good); }
  .pnl-neg { color: var(--bad); }
  .tag {
    font-size: 10.5px; background: var(--chip-bg); color: var(--accent);
    border: 1px solid var(--border); border-radius: 5px; padding: 1px 6px;
  }
"""


def badge_html(v: str | None) -> str:
    if not v:
        return '<span class="badge badge-n_a">—</span>'
    return f'<span class="badge badge-{v}">{v.replace("_", " ")}</span>'


def direction_badge_html(v: str | None) -> str:
    if not v:
        return '<span class="badge badge-n_a">—</span>'
    cls = "badge-good" if v == "LONG" else "badge-bad" if v == "SHORT" else "badge-neutral"
    return f'<span class="badge {cls}">{v}</span>'


def actionable_badge_html(v: str | None) -> str:
    if not v:
        return '<span class="badge badge-n_a">—</span>'
    cls = "badge-bad" if v == "Pass" else "badge-good" if v == "No Change" else "badge-neutral"
    return f'<span class="badge {cls}">{v}</span>'


def fmt_pnl(v: float | None) -> str:
    if v is None:
        return ""
    cls = "pnl-pos" if v >= 0 else "pnl-neg"
    sign = "+" if v >= 0 else ""
    return f'<span class="{cls}">{sign}${v:,.2f}</span>'


def detail_filename(review: dict) -> str:
    safe_ticker = re.sub(r"[^A-Za-z0-9]", "", review["underlying"]) or "X"
    d = review["entryDate"] or "unknown"
    return f'{review["id"]}_{safe_ticker}_{d}.html'


def _row_to_json(r: pd.Series) -> dict:
    def s(v):
        if pd.isna(v):
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v

    return {
        "id": int(r["id"]),
        "underlying": r["underlying_symbol"],
        "symbol": r["symbol"],
        "_conid": int(r["conid"]) if pd.notna(r.get("conid")) else None,
        "assetCategory": s(r.get("asset_category")),
        "entryDate": s(r["entry_date"]),
        "exitDate": s(r.get("exit_date")),
        "entryVerdict": s(r.get("entry_verdict")),
        "entryReason": s(r.get("entry_reason")),
        "exitVerdict": s(r.get("exit_verdict")),
        "exitReason": s(r.get("exit_reason")),
        "marketContext": s(r.get("market_context")),
        "actionableAnalysis": s(r.get("actionable_analysis")),
        "actionableVerdict": s(r.get("actionable_verdict")),
        "tags": [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()],
        "realizedPnl": s(r.get("realized_pnl")),
    }


def _fill_events(conn, conid: int, trade_date: date, sides: tuple[str, ...]) -> list[tuple[datetime, float]]:
    if conid is None:
        return []
    placeholders = ",".join(["%s"] * len(sides))
    df = pd.read_sql(
        f"""SELECT trade_datetime, trade_price FROM journal_trades
            WHERE conid = %s AND trade_date = %s AND open_close IN ({placeholders})
            ORDER BY trade_datetime""",
        conn, params=[conid, trade_date, *sides],
    )
    return [(r.trade_datetime.to_pydatetime(), float(r.trade_price)) for r in df.itertuples()]


def _epoch(dt: datetime) -> int:
    """Treat a naive ET wall-clock datetime AS UTC -- see run_trade_review_pages history
    for why (avoids host-timezone dependence; lightweight-charts displays numeric
    times as UTC by default, so this makes the label show the correct ET time)."""
    return calendar.timegm(dt.timetuple())


def _floor_5min(dt: datetime) -> datetime:
    return dt.replace(minute=(dt.minute // 5) * 5, second=0, microsecond=0)


def _candles_json(df: pd.DataFrame, *, intraday: bool) -> list[dict]:
    out = []
    for ts, row in df.iterrows():
        t = _epoch(ts.to_pydatetime()) if intraday else ts.strftime("%Y-%m-%d")
        out.append({"time": t, "open": round(float(row["open"]), 4), "high": round(float(row["high"]), 4),
                     "low": round(float(row["low"]), 4), "close": round(float(row["close"]), 4)})
    return out


# ── Chart data ───────────────────────────────────────────────────────────────

async def _build_daily_chart(client: TradierClient, underlying: str, entry_date: date,
                              exit_date: date | None, entry_fills, exit_fills, symbol: str,
                              asset_category: str) -> dict:
    lookback_start = entry_date - timedelta(days=55)
    lookahead_end = (exit_date + timedelta(days=10)) if exit_date else date.today()
    df = await get_daily_history_cached(underlying, lookback_start, lookahead_end, client=client)
    if df is None or df.empty:
        return {"type": "none", "candles": [], "sma20": [], "markers": [],
                "note": "No daily price history available for this window."}
    # df is a slice of the shared, cached DataFrame (see price_cache._daily_mem) --
    # copy before mutating, or these column assignments risk corrupting the cache
    # that every other review for this symbol reads from.
    df = df.copy()
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["sma20"] = df["close"].rolling(20).mean()

    candles = _candles_json(df, intraday=False)
    sma20 = [{"time": ts.strftime("%Y-%m-%d"), "value": round(float(v), 4)}
              for ts, v in df["sma20"].items() if pd.notna(v)]

    markers = []
    if entry_fills:
        avg = sum(x[1] for x in entry_fills) / len(entry_fills)
        markers.append({"time": entry_date.strftime("%Y-%m-%d"), "position": "belowBar",
                         "color": "#34c98c", "shape": "arrowUp", "text": f"{symbol} entry ${avg:.2f}"})
    if exit_fills and exit_date:
        avg = sum(x[1] for x in exit_fills) / len(exit_fills)
        markers.append({"time": exit_date.strftime("%Y-%m-%d"), "position": "aboveBar",
                         "color": "#ef6b6b", "shape": "arrowDown", "text": f"{symbol} exit ${avg:.2f}"})

    note = None
    if asset_category == "OPT":
        note = "Chart is the underlying's daily price -- markers show the option's actual fill dates/prices."
    return {"type": "daily", "candles": candles, "sma20": sma20, "markers": markers, "note": note}


async def _build_intraday_chart(client: TradierClient, underlying: str, entry_date: date,
                                 entry_fills, exit_fills, symbol: str, asset_category: str) -> dict | None:
    bars = await get_intraday_bars_cached(underlying, entry_date, client=client)
    if bars is None or bars.empty:
        return None
    candles = _candles_json(bars, intraday=True)
    markers = []
    if entry_fills:
        t, _ = entry_fills[0]
        avg = sum(x[1] for x in entry_fills) / len(entry_fills)
        markers.append({"time": _epoch(_floor_5min(t)), "position": "belowBar",
                         "color": "#34c98c", "shape": "arrowUp", "text": f"{symbol} entry ${avg:.2f}"})
    if exit_fills:
        t, _ = exit_fills[-1]
        avg = sum(x[1] for x in exit_fills) / len(exit_fills)
        markers.append({"time": _epoch(_floor_5min(t)), "position": "aboveBar",
                         "color": "#ef6b6b", "shape": "arrowDown", "text": f"{symbol} exit ${avg:.2f}"})
    note = None
    if asset_category == "OPT":
        note = "Chart is the underlying's intraday price -- Tradier doesn't have usable intraday option premium history (trade-prints only). Markers show the option's actual fill times/prices."
    return {"type": "intraday", "candles": candles, "sma20": [], "markers": markers, "note": note}


async def _build_chart_data(client: TradierClient, conn, review: dict) -> dict:
    underlying = review["underlying"]
    entry_date = date.fromisoformat(review["entryDate"])
    exit_date = date.fromisoformat(review["exitDate"]) if review["exitDate"] else None
    conid = review.get("_conid")
    symbol, asset_category = review["symbol"], review["assetCategory"]
    same_day = exit_date is not None and exit_date == entry_date

    entry_fills = _fill_events(conn, conid, entry_date, ("O", "C;O"))
    exit_fills = _fill_events(conn, conid, exit_date, ("C", "C;O")) if exit_date else []

    daily = await _build_daily_chart(client, underlying, entry_date, exit_date,
                                      entry_fills, exit_fills, symbol, asset_category)

    if same_day:
        intraday = await _build_intraday_chart(client, underlying, entry_date,
                                                 entry_fills, exit_fills, symbol, asset_category)
        if intraday is not None:
            return {"type": "same_day_pair", "daily": daily, "intraday": intraday}
        daily["note"] = ((daily.get("note") or "") + " Intraday data unavailable for this date; showing daily context only.").strip()
        return daily

    return daily


# ── Detail page ──────────────────────────────────────────────────────────────

CHART_JS = """
function renderChart(cd, container) {
  if (!cd) { container.innerHTML = '<div class="chart-empty">No chart data available.</div>'; return; }
  if (cd.type === 'same_day_pair') {
    container.innerHTML = `
      <div class="chart-pair-label">Daily context (was the setup right?)</div>
      <div class="chart-sub" id="${container.id}-daily"></div>
      <div class="chart-pair-label">5-min intraday (was the entry/exit timing right?)</div>
      <div class="chart-sub" id="${container.id}-intraday"></div>
    `;
    renderOneChart(cd.daily, document.getElementById(`${container.id}-daily`));
    renderOneChart(cd.intraday, document.getElementById(`${container.id}-intraday`));
    return;
  }
  renderOneChart(cd, container);
}
function renderOneChart(cd, container) {
  if (!cd || !cd.candles || !cd.candles.length) {
    container.innerHTML = `<div class="chart-empty">${(cd && cd.note) || 'No chart data available.'}</div>`;
    return;
  }
  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth || 860, height: 300,
    layout: { background: { color: '#12141c' }, textColor: '#8b93a7' },
    grid: { vertLines: { color: '#262b38' }, horzLines: { color: '#262b38' } },
    rightPriceScale: { borderColor: '#262b38' },
    timeScale: { borderColor: '#262b38', timeVisible: cd.type === 'intraday', secondsVisible: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  });
  const candleSeries = chart.addCandlestickSeries({
    upColor: '#34c98c', downColor: '#ef6b6b', borderVisible: false,
    wickUpColor: '#34c98c', wickDownColor: '#ef6b6b',
  });
  candleSeries.setData(cd.candles);
  if (cd.markers && cd.markers.length) candleSeries.setMarkers(cd.markers);
  if (cd.sma20 && cd.sma20.length) {
    chart.addLineSeries({ color: '#5b8def', lineWidth: 2 }).setData(cd.sma20);
  }
  chart.timeScale().fitContent();
  if (cd.note) {
    const note = document.createElement('div');
    note.className = 'chart-note';
    note.textContent = cd.note;
    container.appendChild(note);
  }
}
"""

DETAIL_CSS = BASE_CSS + """
  body { padding: 24px 28px 50px; }
  a.back { color: var(--accent); text-decoration: none; font-size: 12.5px; }
  a.back:hover { text-decoration: underline; }
  h1 { font-size: 22px; margin: 14px 0 4px; }
  .dates { color: var(--muted); font-size: 13px; margin-bottom: 18px; }
  .verdicts { display: flex; gap: 8px; margin-bottom: 14px; }
  .block { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 14px; }
  .block h2 { margin: 0 0 8px; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  .block p { margin: 0; }
  .block.actionable { border-left: 3px solid var(--accent); }
  .block.actionable p { white-space: pre-wrap; }
  .context { color: var(--muted); font-style: italic; font-size: 12.5px; margin-top: 8px; }
  .tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
  .pnl-line { font-size: 15px; margin-bottom: 14px; }
  .chart-box { border: 1px solid var(--border); border-radius: 8px; padding: 10px; background: #12141c; margin-bottom: 8px; }
  .chart-note { color: var(--muted); font-size: 11.5px; font-style: italic; margin-top: 6px; }
  .chart-empty { color: var(--muted); font-size: 12.5px; padding: 16px; }
  .chart-pair-label { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 4px 0; }
  .chart-pair-label:first-child { margin-top: 0; }
"""


def render_detail_page(review: dict, chart_data: dict) -> str:
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in review["tags"])
    pnl_label = "Unrealized (last snapshot)" if review["exitDate"] is None else "Realized P&L"
    context_html = f'<div class="context">{review["marketContext"]}</div>' if review["marketContext"] else ""
    actionable_html = (
        f'<div class="block actionable"><h2>Actionable analysis '
        f'{actionable_badge_html(review.get("actionableVerdict"))}</h2><p>{review["actionableAnalysis"]}</p></div>'
        if review.get("actionableAnalysis") else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{review['underlying']} {review['entryDate']}</title>
{LIGHTWEIGHT_CHARTS_SCRIPT}
<style>{DETAIL_CSS}</style>
</head>
<body>
<a class="back" href="../trade_reviews.html">&larr; All reviews</a>
<h1>{review['underlying']} <span style="color:var(--muted); font-weight:400;">{review['symbol']}</span></h1>
<div class="dates">{review['entryDate']} &rarr; {review['exitDate'] or 'open'}</div>
<div class="pnl-line">{pnl_label}: {fmt_pnl(review['realizedPnl'])}</div>

<div class="verdicts">{direction_badge_html(review.get('direction'))} {badge_html(review['entryVerdict'])} {badge_html(review['exitVerdict'])}</div>

<div class="block">
  <h2>Entry</h2>
  <p>{review['entryReason'] or ''}</p>
</div>
<div class="block">
  <h2>Exit / Current status</h2>
  <p>{review['exitReason'] or ''}</p>
  {context_html}
  <div class="tags">{tags_html}</div>
</div>
{actionable_html}

<div class="chart-box" id="chart"></div>

<script>
const CHART_DATA = {json.dumps(chart_data)};
{CHART_JS}
renderChart(CHART_DATA, document.getElementById('chart'));
</script>
</body>
</html>
"""


# ── Index page ───────────────────────────────────────────────────────────────

INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Trade Reviews</title>
<style>
""" + BASE_CSS + """
  header {
    padding: 20px 28px 14px; border-bottom: 1px solid var(--border);
    position: sticky; top: 0; background: var(--bg); z-index: 5;
  }
  h1 { margin: 0 0 4px; font-size: 20px; }
  .sub { color: var(--muted); font-size: 12.5px; }
  .controls { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-top: 14px; }
  input[type=text], select {
    background: var(--panel); border: 1px solid var(--border); color: var(--text);
    border-radius: 7px; padding: 7px 10px; font-size: 13px;
  }
  input[type=text] { min-width: 220px; }
  .stat { color: var(--muted); font-size: 12.5px; margin-left: auto; }
  main { padding: 18px 28px 40px; }
  table { border-collapse: collapse; width: 100%; }
  thead th {
    text-align: left; font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em;
    color: var(--muted); padding: 8px 10px; border-bottom: 1px solid var(--border);
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--text); }
  tbody tr { border-bottom: 1px solid var(--border); vertical-align: top; cursor: pointer; }
  tbody tr:hover { background: rgba(255,255,255,0.03); }
  td { padding: 10px; font-size: 13px; }
  td.ticker { font-weight: 600; white-space: nowrap; }
  td.dates { white-space: nowrap; color: var(--muted); font-size: 12.5px; }
  td.pnl { white-space: nowrap; text-align: right; font-variant-numeric: tabular-nums; }
  .reason { color: var(--muted); font-size: 12.5px; max-width: 340px; }
  .tags { margin-top: 4px; display: flex; gap: 4px; flex-wrap: wrap; }
  .tag { cursor: pointer; }
  .tag:hover { border-color: var(--accent); }
  .tag.active { background: var(--accent); color: #0f1115; }
  .context { color: var(--muted); font-size: 12px; font-style: italic; }
  .empty { color: var(--muted); padding: 40px; text-align: center; }
</style>
</head>
<body>
<header>
  <h1>Trade Reviews</h1>
  <div class="sub">Entry/exit quality judged on facts at the time, not outcome. Click a row for its chart. Generated __GENERATED_AT__.</div>
  <div class="controls">
    <input type="text" id="search" placeholder="Search ticker, reason, tags…">
    <select id="direction"><option value="">Direction: all</option></select>
    <select id="entryVerdict"><option value="">Entry verdict: all</option></select>
    <select id="exitVerdict"><option value="">Exit verdict: all</option></select>
    <select id="actionableVerdict"><option value="">Fix: all</option></select>
    <span class="stat" id="stat"></span>
  </div>
</header>
<main>
  <table id="tbl">
    <thead>
      <tr>
        <th data-key="underlying">Ticker</th>
        <th data-key="direction">Dir</th>
        <th data-key="entryDate">Entry / Exit</th>
        <th data-key="entryVerdict">Entry</th>
        <th data-key="exitVerdict">Exit</th>
        <th data-key="actionableVerdict">Fix</th>
        <th data-key="realizedPnl">P&amp;L</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none">No reviews match.</div>
</main>

<script>
const DATA = __DATA_JSON__;
let sortKey = "entryDate", sortDir = 1, activeTag = null;

function badge(v) {
  if (!v) return '<span class="badge badge-n_a">—</span>';
  return `<span class="badge badge-${v}">${v.replace(/_/g,' ')}</span>`;
}
function directionBadge(v) {
  if (!v) return '<span class="badge badge-n_a">—</span>';
  const cls = v === 'LONG' ? 'badge-good' : v === 'SHORT' ? 'badge-bad' : 'badge-neutral';
  return `<span class="badge ${cls}">${v}</span>`;
}
function actionableBadge(v) {
  if (!v) return '<span class="badge badge-n_a">—</span>';
  const cls = v === 'Pass' ? 'badge-bad' : v === 'No Change' ? 'badge-good' : 'badge-neutral';
  return `<span class="badge ${cls}">${v}</span>`;
}
function fmtPnl(v) {
  if (v === null || v === undefined) return '';
  const cls = v >= 0 ? 'pnl-pos' : 'pnl-neg';
  const sign = v >= 0 ? '+' : '';
  return `<span class="${cls}">${sign}$${v.toFixed(2)}</span>`;
}
function populateFilters() {
  const ev = new Set(), xv = new Set(), dir = new Set(), av = new Set();
  DATA.forEach(r => { if (r.entryVerdict) ev.add(r.entryVerdict); if (r.exitVerdict) xv.add(r.exitVerdict); if (r.direction) dir.add(r.direction); if (r.actionableVerdict) av.add(r.actionableVerdict); });
  const fill = (sel, set) => { [...set].sort().forEach(v => {
    const o = document.createElement('option'); o.value = v; o.textContent = v.replace(/_/g,' '); sel.appendChild(o);
  }); };
  fill(document.getElementById('entryVerdict'), ev);
  fill(document.getElementById('exitVerdict'), xv);
  fill(document.getElementById('direction'), dir);
  fill(document.getElementById('actionableVerdict'), av);
}
function matches(r, q, ev, xv, dir, av, tag) {
  if (ev && r.entryVerdict !== ev) return false;
  if (xv && r.exitVerdict !== xv) return false;
  if (dir && r.direction !== dir) return false;
  if (av && r.actionableVerdict !== av) return false;
  if (tag && !r.tags.includes(tag)) return false;
  if (!q) return true;
  q = q.toLowerCase();
  const hay = [r.underlying, r.symbol, r.entryReason, r.exitReason, r.marketContext, r.direction, r.actionableVerdict, ...r.tags]
    .filter(Boolean).join(' ').toLowerCase();
  return hay.includes(q);
}
function render() {
  const q = document.getElementById('search').value.trim();
  const ev = document.getElementById('entryVerdict').value;
  const xv = document.getElementById('exitVerdict').value;
  const dir = document.getElementById('direction').value;
  const av = document.getElementById('actionableVerdict').value;
  let rows = DATA.filter(r => matches(r, q, ev, xv, dir, av, activeTag));
  rows.sort((a, b) => {
    let av = a[sortKey], bv = b[sortKey];
    if (av === null || av === undefined) av = '';
    if (bv === null || bv === undefined) bv = '';
    if (av < bv) return -1 * sortDir;
    if (av > bv) return 1 * sortDir;
    return 0;
  });
  const tbody = document.getElementById('rows');
  tbody.innerHTML = '';
  document.getElementById('empty').style.display = rows.length ? 'none' : 'block';
  document.getElementById('stat').textContent = `${rows.length} of ${DATA.length} reviews`;
  for (const r of rows) {
    const tr = document.createElement('tr');
    const tagsHtml = r.tags.map(t => `<span class="tag ${t === activeTag ? 'active' : ''}" data-tag="${t}">${t}</span>`).join('');
    tr.innerHTML = `
      <td class="ticker">${r.underlying}${r.symbol !== r.underlying ? `<div class="reason">${r.symbol}</div>` : ''}</td>
      <td>${directionBadge(r.direction)}</td>
      <td class="dates">${r.entryDate || ''} → ${r.exitDate || 'open'}</td>
      <td>${badge(r.entryVerdict)}<div class="reason">${r.entryReason || ''}</div></td>
      <td>${badge(r.exitVerdict)}<div class="reason">${r.exitReason || ''}</div>
          ${r.marketContext ? `<div class="context">${r.marketContext}</div>` : ''}
          <div class="tags">${tagsHtml}</div></td>
      <td>${actionableBadge(r.actionableVerdict)}</td>
      <td class="pnl">${fmtPnl(r.realizedPnl)}</td>
    `;
    tr.addEventListener('click', (e) => {
      if (e.target.closest('.tag')) return;
      window.location.href = 'trades/' + r.detailFile;
    });
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll('.tag').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const t = el.dataset.tag;
      activeTag = activeTag === t ? null : t;
      render();
    });
  });
}
document.querySelectorAll('thead th').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.key;
    if (sortKey === key) sortDir *= -1; else { sortKey = key; sortDir = 1; }
    render();
  });
});
document.getElementById('search').addEventListener('input', render);
document.getElementById('entryVerdict').addEventListener('change', render);
document.getElementById('exitVerdict').addEventListener('change', render);
document.getElementById('direction').addEventListener('change', render);
populateFilters();
render();
</script>
</body>
</html>
"""


async def _build_all(reviews: list[dict], no_charts: bool) -> None:
    conn = _get_conn()
    TRADES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if no_charts:
            for r in reviews:
                cd = {"type": "none", "candles": [], "sma20": [], "markers": [], "note": "Charts skipped (--no-charts)."}
                (TRADES_DIR / detail_filename(r)).write_text(render_detail_page(r, cd))
            return
        async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
            for i, r in enumerate(reviews, 1):
                try:
                    cd = await _build_chart_data(client, conn, r)
                except Exception as e:
                    cd = {"type": "error", "candles": [], "sma20": [], "markers": [],
                          "note": f"Chart build failed: {type(e).__name__}: {e}"}
                (TRADES_DIR / detail_filename(r)).write_text(render_detail_page(r, cd))
                if i % 50 == 0:
                    print(f"  ...{i}/{len(reviews)} detail pages written")
    finally:
        conn.close()


def _compute_directions(rows: list[dict]) -> None:
    """Adds 'direction' to each row in place: LONG/SHORT for single-instrument
    trades (from the actual opening fill's buy/sell, not stored anywhere else),
    or STRADDLE/CONDOR/SPREAD for systematic multi-leg structures, where a
    single LONG/SHORT label would misrepresent the position."""
    conid_list = sorted({r["_conid"] for r in rows if r.get("_conid") is not None})
    first_fill = {}
    if conid_list:
        conn = _get_conn()
        try:
            placeholders = ",".join(["%s"] * len(conid_list))
            df = pd.read_sql(
                f"""SELECT conid, trade_date, trade_datetime, buy_sell FROM journal_trades
                    WHERE conid IN ({placeholders}) AND open_close IN ('O', 'C;O')
                    ORDER BY conid, trade_date, trade_datetime""",
                conn, params=conid_list,
            )
        finally:
            conn.close()
        first_fill = df.groupby(["conid", "trade_date"])["buy_sell"].first().to_dict()

    for r in rows:
        tags = r.get("tags") or []
        if "straddle_screener" in tags:
            r["direction"] = "STRADDLE"
            continue
        if "iron_condor" in tags:
            r["direction"] = "CONDOR"
            continue
        if "systematic_spread_likely" in tags:
            r["direction"] = "SPREAD"
            continue
        conid, ed = r.get("_conid"), r.get("entryDate")
        bs = first_fill.get((conid, pd.Timestamp(ed).date())) if conid is not None and ed else None
        r["direction"] = "LONG" if bs == "BUY" else ("SHORT" if bs == "SELL" else None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-charts", action="store_true", help="skip Tradier entirely (fast, text-only detail pages)")
    a = ap.parse_args()

    df = get_trade_reviews()
    rows = [_row_to_json(r) for _, r in df.iterrows()]
    for r in rows:
        r["detailFile"] = detail_filename(r)
    _compute_directions(rows)

    print(f"Building {len(rows)} detail pages" + (" (--no-charts)" if a.no_charts else " (Tradier calls, cached per-symbol)") + "...")
    asyncio.run(_build_all(rows, a.no_charts))

    public_rows = [{k: v for k, v in r.items() if k != "_conid"} for r in rows]
    html = INDEX_TEMPLATE.replace("__DATA_JSON__", json.dumps(public_rows))
    html = html.replace("__GENERATED_AT__", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    INDEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    INDEX_OUT.write_text(html)
    print(f"Wrote {INDEX_OUT} (index) + {len(rows)} files in {TRADES_DIR}/")


if __name__ == "__main__":
    main()

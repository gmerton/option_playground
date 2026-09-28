#!/usr/bin/env python3
"""Martin Luk's trades from his livestreams, in the journal site's style: data/journal/luk/index.html + one page per
trade campaign. The parallel of run_tito_trade_pages.py (Gabe 2026-09-27: "a parallel journal ... for Martin, all known
trades, with the commentary he offered").

Source: data/martin_luk/trades/observed_trades.jsonl (one row per thing he said about a position: entry, hold, add,
trim, stop, exit ...) with Gabe's fixes from data/martin_luk/trades/clarify_worklist.csv applied (ticker_fixed,
direction_fixed, fill_date_fixed; ';' in ticker_fixed = several names; keep_or_drop = drop removes the row).

Rows are grouped into CAMPAIGNS: per (ticker, direction), an entry-type action (entry / buy / short / reentry) opens a
campaign, later rows attach to it, and stopped_out / exit / cover close it. Rows about a position with no logged entry
start a campaign of their own.

⚠ Charts are WITHHELD for any campaign that still has a row open on the clarification worklist: showing how a trade
played out would bias the remaining clarifications (the scoring test's rule is "resolve from the video only").
Retrospective rows (the 2026-01-31 review of hand-picked 2025 trades, month-level dates) are shown and labelled; they
are excluded from the pre-registered scoring test. Re-run after each worklist session.

  PYTHONPATH=src:. .venv/bin/python3 run_luk_trade_pages.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from run_trade_review_pages import BASE_CSS, DETAIL_CSS, LIGHTWEIGHT_CHARTS_SCRIPT

SRC = Path("data/martin_luk/trades")
OUT = Path("data/journal/luk")
# decodes Gabe confirmed on one row apply to every row with the same garble
ALIAS = {"AOI": "AAOI", "UMY": "UAMY"}
OPENERS = {"entry", "buy", "short", "reentry"}
CLOSERS = {"stopped_out", "exit", "cover"}
e = html.escape


def yt(src: str) -> str | None:
    m = re.match(r"(\d{4}-\d\d-\d\d)_([A-Za-z0-9_-]{11})@(\d+):(\d+)", str(src))
    return f"https://youtu.be/{m[2]}?t={int(m[3]) * 60 + int(m[4])}" if m else None


def load() -> pd.DataFrame:
    d = pd.DataFrame([json.loads(l) for l in open(SRC / "observed_trades.jsonl") if l.strip()])
    d["line_no"] = np.arange(1, len(d) + 1)
    W = pd.read_csv(SRC / "clarify_worklist.csv", dtype=str)
    W["line_no"] = W.line_no.astype(int)
    d = d.merge(W[["line_no", "ticker_fixed", "direction_fixed", "fill_date_fixed", "keep_or_drop", "your_note", "issue"]],
                on="line_no", how="left")
    kd = d.keep_or_drop.fillna("")
    d["state"] = np.where(d.issue.notna() & (kd == ""), "pending",
                          np.where(kd.str.contains("retrospective"), "retrospective",
                                   np.where(kd.str.startswith("drop"), "dropped", "ok")))
    d["tk"] = d.ticker_fixed.fillna(d.ticker.replace(ALIAS)).astype(str)
    d["dirn"] = d.direction_fixed.fillna(d.direction)
    d["fill"] = pd.to_datetime(d.fill_date_fixed.fillna(d.fill_date), errors="coerce")
    d["vid"] = pd.to_datetime(d.source.astype(str).str[:10], errors="coerce")
    d["when"] = d.fill.fillna(pd.to_datetime(d.date, errors="coerce"))
    rows = []
    for r in d.to_dict("records"):                                   # expand multi-ticker fixes
        for t in str(r["tk"]).split(";"):
            rows.append({**r, "tk": t.strip()})
    d = pd.DataFrame(rows)
    return d[d.state != "dropped"].sort_values(["when", "vid", "line_no"]).reset_index(drop=True)


def campaigns(d: pd.DataFrame) -> list[dict]:
    out, open_ = [], {}
    for r in d.to_dict("records"):
        key = (r["tk"], r["dirn"])
        act = str(r["action"])
        if act in OPENERS or key not in open_:
            if key in open_ and act in OPENERS and act == "reentry":
                pass
            c = dict(tk=r["tk"], dirn=r["dirn"], rows=[])
            out.append(c); open_[key] = c
        open_[key]["rows"].append(r)
        if act in CLOSERS:
            open_.pop(key, None)
    for n, c in enumerate(out, 1):
        R = c["rows"]
        c["n"] = n
        c["start"] = min(x["when"] for x in R if pd.notna(x["when"]))
        c["end"] = max(x["when"] for x in R if pd.notna(x["when"]))
        states = {x["state"] for x in R}
        c["state"] = "pending" if "pending" in states else ("retrospective" if "retrospective" in states else "ok")
        acts = [str(x["action"]) for x in R]
        c["ended"] = next((a for a in reversed(acts) if a in CLOSERS), None) or ("trimmed / open" if {"trim", "sell"} & set(acts) else "open / not reported")
        c["has_entry"] = any(a in OPENERS for a in acts)
        c["resolved_tk"] = c["tk"] not in ("?", "", "nan") and "/" not in c["tk"] and " " not in c["tk"]
        c["slug"] = f"{n:03d}_{re.sub(r'[^A-Za-z0-9]', '', c['tk']) or 'UNK'}"
    return out


def chart_data(c: dict, H: dict) -> dict:
    empty = {"candles": [], "ema9": [], "ema21": [], "markers": [], "volume": []}
    if c["state"] == "pending" or not c["resolved_tk"] or c["tk"] not in H:
        return empty
    h = H[c["tk"]]
    lo, hi = c["start"] - pd.Timedelta(days=60), c["end"] + pd.Timedelta(days=25)
    w = h[(h.index >= lo) & (h.index <= hi)]
    if w.empty:
        return empty
    full = h[h.index <= hi]
    e9, e21 = full.Close.ewm(span=9, adjust=False).mean(), full.Close.ewm(span=21, adjust=False).mean()
    ts = lambda i: i.strftime("%Y-%m-%d")
    cand = [{"time": ts(i), "open": round(float(r.Open), 4), "high": round(float(r.High), 4), "low": round(float(r.Low), 4),
             "close": round(float(r.Close), 4)} for i, r in w.iterrows()]
    vol = [{"time": ts(i), "value": float(r.Volume), "color": "#b8e0cb" if r.Close >= r.Open else "#f0c4c4"} for i, r in w.iterrows()]
    idx = w.index
    mk = []
    for x in c["rows"]:
        if pd.isna(x["when"]):
            continue
        k = idx.searchsorted(x["when"])
        if k >= len(idx):
            continue
        a = str(x["action"]); short = c["dirn"] == "short"
        if a in OPENERS or a == "add":
            m = dict(position="belowBar" if not short else "aboveBar", color="#157a4d" if not short else "#c23b3b",
                     shape="arrowUp" if not short else "arrowDown", text=a)
        elif a in CLOSERS:
            m = dict(position="aboveBar" if not short else "belowBar", color="#5b6272", shape="arrowDown" if not short else "arrowUp", text=a)
        elif a in ("trim", "sell"):
            m = dict(position="aboveBar", color="#e08a1e", shape="circle", text=a)
        else:
            m = dict(position="aboveBar", color="#9aa3b2", shape="circle", text=a)
        mk.append({"time": ts(idx[k]), **m})
    mk.sort(key=lambda z: z["time"])
    return {"candles": cand, "volume": vol, "markers": mk,
            "ema9": [{"time": ts(i), "value": round(float(v), 4)} for i, v in e9.items() if i >= w.index[0]],
            "ema21": [{"time": ts(i), "value": round(float(v), 4)} for i, v in e21.items() if i >= w.index[0]]}


PAGE_JS = """
function mk(container, h) {
  return LightweightCharts.createChart(container, {
    width: container.clientWidth || 860, height: h,
    layout: { background: { color: '#ffffff' }, textColor: '#6b7280' },
    grid: { vertLines: { color: '#e1e4ea' }, horzLines: { color: '#e1e4ea' } },
    rightPriceScale: { borderColor: '#e1e4ea' }, timeScale: { borderColor: '#e1e4ea' },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal } });
}
function render(u, why) {
  const c1 = document.getElementById('und');
  if (!u.candles.length) { c1.innerHTML = '<div class="chart-empty">' + why + '</div>'; return; }
  const ch = mk(c1, 380);
  const cs = ch.addCandlestickSeries({ upColor: '#157a4d', downColor: '#c23b3b', borderVisible: false, wickUpColor: '#157a4d', wickDownColor: '#c23b3b' });
  cs.setData(u.candles); if (u.markers.length) cs.setMarkers(u.markers);
  const vs = ch.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'vol', lastValueVisible: false, priceLineVisible: false });
  vs.setData(u.volume); ch.priceScale('vol').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
  cs.priceScale().applyOptions({ scaleMargins: { top: 0.06, bottom: 0.26 } });
  ch.addLineSeries({ color: '#3f6fd8', lineWidth: 2, title: '9 EMA' }).setData(u.ema9);
  ch.addLineSeries({ color: '#e08a1e', lineWidth: 2, title: '21 EMA' }).setData(u.ema21);
  ch.timeScale().fitContent();
}
"""

STATE_TXT = {"pending": "⏳ pending clarification: chart withheld until the worklist rows are resolved",
             "retrospective": "↩ retrospective: he reviewed this trade after the fact (outcome known when chosen); dates may be approximate",
             "ok": ""}


def trade_page(c: dict, u: dict) -> str:
    why = ("Chart withheld: this campaign still has a row on the clarification worklist." if c["state"] == "pending"
           else "No daily history for this symbol (unresolved ticker or not on yfinance).")
    tl = []
    for x in c["rows"]:
        link = yt(x["source"])
        src = f'<a href="{link}" target="_blank">{e(str(x["source"])[:10])} @{e(str(x["source"]).split("@")[-1])}</a>' if link else e(str(x["source"]))
        fill = x["fill"].date().isoformat() if pd.notna(x["fill"]) else "—"
        bits = [f"<b>{e(str(x['action']))}</b> &middot; fill {fill} &middot; {src} &middot; <span class='muted'>{e(str(x['confidence']))}</span>"
                + (f" &middot; <span class='warn'>{e(x['state'])}</span>" if x["state"] != "ok" else "")]
        for lab, key in (("Setup", "setup"), ("Entry basis", "entry_basis"), ("Stop", "stop"), ("Notes", "notes"), ("Clarified", "your_note")):
            v = x.get(key)
            if isinstance(v, str) and v.strip() and v != "nan":
                bits.append(f"<div><span class='lab'>{lab}.</span> {e(v)}</div>")
        tl.append("<li>" + "".join(bits) + "</li>")
    head = f"{e(c['tk'])} {c['dirn']}"
    return f"""<meta charset="utf-8">
<title>Luk #{c['n']} {head}</title>
<style>{DETAIL_CSS}
 ul.tl {{ list-style: none; padding: 0; margin: 0; }} ul.tl li {{ border-left: 3px solid var(--border); padding: 6px 0 10px 12px; margin-bottom: 6px; font-size: 13px; }}
 .lab {{ color: var(--muted); }} .muted {{ color: var(--muted); }} .warn {{ color: #b26b00; font-weight: 600; }} #und {{ width: 100%; }}
</style>
{LIGHTWEIGHT_CHARTS_SCRIPT}
<a class="back" href="index.html">&larr; Martin Luk's trades</a>
<h1>#{c['n']} {head}</h1>
<div class="dates">{c['start'].date()} &rarr; {c['end'].date()} &middot; {len(c['rows'])} updates &middot; ended: {e(c['ended'])}{('<br><span class="warn">' + STATE_TXT[c['state']] + '</span>') if STATE_TXT[c['state']] else ''}</div>
<div class="block"><h2>Daily chart</h2><div class="chart-box"><div id="und"></div></div>
<div class="chart-note">Blue = 9 EMA, orange = 21 EMA. Green arrow = entry / add (red, pointing down, for shorts), amber dot = trim / sell,
grey arrow = exit / stop-out, grey dot = a mention (hold, stop change). Markers sit on the FILL date where he gave one, else the stream date.
Daily bars only: his intraday fills are not visible.</div></div>
<div class="block commentary"><h2>What he said, in order</h2><ul class="tl">{''.join(tl)}</ul>
<div class="chart-note">Commentary is from auto-captions of his livestreams (tickers often garbled; see the clarification notes). Timestamps link to the video.</div></div>
<script>{PAGE_JS}
render({json.dumps(u)}, {json.dumps(why)});</script>
"""


def index_page(cs: list[dict], d: pd.DataFrame) -> str:
    n_pend = sum(c["state"] == "pending" for c in cs); n_retro = sum(c["state"] == "retrospective" for c in cs)
    rows = []
    for c in sorted(cs, key=lambda z: z["start"], reverse=True):
        badge = {"pending": "<span class='warn'>pending</span>", "retrospective": "<span class='muted'>retro</span>", "ok": ""}[c["state"]]
        first = c["rows"][0]
        setup = str(first.get("setup") or "")[:90]
        rows.append(f"<tr onclick=\"location.href='{c['slug']}.html'\"><td>{c['n']}</td><td><b>{e(c['tk'])}</b></td><td>{c['dirn']}</td>"
                    f"<td>{c['start'].date()}</td><td>{c['end'].date()}</td><td class='num'>{len(c['rows'])}</td><td>{e(c['ended'])}</td>"
                    f"<td>{badge}</td><td class='setup'>{e(setup)}</td></tr>")
    return f"""<meta charset="utf-8">
<title>Martin Luk's Trades</title>
<style>{BASE_CSS}
 body {{ padding: 24px 28px 50px; }} h1 {{ font-size: 22px; margin: 10px 0 4px; }} .sub {{ color: var(--muted); font-size: 12.5px; margin-bottom: 16px; max-width: 1000px; }}
 a.back {{ color: var(--accent); text-decoration: none; font-size: 12.5px; }} .warn {{ color: #b26b00; font-weight: 600; }} .muted {{ color: var(--muted); }}
 .wrap {{ overflow-x: auto; }} table {{ border-collapse: collapse; width: 100%; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; font-size: 12.5px; }}
 th, td {{ padding: 7px 10px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }} th {{ color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; }}
 td.setup {{ white-space: normal; min-width: 280px; color: var(--muted); }} td.num, th.num {{ text-align: right; }} tr:hover td {{ background: #f2f5fb; cursor: pointer; }}
</style>
<a class="back" href="../index.html">&larr; Home</a> &middot; <a class="back" href="../tito/index.html">Tito's best trades</a> &middot; <a class="back" href="../trade_reviews.html">Trade journal</a>
<h1>Martin Luk: trades from his livestreams</h1>
<div class="sub">Every position he mentioned on stream ({len(d)} logged updates from {d.vid.min().date()} to {d.vid.max().date()}), grouped into
{len(cs)} campaigns: entry, holds, adds, trims and exits, with what he said and a link to the moment in the video. Newest first.
<br><b>{n_pend}</b> campaigns are <span class="warn">pending</span> clarification (garbled ticker, vague date or unconfirmed entry): their charts are withheld until
resolved, so the outcome can't bias the clarification. <b>{n_retro}</b> are <span class="muted">retrospective</span> (reviewed after the fact, outcome known).
<br>Unlike Tito's list this is NOT curated: it's everything he disclosed, winners and losers. It's still his account of his trades, not audited fills,
and it isn't evidence for our setup selection; the admissible comparison is the pre-registered picks-vs-controls test (TEST_INDEX section 10).</div>
<div class="wrap"><table><tr><th>#</th><th>Ticker</th><th>Side</th><th>First</th><th>Last</th><th class="num">Updates</th><th>Ended</th><th></th><th>Setup (first mention)</th></tr>
{''.join(rows)}</table></div>
"""


def main() -> int:
    d = load(); cs = campaigns(d); OUT.mkdir(parents=True, exist_ok=True)
    tks = sorted({c["tk"] for c in cs if c["resolved_tk"] and c["state"] != "pending"})
    H = {}
    px = yf.download(tks, start="2024-10-01", auto_adjust=False, progress=False, group_by="ticker", threads=True)
    for t in tks:
        try:
            h = px[t].dropna(subset=["Close"]) if len(tks) > 1 else px.dropna(subset=["Close"])
            if len(h):
                H[t] = h
        except KeyError:
            pass
    for c in cs:
        (OUT / f"{c['slug']}.html").write_text(trade_page(c, chart_data(c, H)))
    (OUT / "index.html").write_text(index_page(cs, d))
    print(f"wrote {OUT}/index.html + {len(cs)} campaign pages | pending {sum(c['state'] == 'pending' for c in cs)}, "
          f"retrospective {sum(c['state'] == 'retrospective' for c in cs)}, charted {sum(c['tk'] in H and c['state'] != 'pending' for c in cs)}, "
          f"no price data for: {sorted(set(tks) - set(H))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

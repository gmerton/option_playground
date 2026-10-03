#!/usr/bin/env python3
"""Ariel Hernandez's trades from his daily recap videos, in the journal site's style: data/journal/ariel/index.html +
one page per trade campaign. The parallel of run_luk_trade_pages.py and run_tito_trade_pages.py (Gabe 2026-10-02:
"let's start by creating pages for Ariel similar to what we have for Tito and Martin").

Sources:
  data/ariel_hernandez/trades/observed_trades.jsonl  one row per thing he said about a position (decodes applied)
  data/ariel_hernandez/trades/broker_trades.csv      P&L per trade from his on-screen monthly recap slides
Rows are grouped into CAMPAIGNS exactly as for Luk: per (ticker, direction), an entry / short / reentry opens a
campaign, later rows attach, and stopped_out / exit / cover close it.

Per opening row the page shows WHERE THE FILL COULD HAVE BEEN, in ADR units from the 20 EMA: the fill day's low,
high, open and close as (price - EMA20[t-1]) / (ADR%[t-1] x close[t-1]), and the exact figure where he stated a fill
price. Daily bars (yfinance, unadjusted -- his stated prices are unadjusted too); intraday fills are not visible.

Retrospective rows (is_retrospective: he chose to talk about it after the outcome was known) are shown and labelled.
His recaps are his own account, not audited fills, and are not evidence for our setup selection.

  PYTHONPATH=src:. .venv/bin/python3 run_ariel_trade_pages.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from run_luk_trade_pages import PAGE_JS as _LUK_JS, ext, ext_html, yt
from run_trade_review_pages import BASE_CSS, DETAIL_CSS, LIGHTWEIGHT_CHARTS_SCRIPT

SRC = Path("data/ariel_hernandez/trades")
OUT = Path("data/journal/ariel")
OPENERS = {"entry", "short", "reentry"}
CLOSERS = {"stopped_out", "exit", "cover"}
e = html.escape

PAGE_JS = (_LUK_JS.replace("title: '9 EMA'", "title: '10 EMA'").replace("u.ema9)", "u.ema10)")
           .replace("title: '21 EMA'", "title: '20 EMA'").replace("u.ema21)", "u.ema20)")
           .replace("  ch.timeScale().fitContent();\n}",
                    "  ch.addLineSeries({ color: '#7a4fc9', lineWidth: 1, title: '50 SMA' }).setData(u.sma50);\n"
                    "  ch.timeScale().fitContent();\n}"))


def load() -> pd.DataFrame:
    d = pd.DataFrame([json.loads(l) for l in open(SRC / "observed_trades.jsonl") if l.strip()])
    d["line_no"] = np.arange(1, len(d) + 1)
    d["tk"] = d.ticker.astype(str).str.strip()
    d["dirn"] = d.direction.astype(str)
    d["fill"] = pd.to_datetime(d.fill_date.replace("", None), errors="coerce")
    d["vid"] = pd.to_datetime(d.source.astype(str).str[:10], errors="coerce")
    d["when"] = d.fill.fillna(pd.to_datetime(d.date, errors="coerce"))
    d["retro"] = d.is_retrospective.fillna(False).astype(bool)
    return d.sort_values(["when", "vid", "line_no"]).reset_index(drop=True)


def campaigns(d: pd.DataFrame) -> list[dict]:
    out, open_ = [], {}
    for r in d.to_dict("records"):
        key = (r["tk"], r["dirn"]); act = str(r["action"])
        if act in OPENERS or key not in open_:
            c = dict(tk=r["tk"], dirn=r["dirn"], rows=[]); out.append(c); open_[key] = c
        open_[key]["rows"].append(r)
        if act in CLOSERS:
            open_.pop(key, None)
    for n, c in enumerate(out, 1):
        R = c["rows"]; c["n"] = n
        ws = [x["when"] for x in R if pd.notna(x["when"])]
        c["start"], c["end"] = (min(ws), max(ws)) if ws else (pd.NaT, pd.NaT)
        c["retro"] = all(x["retro"] for x in R)
        acts = [str(x["action"]) for x in R]
        c["ended"] = next((a for a in reversed(acts) if a in CLOSERS), None) or ("trimmed / open" if "trim" in acts else "open / not reported")
        c["resolved_tk"] = bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,6}", c["tk"])) and c["tk"] not in ("NQ", "ES")
        c["slug"] = f"{n:04d}_{re.sub(r'[^A-Za-z0-9]', '', c['tk']) or 'UNK'}"
        c["broker"] = []
    return [c for c in out if pd.notna(c["start"])]


def attach_broker(cs: list[dict]) -> int:
    b = pd.read_csv(SRC / "broker_trades.csv")
    b["open_date"] = pd.to_datetime(b.open_date, errors="coerce")
    hit = 0
    for r in b.dropna(subset=["open_date"]).to_dict("records"):
        best = None
        for c in cs:
            if c["tk"] != str(r["symbol"]).strip():
                continue
            if isinstance(r.get("direction"), str) and r["direction"] in ("long", "short") and r["direction"] != c["dirn"]:
                continue
            gap = abs((c["start"] - r["open_date"]).days)
            if gap <= 3 and (best is None or gap < best[0]):
                best = (gap, c)
        if best:
            best[1]["broker"].append(r); hit += 1
    return hit


def chart_data(c: dict, H: dict) -> dict:
    empty = {"candles": [], "ema10": [], "ema20": [], "sma50": [], "markers": [], "volume": []}
    if not c["resolved_tk"] or c["tk"] not in H:
        return empty
    h = H[c["tk"]]
    lo, hi = c["start"] - pd.Timedelta(days=60), c["end"] + pd.Timedelta(days=25)
    w = h[(h.index >= lo) & (h.index <= hi)]
    if w.empty:
        return empty
    full = h[h.index <= hi]
    ts = lambda i: i.strftime("%Y-%m-%d")
    line = lambda s: [{"time": ts(i), "value": round(float(v), 4)} for i, v in s.items() if i >= w.index[0] and np.isfinite(v)]
    mk = []
    for x in c["rows"]:
        if pd.isna(x["when"]):
            continue
        k = w.index.searchsorted(x["when"])
        if k >= len(w):
            continue
        a = str(x["action"]); short = c["dirn"] == "short"
        px = f" @{x['price']:g}" if x.get("price_kind") == "fill" and isinstance(x.get("price"), (int, float)) and np.isfinite(x["price"]) else ""
        if a in OPENERS or a == "add":
            m = dict(position="aboveBar" if short else "belowBar", color="#c23b3b" if short else "#157a4d",
                     shape="arrowDown" if short else "arrowUp", text=a + px)
        elif a in CLOSERS:
            m = dict(position="belowBar" if short else "aboveBar", color="#5b6272", shape="arrowUp" if short else "arrowDown", text=a + px)
        elif a == "trim":
            m = dict(position="aboveBar", color="#e08a1e", shape="circle", text=a + px)
        else:
            m = dict(position="aboveBar", color="#9aa3b2", shape="circle", text=a)
        mk.append({"time": ts(w.index[k]), **m})
    mk.sort(key=lambda z: z["time"])
    return {"candles": [{"time": ts(i), "open": round(float(r.Open), 4), "high": round(float(r.High), 4), "low": round(float(r.Low), 4),
                         "close": round(float(r.Close), 4)} for i, r in w.iterrows()],
            "volume": [{"time": ts(i), "value": float(r.Volume), "color": "#b8e0cb" if r.Close >= r.Open else "#f0c4c4"} for i, r in w.iterrows()],
            "markers": mk, "ema10": line(full.Close.ewm(span=10, adjust=False).mean()),
            "ema20": line(full.Close.ewm(span=20, adjust=False).mean()), "sma50": line(full.Close.rolling(50).mean())}


def money(v) -> str:
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else ("-" if v < 0 else "+") + f"${abs(v):,.0f}"


def trade_page(c: dict, u: dict, H: dict) -> str:
    why = "No daily history for this symbol (unresolved ticker, futures, or not on yfinance)."
    tl = []
    for x in c["rows"]:
        link = yt(x["source"])
        src = f'<a href="{link}" target="_blank">{e(str(x["source"])[:10])} @{e(str(x["source"]).split("@")[-1])}</a>' if link else e(str(x["source"]))
        fill = x["fill"].date().isoformat() if pd.notna(x["fill"]) else "—"
        bits = [f"<b>{e(str(x['action']))}</b> &middot; fill {fill} &middot; {src} &middot; <span class='muted'>{e(str(x['confidence']))}</span>"
                + (" &middot; <span class='muted'>retrospective</span>" if x["retro"] else "")]
        if isinstance(x.get("price"), (int, float)) and np.isfinite(x["price"]):
            bits.append(f"<div><span class='lab'>Price.</span> {x['price']:g} ({e(str(x.get('price_kind') or ''))})</div>")
        for lab, key in (("Vehicle", "vehicle"), ("Setup", "setup"), ("Entry basis", "entry_basis"), ("Stop", "stop"), ("Size", "size"),
                         ("Quote", "quote"), ("Notes", "notes")):
            v = x.get(key)
            if isinstance(v, str) and v.strip() and v != "nan":
                bits.append(f"<div><span class='lab'>{lab}.</span> {'&ldquo;' + e(v) + '&rdquo;' if key == 'quote' else e(v)}</div>")
        if str(x["action"]) in OPENERS | {"add"} and c["tk"] in H and pd.notna(x["fill"]):
            p = x["price"] if x.get("price_kind") == "fill" and isinstance(x.get("price"), (int, float)) else None
            bits.append(ext_html(ext(H[c["tk"]], x["fill"], p), c["dirn"]))
        tl.append("<li>" + "".join(bits) + "</li>")
    brk = ""
    if c["broker"]:
        rows = "".join(f"<tr><td>{pd.Timestamp(r['open_date']).date()}</td><td>{e(str(r['status']))}</td><td class='num'>{money(r['pnl_usd'])}</td>"
                       f"<td class='num'>{'' if pd.isna(r['pnl_pct']) else f'{r['pnl_pct']:+.2f}%'}</td><td>{e(str(r['note']) if isinstance(r['note'], str) else '')}</td></tr>"
                       for r in c["broker"])
        brk = (f"<div class='block'><h2>Broker P&amp;L (his on-screen monthly recap)</h2><table class='facts'><tr><th>Opened</th><th>Status</th>"
               f"<th class='num'>P&amp;L</th><th class='num'>%</th><th>Note</th></tr>{rows}</table>"
               "<div class='chart-note'>Matched on ticker, side and an open date within 3 days of this campaign's first row.</div></div>")
    head = f"{e(c['tk'])} {c['dirn']}"
    return f"""<meta charset="utf-8">
<title>Ariel #{c['n']} {head}</title>
<style>{DETAIL_CSS}
 ul.tl {{ list-style: none; padding: 0; margin: 0; }} ul.tl li {{ border-left: 3px solid var(--border); padding: 6px 0 10px 12px; margin-bottom: 6px; font-size: 13px; }}
 .lab {{ color: var(--muted); }} .muted {{ color: var(--muted); }} .warn {{ color: #b26b00; font-weight: 600; }} #und {{ width: 100%; }}
 .ext {{ margin-top: 4px; padding: 4px 8px; background: #f2f5fb; border-radius: 6px; display: inline-block; }}
 table.facts {{ border-collapse: collapse; width: 100%; font-size: 13px; }} table.facts th, table.facts td {{ text-align: left; padding: 5px 10px 5px 0; }}
 table.facts th {{ color: var(--muted); font-weight: 500; }} .num {{ text-align: right; }}
</style>
{LIGHTWEIGHT_CHARTS_SCRIPT}
<a class="back" href="index.html">&larr; Ariel Hernandez's trades</a>
<h1>#{c['n']} {head}</h1>
<div class="dates">{c['start'].date()} &rarr; {c['end'].date()} &middot; {len(c['rows'])} updates &middot; ended: {e(c['ended'])}{'<br><span class="muted">↩ retrospective: he discussed this trade after the outcome was known</span>' if c['retro'] else ''}</div>
{brk}
<div class="block"><h2>Daily chart</h2><div class="chart-box"><div id="und"></div></div>
<div class="chart-note">Blue = 10 EMA, orange = 20 EMA, purple = 50 SMA. Green arrow = entry / add (red, pointing down, for shorts), amber dot = trim,
grey arrow = exit / stop-out / cover, grey dot = a mention (hold). Markers sit on the FILL date where one is known, else the video date; "@price" = a fill price he stated.
Daily bars only: his intraday fills are not visible.</div></div>
<div class="block commentary"><h2>What he said, in order</h2><ul class="tl">{''.join(tl)}</ul>
<div class="chart-note">From auto-captions of his recap videos (decodes confirmed by Gabe applied). "Fill-day range vs 20 EMA" = where on that day's bar a fill could have been:
(price &minus; prior day's 20 EMA) &divide; (20-day ADR in dollars). Positive = above the EMA.</div></div>
<script>{PAGE_JS}
render({json.dumps(u)}, {json.dumps(why)});</script>
"""


def index_page(cs: list[dict], d: pd.DataFrame, n_broker: int) -> str:
    rows = []
    for c in sorted(cs, key=lambda z: z["start"], reverse=True):
        pnl = sum(float(r["pnl_usd"]) for r in c["broker"] if pd.notna(r["pnl_usd"])) if c["broker"] else None
        x0 = c.get("ext0")
        rng = f"{x0['low']:+.1f} … {x0['high']:+.1f}" if x0 else "—"
        setup = str(c["rows"][0].get("setup") or "")[:90]
        rows.append(f"<tr onclick=\"location.href='{c['slug']}.html'\"><td>{c['n']}</td><td><b>{e(c['tk'])}</b></td><td>{c['dirn']}</td>"
                    f"<td>{c['start'].date()}</td><td>{c['end'].date()}</td><td class='num'>{len(c['rows'])}</td><td>{e(c['ended'])}</td>"
                    f"<td class='num'>{rng}</td><td class='num'>{money(pnl) if pnl is not None else ''}</td>"
                    f"<td>{'<span class=muted>retro</span>' if c['retro'] else ''}</td><td class='setup'>{e(setup)}</td></tr>")
    return f"""<meta charset="utf-8">
<title>Ariel Hernandez's Trades</title>
<style>{BASE_CSS}
 body {{ padding: 24px 28px 50px; }} h1 {{ font-size: 22px; margin: 10px 0 4px; }} .sub {{ color: var(--muted); font-size: 12.5px; margin-bottom: 16px; max-width: 1000px; }}
 a.back {{ color: var(--accent); text-decoration: none; font-size: 12.5px; }} .muted {{ color: var(--muted); }}
 .wrap {{ overflow-x: auto; }} table {{ border-collapse: collapse; width: 100%; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; font-size: 12.5px; }}
 th, td {{ padding: 7px 10px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }} th {{ color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; }}
 td.setup {{ white-space: normal; min-width: 280px; color: var(--muted); }} td.num, th.num {{ text-align: right; }} tr:hover td {{ background: #f2f5fb; cursor: pointer; }}
</style>
<a class="back" href="../index.html">&larr; Home</a> &middot; <a class="back" href="../luk/index.html">Martin Luk's trades</a> &middot; <a class="back" href="../tito/index.html">Tito's best trades</a>
<h1>Ariel Hernandez: trades from his daily recaps</h1>
<div class="sub">Every position he mentioned ({len(d)} logged updates from {d.vid.min().date()} to {d.vid.max().date()}), grouped into {len(cs)} campaigns,
with what he said and a link to the moment in the video. Newest first. <b>Entry range</b> = the first opening day's low &hellip; high in ADR from the prior day's 20 EMA:
his fill was somewhere in there (exact where he stated a price, on the page). <b>Broker P&amp;L</b> = from his on-screen monthly recap slides ({n_broker} trades matched).
<br>Not curated, but it's his own account, not audited fills; <span class="muted">retro</span> = discussed after the outcome was known. Not evidence for our setup selection.</div>
<div class="wrap"><table><tr><th>#</th><th>Ticker</th><th>Side</th><th>First</th><th>Last</th><th class="num">Updates</th><th>Ended</th>
<th class="num">Entry range (ADR vs 20 EMA)</th><th class="num">Broker P&amp;L</th><th></th><th>Setup (first mention)</th></tr>
{''.join(rows)}</table></div>
"""


def main() -> int:
    d = load(); cs = campaigns(d); n_broker = attach_broker(cs); OUT.mkdir(parents=True, exist_ok=True)
    tks = sorted({c["tk"] for c in cs if c["resolved_tk"]})
    px = yf.download(tks, start="2024-10-01", auto_adjust=False, progress=False, group_by="ticker", threads=True)
    H = {}
    for t in tks:
        try:
            h = px[t].dropna(subset=["Close"])
            if len(h):
                H[t] = h
        except KeyError:
            pass
    stats = []
    for c in cs:
        first = next((x for x in c["rows"] if str(x["action"]) in OPENERS and pd.notna(x["fill"])), None)
        if first is not None and c["tk"] in H:
            p = first["price"] if first.get("price_kind") == "fill" and isinstance(first.get("price"), (int, float)) else None
            c["ext0"] = ext(H[c["tk"]], first["fill"], p)
            if c["ext0"]:
                stats.append({**c["ext0"], "dirn": c["dirn"], "retro": c["retro"], "tk": c["tk"]})
        (OUT / f"{c['slug']}.html").write_text(trade_page(c, chart_data(c, H), H))
    (OUT / "index.html").write_text(index_page(cs, d, n_broker))
    # drop pages from earlier runs whose numbering no longer exists (2026-10-03: 205 Luk orphans were deployed by the sync)
    keep = {f"{c['slug']}.html" for c in cs} | {"index.html"}
    stale = [f for f in OUT.glob("*.html") if f.name not in keep]
    for f in stale:
        f.unlink()
    S = pd.DataFrame(stats); S.to_csv("data/studies/ariel_entry_ext_2026-10-02.csv", index=False)
    print(f"wrote {OUT}/index.html + {len(cs)} campaign pages, removed {len(stale)} stale | charted {sum(c['tk'] in H for c in cs)}, broker-matched {n_broker}, "
          f"entry ranges {len(S)}, no price data for {len(set(tks) - set(H))}: {sorted(set(tks) - set(H))[:30]}")
    if len(S):
        st = S.dropna(subset=["stated"]) if "stated" in S else S.iloc[:0]
        print(f"stated fills: {len(st)}, inside the day's range {st.stated_in_range.mean():.0%}" if len(st) else "no stated fills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

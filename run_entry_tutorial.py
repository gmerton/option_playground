#!/usr/bin/env python3
"""Flip-book entry tutorial for the journal site: one card per entry, front = the setup exactly as it looked at the
fill (daily chart to the prior close, 5-min chart to the entry bar, the facts the rubric uses), back = verdict, why,
what happened, the rule. Answers are kept in the browser's localStorage and scored at the end.

  PYTHONPATH=src:. .venv/bin/python3 run_entry_tutorial.py            # QCOM Aug 31 - Sep 11 (default content)
Content (authored): data/studies/tutorials/qcom_2026-09.json. Bars/facts cache: data/cache/tutorial_qcom/.
"""
from __future__ import annotations

import argparse, calendar, html, json
from pathlib import Path

import pandas as pd

from run_trade_review_pages import BASE_CSS, LIGHTWEIGHT_CHARTS_SCRIPT


def epoch(ts: pd.Timestamp) -> int:
    return calendar.timegm(ts.to_pydatetime().timetuple())      # naive ET shown as UTC (the journal's convention)


def candles(df: pd.DataFrame, intraday: bool) -> list[dict]:
    return [{"time": epoch(t) if intraday else t.strftime("%Y-%m-%d"), "open": round(float(r.open), 2), "high": round(float(r.high), 2),
             "low": round(float(r.low), 2), "close": round(float(r.close), 2)} for t, r in df.iterrows()]


def line(s: pd.Series, intraday: bool) -> list[dict]:
    return [{"time": epoch(t) if intraday else t.strftime("%Y-%m-%d"), "value": round(float(v), 2)} for t, v in s.items() if pd.notna(v)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default="data/studies/tutorials/qcom_2026-09.json")
    ap.add_argument("--cache", default="data/cache/tutorial_qcom")
    ap.add_argument("--out", default="data/journal/tutorial/qcom/index.html")
    a = ap.parse_args()
    C = json.loads(Path(a.content).read_text()); cache = Path(a.cache)
    daily = pd.read_csv(cache / "qcom_tut_daily.csv", index_col=0, parse_dates=True)
    daily["ema9"] = daily.close.ewm(span=9, adjust=False).mean(); daily["ema21"] = daily.close.ewm(span=21, adjust=False).mean()
    ctx = json.loads((cache / "qcom_tut_ctx.json").read_text())
    facts = {(f["inst"].strip(), f["t"]): f for f in json.loads((cache / "qcom_tut_entries.json").read_text())}
    cards, pnl_rows = [], []
    for c in C["cards"]:
        et = pd.Timestamp(c["t"]); d = et.normalize(); key = (c["sym"].strip(), et.strftime("%m-%d %H:%M"))
        f = facts[key]; cx = ctx[str(d.date())]
        i5 = pd.read_csv(cache / f"qcom_tut_5m_{d.date()}.csv", index_col=0, parse_dates=True)
        i5["vw"] = (i5.close * i5.volume).cumsum() / i5.volume.cumsum()
        front5 = i5[i5.index <= et.floor("5min")]
        dstart = d - pd.Timedelta(days=90)
        dfront = daily[(daily.index >= dstart) & (daily.index < d)]; dback = daily[daily.index >= dstart]
        pre = daily[daily.index < d]; pivot = float(pre.high.tail(15).max())
        exits = f.get("exits") or []
        mk_d = [{"time": d.strftime("%Y-%m-%d"), "position": "belowBar", "color": "#157a4d", "shape": "arrowUp", "text": "entry"}]
        mk_i = [{"time": epoch(et.floor("5min")), "position": "belowBar", "color": "#157a4d", "shape": "arrowUp", "text": f"entry {f['px']}"}]
        _rem = 100.0 if (c["sym"].strip() == "QCOM" and et.strftime("%H:%M") == "15:26") else float(f["qty"])
        used = []
        for (xt, xq, xp) in exits:
            if _rem <= 0: break
            used.append((xt, xq, xp)); _rem -= float(xq)
        for (xt, xq, xp) in used:
            xts = pd.Timestamp(f"2026-{xt}")
            mk_d.append({"time": xts.strftime("%Y-%m-%d"), "position": "aboveBar", "color": "#c23b3b", "shape": "arrowDown", "text": f"exit {xp}"})
            if xts.normalize() == d:
                mk_i.append({"time": epoch(xts.floor("5min")), "position": "aboveBar", "color": "#c23b3b", "shape": "arrowDown", "text": f"exit {xp}"})
        mk_d = sorted({m["time"] + m["text"]: m for m in mk_d}.values(), key=lambda m: m["time"])
        mk_i = sorted(mk_i, key=lambda m: m["time"])
        opt = f.get("dte") == f.get("dte") and f.get("dte") is not None
        front_facts = [("Time", et.strftime("%a %-m/%-d %H:%M")), ("Trade", c["label"]),
                       ("QCOM at entry", f"{f['S']:.2f} ({f['day_chg']:+.1f}% on the day; opened {f['gap']:+.1f}%)"),
                       ("vs VWAP", f"{f['vs_vwap']:+.2f}%"), ("Day's range so far", f"{f['lod']:.2f} – {f['hod']:.2f} (opening range {f['orl']:.2f} – {f['orh']:.2f})"),
                       ("15-day high", f"{f['pivot']:.2f} (price {f['vs_pivot']:+.1f}% from it)"), ("vs 21 EMA", f"{f['ext21_adr']:+.2f} ADR"),
                       ("Daily chart", f"{cx['state']}: {cx['reason']}")]
        if opt:
            front_facts.append(("Contract", f"{int(f['dte'])} days to expiry, {f['otm']:.1f}% out of the money"))
        # realised P&L from the fills (commissions excluded)
        mult = 100 if opt else 1; qty = float(f["qty"])
        if c["sym"].strip() == "QCOM" and et.strftime("%H:%M") == "15:26":
            qty = 100.0                                      # the three 15:26 fills are one 100-share purchase
        rem = qty; realised = 0.0
        for (_, xq, xp) in exits:
            take = min(rem, float(xq)); realised += take * (float(xp) - float(f["px"])) * mult; rem -= take
            if rem <= 0: break
        side = -1 if "P00" in c["sym"] and "155000" in c["sym"] else 1
        pnl_rows.append({"label": c["label"], "verdict": c["verdict"], "realised": round(realised * side, 0), "open": rem > 0})
        cards.append(dict(t=c["t"], label=c["label"], verdict=c["verdict"], why=c["why"], happened=c["happened"], rule=c["rule"],
                          grade=f["grade"], facts=front_facts,
                          front=dict(daily=candles(dfront, False), e9=line(dfront.ema9, False), e21=line(dfront.ema21, False),
                                     intraday=candles(front5, True), vwap=line(front5.vw, True), pivot=round(pivot, 2)),
                          back=dict(daily=candles(dback, False), e9=line(dback.ema9, False), e21=line(dback.ema21, False),
                                    intraday=candles(i5, True), vwap=line(i5.vw, True), pivot=round(pivot, 2), mk_d=mk_d, mk_i=mk_i)))
    good = [r for r in pnl_rows if r["verdict"] == "good"]; bad = [r for r in pnl_rows if r["verdict"] != "good"]
    summary = dict(good_real=sum(r["realised"] for r in good), bad_real=sum(r["realised"] for r in bad),
                   n_good=len(good), n_bad=len([r for r in pnl_rows if r["verdict"] == "bad"]), n_gray=len([r for r in pnl_rows if r["verdict"] == "gray"]))
    data = dict(title=C["title"], intro=C["intro"], checklist=C["checklist"], cards=cards, summary=summary, pnl=pnl_rows)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PAGE.replace("__CSS__", BASE_CSS + CSS).replace("__LWC__", LIGHTWEIGHT_CHARTS_SCRIPT)
                   .replace("__TITLE__", html.escape(C["title"])).replace("__DATA__", json.dumps(data)))
    print(f"wrote {out} ({len(cards)} cards, {out.stat().st_size // 1024} KB)")
    return 0


CSS = """
 body { padding: 22px 26px 60px; max-width: 1100px; margin: 0 auto; }
 a.back { color: var(--accent); text-decoration: none; font-size: 12.5px; }
 h1 { font-size: 21px; margin: 10px 0 2px; } .muted { color: var(--muted); }
 .nav { display: flex; align-items: center; gap: 10px; margin: 14px 0; flex-wrap: wrap; }
 .nav button, .ans button { font: inherit; border: 1px solid var(--border); background: var(--panel); border-radius: 8px; padding: 7px 14px; cursor: pointer; }
 .nav button:hover, .ans button:hover { border-color: var(--accent); }
 .dots { display: flex; gap: 5px; flex-wrap: wrap; } .dot { width: 12px; height: 12px; border-radius: 50%; background: #d7dbe3; cursor: pointer; }
 .dot.cur { outline: 2px solid var(--accent); } .dot.ok { background: var(--good); } .dot.no { background: var(--bad); } .dot.gy { background: var(--neutral); }
 .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; }
 .card h2 { margin: 0 0 4px; font-size: 18px; } .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
 @media (max-width: 820px) { .grid { grid-template-columns: 1fr; } }
 .chart { border: 1px solid var(--border); border-radius: 8px; min-height: 260px; } .clabel { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 0 0 4px; }
 table.facts { border-collapse: collapse; width: 100%; font-size: 13px; margin-top: 12px; }
 table.facts th { text-align: left; color: var(--muted); font-weight: 500; padding: 4px 12px 4px 0; width: 170px; vertical-align: top; } table.facts td { padding: 4px 0; }
 .prompt { margin-top: 14px; font-weight: 600; } .ans { display: flex; gap: 10px; margin-top: 8px; }
 .ans button.take { border-color: rgba(21,122,77,.5); } .ans button.pass { border-color: rgba(194,59,59,.5); }
 .back { margin-top: 16px; border-top: 1px dashed var(--border); padding-top: 14px; }
 .v { display: inline-block; padding: 3px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
 .v.good { background: rgba(52,201,140,.15); color: var(--good); } .v.bad { background: rgba(239,107,107,.15); color: var(--bad); } .v.gray { background: rgba(240,181,86,.18); color: var(--neutral); }
 .back ul { margin: 8px 0; padding-left: 18px; } .back li { margin: 3px 0; } .rule { margin-top: 10px; background: #eef3ff; border-left: 3px solid var(--accent); padding: 8px 12px; border-radius: 6px; }
 .yours { font-size: 12.5px; margin-left: 8px; } .check li { margin: 5px 0; } .kbd { font-size: 11px; color: var(--muted); }
 table.pnl { border-collapse: collapse; width: 100%; font-size: 13px; } table.pnl td, table.pnl th { padding: 5px 8px; border-bottom: 1px solid var(--border); text-align: left; } td.num { text-align: right; }
"""

PAGE = """<title>__TITLE__</title>
<style>__CSS__</style>
__LWC__
<a class="back" href="../../index.html">&larr; Home</a> &middot; <a class="back" href="../../trade_reviews.html">Trade journal</a>
<h1>__TITLE__</h1>
<div class="muted" style="font-size:12.5px">A flip book: judge each entry from the front of the card, then flip it. <span class="kbd">Keys: &larr; &rarr; to move, T = take it, P = pass, F = flip.</span></div>
<div class="nav"><button id="prev">&larr; Prev</button><div class="dots" id="dots"></div><button id="next">Next &rarr;</button><span class="muted" id="pos"></span></div>
<div id="stage"></div>
<script>
const D = __DATA__;
const N = D.cards.length + 2;               // intro + cards + summary
let idx = 0, charts = [];
const K = 'qcom_tutorial_answers_v1';
function load() { try { return JSON.parse(localStorage.getItem(K) || '{}'); } catch (e) { return {}; } }
function save(a) { try { localStorage.setItem(K, JSON.stringify(a)); } catch (e) {} }
let answers = load();
function esc(s) { return String(s).replace(/[&<>]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c])); }
function correct(v, a) { return v === 'gray' ? true : (v === 'good' ? a === 'take' : a === 'pass'); }
function clearCharts() { charts.forEach(c => { try { c.remove(); } catch (e) {} }); charts = []; }
function mkChart(el, intraday) {
  const ch = LightweightCharts.createChart(el, { width: el.clientWidth || 520, height: 260,
    layout: { background: { color: '#ffffff' }, textColor: '#6b7280' }, grid: { vertLines: { color: '#eef0f4' }, horzLines: { color: '#eef0f4' } },
    rightPriceScale: { borderColor: '#e1e4ea' }, timeScale: { borderColor: '#e1e4ea', timeVisible: intraday, secondsVisible: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal } });
  charts.push(ch); return ch;
}
function drawDaily(el, s, withMarkers) {
  const ch = mkChart(el, false);
  const cs = ch.addCandlestickSeries({ upColor: '#157a4d', downColor: '#c23b3b', borderVisible: false, wickUpColor: '#157a4d', wickDownColor: '#c23b3b' });
  cs.setData(s.daily); if (withMarkers && s.mk_d) cs.setMarkers(s.mk_d);
  ch.addLineSeries({ color: '#3f6fd8', lineWidth: 2 }).setData(s.e9);
  ch.addLineSeries({ color: '#e08a1e', lineWidth: 2 }).setData(s.e21);
  cs.createPriceLine({ price: s.pivot, color: '#5b6272', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '15-day high' });
  ch.timeScale().fitContent();
}
function drawIntra(el, s, withMarkers) {
  const ch = mkChart(el, true);
  const cs = ch.addCandlestickSeries({ upColor: '#157a4d', downColor: '#c23b3b', borderVisible: false, wickUpColor: '#157a4d', wickDownColor: '#c23b3b' });
  cs.setData(s.intraday); if (withMarkers && s.mk_i) cs.setMarkers(s.mk_i);
  ch.addLineSeries({ color: '#8b5cf6', lineWidth: 2 }).setData(s.vwap);
  ch.timeScale().fitContent();
}
function dots() {
  const el = document.getElementById('dots'); el.innerHTML = '';
  for (let i = 0; i < N; i++) {
    const d = document.createElement('div'); d.className = 'dot' + (i === idx ? ' cur' : '');
    if (i >= 1 && i <= D.cards.length) { const a = answers[i - 1]; if (a) { const v = D.cards[i - 1].verdict; d.className += v === 'gray' ? ' gy' : (correct(v, a) ? ' ok' : ' no'); } }
    d.title = i === 0 ? 'Intro' : (i === N - 1 ? 'Summary' : D.cards[i - 1].label); d.onclick = () => go(i); el.appendChild(d);
  }
  document.getElementById('pos').textContent = idx === 0 ? 'Intro' : (idx === N - 1 ? 'Summary' : `Card ${idx} of ${D.cards.length}`);
}
function renderIntro(st) {
  st.innerHTML = `<div class="card"><h2>How to use this</h2><p>${esc(D.intro)}</p><h2 style="margin-top:14px">The checklist</h2><ul class="check">${D.checklist.map(x => `<li>${esc(x)}</li>`).join('')}</ul>
  <p class="muted" style="font-size:12.5px">Daily chart: blue = 9 EMA, orange = 21 EMA, dashed = 15-day high. 5-minute chart: purple = VWAP. The front of each card only shows what you could see at the fill.</p>
  <div class="ans"><button onclick="go(1)">Start &rarr;</button><button onclick="answers={};save(answers);dots()">Reset my answers</button></div></div>`;
}
function renderCard(st, i, flipped) {
  const c = D.cards[i], a = answers[i];
  st.innerHTML = `<div class="card"><h2>${esc(c.label)}</h2><div class="muted">${esc(c.t)}</div>
   <div class="grid"><div><div class="clabel">Daily${flipped ? ' (through 9/11)' : ' (to the prior close)'}</div><div class="chart" id="cd"></div></div>
   <div><div class="clabel">5-minute${flipped ? ' (the whole day)' : ' (to the entry bar)'}</div><div class="chart" id="ci"></div></div></div>
   <table class="facts">${c.facts.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('')}</table>
   <div class="prompt">Your call: take this entry, or pass?</div>
   <div class="ans"><button class="take" onclick="answer(${i},'take')">Take it</button><button class="pass" onclick="answer(${i},'pass')">Pass</button>
   <button onclick="flip(${i})">Flip card</button>${a ? `<span class="yours">You said: <b>${a === 'take' ? 'take it' : 'pass'}</b></span>` : ''}</div>
   ${flipped ? `<div class="back"><span class="v ${c.verdict}">${c.verdict === 'gray' ? 'gray area' : c.verdict + ' entry'}</span> <span class="muted" style="font-size:12.5px">rubric grade ${esc(c.grade)}</span>
     ${a ? `<span class="yours">${c.verdict === 'gray' ? 'Gray: either answer is defensible, the lesson is in the why.' : (correct(c.verdict, a) ? '✓ You matched the verdict.' : '✗ The verdict differs.')}</span>` : ''}
     <ul>${c.why.map(x => `<li>${esc(x)}</li>`).join('')}</ul><div><b>What happened.</b> ${esc(c.happened)}</div><div class="rule"><b>Rule.</b> ${esc(c.rule)}</div></div>` : ''}
  </div>`;
  const s = flipped ? c.back : c.front;
  drawDaily(document.getElementById('cd'), s, flipped); drawIntra(document.getElementById('ci'), s, flipped);
}
function renderSummary(st) {
  let n = 0, ok = 0; D.cards.forEach((c, i) => { if (answers[i]) { n++; if (correct(c.verdict, answers[i])) ok++; } });
  const S = D.summary;
  st.innerHTML = `<div class="card"><h2>Summary</h2>
   <p><b>Your score:</b> ${n ? `${ok} of ${n} answered cards match the verdict (gray cards count either way).` : 'answer some cards to get a score.'}</p>
   <p><b>The ${S.n_good} good entries</b> share one shape: the daily chart in play, a quiet location near the 21 EMA or right at the 15-day high, a 3-11 week contract around 0.2-0.3 delta, and then no touching it.
   <b>The ${S.n_bad} bad and ${S.n_gray} gray entries</b> share the opposite: an out-of-play daily chart, a gap-down bounce or a late-day stab, contracts with under a week left or in size, several vehicles on one idea, and exits within the hour with no stop hit.</p>
   <table class="pnl"><tr><th>Entry</th><th>Verdict</th><th class="num">Realised P&amp;L</th><th>Still open</th></tr>
   ${D.pnl.map(r => `<tr><td>${esc(r.label)}</td><td><span class="v ${r.verdict}">${r.verdict}</span></td><td class="num">${r.realised >= 0 ? '+' : ''}${r.realised}</td><td>${r.open ? 'yes' : ''}</td></tr>`).join('')}</table>
   <p class="muted" style="font-size:12.5px">Realised P&amp;L from the fills, commissions excluded. The open good entries (the put spread and the Nov 200C) carry their gains unrealised: about +$112 and +$489 at the 9/10-9/11 marks.</p>
   <div class="rule"><b>The one sentence.</b> Your winners were bought once, quietly, with the right contract, and left alone. Your losers were bought on noise, with the wrong contract, and sold on noise.</div></div>`;
}
let flippedState = {};
function go(i) { idx = Math.max(0, Math.min(N - 1, i)); clearCharts(); const st = document.getElementById('stage');
  if (idx === 0) renderIntro(st); else if (idx === N - 1) renderSummary(st); else renderCard(st, idx - 1, !!flippedState[idx - 1]); dots(); }
function answer(i, a) { answers[i] = a; save(answers); flippedState[i] = true; go(i + 1); }
function flip(i) { flippedState[i] = !flippedState[i]; go(i + 1); }
document.getElementById('prev').onclick = () => go(idx - 1); document.getElementById('next').onclick = () => go(idx + 1);
document.addEventListener('keydown', e => { if (e.key === 'ArrowRight') go(idx + 1); else if (e.key === 'ArrowLeft') go(idx - 1);
  else if (idx >= 1 && idx <= D.cards.length) { const i = idx - 1; if (e.key === 't' || e.key === 'T') answer(i, 'take'); else if (e.key === 'p' || e.key === 'P') answer(i, 'pass'); else if (e.key === 'f' || e.key === 'F') flip(i); } });
go(0);
</script>
"""

if __name__ == "__main__":
    raise SystemExit(main())

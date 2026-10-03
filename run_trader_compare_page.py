#!/usr/bin/env python3
"""Ariel vs Martin Luk vs Gabe: high-level entry / holding / return stats on one page (data/journal/compare/index.html).
Gabe 2026-10-03: "a page that compares high level stats of Ariel, Martin Luk and myself ... average entry point, in terms
of adr from the 20-EMA, and if possible, average holding period and return. Restrict my journal to just long and short
stock strategies."

ENTRY POINT = (price - EMA20[t-1]) / (ADR%[t-1] x close[t-1]) on the fill day, the same definition as the Ariel / Luk
campaign pages (ext() in run_luk_trade_pages.py), on unadjusted yfinance dailies.
  Gabe   exact: his broker entry price (lib.mysql_lib.reconstruct_trade_cycles, STK cycles whose review is 'long stock'
         or 'short stock').
  Ariel  exact where he stated a fill price that lies inside the day's range; otherwise only the day's range is known.
  Luk    the day's range only.
  For a like-for-like number all three also get the fill-day MIDPOINT ((low+high)/2) -- Gabe's exact-vs-midpoint gap
  shows how far that proxy can sit from a real fill.
HOLDING PERIOD = trading days from the opening fill to the closing row (Gabe: broker exit date). Ariel / Luk closing
  rows carry the video date when no fill date was given, so their holds are approximate.
RETURN per trade, signed for direction:
  actual  Gabe from his fills; Ariel from his monthly recap slides (broker_trades.csv 'P&L %', most likely return on
          the position; Oct 2025 - Mar 2026 only); Luk never states one.
  proxy   fill-day midpoint -> exit-day midpoint, for all three (same-day trades = that day's midpoint both sides = 0,
          so the proxy is only shown for multi-day holds).
Retrospective campaigns (discussed after the outcome was known) and Luk's pending-clarification campaigns are excluded.
Descriptive only: none of this is evidence for setup selection (CLAUDE.md), and the three samples cover different
periods -- the SAME-WINDOW block restricts all three to Gabe's window.

  PYTHONPATH=src:. .venv/bin/python3 run_trader_compare_page.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import run_ariel_trade_pages as AR
import run_luk_trade_pages as LK
from lib.mysql_lib import reconstruct_trade_cycles
from run_trade_review_pages import BASE_CSS

OUT = Path("data/journal/compare")
e = html.escape


def bars(tks: list[str]) -> dict[str, pd.DataFrame]:
    px = yf.download(sorted(set(tks)), start="2024-10-01", auto_adjust=False, progress=False, group_by="ticker", threads=True)
    H = {}
    for t in set(tks):
        try:
            h = px[t].dropna(subset=["Close"])
            if len(h):
                H[t] = h
        except KeyError:
            pass
    return H


def mid(h: pd.DataFrame, day) -> float | None:
    k = h.index.searchsorted(pd.Timestamp(day))
    return float((h.High.iloc[k] + h.Low.iloc[k]) / 2) if k < len(h) else None


def hold_days(a, b) -> int | None:
    if pd.isna(a) or pd.isna(b) or pd.Timestamp(b) < pd.Timestamp(a):
        return None
    return int(np.busday_count(pd.Timestamp(a).date(), pd.Timestamp(b).date()))


def row(trader, side, tk, d0, d1, ext0, exact, actual) -> dict:
    return dict(trader=trader, side=side, tk=tk, entry=pd.Timestamp(d0), exit=pd.Timestamp(d1) if d1 is not None and pd.notna(d1) else pd.NaT,
                lo=ext0["low"] if ext0 else np.nan, hi=ext0["high"] if ext0 else np.nan,
                mid=(ext0["low"] + ext0["high"]) / 2 if ext0 else np.nan, exact=exact, actual=actual)


def gabe() -> list[dict]:
    rv = pd.DataFrame(json.load(open("data/journal/trade_reviews_data.json"))["rows"])
    rv = rv[rv.vehicle.isin(["long stock", "short stock"])]
    keep = {(r.underlying, r.entryDate, "LONG" if r.vehicle == "long stock" else "SHORT") for r in rv.itertuples()}
    c = reconstruct_trade_cycles()
    c = c[c.asset_category == "STK"].copy()
    c = c[[(r.underlying_symbol, str(r.entry_date), r.first_side) in keep for r in c.itertuples()]]
    return [dict(tk=r.underlying_symbol, side="long" if r.first_side == "LONG" else "short", d0=r.entry_date,
                 d1=None if r.still_open else r.exit_date, px0=float(r.entry_price),
                 actual=None if r.still_open else (float(r.exit_price) / float(r.entry_price) - 1) * 100 * (1 if r.first_side == "LONG" else -1))
            for r in c.itertuples()]


def from_campaigns(cs: list[dict], trader: str, skip) -> list[dict]:
    out = []
    for c in cs:
        if skip(c) or c["dirn"] not in ("long", "short"):
            continue
        op = next((x for x in c["rows"] if str(x["action"]) in AR.OPENERS | LK.OPENERS and pd.notna(x["fill"])), None)
        if op is None:
            continue
        cl = next((x for x in reversed(c["rows"]) if str(x["action"]) in AR.CLOSERS and pd.notna(x["when"])), None)
        px = op.get("price") if op.get("price_kind") == "fill" and isinstance(op.get("price"), (int, float)) and np.isfinite(op.get("price")) else None
        act = None
        if trader == "Ariel" and c.get("broker"):
            v = [float(b["pnl_pct"]) for b in c["broker"] if str(b.get("status")) == "closed" and pd.notna(b.get("pnl_pct"))]
            act = float(np.mean(v)) if v else None
        out.append(dict(tk=c["tk"], side=c["dirn"], d0=op["fill"], d1=cl["when"] if cl is not None else None, px0=px, actual=act))
    return out


def build(trader: str, recs: list[dict], H: dict) -> list[dict]:
    rows = []
    for r in recs:
        if r["tk"] not in H:
            continue
        h = H[r["tk"]]
        x = LK.ext(h, pd.Timestamp(r["d0"]), r["px0"])
        if not x:
            continue
        exact = x.get("stated") if x.get("stated_in_range", True) else None
        if trader == "Gabe":
            exact = x.get("stated")
        R = row(trader, r["side"], r["tk"], r["d0"], r["d1"], x, exact, r["actual"])
        R["hold"] = hold_days(R["entry"], R["exit"])
        m0, m1 = mid(h, R["entry"]), (mid(h, R["exit"]) if pd.notna(R["exit"]) else None)
        R["proxy"] = ((m1 / m0 - 1) * 100 * (1 if r["side"] == "long" else -1)) if (m0 and m1 and R["hold"]) else np.nan
        rows.append(R)
    return rows


def stats(g: pd.DataFrame) -> dict:
    f = lambda s, fn: (fn(s.dropna()) if s.notna().sum() else np.nan)
    hold = g.hold.dropna()
    act = g.actual.dropna()
    return dict(n=len(g), window=f"{g.entry.min():%Y-%m-%d} &rarr; {g.entry.max():%Y-%m-%d}" if len(g) else "",
                exact_n=int(g.exact.notna().sum()), exact_med=f(g.exact, np.median), exact_mean=f(g.exact, np.mean),
                mid_med=f(g.mid, np.median), mid_mean=f(g.mid, np.mean), lo_med=f(g.lo, np.median), hi_med=f(g.hi, np.median),
                mid_p25=f(g.mid, lambda s: np.percentile(s, 25)), mid_p75=f(g.mid, lambda s: np.percentile(s, 75)),
                ext2=f(g.mid, lambda s: (s > 2).mean() * 100),
                hold_n=len(hold), hold_med=hold.median() if len(hold) else np.nan, hold_mean=hold.mean() if len(hold) else np.nan,
                same_day=(hold == 0).mean() * 100 if len(hold) else np.nan,
                act_n=len(act), act_mean=act.mean() if len(act) else np.nan, act_med=act.median() if len(act) else np.nan,
                act_win=(act > 0).mean() * 100 if len(act) else np.nan,
                prx_n=int(g.proxy.notna().sum()), prx_mean=f(g.proxy, np.mean), prx_med=f(g.proxy, np.median),
                prx_win=f(g.proxy, lambda s: (s > 0).mean() * 100))


def fmt(v, spec="+.2f", suf="") -> str:
    return "&mdash;" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:{spec}}{suf}"


METRICS = [
    ("Entries (with daily data)", lambda s: f"{s['n']}"),
    ("Entry dates", lambda s: s["window"]),
    ("<b>Entry vs 20 EMA, exact fill</b> (median / mean, ADR)", lambda s: f"<b>{fmt(s['exact_med'])}</b> / {fmt(s['exact_mean'])} <span class=m>(n {s['exact_n']})</span>" if s["exact_n"] else "&mdash;"),
    ("<b>Entry vs 20 EMA, fill-day midpoint</b> (median / mean)", lambda s: f"<b>{fmt(s['mid_med'])}</b> / {fmt(s['mid_mean'])}"),
    ("&nbsp;&nbsp;midpoint middle half (p25 &hellip; p75)", lambda s: f"{fmt(s['mid_p25'])} &hellip; {fmt(s['mid_p75'])}"),
    ("&nbsp;&nbsp;fill-day range (median low &hellip; median high)", lambda s: f"{fmt(s['lo_med'])} &hellip; {fmt(s['hi_med'])}"),
    ("&nbsp;&nbsp;share entered &gt; 2 ADR from the EMA (midpoint)", lambda s: fmt(s["ext2"], ".0f", "%")),
    ("<b>Holding period</b>, trading days (median / mean)", lambda s: f"<b>{fmt(s['hold_med'], '.0f')}</b> / {fmt(s['hold_mean'], '.1f')} <span class=m>(n {s['hold_n']})</span>" if s["hold_n"] else "&mdash;"),
    ("&nbsp;&nbsp;same-day round trips", lambda s: fmt(s["same_day"], ".0f", "%")),
    ("<b>Return per trade, actual</b> (mean / median, win rate)", lambda s: f"<b>{fmt(s['act_mean'], '+.2f', '%')}</b> / {fmt(s['act_med'], '+.2f', '%')}, {fmt(s['act_win'], '.0f', '%')} win <span class=m>(n {s['act_n']})</span>" if s["act_n"] else "&mdash; (not stated)"),
    ("Return per multi-day trade, proxy (median / mean, win)", lambda s: f"{fmt(s['prx_med'], '+.2f', '%')} / {fmt(s['prx_mean'], '+.2f', '%')}, {fmt(s['prx_win'], '.0f', '%')} win <span class=m>(n {s['prx_n']})</span>" if s["prx_n"] else "&mdash;"),
]


def table(D: pd.DataFrame, title: str) -> str:
    cols = [(t, sd) for sd in ("long", "short") for t in ("Gabe", "Ariel", "Luk")]
    S = {k: stats(D[(D.trader == k[0]) & (D.side == k[1])]) for k in cols}
    head = "".join(f"<th class='{'sep' if t == 'Gabe' else ''}'>{t}<div class=m>{sd}</div></th>" for t, sd in cols)
    body = "".join("<tr><td class=lab>" + lab + "</td>" + "".join(f"<td class='{'sep' if t == 'Gabe' else ''}'>{fn(S[(t, sd)])}</td>" for t, sd in cols) + "</tr>"
                   for lab, fn in METRICS)
    return f"<div class=block><h2>{title}</h2><div class=wrap><table><tr><th></th>{head}</tr>{body}</table></div></div>"


def page(D: pd.DataFrame, w0, w1) -> str:
    same = D[(D.entry >= w0) & (D.entry <= w1)]
    return f"""<meta charset="utf-8">
<title>Trader Comparison</title>
<style>{BASE_CSS}
 body {{ padding: 24px 28px 50px; }} h1 {{ font-size: 22px; margin: 10px 0 4px; }} .sub {{ color: var(--muted); font-size: 12.5px; margin-bottom: 16px; max-width: 1000px; line-height: 1.5; }}
 a.back {{ color: var(--accent); text-decoration: none; font-size: 12.5px; }} .m {{ color: var(--muted); font-size: 11px; font-weight: 400; }}
 .block {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 16px; }}
 .block h2 {{ font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 0 0 10px; }}
 .wrap {{ overflow-x: auto; }} table {{ border-collapse: collapse; width: 100%; font-size: 12.5px; }}
 th, td {{ padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: right; white-space: nowrap; }} th {{ font-weight: 600; }}
 td.lab {{ text-align: left; color: var(--text); }} .sep {{ border-left: 2px solid var(--border); }}
</style>
<a class="back" href="../index.html">&larr; Home</a> &middot; <a class="back" href="../ariel/index.html">Ariel's trades</a> &middot; <a class="back" href="../luk/index.html">Luk's trades</a> &middot; <a class="back" href="../trade_reviews.html">Trade journal</a>
<h1>Gabe vs Ariel Hernandez vs Martin Luk</h1>
<div class="sub"><b>Entry vs 20 EMA</b> = (price &minus; prior day's 20 EMA) &divide; (20-day ADR in dollars); positive = above the EMA, for shorts too.
Gabe's is his exact broker fill; Ariel's exact column uses only fills he stated that sit inside the day's range; Luk never states fills.
The <b>midpoint</b> row puts all three on the same footing: the middle of the fill day's range.
<b>Holding period</b> = trading days from the opening fill to the closing mention (Ariel / Luk: approximate, the closing row often carries the video date).
<b>Actual return</b>: Gabe from his fills, Ariel from his monthly recap slides (Oct 2025 &ndash; Mar 2026, return on the position); Luk never states one.
<b>Proxy return</b>: fill-day midpoint &rarr; exit-day midpoint, multi-day holds only &mdash; read the median: when Ariel or Luk never report a close,
a much later mention can become the "exit" (e.g. a 150-day Luk HUT hold), which inflates the mean.
Gabe = long and short stock trades only. Retrospective campaigns are excluded.
<br>⚠ Descriptive, not evidence: their logs are their own accounts, and the full-period samples cover different markets &mdash; use the same-window block to compare like with like.</div>
{table(same, f"Same window: {w0:%Y-%m-%d} &rarr; {w1:%Y-%m-%d} (Gabe's journal)")}
{table(D, "Full samples")}
<div class=m>Generated {pd.Timestamp.now():%Y-%m-%d %H:%M} by run_trader_compare_page.py. Per-trade rows: data/studies/trader_compare_rows.csv.</div>
"""


def main() -> int:
    g = gabe()
    a_cs = AR.campaigns(AR.load()); AR.attach_broker(a_cs)
    a = from_campaigns(a_cs, "Ariel", lambda c: c["retro"])
    l_cs = LK.campaigns(LK.load())
    l = from_campaigns(l_cs, "Luk", lambda c: c["state"] in ("pending", "retrospective") or not c["resolved_tk"])
    H = bars([r["tk"] for r in g + a + l])
    D = pd.DataFrame(build("Gabe", g, H) + build("Ariel", a, H) + build("Luk", l, H))
    OUT.mkdir(parents=True, exist_ok=True)
    D.to_csv("data/studies/trader_compare_rows.csv", index=False)
    gd = D[D.trader == "Gabe"]
    (OUT / "index.html").write_text(page(D, gd.entry.min(), gd.entry.max()))
    print(f"wrote {OUT}/index.html | rows: {D.groupby(['trader', 'side']).size().to_dict()}")
    for (t, sd), x in D.groupby(["trader", "side"]):
        s = stats(x)
        print(f"{t:5s} {sd:5s} n {s['n']:4d} exact {s['exact_med']:+.2f} mid {s['mid_med']:+.2f} hold {s['hold_med']} same-day {s['same_day']:.0f}% "
              f"act {s['act_mean']:+.2f}% (n {s['act_n']}) proxy {s['prx_mean']:+.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

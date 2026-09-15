#!/usr/bin/env python3
"""Chart pages for Tito Adhikary's 20 curated best trades (data/studies/Adhikary/Adhikary_Options.csv),
in the journal site's style: data/journal/tito/index.html + one page per trade.

Per trade: (1) the underlying's daily candles with the 9/21 EMAs, the pivot (high of the prior 15 sessions)
and entry / implied-exit / expiry markers; (2) the inferred option contract's daily closing mid from
silver.options_daily_v3 with his entry price and his implied exit price (entry x (1 + his return)).
Daily data only -- 2024 intraday bars are not retained, so intraday fills/peaks are invisible.
Strikes are inferred (Adhikary_inferred_strikes.csv), not his actual fills; the list is curated (20/20 wins).

  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_tito_trade_pages.py
"""
from __future__ import annotations

import asyncio, html, json, os
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from lib.athena_lib import athena
from lib.constants import CATALOG, DB, TABLE
from lib.tradier.get_daily_history import get_daily_history
from lib.tradier.tradier_client_wrapper import TradierClient
from run_trade_review_pages import BASE_CSS, DETAIL_CSS, LIGHTWEIGHT_CHARTS_SCRIPT, _candles_json

SRC = Path("data/studies/Adhikary")
OUT = Path("data/journal/tito")
TRADIER_SYM = {"BRKB": "BRK/B", "BTC": "BITO"}
V3_TICKERS = {"BRKB": ("BRK",), "BTC": ("BITO",)}
# His "BTC" call (11/6/24, 11/22 expiry): spot-bitcoin-ETF options (BTC/IBIT/GBTC) did not list until 11/19-21/2024,
# so the chart uses BITO (bitcoin-futures ETF) as a labeled proxy -- its 11/22 16C was 4.45/4.60 on 11/6.
PROXY_NOTE = {"BTC": "PROXY: spot-bitcoin-ETF options (BTC/IBIT/GBTC) first listed 11/19-21/2024, after this entry; charts use BITO (bitcoin-futures ETF) and its nearest-priced 11/22 call as a stand-in, not his confirmed contract."}


def load_trades() -> pd.DataFrame:
    t = pd.read_csv(SRC / "Adhikary_Options.csv"); t.columns = [c.strip() for c in t.columns]
    t = t.rename(columns={"Number": "n", "Entry Date": "entry", "Ticker": "ticker", "Expiration": "expiry", "Call / Put": "cp",
                          "Days_In_Trade": "days_in", "Setup_Type": "setup", "Entry_Price": "entry_px", "Return": "ret"})
    t["setup"] = t.setup.str.strip(); t["cp"] = t.cp.str.strip()
    t["entry"] = pd.to_datetime(t.entry, format="%m/%d/%y").dt.date; t["expiry"] = pd.to_datetime(t.expiry, format="%m/%d/%y").dt.date
    inf = pd.read_csv(SRC / "Adhikary_inferred_strikes.csv")[["n", "infer_strike", "delta"]]
    return t.merge(inf, on="n", how="left")


def v3_path(tk: str, cp: str, strike: float, exp: date, d0: date) -> pd.DataFrame:
    names = ",".join(f"'{x}'" for x in V3_TICKERS.get(tk, (tk,)))
    q = f"""SELECT trade_date, bid, ask, last, volume, delta FROM "{CATALOG}"."{DB}"."{TABLE}"
            WHERE ticker IN ({names}) AND cp='{cp}' AND strike={strike} AND expiry=DATE '{exp}'
              AND trade_date BETWEEN DATE '{d0}' AND DATE '{exp}' ORDER BY trade_date"""
    d = athena(q)
    if d is None or d.empty:
        return pd.DataFrame()
    d = d.drop_duplicates("trade_date").copy()
    d["mid"] = ((d.bid + d.ask) / 2).where((d.bid > 0) & (d.ask > 0), d["last"])
    d["trade_date"] = pd.to_datetime(d.trade_date)
    return d


def infer_strike_v3(tk: str, cp: str, exp: date, d0: date, px: float) -> float | None:
    names = ",".join(f"'{x}'" for x in V3_TICKERS.get(tk, (tk,)))
    q = f"""SELECT strike, bid, ask, last FROM "{CATALOG}"."{DB}"."{TABLE}"
            WHERE ticker IN ({names}) AND cp='{cp}' AND expiry=DATE '{exp}' AND trade_date=DATE '{d0}'"""
    d = athena(q)
    if d is None or d.empty:
        return None
    d["mid"] = ((d.bid + d.ask) / 2).where((d.bid > 0) & (d.ask > 0), d["last"])
    d = d.dropna(subset=["mid"])
    return float(d.iloc[(d.mid - px).abs().argsort().iloc[0]].strike) if len(d) else None


async def daily_all(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        for r in trades.itertuples():
            sym = TRADIER_SYM.get(r.ticker, r.ticker)
            end = max(r.expiry, r.entry + timedelta(days=int(r.days_in))) + timedelta(days=12)
            h = await get_daily_history(sym, r.entry - timedelta(days=160), end, client=c)
            if h is not None and len(h):
                h = h.copy(); h.index = pd.to_datetime(h.index)
                for col in ("open", "high", "low", "close"): h[col] = pd.to_numeric(h[col], errors="coerce")
            out[r.n] = h
    return out


def snap(idx: pd.DatetimeIndex, d: date) -> str | None:
    s = idx[idx >= pd.Timestamp(d)]
    return s[0].strftime("%Y-%m-%d") if len(s) else None


def build(r, h: pd.DataFrame | None, op: pd.DataFrame) -> dict:
    ret_x = 1 + r.ret / 100; exit_px = r.entry_px * ret_x
    info = dict(n=int(r.n), ticker=r.ticker, entry=str(r.entry), expiry=str(r.expiry), cp=r.cp, setup=r.setup, days_in=int(r.days_in),
                entry_px=float(r.entry_px), ret=float(r.ret), ret_x=round(ret_x, 1), exit_px=round(exit_px, 2),
                strike=None if pd.isna(r.infer_strike) else float(r.infer_strike), delta=None if pd.isna(r.delta) else float(r.delta),
                dte=(r.expiry - r.entry).days)
    und = {"candles": [], "ema9": [], "ema21": [], "markers": [], "pivot": None, "volume": []}
    if h is not None and len(h):
        h["ema9"] = h.close.ewm(span=9, adjust=False).mean(); h["ema21"] = h.close.ewm(span=21, adjust=False).mean()
        pre = h[h.index < pd.Timestamp(r.entry)]
        und["pivot"] = round(float(pre.high.tail(15).max()), 4) if len(pre) else None
        show = h[h.index >= pd.Timestamp(r.entry) - pd.Timedelta(days=50)]
        und["candles"] = _candles_json(show, intraday=False)
        und["ema9"] = [{"time": t.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for t, v in show.ema9.items()]
        und["ema21"] = [{"time": t.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for t, v in show.ema21.items()]
        if "volume" in show.columns:
            und["volume"] = [{"time": t.strftime("%Y-%m-%d"), "value": float(v),
                              "color": "rgba(21,122,77,0.45)" if c >= o else "rgba(194,59,59,0.45)"}
                             for t, v, c, o in zip(show.index, pd.to_numeric(show.volume, errors="coerce").fillna(0), show.close, show.open)]
        e = snap(show.index, r.entry); x = snap(show.index, r.entry + timedelta(days=int(r.days_in))); ex = snap(show.index, r.expiry)
        mk = []
        if e: mk.append({"time": e, "position": "belowBar", "color": "#157a4d", "shape": "arrowUp", "text": f"entry {r.cp} @{r.entry_px:.2f}"})
        if x and x != e and x != ex: mk.append({"time": x, "position": "aboveBar", "color": "#a3690a", "shape": "circle", "text": f"~exit ({int(r.days_in)}d held)"})
        if ex: mk.append({"time": ex, "position": "aboveBar", "color": "#c23b3b", "shape": "arrowDown", "text": "expiry"})
        und["markers"] = sorted(mk, key=lambda m: m["time"])
        info["und_entry_close"] = round(float(h.close.asof(pd.Timestamp(r.entry))), 2)
        info["und_move_to_exp"] = round((float(h.close.asof(pd.Timestamp(r.expiry))) / info["und_entry_close"] - 1) * 100, 1)
    opt = {"line": [], "markers": []}
    if len(op):
        opt["line"] = [{"time": t.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for t, v in zip(op.trade_date, op["mid"]) if pd.notna(v)]
        hit = op[op["mid"] >= exit_px]
        info["reached_eod"] = hit.trade_date.iloc[0].strftime("%Y-%m-%d") if len(hit) else None
        info["max_eod_mid"] = round(float(op["mid"].max()), 2); info["max_eod_date"] = op.loc[op["mid"].idxmax(), "trade_date"].strftime("%Y-%m-%d")
        info["eod_entry_mid"] = round(float(op["mid"].iloc[0]), 2)
        info["exp_mid"] = round(float(op["mid"].iloc[-1]), 2)
        info["x_at_exp_from_his_entry"] = round(info["exp_mid"] / r.entry_px, 1)
        info["x_max_eod_from_his_entry"] = round(info["max_eod_mid"] / r.entry_px, 1)
        m = [{"time": op.trade_date.iloc[0].strftime("%Y-%m-%d"), "position": "belowBar", "color": "#157a4d", "shape": "arrowUp", "text": "entry day close"}]
        if info["reached_eod"]:
            m.append({"time": info["reached_eod"], "position": "aboveBar", "color": "#c23b3b", "shape": "arrowDown", "text": f"first close >= his exit ({info['ret_x']}x)"})
        opt["markers"] = m
    tag, ctext = CATALYST.get(int(r.n), (None, None))
    info["cat_tag"] = tag
    info["catalyst"] = ctext or "No single catalyst is established in our notes -- on the chart it reads as a technical breakout."
    info["technical"] = technicals(r, h) if h is not None and len(h) else "No daily history."
    info["played_out"] = played_out(r, h, op)
    info["scale"] = scale_out(r, h, op)
    return {"info": info, "und": und, "opt": opt}


# Catalyst notes: market history, not Tito's own commentary. Only stated where the event is well established;
# otherwise the page says no single catalyst is established. (tag, text)
CATALYST = {
    1: ("CES / AI breakout", "Start of the 2024 AI run: NVDA broke out of its Aug-Dec 2023 base to new highs in the week of CES, rising about 6% on 1/8 itself."),
    2: ("Pre-announced beat", "SMCI pre-announced a big raise to its fiscal-Q2 revenue after the close on 1/18/24 and gapped roughly +35% on 1/19, the entry day."),
    3: ("Bitcoin ETF wave", "Bitcoin was climbing back toward $45-48k in early February 2024 on inflows into the newly launched spot-bitcoin ETFs; MSTR trades as a leveraged bitcoin proxy."),
    4: ("Earnings gap", "ARM reported its fiscal-Q3 results after the close on 2/7/24 (beat and raise) and gapped roughly +48% on 2/8, the entry day, then kept running for days. Tito's own label: Earnings."),
    5: ("Bitcoin ETF wave", "Same spot-bitcoin-ETF inflow wave as MSTR; Coinbase reported its Q4 2023 results on 2/15, during the hold (its first profitable quarter in two years)."),
    6: ("Blow-off top", "Exhaustion: after a parabolic run, SMCI spiked above $1,000 intraday on 2/16/24 and reversed about 20% by the close. A 0DTE put on the blow-off top, the same day."),
    7: ("Gold breakout", "Gold broke out to all-time highs in early March 2024 on Fed-cut expectations and heavy central-bank buying, resolving a months-long base."),
    8: ("Blow-off top", "Exhaustion: NVDA gapped to a new high on 3/8/24 after a straight-up post-earnings run and reversed to close about 5.5% down. A 0DTE put on the reversal."),
    9: ("WWDC", "Apple unveiled 'Apple Intelligence' at WWDC on 6/10/24; after a sell-the-news dip that day, AAPL rose about 7% on 6/11 to an all-time high, the entry day."),
    10: ("CPI rotation", "The soft June CPI print on 7/11/24 set off a sharp rotation out of mega-cap tech into value and small caps; Berkshire caught that bid."),
    11: ("CPI rotation", "The soft June CPI print on 7/11/24 set off the July 2024 small-cap rotation: IWM rose about 3.5% that day and roughly 10% over the next week."),
    12: (None, None),
    13: (None, None),
    14: ("China stimulus", "Entered the day after the Fed's first cut (50 bp on 9/18/24). From 9/24 China announced a stimulus package (PBOC rate cuts, property and stock-market support) and Chinese stocks jumped 30-40% in about a week."),
    15: (None, None),
    16: ("Election odds", "Trump Media rallied through October 2024 as Trump's odds rose in the prediction markets: a pure political proxy, entered two weeks before the vote and sold into the run-up. Tito's own label: Catalyst."),
    17: ("Earnings + election", "Palantir reported a strong Q3 after the close on 11/4/24 and gapped about 23% on 11/5, Election Day, the entry day. The post-election rally followed, and during the hold it moved its listing to Nasdaq, setting up its December Nasdaq-100 inclusion."),
    18: ("Election", "The 2024 US presidential election (11/5). Elon Musk was Trump's most prominent backer, so TSLA traded as the main 'Trump trade'. Trump's win was called overnight; TSLA opened sharply higher on 11/6 and rose about 30% in four sessions. He bought on Election Day, before the result: buying the event, not the reaction. Tito's own label: Catalyst."),
    19: ("Election / crypto", "The election result raised expectations of a crypto-friendly administration and bitcoin broke to new all-time highs on 11/6/24. (His contract is unexplained -- see the proxy note.)"),
    20: (None, None),
}


def technicals(r, h: pd.DataFrame) -> str:
    e = pd.Timestamp(r.entry); pre = h[h.index < e]; post = h[h.index >= e]
    if len(pre) < 25 or not len(post):
        return "Not enough daily history to describe the setup."
    day = post.iloc[0]; prev = float(pre.close.iloc[-1])
    adr = float(((pre.high - pre.low) / pre.close.shift(1)).tail(20).mean() * 100)
    gap = (day.open / prev - 1) * 100; chg = (day.close / prev - 1) * 100
    pivot = float(pre.high.tail(15).max()); vs = (day.close / pivot - 1) * 100
    e9, e21 = float(h.ema9.asof(e)), float(h.ema21.asof(e)); ext = (day.close - e21) / (adr / 100 * prev)
    mv = (pre.close.pct_change() * 100).tail(10); bi = mv.abs().idxmax()
    vol = pd.to_numeric(h.get("volume"), errors="coerce") if "volume" in h.columns else None
    rvol = (float(vol.loc[post.index[0]]) / float(vol[vol.index < e].tail(20).mean())) if vol is not None and vol[vol.index < e].tail(20).mean() > 0 else None
    rv_txt = (f" Entry-day volume {rvol:.1f}x the 20-day average ({'clears' if rvol >= 1.8 else 'below'} the 1.8x breakout-volume bar)." if rvol else "")
    return (f"Entry day: opened {gap:+.1f}%, closed {chg:+.1f}% at {day.close:.2f}, {abs(vs):.1f}% {'above' if vs >= 0 else 'below'} the 15-day pivot "
            f"{pivot:.2f} ({'a breakout close' if day.close > pivot else 'buying under the pivot, ahead of the move'}). "
            f"{ext:+.1f} ADR over the 21 EMA, with the 9 EMA {'above' if e9 > e21 else 'below'} the 21 ({'uptrend stack' if e9 > e21 else 'not yet stacked'}); "
            f"ADR {adr:.1f}%. Biggest move in the 10 sessions before entry: {mv.loc[bi]:+.1f}% on {bi:%-m/%-d}." + rv_txt)


def _worst_dd(v: pd.Series, dts: pd.Series) -> tuple[float, str, float, str, float] | None:
    """Largest peak-to-trough decline during the hold: (pct, peak date, peak, trough date, trough)."""
    v = v.reset_index(drop=True); dts = dts.reset_index(drop=True)
    run = v.cummax(); dd = v / run - 1
    if not len(dd) or dd.min() > -0.05:
        return None
    t = int(dd.idxmin()); p = int(v.iloc[: t + 1].idxmax())
    return float(dd.iloc[t] * 100), f"{dts.iloc[p]:%-m/%-d}", float(v.iloc[p]), f"{dts.iloc[t]:%-m/%-d}", float(v.iloc[t])


def played_out(r, h: pd.DataFrame | None, op: pd.DataFrame) -> str:
    out = []
    if h is not None and len(h):
        e = pd.Timestamp(r.entry); x = pd.Timestamp(r.expiry); w = h[(h.index >= e) & (h.index <= x)]
        if len(w) > 1:
            c0 = float(w.close.iloc[0]); pk = w.close.idxmax(); pv = float(w.close.max())
            s1 = f"The stock ran from {c0:.2f} (entry-day close) to a {pv:.2f} close on {pk:%-m/%-d} ({(pv / c0 - 1) * 100:+.0f}%) and closed at {float(w.close.iloc[-1]):.2f} at expiry"
            dd = _worst_dd(w.close, pd.Series(w.index))
            s1 += (f"; the worst drop during the hold was {dd[0]:.0f}% ({dd[2]:.2f} on {dd[1]} to {dd[4]:.2f} on {dd[3]})." if dd else ".")
            out.append(s1)
    if len(op) > 1:
        m = op["mid"].reset_index(drop=True); dts = op["trade_date"].reset_index(drop=True)
        pk = int(m.idxmax()); pv = float(m.max())
        s2 = f"The option's best daily close was {pv:.2f} on {dts.iloc[pk]:%-m/%-d}, and it finished at {float(m.iloc[-1]):.2f}"
        dd = _worst_dd(m, dts)
        s2 += (f". Holding it meant sitting through a {dd[0]:.0f}% drop ({dd[2]:.2f} on {dd[1]} to {dd[4]:.2f} on {dd[3]})." if dd else ", with no drop of 5% or more along the way.")
        out.append(s2)
    return " ".join(out)



def scale_out(r, h: pd.DataFrame | None, op: pd.DataFrame, target: float = 3.0) -> dict | None:
    """The playbook's scale-out rule: a GTC sell of 50% (or 75%) at `target` x his entry (assumed to fill at exactly
    target x -- daily closes can't show the intraday touch), the rest trailed: exit at the option's close on the first
    day the underlying closes below its 20 EMA, else at expiry."""
    if h is None or len(op) < 2 or r.entry == r.expiry:
        return None
    px = float(r.entry_px); m = op.set_index("trade_date")["mid"].astype(float)
    h = h.copy(); h["ema20"] = h.close.ewm(span=20, adjust=False).mean()
    hold = h[(h.index > pd.Timestamp(r.entry)) & (h.index <= pd.Timestamp(r.expiry))]
    brk = hold[hold.close < hold.ema20]
    if len(brk):
        t_exit = brk.index[0]; trail_x = float(m.asof(t_exit)) / px; trail_txt = f"stock closed below its 20 EMA on {t_exit:%-m/%-d}"
    else:
        trail_x = float(m.iloc[-1]) / px; trail_txt = "stock never closed below its 20 EMA -- held to expiry"
    hit = m[m >= target * px]
    x3 = f"{hit.index[0]:%-m/%-d}" if len(hit) else None
    tx = target if x3 else trail_x          # never tripled at a close: everything rides the trail
    return dict(x3=x3, trail_x=round(trail_x, 1), trail_txt=trail_txt, all_out=round(tx, 1) if x3 else None,
                s50=round(0.5 * tx + 0.5 * trail_x, 1), s75=round(0.75 * tx + 0.25 * trail_x, 1),
                hold=round(float(m.iloc[-1]) / px, 1))

PAGE_JS = """
function mk(container, h) {
  return LightweightCharts.createChart(container, {
    width: container.clientWidth || 860, height: h,
    layout: { background: { color: '#ffffff' }, textColor: '#6b7280' },
    grid: { vertLines: { color: '#e1e4ea' }, horzLines: { color: '#e1e4ea' } },
    rightPriceScale: { borderColor: '#e1e4ea' }, timeScale: { borderColor: '#e1e4ea' },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal } });
}
function renderTrade(d) {
  const u = d.und, o = d.opt, i = d.info;
  const c1 = document.getElementById('und');
  if (u.candles.length) {
    const ch = mk(c1, 380);
    const cs = ch.addCandlestickSeries({ upColor: '#157a4d', downColor: '#c23b3b', borderVisible: false, wickUpColor: '#157a4d', wickDownColor: '#c23b3b' });
    cs.setData(u.candles); if (u.markers.length) cs.setMarkers(u.markers);
    if (u.volume && u.volume.length) {
      const vs = ch.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'vol', lastValueVisible: false, priceLineVisible: false });
      vs.setData(u.volume);
      ch.priceScale('vol').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
      cs.priceScale().applyOptions({ scaleMargins: { top: 0.06, bottom: 0.26 } });
    }
    ch.addLineSeries({ color: '#3f6fd8', lineWidth: 2, title: '9 EMA' }).setData(u.ema9);
    ch.addLineSeries({ color: '#e08a1e', lineWidth: 2, title: '21 EMA' }).setData(u.ema21);
    if (u.pivot) cs.createPriceLine({ price: u.pivot, color: '#5b6272', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'pivot (15d high)' });
    ch.timeScale().fitContent();
  } else { c1.innerHTML = '<div class="chart-empty">No daily history for the underlying.</div>'; }
  const c2 = document.getElementById('opt');
  if (o.line.length > 1) {
    const ch = mk(c2, 260);
    const ls = ch.addLineSeries({ color: '#1a1d24', lineWidth: 2, title: 'option close (mid)' });
    ls.setData(o.line); if (o.markers.length) ls.setMarkers(o.markers);
    ls.createPriceLine({ price: i.entry_px, color: '#157a4d', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'his entry' });
    ls.createPriceLine({ price: i.exit_px, color: '#c23b3b', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'his exit (' + i.ret_x + 'x)' });
    ch.timeScale().fitContent();
  } else {
    c2.innerHTML = '<div class="chart-empty">' + (o.line.length === 1 ? 'Same-day (0DTE) trade: one daily print only -- the intraday path is not in daily data.' : 'No daily option data found for the inferred contract.') + '</div>';
  }
}
"""


def fmt_x(v):
    return "—" if v is None else f"{v:,.1f}x"


def scale_block(i: dict) -> str:
    sc = i.get("scale")
    head = ('<div class="block"><h2>Scale-out rule</h2><p style="margin-bottom:8px">When the option first triples, sell half to three quarters '
            '(a GTC set at entry); trail the rest until the stock closes below its 20 EMA. Banks spike trades, keeps a runner for grinds.</p>')
    if not sc:
        return head + '<p class="chart-note">Not applicable: same-day (0DTE) trade or no daily option data.</p></div>'
    rows = [("His actual", f"<b>{i['ret_x']}x</b>"),
            ("All out when it triples", f"{sc['all_out']}x (first close at 3x on {sc['x3']})" if sc["x3"] else "never tripled at a daily close"),
            ("Half out at 3x, half trailed", f"<b>{sc['s50']}x</b>"),
            ("Three quarters out at 3x, rest trailed", f"{sc['s75']}x"),
            ("Trailed portion alone", f"{sc['trail_x']}x -- {sc['trail_txt']}"),
            ("Held everything to expiry", f"{sc['hold']}x")]
    tbl = "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in rows)
    return head + f'<table class="facts">{tbl}</table><div class="chart-note">Multiples are of his entry price. The 3x sale assumes the GTC fills at exactly 3.0x; the trailed portion exits at the option\'s daily closing mid.</div></div>'


def trade_page(d: dict) -> str:
    i = d["info"]; e = html.escape
    k = f"{i['strike']:g}" if i["strike"] else "?"
    reached = (f"first daily close at or above his exit on <b>{i['reached_eod']}</b>" if i.get("reached_eod")
               else (f"never at a daily close -- best close {i['max_eod_mid']} on {i['max_eod_date']} "
                     f"({i['x_max_eod_from_his_entry']}x from his entry), so his exit was intraday" if i.get("max_eod_mid") else "no option data"))
    rows = [("Setup", i["setup"]), ("Vehicle (inferred)", f"{i['ticker']} {i['expiry']} {k}{i['cp']}" + (f" &middot; &Delta; {i['delta']:+.2f} at entry" if i["delta"] else "")),
            ("Entry", f"{i['entry']} @ {i['entry_px']:.2f} ({i['dte']} DTE)"), ("Days in trade (his)", i["days_in"]),
            ("His return", f"<b>+{i['ret']:,.0f}%</b> = {i['ret_x']}x &rarr; implied exit &asymp; {i['exit_px']:.2f}"),
            ("Option at expiry (daily close)", f"{i.get('exp_mid', '—')} = {fmt_x(i.get('x_at_exp_from_his_entry'))} from his entry"),
            ("Entry-day close of the option", f"{i.get('eod_entry_mid', '—')} (his fill was intraday)"), ("His exit vs daily closes", reached),
            ("Underlying", f"close {i.get('und_entry_close', '—')} on entry day, {i.get('und_move_to_exp', '—')}% to expiry")]
    if i["ticker"] in PROXY_NOTE: rows.insert(0, ("⚠ Proxy", PROXY_NOTE[i["ticker"]]))
    tbl = "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in rows)
    return f"""<meta charset="utf-8">
<title>Tito #{i['n']} {e(i['ticker'])} {i['cp']} +{i['ret']:,.0f}%</title>
<style>{DETAIL_CSS}
 table.facts {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
 table.facts th {{ text-align: left; color: var(--muted); font-weight: 500; padding: 5px 12px 5px 0; width: 230px; vertical-align: top; }}
 table.facts td {{ padding: 5px 0; }}
 #und, #opt {{ width: 100%; }}
</style>
{LIGHTWEIGHT_CHARTS_SCRIPT}
<a class="back" href="index.html">&larr; Tito's best trades</a>
<h1>#{i['n']} {e(i['ticker'])} {i['cp']} &middot; +{i['ret']:,.0f}% ({i['ret_x']}x)</h1>
<div class="dates">{i['setup']} &middot; entered {i['entry']} &middot; expiry {i['expiry']}</div>
<div class="block"><table class="facts">{tbl}</table></div>
<div class="block commentary"><h2>Commentary</h2>
<p><b>Catalyst.</b> {e(i['catalyst'])}</p>
<p style="margin-top:8px"><b>Technical trigger.</b> {e(i['technical'])}</p>
<p style="margin-top:8px"><b>How it played out.</b> {e(i['played_out'])}</p>
<div class="chart-note">Catalyst notes come from market history, not from Tito's commentary. Technical numbers are computed from daily bars.</div></div>
{scale_block(i)}
<div class="block"><h2>Underlying, daily</h2><div class="chart-box"><div id="und"></div></div>
<div class="chart-note">Blue = 9 EMA, orange = 21 EMA, dashed = pivot (high of the 15 sessions before entry). Bars at the bottom = daily volume (green = up day, red = down day). Green arrow = entry, amber dot = entry + his days-in-trade, red arrow = expiry.</div></div>
<div class="block"><h2>Option, daily closing mid</h2><div class="chart-box"><div id="opt"></div></div>
<div class="chart-note">From silver.options_daily_v3 for the inferred contract. Dashed green = his entry price, dashed red = his implied exit (entry &times; (1 + return)). Daily closes only: intraday entries and peaks are not visible.</div></div>
<script>{PAGE_JS}
renderTrade({json.dumps(d)});</script>
"""


def index_page(ds: list[dict]) -> str:
    rows = []
    for d in sorted(ds, key=lambda z: -z["info"]["ret"]):
        i = d["info"]; k = f"{i['strike']:g}{i['cp']}" if i["strike"] else f"?{i['cp']}"
        reached = i.get("reached_eod") or ("intraday only" if i.get("max_eod_mid") else "—")
        rows.append(f"<tr onclick=\"location.href='{i['n']:02d}_{i['ticker']}.html'\"><td>{i['n']}</td><td><b>{i['ticker']}</b></td><td>{i['entry']}</td>"
                    f"<td>{i['setup']}</td><td>{i.get('cat_tag') or '&mdash;'}</td><td>{i['expiry']} {k}{' (BITO proxy)' if i['ticker'] in PROXY_NOTE else ''}</td><td class='num'>{i['dte']}</td><td class='num'>{i['days_in']}</td>"
                    f"<td class='num'>{i['entry_px']:.2f}</td><td class='num'><b>+{i['ret']:,.0f}%</b> ({i['ret_x']}x)</td>"
                    f"<td class='num'>{fmt_x(i.get('x_at_exp_from_his_entry'))}</td><td class='num'>{fmt_x(i.get('x_max_eod_from_his_entry'))}</td><td class='num'>{fmt_x((i.get('scale') or {}).get('s50'))}</td><td>{reached}</td></tr>")
    return f"""<meta charset="utf-8">
<title>Tito's Best Trades</title>
<style>{BASE_CSS}
 body {{ padding: 24px 28px 50px; }} h1 {{ font-size: 22px; margin: 10px 0 4px; }} .sub {{ color: var(--muted); font-size: 12.5px; margin-bottom: 16px; max-width: 980px; }}
 a.back {{ color: var(--accent); text-decoration: none; font-size: 12.5px; }}
 .wrap {{ overflow-x: auto; }} table {{ border-collapse: collapse; width: 100%; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; font-size: 12.5px; }}
 th, td {{ padding: 7px 10px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }} th {{ color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; }}
 td.num, th.num {{ text-align: right; }} tr:hover td {{ background: #f2f5fb; cursor: pointer; }}
</style>
<a class="back" href="../index.html">&larr; Home</a> &middot; <a class="back" href="../trade_reviews.html">Trade journal</a>
<h1>Tito Adhikary: 20 curated best trades</h1>
<div class="sub">His own list (20/20 winners, so it describes what his winners look like, not a hit rate). Strikes are inferred from the option chains; charts use daily closes only.
"x at expiry" and "best daily close" are measured from HIS entry price; his fills were intraday, usually below the entry-day close. Click a row for the charts.<br><b>Scale-out rule</b> (from the playbook): when the option first triples, sell half to three quarters; trail the rest until the stock closes below its 20 EMA. "Scale-out 50/50" shows what half-and-half would have made, as a multiple of his entry.</div>
<div class="wrap"><table><tr><th>#</th><th>Ticker</th><th>Entry</th><th>Setup</th><th>Catalyst</th><th>Contract (inferred)</th><th class="num">DTE</th><th class="num">Days held</th>
<th class="num">Entry px</th><th class="num">His return</th><th class="num">x at expiry</th><th class="num">Best daily close</th><th class="num">Scale-out 50/50</th><th>His exit first reached at a close</th></tr>
{''.join(rows)}</table></div>
"""


def main() -> int:
    trades = load_trades(); OUT.mkdir(parents=True, exist_ok=True)
    for r in trades[trades.infer_strike.isna()].itertuples():
        k = infer_strike_v3(r.ticker, r.cp, r.expiry, r.entry, float(r.entry_px))
        trades.loc[trades.n == r.n, "infer_strike"] = k
        print(f"  inferred {r.ticker} #{r.n}: strike {k}")
    H = asyncio.run(daily_all(trades)); ds = []
    for r in trades.itertuples():
        op = v3_path(r.ticker, r.cp, float(r.infer_strike), r.expiry, r.entry) if pd.notna(r.infer_strike) else pd.DataFrame()
        d = build(r, H.get(r.n), op); ds.append(d)
        (OUT / f"{int(r.n):02d}_{r.ticker}.html").write_text(trade_page(d))
        i = d["info"]
        print(f"#{i['n']:2d} {i['ticker']:5s} {i['cp']} K={i['strike']} | candles {len(d['und']['candles'])} opt pts {len(d['opt']['line'])} | "
              f"his {i['ret_x']}x | at exp {fmt_x(i.get('x_at_exp_from_his_entry'))} | best close {fmt_x(i.get('x_max_eod_from_his_entry'))} | reached at close: {i.get('reached_eod')}")
    (OUT / "index.html").write_text(index_page(ds))
    print(f"wrote {OUT}/index.html + {len(ds)} trade pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

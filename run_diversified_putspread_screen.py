#!/usr/bin/env python3
"""Diversifying bull-put-spread screen (a TOOL, not a study) -- first built ad hoc 2026-09-28, scripted 2026-09-29.

Finds put-spread candidates OUTSIDE the book's current exposure (tech / AI / semis), live from Tradier:
  1. liquid-panel names in an uptrend: close > rising 50 SMA > 200 SMA, ADDV50 >= $100M, price >= $20
  2. low correlation over the last 60 sessions to SMH and IGV (< 0.40 each); SPY correlation and beta reported
  3. sector not Technology / Communication Services (yfinance), and not already in the book (--exclude)
  4. expiry: the latest listed expiry 17-55 DTE that falls BEFORE the next earnings date, preferring the monthly
     (3rd Friday), nearest 30 DTE
  5. spread: short put |delta| nearest 0.30, long put nearest 0.15 (Tradier greeks); house fills (mid -/+ 25% of the
     bid-ask per leg, $0.0065/share/leg); credit / width = the ranking statistic (it beat IV rank, TEST_INDEX)
  6. tradeable: short-leg bid-ask <= 15% of mid, short-leg OI >= 200, credit / width >= 0.15
Evidence caveats (state them with any output): single-name put spreads are UNCERTIFIED and mostly beta
(stress_put_delta_control, breakout_putspread_vs_stock); calm_weekly_put_panel_2026-09-28 found the premium sits in
names that fall with SPY. This tool buys diversification of the drawdown, not an edge. Quotes are only meaningful in
market hours.

Usage: PYTHONPATH=src .venv/bin/python3 run_diversified_putspread_screen.py --exclude AAPL,MSFT,... [--out path]
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from lib.regime.trailing import Panel

API = "https://api.tradier.com/v1"
ET = ZoneInfo("America/New_York")


def get(path, **q):
    h = {"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"}
    for i in range(4):
        r = requests.get(API + path, params=q, headers=h, timeout=20)
        if r.status_code == 200:
            return r.json()
        time.sleep(1.5 * (i + 1))
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", default="")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    excl = {t.strip().upper() for t in a.exclude.split(",") if t.strip()}
    now = datetime.now(ET); today = pd.Timestamp(now.date())
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); p = Panel.from_long(raw)
    C = p.close; addv = p.dolvol.rolling(50).mean(); s50, s200 = C.rolling(50).mean(), C.rolling(200).mean()
    up = (C.iloc[-1] > s50.iloc[-1]) & (s50.iloc[-1] > s200.iloc[-1]) & (s50.iloc[-1] > s50.iloc[-21]) & (addv.iloc[-1] >= 100e6) & (C.iloc[-1] >= 20)
    cand = [t for t in up[up].index if t not in {"SPY", "QQQ", "IWM", "RSP"} | excl]
    etf = yf.download(["SMH", "IGV", "SPY"], period="6mo", progress=False, auto_adjust=True)["Close"]
    R = C[cand].pct_change().iloc[-60:]; E = etf.pct_change().reindex(R.index)
    corr = pd.DataFrame({"cSMH": R.corrwith(E.SMH), "cIGV": R.corrwith(E.IGV), "cSPY": R.corrwith(E.SPY),
                         "betaSPY": R.apply(lambda c: c.cov(E.SPY) / E.SPY.var())})
    low = corr[(corr.cSMH < 0.40) & (corr.cIGV < 0.40)].index
    print(f"panel as of {C.index[-1].date()} | uptrend+liquid {len(cand)} -> low corr to SMH & IGV {len(low)} | now {now:%H:%M} ET")
    out = []
    for t in low:
        try:
            tk = yf.Ticker(t); info = tk.info
        except Exception:
            continue
        sec = info.get("sector") or "?"
        if sec in ("Technology", "Communication Services", "?"):
            continue
        ed = None
        try:
            cal = tk.calendar
            if isinstance(cal, dict) and cal.get("Earnings Date"):
                ed = pd.Timestamp(cal["Earnings Date"][0])
        except Exception:
            pass
        ex = (get("/markets/options/expirations", symbol=t).get("expirations") or {}).get("date") or []
        ex = [pd.Timestamp(e) for e in (ex if isinstance(ex, list) else [ex])]
        ok = [e for e in ex if 17 <= (e - today).days <= 55 and (ed is None or e < ed)]
        if not ok:
            out.append(dict(t=t, sector=sec, earnings=str(ed.date()) if ed is not None else "?", note="no expiry 17-55 DTE before earnings"))
            continue
        mon = [e for e in ok if 15 <= e.day <= 21 and e.dayofweek == 4]
        e = min(mon or ok, key=lambda x: abs((x - today).days - 30))
        ch = (get("/markets/options/chains", symbol=t, expiration=e.strftime("%Y-%m-%d"), greeks="true").get("options") or {}).get("option") or []
        ch = pd.DataFrame([dict(K=o["strike"], bid=o["bid"], ask=o["ask"], oi=o.get("open_interest", 0), d=(o.get("greeks") or {}).get("delta"))
                           for o in ch if o["option_type"] == "put"])
        if ch.empty:
            continue
        ch = ch.dropna(subset=["d"]); ch = ch[(ch.bid > 0) & (ch.ask > ch.bid)]
        if ch.empty:
            continue
        sh = ch.loc[(ch.d + 0.30).abs().idxmin()]; lg = ch[ch.K < sh.K]
        if lg.empty:
            continue
        lg = lg.loc[(lg.d + 0.15).abs().idxmin()]
        mid = lambda x: (x.bid + x.ask) / 2
        credit = mid(sh) - 0.25 * (sh.ask - sh.bid) - mid(lg) - 0.25 * (lg.ask - lg.bid) - 2 * 0.0065
        w = sh.K - lg.K
        q = (get("/markets/quotes", symbols=t).get("quotes") or {}).get("quote") or {}
        out.append(dict(t=t, sector=sec, industry=(info.get("industry") or "")[:26], px=q.get("last"), expiry=e.date(), dte=(e - today).days,
                        earnings=str(ed.date()) if ed is not None else "?", short=sh.K, long=lg.K, d_s=round(sh.d, 2), d_l=round(lg.d, 2),
                        credit=round(credit, 2), width=w, cw=round(credit / w, 3) if w else np.nan, maxloss=round((w - credit) * 100),
                        oi_s=int(sh.oi), ba_s=round((sh.ask - sh.bid) / mid(sh), 2), cSPY=round(corr.cSPY[t], 2), beta=round(corr.betaSPY[t], 2),
                        cSMH=round(corr.cSMH[t], 2), cIGV=round(corr.cIGV[t], 2), note=""))
        time.sleep(0.2)
    O = pd.DataFrame(out)
    path = a.out or f"data/watchlist/diversified_putspread_screen_{today.date()}.csv"
    O.to_csv(path, index=False)
    P = O[O.note == ""]
    good = P[(P.ba_s <= 0.15) & (P.oi_s >= 200) & (P.credit > 0) & (P.cw >= 0.15)]
    print(f"priced {len(P)} | tradeable (short-leg bid-ask <= 15% of mid, OI >= 200, credit/width >= 0.15): {len(good)} | csv {path}")
    cols = ["t", "sector", "industry", "px", "expiry", "dte", "earnings", "short", "long", "d_s", "credit", "width", "cw", "maxloss",
            "oi_s", "ba_s", "cSPY", "beta", "cSMH", "cIGV"]
    print(good.sort_values(["sector", "cw"], ascending=[True, False])[cols].to_string(index=False))


if __name__ == "__main__":
    main()

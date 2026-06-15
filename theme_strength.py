"""Theme / industry-group relative-strength scorer (the quantitative 'narrative' spine).

Ranks the themes spanning the watchlist by their representative ETF's RS vs SPY
(or, for themes with no clean ETF, the median RS of their members), then emits a
per-ticker tilt + size multiplier the breakout monitor can consume.

RS = stock/ETF % change minus SPY % change. Theme score weights recent momentum
more (0.6*1-month + 0.4*3-month) because 'rising fast NOW' is the narrative we want.

Run:  PYTHONPATH=src .venv/bin/python3 theme_strength.py
Writes: data/theme_scores.json  (ticker -> {theme, theme_rs, size_mult, priority_mult})
"""
import os, json, asyncio
from datetime import date, timedelta
import numpy as np
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
K_PRIORITY = 2.0      # priority_mult = 1 + K*theme_rs   (heavy tilt)
SIZE_K = 1.5          # size_mult = clip(1 + SIZE_K*theme_rs, 0.5, 1.6)

# news overlay (manual, refresh when the macro story changes): theme -> (news_mult, catalyst)
# captures event narrative price hasn't fully reflected; reconciles with group RS below.
NEWS_OVERLAY = {
    "Semis/AI-cap":   (1.15, "AI capex = defining 2026 theme; TSMC capex up; memory upcycle; ceasefire risk-on"),
    "Optical/Network":(1.07, "AI-infra adjacent (rides capex)"),
    "DataCtr-Power":  (1.10, "AI power-buildout narrative intact though price consolidating (RS/news diverge)"),
    "Financials":     (1.05, "risk-on tailwind from ceasefire"),
    "Cybersecurity":  (1.10, "AI-driven security spend cycle; durable dual-timeframe RS"),
    "Airlines":       (1.10, "ceasefire->cheap jet fuel tailwind (flip side of energy headwind)"),
    "Energy":         (0.85, "HEADWIND: ceasefire->oil down/Hormuz reopen; FLIPS to tailwind if truce breaks"),
    "Staples/Food":   (0.97, "risk-on rotates out of defensives"),
    "Healthcare":     (1.00, ""),
    "Industrials":    (1.00, ""),
    "Retail/Luxury":  (1.00, ""),
    "Homebuilders":   (1.00, ""),
}

# theme -> (representative ETF or None for basket, [member tickers])
THEMES = {
    "Semis/AI-cap":   ("SMH", ["AMKR","ONTO","AMAT","INTC","UCTT","AMD","ADI","AEHR","SKYT","KEYS"]),
    "Optical/Network":(None,  ["LITE","VIAV","AAOI"]),
    "DataCtr-Power":  (None,  ["VRT","GEV","NVT"]),
    "Financials":     ("XLF", ["STT","C","FITB","KEY","IBKR","MS","BNY","RY","TD","BEN","HOOD"]),
    "Cybersecurity":  ("CIBR",["FTNT","CRWD","PANW","ZS","NET","S","OKTA","TENB"]),
    "Airlines":       ("JETS",["DAL","UAL","AAL","LUV"]),
    "Energy":         ("XLE", ["SLB","VLO","MPC","DINO"]),
    "Industrials":    ("XLI", ["CAT","CMI","GWW","JBHT","FIX","FLS","CP"]),
    "Healthcare":     ("XLV", ["RVMD","RPRX","CVS"]),
    "Staples/Food":   ("XLP", ["MNST","MDLZ","BG","ARMK"]),
    "Homebuilders":   ("XHB", ["LEN","BLD"]),
    "Retail/Luxury":  ("XRT", ["TPR"]),
}

def perf(c, n):
    return np.nan if c is None or len(c) <= n else c.iloc[-1]/c.iloc[-n-1]-1

async def fetch(t, tk, start, end):
    try:
        df = await get_daily_history(tk, start, end, client=t)
        return tk, (df["close"].astype(float) if df is not None and len(df) >= 70 else None)
    except Exception:
        return tk, None

async def main():
    end = date.today(); start = end - timedelta(days=200)
    need = set(["SPY"])
    for etf, members in THEMES.values():
        if etf: need.add(etf)
        need.update(members)
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        res = dict(await asyncio.gather(*[fetch(t, tk, start, end) for tk in need]))
    spy = res.get("SPY")
    spy21, spy63 = perf(spy, 21), perf(spy, 63)

    def rs(c):
        return (0.6*((perf(c,21)-spy21)) + 0.4*((perf(c,63)-spy63))) if c is not None else np.nan

    scored = []
    for theme, (etf, members) in THEMES.items():
        if etf and res.get(etf) is not None:
            r = rs(res[etf]); basis = f"ETF {etf}"
        else:
            member_rs = [rs(res[m]) for m in members if res.get(m) is not None]
            r = float(np.nanmedian(member_rs)) if member_rs else np.nan
            basis = "basket median"
        nm, cat = NEWS_OVERLAY.get(theme, (1.0, ""))
        prio = (1 + K_PRIORITY*r) * nm if not np.isnan(r) else np.nan
        size = float(np.clip((1 + SIZE_K*r) * nm, 0.5, 1.7)) if not np.isnan(r) else np.nan
        scored.append((theme, r, prio, size, nm, cat, basis, members))
    scored.sort(key=lambda x: (-(x[2] if not np.isnan(x[2]) else -9)))   # rank by final priority

    print(f"SPY ref: 1m {spy21*100:+.1f}%  3m {spy63*100:+.1f}%\n")
    print(f"{'#':>2} {'THEME':16} {'RS':>7} {'news':>5} {'prio_x':>7} {'size_x':>7}  catalyst / basis")
    out = {}
    for i, (theme, r, prio, size, nm, cat, basis, members) in enumerate(scored, 1):
        if np.isnan(r):
            print(f"{i:>2} {theme:16} {'n/a':>7}"); continue
        flag = "HOT" if prio >= 1.20 else ("cold" if prio <= 0.95 else "")
        info = cat if cat else basis
        print(f"{i:>2} {theme:16} {r*100:+6.1f}% {nm:5.2f} {prio:7.2f} {size:7.2f}  [{flag}] {info}")
        for m in members:
            out[m] = {"theme": theme, "theme_rs": round(r,4),
                      "priority_mult": round(prio,3), "size_mult": round(size,3),
                      "rank": i, "catalyst": cat}

    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "theme_scores.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nWrote {len(out)} ticker tags -> {path}")

asyncio.run(main())

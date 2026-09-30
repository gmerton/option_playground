#!/usr/bin/env python3
"""House breakout (long, BB-3) and mirror breakdown (short) on 31 sector/industry ETFs (2026-09-29).
PRE-REGISTERED: data/studies/etf_breakouts_breakdowns_2026-09-29.md (committed b15f8d6 before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_etf_breakouts_breakdowns.py  (harness detail -> data/studies/logs/etf_bb.log)
"""
import sys

import numpy as np
import pandas as pd
import yfinance as yf

from lib.studies import pattern_test as pt
from run_haber_setups import refire_filter

ETFS = ["ARKK", "CIBR", "GDX", "IGV", "IHI", "ITB", "IYT", "JETS", "KIE", "KRE", "KWEB", "OIH", "SMH", "TAN", "URA", "XAR",
        "XBI", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY", "XME", "XOP", "XRT"]
SINCE, UNTIL, SPLIT, BAR = "2010-01-01", "2026-06-30", "2018-01-01", 3.2
CACHE = pt.REPO / "data/cache/group_etf_ohlcv.parquet"
LOG = pt.REPO / "data/studies/logs/etf_bb.log"
SUMMARY = pt.REPO / "data/studies/etf_breakouts_breakdowns_2026-09-29.log"


def panel():
    if not CACHE.exists():
        d = yf.download(ETFS, start="2008-01-01", end="2026-09-30", auto_adjust=True, progress=False, group_by="ticker")
        rows = []
        for t in ETFS:
            x = d[t].dropna(subset=["Close"]).reset_index().rename(columns=str.lower)
            x["ticker"] = t; rows.append(x[["date", "ticker", "open", "high", "low", "close", "volume"]])
        pd.concat(rows).to_parquet(CACHE, index=False)
    r = pd.read_parquet(CACHE)
    pv = lambda c: r.pivot(index="date", columns="ticker", values=c).sort_index()
    O, H, L, C, V = (pv(c) for c in ("open", "high", "low", "close", "volume"))
    P = pt.DailyPanel(open=O, high=H, low=L, close=C, adr=(H / L - 1).shift(1).rolling(20).mean() * 100,
                      elig=C.notna(), ema20=C.ewm(span=20, adjust=False).mean())
    return P, V


def signals(P, V):
    C, H, L = P.close, P.high, P.low
    s10, s20, s50 = (C.rolling(n).mean() for n in (10, 20, 50))
    rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan)
    hi20, lo20 = H.shift(1).rolling(20).max(), L.shift(1).rolling(20).min()
    win = (C.index >= SINCE) & (C.index <= UNTIL)
    lng = (C > hi20) & ~(C.shift(1) > hi20.shift(1)) & (rvol >= 1.1) & (pos >= 0.5) & (s10 > s20) & (s20 > s50)
    sht = (C < lo20) & ~(C.shift(1) < lo20.shift(1)) & (rvol >= 1.1) & (pos <= 0.5) & (s10 < s20) & (s20 < s50)
    out = {}
    for k, m, stop in (("LONG breakout", lng, np.minimum(L, C * 0.98)), ("SHORT breakdown", sht, np.maximum(H, C * 1.02))):
        mv = m.fillna(False).values.copy(); mv[~win] = False
        out[k] = (pd.DataFrame(refire_filter(mv, 10), index=C.index, columns=C.columns), stop)
    return out


def main():
    P, V = panel()
    rows = []
    for k, (hit, stop) in signals(P, V).items():
        side = "long" if k.startswith("LONG") else "short"
        for ctrl in ("xname", "post"):
            fn = lambda _P, h=hit, s=stop, sd=side: pt.daily_signals(h, stop=s, side=sd, since=SINCE)
            tab = pt.run_daily(f"ETF {k} [{ctrl}]", fn, hold=60, panel=P, entry_at="close", control=ctrl, split=SPLIT,
                               ledger=(ctrl == "xname"), note="pre-registered 2026-09-29 (b15f8d6)")
            a = tab.attrs["arms"]["ema20"]
            T = pd.read_parquet(pt.REPO / f"data/cache/pattern_etf_{k.replace(' ', '_').lower()}_[{ctrl}]_daily.parquet")
            rows.append(dict(setup=k, control=ctrl, n=int(tab.loc["ema20", "n"]), etfs=T.sym.nunique(), meanR=tab.loc["ema20", "meanR"],
                             paired_edge=a["pedge"], t=a["edge_t"], h1=a["eh1"], h2=a["eh2"], p_search=tab.attrs.get("p_search")))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        R = main()
    finally:
        sys.stdout.close(); sys.stdout = real
    lines = ["# ETF breakout (long) / breakdown (short), arm ema20 (pre-registration in the md)", R.round(3).to_string(index=False)]
    for k in ("LONG breakout", "SHORT breakdown"):
        r = R[(R.setup == k) & (R.control == "xname")].iloc[0]
        ok = r.paired_edge > 0 and r.t >= BAR and r.h1 > 0 and r.h2 > 0 and (r.meanR > 0 if k.startswith("SHORT") else True)
        lines.append(f"PASS {k}: {'YES' if ok else 'no'}")
    SUMMARY.write_text("\n".join(lines) + "\n"); print("\n".join(lines))

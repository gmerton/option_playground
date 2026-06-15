"""Broad industry/thematic RS scan vs SPY -- find the leaders regardless of watchlist."""
import os, asyncio
from datetime import date, timedelta
import numpy as np
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")

# ETF -> industry label (broad coverage incl. thematics not in the watchlist)
ETFS = {
    "SMH":"Semiconductors","SOXX":"Semiconductors(alt)","IGV":"Software","WCLD":"Cloud SW",
    "CIBR":"Cybersecurity","SKYY":"Cloud","BOTZ":"Robotics/AI","ARKQ":"Autonomous/Robotics",
    "QTUM":"Quantum/Tech","FDN":"Internet","XLK":"Tech(sector)","XLC":"Comm Svcs",
    "XBI":"Biotech","IBB":"Biotech(lg)","IHI":"Medical Devices","PPH":"Pharma",
    "XLV":"Healthcare","KRE":"Regional Banks","KBE":"Banks","IAI":"Broker/Cap Mkts",
    "KIE":"Insurance","XLF":"Financials","ITA":"Aero & Defense","PPA":"Aero & Defense(alt)",
    "XAR":"Aerospace","JETS":"Airlines","IYT":"Transports","PAVE":"Infrastructure",
    "XLI":"Industrials","XHB":"Homebuilders","ITB":"Homebuilders(alt)","XME":"Metals & Mining",
    "GDX":"Gold Miners","GDXJ":"Jr Gold Miners","SIL":"Silver Miners","COPX":"Copper Miners",
    "SLX":"Steel","URA":"Uranium","URNM":"Uranium(pure)","NLR":"Nuclear","LIT":"Lithium/Battery",
    "TAN":"Solar","ICLN":"Clean Energy","XLE":"Energy","XOP":"Oil&Gas E&P","OIH":"Oil Services",
    "XLU":"Utilities","XLB":"Materials","XLP":"Staples","XLY":"Consumer Disc","XRT":"Retail",
    "KWEB":"China Internet","BLOK":"Blockchain","FINX":"Fintech","ARKG":"Genomics",
    "REMX":"Rare Earth/Strat Metals","PHO":"Water","SEA":"Shipping","AMLP":"MLP/Midstream",
}

def perf(c, n): return np.nan if c is None or len(c) <= n else c.iloc[-1]/c.iloc[-n-1]-1

async def fetch(t, tk, start, end):
    try:
        df = await get_daily_history(tk, start, end, client=t)
        return tk, (df["close"].astype(float) if df is not None and len(df) >= 70 else None)
    except Exception:
        return tk, None

async def main():
    end = date.today(); start = end - timedelta(days=200)
    need = list(ETFS) + ["SPY"]
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        sem = asyncio.Semaphore(10)
        async def bound(tk):
            async with sem: return await fetch(t, tk, start, end)
        res = dict(await asyncio.gather(*[bound(tk) for tk in need]))
    spy = res.get("SPY"); spy21, spy63 = perf(spy,21), perf(spy,63)
    rows = []
    for etf, label in ETFS.items():
        c = res.get(etf)
        if c is None: continue
        rs1 = perf(c,21)-spy21; rs3 = perf(c,63)-spy63
        rs = 0.6*rs1 + 0.4*rs3
        rows.append((etf, label, rs, rs1, rs3, (c.iloc[-1]/c.tail(252).max()-1)))
    rows.sort(key=lambda x: -x[2])
    print(f"SPY: 1m {spy21*100:+.1f}%  3m {spy63*100:+.1f}%   (RS = 0.6*1m + 0.4*3m vs SPY)\n")
    print(f"{'#':>2} {'ETF':6} {'Industry':22} {'RS':>7} {'1m':>7} {'3m':>7} {'fromHi':>7}")
    for i,(etf,label,rs,rs1,rs3,fh) in enumerate(rows,1):
        flag = "  <<" if i<=5 else ""
        print(f"{i:>2} {etf:6} {label:22} {rs*100:+6.1f}% {rs1*100:+6.1f}% {rs3*100:+6.1f}% {fh*100:+6.1f}%{flag}")

asyncio.run(main())

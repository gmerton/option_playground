"""Full evaluation (grade + triggers) for tickers passed as argv. Tradier data."""
import os, asyncio, sys
from datetime import date, timedelta
import numpy as np
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TICKERS = [t.upper() for t in sys.argv[1:]] or ["MS", "ARMK", "RPRX"]

def sma(s, n): return s.rolling(n).mean().iloc[-1] if len(s) >= n else np.nan
def perf(c, n): return np.nan if len(c) <= n else c.iloc[-1]/c.iloc[-n-1]-1

async def fetch(t, tk, start, end):
    try:
        df = await get_daily_history(tk, start, end, client=t)
        return tk, (df if df is not None and len(df) >= 60 else None)
    except Exception:
        return tk, None

async def main():
    end = date.today(); start = end - timedelta(days=430)
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        _, spy = await fetch(t, "SPY", start, end)
        spyc = spy["close"] if spy is not None else None
        res = await asyncio.gather(*[fetch(t, tk, start, end) for tk in TICKERS])
    rows = []
    for tk, df in res:
        if df is None:
            rows.append({"ticker": tk, "note": "NO DATA"}); continue
        c=df["close"].astype(float); h=df["high"].astype(float)
        l=df["low"].astype(float); v=df["volume"].astype(float)
        spot=c.iloc[-1]; s50,s150,s200=sma(c,50),sma(c,150),sma(c,200)
        s200p = c.rolling(200).mean().iloc[-22] if len(c)>=222 else np.nan
        hi52=c.tail(252).max(); lo52=c.tail(252).min()
        rules=[spot>s150 and spot>s200, s150>s200,
               (not np.isnan(s200p)) and s200>s200p, s50>s150 and s50>s200,
               spot>s50, spot>=1.3*lo52, spot>=0.75*hi52]
        npass=sum(bool(x) for x in rules)
        adr=((h-l)/c).tail(20).mean()*100
        ema10=c.ewm(span=10).mean().iloc[-1]; ema20=c.ewm(span=20).mean().iloc[-1]
        h5,h10,h20=h.tail(5).max(),h.tail(10).max(),h.tail(20).max()
        l10=l.tail(10).min()
        rng10=h.tail(10).max()/l.tail(10).min()-1
        rng20=h.tail(20).max()/l.tail(20).min()-1
        pivot=h20  # breakout level
        stop=ema20
        rows.append(dict(ticker=tk, spot=spot, n_pass=npass,
            from_high=(spot/hi52-1)*100, rs3m=(perf(c,63)-(perf(spyc,63) if spyc is not None else 0))*100,
            rs6m=(perf(c,126)-(perf(spyc,126) if spyc is not None else 0))*100,
            p1m=perf(c,21)*100, adr=adr, ext10=(spot/ema10-1)*100,
            rng10=rng10*100, rng20=rng20*100,
            pivot=pivot, early=h5, stop=stop, hard=l10,
            risk=(pivot-stop)/pivot*100, to_go=(pivot/spot-1)*100,
            volx=v.iloc[-1]/v.tail(50).mean()))
    out=pd.DataFrame(rows)
    pd.set_option("display.width",240,"display.max_columns",40)
    cols=["ticker","spot","n_pass","from_high","rs3m","rs6m","p1m","adr","ext10",
          "rng10","rng20","pivot","early","to_go","stop","risk","hard"]
    cols=[x for x in cols if x in out.columns]
    print(out[cols].to_string(index=False, float_format=lambda x:f"{x:8.2f}"))

asyncio.run(main())

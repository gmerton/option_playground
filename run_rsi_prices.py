# Pull adjusted daily closes for every underlying in the two trade sets + SPY/QQQ full history.
import pandas as pd, yfinance as yf
SP="data/cache/"
R=pd.read_parquet("data/cache/etf_condor_recon.parquet")
L=pd.read_parquet("data/cache/straddle_recenter/leg_decomp.parquet")
tick=sorted(set(R.ticker)|set(L[L.pass_both].ticker)|{"SPY","QQQ"})
px=yf.download(tick, start="1993-01-01", end="2026-09-17", auto_adjust=True, progress=False, group_by="column", threads=True)
c=px["Close"]; c.index=pd.to_datetime(c.index).tz_localize(None)
c.to_parquet(SP+"rsi_closes.parquet")
miss=[t for t in tick if t not in c or c[t].dropna().empty]
print(c.shape, "missing:", miss)

"""Pull adjusted daily OHLCV (yfinance) for every ticker in data/top_gainers/*.csv, 2019-01-01 -> today.
Output: data/cache/top_gainers_daily.parquet (date, ticker, open, high, low, close, volume).
Feeds the descriptive leader chart study (top_gainers_chart_study_2026-11-17.md)."""
import glob, pandas as pd, yfinance as yf
t = sorted({x for f in glob.glob('data/top_gainers/*.csv') for x in pd.read_csv(f).ticker})
yt = {x: x.replace('.', '-') for x in t}          # MOG.A -> MOG-A
raw = yf.download(list(yt.values()), start='2019-01-01', auto_adjust=True, group_by='ticker', threads=True, progress=False)
rows = []
for x, y in yt.items():
    if y not in raw.columns.get_level_values(0): continue
    d = raw[y].dropna(subset=['Close']).reset_index()
    if d.empty: continue
    d.columns = [c.lower() for c in d.columns]; d['ticker'] = x
    rows.append(d[['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']])
out = pd.concat(rows); out.to_parquet('data/cache/top_gainers_daily.parquet', index=False)
print(len(t), 'tickers;', out.ticker.nunique(), 'with data;', out.date.min().date(), '->', out.date.max().date())
print('missing:', sorted(set(t) - set(out.ticker)))

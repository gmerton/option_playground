import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from math import sqrt
from lib.regime.trailing import Panel, liquidity_mask
raw=pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw=raw[~raw.ticker.isin(["SPY","QQQ","IWM","RSP"])]
p=Panel.from_long(raw); C,H,L=p.close,p.high,p.low
elig=liquidity_mask(p,addv_min=50e6,px_min=5.0)&~p.suspect()
e9=C.ewm(span=9,adjust=False).mean(); e21=C.ewm(span=21,adjust=False).mean()
adr=(H/L-1).rolling(20).mean()*100; hi52=H.rolling(252,min_periods=120).max()
A40=(C>e21).rolling(40).mean(); S21=(e21/e21.shift(10)-1)*100/adr; ext=(C/e21-1)*100/adr
off=(C/hi52-1)*100
f20=C.shift(-20)/C-1; f60=C.shift(-60)/C-1
dates=C.index[C.index>='2019-10-01'][::20]
rows=[]
for d in dates:
    m=elig.loc[d]
    df=pd.DataFrame(dict(a40=A40.loc[d],s21=S21.loc[d],ext=ext.loc[d],off=off.loc[d],adr=adr.loc[d],f20=f20.loc[d],f60=f60.loc[d]))[m].dropna(subset=['a40','s21','off','f20'])
    if len(df)<200: continue
    df['f20x']=df.f20-df.f20.mean(); df['f60x']=df.f60-df.f60.mean(); df['date']=d; rows.append(df)
X=pd.concat(rows)
lead=X[(X.off>-15)&(X.adr>=3)]
print("leaders (within 15% of 52wk high, ADR>=3):",len(lead),"obs,",lead.date.nunique(),"dates")
def bucket(df,col,edges,y):
    df=df.assign(b=pd.cut(df[col],edges)); t=df.groupby(['date','b'])[y].mean().unstack()
    return t
for col,edges in (('a40',[0,0.6,0.8,0.9,0.95,1.01]),('s21',[-9,0,0.25,0.5,1.0,9])):
    for y in ('f20x','f60x'):
        t=bucket(lead,col,edges,y); n=lead.assign(b=pd.cut(lead[col],edges)).b.value_counts().sort_index()
        top,bot=t.columns[-1],t.columns[0]; sp=(t[top]-t[bot]).dropna()
        print(f"  {col} {y}: "+"  ".join(f"{str(c)}:{t[c].mean()*100:+.2f}(n{n[c]})" for c in t.columns)+f" | top-bottom {sp.mean()*100:+.2f}pp t {sp.mean()/(sp.std(ddof=1)/sqrt(len(sp))):+.2f}")
# the DINO profile: a40>=0.9, slope>0, within 1 ADR of 21 EMA (a breather in a smooth trend) vs other leaders
prof=(lead.a40>=0.9)&(lead.s21>0)&(lead.ext.between(-0.5,1.0))
for y in ('f20x','f60x'):
    a=lead[prof].groupby('date')[y].mean(); b=lead[~prof].groupby('date')[y].mean(); d=(a-b).dropna()
    h1=d[d.index<'2023-01-01']; h2=d[d.index>='2023-01-01']
    print(f"DINO profile vs other leaders {y}: {a.mean()*100:+.2f} vs {b.mean()*100:+.2f} | diff {d.mean()*100:+.2f}pp t {d.mean()/(d.std(ddof=1)/sqrt(len(d))):+.2f} | halves {h1.mean()*100:+.2f}/{h2.mean()*100:+.2f} | n {prof.sum()}")

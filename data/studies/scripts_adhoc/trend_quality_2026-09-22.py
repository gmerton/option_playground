import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from math import sqrt
from lib.regime.trailing import Panel, liquidity_mask
raw=pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw=raw[~raw.ticker.isin(["SPY","QQQ","IWM","RSP"])]
p=Panel.from_long(raw); C,H,L=p.close,p.high,p.low
elig=liquidity_mask(p,addv_min=50e6,px_min=5.0)&~p.suspect()
e9=C.ewm(span=9,adjust=False).mean(); e21=C.ewm(span=21,adjust=False).mean()
adr=(H/L-1).rolling(20).mean()*100
f=pd.DataFrame()
feat={
 'above21_40':(C>e21).rolling(40).mean(),                      # share of last 40 closes above the 21 EMA
 'above9_40':(C>e9).rolling(40).mean(),
 'slope21':(e21/e21.shift(10)-1)*100/adr,                      # 10-session 21 EMA slope in ADR units
 'slope9':(e9/e9.shift(5)-1)*100/adr,
 'mom60':C/C.shift(60)-1,                                      # plain momentum (control)
 'mom20':C/C.shift(20)-1,
 'ext21':(C/e21-1)*100/adr,
}
fwd20=C.shift(-20)/C-1; fwd60=C.shift(-60)/C-1
dates=C.index[(C.index>='2019-10-01')][::20]                   # non-overlapping 20d steps
rows=[]
for d in dates:
    m=elig.loc[d]&(C.loc[d]>0)
    df=pd.DataFrame({k:v.loc[d] for k,v in feat.items()})[m].dropna()
    df['f20']=fwd20.loc[d]; df['f60']=fwd60.loc[d]
    df=df.dropna(subset=['f20'])
    if len(df)<200: continue
    df['f20x']=df.f20-df.f20.mean(); df['f60x']=df.f60-df.f60.mean()
    df['date']=d; rows.append(df)
X=pd.concat(rows); print("dates",X.date.nunique(),"obs",len(X), X.date.min().date(), X.date.max().date())
def fm_quint(col,y='f20x'):
    q=X.groupby('date')[col].transform(lambda s:pd.qcut(s.rank(method='first'),5,labels=False))
    t=X.assign(q=q).groupby(['date','q'])[y].mean().unstack()
    spread=(t[4]-t[0]); return (t.mean()*100).round(2).tolist(), spread.mean()*100, spread.mean()/(spread.std(ddof=1)/sqrt(len(spread)))
print("\n20d forward return in excess of the cross-section, by quintile (Q1 low .. Q5 high), Fama-MacBeth over non-overlapping dates")
for c in feat:
    qs,sp,t=fm_quint(c); print(f"  {c:11} {qs}  Q5-Q1 {sp:+.2f}pp t {t:+.2f}")
# does trend smoothness add beyond plain momentum? cross-sectional regression each date on ranks
import statsmodels.api as sm
def fm_reg(cols,y='f20x'):
    B=[]
    for d,g in X.groupby('date'):
        Z=g[cols].rank(pct=True)-0.5; Z=sm.add_constant(Z); B.append(sm.OLS(g[y],Z).fit().params[cols])
    B=pd.DataFrame(B); return (B.mean()*100).round(3), (B.mean()/(B.std(ddof=1)/np.sqrt(len(B)))).round(2)
for cols in (['mom60'],['mom60','above21_40'],['mom60','above21_40','slope21','ext21'],['mom60','slope21']):
    b,t=fm_reg(cols); print("  FM reg (rank, pp per full rank range):",dict(zip(cols,zip(b,t))))
print("\n60d forward (overlapping less a concern at 20d steps, t inflated ~):")
for c in ['above21_40','slope21','mom60']:
    qs,sp,t=fm_quint(c,'f60x'); print(f"  {c:11} {qs}  Q5-Q1 {sp:+.2f}pp t~{t:+.2f}")
# halves for the key one
for lab,sub in (('<2023',X[X.date<'2023-01-01']),('>=2023',X[X.date>='2023-01-01'])):
    q=sub.groupby('date')['above21_40'].transform(lambda s:pd.qcut(s.rank(method='first'),5,labels=False))
    t=sub.assign(q=q).groupby(['date','q']).f20x.mean().unstack(); sp=t[4]-t[0]
    print(f"  above21_40 Q5-Q1 {lab}: {sp.mean()*100:+.2f}pp t {sp.mean()/(sp.std(ddof=1)/sqrt(len(sp))):+.2f}")
X.to_parquet("/private/tmp/claude-501/-Users-gmerton-v2-options-playground/3a3e8e39-6b8b-4522-a50b-00737d5d836a/scratchpad/tq.parquet")

#!/usr/bin/env python3
"""ORB9 stop-floor study (2026-09-21): re-score every cached ORB9 alert with the stop floored at k ADR under the entry.
Reads logs/alert_study_scores.csv + cached 1-min bars + alert_ctx_v7. Writes data/studies/orb9_stop_floor.csv.
Run: PYTHONPATH=src .venv/bin/python3 run_orb9_stop_floor_study.py"""
import pandas as pd, numpy as np, os
from functools import lru_cache
B='data/cache/intraday_1min'
d=pd.read_csv('data/watchlist/logs/alert_study_scores.csv')
o=d[(d.kind=='ORB9')&d.R.notna()].drop_duplicates(['date','t','sym']).copy()
ctl=set(l.split()[0] for l in open('data/watchlist/universe_study_extra.txt') if l.strip() and not l.startswith('#'))
@lru_cache(None)
def ctx(dt):
    f=f'data/cache/alert_ctx_v7_{dt}.parquet'
    return pd.read_parquet(f).set_index('symbol') if os.path.exists(f) else None
rows=[]
for r in o.itertuples():
    c=ctx(r.date); f=f'{B}/{r.sym}_{r.date}.parquet'
    if c is None or r.sym not in c.index or not os.path.exists(f): continue
    adr=c.loc[r.sym,'adr_pct']; ds=c.loc[r.sym,'day_state']
    if not adr or adr!=adr: continue
    m=pd.read_parquet(f); hm=m.index.strftime('%H:%M'); m=m[(hm>='09:30')&(hm<'16:00')]; hm=m.index.strftime('%H:%M')
    orh=m[hm<'09:45'].high.max(); seg=m[hm>r.t]
    if seg.empty: continue
    a=r.px*adr/100
    stops={'base':r.stop}
    for k in (0.25,0.4,0.6,1.0): stops[f'floor{k}']=min(r.stop, r.px-k*a)
    stops['orh-0.1']=min(r.stop, orh-0.1*a)
    out=dict(date=r.date,sym=r.sym,t=r.t,ds=ds,ctl=r.sym in ctl,dist_adr=(r.px-r.stop)/a)
    close=seg.close.iloc[-1]
    for n,s in stops.items():
        risk=r.px-s
        if risk<=0: out[n]=np.nan; continue
        hit=seg[seg.low<=s]
        out[n]=-1.0 if len(hit) else (close-r.px)/risk
        out[n+'_pct']=(-risk if len(hit) else close-r.px)/r.px*100
        out[n+'_st']=len(hit)>0
    rows.append(out)
X=pd.DataFrame(rows); X.to_csv('data/studies/orb9_stop_floor.csv',index=False)
days=sorted(X.date.unique()); X['half']=np.where(X.date.isin(days[:len(days)//2]),'A','B')
X['noise']=X.dist_adr<0.4
V=['base','floor0.25','floor0.4','floor0.6','floor1.0','orh-0.1']
def tab(g):
    r={}
    for v in V:
        x=g[v].dropna(); r[v]=f"{x.mean():+.2f}R t{x.mean()/(x.std()/np.sqrt(len(x))):.1f} st{100*g[v+'_st'].mean():.0f}%"
    return pd.Series(r)
print('n',len(X),'  median base stop %.2f ADR; share <0.4 ADR %.0f%%'%(X.dist_adr.median(),100*X.noise.mean()))
pd.set_option('display.width',250)
for name,g in [('all',X),('curated',X[~X.ctl]),('control',X[X.ctl]),('curated half A',X[~X.ctl&(X.half=='A')]),('curated half B',X[~X.ctl&(X.half=='B')]),
               ('control half A',X[X.ctl&(X.half=='A')]),('control half B',X[X.ctl&(X.half=='B')]),
               ('curated noise (<0.4 ADR)',X[~X.ctl&X.noise]),('curated not noise',X[~X.ctl&~X.noise]),('control noise',X[X.ctl&X.noise]),
               ('curated dayLONG/FLAT',X[~X.ctl&X.ds.isin(['LONG','FLAT'])])]:
    print(f'\n{name}  n={len(g)}'); print(tab(g).to_string())

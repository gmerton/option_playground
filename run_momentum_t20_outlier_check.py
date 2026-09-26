import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
import run_momentum_portfolio as M, run_dip_survivorship as DS
C,V=DS.adjust_and_clean(DS.pull()); liq=((V.rolling(50,min_periods=30).mean()>=1000)&(C>=5)).fillna(False)
idx=C.index; Cv=C.values; E=liq.values
lv=np.array([np.flatnonzero(np.isfinite(Cv[:,j])).max() if np.isfinite(Cv[:,j]).any() else -1 for j in range(Cv.shape[1])])
me=[i for i in M.month_ends(idx) if pd.Timestamp(M.START)<=idx[i]<=pd.Timestamp(M.END)]
rows=[]
for a,b in zip(me[:-1],me[1:]):
    s=Cv[a-21]/Cv[a-252]-1; ok=E[a]&np.isfinite(s)&np.isfinite(Cv[a]); n=np.flatnonzero(ok)
    if len(n)<50: continue
    o=n[np.argsort(-s[n])][:20]; ex=np.minimum(b,lv[n]); r=pd.Series(Cv[ex,n]/Cv[a,n]-1,index=n)
    ew=r.mean()
    for j in o: rows.append(dict(m=idx[b].to_period("M"),t=C.columns[j],score=s[j],r=r[j],ew=ew,delist=lv[j]<b))
T=pd.DataFrame(rows); T["x"]=T.r-T.ew
print("name-months",len(T),"delisted inside month",T.delist.sum(), "median score",T.score.median().round(2))
print("top 10 contributions:\n",T.nlargest(10,"x")[["m","t","score","r"]].round(2).to_string(index=False))
for q in (0.99,0.98,0.95):
    c=T.x.quantile(q); t=T.assign(x=T.x.clip(upper=c)).groupby("m").x.mean()*100
    print(f"winsorised at p{int(q*100)} ({c:+.2f}): excess {t.mean():+.2f}pp t_NW {M.nw_t(t):+.2f}")
g=T.groupby("t").x.sum().sort_values(ascending=False); print("names:",T.t.nunique(),"| top 5 names share of total excess:", round(g.head(5).sum()/T.x.sum(),2), g.head(5).round(2).to_dict())

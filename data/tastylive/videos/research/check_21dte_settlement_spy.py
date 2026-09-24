import pandas as pd, numpy as np
from lib.mysql_lib import _get_engine
import run_21dte_exit_test as R
eng=_get_engine()
ent=pd.read_sql("""SELECT trade_date,expiry,cp,strike,bid,ask,delta FROM options_cache
 WHERE ticker='SPY' AND trade_date BETWEEN '2018-01-01' AND '2026-02-20' AND DAYOFWEEK(trade_date)=6
 AND DATEDIFF(expiry,trade_date) BETWEEN 40 AND 50 AND ABS(delta) BETWEEN 0.10 AND 0.30""",eng)
fin=pd.read_sql("""SELECT trade_date,expiry,cp,strike,bid,ask,last,mid FROM options_cache
 WHERE ticker='SPY' AND trade_date=expiry AND trade_date BETWEEN '2018-02-01' AND '2026-04-30'""",eng)
print(len(ent),len(fin),flush=True)
for c in ["trade_date","expiry"]:
    ent[c]=pd.to_datetime(ent[c]); fin[c]=pd.to_datetime(fin[c])
ent=ent[(ent.bid>0)&(ent.ask>0)]; ent["dte"]=(ent.expiry-ent.trade_date).dt.days
fk=fin.set_index(["expiry","cp","strike"]).sort_index()
out=[]
for d,day in ent.groupby("trade_date"):
    exp=day.iloc[(day.dte-45).abs().argsort()[:1]].expiry.iloc[0]
    ch=day[day.expiry==exp]
    sp=R.pick(ch[ch.cp=="P"],0.2); sc=R.pick(ch[ch.cp=="C"],0.2)
    if sp is None or sc is None: continue
    credit=sp.bid+sc.bid-2*R.COMM
    rows=[]
    for cp,k in (("P",sp.strike),("C",sc.strike)):
        try: rows.append(fk.loc[(exp,cp,k)])
        except KeyError: pass
    r=pd.DataFrame(rows) if rows else pd.DataFrame()
    q=r[(r.bid>0)&(r.ask>0)] if len(r) else r
    out.append(dict(entry=d,exp=exp,credit=credit,raw_n=len(r),kept=len(q)>0,
       cost_raw=float(r["last"].fillna(r["mid"]).clip(lower=0).sum()) if len(r) else np.nan,
       cost_kept=float(q["last"].fillna(q["mid"]).clip(lower=0).sum()) if len(q) else np.nan))
o=pd.DataFrame(out)
print("entries",len(o),"kept (study convention)",o.kept.sum(),"dropped",(~o.kept).sum(),"of which raw expiry rows exist",((~o.kept)&(o.raw_n>0)).sum(),"no expiry rows at all",(o.raw_n==0).sum())
k=o[o.kept]; print("study-convention mean pnl",(k.credit-k.cost_kept).mean(),"win",((k.credit-k.cost_kept)>0).mean())
a=o[o.raw_n>0]; p=a.credit-a.cost_raw; print("all with any expiry row: n",len(a),"mean",p.mean(),"median",p.median(),"win",(p>0).mean())
dr=o[(~o.kept)&(o.raw_n>0)]; print("dropped-trade pnl mean",(dr.credit-dr.cost_raw).mean())

#!/usr/bin/env python3
"""Diagnostic for run_momentum_52wk_sue.py (2026-10-02, after the run, descriptive only): median 63d vol, 12-1 return
and overlap of the 52-week-high decile vs the 12-1 decile at each formation."""
import numpy as np, pandas as pd, run_momentum_portfolio as M, run_dip_survivorship as DS
d=DS.pull(); C,V=DS.adjust_and_clean(d)
elig=((V.rolling(50,min_periods=30).mean()>=M.OPTVOL_MIN)&(C>=M.PX_MIN)).fillna(False).values
Cv=C.values; pth=Cv/C.rolling(252,min_periods=252).max().values
vol=(C.pct_change().rolling(63,min_periods=40).std()*np.sqrt(252)).values
idx=C.index; me=[i for i in M.month_ends(idx) if pd.Timestamp(M.START)<=idx[i]<=pd.Timestamp(M.END)]
rows=[]
for a in me[:-1]:
    m=Cv[a-21]/Cv[a-252]-1; ok=elig[a]&np.isfinite(m)&np.isfinite(pth[a])&np.isfinite(vol[a])
    n=np.flatnonzero(ok)
    sm=n[m[n]>=np.quantile(m[n],.9)]; sp=n[pth[a][n]>=np.quantile(pth[a][n],.9)]
    rows.append(dict(vol_univ=np.median(vol[a][n]),vol_mom=np.median(vol[a][sm]),vol_pth=np.median(vol[a][sp]),
                     mom12_of_pth=np.median(m[sp]),mom12_of_mom=np.median(m[sm]),overlap=len(set(sm)&set(sp))/len(sp),at_high=(pth[a][n]>=0.999).mean()))
print(pd.DataFrame(rows).median().round(3).to_string())

import numpy as np, pandas as pd, sys
sys.path.insert(0, "."); import run_vol_decay_exit as v
from run_precision_tier_control import build
P, brk, prec = build(); ind = v.indicators(P)
C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
def stop_only(i, j):
    entry = C[i, j]*(1+v.SLIP); stop = L[i, j]; end = min(i+v.HOLD, len(C)-1); k = i; why = "time"
    for k in range(i+1, end+1):
        c = C[k, j]
        if not np.isfinite(c): continue
        if c < stop: why = "stop"; break
    return 100*(C[k, j]*(1-v.SLIP)/entry-1), why
def reason(i, j, key):
    hk, lo, _ = ind[key]; entry = C[i, j]*(1+v.SLIP); stop = L[i, j]; end = min(i+v.HOLD, len(C)-1)
    for k in range(i+1, end+1):
        c = C[k, j]
        if not np.isfinite(c): continue
        if c < stop: return "stop"
        if np.isfinite(hk[k, j]) and np.isfinite(lo[k, j]) and hk[k, j] < lo[k, j]: return "vd"
    return "time"
for tag in ("precision", "generic"):
    T = pd.read_parquet(f"data/studies/logs/vol_decay_exit_{tag}_trades.parquet")
    ci = {d: n for n, d in enumerate(P.close.index)}; cj = {s: n for n, s in enumerate(P.close.columns)}
    so, why, r120 = [], [], []
    for d, s in zip(T.date, T.sym):
        i, j = ci[pd.Timestamp(d)], cj[s]
        a, b = stop_only(i, j); so.append(a); why.append(b); r120.append(reason(i, j, (0.2, 120)))
    T["SO_pct"] = so
    for a in ("SO", "VD_k0.2_L120"):
        dp = T[a+"_pct"] - T.BASE_pct
        print(f"{tag:9s} {a:13s} - BASE {dp.mean():+.3f}pp t {v.tstat_by_date(dp, T.date):+.2f}")
    dp = T["VD_k0.2_L120_pct"] - T.SO_pct
    print(f"{tag:9s} VD_k0.2_L120 - STOP_ONLY {dp.mean():+.3f}pp t {v.tstat_by_date(dp, T.date):+.2f} | "
          f"exit reasons L120: {pd.Series(r120).value_counts(normalize=True).round(2).to_dict()} | stop-only: {pd.Series(why).value_counts(normalize=True).round(2).to_dict()}")

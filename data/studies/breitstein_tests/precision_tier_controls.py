"""House process (close entry, stop = day low, ema20 trail, hold 60) vs THREE controls, unclipped and clipped:
month (original, look-ahead), post (random later session, no look-ahead), xname (random other name, same date)."""
import sys; sys.path.insert(0, "src"); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals
from run_precision_tier_control import build

pt.R_CLIP = 1e9
_arms = pt._daily_arms
def arms_with_risk(P, j, i, stop, side, hold, entry_at="next_open"):
    o = _arms(P, j, i, stop, side, hold, entry_at)
    if o:
        e = (P.close.values[i, j] if entry_at == "close" else P.open.values[i + 1, j]) * (1 + pt.SLIP)
        o["risk_pct"] = (e - stop) / e
    return o
pt._daily_arms = arms_with_risk
cap = {}
_rep = pt._report
def rep(name, T, K, arms, split, note, timeframe, ledger=True):
    cap["T"], cap["K"] = T, K
    return _rep(name, T, K, arms, split, note, timeframe, ledger=False)
pt._report = rep

P, brk, prec = build()
rows = []
for ctrl_mode in ("post", "xname", "month"):
    pt.run_daily(f"precision house process, ctrl {ctrl_mode}", lambda _P: daily_signals(prec, stop=P.low, side="long"),
                 hold=60, panel=P, ledger=False, entry_at="close", control=ctrl_mode)
    T, K = cap["T"], cap["K"]
    K.to_parquet(f"data/cache/precision_ctrl_{ctrl_mode}_K.parquet")
    for floor in (0.0, 0.02):
        for clip in (10, 20, None):
            for arm in ("ema20", "stop_hold", "trail_bar", "t2R"):
                s = T[T.risk_pct >= floor][arm]; k = K[K.risk_pct >= floor][arm]
                if clip: s, k = s.clip(-clip, clip), k.clip(-clip, clip)
                d = s.groupby(T.loc[s.index, "date"]).mean(); dk = k.groupby(K.loc[k.index, "date"]).mean()
                rows.append(dict(ctrl=ctrl_mode, floor=f"{floor:.0%}", clip=clip or "none", arm=arm, n=len(s), n_ctrl=len(k),
                                 sig=s.mean(), sig_med=s.median(), sig_t=d.mean()/d.std()*np.sqrt(len(d)),
                                 ctrl_mean=k.mean(), ctrl_med=k.median(), ctrl_t=dk.mean()/dk.std()*np.sqrt(len(dk)),
                                 edge=s.mean()-k.mean(), sig_win=100*(s>0).mean(), ctrl_win=100*(k>0).mean()))
    t2 = T[T.risk_pct >= 0.02]; k2 = K[K.risk_pct >= 0.02]
    yr = pd.DataFrame({"sig": t2.groupby(pd.to_datetime(t2.date).dt.year).ema20.mean(),
                       "ctrl": k2.groupby(pd.to_datetime(k2.date).dt.year).ema20.mean()})
    print(f"\nby year, ema20, floor 2%, unclipped, ctrl={ctrl_mode}:"); print(yr.round(2).T.to_string())
R = pd.DataFrame(rows)
print("\n\n################ SUMMARY: signal vs each control ################")
print(R.round(3).to_string(index=False))
R.to_csv("data/studies/breitstein_tests/precision_tier_controls_2026-09-19.csv", index=False)

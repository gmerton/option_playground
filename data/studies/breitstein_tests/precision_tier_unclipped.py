"""Signal vs same-name control for the house process (close entry, hold 60) WITHOUT the harness's +/-10R clip,
at several risk floors and clips, so the verdict does not hinge on one winsorisation choice."""
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
for entry_at in ("close", "next_open"):
    pt.run_daily(f"precision unclipped {entry_at}", lambda _P: daily_signals(prec, stop=P.low, side="long"),
                 hold=60, panel=P, ledger=False, entry_at=entry_at)
    T, K = cap["T"], cap["K"]
    T.to_parquet(f"data/cache/precision_unclipped_{entry_at}_T.parquet"); K.to_parquet(f"data/cache/precision_unclipped_{entry_at}_K.parquet")
    print(f"\n\n##### {entry_at} entry, hold 60: signal vs control, unclipped, by risk floor x clip #####")
    rows = []
    for floor in (0.0, 0.02, 0.03):
        for clip in (10, 20, 50, None):
            for arm in ("ema20", "stop_hold", "trail_bar"):
                s = T[T.risk_pct >= floor][arm]; k = K[K.risk_pct >= floor][arm]
                if clip: s, k = s.clip(-clip, clip), k.clip(-clip, clip)
                d = s.groupby(T.loc[s.index, "date"]).mean()
                rows.append(dict(floor=f"{floor:.0%}", clip=clip or "none", arm=arm, n=len(s), sig=s.mean(), sig_med=s.median(),
                                 sig_t=d.mean()/d.std()*np.sqrt(len(d)), ctrl=k.mean(), ctrl_med=k.median(), edge=s.mean()-k.mean(),
                                 sig_win=100*(s>0).mean(), ctrl_win=100*(k>0).mean()))
    R = pd.DataFrame(rows); print(R.round(3).to_string(index=False))
    R.to_csv(f"data/studies/breitstein_tests/precision_tier_unclipped_{entry_at}_2026-09-19.csv", index=False)
    # by year, ema20, floor 2%, no clip
    t2 = T[T.risk_pct >= 0.02]; k2 = K[K.risk_pct >= 0.02]
    yr = pd.DataFrame({"sig": t2.groupby(pd.to_datetime(t2.date).dt.year).ema20.mean(),
                       "n": t2.groupby(pd.to_datetime(t2.date).dt.year).ema20.size(),
                       "ctrl": k2.groupby(pd.to_datetime(k2.date).dt.year).ema20.mean()})
    print("\nby year, ema20, risk floor 2%, unclipped:"); print(yr.round(2).to_string())

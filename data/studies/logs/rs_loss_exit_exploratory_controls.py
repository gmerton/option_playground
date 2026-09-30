import numpy as np, pandas as pd
import run_rs_loss_exit as R
from run_precision_tier_control import build
P, brk, prec = build()
C, L, E20 = P.close.values, P.low.values, P.ema20.values
S50 = P.close.rolling(50).mean().values
E50 = P.close.ewm(span=50, adjust=False).mean().values
for tag, mask in (("precision", prec), ("generic", brk)):
    T = pd.read_parquet(f"data/studies/logs/rs_loss_exit_{tag}_trades.parquet")
    idx = {d: n for n, d in enumerate(P.close.index)}; col = {s: n for n, s in enumerate(P.close.columns)}
    out = {k: [] for k in ("HOLD60", "SMA50", "EMA50", "HOLDmatch")}
    rng = np.random.default_rng(1)
    for r in T.itertuples():
        i, j = idx[r.date], col[r.sym]; end = min(i + R.HOLD, len(C) - 1)
        for arm, M in (("HOLD60", None), ("SMA50", S50), ("EMA50", E50)):
            k = i
            for k in range(i + 1, end + 1):
                c = C[k, j]
                if not np.isfinite(c): continue
                if c < L[i, j]: break
                if M is not None and np.isfinite(M[k, j]) and c < M[k, j]: break
            out[arm].append(100 * (C[k, j] * (1 - R.SLIP) / r.entry - 1))
        # hold-matched: exit at C's own session count but ignore the RS signal -> a random other trade's C_k
        k = min(int(rng.choice(T.C_k.values)), end - i); px = C[i + k, j]
        out["HOLDmatch"].append(100 * (px * (1 - R.SLIP) / r.entry - 1) if np.isfinite(px) else r.A_pct)
    for a, v in out.items(): T[a + "_pct"] = v
    h1 = T.date < R.SPLIT
    print(f"\n{tag}: n {len(T)}  mean %: A {T.A_pct.mean():.2f} C {T.C_pct.mean():.2f} " + " ".join(f"{a} {T[a+'_pct'].mean():.2f}" for a in out))
    for a in out:
        d = T.C_pct - T[a + "_pct"]
        print(f"  C - {a:9s} {d.mean():+.3f}pp t {R.tstat_by_date(d, T.date):+.2f} halves {d[h1].mean():+.2f}/{d[~h1].mean():+.2f}")

#!/usr/bin/env python3
"""
What predicts whether a breakout HOLDS or comes back to the level?

retrace_entry_2026-09-20.md found the breakout book is bimodal: of 43,970 house breakouts, the 23.6%
that never return to the breakout level within 20 sessions average +1.273R, and the 76.4% that do
average -0.374R. The book's +0.014 average is a blend of two unrelated populations, and "never
returned" is survivorship -- not a rule.

So the question is whether the split is callable AT ENTRY. Everything tested here is already in the
book -- location vs the 21 EMA, volume pace, ADR, the precision-tier components, range position, gap,
extension -- and none of it has ever been scored against THIS target.

Two numbers per bucket, and only the second is tradeable:
  held%   -- share of breakouts in the bucket that never returned to the level (the classification)
  meanR   -- mean R of EVERY breakout in the bucket (what you would actually earn gating on it)

A predictor is only useful if meanR sorts. held% can sort while meanR does not, if the winners in the
good bucket are smaller or the losers deeper -- so held% alone would be a trap.

Usage: PYTHONPATH=src .venv/bin/python3 run_breakout_hold_predictors.py > data/studies/breakout_hold_predictors_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 210)
from lib.studies.pattern_test import load_panel
from run_retrace_entry import masks

HOLD, KSTOP = 5, 1.0


def main():
    P = load_panel()
    C, H, L, O, A = P.close, P.high, P.low, P.open, P.adr
    # DailyPanel carries no volume; pivot it from the raw panel and align to the close grid
    _raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    V = _raw.pivot(index="date", columns="ticker", values="volume").reindex(index=C.index, columns=C.columns)
    brk, _, mat = masks(P, 20, 0.0)               # mat = broke out AND came back within 20d
    held = brk & ~mat

    level = H.shift(1).rolling(20).max()
    ema21 = C.ewm(span=21, adjust=False).mean()
    sma10, sma20, sma50 = (C.rolling(k).mean() for k in (10, 20, 50))
    hi52 = C.rolling(252, min_periods=60).max()
    feats = {
        "ext_above_level_ADR": (C / level - 1) * 100 / A,
        "dist_21ema_ADR":      (C / ema21 - 1) * 100 / A,
        "rvol20":              V / V.rolling(20).mean(),
        "adr_pct":             A,
        "range_pos":           (C - L) / (H - L).replace(0, np.nan),
        "gap_ADR":             (O / C.shift(1) - 1) * 100 / A,
        "pct_off_52w_high":    (C / hi52 - 1) * 100,
        "sma_stacked":         ((sma10 > sma20) & (sma20 > sma50)).astype(float),
        "dolvol_musd":         P.close * V / 1e6,
    }

    cv, av, hv, lv = C.values, A.values, H.values, L.values
    n = len(cv)
    pts = np.argwhere(brk.values)
    recs = []
    for i, j in pts:
        if i + HOLD >= n: continue
        e, a = cv[i, j], av[i, j]
        if not (np.isfinite(e) and np.isfinite(a)) or a <= 0: continue
        stop = e * (1 - KSTOP * a / 100); risk = e - stop
        pl, pc = lv[i + 1:i + 1 + HOLD, j], cv[i + 1:i + 1 + HOLD, j]
        if not np.isfinite(pc).all(): continue
        hit = np.flatnonzero(pl <= stop)
        recs.append(dict(i=i, j=j, R=((stop if len(hit) else pc[-1]) - e) / risk,
                         held=bool(held.values[i, j])))
    D = pd.DataFrame(recs)
    for k, f in feats.items():
        D[k] = f.values[D.i.values, D.j.values]
    D["date"] = C.index[D.i.values]
    print(f"{len(D):,} scored breakouts | held {100*D.held.mean():.1f}% | "
          f"meanR all {D.R.mean():+.3f} | held {D[D.held].R.mean():+.3f} | failed {D[~D.held].R.mean():+.3f}\n")

    print("="*100)
    print("UNIVARIATE: quintile of each feature -> held% and meanR of every breakout in the bucket")
    print("="*100)
    rank = []
    for k in feats:
        x = D[[k, "R", "held", "date"]].dropna()
        if x[k].nunique() < 5:
            g = x.groupby(x[k]).agg(n=("R", "size"), held_pct=("held", lambda s: 100*s.mean()), meanR=("R", "mean"))
        else:
            # no explicit labels: with duplicates="drop" a skewed feature can yield <5 bins
            q = pd.qcut(x[k], 5, duplicates="drop")
            g = x.groupby(q).agg(n=("R", "size"), held_pct=("held", lambda s: 100*s.mean()), meanR=("R", "mean"))
        spread_h = g.held_pct.max() - g.held_pct.min()
        spread_r = g.meanR.max() - g.meanR.min()
        mono = abs(pd.Series(g.meanR.values).corr(pd.Series(range(len(g))), method="spearman"))
        print(f"\n--- {k} ---")
        print(g.round(3).to_string())
        print(f"    held% spread {spread_h:5.1f}pp | meanR spread {spread_r:+.3f} | monotonicity |rho| {mono:.2f}")
        rank.append(dict(feature=k, held_spread_pp=spread_h, meanR_spread=spread_r, monotonic=mono,
                         best_bucket=str(g.meanR.idxmax()), best_meanR=g.meanR.max(),
                         worst_meanR=g.meanR.min()))

    print("\n\n" + "="*100)
    print("RANKED BY meanR SPREAD (the tradeable one)")
    print("="*100)
    Rk = pd.DataFrame(rank).sort_values("meanR_spread", ascending=False)
    print(Rk.round(3).to_string(index=False))
    print(f"\nbaseline meanR (no gate): {D.R.mean():+.3f}")
    print("A feature is a gate only if meanR sorts monotonically AND the best bucket clears the baseline")
    print("by enough to survive the 0.4R entry-timing effect already measured.")
    D.to_parquet("data/cache/breakout_hold_features.parquet", index=False)


if __name__ == "__main__":
    main()

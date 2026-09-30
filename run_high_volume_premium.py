#!/usr/bin/env python3
"""High-volume return premium (GKM 2001) on liquid_panel_2009 (2026-09-29).
PRE-REGISTERED: data/studies/high_volume_premium_2026-09-29.md (committed before this ran).
Usage: PYTHONPATH=src .venv/bin/python3 run_high_volume_premium.py > data/studies/high_volume_premium_2026-09-29.log
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.regime.trailing import Panel, liquidity_mask

SPLIT, HS, COST = pd.Timestamp("2018-01-01"), (5, 20, 60), 0.0010


def nw(x, lags=4):
    x = x.dropna()
    f = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(f.params[0]), float(f.tvalues[0])


raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw)
C, H, L = p.close, p.high, p.low
V = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex_like(C)
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
adr = (H / L - 1).shift(1).rolling(20).mean()
wk = V.rolling(5).sum()
base = V.shift(5).rolling(49, min_periods=40).mean() * 5
AV = wk / base
wret = C / C.shift(5) - 1
idx = C.index
fri = pd.Series(idx).groupby(pd.Series(idx).dt.to_period("W")).max()
fri = [d for d in fri if pd.Timestamp("2010-03-01") <= d <= pd.Timestamp("2026-06-30")]
pos = {d: i for i, d in enumerate(idx)}
rows = []
for d in fri:
    i = pos[d]
    ok = elig.iloc[i].fillna(False) & AV.iloc[i].notna() & wret.iloc[i].notna() & adr.iloc[i].notna()
    names = ok[ok].index
    if len(names) < 200:
        continue
    X = pd.DataFrame({"av": AV.iloc[i][names], "wr": wret.iloc[i][names], "adr": adr.iloc[i][names]})
    for h in HS:
        X[f"f{h}"] = C.iloc[min(i + h, len(idx) - 1)][names] / C.iloc[i][names] - 1 if i + h < len(idx) else np.nan
    X["dec"] = pd.qcut(X.av.rank(method="first"), 10, labels=False)
    X["cell"] = pd.qcut(X.wr.rank(method="first"), 5, labels=False).astype(str) + pd.qcut(X.adr.rank(method="first"), 3, labels=False).astype(str)
    X["date"] = d
    rows.append(X.reset_index().rename(columns={"index": "ticker"}))
D = pd.concat(rows, ignore_index=True)
out = [f"# High-volume premium (pre-registration in the md). formations {D.date.nunique()}, name-weeks {len(D):,}"]


def excess(sig_mask, h):
    col = f"f{h}"
    base_ = D[(D.dec > 0) & (D.dec < 9)].groupby(["date", "cell"])[col].mean().rename("ctl")
    S = D[sig_mask].join(base_, on=["date", "cell"]).dropna(subset=[col, "ctl"])
    S["ex"] = S[col] - S.ctl
    return S.groupby("date").ex.mean(), S


res = []
for lab, m in (("HIGH", D.dec == 9), ("LOW", D.dec == 0), ("HIGH up-week", (D.dec == 9) & (D.wr > 0)), ("HIGH down-week", (D.dec == 9) & (D.wr <= 0))):
    for h in HS:
        g, S = excess(m, h)
        mu, t = nw(g, lags=max(4, h // 5))
        hm = g.index < SPLIT; yr = g.groupby(g.index.year).mean()
        res.append(dict(signal=lab, h=h, n=len(S), excess_pct=100 * mu, t=t, h1=100 * g[hm].mean(), h2=100 * g[~hm].mean(),
                        yrs_pos=f"{int((yr > 0).sum())}/{len(yr)}", yrs_share=(yr > 0).mean(), abs_net_pct=100 * (S[f'f{h}'].mean() - 2 * COST)))
R = pd.DataFrame(res)
out.append(R.round(3).to_string(index=False))
gh, _ = excess(D.dec == 9, 20); gl, _ = excess(D.dec == 0, 20)
d = (gh - gl).dropna(); mu, t = nw(d, 4)
out.append(f"HIGH - LOW +20: {100 * mu:+.3f}% t {t:+.2f}")
p0 = R[(R.signal == "HIGH") & (R.h == 20)].iloc[0]
ok = p0.excess_pct > 0 and p0.t >= 3 and p0.h1 > 0 and p0.h2 > 0 and p0.yrs_share > 0.5
out.append(f"PRIMARY HIGH +20: {p0.excess_pct:+.3f}% t {p0.t:+.2f}, halves {p0.h1:+.3f}/{p0.h2:+.3f}, yrs+ {p0.yrs_pos} -> {'PASS' if ok else 'FAIL'}")
print("\n".join(out))

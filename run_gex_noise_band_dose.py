#!/usr/bin/env python3
"""QQQ noise band: gamma-depth dose-response with a VIX control (2026-09-29, audit step 3 item 4).

PRE-REGISTERED: data/studies/gex_noise_band_dose_2026-09-29.md (committed before this ran). Unit = the unchanged
engine output of run_noise_band.py QQQ (game mode); prior-close QQQ GEX -> trailing 252-session percentile rank ->
quintiles (Q1 = most negative). Primary: NW slope of net P&L on score (t >= 3.2, both halves > 0) AND the same slope
with VIX(t-1) tercile dummies (t >= 3.2).

Usage (from repo root):
  PYTHONPATH=src:. .venv/bin/python3 run_gex_noise_band_dose.py > data/studies/gex_noise_band_dose_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm

import run_gex_regime_pin as base

pd.set_option("display.width", 220)
SPLIT = pd.Timestamp("2018-01-01")
BAR = 3.2


def nw(y, X, lags=5):
    return sm.OLS(y, sm.add_constant(X), missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def tstat(x):
    x = x.dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def main():
    r = pd.read_csv("data/cache/gex/noise_band_qqq_game_daily.csv", parse_dates=["day"]).set_index("day")
    bars = base.daily_bars("QQQ")
    _, net, _ = base.gex_series("QQQ", bars)
    net = net.sort_index()
    # trailing 252-session percentile rank, known at the close it is computed on
    rank = net.rolling(252, min_periods=252).apply(lambda w: (w[:-1] < w[-1]).mean() + 0.5 * (w[:-1] == w[-1]).mean(), raw=True)
    vix = pd.read_parquet("data/cache/vix_daily_long.parquet")
    vix = vix.set_index(pd.to_datetime(vix.trade_date)).vix_close

    sess = r.index
    prev = pd.Series(sess, index=sess).shift(1)
    r["gex_prev"] = net.reindex(prev.values).values
    r["rank_prev"] = rank.reindex(prev.values).values
    r["vix_prev"] = vix.reindex(prev.values).values
    r = r[(r.index <= base.END)].dropna(subset=["gex_prev", "rank_prev", "vix_prev"])
    r["q"] = pd.qcut(r.rank_prev, 5, labels=[1, 2, 3, 4, 5]).astype(int)  # Q1 = most negative gamma
    r["score"] = 5 - r.q
    r["vt"] = pd.qcut(r.vix_prev, 3, labels=["lowVIX", "midVIX", "highVIX"])
    r["NEG"] = r.gex_prev < 0
    y = r.net * 1e4  # bps
    print(f"window {r.index.min().date()} -> {r.index.max().date()}: {len(r):,} sessions; "
          f"negative-GEX {100 * r.NEG.mean():.1f}%; VIX tercile cuts {r.vix_prev.quantile([1/3, 2/3]).round(2).tolist()}")

    print("\n-- by gamma quintile (Q1 = most negative trailing rank); net bps/session --")
    Q = r.assign(y=y).groupby("q").agg(n=("y", "size"), mean_bps=("y", "mean"), neg_gex_pct=("NEG", "mean"),
                                        vix_mean=("vix_prev", "mean"), traded_pct=("trades", lambda s: (s > 0).mean()))
    Q["t"] = [tstat(y[r.q == q]) for q in Q.index]
    Q["h1_bps"] = [y[(r.q == q) & (r.index < SPLIT)].mean() for q in Q.index]
    Q["h2_bps"] = [y[(r.q == q) & (r.index >= SPLIT)].mean() for q in Q.index]
    Q["neg_gex_pct"] *= 100; Q["traded_pct"] *= 100
    print(Q.round(2).to_string())

    print("\n-- PRIMARY 1: net_bps ~ score (NW 5) --")
    f1 = nw(y, r[["score"]])
    h = {}
    for lab, m in [("2010-17", r.index < SPLIT), ("2018-26", r.index >= SPLIT)]:
        fh = nw(y[m], r.loc[m, ["score"]]); h[lab] = (fh.params.score, fh.tvalues.score)
    print(f"slope {f1.params.score:+.3f} bps per quintile step, t {f1.tvalues.score:.2f}; "
          f"halves {h['2010-17'][0]:+.3f} (t {h['2010-17'][1]:.2f}) / {h['2018-26'][0]:+.3f} (t {h['2018-26'][1]:.2f})")
    c1 = f1.params.score > 0 and f1.tvalues.score >= BAR and all(v[0] > 0 for v in h.values())

    print("\n-- PRIMARY 2: net_bps ~ score + VIX-tercile dummies (NW 5) --")
    X2 = pd.concat([r[["score"]], pd.get_dummies(r.vt, drop_first=True).astype(float)], axis=1)
    f2 = nw(y, X2)
    print(f2.summary().tables[1])
    c2 = f2.params.score > 0 and f2.tvalues.score >= BAR
    print(f"\nPASS condition 1 (dose slope t >= {BAR}, both halves > 0): {'YES' if c1 else 'no'}")
    print(f"PASS condition 2 (slope beyond VIX t >= {BAR}): {'YES' if c2 else 'no'}")
    print(f"VERDICT: {'PASS' if c1 and c2 else 'FAIL'}")

    print("\n-- exploratory: slope within each VIX tercile; Q1 and Q5 mean bps --")
    for vt, g in r.groupby("vt", observed=True):
        fg = nw(y[g.index], g[["score"]])
        print(f"{vt:8s} n {len(g):5d}  slope {fg.params.score:+.3f} t {fg.tvalues.score:5.2f}  "
              f"Q1 {y[g.index][g.q == 1].mean():+.2f}  Q5 {y[g.index][g.q == 5].mean():+.2f}")

    print("\n-- exploratory: sign split on this window --")
    for lab, m in [("NEG", r.NEG), ("POS", ~r.NEG)]:
        print(f"{lab}: n {m.sum():,}  mean {y[m].mean():+.2f} bps  t {tstat(y[m]):.2f}")

    print("\n-- exploratory: per-year mean bps by quintile --")
    Y = r.assign(y=y, yr=r.index.year).pivot_table(index="yr", columns="q", values="y", aggfunc="mean")
    Y["Q1-Q5"] = Y[1] - Y[5]
    print(Y.round(1).to_string())
    Q.to_csv("data/studies/gex_noise_band_dose_2026-09-29.csv")


if __name__ == "__main__":
    main()

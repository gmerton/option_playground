#!/usr/bin/env python3
"""Noise band gated on SPY dealer-gamma sign: cell Q (QQQ engine) and cell S (SPY engine) (2026-09-29, audit item 4b).

PRE-REGISTERED: data/studies/gex_noise_band_spy_gamma_2026-09-29.md (committed before this ran). Same arms/metrics as
run_gex_noise_band.py; only the gate (SPY GEX, prior close) and the underlying change. Bar t >= 3.4 (Sidak k = 4).

Usage (from repo root):
  .venv/bin/python3 run_noise_band.py SPY --out data/cache/gex/noise_band_spy_game_daily.csv
  PYTHONPATH=src:. .venv/bin/python3 run_gex_noise_band_spy_gamma.py > data/studies/gex_noise_band_spy_gamma_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

import run_gex_regime_pin as base

pd.set_option("display.width", 220)
SPLIT = pd.Timestamp("2018-01-01")
BAR = 3.4


def tstat(x):
    return x.mean() / (x.std(ddof=1) / sqrt(len(x)))


def cell(label, path, gex):
    r = pd.read_csv(path, parse_dates=["day"]).set_index("day")
    prev = pd.Series(r.index, index=r.index).shift(1)
    r["gex_prev"] = gex.reindex(prev.values).values
    r = r[(r.index <= base.END) & r.gex_prev.notna()]
    r["NEG"] = r.gex_prev < 0
    n = len(r)
    print(f"\n{'=' * 100}\nCELL {label}: {path}\nwindow {r.index.min().date()} -> {r.index.max().date()}: {n:,} sessions;"
          f" SPY negative-GEX {100 * r.NEG.mean():.1f}%")

    def row(arm, x):
        h1, h2 = x[x.index < SPLIT], x[x.index >= SPLIT]
        sd = x.std(ddof=1) * sqrt(252)
        return dict(cell=label, arm=arm, sessions=len(x), mean_bps=x.mean() * 1e4, t=tstat(x),
                    sharpe=x.mean() * 252 / sd, ann_own=x.mean() * 252 * 100, ann_window=x.sum() / n * 252 * 100,
                    h1_bps=h1.mean() * 1e4, t_h1=tstat(h1), h2_bps=h2.mean() * 1e4, t_h2=tstat(h2))

    T = pd.DataFrame([row("A all", r.net), row("N neg SPY GEX", r[r.NEG].net), row("P pos SPY GEX", r[~r.NEG].net)])
    print(T.drop(columns="cell").round(2).to_string(index=False))
    A, N = T.iloc[0], T.iloc[1]
    ok = N.mean_bps > 0 and N.t >= BAR and N.h1_bps > 0 and N.h2_bps > 0 and N.mean_bps > A.mean_bps
    d = r[r.NEG].net.mean() - r[~r.NEG].net.mean()
    se = sqrt(r[r.NEG].net.var() / r.NEG.sum() + r[~r.NEG].net.var() / (~r.NEG).sum())
    print(f"N minus P: {d * 1e4:+.2f} bps/session (Welch t {d / se:.2f})")
    print(f"PASS cell {label} (N: mean > 0, t >= {BAR}, both halves > 0, beats A): {'YES' if ok else 'no'}")
    r["yr"] = r.index.year
    Y = pd.DataFrame({"N_net%": r[r.NEG].groupby("yr").net.sum() * 100, "N_days": r[r.NEG].groupby("yr").size(),
                      "P_net%": r[~r.NEG].groupby("yr").net.sum() * 100, "A_net%": r.groupby("yr").net.sum() * 100})
    print("by year (summed net % of $10k):"); print(Y.round(1).T.to_string())
    return T, r.NEG.rename(label)


def main():
    _, gex, _ = base.gex_series("SPY", base.daily_bars("SPY"))
    gex = gex.sort_index()
    TQ, nq = cell("Q", "data/cache/gex/noise_band_qqq_game_daily.csv", gex)
    TS, ns = cell("S", "data/cache/gex/noise_band_spy_game_daily.csv", gex)
    # exploratory: agreement of SPY and QQQ gamma sign on the QQQ window
    _, qg, _ = base.gex_series("QQQ", base.daily_bars("QQQ"))
    j = pd.concat([gex.rename("spy") < 0, qg.rename("qqq") < 0], axis=1).dropna()
    print(f"\nexploratory: SPY and QQQ prior-close gamma signs agree on {100 * (j.spy == j.qqq).mean():.1f}% of {len(j):,} days")
    pd.concat([TQ, TS]).to_csv("data/studies/gex_noise_band_spy_gamma_2026-09-29.csv", index=False)


if __name__ == "__main__":
    main()

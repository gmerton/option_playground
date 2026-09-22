#!/usr/bin/env python3
"""QQQ noise-band intraday momentum gated by prior-close QQQ dealer-gamma sign (2026-09-21, GEX follow-up item 3).

PRE-REGISTERED: data/studies/gex_noise_band_2026-09-21.md. The engine is run_noise_band.py with its default
configuration (game mode); its per-session output is split by the prior session's QQQ net GEX (naive sign, computed
by run_gex_regime_pin.gex_series). Sessions are independent in game mode, so gating = keeping/skipping sessions.

Usage (from repo root):
  .venv/bin/python3 run_noise_band.py QQQ --out data/cache/gex/noise_band_qqq_game_daily.csv
  PYTHONPATH=src:. .venv/bin/python3 run_gex_noise_band.py | tee data/studies/gex_noise_band_2026-09-21.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

import run_gex_regime_pin as base

pd.set_option("display.width", 220)
SPLIT = pd.Timestamp("2018-01-01")


def main():
    r = pd.read_csv("data/cache/gex/noise_band_qqq_game_daily.csv", parse_dates=["day"]).set_index("day")
    bars = base.daily_bars("QQQ")
    _, net, _ = base.gex_series("QQQ", bars)
    net = net.sort_index()
    # prior session's GEX attached to day t (sessions from the noise-band engine's own calendar)
    sess = r.index
    prev = pd.Series(sess, index=sess).shift(1)
    r["gex_prev"] = net.reindex(prev.values).values
    r = r[(r.index <= base.END) & r.gex_prev.notna()]
    r["NEG"] = r.gex_prev < 0
    n_all = len(r)
    print(f"window {r.index.min().date()} -> {r.index.max().date()}: {n_all:,} sessions; negative-GEX {r.NEG.sum():,} ({100 * r.NEG.mean():.1f}%)")

    def row(label, x, n_window):
        x = x.dropna()
        t = x.mean() / (x.std(ddof=1) / sqrt(len(x)))
        sd = x.std(ddof=1) * sqrt(252)
        return dict(arm=label, sessions=len(x), mean_bps=x.mean() * 1e4, ann_own=x.mean() * 252 * 100,
                    ann_window=x.sum() / n_window * 252 * 100, sharpe=x.mean() * 252 / sd if sd else np.nan, t=t,
                    h1_bps=x[x.index < SPLIT].mean() * 1e4, h2_bps=x[x.index >= SPLIT].mean() * 1e4,
                    t_h1=x[x.index < SPLIT].mean() / (x[x.index < SPLIT].std(ddof=1) / sqrt((x.index < SPLIT).sum())),
                    t_h2=x[x.index >= SPLIT].mean() / (x[x.index >= SPLIT].std(ddof=1) / sqrt((x.index >= SPLIT).sum())),
                    gross_bps=r.loc[x.index, "gross"].mean() * 1e4, traded_pct=100 * (r.loc[x.index, "trades"] > 0).mean())

    T = pd.DataFrame([row("A all sessions", r.net, n_all), row("N negative GEX", r[r.NEG].net, n_all),
                      row("P positive GEX", r[~r.NEG].net, n_all)])
    print("\nNET daily P&L, % of the fixed $10k (bps = per session in the arm; ann_own = x252 over the arm's sessions;"
          " ann_window = sitting flat on skipped sessions)")
    print(T.round(2).to_string(index=False))
    A, N = T.iloc[0], T.iloc[1]
    ok = N.mean_bps > 0 and N.t >= 3 and N.h1_bps > 0 and N.h2_bps > 0 and N.mean_bps > A.mean_bps
    print(f"\nPASS (arm N: mean > 0, t >= 3, both halves > 0, beats arm A): {'YES' if ok else 'no'}")
    diff = r[r.NEG].net.mean() - r[~r.NEG].net.mean()
    se = sqrt(r[r.NEG].net.var() / r.NEG.sum() + r[~r.NEG].net.var() / (~r.NEG).sum())
    print(f"N minus P: {diff * 1e4:+.2f} bps/session (Welch t {diff / se:.2f})")
    r["yr"] = r.index.year
    Y = pd.DataFrame({"N_net%": r[r.NEG].groupby("yr").net.sum() * 100, "N_days": r[r.NEG].groupby("yr").size(),
                      "P_net%": r[~r.NEG].groupby("yr").net.sum() * 100, "P_days": r[~r.NEG].groupby("yr").size(),
                      "A_net%": r.groupby("yr").net.sum() * 100})
    print("\nby year (summed net % of $10k):"); print(Y.round(1).T.to_string())
    T.to_csv("data/studies/gex_noise_band_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

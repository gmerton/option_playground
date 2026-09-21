#!/usr/bin/env python3
"""
Profit-lock exits on the house breakout: do breakeven / lock-in / trim rules beat the plain 20-EMA close trail?

Question (Gabe, 2026-09-20): "it's psychologically uncomfortable to set stops that would kill the profits we've made"
-- AMD +10% over two days with the rule stop at the entry-day low. Is protecting open profit better or worse?

Trades = the house process exactly (run_precision_tier_control.py `precision` mask): enter at the breakout CLOSE
(+10 bps), initial stop = breakout-day low judged on the close, risk floor 2% (honest variant), hold cap 60.
Every arm runs on the SAME trades, so the comparison is paired (arm - BASE, clustered by entry date).

Arms (all close-judged; every arm keeps the 20-EMA close exit and the initial stop):
  BASE        20-EMA close trail (the house rule)
  BE_1R       once a close >= entry + 1R, stop -> entry
  BE_2R       once a close >= entry + 2R, stop -> entry
  LOCK_2R_1R  once a close >= entry + 2R, stop -> entry + 1R
  BE_EXT2     once the close is >= 2 ADR above the 20 EMA (AMD's state), stop -> entry
  EMA10_EXT2  once >= 2 ADR above the 20 EMA, switch the trail to the 10 EMA
  TRIM_2R     sell half at the first close >= +2R, rest = BASE
  TRIM_EXT2   sell half at the first close >= 2 ADR above the 20 EMA, rest = BASE
  TRIM_EXT3   same at 3 ADR

Usage: PYTHONPATH=src .venv/bin/python3 run_profit_lock_study.py > data/studies/profit_lock/profit_lock_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
TODAY = date.today().isoformat()
SLIP, HOLD, FLOOR = pt.SLIP, 60, 0.02
ARMS = ["BASE", "BE_1R", "BE_2R", "LOCK_2R_1R", "BE_EXT2", "EMA10_EXT2", "TRIM_2R", "TRIM_EXT2", "TRIM_EXT3"]
OUT = pt.REPO / "data/studies/profit_lock"


def simulate(C, E20, E10, ADR, i, j, arm):
    """One trade, one arm. Returns (R, bars held, peak close R)."""
    entry = C[i, j] * (1 + SLIP)
    stop0 = STOP[i, j]
    risk = entry - stop0
    stop, trail, trim_r, peak = stop0, E20, None, 0.0
    end = min(i + HOLD, len(C) - 1)
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        r_now = (c * (1 - SLIP) - entry) / risk
        peak = max(peak, (c - entry) / risk)
        if c < stop or (np.isfinite(trail[k, j]) and c < trail[k, j]):
            break
        ext = (c - E20[k, j]) / (ADR[k, j] / 100 * c) if np.isfinite(ADR[k, j]) and ADR[k, j] > 0 else np.nan
        # updates take effect from the next close
        if arm == "BE_1R" and c >= entry + risk:
            stop = max(stop, entry)
        elif arm == "BE_2R" and c >= entry + 2 * risk:
            stop = max(stop, entry)
        elif arm == "LOCK_2R_1R" and c >= entry + 2 * risk:
            stop = max(stop, entry + risk)
        elif arm == "BE_EXT2" and ext >= 2:
            stop = max(stop, entry)
        elif arm == "EMA10_EXT2" and ext >= 2:
            trail = E10
        elif trim_r is None and ((arm == "TRIM_2R" and c >= entry + 2 * risk)
                                 or (arm == "TRIM_EXT2" and ext >= 2) or (arm == "TRIM_EXT3" and ext >= 3)):
            trim_r = r_now
    r = (C[k, j] * (1 - SLIP) - entry) / risk
    if trim_r is not None:
        r = 0.5 * trim_r + 0.5 * r
    return r, k - i, peak


def paired_t(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return g.mean() / g.std() * np.sqrt(len(g)) if len(g) > 2 else np.nan


def main():
    global STOP
    P, _, prec = build()
    C, L = P.close.values, P.low.values
    STOP = L
    E20 = P.ema20.values
    E10 = P.close.ewm(span=10, adjust=False).mean().values
    ADR = P.adr.values
    m = prec[prec.index >= "2019-10-01"]
    off = len(prec) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP)
        risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C):
            continue
        rec = dict(date=P.close.index[i], sym=P.close.columns[j], risk_pct=100 * risk / entry)
        for a in ARMS:
            r, held, peak = simulate(C, E20, E10, ADR, i, j, a)
            rec[a], rec[a + "_held"] = r, held
            if a == "BASE":
                rec["peakR"] = peak
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["date"] = pd.to_datetime(T.date)
    OUT.mkdir(parents=True, exist_ok=True)
    T.to_parquet(OUT / f"profit_lock_trades_{TODAY}.parquet", index=False)
    print(f"{len(T):,} house trades (precision tier, close entry, risk >= 2%), {T.sym.nunique()} names, "
          f"{T.date.nunique()} entry dates, {T.date.min().date()} -> {T.date.max().date()}")

    reached1 = T.peakR >= 1
    out = []
    for cap in [None, 20, 10]:
        X = T[ARMS].clip(-cap, cap) if cap else T[ARMS]
        for a in ARMS:
            d = X[a] - X["BASE"]
            h1, h2 = T.date < "2023-01-01", T.date >= "2023-01-01"
            out.append(dict(cap=cap or "none", arm=a, meanR=X[a].mean(), medR=X[a].median(),
                            win=100 * (X[a] > 0).mean(), t_arm=paired_t(X[a], T.date),
                            diff=d.mean(), t_diff=paired_t(d, T.date),
                            diff_h1=d[h1].mean(), diff_h2=d[h2].mean(),
                            giveback=100 * ((X[a] <= 0) & reached1).sum() / reached1.sum(),
                            p95=X[a].quantile(0.95), held=T[a + "_held"].median()))
    S = pd.DataFrame(out)
    for cap in ["none", 20, 10]:
        print(f"\n=== R cap {cap} | diff = arm - BASE, paired, t clustered by entry date "
              f"| giveback = % of trades that closed >= +1R and still ended <= 0 ===")
        print(S[S.cap == cap].drop(columns="cap").round(3).to_string(index=False))

    print("\n=== by year: arm - BASE, mean R (no cap) ===")
    Y = pd.DataFrame({a: (T[a] - T.BASE).groupby(T.date.dt.year).mean() for a in ARMS[1:]})
    Y["n"] = T.groupby(T.date.dt.year).size()
    print(Y.round(3).to_string())

    # where does each rule win and lose? split by the BASE outcome
    print("\n=== decomposition: arm - BASE summed R, by BASE outcome bucket (no cap) ===")
    bucket = pd.cut(T.BASE, [-np.inf, 0, 2, 5, np.inf], labels=["BASE<=0", "0-2R", "2-5R", ">5R"])
    D = pd.DataFrame({a: (T[a] - T.BASE).groupby(bucket).sum() for a in ARMS[1:]})
    D["n"] = bucket.value_counts()
    print(D.round(1).to_string())

    # equity-curve pain: fixed 1R per trade, trades in date order
    print("\n=== fixed 1R/trade equity curve (no cap): total R, max drawdown R, worst month R ===")
    eq = []
    for a in ARMS:
        s = T.sort_values("date")[a].values
        cum = np.cumsum(s)
        mo = T.groupby(T.date.dt.to_period("M"))[a].sum()
        eq.append(dict(arm=a, totalR=cum[-1], maxDD=(np.maximum.accumulate(cum) - cum).max(), worst_month=mo.min(),
                       pos_months=100 * (mo > 0).mean()))
    print(pd.DataFrame(eq).round(1).to_string(index=False))
    S.to_csv(OUT / f"profit_lock_summary_{TODAY}.csv", index=False)


if __name__ == "__main__":
    main()

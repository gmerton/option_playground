#!/usr/bin/env python3
"""
DOES THE 20-EMA TRAIL COST MONEY? STOP_ONLY vs BASE with exposure held fixed (pre-registered 2026-09-26, before the
run; queued the same day from the vol-decay exit run's exploratory check; Gabe: "do it").

THE LEAD. vol_decay_exit_2026-09-26 (exploratory, not pre-registered): STOP_ONLY -- initial stop + 60-session time
exit, no trail -- beat the house 20-EMA close trail by +1.25pp per trade (t 5.2) on the generic pool and +1.28pp
(t 3.6) on the precision pool, in raw % return. ⚠ Confound: STOP_ONLY holds longer in a rising 2019-26 sample, so
it collects more market beta. And the O'Neil 8-week hold (2026-09-22) was NULL on the precision pool.

POOLS    exactly as run_vol_decay_exit.py / run_qullamaggie_exit.py (run_precision_tier_control.build()): entry =
         breakout CLOSE + slip; initial stop = breakout-day low judged on the CLOSE; 2% risk floor, 25% cap; max hold
         60 sessions; 2019-10 -> 2026-09. PRIMARY = precision-tier pool; secondary = generic pool (ADR >= 3).
ARMS     BASE = 20-EMA close trail + initial stop (the house rule). STOP_ONLY = initial stop + 60-session time exit.
CONTROL  (the point of this test, declared now) BASE+FILL: take BASE's trade, then from BASE's exit close to
         STOP_ONLY's exit close hold beta x SPY (10 bp in and out). beta = the stock's market beta on SPY over the 252
         sessions before entry (daily returns, >= 150 obs), clipped to [0.5, 2.5]; 1.0 if unavailable.
         So both arms are exposed to the market for the same days, with the stock's own beta; the difference is
         ONLY "keep holding this stock" vs "hold the market" after the trail fires.
PRIMARY  STOP_ONLY - BASE+FILL on the precision pool, % return per trade, paired, t on entry-date cluster means.
         BAR: t >= 3, both halves (split 2023-01) the same sign, the same sign in a majority of years.
         (One primary; the generic pool and the variants below are secondary / descriptive.)
REPORTED raw STOP_ONLY - BASE (reproduces the lead); the beta = 1 fill; SPY-hedged per trade (r - beta x SPY over each
         arm's own window) for both arms; per year; held days; exit reasons; the top-decile / tail (p5) of each arm;
         the share of trades where the arms differ at all (both exit at the stop on the same day for many trades).
READ     PASS -> the trail costs money beyond beta: queue a replacement-exit test (it changes the exit on every
         breakout). FAIL with raw lead intact -> the lead was market exposure: keep the trail (it frees capital).
Local vs cloud: local (cached liquid panel, minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_trail_cost_exposure.py   (log -> data/studies/logs/trail_cost_exposure.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/trail_cost_exposure.log"
SLIP, HOLD, FLOOR, START, SPLIT, FILL_COST = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01", 0.0010


def exits(C, L, E20, i, j):
    """(k_base, why_base, k_so, why_so) -- exit indices judged on the close."""
    stop = L[i, j]; end = min(i + HOLD, len(C) - 1)
    kb = ks = None; wb = ws = "time"
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop:
            if kb is None: kb, wb = k, "stop"
            if ks is None: ks, ws = k, "stop"
            break
        if kb is None and np.isfinite(E20[k, j]) and c < E20[k, j]:
            kb, wb = k, "trail"
    last = k
    return (kb if kb is not None else last), wb, (ks if ks is not None else last), ws


def tclu(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def run_pool(label, mask, P, spy, lines, tag, primary):
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    S = spy.reindex(P.close.index).ffill().values
    R = P.close.pct_change(fill_method=None)
    rs = pd.Series(S, index=P.close.index).pct_change()
    cov = R.rolling(252, min_periods=150).cov(rs)
    var = rs.rolling(252, min_periods=150).var()
    B = cov.div(var, axis=0).shift(1).values                     # beta known before entry
    m = mask[mask.index >= START]; off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP); risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C) \
                or not np.isfinite(ADR[i, j]):
            continue
        kb, wb, ks, ws = exits(C, L, E20, i, j)
        rb = C[kb, j] * (1 - SLIP) / entry - 1
        rso = C[ks, j] * (1 - SLIP) / entry - 1
        beta = B[i, j] if np.isfinite(B[i, j]) else 1.0
        beta = float(np.clip(beta, 0.5, 2.5))
        spy_fill = S[ks] / S[kb] - 1 if ks > kb else 0.0
        fill_cost = 2 * FILL_COST if ks > kb else 0.0
        rbf = (1 + rb) * (1 + beta * spy_fill - fill_cost) - 1
        rbf1 = (1 + rb) * (1 + spy_fill - fill_cost) - 1
        rows.append(dict(date=P.close.index[i], sym=P.close.columns[j], beta=beta, held_b=kb - i, held_so=ks - i,
                         why_b=wb, why_so=ws, BASE=100 * rb, SO=100 * rso, BASE_FILL=100 * rbf, BASE_FILL_b1=100 * rbf1,
                         BASE_h=100 * (rb - beta * (S[kb] / S[i] - 1)), SO_h=100 * (rso - beta * (S[ks] / S[i] - 1))))
    T = pd.DataFrame(rows); T["date"] = pd.to_datetime(T.date)
    h1 = T.date < SPLIT
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates; "
                 f"arms differ on {100 * (T.held_b != T.held_so).mean():.0f}% of trades; median beta {T.beta.median():.2f}")
    lines.append(f"  held days: BASE {T.held_b.mean():.1f}, STOP_ONLY {T.held_so.mean():.1f} | exits BASE "
                 f"{T.why_b.value_counts(normalize=True).round(2).to_dict()} | STOP_ONLY {T.why_so.value_counts(normalize=True).round(2).to_dict()}")
    res = {}
    for name, a, b in [("PRIMARY  STOP_ONLY - BASE+FILL(beta)", "SO", "BASE_FILL"),
                       ("         STOP_ONLY - BASE+FILL(beta=1)", "SO", "BASE_FILL_b1"),
                       ("         STOP_ONLY - BASE, SPY-hedged each", "SO_h", "BASE_h"),
                       ("  raw    STOP_ONLY - BASE (the lead)", "SO", "BASE")]:
        d = T[a] - T[b]
        yr = d.groupby(T.date.dt.year).mean()
        t = tclu(d, T.date)
        lines.append(f"  {name:42s} {d.mean():+.3f}pp  t {t:+.2f}  halves {d[h1].mean():+.3f} / {d[~h1].mean():+.3f}  "
                     f"years same sign as mean {(np.sign(yr) == np.sign(d.mean())).sum()}/{len(yr)}")
        if a == "SO" and b == "BASE_FILL":
            res = dict(m=d.mean(), t=t, h1=d[h1].mean(), h2=d[~h1].mean(), ys=(np.sign(yr) == np.sign(d.mean())).sum(),
                       ny=len(yr), yr=yr)
    for a in ("BASE", "BASE_FILL", "SO"):
        x = T[a]
        lines.append(f"  {a:10s} mean {x.mean():+.2f}%  median {x.median():+.2f}%  win {100 * (x > 0).mean():.0f}%  "
                     f"p5 {x.quantile(.05):+.1f}%  top-decile mean {x[x >= x.quantile(.9)].mean():+.1f}%")
    lines.append("  per year STOP_ONLY - BASE+FILL: " + " ".join(f"{y}:{v:+.2f}" for y, v in res["yr"].items()))
    T.to_parquet(REPO / f"data/studies/logs/trail_cost_exposure_{tag}.parquet", index=False)
    if primary:
        ok = res["t"] >= 3 and res["h1"] > 0 and res["h2"] > 0 and res["ys"] > res["ny"] / 2
        lines.append(f"  BAR (primary): {'PASS' if ok else 'NOT MET'}")
    return res


def main():
    P, brk, prec = build()
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "close"])
    spy = raw[raw.ticker == "SPY"].assign(date=lambda d: pd.to_datetime(d.date)).set_index("date").close.sort_index()
    lines = ["# Does the 20-EMA trail cost money? STOP_ONLY vs BASE, exposure held fixed (pre-registration in the docstring)"]
    run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, spy, lines, "precision", True)
    run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, spy, lines, "generic", False)
    print("\n".join(lines))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

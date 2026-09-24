#!/usr/bin/env python3
"""
[WL-5b] Intraday reversion to the largest-|GEX| strike, SPY underlying only (pre-registered 2026-09-23; spec from
data/option_alpha/videos/2026-03-16_O2vTwL4R6kI/notes.md "Not tested, could be" #1, written before running).

Claim (Option Alpha / GEX-levels traders): price that overshoots the big-gamma strike gets pulled back to it.
Our DAILY pin test was NULL (+0.6 bps, t 0.3 on SPY expiry days); this is the intraday version.

Data: SPY 1-min (data/cache/intraday_hist/SPY_1min.parquet); per-strike gamma (data/cache/gex/SPY_gex_strikes.parquet,
2010-01 -> 2026-02). GEX per strike = (cg - pg) * 100 * S^2 * 0.01, EXACTLY as run_gex_regime_pin.py, from the PRIOR
trade date's chain (known before the open).
K*      = the largest-|GEX| strike within +/-1% of today's open.
Mirror  = the listed strike nearest to 2*open - K* (same distance on the other side of the open) -- distance-matched.
d       = 0.15 x daily ATR14 (prior days only), in $.
Event   = first 1-min close in 09:45 .. 14:30 that is on the OPPOSITE side of the level from the open and >= d beyond it
          (the level was crossed and overshot). One event per level per day.
Outcome = signed return TOWARD the level (bps) at +30 and +60 min from the event close; P(touch the level within 60 min).
PRIMARY: all days, +60 min toward-return: K* events minus mirror events (difference of means, Welch t on the two
  samples; both-cross days are rare, so not paired). Bar |t| >= 3 with K* > mirror, both halves (split 2018-01-01) the
  same sign, per-year shown.
Secondary (report only): +30 min; P(touch 60); positive- vs negative-GEX days (prior-day net GEX sign, same series as
  the GEX study); random-minute baseline (toward-K* return from a random 09:45-14:30 minute, same session -- tests
  generic attraction, no event conditioning).
Prior: low. The option leg cannot be priced (no intraday SPY option quotes); if the underlying fails, stop.

Run: PYTHONPATH=src .venv/bin/python3 run_gex_strike_revert.py   (log -> data/studies/logs/gex_strike_revert.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/gex_strike_revert.log"
SPLIT = "2018-01-01"
M0, M1, H1, H2 = 15, 300, 30, 60         # 09:45 .. 14:30 in minutes from 09:30
RNG = np.random.default_rng(20260923)


def load_bars():
    df = pd.read_parquet(REPO / "data/cache/intraday_hist/SPY_1min.parquet")
    df["day"] = df.ts.dt.normalize()
    df["m"] = df.ts.dt.hour * 60 + df.ts.dt.minute - 570
    df = df[(df.m >= 0) & (df.m < 390)]
    days = np.array(sorted(df.day.unique()))
    di = pd.Series(np.arange(len(days)), index=days)[df.day].values
    g = {c: np.full((len(days), 390), np.nan) for c in ("open", "high", "low", "close")}
    for c in g:
        g[c][di, df.m.values] = df[c].values
    dh, dl = np.nanmax(g["high"], 1), np.nanmin(g["low"], 1)
    dc = np.array([r[np.isfinite(r)][-1] if np.isfinite(r).any() else np.nan for r in g["close"]])
    pc = np.r_[np.nan, dc[:-1]]
    tr = np.nanmax(np.c_[dh - dl, np.abs(dh - pc), np.abs(dl - pc)], 1)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    return pd.DatetimeIndex(days), g, atr, dc


def event(g, d, K, dist):
    """First overshoot of K in the window; returns (m, side) where side = sign(close - K) at the event."""
    O, C = g["open"][d], g["close"][d]
    s0 = np.sign(O[0] - K)
    if s0 == 0 or not np.isfinite(O[0]):
        return None
    for m in range(M0, M1 + 1):
        c = C[m]
        if np.isfinite(c) and np.sign(c - K) == -s0 and abs(c - K) >= dist:
            return m, np.sign(c - K)
    return None


def outcome(g, d, m, side, K):
    C, H, L = g["close"][d], g["high"][d], g["low"][d]
    c0 = C[m]
    out = {}
    for h in (H1, H2):
        k = min(m + h, 389)
        ck = C[k] if np.isfinite(C[k]) else np.nan
        out[f"tw{h}"] = -side * (ck / c0 - 1) * 1e4           # > 0 = moved back toward the level
    seg = slice(m + 1, min(m + 1 + H2, 390))
    out["touch60"] = bool(np.nanmin(L[seg]) <= K) if side > 0 else bool(np.nanmax(H[seg]) >= K)
    return out


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def welch(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    return float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))


def main():
    days, g, atr, dc = load_bars()
    S = pd.read_parquet(REPO / "data/cache/gex/SPY_gex_strikes.parquet")
    S["trade_date"] = pd.to_datetime(S.trade_date)
    close_by_day = pd.Series(dc, index=days)
    S = S.join(close_by_day.rename("S"), on="trade_date").dropna(subset=["S"])
    S = S[(S.strike >= 0.8 * S.S) & (S.strike <= 1.2 * S.S)]
    S["gex"] = (S.cg - S.pg) * 100 * S.S ** 2 * 0.01
    net = S.groupby("trade_date").gex.sum()
    by = dict(tuple(S.groupby("trade_date")))
    gdays = sorted(by)
    rows = []
    for d, t in enumerate(days):
        if d == 0 or not np.isfinite(atr[d]):
            continue
        prev = days[d - 1]
        if prev not in by:
            continue
        o = g["open"][d][0]
        if not np.isfinite(o):
            continue
        ch = by[prev]
        near = ch[(ch.strike >= o * 0.99) & (ch.strike <= o * 1.01)]
        if len(near) < 3:
            continue
        K = float(near.loc[near.gex.abs().idxmax(), "strike"])
        Km = float(ch.strike.values[np.argmin(np.abs(ch.strike.values - (2 * o - K)))])
        dist = 0.15 * atr[d]
        sign = np.sign(net.get(prev, np.nan))
        for lab, lvl in (("kstar", K), ("mirror", Km)):
            if lvl == o:
                continue
            e = event(g, d, lvl, dist)
            if e:
                rows.append(dict(day=t, level=lab, m=e[0], gex_sign=sign, **outcome(g, d, e[0], e[1], lvl)))
        mr = int(RNG.integers(M0, M1 + 1))
        c = g["close"][d][mr]
        if np.isfinite(c) and c != K:
            side = np.sign(c - K)
            rows.append(dict(day=t, level="random", m=mr, gex_sign=sign, **outcome(g, d, mr, side, K)))
    T = pd.DataFrame(rows)
    T = T[T.day <= pd.Timestamp("2026-03-01")]
    lines = [f"# GEX-strike revert [WL-5b] -- {T.day.nunique()} sessions {T.day.min().date()} -> {T.day.max().date()}"]
    for lab in ("kstar", "mirror", "random"):
        x = T[T.level == lab]
        lines.append(f"{lab:7s} events {len(x):5d} | toward +30 {x.tw30.mean():+.2f} bps (t {tstat(x.tw30):+.2f}) | "
                     f"+60 {x.tw60.mean():+.2f} bps (t {tstat(x.tw60):+.2f}) | touch60 {100 * x.touch60.mean():.1f}%")
    k, mi = T[T.level == "kstar"], T[T.level == "mirror"]
    h = lambda x: x.day < SPLIT
    lines.append("\n## PRIMARY: K* minus mirror, toward-return at +60 min (bps)")
    lines.append(f"diff {k.tw60.mean() - mi.tw60.mean():+.2f} bps | Welch t {welch(k.tw60, mi.tw60):+.2f} | halves "
                 f"{k[h(k)].tw60.mean() - mi[h(mi)].tw60.mean():+.2f} / {k[~h(k)].tw60.mean() - mi[~h(mi)].tw60.mean():+.2f}")
    lines.append(f"+30: diff {k.tw30.mean() - mi.tw30.mean():+.2f} (t {welch(k.tw30, mi.tw30):+.2f}) | touch60 diff "
                 f"{100 * (k.touch60.mean() - mi.touch60.mean()):+.1f}pp (t {welch(k.touch60.astype(float), mi.touch60.astype(float)):+.2f})")
    yk, ym = k.groupby(k.day.dt.year).tw60.mean(), mi.groupby(mi.day.dt.year).tw60.mean()
    lines.append("per year, K* - mirror +60 (bps):\n" + pd.DataFrame({"kstar": yk, "mirror": ym, "diff": yk - ym,
                 "n_k": k.groupby(k.day.dt.year).size()}).round(2).T.to_string())
    lines.append("\n## by prior-day GEX sign (secondary)")
    for s_, lab in ((1.0, "positive GEX"), (-1.0, "negative GEX")):
        a, b = k[k.gex_sign == s_], mi[mi.gex_sign == s_]
        lines.append(f"{lab:12s} K* n {len(a):5d} +60 {a.tw60.mean():+.2f} | mirror n {len(b):5d} +60 {b.tw60.mean():+.2f} | "
                     f"diff {a.tw60.mean() - b.tw60.mean():+.2f} (t {welch(a.tw60, b.tw60):+.2f}) | touch60 "
                     f"{100 * a.touch60.mean():.1f}% vs {100 * b.touch60.mean():.1f}%")
    print("\n".join(lines))
    T.to_csv(REPO / "data/studies/logs/gex_strike_revert_events.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

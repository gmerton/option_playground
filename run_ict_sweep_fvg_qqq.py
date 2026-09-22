#!/usr/bin/env python3
"""ICT liquidity sweep -> 1-min FVG retrace entry on QQQ, PAPER vs QUEUE-AWARE limit fills (2026-09-21).

PRE-REGISTERED: data/studies/ict_sweep_fvg_qqq_2026-09-21.md -- the rules below are that spec; do not tune them
against this script's output. Replicates the loose "as-traded" survivor from AI Pathways' 25,000-config ICT test
(video KML09tRtHM8) with one change that matters: a limit order fills only if price trades THROUGH it by a tick.

Usage: PYTHONPATH=src .venv/bin/python3 run_ict_sweep_fvg_qqq.py | tee data/studies/ict_sweep_fvg_qqq_2026-09-21.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
DATA = "data/cache/intraday_hist/QQQ_1min.parquet"
TICK = 0.01
SWING_N, SWING_LIFE = 3, 60          # fractal half-width, bars a swing stays live
FVG_WITHIN, LIMIT_LIFE = 10, 20       # bars after the sweep to find the gap; bars the limit stays live
GAP_MIN_PCT = 0.0001
TARGET_R = 2.0
COMM = 0.0035                          # $/share each side
T0, T1, TEND = 5, 360, 389             # minute-of-session: entries 09:35..15:30, flat at 15:59 close
RNG = np.random.default_rng(20260921)
PERIODS = [("2007-2016", "2007-01-01", "2017-01-01"), ("2017-2023", "2017-01-01", "2024-01-01"),
           ("2024-2026", "2024-01-01", "2027-01-01")]


def run_exit(o, h, l, c, k0, side, entry, stop, target):
    """Walk from bar k0 (the fill bar) to the close. Returns R (after commission) and exit bar.
    Fill bar counts too: a stop touched on the fill bar is a loss (conservative)."""
    risk = side * (entry - stop)
    if risk <= 0:
        return None
    n = len(c)
    for k in range(k0, n):
        hit_stop = (l[k] <= stop) if side > 0 else (h[k] >= stop)
        hit_tgt = (h[k] >= target) if side > 0 else (l[k] <= target)
        if k == k0:
            hit_tgt = hit_tgt and False              # never book the target on the fill bar itself (order unknown)
        if hit_stop:                                  # stop (and stop+target same bar = loss)
            px = stop - side * TICK
            if k > k0 and ((side > 0 and o[k] < stop) or (side < 0 and o[k] > stop)):
                px = o[k]                             # gapped through the stop
            return (side * (px - entry) - 2 * COMM) / risk, k
        if hit_tgt:
            return (side * (target - entry) - 2 * COMM) / risk, k
        if k >= TEND:
            break
    return (side * (c[min(TEND, n - 1)] - entry) - 2 * COMM) / risk, min(TEND, n - 1)


def day_signals(o, h, l, c, queue: bool):
    """Scan one session; returns trades [(side, fill_bar, entry, stop, target, R)]."""
    n = len(c)
    trades = []
    swings = {1: [], -1: []}        # side-to-fade -> list of [level, confirm_bar]; 1 = swing LOW (long fade)
    armed = []                      # pending sweeps: [side, sweep_bar, extreme]
    orders = []                     # live limits: [side, limit, stop, target, expiry_bar]
    busy_until = -1
    for k in range(n):
        # 1) confirm swings formed at j = k - SWING_N
        j = k - SWING_N
        if j >= SWING_N:
            if l[j] < l[j - SWING_N:j].min() and l[j] < l[j + 1:k + 1].min():
                swings[1].append([l[j], k])
            if h[j] > h[j - SWING_N:j].max() and h[j] > h[j + 1:k + 1].max():
                swings[-1].append([h[j], k])
        for s in (1, -1):
            swings[s] = [w for w in swings[s] if k - w[1] <= SWING_LIFE]
        # 2) live limit orders: fill / cancel (only when flat)
        if k > busy_until and orders:
            keep = []
            for side, lim, stp, tgt, exp in orders:
                if k > exp or k > T1:
                    continue
                if (side > 0 and h[k] >= tgt) or (side < 0 and l[k] <= tgt):
                    continue                                  # ran to the target unfilled: cancel
                thr = lim - side * TICK if queue else lim
                touched = (l[k] <= thr) if side > 0 else (h[k] >= thr)
                if touched and k > busy_until and T0 <= k <= T1:
                    entry = min(o[k], lim) if side > 0 else max(o[k], lim)
                    res = run_exit(o, h, l, c, k, side, entry, stp, tgt)
                    if res:
                        R, kx = res
                        trades.append((side, k, entry, stp, tgt, R))
                        busy_until = kx
                    continue
                keep.append([side, lim, stp, tgt, exp])
            orders = keep if k > busy_until else []
        # 3) sweeps of live swings
        for s in (1, -1):
            hitl = [w for w in swings[s] if (l[k] <= w[0] - TICK if s > 0 else h[k] >= w[0] + TICK)]
            if hitl:
                swings[s] = [w for w in swings[s] if w not in hitl]
                armed.append([s, k, l[k] if s > 0 else h[k]])
        # 4) armed sweeps: track the extreme, look for the fade-direction FVG
        still = []
        for s, kb, ext in armed:
            ext = min(ext, l[k]) if s > 0 else max(ext, h[k])
            if k - kb > FVG_WITHIN:
                continue
            if k >= kb + 2 and k >= 2:
                if s > 0 and l[k] > h[k - 2] and (l[k] - h[k - 2]) >= max(TICK, GAP_MIN_PCT * c[k]):
                    lim = round((l[k] + h[k - 2]) / 2, 2); stp = round(ext - TICK, 2)
                    orders.append([1, lim, stp, lim + TARGET_R * (lim - stp), k + LIMIT_LIFE]); continue
                if s < 0 and h[k] < l[k - 2] and (l[k - 2] - h[k]) >= max(TICK, GAP_MIN_PCT * c[k]):
                    lim = round((h[k] + l[k - 2]) / 2, 2); stp = round(ext + TICK, 2)
                    orders.append([-1, lim, stp, lim - TARGET_R * (stp - lim), k + LIMIT_LIFE]); continue
            still.append([s, kb, ext])
        armed = still
    return trades


def controls(o, h, l, c, trades, per=3):
    out = []
    for side, k, entry, stp, tgt, R in trades:
        stop_pct = (entry - stp) / entry
        for kk in RNG.choice(np.arange(T0, T1 + 1), size=per, replace=False):
            e = o[kk]
            s2 = e * (1 - stop_pct)
            t2 = e + TARGET_R * (e - s2)
            res = run_exit(o, h, l, c, int(kk), side, e, s2, t2)
            if res:
                out.append(res[0])
    return out


def summarise(T: pd.DataFrame, K: pd.DataFrame, label: str) -> dict:
    d = T.groupby("date").R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
    years = T.date.dt.year.nunique()
    row = dict(fill=label, trades=len(T), per_year=len(T) / years, days=T.date.nunique(), win=100 * (T.R > 0).mean(),
               meanR=T.R.mean(), t=t, ctrlR=K.R.mean(), edge=T.R.mean() - K.R.mean(), R_per_year=T.R.sum() / years,
               bps_per_trade=1e4 * (T.R * T.risk_pct).mean())
    for name, a, b in PERIODS:
        row[name] = T[(T.date >= a) & (T.date < b)].R.mean()
    return row


def main():
    df = pd.read_parquet(DATA)
    df["date"] = df.ts.dt.normalize()
    rows, allT = [], {}
    for queue, label in ((False, "PAPER (touch fills)"), (True, "QUEUE-AWARE (through by 1 tick)")):
        recs, crecs = [], []
        for day, g in df.groupby("date", sort=True):
            g = g[(g.ts.dt.hour * 60 + g.ts.dt.minute >= 570) & (g.ts.dt.hour * 60 + g.ts.dt.minute < 960)]
            if len(g) < 380:
                continue                                          # half days / gaps in the file
            o, h, l, c = (g[x].to_numpy() for x in ("open", "high", "low", "close"))
            tr = day_signals(o, h, l, c, queue)
            for side, k, entry, stp, tgt, R in tr:
                recs.append(dict(date=day, side=side, bar=k, entry=entry, R=R, risk_pct=abs(entry - stp) / entry))
            for R in controls(o, h, l, c, tr):
                crecs.append(dict(date=day, R=R))
        T, K = pd.DataFrame(recs), pd.DataFrame(crecs)
        allT[label] = T
        rows.append(summarise(T, K, label))
        print(f"{label}: {len(T):,} trades, {len(K):,} control trades", flush=True)
    R = pd.DataFrame(rows)
    print("\n== SUMMARY (R per trade after $0.0035/sh each side; control = same day, random minute, same side/stop%/2R) ==")
    print(R.round(3).to_string(index=False))
    q = R.iloc[1]
    ok = (q.meanR > 0) and (q.edge > 0) and (abs(q.t) >= 3) and (q.t > 0) and all(q[p[0]] > 0 for p in PERIODS)
    print(f"\nPASS (queue-aware, pre-registered bar): {'YES' if ok else 'no'}")
    for label, T in allT.items():
        T["year"] = T.date.dt.year
        print(f"\n{label} by year (mean R / trades):")
        print(T.groupby("year").R.agg(["mean", "size"]).round(3).T.to_string())
    pd.concat([T.assign(fill=lbl) for lbl, T in allT.items()]).to_parquet("data/cache/ict_sweep_fvg_qqq_trades.parquet", index=False)
    R.to_csv("data/studies/ict_sweep_fvg_qqq_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

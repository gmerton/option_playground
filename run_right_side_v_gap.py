#!/usr/bin/env python3
"""
Right side of the V on the index opening-gap fade (pre-registered 2026-09-30, BEFORE running; TEST_INDEX §10 row
"Right side of the V", spec data/lance_breitstein/principles/right-side-of-the-v.md).

Breitstein: the same trade has a higher EV after "the turn is in" (break of the prior bar's high for a long), because
a real stop exists (the session extreme) and the win rate rises. The daily form is already answered (confirmation
ladder 2026-09-25: confirmation lifts holds 13% -> 59% but charges 1-for-1 in price, fwd flat). Untested: the intraday
gap fade, where the repo's daily gap study could not order stop vs target (Carter KB opening-gap-fade.md).

DATA   data/cache/intraday_hist/{SPY,QQQ}_1min.parquet (RTH 1-min, 2007-01 -> 2026-09). PRIMARY = SPY; QQQ secondary.
EVENT  gap = 09:30 open / prior session's last close - 1; |gap| >= 0.5 x ATR14 (daily, through the prior session).
       Fade direction: gap down -> long, gap up -> short. Target = the prior close (gap fill). Exit at 15:59 otherwise.
       Fills: entry at a 5-min bar's closing 1-min close; stop/target on 1-min highs/lows in minute order (stop fills at
       the stop or the bar open if gapped through; a minute that touches both = STOP, conservative); 1 bp per side.
ARMS   A  LEFT side: fade at the close of the first 5-min bar (09:34), no stop (his point: no true stop exists).
       A_s LEFT side with a stop of the SAME % width B uses that day (width-matched), from A's entry.
       B  RIGHT side: the first 5-min bar in 09:35-11:00 whose close breaks the PRIOR 5-min bar's high (long) / low
          (short), with the gap still unfilled at that close. Stop = the session extreme so far (low for a long).
       R  RANDOM: same day, same direction, entry at a random 5-min close in 09:35-11:00 with the gap unfilled, stop =
          session extreme so far, same exits; 50 draws averaged. Isolates the TRIGGER from "entering later".
PRIMARY  B - A on the days B fires, return in bp of price, paired by day, SPY. (A on those days is conditioned on a
         later turn happening, which FLATTERS A -> conservative for B.)
SECONDARY B - R (the trigger itself, Stage-A style control), B - A_s, win rates (his claim is win rate), QQQ, gaps
         >= 0.25 ATR, A on all event days.
BAR    |t| >= 3, halves 2007-2016 / 2017-2026 same sign, per-year sign table. Sidak over the 3 SPY secondaries
       (|t| >= 2.39) for B - R and B - A_s.
Prior: low-moderate. Stage A: intraday triggers ~ a random later minute; the ladder: confirmation is paid for in price.

Run: PYTHONPATH=src .venv/bin/python3 run_right_side_v_gap.py   (log -> data/studies/logs/right_side_v_gap.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/right_side_v_gap.log"
COST = 1e-4
NRAND = 50
SPLIT = 2017


def sim(lo, hi, op, cl, k0, side, entry, stop, target):
    """1-min bars from index k0+1 to the end; returns exit price."""
    for k in range(k0 + 1, len(cl)):
        if side > 0:
            if stop is not None and lo[k] <= stop:
                return min(stop, op[k])
            if hi[k] >= target:
                return max(target, op[k]) if op[k] > target else target
        else:
            if stop is not None and hi[k] >= stop:
                return max(stop, op[k])
            if lo[k] <= target:
                return min(target, op[k]) if op[k] < target else target
    return cl[-1]


def ret_bp(side, entry, exitp):
    return 1e4 * (side * (exitp / entry - 1) - 2 * COST)


def run_symbol(sym: str, gap_k: float, rng) -> pd.DataFrame:
    d = pd.read_parquet(REPO / f"data/cache/intraday_hist/{sym}_1min.parquet")
    d["ts"] = pd.to_datetime(d.ts)
    d = d[(d.ts.dt.time >= pd.Timestamp("09:30").time()) & (d.ts.dt.time <= pd.Timestamp("15:59").time())]
    d["day"] = d.ts.dt.normalize()
    daily = d.groupby("day").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), n=("close", "size"))
    pc = daily.c.shift(1)
    tr = pd.concat([daily.h - daily.l, (daily.h - pc).abs(), (daily.l - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    rows = []
    for day, g in d.groupby("day"):
        if day not in daily.index or not np.isfinite(atr.get(day, np.nan)) or daily.n[day] < 300:
            continue
        prev = pc[day]
        o = g.open.iloc[0]
        gap = o / prev - 1
        if abs(o - prev) < gap_k * atr[day]:
            continue
        side = -1 if gap > 0 else 1
        t = g.ts.dt.time.values
        lo, hi, op, cl = g.low.values, g.high.values, g.open.values, g.close.values
        mins = (g.ts - day).dt.total_seconds().values / 60 - 570      # minutes since 09:30
        # 5-min bars over 09:30-11:00
        b5 = []
        for s in range(0, 90, 5):
            idx = np.where((mins >= s) & (mins < s + 5))[0]
            if len(idx):
                b5.append((idx[-1], hi[idx].max(), lo[idx].min(), cl[idx[-1]]))
        if len(b5) < 3:
            continue
        unfilled = lambda px: (px < prev) if side > 0 else (px > prev)
        # A: first 5-min close
        kA, _, _, pA = b5[0]
        if not unfilled(pA):
            continue
        # B: first trigger in 09:35-11:00
        kB = None
        for n in range(1, len(b5)):
            k, h5, l5, c5 = b5[n]
            ph, pl = b5[n - 1][1], b5[n - 1][2]
            if ((side > 0 and c5 > ph) or (side < 0 and c5 < pl)) and unfilled(c5):
                kB, pB = k, c5
                break
        rec = dict(day=day, gap_bp=1e4 * gap, gap_atr=abs(o - prev) / atr[day], side=side)
        rec["A_all"] = ret_bp(side, pA, sim(lo, hi, op, cl, kA, side, pA, None, prev))
        if kB is not None:
            ext = lo[:kB + 1].min() if side > 0 else hi[:kB + 1].max()
            width = abs(pB / ext - 1)
            rec["B"] = ret_bp(side, pB, sim(lo, hi, op, cl, kB, side, pB, ext, prev))
            rec["B_win"] = rec["B"] > 0
            rec["A"] = rec["A_all"]
            sA = pA * (1 - side * width)
            rec["A_s"] = ret_bp(side, pA, sim(lo, hi, op, cl, kA, side, pA, sA, prev))
            rec["stop_bp"] = 1e4 * width
            rec["entry_min"] = mins[kB]
            cands = [(k, c5) for (k, _, _, c5) in b5[1:] if unfilled(c5)]
            acc = []
            for _ in range(NRAND):
                k, c5 = cands[rng.integers(len(cands))]
                ext_r = lo[:k + 1].min() if side > 0 else hi[:k + 1].max()
                acc.append(ret_bp(side, c5, sim(lo, hi, op, cl, k, side, c5, ext_r, prev)))
            rec["R"] = float(np.mean(acc))
        rows.append(rec)
    return pd.DataFrame(rows)


def tday(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 else np.nan


def report(sym, T, L, primary):
    E = T.dropna(subset=["B"]).copy()
    yr = E.day.dt.year
    h1 = yr < SPLIT
    L.append(f"\n## {sym}: {len(T):,} gap days, B fires on {len(E):,} ({100 * len(E) / len(T):.0f}%); "
             f"median B entry {E.entry_min.median():.0f} min after the open, median stop {E.stop_bp.median():.0f} bp")
    L.append(f"  means (bp/trade): A_all {T.A_all.mean():+.2f} (all gap days) | on B days: A {E.A.mean():+.2f}, "
             f"A_s {E.A_s.mean():+.2f}, B {E.B.mean():+.2f}, R {E.R.mean():+.2f}")
    L.append(f"  win rates on B days: A {100 * (E.A > 0).mean():.1f}%  A_s {100 * (E.A_s > 0).mean():.1f}%  "
             f"B {100 * (E.B > 0).mean():.1f}%")
    out = {}
    for name, a, b in [("PRIMARY B - A" if primary else "B - A", "B", "A"), ("B - R (trigger vs random minute)", "B", "R"),
                       ("B - A_s (width-matched left side)", "B", "A_s")]:
        dd = E[a] - E[b]
        ys = dd.groupby(yr).mean()
        L.append(f"  {name:36s} {dd.mean():+.2f} bp  t {tday(dd):+.2f}  halves {dd[h1].mean():+.2f} / {dd[~h1].mean():+.2f}  "
                 f"years + {int((ys > 0).sum())}/{len(ys)}")
        out[name] = dd
    pr = list(out.values())[0]
    L.append("  per year B - A: " + " ".join(f"{y}:{v:+.1f}" for y, v in pr.groupby(yr).mean().items()))
    return E, pr


def main():
    rng = np.random.default_rng(20260930)
    L = ["# Right side of the V: index opening-gap fade (pre-registration in the docstring)"]
    res = {}
    for sym, k, prim in (("SPY", 0.5, True), ("QQQ", 0.5, False)):
        T = run_symbol(sym, k, rng)
        T.to_parquet(REPO / f"data/studies/logs/right_side_v_gap_{sym}.parquet", index=False)
        res[sym] = report(f"{sym} |gap| >= {k} ATR", T, L, prim)
    T = run_symbol("SPY", 0.25, rng)
    report("SPY |gap| >= 0.25 ATR (secondary)", T, L, False)
    print("\n".join(L))
    E, pr = res["SPY"]
    h1 = E.day.dt.year < SPLIT
    print(f"\nPRIMARY SPY B - A: {pr.mean():+.2f} bp t {tday(pr):+.2f} halves {pr[h1].mean():+.2f}/{pr[~h1].mean():+.2f} n {len(pr)}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

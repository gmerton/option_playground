#!/usr/bin/env python3
"""
Swing-low structural trail vs the house 20-EMA trail (pre-registered 2026-09-30, BEFORE running; spec #3 in
data/traderlion/videos/interviews/2026-09-13_-dv_2h61a2o/notes.md; Ariel [1:43-1:45] "trail on structure (higher lows),
not moving averages").

POOLS   as run_trail_cost_exposure.py / run_rs_loss_exit.py (run_precision_tier_control.build): entry = breakout CLOSE +
        slip, initial stop = breakout-day low judged on the CLOSE, 2% floor / 25% cap, 60-session cap, 2019-10 -> 2026-09.
        PRIMARY = precision-tier pool; secondary = generic pool (ADR >= 3).
ARMS    BASE = 20-EMA close trail + initial stop (house).
        SW   = swing-low trail: pivot low at bar p = low[p] < min(low[p-3..p-1]) and low[p] <= min(low[p+1..p+3]);
               confirmed (usable) from the close of p+3. Stop for the close of day k = max(initial stop, every pivot
               level confirmed through day k-1) -- ratchets up, never down. Exit on the first close below it.
        Exploratory only (no verdict): pivot width 2 and 5.
CONTROL (governs; the RS-loss exit's 9/30 "pass" was exposure): EXPOSURE-MATCHED. Whichever arm exits first is extended
        with beta x SPY from its exit close to the other arm's exit close (10 bp in and out), beta = 252d pre-entry beta
        clipped [0.5, 2.5] (exactly run_trail_cost_exposure's fill). So both arms are exposed for the same days.
PRIMARY SW - BASE, exposure-matched, % per trade, precision pool, paired, t on entry-date cluster means.
        BAR: |t| >= 3, both halves (split 2023-01-01) same sign, same sign in a majority of years.
REPORTED raw SW - BASE; SW - RAND (same trade, exit at a hold length drawn from SW's own hold distribution, initial stop
        still live, 100 draws averaged) = does the structure pick better days than a same-length random exit;
        share of trades where the arms differ; held days; generic pool; widths 2 / 5.
Prior: low. A looser trail wins raw on exposure in this bull sample; trail_bar (prior-bar low) never beat the 20 EMA.
Local (cached panel, minutes).

Run: PYTHONPATH=src .venv/bin/python3 run_swing_low_trail.py   (log -> data/studies/logs/swing_low_trail.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/swing_low_trail.log"
SLIP, HOLD, FLOOR, START, SPLIT, FILL_COST = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01", 0.0010
NRAND = 100


def pivot_levels(Lo: pd.DataFrame, w: int) -> np.ndarray:
    """Level of the most recent pivot low confirmed by the close of each day (NaN before the first)."""
    left = Lo.shift(1).rolling(w).min()
    right = Lo.shift(-w).rolling(w).min()
    piv = (Lo < left) & (Lo <= right)
    return Lo.where(piv).shift(w).ffill().values          # pivot at p becomes usable at p + w


def walk(C, E20, LV, stop0, i, j, arm):
    stop = stop0
    end = min(i + HOLD, len(C) - 1)
    k = i
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop:
            return k
        if arm == "BASE" and np.isfinite(E20[k, j]) and c < E20[k, j]:
            return k
        if arm == "SW" and np.isfinite(LV[k, j]):
            stop = max(stop, LV[k, j])                      # used from the next close
    return k


def tclu(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def run_pool(label, mask, P, S, B, lines, tag, primary):
    C, Lo, E20 = P.close.values, P.low.values, P.ema20.values
    LV = {w: pivot_levels(P.low, w) for w in (3, 2, 5)}
    m = mask[mask.index >= START]
    off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP)
        stop0 = Lo[i, j]
        risk = entry - stop0
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C):
            continue
        beta = float(np.clip(B[i, j], 0.5, 2.5)) if np.isfinite(B[i, j]) else 1.0
        kb = walk(C, E20, None, stop0, i, j, "BASE")
        ks = {w: walk(C, E20, LV[w], stop0, i, j, "SW") for w in (3, 2, 5)}
        r = lambda k: C[k, j] * (1 - SLIP) / entry - 1

        def matched(k_a, k_b):
            """arm a's return extended with beta x SPY to max(k_a, k_b)."""
            ra = r(k_a)
            if k_a < k_b:
                return (1 + ra) * (1 + beta * (S[k_b] / S[k_a] - 1) - 2 * FILL_COST) - 1
            return ra
        rec = dict(date=P.close.index[i], sym=P.close.columns[j], beta=beta, held_b=kb - i, held_sw=ks[3] - i,
                   BASE=100 * r(kb), SW=100 * r(ks[3]), BASE_m=100 * matched(kb, ks[3]), SW_m=100 * matched(ks[3], kb))
        for w in (2, 5):
            rec[f"SW{w}"] = 100 * r(ks[w])
            rec[f"SW{w}_m"] = 100 * matched(ks[w], kb)
            rec[f"BASE_m{w}"] = 100 * matched(kb, ks[w])
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["date"] = pd.to_datetime(T.date)

    # random same-length exit control (hold lengths drawn from SW's own distribution, initial stop live)
    rng = np.random.default_rng(20260930)
    pool = T.held_sw.values
    idx = {d: n for n, d in enumerate(P.close.index)}
    col = {s: n for n, s in enumerate(P.close.columns)}
    rand = np.zeros(len(T))
    for n, rr in enumerate(T.itertuples()):
        i, j = idx[rr.date], col[rr.sym]
        entry = C[i, j] * (1 + SLIP)
        stop0 = Lo[i, j]
        end = min(i + HOLD, len(C) - 1)
        path = C[i + 1:end + 1, j]
        hit = np.where(path < stop0)[0]
        kstop = i + 1 + hit[0] if len(hit) else end
        acc = 0.0
        for h in rng.choice(pool, NRAND):
            k = min(i + max(int(h), 1), kstop, end)
            px = C[k, j] if np.isfinite(C[k, j]) else C[i + rr.held_b, j]
            acc += px * (1 - SLIP) / entry - 1
        rand[n] = 100 * acc / NRAND
    T["RAND"] = rand

    h1 = T.date < SPLIT
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates; "
                 f"arms differ on {100 * (T.held_b != T.held_sw).mean():.0f}% of trades; held BASE {T.held_b.mean():.1f} "
                 f"vs SW {T.held_sw.mean():.1f} sessions; SW exits earlier on {100 * (T.held_sw < T.held_b).mean():.0f}%")
    res = None
    for name, a, b in [("PRIMARY  SW - BASE, exposure-matched", "SW_m", "BASE_m"),
                       ("  raw    SW - BASE", "SW", "BASE"),
                       ("         SW - RAND (same-length random exit)", "SW", "RAND"),
                       ("  expl   SW(w2) - BASE, exposure-matched", "SW2_m", "BASE_m2"),
                       ("  expl   SW(w5) - BASE, exposure-matched", "SW5_m", "BASE_m5")]:
        d = T[a] - T[b]
        yr = d.groupby(T.date.dt.year).mean()
        t = tclu(d, T.date)
        ys = int((np.sign(yr) == np.sign(d.mean())).sum())
        lines.append(f"  {name:44s} {d.mean():+.3f}pp  t {t:+.2f}  halves {d[h1].mean():+.3f} / {d[~h1].mean():+.3f}  "
                     f"years same sign {ys}/{len(yr)}")
        if res is None:
            res = dict(m=d.mean(), t=t, h1=d[h1].mean(), h2=d[~h1].mean(), ys=ys, ny=len(yr), yr=yr)
    for a in ("BASE", "SW", "RAND"):
        x = T[a]
        lines.append(f"  {a:5s} mean {x.mean():+.2f}%  median {x.median():+.2f}%  win {100 * (x > 0).mean():.0f}%  "
                     f"p5 {x.quantile(.05):+.1f}%  top-decile mean {x[x >= x.quantile(.9)].mean():+.1f}%")
    lines.append("  per year PRIMARY: " + " ".join(f"{y}:{v:+.2f}" for y, v in res["yr"].items()))
    if primary:
        ok = abs(res["t"]) >= 3 and np.sign(res["h1"]) == np.sign(res["h2"]) and res["ys"] > res["ny"] / 2
        lines.append(f"  BAR (primary): {'MET' if ok else 'NOT MET'}")
    T.to_parquet(REPO / f"data/studies/logs/swing_low_trail_{tag}.parquet", index=False)
    return res


def main():
    P, brk, prec = build()
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "close"])
    spy = raw[raw.ticker == "SPY"].assign(date=lambda d: pd.to_datetime(d.date)).set_index("date").close.sort_index()
    S = spy.reindex(P.close.index).ffill().values
    R = P.close.pct_change(fill_method=None)
    rs = pd.Series(S, index=P.close.index).pct_change()
    B = R.rolling(252, min_periods=150).cov(rs).div(rs.rolling(252, min_periods=150).var(), axis=0).shift(1).values
    lines = ["# Swing-low structural trail vs 20-EMA trail (pre-registration in the docstring)"]
    r = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, S, B, lines, "precision", True)
    run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, S, B, lines, "generic", False)
    print("\n".join(lines))
    print(f"\nPRIMARY SW - BASE exposure-matched (precision): {r['m']:+.3f}pp t {r['t']:+.2f} halves "
          f"{r['h1']:+.3f}/{r['h2']:+.3f} years {r['ys']}/{r['ny']}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

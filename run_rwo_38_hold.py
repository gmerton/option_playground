#!/usr/bin/env python3
"""
Right Way Options "3/8 trap": enter on the 3/8 EMA CROSS vs wait for the cross to HOLD (pre-registered 2026-10-05,
BEFORE any outcome was computed).

Origin: Doug Campbell, Right Way Options (@RightWayOptions; videos -xPjYd4WKY4 "Don't Trade the Cross -- Trade the
Hold", jJdUDjG_kiM "My Favorite Trade Patterns", LJFqaNHLWeM "My Favorite Indicators"). His one quantified claim:
"crossovers will only work about 50% of the time ... when you let the crossover occur and then hold the higher low ...
70 to 75% probability of success" (3 = 3-period EMA, 8 = 8-period EMA, "trendinator" = 17 EMA). Daily charts are his
swing frame. A WIN RATE is not an edge: the house finding is that waiting raises the hit rate by deselecting the
runners (pullback-wait INVERTED t -2.01, breakout-vs-EMA-zone -0.74pp t -2.56, reclaim NULL). So the PRIMARY is the
per-event return of the two POLICIES, not the win rate; the win rates are reported as the replication of his claim.

Universe: liquid_panel_2009 (⚠ survivors -- both arms share the bias; the comparison is paired on the same events),
  eligible (ADDV >= $50M, px >= $5) and ADR20 >= 3% on the cross day, 2010-01-01 -> 2026-06-30.
EMAs on closes: E3, E8, E17 (span 3/8/17, adjust=False).
EVENT: cross day c = first close with E3 > E8 after a close with E3 <= E8. A new cross inside an open CROSS-arm trade on
  the same name is skipped (one live event per name).
STRUCTURAL STOP (his "support"; fixed per event, both arms): lowest low of sessions c-10 .. c.
ARMS (same event set; costs 0.10% a side):
  CROSS   enter at close c.
  HOLD3   enter at close c+3 only if E3 > E8 on every close c..c+3 AND no close < stop in c+1..c+3; otherwise NO TRADE
          (the event earns 0, capital idle).
EXIT (both arms, from their own entry): first close < stop, or first close with E3 < E8 (his "momentum shifted"), max
  40 sessions. METRIC = % return per event after costs; R (risk = entry - stop, floor 2%, cap 20) second.
PRIMARY: per event, d = ret(HOLD3 policy) - ret(CROSS); mean by date, t over dates. Bar: |t| >= 3, both halves (split
  2018-01-01) the same sign as the mean, a majority of years. HOLD3 BETTER -> SUPPORTED/CERTIFIED per the verdict scheme;
  INVERTED if t <= -3 under the same conditions.
CLAIM REPLICATION (descriptive, no verdict): win rate (ret > 0) of CROSS on all events vs of HOLD3 on the held events.
  "Replicates" = CROSS 45-55% AND HOLD3 >= 65%.
DECOMPOSITION (descriptive): on HELD events, CROSS-entry vs HOLD3-entry return (the price paid for waiting); on FAILED
  events, the CROSS return (the loss avoided); held share.
Exploratory (Sidak k = 5, no verdict of their own):
  X1 HOLD2;  X2 HOLD5;  X3 HOLD3 + trend stack E8 > E17 at entry;  X4 HOLD3 + higher low (min low c+1..c+3 > the
  stop);  X5 CROSS only when E8 > E17 at c (trend context) vs CROSS.
Prior: LOW -- every "wait for confirmation" entry on this book has paid less than taking the signal.

Run: PYTHONPATH=src .venv/bin/python3 run_rwo_38_hold.py   (log -> data/studies/logs/rwo_38_hold.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from lib.studies.pattern_test import load_panel

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/rwo_38_hold.log"
START, UNTIL, SPLIT = "2010-01-01", "2026-06-30", "2018-01-01"
SLIP, HOLD, STOP_LB, ADR_MIN = 0.001, 40, 10, 3.0
K_EXPL = 5


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def trade(C, E3, E8, j: int, i: int, stop: float) -> tuple[float, int] | None:
    """Enter at close i; exit on the first close < stop or with E3 < E8, max HOLD. (% return, exit index)."""
    n = len(C)
    if i + 1 >= n or not np.isfinite(C[i, j]):
        return None
    entry = C[i, j] * (1 + SLIP)
    k_exit = min(i + HOLD, n - 1)
    for k in range(i + 1, min(i + 1 + HOLD, n)):
        c = C[k, j]
        if np.isfinite(c) and (c < stop or E3[k, j] < E8[k, j]):
            k_exit = k
            break
    px = C[k_exit, j]
    return (100 * (px * (1 - SLIP) / entry - 1), k_exit) if np.isfinite(px) else None


def held(C, L, E3, E8, j: int, c: int, n: int, stop: float) -> bool:
    if c + n >= len(C):
        return False
    w = slice(c, c + n + 1)
    return bool(np.all(E3[w, j] > E8[w, j]) and np.all(C[c + 1:c + n + 1, j] >= stop))


def events(P) -> pd.DataFrame:
    C, L = P.close.values, P.low.values
    E3 = P.close.ewm(span=3, adjust=False).mean().values
    E8 = P.close.ewm(span=8, adjust=False).mean().values
    E17 = P.close.ewm(span=17, adjust=False).mean().values
    up = E3 > E8
    cross = up[1:] & ~up[:-1]
    elig, adr, idx = P.elig.values, P.adr.values, P.close.index
    lo, hi = idx.searchsorted(pd.Timestamp(START)), idx.searchsorted(pd.Timestamp(UNTIL), side="right")
    rows = []
    for j in range(C.shape[1]):
        busy = -1
        for c in np.where(cross[:, j])[0] + 1:
            if c < max(lo, STOP_LB) or c >= hi or c <= busy or not elig[c, j] or not adr[c, j] >= ADR_MIN:
                continue
            stop = np.nanmin(L[c - STOP_LB:c + 1, j])
            if not np.isfinite(stop) or stop >= C[c, j]:
                continue
            a = trade(C, E3, E8, j, c, stop)
            if a is None:
                continue
            busy = a[1]
            r = dict(date=idx[c], sym=P.close.columns[j], cross=a[0],
                     R_cross=float(np.clip(a[0] / max(100 * (C[c, j] - stop) / C[c, j], 2), -20, 20)),
                     stack_c=E8[c, j] > E17[c, j])
            for n in (2, 3, 5):
                h = held(C, L, E3, E8, j, c, n, stop)
                b = trade(C, E3, E8, j, c + n, stop) if h else None
                r[f"held{n}"] = h and b is not None
                r[f"hold{n}"] = b[0] if r[f"held{n}"] else 0.0
                if n == 3:
                    r["stack3"] = r["held3"] and E8[c + 3, j] > E17[c + 3, j]
                    r["hl3"] = r["held3"] and np.nanmin(L[c + 1:c + 4, j]) > stop
                    r["R_hold3"] = (float(np.clip(b[0] / max(100 * (C[c + 3, j] - stop) / C[c + 3, j], 2), -20, 20))
                                    if r["held3"] else 0.0)
            rows.append(r)
    return pd.DataFrame(rows)


def paired(T: pd.DataFrame, d: pd.Series) -> dict:
    dd = d.groupby(T.date).mean()
    yr = dd.groupby(dd.index.year).mean()
    return dict(n=len(d), dates=len(dd), mean=dd.mean(), t=tstat(dd), h1=dd[dd.index < SPLIT].mean(),
                h2=dd[dd.index >= SPLIT].mean(), ypos=int((yr > 0).sum()), yn=len(yr), _yr=yr)


def fmt(r: dict) -> str:
    return (f"n {r['n']:,} events / {r['dates']:,} dates | diff {r['mean']:+.3f}pp t {r['t']:+.2f} | "
            f"halves {r['h1']:+.3f}/{r['h2']:+.3f} | years + {r['ypos']}/{r['yn']}")


def main():
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    T = events(P)
    print(f"# RWO 3/8 trap: cross vs hold -- {len(T):,} cross events, {T.sym.nunique()} names, "
          f"{T.date.min().date()} -> {T.date.max().date()} (after 0.10%/side)")

    h = T.held3
    print("\n## CLAIM REPLICATION (win rate = ret > 0)")
    print(f"CROSS, all events:  win {100 * (T.cross > 0).mean():.1f}% | mean {T.cross.mean():+.2f}%")
    print(f"HOLD3, held events: win {100 * (T.hold3[h] > 0).mean():.1f}% | mean {T.hold3[h].mean():+.2f}% | "
          f"held share {100 * h.mean():.1f}%")
    rep = 45 <= 100 * (T.cross > 0).mean() <= 55 and 100 * (T.hold3[h] > 0).mean() >= 65
    print(f"his 50% vs 70-75% claim replicates: {'YES' if rep else 'NO'}")

    print("\n## PRIMARY: HOLD3 policy - CROSS, per event (% after costs), t over dates")
    P1 = paired(T, T.hold3 - T.cross)
    print(fmt(P1))
    print("per year: " + " ".join(f"{y}:{v:+.2f}" for y, v in P1["_yr"].items()))
    R1 = paired(T, T.R_hold3 - T.R_cross)
    print(f"R (floor 2%, cap 20): diff {R1['mean']:+.3f} t {R1['t']:+.2f}")
    years_agree = (P1["ypos"] > P1["yn"] / 2) if P1["mean"] > 0 else (P1["ypos"] < P1["yn"] / 2)
    ok = abs(P1["t"]) >= 3 and np.sign(P1["h1"]) == np.sign(P1["h2"]) == np.sign(P1["mean"]) and years_agree
    print(f"bar: {'PASSES' if ok and P1['mean'] > 0 else 'INVERTED' if ok else 'NOT MET'}")

    print("\n## DECOMPOSITION (descriptive)")
    print(f"held events ({h.sum():,}): CROSS-entry {T.cross[h].mean():+.2f}% vs HOLD3-entry {T.hold3[h].mean():+.2f}% "
          f"-> cost of waiting {T.hold3[h].mean() - T.cross[h].mean():+.2f}pp")
    print(f"failed events ({(~h).sum():,}): CROSS {T.cross[~h].mean():+.2f}% (the loss HOLD3 avoids), "
          f"win {100 * (T.cross[~h] > 0).mean():.1f}%")
    q = T.cross.quantile(0.9)
    print(f"CROSS top-decile winners (> {q:.1f}%): {100 * h[T.cross > q].mean():.1f}% would have been HOLD3-held")

    thr = norm.ppf(1 - (1 - 0.95 ** (1 / K_EXPL)) / 2)
    print(f"\n## exploratory (Sidak k = {K_EXPL}, |t| >= {thr:.2f}; no verdict of their own)")
    expl = {"X1 HOLD2 - CROSS": T.hold2 - T.cross,
            "X2 HOLD5 - CROSS": T.hold5 - T.cross,
            "X3 HOLD3+stack(E8>E17) - CROSS": T.hold3.where(T.stack3, 0.0) - T.cross,
            "X4 HOLD3+higher low - CROSS": T.hold3.where(T.hl3, 0.0) - T.cross,
            "X5 CROSS if E8>E17 at c - CROSS": T.cross.where(T.stack_c, 0.0) - T.cross}
    for name, d in expl.items():
        print(f"  {name:34s} " + fmt(paired(T, d)))
    T.to_csv(REPO / "data/studies/logs/rwo_38_hold_events.csv", index=False)
    return P1


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

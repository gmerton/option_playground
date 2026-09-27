#!/usr/bin/env python3
"""
EXIT SPEED BY MARKET STATE AT ENTRY: should breakout exits be faster when the tape is unstable? (pre-registered
2026-09-26, before any code or run; Gabe: calibrating exits to market conditions -- "perhaps in some markets we exit
faster". The FEEDBACK version of the same idea -- retuning knobs from recent results -- is an arm of the queued
simulated-adaptive-trader row, not this test.) Run 2026-09-26 on Gabe's go ("run #4"); design unchanged.

WHY NEW. The dealer-gamma regime is the ledger's strongest certified MECHANISM: negative SPY net gamma -> ~+8%
realised vol beyond VIX (t 7.7). It was tested on the 7-DTE book straddles (NULL, t 0.55) and on 1-day SPY option
structures, never on how long to hold a stock breakout. Every exit test so far used one exit rule for all states.

POOL     the precision-tier house breakouts and the generic pool (ADR >= 3), built by run_precision_tier_control.build()
         exactly as run_vol_decay_exit.py / run_qullamaggie_exit.py: entry = breakout CLOSE + slip, initial stop =
         breakout-day low on the CLOSE, 2% risk floor, 25% cap, 60-session max hold, 2019-10 -> 2026-02 (the SPY GEX
         series ends with v3 bid/ask).
STATE    at the entry close, declared now (no look-ahead):
         GAMMA  SPY net GEX sign from run_gex_regime_pin.gex_series("SPY") -- NEG vs POS.   <- PRIMARY state
         VIX    VIX close tercile over the trailing 252 sessions (exploratory state).
ARMS     every arm on the SAME trades, initial stop kept, exits judged on the close:
         BASE    the house 20-EMA close trail
         FAST    10-EMA close trail
         TIME10  exit at the 10th session's close (or earlier at the stop)
         SLOW    hold to the stop or 60 sessions, no trail (the queued STOP_ONLY arm)
PRIMARY  the interaction on the precision pool, in % return per trade (not R):
           I = [FAST - BASE | NEG gamma] - [FAST - BASE | POS gamma]
         Paired per trade, t on entry-date cluster means, I = difference of the two cluster means with SE from the two
         independent date sets. The idea predicts I > 0 (faster exits help more in negative gamma).
         BAR: t >= 3, both halves (split 2023-01) the same sign, a majority of years the same sign where both states
         occur. Secondary (declared): the same I for TIME10 and SLOW, and all three on the generic pool; 6 cells
         -> Sidak |t| ~ 2.6 for the secondaries; the house 3 governs the primary.
REPORTED per state: each arm's mean %, win rate, held days, top-decile winners' mean (does the fast exit cut the tail
         in NEG gamma less than in POS?), n trades / dates per state, per year.
DEPENDENCY  run AFTER the queued "does the 20-EMA trail cost money? STOP_ONLY vs BASE, exposure-matched" test: if the
         trail itself loses once beta is removed, the baseline arm changes and this is re-read against SLOW.
PRIOR    low-moderate. Gamma forecasts SPY vol, but a single stock's breakout path is mostly idiosyncratic; the NULL on
         the book straddles says market gamma didn't separate single-name outcomes there.
Local vs cloud: local (cached liquid panel + cached SPY GEX strikes; minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_exit_speed_by_state.py   (log -> data/studies/logs/exit_speed_by_state.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build
import run_gex_regime_pin as G

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/exit_speed_by_state.log"
SLIP, HOLD, FLOOR, START, SPLIT = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01"
ARMS = ["BASE", "FAST", "TIME10", "SLOW"]


def simulate(C, L, E20, E10, i, j, arm):
    entry = C[i, j] * (1 + SLIP); stop = L[i, j]
    end = min(i + HOLD, len(C) - 1); k = i
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop:
            break
        if arm == "BASE" and np.isfinite(E20[k, j]) and c < E20[k, j]:
            break
        if arm == "FAST" and np.isfinite(E10[k, j]) and c < E10[k, j]:
            break
        if arm == "TIME10" and k - i >= 10:
            break
    return 100 * (C[k, j] * (1 - SLIP) / entry - 1), k - i


def cl(x: pd.Series, d: pd.Series):
    g = x.groupby(d).mean()
    return g.mean(), g.std(ddof=1) / np.sqrt(len(g)), len(g)


def interaction(T: pd.DataFrame, arm: str, state: str = "NEG") -> tuple[float, float, int, int]:
    d = T[arm] - T.BASE
    a, b = T[state], ~T[state]
    ma, sa, na = cl(d[a], T.date[a]); mb, sb, nb = cl(d[b], T.date[b])
    return ma - mb, (ma - mb) / np.sqrt(sa ** 2 + sb ** 2), na, nb


def trades(mask, P, gam, vterc):
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    E10 = P.close.ewm(span=10, adjust=False).mean().values
    m = mask[(mask.index >= START) & (mask.index <= G.END)]
    off = mask.index.get_loc(m.index[0])
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP); risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C) \
                or not np.isfinite(ADR[i, j]):
            continue
        dt = P.close.index[i]
        g = gam.get(dt, np.nan)
        if not np.isfinite(g):
            continue
        rec = dict(date=dt, sym=P.close.columns[j], NEG=bool(g < 0), vt=vterc.get(dt, np.nan))
        for a in ARMS:
            rec[a], rec[a + "_held"] = simulate(C, L, E20, E10, i, j, a)
        rows.append(rec)
    T = pd.DataFrame(rows); T["date"] = pd.to_datetime(T.date)
    return T


def report(T, label, lines, primary):
    lines.append(f"\n## {label}: {len(T):,} trades on {T.date.nunique()} dates; NEG-gamma {T.NEG.sum():,} trades on "
                 f"{T[T.NEG].date.nunique()} dates ({100 * T.NEG.mean():.0f}%)")
    for st, msk in (("NEG gamma", T.NEG), ("POS gamma", ~T.NEG)):
        U = T[msk]; top = U.BASE >= U.BASE.quantile(0.9)
        lines.append(f"  {st}: " + " | ".join(f"{a} {U[a].mean():+.2f}% win {100 * (U[a] > 0).mean():.0f}% held "
                                              f"{U[a + '_held'].mean():.1f} top10 {U.loc[top, a].mean():+.1f}" for a in ARMS))
    out = {}
    for a in ("FAST", "TIME10", "SLOW"):
        I, t, na, nb = interaction(T, a)
        h1, h2 = T.date < SPLIT, T.date >= SPLIT
        Ih1 = interaction(T[h1], a)[0]; Ih2 = interaction(T[h2], a)[0]
        yrs = []
        for y, g in T.groupby(T.date.dt.year):
            if g.NEG.sum() >= 5 and (~g.NEG).sum() >= 5:
                yrs.append(interaction(g, a)[0])
        yrs = np.array(yrs)
        tag = "  *PRIMARY*" if (primary and a == "FAST") else ""
        lines.append(f"  I[{a:6s} - BASE | NEG - POS] {I:+.3f}pp  t {t:+.2f}  halves {Ih1:+.3f} / {Ih2:+.3f}  "
                     f"years same sign {(np.sign(yrs) == np.sign(I)).sum()}/{len(yrs)}{tag}")
        out[a] = (I, t, Ih1, Ih2, (np.sign(yrs) == np.sign(I)).sum(), len(yrs))
    # exploratory: VIX top tercile vs bottom two
    T2 = T.dropna(subset=["vt"]).assign(HI=lambda d: d.vt == 3)
    for a in ("FAST", "TIME10", "SLOW"):
        I, t, _, _ = interaction(T2, a, "HI")
        lines.append(f"  [expl] I[{a} - BASE | VIX top tercile - rest] {I:+.3f}pp t {t:+.2f}")
    return out


def main():
    P, brk, prec = build()
    bars = G.daily_bars("SPY"); _, net, _ = G.gex_series("SPY", bars)
    gam = net.to_dict()
    vix = pd.read_parquet(REPO / "data/cache/vix_daily_long.parquet")
    vix["trade_date"] = pd.to_datetime(vix.trade_date); v = vix.set_index("trade_date").vix_close.sort_index()
    pct = v.rolling(252, min_periods=150).rank(pct=True)
    vterc = pd.cut(pct, [0, 1 / 3, 2 / 3, 1.0001], labels=[1, 2, 3]).astype(float).to_dict()
    lines = ["# Exit speed by SPY gamma state at entry (pre-registration in the docstring)"]
    Tp = trades(prec, P, gam, vterc)
    r = report(Tp, "PRIMARY pool: precision-tier house breakouts", lines, True)
    Tg = trades(brk, P, gam, vterc)
    report(Tg, "second pool: generic house breakouts (ADR >= 3)", lines, False)
    I, t, h1, h2, ys, ny = r["FAST"]
    ok = t >= 3 and np.sign(h1) == np.sign(h2) == np.sign(I) and ys > ny / 2
    lines.append(f"\nBAR (PRIMARY I[FAST] precision): {'PASS' if ok else 'NOT MET'}")
    Tp.to_parquet(REPO / "data/studies/logs/exit_speed_precision.parquet", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

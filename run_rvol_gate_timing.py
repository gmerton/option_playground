#!/usr/bin/env python3
"""
Does the RVOL >= 1.1 gate make the precision tier enter LATER and more extended -- and does that cost money?
(pre-registered 2026-09-24, before the first run; Gabe after TWLO: "a typical trader would say 9/22 is too late...
a couple of days earlier is the natural buy location. But let's see what the math says.")

WHAT IS ALREADY ANSWERED: gate ablation 2026-09-24 -- the breakouts the RVOL gate rejects are about as good as the tier
(T - M = +0.14pp, t 0.21), so the gate is not a proven selection lever. NEW AXIS: TIMING. When the gate rejects a
breakout and the name qualifies a few sessions later, the tier buys higher. Nobody has priced that delay.

THE TRAP (why this is a policy test, not an early-vs-late comparison): comparing a rejected early cross with the
qualifying cross that FOLLOWED it conditions on the future -- the follow-up exists only because the stock kept rising,
so the early entry wins by construction (CLAUDE.md: outcome conditioning; never evaluate an alternative on a sample
selected by the original threshold). So compare two complete POLICIES on every rejected cross:
  A (today's rules)  buy only tier signals WITH RVOL >= 1.1.
  B (no RVOL gate)   buy the tier signal even when RVOL < 1.1.
  EPISODE = each B-only entry (a tier signal except RVOL < 1.1), name-level, one position per name at a time.
  In the episode, A buys the first RVOL-qualifying tier signal on that name within W sessions (else A stays flat);
  B holds its early trade, and ALSO takes that A signal if its early trade has already exited by then.
  Tier signals not preceded by a B-only cross are identical under both policies and cancel.

DESIGN
  signals    precision tier as in run_precision_gate_ablation (base scan + 9 gates), liquid panel 2019-10 ->.
  process    house: close entry +10 bps, stop = min(signal-day low, 2% below close) judged on the close, exit first close
             under the 20 EMA, <= 60 sessions, -10 bps. Returns in % of price (equal notional per trade) and R.
  PRIMARY    per-episode (B - A) in % of price, W = 10 sessions, t clustered by episode date; bar t >= 3, both halves
             (2023-01) same sign. Positive = dropping the gate pays.
  SECONDARY  W = 5 / 20; the same in R (sum of R); share of episodes where A follows at all; entry extension
             (ADR above the 21 EMA) of A's follow-on entry vs B's early entry; per-year.
  DESCRIPTIVE (biased, labelled): early-vs-late paired return on the episodes where A did follow -- shown only to
             quantify the conditioning bias, never as the answer.
  caveat     survivor panel.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_rvol_gate_timing.py   (log -> data/studies/logs/rvol_gate_timing.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/rvol_gate_timing.log"
START, SPLIT, HOLD, SL = "2019-10-01", pd.Timestamp("2023-01-01"), 60, 0.001


def tstat_by(x: pd.Series, g: pd.Series) -> float:
    m = x.groupby(g).mean()
    return float(m.mean() / m.std(ddof=1) * sqrt(len(m))) if len(m) > 2 else np.nan


def main() -> None:
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    piv = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    sd = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    e20 = C.ewm(span=20, adjust=False).mean(); e21 = C.ewm(span=21, adjust=False).mean()
    ext = (C - e21) / (adr / 100 * C)
    tier_x = (elig & (adr >= 4) & (adr <= 7) & (C >= piv) & (C.shift(1) < piv) & (pos >= 0.5) & (sd >= 5) & (sd <= 40)
              & (gap < 0.05) & (chg < 0.08) & (off52 > -15)).fillna(False)          # every tier gate except RVOL
    A_sig = tier_x & (rvol >= 1.1)
    B_only = tier_x & (rvol < 1.1)

    Cv, Lv, E, X = C.values, L.values, e20.values, ext.values
    idx = C.index; i0 = idx.get_indexer([pd.Timestamp(START)], method="bfill")[0]

    def trade(i, j):
        c = Cv[i, j]
        if not np.isfinite(c):
            return None
        entry, stop = c * (1 + SL), min(Lv[i, j], c * 0.98)
        k = i
        for k in range(i + 1, min(i + HOLD, len(Cv) - 1) + 1):
            if np.isfinite(Cv[k, j]) and (Cv[k, j] < stop or Cv[k, j] < E[k, j]):
                break
        if k == i:
            return None
        out = Cv[k, j] * (1 - SL)
        return dict(pct=100 * (out / entry - 1), R=(out - entry) / (entry - stop), exit=k, ext=X[i, j])

    Aa, Bb = A_sig.values, B_only.values
    res = {}
    for W in (5, 10, 20):
        rows = []
        for j in range(Cv.shape[1]):
            busy_until = -1
            bi = np.where(Bb[:, j])[0]
            for i in bi[bi >= i0]:
                if i <= busy_until:
                    continue
                tb = trade(i, j)
                if tb is None:
                    continue
                later = np.where(Aa[i + 1:i + 1 + W, j])[0]
                a_i = i + 1 + later[0] if len(later) else None
                ta = trade(a_i, j) if a_i is not None else None
                A_pct = ta["pct"] if ta else 0.0
                A_R = ta["R"] if ta else 0.0
                B_pct, B_R = tb["pct"], tb["R"]
                if ta and a_i > tb["exit"]:              # B is flat again by then: B takes the A signal too
                    B_pct += ta["pct"]; B_R += ta["R"]
                rows.append(dict(date=idx[i], sym=C.columns[j], follows=ta is not None, B_pct=B_pct, A_pct=A_pct,
                                 B_R=B_R, A_R=A_R, early_pct=tb["pct"], late_pct=ta["pct"] if ta else np.nan,
                                 early_ext=tb["ext"], late_ext=ta["ext"] if ta else np.nan,
                                 lag=(a_i - i) if a_i is not None else np.nan))
                busy_until = max(tb["exit"], a_i or 0, (ta or {}).get("exit", 0))
        res[W] = pd.DataFrame(rows)

    out = []
    pr = out.append
    pr("# RVOL gate timing: policy B (no RVOL gate) vs policy A (today's rules), per B-only episode\n")
    for W in (10, 5, 20):
        T = res[W]; d = T.B_pct - T.A_pct; dR = T.B_R - T.A_R
        t = tstat_by(d, T.date)
        h1 = d[T.date < SPLIT]; h2 = d[T.date >= SPLIT]
        tag = "PRIMARY" if W == 10 else "secondary"
        pr(f"## {tag}: W = {W} sessions | episodes {len(T):,} ({T.sym.nunique()} names), A follows in {100 * T.follows.mean():.0f}%")
        pr(f"  B - A per episode: {d.mean():+.3f}% of price (median {d.median():+.2f}), t {t:+.2f} | halves "
           f"{h1.mean():+.3f} (t {tstat_by(h1, T.date[T.date < SPLIT]):+.2f}) / {h2.mean():+.3f} "
           f"(t {tstat_by(h2, T.date[T.date >= SPLIT]):+.2f}) | in R {dR.mean():+.3f} (t {tstat_by(dR, T.date):+.2f})")
        pr(f"  policy means: B {T.B_pct.mean():+.3f}%  A {T.A_pct.mean():+.3f}%")
        if W == 10:
            ok = abs(t) >= 3 and np.sign(h1.mean()) == np.sign(h2.mean())
            pr(f"  bar |t| >= 3, halves same sign: {'PASS -> ' + ('drop the gate' if d.mean() > 0 else 'keep the gate') if ok else 'FAIL'}")
            yr = d.groupby(T.date.dt.year).mean()
            pr("  per year: " + "  ".join(f"{y} {v:+.2f}" for y, v in yr.items()))
            F = T[T.follows]
            nf = T[~T.follows]
            pr(f"\n  split (descriptive): A follows n {len(F):,}: B {F.B_pct.mean():+.2f}% vs A {F.A_pct.mean():+.2f}% | "
               f"A never follows n {len(nf):,}: B's early trade {nf.B_pct.mean():+.2f}% (A flat)")
            pr(f"  entry extension (ADR above 21 EMA) where A follows: early {F.early_ext.median():.2f} -> late "
               f"{F.late_ext.median():.2f} (median), lag {F.lag.median():.0f} sessions")
            pr(f"  ⚠ BIASED early-vs-late on the follow set only (conditioned on the later breakout): early "
               f"{F.early_pct.mean():+.2f}% vs late {F.late_pct.mean():+.2f}% -- NOT the answer, shown to size the bias")
        pr("")
    print("\n".join(out))
    res[10].to_csv(REPO / "data/studies/rvol_gate_timing_2026-09-24.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

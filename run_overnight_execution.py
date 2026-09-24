#!/usr/bin/env python3
"""
Overnight-aware EXECUTION on the precision-tier breakout book (pre-registered 2026-09-24, before the first run; Gabe:
"is there anything to be gained by combining [overnight persistence] with our existing strategies?"). Parent result:
overnight_persistence_2026-09-24.md (top decile of trailing-252 mean overnight return earns +1.18%/month overnight
gross, t 9.0, and gives back -0.76% intraday). NEW AXIS: no extra trades -- only move a fill by half a session.

DESIGN
  trades    precision-tier house breakouts (run_precision_tier_control.build), house process: buy the signal close,
            stop = signal-day low judged on the close, exit on the first close under the 20 EMA, <= 60 sessions.
  signal    the name's trailing-252 mean overnight return, ranked into deciles across eligible names ON THE DAY of the
            fill decision (no look-ahead).
  EXIT arm  when the exit fires on day k, sell at the NEXT OPEN (k+1) instead of the close k.
  ENTRY arm buy at the NEXT OPEN (i+1) instead of the signal close i (exit unchanged).
  measure   paired per trade, in % of the entry price: (alt fill - base fill) / entry; same slippage both ways.
  PRIMARY   EXIT arm on trades whose name is in the TOP overnight decile at the exit date: mean paired gain, t clustered
            by exit date; bar t >= 3, both halves (2023-01) > 0. Prior: small positive.
  SECONDARY the EXIT and ENTRY shifts by overnight decile (1..10) -- the effect should be monotone in the decile if
            it is the overnight premium and not a generic close-vs-open effect; ENTRY arm on the BOTTOM decile.
  caveat    yfinance opens differ from the first 1-min bar by > 0.5% on ~19% of sampled name-days (parent study).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_overnight_execution.py   (log -> data/studies/logs/overnight_execution.log)
"""
from __future__ import annotations

import contextlib
import io
import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/overnight_execution.log"
SPLIT = pd.Timestamp("2023-01-01")


def tby(x: pd.Series, g: pd.Series) -> float:
    m = pd.Series(x.values, index=g.values).dropna().groupby(level=0).mean()
    return float(m.mean() / m.std(ddof=1) * sqrt(len(m))) if len(m) > 2 else np.nan


def main() -> None:
    from run_precision_tier_control import build
    with contextlib.redirect_stdout(io.StringIO()):
        P, brk, prec = build()
    O, C, L, E20 = P.open.values, P.close.values, P.low.values, P.ema20.values
    idx = P.close.index
    on = P.open / P.close.shift(1) - 1
    sig = on.rolling(252, min_periods=200).mean().where(P.elig.fillna(False))
    dec = sig.rank(axis=1, pct=True).mul(10).apply(np.ceil).clip(1, 10).values   # 1..10 across eligible names
    m = prec[prec.index >= "2019-10-01"]
    off = len(prec) - len(m)
    rows = []
    for i, j in zip(*np.where(m.values)):
        i += off
        if i + 2 >= len(idx):
            continue
        entry, stop = C[i, j], min(L[i, j], C[i, j] * 0.98)
        k = None
        for q in range(i + 1, min(i + 60, len(idx) - 2) + 1):
            if np.isfinite(C[q, j]) and (C[q, j] < stop or C[q, j] < E20[q, j]):
                k = q; break
        if k is None or not np.isfinite(O[k + 1, j]) or not np.isfinite(O[i + 1, j]):
            continue
        rows.append(dict(date=idx[i], exit_date=idx[k], sym=P.close.columns[j],
                         dec_entry=dec[i, j], dec_exit=dec[k, j],
                         base=100 * (C[k, j] / entry - 1),
                         exit_gain=100 * (O[k + 1, j] - C[k, j]) / entry,          # sell next open vs close k
                         entry_gain=100 * (C[i, j] - O[i + 1, j]) / entry))        # buy next open vs close i
    T = pd.DataFrame(rows).dropna(subset=["dec_exit", "dec_entry"])
    out = ["# Overnight-aware execution on the precision-tier book (pre-registration in the docstring)\n",
           f"{len(T):,} trades {T.date.min().date()} -> {T.date.max().date()}; house base {T.base.mean():+.2f}%/trade\n"]
    top = T[T.dec_exit == 10]
    x = top.exit_gain; tt = tby(x, top.exit_date)
    h1, h2 = x[top.exit_date < SPLIT].mean(), x[top.exit_date >= SPLIT].mean()
    out.append(f"## PRIMARY: EXIT at the next open, top-decile names at exit: n {len(top)}, gain {x.mean():+.3f}% of entry "
               f"(median {x.median():+.3f}), t {tt:+.2f}, halves {h1:+.3f} / {h2:+.3f} -> "
               f"{'PASS' if tt >= 3 and h1 > 0 and h2 > 0 else 'FAIL'}")
    out.append(f"   whole book if applied only to top-decile exits: {top.exit_gain.sum() / len(T):+.3f}%/trade")
    out.append("\n## by overnight decile (1 = lowest trailing overnight return, 10 = highest)")
    out.append(f"{'dec':>4s} {'n exit':>7s} {'EXIT gain':>10s} {'t':>6s} | {'n entry':>7s} {'ENTRY gain':>10s} {'t':>6s}")
    for d in range(1, 11):
        a = T[T.dec_exit == d]; b = T[T.dec_entry == d]
        out.append(f"{d:>4d} {len(a):>7,} {a.exit_gain.mean():>+10.3f} {tby(a.exit_gain, a.exit_date):>6.2f} | "
                   f"{len(b):>7,} {b.entry_gain.mean():>+10.3f} {tby(b.entry_gain, b.date):>6.2f}")
    out.append(f"\nall trades: EXIT at next open {T.exit_gain.mean():+.3f} (t {tby(T.exit_gain, T.exit_date):+.2f}); "
               f"ENTRY at next open {T.entry_gain.mean():+.3f} (t {tby(T.entry_gain, T.date):+.2f})")
    bot = T[T.dec_entry == 1]
    out.append(f"ENTRY at next open, bottom-decile names: n {len(bot)}, {bot.entry_gain.mean():+.3f} (t {tby(bot.entry_gain, bot.date):+.2f})")
    corr = np.corrcoef(T.dec_exit, T.exit_gain)[0, 1]
    out.append(f"monotonicity: corr(decile at exit, exit gain) {corr:+.3f}")
    T.to_csv(REPO / "data/studies/overnight_execution_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

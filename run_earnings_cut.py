#!/usr/bin/env python3
"""
CUT SIZE BEFORE EARNINGS on an open breakout (Oliver Kell principle 9, "don't gamble on earnings") -- pre-registered
2026-09-27, before the run; Gabe: "go ahead and run those tests". Spec = the TEST_INDEX section 10 row, with one
declared change: the pools are the 2019-10 -> 2026-09 precision / generic house breakouts that every other exit test
uses (run_precision_tier_control.build()), because 2010-19 has only ~390 precision trades on liquid_panel_2009.

CLAIM. Kell: cut a winning position into the print (MDB 15% -> 9%), hold only with a cushion, or wait and buy after.
WHY NEW. Every earnings row in the ledger is options or new entries; none holds vs cuts an OPEN stock position.

TRADES   house rule: close entry (+slip), stop = breakout-day low judged on the close, exit on a close below the stop
         or the 20 EMA, 60-session cap.
PRINT    data/cache/earnings_yf.parquet. Pre-print close = the close of the report day for AMC, the close of the day
         before for BMO (unknown timing -> the day before). COHORT = trades still open at a pre-print close that is
         after their entry day (first print only).
ARMS     HOLD (the house rule through the print) · CUT40 (sell 40% at the pre-print close, rest follows the house rule)
         · EXIT (flat at the pre-print close). Returns in % of entry, net of slippage on every sale.
CONTROL  the known trim cost (trims -0.25..-0.33R) would otherwise masquerade as an earnings effect. For each print
         event date D: open house trades on D with NO print within +/-10 sessions of D, matched on days-in-trade bucket
         (1-5, 6-15, 16+) and open-gain bucket (< 0, 0-1 ADR, >= 1 ADR); apply the same cut at D's close.
PRIMARY  precision pool, diff-in-diff for CUT40: (CUT40 - HOLD | print) - mean(CUT40 - HOLD | matched no-print on D),
         % per trade, t on event-date cluster means. BAR: |t| >= 3 (Sidak k = 6: 3 arms x 2 pools), both halves
         (split 2023-01) the same sign, per year shown. Positive = cutting before earnings helps.
SECONDARY EXIT diff-in-diff; the cushion split (open gain >= 1 ADR vs < 1 ADR); the generic pool. Also raw CUT40 - HOLD,
         and the variance / p5 / top-decile share of HOLD vs CUT40 on print trades: a variance-only difference is
         declared a RISK lever, not a return lever.
PRIOR    leans HOLD (the earnings-announcement premium is positive on average).
Local.

Run: PYTHONPATH=src:. .venv/bin/python3 run_earnings_cut.py   (log -> data/studies/logs/earnings_cut.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/earnings_cut.log"
SLIP, SPLIT = pt.SLIP, "2023-01-01"


def bucket_days(n):
    return 0 if n <= 5 else (1 if n <= 15 else 2)


def bucket_gain(g_adr):
    return 0 if g_adr < 0 else (1 if g_adr < 1 else 2)


def paths(mask, P):
    """House trades: list of (i, j, entry, exit_k)."""
    C, L, E20 = P.close.values, P.low.values, P.ema20.values
    m = mask[mask.index >= "2019-10-01"]; off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    T = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP); stop = L[i, j]
        if not (np.isfinite(entry) and np.isfinite(stop)) or entry <= stop or i + 1 >= len(C):
            continue
        end = min(i + 60, len(C) - 1); k = i
        for k in range(i + 1, end + 1):
            c = C[k, j]
            if not np.isfinite(c):
                continue
            if c < stop or (np.isfinite(E20[k, j]) and c < E20[k, j]):
                break
        T.append((i, j, entry, k))
    return T


def arms(C, entry, j, d, k):
    hold = 100 * (C[k, j] * (1 - SLIP) / entry - 1)
    cut_px = C[d, j] * (1 - SLIP)
    exit_ = 100 * (cut_px / entry - 1)
    cut40 = 0.4 * exit_ + 0.6 * hold
    return hold, cut40, exit_


def run_pool(label, mask, P, pre_idx, out, primary):
    C, ADR = P.close.values, P.adr.values
    cols = P.close.columns
    T = paths(mask, P)
    # index trades open on each day for the control
    open_on = {}
    for (i, j, entry, k) in T:
        for d in range(i + 1, k):
            open_on.setdefault(d, []).append((i, j, entry, k))
    ev = []
    for (i, j, entry, k) in T:
        ds = [d for d in pre_idx.get(cols[j], []) if i < d < k]
        if not ds:
            continue
        d = ds[0]
        hold, cut40, exit_ = arms(C, entry, j, d, k)
        g = (C[d, j] / entry - 1) * 100 / ADR[i, j] if np.isfinite(ADR[i, j]) and ADR[i, j] > 0 else 0.0
        bd, bg = bucket_days(d - i), bucket_gain(g)
        ctrl = []
        for (i2, j2, e2, k2) in open_on.get(d, []):
            if j2 == j:
                continue
            near = [x for x in pre_idx.get(cols[j2], []) if abs(x - d) <= 10]
            if near:
                continue
            g2 = (C[d, j2] / e2 - 1) * 100 / ADR[i2, j2] if np.isfinite(ADR[i2, j2]) and ADR[i2, j2] > 0 else 0.0
            if bucket_days(d - i2) != bd or bucket_gain(g2) != bg:
                continue
            h2, c2, x2 = arms(C, e2, j2, d, k2)
            ctrl.append((c2 - h2, x2 - h2))
        if not ctrl:
            continue
        ctrl = np.array(ctrl)
        ev.append(dict(date=P.close.index[d], sym=cols[j], hold=hold, cut40=cut40, exit=exit_, cushion=bg == 2,
                       raw_cut=cut40 - hold, raw_exit=exit_ - hold, ctrl_cut=ctrl[:, 0].mean(), ctrl_exit=ctrl[:, 1].mean(),
                       n_ctrl=len(ctrl)))
    E = pd.DataFrame(ev)
    E["did_cut"] = E.raw_cut - E.ctrl_cut; E["did_exit"] = E.raw_exit - E.ctrl_exit
    out.append(f"\n## {label}: {len(T):,} house trades; {len(E):,} open through a print with matched controls "
               f"(median {E.n_ctrl.median():.0f} controls each); cushion >= 1 ADR: {100 * E.cushion.mean():.0f}%")

    def st(x, d):
        g = x.groupby(d).mean(); return g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g))
    h = E.date < SPLIT
    res = {}
    for arm in ("cut", "exit"):
        m, t = st(E[f"did_{arm}"], E.date)
        yr = E.groupby(E.date.dt.year)[f"did_{arm}"].mean()
        tag = "  *PRIMARY*" if (primary and arm == "cut") else ""
        out.append(f"  DiD {arm.upper():4s}: {m:+.3f}pp  t {t:+.2f}  halves {E[h][f'did_{arm}'].mean():+.3f} / "
                   f"{E[~h][f'did_{arm}'].mean():+.3f} | raw {E[f'raw_{arm}'].mean():+.3f}pp, control {E[f'ctrl_{arm}'].mean():+.3f}pp"
                   f" | per year " + " ".join(f"{y}:{v:+.2f}" for y, v in yr.items()) + tag)
        for cu, lab in ((True, "cushion >= 1 ADR"), (False, "cushion < 1 ADR")):
            s = E[E.cushion == cu]
            if len(s) > 10:
                m2, t2 = st(s[f"did_{arm}"], s.date)
                out.append(f"      {lab:17s} n {len(s):4d}  {m2:+.3f}pp t {t2:+.2f}")
        res[arm] = (m, t, E[h][f"did_{arm}"].mean(), E[~h][f"did_{arm}"].mean())
    for a in ("hold", "cut40", "exit"):
        x = E[a]
        out.append(f"  {a:5s} on print trades: mean {x.mean():+.2f}%  sd {x.std():.1f}  p5 {x.quantile(.05):+.1f}%  "
                   f"top-decile mean {x[x >= x.quantile(.9)].mean():+.1f}%")
    E.to_csv(REPO / f"data/studies/logs/earnings_cut_{'precision' if primary else 'generic'}.csv", index=False)
    return res


def main():
    P, brk, prec = build()
    er = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet")[["ticker", "session", "timing"]]
    er["session"] = pd.to_datetime(er.session)
    idx = P.close.index
    pre_idx = {}
    for r in er[er.ticker.isin(P.close.columns) & (er.session >= "2019-09-01")].itertuples():
        k = idx.searchsorted(r.session)
        if k >= len(idx):
            continue
        day_is_session = idx[k] == r.session
        if str(r.timing).upper() == "AMC" and day_is_session:
            d = k
        else:
            d = k - 1
        if d >= 0:
            pre_idx.setdefault(r.ticker, []).append(d)
    for t in pre_idx:
        pre_idx[t] = sorted(set(pre_idx[t]))
    out = ["# Cut size before earnings on an open breakout (pre-registration in the docstring)"]
    r = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, pre_idx, out, True)
    run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, pre_idx, out, False)
    m, t, h1, h2 = r["cut"]
    ok = abs(t) >= 3 and np.sign(h1) == np.sign(h2) == np.sign(m)
    out.append(f"\nBAR (PRIMARY CUT40 DiD, precision): {'PASS (' + ('cut helps' if m > 0 else 'HOLD better') + ')' if ok else 'NOT MET'}")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

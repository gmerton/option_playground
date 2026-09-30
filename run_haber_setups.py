#!/usr/bin/env python3
"""Haber LAUNCHPAD and FIRST 50-DAY PULLBACK (2026-09-29).
PRE-REGISTERED: data/studies/haber_launchpad_pullback_2026-09-29.md (committed ec69b3b before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_haber_setups.py   (harness verbose -> data/studies/logs/haber_setups.log;
       summary -> data/studies/haber_launchpad_pullback_2026-09-29.log)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

SINCE, UNTIL, SPLIT, BAR, REFIRE = "2010-01-01", "2026-06-30", "2018-01-01", 3.2, 20
LOG = pt.REPO / "data/studies/logs/haber_setups.log"
SUMMARY = pt.REPO / "data/studies/haber_launchpad_pullback_2026-09-29.log"


def refire_filter(mask: np.ndarray, gap: int = REFIRE) -> np.ndarray:
    out = np.zeros_like(mask)
    for j in range(mask.shape[1]):
        last = -10 ** 9
        for i in np.flatnonzero(mask[:, j]):
            if i - last >= gap:
                out[i, j] = True; last = i
    return out


def launchpad(P):
    C, H = P.close, P.high
    mas = [C.rolling(10).mean(), C.rolling(21).mean(), C.ewm(span=23, adjust=False).mean(), C.rolling(50).mean(),
           C.ewm(span=65, adjust=False).mean()]
    mx = np.fmax.reduce([m.values for m in mas]); mn = np.fmin.reduce([m.values for m in mas])
    spread = pd.DataFrame((mx - mn) / C.values, index=C.index, columns=C.columns)
    q10 = spread.rolling(252, min_periods=200).quantile(0.10)
    tight = (spread <= q10).shift(1).rolling(10, min_periods=1).max().fillna(0).astype(bool)
    above = C.values > mx
    prev_above = np.vstack([np.zeros((1, C.shape[1]), bool), above[:-1]])
    rising = np.logical_and.reduce([(m > m.shift(5)).values for m in mas])
    cand = above & ~prev_above & rising & tight.values & P.elig.fillna(False).values
    idx = C.index
    cand[(idx < SINCE) | (idx > UNTIL)] = False
    Hv, Cv = H.values, C.values
    ok = np.zeros_like(cand)
    for i, j in zip(*np.where(cand)):
        if i < 130:
            continue
        w1 = Hv[i - 120:i - 10, j]
        if not np.isfinite(w1).any():
            continue
        i1 = i - 120 + int(np.nanargmax(w1)); h1 = Hv[i1, j]
        if i1 + 10 > i - 3:
            continue
        w2 = Hv[i1 + 10:i - 2, j]
        if not np.isfinite(w2).any():
            continue
        i2 = i1 + 10 + int(np.nanargmax(w2)); h2 = Hv[i2, j]
        if not h2 < h1:
            continue
        line = h1 + (h2 - h1) / (i2 - i1) * (i - i1)
        ok[i, j] = Cv[i, j] > line
    ok = refire_filter(ok)
    stop = pd.DataFrame(np.minimum(mn, Cv * 0.98), index=idx, columns=C.columns)
    return pd.DataFrame(ok, index=idx, columns=C.columns), stop


def pullback(P):
    C, H = P.close, P.high
    idx = C.index
    s50 = C.rolling(50).mean()
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    newhigh = (C > hi252)
    recent = newhigh.shift(1).rolling(126, min_periods=100).max()
    r126 = C / C.shift(126) - 1
    rs = r126.where(P.elig).rank(axis=1, pct=True)
    brk = (newhigh & (recent == 0) & (s50 > s50.shift(10)) & (rs >= 0.7) & P.elig).fillna(False).values
    brk[(idx < SINCE) | (idx > UNTIL)] = False
    Cv, S = C.values, s50.values
    sig = np.zeros_like(brk); bsig = np.zeros_like(brk)
    for b, j in zip(*np.where(brk)):
        for k in range(b + 3, min(b + 61, len(idx))):
            if np.isfinite(S[k, j]) and 0.98 * S[k, j] <= Cv[k, j] <= 1.01 * S[k, j]:
                sig[k, j] = True; bsig[b, j] = True
                break
    stop_pb = pd.DataFrame(S * 0.975, index=idx, columns=C.columns)
    stop_bo = pd.DataFrame(np.minimum(P.low.values, Cv * 0.98), index=idx, columns=C.columns)
    return (pd.DataFrame(sig, index=idx, columns=C.columns), stop_pb,
            pd.DataFrame(bsig, index=idx, columns=C.columns), stop_bo)


def run(label, hit, stop, arm, P, control, ledger):
    fn = lambda _P, h=hit, s=stop: pt.daily_signals(h, stop=s, side="long", since=SINCE)
    tab = pt.run_daily(label + f" [{control}]", fn, hold=60, panel=P, entry_at="close", control=control, split=SPLIT,
                       ledger=ledger, note="pre-registered 2026-09-29 (ec69b3b)")
    a = tab.attrs["arms"][arm]
    return dict(setup=label, control=control, arm=arm, n=int(tab.loc[arm, "n"]), meanR=tab.loc[arm, "meanR"],
                paired_edge=a["pedge"], t=a["edge_t"], h1=a["eh1"], h2=a["eh2"], p_search=tab.attrs.get("p_search"))


def main():
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    lp, lp_stop = launchpad(P)
    pb, pb_stop, bo, bo_stop = pullback(P)
    print(f"signals: launchpad {int(lp.values.sum()):,} | first 50d pullbacks {int(pb.values.sum()):,} "
          f"(from {int(bo.values.sum()):,} stage-2 breaks that got one)", flush=True)
    rows = []
    for ctrl in ("xname", "post"):
        rows.append(run("HABER launchpad", lp, lp_stop, "ema20", P, ctrl, ledger=(ctrl == "xname")))
        rows.append(run("HABER first 50d pullback", pb, pb_stop, "stop_hold", P, ctrl, ledger=(ctrl == "xname")))
    rows.append(run("HABER stage-2 breakout entry (same names)", bo, bo_stop, "stop_hold", P, "xname", ledger=False))
    return pd.DataFrame(rows), int(lp.values.sum()), int(pb.values.sum())


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        R, nlp, npb = main()
    finally:
        sys.stdout.close(); sys.stdout = real
    lines = [f"# Haber setups (pre-registration in the md). launchpad signals {nlp:,}; first-50d-pullback signals {npb:,}",
             R.round(3).to_string(index=False)]
    for s in ("HABER launchpad", "HABER first 50d pullback"):
        r = R[(R.setup == s) & (R.control == "xname")].iloc[0]
        ok = r.paired_edge > 0 and r.t >= BAR and r.h1 > 0 and r.h2 > 0
        lines.append(f"PASS {s} (vs xname, t >= {BAR}, halves > 0): {'YES' if ok else 'no'}")
    SUMMARY.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

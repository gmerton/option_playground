#!/usr/bin/env python3
"""
Is the breakout's negative R an ENTRY problem or a STOP problem?

The ledger has a consistent, large anomaly: across 40 daily patterns the same-name random-later
control beats the signal in 22, and on every breakout variant the control is POSITIVE (+0.13 to
+0.21R) while the signal is NEGATIVE (-0.21 to -0.33R). Same names, same stop rule, same exit arm --
a ~0.4R swing from entry timing alone. The FTD split (2026-09-20) surfaced the same shape.

Two explanations, and they imply opposite fixes:

  A. ENTRY: the breakout bar is by definition an extended bar (a 20-session high), so you buy the
     worst price of the move. Fix = enter later/lower.
  B. STOP: the breakout bar is a high-range bar, so a stop struck off it sits inside that day's
     noise and gets hit by ordinary wiggle. The raw move is fine; the stop converts it to a loss.
     Fix = the stop, not the entry.

They separate cleanly: measure the SAME entries with NO stop (raw forward return) and with the stop.
If raw returns are similar for signal and control but R diverges, it is the stop (B). If raw returns
diverge too, it is genuinely the entry (A).

This also reconciles the two existing studies: the pullback study found breakout entries BEST on raw
percent (+2.6%/trade), while the ledger has them worst in R. Both can be true -- and B is what that
would mean.

Usage: PYTHONPATH=src .venv/bin/python3 run_entry_vs_stop.py > data/studies/entry_vs_stop_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)
from lib.studies.pattern_test import load_panel

RNG = np.random.default_rng(20260920)
HOLDS = (5, 10, 21)


def main():
    P = load_panel()
    C, H, L, A = P.close, P.high, P.low, P.adr
    brk = (C > H.shift(1).rolling(20).max()) & (A >= 3) & P.elig
    cv, hv, lv, av = C.values, H.values, L.values, A.values
    n, m = cv.shape
    sig = np.argwhere(brk.values)
    print(f"panel {n} sessions x {m} names | house breakouts {len(sig):,}")

    # control: a random LATER session in the same name (mirrors the harness's `post`)
    ctl = []
    for i, j in sig:
        if i + 1 < n - max(HOLDS):
            ctl.append((RNG.integers(i + 1, n - max(HOLDS)), j))
    ctl = np.array(ctl)
    print(f"controls drawn: {len(ctl):,}\n")

    def measure(pts, hold, k_stop):
        raw, R, stopped, gap_adr = [], [], 0, []
        for i, j in pts:
            if i + hold >= n: continue
            e = cv[i, j]; a = av[i, j]
            if not np.isfinite(e) or not np.isfinite(a) or a <= 0 or e <= 0: continue
            stop = e * (1 - k_stop * a / 100.0)
            risk = e - stop
            path_l = lv[i + 1:i + 1 + hold, j]
            path_c = cv[i + 1:i + 1 + hold, j]
            if not np.isfinite(path_c).all(): continue
            hit = np.flatnonzero(path_l <= stop)
            exit_px = stop if len(hit) else path_c[-1]
            if len(hit): stopped += 1
            R.append((exit_px - e) / risk)
            raw.append(path_c[-1] / e - 1)          # same entry, NO stop
            # how far above the 20d-prior high the entry sits, in ADR -- the extension measure
            prior = np.nanmax(hv[max(0, i - 20):i, j]) if i > 0 else np.nan
            if np.isfinite(prior) and prior > 0:
                gap_adr.append((e / prior - 1) * 100 / a)
        return (np.array(raw), np.array(R), stopped / max(len(R), 1), np.array(gap_adr))

    for k in (1.0, 2.0):
        print(f"\n{'='*86}\nSTOP = {k:g} ADR below the entry close\n{'='*86}")
        rows = []
        for hold in HOLDS:
            sr, sR, ss, sg = measure(sig, hold, k)
            cr, cR, cs, cg = measure(ctl, hold, k)
            rows.append(dict(hold=f"{hold}d",
                             sig_raw=100 * sr.mean(), ctl_raw=100 * cr.mean(),
                             raw_gap=100 * (sr.mean() - cr.mean()),
                             sig_R=sR.mean(), ctl_R=cR.mean(), R_gap=sR.mean() - cR.mean(),
                             sig_stopped=100 * ss, ctl_stopped=100 * cs,
                             sig_ext_adr=np.nanmean(sg), ctl_ext_adr=np.nanmean(cg)))
        t = pd.DataFrame(rows)
        print(t.round(3).to_string(index=False))
        print("\n  raw_gap > 0 and R_gap < 0  =>  the ENTRY is fine, the STOP is doing the damage (B)")
        print("  raw_gap < 0                =>  genuinely a worse entry price (A)")


if __name__ == "__main__":
    main()

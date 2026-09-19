#!/usr/bin/env python3
"""
What does a same-day exit cost, on our own universe? (Tito's intraday book vs our daily-close book.)

Pool: the Adhikary precision-shaped breakout (run_adhikary_validation.py gates) -- ADR 4-7, within 15% of the
52-week high, 15-day pivot break on RVOL >= 1.1, upper-half close, stacked. Panel liquid_panel_2019 (2019-10 ->
2026-09).

Our book enters at the breakout-day CLOSE, so "exit the same day" is impossible by construction. To price the
comparison we enter at the NEXT OPEN (the proxy for Tito's intraday entry) and vary only the exit:

  scalp_close     exit at that same day's close                      (Tito's sub-day trade)
  scalp_strength  exit at entry + 1 ADR if the day's high reaches it, else that close   (sell intraday strength,
                  optimistic: assumes the touch fills; treat as an upper bound)
  hold_2 / 3 / 5  exit at the close N sessions later
  trail           stop = breakout-day low on a close, else first close below the 20 EMA, cap 60 sessions
  book_close      OUR process for reference: enter at the breakout-day close, same trail

R = return / (entry - stop distance), stop = the breakout day's low, so the denominator is the same risk in
every policy and the numbers are comparable. Costs: 5 bps per side on the underlying.

Usage:
  PYTHONPATH=src .venv/bin/python3 run_exit_timing_study.py > data/studies/exit_timing_study_2026-09-18.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
COST = 0.0005


def main() -> None:
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max()
    rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan)
    gap = O / C.shift(1) - 1
    chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr)
    off52 = (C / hi52 - 1) * 100

    gate = (adr >= 3) & (range52 >= 17) & elig
    brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
    precision = brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days >= 5) & (stack_days <= 40)

    idx, cols = C.index, C.columns
    Cv, Ov, Hv, Lv, E20v, ADRv = C.values, O.values, H.values, L.values, e20.values, adr.values
    rows = []
    for name, mask in (("all breakouts", brk), ("precision tier", precision)):
        mm = mask.fillna(False).astype(bool)
        mm = mm[mm.index >= "2019-10-01"]
        ii, jj = np.where(mm.values)
        ii = ii + (len(C) - len(mm))
        for i, j in zip(ii, jj):
            if i + 6 >= len(Cv):
                continue
            stop = Lv[i, j]
            entry = Ov[i + 1, j]                     # next open = the intraday-entry proxy
            if not np.isfinite(entry) or not np.isfinite(stop) or entry <= stop:
                continue
            risk = entry - stop
            a = ADRv[i, j] / 100 * entry
            rec = dict(pool=name, year=idx[i].year, date=idx[i], entry=entry, risk=risk)

            def net(exit_px):
                return (exit_px * (1 - COST) - entry * (1 + COST))

            rec["scalp_close"] = net(Cv[i + 1, j]) / risk
            tgt = entry + a
            rec["scalp_strength"] = net(tgt if Hv[i + 1, j] >= tgt else Cv[i + 1, j]) / risk
            for n in (2, 3, 5):
                rec[f"hold_{n}"] = net(Cv[i + n, j]) / risk
            # trail from the next open, stop = breakout-day low on a close
            r = np.nan
            for k in range(i + 1, min(i + 61, len(Cv))):
                c = Cv[k, j]
                if not np.isfinite(c):
                    continue
                if c < stop or c < E20v[k, j]:
                    r = net(c) / risk
                    rec["trail_days"] = k - i
                    break
            if not np.isfinite(r):
                k = min(i + 60, len(Cv) - 1)
                r = net(Cv[k, j]) / risk
                rec["trail_days"] = k - i
            rec["trail"] = r
            # our actual book: enter at the breakout close instead
            e2 = Cv[i, j]
            if np.isfinite(e2) and e2 > stop:
                r2 = np.nan
                for k in range(i + 1, min(i + 61, len(Cv))):
                    c = Cv[k, j]
                    if not np.isfinite(c):
                        continue
                    if c < stop or c < E20v[k, j]:
                        r2 = (c * (1 - COST) - e2 * (1 + COST)) / (e2 - stop)
                        break
                if not np.isfinite(r2):
                    k = min(i + 60, len(Cv) - 1)
                    r2 = (Cv[k, j] * (1 - COST) - e2 * (1 + COST)) / (e2 - stop)
                rec["book_close"] = r2
            rows.append(rec)
    T = pd.DataFrame(rows)
    T.to_parquet("data/cache/exit_timing_trades.parquet", index=False)

    POL = ["scalp_close", "scalp_strength", "hold_2", "hold_3", "hold_5", "trail", "book_close"]
    for pool, x in T.groupby("pool"):
        print(f"\n=== {pool.upper()} (n={len(x):,}, {x.date.min().date()} -> {x.date.max().date()}) — R per trade ===")
        out = {}
        for c in POL:
            s = x[c].dropna()
            d = s.groupby(x.loc[s.index, "date"]).mean()          # cluster by entry date
            out[c] = dict(n=len(s), meanR=s.mean(), medR=s.median(), win=100 * (s > 0).mean(),
                          t=d.mean() / d.std() * np.sqrt(len(d)), p90=s.quantile(0.9), p10=s.quantile(0.1))
        print(pd.DataFrame(out).T.round(2).to_string())
        print("  mean R by year:")
        print("   " + x.groupby("year")[POL].mean().round(2).to_string().replace("\n", "\n   "))
        print(f"  median trail hold: {x.trail_days.median():.0f} sessions; "
              f"share where scalp_close beat trail: {100 * (x.scalp_close > x.trail).mean():.0f}%")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
WEAK-MARKET GAP-UP FADE x BREADTH (pre-registered 2026-09-26, before the run; SMB Capital SE1r3UlzWss "A profitable
trade setup for a very weak market", queued in TEST_INDEX section 10 the same day; Gabe: "sure").

CLAIM. In a weak tape (breadth -- % of stocks above their 20/50/200-day SMAs -- falling), a stock that gaps up >= 5%
on a catalyst while in its own down-cycle (below a declining 10-day MA) fails intraday: short the 1-min opening-range
low, stop at the high of day, cover within ~60 minutes or into the prior day's high. "This is something that has
worked for a long period of time" (Bellafiore) -- one GME trade shown, no data.

WHY NEW. The ledger's shorts are multi-week drift (short-universe 0/10: weak names drift UP) or intraday triggers on a
2026 watchlist. Gap fades were tested only on index ETFs (Carter) or unconditionally (SPY gap study, left side).
A single-name news-gap fade conditioned on breadth has never been run. Horizon here is ONE session, so the "weak
names drift up" result does not rule it out.

DAILY PROXY (the ORB trigger and 60-minute exit need minute bars we don't have for 2010-26; the proxy is open -> close)
  panel    liquid_panel_2009 (yfinance-adjusted OHLCV), eligible = ADDV >= $50M and price >= $5 on the PRIOR day,
           2010-01 -> 2026-09. ⚠ Survivorship: names liquid as of 2026 only; failed names are missing. That biases
           AGAINST shorts, so a positive result is conservative and a null is slightly pessimistic.
  event    gap = open_t / close_{t-1} - 1 >= 5% AND gap >= 1.5 x ADR (20-day, lagged); down-cycle = close_{t-1} <
           SMA50_{t-1} AND SMA50 declining (SMA50_{t-1} < SMA50_{t-6}). (His 10-day MA is noisier; 50 is declared
           PRIMARY, 10 exploratory.) No news archive: the gap stands in for the catalyst.
  trade    short at the open, cover at the close. Net = -(C/O - 1) - 2 x 10 bp (house stock slippage per side);
           one-day borrow ignored.
  control  same-date eligible names with |gap| < 1% (no event): their mean open -> close is subtracted, so the day's
           market move is held fixed. excess_short = -(r_event - r_ctrl) - 20 bp.
  breadth  B_t = % of eligible names with close > SMA50, measured at t-1. FALLING = B_{t-1} - B_{t-21} < 0.
PRIMARY    the FALLING-breadth arm: mean excess_short per event, t on date-cluster means (events on the same day share
           a date), vs zero. Bar: t >= 3, both halves (split 2018-01) positive, positive in a majority of years.
SECONDARY  (declared) FALLING minus RISING arm (Welch t on date means): does the weak tape add anything?
           Also shown: raw net short return (unhedged -- what the trade as taught would earn).
EXPLORATORY (no bar): 10-day-MA down-cycle version; breadth LEVEL < 40%; SPY below its 50-day SMA as the regime;
           gap-size buckets; the fade with NO down-cycle filter (the SPY gap study's unconditional analogue, single names).
Local vs cloud: local (cached panel, minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_gap_fade_breadth.py   (log -> data/studies/logs/gap_fade_breadth.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/gap_fade_breadth.log"
START, SPLIT, SLIP = "2010-01-01", "2018-01-01", 0.0010


def tclu(x: pd.Series, dates: pd.Series) -> tuple[float, float, int]:
    g = x.groupby(dates).mean()
    return float(g.mean()), float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan, len(g)


def welch(a: pd.Series, da: pd.Series, b: pd.Series, db: pd.Series) -> float:
    ga, gb = a.groupby(da).mean(), b.groupby(db).mean()
    return float((ga.mean() - gb.mean()) / np.sqrt(ga.var(ddof=1) / len(ga) + gb.var(ddof=1) / len(gb)))


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)     # drop thin/partial data days
    O, C, ADR = P.open.loc[keep], P.close.loc[keep], P.adr.loc[keep]
    E = P.elig.loc[keep].fillna(False).shift(1).fillna(False).astype(bool)         # eligible on the prior day
    gap = O / C.shift(1) - 1
    oc = C / O - 1
    s50, s10 = C.rolling(50).mean(), C.rolling(10).mean()
    down50 = (C < s50) & (s50 < s50.shift(5))
    down10 = (C < s10) & (s10 < s10.shift(5))
    above = (C > s50).where(E)
    B = 100 * above.sum(axis=1) / E.sum(axis=1)
    Bp = B.shift(1)
    falling = (Bp - B.shift(21)) < 0
    spy = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    spy = spy[spy.ticker == "SPY"].set_index("date").close.sort_index().reindex(C.index)
    spy_weak = (spy < spy.rolling(50).mean()).shift(1)

    big = (gap >= 0.05) & (gap * 100 >= 1.5 * ADR) & E & oc.notna()
    ctrl = E & (gap.abs() < 0.01) & oc.notna()
    r_ctrl = oc.where(ctrl).mean(axis=1)

    ii, jj = np.where(big.values)
    ev = pd.DataFrame(dict(date=C.index[ii], sym=C.columns[jj], gap=gap.values[ii, jj], oc=oc.values[ii, jj],
                           down50=down50.shift(1).values[ii, jj], down10=down10.shift(1).values[ii, jj]))
    ev = ev[ev.date >= START].copy()
    ev["ctrl"] = r_ctrl.reindex(ev.date).values
    ev["falling"] = falling.reindex(ev.date).values.astype(bool)
    ev["B"] = Bp.reindex(ev.date).values
    ev["spy_weak"] = spy_weak.reindex(ev.date).values.astype(bool)
    ev = ev.dropna(subset=["ctrl", "B"])
    ev["raw"] = 100 * (-ev.oc - 2 * SLIP)
    ev["xs"] = 100 * (-(ev.oc - ev.ctrl) - 2 * SLIP)
    ev["down50"] = ev.down50.astype(bool); ev["down10"] = ev.down10.astype(bool)

    out = []
    def row(name, d, primary=False):
        if len(d) < 10:
            out.append(f"  {name:48s} n {len(d):5d}  (too few)"); return None
        m, t, nd = tclu(d.xs, d.date)
        h1 = d[d.date < SPLIT]; h2 = d[d.date >= SPLIT]
        yrs = d.groupby(d.date.dt.year).xs.mean()
        out.append(f"  {name:48s} n {len(d):5d} dates {nd:4d}  excess {m:+.3f}% t {t:+.2f}  halves "
                   f"{h1.xs.mean():+.3f}/{h2.xs.mean():+.3f}  yrs+ {(yrs > 0).sum()}/{len(yrs)}  raw net {d.raw.mean():+.3f}%"
                   f"  win {100 * (d.xs > 0).mean():.0f}%" + ("  *PRIMARY*" if primary else ""))
        return dict(m=m, t=t, h1=h1.xs.mean(), h2=h2.xs.mean(), yp=(yrs > 0).sum(), ny=len(yrs))

    base = ev[ev.down50]
    out.append(f"# Gap-up fade x breadth -- events: {len(ev):,} big gaps; {len(base):,} in a 50-day down-cycle "
               f"({ev.date.min().date()} -> {ev.date.max().date()}); short open->close, net 20 bp, excess vs same-date "
               f"no-gap names; t on date-cluster means\n")
    out.append("PRIMARY / SECONDARY")
    P1 = row("FALLING breadth, down50 (PRIMARY)", base[base.falling], primary=True)
    row("RISING breadth, down50", base[~base.falling])
    tw = welch(base[base.falling].xs, base[base.falling].date, base[~base.falling].xs, base[~base.falling].date)
    out.append(f"  SECONDARY falling - rising: {base[base.falling].xs.mean() - base[~base.falling].xs.mean():+.3f}pp, "
               f"Welch t on date means {tw:+.2f}")
    out.append("\nEXPLORATORY (no bar)")
    row("down10, falling breadth", ev[ev.down10 & ev.falling])
    row("down50, breadth level < 40%", base[base.B < 40])
    row("down50, SPY < 50-day SMA", base[base.spy_weak])
    row("NO down-cycle filter, falling breadth", ev[ev.falling])
    row("NO down-cycle filter, all", ev)
    for lo, hi in ((0.05, 0.08), (0.08, 0.15), (0.15, 9)):
        row(f"down50 falling, gap {int(lo*100)}-{'+' if hi > 1 else int(hi*100)}%",
            base[base.falling & (base.gap >= lo) & (base.gap < hi)])
    Y = base[base.falling].groupby(base[base.falling].date.dt.year).agg(n=("xs", "size"), excess=("xs", "mean"),
                                                                          raw=("raw", "mean"))
    out.append("\nPRIMARY by year:\n" + Y.round(3).T.to_string())
    ok = P1 is not None and P1["t"] >= 3 and P1["h1"] > 0 and P1["h2"] > 0 and P1["yp"] > P1["ny"] / 2
    out.append(f"\nBAR: {'PASS' if ok else 'NOT MET'} (t >= 3, both halves > 0, majority of years > 0)")
    ev.to_parquet(REPO / "data/studies/logs/gap_fade_breadth_events.parquet", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

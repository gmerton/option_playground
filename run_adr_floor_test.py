#!/usr/bin/env python3
"""
Lowering the ADR floor for longs: are the bands just below the cuts as good as the bands above them?
(pre-registered 2026-09-24, before the first run; Gabe: "lower the ADR threshold we have in place for longing stocks")

WHAT IS ALREADY ANSWERED (not re-tested): dropping the ADR >= 3 gate entirely halves mean R (adhikary validation
2026-09-08); ADR >= 4 is the best universe (HYB-B, t 2.6); a 2019-22 refit moved the precision band UP to 5-7 and
the tier is a regime finding (freeze-forward 2026-09-23). NEW AXIS: the band immediately below each cut, head to head
with the band above it, with ADR-MATCHED controls -- the earlier tests pooled everything below the cut together.

DESIGN
  events     the house breakout exactly as run_precision_tier_control.build() defines it (15d pivot cleared on the
             close, RVOL >= 1.1, close in the upper half, stacked >= 5d, no >= 5% gap / >= 8% day), with the
             ADR gate lowered to 2 so the lower bands exist. Two families:
               SCAN  all house breakouts                               -> question: 2-3 vs 3-4 (the ADR >= 3 gate)
               TIER  + within 15% of the 52wk high + stacked 5-40d     -> question: 3-4 vs 4-7 (the precision floor 4)
  bands      ADR (20d, prior day) 2-3, 3-4, 4-7, 7+ (context only).
  process    the house process: entry at the signal CLOSE, stop = day low FLOORED at 2% below the close (the honest
             variant of 2026-09-19), judged on the close, exit = first close under the 20 EMA, hold <= 60.
  metrics    (1) PRIMARY: 20-session forward return minus the same-date mean of ELIGIBLE NAMES IN THE SAME ADR BAND
                 (ADR-matched selection excess), date-clustered t.
             (2) the house process in % and in R (R cap 20), by band, with by-year and halves.
  bar        a lowered band is worth admitting only if, on the PRIMARY metric, it clears the house bar on its own:
             excess > 0, |t| >= 3 (Sidak over the 2 lowered-band cells = 2.24; 3 governs), both halves (2023-01)
             positive, positive in >= 5 of 7 years -- AND its house-process % return is not below the band above it
             by more than noise (difference t > -2). The band ABOVE is reported under the same bar for comparison;
             if it does not clear either, the floor is not a lever in either direction.
  caveat     survivor panel (flatters absolute levels; compare bands). Judge in %, not R (low-ADR names have tighter
             stops, so R flatters them even with the 2% floor).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_adr_floor_test.py > data/studies/logs/adr_floor_test.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt

START, SPLIT, H = "2019-10-01", "2023-01-01", 20
BANDS = [(2, 3), (3, 4), (4, 7), (7, 99)]
R_CAP = 20.0


def tstat(x: pd.Series) -> float:
    x = x.dropna(); return x.mean() / x.std(ddof=1) * sqrt(len(x)) if len(x) > 2 else np.nan


def build():
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, Hh, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (Hh / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = Hh.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = Hh.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (Hh - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    gate = (adr >= 2) & (range52 >= 17) & elig                                  # lowered from 3
    brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)).fillna(False)
    tier = (brk & (off52 > -15) & (stack_days <= 40)).fillna(False)
    P = pt.DailyPanel(open=O, high=Hh, low=L, close=C, adr=adr, elig=elig, ema20=C.ewm(span=20, adjust=False).mean())
    return P, brk, tier


def house(P, mask: pd.DataFrame) -> pd.DataFrame:
    C, L = P.close.values, P.low.values
    m = mask[mask.index >= START]; off = len(mask) - len(m)
    ii, jj = np.where(m.values); ii = ii + off
    rows = []
    for i, j in zip(ii, jj):
        c = C[i, j]
        stop = min(L[i, j], c * 0.98)
        o = pt._daily_arms(P, j, i, stop, "long", 60, entry_at="close")
        if not o:
            continue
        risk = (c * (1 + pt.SLIP) - stop) / (c * (1 + pt.SLIP))
        r = float(np.clip(o["ema20"], -R_CAP, R_CAP))
        rows.append(dict(i=i, j=j, date=P.close.index[i], R=r, pct=100 * o["ema20"] * risk, adr=P.adr.values[i, j]))
    return pd.DataFrame(rows)


def main() -> None:
    P, brk, tier = build()
    C = P.close
    fr = (C.shift(-H) / C - 1) * 100
    band_of = lambda a: next((f"{lo}-{hi if hi < 99 else '+'}" for lo, hi in BANDS if lo <= a < hi), None)
    # same-date, same-band mean forward return of eligible names (the ADR-matched benchmark)
    A = P.adr.values; E = P.elig.values; F = fr.values
    bench = {}
    for lo, hi in BANDS:
        mk = E & (A >= lo) & (A < hi) & np.isfinite(F)
        s = np.where(mk, F, 0).sum(axis=1); n = mk.sum(axis=1)
        bench[f"{lo}-{hi if hi < 99 else '+'}"] = np.where(n >= 10, s / np.maximum(n, 1), np.nan)
    out, detail = [], {}
    for fam, mask in (("SCAN", brk), ("TIER", tier)):
        T = house(P, mask)
        T["band"] = T.adr.map(band_of)
        T["fwd"] = [F[i, j] for i, j in zip(T.i, T.j)]
        T["excess"] = [F[i, j] - bench[b][i] if b else np.nan for i, j, b in zip(T.i, T.j, T.band)]
        T["year"] = pd.to_datetime(T.date).dt.year
        for b in ["2-3", "3-4", "4-7", "7-+"]:
            g = T[T.band == b]
            if len(g) < 30:
                continue
            ex = g.groupby("date").excess.mean()                             # date-clustered
            yrs = g.groupby("year").excess.mean()
            h1, h2 = g[g.date < SPLIT].excess.mean(), g[g.date >= SPLIT].excess.mean()
            out.append(dict(family=fam, band=b, n=len(g), dates=len(ex), fwd20=g.fwd.mean(), excess20=g.excess.mean(),
                            t=tstat(ex), h1=h1, h2=h2, yrs_pos=f"{(yrs > 0).sum()}/{len(yrs)}",
                            house_pct=g.pct.mean(), house_pct_med=g.pct.median(), house_R=g.R.mean(),
                            win=100 * (g.pct > 0).mean()))
            detail[(fam, b)] = g
    R = pd.DataFrame(out)
    print(f"house breakout, ADR gate lowered to 2; events from {START}; 20d ADR-matched excess = PRIMARY; house process"
          f" = close entry, day-low stop floored at 2%, 20-EMA exit, <= 60 sessions (% of price and R, cap {R_CAP:.0f})\n")
    print(R.round(3).to_string(index=False))
    print("\nhouse-process % return: lowered band minus the band above it (per-date difference in means, date-clustered)")
    for fam, lo_b, hi_b in (("SCAN", "2-3", "3-4"), ("TIER", "3-4", "4-7")):
        a = detail[(fam, lo_b)].groupby("date").pct.mean(); b = detail[(fam, hi_b)].groupby("date").pct.mean()
        d = (a.reindex(a.index.union(b.index)).mean() - b.mean())
        # difference t via a two-sample on date means
        se = sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        print(f"  {fam}: {lo_b} {a.mean():+.2f}% vs {hi_b} {b.mean():+.2f}%  diff {a.mean() - b.mean():+.2f}pp, t {(a.mean() - b.mean()) / se:+.2f}")
    print("\nby year, 20d ADR-matched excess (pp):")
    for fam, b in (("SCAN", "2-3"), ("SCAN", "3-4"), ("TIER", "3-4"), ("TIER", "4-7")):
        g = detail[(fam, b)]
        print(f"  {fam} {b}: " + "  ".join(f"{y} {v:+.2f}" for y, v in g.groupby("year").excess.mean().items()))
    verdict = []
    for fam, lo_b, hi_b in (("SCAN", "2-3", "3-4"), ("TIER", "3-4", "4-7")):
        r = R[(R.family == fam) & (R.band == lo_b)].iloc[0]
        a = detail[(fam, lo_b)].groupby("date").pct.mean(); b = detail[(fam, hi_b)].groupby("date").pct.mean()
        dt = (a.mean() - b.mean()) / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        ok = bool(r.excess20 > 0 and r.t >= 3 and r.h1 > 0 and r.h2 > 0 and int(r.yrs_pos.split("/")[0]) >= 5 and dt > -2)
        verdict.append(f"{fam} admit {lo_b}: {'YES' if ok else 'no'}")
    print("\n" + " | ".join(verdict))
    R.to_csv(pt.REPO / "data/studies/adr_floor_test_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()

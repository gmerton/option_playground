#!/usr/bin/env python3
"""
BREAKOUT CLOSE vs WAITING TO BUY NEAR THE 20 EMA, SAME NAMES, PAIRED (pre-registered 2026-10-03, before any run)

WHY. Gabe 2026-10-03: Luk and Ariel buy ~0.7-0.8 ADR above the 20 EMA vs the precision tier's +2.8 ADR; "has the
house breakout beaten buying lower and closer to the 20 EMA?" The ledger has no direct answer and two indirect ones
that disagree (TEST_INDEX §4): the pullback-entry study (2026-09-17) had the breakout ahead (+2.6% vs +1.2-2.4%, no
t on the gap); the entry-extension study (2026-09-20) had a random LATER entry in the same name ~2.6 ADR lower beating
it by ~0.4R. Different cohorts, horizons and exits. This test holds the names and the exit date fixed and moves only
the entry price.

SIGNALS. Every precision-tier house breakout (run_precision_tier_control.build on liquid_panel_2009: ADR 4-7, within
15% of the 52-week high, EMA stack 5-40 days, fresh close above the 15-day pivot, RVOL >= 1.1, top half of the range,
gap < 5%, day change < 8%), signal dates 2010-01-04 -> 2026-08 (room for the horizon). ⚠ 2026-survivor panel.

ARMS (per signal, same name, same EXIT DATE):
  A  BREAKOUT   buy the close of the signal day t.
  B  PULLBACK   resting limit from t+1 through t+10 at L_d = EMA20[d-1] + 1.0 x ADR$[d-1] (ADR$ = ADR% x close[d-1];
                both known at the prior close). Filled on the first day d whose LOW <= L_d, at min(open_d, L_d).
                Not filled in 10 sessions -> NO TRADE (return 0: the order expires, the cash sits).
  EXIT (primary) both arms sell the close of t+20, no stop. One exit date for both, so the difference is the entry
                price plus B's missed trades -- nothing about stops or trails.
  COSTS 10 bp per side on every filled trade.

PRIMARY. Per signal: B - A in % (B = 0 when unfilled). Mean over signals, t clustered by signal date. This is the
  return of the RULE "wait for the pullback" vs the rule "buy the breakout", including the winners it misses; nothing
  is conditioned on what happened later.
BAR (discovery): t >= 3 with both halves (2010-18 / 2019-26) the same sign. Positive -> waiting for the 20-EMA zone
  BEATS the breakout close (PASS for "buy lower"). Negative -> the breakout close wins (INVERTED for "buy lower").
  Otherwise NULL / UNDERPOWERED (MDE = 2.8 x SE).
REPORTED, not a pass:
  - fill rate; A's return on the signals B never filled (what waiting gives up); A vs B on filled signals only
    (⚠ conditioned on a pullback having happened -- descriptive, the cohort B can see);
  - B per day of capital (B holds fewer sessions);
  - variants: band 0.5 ADR; wait 5 / 20 sessions; fill on a CLOSE inside the band (buy that close) instead of a limit;
  - house-managed version: A = day-low stop judged on the close + exit on the first close below the 20 EMA (cap 60);
    B = exit on the first close below the 20 EMA after fill, or a close 1 ADR below the fill (cap 60);
  - per year; the generic (non-precision) breakout pool as a second cohort.
PRIOR ~35% that B wins: the extension mechanism says the 2.6 ADR is real money; the pullback study says the strongest
  names never come back, and B gives those up.

  PYTHONPATH=src:. .venv/bin/python3 run_breakout_vs_pullback_entry.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from run_precision_tier_control import build

OUT = "data/studies/breakout_vs_pullback_entry_2026-10-03"
COST, H, CAP = 0.0010, 20, 60
SPLIT = pd.Timestamp("2019-01-01")


def run(P, mask, band=1.0, wait=10, fill="limit", managed=False) -> pd.DataFrame:
    C, Hh, Lo, O = P.close.values, P.high.values, P.low.values, P.open.values
    E20 = P.ema20.values; A = P.adr.values / 100
    dates = P.close.index
    ii, jj = np.where(mask.values)
    lo, hi = dates.searchsorted(pd.Timestamp("2010-01-04")), len(dates) - max(H, CAP) - 1
    rows = []
    for i, j in zip(ii, jj):
        if not (lo <= i < hi) or not np.isfinite(C[i, j]):
            continue
        # arm A
        if managed:
            stop = Lo[i, j]; ra, xa = None, None
            for k in range(i + 1, min(i + CAP, len(dates) - 1) + 1):
                if not np.isfinite(C[k, j]):
                    continue
                if C[k, j] < stop or C[k, j] < E20[k, j] or k == i + CAP:
                    ra, xa = C[k, j] / C[i, j] - 1, k; break
            if ra is None:
                continue
        else:
            if not np.isfinite(C[i + H, j]):
                continue
            ra, xa = C[i + H, j] / C[i, j] - 1, i + H
        ra -= 2 * COST
        # arm B
        fd, fpx = None, None
        for d in range(i + 1, i + wait + 1):
            lvl = E20[d - 1, j] + band * A[d, j] * C[d - 1, j]
            if not np.isfinite(lvl) or not np.isfinite(Lo[d, j]):
                continue
            if fill == "limit" and Lo[d, j] <= lvl:
                fd, fpx = d, min(O[d, j], lvl) if np.isfinite(O[d, j]) else lvl; break
            if fill == "close" and C[d, j] <= lvl:
                fd, fpx = d, C[d, j]; break
        if fd is None:
            rb, xb, filled = 0.0, None, False
        else:
            filled = True
            if managed:
                xb = None
                for k in range(fd + 1, min(fd + CAP, len(dates) - 1) + 1):
                    if not np.isfinite(C[k, j]):
                        continue
                    if C[k, j] < E20[k, j] or C[k, j] < fpx * (1 - A[fd, j]) or k == fd + CAP:
                        xb = k; break
                if xb is None:
                    continue
                rb = C[xb, j] / fpx - 1 - 2 * COST
            else:
                xb = i + H
                rb = C[xb, j] / fpx - 1 - 2 * COST
        rows.append(dict(date=dates[i], sym=P.close.columns[j], ra=ra * 100, rb=rb * 100, filled=filled,
                         days_a=xa - i, days_b=(xb - fd) if filled else 0,
                         ext_a=(C[i, j] - E20[i, j]) / (A[i, j] * C[i - 1, j]),
                         ext_b=((fpx - E20[fd - 1, j]) / (A[fd, j] * C[fd - 1, j])) if filled else np.nan))
    return pd.DataFrame(rows)


def ct(x: pd.Series, d: pd.Series) -> tuple[float, float, int]:
    x = x.dropna(); d = d.loc[x.index]; n = len(x)
    if n < 20:
        return np.nan, np.nan, n
    mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
    se = np.sqrt((g ** 2).sum()) / n * np.sqrt(G / (G - 1))
    return mu, mu / se, n


def main() -> None:
    P, brk, prec = build("data/cache/liquid_panel_2009.parquet")
    R = run(P, prec)
    R.to_csv(f"{OUT}_signals.csv", index=False)
    R["diff"] = R.rb - R.ra
    mu, t, n = ct(R["diff"], R.date)
    h1, h2 = R[R.date < SPLIT]["diff"].mean(), R[R.date >= SPLIT]["diff"].mean()
    se = abs(mu / t); mde = 2.8 * se
    if t >= 3 and h1 > 0 and h2 > 0:
        v = "PASS -- waiting for the 20-EMA zone beats the breakout close"
    elif t <= -3 and h1 < 0 and h2 < 0:
        v = "INVERTED -- the breakout close beats waiting"
    else:
        v = "NULL" if abs(mu) < mde else "UNDERPOWERED"
    f = R[R.filled]; nf = R[~R.filled]
    L = [f"# Breakout close vs waiting for the 20-EMA zone ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(R)} precision-tier breakouts {R.date.min().date()} -> {R.date.max().date()} (liquid_panel_2009, survivors).", "",
         f"**{v}**", "",
         f"PRIMARY B - A per signal (unfilled B = 0), exit both at t+20 close: **{mu:+.2f}pp, t {t:.2f}**, n {n}; "
         f"halves 2010-18 {h1:+.2f} / 2019-26 {h2:+.2f}; MDE {mde:.2f}pp", "",
         f"- A breakout close: {R.ra.mean():+.2f}% per signal; B pullback rule: {R.rb.mean():+.2f}% per signal", "",
         "## Reported, not a pass", "",
         f"- fill rate {R.filled.mean():.0%}; entry vs 20 EMA: A median {R.ext_a.median():+.2f} ADR, B fills {f.ext_b.median():+.2f} ADR",
         f"- what waiting gives up: A on never-filled signals {nf.ra.mean():+.2f}% (n {len(nf)})",
         f"- filled only (⚠ conditioned on a pullback): A {f.ra.mean():+.2f}% vs B {f.rb.mean():+.2f}% (n {len(f)})",
         f"- B per held session: {(f.rb / f.days_b.replace(0, np.nan)).mean():+.3f}% vs A {(R.ra / R.days_a).mean():+.3f}%"]
    for lab, kw in (("band 0.5 ADR", dict(band=0.5)), ("wait 5", dict(wait=5)), ("wait 20", dict(wait=20)),
                    ("fill on a close in the band", dict(fill="close")), ("house-managed both arms", dict(managed=True))):
        X = run(P, prec, **kw); X["diff"] = X.rb - X.ra
        a, b_, c = ct(X["diff"], X.date)
        L.append(f"- {lab}: B - A {a:+.2f}pp t {b_:.2f} n {c}; fill {X.filled.mean():.0%}; halves "
                 f"{X[X.date < SPLIT]['diff'].mean():+.2f} / {X[X.date >= SPLIT]['diff'].mean():+.2f}")
    G = run(P, brk & ~prec); G["diff"] = G.rb - G.ra
    a, b_, c = ct(G["diff"], G.date)
    L.append(f"- generic (non-precision) breakouts: B - A {a:+.2f}pp t {b_:.2f} n {c}; fill {G.filled.mean():.0%}")
    L += ["", "Per year (primary B - A, pp):", "", R.groupby(R.date.dt.year)["diff"].agg(["mean", "count"]).round(2).to_string()]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

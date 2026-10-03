#!/usr/bin/env python3
"""
"THEIR STRATEGY" vs THE HOUSE BREAKOUT, SAME PERIOD (pre-registered 2026-10-03, before any scoring of this subset)

WHY. Gabe 2026-10-03, after the overlap check (creator_vs_house_overlap_2026-10-03.md: 0-1% of Luk's / Ariel's long
entries were a house breakout; they buy faster leaders ~14-18% off the high, inside the base below the 15-day pivot,
~0.8 ADR above the 20 EMA, on an intraday trigger with a 1-2.5% stop): test their strategy as a whole against ours.

THEIR STRATEGY = the Luk-style intraday pullback entry already built and run in run_luk_tight_stop_survival.py
(pre-registered 9/30; entries in data/studies/logs/luk_tight_stop_survival_trades.csv, 2024-10 -> 2026-08, 674 liquid
names): leading-list names (close > EMA50 > EMA150, EMA21 rising, ADR >= 4, ADDV >= $100M), session low in the rising-
EMA zone, a 5-minute turn (break of the prior bar's high after a lower high) 10:00-15:30, stop = session low (0.4-2%),
exit the first daily close below the 9 EMA, cap 20 sessions, 10 bp/side ("ret_tight"). FIRST attempt per name-day only.
NEW HERE: their SELECTION PROFILE as a gate. For each of 4 features, measured at the prior close (t-1) so the rule is
tradeable, the gate is the 10th-90th percentile of the SAME feature over Luk's and Ariel's actual long entries
(run_creator_vs_house_overlap.entries(), features recomputed at t-1 here). Bands come from their features only, never
from outcomes:
  ADR % (20-day, through t-1) · % off the 52-week high · EMA stack days · close vs the 15-day pivot, in ADR
PROFILE = entries inside all four bands.

THE HOUSE = precision-tier breakouts (run_precision_tier_control.build, liquid_panel_2019) with signal dates in the same
window, house-managed: buy the close, stop = the signal day's low judged on the close, exit the first close below the
20 EMA, cap 60, 10 bp/side.

PRIMARY. Mean % per trade, PROFILE minus HOUSE, each under its own management. SE = the two date-clustered SEs
combined (independent samples). BAR (discovery): |t| >= 3 and both halves (split 2025-10-01) the same sign.
  positive -> their strategy beats the house breakout; negative -> the house beats it; else NULL / UNDERPOWERED.
REPORTED, not a pass: PROFILE vs the rest of the tight-stop entries (does their selection profile add to the entry?);
  % per trade per session held; win rate; same-day stop rate; per-month means; n per side.
⚠ One tape (2024-10 -> 2026-08), survivor universes on both sides, different holding periods by design (theirs is
  shorter). The tight-stop test as a whole was NULL vs beta (t +0.02); this asks whether the profile slice differs and
  how both compare with the house rule over the same months.

  PYTHONPATH=src:. .venv/bin/python3 run_creator_profile_strategy.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from run_creator_vs_house_overlap import entries
from run_luk_picks_vs_controls import stack_run
from run_precision_tier_control import build

TRADES = "data/studies/logs/luk_tight_stop_survival_trades.csv"
OUT = "data/studies/creator_profile_strategy_2026-10-03"
SPLIT = pd.Timestamp("2025-10-01")
COST, CAP = 0.0010, 60


def features(P):
    C, H = P.close, P.high
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    piv = H.shift(1).rolling(15).max()
    stack = stack_run(C, adr=P.adr)
    # every feature as of the PRIOR close, shifted onto day t
    return {"adr": P.adr, "off52": ((C / hi52 - 1) * 100).shift(1), "stack": stack.shift(1),
            "vs_piv": ((C / piv - 1) * 100 / P.adr).shift(1)}


def at(F, tk, d):
    try:
        return F.at[d, tk]
    except KeyError:
        return np.nan


def house(P, prec, d0, d1) -> pd.DataFrame:
    C, Lo, E20 = P.close.values, P.low.values, P.ema20.values
    dates = P.close.index; rows = []
    for i, j in zip(*np.where(prec.values)):
        if not (d0 <= dates[i] <= d1):
            continue
        for k in range(i + 1, min(i + CAP, len(dates) - 1) + 1):
            if np.isfinite(C[k, j]) and (C[k, j] < Lo[i, j] or C[k, j] < E20[k, j] or k == i + CAP):
                rows.append(dict(date=dates[i], ret=(C[k, j] / C[i, j] - 1 - 2 * COST) * 100, held=k - i)); break
    return pd.DataFrame(rows)


def ct(x: pd.Series, d: pd.Series):
    n = len(x); mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
    return mu, np.sqrt((g ** 2).sum()) / n * np.sqrt(G / (G - 1)), n


def main() -> None:
    P, brk, prec = build()
    F = features(P)
    # creators' bands
    E = entries(); E = E[E.side == "long"]
    cr = pd.DataFrame({n: [at(F[n], r.tk, P.close.index[min(P.close.index.searchsorted(pd.Timestamp(r.fill)), len(P.close.index) - 1)])
                           for r in E.itertuples()] for n in F}).dropna()
    bands = {n: (cr[n].quantile(0.10), cr[n].quantile(0.90)) for n in F}
    # their-strategy entries
    T = pd.read_csv(TRADES, parse_dates=["date"])
    T = T[T.attempt == 0].copy()
    for n in F:
        T[n] = [at(F[n], tk, d) for tk, d in zip(T.ticker, T.date)]
    inb = np.logical_and.reduce([(T[n] >= lo) & (T[n] <= hi) for n, (lo, hi) in bands.items()])
    T["ret"] = T.ret_tight * 100
    Pf, Rest = T[inb], T[~inb & T[list(F)].notna().all(axis=1)]
    Hh = house(P, prec, T.date.min(), T.date.max())
    mu1, se1, n1 = ct(Pf.ret, Pf.date); mu2, se2, n2 = ct(Hh.ret, Hh.date)
    diff = mu1 - mu2; t = diff / np.sqrt(se1 ** 2 + se2 ** 2)
    h = []
    for sel in (lambda z: z.date < SPLIT, lambda z: z.date >= SPLIT):
        h.append(Pf[sel(Pf)].ret.mean() - Hh[sel(Hh)].ret.mean())
    mde = 2.8 * np.sqrt(se1 ** 2 + se2 ** 2)
    v = ("THEIR STRATEGY BEATS THE HOUSE" if t >= 3 and min(h) > 0 else "THE HOUSE BEATS THEIR STRATEGY" if t <= -3 and max(h) < 0
         else "NULL" if abs(diff) < mde else "UNDERPOWERED")
    mu3, se3, n3 = ct(Rest.ret, Rest.date)
    L = [f"# Their strategy (creator profile + Luk-style intraday pullback) vs the house breakout ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         "Bands (10th-90th pct of Luk's + Ariel's long entries, prior-close features, n %d): " % len(cr)
         + "; ".join(f"{n} {lo:+.2f}..{hi:+.2f}" for n, (lo, hi) in bands.items()), "",
         f"**{v}**", "",
         f"PRIMARY PROFILE − HOUSE: **{diff:+.2f}pp per trade, t {t:.2f}**; halves {h[0]:+.2f} / {h[1]:+.2f}; MDE {mde:.2f}pp", "",
         f"- PROFILE (their strategy): {mu1:+.2f}% per trade (t {mu1 / se1:.2f}), n {n1}, win {(Pf.ret > 0).mean():.0%}, "
         f"stopped same day {Pf.stopped_same_day.mean():.0%}, mean held {Pf.held.mean():.1f} sessions",
         f"- HOUSE breakout: {mu2:+.2f}% per trade (t {mu2 / se2:.2f}), n {n2}, win {(Hh.ret > 0).mean():.0%}, mean held {Hh.held.mean():.1f} sessions", "",
         "## Reported, not a pass", "",
         f"- does the profile add to the entry? PROFILE − REST of the tight-stop entries: {mu1 - mu3:+.2f}pp, t {(mu1 - mu3) / np.sqrt(se1 ** 2 + se3 ** 2):.2f} (rest n {n3}, {mu3:+.2f}%)",
         f"- per session held: PROFILE {(Pf.ret / Pf.held.clip(lower=1)).mean():+.3f}% vs HOUSE {(Hh.ret / Hh.held.clip(lower=1)).mean():+.3f}%",
         "", "Per month (mean % per trade, n):", "",
         pd.DataFrame({"profile": Pf.groupby(Pf.date.dt.to_period("M")).ret.mean(), "n_p": Pf.groupby(Pf.date.dt.to_period("M")).size(),
                       "house": Hh.groupby(Hh.date.dt.to_period("M")).ret.mean(), "n_h": Hh.groupby(Hh.date.dt.to_period("M")).size()}).round(2).to_string()]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
UR + VOLUME SPIKE IN A WEAK TAPE -- out-of-sample holdout, 2000-2009 (pre-registered 2026-10-03, before any data pull)

ORIGIN. Exploratory cell of run_weak_market_entries.py (2026-10-02, TEST_INDEX §7): undercut-and-reclaim on leaders,
with event-day volume >= 1.5x its 20-day average, on WEAK-regime days: +1.34pp (lo10 level, t 2.22, n 544) and
+1.60pp (EMA50 level, t 2.17, n 283) of 10-session excess over same-date random leaders; EMA20 level +0.38pp
(t 0.38, n 168). Drendel's claim (video xYLU6Ep2U1M): "you want to see volume peak on the undercut". Found by looking
at ~27 exploratory cells, so it is a lead, not a result. This script tests it once, on data it has never seen.

HOLDOUT DATA. Signals 2000-01-03 -> 2009-12-17 (the discovery run's signals began 2010-01-04; 2009 was warm-up
only). Same tickers as liquid_panel_2009 (1,728 names, liquid as of 2026) + SPY, yfinance ADJUSTED daily from
1999-01-01, built by --build into data/cache/liquid_panel_1999_holdout.parquet. ⚠ Survivorship is WORSE here than in
discovery (a 2026 survivor list projected back 10-26 years). It flatters dip-buying; the same-date control comes
from the same survivor panel, which offsets part of it, but a PASS must be read with that caveat. Local: ~1.7k
yfinance pulls, minutes of CPU.

FROZEN SPEC -- identical to the discovery code, nothing re-tuned:
  universe  eligible (ADDV50 >= $50M nominal, px >= $5, not suspect), ADR >= 3, 63-session return at t-1 in the
            top 30% of eligible names that date. (Nominal $50M leaves fewer names in 2000-09; reported, not changed.)
  context   close[t-1] <= max(close[t-10..t-1]) - 1 ADR (in price)
  UR        L in {min low[t-10..t-1], EMA20[t-1], EMA50[t-1]}: open[t] >= L, low[t] < L, close[t] > L
  VOLSPIKE  volume[t] >= 1.5 x mean(volume[t-20..t-1])
  WEAK[t-1] (SPY close < EMA20 and EMA10 < EMA20) OR (< 40% of eligible names above their 50-SMA)
  entry     close[t]; outcome = % return to close[t+10] minus the mean of 3 random OTHER leaders, same date, same
            entry (excess return; slippage cancels). Month-clustered SE.

PRIMARY (one cell): the three levels POOLED (one event per name-day), UR & VOLSPIKE & WEAK.
  The pooled cell is pre-registered rather than the two levels that looked best, so the level choice is not a
  second look at the discovery data.
BAR (holdout of one pre-specified cell):
  PASS  t >= 2.0 AND point estimate >= +0.65pp (half the discovery's ~+1.3pp) AND both holdout halves
        (2000-04 / 2005-09) > 0.
  then  ADOPTION-eligible only if the discovery + holdout pooled t >= 3.0 (the house discovery bar).
  FAIL  t < 1 or estimate <= 0 -> the lead is RETRACTED as an exploratory artefact.
  else  UNDERPOWERED.
KEY SECONDARY (does the VOLUME do the work?): UR & VOLSPIKE & WEAK minus UR & no-spike & WEAK, same holdout. If the
  primary passes but this gap is ~0, the edge belongs to weak-tape UR, not to the volume condition.
Also reported, not a pass: per-level cells, the STRONG-regime analogue, n eligible leaders per year, per-year signs.
POWER (stated in advance): discovery SE ~0.6pp at n ~550. Expect n ~300-700 here (fewer liquid names, more weak
  days in 2000-03 and 2008-09). At a true +0.7pp that is t ~1-1.5, so UNDERPOWERED is a likely outcome; a true
  +1.3pp gives t ~2.
PRIOR: ~20%. Exploratory best-of-many cells usually shrink by half or more out of sample.
IF UNDERPOWERED: stage 2 is a forward lockbox (log every qualifying event from the daily panel from the commit
  date on, score after >= 150 weak-regime events). Not built until stage 1 reports.

  PYTHONPATH=src .venv/bin/python3 run_ur_volspike_holdout.py --build     # pull the 1999-2009 panel (once)
  PYTHONPATH=src .venv/bin/python3 run_ur_volspike_holdout.py             # the test
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
import yfinance as yf

from lib.studies.pattern_test import load_panel

PANEL = "data/cache/liquid_panel_1999_holdout.parquet"
DISCOVERY = "data/studies/weak_market_entries_2026-10-02_events.csv"
OUT = "data/studies/ur_volspike_holdout_2026-10-03"
HOLD, N_CTL = 10, 3
SIG0, SIG1 = "2000-01-03", "2009-12-17"
HALF = pd.Timestamp("2005-01-01")
RNG = np.random.default_rng(20261003)


def build() -> None:
    tks = sorted(pd.read_parquet("data/cache/liquid_panel_2009.parquet", columns=["ticker"]).ticker.unique())
    frames, t0 = [], time.time()
    for k in range(0, len(tks), 100):
        px = yf.download(tks[k:k + 100], start="1999-01-01", end="2010-01-31", auto_adjust=True, progress=False,
                         group_by="ticker", threads=True)
        for t in tks[k:k + 100]:
            try:
                h = px[t].dropna(subset=["Close"])
            except KeyError:
                continue
            if len(h):
                f = h.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].reset_index().rename(columns={"Date": "date"})
                f["ticker"] = t; f["dolvol"] = f.close * f.volume; frames.append(f)
        print(f"  {min(k + 100, len(tks))}/{len(tks)} names, {time.time() - t0:.0f}s", flush=True)
    P = pd.concat(frames, ignore_index=True)
    P.to_parquet(PANEL, index=False)
    print(f"wrote {PANEL}: {P.ticker.nunique()} names with data, {P.date.min().date()} -> {P.date.max().date()}")


def events(P, V) -> pd.DataFrame:
    """The frozen discovery definitions (run_weak_market_entries.py), UR only, plus the volume flag."""
    O, H, L, C = P.open.reindex_like(P.close), P.high, P.low, P.close
    dates = C.index
    adr_px = P.adr / 100 * C.shift(1)
    e10 = C.ewm(span=10, adjust=False).mean(); e20 = P.ema20; e50 = C.ewm(span=50, adjust=False).mean()
    sma50 = C.rolling(50).mean()
    elig = P.elig & (P.adr >= 3)
    rk = (C.shift(1) / C.shift(64) - 1).where(P.elig.shift(1, fill_value=False)).rank(axis=1, pct=True)
    leader = elig & (rk >= 0.70)
    spy = C["SPY"]
    down = (spy < e20["SPY"]) & (e10["SPY"] < e20["SPY"])
    el = P.elig.fillna(False).astype(bool)
    breadth = ((C > sma50) & el).sum(axis=1).astype(float) / el.sum(axis=1).astype(float).replace(0, np.nan)
    weak = (down | (breadth < 0.40)).shift(1, fill_value=False)
    pb = C.shift(1) <= C.rolling(10).max().shift(1) - adr_px
    lv = {"lo10": L.rolling(10).min().shift(1), "ema20": e20.shift(1), "ema50": e50.shift(1)}
    spike = (V >= 1.5 * V.rolling(20).mean().shift(1)).values
    F = ((C.shift(-HOLD) / C - 1) * 100).values
    lo, hi = dates.searchsorted(pd.Timestamp(SIG0)), dates.searchsorted(pd.Timestamp(SIG1), side="right")
    LA = leader.values; rows = []
    for lvl, x in lv.items():
        M = (pb & (O >= x) & (L < x) & (C > x) & leader).values
        for i in range(lo, min(hi, len(dates) - HOLD - 1)):
            js = np.flatnonzero(M[i])
            if not len(js):
                continue
            pool = np.flatnonzero(LA[i] & np.isfinite(F[i]))
            for j in js:
                cp = pool[pool != j]
                if not np.isfinite(F[i, j]) or len(cp) < N_CTL:
                    continue
                rows.append((lvl, dates[i], C.columns[j], F[i, j], F[i, j] - F[i, RNG.choice(cp, N_CTL, replace=False)].mean(), bool(spike[i, j])))
    E = pd.DataFrame(rows, columns=["level", "date", "sym", "ret", "excess", "volspike"])
    E["weak"] = weak.reindex(E.date).values
    E["month"] = E.date.dt.to_period("M")
    n_lead = leader.loc[SIG0:SIG1].sum(axis=1).groupby(lambda d: d.year).mean().round(0)
    return E, n_lead


def ms(x: pd.DataFrame) -> tuple[float, float, int]:
    n = len(x)
    if n < 20 or x.month.nunique() < 6:
        return np.nan, np.nan, n
    mu = x.excess.mean(); g = x.month.nunique()
    se = np.sqrt(((x.excess - mu).groupby(x.month).sum() ** 2).sum()) / n * np.sqrt(g / (g - 1))
    return mu, se, n


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); a = ap.parse_args()
    if a.build:
        build(); return
    P = load_panel(PANEL)
    raw = pd.read_parquet(PANEL)
    V = raw.pivot(index="date", columns="ticker", values="volume").reindex_like(P.close)
    E, n_lead = events(P, V)
    E.to_csv(f"{OUT}_events.csv", index=False)
    pooled = E.sort_values("level").drop_duplicates(["date", "sym"])
    prim = pooled[pooled.weak & pooled.volspike]
    mu, se, n = ms(prim); t = mu / se
    h1, h2 = ms(prim[prim.date < HALF])[0], ms(prim[prim.date >= HALF])[0]
    nos = pooled[pooled.weak & ~pooled.volspike]; mu0, se0, n0 = ms(nos)
    gap, gap_t = mu - mu0, (mu - mu0) / np.sqrt(se ** 2 + se0 ** 2)
    # discovery + holdout pooled, same cell
    D = pd.read_csv(DISCOVERY, parse_dates=["date"])
    D = D[(D.tactic == "UR")].sort_values("level").drop_duplicates(["date", "sym"])
    D = D[D.weak & D.volspike][["date", "sym", "excess"]].assign(month=lambda z: z.date.dt.to_period("M"))
    cmu, cse, cn = ms(pd.concat([D, prim[["date", "sym", "excess", "month"]]]))
    if t >= 2.0 and mu >= 0.65 and h1 > 0 and h2 > 0:
        verdict = "PASS (holdout)" + (" + ADOPTION-ELIGIBLE (pooled t >= 3)" if cmu / cse >= 3 else " -- pooled t < 3: PARKED")
    elif t < 1 or mu <= 0:
        verdict = "FAIL -> lead RETRACTED"
    else:
        verdict = "UNDERPOWERED -> stage 2 forward lockbox"
    L = [f"# UR + volume spike, weak tape -- 2000-09 holdout ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"**{verdict}**", "",
         f"PRIMARY pooled levels, UR & volspike & WEAK: {mu:+.2f}pp, t {t:.2f}, n {n}; halves 2000-04 {h1:+.2f} / 2005-09 {h2:+.2f}",
         f"KEY SECONDARY volume gap (spike - no spike, weak UR): {gap:+.2f}pp, t {gap_t:.2f} (no-spike {mu0:+.2f}pp, n {n0})",
         f"Discovery + holdout pooled: {cmu:+.2f}pp, t {cmu / cse:.2f}, n {cn}", "", "## Reported, not a pass", ""]
    for lvl, g in E.groupby("level"):
        for lab, sel in (("weak+spike", g.weak & g.volspike), ("weak, no spike", g.weak & ~g.volspike), ("strong+spike", ~g.weak & g.volspike)):
            m_, s_, n_ = ms(g[sel]); L.append(f"- {lvl:5s} {lab:15s} {m_:+.2f}pp t {m_ / s_ if s_ else np.nan:.2f} n {n_}")
    yr = prim.groupby(prim.date.dt.year).excess.agg(["mean", "count"]).round(2)
    L += ["", "Per year (primary):", "", yr.to_string(), "", "Mean eligible leaders per day, by year:", "", n_lead.to_string()]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main()

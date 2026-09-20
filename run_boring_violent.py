#!/usr/bin/env python3
"""
Breitstein test 2: "boring stock, violent move" (ubofAZwgd4w [06:15]) -- capitulation reversion once the
shock is normalised by the name's OWN range. Refines the crash-leader study, which never normalised.

Pre-registered spec (memory: project_breitstein_test_queue #2):
  violent    1-day close-to-close drop >= k x the name's trailing-20 ADR (k = 4 primary; 3 / 5 sweeps)
  boring     prior ADR (as of yesterday) in the BOTTOM tercile of the eligible universe that day
  entry      long at the next session's open (harness), 10 bps slippage
  stop       the signal bar's low
  arms       harness five (stop_hold / t1R / t2R / trail_bar / ema20), hold 5
  also       5 / 20 / 60-session forward return (%) from the entry open vs (a) the same-name random
             control, same month, and (b) SPY over the same window
  A/B        the same k WITHOUT the boring leg (any ADR tercile) -> does "boring" add anything?
  un-norm    raw 1-day drop >= 15% (his "drops 15% in a day"), no ADR normalisation = the crash-leader cell
  veto       split by tape: SPY close > 21 EMA on the signal date (healthy) vs not; and breadth
             (% of eligible names above their 200sma) above / below its median
  news       (partial) names with earnings coverage in MySQL: within +/-1 session of a report vs not
  ledger     only A (k=4) and B (k=4); everything else report-only

Usage:
  PYTHONPATH=src MYSQL_PASSWORD=... .venv/bin/python3 run_boring_violent.py > data/studies/breitstein_tests/logs/boring_violent_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals, load_panel, run_daily, SLIP

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

TODAY = date.today().isoformat()
HORIZONS = (5, 20, 60)
RNG = np.random.default_rng(20260919)
RAW_DROP = 15.0


def frames(P):
    ret = P.close.pct_change(fill_method=None) * 100
    q = P.adr.where(P.elig).quantile(1 / 3, axis=1)
    boring = P.adr.le(q, axis=0) & P.elig
    return ret, boring


def cell_mask(P, kind: str, k: float):
    ret, boring = frames(P)
    if kind == "A":       # boring + violent
        return (ret <= -k * P.adr) & boring & P.elig
    if kind == "B":       # violent, any ADR
        return (ret <= -k * P.adr) & P.elig
    if kind == "C":       # un-normalised raw drop
        return (ret <= -RAW_DROP) & P.elig
    if kind == "CB":      # raw drop AND boring (his exact example)
        return (ret <= -RAW_DROP) & boring & P.elig
    raise ValueError(kind)


def pattern(P, kind, k):
    m = cell_mask(P, kind, k)
    return lambda _P: daily_signals(m, stop=P.low, side="long")


def fwd_table(P, S: pd.DataFrame, label: str, controls: int = 3) -> pd.DataFrame:
    """5/20/60-session forward return from the entry open, signal vs same-name control vs SPY."""
    O, C, idx = P.open.values, P.close.values, P.close.index
    spy = P.close.columns.get_loc("SPY")
    keys = {(int(r.j), int(r.i)) for r in S.itertuples()}
    rows = []

    def one(j, i, tag):
        if i + 1 >= len(C) or not np.isfinite(O[i + 1, j]):
            return
        e = O[i + 1, j] * (1 + SLIP)
        es = O[i + 1, spy]
        d = dict(tag=tag, date=idx[i], sym=P.close.columns[j])
        for h in HORIZONS:
            kk = i + h
            if kk < len(C) and np.isfinite(C[kk, j]):
                d[f"r{h}"] = 100 * (C[kk, j] * (1 - SLIP) / e - 1)
                d[f"x{h}"] = d[f"r{h}"] - 100 * (C[kk, spy] / es - 1)
        rows.append(d)

    for r in S.itertuples(index=False):
        j, i = int(r.j), int(r.i)
        one(j, i, "signal")
        d = pd.Timestamp(r.date)
        same = np.flatnonzero((idx.year == d.year) & (idx.month == d.month))
        cand = [c for c in same if (j, int(c)) not in keys and P.elig.values[c, j]]
        for c in RNG.choice(cand, size=min(controls, len(cand)), replace=False) if cand else []:
            one(j, int(c), "control")
    F = pd.DataFrame(rows)
    out = {}
    for tag in ("signal", "control"):
        f = F[F.tag == tag]
        for h in HORIZONS:
            s = f[f"r{h}"].dropna()
            by_day = s.groupby(f.loc[s.index, "date"]).mean()
            out[(tag, f"r{h}")] = dict(n=len(s), mean=s.mean(), med=s.median(), win=100 * (s > 0).mean(),
                                      t=by_day.mean() / by_day.std() * np.sqrt(len(by_day)) if len(by_day) > 2 else np.nan,
                                      xSPY=f[f"x{h}"].mean())
    T = pd.DataFrame(out).T
    print(f"\n--- forward returns (%), {label}: {int((F.tag=='signal').sum()):,} signals ---")
    print(T.round(2).to_string())
    for h in HORIZONS:
        print(f"  edge vs same-name control @{h}: {T.loc[('signal', f'r{h}'), 'mean'] - T.loc[('control', f'r{h}'), 'mean']:+.2f} pp")
    return F


def tape_series(P):
    spy = P.close["SPY"]
    healthy = spy > spy.ewm(span=21, adjust=False).mean()
    sma200 = P.close.rolling(200).mean()
    breadth = (P.close > sma200).where(P.elig).mean(axis=1)
    return healthy, breadth


def split_report(P, F: pd.DataFrame, cond: pd.Series, name: str):
    f = F[F.tag == "signal"].copy()
    f["cond"] = cond.reindex(pd.to_datetime(f.date)).values
    print(f"\n--- {name} split (signal forward returns %, mean / median / win / n) ---")
    rows = []
    for val, g in f.groupby("cond"):
        d = dict(cond=val, n=len(g))
        for h in HORIZONS:
            s = g[f"r{h}"].dropna()
            d[f"r{h}"] = s.mean(); d[f"med{h}"] = s.median(); d[f"win{h}"] = 100 * (s > 0).mean()
            d[f"xSPY{h}"] = g[f"x{h}"].mean()
        rows.append(d)
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def earnings_split(P, F: pd.DataFrame):
    try:
        from lib.mysql_lib import _get_engine
        E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
    except Exception as e:  # noqa: BLE001
        print(f"\n(earnings split skipped: {type(e).__name__}: {str(e)[:80]})")
        return
    E["d"] = pd.to_datetime(E.raw_date)
    cov = set(E.ticker)
    idx = P.close.index
    pos = {t: np.searchsorted(idx.values, g.d.values) for t, g in E.groupby("ticker")}
    f = F[(F.tag == "signal") & F.sym.isin(cov)].copy()
    ii = np.searchsorted(idx.values, pd.to_datetime(f.date).values)
    near = []
    for s, i in zip(f.sym, ii):
        near.append(bool(np.any(np.abs(pos[s] - i) <= 1)))
    f["near_earnings"] = near
    print(f"\n--- earnings split (covered names only: {f.sym.nunique()} names, {len(f)} signals) ---")
    rows = []
    for val, g in f.groupby("near_earnings"):
        d = dict(near_earnings=val, n=len(g))
        for h in HORIZONS:
            s = g[f"r{h}"].dropna(); d[f"r{h}"] = s.mean(); d[f"med{h}"] = s.median(); d[f"win{h}"] = 100 * (s > 0).mean()
        rows.append(d)
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def main():
    P = load_panel()
    ret, boring = frames(P)
    print(f"panel {P.close.shape[0]} x {P.close.shape[1]}; boring tercile ADR cut (median over days): "
          f"{P.adr.where(P.elig).quantile(1/3, axis=1).median():.2f}%; eligible-day ADR median "
          f"{P.adr.where(P.elig).stack().median():.2f}%")
    healthy, breadth = tape_series(P)
    print(f"healthy tape (SPY > 21 EMA) share: {100*healthy.mean():.0f}%; breadth median {breadth.median():.2f}")

    # ---- harness runs (R arms, hold 5, same-name control) ----
    cells = [("A", 4.0, True), ("B", 4.0, True), ("A", 3.0, False), ("A", 5.0, False),
             ("B", 3.0, False), ("C", 0, False), ("CB", 0, False)]
    names = {"A": "boring stock, violent move (drop >= {k:g}x own ADR, ADR bottom tercile)",
             "B": "violent move, any ADR (drop >= {k:g}x own ADR)",
             "C": f"raw 1-day drop >= {RAW_DROP:g}% (un-normalised, crash-leader style)",
             "CB": f"raw 1-day drop >= {RAW_DROP:g}% AND ADR bottom tercile"}
    sigs, tabs = {}, {}
    for kind, k, ledger in cells:
        nm = names[kind].format(k=k)
        m = cell_mask(P, kind, k)
        S = daily_signals(m, stop=P.low, side="long")
        sigs[(kind, k)] = S
        dd = (P.close / P.close.rolling(252).max() - 1).values[S.i.values, S.j.values] * 100
        print(f"\n\n================ {nm}: {len(S):,} signals, {S.sym.nunique()} names; median drawdown from 252d high "
              f"at signal {np.nanmedian(dd):.1f}%; median 1-day drop {np.nanmedian(ret.values[S.i.values, S.j.values]):.1f}% "
              f"================")
        tabs[(kind, k)] = run_daily(nm, pattern(P, kind, k), hold=5, panel=P, ledger=ledger,
                                    note="Breitstein test 2; stop = signal-bar low; ctrl = same name, random session, same month"
                                    + ("" if kind == "A" else "; A/B leg for the boring-stock cell"))

    # ---- forward returns 5/20/60 ----
    fwd = {}
    for kind, k in [("A", 4.0), ("A", 3.0), ("A", 5.0), ("B", 4.0), ("B", 3.0), ("C", 0), ("CB", 0)]:
        fwd[(kind, k)] = fwd_table(P, sigs[(kind, k)], names[kind].format(k=k))

    # ---- veto check on the boring cells (k=4 primary, k=3 for n) ----
    for kind, k in [("A", 4.0), ("A", 3.0), ("C", 0)]:
        lab = names[kind].format(k=k)
        split_report(P, fwd[(kind, k)], healthy.rename("SPY>21EMA"), f"{lab} | tape SPY>21EMA")
        split_report(P, fwd[(kind, k)], (breadth > breadth.median()).rename("breadth>median"), f"{lab} | breadth")

    # ---- earnings (partial coverage) on the pooled boring cell k=3 ----
    earnings_split(P, fwd[("A", 3.0)])

    # ---- summary ----
    print("\n\n################ SUMMARY ################")
    rows = []
    for (kind, k), tab in tabs.items():
        F = fwd[(kind, k)] if (kind, k) in fwd else None
        d = dict(cell=names[kind].format(k=k)[:60], n=int(tab.n.max()), best_arm=tab.meanR.idxmax(),
                 best_meanR=tab.meanR.max(), best_ctrl=tab.loc[tab.meanR.idxmax(), "ctrl"], t1R=tab.loc["t1R", "meanR"],
                 stop_hold=tab.loc["stop_hold", "meanR"], edge_best=tab.edge.max())
        if F is not None:
            for h in HORIZONS:
                s, c = F[F.tag == "signal"][f"r{h}"], F[F.tag == "control"][f"r{h}"]
                d[f"r{h}"] = s.mean(); d[f"r{h}_vs_ctrl"] = s.mean() - c.mean()
        rows.append(d)
    S = pd.DataFrame(rows)
    print(S.round(2).to_string(index=False))
    S.to_csv(pt.REPO / f"data/studies/breitstein_tests/boring_violent_summary_{TODAY}.csv", index=False)


if __name__ == "__main__":
    main()

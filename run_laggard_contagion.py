#!/usr/bin/env python3
"""
Laggard-breakdown contagion (pre-registered 2026-09-30, BEFORE running; spec #1 in
data/traderlion/videos/interviews/2026-09-13_-dv_2h61a2o/notes.md; Ariel Hernandez [00:47:45-00:49:30]: "when the
laggard breaks structure first, the leader is usually one to three weeks away from doing the same" -- his example CIEN,
a long-uptrend optics name breaking its 50-day on earnings, then the other optics names "turned into a headache").

PANEL   liquid_panel_2009 via run_precision_tier_control.build (elig = ADDV >= $50M, px >= $5, not suspect),
        2010-01 -> 2026-09; industry = data/ticker_industry_map.csv (yfinance industry).
EVENT   name X on day t: close < SMA50 on t after >= 40 consecutive closes >= SMA50; X ranked in the TOP QUINTILE of its
        industry by 126-session return 20 sessions earlier (a former leader, per his CIEN example); the industry has
        >= 4 eligible names on t; first event in that industry in 20 sessions (later ones in the window are dropped).
PEERS   the industry's OTHER eligible names still closing >= their SMA50 on t ("the leaders").
CONTROL same-date eligible names >= their SMA50 in industries with NO event in [t-20, t] (past only: excluding
        industries that break LATER would leak the outcome), reweighted to the peers' ADR-decile mix (TT-ablation method).
        It holds the date, the above-50 state and the volatility mix fixed and varies whether a group-mate just broke.
PRIMARY peer mean 15-session forward return (close t -> close t+15) minus the ADR-matched control, one observation per
        event, t clustered by event date. TWO-SIDED (he says peers follow down; rotation/weak-tape results lean to mean
        reversion). Bar |t| >= 3, halves (split 2018-01-01) same sign, per-year table; 5d and 10d secondary (Sidak over
        3 horizons -> |t| >= 2.39 for those).
SECONDARY (his literal claim) share of peers that close below their own SMA50 within 15 sessions, vs control names
        matched on ADR decile AND distance above SMA50 (in ADR units, deciles) -- distance to the line is the obvious
        confound for a "breaks its 50 too" rate.
REPORTED  peers' day-0 return vs control (the common-shock check: if the laggard broke because the industry fell, the
        peers fell on day 0 too); event count / per year; the break-rate gap at 5/10/15.
Prior: low. Group-level RS has been descriptive, not predictive, every time (rotation study, theme co-breakouts NULL).
Local (cached panel, minutes).

Run: PYTHONPATH=src .venv/bin/python3 run_laggard_contagion.py   (log -> data/studies/logs/laggard_contagion.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

import run_precision_tier_control as pc

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/laggard_contagion.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, SPLIT = "2010-01-01", "2018-01-01"
HS = (5, 10, 15)


def run_length(b: pd.DataFrame) -> pd.DataFrame:
    """consecutive True count ending at each row."""
    v = b.values.astype(int)
    out = np.zeros_like(v)
    for r in range(len(v)):
        out[r] = (out[r - 1] + 1) * v[r] if r else v[r]
    return pd.DataFrame(out, index=b.index, columns=b.columns)


def tclu(x: pd.Series, dates: pd.Series) -> float:
    g = x.groupby(dates).mean().dropna()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def main():
    P, _b, _p = pc.build(PANEL)
    C, H, Lo = P.close, P.high, P.low
    elig = P.elig.fillna(False).astype(bool)
    ind = pd.read_csv(REPO / "data/ticker_industry_map.csv").set_index("ticker").industry
    cols = [c for c in C.columns if c in ind.index and isinstance(ind[c], str)]
    C, elig = C[cols], elig[cols]
    ind = ind[cols]
    sma = C.rolling(50, min_periods=50).mean()
    above = (C >= sma) & sma.notna()
    run = run_length(above)
    adr = ((H[cols] / Lo[cols] - 1).rolling(20).mean() * 100)
    dist = (C / sma - 1) * 100 / adr                         # distance above SMA50 in ADR units
    r126 = C / C.shift(126) - 1
    # within-industry RS rank (eligible names), lagged 20 sessions
    rank = pd.DataFrame(np.nan, index=C.index, columns=cols)
    groups = ind.groupby(ind).groups
    for g, names in groups.items():
        names = list(names)
        if len(names) < 4:
            continue
        rank[names] = r126[names].where(elig[names]).rank(axis=1, pct=True)
    top_lag = rank.shift(20) >= 0.8
    brk = (~above) & (run.shift(1) >= 40) & elig & top_lag
    n_ind = {g: elig[list(n)].sum(axis=1) for g, n in groups.items()}

    dates = C.index
    di = {d: i for i, d in enumerate(dates)}
    fr = {h: C.shift(-h) / C - 1 for h in HS}
    d0 = C.pct_change(fill_method=None)
    below_by = {h: (~above).iloc[::-1].rolling(h, min_periods=1).max().iloc[::-1].shift(-1).fillna(0).astype(bool)
                for h in HS}                                  # closes below SMA50 on any of t+1..t+h
    adr_dec = adr.rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int)
    dist_dec = dist.where(above).rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int)

    # events, first per industry per 20 sessions
    ev = []
    last = {}
    ii, jj = np.where(brk.values)
    order = np.argsort(ii, kind="stable")
    for i, j in zip(ii[order], jj[order]):
        d = dates[i]
        if d < pd.Timestamp(START) or i + max(HS) >= len(dates):
            continue
        g = ind.iloc[j]
        if n_ind[g].iloc[i] < 4:
            continue
        if g in last and i - last[g] <= 20:
            continue
        last[g] = i
        ev.append((i, j, g))
    ev_ind_days = pd.DataFrame(False, index=dates, columns=sorted(groups))
    for i, j, g in ev:
        ev_ind_days.iloc[i:i + 21, ev_ind_days.columns.get_loc(g)] = True   # industry "had an event in [t-20, t]"

    rows = []
    for i, j, g in ev:
        d = dates[i]
        peers = [c for c in groups[g] if c != cols[j] and elig[c].iloc[i] and above[c].iloc[i]]
        if not peers:
            continue
        bad_ind = set(ev_ind_days.columns[ev_ind_days.iloc[i].values])
        ctrl = [c for c in cols if ind[c] not in bad_ind and elig[c].iloc[i] and above[c].iloc[i]]
        if len(ctrl) < 20:
            continue
        pd_ = adr_dec.iloc[i][peers]
        cd_ = adr_dec.iloc[i][ctrl]
        w = pd_.value_counts(normalize=True)
        rec = dict(date=d, laggard=cols[j], industry=g, n_peers=len(peers), n_ctrl=len(ctrl))

        def matched(vals: pd.Series, keyp: pd.Series, keyc: pd.Series):
            gm = vals[ctrl].groupby(keyc).mean()
            wk = keyp.value_counts(normalize=True)
            com = wk.index.intersection(gm.dropna().index)
            return float((wk[com] / wk[com].sum() * gm[com]).sum()) if len(com) else np.nan
        for h in HS:
            v = fr[h].iloc[i]
            rec[f"peer{h}"] = 100 * v[peers].mean()
            rec[f"ctrl{h}"] = 100 * matched(v, pd_, cd_)
            # break rate, matched on ADR decile x distance decile
            bv = below_by[h].iloc[i].astype(float)
            kp = pd_.astype(str) + "_" + dist_dec.iloc[i][peers].astype(str)
            kc = cd_.astype(str) + "_" + dist_dec.iloc[i][ctrl].astype(str)
            rec[f"pbrk{h}"] = 100 * bv[peers].mean()
            rec[f"cbrk{h}"] = 100 * matched(bv, kp, kc)
        v = d0.iloc[i]
        rec["peer_d0"] = 100 * v[peers].mean()
        rec["ctrl_d0"] = 100 * matched(v, pd_, cd_)
        rows.append(rec)
    E = pd.DataFrame(rows)
    E["date"] = pd.to_datetime(E.date)
    yr = E.date.dt.year
    h1 = E.date < SPLIT
    L = ["# Laggard-breakdown contagion (pre-registration in the docstring)",
         f"events {len(E):,} on {E.date.nunique()} dates, {E.industry.nunique()} industries; median peers {E.n_peers.median():.0f}, "
         f"control names {E.n_ctrl.median():.0f}"]
    L.append(f"day 0 (common-shock check): peers {E.peer_d0.mean():+.2f}% vs ADR-matched control {E.ctrl_d0.mean():+.2f}% "
             f"(diff t {tclu(E.peer_d0 - E.ctrl_d0, E.date):+.2f})")
    res = {}
    for h in HS:
        dd = E[f"peer{h}"] - E[f"ctrl{h}"]
        bb = E[f"pbrk{h}"] - E[f"cbrk{h}"]
        ys = dd.groupby(yr).mean()
        res[h] = (dd.mean(), tclu(dd, E.date), dd[h1].mean(), dd[~h1].mean())
        L.append(f"{'PRIMARY ' if h == 15 else '        '}{h:>2}d  peer - control {dd.mean():+.3f}pp  t {res[h][1]:+.2f}  "
                 f"halves {res[h][2]:+.3f} / {res[h][3]:+.3f}  years + {int((ys > 0).sum())}/{len(ys)}  | "
                 f"break-below-50 rate peers {E[f'pbrk{h}'].mean():.1f}% vs matched {E[f'cbrk{h}'].mean():.1f}% "
                 f"(diff {bb.mean():+.1f}pp t {tclu(bb, E.date):+.2f})")
    Y = pd.DataFrame({"n": E.groupby(yr).size(), "15d_pp": (E.peer15 - E.ctrl15).groupby(yr).mean(),
                      "brk15_pp": (E.pbrk15 - E.cbrk15).groupby(yr).mean()})
    L.append("\nper year:\n" + Y.round(2).T.to_string())
    E.to_csv(REPO / "data/studies/logs/laggard_contagion_events.csv", index=False)
    print("\n".join(L))
    m, t, a, b = res[15]
    print(f"\nPRIMARY 15d peer - control: {m:+.3f}pp t {t:+.2f} halves {a:+.3f}/{b:+.3f}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

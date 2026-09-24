#!/usr/bin/env python3
"""
[WL-5h] Same-morning theme co-breakouts (Corsellis "group confirmation"), DAILY version A (pre-registered 2026-09-23;
spec from data/qullamaggie/videos/relayed/2026-07-24_zZls8f2At9k/notes.md "Not tested, could be" A, written before
running).

Claim: take a breakout only when most of the stock's theme breaks out with it; a lone breakout is "more failure prone".
Pool: house breakouts = close > prior 20d high, RVOL (volume / trailing-50 mean) >= 1.8, close > SMA50 and > SMA200,
  liquid-eligible; liquid panel 2019-10 -> 2026-09.
Group: data/ticker_industry_map.csv industry (frozen), groups with >= 5 members in the panel.
  peer_brk = share of the OTHER eligible members of the group that also close above their own prior 20d high that
  day (same-day closes only -> knowable at the entry close).
Arms: CONFIRMED peer_brk >= 0.30 · LONE peer_brk == 0 · middle reported only.
Trade: enter at the close, stop = breakout day's low judged on the close, 20-EMA close trail, max 60 sessions, 0.10% a
  side (pct_trade from run_vcp_damped_sine). R = % / stop%, stop floor 2%, cap 20.
PRIMARY: CONFIRMED - LONE, SAME-DATE paired (dates with both arms), 20-EMA trail, % return (R alongside), t clustered by
  date; win rate of each arm reported. Bar |t| >= 3, both halves (split 2023-01-01) the same sign, per-year shown.
Secondary (Sidak over 2 arms x 3 horizons ~ 2.64; house 3 governs): fixed-horizon close-to-close returns at 10/21/63
  sessions, same pairing. Theme-day control: CONFIRMED breakouts vs same-group NON-breakout names entered at the same
  close with the same stop % (does the breakout add anything once the theme is known to be running?).
Prior: CONFIRMED higher short-horizon win rate, LOWER 63d return (the rotation study favours lone / weak-group names by
  +5.6pp). A positive CONFIRMED - LONE at 63d would contradict it and needs the outcome-conditioning check first.

Run: PYTHONPATH=src .venv/bin/python3 run_theme_cobreakout.py   (log -> data/studies/logs/theme_cobreakout.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import SLIP, load_panel
import run_vcp_damped_sine as V

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/theme_cobreakout.log"
START, SPLIT = "2019-10-01", "2023-01-01"
RNG = np.random.default_rng(20260923)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def pct_with_stop(P, j, i, stop_pct):
    C = P.close.values
    stop = C[i, j] * (1 - stop_pct)
    r = V.pct_trade(P, j, i, stop, np.nan)
    return r[0] if r else np.nan


def main():
    path = "data/cache/liquid_panel_2019.parquet"
    P = load_panel(path)
    raw = pd.read_parquet(REPO / path)
    Vol = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(index=P.close.index,
                                                                                           columns=P.close.columns)
    C, H = P.close, P.high
    lvl = H.shift(1).rolling(20).max()
    at20 = (C > lvl)
    rvol = Vol / Vol.shift(1).rolling(50).mean()
    elig = P.elig.fillna(False)
    brk = (at20 & (rvol >= 1.8) & (C > C.rolling(50).mean()) & (C > C.rolling(200).mean()) & elig).fillna(False)
    brk[brk.index < START] = False
    imap = pd.read_csv(REPO / "data/ticker_industry_map.csv").set_index("ticker").industry
    ind = pd.Series({c: imap.get(c) for c in C.columns})
    sizes = ind.value_counts()
    ok_groups = set(sizes[sizes >= 5].index)
    # peer share per (date, name): other eligible members at a 20d-high close
    at20e = (at20 & elig).astype(float)
    el = elig.astype(float)
    peer = pd.DataFrame(np.nan, index=C.index, columns=C.columns)
    for g in ok_groups:
        cols = ind[ind == g].index
        n_at = at20e[cols].sum(axis=1)
        n_el = el[cols].sum(axis=1)
        for c in cols:
            others = (n_el - el[c]).replace(0, np.nan)
            peer[c] = (n_at - at20e[c]) / others
    adrpx = (P.adr / 100 * C).values
    Cv, Lv = C.values, P.low.values
    rows = []
    for i, j in zip(*np.where(brk.values)):
        pb = peer.values[i, j]
        if not np.isfinite(pb):
            continue
        r = V.pct_trade(P, j, i, Lv[i, j], lvl.values[i, j])
        if r is None:
            continue
        stop_pct = max((Cv[i, j] - Lv[i, j]) / Cv[i, j], 0.02)
        fwd = {h: 100 * (Cv[min(i + h, len(Cv) - 1), j] * (1 - SLIP) / (Cv[i, j] * (1 + SLIP)) - 1)
               for h in (10, 21, 63)}
        rows.append(dict(i=i, j=j, date=C.index[i], sym=C.columns[j], group=ind.iloc[j], peer=pb, ret=r[0],
                         R=float(np.clip(r[0] / (100 * stop_pct), -20, 20)), stop_pct=stop_pct,
                         **{f"f{h}": v for h, v in fwd.items()}))
    T = pd.DataFrame(rows)
    T["arm"] = np.where(T.peer >= 0.30, "CONFIRMED", np.where(T.peer == 0, "LONE", "middle"))
    print(f"# Theme co-breakout [WL-5h] -- {len(T):,} house breakouts in {T.group.nunique()} industries, "
          f"{T.date.min().date()} -> {T.date.max().date()}")
    print(T.groupby("arm").agg(n=("ret", "size"), mean_pct=("ret", "mean"), win=("ret", lambda x: 100 * (x > 0).mean()),
                               R=("R", "mean"), f10=("f10", "mean"), f21=("f21", "mean"), f63=("f63", "mean"),
                               win10=("f10", lambda x: 100 * (x > 0).mean())).round(2).to_string())

    def paired(col):
        g = T[T.arm.isin(["CONFIRMED", "LONE"])].groupby(["date", "arm"])[col].mean().unstack()
        d = (g["CONFIRMED"] - g["LONE"]).dropna()
        return d, g.loc[d.index]
    print("\n## PRIMARY: CONFIRMED - LONE, same-date paired")
    for col, lab in (("ret", "20-EMA trail %"), ("R", "R (floor 2%, cap 20)"), ("f10", "fixed 10d %"),
                     ("f21", "fixed 21d %"), ("f63", "fixed 63d %")):
        d, g = paired(col)
        h = d.index < SPLIT
        print(f"{lab:22s} dates {len(d):4d} | CONFIRMED {g['CONFIRMED'].mean():+.2f} vs LONE {g['LONE'].mean():+.2f} | "
              f"diff {d.mean():+.3f} t {tstat(d):+.2f} | halves {d[h].mean():+.3f} / {d[~h].mean():+.3f}")
    d, _ = paired("ret")
    print("per year (CONFIRMED - LONE, 20-EMA %):\n" + d.groupby(d.index.year).agg(["size", "mean"]).round(2).T.to_string())
    dw, gw = paired("ret")
    Tw = T.assign(win=(T.ret > 0).astype(float))
    gwin = Tw[Tw.arm.isin(["CONFIRMED", "LONE"])].groupby(["date", "arm"]).win.mean().unstack().dropna()
    print(f"win rate (same dates): CONFIRMED {100 * gwin.CONFIRMED.mean():.1f}% vs LONE {100 * gwin.LONE.mean():.1f}% | "
          f"diff t {tstat(gwin.CONFIRMED - gwin.LONE):+.2f}")

    print("\n## theme-day control: CONFIRMED breakouts vs same-group NON-breakout names, same close, same stop %")
    ctl = []
    brkv, elv = brk.values, elig.values
    for r in T[T.arm == "CONFIRMED"].itertuples():
        members = np.flatnonzero((ind == r.group).values)
        cand = [m for m in members if m != r.j and elv[r.i, m] and not brkv[r.i, m] and np.isfinite(Cv[r.i, m])]
        if not cand:
            continue
        picks = RNG.choice(cand, size=min(3, len(cand)), replace=False)
        c = np.nanmean([pct_with_stop(P, int(m), r.i, r.stop_pct) for m in picks])
        ctl.append(dict(date=r.date, sig=r.ret, ctl=c))
    K = pd.DataFrame(ctl).dropna()
    dd = (K.sig - K.ctl).groupby(K.date).mean()
    h = dd.index < SPLIT
    print(f"n {len(K)} | CONFIRMED {K.sig.mean():+.2f}% vs same-group non-breakout {K.ctl.mean():+.2f}% | diff "
          f"{dd.mean():+.3f} t {tstat(dd):+.2f} | halves {dd[h].mean():+.3f} / {dd[~h].mean():+.3f}")
    T.to_csv(REPO / "data/studies/logs/theme_cobreakout_trades.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

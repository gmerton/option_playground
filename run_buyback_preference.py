#!/usr/bin/env python3
"""
Buyback preference (pre-registered 2026-09-24, before the first run). The LEAD came from run_net_issuance.py (same day):
net-buyback names (bottom issuance decile, median -7.6% shares/yr) +0.71pp 60d ADR-matched excess, t 2.94, 2013-2026.
Re-running that exact cell on the same data would be circular, so this test changes what could have produced it:

  1. STRICTER CONTROL: buyback firms skew large and cash-rich, and 2013-2026 favoured mega-caps. PRIMARY control =
     same-date eligible names in the same ADR band x DOLLAR-VOLUME tercile (size proxy). Secondary: same-industry peers.
  2. OUT OF TIME: 2010-2012, which the lead never saw (split adjustment from yfinance split history, all dates).
  3. PLATEAU: thresholds bottom decile / bottom quintile / ISS <= -3% / ISS <= -5% x horizons 20 / 60 / 120 -- all
     reported; a real effect is a plateau, a data-mined one a spike.

ISS as in run_net_issuance.py (split-adjusted 1-yr change in the cover-page share count, point-in-time on filed dates).
PRIMARY: bottom-decile ISS, 60-session excess vs the ADR x size-matched field, one obs per month-end 2013-2026, t across
months. Bar: t >= 3, both halves (2013-2019 / 2020-2026) > 0, AND the 2010-2012 holdout > 0.
SECONDARY: precision-tier trades in buyback names (ISS <= -2%) vs the rest (the tier bucket from the lead) -- descriptive.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_buyback_preference.py   (log -> data/studies/logs/buyback_preference.log)
"""
from __future__ import annotations

import sys
import time
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_net_issuance import build_shares, issuance_on

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/buyback_preference.log"
SPLITS_YF = REPO / "data/cache/splits_yfinance.parquet"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def yf_splits(tickers) -> pd.DataFrame:
    if SPLITS_YF.exists():
        return pd.read_parquet(SPLITS_YF)
    import yfinance as yf
    rows = []
    for k, t in enumerate(tickers):
        try:
            s = yf.Ticker(t).splits
            for d, r in s.items():
                rows.append(dict(ticker=t, execution_date=pd.Timestamp(d).tz_localize(None), split_from=1.0, split_to=float(r)))
        except Exception:  # noqa: BLE001
            pass
        if k % 300 == 0:
            print(f"  yfinance splits {k}/{len(tickers)}", flush=True, file=sys.__stdout__)
        time.sleep(0.05)
    S = pd.DataFrame(rows)
    S.to_parquet(SPLITS_YF, index=False)
    return S


def main() -> None:
    out = ["# Buyback preference (pre-registration in the docstring)\n"]
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "dolvol"])
    DV = raw.pivot(index="date", columns="ticker", values="dolvol").sort_index().reindex(index=C.index, columns=C.columns)
    addv = DV.rolling(50, min_periods=30).mean()
    im = pd.read_csv(REPO / "data/ticker_industry_map.csv").set_index("ticker").industry
    idx = C.index
    F = {h: (C.shift(-h) / C - 1) * 100 for h in (20, 60, 120)}
    splits = yf_splits(list(C.columns))
    splits["execution_date"] = pd.to_datetime(splits.execution_date).values.astype("datetime64[ns]")
    S = build_shares()
    ends = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    ends = ends[(ends >= "2010-06-01") & (ends <= idx[-121])]
    ISS = issuance_on(S, splits, set(C.columns), list(ends.values))

    def excess(d, names, h, mode):
        e, f = E.loc[d], F[h].loc[d]
        ok = e & f.notna()
        if mode == "industry":
            vals = []
            for t in names:
                g = im.get(t)
                if g is None or not ok.get(t, False):
                    continue
                peers = [p for p in im[im == g].index if p in ok.index and p != t and ok[p] and p not in names]
                if len(peers) >= 4:
                    vals.append(f[t] - f[peers].mean())
            return np.mean(vals) if vals else np.nan
        a = A.loc[d]
        sz = pd.qcut(addv.loc[d][ok], 3, labels=False, duplicates="drop").reindex(ok.index)
        vals = []
        for lo, hi in BANDS:
            for s in (0, 1, 2):
                cell = ok & (a >= lo) & (a < hi) & ((sz == s) if mode == "adr_size" else True)
                mem = cell & cell.index.isin(names); fld = cell & ~cell.index.isin(names)
                if mem.sum() and fld.sum() >= 8:
                    vals.append((f[mem] - f[fld].mean()).values)
                if mode != "adr_size":
                    break
        return np.concatenate(vals).mean() if vals else np.nan

    rows = []
    for d in ISS.index:
        iss = ISS.loc[d].reindex(C.columns)[E.loc[d]].dropna()
        if len(iss) < 150:
            continue
        sets = {"decile": iss[iss <= iss.quantile(0.1)].index, "quintile": iss[iss <= iss.quantile(0.2)].index,
                "le_-3%": iss[iss <= -0.03].index, "le_-5%": iss[iss <= -0.05].index}
        rec = dict(month=d)
        for k, names in sets.items():
            for h in (20, 60, 120):
                rec[f"{k}_{h}"] = excess(d, set(names), h, "adr_size")
        rec["decile_60_adr"] = excess(d, set(sets["decile"]), 60, "adr")
        rec["decile_60_ind"] = excess(d, set(sets["decile"]), 60, "industry")
        rows.append(rec)
    M = pd.DataFrame(rows).set_index("month")
    ins, hold = M[M.index >= "2013-01-01"], M[M.index < "2013-01-01"]
    x = ins["decile_60"]; h1, h2 = x[x.index < "2020-01-01"], x[x.index >= "2020-01-01"]
    hx = hold["decile_60"]
    out.append(f"months scored: {len(ins)} (2013-2026) + {len(hold)} holdout (2010-2012)")
    out.append(f"\n## PRIMARY bottom-decile 60d vs ADR x SIZE-matched field: {x.mean():+.2f}pp, t {tstat(x):+.2f}; halves "
               f"{h1.mean():+.2f} / {h2.mean():+.2f}; HOLDOUT 2010-12 {hx.mean():+.2f}pp (t {tstat(hx):+.2f}, n {hx.notna().sum()})")
    ok = tstat(x) >= 3 and h1.mean() > 0 and h2.mean() > 0 and hx.mean() > 0
    out.append(f"  bar (t >= 3, halves > 0, holdout > 0): {'PASS' if ok else 'FAIL'}")
    out.append(f"  same cell, ADR-only control (the lead's) {ins.decile_60_adr.mean():+.2f} (t {tstat(ins.decile_60_adr):+.2f}); "
               f"vs same-INDUSTRY peers {ins.decile_60_ind.mean():+.2f} (t {tstat(ins.decile_60_ind):+.2f})")
    out.append("\n## plateau (2013-2026, ADR x size-matched; pp and t):")
    for k in ("decile", "quintile", "le_-3%", "le_-5%"):
        out.append(f"  {k:9s} " + "  ".join(f"{h}d {ins[f'{k}_{h}'].mean():+.2f} (t {tstat(ins[f'{k}_{h}']):+.2f})" for h in (20, 60, 120)))
    M.to_csv(REPO / "data/studies/buyback_preference_2026-09-24.csv")

    K = pd.read_csv(REPO / "data/studies/net_issuance_trades_2026-09-24.csv", parse_dates=["date"])
    bb, rest = K[K.iss <= -0.02], K[K.iss > -0.02]
    g = lambda z: z.groupby("date").pct.mean()
    a, b = g(bb), g(rest); dd = a.mean() - b.mean(); td = dd / sqrt(a.var() / len(a) + b.var() / len(b))
    out.append(f"\nSECONDARY (descriptive, the lead's own sample): tier trades in buyback names {bb.pct.mean():+.2f}%/trade "
               f"(n {len(bb)}) vs rest {rest.pct.mean():+.2f}% -> {dd:+.2f}pp (t {td:+.2f})")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

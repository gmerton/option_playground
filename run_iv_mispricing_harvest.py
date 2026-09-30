#!/usr/bin/env python3
"""Harvest test: short RICH / long CHEAP ATM straddles in the least-liquid option decile (2026-09-29).

PRE-REGISTERED: data/studies/iv_mispricing_harvest_2026-09-29.md (committed 74c772e before the pull). Population = the
horizon/earnings-clean subset of run_iv_efficiency_horizon_check.py, D1 (and D10 as reference); RICH/CHEAP = top/bottom
third of gap within the month's decile. ATM straddle in the 21-40 DTE expiry nearest 30, held to expiry, settled on the
RAW chain spot. PRIMARY = monthly long-short return at house fills (mid -/+ 25% of spread + $0.0065/leg), t >= 3.

Usage: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_iv_mispricing_harvest.py \
         > data/studies/iv_mispricing_harvest_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import awswrangler as wr
import numpy as np
import pandas as pd

import run_iv_efficiency_by_liquidity as m
import run_quiet_knife_leaps as qk
from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import DB, GLUE_CATALOG

SPLIT, SLIP, COMM = pd.Timestamp("2019-01-01"), 0.25, 0.0065
CACHE = m.CACHE / "harvest_quotes.parquet"


def clean_subset() -> pd.DataFrame:
    """Rebuild the addendum's clean subset exactly as run_iv_efficiency_horizon_check.py does."""
    D = pd.read_parquet(m.CACHE / "panel.parquet")
    x = pd.read_parquet(m.CACHE / "dte_month_end.parquet"); x["trade_date"] = pd.to_datetime(x.trade_date)
    D = D.merge(x.rename(columns={"trade_date": "date"}), on=["ticker", "date"], how="left")
    e1 = pd.read_parquet(m.REPO / "data/cache/earnings_yf.parquet")[["ticker", "session"]].rename(columns={"session": "ed"})
    from lib.mysql_lib import _get_engine
    e2 = pd.read_sql("SELECT ticker, raw_date AS ed FROM earnings_report", _get_engine())
    E = pd.concat([e1, e2]); E["ed"] = pd.to_datetime(E.ed, errors="coerce"); E = E.dropna().drop_duplicates()
    Eg = {t: np.sort(g.ed.values) for t, g in E.groupby("ticker")}

    def cls(t, d, dte):
        a = Eg.get(t)
        if a is None: return "no_cover"
        d64 = np.datetime64(d)
        if not ((a >= d64 - np.timedelta64(400, "D")) & (a <= d64 + np.timedelta64(400, "D"))).any(): return "no_cover"
        hi = d64 + np.timedelta64(int(max(dte if np.isfinite(dte) else 31, 31)), "D")
        return "earn" if ((a > d64) & (a <= hi)).any() else "clean"
    D["ecls"] = [cls(t, d, k) for t, d, k in zip(D.ticker, D.date, D.skew_dte)]
    S = D[D.skew_dte.between(21, 40) & (D.ecls == "clean")].copy()
    S = S[S.groupby("date").ticker.transform("size") >= 50]
    S["dec"] = S.groupby("date").vol21.transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    S["gap"] = np.log(S.iv) - S.F
    S = S[S.dec.isin([0, 9])].copy()
    S["third"] = S.groupby(["date", "dec"]).gap.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    return S


def quotes(req: pd.DataFrame) -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    _ensure_glue_db(DB)
    name, path = qk._tmp(req, ["row_id", "ticker", "entry_date"])
    try:
        q = athena(f"""
        SELECT t.row_id, o.expiry, o.strike, o.cp, o.bid, o.ask, o.delta
        FROM {qk.T} o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t ON o.ticker = t.ticker AND o.trade_date = t.entry_date
        WHERE date_diff('day', o.trade_date, o.expiry) BETWEEN 21 AND 40 AND o.ask > 0 AND o.bid >= 0
          AND o.delta IS NOT NULL AND ABS(o.delta) BETWEEN 0.25 AND 0.75""")
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=name); wr.s3.delete_objects(path)
    q["expiry"] = pd.to_datetime(q.expiry)
    q.to_parquet(CACHE, index=False)
    return q


def mt(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * sqrt(len(x)) if len(x) > 2 else np.nan


def main():
    S = clean_subset().reset_index(drop=True)
    S["row_id"] = [f"r{i}" for i in range(len(S))]
    req = S[["row_id", "ticker", "date"]].rename(columns={"date": "entry_date"})
    Q = quotes(req)
    raw = pd.read_parquet(m.REPO / "data/cache/chain_spot/chain_spot_daily.parquet")
    raw["trade_date"] = pd.to_datetime(raw.trade_date)
    spot = {t: g.set_index("trade_date").spot.sort_index() for t, g in raw.groupby("ticker")}
    rows = []
    for rid, g in Q.groupby("row_id"):
        r = S.loc[int(rid[1:])]
        dte = (g.expiry - r.date).dt.days
        exp = g.expiry.iloc[(dte - 30).abs().argsort().iloc[0]]
        g = g[g.expiry == exp]
        c, p = g[g.cp == "C"].set_index("strike"), g[g.cp == "P"].set_index("strike")
        ks = c.index.intersection(p.index)
        if not len(ks): continue
        K = (c.loc[ks].delta - 0.5).abs().idxmin()
        cq, pq = c.loc[K], p.loc[K]
        if isinstance(cq, pd.DataFrame): cq = cq.iloc[0]
        if isinstance(pq, pd.DataFrame): pq = pq.iloc[0]
        mid = (cq.bid + cq.ask) / 2 + (pq.bid + pq.ask) / 2
        spr = (cq.ask - cq.bid) + (pq.ask - pq.bid)
        s = spot.get(r.ticker)
        if s is None or mid <= 0.05: continue
        s = s.loc[:exp]
        if not len(s) or (exp - s.index[-1]).days > 4: continue
        pay = abs(s.iloc[-1] - K)
        side = -1 if r.third == 2 else (1 if r.third == 0 else 0)          # short RICH, long CHEAP, middle = 0
        # returns per unit of mid premium, for a SHORT (sell) and a LONG (buy) at each fill
        short = {f: ((mid - k * spr) - 2 * COMM - pay) / mid for f, k in (("mid", 0.0), ("house", SLIP), ("cross", 0.5))}
        long_ = {f: (pay - (mid + k * spr) - 2 * COMM) / mid for f, k in (("mid", 0.0), ("house", SLIP), ("cross", 0.5))}
        rows.append(dict(row_id=rid, ticker=r.ticker, date=r.date, dec=int(r.dec) + 1, third=int(r.third), gap=r.gap,
                         spr_pct=spr / mid, **{f"short_{k}": v for k, v in short.items()}, **{f"long_{k}": v for k, v in long_.items()}))
    X = pd.DataFrame(rows)
    X.to_csv(m.REPO / "data/studies/logs/iv_mispricing_harvest_trades.csv", index=False)
    out = [f"# IV-mispricing harvest (pre-registration in the md). priced straddles {len(X):,} of {len(S):,} ticker-months"]
    for dec in (1, 10):
        Z = X[X.dec == dec]
        out.append(f"\n=== D{dec}: n {len(Z)}, months {Z.date.nunique()}, median straddle spread {100 * Z.spr_pct.median():.1f}% of mid ===")
        for f in ("mid", "house", "cross"):
            rich = Z[Z.third == 2].groupby("date")[f"short_{f}"].mean()
            cheap = Z[Z.third == 0].groupby("date")[f"long_{f}"].mean()
            allD = Z.groupby("date")[f"short_{f}"].mean()
            ls = (rich + cheap).dropna()
            h = ls.index < SPLIT; yr = ls.groupby(ls.index.year).mean()
            out.append(f"  [{f:5s}] L/S {100 * ls.mean():+6.2f}%/mo t {mt(ls):+5.2f} halves {100 * ls[h].mean():+.2f}/{100 * ls[~h].mean():+.2f} "
                       f"yrs+ {(yr > 0).sum()}/{len(yr)} | short-RICH {100 * rich.mean():+.2f} (t {mt(rich):+.2f}) | long-CHEAP "
                       f"{100 * cheap.mean():+.2f} (t {mt(cheap):+.2f}) | short-RICH - short-ALL {100 * (rich - allD).mean():+.2f} "
                       f"(t {mt((rich - allD).dropna()):+.2f})")
            if dec == 1 and f == "house":
                ok = mt(ls) >= 3 and ls[h].mean() > 0 and ls[~h].mean() > 0 and (yr > 0).sum() > len(yr) / 2
                prim = f"PRIMARY (D1, house fills): {'PASS' if ok else 'FAIL'}"
    out.append("\n" + prim)
    print("\n".join(out))


if __name__ == "__main__":
    main()

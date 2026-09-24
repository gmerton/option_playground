#!/usr/bin/env python3
"""
Net share issuance (Fama & French 2008 "Dissecting Anomalies": pervasive in micro, small AND big stocks) -- as a
VETO on the precision-tier breakout book (pre-registered 2026-09-24, before the first run). First issuance test in the
ledger. Data: SEC XBRL company facts (run_sec_companyfacts_pull.py), point-in-time on the FILED date.

ISSUANCE on date d, per name: S_now = the latest cover-page share count (dei:EntityCommonStockSharesOutstanding;
  fallback us-gaap:CommonStockSharesOutstanding) FILED on or before d, as of its period end e1; S_prior = the latest such
  count filed on or before d whose end is 300-430 days before e1 (closest to 365). Split-adjusted with Polygon splits
  between the two ends (data/cache/pit/splits.parquet, 2012 ->):  ISS = S_now / (S_prior x split ratio) - 1.
  Signals from 2013 (the split file starts 2012). |ISS| > 150% dropped as a data error / merger outlier.

A (anomaly check, reported first): each month-end, eligible names by ISS: TOP decile (heavy issuers) and BOTTOM decile
  (net buybacks) -> 60-session ADR-matched excess, one observation per month (t across months).
PRIMARY (the veto): precision-tier house trades (close entry, day-low stop floored 2%, 20-EMA exit, % of price), ISS known
  at entry. ISSUERS = ISS >= +5% vs the rest. Difference in mean % per trade (Welch on entry-date means). Bar: issuers
  WORSE with |t| >= 3 and both halves (2020-01 split: the tier runs 2019-10 ->) the same sign; report the book mean
  with and without the veto and how many trades it removes (precision over recall: removing losers is the goal).
caveat survivor panel; shares from XBRL tags can be missing for some names (coverage reported).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_net_issuance.py   (log -> data/studies/logs/net_issuance.log)
"""
from __future__ import annotations

import contextlib
import io
import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/net_issuance.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def welch(a: pd.Series, b: pd.Series):
    a, b = a.dropna(), b.dropna()
    d = a.mean() - b.mean()
    return d, d / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def build_shares() -> pd.DataFrame:
    F = pd.read_parquet(REPO / "data/cache/sec_companyfacts.parquet")
    F = F[F.tag.isin(["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"]) & (F.unit == "shares")]
    F = F.dropna(subset=["val", "end", "filed"])
    F["pri"] = (F.tag == "EntityCommonStockSharesOutstanding").astype(int)
    # one value per (ticker, end, filed): prefer the cover-page tag
    F = F.sort_values(["ticker", "end", "filed", "pri"]).drop_duplicates(["ticker", "end", "filed"], keep="last")
    return F[["ticker", "end", "filed", "val"]]


def issuance_on(S: pd.DataFrame, splits: pd.DataFrame, tickers, dates) -> pd.DataFrame:
    """ISS for each (ticker, date) pair in the product of dates x tickers present in S."""
    out = {}
    sp = {t: g for t, g in splits.groupby("ticker")}
    for t, g in S.groupby("ticker"):
        if t not in tickers:
            continue
        g = g.sort_values("filed")
        fil, end, val = g.filed.values, g.end.values, g.val.values.astype(float)
        spt = sp.get(t)
        res = []
        for d in dates:
            known = fil <= np.datetime64(d)
            if not known.any():
                res.append(np.nan); continue
            e_k, v_k = end[known], val[known]
            k1 = np.argmax(e_k)                                   # most recent period end known at d
            e1, v1 = e_k[k1], v_k[k1]
            lag = (e1 - e_k).astype("timedelta64[D]").astype(int)
            ok = (lag >= 300) & (lag <= 430)
            if not ok.any() or v1 <= 0:
                res.append(np.nan); continue
            k0 = np.flatnonzero(ok)[np.argmin(np.abs(lag[ok] - 365))]
            e0, v0 = e_k[k0], v_k[k0]
            ratio = 1.0
            if spt is not None:
                w = spt[(spt.execution_date > e0) & (spt.execution_date <= e1)]
                ratio = float(np.prod(w.split_to / w.split_from)) if len(w) else 1.0
            iss = v1 / (v0 * ratio) - 1 if v0 > 0 else np.nan
            res.append(iss if np.isfinite(iss) and abs(iss) <= 1.5 else np.nan)
        out[t] = res
    return pd.DataFrame(out, index=pd.DatetimeIndex(dates))


def main() -> None:
    S = build_shares()
    splits = pd.read_parquet(REPO / "data/cache/pit/splits.parquet")
    splits["execution_date"] = pd.to_datetime(splits.execution_date).values.astype("datetime64[ns]")
    out = ["# Net share issuance as a veto (pre-registration in the docstring)\n"]

    # ── A: anomaly check on the liquid universe ──────────────────────────────
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, A, E = P.close.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    F60 = (C.shift(-60) / C - 1) * 100
    ends = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    ends = ends[(ends >= "2013-01-01") & (ends <= idx[-61])]
    ISS = issuance_on(S, splits, set(C.columns), list(ends.values))
    cov = []
    rows = []
    for d in ISS.index:
        e = E.loc[d]; iss = ISS.loc[d].reindex(C.columns)[e].dropna()
        cov.append(len(iss) / max(int(e.sum()), 1))
        if len(iss) < 200:
            continue
        f, a = F60.loc[d], A.loc[d]
        def ex(names):
            vals = []
            for lo, hi in BANDS:
                band = e & (a >= lo) & (a < hi) & f.notna()
                mem = band & band.index.isin(names); fld = band & ~band.index.isin(names)
                if mem.sum() and fld.sum() >= 10:
                    vals.append((f[mem] - f[fld].mean()).values)
            return np.concatenate(vals).mean() if vals else np.nan
        top = iss[iss >= iss.quantile(0.9)].index; bot = iss[iss <= iss.quantile(0.1)].index
        rows.append(dict(month=d, top=ex(top), bot=ex(bot), top_iss=iss[top].median(), bot_iss=iss[bot].median()))
    M = pd.DataFrame(rows).set_index("month")
    out.append(f"coverage: ISS known for {100 * np.mean(cov):.0f}% of eligible names at month-ends ({len(M)} months scored)")
    out.append(f"A  heavy issuers (top decile, median ISS {M.top_iss.median():+.1%}): 60d ADR-matched excess {M.top.mean():+.2f}pp "
               f"(t {tstat(M.top):+.2f}) | buybacks (bottom decile, {M.bot_iss.median():+.1%}): {M.bot.mean():+.2f}pp (t {tstat(M.bot):+.2f}) | "
               f"bottom - top {(M.bot - M.top).mean():+.2f}pp (t {tstat(M.bot - M.top):+.2f})")

    # ── PRIMARY: veto on the precision-tier book ─────────────────────────────
    from run_precision_tier_control import build
    from run_adr_floor_test import house
    with contextlib.redirect_stdout(io.StringIO()):
        P2, brk, prec = build()
        T = house(P2, prec)
    T["sym"] = [P2.close.columns[j] for j in T.j]
    T["date"] = pd.to_datetime(T.date)
    iss_t = []
    for (sym, d) in zip(T.sym, T.date):
        r = issuance_on(S[S.ticker == sym], splits, {sym}, [d])
        iss_t.append(r.iloc[0, 0] if r.shape[1] else np.nan)
    T["iss"] = iss_t
    K = T.dropna(subset=["iss"])
    iss_m, rest = K[K.iss >= 0.05], K[K.iss < 0.05]
    d, t = welch(iss_m.groupby("date").pct.mean(), rest.groupby("date").pct.mean())
    h = pd.Timestamp("2023-01-01")
    d1, _ = welch(iss_m[iss_m.date < h].groupby("date").pct.mean(), rest[rest.date < h].groupby("date").pct.mean())
    d2, _ = welch(iss_m[iss_m.date >= h].groupby("date").pct.mean(), rest[rest.date >= h].groupby("date").pct.mean())
    out.append(f"\n## PRIMARY veto: precision-tier trades with ISS known {len(K):,} of {len(T):,}")
    out.append(f"  ISSUERS (ISS >= +5%) n {len(iss_m):,}: {iss_m.pct.mean():+.2f}%/trade (R {iss_m.R.mean():+.3f}) | rest n {len(rest):,}: "
               f"{rest.pct.mean():+.2f}% (R {rest.R.mean():+.3f})")
    out.append(f"  issuers - rest {d:+.2f}pp, t {t:+.2f} | halves (pre-2023 / 2023+) {d1:+.2f} / {d2:+.2f}")
    ok = d < 0 and abs(t) >= 3 and np.sign(d1) == np.sign(d2) == -1
    out.append(f"  bar (issuers worse, |t| >= 3, halves same sign): {'PASS' if ok else 'FAIL'}")
    out.append(f"  book with the veto: {rest.pct.mean():+.2f}%/trade vs all {K.pct.mean():+.2f}% (removes {100 * len(iss_m) / len(K):.0f}% of trades)")
    for lab, lo, hi in (("buyback (<= -2%)", -9, -0.02), ("flat (-2..+2%)", -0.02, 0.02), ("mild (+2..+5%)", 0.02, 0.05),
                        ("issuer (+5..+15%)", 0.05, 0.15), ("heavy (>= +15%)", 0.15, 9)):
        z = K[(K.iss >= lo) & (K.iss < hi)]
        out.append(f"    {lab:18s} n {len(z):5,}  {z.pct.mean():+.2f}%/trade  R {z.R.mean():+.3f}  win {100 * (z.pct > 0).mean():.0f}%")
    K.to_csv(REPO / "data/studies/net_issuance_trades_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

#!/usr/bin/env python3
"""Paid-to-wait put spread: IV >= 60th-pct gate with full options_iv_daily coverage + delta-matched stock (2026-09-29).

PRE-REGISTERED: data/studies/paid_to_wait_iv_gate_2026-09-29.md (committed a0b69fa before this ran). Trades frozen from
data/studies/paid_to_wait_events.csv (hold to expiry, roc_hold_net). Gate = entry-date call50_iv percentile in the
ticker's trailing 252 sessions (min 126) >= 0.60. Stock control = +0.15 delta of stock, entry close -> expiry close.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_paid_to_wait_iv_gate.py > data/studies/paid_to_wait_iv_gate_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path

import awswrangler as wr
import numpy as np
import pandas as pd

from lib.constants import S3_OUTPUT, WORKGROUP

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/paid_to_wait_iv_daily.parquet"
SPLIT, BAR, DELTA, SCOST = pd.Timestamp("2023-01-01"), 3.2, 0.15, 0.0005
pd.set_option("display.width", 220)


def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * sqrt(len(x)) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def pull(tickers) -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    tl = ",".join(f"'{t}'" for t in sorted(tickers))
    d = wr.athena.read_sql_query(
        f"SELECT ticker, trade_date, call50_iv, put25_iv FROM silver.options_iv_daily "
        f"WHERE trade_date BETWEEN DATE '2018-06-01' AND DATE '2026-03-31' AND ticker IN ({tl})",
        database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog", s3_output=S3_OUTPUT, ctas_approach=False)
    d["trade_date"] = pd.to_datetime(d.trade_date)
    d.to_parquet(CACHE, index=False)
    return d


def pct_at(iv: pd.DataFrame, col: str, ev: pd.DataFrame) -> pd.Series:
    out = np.full(len(ev), np.nan)
    g = {t: s.dropna(subset=[col]).set_index("trade_date")[col].sort_index() for t, s in iv.groupby("ticker")}
    for n, r in enumerate(ev.itertuples()):
        s = g.get(r.ticker)
        if s is None or r.entry_date not in s.index:
            continue
        w = s.loc[:r.entry_date].iloc[-252:]
        if len(w) >= 126:
            out[n] = (w.iloc[:-1] < w.iloc[-1]).mean()
    return pd.Series(out, index=ev.index)


def cell(x: pd.Series, d: pd.Series) -> dict:
    s = pd.Series(x.values, index=d.values).dropna()
    mo = s.groupby(s.index.to_period("M")).mean()
    h = mo.index < pd.Period(SPLIT, "M")
    return dict(n=len(s), mean=s.mean() * 100, t_month=tstat(mo), h1=mo[h].mean() * 100, h2=mo[~h].mean() * 100,
                months=len(mo), win=(s > 0).mean() * 100)


def diff_cell(a: pd.DataFrame, b: pd.DataFrame, col: str) -> dict:
    ma = a.groupby(a.entry_date.dt.to_period("M"))[col].mean(); mb = b.groupby(b.entry_date.dt.to_period("M"))[col].mean()
    dm = (ma - mb).dropna(); h = dm.index < pd.Period(SPLIT, "M")
    return dict(months=len(dm), mean=dm.mean() * 100, t_month=tstat(dm), h1=dm[h].mean() * 100, h2=dm[~h].mean() * 100)


def main():
    ev = pd.read_csv(REPO / "data/studies/paid_to_wait_events.csv", parse_dates=["entry_date", "expiry"])
    iv = pull(ev.ticker.unique())
    ev["pct_c50"] = pct_at(iv, "call50_iv", ev)
    ev["pct_p25"] = pct_at(iv, "put25_iv", ev)
    ev["stock_dm"] = DELTA * (ev.spot_expiry * (1 - SCOST) - ev.close * (1 + SCOST)) / ev.max_loss
    ev["spread_minus_stock"] = ev.roc_hold_net - ev.stock_dm
    print(f"events {len(ev):,}; new percentile known {ev.pct_c50.notna().mean():.1%} (old iv_pct {ev.iv_pct.notna().mean():.1%})")
    both = ev.dropna(subset=["pct_c50", "iv_pct"])
    print(f"sanity: gate agreement new vs old on {len(both)} events: {((both.pct_c50 >= .6) == (both.iv_pct >= .6)).mean():.1%}; "
          f"rank corr {both.pct_c50.corr(both.iv_pct, method='spearman'):.2f}")
    k = ev.dropna(subset=["pct_c50"]).copy()
    G, U = k[k.pct_c50 >= 0.6], k[k.pct_c50 < 0.6]
    print(f"gated {len(G)} / ungated {len(U)} (dropped, no percentile: {len(ev) - len(k)})\n")

    rows = [dict(cell="gated roc_hold_net", **cell(G.roc_hold_net, G.entry_date)),
            dict(cell="ungated roc_hold_net", **cell(U.roc_hold_net, U.entry_date)),
            dict(cell="PRIMARY 1: gated - ungated", **diff_cell(G, U, "roc_hold_net")),
            dict(cell="PRIMARY 2: gated spread - dm stock", **cell(G.spread_minus_stock, G.entry_date)),
            dict(cell="gated dm stock alone", **cell(G.stock_dm, G.entry_date)),
            dict(cell="ungated spread - dm stock", **cell(U.spread_minus_stock, U.entry_date))]
    Gp, Up = k[k.pct_p25 >= 0.6], k[(k.pct_p25 < 0.6)]
    rows += [dict(cell="put25 gate: gated - ungated", **diff_cell(Gp, Up, "roc_hold_net")),
             dict(cell="put25 gate: gated spread - dm stock", **cell(Gp.spread_minus_stock, Gp.entry_date))]
    R = pd.DataFrame(rows)
    print(R.round(2).to_string(index=False))
    p1, p2 = R.iloc[2], R.iloc[3]
    ok1 = p1["mean"] > 0 and p1.t_month >= BAR and p1.h1 > 0 and p1.h2 > 0
    ok2 = p2["mean"] > 0 and p2.t_month >= BAR and p2.h1 > 0 and p2.h2 > 0
    print(f"\nPASS 1 gate effect (t >= {BAR}, halves > 0): {'YES' if ok1 else 'no'}")
    print(f"PASS 2 beats delta-matched stock: {'YES' if ok2 else 'no'}")
    print("READ:", "SUPPORTED" if ok1 and ok2 else "NULL as a vehicle (stock instead)" if ok1 else "NULL: the gate does not separate outcomes")
    print("\nby year, gated vs ungated roc_hold_net (%), and gated spread - dm stock:")
    print(pd.DataFrame({"gated": G.groupby(G.entry_date.dt.year).roc_hold_net.mean() * 100, "n_g": G.groupby(G.entry_date.dt.year).size(),
                        "ungated": U.groupby(U.entry_date.dt.year).roc_hold_net.mean() * 100,
                        "g_minus_stock": G.groupby(G.entry_date.dt.year).spread_minus_stock.mean() * 100}).round(1).T.to_string())
    print("\nby regime state, gated roc_hold_net (%):", (G.groupby("state").roc_hold_net.mean() * 100).round(1).to_dict(),
          G.groupby("state").size().to_dict())
    R.to_csv(REPO / "data/studies/paid_to_wait_iv_gate_2026-09-29.csv", index=False)
    ev.to_csv(REPO / "data/studies/logs/paid_to_wait_iv_gate_events.csv", index=False)


if __name__ == "__main__":
    main()

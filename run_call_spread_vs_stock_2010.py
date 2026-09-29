#!/usr/bin/env python3
"""30/15-delta call debit spread vs delta-matched stock on UNSEEN 2010-01 -> 2019-09 (2026-09-29, audit List A #8).

PRE-REGISTERED: data/studies/call_spread_vs_stock_2010_2026-09-29.md (committed acf91b3 before the pull). Logic frozen from
run_vehicle_benchmark.py; only the window changes, plus a declared settlement rule (last trading day <= expiry, for the
pre-2015 Saturday-dated monthlies). Primary: call - stock $/contract, month-clustered t >= 3, both halves (2015 split),
AND the SPY < 200 SMA cell > 0 with t >= 2.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_call_spread_vs_stock_2010.py > data/studies/call_spread_vs_stock_2010_2026-09-29.log
"""
from __future__ import annotations

import os
import warnings
from math import sqrt

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
CACHE = "data/cache/call_spread_vs_stock_2010_chains.parquet"
NAMES = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMD", "META", "AMZN", "GOOGL",
         "TSLA", "NFLX", "JPM", "XOM", "GLD", "SMH", "COST", "AVGO", "CRM", "WMT"]
COMM, HO_START, HO_END, SPLIT = 0.0065, "2010-01-01", "2019-09-30", "2015-01-01"


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    lst = ", ".join(f"'{t}'" for t in NAMES)
    df = athena(f"""
    SELECT ticker, trade_date, expiry, cp, strike,
           CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask, CAST(delta AS DOUBLE) d,
           CAST((bid_iv + ask_iv)/2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({lst})
      AND trade_date >= TIMESTAMP '2009-06-01 00:00:00' AND trade_date <= TIMESTAMP '2019-12-31 23:59:59'
      AND day_of_week(trade_date) = 5
      AND bid > 0 AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) BETWEEN 25 AND 40
      AND ABS(delta) BETWEEN 0.10 AND 0.40
    """)
    df.to_parquet(CACHE, index=False)
    return df


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.07 else None


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def main():
    raw = pull()
    raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize(); raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
    print(f"pulled {len(raw):,} rows, {raw.ticker.nunique()} names, {raw.trade_date.min().date()} -> {raw.trade_date.max().date()}; "
          f"iv present {raw.iv.notna().mean():.1%}")
    SPOT = spot_from_chain(raw.dropna(subset=["iv"]), delta="d")
    days = pd.DatetimeIndex(sorted(raw.trade_date.unique()))     # Fridays with chains (the settlement candidates)
    panel = pd.read_parquet("data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    panel["date"] = pd.to_datetime(panel.date)
    spy = panel[panel.ticker == "SPY"].set_index("date").close.sort_index(); spy200 = spy.rolling(200).mean()
    vix = pd.read_parquet("data/cache/vix_daily_long.parquet"); VIX = vix.set_index(pd.to_datetime(vix.trade_date)).vix_close
    rows, drop = [], dict(legs=0, spot=0, bad=0)
    for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
        if not (pd.Timestamp(HO_START) <= d <= pd.Timestamp(HO_END)):
            continue
        g = g.copy(); g["gap"] = (g.dte - 30).abs()
        exp = g.sort_values("gap").expiry.iloc[0]; g = g[g.expiry == exp]
        c30, c15 = pick(g[g.cp == "C"], 0.30), pick(g[g.cp == "C"], 0.15)
        p30, p20 = pick(g[g.cp == "P"], 0.30), pick(g[g.cp == "P"], 0.20)
        if any(x is None for x in (c30, c15, p30, p20)):
            drop["legs"] += 1; continue
        sd = days[days <= exp]
        settle = sd[-1] if len(sd) else pd.NaT
        S, ST = SPOT.get((tk, d), np.nan), SPOT.get((tk, settle), np.nan)
        if not (np.isfinite(S) and np.isfinite(ST)) or (exp - settle).days > 3:
            drop["spot"] += 1; continue
        debit = (c30.ask - c15.bid) + 2 * COMM; wc = c15.strike - c30.strike
        credit = (p30.bid - p20.ask) - 2 * COMM; wp = p30.strike - p20.strike
        if debit <= 0 or wc <= 0 or credit <= 0 or wp <= 0 or credit >= wp:
            drop["bad"] += 1; continue
        dlt_call = float(c30.d - c15.d); dlt_put = float(abs(p30.d) - abs(p20.d)); move = ST - S
        rows.append(dict(sym=tk, date=d, expiry=exp, settle=settle, S=S, ST=ST, ret=(ST / S - 1) * 100,
                         pnl_call=(min(max(ST - c30.strike, 0.0), wc) - debit) * 100,
                         pnl_put=(credit - min(max(p30.strike - ST, 0.0), wp)) * 100,
                         risk_call=debit * 100, dlt_call=dlt_call, stock_call=100 * dlt_call * move, stock_put=100 * dlt_put * move,
                         vix=float(VIX.get(d, np.nan)),
                         spy_up=bool(np.isfinite(spy200.get(d, np.nan)) and spy.get(d, np.nan) > spy200.get(d, np.nan))))
    T = pd.DataFrame(rows).sort_values(["sym", "date"])
    T["month"] = T.date.dt.to_period("M")
    T["vs_stock_call"] = T.pnl_call - T.stock_call; T["vs_stock_put"] = T.pnl_put - T.stock_put
    print(f"holdout entries {len(T):,} · {T.sym.nunique()} names · {T.date.min().date()}..{T.date.max().date()} · {T.month.nunique()} months; "
          f"dropped {drop}; Saturday-dated expiries settled on the prior Friday: {(T.expiry != T.settle).mean():.1%}")

    def cl(df, col):
        m = df.groupby("month")[col].mean(); return m.mean(), mt(m), len(m)

    def row(lab, df):
        a, ta, nm = cl(df, "vs_stock_call"); b, tb, _ = cl(df, "vs_stock_put")
        h = df.date < pd.Timestamp(SPLIT)
        a1 = cl(df[h], "vs_stock_call")[0] if h.any() else np.nan; a2 = cl(df[~h], "vs_stock_call")[0] if (~h).any() else np.nan
        return dict(cut=lab, n=len(df), months=nm, call=df.pnl_call.mean(), stock=df.stock_call.mean(), call_vs_stock=a, t=ta,
                    h1=a1, h2=a2, put_vs_stock=b, t_put=tb)
    out = [row("ALL (PRIMARY 1)", T), row("SPY < 200 SMA (PRIMARY 2)", T[~T.spy_up]), row("SPY > 200 SMA", T[T.spy_up])]
    dn = T.groupby("month").ret.mean() < 0
    out.append(row("down months", T[T.month.map(dn)])); out.append(row("up months", T[~T.month.map(dn)]))
    vt = pd.qcut(T.vix, 3, labels=["VIX low", "VIX mid", "VIX high"])
    out += [row(str(k), T[vt == k]) for k in vt.cat.categories]
    out += [row(f"year {y}", g) for y, g in T.groupby(T.date.dt.year)]
    R = pd.DataFrame(out)
    print(R.round(2).to_string(index=False))
    p1, p2 = R.iloc[0], R.iloc[1]
    ok1 = p1.call_vs_stock > 0 and p1.t >= 3 and p1.h1 > 0 and p1.h2 > 0
    ok2 = p2.call_vs_stock > 0 and p2.t >= 2
    print(f"\nPASS 1 (ALL > 0, t >= 3, both halves): {'YES' if ok1 else 'no'}\nPASS 2 (SPY < 200 SMA > 0, t >= 2): {'YES' if ok2 else 'no'}")
    print(f"VERDICT: {'PASS -> SUPPORTED' if ok1 and ok2 else 'FAIL'}")
    old = pd.read_csv("data/studies/vehicle_benchmark_2026-09-22.csv", parse_dates=["date"])
    old["month"] = old.date.dt.to_period("M")
    P = pd.concat([T[["month", "vs_stock_call", "spy_up"]], old[["month", "vs_stock_call", "spy_up"]]])
    m = P.groupby("month").vs_stock_call.mean(); mb = P[~P.spy_up].groupby("month").vs_stock_call.mean()
    print(f"\nexploratory POOLED 2010-2026: call vs stock {m.mean():+.0f} $/contract, t {mt(m):.2f} ({len(m)} months); "
          f"SPY < 200 SMA {mb.mean():+.0f}, t {mt(mb):.2f} ({len(mb)} months)")
    R.to_csv("data/studies/call_spread_vs_stock_2010_2026-09-29.csv", index=False)
    T.to_csv("data/studies/logs/call_spread_vs_stock_2010_entries.csv", index=False)


if __name__ == "__main__":
    main()

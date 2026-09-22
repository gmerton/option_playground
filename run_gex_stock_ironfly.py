#!/usr/bin/env python3
"""1-day 2x iron butterfly on 10 mega-cap stocks, by own-stock GEX (A) and SPY GEX (B) (2026-09-21).

PRE-REGISTERED: data/studies/gex_stock_ironfly_2026-09-21.md -- implements that spec; do not tune against its output.
Inputs: data/cache/gex/stocks/<TK>.parquet (Athena pull: per-strike OI*gamma on expiry-eve days + entry-day quotes
for the next-day expiry + expiry-day quotes for the parity settle), SPY GEX via run_gex_regime_pin.gex_series.
Usage: PYTHONPATH=src:. .venv/bin/python3 run_gex_stock_ironfly.py | tee data/studies/gex_stock_ironfly_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

import run_gex_regime_pin as base

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
NAMES = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX", "AVGO"]
SLIP, COMM, WING, MIN_MID = 0.25, 0.0065, 2.0, 0.10
SPLIT = pd.Timestamp("2018-01-01")


def parity_spot(c: pd.DataFrame, p: pd.DataFrame) -> float:
    ks = c.index.intersection(p.index)
    if not len(ks):
        return np.nan
    d = (c.loc[ks, "mid"] - p.loc[ks, "mid"])
    k = d.abs().idxmin()
    return float(k + d[k])


def legs(df):
    df = df.copy(); df["mid"] = (df.bid + df.ask) / 2; df["ba"] = df.ask - df.bid
    df = df[(df.ask > 0) & (df.ask >= df.bid) & (df.bid >= 0)].sort_values("ba").drop_duplicates(["strike", "cp"])
    return df[df.cp == "C"].set_index("strike").sort_index(), df[df.cp == "P"].set_index("strike").sort_index()


def run_name(tk: str) -> pd.DataFrame:
    x = pd.read_parquet(f"data/cache/gex/stocks/{tk}.parquet")
    x["trade_date"] = pd.to_datetime(x.trade_date); x["expiry"] = pd.to_datetime(x.expiry)
    G = x[x.part == "gex"]; Q = x[x.part == "quotes"]
    E, S = Q[Q.kind == "entry"], Q[Q.kind == "settle"]
    s_by = {k: v for k, v in S.groupby("trade_date")}
    g_by = {k: v for k, v in G.groupby("trade_date")}
    rows = []
    for d, e in E.groupby("trade_date"):
        exp = e.expiry.iloc[0]
        c, p = legs(e)
        S0 = parity_spot(c, p)
        if not np.isfinite(S0) or exp not in s_by or d not in g_by:
            continue
        cs, ps = legs(s_by[exp])
        S1 = parity_spot(cs, ps)
        if not np.isfinite(S1):
            continue
        cd = c.dropna(subset=["delta"])
        ks = cd.index.intersection(p.index)
        if not len(ks):
            continue
        K = (cd.loc[ks].delta - 0.5).abs().idxmin()
        smid = c.loc[K, "mid"] + p.loc[K, "mid"]
        if smid < MIN_MID:
            continue
        cw = c[(c.index > K) & (c.bid > 0)]; pw = p[(p.index < K) & (p.ask > 0)]
        if cw.empty or pw.empty:
            continue
        kc = cw.index[np.abs(cw.index - (K + WING * smid)).argmin()]; kp = pw.index[np.abs(pw.index - (K - WING * smid)).argmin()]
        sell = lambda r: r.mid - SLIP * r.ba; buy = lambda r: r.mid + SLIP * r.ba
        credit = sell(c.loc[K]) + sell(p.loc[K]) - buy(c.loc[kc]) - buy(p.loc[kp]) - 4 * COMM
        width = max(kc - K, K - kp)
        if credit <= 0 or width - credit <= 0:
            continue
        pay = min(max(S1 - K, 0), kc - K) + min(max(K - S1, 0), K - kp)
        pnl = credit - pay
        g = g_by[d]; g = g[(g.strike >= 0.8 * S0) & (g.strike <= 1.2 * S0)]
        gex = float(((g.cg - g.pg) * 100 * S0 * S0 * 0.01).sum())
        ba_pct = (c.loc[K, "ba"] + p.loc[K, "ba"]) / smid * 100
        rows.append(dict(tk=tk, entry=d, expiry=exp, S0=S0, S1=S1, K=K, implied=smid / S0 * 100, ba_pct=ba_pct,
                         credit=credit, maxrisk=width - credit, pnl_usd=pnl * 100, ret_risk=pnl / (width - credit) * 100, gex_own=gex))
    R = pd.DataFrame(rows).sort_values("entry")
    med = R.implied.shift(1).rolling(8, min_periods=4).median()          # trailing, no look-ahead
    R["earnings_skip"] = R.implied > 2 * med
    return R


def by_date_t(g: pd.DataFrame) -> float:
    m = g.groupby("entry").ret_risk.mean()
    return m.mean() / m.std() * np.sqrt(len(m)) if len(m) > 2 and m.std() > 0 else np.nan


def main():
    bars = base.daily_bars("SPY"); _, spy, _ = base.gex_series("SPY", bars)
    X = pd.concat([run_name(t) for t in NAMES], ignore_index=True)
    X["gex_spy"] = spy.reindex(X.entry).values
    print(f"{len(X):,} flies on {X.entry.nunique():,} entry dates; earnings-screened out {int(X.earnings_skip.sum()):,}; "
          f"median ATM straddle bid-ask {X.ba_pct.median():.1f}% of mid (SPY was 1.1%)")
    X = X[~X.earnings_skip]
    X["half"] = np.where(X.entry < SPLIT, "2010-2017", "2018-2026")
    rows = []
    for cond, col in (("A own-stock GEX", "gex_own"), ("B SPY GEX", "gex_spy")):
        Y = X.dropna(subset=[col])
        for lab, g in (("POS", Y[Y[col] > 0]), ("NEG", Y[Y[col] <= 0]), ("ALL", Y)):
            h1, h2 = g[g.half == "2010-2017"], g[g.half == "2018-2026"]
            rows.append(dict(condition=cond, gamma=lab, flies=len(g), dates=g.entry.nunique(), ret_risk=g.ret_risk.mean(), t_dates=by_date_t(g),
                             half1=h1.ret_risk.mean(), t1=by_date_t(h1), half2=h2.ret_risk.mean(), t2=by_date_t(h2),
                             win=(g.pnl_usd > 0).mean() * 100, usd_mean=g.pnl_usd.mean(), worst_usd=g.pnl_usd.min()))
    R = pd.DataFrame(rows)
    print("\n== 2x iron fly, return on max risk at the real fill (%); t across entry dates ==")
    print(R.round(2).to_string(index=False))
    for cond in R.condition.unique():
        pos = R[(R.condition == cond) & (R.gamma == "POS")].iloc[0]; neg = R[(R.condition == cond) & (R.gamma == "NEG")].iloc[0]
        ok = pos.ret_risk > 0 and pos.t_dates >= 3 and pos.half1 > 0 and pos.half2 > 0 and pos.ret_risk > neg.ret_risk
        print(f"PASS {cond}: {'YES' if ok else 'no'}")
    print("\nper name (all entries / own-POS / SPY-POS, mean % on risk; n; median bid-ask %):")
    per = X.groupby("tk").agg(all=("ret_risk", "mean"), n=("ret_risk", "size"), ba=("ba_pct", "median"))
    per["own_POS"] = X[X.gex_own > 0].groupby("tk").ret_risk.mean(); per["spy_POS"] = X[X.gex_spy > 0].groupby("tk").ret_risk.mean()
    print(per.round(1).to_string())
    X.to_csv("data/studies/gex_stock_ironfly_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

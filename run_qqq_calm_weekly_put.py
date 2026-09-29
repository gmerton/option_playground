#!/usr/bin/env python3
"""
REPLICATION on QQQ of the calm-regime weekly put sale (pre-registered 2026-09-28, committed before any run).

The rule is FIXED from the SPY study (spy_calm_weekly_put_2026-09-28.md) and applied unchanged to QQQ's own chain,
price and dealer gamma. QQQ is not independent of SPY (high daily correlation) -- this checks that the result is not a
property of SPY's specific chain / positioning data, not that it holds in an unrelated market.

PRE-REGISTRATION
  Data      silver.options_daily_v3, ticker QQQ, PUTS, DTE 5-9, 2010-11 -> 2026-02 (QQQ GEX history starts 2010-11-22),
            pulled here; QQQ daily close (yfinance, raw -- QQQ has no split in-sample after 2010? checked: none) and VIX.
  Rule      FRIDAY entry; CALM = NOT (QQQ close < its 50-session SMA AND VIX >= 20); GAMMA+ = QQQ net dealer GEX > 0 at
            the entry close (run_gex_regime_pin.gex_series("QQQ")); sell the 7-DTE put (expiry nearest 7 in [5, 9]) at
            |delta| nearest 0.10 (+/-0.025) [primary] and 0.05 (+/-0.015); hold to expiry; settle on QQQ's close; house
            fills (mid - 25% bid-ask - $0.0065/share).
  Statistic excess over beta per trade = net - |delta| x QQQ return entry->expiry (carry-adjusted, q 0.6%, T-bill),
            bp of notional, month-clustered t.
  REPLICATES iff the 10-delta CALM & GAMMA+ excess has t >= 2 (a single confirmatory test of a fixed rule) AND both
            halves (2010-2017 / 2018-2026) are positive. Also reported: the no-gate CALM cell and the CALM & GAMMA- cell
            (does the gate do the same job on QQQ?), 5-delta, worst trade, per-year.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_qqq_calm_weekly_put.py > data/studies/logs/qqq_calm_weekly_put.log
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
Q, SLIP, COMM = 0.006, 0.25, 0.0065
CACHE = Path("data/cache/QQQ_puts_v3_dte5_9.parquet")


def pull():
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    from lib.athena_lib import athena
    fr = []
    for y in range(2010, 2027):
        fr.append(athena(f"""SELECT trade_date, expiry, CAST(strike AS DOUBLE) strike, CAST(bid AS DOUBLE) bid,
                            CAST(ask AS DOUBLE) ask, CAST(delta AS DOUBLE) delta
                            FROM silver.options_daily_v3 WHERE ticker = 'QQQ' AND year(trade_date) = {y}
                            AND upper(substr(cp, 1, 1)) = 'P' AND date_diff('day', trade_date, expiry) BETWEEN 5 AND 9"""))
        print(f"  QQQ puts {y}: {len(fr[-1]):,}", flush=True)
    d = pd.concat(fr, ignore_index=True)
    d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
    d.to_parquet(CACHE, index=False)
    return d


def yf_close(tk):
    import yfinance as yf
    s = yf.download(tk, start="2009-06-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def mclust(x, d):
    df = pd.DataFrame(dict(x=np.asarray(x), m=pd.to_datetime(np.asarray(d)).to_period("M"))).dropna()
    mu = df.x.mean(); s = df.groupby("m").x.sum(); n = df.groupby("m").size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return mu, (mu / se if se > 0 else np.nan)


def main():
    import run_gex_regime_pin as gp
    D = pull()
    S = yf_close("QQQ"); V = yf_close("^VIX").reindex(S.index).ffill(); R = (yf_close("^IRX") / 100).reindex(S.index).ffill()
    jumps = S.pct_change().abs() > 0.2
    print(f"QQQ price jumps > 20% (split check): {int(jumps.sum())}")
    stress = (S < S.rolling(50).mean()) & (V >= 20)
    _, net, _ = gp.gex_series("QQQ", pd.DataFrame({"close": S}))
    D = D[(D.trade_date.dt.dayofweek == 4) & (D.bid > 0) & (D.ask >= D.bid) & D.delta.notna()].copy()
    D["dte"] = (D.expiry - D.trade_date).dt.days; D["ad"] = D.delta.abs()
    D["dd"] = (D.dte - 7).abs()
    D = D[D.dd == D.groupby("trade_date").dd.transform("min")]
    D = D[D.expiry == D.groupby("trade_date").expiry.transform("min")]
    rows = []
    for leg, (tgt, tol) in {"N10": (0.10, 0.025), "N05": (0.05, 0.015)}.items():
        x = D[(D.ad - tgt).abs() <= tol].copy(); x["err"] = (x.ad - tgt).abs()
        x = x.sort_values("err").drop_duplicates("trade_date")
        x["S0"] = S.reindex(x.trade_date).values
        ei = S.index.searchsorted(x.expiry.values, side="right") - 1
        x["ST"] = S.values[ei]; x["r"] = R.reindex(x.trade_date).values
        mid = (x.bid + x.ask) / 2
        x["net"] = (mid - SLIP * (x.ask - x.bid) - COMM - np.maximum(x.strike - x.ST, 0)) / x.S0 * 1e4
        x["excess"] = x.net - x.ad * ((x.ST - x.S0) / x.S0 + (Q - x.r) * x.dte / 365) * 1e4
        x["calm"] = ~stress.reindex(x.trade_date).fillna(False).values
        x["gamma"] = np.sign(net.reindex(x.trade_date).values)
        x["leg"] = leg
        rows.append(x.dropna(subset=["net", "gamma"]))
    X = pd.concat(rows)
    out = []
    for (leg, lab), m in [(("N10", "PRIMARY CALM&G+"), lambda z: z.calm & (z.gamma > 0)), (("N10", "CALM no gate"), lambda z: z.calm),
                          (("N10", "CALM&G- (skipped)"), lambda z: z.calm & (z.gamma < 0)), (("N05", "CALM&G+"), lambda z: z.calm & (z.gamma > 0))]:
        g = X[(X.leg == leg)]; g = g[m(g)]
        mu, t = mclust(g.net, g.trade_date); ex, tx = mclust(g.excess, g.trade_date)
        yr = g.groupby(g.trade_date.dt.year).excess.mean()
        out.append(dict(cell=f"{leg} {lab}", n=len(g), years=f"{g.trade_date.dt.year.min()}-{g.trade_date.dt.year.max() % 100}",
                        net_bp=mu, t_net=t, excess_bp=ex, t_excess=tx,
                        h1=g[g.trade_date < "2018-01-01"].excess.mean(), h2=g[g.trade_date >= "2018-01-01"].excess.mean(),
                        yrs_pos=(yr > 0).mean(), win=100 * (g.net > 0).mean(), worst=g.net.min()))
    T = pd.DataFrame(out); print(T.round(2).to_string(index=False))
    p = T.iloc[0]
    ok = p.t_excess >= 2 and p.h1 > 0 and p.h2 > 0
    print(f"\nREPLICATION (QQQ, fixed SPY rule): excess {p.excess_bp:+.2f} bp t {p.t_excess:+.2f}, halves {p.h1:+.2f}/{p.h2:+.2f} -> "
          f"{'REPLICATES' if ok else 'DOES NOT REPLICATE'}")
    g = X[(X.leg == "N10") & X.calm & (X.gamma > 0)]
    print("per year excess (primary):", g.groupby(g.trade_date.dt.year).excess.mean().round(2).to_dict())
    X.to_csv("data/studies/logs/qqq_calm_weekly_put_entries.csv", index=False)


if __name__ == "__main__":
    main()

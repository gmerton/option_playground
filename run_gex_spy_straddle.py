#!/usr/bin/env python3
"""SPY 1-day ATM straddles by dealer-gamma sign (2026-09-21).

PRE-REGISTERED: data/studies/gex_spy_straddle_2026-09-21.md -- implements that spec; do not tune against its output.
Long on negative-GEX days (item 2), short on positive-GEX days (item 1), straddle from day t-1's close to the expiry
settling on day t, real fills (mid +/- 25% of the bid-ask, $0.0065/sh/leg). GEX and daily bars reuse
run_gex_regime_pin.py so the gamma series is identical to the regime test.

Inputs: data/cache/gex/SPY_short_expiry_quotes.parquet (Athena pull: SPY bid/ask/delta, expiries <= 4 days out),
data/cache/gex/SPY_gex_strikes.parquet, data/cache/intraday_hist/SPY_1min.parquet, ^VIX (yfinance).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_gex_spy_straddle.py | tee data/studies/gex_spy_straddle_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

import run_gex_regime_pin as base

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
SLIP, COMM, MIN_MID = 0.25, 0.0065, 0.10


def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def main():
    import yfinance as yf
    bars = base.daily_bars("SPY")
    _, net, _ = base.gex_series("SPY", bars)
    v = yf.download("^VIX", start="2009-11-01", end="2026-03-05", progress=False, auto_adjust=False)
    vix = v["Close"].squeeze(); vix.index = pd.to_datetime(vix.index).normalize()

    q = pd.read_parquet("data/cache/gex/SPY_short_expiry_quotes.parquet")
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    days = bars.index
    nxt = pd.Series(days[1:], index=days[:-1])                 # next trading day
    q = q[q.trade_date.isin(nxt.index)]
    q = q[q.expiry == q.trade_date.map(nxt)]                    # expiry settles on day t
    q = q[(q.ask >= q.bid) & (q.ask < 9999)]
    q["mid"] = (q.bid + q.ask) / 2; q["ba"] = q.ask - q.bid
    q = q.sort_values("ba").drop_duplicates(["trade_date", "strike", "cp"], keep="first")

    rows = []
    for d, g in q.groupby("trade_date"):
        c = g[g.cp == "C"].set_index("strike"); p = g[g.cp == "P"].set_index("strike")
        ks = c.index.intersection(p.index)
        if not len(ks) or c.loc[ks].delta.isna().all():
            continue
        c, p = c.loc[ks], p.loc[ks]
        K = (c.delta - 0.5).abs().idxmin()
        mid = c.loc[K, "mid"] + p.loc[K, "mid"]; ba = c.loc[K, "ba"] + p.loc[K, "ba"]
        if mid < MIN_MID:
            continue
        t = nxt[d]
        S_prev, S_t = bars.close.get(d, np.nan), bars.close.get(t, np.nan)
        if not np.isfinite(S_t) or d not in net.index or d not in vix.index:
            continue
        pay = abs(S_t - K)
        cost = mid + SLIP * ba + 2 * COMM
        credit = mid - SLIP * ba - 2 * COMM
        rows.append(dict(entry=d, day=t, K=K, S_prev=S_prev, S_t=S_t, mid=mid, ba_pct=ba / mid * 100,
                         implied_pct=mid / S_prev * 100, ratio=pay / mid, gex=net[d], vix=vix[d],
                         long_mid=(pay - mid) / mid * 100, long_fill=(pay - cost) / cost * 100,
                         short_fill=(credit - pay) / credit * 100 if credit > 0 else np.nan,
                         short_usd=(credit - pay) * 100))
    X = pd.DataFrame(rows).set_index("day")
    X["NEG"] = (X.gex < 0).astype(float)
    X["half"] = np.where(X.index < base.SPLIT, "2010-2017", "2018-2026")
    print(f"SPY 1-day straddles: {len(X):,} days {X.index.min().date()} -> {X.index.max().date()}; "
          f"negative-GEX {int(X.NEG.sum()):,}, positive {int((1 - X.NEG).sum()):,}; median bid-ask {X.ba_pct.median():.1f}% of mid")

    print("\n== Mechanism: realised/implied move ratio on NEG, controlling for log VIX(t-1) (Newey-West, 5 lags) ==")
    for lab, g in [("full", X)] + list(X.groupby("half")):
        f = sm.OLS(g.ratio, sm.add_constant(pd.DataFrame({"NEG": g.NEG, "lvix": np.log(g.vix)}))).fit(
            cov_type="HAC", cov_kwds={"maxlags": 5})
        print(f"  {lab:10s} n {len(g):5d}  b_NEG {f.params.NEG:+.3f}  t {f.tvalues.NEG:+.2f}  | ratio NEG {g[g.NEG == 1].ratio.mean():.3f}  POS {g[g.NEG == 0].ratio.mean():.3f}")

    print("\n== Returns on premium (%), by gamma sign ==")
    rows = []
    for (lab, neg), g in [(("full", n), g) for n, g in X.groupby("NEG")] + [((h, n), g) for (h, n), g in X.groupby(["half", "NEG"])]:
        rows.append(dict(sample=lab, gamma="NEG" if neg else "POS", n=len(g), implied=g.implied_pct.median(),
                         ratio=g.ratio.mean(), long_mid=g.long_mid.mean(), long_fill=g.long_fill.mean(), t_long=tstat(g.long_fill),
                         short_fill=g.short_fill.mean(), t_short=tstat(g.short_fill), short_win=(g.short_fill > 0).mean() * 100,
                         worst_short_pct=g.short_fill.min()))
    T = pd.DataFrame(rows); print(T.round(2).to_string(index=False))

    allshort = X.short_fill
    pos, neg = X[X.NEG == 0], X[X.NEG == 1]
    print(f"\nshort on EVERY day: {allshort.mean():+.2f}% (t {tstat(allshort):.2f}, n {len(X)}); "
          f"short on POS days only {pos.short_fill.mean():+.2f}% -> difference {pos.short_fill.mean() - allshort.mean():+.2f}pp "
          f"(POS vs NEG gap {pos.short_fill.mean() - neg.short_fill.mean():+.2f}pp, Welch t "
          f"{(pos.short_fill.mean() - neg.short_fill.mean()) / np.sqrt(pos.short_fill.var() / len(pos) + neg.short_fill.var() / len(neg)):.2f})")
    print(f"worst short days (POS): {pos.short_fill.nsmallest(3).round(0).tolist()}% of credit; "
          f"$ per straddle worst {pos.short_usd.min():,.0f}, mean {pos.short_usd.mean():+.1f}")

    def passes(side):
        g = neg if side == "long" else pos
        col = "long_fill" if side == "long" else "short_fill"
        halves_ok = all(X[(X.half == h) & (X.NEG == (1 if side == "long" else 0))][col].mean() > 0 for h in ("2010-2017", "2018-2026"))
        ok = g[col].mean() > 0 and tstat(g[col]) >= 3 and halves_ok
        if side == "short":
            ok = ok and pos.short_fill.mean() > allshort.mean()
        return ok
    print(f"\nPASS item 2 (long on NEG): {'YES' if passes('long') else 'no'} | PASS item 1 (short on POS): {'YES' if passes('short') else 'no'}")
    print("\nby year (long_fill on NEG / short_fill on POS, %):")
    X["yr"] = X.index.year
    print(pd.DataFrame({"long_NEG": X[X.NEG == 1].groupby("yr").long_fill.mean(), "n_NEG": X[X.NEG == 1].groupby("yr").size(),
                        "short_POS": X[X.NEG == 0].groupby("yr").short_fill.mean(), "n_POS": X[X.NEG == 0].groupby("yr").size()}).round(1).T.to_string())
    X.to_csv("data/studies/gex_spy_straddle_2026-09-21.csv")


if __name__ == "__main__":
    main()

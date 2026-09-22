#!/usr/bin/env python3
"""Post-shock SPY vol premium (2026-09-21): after a >= 2 sigma SPY day, are 1/5/10-day SPY straddles over-priced vs
VIX-matched normal days?

PRE-REGISTERED: data/studies/post_shock_vol_premium_2026-09-21.md -- implements that spec; do not tune against its output.
Inputs: data/cache/gex/SPY_quotes_20d.parquet (Athena: SPY bid/ask/delta, expiries <= 20 calendar days),
SPY 1-min file via run_gex_regime_pin.daily_bars, ^VIX (yfinance), data/studies/gex_spy_straddle_2026-09-21.csv
(weekend diagnostic).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_post_shock_premium.py | tee data/studies/post_shock_vol_premium_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import run_gex_regime_pin as base

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
SLIP, COMM, MIN_MID = 0.25, 0.0065, 0.10
HORIZONS = {1: 0, 5: 2, 10: 2}          # h -> allowed |tdte - h|
SPLIT = pd.Timestamp("2018-01-01")


def shocks(close: pd.Series) -> pd.DataFrame:
    r = np.log(close).diff()
    sd = r.shift(1).rolling(20).std()
    shock = (r.abs() >= 2 * sd) & sd.notna()
    days = close.index
    ep = pd.Series(np.nan, index=days); direction = pd.Series("", index=days)
    ep_id, last_shock_i, first_ret = -1, -99, 0.0
    for i, d in enumerate(days):
        if shock.iloc[i]:
            if i - last_shock_i > 5:
                ep_id += 1; first_ret = r.iloc[i]
            last_shock_i = i
            for j in range(i, min(i + 5, len(days))):
                ep.iloc[j] = ep_id; direction.iloc[j] = "DOWN" if first_ret < 0 else "UP"
    return pd.DataFrame({"ret": r, "shock": shock, "episode": ep, "direction": direction})


def main():
    import yfinance as yf
    bars = base.daily_bars("SPY"); close = bars.close
    days = close.index; pos = {d: i for i, d in enumerate(days)}
    S = shocks(close)
    v = yf.download("^VIX", start="2009-12-01", end="2026-03-05", progress=False, auto_adjust=False)
    vix = v["Close"].squeeze(); vix.index = pd.to_datetime(vix.index).normalize()

    q = pd.read_parquet("data/cache/gex/SPY_quotes_20d.parquet")
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    q = q[q.trade_date.isin(pos) & q.expiry.isin(pos)]
    q = q[(q.ask >= q.bid) & (q.ask < 9999)]
    q["mid"] = (q.bid + q.ask) / 2; q["ba"] = q.ask - q.bid
    q = q.sort_values("ba").drop_duplicates(["trade_date", "expiry", "strike", "cp"], keep="first")
    q["tdte"] = q.expiry.map(pos) - q.trade_date.map(pos)

    rows = []
    for d, g in q.groupby("trade_date"):
        if d not in vix.index:
            continue
        for h, tol in HORIZONS.items():
            ex = g.drop_duplicates("expiry")[["expiry", "tdte"]]
            ex = ex[(ex.tdte - h).abs() <= tol]
            if ex.empty:
                continue
            exp = ex.iloc[(ex.tdte - h).abs().argmin()].expiry
            e = g[g.expiry == exp]
            c = e[e.cp == "C"].set_index("strike").sort_index(); p = e[e.cp == "P"].set_index("strike").sort_index()
            ks = c.index.intersection(p.index)
            cd = c.loc[ks].dropna(subset=["delta"])
            if cd.empty:
                continue
            K = (cd.delta - 0.5).abs().idxmin()
            mid = c.loc[K, "mid"] + p.loc[K, "mid"]; ba = c.loc[K, "ba"] + p.loc[K, "ba"]
            if mid < MIN_MID:
                continue
            S_exp = close.get(exp, np.nan)
            if not np.isfinite(S_exp):
                continue
            pay = abs(S_exp - K)
            credit = mid - SLIP * ba - 2 * COMM
            fly = np.nan
            cw = c[(c.index > K) & (c.bid > 0)]; pw = p[(p.index < K) & (p.ask > 0)]
            if not cw.empty and not pw.empty:
                kc = cw.index[np.abs(cw.index - (K + 2 * mid)).argmin()]; kp = pw.index[np.abs(pw.index - (K - 2 * mid)).argmin()]
                fcred = (c.loc[K, "mid"] - SLIP * c.loc[K, "ba"] + p.loc[K, "mid"] - SLIP * p.loc[K, "ba"]
                         - c.loc[kc, "mid"] - SLIP * c.loc[kc, "ba"] - p.loc[kp, "mid"] - SLIP * p.loc[kp, "ba"] - 4 * COMM)
                risk = max(kc - K, K - kp) - fcred
                if fcred > 0 and risk > 0:
                    fpay = min(max(S_exp - K, 0), kc - K) + min(max(K - S_exp, 0), K - kp)
                    fly = (fcred - fpay) / risk * 100
            rows.append(dict(entry=d, h=h, expiry=exp, K=K, mid=mid, ratio=pay / mid,
                             short=(credit - pay) / credit * 100 if credit > 0 else np.nan, fly=fly, vix=vix[d]))
    X = pd.DataFrame(rows).dropna(subset=["short"])
    X = X.join(S[["episode", "direction"]], on="entry")
    X["POST"] = X.episode.notna().astype(int)
    X["DOWN"] = ((X.POST == 1) & (X.direction == "DOWN")).astype(int)
    X["UP"] = ((X.POST == 1) & (X.direction == "UP")).astype(int)
    X["vdec"] = pd.qcut(X.vix, 10, labels=False)
    X["cl"] = np.where(X.POST == 1, "e" + X.episode.fillna(-1).astype(int).astype(str), "d" + X.entry.dt.strftime("%Y%m%d"))
    X["half"] = np.where(X.entry < SPLIT, "2010-2017", "2018-2026")
    ne = int(S.episode.nunique())
    print(f"SPY {close.index.min().date()} -> {close.index.max().date()}: {int(S.shock.sum())} shock days in {ne} episodes "
          f"({int((S.drop_duplicates('episode').direction == 'DOWN').sum())} DOWN)")

    def reg(g, y, terms="POST"):
        g = g.dropna(subset=[y])
        f = smf.ols(f"{y} ~ {terms} + C(vdec)", data=g).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.cl)[0]})
        return f

    out = []
    for h in HORIZONS:
        g = X[X.h == h]
        f = reg(g, "short"); fr = reg(g, "ratio"); fd = reg(g, "short", "DOWN + UP"); ff = reg(g, "fly")
        h1 = reg(g[g.half == "2010-2017"], "short"); h2 = reg(g[g.half == "2018-2026"], "short")
        post = g[g.POST == 1]
        out.append(dict(h=h, n=len(g), post_n=len(post), post_eps=post.episode.nunique(),
                        post_short=post.short.mean(), normal_short=g[g.POST == 0].short.mean(),
                        b_POST=f.params.POST, t_POST=f.tvalues.POST, b_half1=h1.params.POST, t1=h1.tvalues.POST,
                        b_half2=h2.params.POST, t2=h2.tvalues.POST, b_ratio=fr.params.POST, t_ratio=fr.tvalues.POST,
                        b_DOWN=fd.params.DOWN, t_DOWN=fd.tvalues.DOWN, b_UP=fd.params.UP, t_UP=fd.tvalues.UP,
                        post_fly=post.fly.mean(), b_fly=ff.params.POST, t_fly=ff.tvalues.POST))
    R = pd.DataFrame(out)
    print("\n== Short ATM straddle, return on credit at the real fill (%); POST coefficient vs VIX-decile-matched normal days, episode-clustered t ==")
    print(R.round(2).to_string(index=False))
    for _, r in R.iterrows():
        ok = r.b_POST > 0 and r.t_POST >= 3 and r.b_half1 > 0 and r.b_half2 > 0 and r.post_short > 0
        print(f"PASS h={int(r.h)}: {'YES' if ok else 'no'}")

    print("\n== ten worst post-shock episodes (mean short-straddle return across the window's entries, h=5 and h=10) ==")
    P = X[X.POST == 1]
    ep_first = S[S.episode.notna()].groupby("episode").apply(lambda z: (z.index.min().date(), round(float(z.ret.iloc[0]) * 100, 2)))
    W = P[P.h.isin([5, 10])].groupby(["episode", "h"]).short.mean().unstack()
    W["start, first move %"] = ep_first.reindex(W.index).values
    print(W.sort_values(5).head(10).round(1).to_string())

    print("\n== DIAGNOSTIC (not a verdict): weekend, 1-day straddles from gex_spy_straddle_2026-09-21.csv ==")
    D = pd.read_csv("data/studies/gex_spy_straddle_2026-09-21.csv", parse_dates=["day", "entry"])
    D["gap"] = (D.day - D.entry).dt.days
    D["era"] = np.where(D.day >= "2022-06-01", "daily-expiry era", "before")
    print(D[D.gap.isin([1, 3])].groupby(["era", "gap"]).agg(n=("ratio", "size"), realised_over_implied=("ratio", "mean"),
          short_ret_pct=("short_fill", "mean")).round(3).to_string())
    X.to_csv("data/studies/post_shock_vol_premium_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

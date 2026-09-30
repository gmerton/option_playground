#!/usr/bin/env python3
"""Dealer vanna and charm hedging flows on SPY (2026-09-30).

PRE-REGISTERED: data/studies/vanna_charm_flow_2026-09-30.md (committed b967211 before this script existed) -- this
script implements that spec and must not be tuned against its own output.

Inputs: data/cache/spy_chain_v3/<year>.parquet, data/cache/intraday_hist/SPY_1min.parquet,
data/cache/gex/SPY_gex_strikes.parquet (NEG, via run_gex_regime_pin), ^VIX from yfinance.

Usage: PYTHONPATH=src .venv/bin/python3 run_vanna_charm_flow.py > data/studies/logs/vanna_charm_flow.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

from lib.studies.chain_spot import spot_from_chain
from run_gex_regime_pin import daily_bars, gex_series

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
START, END = pd.Timestamp("2010-01-04"), pd.Timestamp("2026-02-27")
SPLIT = pd.Timestamp("2018-01-01")
BAR_T = 3.2


def bs_delta(S, K, sig, T, is_call):
    d1 = (np.log(S / K) + 0.5 * sig ** 2 * T) / (sig * np.sqrt(T))
    return np.where(is_call, norm.cdf(d1), norm.cdf(d1) - 1.0)


def load_chain() -> pd.DataFrame:
    parts = []
    for y in range(2010, 2027):
        c = pd.read_parquet(f"data/cache/spy_chain_v3/{y}.parquet",
                            columns=["trade_date", "expiry", "strike", "cp", "bid_iv", "ask_iv", "delta", "oi"])
        parts.append(c[(c.trade_date >= START - pd.Timedelta(days=10)) & (c.trade_date <= END)])
    c = pd.concat(parts, ignore_index=True)
    c["cp"] = c.cp.astype(str)
    c = c[(c.bid_iv > 0) & (c.ask_iv > 0)].copy()
    c["iv"] = (c.bid_iv + c.ask_iv) / 2.0
    c["dte"] = (c.expiry - c.trade_date).dt.days
    return c


def flows(c: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    """Per chain date t-1: CF (charm $ purchase over to the next session) and VEX ($ purchase per +1 vol pt)."""
    q = c[(c.delta.abs() >= 0.2) & (c.delta.abs() <= 0.8) & (c.dte >= 1)].assign(ticker="SPY")
    spot = spot_from_chain(q).droplevel(0).rename("S")
    nxt = pd.Series(days[1:], index=days[:-1])            # next session for each session
    c = c[(c.dte >= 1) & (c.oi > 0)].join(spot, on="trade_date").dropna(subset=["S"])
    c = c[(c.strike >= 0.8 * c.S) & (c.strike <= 1.2 * c.S)]
    c["n"] = (c.trade_date.map(nxt) - c.trade_date).dt.days
    c = c.dropna(subset=["n"])
    S, K, sig = c.S.values, c.strike.values.astype(float), c.iv.values.astype(float)
    T = np.maximum(c.dte.values, 0.5) / 365.0
    T1 = np.maximum(c.dte.values - c.n.values, 0.5) / 365.0     # time left at t's close (floor 0.5 day)
    is_call = (c.cp == "C").values
    d1 = (np.log(S / K) + 0.5 * sig ** 2 * T) / (sig * np.sqrt(T))
    d2 = d1 - sig * np.sqrt(T)
    vanna = -norm.pdf(d1) * d2 / sig
    charm = bs_delta(S, K, sig, T1, is_call) - bs_delta(S, K, sig, T, is_call)
    pos = np.where(is_call, -1.0, 1.0) * c.oi.values * 100.0      # naive convention: dealers short calls, long puts
    dte = c.dte.values
    c = c.assign(cf=-pos * charm * S, vex=-pos * vanna * 0.01 * S,
                 cf_short=np.where(dte <= 7, -pos * charm * S, 0.0))
    g = c.groupby("trade_date")
    return pd.DataFrame({"CF": g.cf.sum(), "CF_short": g.cf_short.sum(), "VEX": g.vex.sum()})


def third_fridays(days: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Monthly expiry: the 3rd Friday, or the last session on/before it when it is a holiday."""
    out = []
    for m in pd.period_range(days.min(), days.max() + pd.Timedelta(days=40), freq="M"):
        f = pd.date_range(m.start_time, m.end_time, freq="W-FRI")[2]
        on = days[days <= f]
        if len(on) and (f - on[-1]).days < 4:
            out.append(on[-1])
    return pd.DatetimeIndex(sorted(set(out)))


def nw(y, X, lags=5):
    return sm.OLS(y, sm.add_constant(X), missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def wins(s):
    lo, hi = s.quantile([0.01, 0.99]); return s.clip(lo, hi)


def main():
    import yfinance as yf
    v = yf.download("^VIX", start="2009-11-01", end="2026-03-05", progress=False, auto_adjust=False)
    vix = v["Close"].squeeze(); vix.index = pd.to_datetime(vix.index).normalize()

    bars = daily_bars("SPY")
    m = pd.read_parquet("data/cache/intraday_hist/SPY_1min.parquet", columns=["ts", "close", "volume"])
    m = m[(m.ts >= "2009-10-01") & (m.ts < END + pd.Timedelta(days=1))]
    hm = m.ts.dt.hour * 60 + m.ts.dt.minute
    m = m[(hm >= 570) & (hm < 960)]
    dvol = (m.close * m.volume).groupby(m.ts.dt.normalize()).sum()
    adv = dvol.rolling(20).mean().reindex(bars.index)
    _, net, _ = gex_series("SPY", bars)

    days = bars.index
    c = load_chain()
    F = flows(c, days)
    print(f"chain rows used {len(c):,}; flow dates {len(F):,} {F.index.min().date()} -> {F.index.max().date()}")

    d = pd.DataFrame(index=days)
    d["r"] = np.log(bars.close / bars.prev_close) * 1e4
    d["r_oc"] = np.log(bars.close / bars.open) * 1e4
    prev = pd.Series(days, index=days).shift(1)
    P = prev.values
    d["CF"] = F.CF.reindex(P).values / adv.reindex(P).values
    d["CF_short"] = F.CF_short.reindex(P).values / adv.reindex(P).values
    d["VEX"] = F.VEX.reindex(P).values / adv.reindex(P).values
    d["vix_prev"] = vix.reindex(P).values
    d["dvix"] = vix.reindex(days).values - d.vix_prev
    d["NEG"] = (net.reindex(P).values < 0).astype(float)
    d.loc[pd.isna(net.reindex(P).values), "NEG"] = np.nan
    d["r_prev"] = d.r.shift(1)
    # trading days to the monthly expiry (0 = expiry day), clipped at 15
    tf = third_fridays(days)
    pos = np.searchsorted(days, days)
    nxt_opex = np.searchsorted(tf, days)
    tpos = np.searchsorted(days, tf[np.minimum(nxt_opex, len(tf) - 1)])
    d["to_opex"] = np.clip(tpos - pos, 0, 15)
    d["wd"] = days.dayofweek
    d = d[(d.index >= START) & (d.index <= END)].dropna(subset=["r", "CF", "VEX", "vix_prev", "dvix", "NEG", "r_prev"])
    for col in ("CF", "CF_short", "VEX"):
        d[col] = wins(d[col])
    d["VF"] = d.VEX * d.dvix
    d["VF"] = wins(d.VF)
    d["lvix"] = np.log(d.vix_prev)
    d["half"] = np.where(d.index < SPLIT, "2010-2017", "2018-2026")
    d["year"] = d.index.year
    print(f"sessions {len(d):,} {d.index.min().date()} -> {d.index.max().date()}")
    print(d[["CF", "VEX", "VF"]].describe().round(5).to_string())
    print("corr CF with to_opex:", round(d.CF.corr(d.to_opex), 3), " VEX with lvix:", round(d.VEX.corr(d.lvix), 3))

    fe = lambda g: pd.get_dummies(g.to_opex.astype(int), prefix="o", drop_first=True).astype(float).join(
        pd.get_dummies(g.wd, prefix="w", drop_first=True).astype(float))

    def X1(g, flow="CF", with_fe=True):
        X = pd.DataFrame({flow: g[flow], "lvix": g.lvix, "r_prev": g.r_prev, "NEG": g.NEG})
        return X.join(fe(g)) if with_fe else X

    def X2(g):
        return pd.DataFrame({"VF": g.VF, "dvix": g.dvix, "dvix_lvix": g.dvix * g.lvix, "dvix_neg": g.dvix * g.NEG,
                             "lvix": g.lvix, "NEG": g.NEG})

    res = {}
    for name, flow, Xf, y in [("T1 charm", "CF", X1, "r"), ("T2 vanna", "VF", X2, "r")]:
        print(f"\n{'=' * 100}\n{name} (PRIMARY): r_t on {flow}")
        rows = []
        for lab, g in [("full", d)] + list(d.groupby("half")):
            f = nw(g[y], Xf(g))
            rows.append(dict(sample=lab, n=len(g), b=f.params[flow], t=f.tvalues[flow],
                             bps_per_sd=f.params[flow] * g[flow].std()))
        T = pd.DataFrame(rows); print(T.round(4).to_string(index=False))
        yr = []
        for yv, g in d.groupby("year"):
            f = nw(g[y], Xf(g))
            yr.append(dict(year=yv, n=len(g), b=f.params[flow], t=f.tvalues[flow]))
        Y = pd.DataFrame(yr); print(Y.round(4).to_string(index=False))
        full = T.iloc[0]; sgn = np.sign(full.b)
        same_years = int((np.sign(Y.b) == sgn).sum())
        ok = abs(full.t) >= BAR_T and (np.sign(T.iloc[1:].b) == sgn).all() and same_years >= 10
        print(f"-> |t| {abs(full.t):.2f} (bar {BAR_T}), halves same sign {bool((np.sign(T.iloc[1:].b) == sgn).all())}, "
              f"years same sign {same_years}/{len(Y)}  => {'PASS' if ok else 'below bar'}; "
              f"sign {'+ (naive convention: dealers long puts)' if sgn > 0 else '- (consistent with dealers SHORT puts)'}")
        res[name] = dict(t=full.t, b=full.b, bps_sd=full.bps_per_sd, years=same_years, passed=ok)

    print(f"\n{'=' * 100}\nEXPLORATORY (no verdict)")
    g = d
    f = nw(g.r, X1(g, with_fe=False)); print(f"T1 without opex FE: b {f.params.CF:.4f} t {f.tvalues.CF:.2f}")
    f = nw(g.r_oc, X1(g)); print(f"T1 on open->close: b {f.params.CF:.4f} t {f.tvalues.CF:.2f}")
    f = nw(g.r, X1(g, flow="CF_short")); print(f"T1 CF from DTE<=7 only: b {f.params.CF_short:.4f} t {f.tvalues.CF_short:.2f}")
    g2 = d[d.index >= "2022-01-01"]
    f = nw(g2.r, X1(g2)); print(f"T1 2022+: n {len(g2)} b {f.params.CF:.4f} t {f.tvalues.CF:.2f}")
    f = nw(g2.r, X2(g2)); print(f"T2 2022+: n {len(g2)} b {f.params.VF:.4f} t {f.tvalues.VF:.2f}")
    prof = d.groupby("to_opex").agg(n=("r", "size"), mean_r_bps=("r", "mean"), mean_CF=("CF", "mean"))
    prof["t"] = d.groupby("to_opex").r.apply(lambda x: x.mean() / x.std() * np.sqrt(len(x)))
    print("\nopex-cycle profile (trading days to monthly expiry; 0 = expiry day; 15 = 15+):")
    print(prof.round(4).to_string())
    d.to_csv("data/studies/logs/vanna_charm_flow_daily.csv")
    print("\nSUMMARY", res)


if __name__ == "__main__":
    main()

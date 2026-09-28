#!/usr/bin/env python3
"""
Synthetic SPY put legs for 1993-2009 (incl. 2008) -- the stress scenario for step 2 of the structure search
(pre-registered 2026-09-28, before any run).

WHY. The leg surface (spy_leg_surface_2026-09-28.md) shows stress-regime 45-DTE puts with 0/33 losing episodes, but
v3 starts in 2010: every episode in it recovered within ~45 days. No provider we have holds 2008 option chains. We
do have SPY's price path (yfinance raw close 1993->, IBKR 1-min 2007->) and VIX (1990->), so the legs can be priced
synthetically and settled on the real path.

PRE-REGISTRATION (frozen before the first run)
  Legs       PUTS only (calls carry no premium on the surface). Cells = the surface's 8 |delta| x 5 DTE grid.
  IV model   fitted on v3 2010-01 -> 2026-02 surface entries (data/cache/spy_leg_surface_entries.parquet). Entry IV =
             Black-Scholes IV of the MID (inverted here, not the vendor IV), r = 13-week T-bill (^IRX), q = 2.0%.
             Per cell: log(IV / VIX) = a + b x log(VIX)  (skew vs level). Skew scenarios = the cell's residual
             quantiles: LOW q10, CENTRAL q50, HIGH q90 added to the fit.
  Spread     per cell: log(ba / mid) = c + d x log(VIX), central fit; 2008 sensitivity = 2x the spread.
  Strike     solved from the target delta at the cell IV (BS put delta = -e^{-qT} N(-d1)).
  Validation fit on 2010-2017 only, predict 2018-2026 (out of sample): per cell, synthetic vs actual mid (median
             abs % error) and synthetic vs actual mean NET bp, for ALL and STRESS entries. BIAS FACTOR per state =
             sum(actual net bp) / sum(synthetic net bp) over the STRESS 30/45-DTE cells; if < 1 (synthetic too
             generous) the scenario's credits are scaled by it. The scenario itself uses the full 2010-2026 fit.
  Scenario   entries every trading day 1993-02 -> 2009-12; expiry = t + target DTE calendar days, moved back to the
             last trading day on or before it; settle on SPY's actual raw close; P&L = net credit - intrinsic, bp
             of notional. States as on the surface (STRESS = SPY < 50 SMA & VIX >= 20).
             PRIMARY WINDOW 2007-01 -> 2009-12 (the GFC). Extended 1993-2006 is exploratory. 1d/7d/14d tenors did
             not exist before weeklies (2005 SPX, ~2011 SPY): priced as hypothetical legs, flagged.
  Report     per STRESS cell: episodes, episodes negative, mean / worst trade, one-contract-per-expiry cumulative bp
             through the 2008 episode, and its drawdown; the same for 2010-2026 actual for contrast.
  Output     data/cache/spy_synthetic_puts_1993_2009.parquet (scenario matrix for step 2).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_synthetic_stress.py > data/studies/logs/spy_synthetic_stress.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
Q = 0.02
SLIP, COMM = 0.25, 0.0065
DELTAS = [0.05, 0.10, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50]
DTES = [1, 7, 14, 30, 45]


def yf_close(tk, start="1992-06-01"):
    import yfinance as yf
    s = yf.download(tk, start=start, end="2026-05-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def bs_put(S, K, T, r, sig):
    d1 = (np.log(S / K) + (r - Q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    d2 = d1 - sig * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-Q * T) * norm.cdf(-d1)


def implied_vol(P, S, K, T, r):
    lo, hi = np.full_like(P, 0.005), np.full_like(P, 4.0)
    for _ in range(70):
        mid = (lo + hi) / 2
        f = bs_put(S, K, T, r, mid) - P
        hi = np.where(f > 0, mid, hi); lo = np.where(f > 0, lo, mid)
    iv = (lo + hi) / 2
    intrinsic = np.maximum(K * np.exp(-r * T) - S * np.exp(-Q * T), 0)
    return np.where(P > intrinsic + 1e-4, iv, np.nan)


def strike_from_delta(S, T, r, sig, d):
    d1 = -norm.ppf(d * np.exp(Q * T))
    return S * np.exp(-(d1 * sig * np.sqrt(T) - (r - Q + 0.5 * sig ** 2) * T))


def fit(E: pd.DataFrame):
    """per cell: iv ratio fit + residual quantiles, spread fit."""
    out = {}
    for (dt, dc), g in E.groupby(["dtgt", "dcen"]):
        g = g.dropna(subset=["iv", "vix"])
        g = g[(g.iv > 0.01) & (g.mid > 0.01)]
        if len(g) < 100:
            continue
        x = np.log(g.vix / 100); y = np.log(g.iv / (g.vix / 100))
        b, a = np.polyfit(x, y, 1)
        res = y - (a + b * x)
        z = np.log((g.ba / g.mid).clip(lower=1e-3))
        d, c = np.polyfit(x, z, 1)
        out[(dt, dc)] = dict(a=a, b=b, q10=res.quantile(.1), q50=res.quantile(.5), q90=res.quantile(.9), c=c, d=d, n=len(g))
    return out


def synth(S0, vix, r, T, cell, dc, skew="q50", spread_mult=1.0):
    x = np.log(vix / 100)
    sig = (vix / 100) * np.exp(cell["a"] + cell["b"] * x + cell[skew])
    K = strike_from_delta(S0, T, r, sig, dc)
    mid = bs_put(S0, K, T, r, sig)
    ba = mid * np.exp(cell["c"] + cell["d"] * x) * spread_mult
    return K, mid, ba, sig


def episodes(dates: pd.Series, flag: pd.Series) -> pd.Series:
    d = pd.DataFrame(dict(t=dates.values, s=flag.values)).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    ep = np.full(len(d), -1); k = -1; last = -999
    for i, s in enumerate(d.s):
        if s:
            if i - last > 20:
                k += 1
            ep[i] = k; last = i
    return pd.Series(ep, index=d.t)


def main():
    S = yf_close("SPY"); V = yf_close("^VIX", "1990-01-01"); R = yf_close("^IRX", "1990-01-01") / 100
    V, R = V.reindex(S.index).ffill(), R.reindex(S.index).ffill()
    stress = (S < S.rolling(50).mean()) & (V >= 20)

    # ---- calibration data: actual v3 put entries
    E = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    E = E[E.cp == "P"].copy()
    E["T"] = E.dte / 365.0
    E["r"] = R.reindex(E.trade_date).values
    E["vix"] = V.reindex(E.trade_date).values
    E["iv"] = implied_vol(E.mid.values, E.S_0.values, E.strike.values, E["T"].values, E.r.values)
    print(f"calibration entries {len(E):,}, IV solved {E.iv.notna().mean():.1%}")

    # ---- out-of-sample validation: fit 2010-2017, predict 2018-2026
    fit_a = fit(E[E.trade_date < "2018-01-01"])
    Vd = E[E.trade_date >= "2018-01-01"].copy()
    vrows = []
    for (dt, dc), g in Vd.groupby(["dtgt", "dcen"]):
        if (dt, dc) not in fit_a:
            continue
        g = g.dropna(subset=["vix", "r"])
        K, mid, ba, _ = synth(g.S_0.values, g.vix.values, g.r.values, g["T"].values, fit_a[(dt, dc)], dc)
        pay = np.maximum(K - g.S_T.values, 0)
        bp_syn = (mid - SLIP * ba - COMM - pay) / g.S_0.values * 1e4
        for st, m in (("ALL", np.ones(len(g), bool)), ("STRESS", g.stress.values)):
            if m.sum() < 20:
                continue
            vrows.append(dict(state=st, dte=dt, delta=dc, n=int(m.sum()),
                              mid_err_med=np.median(np.abs(mid[m] / g.mid.values[m] - 1)),
                              credit_ratio=np.median(mid[m] / g.mid.values[m]),
                              actual_bp=g.bp_n.values[m].mean(), synth_bp=bp_syn[m].mean()))
    VT = pd.DataFrame(vrows)
    print("\n== OUT-OF-SAMPLE VALIDATION (fit 2010-17, predict 2018-26): synthetic vs actual ==")
    print(VT.round(3).to_string(index=False))
    sel = VT[(VT.state == "STRESS") & VT.dte.isin([30, 45])]
    w = sel.n
    bias = (sel.actual_bp * w).sum() / (sel.synth_bp * w).sum()
    selA = VT[(VT.state == "ALL")]
    biasA = (selA.actual_bp * selA.n).sum() / (selA.synth_bp * selA.n).sum()
    print(f"\nBIAS FACTOR (actual / synthetic net bp): STRESS 30/45-DTE {bias:.3f} | ALL cells {biasA:.3f}")
    scale = min(1.0, bias)
    print(f"scenario credit scale applied (pre-registered: only if < 1): {scale:.3f}")

    # ---- scenario 1993-2009 with the full 2010-2026 fit
    fit_f = fit(E)
    days = S.index[(S.index >= "1993-02-01") & (S.index <= "2009-12-31")]
    rows = []
    for dt in DTES:
        exp_cal = days + pd.Timedelta(days=dt)
        ei = S.index.searchsorted(exp_cal, side="right") - 1
        if dt == 1:   # fixed after the first run: Fri + 1 calendar day rolled back to Fri (same-day settle). Use next session.
            ei = S.index.searchsorted(days, side="right")
        ok = ei < len(S)
        T = np.full(len(days), dt / 365.0)
        for dc in DELTAS:
            cell = fit_f.get((dt, dc))
            if cell is None:
                continue
            for skew in ("q10", "q50", "q90"):
                for sm in ((1.0, 2.0) if skew == "q50" else (1.0,)):
                    K, mid, ba, sig = synth(S.loc[days].values, V.loc[days].values, R.loc[days].values, T, cell, dc, skew, sm)
                    ST = S.values[ei]
                    credit = scale * mid - SLIP * ba - COMM
                    bp = (credit - np.maximum(K - ST, 0)) / S.loc[days].values * 1e4
                    rows.append(pd.DataFrame(dict(trade_date=days, expiry=S.index[ei], dtgt=dt, dcen=dc, skew=skew,
                                                  spread_mult=sm, K=K, S_0=S.loc[days].values, S_T=ST, iv=sig, mid=mid,
                                                  bp_n=bp, stress=stress.loc[days].values)))
    X = pd.concat(rows, ignore_index=True)
    X.to_parquet("data/cache/spy_synthetic_puts_1993_2009.parquet", index=False)
    ep = episodes(X.trade_date, X.stress)
    X["ep"] = X.trade_date.map(ep)

    def report(Y, label):
        out = []
        for (dt, dc), g in Y.groupby(["dtgt", "dcen"]):
            # one contract per WEEK, entered on Fridays (the certified strategy's cadence); synthetic expiries are
            # daily, so "one per expiry" would stack ~5 overlapping positions a week (fixed after the first run)
            u = g[g.trade_date.dt.dayofweek == 4].sort_values("trade_date")
            s = u[u.stress]
            if len(s) < 5:
                continue
            e = s.groupby("ep").bp_n.sum()
            cum = s.bp_n.cumsum()
            out.append(dict(window=label, dte=dt, delta=dc, stress_trades=len(s), episodes=len(e), episodes_neg=int((e < 0).sum()),
                            mean_bp=s.bp_n.mean(), lose_pct=100 * (s.bp_n < 0).mean(), worst_trade=s.bp_n.min(), worst_episode=e.min(),
                            cum_bp=cum.iloc[-1], max_dd=(cum - cum.cummax()).min(), all_mean_bp=u.bp_n.mean()))
        return pd.DataFrame(out)

    C = X[(X["skew"] == "q50") & (X.spread_mult == 1.0)]
    print(f"\nscenario rows {len(X):,}; stress episodes 1993-2009: {int(ep.max()) + 1}")
    for lab, lo, hi in (("GFC 2007-09 (PRIMARY)", "2007-01-01", "2009-12-31"), ("1993-2006 (explor.)", "1993-01-01", "2006-12-31")):
        Y = C[(C.trade_date >= lo) & (C.trade_date <= hi)]
        print(f"\n== {lab}: STRESS-regime puts, one contract per expiry, CENTRAL skew, 1x spread (bp of notional) ==")
        print(report(Y, lab).round({"mean_bp":1,"lose_pct":0,"worst_trade":0,"worst_episode":0,"cum_bp":0,"max_dd":0,"all_mean_bp":1}).to_string(index=False))
    print("\n== GFC sensitivity: STRESS 30/45-DTE puts, cumulative bp and worst episode by skew / spread scenario ==")
    G = X[(X.trade_date >= "2007-01-01") & X.dtgt.isin([30, 45])]
    sens = []
    for (sk, sm), g in G.groupby(["skew", "spread_mult"]):
        r = report(g, f"{sk} x{sm:g}")
        sens.append(r)
    print(pd.concat(sens).round({"mean_bp":1,"worst_trade":0,"worst_episode":0,"cum_bp":0,"max_dd":0})[["window", "dte", "delta", "episodes_neg", "mean_bp", "worst_trade", "worst_episode", "cum_bp", "max_dd"]].to_string(index=False))
    A = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    A = A[(A.cp == "P") & (A.trade_date.dt.dayofweek == 4)].copy()
    A["ep"] = A.trade_date.map(episodes(A.trade_date, A.stress))
    print("\n== CONTRAST: ACTUAL v3 2010-2026, same weekly cadence, STRESS-regime puts ==")
    print(report(A, "v3 2010-26").round({"mean_bp":1,"lose_pct":0,"worst_trade":0,"worst_episode":0,"cum_bp":0,"max_dd":0,"all_mean_bp":1}).to_string(index=False))
    print("\n== The 2008 path: STRESS 45-DTE 10-delta put, CENTRAL, per expiry month (2008-06 -> 2009-06) ==")
    p = C[(C.dtgt == 45) & (C.dcen == 0.10) & C.stress & (C.trade_date >= "2008-06-01") & (C.trade_date <= "2009-06-30")]
    p = p[p.trade_date.dt.dayofweek == 4].sort_values("trade_date")
    print(p.groupby(p.trade_date.dt.to_period("M")).agg(trades=("bp_n", "size"), mean_bp=("bp_n", "mean"), worst=("bp_n", "min"),
                                                        sum_bp=("bp_n", "sum"), iv=("iv", "mean"), S0=("S_0", "mean")).round(1).to_string())


if __name__ == "__main__":
    main()

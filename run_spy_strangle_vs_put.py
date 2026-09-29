#!/usr/bin/env python3
"""
SPY 45-DTE 16-delta STRANGLE vs the 16-delta SHORT PUT vs the DELTA-HEDGED put, 1993-2026 incl. 2000-02 and 2008
(pre-registered 2026-09-28, committed before any run).

WHY. The short put's P&L is 60-80% beta (stress_put_delta_control.log) and the stress rebound that carries it failed
1990-2009 (stress_rebound_2026-09-28.md). Short calls lose raw money on SPY but beat a delta-matched short-stock
position (long_call_vs_stock_check.log), i.e. they carry a vol premium and pay for being short the drift. A 16-delta
strangle is roughly delta-neutral: it collects both premiums without depending on the drift or the rebound. Question:
is it the more ROBUST structure across eras, per unit of tail? (Sosnoff's 45-DTE ~16-20 delta SPY strangle.)

PRE-REGISTRATION
  Entries   every Friday; 45-DTE 16-delta legs (the leg-surface cell: expiry nearest 45 in [40, 50], |delta| nearest
            0.16 +/- 0.025); hold to expiry; house fills (mid - 25% bid-ask - $0.0065/share/leg; no exit cost at expiry).
  Arms      PUT       short 16-delta put
            STRANGLE  short 16-delta put + short 16-delta call, SAME expiry (Fridays without both legs dropped)
            HEDGED    short 16-delta put + short |put delta| SPY shares at entry, closed at expiry (static hedge;
                      carry: short earns r, pays q = 1.8%; 1 bp cost each way on the shares)
  Data      2010-01 -> 2026-02: v3 actual (data/cache/spy_leg_surface_entries.parquet).
            1993-02 -> 2009-12: SYNTHETIC. The put leg = the stress scenario's model (run_spy_synthetic_stress.py
            form); the call leg = the SAME method fitted on v3 45-DTE 16-delta CALLS: log(IV/VIX) = a + b log VIX,
            strike from the call delta, BS pricing, q = 1.8%, r = T-bill, spread model log(ba/mid) on log VIX.
            VALIDATION (per leg): fit 2010-17, predict 2018-26, report median |mid error| and the credit ratio;
            BIAS FACTOR per leg = sum(actual net bp) / sum(synthetic net bp) over 2018-26; applied to that leg's
            synthetic credit only if < 1.
  Units     bp of SPY notional per unit (one contract per leg); monthly P&L = sum of that month's Friday entries.
  Scaling   each arm scaled to the same monthly CVaR_5% over 1993-2026 (a comparison normalisation, not a trading
            rule -- it uses the full sample).
  PRIMARY   STRANGLE - PUT, paired monthly P&L at equal CVaR, t over months; STRANGLE is BETTER iff t >= 3 AND the
            1993-2009 (synthetic) and 2010-2026 (actual) halves are both positive. WORSE iff t <= -3 with both halves
            negative. Otherwise EQUIVALENT.
  Secondary HEDGED - PUT, same rule. Era table (1993-99, 2000-02, 2003-06, 2007-09, 2010-19, 2020-26): mean, worst
            month, max drawdown per arm; mean / CVaR per arm; share of P&L from beta.
  Caveats   1993-2009 is synthetic (model risk concentrated exactly in the crises); the static hedge is not
            re-balanced; SPY is American (early assignment ignored).

CORRECTION after the first run (disclosed): the registered bias rule divides net bp, which fails when both nets are
negative (the call leg); credits are now scaled by 1 / median credit ratio. As-registered log kept:
logs/spy_strangle_vs_put_as_registered.log.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_strangle_vs_put.py > data/studies/logs/spy_strangle_vs_put.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
Q, SLIP, COMM, DT, DC = 0.018, 0.25, 0.0065, 45, 0.16


def yf_close(tk, start="1992-06-01"):
    import yfinance as yf
    s = yf.download(tk, start=start, end="2026-05-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def bs(S, K, T, r, sig, cp):
    d1 = (np.log(S / K) + (r - Q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T)); d2 = d1 - sig * np.sqrt(T)
    if cp == "C":
        return S * np.exp(-Q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-Q * T) * norm.cdf(-d1)


def ivol(P, S, K, T, r, cp):
    lo, hi = np.full_like(P, 0.005), np.full_like(P, 4.0)
    for _ in range(70):
        m = (lo + hi) / 2; f = bs(S, K, T, r, m, cp) - P
        hi = np.where(f > 0, m, hi); lo = np.where(f > 0, lo, m)
    return (lo + hi) / 2


def strike(S, T, r, sig, d, cp):
    d1 = norm.ppf(d * np.exp(Q * T)) if cp == "C" else -norm.ppf(d * np.exp(Q * T))
    return S * np.exp(-(d1 * sig * np.sqrt(T) - (r - Q + 0.5 * sig ** 2) * T))


def fit(E):
    x = np.log(E.vix / 100); y = np.log(E.iv / (E.vix / 100)); b, a = np.polyfit(x, y, 1)
    z = np.log((E.ba / E.mid).clip(lower=1e-3)); d, c = np.polyfit(x, z, 1)
    return dict(a=a, b=b, c=c, d=d)


def synth(S0, vix, r, T, f, cp, scale=1.0):
    x = np.log(vix / 100); sig = (vix / 100) * np.exp(f["a"] + f["b"] * x)
    K = strike(S0, T, r, sig, DC, cp); mid = bs(S0, K, T, r, sig, cp); ba = mid * np.exp(f["c"] + f["d"] * x)
    return K, scale * mid - SLIP * ba - COMM


def cvar(x, a=0.05):
    x = np.sort(np.asarray(x)); k = max(1, int(np.ceil(a * len(x)))); return -x[:k].mean()


def main():
    S = yf_close("SPY"); V = yf_close("^VIX", "1990-01-01").reindex(S.index).ffill()
    R = (yf_close("^IRX", "1990-01-01") / 100).reindex(S.index).ffill()
    A = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    A = A[(A.dtgt == DT) & (A.dcen == DC)].copy()
    A["T"] = A.dte / 365; A["r"] = R.reindex(A.trade_date).values; A["vix"] = V.reindex(A.trade_date).values
    A["iv"] = np.nan
    for cp in ("P", "C"):
        m = A.cp == cp
        A.loc[m, "iv"] = ivol(A[m].mid.values, A[m].S_0.values, A[m].strike.values, A[m]["T"].values, A[m].r.values, cp)
    A = A[(A.iv > 0.01) & (A.iv < 3.9)]
    # ---- validation + bias per leg
    fits, scale = {}, {}
    print("== VALIDATION (fit 2010-17, predict 2018-26), 45-DTE 16-delta legs ==")
    for cp in ("P", "C"):
        a = A[A.cp == cp]
        fa = fit(a[a.trade_date < "2018-01-01"]); v = a[a.trade_date >= "2018-01-01"]
        K, cr = synth(v.S_0.values, v.vix.values, v.r.values, v["T"].values, fa, cp)
        mid_syn = bs(v.S_0.values, K, v["T"].values, v.r.values,
                     (v.vix.values / 100) * np.exp(fa["a"] + fa["b"] * np.log(v.vix.values / 100)), cp)
        pay = np.maximum(K - v.S_T.values, 0) if cp == "P" else np.maximum(v.S_T.values - K, 0)
        bp_syn = (cr - pay) / v.S_0.values * 1e4
        b = v.bp_n.sum() / bp_syn.sum()
        # CORRECTION (after the first run, disclosed): the registered net-bp ratio is meaningless when both nets are
        # negative (calls: -1.97 vs -3.86 -> 0.512 cut the synthetic call CREDIT in half although the synthetic was
        # too PESSIMISTIC). Scale credits by 1 / median credit ratio instead (the level error of the IV model).
        cr_ratio = np.median(mid_syn / v.mid.values)
        scale[cp] = 1.0 / cr_ratio
        print(f"  {cp}: median |mid err| {np.median(np.abs(mid_syn / v.mid.values - 1)):.1%}, credit ratio {np.median(mid_syn / v.mid.values):.3f}, "
              f"actual net {v.bp_n.mean():+.2f} bp vs synthetic {bp_syn.mean():+.2f} -> registered bias {b:.3f} (NOT used), credit scale applied {scale[cp]:.3f}")
        fits[cp] = fit(a)
    # ---- weekly legs: actual 2010-26
    F = A[A.trade_date.dt.dayofweek == 4]
    P = F[F.cp == "P"].set_index("trade_date"); Cc = F[F.cp == "C"].set_index("trade_date")
    rows = []
    for d in P.index:
        p = P.loc[d]
        if isinstance(p, pd.DataFrame):
            p = p.iloc[0]
        rec = dict(date=d, src="v3", put=p.bp_n, S0=p.S_0, ST=p.S_T, dput=abs(p.delta), exp=p.expiry)
        if d in Cc.index:
            c = Cc.loc[d]
            if isinstance(c, pd.DataFrame):
                c = c.iloc[0]
            if c.expiry == p.expiry:
                rec["call"] = c.bp_n
        rows.append(rec)
    # ---- synthetic 1993-2009
    fr = [d for d in S.index if d.dayofweek == 4 and pd.Timestamp("1993-02-01") <= d <= pd.Timestamp("2009-12-31")]
    for d in fr:
        ex = d + pd.Timedelta(days=DT); ei = S.index.searchsorted(ex, side="right") - 1; ST = S.iloc[ei]
        S0, v, r = S[d], V[d], R[d]; T = DT / 365
        Kp, crp = synth(S0, v, r, T, fits["P"], "P", scale["P"]); Kc, crc = synth(S0, v, r, T, fits["C"], "C", scale["C"])
        sigp = (v / 100) * np.exp(fits["P"]["a"] + fits["P"]["b"] * np.log(v / 100))
        d1 = (np.log(S0 / Kp) + (r - Q + 0.5 * sigp ** 2) * T) / (sigp * np.sqrt(T))
        rows.append(dict(date=d, src="synthetic", put=(crp - max(Kp - ST, 0)) / S0 * 1e4, call=(crc - max(ST - Kc, 0)) / S0 * 1e4,
                         S0=S0, ST=ST, dput=np.exp(-Q * T) * norm.cdf(-d1), exp=S.index[ei]))
    X = pd.DataFrame(rows).sort_values("date")
    X["r"] = R.reindex(X.date).values
    T_ = (pd.to_datetime(X.exp) - X.date).dt.days / 365
    X["hedge"] = -X.dput * ((X.ST - X.S0) / X.S0 + (Q - X.r) * T_) * 1e4 - 2 * X.dput * 1.0
    X = X.dropna(subset=["put", "call"])
    X["PUT"] = X.put; X["STRANGLE"] = X.put + X.call; X["HEDGED"] = X.put + X.hedge
    X["beta"] = X.dput * (X.ST - X.S0) / X.S0 * 1e4
    M = X.groupby(X.date.dt.to_period("M"))[["PUT", "STRANGLE", "HEDGED", "beta", "call"]].sum()
    print(f"\nFridays with both legs: {len(X)} ({(X.src == 'synthetic').sum()} synthetic 1993-2009, {(X.src == 'v3').sum()} v3 2010-26); months {len(M)}")
    arms = ["PUT", "STRANGLE", "HEDGED"]
    k = {a: 100.0 / cvar(M[a].values) for a in arms}
    Z = pd.DataFrame({a: M[a] * k[a] for a in arms})
    print("scale to monthly CVaR_5% = 100 bp:", {a: round(v, 3) for a, v in k.items()})
    eras = [("1993-99", 1993, 1999), ("2000-02", 2000, 2002), ("2003-06", 2003, 2006), ("2007-09", 2007, 2009),
            ("2010-19", 2010, 2019), ("2020-26", 2020, 2026), ("ALL", 1993, 2026)]
    out = []
    for lab, a0, a1 in eras:
        z = Z[(Z.index.year >= a0) & (Z.index.year <= a1)]
        for a in arms:
            c = z[a].cumsum()
            out.append(dict(era=lab, arm=a, months=len(z), mean_bp=z[a].mean(), worst_month=z[a].min(),
                            max_dd=(c - c.cummax()).min(), mean_over_cvar=z[a].mean() / max(cvar(z[a].values), 1e-9)))
    print("\n== per era, each arm at equal full-sample CVaR (monthly bp) ==")
    print(pd.DataFrame(out).pivot(index="era", columns="arm", values="mean_bp").round(2).to_string())
    print(pd.DataFrame(out).pivot(index="era", columns="arm", values="max_dd").round(0).to_string())
    print(pd.DataFrame(out).pivot(index="era", columns="arm", values="worst_month").round(0).to_string())
    raw = X.groupby(X.src)[["PUT", "call", "STRANGLE", "HEDGED", "beta"]].mean()
    print("\nraw mean bp per Friday entry (unscaled), and the put's beta component:"); print(raw.round(2).to_string())
    for a, bname in (("STRANGLE", "PRIMARY"), ("HEDGED", "SECONDARY")):
        dd = Z[a] - Z["PUT"]; t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
        h1, h2 = dd[dd.index.year <= 2009].mean(), dd[dd.index.year >= 2010].mean()
        v = "BETTER" if (t >= 3 and h1 > 0 and h2 > 0) else ("WORSE" if (t <= -3 and h1 < 0 and h2 < 0) else "EQUIVALENT")
        print(f"{bname} {a} - PUT at equal CVaR: {dd.mean():+.2f} bp/month, t {t:+.2f}, halves 1993-09 {h1:+.2f} / 2010-26 {h2:+.2f} -> {v}")
    X.to_csv("data/studies/logs/spy_strangle_vs_put_entries.csv", index=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Stress-bucket VEHICLE head-to-head: the certified bull put vertical vs a naked 30-DTE low-delta put, judged on the
premium BEYOND BETA per $ of risk capital, on the same stress Fridays (pre-registered 2026-09-28, before any run).

WHY. The delta-matched control (stress_put_delta_control.log) found 60-80% of stress short-put P&L is beta; the
premium beyond beta clears |t| >= 3 only for naked 30-DTE low-delta puts (5-delta t 4.15, 10-delta t 3.10). The
certified vehicle (20 DTE 0.25/0.15 vertical, 50% take) is not on that grid and has never had the control.

PRE-REGISTRATION (frozen before the first run)
  Days      Fridays 2010-01 -> 2026-02 in the STRESS regime (SPY close < 50 SMA AND VIX >= 20), v3 EOD quotes
            (data/cache/spy_chain_v3/). Both arms must exist on a Friday for the PAIRED comparison.
  CERT      expiry nearest 20 DTE in [15, 25]; short put |delta| nearest 0.25 (+/-0.03), long put nearest 0.15
            (+/-0.03), same expiry. Close at the first daily close where the cost to close <= 50% of the entry credit
            (take-profit); else hold to expiry. No stop. House fills: open = sell short at mid - 25% ba, buy long at
            mid + 25% ba, $0.0065/share/leg; close = the reverse on that day's quotes (no exit cost at expiry).
  NAKED10   expiry nearest 30 DTE in [25, 35], short put |delta| nearest 0.10 (+/-0.025), hold to expiry.
  NAKED05   same at 0.05 (+/-0.015). (secondary)
  Capital   CERT: width - net credit (max loss). NAKED: Reg-T naked put = premium + max(20% x S - OTM amount, 10% x K).
            Return on capital (RoC, %) = net P&L / capital.
  Beta      control P&L = position delta at entry (|short delta| - |long delta| for CERT) x SPY return from entry to
            the arm's own exit date, + delta x (q - r) x holding time (q = 1.8%, r = 13-week T-bill); expressed per
            $ of the same capital. EXCESS RoC = RoC - control RoC.
  Episodes  stress Fridays more than 31 days apart start a new episode; SEs cluster by episode.
  PRIMARY   paired NAKED10 - CERT excess RoC on the same Fridays, episode-clustered t. SWITCH the vehicle only if
            t >= 3, both halves (split 2018-01-01) positive, AND the 2008 test passes. Otherwise the certified
            vehicle stays. Secondary: NAKED05 - CERT; each arm's own excess RoC.
  2008 test synthetic 2007-01 -> 2009-12 stress Fridays (IV model = run_spy_synthetic_stress.py's form, fitted here
            on these exact v3 legs, credits x 0.888, hold to expiry for BOTH arms because synthetic mid-life marks
            are not modelled): NAKED passes iff its mean RoC >= CERT's mean RoC over those Fridays.
  Caveats   Reg-T is a broker-dependent proxy (portfolio margin would favour the naked put); ~30 stress episodes.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_stress_vehicle_h2h.py > data/studies/logs/stress_vehicle_h2h.log
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
CH = Path("data/cache/spy_chain_v3")
SLIP, COMM, Q, SCALE = 0.25, 0.0065, 0.018, 0.888
SPLIT = pd.Timestamp("2018-01-01")


def yf_close(tk, start="1992-06-01"):
    import yfinance as yf
    s = yf.download(tk, start=start, end="2026-05-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def pick(g: pd.DataFrame, target: float, tol: float):
    x = g[(g.ad - target).abs() <= tol]
    return None if x.empty else x.loc[(x.ad - target).abs().idxmin()]


def bs_put(S, K, T, r, sig):
    d1 = (np.log(S / K) + (r - Q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T)); d2 = d1 - sig * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-Q * T) * norm.cdf(-d1)


def ivol(P, S, K, T, r):
    lo, hi = np.full_like(P, 0.005), np.full_like(P, 4.0)
    for _ in range(70):
        m = (lo + hi) / 2; f = bs_put(S, K, T, r, m) - P
        hi = np.where(f > 0, m, hi); lo = np.where(f > 0, lo, m)
    return (lo + hi) / 2


def regt(S, K, prem):
    return prem + np.maximum(0.20 * S - np.maximum(S - K, 0), 0.10 * K)


def main():
    S = yf_close("SPY"); V = yf_close("^VIX", "1990-01-01").reindex(S.index).ffill()
    R = (yf_close("^IRX", "1990-01-01") / 100).reindex(S.index).ffill()
    stress = (S < S.rolling(50).mean()) & (V >= 20)
    fridays = [d for d in S.index if d.dayofweek == 4 and stress.get(d, False) and pd.Timestamp("2010-01-01") <= d <= pd.Timestamp("2026-02-20")]
    fr = set(fridays)

    chain = pd.concat([pd.read_parquet(f, columns=["trade_date", "expiry", "strike", "cp", "bid", "ask", "delta"])
                       for f in sorted(CH.glob("*.parquet"))])
    chain = chain[chain.cp == "P"]
    chain["dte"] = (chain.expiry - chain.trade_date).dt.days
    chain["ad"] = chain.delta.abs()
    E = chain[chain.trade_date.isin(fr) & (chain.bid > 0) & (chain.ask >= chain.bid)]
    rows, legs = [], []
    for d, g in E.groupby("trade_date"):
        S0 = S[d]; r0 = R[d]
        out = dict(date=d, S0=S0, r=r0)
        # CERT
        c = g[(g.dte >= 15) & (g.dte <= 25)]
        if not c.empty:
            ex = c.loc[(c.dte - 20).abs().idxmin(), "expiry"]; c = c[c.expiry == ex]
            sh, lg = pick(c, 0.25, 0.03), pick(c, 0.15, 0.03)
            if sh is not None and lg is not None and sh.strike > lg.strike:
                out["cert"] = dict(expiry=ex, Ks=sh.strike, Kl=lg.strike, ds=sh.ad, dl=lg.ad,
                                   credit=(sh.bid + sh.ask) / 2 - SLIP * (sh.ask - sh.bid) - (lg.bid + lg.ask) / 2 - SLIP * (lg.ask - lg.bid) - 2 * COMM,
                                   mids=(sh.bid + sh.ask) / 2, midl=(lg.bid + lg.ask) / 2)
                legs += [(ex, sh.strike), (ex, lg.strike)]
        for name, tgt, tol in (("n10", 0.10, 0.025), ("n05", 0.05, 0.015)):
            n = g[(g.dte >= 25) & (g.dte <= 35)]
            if n.empty:
                continue
            ex = n.loc[(n.dte - 30).abs().idxmin(), "expiry"]; n = n[n.expiry == ex]
            p = pick(n, tgt, tol)
            if p is not None:
                mid = (p.bid + p.ask) / 2
                out[name] = dict(expiry=ex, K=p.strike, d=p.ad, mid=mid, credit=mid - SLIP * (p.ask - p.bid) - COMM)
        rows.append(out)
    # path marks for CERT legs
    key = pd.DataFrame(legs, columns=["expiry", "strike"]).drop_duplicates()
    M = chain.merge(key, on=["expiry", "strike"])[["trade_date", "expiry", "strike", "bid", "ask"]]
    M = M.set_index(["expiry", "strike", "trade_date"]).sort_index()

    def settle(ex):
        i = S.index.searchsorted(ex, side="right") - 1
        return S.index[i], S.iloc[i]

    res = []
    for o in rows:
        d, S0, r0 = o["date"], o["S0"], o["r"]
        rec = dict(date=d)
        if "cert" in o:
            c = o["cert"]; w = c["Ks"] - c["Kl"]; cap = w - c["credit"]
            exit_d, pnl = None, None
            try:
                ms = M.loc[(c["expiry"], c["Ks"])]; ml = M.loc[(c["expiry"], c["Kl"])]
                j = ms.join(ml, lsuffix="_s", rsuffix="_l", how="inner")
                j = j[(j.index > d) & (j.index < c["expiry"])]
                close_cost = ((j.bid_s + j.ask_s) / 2 + SLIP * (j.ask_s - j.bid_s) - (j.bid_l + j.ask_l) / 2 + SLIP * (j.ask_l - j.bid_l) + 2 * COMM)
                hit = close_cost[close_cost <= 0.5 * c["credit"]]
                if len(hit):
                    exit_d = hit.index[0]; pnl = c["credit"] - hit.iloc[0]; S1 = S[exit_d]
            except KeyError:
                pass
            if exit_d is None:
                exit_d, S1 = settle(c["expiry"])
                pnl = c["credit"] - (max(c["Ks"] - S1, 0) - max(c["Kl"] - S1, 0))
            T = max((exit_d - d).days, 1) / 365
            delta = c["ds"] - c["dl"]
            ctrl = delta * ((S1 - S0) + S0 * (Q - r0) * T)
            if cap > 0:
                rec.update(cert_roc=pnl / cap * 100, cert_ctrl=ctrl / cap * 100, cert_take=exit_d < c["expiry"])
        for name in ("n10", "n05"):
            if name in o:
                n = o[name]; ex_d, S1 = settle(n["expiry"])
                pnl = n["credit"] - max(n["K"] - S1, 0)
                cap = regt(S0, n["K"], n["mid"])
                T = max((ex_d - d).days, 1) / 365
                ctrl = n["d"] * ((S1 - S0) + S0 * (Q - r0) * T)
                rec.update({f"{name}_roc": pnl / cap * 100, f"{name}_ctrl": ctrl / cap * 100})
        res.append(rec)
    X = pd.DataFrame(res).sort_values("date").reset_index(drop=True)
    gap = X.date.diff().dt.days.fillna(0) > 31
    X["ep"] = gap.cumsum()
    for a in ("cert", "n10", "n05"):
        X[f"{a}_ex"] = X[f"{a}_roc"] - X[f"{a}_ctrl"]

    def ct(x, g):
        df = pd.DataFrame(dict(x=x.values, g=g.values)).dropna()
        mu = df.x.mean(); s = df.groupby("g").x.sum(); n = df.groupby("g").size()
        se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
        return mu, mu / se, len(df), df.g.nunique()

    print(f"stress Fridays {len(X)}, episodes {X.ep.nunique()}, CERT take-profit share {X.cert_take.mean():.0%}")
    stats = []
    for a in ("cert", "n10", "n05"):
        for col, lab in ((f"{a}_roc", "RoC"), (f"{a}_ctrl", "beta RoC"), (f"{a}_ex", "EXCESS RoC")):
            mu, t, n, ne = ct(X[col], X.ep)
            stats.append(dict(arm=a, metric=lab, n=n, episodes=ne, mean_pct=mu, t=t,
                             h1=X[X.date < SPLIT][col].mean(), h2=X[X.date >= SPLIT][col].mean(), worst=X[col].min()))
    print(pd.DataFrame(stats).round(3).to_string(index=False))
    verdicts = {}
    for a in ("n10", "n05"):
        P = X.dropna(subset=[f"{a}_ex", "cert_ex"])
        dlt = P[f"{a}_ex"] - P["cert_ex"]
        mu, t, n, ne = ct(dlt, P.ep)
        h1, h2 = dlt[P.date < SPLIT].mean(), dlt[P.date >= SPLIT].mean()
        verdicts[a] = (mu, t, h1, h2)
        print(f"\nPAIRED {a.upper()} - CERT excess RoC: {mu:+.3f} pp/trade, t {t:+.2f}, n {n}, episodes {ne}, halves {h1:+.3f} / {h2:+.3f}")
        yr = pd.DataFrame(dict(d=dlt.values, y=P.date.dt.year.values)).groupby("y").d.agg(["mean", "size"])
        print(yr.round(2).T.to_string())

    # ---- 2008 test (synthetic, hold to expiry, both arms)
    cells = {"cs": ("cert", "Ks", "ds", 20), "cl": ("cert", "Kl", "dl", 20), "n10": ("n10", "K", "d", 30), "n05": ("n05", "K", "d", 30)}
    fit = {}
    for key_, (arm, kcol, dcol, dte_t) in cells.items():
        pts = []
        for o in rows:
            if arm in o:
                a = o[arm]; K = a[kcol]; ex = a["expiry"]
                mid = a["mids"] if key_ == "cs" else (a["midl"] if key_ == "cl" else a["mid"])
                T = max((ex - o["date"]).days, 1) / 365
                pts.append((o["date"], o["S0"], K, T, o["r"], mid, V[o["date"]], a[dcol]))
        P = pd.DataFrame(pts, columns=["d", "S", "K", "T", "r", "mid", "vix", "delta"])
        P["iv"] = ivol(P.mid.values, P.S.values, P.K.values, P["T"].values, P.r.values)
        P = P[(P.iv > 0.01) & (P.iv < 3.9)]
        x = np.log(P.vix / 100); y = np.log(P.iv / (P.vix / 100))
        b, a0 = np.polyfit(x, y, 1)
        fit[key_] = (a0, b, P.delta.median(), dte_t)
    gd = [d for d in S.index if d.dayofweek == 4 and stress.get(d, False) and pd.Timestamp("2007-01-01") <= d <= pd.Timestamp("2009-12-31")]

    def synth(d, key_):
        a0, b, dl, dte_t = fit[key_]
        S0, r0, v = S[d], R[d], V[d]
        sig = (v / 100) * np.exp(a0 + b * np.log(v / 100)); T = dte_t / 365
        d1 = -norm.ppf(dl * np.exp(Q * T)); K = S0 * np.exp(-(d1 * sig * np.sqrt(T) - (r0 - Q + 0.5 * sig ** 2) * T))
        return K, bs_put(S0, K, T, r0, sig) * SCALE

    syn = []
    for d in gd:
        ex = d + pd.Timedelta(days=20); _, S20 = settle(ex)
        Ks, ms = synth(d, "cs"); Kl, ml = synth(d, "cl")
        cr = ms - ml - 2 * COMM - SLIP * 0.03 * (ms + ml)          # spread cost proxy: 3% of mid per leg
        pnl = cr - (max(Ks - S20, 0) - max(Kl - S20, 0)); cap = (Ks - Kl) - cr
        r = dict(date=d, cert=pnl / cap * 100 if cap > 0 else np.nan)
        ex = d + pd.Timedelta(days=30); _, S30 = settle(ex)
        for key_ in ("n10", "n05"):
            K, m = synth(d, key_)
            r[key_] = (m - SLIP * 0.03 * m - COMM - max(K - S30, 0)) / regt(S[d], K, m) * 100
        syn.append(r)
    Y = pd.DataFrame(syn)
    print(f"\n== 2008 TEST: synthetic 2007-09 stress Fridays (n {len(Y)}), hold to expiry, mean RoC % / worst / sum ==")
    print(Y[["cert", "n10", "n05"]].agg(["mean", "min", "sum"]).round(2).to_string())
    for a in ("n10", "n05"):
        ok08 = Y[a].mean() >= Y["cert"].mean()
        mu, t, h1, h2 = verdicts[a]
        switch = t >= 3 and h1 > 0 and h2 > 0 and ok08
        print(f"VERDICT {a.upper()}: paired t {t:+.2f} (bar 3), halves {h1:+.2f}/{h2:+.2f}, 2008 test {'PASS' if ok08 else 'FAIL'} -> {'SWITCH' if switch else 'KEEP the certified vehicle'}")
    X.to_csv("data/studies/logs/stress_vehicle_h2h_trades.csv", index=False)


if __name__ == "__main__":
    main()

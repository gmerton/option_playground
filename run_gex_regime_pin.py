#!/usr/bin/env python3
"""Dealer gamma exposure (GEX): regime, intraday momentum, expiry pin (2026-09-21).

PRE-REGISTERED: data/studies/gex_regime_pin_2026-09-21.md -- this script implements that spec and must not be tuned
against its own output. Inputs: data/cache/gex/<TK>_gex_strikes.parquet (Athena pull of options_daily_v3: per
trade_date x strike, sum OI*gamma for calls / puts over all expiries, OI of the next-expiring series),
data/cache/intraday_hist/<TK>_1min.parquet, ^VIX from yfinance.

Usage: PYTHONPATH=src .venv/bin/python3 run_gex_regime_pin.py | tee data/studies/gex_regime_pin_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
END = pd.Timestamp("2026-02-27")
SPLIT = pd.Timestamp("2018-01-01")
RNG = np.random.default_rng(20260921)


def daily_bars(tk: str) -> pd.DataFrame:
    m = pd.read_parquet(f"data/cache/intraday_hist/{tk}_1min.parquet")
    m = m[(m.ts >= "2009-12-01") & (m.ts < END + pd.Timedelta(days=1))]
    hm = m.ts.dt.hour * 60 + m.ts.dt.minute
    m = m[(hm >= 570) & (hm < 960)].copy()
    m["date"] = m.ts.dt.normalize(); m["hm"] = hm[m.index]
    m["lr"] = np.log(m.close).groupby(m.date).diff()
    g = m.groupby("date")
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                      "rv": np.sqrt(g.lr.apply(lambda x: np.nansum(x ** 2))), "bars": g.size()})
    at = lambda t: m[m.hm == t].set_index("date").close
    d["c1000"] = at(599)          # close of the 09:59 bar = the 10:00 price
    d["c1530"] = at(929)          # close of the 15:29 bar
    d = d[d.bars >= 380]
    d["prev_close"] = d.close.shift(1)
    d["r_first"] = np.log(d.c1000 / d.prev_close)
    d["r_last"] = np.log(d.close / d.c1530)
    d["range"] = (d.high - d.low) / d.open
    return d


def gex_series(tk: str, bars: pd.DataFrame):
    s = pd.read_parquet(f"data/cache/gex/{tk}_gex_strikes.parquet")
    s["trade_date"] = pd.to_datetime(s.trade_date); s["next_exp"] = pd.to_datetime(s.next_exp)
    S = bars.close.rename("S")
    s = s.join(S, on="trade_date").dropna(subset=["S"])
    s = s[(s.strike >= 0.8 * s.S) & (s.strike <= 1.2 * s.S)]
    s["gex"] = (s.cg - s.pg) * 100 * s.S ** 2 * 0.01
    net = s.groupby("trade_date").gex.sum()
    nxt = s.groupby("trade_date").next_exp.first()
    return s, net, nxt


def nw(y, X, lags=5):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def run(tk: str, vix: pd.Series) -> dict:
    d = daily_bars(tk)
    s, net, nxt = gex_series(tk, d)
    # GEX known at t-1 close -> attach to day t
    prev_day = pd.Series(d.index, index=d.index).shift(1)
    d["gex_prev"] = net.reindex(prev_day.values).values
    d["next_exp_prev"] = nxt.reindex(prev_day.values).values
    d["vix_prev"] = vix.reindex(prev_day.values).values
    d["rv_prev"] = d.rv.shift(1)
    d = d.dropna(subset=["gex_prev", "vix_prev", "rv_prev", "r_first", "r_last"])
    d = d[(d.index >= "2010-01-01") & (d.index <= END)]
    d["NEG"] = (d.gex_prev < 0).astype(float)
    d["half"] = np.where(d.index < SPLIT, "2010-2017", "2018-2026")
    out = {"tk": tk, "days": len(d), "neg_share": d.NEG.mean()}
    print(f"\n{'=' * 100}\n{tk}: {len(d):,} days {d.index.min().date()} -> {d.index.max().date()}; negative-GEX days {100 * d.NEG.mean():.1f}%")

    # ---- Test 1: regime
    print("\n-- Test 1: log realised vol on NEG, controlling for log VIX(t-1) and log RV(t-1) (Newey-West, 5 lags) --")
    rows = []
    for lab, g in [("full", d)] + list(d.groupby("half")):
        y = np.log(g.rv)
        f = nw(y, pd.DataFrame({"NEG": g.NEG, "lvix": np.log(g.vix_prev), "lrv": np.log(g.rv_prev)}))
        f0 = nw(y, pd.DataFrame({"NEG": g.NEG}))
        fr = nw(np.log(g["range"]), pd.DataFrame({"NEG": g.NEG, "lvix": np.log(g.vix_prev), "lrv": np.log(g.rv_prev)}))
        rows.append(dict(sample=lab, days=len(g), neg_days=int(g.NEG.sum()),
                         b_NEG=f.params.NEG, t_NEG=f.tvalues.NEG, pct_effect=100 * (np.exp(f.params.NEG) - 1),
                         b_noctrl=f0.params.NEG, t_noctrl=f0.tvalues.NEG, b_range=fr.params.NEG, t_range=fr.tvalues.NEG,
                         rv_neg=g[g.NEG == 1].rv.mean() * 100, rv_pos=g[g.NEG == 0].rv.mean() * 100))
    T1 = pd.DataFrame(rows); print(T1.round(3).to_string(index=False))
    full = T1.iloc[0]
    out["T1_pass"] = bool(full.b_NEG > 0 and full.t_NEG >= 3 and (T1.iloc[1:].b_NEG > 0).all())
    out.update(T1_b=full.b_NEG, T1_t=full.t_NEG, T1_pct=full.pct_effect)

    # ---- Test 2: momentum
    print("\n-- Test 2: r_last(15:30->close) on r_first(prev close->10:00) and r_first x NEG (Newey-West, 5 lags) --")
    rows = []
    for lab, g in [("full", d)] + list(d.groupby("half")):
        f = nw(g.r_last * 1e4, pd.DataFrame({"r_first": g.r_first * 1e4, "x_neg": g.r_first * 1e4 * g.NEG, "NEG": g.NEG}))
        rows.append(dict(sample=lab, days=len(g), b_first=f.params.r_first, t_first=f.tvalues.r_first,
                         g_interact=f.params.x_neg, t_interact=f.tvalues.x_neg))
    T2 = pd.DataFrame(rows); print(T2.round(4).to_string(index=False))
    full = T2.iloc[0]
    out["T2_pass"] = bool(full.g_interact > 0 and full.t_interact >= 3 and (T2.iloc[1:].g_interact > 0).all())
    out.update(T2_g=full.g_interact, T2_t=full.t_interact)

    # ---- Test 3: pin on expiry days
    s_by = dict(tuple(s.groupby("trade_date")))
    rows = []
    for t, r in d.iterrows():
        pd_ = prev_day.get(t)
        if pd_ not in s_by:
            continue
        g = s_by[pd_]
        g = g[(g.strike >= r.open * 0.98) & (g.strike <= r.open * 1.02)]
        if len(g) < 3:
            continue
        expiry = pd.notna(r.next_exp_prev) and pd.Timestamp(r.next_exp_prev) == t
        att = lambda K: (abs(r.open - K) - abs(r.close - K)) / r.open * 1e4
        k_gex = g.loc[g.gex.abs().idxmax(), "strike"]
        k_oi = g.loc[g.oi_next.idxmax(), "strike"] if g.oi_next.max() > 0 else np.nan
        ks = RNG.choice(g.strike.values, size=20, replace=True)
        rows.append(dict(date=t, expiry=expiry, a_gex=att(k_gex), a_oi=att(k_oi) if pd.notna(k_oi) else np.nan,
                         a_rand=np.mean([att(k) for k in ks]),
                         d_gex=abs(r.close - k_gex) / r.open * 1e4))
    P = pd.DataFrame(rows).set_index("date")
    P["half"] = np.where(P.index < SPLIT, "2010-2017", "2018-2026")
    P["edge_gex"] = P.a_gex - P.a_rand; P["edge_oi"] = P.a_oi - P.a_rand
    tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
    print("\n-- Test 3: attraction of the close toward the largest-|GEX| strike vs a random strike (bps; > 0 = pulled toward) --")
    rows = []
    for (lab, e), g in P.groupby(["half", "expiry"]):
        rows.append(dict(half=lab, expiry_day=e, days=len(g), gex_vs_random=g.edge_gex.mean(), t=tt(g.edge_gex),
                         oi_vs_random=g.edge_oi.mean(), t_oi=tt(g.edge_oi.dropna())))
    for e, g in P.groupby("expiry"):
        rows.append(dict(half="full", expiry_day=e, days=len(g), gex_vs_random=g.edge_gex.mean(), t=tt(g.edge_gex),
                         oi_vs_random=g.edge_oi.mean(), t_oi=tt(g.edge_oi.dropna())))
    T3 = pd.DataFrame(rows); print(T3.round(3).to_string(index=False))
    E = P[P.expiry]
    out["T3_pass"] = bool(E.edge_gex.mean() > 0 and tt(E.edge_gex) >= 3 and
                          all(E[E.half == h].edge_gex.mean() > 0 for h in ("2010-2017", "2018-2026")))
    out.update(T3_edge=E.edge_gex.mean(), T3_t=tt(E.edge_gex), T3_days=len(E))
    return out


def main():
    import yfinance as yf
    v = yf.download("^VIX", start="2009-11-01", end="2026-03-05", progress=False, auto_adjust=False)
    vix = v["Close"].squeeze(); vix.index = pd.to_datetime(vix.index).normalize()
    res = [run("SPY", vix), run("QQQ", vix)]
    R = pd.DataFrame(res)
    print("\n\n== SUMMARY (pass = pre-registered bar; SPY primary, QQQ robustness) ==")
    print(R.round(3).to_string(index=False))
    R.to_csv("data/studies/gex_regime_pin_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pooled ETF bull-put-spread study: which conditions make a one-sided put credit spread pay?

Trade: every Friday, per ETF, at the expiry nearest 30 DTE (21-40): sell the ~30-delta put, buy the
~15-delta put. Returns on max loss (width - credit), net of the house cost model (25% of each leg's
bid-ask + $0.0065/sh/leg per trade; expiry settles free). Two exits:
  hold    to expiry (settle at intrinsic);
  managed take profit when the spread's mid <= 50% of the credit, stop when it >= 2x the credit
          (a loss of about 1x credit), else expiry. Daily mids from options_cache.

Prices: the entry spot is put-call parity at the ATM strike (unadjusted, consistent with strikes);
later prices scale it by split-adjusted Tradier closes (S_T = S_entry * close_T / close_entry), so
share splits never break settlement (the XLE-style cache mismatch).

Features at entry (no lookahead; IV by BS inversion of each option's mid):
  log_ivrv  log(ATM 30d IV / trailing 21-session RV)
  ivp       ATM 30d IV percentile vs the ETF's own prior 52 Fridays
  skew_z    put skew (25d put IV / ATM IV - 1) z-scored vs its own prior 52 Fridays
  ff        forward factor from the ATM 30d and ~60d IVs: (iv30 - fwd) / fwd
  trend_z   log(close / 50-day SMA) / (RV21 * sqrt(50/252))
  vix       VIX close
Train 2018-06..2022-12, test 2023-01..2026-01. t-stats on the equal-weight WEEKLY portfolio
(Newey-West, 4 lags), because same-Friday trades across ETFs are correlated.

Usage: MYSQL_PASSWORD=... TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_etf_put_spread_regression.py
"""
from __future__ import annotations
import asyncio, math, os, sys
from datetime import date
import numpy as np, pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm
from lib.mysql_lib import _get_engine
from lib.studies.costs import COMMISSION_PER_LEG, SLIPPAGE_FRAC

ETFS = ["SPY", "QQQ", "IWM", "GLD", "TLT", "XOP", "XBI", "XLK", "XLE", "XLV", "EEM", "GDX", "USO", "XLU", "FXI", "XLP",
        "XLF", "ASHR", "SOXX", "UUP", "INDA"]
R = 0.04
TRAIN_END = pd.Timestamp("2022-12-31")
FEATURES = ["log_ivrv", "ivp", "skew_z", "ff", "trend_z", "vix"]
OUT = "data/studies/etf_put_spread_trades.csv"


def bs_put(S, K, T, s):
    d1 = (math.log(S / K) + (R + s * s / 2) * T) / (s * math.sqrt(T)); d2 = d1 - s * math.sqrt(T)
    return K * math.exp(-R * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def put_iv(p, S, K, T):
    if p <= max(K * math.exp(-R * T) - S, 0) + 1e-4: return np.nan
    try: return brentq(lambda s: bs_put(S, K, T, s) - p, 0.02, 5.0, xtol=1e-5)
    except Exception: return np.nan


async def closes() -> dict[str, pd.Series]:
    from lib.tradier.tradier_client_wrapper import TradierClient
    out, sem = {}, asyncio.Semaphore(2)
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        async def one(t):
            async with sem:
                h = await c.get_json("/markets/history", params={"symbol": t, "interval": "daily", "start": "2017-01-01", "end": "2026-03-20"})
                d = pd.DataFrame(h["history"]["day"]); d["date"] = pd.to_datetime(d.date)
                out[t] = d.set_index("date").close.astype(float)
        await asyncio.gather(*(one(t) for t in ETFS + ["VIX"] if t != "VIX"))
    return out


def load_friday_chains() -> pd.DataFrame:
    tl = ",".join(f"'{t}'" for t in ETFS)
    o = pd.read_sql(f"""SELECT ticker, trade_date, expiry, cp, strike, bid, ask, mid, delta FROM options_cache
        WHERE ticker IN ({tl}) AND DAYOFWEEK(trade_date)=6 AND DATEDIFF(expiry, trade_date) BETWEEN 21 AND 75
          AND bid > 0 AND ask >= bid AND mid > 0
          AND ((cp='P' AND delta BETWEEN -0.70 AND -0.05) OR (cp='C' AND delta BETWEEN 0.30 AND 0.70))""", _get_engine())
    o["trade_date"] = pd.to_datetime(o.trade_date); o["expiry"] = pd.to_datetime(o.expiry)
    for c in ("strike", "bid", "ask", "mid", "delta"): o[c] = o[c].astype(float)
    o["ba"] = o.ask - o.bid
    return o


def build(o: pd.DataFrame, cl: dict[str, pd.Series], vix: pd.Series) -> pd.DataFrame:
    rows = []
    for (t, d), day in o.groupby(["ticker", "trade_date"]):
        s = cl.get(t)
        if s is None or d not in s.index: continue
        dte = (day.expiry - d).dt.days
        e30s = day.expiry[(dte >= 21) & (dte <= 40)].unique(); e60s = day.expiry[(dte >= 45) & (dte <= 75)].unique()
        if not len(e30s): continue
        e30 = min(e30s, key=lambda e: abs((e - d).days - 30))
        x = day[day.expiry == e30]; P = x[x.cp == "P"].set_index("strike"); C = x[x.cp == "C"].set_index("strike")
        P = P[~P.index.duplicated()]; C = C[~C.index.duplicated()]
        both = P.index.intersection(C.index)
        if not len(both) or len(P) < 4: continue
        k0 = min(both, key=lambda k: abs(C.loc[k, "mid"] - P.loc[k, "mid"]))
        S = k0 + C.loc[k0, "mid"] - P.loc[k0, "mid"]
        T1 = (e30 - d).days / 365
        ka = min(P.index, key=lambda k: abs(k - S)); iv30 = put_iv(P.loc[ka, "mid"], S, ka, T1)
        k25 = (P.delta + 0.25).abs().idxmin(); iv25 = put_iv(P.loc[k25, "mid"], S, k25, T1)
        ks = (P.delta + 0.30).abs().idxmin(); lows = P[P.index < ks]
        if lows.empty or not np.isfinite(iv30): continue
        kl = (lows.delta + 0.15).abs().idxmin()
        credit = P.loc[ks, "mid"] - P.loc[kl, "mid"]; width = ks - kl
        if credit <= 0.02 or width <= credit: continue
        ff = np.nan
        if len(e60s):
            e60 = min(e60s, key=lambda e: abs((e - d).days - 60)); y = day[(day.expiry == e60) & (day.cp == "P")].set_index("strike")
            y = y[~y.index.duplicated()]
            if len(y):
                kb = min(y.index, key=lambda k: abs(k - S)); T2 = (e60 - d).days / 365; iv60 = put_iv(y.loc[kb, "mid"], S, kb, T2)
                if np.isfinite(iv60):
                    fv2 = (iv60 ** 2 * T2 - iv30 ** 2 * T1) / (T2 - T1)
                    if fv2 > 0: ff = (iv30 - math.sqrt(fv2)) / math.sqrt(fv2)
        hist = s.loc[:d]
        if len(hist) < 60: continue
        rv = float(np.log(hist).diff().tail(21).std() * math.sqrt(252))
        trend_z = math.log(hist.iloc[-1] / hist.tail(50).mean()) / (rv * math.sqrt(50 / 252)) if rv > 0 else np.nan
        cost = 2 * COMMISSION_PER_LEG + SLIPPAGE_FRAC * (P.loc[ks, "ba"] + P.loc[kl, "ba"])
        se = s.loc[:e30]
        if e30 > s.index[-1] or se.index[-1] < e30 - pd.Timedelta(days=4): continue
        ST = S * se.iloc[-1] / hist.iloc[-1]
        settle = min(max(ks - ST, 0) - max(kl - ST, 0), width)
        rows.append(dict(ticker=t, entry=d, expiry=e30, S=S, ks=ks, kl=kl, credit=credit, width=width, maxloss=width - credit,
                         cost=cost, ba_s=P.loc[ks, "ba"], ba_l=P.loc[kl, "ba"], iv30=iv30, rv21=rv, log_ivrv=math.log(iv30 / rv) if rv > 0 else np.nan,
                         put_skew=(iv25 / iv30 - 1) if np.isfinite(iv25) else np.nan, ff=ff, trend_z=trend_z,
                         vix=float(vix.asof(d)) if d >= vix.index[0] else np.nan, ST=ST,
                         roc_hold=(credit - settle - cost) / (width - credit)))
    df = pd.DataFrame(rows).sort_values(["ticker", "entry"])
    g = df.groupby("ticker")
    df["ivp"] = g.iv30.transform(lambda x: x.rolling(53, min_periods=27).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True))
    df["skew_z"] = g.put_skew.transform(lambda x: (x - x.shift(1).rolling(52, min_periods=26).mean()) / x.shift(1).rolling(52, min_periods=26).std())
    return df


def manage(df: pd.DataFrame) -> pd.Series:
    """50% take / 2x-credit stop on daily mids, else the hold result."""
    eng = _get_engine(); out = pd.Series(np.nan, index=df.index)
    for t, g in df.groupby("ticker"):
        exps = ",".join(f"'{e.date()}'" for e in g.expiry.unique()); ks = ",".join(str(float(k)) for k in set(g.ks) | set(g.kl))
        m = pd.read_sql(f"""SELECT trade_date, expiry, strike, mid, bid, ask FROM options_cache WHERE ticker='{t}' AND cp='P'
                            AND expiry IN ({exps}) AND strike IN ({ks}) AND mid > 0""", eng)
        m["trade_date"] = pd.to_datetime(m.trade_date); m["expiry"] = pd.to_datetime(m.expiry); m["strike"] = m.strike.astype(float); m["mid"] = m.mid.astype(float)
        mids = m.drop_duplicates(["trade_date", "expiry", "strike"]).set_index(["expiry", "strike", "trade_date"]).mid.sort_index()
        for i, r in g.iterrows():
            try:
                a = mids.loc[(r.expiry, r.ks)]; b = mids.loc[(r.expiry, r.kl)]
            except KeyError:
                out[i] = r.roc_hold; continue
            v = (a - b).dropna(); v = v[(v.index > r.entry) & (v.index < r.expiry)]
            res = r.roc_hold
            exit_cost = 2 * COMMISSION_PER_LEG + SLIPPAGE_FRAC * (r.ba_s + r.ba_l)
            for dd, val in v.items():
                if val <= 0.5 * r.credit or val >= 2.0 * r.credit:
                    res = (r.credit - val - r.cost - exit_cost) / r.maxloss; break
            out[i] = res
    return out


def nw_t(x: pd.Series, lags: int = 4) -> float:
    x = x.dropna().values
    if len(x) < 10: return np.nan
    u = x - x.mean(); s = (u @ u) / len(x)
    for L in range(1, lags + 1): s += 2 * (1 - L / (lags + 1)) * (u[L:] @ u[:-L]) / len(x)
    return x.mean() / math.sqrt(s / len(x))


def weekly(D: pd.DataFrame, col: str) -> str:
    if D.empty: return "n=0"
    w = D.groupby("entry")[col].mean()
    return (f"trades {len(D):5d} weeks {len(w):3d} | trade mean {100*D[col].mean():+6.2f}% win {100*(D[col]>0).mean():4.1f}% "
            f"worst {100*D[col].min():+6.1f}% | weekly-portfolio mean {100*w.mean():+6.2f}% t {nw_t(w):+5.2f} weeks+ {100*(w>0).mean():3.0f}%")


def main() -> int:
    cl = asyncio.run(closes())
    v = pd.read_parquet("data/cache/vix_daily.parquet"); v["trade_date"] = pd.to_datetime(v.trade_date)
    vix = v.set_index("trade_date")["close" if "close" in v else v.columns[-1]].astype(float).sort_index()
    o = load_friday_chains(); print(f"chains: {len(o):,} rows, {o.ticker.nunique()} ETFs", flush=True)
    df = build(o, cl, vix); print(f"trades built: {len(df):,}", flush=True)
    df["roc_mgd"] = manage(df)
    df = df.dropna(subset=FEATURES + ["roc_hold", "roc_mgd"])
    df.to_csv(OUT, index=False)
    tr, te = df[df.entry <= TRAIN_END], df[df.entry > TRAIN_END]
    pd.set_option("display.width", 230)
    print(f"\n{len(df):,} trades after feature warm-up | {df.entry.min().date()} .. {df.entry.max().date()} | train {len(tr):,} test {len(te):,}")
    print(f"median credit/width {100*(df.credit/df.width).median():.1f}% | median short delta ~0.30 | median DTE {(df.expiry-df.entry).dt.days.median():.0f}")
    for col in ("roc_hold", "roc_mgd"):
        print(f"\n===== {col} =====")
        for nm, D in (("ALL", df), ("train 2018-22", tr), ("test 2023-26", te)): print(f"  BASELINE {nm:14s} {weekly(D, col)}")
        print("  by ETF (all years):  " + "  ".join(f"{t} {100*g[col].mean():+.1f}" for t, g in df.groupby("ticker")))
        print("  UNIVARIATE quintiles (train bins): mean return, train | test")
        for f in FEATURES:
            e = np.unique(np.quantile(tr[f], [0, .2, .4, .6, .8, 1])); e[0], e[-1] = -np.inf, np.inf
            a = tr.groupby(pd.cut(tr[f], e), observed=True)[col].mean(); b = te.groupby(pd.cut(te[f], e), observed=True)[col].mean()
            print(f"    {f:9s} " + " | ".join(f"Q{i+1} {100*a.iloc[i]:+5.1f} {100*b.iloc[i] if i < len(b) else float('nan'):+5.1f}" for i in range(len(a))))
        mu, sd = tr[FEATURES].mean(), tr[FEATURES].std(); Z = lambda D: np.column_stack([np.ones(len(D)), ((D[FEATURES] - mu) / sd).values])
        b = np.linalg.lstsq(Z(tr), tr[col].values, rcond=None)[0]
        ptr, pte = Z(tr) @ b, Z(te) @ b
        print("  OLS (train): " + " | ".join(f"{n} {x:+.3f}" for n, x in zip(["const"] + FEATURES, b)))
        print(f"  corr(pred, realized): train {np.corrcoef(ptr, tr[col])[0,1]:+.3f} | TEST {np.corrcoef(pte, te[col])[0,1]:+.3f}")
        for q in (0.5, 0.67, 0.8):
            th = np.quantile(ptr, q); m = pte > th
            print(f"   test, pred > train {int(q*100)}th pct:  {weekly(te[m], col)}")
            print(f"   test, skipped:                {weekly(te[~m], col)}")
        print("  SIMPLE RULES (test | train):")
        rules = {"uptrend (trend_z > 0)": lambda D: D.trend_z > 0, "uptrend & VIX >= 20": lambda D: (D.trend_z > 0) & (D.vix >= 20),
                 "IVP 30-60": lambda D: D.ivp.between(0.3, 0.6), "IVP < 80 (veto >= 80)": lambda D: D.ivp < 0.8,
                 "washout: downtrend & IVP >= 80": lambda D: (D.trend_z < 0) & (D.ivp >= 0.8), "IV > RV": lambda D: D.log_ivrv > 0,
                 "put skew rich (skew_z > 1)": lambda D: D.skew_z > 1, "downtrend & IVP < 80 (the bad cell)": lambda D: (D.trend_z < 0) & (D.ivp < 0.8),
                 "uptrend & IVP < 80": lambda D: (D.trend_z > 0) & (D.ivp < 0.8)}
        for lab, fn in rules.items():
            print(f"    {lab:36s} test  {weekly(te[fn(te)], col)}\n    {'':36s} train {weekly(tr[fn(tr)], col)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

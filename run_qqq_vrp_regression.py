#!/usr/bin/env python3
"""QQQ VRP regression: can the oquants-style model (log IV/RV, IV percentile, term structure) pick
better weeks to sell a 30-day ATM straddle?

Trades: every Friday 2018-01 .. 2026-01, sell the ATM straddle at the expiry nearest 30 DTE (21-40),
hold to expiry, settle at |S_T - K| from the QQQ close on expiry. Return on credit, net of the house
cost model (25% of each leg's bid-ask + $0.0065/sh/leg on entry; expiry settles free). Also an iron
butterfly: wings at K +/- (nearest strike to one straddle-width), return on max loss.

Features at entry (no lookahead):
  iv30      straddle-implied vol of the traded straddle ~ credit / (0.8 * S * sqrt(T))
  rv30      trailing 21-session close-to-close vol, annualized
  log_ivrv  log(iv30 / rv30)
  ivp       1-year percentile of ATM 30-day IV vs its own prior 252 days (qqq_iv30 series, BS-inverted puts)
  ff        forward factor from the 30- and ~60-DTE straddles: (iv30 - fwd) / fwd  (oquants' FF definition;
            stand-in for their Flat Fwd Ratio, which has no published formula)
Model: OLS on 2018-2022 (train), scored on 2023-2026 (test). Weekly entries with 4-week holds overlap,
so t-stats use Newey-West (4 lags).

Usage: MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_qqq_vrp_regression.py [--iv path/to/qqq_iv30.parquet]
"""
from __future__ import annotations
import argparse, math
from datetime import date
import numpy as np, pandas as pd
from lib.mysql_lib import _get_engine
from lib.studies.costs import COMMISSION_PER_LEG, SLIPPAGE_FRAC

TRAIN_END = "2022-12-31"
FEATURES = ["log_ivrv", "ivp", "ff"]


def load(iv_path: str):
    o = pd.read_sql("""SELECT trade_date, expiry, cp, strike, bid, ask, mid FROM options_cache
        WHERE ticker='QQQ' AND DAYOFWEEK(trade_date)=6 AND DATEDIFF(expiry, trade_date) BETWEEN 21 AND 75
          AND bid > 0 AND ask > 0 AND ask >= bid""", _get_engine())
    o["trade_date"] = pd.to_datetime(o.trade_date); o["expiry"] = pd.to_datetime(o.expiry)
    for c in ("strike", "bid", "ask", "mid"): o[c] = o[c].astype(float)
    o["ba"] = o.ask - o.bid
    s = pd.read_parquet("data/cache/QQQ_stock.parquet"); s["trade_date"] = pd.to_datetime(s.trade_date)
    s = s.sort_values("trade_date").set_index("trade_date").close.astype(float)
    iv = pd.read_parquet(iv_path); iv.index = pd.to_datetime(iv.index)
    return o, s, iv


def straddle(day: pd.DataFrame, exp, spot: float):
    x = day[day.expiry == exp]
    c, p = x[x.cp == "C"].set_index("strike"), x[x.cp == "P"].set_index("strike")
    ks = c.index.intersection(p.index)
    if not len(ks): return None
    k = min(ks, key=lambda z: abs(z - spot))
    return k, c, p


def build(o, s, iv) -> pd.DataFrame:
    rv = np.log(s).diff().rolling(21).std() * math.sqrt(252)
    rows = []
    for d, day in o.groupby("trade_date"):
        if d not in s.index: continue
        spot = float(s.loc[d]); dte = (day.expiry - d).dt.days
        e30 = day.expiry[(dte >= 21) & (dte <= 40)].unique()
        e60 = day.expiry[(dte >= 45) & (dte <= 75)].unique()
        if not len(e30) or not len(e60): continue
        ex = min(e30, key=lambda e: abs((e - d).days - 30)); ex2 = min(e60, key=lambda e: abs((e - d).days - 60))
        a = straddle(day, ex, spot); b = straddle(day, ex2, spot)
        if a is None or b is None: continue
        k, c, p = a; k2, c2, p2 = b
        credit = c.loc[k, "mid"] + p.loc[k, "mid"]
        T1, T2 = (ex - d).days / 365, (ex2 - d).days / 365
        iv1 = credit / (0.8 * spot * math.sqrt(T1))
        iv2 = (c2.loc[k2, "mid"] + p2.loc[k2, "mid"]) / (0.8 * spot * math.sqrt(T2))
        fv2 = (iv2 ** 2 * T2 - iv1 ** 2 * T1) / (T2 - T1)
        if fv2 <= 0: continue
        fwd = math.sqrt(fv2); ff = (iv1 - fwd) / fwd
        # settlement: QQQ close on (or the last trading day before) expiry
        se = s.loc[:ex]
        if se.index[-1] < ex - pd.Timedelta(days=4) or ex > s.index[-1]: continue
        ST = float(se.iloc[-1]); payoff = abs(ST - k)
        cost = 2 * COMMISSION_PER_LEG + SLIPPAGE_FRAC * (c.loc[k, "ba"] + p.loc[k, "ba"])
        # iron fly: wings at K +/- nearest strikes to one straddle-width
        wc = min((z for z in c.index if z > k), key=lambda z: abs(z - (k + credit)), default=None)
        wp = min((z for z in p.index if z < k), key=lambda z: abs(z - (k - credit)), default=None)
        fly = None
        if wc is not None and wp is not None:
            fcred = credit - c.loc[wc, "mid"] - p.loc[wp, "mid"]
            fcost = cost + 2 * COMMISSION_PER_LEG + SLIPPAGE_FRAC * (c.loc[wc, "ba"] + p.loc[wp, "ba"])
            w = max(wc - k, k - wp); maxloss = w - fcred
            fpay = min(max(ST - k, 0), wc - k) + min(max(k - ST, 0), k - wp)
            if maxloss > 0: fly = (fcred - fpay - fcost) / maxloss
        ivp = iv.iv_pct.asof(d) if d >= iv.index[0] else np.nan
        rows.append(dict(entry=d.date(), expiry=ex.date(), dte=(ex - d).days, spot=spot, strike=k, credit=round(credit, 3),
                         settle=round(payoff, 3), iv30=iv1, rv30=float(rv.loc[d]), ivp=ivp, ff=ff,
                         ret_gross=(credit - payoff) / credit, ret=(credit - payoff - cost) / credit, fly_ret=fly))
    df = pd.DataFrame(rows).dropna(subset=["rv30", "ivp"])
    df["log_ivrv"] = np.log(df.iv30 / df.rv30)
    return df


def ols_nw(X: np.ndarray, y: np.ndarray, lags: int = 4):
    X1 = np.column_stack([np.ones(len(X)), X]); b = np.linalg.lstsq(X1, y, rcond=None)[0]; u = y - X1 @ b
    XtXi = np.linalg.inv(X1.T @ X1); S = (X1 * u[:, None]).T @ (X1 * u[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1); G = (X1[L:] * u[L:, None]).T @ (X1[:-L] * u[:-L, None]); S += w * (G + G.T)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi)); r2 = 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))
    return b, b / se, r2


def summ(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) < 3: return f"n={len(x)}"
    t = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
    return f"n={len(x):3d} mean {100*x.mean():+6.2f}% med {100*x.median():+6.2f}% win {100*(x>0).mean():4.1f}% worst {100*x.min():+7.1f}% t {t:+5.2f}"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--iv", required=True); ap.add_argument("--out", default="data/studies/qqq_vrp_regression_trades.csv")
    a = ap.parse_args()
    o, s, iv = load(a.iv)
    df = build(o, s, iv); df.to_csv(a.out, index=False)
    tr, te = df[df.entry <= date.fromisoformat(TRAIN_END)], df[df.entry > date.fromisoformat(TRAIN_END)]
    print(f"trades {len(df)} ({df.entry.min()} .. {df.entry.max()}) | train {len(tr)} | test {len(te)} | median DTE {df.dte.median():.0f}")
    print(f"feature means: iv30 {df.iv30.mean():.3f}  rv30 {df.rv30.mean():.3f}  log_ivrv {df.log_ivrv.mean():+.3f}  ivp {df.ivp.mean():.2f}  ff {df.ff.mean():+.3f}")
    for nm, D in (("ALL", df), ("train 2018-22", tr), ("test 2023-26", te)):
        print(f"\nBASELINE {nm:14s} straddle net: {summ(D.ret)}\n{'':24s} fly net:      {summ(D.fly_ret)}\n{'':24s} straddle gross {100*D.ret_gross.mean():+.2f}%")
    print("\nUNIVARIATE: straddle net return by feature quintile (bins from the TRAIN period), train vs test")
    for f in FEATURES:
        edges = np.unique(np.quantile(tr[f], [0, .2, .4, .6, .8, 1])); edges[0], edges[-1] = -np.inf, np.inf
        g = lambda D: D.groupby(pd.cut(D[f], edges), observed=True).ret.agg(["size", "mean"])
        t1, t2 = g(tr), g(te)
        print(f"  {f}: " + " | ".join(f"Q{i+1} tr {100*t1['mean'].iloc[i]:+5.1f}% ({int(t1['size'].iloc[i])}) te {100*t2['mean'].iloc[i]:+5.1f}% ({int(t2['size'].iloc[i])})" if i < len(t2) else "" for i in range(len(t1))))
    mu, sd = tr[FEATURES].mean(), tr[FEATURES].std()
    Z = lambda D: ((D[FEATURES] - mu) / sd).values
    for tgt in ("ret", "fly_ret"):
        T = tr.dropna(subset=[tgt]); b, t, r2 = ols_nw(Z(T), T[tgt].values)
        print(f"\nOLS on train, target {tgt}: R2 {r2:.3f} | " + " | ".join(f"{n} {bb:+.3f} (t {tt:+.2f})" for n, bb, tt in zip(["const"] + FEATURES, b, t)))
        for nm, D in (("train", T), ("test", te.dropna(subset=[tgt]))):
            pred = np.column_stack([np.ones(len(D)), Z(D)]) @ b
            D = D.assign(pred=pred)
            oos = 1 - ((D[tgt] - D.pred) ** 2).sum() / ((D[tgt] - T[tgt].mean()) ** 2).sum()
            corr = np.corrcoef(D.pred, D[tgt])[0, 1]
            print(f"  {nm}: corr(pred, realized) {corr:+.3f} | R2 vs the train mean {oos:+.3f}")
            q = pd.qcut(D.pred, 5, labels=False, duplicates="drop")
            print("    by predicted quintile: " + " | ".join(f"Q{i+1} {100*D[tgt][q == i].mean():+5.1f}%" for i in sorted(q.unique())))
            thr = np.quantile(np.column_stack([np.ones(len(T)), Z(T)]) @ b, [0.5, 0.67])
            for lab, th in (("pred > 0", 0.0), ("pred > train median", thr[0]), ("pred > train 67th pct", thr[1])):
                print(f"    {lab:22s} {summ(D[tgt][D.pred > th])}   | skipped: {summ(D[tgt][D.pred <= th])}")
    print("\nSIMPLE GATES (no model), straddle net, test period:")
    for lab, m in (("ivp < 0.80", te.ivp < 0.80), ("log_ivrv > 0 (IV > RV)", te.log_ivrv > 0), ("ff <= 0 (contango/flat)", te.ff <= 0),
                   ("all three", (te.ivp < 0.80) & (te.log_ivrv > 0) & (te.ff <= 0))):
        print(f"  {lab:26s} {summ(te.ret[m])}   | rest: {summ(te.ret[~m])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

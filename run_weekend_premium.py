#!/usr/bin/env python3
"""Weekend premium in SPY 1-day options + overlap with the positive-gamma fly (2026-09-21).
PRE-REGISTERED: data/studies/weekend_premium_spy_2026-09-21.md. Same data/entry/fills as run_gex_spy_ironfly.py (2x wings).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_weekend_premium.py | tee data/studies/weekend_premium_spy_2026-09-21.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import run_gex_regime_pin as base
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
SLIP, COMM, MIN_MID = 0.25, 0.0065, 0.10


def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def main():
    bars = base.daily_bars("SPY"); _, net, _ = base.gex_series("SPY", bars)
    q = pd.read_parquet("data/cache/gex/SPY_short_expiry_quotes.parquet")
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    nxt = pd.Series(bars.index[1:], index=bars.index[:-1])
    q = q[q.trade_date.isin(nxt.index)]; q = q[q.expiry == q.trade_date.map(nxt)]
    q = q[(q.ask >= q.bid) & (q.ask < 9999) & (q.bid >= 0)]
    q["mid"] = (q.bid + q.ask) / 2; q["ba"] = q.ask - q.bid
    q = q.sort_values("ba").drop_duplicates(["trade_date", "strike", "cp"], keep="first")
    rows = []
    for d, g in q.groupby("trade_date"):
        if d not in net.index: continue
        c = g[g.cp == "C"].set_index("strike").sort_index(); p = g[g.cp == "P"].set_index("strike").sort_index()
        ks = c.index.intersection(p.index)
        if not len(ks) or c.loc[ks].delta.isna().all(): continue
        K = (c.loc[ks].delta - 0.5).abs().idxmin(); smid = c.loc[K, "mid"] + p.loc[K, "mid"]; sba = c.loc[K, "ba"] + p.loc[K, "ba"]
        if smid < MIN_MID: continue
        t = nxt[d]; S_t = bars.close.get(t, np.nan)
        if not np.isfinite(S_t): continue
        cw = c[(c.index > K) & (c.bid > 0)]; pw = p[(p.index < K) & (p.ask > 0)]
        if cw.empty or pw.empty: continue
        kc = cw.index[np.abs(cw.index - (K + 2 * smid)).argmin()]; kp = pw.index[np.abs(pw.index - (K - 2 * smid)).argmin()]
        s_ = lambda r: r.mid - SLIP * r.ba; b_ = lambda r: r.mid + SLIP * r.ba
        cr = s_(c.loc[K]) + s_(p.loc[K]) - b_(c.loc[kc]) - b_(p.loc[kp]) - 4 * COMM
        risk = max(kc - K, K - kp) - cr
        if cr <= 0 or risk <= 0: continue
        pay_f = min(max(S_t - K, 0), kc - K) + min(max(K - S_t, 0), K - kp)
        scr = smid - SLIP * sba - 2 * COMM; pay_s = abs(S_t - K)
        rows.append(dict(entry=d, day=t, gap=(t - d).days, POS=int(net[d] > 0), fly=(cr - pay_f) / risk * 100,
                         straddle=(scr - pay_s) / scr * 100 if scr > 0 else np.nan, ratio=pay_s / smid))
    X = pd.DataFrame(rows)
    X["WKND"] = (X.gap >= 3).astype(int)
    X["half"] = np.where(X.day < base.SPLIT, "2010-2017", "2018-2026")
    print(f"{len(X):,} 1-day entries; weekend {int(X.WKND.sum())} (first {X[X.WKND == 1].day.min().date()}), weekday {int((1 - X.WKND).sum())}")

    print("\n== W1: weekend vs weekday, 2x fly return on max risk at the real fill (%) ==")
    rows = []
    for w, g in X.groupby("WKND"):
        for lab, gg in (("all", g),) + tuple(g.groupby("half")):
            rows.append(dict(entries="weekend" if w else "weekday", sample=lab, n=len(gg), fly=gg.fly.mean(), t=tstat(gg.fly),
                             straddle=gg.straddle.mean(), realised_over_implied=gg.ratio.mean(), win=(gg.fly > 0).mean() * 100))
    W1 = pd.DataFrame(rows); print(W1.round(2).to_string(index=False))
    wk, wd = X[X.WKND == 1], X[X.WKND == 0]
    halves_ok = all(wk[wk.half == h].fly.mean() > 0 for h in wk.half.unique())
    ok1 = wk.fly.mean() > 0 and tstat(wk.fly) >= 3 and halves_ok and wk.fly.mean() > wd.fly.mean()
    diff_t = (wk.fly.mean() - wd.fly.mean()) / np.sqrt(wk.fly.var() / len(wk) + wd.fly.var() / len(wd))
    print(f"weekend minus weekday {wk.fly.mean() - wd.fly.mean():+.2f}pp (Welch t {diff_t:.2f}); halves present for weekend: {sorted(wk.half.unique())}")
    print(f"PASS W1: {'YES' if ok1 else 'no'}")

    print("\n== W2: weekend x gamma cells (fly %, n) and regression ==")
    cells = X.groupby(["WKND", "POS"]).fly.agg(["mean", "size", tstat]).rename(columns={"tstat": "t"})
    cells.index = [f"{'weekend' if a else 'weekday'} / {'POS' if b else 'NEG'}" for a, b in cells.index]
    print(cells.round(2).to_string())
    f = smf.ols("fly ~ WKND * POS", data=X).fit(cov_type="HC1")
    print(f.summary().tables[1])
    wdX = X[X.WKND == 0]
    pos, neg = wdX[wdX.POS == 1].fly, wdX[wdX.POS == 0].fly
    t2 = (pos.mean() - neg.mean()) / np.sqrt(pos.var() / len(pos) + neg.var() / len(neg))
    print(f"weekday-only: POS {pos.mean():+.2f}% (n {len(pos)}, t {tstat(pos):.2f}) vs NEG {neg.mean():+.2f}% (n {len(neg)}) -> difference {pos.mean() - neg.mean():+.2f}pp, Welch t {t2:.2f}")
    for h, g in wdX.groupby("half"):
        print(f"   {h}: weekday POS {g[g.POS == 1].fly.mean():+.2f}% (n {int(g.POS.sum())}) vs NEG {g[g.POS == 0].fly.mean():+.2f}%")
    print(f"PASS W2 (gamma edge survives without weekends): {'YES' if (pos.mean() > neg.mean() and t2 >= 2) else 'no'}")
    X.to_csv("data/studies/weekend_premium_spy_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

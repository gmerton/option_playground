#!/usr/bin/env python3
"""
QQQ bull put spreads conditioned on QQQ's OWN 30-day ATM put IV percentile (trailing 252), on top of the
50MA x VIX regime the playbook already uses. Real bid/ask from MySQL options_cache (2018-01 .. 2026-02),
cost model on (lib.studies.costs), 20 DTE, 50% profit take / 2x stop, Friday entries.

IV history: <scratch>/qqq_iv30.parquet (built by BS-inverting ~30-DTE ATM put mids against the stock cache).
Usage: MYSQL_PASSWORD=... PYTHONPATH=src python run_qqq_iv_gate_study.py --iv path/to/qqq_iv30.parquet
"""
import argparse, warnings
import numpy as np, pandas as pd
from datetime import date, timedelta
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
import run_tlt_strategy_study as E
from lib.mysql_lib import _get_engine

def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

def load_puts(ticker):
    sql = f"""SELECT trade_date, expiry, strike, mid, bid, ask, delta, cp, DATEDIFF(expiry, trade_date) AS dte FROM options_cache
      WHERE ticker='{ticker}' AND cp='P' AND mid>0 AND delta<0 AND ABS(delta) BETWEEN 0.07 AND 0.60 AND DATEDIFF(expiry, trade_date) BETWEEN 10 AND 30 ORDER BY trade_date, expiry, strike"""
    df = pd.read_sql(sql, _get_engine())
    df["trade_date"] = pd.to_datetime(df.trade_date).dt.date; df["expiry"] = pd.to_datetime(df.expiry).dt.date
    for c in ("strike", "mid", "bid", "ask"): df[c] = df[c].astype(float)
    df["delta"] = df.delta.abs().astype(float); df["dte"] = df.dte.astype(int); return df

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--iv", required=True); ap.add_argument("--ticker", default="QQQ"); a = ap.parse_args()
    E.APPLY_COSTS = True
    opts = load_puts(a.ticker); stock = E.load_stock(a.ticker); vix = E.load_vix(); reg = E.build_regime_map(stock, vix)
    stock_map = dict(zip(stock.trade_date, stock.close)); daily_p = {(r.trade_date, r.expiry, r.strike): r.mid for r in opts.itertuples(index=False)}
    iv = pd.read_parquet(a.iv); iv.index = pd.to_datetime(iv.index).date
    vixs = pd.Series(vix); vixs.index = pd.to_datetime(list(vixs.index)); vixs = vixs.sort_index(); vix_pct = vixs.rolling(252, min_periods=120).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True); vix_pct.index = vix_pct.index.date
    by_date = {d: g for d, g in opts.groupby("trade_date")}
    pairs = [(0.35, 0.25), (0.45, 0.35), (0.25, 0.15)]
    rows = []
    for edate in sorted(by_date):
        if edate.weekday() != 4 or edate not in reg: continue
        day = by_date[edate]; r = reg[edate]; regime = E.classify_regime(r)
        for sd, ld in pairs:
            s = E.find_option(day, "P", sd)
            if s is None: continue
            l = E.find_option(day, "P", ld, expiry=s["expiry"])
            if l is None or l["strike"] >= s["strike"]: continue
            credit = s["mid"] - l["mid"]
            if credit <= 0: continue
            sim = E._net(E.sim_spread(edate, s["expiry"], s["strike"], l["strike"], "P", credit, daily_p, stock_map), [s, l])
            width = s["strike"] - l["strike"]
            rows.append(dict(edate=edate, pair=f"{sd:.2f}/{ld:.2f}", regime=regime, credit=credit, width=width, max_loss=width - credit, pnl=sim["pnl"], pnl_gross=sim["pnl_gross"], cost=sim["cost"], exit=sim["exit"], days=sim["days"],
                             iv_pct=iv.iv_pct.get(edate, np.nan), iv30=iv.iv30.get(edate, np.nan), vix=r.get("vix", np.nan), vix_pct=vix_pct.get(edate, np.nan)))
    df = pd.DataFrame(rows); df["roc"] = df.pnl / df.max_loss; df["roc_gross"] = df.pnl_gross / df.max_loss; df["win"] = df.pnl > 0; df["year"] = pd.to_datetime(df.edate).dt.year
    df["iv_b"] = pd.cut(df.iv_pct, [-0.01, 0.3, 0.6, 0.8, 1.01], labels=["<30", "30-60", "60-80", ">=80"]); df["vix_b"] = pd.cut(df.vix_pct, [-0.01, 0.3, 0.6, 0.8, 1.01], labels=["<30", "30-60", "60-80", ">=80"])
    df.to_csv(f"data/studies/{a.ticker.lower()}_iv_gate_events.csv", index=False)
    def line(lbl, g):
        print(f"  {lbl:34s} n={len(g):4d}  roc net {100*g.roc.mean():+6.2f}%  gross {100*g.roc_gross.mean():+6.2f}%  win {100*g.win.mean():5.1f}%  med {100*g.roc.median():+6.2f}%  t {tstat(g.roc):+5.2f}  credit/width {100*(g.credit/g.width).mean():4.1f}%  stops {100*(g.exit=='stop_loss').mean():4.1f}%")
    print(f"{a.ticker} bull put spreads, 20 DTE, Fridays 2018-2026, after costs. IV pct known on {df.iv_pct.notna().mean():.0%} of trades.")
    for pair, dfp in df.groupby("pair"):
        print(f"\n===== pair {pair} =====")
        line("ALL", dfp)
        print("  by OWN IV percentile:")
        for k, g in dfp.groupby("iv_b", observed=True): line(f"    IV pct {k}", g)
        print("  by VIX percentile (the proxy the playbook effectively uses):")
        for k, g in dfp.groupby("vix_b", observed=True): line(f"    VIX pct {k}", g)
        print("  regime x IV percentile:")
        for (rg, k), g in dfp.groupby(["regime", "iv_b"], observed=True):
            if len(g) >= 15: line(f"    {rg:15s} IV {k}", g)
        print("  IV pct >= 60, by year:")
        for k, g in dfp[dfp.iv_pct >= 0.6].groupby("year"): line(f"    {k}", g)
        print("  IV pct < 60, by year:")
        for k, g in dfp[dfp.iv_pct < 0.6].groupby("year"): line(f"    {k}", g)

if __name__ == "__main__":
    main()

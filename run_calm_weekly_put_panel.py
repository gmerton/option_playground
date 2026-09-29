#!/usr/bin/env python3
"""
Does the calm weekly put sale carry to UNCORRELATED liquid ETFs and to the most liquid STOCKS? (pre-registered
2026-09-28, committed before any run)

WHY. The SPY rule (spy_calm_weekly_put_2026-09-28.md) replicates on QQQ and IWM, but all three crash together. Gabe asks
for exposures that do not. Prior for stocks: short-dated single-name premium selling FAILED on costs (TEST_INDEX row 69:
net negative, costs 136% of gross; only SPY + NVDA/AMZN/AAPL/V liquid enough) and far-OTM puts have the worst
cost-to-premium ratio -- so the stock universe is largely a cost check.

PRE-REGISTRATION
  Universes  A (uncorrelated ETFs, PRIMARY): GLD, TLT, SLV, EEM, FXI, XLE, XLU, EWZ, USO, HYG
             B (liquid stocks, secondary): AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, NFLX, JPM
  Data       silver.options_daily_v3 PUTS, DTE 5-9, 2010-01 -> 2026-02 (bid/ask era), cached per ticker; daily close
             (yfinance raw Close); ^VIX; ^IRX.
  Rule       the SPY rule WITHOUT the gamma gate (the GEX gate is certified for SPY only; the naive sign misreads IWM and
             single stocks): FRIDAY entry; CALM = NOT (own close < own 50-session SMA AND VIX >= 20); sell the 7-DTE put
             (expiry nearest 7 in [5, 9]) at |delta| nearest 0.10 (+/-0.025) [primary] and 0.05 (+/-0.015); hold to
             expiry; settle on the ticker's close; house fills (mid - 25% bid-ask - $0.0065/share).
             Stocks: skip any Friday whose window (entry -> expiry) contains an earnings session (earnings_yf.parquet).
  Statistic  per trade: EXCESS over own beta = net - |delta| x own return entry->expiry (carry: q 0 for simplicity, - T-bill
             x T; small at 7 days), bp of the ticker's notional. POOLED per universe: each Friday's mean across tickers,
             month-clustered t (dates are the unit, so correlated tickers do not multiply the sample).
  PRIMARY    universe A, 10-delta: pooled excess t >= 3 AND both halves (2010-2017 / 2018-2026) positive -> the premium
             carries to uncorrelated ETFs. Secondary: A 5-delta; B 10 / 5-delta; every ticker's own row (net, excess, t,
             win, worst, median bid-ask % of mid); gross-vs-net cost share.
  Diversification check (descriptive): each ticker's mean P&L in SPY's 20 worst entry weeks (2010-2026), to show
             whether its tail coincides with SPY's.

DATA FIX (after the first run, disclosed): closes are un-adjusted to RAW with data/cache/pit/splits.parquet to match
v3's raw strikes; only trades spanning a split date are dropped. First-run log: calm_weekly_put_panel_SPLITBUG.log (void).

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_calm_weekly_put_panel.py > data/studies/logs/calm_weekly_put_panel.log
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
A = ["GLD", "TLT", "SLV", "EEM", "FXI", "XLE", "XLU", "EWZ", "USO", "HYG"]
B = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD", "NFLX", "JPM"]
SLIP, COMM = 0.25, 0.0065
CDIR = Path("data/cache/weekly_puts")


def pull(tk):
    f = CDIR / f"{tk}_puts_dte5_9.parquet"
    if f.exists():
        return pd.read_parquet(f)
    from lib.athena_lib import athena
    d = athena(f"""SELECT trade_date, expiry, CAST(strike AS DOUBLE) strike, CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask,
                  CAST(delta AS DOUBLE) delta FROM silver.options_daily_v3 WHERE ticker = '{tk}'
                  AND trade_date BETWEEN DATE '2010-01-01' AND DATE '2026-02-28' AND day_of_week(trade_date) = 5
                  AND upper(substr(cp, 1, 1)) = 'P' AND date_diff('day', trade_date, expiry) BETWEEN 5 AND 9""")
    d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
    CDIR.mkdir(parents=True, exist_ok=True); d.to_parquet(f, index=False)
    print(f"  pulled {tk}: {len(d):,}", flush=True)
    return d


def mclust(x, d):
    df = pd.DataFrame(dict(x=np.asarray(x), m=pd.to_datetime(np.asarray(d)).to_period("M"))).dropna()
    if len(df) < 12:
        return np.nan, np.nan
    mu = df.x.mean(); s = df.groupby("m").x.sum(); n = df.groupby("m").size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return mu, (mu / se if se > 0 else np.nan)


def main():
    import yfinance as yf
    tick = A + B + ["SPY"]
    px = yf.download(tick, start="2009-06-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"]
    px.index = pd.to_datetime(px.index).normalize()
    vix = yf.download("^VIX", start="2009-06-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"].squeeze()
    vix.index = pd.to_datetime(vix.index).normalize(); vix = vix.reindex(px.index).ffill()
    irx = (yf.download("^IRX", start="2009-06-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"].squeeze() / 100)
    irx.index = pd.to_datetime(irx.index).normalize(); irx = irx.reindex(px.index).ffill()
    # DATA FIX after the first run (disclosed): v3 strikes are RAW; yfinance Close is split-ADJUSTED. Un-adjust every
    # close with the split history (raw = adjusted x each LATER split's to/from ratio), and drop only trades whose window
    # spans a split date. The first run (log kept as calm_weekly_put_panel_SPLITBUG.log) settled raw strikes against
    # adjusted prices and is void for every name with a split (AAPL NVDA AMZN GOOGL TSLA NFLX USO XLE XLU).
    sp = pd.read_parquet("data/cache/pit/splits.parquet"); sp["execution_date"] = pd.to_datetime(sp.execution_date)
    split_dates = {}
    for r_ in sp[sp.ticker.isin(A + B)].itertuples():
        ratio = r_.split_to / r_.split_from
        m = px.index < r_.execution_date
        px.loc[m, r_.ticker] = px.loc[m, r_.ticker] * ratio
        split_dates.setdefault(r_.ticker, []).append(r_.execution_date)
    earn = pd.read_parquet("data/cache/earnings_yf.parquet")
    earn["session"] = pd.to_datetime(earn.session)
    rows = []
    for tk in A + B:
        S = px[tk].dropna()
        jumps = int((S.pct_change().abs() > 0.35).sum())   # after un-adjusting, remaining jumps are real moves
        calm = ~((S < S.rolling(50).mean()) & (vix.reindex(S.index) >= 20))
        D = pull(tk)
        D = D[(D.bid > 0) & (D.ask >= D.bid) & D.delta.notna()].copy()
        if D.empty:
            continue
        D["dte"] = (D.expiry - D.trade_date).dt.days; D["ad"] = D.delta.abs(); D["dd"] = (D.dte - 7).abs()
        D = D[D.dd == D.groupby("trade_date").dd.transform("min")]
        D = D[D.expiry == D.groupby("trade_date").expiry.transform("min")]
        es = earn[earn.ticker == tk].session.values
        for leg, (tgt, tol) in {"N10": (0.10, 0.025), "N05": (0.05, 0.015)}.items():
            x = D[(D.ad - tgt).abs() <= tol].copy(); x["err"] = (x.ad - tgt).abs()
            x = x.sort_values("err").drop_duplicates("trade_date")
            x["S0"] = S.reindex(x.trade_date).values
            ei = S.index.searchsorted(x.expiry.values, side="right") - 1
            x["ST"] = S.values[ei]
            x = x.dropna(subset=["S0", "ST"])
            for sd in split_dates.get(tk, []):          # a trade spanning a split date cannot be settled cleanly
                x = x[~((x.trade_date < sd) & (x.expiry >= sd))]
            x["calm"] = calm.reindex(x.trade_date).fillna(False).values
            if tk in B and len(es):
                has = np.array([((es > t) & (es <= e)).any() or ((es == t)).any() for t, e in zip(x.trade_date.values, x.expiry.values)])
                x = x[~has]
            mid = (x.bid + x.ask) / 2
            x["gross"] = (mid - np.maximum(x.strike - x.ST, 0)) / x.S0 * 1e4
            x["net"] = (mid - SLIP * (x.ask - x.bid) - COMM - np.maximum(x.strike - x.ST, 0)) / x.S0 * 1e4
            r = irx.reindex(x.trade_date).values
            x["excess"] = x.net - x.ad * ((x.ST - x.S0) / x.S0 - r * x.dte / 365) * 1e4
            x["ba_pct"] = (x.ask - x.bid) / mid
            x["tk"], x["leg"], x["univ"] = tk, leg, "A" if tk in A else "B"
            rows.append(x[x.calm])
        if jumps:
            print(f"  note {tk}: {jumps} daily moves > 35% in the raw series (real moves, kept)")
    X = pd.concat(rows, ignore_index=True)
    per = []
    for (u, leg, tk), g in X.groupby(["univ", "leg", "tk"]):
        mu, t = mclust(g.excess, g.trade_date); nn, tn = mclust(g.net, g.trade_date)
        per.append(dict(univ=u, leg=leg, tk=tk, n=len(g), yrs=f"{g.trade_date.dt.year.min()}-{g.trade_date.dt.year.max() % 100}",
                        gross=g.gross.mean(), net=nn, t_net=tn, excess=mu, t_excess=t, win=100 * (g.net > 0).mean(),
                        worst=g.net.min(), ba_med=g.ba_pct.median(), cost_share=1 - g.net.mean() / g.gross.mean() if g.gross.mean() > 0 else np.nan))
    P = pd.DataFrame(per)
    print("== per ticker, CALM Fridays (bp of the ticker's notional per trade) ==")
    print(P.round(2).to_string(index=False))
    print("\n== POOLED (each Friday = mean across tickers; dates are the unit) ==")
    pooled = []
    for (u, leg), g in X.groupby(["univ", "leg"]):
        d = g.groupby("trade_date")[["excess", "net", "gross"]].mean()
        mu, t = mclust(d.excess, d.index); nn, tn = mclust(d.net, d.index)
        h1, h2 = d[d.index < "2018-01-01"].excess.mean(), d[d.index >= "2018-01-01"].excess.mean()
        pooled.append(dict(univ=u, leg=leg, fridays=len(d), gross=d.gross.mean(), net=nn, t_net=tn, excess=mu, t_excess=t, h1=h1, h2=h2))
    Pl = pd.DataFrame(pooled); print(Pl.round(2).to_string(index=False))
    p = Pl[(Pl.univ == "A") & (Pl.leg == "N10")].iloc[0]
    ok = p.t_excess >= 3 and p.h1 > 0 and p.h2 > 0
    print(f"\nPRIMARY (universe A, 10-delta): pooled excess {p.excess:+.2f} bp t {p.t_excess:+.2f}, halves {p.h1:+.2f}/{p.h2:+.2f} -> "
          f"{'CARRIES to uncorrelated ETFs' if ok else 'DOES NOT CARRY'}")
    # diversification: P&L in SPY's 20 worst weeks
    spy = px["SPY"].dropna(); fr = spy[spy.index.dayofweek == 4]
    wk = (spy.shift(-5).reindex(fr.index) / fr - 1).dropna().sort_values().head(20).index
    Xw = X[(X.leg == "N10") & X.trade_date.isin(wk)]
    print(f"\nmean 10-delta net bp in SPY's 20 worst forward weeks (entry Fridays; CALM-only trades): ")
    print(Xw.groupby("tk").net.agg(["mean", "size"]).round(1).T.to_string())
    X.to_csv("data/studies/logs/calm_weekly_put_panel_trades.csv", index=False)


if __name__ == "__main__":
    main()

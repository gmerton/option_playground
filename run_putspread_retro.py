#!/usr/bin/env python3
"""
Retrospective: Gabe's put spreads vs the same delta in stock, size-neutral (descriptive, 2026-10-04).

Gabe: put spreads are one of the more profitable plays in the book (Performance page: 46 trades, 70% closed winners,
+$2,871 combined). Our research says single-name put spreads are mostly delta in disguise (OptionsPlay spec vs
delta-matched stock t -2.21; paid-to-wait spread - delta-matched stock -9.1pp, t -3.21). Question: did these spreads
beat simply holding their delta in the stock over the same days?

ROWS: the Put Spreads card's own membership (run_trade_review_pages._strategy_rows with the put_spreads spec, campaign-
  deduped), CLOSED only (open ones listed, not scored).
LEGS: the campaign's ORIGINAL opening legs (first trade date): put strikes, sides, quantities, fill prices, expiry.
DELTA at entry: implied vol backed out of each leg's fill price (Black-Scholes, r = 4%, q = 0, T = calendar days / 365),
  underlying = the 1-minute bar at the fill minute when cached locally, else that day's close (yfinance, unadjusted).
  Position delta (shares) = sum over legs of side x qty x 100 x put delta (a bull put spread is net long delta).
CAPITAL BASIS: max risk = (width - net credit) x 100 x contracts (credit spreads); debit spreads: the debit.
COMPARISON over the SAME window (entry date -> exit date, or expiry if it expired):
  SPREAD  realized P&L (Flex, net of commissions; includes any rolls)
  STOCK   position delta x (close on the exit date - entry underlying price)        -- the delta-matched stock
  SPY     the same DOLLAR delta in SPY: delta x entry price x SPY return over the window
  All as % of max risk; paired differences with t clustered by entry date; dollar totals; by credit / debit, by expiry
  outcome. Descriptive: the journal is admissible for execution / vehicle realism, not as proof of an edge.

  PYTHONPATH=src:. .venv/bin/python3 run_putspread_retro.py
"""
from __future__ import annotations

import json
from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from lib.mysql_lib import _get_conn
from run_trade_review_pages import STRATEGIES, _strategy_rows

OUT = "data/studies/putspread_retro_2026-10-04"
R_RATE = 0.04


def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))


def bs_put(S, K, T, v, r=R_RATE):
    if T <= 0 or v <= 0:
        return max(K - S, 0.0)
    d1 = (log(S / K) + (r + v * v / 2) * T) / (v * sqrt(T)); d2 = d1 - v * sqrt(T)
    return K * exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)


def put_delta(S, K, T, price, r=R_RATE):
    lo, hi = 0.01, 5.0
    intrinsic = max(K * exp(-r * T) - S, 0)
    if price <= intrinsic + 1e-6:
        return -1.0 if K > S else 0.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if bs_put(S, K, T, mid) > price: hi = mid
        else: lo = mid
    v = (lo + hi) / 2
    d1 = (log(S / K) + (r + v * v / 2) * T) / (v * sqrt(T))
    return ncdf(d1) - 1


def spot_at(sym, ts, daily):
    f = Path(f"data/cache/intraday_1min/{sym}_{ts.date()}.parquet")
    if f.exists():
        try:
            b = pd.read_parquet(f)
            if not isinstance(b.index, pd.DatetimeIndex):
                b = b.set_index(pd.to_datetime(b["timestamp"]))
            col = "close" if "close" in b.columns else "price"
            s = b[col][b.index <= ts.tz_localize(None) if ts.tzinfo else b.index <= ts]
            if len(s):
                return float(s.iloc[-1])
        except Exception:
            pass
    d = daily.get(sym)
    if d is not None:
        v = d[d.index <= pd.Timestamp(ts.date())]
        if len(v):
            return float(v.iloc[-1])
    return np.nan


def main() -> None:
    rows = json.load(open("data/journal/trade_reviews_data.json"))["rows"]
    spec = next(s for s in STRATEGIES if s["key"] == "put_spreads")
    srows = _strategy_rows(rows, spec)
    conn = _get_conn()
    ids = sorted({r["campaignId"] for r in srows if r.get("campaignId") is not None})
    ph = ",".join(["%s"] * len(ids))
    legs = pd.read_sql(f"""SELECT ct.campaign_id, t.put_call, t.strike, t.expiry, t.buy_sell, t.quantity, t.trade_price,
                                  t.trade_date, t.trade_datetime, t.underlying_symbol
                           FROM journal_campaign_trades ct JOIN journal_trades t ON t.trade_id = ct.trade_id
                           WHERE ct.campaign_id IN ({ph}) AND t.open_close IN ('O','C;O') AND t.asset_category='OPT'""", conn, params=ids)
    conn.close()
    legs["trade_date"] = pd.to_datetime(legs.trade_date); legs["expiry"] = pd.to_datetime(legs.expiry)
    legs["trade_datetime"] = pd.to_datetime(legs.trade_datetime)
    syms = sorted(set(legs.underlying_symbol) | {"SPY"})
    px = yf.download(syms, start="2026-07-01", end=pd.Timestamp.today() + pd.Timedelta(days=1), auto_adjust=False, progress=False, group_by="ticker")
    daily = {s: px[s]["Close"].dropna() for s in syms if s in px.columns.get_level_values(0)}
    for s in daily:
        daily[s].index = pd.to_datetime(daily[s].index).tz_localize(None)
    out = []
    for r in srows:
        cid = r.get("campaignId")
        g = legs[legs.campaign_id == cid]
        if g.empty:
            continue
        g = g[g.trade_date == g.trade_date.min()]
        g = g[g.put_call == "P"]
        if len(g) < 2:
            continue
        sym = g.underlying_symbol.iloc[0]; t0 = g.trade_datetime.min(); exp_ = g.expiry.max()
        S0 = spot_at(sym, t0, daily)
        T = max((exp_ - pd.Timestamp(t0.date())).days, 1) / 365
        delta, credit, contracts = 0.0, 0.0, 0.0
        for l in g.itertuples():
            q = abs(float(l.quantity)); side = 1 if l.buy_sell == "BUY" else -1
            d = put_delta(S0, float(l.strike), T, float(l.trade_price))
            delta += side * q * 100 * d
            credit += -side * q * float(l.trade_price) * 100
            contracts = max(contracts, q)
        ks = sorted(g.strike.astype(float).unique())
        width = (ks[-1] - ks[0]) * 100 * contracts
        max_risk = width - credit if credit > 0 else -credit
        ex = pd.Timestamp(r["exitDate"]) if r.get("exitDate") else None
        closed = ex is not None
        rec = dict(tk=sym, entry=pd.Timestamp(t0.date()), exit=ex, expiry=exp_, contracts=contracts, credit=credit, width=width,
                   max_risk=max_risk, delta_sh=delta, S0=S0, realized=r.get("realizedPnl"), closed=closed)
        if closed and max_risk > 0 and np.isfinite(S0):
            s = daily.get(sym); spy = daily.get("SPY")
            S1 = float(s[s.index <= ex].iloc[-1]) if s is not None and len(s[s.index <= ex]) else np.nan
            spy0 = float(spy[spy.index <= rec["entry"]].iloc[-1]); spy1 = float(spy[spy.index <= ex].iloc[-1])
            stock = delta * (S1 - S0); spyp = delta * S0 * (spy1 / spy0 - 1)
            rec.update(S1=S1, stock=stock, spy=spyp, spread_pct=r["realizedPnl"] / max_risk * 100, stock_pct=stock / max_risk * 100,
                       spy_pct=spyp / max_risk * 100, days=(ex - rec["entry"]).days)
        out.append(rec)
    D = pd.DataFrame(out)
    D.to_csv(f"{OUT}_trades.csv", index=False)
    C = D[D.closed & D.spread_pct.notna()].copy()

    def ct(x, g):
        n = len(x); mu = x.mean(); s = (x - mu).groupby(g).sum(); G = len(s)
        se = np.sqrt((s ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1)); return mu, mu / se if se > 0 else np.nan, n
    a = ct(C.spread_pct - C.stock_pct, C.entry); b = ct(C.spread_pct - C.spy_pct, C.entry)
    L = [f"# Put spreads vs the same delta in stock ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(D)} put-spread campaigns on the card; {len(C)} closed and scored ({(~D.closed).sum()} open, not scored). "
         f"Entries {C.entry.min().date()} → {C.entry.max().date()}; median hold {C.days.median():.0f} days; median position delta {C.delta_sh.median():.0f} shares.", "",
         "| per trade, % of max risk | mean | median | win |", "|---|---|---|---|",
         f"| put spread (realized) | {C.spread_pct.mean():+.1f}% | {C.spread_pct.median():+.1f}% | {(C.spread_pct > 0).mean():.0%} |",
         f"| same delta in the stock | {C.stock_pct.mean():+.1f}% | {C.stock_pct.median():+.1f}% | {(C.stock_pct > 0).mean():.0%} |",
         f"| same dollar delta in SPY | {C.spy_pct.mean():+.1f}% | {C.spy_pct.median():+.1f}% | {(C.spy_pct > 0).mean():.0%} |", "",
         f"- **spread − delta-matched stock: {a[0]:+.1f}pp per trade, t {a[1]:.2f}** (clustered by entry date, n {a[2]}); spread better on {(C.spread_pct > C.stock_pct).mean():.0%}",
         f"- spread − SPY at the same dollar delta: {b[0]:+.1f}pp, t {b[1]:.2f}",
         f"- dollars: spreads {C.realized.sum():+,.0f} vs delta-matched stock {C.stock.sum():+,.0f} vs SPY {C.spy.sum():+,.0f}; total max risk {C.max_risk.sum():,.0f}",
         f"- when the stock FELL over the hold (n {(C.S1 < C.S0).sum()}): spread {C[C.S1 < C.S0].spread_pct.mean():+.1f}% vs stock {C[C.S1 < C.S0].stock_pct.mean():+.1f}%; "
         f"when it ROSE (n {(C.S1 >= C.S0).sum()}): spread {C[C.S1 >= C.S0].spread_pct.mean():+.1f}% vs stock {C[C.S1 >= C.S0].stock_pct.mean():+.1f}%",
         "", "⚠ Delta is backed out of fill prices with Black-Scholes (r 4%, no dividends); underlying = the fill-minute bar when cached, else the day's close. Two months, one up-trending tape.",
         "", "## Trades", "",
         D[["tk", "entry", "exit", "expiry", "contracts", "credit", "max_risk", "delta_sh", "realized", "stock", "spy", "spread_pct", "stock_pct"]]
         .assign(entry=lambda z: z.entry.dt.date, exit=lambda z: z.exit.dt.date, expiry=lambda z: z.expiry.dt.date).round(1).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()

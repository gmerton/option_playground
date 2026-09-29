#!/usr/bin/env python3
"""
DESCRIPTIVE (not a test): last month's precision-tier breakout list (2026-08-28 -> 2026-09-28, one position per name,
data/watchlist/backtest_precision_month_2026-09-28_one_per_name.csv) traded as the house STOCK trade vs a BULL PUT
SPREAD on the same entry close. The full-history test already exists (breakout_putspread_vs_stock_2026-09-24.md:
spread vs stock NULL leaning stock, t -1.77); this is one month of it, for Gabe's live list.

APPROXIMATIONS (forced by the data; stated up front):
  - v3 has NO bid/ask or deltas after ~Mar 2026, only daily trade prints ('last', with 'volume'). Legs are priced at
    the day's print; cost = 25% of an ASSUMED bid-ask of 8% of the print per leg + $0.0065/share/leg (house model).
  - Delta: ATM implied vol from the at-the-money put print (Black-Scholes, r = T-bill, q = 0); strikes chosen where the
    flat-IV put delta is nearest 0.30 (short) and 0.15 (long). A flat smile puts the strikes slightly further OTM
    than true 0.30/0.15 deltas (real OTM put IV is higher).
  - Expiry nearest 30 DTE in [20, 45]. Held to expiry (as in the full-history study); expiries after 2026-09-25 (the
    last v3 date) are MARKED at the 9/25 prints. The stock arm uses the house rule, marked at 9/25 if still open.
  - Equal risk: each trade sized to $500 of risk -- stock: (entry - stop) x shares; spread: (width - credit) x 100.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_breakout_month_stock_vs_putspread.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

from lib.athena_lib import athena

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
MARK = pd.Timestamp("2026-09-25")
RISK = 500.0
SPREAD_PCT, SLIP, COMM = 0.08, 0.25, 0.0065


def bs_put(S, K, T, r, s):
    d1 = (np.log(S / K) + (r + 0.5 * s * s) * T) / (s * np.sqrt(T)); d2 = d1 - s * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def put_delta(S, K, T, r, s):
    return norm.cdf((np.log(S / K) + (r + 0.5 * s * s) * T) / (s * np.sqrt(T))) - 1


def iv(P, S, K, T, r):
    lo, hi = 0.01, 5.0
    for _ in range(80):
        m = (lo + hi) / 2
        if bs_put(S, K, T, r, m) > P: hi = m
        else: lo = m
    return (lo + hi) / 2


def main():
    import yfinance as yf
    T = pd.read_csv("data/watchlist/backtest_precision_month_2026-09-28_one_per_name.csv", parse_dates=["entry_date"])
    T = T[T.entry_date <= MARK].copy()          # 9/28 entries have no option prints yet
    tick = sorted(T.ticker.unique())
    dates = sorted(set(T.entry_date.dt.date.astype(str)) | {str(MARK.date())})
    q = f"""SELECT ticker, trade_date, expiry, CAST(strike AS DOUBLE) strike, CAST(last AS DOUBLE) last, volume
            FROM silver.options_daily_v3 WHERE ticker IN ({','.join(repr(t) for t in tick)})
            AND trade_date IN ({','.join(f"DATE '{d}'" for d in dates)}) AND upper(substr(cp,1,1))='P'
            AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 50"""
    Q = athena(q); Q["trade_date"] = pd.to_datetime(Q.trade_date); Q["expiry"] = pd.to_datetime(Q.expiry)
    px = yf.download(tick, start="2026-08-20", end="2026-09-30", progress=False, auto_adjust=False)["Close"]
    irx = yf.download("^IRX", start="2026-08-20", end="2026-09-30", progress=False, auto_adjust=False)["Close"].squeeze() / 100
    rows = []
    for r in T.itertuples():
        d, t = r.entry_date, r.ticker
        S0 = r.entry; rr = float(irx.asof(d))
        g = Q[(Q.ticker == t) & (Q.trade_date == d) & (Q["last"] > 0)]
        g = g.assign(dte=(g.expiry - d).dt.days)
        g = g[(g.dte >= 20) & (g.dte <= 45)]
        sR = r.R
        if str(r.exit_date) == "OPEN" or pd.Timestamp(r.exit_date) > MARK:   # align the stock mark with the spread (9/25)
            p925 = float(px[t].asof(MARK)); sR = round((p925 - r.entry) / (r.entry - r.stop), 2)
        rec = dict(ticker=t, entry_date=d.date(), stock_R=sR, stock_exit=r.exit_date if sR == r.R else "mark 9/25")
        if g.empty:
            rows.append({**rec, "note": "no printed puts 20-45 DTE"}); continue
        ex = g.loc[(g.dte - 30).abs().idxmin(), "expiry"]; g = g[g.expiry == ex]
        Tt = (ex - d).days / 365
        atm = g.loc[(g.strike - S0).abs().idxmin()]
        sig = iv(atm["last"], S0, atm.strike, Tt, rr)
        g = g.assign(delta=put_delta(S0, g.strike.values, Tt, rr, sig))
        sh = g.loc[(g.delta + 0.30).abs().idxmin()]; lg = g[g.strike < sh.strike]
        if lg.empty:
            rows.append({**rec, "note": "no long strike"}); continue
        lg = lg.loc[(lg.delta + 0.15).abs().idxmin()]
        cost = SLIP * SPREAD_PCT * (sh["last"] + lg["last"]) + 2 * COMM
        credit = sh["last"] - lg["last"] - cost
        width = sh.strike - lg.strike; risk = width - credit
        if risk <= 0 or credit <= 0:
            rows.append({**rec, "note": f"bad spread credit {credit:.2f} width {width:.2f}"}); continue
        if ex <= MARK:
            St = float(px[t].asof(ex)); value = max(sh.strike - St, 0) - max(lg.strike - St, 0); how = f"expired {ex.date()} @ {St:.2f}"
        else:
            m = Q[(Q.ticker == t) & (Q.trade_date == MARK) & (Q.expiry == ex)].set_index("strike")["last"]
            if sh.strike in m.index and lg.strike in m.index:
                value = m[sh.strike] - m[lg.strike] + SLIP * SPREAD_PCT * (m[sh.strike] + m[lg.strike]) + 2 * COMM
                how = f"marked 9/25 (exp {ex.date()})"
            else:
                St = float(px[t].asof(MARK))
                value = max(sh.strike - St, 0) - max(lg.strike - St, 0); how = f"no 9/25 print: intrinsic @ {St:.2f}"
        pnl = credit - value
        rec.update(expiry=ex.date(), atm_iv=round(sig, 3), short_K=sh.strike, long_K=lg.strike, credit=round(credit, 2),
                   width=width, spread_R=round(pnl / risk, 2), spread_how=how,
                   stock_usd=round(sR * RISK, 0), spread_usd=round(pnl / risk * RISK, 0), note="")
        rows.append(rec)
    X = pd.DataFrame(rows)
    print(X.to_string(index=False))
    ok = X.dropna(subset=["spread_R"])
    print(f"\ncomparable trades {len(ok)} of {len(X)} (at ${RISK:.0f} risk each):")
    print(f"  STOCK  total ${ok.stock_usd.sum():+,.0f} | mean R {ok.stock_R.mean():+.2f} | winners {(ok.stock_R > 0).sum()}")
    print(f"  SPREAD total ${ok.spread_usd.sum():+,.0f} | mean R {ok.spread_R.mean():+.2f} | winners {(ok.spread_R > 0).sum()}")
    X.to_csv("data/watchlist/breakout_month_stock_vs_putspread_2026-09-28.csv", index=False)


if __name__ == "__main__":
    main()

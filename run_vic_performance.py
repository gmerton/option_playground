"""Performance to date of every captured Value Investors Club idea.

Input:  data/vic/index.csv (from run_vic_parse.py) + data/vic/symbol_map.csv (VIC ticker -> priceable symbol; edit by hand
        when a new idea's ticker does not resolve -- the script lists any unmapped ticker and skips it).
Output: data/vic/performance.csv -- one row per idea: author, ticker, direction, post date, and its performance to date.

Definitions
  entry      first close ON OR AFTER the post date (VIC does not give a post time, so the post-date close is the earliest
             price a reader could have had). vic_price = the price printed on the write-up, for reference.
  stock_ret  last close / entry close - 1, on dividend- and split-adjusted closes (total return) where the source has them
             (Yahoo); Tradier symbols are price-only.
  pos_ret    stock_ret for a long, -stock_ret for a short (no borrow cost, no dividends paid on the short leg).
  spy_ret    SPY total return over the same dates -- the control.
  excess     direction x (stock_ret - spy_ret): the position's return beyond the market move it carried.
  Returns are in the listing's own currency (see currency); SPY is USD, so excess on non-USD listings includes FX.
Idempotent: re-run any day to refresh "to date".

Run: PYTHONPATH=src .venv/bin/python3 run_vic_performance.py
"""
import csv
import os
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parent / "data" / "vic"
COLS = ["idea_id", "author", "ticker", "direction", "post_date", "company", "symbol", "currency", "vic_price",
        "entry_date", "entry_close", "last_date", "last_close", "days", "stock_ret", "pos_ret", "spy_ret", "excess", "url"]


def yahoo(sym: str, start: str) -> tuple[pd.Series, str]:
    t = yf.Ticker(sym)
    h = t.history(start=start, auto_adjust=True)
    cur = (t.fast_info.get("currency") or "").upper() if h is not None else ""
    return h["Close"].dropna(), cur


def tradier(sym: str, start: str) -> tuple[pd.Series, str]:
    r = requests.get("https://api.tradier.com/v1/markets/history",
                     params=dict(symbol=sym, interval="daily", start=start, end=date.today().isoformat()),
                     headers={"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"},
                     timeout=30)
    r.raise_for_status()
    days = (r.json().get("history") or {}).get("day") or []
    days = days if isinstance(days, list) else [days]
    s = pd.Series({pd.Timestamp(d["date"]): float(d["close"]) for d in days}).dropna()
    return s, "USD"


def window(s: pd.Series, start: str) -> pd.Series:
    s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
    return s[s.index >= pd.Timestamp(start)]


def main():
    ideas = pd.read_csv(ROOT / "index.csv", dtype=str)
    smap = pd.read_csv(ROOT / "symbol_map.csv", dtype=str).set_index("vic_ticker")
    spy, _ = yahoo("SPY", ideas.post_date.min())
    spy = window(spy, ideas.post_date.min())
    rows = []
    for r in ideas.itertuples():
        if r.ticker not in smap.index:
            print(f"UNMAPPED {r.ticker} ({r.company}) -- add it to symbol_map.csv"); continue
        m = smap.loc[r.ticker]
        px, cur = (tradier if m.source == "tradier" else yahoo)(m.symbol, r.post_date)
        px = window(px, r.post_date)
        if len(px) < 1:
            print(f"NO PRICES {r.ticker} -> {m.symbol}"); continue
        e_d, l_d = px.index[0], px.index[-1]
        s = spy[(spy.index >= e_d) & (spy.index <= l_d)]
        sgn = -1 if r.side == "short" else 1
        stock = px.iloc[-1] / px.iloc[0] - 1
        spy_r = s.iloc[-1] / s.iloc[0] - 1
        rows.append(dict(idea_id=r.idea_id, author=r.author, ticker=r.ticker, direction=r.side, post_date=r.post_date,
                         company=r.company, symbol=m.symbol, currency=cur, vic_price=r.price,
                         entry_date=e_d.date(), entry_close=round(px.iloc[0], 4), last_date=l_d.date(),
                         last_close=round(px.iloc[-1], 4), days=(l_d - e_d).days, stock_ret=round(stock, 4),
                         pos_ret=round(sgn * stock, 4), spy_ret=round(spy_r, 4), excess=round(sgn * (stock - spy_r), 4),
                         url=r.url))
    rows.sort(key=lambda x: x["post_date"], reverse=True)
    with open(ROOT / "performance.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} of {len(ideas)} ideas -> {ROOT / 'performance.csv'}")


if __name__ == "__main__":
    main()

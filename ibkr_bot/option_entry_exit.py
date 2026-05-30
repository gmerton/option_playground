#!/usr/bin/env python3
"""
Replay the proposed PHB trades as CALL options, pulling option quotes only at the
entry and exit timestamps (not full-day series) to keep API calls minimal.

For each winner: derive the trigger entry time from the cached 1-min bars, take
exit = session close, pick the ATM call at the target expiry, and pull a single
BID_ASK 1-min bar at each of the two timestamps. Then model the round-trip:
buy at the entry ask, sell at the exit bid -> realized option P&L net of spread,
next to the stock move for comparison.

Two small historical requests per name (+ one chain lookup). ATM only for now;
expand to a delta ladder once we know which names are liquid enough.

Usage:
  .venv/bin/python3 ibkr_bot/option_entry_exit.py CIEN IBM DDOG SNOW PANW APP --expiry 20260605
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators  # noqa: E402
from conn import connect_ib  # noqa: E402
from ib_async import Option, Stock  # noqa: E402
import power_hour_trigger as pht  # noqa: E402

DATA_DIR = os.path.join(HERE, "data")
pht.SCAN_START, pht.SCAN_END = "14:30", "15:30"   # intraday-flat window


def _session(sym: str):
    hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{sym}_*_1min.csv")))
    if not hits:
        return None
    df = pd.read_csv(hits[-1], parse_dates=["time"])
    day = df["time"].dt.date.iloc[-1]
    return add_indicators(df[df["time"].dt.date == day].reset_index(drop=True))


def _ba_bar(ib, opt, when) -> dict | None:
    """BID_ASK bar(s) around minute `when`. For BID_ASK bars: high=max ask,
    low=min bid -> use the band for a conservative, real spread. Falls back to a
    wider window if the exact minute is empty (thin options)."""
    for dur in ("180 S", "600 S"):
        end = (when + pd.Timedelta(minutes=1)).to_pydatetime()
        try:
            bars = ib.reqHistoricalData(opt, endDateTime=end, durationStr=dur,
                                        barSizeSetting="1 min", whatToShow="BID_ASK",
                                        useRTH=False, timeout=20) or []
        except Exception:
            bars = []
        if bars:
            b = bars[-1]
            ask, bid = b.high, b.low      # max ask / min bid within the minute
            if ask <= 0 or bid <= 0:
                continue
            return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2,
                    "spread_pct": (ask - bid) / ((ask + bid) / 2) * 100}
    return None


def replay(ib, sym: str, expiry: str) -> dict:
    sess = _session(sym)
    if sess is None:
        return {"symbol": sym, "err": "no cached CSV"}
    trig = pht.find_trigger(sess)
    if not trig:
        return {"symbol": sym, "err": "no trigger fired"}
    i = trig["i"]
    entry_t = sess["time"].iloc[i]
    exit_t = sess["time"].iloc[-1]
    entry_px, exit_px = sess["close"].iloc[i], sess["close"].iloc[-1]

    stk = Stock(sym, "SMART", "USD"); ib.qualifyContracts(stk)
    chains = ib.reqSecDefOptParams(stk.symbol, "", stk.secType, stk.conId)
    chain = next((c for c in chains if c.exchange == "SMART"), chains[0])
    if expiry not in chain.expirations:
        return {"symbol": sym, "err": f"no {expiry} expiry"}
    strike = min(chain.strikes, key=lambda s: abs(s - entry_px))
    opt = Option(sym, expiry, strike, "C", "SMART", tradingClass=chain.tradingClass)
    if not ib.qualifyContracts(opt) or not opt.conId:
        return {"symbol": sym, "err": f"no ATM call (~{strike})"}

    en = _ba_bar(ib, opt, entry_t)
    ex = _ba_bar(ib, opt, exit_t)
    out = {"symbol": sym, "strike": strike,
           "entry_t": entry_t.strftime("%H:%M"), "exit_t": exit_t.strftime("%H:%M"),
           "stock_move": round((exit_px / entry_px - 1) * 100, 2), "en": en, "ex": ex}
    if en and ex and en["ask"] and ex["bid"]:
        buy, sell = en["ask"], ex["bid"]       # pay ask in, hit bid out
        out["opt_pnl_pct"] = round((sell / buy - 1) * 100, 1)
        out["leverage"] = round((sell / buy - 1) / (out["stock_move"] / 100), 1) if out["stock_move"] else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiry", required=True, help="YYYYMMDD")
    a = ap.parse_args()

    ib = connect_ib(client_id=26)
    ib.reqMarketDataType(2)
    print(f"OK Connected (paper {ib.managedAccounts()}). ATM calls exp {a.expiry}\n")
    rows = []
    for s in a.symbols:
        rows.append(replay(ib, s.upper(), a.expiry))
        ib.sleep(1)
    ib.disconnect()

    hdr = (f"{'sym':<6}{'strike':>8}{'entry':>7}{'exit':>6}{'stk%':>7}"
           f"{'  buy(ask)':>11}{'sell(bid)':>10}{'enSpr%':>8}{'opt%':>8}{'lever':>7}")
    print(hdr); print("-" * len(hdr))
    for r in rows:
        if "err" in r:
            print(f"{r['symbol']:<6}  -- {r['err']}")
            continue
        en, ex = r.get("en"), r.get("ex")
        buy = f"{en['ask']:.2f}" if en else "n/a"
        sell = f"{ex['bid']:.2f}" if ex else "n/a"
        ensp = f"{en['spread_pct']:.1f}" if en and en["spread_pct"] is not None else "n/a"
        op = f"{r['opt_pnl_pct']:+.1f}" if "opt_pnl_pct" in r else "n/a"
        lev = f"{r['leverage']}" if r.get("leverage") is not None else "n/a"
        print(f"{r['symbol']:<6}{r['strike']:>8.1f}{r['entry_t']:>7}{r['exit_t']:>6}"
              f"{r['stock_move']:>+7.2f}{buy:>11}{sell:>10}{ensp:>8}{op:>8}{lev:>7}")
    print("\nopt% = round-trip buying entry ask / selling exit bid (real spread cost included); "
          "lever = opt% / stock-move%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

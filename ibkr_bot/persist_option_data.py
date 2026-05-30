#!/usr/bin/env python3
"""
Persist today's intraday option data to CSV before it ages out of IBKR.

For each name, picks calls across a delta ladder (0.80/0.65/0.50/0.35 via EOD
greeks) and saves the FULL afternoon 1-min BID_ASK path of each -- so any future
delta or exit-rule (trailing stop, different times) analysis is reproducible
offline. Writes two files under ibkr_bot/data/options/:
  phb_option_bars_<DATE>.csv  -- long: symbol,expiry,strike,delta_eod,time,bid,ask
  phb_option_meta_<DATE>.csv  -- per strike: greeks + trigger entry/exit + stock px

Usage:
  .venv/bin/python3 ibkr_bot/persist_option_data.py CIEN IBM DDOG PANW CSCO KLAR NVDA --expiry 20260605
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
OUT_DIR = os.path.join(DATA_DIR, "options")
pht.SCAN_START, pht.SCAN_END = "14:30", "15:30"
TARGETS = [0.80, 0.65, 0.50, 0.35]


def _session(sym):
    hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{sym}_*_1min.csv")))
    if not hits:
        return None
    df = pd.read_csv(hits[-1], parse_dates=["time"])
    day = df["time"].dt.date.iloc[-1]
    return add_indicators(df[df["time"].dt.date == day].reset_index(drop=True)), day


def _entry_exit(sess):
    """Trigger entry (filter on; fall back to filter-off for rejected names) + vwap exit."""
    for mvd, tag in ((1.0, "fired"), (0.0, "filtered_out")):
        pht.MIN_VWAP_DIST = mvd
        t = pht.find_trigger(sess)
        if t:
            i = t["i"]
            xt, _, reason = pht.simulate_exit(sess, i, "vwap")
            return {"entry_t": sess["time"].iloc[i].strftime("%H:%M"),
                    "exit_t": xt, "exit_reason": reason,
                    "stk_entry": round(sess["close"].iloc[i], 2),
                    "stk_exit": round(sess["close"].iloc[sess.index[
                        sess["time"].dt.strftime("%H:%M") == xt][-1]], 2),
                    "fire": tag, "entry_px": sess["close"].iloc[i]}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiry", required=True)
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    ib = connect_ib(client_id=31)
    ib.reqMarketDataType(2)
    print(f"OK Connected (paper {ib.managedAccounts()}). Persisting option data exp {a.expiry}\n")

    bars_rows, meta_rows, day = [], [], None
    for sym in a.symbols:
        sym = sym.upper()
        sd = _session(sym)
        if sd is None:
            print(f"  {sym}: no cached CSV -- skip"); continue
        sess, day = sd
        ee = _entry_exit(sess)
        ref_px = ee["entry_px"] if ee else sess["close"].iloc[-1]

        s = Stock(sym, "SMART", "USD"); ib.qualifyContracts(s)
        chains = ib.reqSecDefOptParams(s.symbol, "", s.secType, s.conId)
        chain = next((c for c in chains if c.exchange == "SMART"), chains[0])
        if a.expiry not in chain.expirations:
            print(f"  {sym}: no {a.expiry} expiry -- skip"); continue

        band = sorted(k for k in chain.strikes if 0.84 * ref_px <= k <= 1.10 * ref_px)
        opts = [Option(sym, a.expiry, k, "C", "SMART", tradingClass=chain.tradingClass) for k in band]
        ib.qualifyContracts(*opts)
        opts = [o for o in opts if o.conId]
        tks = [ib.reqMktData(o, "", False, False) for o in opts]
        ib.sleep(5)
        greeks = {}
        for o, t in zip(opts, tks):
            g = t.modelGreeks
            if g and g.delta:
                greeks[o.strike] = g
            ib.cancelMktData(o)
        if not greeks:
            print(f"  {sym}: no greeks -- skip"); continue

        picks = {}
        for td in TARGETS:
            k = min(greeks, key=lambda x: abs(greeks[x].delta - td))
            picks[k] = round(greeks[k].delta, 2)

        saved = 0
        end = pd.Timestamp(f"{day} 16:00:00", tz="US/Eastern").to_pydatetime()
        for strike, delta in picks.items():
            opt = Option(sym, a.expiry, strike, "C", "SMART", tradingClass=chain.tradingClass)
            ib.qualifyContracts(opt)
            try:
                pbars = ib.reqHistoricalData(opt, endDateTime=end, durationStr="10800 S",
                                             barSizeSetting="1 min", whatToShow="BID_ASK",
                                             useRTH=True, timeout=30) or []
            except Exception:
                pbars = []
            for b in pbars:
                if b.high > 0 and b.low > 0:
                    bars_rows.append({"symbol": sym, "expiry": a.expiry, "strike": strike,
                                      "delta_eod": delta, "time": b.date.strftime("%H:%M"),
                                      "bid": round(b.low, 2), "ask": round(b.high, 2)})
            g = greeks[strike]
            meta_rows.append({"symbol": sym, "expiry": a.expiry, "strike": strike,
                              "delta_eod": delta, "iv": round((g.impliedVol or 0), 3),
                              "gamma": round((g.gamma or 0), 4), "theta": round((g.theta or 0), 3),
                              "bars": len(pbars), **(ee or {})})
            saved += 1
            ib.sleep(1.5)
        print(f"  {sym}: {saved} strikes "
              f"(Δ {sorted(picks.values())}), {'fired '+ee['entry_t'] if ee else 'no trade'}")

    ib.disconnect()
    if not bars_rows:
        print("nothing to write"); return 1
    bpath = os.path.join(OUT_DIR, f"phb_option_bars_{day}.csv")
    mpath = os.path.join(OUT_DIR, f"phb_option_meta_{day}.csv")
    pd.DataFrame(bars_rows).to_csv(bpath, index=False)
    pd.DataFrame(meta_rows).to_csv(mpath, index=False)
    print(f"\nwrote {len(bars_rows)} bar rows -> {bpath}")
    print(f"wrote {len(meta_rows)} strike rows -> {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

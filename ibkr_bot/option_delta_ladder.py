#!/usr/bin/env python3
"""
Delta-ladder replay: for each name, replay the PHB trade as calls at ~0.35 / 0.50
/ 0.65 delta to compare leverage vs premium vs spread and pick an optimal delta.

Per name: derive trigger entry time + exit (close) from cached bars; pull EOD
frozen greeks for a band of call strikes to label deltas; pick the strikes nearest
each target delta; then pull BID_ASK only at the entry and exit minutes for those
strikes (lean -- a few small requests/name). Round-trip = buy entry ask / sell
exit bid; leverage = opt% / stock-move%.

Usage:
  .venv/bin/python3 ibkr_bot/option_delta_ladder.py IBM DDOG PANW --expiry 20260605
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
pht.SCAN_START, pht.SCAN_END = "14:30", "15:30"
TARGET_DELTAS = [0.65, 0.50, 0.35]


def _session(sym):
    hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{sym}_*_1min.csv")))
    if not hits:
        return None
    df = pd.read_csv(hits[-1], parse_dates=["time"])
    day = df["time"].dt.date.iloc[-1]
    return add_indicators(df[df["time"].dt.date == day].reset_index(drop=True))


def _ba_bar(ib, opt, when):
    for dur in ("180 S", "600 S"):
        end = (when + pd.Timedelta(minutes=1)).to_pydatetime()
        try:
            bars = ib.reqHistoricalData(opt, endDateTime=end, durationStr=dur,
                                        barSizeSetting="1 min", whatToShow="BID_ASK",
                                        useRTH=False, timeout=20) or []
        except Exception:
            bars = []
        if bars and bars[-1].high > 0 and bars[-1].low > 0:
            b = bars[-1]
            return {"ask": b.high, "bid": b.low, "mid": (b.high + b.low) / 2,
                    "spread_pct": (b.high - b.low) / ((b.high + b.low) / 2) * 100}
    return None


def _pick_by_delta(ib, sym, expiry, entry_px, chain):
    """Frozen greeks across a strike band -> strike nearest each target delta."""
    band = sorted(s for s in chain.strikes if 0.90 * entry_px <= s <= 1.08 * entry_px)
    opts = [Option(sym, expiry, k, "C", "SMART", tradingClass=chain.tradingClass) for k in band]
    ib.qualifyContracts(*opts)
    opts = [o for o in opts if o.conId]
    tks = [ib.reqMktData(o, "", False, False) for o in opts]
    ib.sleep(5)
    sd = [(o.strike, t.modelGreeks.delta) for o, t in zip(opts, tks)
          if t.modelGreeks and t.modelGreeks.delta]
    for t in tks:
        ib.cancelMktData(t.contract)
    picks = {}
    for td in TARGET_DELTAS:
        if sd:
            k, d = min(sd, key=lambda x: abs(x[1] - td))
            picks[td] = (k, d)
    return picks


def replay(ib, sym, expiry):
    sess = _session(sym)
    if sess is None:
        return {"symbol": sym, "err": "no cached CSV"}
    trig = pht.find_trigger(sess)
    if not trig:
        return {"symbol": sym, "err": "no trigger"}
    i = trig["i"]
    entry_t, exit_t = sess["time"].iloc[i], sess["time"].iloc[-1]
    entry_px, exit_px = sess["close"].iloc[i], sess["close"].iloc[-1]
    stk = (exit_px / entry_px - 1) * 100

    s = Stock(sym, "SMART", "USD"); ib.qualifyContracts(s)
    chains = ib.reqSecDefOptParams(s.symbol, "", s.secType, s.conId)
    chain = next((c for c in chains if c.exchange == "SMART"), chains[0])
    if expiry not in chain.expirations:
        return {"symbol": sym, "err": f"no {expiry} expiry"}

    picks = _pick_by_delta(ib, sym, expiry, entry_px, chain)
    rows = []
    for td, (strike, delta) in picks.items():
        opt = Option(sym, expiry, strike, "C", "SMART", tradingClass=chain.tradingClass)
        ib.qualifyContracts(opt)
        en, ex = _ba_bar(ib, opt, entry_t), _ba_bar(ib, opt, exit_t)
        row = {"target": td, "strike": strike, "delta": round(delta, 2)}
        if en and ex:
            buy, sell = en["ask"], ex["bid"]
            row.update({"prem": round(buy, 2), "enSpr": round(en["spread_pct"], 1),
                        "opt": round((sell / buy - 1) * 100, 1),
                        "lev": round((sell / buy - 1) / (stk / 100), 1) if stk else None})
        rows.append(row)
    return {"symbol": sym, "stk": round(stk, 2), "entry_t": entry_t.strftime("%H:%M"), "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiry", required=True)
    a = ap.parse_args()

    ib = connect_ib(client_id=27)
    ib.reqMarketDataType(2)
    print(f"OK Connected (paper {ib.managedAccounts()}). Delta ladder exp {a.expiry}\n")
    print(f"{'sym':<6}{'stk%':>6}{'tgtΔ':>6}{'strike':>8}{'Δ':>6}{'prem':>8}{'spr%':>6}{'opt%':>8}{'lever':>7}")
    print("-" * 61)
    for sym in a.symbols:
        r = replay(ib, sym.upper(), a.expiry)
        if "err" in r:
            print(f"{sym:<6}  -- {r['err']}")
            continue
        for row in r["rows"]:
            opt = f"{row['opt']:+.1f}" if "opt" in row else "n/a"
            lev = f"{row['lev']}" if row.get("lev") is not None else "n/a"
            prem = f"{row['prem']:.2f}" if "prem" in row else "n/a"
            spr = f"{row['enSpr']:.1f}" if "enSpr" in row else "n/a"
            print(f"{r['symbol']:<6}{r['stk']:>+6.1f}{row['target']:>6.2f}{row['strike']:>8.1f}"
                  f"{row['delta']:>6.2f}{prem:>8}{spr:>6}{opt:>8}{lev:>7}")
        ib.sleep(1)
    ib.disconnect()
    print("\nprem = entry ask (capital/contract ÷100); opt% = round-trip; lever = opt%/stock-move%.")


if __name__ == "__main__":
    raise SystemExit(main())

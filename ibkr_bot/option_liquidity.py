#!/usr/bin/env python3
"""
Quick option-liquidity triage for intraday call scalps.

For each symbol, finds the ATM call at a target expiry and pulls today's intraday
option bars to answer the only question that matters before delta selection:
*can you actually trade this option intraday, and what does the spread cost?*

Reports, for the ATM call:
  - day volume + power-hour (15:00-16:00 ET) volume, in contracts
  - active bars: % of 1-min bars that printed at least one trade (in power hour)
  - typical power-hour bid/ask spread (% of mid), from 1-min BID_ASK bars

Thin names (near-zero power-hour volume, wide spreads) are poor scalp vehicles
however good the underlying signal -- you can't get filled and you pay the spread
round-trip on a 1-4% move.

Usage:
  .venv/bin/python3 ibkr_bot/option_liquidity.py CIEN IBM DDOG SNOW PANW APP --expiry 20260605
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from conn import connect_ib  # noqa: E402
from ib_async import Option, Stock  # noqa: E402

DATA_DIR = os.path.join(HERE, "data")


def _hist(ib, contract, what: str):
    """reqHistoricalData wrapped so one timeout doesn't kill the run."""
    try:
        return ib.reqHistoricalData(contract, endDateTime="", durationStr="1 D",
                                    barSizeSetting="5 mins", whatToShow=what,
                                    useRTH=True, timeout=30) or []
    except Exception:
        return []


def _spot(ib, sym: str) -> float | None:
    # prefer a cached intraday CSV close (no API request); fall back to a daily bar
    hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{sym}_*_1min.csv")))
    if hits:
        return float(pd.read_csv(hits[-1])["close"].iloc[-1])
    stk = Stock(sym, "SMART", "USD")
    if not ib.qualifyContracts(stk):
        return None
    bars = _hist(ib, stk, "TRADES")
    return bars[-1].close if bars else None


def _atm_call(ib, sym: str, spot: float, expiry: str):
    stk = Stock(sym, "SMART", "USD"); ib.qualifyContracts(stk)
    chains = ib.reqSecDefOptParams(stk.symbol, "", stk.secType, stk.conId)
    chain = next((c for c in chains if c.exchange == "SMART"), chains[0])
    if expiry not in chain.expirations:
        return None, None
    strike = min(chain.strikes, key=lambda s: abs(s - spot))
    opt = Option(sym, expiry, strike, "C", "SMART", tradingClass=chain.tradingClass)
    if not ib.qualifyContracts(opt) or not opt.conId:
        return None, strike
    return opt, strike


def _power_hour(bars):
    return [b for b in bars if 15 <= b.date.hour < 16]


def triage(ib, sym: str, expiry: str) -> dict:
    spot = _spot(ib, sym)
    if not spot:
        return {"symbol": sym, "err": "no spot"}
    opt, strike = _atm_call(ib, sym, spot, expiry)
    if not opt:
        return {"symbol": sym, "err": f"no ATM call (strike~{strike})"}

    trades = _hist(ib, opt, "TRADES")
    ba = _hist(ib, opt, "BID_ASK")
    day_vol = sum(b.volume for b in trades if b.volume > 0)
    ph = _power_hour(trades)
    ph_vol = sum(b.volume for b in ph if b.volume > 0)
    ph_active = (sum(1 for b in ph if b.volume > 0) / len(ph) * 100) if ph else 0
    # BID_ASK 1-min: low~bid, high~ask within the minute -> spread band
    ph_ba = _power_hour(ba)
    spreads = []
    for b in ph_ba:
        mid = (b.high + b.low) / 2
        if mid > 0 and b.high > b.low:
            spreads.append((b.high - b.low) / mid * 100)
    med_spread = sorted(spreads)[len(spreads) // 2] if spreads else None
    return {"symbol": sym, "spot": round(spot, 2), "strike": strike,
            "day_vol": int(day_vol), "ph_vol": int(ph_vol),
            "ph_active": round(ph_active), "ph_spread": med_spread}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiry", required=True, help="YYYYMMDD")
    a = ap.parse_args()

    ib = connect_ib(client_id=25)
    print(f"OK Connected (paper {ib.managedAccounts()}). ATM calls exp {a.expiry}\n")
    rows = []
    for s in a.symbols:
        rows.append(triage(ib, s.upper(), a.expiry))
        ib.sleep(2)  # pace historical requests to avoid IBKR throttling
    ib.disconnect()

    ok = [r for r in rows if "err" not in r]
    ok.sort(key=lambda r: -r["ph_vol"])
    hdr = f"{'sym':<6}{'spot':>9}{'strike':>8}{'dayVol':>8}{'pwrVol':>8}{'active%':>8}{'spread%':>9}{'verdict':>10}"
    print(hdr); print("-" * len(hdr))
    for r in ok:
        sp = f"{r['ph_spread']:.1f}" if r["ph_spread"] is not None else "n/a"
        # crude verdict: need meaningful power-hour volume AND a tradeable spread
        liquid = r["ph_vol"] >= 50 and r["ph_active"] >= 40 and (r["ph_spread"] or 99) <= 5
        thin = r["ph_vol"] < 10 or (r["ph_spread"] or 99) > 10
        verdict = "OK" if liquid else ("THIN" if thin else "marginal")
        print(f"{r['symbol']:<6}{r['spot']:>9.2f}{r['strike']:>8.1f}{r['day_vol']:>8}"
              f"{r['ph_vol']:>8}{r['ph_active']:>8}{sp:>9}{verdict:>10}")
    for r in rows:
        if "err" in r:
            print(f"{r['symbol']:<6}  -- {r['err']}")
    print("\npwrVol/active% = ATM-call trade volume & fraction of minutes printing in 15:00-16:00 ET; "
          "spread% = median 1-min bid/ask band.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

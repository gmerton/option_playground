#!/usr/bin/env python3
"""
Expectancy-by-delta: replay the FULL set of intraday-flat PHB trades (winners and
losers) as calls at several deltas, exiting each at its real stop/close, and
compute expectancy per delta. This is what actually picks the optimal delta --
leverage helps winners but hurts losers, so the answer needs both.

Per trade: trigger entry + simulate_exit(vwap stop, else close) from the cached
bars; for each target delta, pick the strike via frozen greeks, pull BID_ASK at
the entry and the real exit minute, round-trip = buy ask / sell bid. Aggregate
per delta: win-rate, avg option return (equal-$ per trade), total, profit factor.

Usage:
  .venv/bin/python3 ibkr_bot/option_expectancy.py CIEN IBM DDOG PANW CSCO KLAR FLEX \
      --expiry 20260605 --deltas 0.70,0.50,0.35
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
pht.SCAN_START, pht.SCAN_END, pht.MIN_VWAP_DIST = "14:30", "15:30", 1.0


def _session(sym):
    hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{sym}_*_1min.csv")))
    if not hits:
        return None
    df = pd.read_csv(hits[-1], parse_dates=["time"])
    day = df["time"].dt.date.iloc[-1]
    return add_indicators(df[df["time"].dt.date == day].reset_index(drop=True))


def _ba(ib, opt, when):
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
            return {"ask": b.high, "bid": b.low}
    return None


def _strikes_by_delta(ib, sym, expiry, ref_px, chain, targets):
    band = sorted(s for s in chain.strikes if 0.86 * ref_px <= s <= 1.10 * ref_px)
    opts = [Option(sym, expiry, k, "C", "SMART", tradingClass=chain.tradingClass) for k in band]
    ib.qualifyContracts(*opts)
    opts = [o for o in opts if o.conId]
    tks = [ib.reqMktData(o, "", False, False) for o in opts]
    ib.sleep(5)
    sd = [(o.strike, t.modelGreeks.delta) for o, t in zip(opts, tks)
          if t.modelGreeks and t.modelGreeks.delta]
    for t in tks:
        ib.cancelMktData(t.contract)
    out = {}
    for td in targets:
        if sd:
            k, d = min(sd, key=lambda x: abs(x[1] - td))
            out[td] = (k, round(d, 2))
    return out


def replay(ib, sym, expiry, targets, stop="vwap"):
    sess = _session(sym)
    if sess is None:
        return None
    trig = pht.find_trigger(sess)
    if not trig:
        return None
    i = trig["i"]
    entry_t, entry_px = sess["time"].iloc[i], sess["close"].iloc[i]
    xt_str, exit_px, reason = pht.simulate_exit(sess, i, stop)
    hhmm = sess["time"].dt.strftime("%H:%M")
    exit_idx = sess.index[hhmm == xt_str][-1]
    exit_t = sess["time"].iloc[exit_idx]
    stk = (exit_px / entry_px - 1) * 100

    s = Stock(sym, "SMART", "USD"); ib.qualifyContracts(s)
    chains = ib.reqSecDefOptParams(s.symbol, "", s.secType, s.conId)
    chain = next((c for c in chains if c.exchange == "SMART"), chains[0])
    if expiry not in chain.expirations:
        return None
    picks = _strikes_by_delta(ib, sym, expiry, entry_px, chain, targets)

    res = {"symbol": sym, "stk": round(stk, 2), "reason": reason, "by_delta": {}}
    for td, (strike, delta) in picks.items():
        opt = Option(sym, expiry, strike, "C", "SMART", tradingClass=chain.tradingClass)
        ib.qualifyContracts(opt)
        en, ex = _ba(ib, opt, entry_t), _ba(ib, opt, exit_t)
        if en and ex and en["ask"] > 0:
            res["by_delta"][td] = {"delta": delta, "strike": strike,
                                   "opt": round((ex["bid"] / en["ask"] - 1) * 100, 1)}
        else:
            res["by_delta"][td] = {"delta": delta, "strike": strike, "opt": None}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiry", required=True)
    ap.add_argument("--deltas", default="0.70,0.50,0.35")
    ap.add_argument("--stop", default="vwap", help="vwap | trail:X | pct:X | ema9 | bar_low")
    a = ap.parse_args()
    targets = [float(x) for x in a.deltas.split(",")]

    ib = connect_ib(client_id=30)
    ib.reqMarketDataType(2)
    print(f"OK Connected (paper {ib.managedAccounts()}). Expectancy by delta, exp {a.expiry}\n")
    print(f"(exit stop = {a.stop})")
    results = []
    for sym in a.symbols:
        r = replay(ib, sym.upper(), a.expiry, targets, a.stop)
        if r:
            results.append(r)
        ib.sleep(1)
    ib.disconnect()

    # per-trade table
    head = f"{'sym':<6}{'stk%':>7}{'exit':>7}"
    for td in targets:
        head += f"{('Δ'+str(td)):>9}"
    print(head); print("-" * len(head))
    for r in results:
        line = f"{r['symbol']:<6}{r['stk']:>+7.2f}{r['reason']:>7}"
        for td in targets:
            o = r["by_delta"].get(td, {}).get("opt")
            line += f"{(f'{o:+.0f}%' if o is not None else 'n/a'):>9}"
        print(line)

    # expectancy per delta (equal-$ per trade -> mean of option returns)
    print(f"\n{'delta':>6}{'trades':>8}{'win%':>7}{'avg%':>8}{'total%':>9}{'PF':>7}")
    print("-" * 45)
    for td in targets:
        vals = [r["by_delta"][td]["opt"] for r in results
                if r["by_delta"].get(td, {}).get("opt") is not None]
        if not vals:
            continue
        wins = [v for v in vals if v > 0]
        gl = -sum(v for v in vals if v <= 0)
        pf = (sum(wins) / gl) if gl else float("inf")
        print(f"{td:>6.2f}{len(vals):>8}{len(wins)/len(vals)*100:>6.0f}%"
              f"{sum(vals)/len(vals):>+8.1f}{sum(vals):>+9.1f}{pf:>7.2f}")
    print("\navg%/total% = equal-$ per trade; PF = gains/|losses|. "
          "Lower delta amplifies BOTH wins and losses.")


if __name__ == "__main__":
    raise SystemExit(main())

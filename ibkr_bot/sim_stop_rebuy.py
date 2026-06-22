#!/usr/bin/env python3
"""Backtest the stop-and-rebuy idea on each name's last ~1y of daily bars.

For each name we run three strategies on the SAME bars and compare to buy-and-hold:
  BH         : buy and hold, no stop.
  STOP_ONLY  : trailing stop D% under the running high; on a stop, go to CASH and stay.
  STOP_REBUY : same stop, but REBUY when price CLOSES back above the level we got
               stopped at (the user's idea). Repeat all year.

D (trailing distance) = each name's CURRENT stop room% (how tight they actually run it),
so the sim reflects the real book. Slippage is applied ONLY to stop-induced transactions
(the extra round-trips) -- exit fills at stop*(1-slip), rebuy at close*(1+slip) -- so the
comparison isolates the cost of the churn. Initial buy / final mark are slip-free for all.

Reads: IB 1-day bars (1 Y). Read-only.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock  # noqa: E402

# name -> current stop room% (from eval_stops): trailing distance D
ROOM = {
    "APLE": 3.6, "BIRD": 7.9, "TE": 6.4, "CIFR": 7.5, "FCEL": 6.4, "ARMG": 7.2,
    "GLW": 3.3, "MRNA": 2.7, "HOOD": 5.1, "MRVL": 3.4, "RY": 1.3, "AMD": 2.5,
    "VSH": 3.7, "GEV": 4.5, "ENTG": 3.8, "CAT": 1.1, "GWW": 1.9, "SOXL": 12.3,
    "AMAT": 7.6, "MU": 4.1,
}
SLIP = float(os.environ.get("SLIP", "0.005"))   # per-side slippage on churn (0.5%)


def simulate(bars, D, rebuy):
    """Return (equity_multiple, n_roundtrips). Trailing stop at D below running high."""
    closes = [b.close for b in bars]
    lows = [b.low for b in bars]
    eq = 1.0
    long = True
    p_in = closes[0]
    trail_hi = closes[0]
    stop_lvl = None
    n_rt = 0
    for i in range(1, len(bars)):
        if long:
            trail_hi = max(trail_hi, closes[i])
            stop = trail_hi * (1 - D)
            if lows[i] <= stop:                      # stopped out
                fill = stop * (1 - SLIP)
                eq *= fill / p_in
                long = False
                stop_lvl = stop
                n_rt += 1
        else:
            if rebuy and closes[i] > stop_lvl:       # close back above stop level
                p_in = closes[i] * (1 + SLIP)
                long = True
                trail_hi = closes[i]
    if long:                                          # mark to last close
        eq *= closes[-1] / p_in
    return eq, n_rt


def fwd_after_drop(bars):
    """Mean-reversion check: avg 3-day fwd return after a >=1-ATR down day."""
    trs, rets3 = [], []
    for i in range(1, len(bars)):
        h, l, pc = bars[i].high, bars[i].low, bars[i-1].close
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < 20:
        return None
    atr = sum(trs[-60:]) / min(60, len(trs))
    closes = [b.close for b in bars]
    for i in range(1, len(closes) - 3):
        if closes[i] - closes[i-1] <= -atr:           # big down day
            rets3.append((closes[i+3] / closes[i] - 1) * 100)
    if not rets3:
        return None
    return sum(rets3) / len(rets3), len(rets3)


def main() -> int:
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "11")))
    print(f"CONNECTED {ib.managedAccounts()}  (slip/side={SLIP*100:.1f}%)\n", flush=True)
    hdr = (f"{'sym':5s}{'bars':>5}{'D%':>5}{'BH%':>8}{'StpOnly%':>9}{'Rebuy%':>8}"
           f"{'RTrips':>7}{'fwd3d%':>8}{'n':>4}  verdict")
    print(hdr); print("-" * len(hdr), flush=True)
    agg = {"bh": [], "so": [], "rb": [], "rt": []}
    for sym, room in ROOM.items():
        c = Stock(sym, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y",
                                    barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
        if not bars or len(bars) < 30:
            print(f"{sym:5s}  insufficient bars ({len(bars) if bars else 0})", flush=True)
            continue
        D = room / 100.0
        bh = (bars[-1].close / bars[0].close - 1) * 100
        so, _ = simulate(bars, D, rebuy=False)
        rb, nrt = simulate(bars, D, rebuy=True)
        so = (so - 1) * 100; rb = (rb - 1) * 100
        mr = fwd_after_drop(bars)
        fwd, n = (mr if mr else (float("nan"), 0))
        # verdict: did stop-rebuy beat buy-and-hold? did stop help at all?
        if rb > bh + 2:
            v = "rebuy WINS"
        elif so > bh + 2:
            v = "stop-only wins (rebuy bleeds)"
        elif bh > rb + 2:
            v = "HOLD wins (churn hurt)"
        else:
            v = "~wash"
        print(f"{sym:5s}{len(bars):>5}{room:>5.1f}{bh:>8.1f}{so:>9.1f}{rb:>8.1f}"
              f"{nrt:>7}{fwd:>8.1f}{n:>4}  {v}", flush=True)
        agg["bh"].append(bh); agg["so"].append(so); agg["rb"].append(rb); agg["rt"].append(nrt)
    ib.disconnect()
    n = len(agg["bh"])
    if n:
        print("-" * len(hdr))
        print(f"MEAN  BH {sum(agg['bh'])/n:+.1f}%   StopOnly {sum(agg['so'])/n:+.1f}%   "
              f"Rebuy {sum(agg['rb'])/n:+.1f}%   avg RoundTrips/yr {sum(agg['rt'])/n:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

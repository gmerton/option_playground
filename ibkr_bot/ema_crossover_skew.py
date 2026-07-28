#!/usr/bin/env python3
"""Does the low-delta preference survive VOLATILITY SKEW?

Open question from the IV-calibration pass: per-name IV (calibrated to the
symbol's standard deviation) did NOT kill the "lower delta = better" result --
it slightly helped. But a std-calibrated Black-Scholes IV prices a LOGNORMAL
tail, while this cache's open->close distribution is right-skewed and
fat-tailed. BS therefore underprices exactly the far-OTM strikes that the
low-delta result depends on.

Real markets charge for that through the volatility SKEW: on momentum names,
out-of-the-money calls trade at an IV above the at-the-money level. This script
puts that charge back in and asks whether low delta still wins.

  iv(K) = iv_atm + skew * (K/S - 1)

`skew` is in IV-points per 1.0 of moneyness, so --skew 2.0 means a strike 5%
OTM is priced 10 vol points above ATM. The strike is still solved for the target
delta at the ATM IV (so "0.25 delta" labels the same strike across skew levels
and the comparison isolates the PRICE paid), then both entry and exit are priced
at that strike's skewed IV.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_skew.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_skew.py --vrp 1.15
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_options import bs_call, strike_for_delta  # noqa: E402
from ema_crossover_iv_calib import load_sessions, loo_iv, g_of_f  # noqa: E402

DELTAS = [0.85, 0.65, 0.45, 0.25]
SKEWS = [0.0, 0.5, 1.0, 2.0, 4.0]
SIZES = [0.05, 0.10, 0.20]
YEAR_MIN = 365 * 24 * 60


def opt_return_skew(entry_px, exit_px, hold_min, dte, iv_atm, target_delta, skew):
    """% return of a target-delta call when OTM strikes carry a skew premium."""
    T0 = dte / 365.0
    K = strike_for_delta(entry_px, T0, iv_atm, target_delta)
    iv_k = iv_atm + skew * (K / entry_px - 1.0)          # skewed IV at that strike
    if iv_k <= 0.01:
        return None
    prem_in = bs_call(entry_px, K, T0, iv_k)
    T1 = max(1e-6, T0 - hold_min / YEAR_MIN)
    prem_out = bs_call(exit_px, K, T1, iv_k)
    if prem_in <= 1e-6:
        return None
    return (prem_out / prem_in - 1) * 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--dte", type=int, default=5)
    ap.add_argument("--vrp", type=float, default=1.0,
                    help="multiplier on per-name ATM IV before skew is applied")
    a = ap.parse_args()

    sessions = load_sessions(
        a.glob if os.path.isabs(a.glob) else os.path.join(HERE, a.glob), a.min_bars)
    ivs = loo_iv(sessions) * a.vrp
    stock = np.array([c / o - 1.0 for (_, o, c, _) in sessions])

    print(f"\nCALL-SKEW SENSITIVITY   [{len(sessions)} sessions, DTE={a.dte}, "
          f"per-name IV x {a.vrp:.2f}]")
    print("\n  skew = IV-points per 1.0 moneyness; skew 2.0 => 5% OTM priced +10 vol pts.")
    print(f"\n  stock 1.0d reference: mean {stock.mean()*100:+.2f}%  "
          f"win {(stock > 0).mean()*100:.1f}%  g@10% {g_of_f(stock, 0.10):+.4f}\n")

    hdr = "".join(f"{f'g@10% d{d:.2f}':>14}" for d in DELTAS)
    print(f"  {'skew':>6}{hdr}      best")
    for sk in SKEWS:
        gs, means = [], []
        for d in DELTAS:
            vals = []
            for (sym, o, c, h), iv in zip(sessions, ivs):
                v = opt_return_skew(o, c, max(1, h), a.dte, float(iv), d, sk)
                if v is not None:
                    vals.append(v / 100.0)
            r = np.array(vals)
            gs.append(g_of_f(r, 0.10))
            means.append(r.mean() * 100)
        cells = "".join((f"{g:>14.4f}" if np.isfinite(g) else f"{'RUIN':>14}") for g in gs)
        best = DELTAS[int(np.argmax([g if np.isfinite(g) else -1e9 for g in gs]))]
        print(f"  {sk:>6.1f}{cells}      {best:.2f}d")

    print("\n  arithmetic mean %/trade for the same grid:")
    print(f"  {'skew':>6}" + "".join(f"{f'mean d{d:.2f}':>14}" for d in DELTAS))
    for sk in SKEWS:
        means = []
        for d in DELTAS:
            vals = [opt_return_skew(o, c, max(1, h), a.dte, float(iv), d, sk)
                    for (sym, o, c, h), iv in zip(sessions, ivs)]
            vals = [v for v in vals if v is not None]
            means.append(np.mean(vals))
        print(f"  {sk:>6.1f}" + "".join(f"{m:>+14.2f}" for m in means))

    print("\n  g(f)=mean(log(1+f*r)) at 10% of bankroll per trade. Cache is mover-biased")
    print("  -> levels are UPPER BOUNDS; the trend across skew is the point.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

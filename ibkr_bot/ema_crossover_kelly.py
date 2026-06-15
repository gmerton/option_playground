#!/usr/bin/env python3
"""Position-sizing / Kelly analysis on the option-leverage distribution.

The deploy gate: a 45%-win, fat-tailed long-option edge (big bounded-downside
losers, rare huge winners) can be growth-optimal yet still ruin you if oversized.
This computes, per vehicle (delta):

  f*   -- full-Kelly fraction of bankroll to spend on premium per trade,
          = argmax_f mean(log(1 + f*r)) over the per-trade option returns r
  g    -- per-trade log-growth at f* (and the implied multiple over a horizon)

then Monte-Carlo the equity path at full / half / quarter Kelly and a fixed 2% to
show median growth vs drawdown vs blow-up probability. Trades are treated as
SEQUENTIAL & INDEPENDENT (standard Kelly) -- reality is worse: open-hour entries
CLUSTER same-day (correlated simultaneous bets), so the safe fraction is even
smaller than what's printed.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_kelly.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_kelly.py --iv 0.6 --horizon 250
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_options import collect_trades, opt_return  # noqa: E402

DELTAS = [("0.35Δ OTM", 0.35), ("0.50Δ ATM", 0.50),
          ("0.65Δ ITM", 0.65), ("0.80Δ ITM", 0.80)]


def kelly_f(r: np.ndarray) -> tuple[float, float]:
    """argmax_f mean(log(1+f r)) subject to 1+f r > 0 for all r."""
    cap = 1.0 / max(1e-9, -r.min()) - 1e-4      # no single-trade ruin
    fs = np.linspace(1e-4, cap, 6000)
    g = np.array([np.mean(np.log1p(f * r)) for f in fs])
    k = int(np.argmax(g))
    return float(fs[k]), float(g[k])


def mc(r: np.ndarray, f: float, horizon: int, paths: int, rng) -> dict:
    idx = rng.integers(0, len(r), size=(paths, horizon))
    step = 1.0 + f * r[idx]                      # paths x horizon multipliers
    eq = np.cumprod(step, axis=1)
    runmax = np.maximum.accumulate(eq, axis=1)
    maxdd = (1.0 - eq / runmax).max(axis=1)
    term = eq[:, -1]
    return {
        "med_mult": float(np.median(term)),
        "p5_mult": float(np.percentile(term, 5)),
        "p95_mult": float(np.percentile(term, 95)),
        "med_dd": float(np.median(maxdd)) * 100,
        "p_dd50": float(np.mean(maxdd > 0.50)) * 100,
        "p_lose": float(np.mean(term < 1.0)) * 100,
        "p_ruin80": float(np.mean(term < 0.20)) * 100,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--index", default="SPY")
    ap.add_argument("--iv", type=float, default=0.60)
    ap.add_argument("--dte", type=int, default=5)
    ap.add_argument("--horizon", type=int, default=250, help="trades to simulate")
    ap.add_argument("--paths", type=int, default=20000)
    a = ap.parse_args()

    trades = collect_trades(
        a.glob if os.path.isabs(a.glob) else os.path.join(HERE, a.glob),
        a.min_bars, a.index)
    rng = np.random.default_rng(42)

    print(f"\nKELLY / SIZING -- best config option distribution "
          f"(IV={a.iv:.0%}, DTE={a.dte}, {len(trades)} trades)")
    print(f"horizon={a.horizon} trades, {a.paths} Monte-Carlo paths, "
          f"sequential-independent (reality: same-day clustering -> use LESS)\n")

    # per-vehicle Kelly
    print(f"  {'vehicle':<12}{'mean r%':>9}{'win%':>6}{'worst%':>8}"
          f"{'full-Kelly f*':>14}{'g/trade':>9}")
    dist = {}
    for label, td in DELTAS:
        r = np.array([opt_return(t["entry"], t["exit"], t["hold_min"], a.dte, a.iv, td)
                      for t in trades if opt_return(t["entry"], t["exit"],
                      t["hold_min"], a.dte, a.iv, td) is not None]) / 100.0
        dist[label] = r
        f, g = kelly_f(r)
        wins = (r > 0).mean() * 100
        print(f"  {label:<12}{r.mean()*100:>+9.1f}{wins:>6.1f}{r.min()*100:>+8.1f}"
              f"{f*100:>12.1f}%{g:>+9.4f}")

    # Monte-Carlo equity for the ATM vehicle at fractions of Kelly
    label = "0.50Δ ATM"
    r = dist[label]
    fk, _ = kelly_f(r)
    print(f"\n  Monte-Carlo equity ({label}, full-Kelly f*={fk*100:.1f}% premium/trade):")
    print(f"    {'sizing':<16}{'f%':>6}{'median x':>10}{'5th x':>9}{'95th x':>10}"
          f"{'med maxDD':>11}{'P(DD>50%)':>11}{'P(lose)':>9}{'P(-80%)':>9}")
    for name, frac in [("full Kelly", 1.0), ("half Kelly", 0.5),
                       ("quarter Kelly", 0.25), ("fixed 2%", None)]:
        f = fk * frac if frac is not None else 0.02
        m = mc(r, f, a.horizon, a.paths, rng)
        print(f"    {name:<16}{f*100:>6.1f}{m['med_mult']:>10.2f}{m['p5_mult']:>9.2f}"
              f"{m['p95_mult']:>10.1f}{m['med_dd']:>10.0f}%{m['p_dd50']:>10.0f}%"
              f"{m['p_lose']:>8.0f}%{m['p_ruin80']:>8.0f}%")

    print("\n  f* = premium as %% of bankroll PER TRADE. median/5th/95th x = terminal")
    print("  wealth multiple. ⚠️ distribution is an UPPER BOUND (hand-picked cache) ->")
    print("  TRUE Kelly is far lower; full-Kelly on an optimistic fat tail = ruin.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Verification of the TQQQ/SQQQ systematic strategy claims from the KINFO interview
(`pBS5vrqrUjk`, 2025-09-11, "This Trader Made +$700K in 6 MONTHS").

CLAIMS UNDER TEST
  1. "80% return per year" backtested on NDX from 1985, vs QQQ buy-and-hold ~12%.
  2. The stated rule: go 100% TQQQ when price is above the 50-day AND 250-day moving average;
     the short/mean-reversion sub-strategies take over when the trend breaks.
  3. "+200% in 2000 and +152% in 2001" through the dot-com crash.
  4. Live: ~40%/yr over ~3 years with a 30-33% max drawdown.

WHY THE 1985 BACKTEST IS SYNTHETIC
  TQQQ launched Feb 2010 and SQQQ Feb 2010. Everything before that must be simulated from the
  NDX index. A leveraged ETF is NOT 3x the index return over any period longer than a day — it
  resets daily, so it compounds daily 3x returns and suffers volatility drag of roughly
  (L^2-L)/2 * sigma^2 per year (~75%/yr at 50% realized vol, which is what NDX ran in 2000-02).
  It also pays an expense ratio (~0.84-0.95%) and embedded financing on the 2x borrowed
  notional. This script models all three so the synthetic series is honest.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/check_tqqq_claim.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

EXPENSE = 0.0095          # annual expense ratio, ProShares 3x funds
FIN_SPREAD = 0.005        # financing spread over the risk-free rate on borrowed notional
# ⚠ A FLAT risk-free rate badly misprices the 2010-2021 ZIRP decade and biases the whole test
# against any levered strategy. Use the actual 13-week T-bill (^IRX) as a time series instead.
RF_FALLBACK = 0.03
COST_BP = 5.0             # round-trip trading cost per switch, bp


def synth(idx: pd.Series, lev: float, rf: pd.Series | float = RF_FALLBACK) -> pd.Series:
    """Daily-reset leveraged ETF simulated from an index. lev = +3 (TQQQ) or -3 (SQQQ)."""
    r = idx.pct_change().fillna(0.0)
    # borrowed notional = |lev| - 1 for a long fund; a -3x fund is short 3x and long 1x cash
    borrow = abs(lev) - 1.0
    rfs = rf.reindex(idx.index).ffill().bfill() if isinstance(rf, pd.Series) else rf
    daily_cost = (EXPENSE + borrow * (rfs + FIN_SPREAD)) / 252.0
    return (1.0 + lev * r - daily_cost).cumprod()


def stats(eq: pd.Series, label: str) -> dict:
    eq = eq.dropna()
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0
    dd = (eq / eq.cummax() - 1).min()
    return {"strategy": label, "years": yrs, "CAGR%": 100 * cagr, "maxDD%": 100 * dd,
            "final_x": eq.iloc[-1] / eq.iloc[0],
            "MAR": (100 * cagr) / abs(100 * dd) if dd < 0 else np.nan}


def main() -> None:
    print("downloading ^NDX, QQQ, TQQQ, ^IRX ...", flush=True)
    irx = yf.download("^IRX", start="1985-01-01", end="2026-07-27", auto_adjust=True,
                      progress=False)["Close"].squeeze().dropna() / 100.0
    ndx = yf.download("^NDX", start="1985-01-01", end="2026-07-27", auto_adjust=True,
                      progress=False)["Close"].squeeze().dropna()
    qqq = yf.download("QQQ", start="1999-01-01", end="2026-07-27", auto_adjust=True,
                      progress=False)["Close"].squeeze().dropna()
    tqqq = yf.download("TQQQ", start="2010-01-01", end="2026-07-27", auto_adjust=True,
                       progress=False)["Close"].squeeze().dropna()
    print(f"  NDX {ndx.index[0].date()} -> {ndx.index[-1].date()}  ({len(ndx):,} bars)")

    # ---------------------------------------------------------------- validate the simulator
    print("\n" + "=" * 100)
    print("0.  DOES THE SIMULATOR REPRODUCE THE REAL TQQQ?  (2010-2026, out of sample for it)")
    print("=" * 100)
    sim = synth(ndx.reindex(tqqq.index).ffill(), 3.0, irx)
    sim = sim / sim.iloc[0]
    real = tqqq / tqqq.iloc[0]
    comp = pd.DataFrame({"simulated": stats(sim, "sim 3x"), "actual TQQQ": stats(real, "TQQQ")}).T
    print(comp[["years", "CAGR%", "maxDD%", "final_x"]].round(2).to_string())
    print(f"\n  tracking: simulated final {sim.iloc[-1]:.1f}x vs actual {real.iloc[-1]:.1f}x "
          f"-> ratio {sim.iloc[-1]/real.iloc[-1]:.2f}")
    print("  (close ratio = the daily-reset + cost model is sound enough to trust pre-2010)")

    # ---------------------------------------------------------------- the strategy
    ma50 = ndx.rolling(50).mean()
    ma250 = ndx.rolling(250).mean()
    above = (ndx > ma50) & (ndx > ma250)
    below = (ndx < ma50) & (ndx < ma250)
    # signal known at the close, traded at the next close -> shift(1), no look-ahead
    pos = pd.Series(0.0, index=ndx.index)
    pos[above] = 3.0
    pos[below] = -3.0
    pos = pos.shift(1).fillna(0.0)

    r = ndx.pct_change().fillna(0.0)
    rfs = irx.reindex(ndx.index).ffill().bfill()
    borrow_cost = ((EXPENSE + 2.0 * (rfs + FIN_SPREAD)) / 252.0).to_numpy()
    switch = (pos != pos.shift(1)).astype(float) * COST_BP / 1e4
    gross = 1.0 + pos * r
    net = gross - np.where(pos != 0, borrow_cost, 0.0) - switch
    eq_net = pd.Series(net, index=ndx.index).cumprod()
    eq_gross = pd.Series(1.0 + pos * r, index=ndx.index).cumprod()   # naive: no costs at all

    print("\n" + "=" * 100)
    print("1.  THE STATED RULE, 1985-2026: long 3x above BOTH the 50d and 250d MA, short 3x below")
    print("=" * 100)
    rows = [stats(eq_gross, "NAIVE 3x (no ETF costs, no fees) <- what a careless backtest shows"),
            stats(eq_net, "MODELLED 3x (expense + financing + 5bp/switch)"),
            stats(synth(ndx, 3.0, irx), "buy & hold synthetic TQQQ"),
            stats(ndx, "NDX index (price only)")]
    print(pd.DataFrame(rows).set_index("strategy").round(2).to_string())

    print("\n  ⚠ REDUCTIO: $10,000 compounded at the claimed 80%/yr for 40 years")
    print(f"     = ${10000 * 1.8 ** 40:,.0f}  — larger than world equity market cap.")
    print(f"     This backtest's own modelled figure implies ${10000*eq_net.iloc[-1]:,.0f}.")

    # ---------------------------------------------------------------- dot-com years
    print("\n" + "=" * 100)
    print("2.  THE DOT-COM CLAIM: '+200% in 2000 and +152% in 2001'")
    print("=" * 100)
    yr = pd.DataFrame({"modelled": pd.Series(net, index=ndx.index),
                       "naive": pd.Series(1.0 + pos * r, index=ndx.index)})
    ann = yr.groupby(yr.index.year).apply(lambda g: (g.prod() - 1) * 100)
    print(ann.loc[1998:2003].round(1).to_string())

    # ---------------------------------------------------------------- live window
    print("\n" + "=" * 100)
    print("3.  THE LIVE WINDOW (~3 years to Sep 2025): his ~40%/yr vs the obvious benchmarks")
    print("=" * 100)
    lo, hi = "2022-09-01", "2025-09-11"
    seg = {}
    for name, s in [("NDX", ndx), ("QQQ", qqq), ("TQQQ (actual)", tqqq),
                    ("strategy, modelled", eq_net)]:
        w = s.loc[lo:hi]
        if len(w) > 100:
            seg[name] = stats(w / w.iloc[0], name)
    print(pd.DataFrame(seg).T[["years", "CAGR%", "maxDD%", "final_x"]].round(2).to_string())
    print("\n  his stated live result: ~40%/yr CAGR, 30-33% max drawdown")


if __name__ == "__main__":
    main()

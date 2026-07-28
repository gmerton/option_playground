#!/usr/bin/env python3
"""
TQQQ/SQQQ LAB — can a rule using only these two ETFs be CONSISTENTLY profitable?

Motivated by the KINFO/Malik interview review (`data/video_reviews/kinfo_malik_tqqq_2025-09-11.md`),
which failed on two things this script is built to avoid.

⚠ ANTI-DATA-MINING PROTOCOL (the whole point)
  He tested 300-350 strategies and kept 7. That guarantees the survivors look good by chance.
  Rules here:
    1. **8 candidate rules, pre-specified**, each justified by a MECHANISM before being run.
    2. **No parameter tuning.** 200-day MA, 20-day vol, 50/250 MA — all conventional values used
       off the shelf. Nothing is optimized, so there is nothing to overfit.
    3. **Every rule is reported**, winners and losers, in every period. No cherry-picking.
    4. **Three disjoint periods reported separately, never pooled**: synthetic 1985-2009,
       real 2010-2017, real 2018-2026. A rule that only works in one is not a strategy.

⚠ TWO MODELLING POINTS HE GOT WRONG
  (a) REAL TQQQ prices ALREADY CONTAIN the expense ratio and financing costs. Adding a cost model
      on top of real prices double-counts. Costs are modelled ONLY on the synthetic pre-2010
      series; on real data we charge slippage per switch and nothing else.
  (b) The synthetic series is CALIBRATED to real TQQQ (2010-2026) rather than assumed. We solve
      for the daily drag constant that reproduces actual TQQQ, instead of guessing an expense
      ratio and a financing spread.

⚠ WHY SQQQ IS STRUCTURALLY DIFFERENT, NOT JUST "THE OTHER SIDE"
  NDX has positive drift, so a -3x product fights BOTH the drift and the volatility drag. SQQQ has
  lost >99.9% since inception. Any rule using it must earn its keep against that; rule 5 exists
  purely to measure whether adding the short side helps or hurts.

Usage: PYTHONPATH=src .venv/bin/python3 data/studies/tqqq_lab/build_tqqq_lab.py
"""
from __future__ import annotations

import os
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

HERE = "data/studies/tqqq_lab"
SLIP_BP = 5.0            # per switch, each way, on real prices
ANN = 252


# ------------------------------------------------------------------ data

def load() -> dict:
    os.makedirs(HERE, exist_ok=True)
    cache = f"{HERE}/raw.parquet"
    if os.path.exists(cache):
        df = pd.read_parquet(cache)
    else:
        cols = {}
        for t in ("^NDX", "QQQ", "TQQQ", "SQQQ"):
            s = yf.download(t, start="1985-01-01", end="2026-07-27", auto_adjust=True,
                            progress=False)["Close"].squeeze().dropna()
            cols[t.replace("^", "")] = s
            print(f"  {t}: {len(s):,} bars {s.index[0].date()} -> {s.index[-1].date()}", flush=True)
        df = pd.DataFrame(cols)
        df.to_parquet(cache)
    return {c: df[c].dropna() for c in df.columns}


def calibrate_drag(ndx: pd.Series, tqqq: pd.Series) -> float:
    """Solve for the daily drag constant that reproduces real TQQQ from NDX, 2010-2026.

    Rather than assuming an expense ratio and financing spread, measure them jointly: the
    residual between 3x-compounded NDX and actual TQQQ IS the all-in holding cost.
    """
    idx = tqqq.index
    r = ndx.reindex(idx).ffill().pct_change().fillna(0.0)
    tq = tqqq.pct_change().fillna(0.0)
    # mean daily difference between 3x index return and the fund's actual return
    return float((3.0 * r - tq).mean())


def synth(ndx: pd.Series, lev: float, drag: float) -> pd.Series:
    r = ndx.pct_change().fillna(0.0)
    return (1.0 + lev * r - drag).cumprod()


# ------------------------------------------------------------------ rules
# Each returns a target weight series on (TQQQ, SQQQ). Weight 1.0 = fully in that ETF.
# All signals are computed on close t and applied from close t+1 (shift(1)) — no look-ahead.

def rules(ndx: pd.Series) -> dict[str, pd.DataFrame]:
    ma200 = ndx.rolling(200).mean()
    ma50 = ndx.rolling(50).mean()
    ma250 = ndx.rolling(250).mean()
    rising = ma200 > ma200.shift(20)
    ret = ndx.pct_change()
    vol20 = ret.rolling(20).std() * np.sqrt(ANN)
    # expanding median so the threshold uses only information available at the time
    vol_med = vol20.expanding(min_periods=500).median()

    up = ndx > ma200
    out = {}

    def mk(t, s=None):
        return pd.DataFrame({"TQQQ": t.astype(float),
                             "SQQQ": (s if s is not None else t * 0).astype(float)}).shift(1).fillna(0.0)

    # 1-2 are benchmarks, handled separately.
    # 3. MECHANISM: the repo's own largest finding — a 200d regime gate halved drawdown and
    #    tripled MAR on equities. Apply it to the levered vehicle.
    out["3 MA200 gate"] = mk(up)
    # 4. MECHANISM: a rising 200d beat a flat one in REGIME.md. Adds a slope condition.
    out["4 MA200 + rising"] = mk(up & rising)
    # 5. MECHANISM: does the short side pay for itself, given SQQQ's structural decay?
    out["5 MA200 long/short"] = mk(up, ~up)
    # 6. MECHANISM: leveraged-ETF drag is (L^2-L)/2 * sigma^2 — it is a VOLATILITY tax, so gate
    #    on volatility directly, not just on trend.
    out["6 MA200 + low vol"] = mk(up & (vol20 < vol_med))
    # 7. MECHANISM: same idea, continuous rather than binary — scale exposure inversely to vol
    #    so the drag term is held roughly constant. Classic vol targeting, 25% target.
    w = (0.25 / vol20).clip(0, 1.0).where(up, 0.0)
    out["7 vol-targeted 25%"] = pd.DataFrame({"TQQQ": w, "SQQQ": w * 0}).shift(1).fillna(0.0)
    # 8. Malik's demonstrated rule, long-only (cash instead of SQQQ below).
    out["8 Malik 50/250 long-only"] = mk((ndx > ma50) & (ndx > ma250))
    return out


# ------------------------------------------------------------------ engine

def run(weights: pd.DataFrame, tq: pd.Series, sq: pd.Series) -> pd.Series:
    """Daily equity curve. Costs = slippage on turnover only; holding costs are already in prices."""
    idx = weights.index
    rt = tq.reindex(idx).ffill().pct_change().fillna(0.0)
    rs = sq.reindex(idx).ffill().pct_change().fillna(0.0)
    gross = weights["TQQQ"] * rt + weights["SQQQ"] * rs
    turn = weights.diff().abs().sum(axis=1).fillna(0.0)
    return (1.0 + gross - turn * SLIP_BP / 1e4).cumprod()


def stats(eq: pd.Series, w: pd.DataFrame | None = None) -> dict:
    eq = eq.dropna()
    if len(eq) < 250:
        return {}
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    dr = eq.pct_change().dropna()
    roll = eq / eq.shift(252) - 1                    # rolling 12-month return
    roll = roll.dropna()
    d = {"CAGR%": 100 * cagr, "maxDD%": 100 * dd,
         "MAR": (100 * cagr) / abs(100 * dd) if dd < 0 else np.nan,
         "Sharpe": dr.mean() / dr.std() * np.sqrt(ANN) if dr.std() > 0 else np.nan,
         "12m>0 %": 100 * (roll > 0).mean() if len(roll) else np.nan,
         "worst12m%": 100 * roll.min() if len(roll) else np.nan}
    if w is not None:
        d["in mkt%"] = 100 * (w.abs().sum(axis=1) > 0).mean()
        d["trades/yr"] = float(w.diff().abs().sum(axis=1).gt(0).sum() / yrs)
    return d


def main() -> None:
    print("loading ...", flush=True)
    d = load()
    ndx, qqq, tqqq, sqqq = d["NDX"], d["QQQ"], d["TQQQ"], d["SQQQ"]

    drag = calibrate_drag(ndx, tqqq)
    print(f"\ncalibrated all-in daily holding cost from real TQQQ: {drag*1e4:.2f} bp/day "
          f"= {drag*252*100:.2f}%/yr")
    chk = synth(ndx.reindex(tqqq.index).ffill(), 3.0, drag)
    print(f"  calibration check: synthetic {chk.iloc[-1]/chk.iloc[0]:.1f}x vs "
          f"real TQQQ {tqqq.iloc[-1]/tqqq.iloc[0]:.1f}x")

    # synthetic pre-2010 series for the out-of-sample-in-time period
    pre = ndx.loc[:"2010-02-10"]
    syn_t = synth(pre, 3.0, drag)
    syn_s = synth(pre, -3.0, drag)

    R = rules(ndx)
    periods = [("SYNTHETIC 1985-2009", "1986-01-01", "2010-02-09", syn_t, syn_s),
               ("REAL 2010-2017", "2010-02-11", "2017-12-31", tqqq, sqqq),
               ("REAL 2018-2026", "2018-01-01", "2026-07-23", tqqq, sqqq)]

    for label, lo, hi, T, S in periods:
        print("\n" + "=" * 118)
        print(f"{label}")
        print("=" * 118)
        rows = {}
        bq = qqq.loc[lo:hi]
        if len(bq) > 250:
            rows["1 buy&hold QQQ"] = stats(bq / bq.iloc[0])
        bt = T.loc[lo:hi]
        if len(bt) > 250:
            rows["2 buy&hold TQQQ"] = stats(bt / bt.iloc[0])
        for name, w in R.items():
            ww = w.loc[lo:hi]
            if len(ww) < 250:
                continue
            eq = run(ww, T, S)
            rows[name] = stats(eq, ww)
        df = pd.DataFrame(rows).T
        print(df.round(2).to_string())

    print("\n" + "=" * 118)
    print("CONSISTENCY — CAGR% by calendar year, real data only (2010-2026)")
    print("=" * 118)
    yr = {}
    bq = qqq.loc["2010-02-11":]
    yr["1 buy&hold QQQ"] = bq.groupby(bq.index.year).apply(lambda g: 100 * (g.iloc[-1] / g.iloc[0] - 1))
    bt = tqqq.loc["2010-02-11":]
    yr["2 buy&hold TQQQ"] = bt.groupby(bt.index.year).apply(lambda g: 100 * (g.iloc[-1] / g.iloc[0] - 1))
    for name, w in R.items():
        ww = w.loc["2010-02-11":]
        eq = run(ww, tqqq, sqqq)
        yr[name] = eq.groupby(eq.index.year).apply(lambda g: 100 * (g.iloc[-1] / g.iloc[0] - 1))
    out = pd.DataFrame(yr).round(1)
    print(out.to_string())
    print("\n  losing years per rule:")
    print((out < 0).sum().to_string())
    out.to_csv(f"{HERE}/annual_returns.csv")
    print(f"\nwrote {HERE}/annual_returns.csv")


if __name__ == "__main__":
    main()

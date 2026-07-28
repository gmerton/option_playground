#!/usr/bin/env python3
"""
TQQQ LAB v2 — the control that decides everything: does the LEVERAGE add anything?

v1 found vol-targeted, long-only, 200d-gated TQQQ was the best of eight pre-specified rules,
consistently across three disjoint periods. But "best levered rule" is not the question. The
question is whether the 3x vehicle earns its place, or whether the TIMING RULE is doing all the
work and the leverage is just scaling the result up (and adding drag).

Sharpe answers it directly — it is volatility-normalised, so if the levered and unlevered versions
of the SAME rule have the same Sharpe, the leverage contributes nothing but size.

Also tested here:
  * vol-target SENSITIVITY (15/20/25/30/35%) — reported as a sweep, NOT selected from. If the
    result only holds at one setting it is a fitting artifact.
  * the two drawdown-control ideas from v1 combined (low-vol gate + vol targeting)
  * a fixed fractional-TQQQ allocation, i.e. buying ~1.5x exposure instead of 3x

Same protocol as v1: pre-specified, untuned, all results reported, three disjoint periods.

Usage: PYTHONPATH=src .venv/bin/python3 data/studies/tqqq_lab/build_tqqq_lab_v2.py
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, "data/studies/tqqq_lab")
from build_tqqq_lab import ANN, HERE, calibrate_drag, load, run, stats, synth  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)


def build(ndx: pd.Series) -> dict[str, pd.DataFrame]:
    ma200 = ndx.rolling(200).mean()
    ret = ndx.pct_change()
    vol20 = ret.rolling(20).std() * np.sqrt(ANN)
    vol_med = vol20.expanding(min_periods=500).median()
    up = ndx > ma200
    out = {}

    def dfw(t=None, q=None):
        return pd.DataFrame({"TQQQ": t if t is not None else 0.0,
                             "QQQ": q if q is not None else 0.0},
                            index=ndx.index).fillna(0.0).shift(1).fillna(0.0)

    # ---- the control pair: identical timing rule, levered vs unlevered vehicle
    out["A1 QQQ, MA200 gate"] = dfw(q=up.astype(float))
    out["A2 TQQQ, MA200 gate"] = dfw(t=up.astype(float))

    # ---- vol-target sweep on TQQQ (sensitivity, not selection)
    for tgt in (0.15, 0.20, 0.25, 0.30, 0.35):
        out[f"B TQQQ voltgt {int(tgt*100)}%"] = dfw(t=(tgt / vol20).clip(0, 1.0).where(up, 0.0))

    # ---- the same vol target applied to the UNLEVERED vehicle, capped at 1x (no margin)
    out["C QQQ voltgt 25% (cap 1x)"] = dfw(q=(0.25 / (vol20 / 3.0)).clip(0, 1.0).where(up, 0.0))

    # ---- v1's two drawdown ideas combined
    out["D TQQQ voltgt + low-vol gate"] = dfw(
        t=(0.25 / vol20).clip(0, 1.0).where(up & (vol20 < vol_med), 0.0))

    # ---- fixed fractional exposure: 50% TQQQ = ~1.5x, avoids the worst of the drag
    out["E 50% TQQQ, MA200 gate"] = dfw(t=0.5 * up.astype(float))
    out["F 67% TQQQ, MA200 gate"] = dfw(t=(2 / 3) * up.astype(float))
    return out


def run2(w: pd.DataFrame, tq: pd.Series, qq: pd.Series) -> pd.Series:
    idx = w.index
    rt = tq.reindex(idx).ffill().pct_change().fillna(0.0)
    rq = qq.reindex(idx).ffill().pct_change().fillna(0.0)
    gross = w["TQQQ"] * rt + w["QQQ"] * rq
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return (1.0 + gross - turn * 5.0 / 1e4).cumprod()


def main() -> None:
    d = load()
    ndx, qqq, tqqq = d["NDX"], d["QQQ"], d["TQQQ"]
    drag = calibrate_drag(ndx, tqqq)
    pre = ndx.loc[:"2010-02-10"]
    syn_t, syn_q = synth(pre, 3.0, drag), synth(pre, 1.0, 0.0)

    R = build(ndx)
    periods = [("SYNTHETIC 1985-2009", "1986-01-01", "2010-02-09", syn_t, syn_q),
               ("REAL 2010-2017", "2010-02-11", "2017-12-31", tqqq, qqq),
               ("REAL 2018-2026", "2018-01-01", "2026-07-23", tqqq, qqq)]

    curves = {}
    for label, lo, hi, T, Q in periods:
        print("\n" + "=" * 122)
        print(label)
        print("=" * 122)
        rows = {}
        for bn, bs in (("0 buy&hold QQQ", Q), ("0 buy&hold TQQQ", T)):
            b = bs.loc[lo:hi]
            if len(b) > 250:
                rows[bn] = stats(b / b.iloc[0])
        for name, w in R.items():
            ww = w.loc[lo:hi]
            if len(ww) < 250:
                continue
            eq = run2(ww, T, Q)
            s = stats(eq, ww)
            s["realvol%"] = 100 * eq.pct_change().std() * np.sqrt(ANN)
            rows[name] = s
            if label.startswith("REAL 2018"):
                curves[name] = eq
        print(pd.DataFrame(rows).T.round(2).to_string())

    print("\n" + "=" * 122)
    print("THE CONTROL — identical 200d timing rule, unlevered vs 3x. Sharpe is vol-normalised,")
    print("so if Sharpe does not improve, the leverage contributes size and drag, not edge.")
    print("=" * 122)
    for label, lo, hi, T, Q in periods:
        a1 = stats(run2(R["A1 QQQ, MA200 gate"].loc[lo:hi], T, Q))
        a2 = stats(run2(R["A2 TQQQ, MA200 gate"].loc[lo:hi], T, Q))
        if not a1 or not a2:
            continue
        print(f"\n  {label}")
        print(f"    QQQ  gate : CAGR {a1['CAGR%']:6.2f}%  DD {a1['maxDD%']:7.2f}%  "
              f"MAR {a1['MAR']:5.2f}  Sharpe {a1['Sharpe']:5.2f}")
        print(f"    TQQQ gate : CAGR {a2['CAGR%']:6.2f}%  DD {a2['maxDD%']:7.2f}%  "
              f"MAR {a2['MAR']:5.2f}  Sharpe {a2['Sharpe']:5.2f}")
        print(f"    -> Sharpe delta from leverage: {a2['Sharpe']-a1['Sharpe']:+.2f}   "
              f"MAR delta: {a2['MAR']-a1['MAR']:+.2f}")

    print("\n" + "=" * 122)
    print("ANNUAL RETURNS, real data 2010-2026 — the consistency test")
    print("=" * 122)
    yr = {}
    for name in ("A1 QQQ, MA200 gate", "A2 TQQQ, MA200 gate", "B TQQQ voltgt 25%",
                 "D TQQQ voltgt + low-vol gate", "E 50% TQQQ, MA200 gate"):
        eq = run2(R[name].loc["2010-02-11":], tqqq, qqq)
        yr[name] = eq.groupby(eq.index.year).apply(lambda g: 100 * (g.iloc[-1] / g.iloc[0] - 1))
    bq = qqq.loc["2010-02-11":]
    yr["buy&hold QQQ"] = bq.groupby(bq.index.year).apply(lambda g: 100 * (g.iloc[-1] / g.iloc[0] - 1))
    t = pd.DataFrame(yr).round(1)
    print(t.to_string())
    print("\n  losing years / 17:")
    print((t < 0).sum().to_string())
    t.to_csv(f"{HERE}/annual_returns_v2.csv")
    print(f"\nwrote {HERE}/annual_returns_v2.csv")


if __name__ == "__main__":
    main()

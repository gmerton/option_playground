#!/usr/bin/env python3
"""
Squeeze backtest #3 — the DIRECTION-FREE claim.

Backtests 1 and 2 tested "which way does it go", which is the momentum-histogram rule.
Carter's underlying claim is weaker and different: the squeeze marks volatility
COMPRESSION, and compression resolves into EXPANSION. That claim is direction-free and
is the one worth testing for an options book -- if true, the squeeze is a long-premium
(straddle/strangle) timing signal, not a stock-direction signal.

Measures, for fired-squeeze bars vs the same-universe baseline:
  |fwd return| over 5/10/20d          -- magnitude of the move
  realized vol of daily returns over the next 10/20d
  ratio of next-20d realized vol to trailing-20d realized vol (the expansion ratio)

Run:  PYTHONPATH=src:<thisdir> .venv/bin/python3 run_vol_expansion.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from squeeze_lib import squeeze, squeeze_duration

SRC = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
ERAS = [("2006-2011", "2006-01-01", "2011-12-31"), ("2012-2018", "2012-01-01", "2018-12-31"),
        ("2019-2021", "2019-01-01", "2021-12-31"), ("2022-2026", "2022-01-01", "2026-12-31")]


def load():
    df = pd.read_parquet(SRC)
    df["date"] = pd.to_datetime(df["date"])
    piv = lambda c: df.pivot(index="date", columns="ticker", values=c).sort_index()
    return piv("close"), piv("high"), piv("low"), piv("close") * piv("volume")


def cmp(sig, metric, elig, label):
    s = metric.where(sig & elig).stack().dropna()
    b = metric.where(elig).stack().dropna()
    if len(s) < 50:
        return {"metric": label, "n": len(s)}
    sd = metric.where(sig & elig).mean(axis=1)
    bd = metric.where(elig).mean(axis=1)
    exc = (sd - bd).dropna()
    t = exc.mean() / (exc.std(ddof=1) / np.sqrt(len(exc))) if len(exc) > 2 else np.nan
    return {"metric": label, "n": len(s), "signal": s.mean(), "baseline": b.mean(),
            "ratio": s.mean() / b.mean() if b.mean() else np.nan, "t_date": t}


def main() -> None:
    close, high, low, dolvol = load()
    addv = dolvol.rolling(50, min_periods=50).mean()
    elig = (close >= 10) & (addv >= 20e6) & close.notna()

    r = squeeze(close, high, low)
    fire, on = r["fire"], r["on"]
    dur = squeeze_duration(on).shift(1)

    ret = close.pct_change()
    rv_trail = ret.rolling(20, min_periods=20).std()
    fwd_abs = {h: (close.shift(-h) / close - 1.0).abs() * 100 for h in (5, 10, 20)}
    rv_fwd = {h: ret.shift(-h).rolling(h, min_periods=h).std().shift(-0) * np.sqrt(252) * 100
              for h in (10, 20)}
    # forward realized vol: stdev of the NEXT h daily returns
    rv_fwd = {h: ret.rolling(h, min_periods=h).std().shift(-h) * np.sqrt(252) * 100
              for h in (10, 20)}
    expansion = (rv_fwd[20] / (rv_trail * np.sqrt(252) * 100)).replace([np.inf, -np.inf], np.nan)

    pd.set_option("display.width", 200, "display.max_columns", 30)

    print("=" * 92)
    print("VOLATILITY EXPANSION after a squeeze fires — full period 2006-2026")
    print("=" * 92)
    rows = []
    for h in (5, 10, 20):
        rows.append(cmp(fire, fwd_abs[h], elig, f"|fwd return| {h}d  (%)"))
    for h in (10, 20):
        rows.append(cmp(fire, rv_fwd[h], elig, f"fwd realized vol {h}d (ann. %)"))
    rows.append(cmp(fire, expansion, elig, "fwd20 RV / trailing20 RV"))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 92)
    print("CONTROL — bars still INSIDE the squeeze (compression should show LOW fwd vol)")
    print("=" * 92)
    rows = [cmp(on, fwd_abs[10], elig, "|fwd return| 10d (%)"),
            cmp(on, rv_fwd[20], elig, "fwd realized vol 20d (ann. %)"),
            cmp(on, expansion, elig, "fwd20 RV / trailing20 RV")]
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 92)
    print("LONGER SQUEEZE = BIGGER MOVE?  (Carter's stated rule)")
    print("=" * 92)
    rows = []
    for lo, hi in [(1, 5), (6, 11), (12, 19), (20, 999)]:
        m = fire & (dur >= lo) & (dur <= hi)
        rows.append({**cmp(m, fwd_abs[10], elig, f"dur {lo}-{hi if hi<999 else '+'} : |fwd10|")})
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 92)
    print("BY ERA — expansion ratio (fwd20 RV / trailing20 RV) after a fire")
    print("=" * 92)
    rows = []
    for name, a, b in ERAS:
        m = (close.index >= a) & (close.index <= b)
        d = cmp(fire.loc[m], expansion.loc[m], elig.loc[m], name)
        rows.append(d)
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Squeeze backtest #4 — the decisive question: realized vs IMPLIED.

Backtest #3 showed post-squeeze names expand ~5% more than typical RELATIVE to their own
prior vol, while remaining below-average-vol names in absolute terms. That is only
tradable if the options are priced BELOW the expansion that follows. This tests exactly
that.

  iv30      = ATM ~30d implied vol on the signal date (Athena options_daily_v3)
  rv_fwd    = realized vol of the next 21 trading days, annualized
  VRP       = rv_fwd - iv30      (positive => buying premium won)
  ratio     = rv_fwd / iv30

Long premium is a losing trade on average (the variance risk premium is negative for
buyers). The question is NOT "is VRP positive after a squeeze" but "is VRP LESS NEGATIVE
after a squeeze than at baseline" -- i.e. does the squeeze identify relatively cheap options.

Run:  PYTHONPATH=src:<thisdir> .venv/bin/python3 run_vrp_test.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from squeeze_lib import squeeze, squeeze_duration

PX = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
IV = "data/carter_mastering_the_trade/backtests/squeeze/iv30.parquet"
ERAS = [("2010-2013", "2010-01-01", "2013-12-31"), ("2014-2018", "2014-01-01", "2018-12-31"),
        ("2019-2021", "2019-01-01", "2021-12-31"), ("2022-2026", "2022-01-01", "2026-12-31")]
H = 21


def cmp(sig, metric, elig, label):
    s = metric.where(sig & elig).stack().dropna()
    b = metric.where(elig).stack().dropna()
    if len(s) < 50:
        return {"cohort": label, "n": len(s)}
    sd = metric.where(sig & elig).mean(axis=1)
    bd = metric.where(elig).mean(axis=1)
    exc = (sd - bd).dropna()
    t = exc.mean() / (exc.std(ddof=1) / np.sqrt(len(exc))) if len(exc) > 2 else np.nan
    return {"cohort": label, "n": len(s), "signal": s.mean(), "baseline": b.mean(),
            "diff": s.mean() - b.mean(), "t_date": t}


def main() -> None:
    df = pd.read_parquet(PX)
    df["date"] = pd.to_datetime(df["date"])
    piv = lambda c: df.pivot(index="date", columns="ticker", values=c).sort_index()
    close, high, low = piv("close"), piv("high"), piv("low")
    dolvol = close * piv("volume")

    ivdf = pd.read_parquet(IV)
    iv = (ivdf.pivot(index="trade_date", columns="ticker", values="iv30")
          .reindex(index=close.index, columns=close.columns))
    nct = (ivdf.pivot(index="trade_date", columns="ticker", values="n_contracts")
           .reindex(index=close.index, columns=close.columns))
    iv = iv.where(nct >= 2)                       # drop 1-contract days (noisy ATM proxy)

    ret = close.pct_change()
    rv_fwd = ret.rolling(H, min_periods=H).std().shift(-H) * np.sqrt(252)
    vrp = (rv_fwd - iv) * 100                      # vol points
    ratio = rv_fwd / iv

    addv = dolvol.rolling(50, min_periods=50).mean()
    elig = (close >= 10) & (addv >= 20e6) & close.notna() & iv.notna() & rv_fwd.notna()

    r = squeeze(close, high, low)
    fire, on, mom = r["fire"], r["on"], r["mom"]
    dur = squeeze_duration(on).shift(1)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(f"IV coverage: {iv.notna().sum().sum():,} ticker-days   "
          f"eligible cells: {int(elig.sum().sum()):,}")
    print(f"fires with IV: {int((fire & elig).sum().sum()):,}\n")

    print("=" * 96)
    print("IS THE OPTION CHEAP?  VRP = fwd 21d realized vol - ATM 30d IV, in vol points")
    print("(less negative than baseline = relatively cheap premium)")
    print("=" * 96)
    rows = [cmp(fire, vrp, elig, "squeeze FIRED"),
            cmp(on, vrp, elig, "still IN squeeze"),
            cmp(fire & (mom > 0), vrp, elig, "fired + mom>0"),
            cmp(fire & (dur >= 12), vrp, elig, "fired, dur>=12")]
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 96)
    print("COMPONENTS — is IV depressed MORE or LESS than realized vol?")
    print("=" * 96)
    rows = [cmp(fire, iv * 100, elig, "IV30 (ann. %)  : fired"),
            cmp(on, iv * 100, elig, "IV30 (ann. %)  : in squeeze"),
            cmp(fire, rv_fwd * 100, elig, "fwd RV (ann. %): fired"),
            cmp(on, rv_fwd * 100, elig, "fwd RV (ann. %): in squeeze"),
            cmp(fire, ratio, elig, "RV/IV ratio    : fired"),
            cmp(on, ratio, elig, "RV/IV ratio    : in squeeze")]
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 96)
    print("BY ERA — VRP diff vs baseline (vol points), squeeze FIRED")
    print("=" * 96)
    rows = []
    for name, a, b in ERAS:
        m = (close.index >= a) & (close.index <= b)
        rows.append(cmp(fire.loc[m], vrp.loc[m], elig.loc[m], name))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))

    print("\n" + "=" * 96)
    print("BY SQUEEZE DURATION — VRP diff vs baseline (vol points)")
    print("=" * 96)
    rows = []
    for lo, hi in [(1, 5), (6, 11), (12, 19), (20, 999)]:
        rows.append(cmp(fire & (dur >= lo) & (dur <= hi), vrp, elig,
                        f"dur {lo}-{hi if hi < 999 else '+'}"))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:9.4f}"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Squeeze backtest #2 — 20 years, era-split. This is the one that addresses regime decay.

Eras:
  2006-2011  GFC + recovery
  2012-2018  the tape the 3rd edition was written against
  2019-2021  3rd-edition publication + COVID
  2022-2026  the 0DTE era (SPX dailies completed 2022)

Everything is reported as signal-minus-baseline over the same universe/dates, so the
universe's survivorship bias largely cancels. Date-level t-stats (mean excess per date,
then stats across dates) are the honest significance measure — raw n is not independent.

Run:  PYTHONPATH=src:<thisdir> .venv/bin/python3 run_longhistory_backtest.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from squeeze_lib import squeeze, squeeze_duration, forward_returns

SRC = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
ERAS = [("2006-2011", "2006-01-01", "2011-12-31"),
        ("2012-2018", "2012-01-01", "2018-12-31"),
        ("2019-2021", "2019-01-01", "2021-12-31"),
        ("2022-2026", "2022-01-01", "2026-12-31")]
HORIZONS = (5, 10, 20)


def load():
    df = pd.read_parquet(SRC)
    df["date"] = pd.to_datetime(df["date"])
    piv = lambda c: df.pivot(index="date", columns="ticker", values=c).sort_index()
    return piv("close"), piv("high"), piv("low"), piv("close") * piv("volume")


def row(sig, f, elig, label, era):
    s = f.where(sig & elig).stack().dropna()
    b = f.where(elig).stack().dropna()
    if len(s) < 50:
        return {"era": era, "setup": label, "n": len(s)}
    sd = f.where(sig & elig).mean(axis=1)
    bd = f.where(elig).mean(axis=1)
    exc = (sd - bd).dropna()
    t = exc.mean() / (exc.std(ddof=1) / np.sqrt(len(exc))) if len(exc) > 2 else np.nan
    return {"era": era, "setup": label, "n": len(s),
            "mean%": s.mean() * 100, "win%": (s > 0).mean() * 100,
            "base%": b.mean() * 100, "basewin%": (b > 0).mean() * 100,
            "edge%": (s.mean() - b.mean()) * 100, "t_date": t}


def main() -> None:
    close, high, low, dolvol = load()
    print(f"{close.shape[1]} names, {close.index.min().date()} -> {close.index.max().date()}, "
          f"{len(close)} sessions\n")

    addv = dolvol.rolling(50, min_periods=50).mean()
    elig_all = (close >= 10) & (addv >= 20e6) & close.notna()

    r = squeeze(close, high, low)
    fire, mom, on = r["fire"], r["mom"], r["on"]
    dur = squeeze_duration(on).shift(1)
    fwd = forward_returns(close, HORIZONS)
    mom_up = mom > 0

    sigs = {
        "fire + mom>0  [Carter LONG]": fire & mom_up,
        "fire + mom<0  [Carter SHORT]": fire & ~mom_up,
        "fire (any direction)": fire,
        "fire + mom>0 + dur>=6": fire & mom_up & (dur >= 6),
    }

    pd.set_option("display.width", 220, "display.max_columns", 50)

    print("=" * 100)
    print("FULL PERIOD 2006-2026")
    print("=" * 100)
    rows = [row(s, fwd[h], elig_all, f"{lbl}  h={h}", "all")
            for lbl, s in sigs.items() for h in HORIZONS]
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    print("\n" + "=" * 100)
    print("BY ERA — Carter's long signal (fire + mom>0), the regime-decay question")
    print("=" * 100)
    rows = []
    for name, a, b in ERAS:
        m = (close.index >= a) & (close.index <= b)
        e = elig_all.loc[m]
        for h in HORIZONS:
            rows.append(row((fire & mom_up).loc[m], fwd[h].loc[m], e, f"long h={h}", name))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    print("\n" + "=" * 100)
    print("BY ERA — squeeze-ON rate (is the indicator even firing the same amount?)")
    print("=" * 100)
    rows = []
    for name, a, b in ERAS:
        m = (close.index >= a) & (close.index <= b)
        e = elig_all.loc[m]
        rows.append({"era": name,
                     "on_rate%": on.loc[m].where(e).stack().mean() * 100,
                     "fires": int((fire & elig_all).loc[m].sum().sum()),
                     "sessions": int(m.sum())})
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    out = "data/carter_mastering_the_trade/backtests/squeeze/longhistory_results.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

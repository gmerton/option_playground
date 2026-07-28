#!/usr/bin/env python3
"""
RE-ENTRY TEST — does allowing re-entry make tight stops viable?

WHY
    Two successful traders give opposite advice on the crux question:
      LUK          1-1.5% stops on SWING trades; tightened them over years and says performance
                   "lifted off" as he did. His trade log contains explicit `action: reentry` rows
                   ("Yes, I did get stopped out, but I re-entered it").
      BREITSTEIN   tight intraday stops on daily setups were his BIGGEST early mistake. "If you're
                   trading based on the daily chart, your risk management needs to align with the
                   daily chart… if your stop is three times wider, your size needs to be three
                   times smaller."  (`k-X0164r66U` @06:50-08:24)

    The most likely reconciliation: a tight stop is not a rejection of the thesis, it is a cheap
    PROBE — you pay several small stops to be positioned for one large win, and the trade only
    works if you go back in. Luk re-enters; a simulation that forbids re-entry pays every stop and
    collects none of the eventual win.

    ⚠ Every backtest in this repo used COOLDOWN = 10 trading days, which STRUCTURALLY FORBIDS
    exactly that behaviour. Tight stops were therefore tested in the one configuration guaranteed
    to make them look worst.

TEST
    Same broad panel, same regime gate, GATES entry. Vary only the cooldown (10 -> 3 -> 0) across
    tight and wide stops. If the re-entry thesis is right, shortening the cooldown should help the
    TIGHT stops disproportionately and barely move the wide ones.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/run_reentry.py
"""
from __future__ import annotations

import glob
import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, "data/carter_mastering_the_trade/backtests/risk_architecture")
import arch_lib as A  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

HERE = "data/carter_mastering_the_trade/backtests/risk_architecture"
BROAD = f"{HERE}/broad_history/part_*.parquet"
SPY_SRC = "data/carter_mastering_the_trade/backtests/opening_gap/gapdata.parquet"

A.STOPS = [s for s in A.STOPS if s[0] in ("1.5%", "3.0%", "bar low", "2.0ATR")]
A.EXITS = ["close<50EMA"]
COOLDOWNS = [10, 3, 0]
TIERS = ("GATES", "BREAKOUT")


def regime_on() -> pd.Series:
    spy = pd.read_parquet(SPY_SRC)
    spy = spy[spy.ticker == "SPY"].sort_values("date").set_index("date")["close"]
    ma = spy.rolling(200, min_periods=200).mean()
    return ((spy > ma) & (ma > ma.shift(20))).fillna(False)


def main() -> None:
    parts = sorted(glob.glob(BROAD))
    if not parts:
        sys.exit("no broad_history parts")
    rser = regime_on()
    panel = [pd.read_parquet(p) for p in parts]

    rows, ptrows = [], []
    for cd in COOLDOWNS:
        A.COOLDOWN = cd
        trades = []
        for px in panel:
            px = px.dropna(subset=["open", "close"]).sort_values(["ticker", "date"])
            for tkr, g in px.groupby("ticker"):
                if len(g) < 400:
                    continue
                a = A.prep(g.reset_index(drop=True))
                on = rser.reindex(pd.DatetimeIndex(a["dates"])).ffill().fillna(False).to_numpy()
                tiers = A.entry_tiers(a)
                for name in TIERS:
                    sig = A.to_indices(tiers[name] & on, len(a["c"]))
                    trades += A.run(a, sig, tkr, name)
        df = pd.DataFrame(trades)
        if df.empty:
            continue
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        df["exit_date"] = pd.to_datetime(df["exit_date"])
        print(f"cooldown={cd:2}d: {len(df):,} trade rows", flush=True)

        for (en, st), g in df.groupby(["entry", "stop"], observed=True):
            acct = g["pos"] * g["ret"]
            ptrows.append({"cooldown": cd, "entry": en, "stop": st, "n": len(g),
                           "stop_w%": 100 * g.stop_pct.mean(),
                           "mean_ret%": 100 * g.ret.mean(),
                           "acct_bp": 1e4 * acct.mean(),
                           "t": acct.mean() / (acct.std(ddof=1) / np.sqrt(len(g))),
                           "stopout%": 100 * (g.why == "stop").mean()})
            for slots in (30, 50):
                r = A.simulate(g, slots=slots)
                if r:
                    rows.append({"cooldown": cd, "entry": en, "stop": st, "slots": slots, **r})

    pt = pd.DataFrame(ptrows)
    res = pd.DataFrame(rows)
    res.to_csv(f"{HERE}/reentry_results.csv", index=False)

    order = ["1.5%", "bar low", "3.0%", "2.0ATR"]
    print("\n" + "=" * 110)
    print("1.  TRADE COUNT — does a shorter cooldown actually produce re-entries?")
    print("=" * 110)
    print(pt[pt.entry == "GATES"].pivot(index="stop", columns="cooldown", values="n")
          .reindex(order).to_string())

    print("\n" + "=" * 110)
    print("2.  ACCOUNT bp PER TRADE, by cooldown  (GATES, regime-gated)")
    print("    Re-entry thesis predicts: tight stops improve a lot, wide stops barely move.")
    print("=" * 110)
    for tier in TIERS:
        s = pt[pt.entry == tier]
        if s.empty:
            continue
        print(f"\n  {tier}:")
        print(s.pivot(index="stop", columns="cooldown", values="acct_bp")
              .reindex(order).round(2).to_string())
        print("  stop-out %:")
        print(s.pivot(index="stop", columns="cooldown", values="stopout%")
              .reindex(order).round(1).to_string())

    print("\n" + "=" * 110)
    print("3.  PORTFOLIO CAGR % (50 slots) — the decision-relevant number")
    print("=" * 110)
    for tier in TIERS:
        s = res[(res.entry == tier) & (res.slots == 50)]
        if s.empty:
            continue
        print(f"\n  {tier}:")
        print(s.pivot(index="stop", columns="cooldown", values="CAGR%")
              .reindex(order).round(2).to_string())
        print("  max drawdown %:")
        print(s.pivot(index="stop", columns="cooldown", values="maxDD%")
              .reindex(order).round(1).to_string())
        print("  avg exposure %:")
        print(s.pivot(index="stop", columns="cooldown", values="avg_expo%")
              .reindex(order).round(1).to_string())

    print(f"\nwrote {HERE}/reentry_results.csv")


if __name__ == "__main__":
    main()

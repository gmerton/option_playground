#!/usr/bin/env python3
"""
Opening-gap fade study — Carter, *Mastering the Trade* (3rd ed.), ch. 7.

WHAT THIS TESTS
    The claim under test is the base statistic, not Carter's discretionary execution:
    "index gaps fill intraday at a high rate, so fade them."

    Fade = at the open, take the side opposite the gap. Target = prior close (the fill).
    If the gap never fills, exit on the close.

WHAT DAILY BARS CAN AND CANNOT SEE
    CAN, exactly:
      * fill / no-fill              gap up: low <= prior close     (gap down: high >= prior close)
      * adverse excursion (MAE)     gap up: high - open
      * favorable excursion (MFE)   gap up: open - low
    CANNOT:
      * the ORDER of the intraday touches. On a day that touches both the stop and the fill,
        daily bars cannot say which came first. Every stopped variant is therefore reported as a
        BRACKET: pessimistic (ambiguous day = stopped out) and optimistic (ambiguous = filled).
        The truth is inside the bracket. The ambiguity rate is printed so the bracket's width
        is never hidden.
      * Carter's actual entry, which is ~15-20 min after the bell, not at the bell. Entering at
        the open is a BETTER price for a fade than waiting for the pullback to fail, so the
        no-stop numbers here are optimistic relative to the book.

    Design consequence: if the optimistic-entry / pessimistic-ambiguity version is negative,
    the setup is dead and no intraday data is needed to bury it.

THRESHOLDS
    Carter states gap-size filters in INDEX POINTS. SPX roughly doubled since the 2019 edition,
    so his points are not portable. Everything here is bucketed in ATR units (gap / ATR14 known
    before the open), which is the scale-free version of the same rule.

Usage:  PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/opening_gap/run_gap_study.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

HERE = "data/carter_mastering_the_trade/backtests/opening_gap"
COST_BP = 2.0          # round-trip slippage+commission, basis points of notional
ATR_N = 14
PRIMARY = "SPY"

BUCKETS = [0.0, 0.25, 0.5, 1.0, 2.0, np.inf]
BUCKET_LABELS = ["0-0.25", "0.25-0.5", "0.5-1.0", "1.0-2.0", ">2.0"]


# ---------------------------------------------------------------- data prep

def build(df: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    out = []
    for tkr, g in df.groupby("ticker"):
        g = g.sort_values("date").copy()
        pc = g["close"].shift(1)
        tr = pd.concat([g["high"] - g["low"],
                        (g["high"] - pc).abs(),
                        (g["low"] - pc).abs()], axis=1).max(axis=1)
        # ATR known BEFORE the open of day t -> shift(1)
        g["atr"] = tr.rolling(ATR_N, min_periods=ATR_N).mean().shift(1)
        g["prev_close"] = pc
        g["prev_high"] = g["high"].shift(1)
        g["prev_low"] = g["low"].shift(1)
        g["prev_ret"] = (g["close"] / pc - 1.0).shift(1)
        g["prev_range"] = (g["high"] - g["low"]).shift(1)
        out.append(g)
    d = pd.concat(out, ignore_index=True)

    d["gap"] = d["open"] - d["prev_close"]
    d["gap_pct"] = d["gap"] / d["prev_close"]
    d["gap_atr"] = d["gap"] / d["atr"]
    d["agap_atr"] = d["gap_atr"].abs()
    d = d.dropna(subset=["gap_atr", "atr"])
    d = d[d["gap"] != 0].copy()

    d["side"] = -np.sign(d["gap"])                       # fade: short a gap up
    up = d["gap"] > 0

    # exact from daily bars
    d["filled"] = np.where(up, d["low"] <= d["prev_close"], d["high"] >= d["prev_close"])
    d["mae"] = np.where(up, d["high"] - d["open"], d["open"] - d["low"]) / d["open"]
    d["mfe"] = np.where(up, d["open"] - d["low"], d["high"] - d["open"]) / d["open"]
    d["mae_r"] = d["mae"] * d["open"] / d["gap"].abs()   # adverse excursion in units of gap size
    d["ret_target"] = d["gap"].abs() / d["open"]         # payoff if the fill is reached
    d["ret_close"] = d["side"] * (d["close"] - d["open"]) / d["open"]
    d["oc_long"] = (d["close"] - d["open"]) / d["open"]  # unconditional open->close drift

    d["bucket"] = pd.cut(d["agap_atr"], bins=BUCKETS, labels=BUCKET_LABELS, right=False)
    d["dir"] = np.where(up, "gap up", "gap down")
    d["year"] = d["date"].dt.year
    d["era"] = np.where(d["date"] >= "2022-05-01", "post-0DTE (2022-05+)", "pre-0DTE")
    # open inside the prior day's range vs. beyond it (Carter's breakaway distinction)
    d["inside_prior_range"] = np.where(up, d["open"] <= d["prev_high"], d["open"] >= d["prev_low"])
    d["after_trend_day"] = d["prev_ret"].abs() * d["prev_close"] >= d["atr"]
    d["first_of_month"] = d["date"].dt.month != d["date"].shift(1).dt.month

    d = d.merge(vix, on="date", how="left")
    d["vix_prev"] = d.groupby("ticker")["vix"].shift(1)
    return d


# ---------------------------------------------------------- trade evaluation

def no_stop(d: pd.DataFrame) -> pd.Series:
    """Fade with no stop: exit at the fill, else at the close."""
    return np.where(d["filled"], d["ret_target"], d["ret_close"]) - COST_BP / 1e4


def with_stop(d: pd.DataFrame, stop_dollars: pd.Series):
    """Fade with a hard stop. Returns (pessimistic, optimistic, ambiguous_flag)."""
    up = d["gap"] > 0
    stop_hit = np.where(up, d["high"] >= d["open"] + stop_dollars,
                            d["low"] <= d["open"] - stop_dollars)
    ret_stop = -stop_dollars / d["open"]
    filled = d["filled"].values
    ambiguous = stop_hit & filled

    base = np.where(~stop_hit & ~filled, d["ret_close"], np.nan)
    pess = np.where(stop_hit, ret_stop, np.where(filled, d["ret_target"], d["ret_close"]))
    opt = np.where(filled, d["ret_target"], np.where(stop_hit, ret_stop, d["ret_close"]))
    del base
    return (pd.Series(pess, index=d.index) - COST_BP / 1e4,
            pd.Series(opt, index=d.index) - COST_BP / 1e4,
            pd.Series(ambiguous, index=d.index))


# ------------------------------------------------------------------ reports

def stats(r: pd.Series) -> dict:
    r = pd.Series(r).dropna()
    n = len(r)
    if n < 20:
        return {}
    mean_bp = r.mean() * 1e4
    t = r.mean() / (r.std(ddof=1) / np.sqrt(n)) if r.std(ddof=1) > 0 else np.nan
    wins, losses = r[r > 0], r[r <= 0]
    return {
        "n": n,
        "win%": 100 * len(wins) / n,
        "mean_bp": mean_bp,
        "t": t,
        "med_win_bp": wins.median() * 1e4 if len(wins) else np.nan,
        "med_loss_bp": losses.median() * 1e4 if len(losses) else np.nan,
        "worst_bp": r.min() * 1e4,
        "p01_bp": r.quantile(0.01) * 1e4,
        "sum_pct": r.sum() * 100,
    }


def table(d: pd.DataFrame, retcol: str, by, title: str) -> None:
    rows = {}
    for key, g in d.groupby(by, observed=True):
        s = stats(g[retcol])
        if s:
            rows[key if not isinstance(key, tuple) else " / ".join(map(str, key))] = s
    if not rows:
        return
    t = pd.DataFrame(rows).T
    t["n"] = t["n"].astype(int)
    print(f"\n{title}")
    print(t.round(2).to_string())


def hline(s: str) -> None:
    print("\n" + "=" * 100)
    print(s)
    print("=" * 100)


# --------------------------------------------------------------------- main

def main() -> None:
    px = pd.read_parquet(f"{HERE}/gapdata.parquet")
    vix = pd.read_parquet(f"{HERE}/vix.parquet")
    d = build(px, vix)

    hline("0.  SAMPLE")
    for tkr, g in d.groupby("ticker"):
        print(f"  {tkr}: {len(g):,} gap days  {g.date.min().date()} -> {g.date.max().date()}"
              f"   median |gap| = {g.gap_pct.abs().median()*1e4:.0f} bp"
              f"   = {g.agap_atr.median():.2f} ATR")
    print(f"\n  Costs applied: {COST_BP:.0f} bp round trip. ATR = {ATR_N}d, known before the open.")

    # ---------------------------------------------------------------- 1. fill rates
    hline("1.  FILL RATE — the headline statistic, exactly measurable from daily bars")
    fr = d.pivot_table(index="bucket", columns="ticker", values="filled",
                       aggfunc="mean", observed=True) * 100
    cnt = d.pivot_table(index="bucket", columns="ticker", values="filled",
                        aggfunc="size", observed=True)
    print("\n  same-session fill %, by gap size (ATR units)")
    print(fr.round(1).to_string())
    print("\n  n days")
    print(cnt.to_string())
    print("\n  ALL gaps, fill % by ticker:")
    print((d.groupby("ticker")["filled"].mean() * 100).round(1).to_string())
    print("\n  fill % by ticker x direction:")
    print((d.pivot_table(index="dir", columns="ticker", values="filled",
                         aggfunc="mean") * 100).round(1).to_string())

    # ---------------------------------------------------------------- 2. MAE
    hline("2.  WHAT THE FILL RATE HIDES — adverse excursion before the fill is available")
    sp = d[d.ticker == PRIMARY]
    mae = sp.groupby("bucket", observed=True).agg(
        n=("mae_r", "size"),
        fill_pct=("filled", lambda x: 100 * x.mean()),
        med_MAE_in_gaps=("mae_r", "median"),
        p75_MAE=("mae_r", lambda x: x.quantile(0.75)),
        p95_MAE=("mae_r", lambda x: x.quantile(0.95)),
        med_MAE_bp=("mae", lambda x: x.median() * 1e4),
        p95_MAE_bp=("mae", lambda x: x.quantile(0.95) * 1e4),
    )
    print(f"\n  {PRIMARY}: adverse excursion from the open, in multiples of the gap being faded.")
    print("  (MAE 1.0 = price ran against you by the full size of the gap before doing anything else)")
    print(mae.round(2).to_string())

    # ---------------------------------------------------------------- 3. no-stop expectancy
    d["r_nostop"] = no_stop(d)
    hline("3.  EXPECTANCY, NO STOP  (fill -> exit at prior close; no fill -> exit at the close)")
    print("  This is the purest form of the claim, and the most favorable framing it can get:")
    print("  entry at the open, no stop to whipsaw, full gap captured on every fill.")
    table(d, "r_nostop", "ticker", "  by instrument, ALL gaps")
    table(d[d.ticker == PRIMARY], "r_nostop", "bucket", f"  {PRIMARY} by gap size (ATR)")
    table(d[d.ticker == PRIMARY], "r_nostop", "dir", f"  {PRIMARY} by direction")
    table(d[d.ticker == PRIMARY], "r_nostop", ["dir", "bucket"],
          f"  {PRIMARY} by direction x gap size")

    print("\n  REFERENCE — unconditional open->close drift on the same days (long, no cost):")
    ref = {}
    for tkr, g in d.groupby("ticker"):
        ref[tkr] = {"n": len(g), "mean_bp": g.oc_long.mean() * 1e4,
                    "up_days_mean_bp": g.loc[g.gap > 0, "oc_long"].mean() * 1e4,
                    "dn_days_mean_bp": g.loc[g.gap < 0, "oc_long"].mean() * 1e4}
    print(pd.DataFrame(ref).T.round(2).to_string())

    # ---------------------------------------------------------------- 4. stops
    hline("4.  EXPECTANCY WITH A STOP — reported as a bracket (daily bars can't order the touches)")
    variants = {
        "stop = 1.0x gap (1:1)": d["gap"].abs(),
        "stop = 0.5 ATR": 0.5 * d["atr"],
        "stop = 1.0 ATR": 1.0 * d["atr"],
    }
    for name, sd in variants.items():
        pess, opt, amb = with_stop(d, sd)
        d[f"pess::{name}"] = pess
        d[f"opt::{name}"] = opt
        sub = d[d.ticker == PRIMARY]
        sp_amb = amb[d.ticker == PRIMARY]
        p, o = stats(sub[f"pess::{name}"]), stats(sub[f"opt::{name}"])
        print(f"\n  {PRIMARY}  {name}   ambiguous days (stop AND fill touched): "
              f"{100*sp_amb.mean():.1f}%")
        print(f"    pessimistic : n={p['n']}  win%={p['win%']:.1f}  mean={p['mean_bp']:+.2f} bp  "
              f"t={p['t']:+.2f}  worst={p['worst_bp']:.0f} bp")
        print(f"    optimistic  : n={o['n']}  win%={o['win%']:.1f}  mean={o['mean_bp']:+.2f} bp  "
              f"t={o['t']:+.2f}  worst={o['worst_bp']:.0f} bp")

    # ---------------------------------------------------------------- 5. regime
    hline("5.  REGIME DECAY — does the 2019-vintage claim survive 0DTE and 2020?")
    table(d[d.ticker == PRIMARY], "r_nostop", "era", f"  {PRIMARY} no-stop, pre/post 0DTE")
    print("\n  fill % by era:")
    print((d.pivot_table(index="era", columns="ticker", values="filled",
                         aggfunc="mean") * 100).round(1).to_string())

    sp = d[d.ticker == PRIMARY].copy()
    sp["vix_bucket"] = pd.qcut(sp["vix_prev"], 3, labels=["VIX low", "VIX mid", "VIX high"])
    table(sp, "r_nostop", "vix_bucket", f"  {PRIMARY} no-stop, by prior-close VIX tercile")
    print("\n  fill % by VIX tercile:")
    print((sp.groupby("vix_bucket", observed=True)["filled"].mean() * 100).round(1).to_string())

    print("\n  by year (mean bp per trade, no stop):")
    yr = sp.groupby("year").agg(n=("r_nostop", "size"),
                                mean_bp=("r_nostop", lambda x: x.mean() * 1e4),
                                fill_pct=("filled", lambda x: 100 * x.mean()))
    print(yr.round(1).to_string())

    # ---------------------------------------------------------------- 6. Carter's filters
    hline("6.  CARTER'S OWN CONDITIONING RULES — do the mechanical ones earn their place?")
    table(sp, "r_nostop", "inside_prior_range",
          f"  {PRIMARY}: open inside prior day's range (True) vs. beyond it (False)")
    print("\n  fill % inside vs beyond prior range:")
    print((sp.groupby("inside_prior_range")["filled"].mean() * 100).round(1).to_string())
    table(sp, "r_nostop", "after_trend_day",
          f"  {PRIMARY}: day after a >=1 ATR move (True = Carter says don't fade)")
    table(sp, "r_nostop", "first_of_month",
          f"  {PRIMARY}: first trading day of month (True = Carter says don't fade)")

    # ---------------------------------------------------------------- 7. tradeable subset
    hline("7.  THE TRADEABLE SUBSET — gaps big enough to be worth the ticket (>= 0.5 ATR)")
    trad = d[(d.agap_atr >= 0.5)]
    table(trad, "r_nostop", "ticker", "  no stop, |gap| >= 0.5 ATR")
    table(trad[trad.ticker == PRIMARY], "r_nostop", ["era", "dir"],
          f"  {PRIMARY}, |gap| >= 0.5 ATR, by era x direction")

    d.to_csv(f"{HERE}/gap_trades.csv", index=False)
    print(f"\n\nwrote {HERE}/gap_trades.csv  ({len(d):,} rows)")


if __name__ == "__main__":
    main()

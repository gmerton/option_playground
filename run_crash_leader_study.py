#!/usr/bin/env python3
"""
Crash-leader reversion study — the anti-Minervini.

QUESTION: does buying a formerly-STRONG stock that has just been MASSIVELY sold off
beat the tape? Minervini buys strength near highs; this buys quality at maximum
discount. Both cannot be right about the same names at the same time.

DESIGN
  universe   data/carter_mastering_the_trade/backtests/risk_architecture/broad_history
             (2,674 names, 2006-2026, daily OHLCV, liquid subset of the Minervini cache)
  strength   measured INTO the peak, so it is a statement about the pre-crash stock:
               runup  = 252d high is >= +RUNUP% above the close 252 bars ago
               2yhigh = the 252d high was also a 504d high (a genuine leader)
  crash      close is <= -DD% below the trailing 252d high, AND that high was set
             within the last 126 bars (recent crash, not a multi-year bleed).
             Vectorized as max(high,126) == max(high,252).
  entry      the fork — "now underpriced" has several defensible readings:
               arrival    first bar the drawdown gate trips (catch the knife)
               stab10     gate tripped + no new 20-bar low for 10 bars (it stopped falling)
               reclaim20  gate tripped + close crosses back above the 20 EMA
               rsi_turn   gate tripped + RSI(14) came from <30 and turned up
             All fills are the NEXT bar's OPEN (signal is a close-based decision).
  vehicle    50d ADDV >= $10M and price >= $5 at signal.
  dedupe     one event per ticker per episode: suppress re-entries for 63 bars.
  measure    forward 21/63/126/252-bar returns, and EXCESS vs the same-date
             cross-sectional median of the eligible universe. The paired design is
             what makes the survivorship bias tolerable: both the event names and
             the benchmark are drawn from the same survivors-only pool on the same
             date, so the market/regime component cancels.

⚠ SURVIVORSHIP: broad_history is the universe that exists TODAY. Names that crashed
  and never recovered (or delisted) are ABSENT. This inflates the raw event returns
  of THIS strategy more than almost any other. Read the excess columns, not the raw.

Run:
    PYTHONPATH=src .venv/bin/python3 run_crash_leader_study.py
    ... --dd 30 --strength runup --entries arrival,stab10,reclaim20
"""
from __future__ import annotations

import argparse
import glob
import sys

import numpy as np
import pandas as pd

HIST = "data/carter_mastering_the_trade/backtests/risk_architecture/broad_history/*.parquet"
HORIZONS = [21, 63, 126, 252]


# ---------------------------------------------------------------- data

def load_panel() -> dict[str, pd.DataFrame]:
    """Load the chunked history into wide date x ticker frames."""
    files = sorted(glob.glob(HIST))
    if not files:
        sys.exit(f"no history found at {HIST}")
    parts = [pd.read_parquet(f) for f in files]
    df = pd.concat(parts, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    out = {}
    for col in ("open", "high", "low", "close", "volume"):
        out[col] = df.pivot(index="date", columns="ticker", values=col).astype("float32")
    return out


# ---------------------------------------------------------------- indicators

def rsi(close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def build_signals(px, dd_pct, runup_pct, strength, entry, addv_min, price_min):
    close, high, low, vol = px["close"], px["high"], px["low"], px["volume"]

    max252 = high.rolling(252, min_periods=252).max()
    max126 = high.rolling(126, min_periods=126).max()
    max504 = high.rolling(504, min_periods=504).max()

    drawdown = close / max252 - 1                       # <= 0
    recent_peak = max126 >= max252 * 0.9999             # peak set in the last 126 bars

    if strength == "runup":
        strong = (max252 / close.shift(252) - 1) >= runup_pct / 100
    elif strength == "2yhigh":
        strong = max252 >= max504 * 0.9999
    elif strength == "both":
        strong = ((max252 / close.shift(252) - 1) >= runup_pct / 100) & (max252 >= max504 * 0.9999)
    else:                                                # no strength filter -- the control
        strong = pd.DataFrame(True, index=close.index, columns=close.columns)

    addv = (close * vol).rolling(50, min_periods=50).mean()
    vehicle = (addv >= addv_min) & (close >= price_min)

    gate = (drawdown <= -dd_pct / 100) & recent_peak & strong & vehicle

    if entry == "arrival":
        trig = gate & ~gate.shift(1, fill_value=False)
    elif entry == "stab10":
        low20 = low.rolling(20, min_periods=20).min()
        no_new_low = (low > low20.shift(1)).rolling(10, min_periods=10).min().astype(bool)
        cond = gate & no_new_low
        trig = cond & ~cond.shift(1, fill_value=False)
    elif entry == "reclaim20":
        ema20 = close.ewm(span=20, adjust=False).mean()
        cross = (close > ema20) & (close.shift(1) <= ema20.shift(1))
        trig = gate & cross
    elif entry == "rsi_turn":
        r = rsi(close)
        was_os = (r < 30).rolling(10, min_periods=1).max().astype(bool)
        cross = was_os & (r > 30) & (r.shift(1) <= 30)
        trig = gate & cross
    else:
        sys.exit(f"unknown entry {entry}")

    return trig.fillna(False), drawdown, vehicle


def dedupe(trig: pd.DataFrame, bars: int = 63) -> pd.DataFrame:
    """Suppress repeat signals within `bars` of a prior one, per ticker."""
    arr = trig.to_numpy()
    out = np.zeros_like(arr, dtype=bool)
    for j in range(arr.shape[1]):
        rows = np.flatnonzero(arr[:, j])
        last = -10**9
        for i in rows:
            if i - last >= bars:
                out[i, j] = True
                last = i
    return pd.DataFrame(out, index=trig.index, columns=trig.columns)


# ---------------------------------------------------------------- returns

def forward_returns(px, vehicle):
    """Fill at next open; measure to close h bars after the signal bar."""
    close, open_ = px["close"], px["open"]
    entry_px = open_.shift(-1)
    fwd, bench = {}, {}
    for h in HORIZONS:
        r = close.shift(-h) / entry_px - 1
        fwd[h] = r
        # same-date benchmark: median forward return of every eligible (liquid) name
        bench[h] = r.where(vehicle).median(axis=1)
    return fwd, bench


def collect(trig, fwd, bench, drawdown):
    rows = []
    idx = trig.index
    for h in HORIZONS:
        r = fwd[h].where(trig)
        stacked = r.stack()
        if stacked.empty:
            continue
        b = bench[h].reindex(stacked.index.get_level_values(0)).to_numpy()
        rows.append(pd.DataFrame({
            "date": stacked.index.get_level_values(0),
            "ticker": stacked.index.get_level_values(1),
            "h": h,
            "ret": stacked.to_numpy(),
            "bench": b,
            "excess": stacked.to_numpy() - b,
        }))
    if not rows:
        return pd.DataFrame(columns=["date", "ticker", "h", "ret", "bench", "excess"])
    return pd.concat(rows, ignore_index=True)


def summarize(ev: pd.DataFrame, label: str) -> pd.DataFrame:
    out = []
    for h in HORIZONS:
        s = ev[ev.h == h].dropna(subset=["excess"])
        if len(s) < 20:
            out.append({"label": label, "h": h, "n": len(s)})
            continue
        # paired t-stat on the same-date excess, clustered crudely by averaging per date
        by_date = s.groupby("date").excess.mean()
        t = by_date.mean() / (by_date.std(ddof=1) / np.sqrt(len(by_date))) if len(by_date) > 1 else np.nan
        out.append({
            "label": label, "h": h, "n": len(s), "dates": len(by_date),
            "ret%": s.ret.mean() * 100,
            "exc%": s.excess.mean() * 100,
            "med_exc%": s.excess.median() * 100,
            "win%": (s.excess > 0).mean() * 100,
            "t": t,
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="Crash-leader reversion study")
    ap.add_argument("--dd", type=float, nargs="+", default=[20, 30, 40, 50],
                    help="drawdown thresholds (%%) to sweep")
    ap.add_argument("--runup", type=float, default=25.0)
    ap.add_argument("--strength", default="runup", choices=["runup", "2yhigh", "both", "none"])
    ap.add_argument("--entries", default="arrival,stab10,reclaim20,rsi_turn")
    ap.add_argument("--addv-min", type=float, default=10e6)
    ap.add_argument("--price-min", type=float, default=5.0)
    ap.add_argument("--out", default="data/studies/crash_leader_events.parquet")
    args = ap.parse_args()

    print("loading panel ...", flush=True)
    px = load_panel()
    print(f"  {px['close'].shape[0]} bars x {px['close'].shape[1]} tickers  "
          f"({px['close'].index.min().date()} -> {px['close'].index.max().date()})", flush=True)

    # vehicle mask is entry-independent; compute the benchmark once
    close, vol = px["close"], px["volume"]
    addv = (close * vol).rolling(50, min_periods=50).mean()
    vehicle_all = (addv >= args.addv_min) & (close >= args.price_min)
    fwd, bench = forward_returns(px, vehicle_all)

    summaries, all_events = [], []
    for dd in args.dd:
        for entry in args.entries.split(","):
            trig, drawdown, _ = build_signals(px, dd, args.runup, args.strength,
                                              entry, args.addv_min, args.price_min)
            trig = dedupe(trig)
            ev = collect(trig, fwd, bench, drawdown)
            ev["dd"], ev["entry"], ev["strength"] = dd, entry, args.strength
            all_events.append(ev)
            label = f"dd{int(dd)}/{entry}"
            s = summarize(ev, label)
            summaries.append(s)
            print(f"\n--- {label}  (strength={args.strength}) ---")
            print(s.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    if all_events:
        pd.concat(all_events, ignore_index=True).to_parquet(args.out)
        print(f"\nevents -> {args.out}")
    print("\n================ SUMMARY (excess vs same-date universe median) ================")
    print(pd.concat(summaries, ignore_index=True)
          .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))


if __name__ == "__main__":
    main()

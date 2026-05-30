#!/usr/bin/env python3
"""
Characterize an intraday session into a standardized "pattern card".

Given a 1-min CSV saved by fetch_intraday.py (or a symbol+date to fetch on the
fly), compute the indicators we use for pattern work (EMA 9/20, session VWAP,
RSI-14, volume) and print a consistent profile: where the low/high were, the
capitulation context at the low, and where each candidate buy trigger first
fired after the low.

This is pattern-agnostic plumbing -- the same card is produced for every
example, so we can compare across days and tickers to set gate/trigger
thresholds. See patterns/CATALOG.md.

Usage:
  .venv/bin/python3 ibkr_bot/characterize.py data/PL_2026-05-29_1min.csv
  .venv/bin/python3 ibkr_bot/characterize.py PL 2026-05-29        # fetches if CSV missing
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
FAST, SLOW = 9, 20


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Attach ema9, ema20, session vwap, rsi14, vol_ma20 to a 1-min OHLCV df."""
    df = df.copy()
    c = df["close"]
    df["ema9"] = c.ewm(span=FAST, adjust=False).mean()
    df["ema20"] = c.ewm(span=SLOW, adjust=False).mean()
    tp = (df["high"] + df["low"] + df["close"]) / 3
    wap = df["wap"].where(df.get("wap", 0) > 0, tp) if "wap" in df else tp
    df["vwap"] = (wap * df["volume"]).cumsum() / df["volume"].cumsum()
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    df["rsi"] = 100 - 100 / (1 + up / dn.replace(0, 1e-9))
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    return df


def _first_after(df: pd.DataFrame, mask: pd.Series, after: int):
    idx = df.index[(df.index >= after) & mask]
    return idx[0] if len(idx) else None


def candidate_triggers(df: pd.DataFrame) -> dict:
    """Boolean masks for each candidate buy trigger (evaluated per-bar)."""
    c = df["close"]
    spread = df["ema9"] - df["ema20"]
    return {
        "RSI up through 40": (df["rsi"] > 40) & (df["rsi"].shift(1) <= 40),
        "2x higher-high+low": (df["high"] > df["high"].shift(1)) & (df["low"] > df["low"].shift(1))
        & (df["high"].shift(1) > df["high"].shift(2)) & (df["low"].shift(1) > df["low"].shift(2)),
        "9 EMA > 20 EMA": (spread > 0) & (spread.shift(1) <= 0),
        "close reclaims VWAP": (c > df["vwap"]) & (c.shift(1) <= df["vwap"].shift(1)),
    }


def card(sym: str, df: pd.DataFrame) -> dict:
    """Print a standardized pattern card and return its key stats as a dict."""
    df = add_indicators(df)
    day = df["time"].dt.date.iloc[-1]
    sess = df[df["time"].dt.date == day].reset_index(drop=True)
    sess = add_indicators(sess)  # recompute vwap/ema within the single session
    t = sess["time"].dt.strftime("%H:%M")

    o = sess["open"].iloc[0]
    lo_i = sess["low"].idxmin(); lo = sess["low"].iloc[lo_i]
    hi_i = sess["high"].idxmax(); hi = sess["high"].iloc[hi_i]
    last = sess["close"].iloc[-1]
    move = hi - lo

    print(f"\n===== {sym}  {day}  ({len(sess)} bars) =====")
    print(f"  open {o:.2f}  low {lo:.2f}@{t.iloc[lo_i]} ({(lo/o-1)*100:+.1f}%)  "
          f"high {hi:.2f}@{t.iloc[hi_i]} ({(hi/lo-1)*100:+.1f}% off low)  close {last:.2f}")
    print(f"  CONTEXT @ low: {(lo/sess['vwap'].iloc[lo_i]-1)*100:+.1f}% vs VWAP, "
          f"RSI {sess['rsi'].iloc[lo_i]:.0f}, "
          f"vol {sess['volume'].iloc[lo_i]:.0f} ({sess['volume'].iloc[lo_i]/sess['vol_ma20'].iloc[lo_i]:.1f}x ma)")

    shape = "low-before-high (reversal)" if hi_i > lo_i else "high-before-low (faded)"
    print(f"  SHAPE: {shape}")

    print(f"  TRIGGERS after low:  {'fires':>6} {'entry':>7} {'%off_low':>9} {'%ahead':>7}")
    rows = {}
    for name, mask in candidate_triggers(sess).items():
        i = _first_after(sess, mask, lo_i)
        if i is None:
            print(f"    {name:<22}{'never':>6}")
            rows[name] = None
            continue
        px = sess["close"].iloc[i]
        ahead = (hi - px) / move * 100 if move else 0
        print(f"    {name:<22}{t.iloc[i]:>6} {px:>7.2f} {(px/lo-1)*100:>+8.1f}% {ahead:>6.0f}%")
        rows[name] = {"time": t.iloc[i], "entry": round(px, 2),
                      "off_low_pct": round((px/lo-1)*100, 1), "ahead_pct": round(ahead)}

    return {
        "symbol": sym, "date": str(day), "open": round(o, 2),
        "low": round(lo, 2), "low_time": t.iloc[lo_i],
        "high": round(hi, 2), "high_time": t.iloc[hi_i],
        "drop_pct": round((lo/o-1)*100, 1), "rally_pct": round((hi/lo-1)*100, 1),
        "vwap_dist_at_low": round((lo/sess['vwap'].iloc[lo_i]-1)*100, 1),
        "rsi_at_low": round(sess['rsi'].iloc[lo_i]), "triggers": rows,
    }


def phb_card(sym: str, df: pd.DataFrame, base_start="12:00", base_end="14:30",
             power_start="15:00", verbose=True) -> dict:
    """Power Hour Breakout card: midday coil → late-day breakout on volume surge.

    Measures the midday base (range, width, position vs VWAP), the breakout of
    the base high during the power hour (time, price, % still ahead to the
    late-session high), the volume expansion (power-hour vs midday, and on the
    breakout bar), and how strong the close is (position in the day's range).
    Set verbose=False to suppress printing (batch use) and just return the dict.
    """
    def emit(s):
        if verbose:
            print(s)
    df = add_indicators(df)
    day = df["time"].dt.date.iloc[-1]
    sess = add_indicators(df[df["time"].dt.date == day].reset_index(drop=True))
    hhmm = sess["time"].dt.strftime("%H:%M")

    base = sess[(hhmm >= base_start) & (hhmm <= base_end)]
    bl, bh = base["low"].min(), base["high"].max()
    bw = (bh / bl - 1) * 100
    base_vwap = base["vwap"].iloc[-1]
    coil_vs_vwap = (base["close"].mean() / base_vwap - 1) * 100

    hod = sess["high"].max(); hod_t = hhmm.iloc[sess["high"].idxmax()]
    last = sess["close"].iloc[-1]
    dlo, dhi = sess["low"].min(), sess["high"].max()
    close_pos = (last - dlo) / (dhi - dlo) * 100 if dhi > dlo else 0

    base_vol_min = base["volume"].mean()
    power = sess[hhmm >= power_start]
    power_vol_x = power["volume"].mean() / base_vol_min if base_vol_min else 0

    # breakout = first bar after the base window whose close clears the base high
    post = sess[(hhmm > base_end)]
    brk = post[post["close"] > bh]
    late_high = post["high"].max()

    emit(f"\n===== PHB  {sym}  {day} =====")
    pos = "below" if coil_vs_vwap < -0.1 else ("above" if coil_vs_vwap > 0.1 else "on")
    emit(f"  BASE {base_start}-{base_end}: {bl:.2f}-{bh:.2f} ({bw:.1f}% wide), "
         f"coils {pos} VWAP ({base_vwap:.2f}, {coil_vs_vwap:+.1f}%)")
    out = {"symbol": sym, "date": str(day), "base_low": round(bl, 2), "base_high": round(bh, 2),
           "base_width_pct": round(bw, 1), "coil_vs_vwap_pct": round(coil_vs_vwap, 1),
           "hod": round(hod, 2), "close": round(last, 2),
           "close_off_hod_pct": round((last/hod-1)*100, 1), "close_pos_in_range_pct": round(close_pos),
           "power_vol_x": round(power_vol_x, 1), "breakout_time": None, "ahead_to_late_high_pct": None}
    if len(brk):
        b = brk.iloc[0]; bt = hhmm.iloc[b.name]; bpx = b["close"]
        bar_x = b["volume"] / sess["volume"].iloc[max(0, b.name-20):b.name].mean()
        ahead = (late_high - bpx) / (late_high - bl) * 100 if late_high > bl else 0
        emit(f"  BREAKOUT of base high @ {bt} ({bpx:.2f}), {ahead:.0f}% ahead to late-high {late_high:.2f}")
        emit(f"  VOLUME surge: power-hour {power_vol_x:.1f}x midday/min; breakout bar {bar_x:.1f}x trailing-20")
        out.update({"breakout_time": bt, "breakout_px": round(bpx, 2),
                    "ahead_to_late_high_pct": round(ahead), "breakout_bar_vol_x": round(bar_x, 1)})
    else:
        emit(f"  no close above base high {bh:.2f} after {base_end} (no clean breakout)")
    strong = "STRONG" if close_pos >= 80 else ("ok" if close_pos >= 60 else "weak")
    emit(f"  CLOSE {last:.2f} = {close_pos:.0f}% up day range, {(last/hod-1)*100:+.1f}% off HOD "
         f"(HOD {hod:.2f}@{hod_t})  -> {strong} close")

    # Heuristic PHB label (sort aid, not ground truth) from the N=3 signature:
    # tight coil + power-hour volume surge + late breakout + strong close.
    out["label"] = _phb_label(out)
    return out


def _phb_label(m: dict) -> str:
    """Bucket a PHB metrics dict into STRONG / weak / COUNTER (sorting aid only)."""
    broke = m["breakout_time"] is not None and m["breakout_time"] >= "15:00"
    surge = m["power_vol_x"] >= 2.5
    strong_close = m["close_pos_in_range_pct"] >= 80
    tight = m["base_width_pct"] <= 3.0
    if broke and surge and strong_close and tight:
        return "STRONG"
    if broke and (surge or strong_close) and tight:
        return "weak"
    return "COUNTER"  # coiled but no late surge/breakout, or faded into the close


def _load(arg: str, date: str | None) -> tuple[str, pd.DataFrame]:
    if arg.endswith(".csv") or os.path.sep in arg:
        path = arg if os.path.isabs(arg) else os.path.join(HERE, arg)
        df = pd.read_csv(path, parse_dates=["time"])
        sym = os.path.basename(path).split("_")[0]
        return sym, df
    sym = arg.upper()
    if date:
        cand = os.path.join(DATA_DIR, f"{sym}_{date}_1min.csv")
        if os.path.exists(cand):
            return sym, pd.read_csv(cand, parse_dates=["time"])
    raise SystemExit(f"No CSV for {sym} {date}. Run fetch_intraday.py {sym} first.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="CSV path, or a SYMBOL (with optional date)")
    ap.add_argument("date", nargs="?", default=None)
    ap.add_argument("--phb", action="store_true", help="Power Hour Breakout card instead of the default (MFR) card")
    args = ap.parse_args()
    sym, df = _load(args.target, args.date)
    (phb_card if args.phb else card)(sym, df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

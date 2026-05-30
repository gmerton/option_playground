#!/usr/bin/env python3
"""
Prototype + backtest the PHB "directional ignition" trigger.

The 45-symbol batch showed volume surge alone is not enough (faders surge too).
This trigger requires a *conjunction* at a power-hour bar:
  - close > VWAP                         (holding the day's value area)
  - 9 EMA > 20 EMA and close > 9 EMA     (short-term uptrend, price leading)
  - close makes a new afternoon high     (breaking out, not rolling over)
  - RSI >= rsi_min and rising             (momentum confirming)
  - bar volume > vol_mult x trailing-20  (participation)

It scans each session's power-hour window minute-by-minute and takes the FIRST
bar meeting all conditions as the entry. We then measure the forward move from
that entry to the session close (and to the best post-entry high), and check
whether the trigger fires on winners but stays silent on faders.

Ground-truth outcome label is taken from where the day actually closed in its
range (independent of the trigger): WIN >= 85% up range, FADE <= 40%, else MID.

Usage:
  .venv/bin/python3 ibkr_bot/power_hour_trigger.py                 # all cached CSVs for the latest date
  .venv/bin/python3 ibkr_bot/power_hour_trigger.py CIEN TXN MSFT   # specific symbols
"""

from __future__ import annotations

import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import DATA_DIR, add_indicators  # noqa: E402

# trigger parameters (tunable)
SCAN_START, SCAN_END = "14:30", "15:45"
REF_START = "12:00"          # "afternoon high" is measured from here
RSI_MIN = 60
RSI_LOOKBACK = 3             # rsi must exceed its value this many bars ago
VOL_MULT = 1.5
MIN_VWAP_DIST = 1.0          # require close >= this % above VWAP (precision filter; 0 = off)
                             # 1.0 cleanly separated winners (≥1.21%) from faders (≤0.93%) incl. NVDA
WIN_THRESH, FADE_THRESH = 85, 40   # close-position-in-range buckets


def find_trigger(sess: pd.DataFrame) -> dict | None:
    """First power-hour bar meeting the directional conjunction; None if never."""
    hhmm = sess["time"].dt.strftime("%H:%M")
    ref_mask = hhmm >= REF_START
    for i in sess.index[(hhmm >= SCAN_START) & (hhmm <= SCAN_END)]:
        if i < RSI_LOOKBACK or i < 20:
            continue
        r = sess.loc[i]
        prior_aft_high = sess.loc[ref_mask & (sess.index < i), "close"].max()
        vol_avg = sess["volume"].iloc[i - 20:i].mean()
        conds = {
            "vwap": r["close"] >= r["vwap"] * (1 + MIN_VWAP_DIST / 100),
            "ema": (r["ema9"] > r["ema20"]) and (r["close"] > r["ema9"]),
            "new_high": pd.notna(prior_aft_high) and r["close"] > prior_aft_high,
            "rsi": r["rsi"] >= RSI_MIN and r["rsi"] > sess.loc[i - RSI_LOOKBACK, "rsi"],
            "vol": vol_avg > 0 and r["volume"] > VOL_MULT * vol_avg,
        }
        if all(conds.values()):
            return {"i": i, "time": hhmm.iloc[i], "px": r["close"]}
    return None


def simulate_exit(sess: pd.DataFrame, i: int, stop_mode: str) -> tuple:
    """Walk forward from entry bar i to model an intraday-flat exit.

    Exit on the stop if hit, else flat at the session close. Returns
    (exit_time, exit_px, reason). Stop modes:
      bar_low   -- structural: exit if a later bar trades to/below the entry bar low
      vwap      -- thesis-invalidation: exit on the first bar that closes back < VWAP
      pct:X     -- fixed: exit if price trades down X% from entry
      ema9      -- trailing: exit on the first bar that closes back below the 9 EMA
      trail:X   -- trailing: exit if price falls X% from the running peak high since entry
    """
    entry = sess["close"].iloc[i]
    entry_low = sess["low"].iloc[i]
    pct = float(stop_mode.split(":")[1]) / 100 if stop_mode.startswith("pct:") else None
    trail = float(stop_mode.split(":")[1]) / 100 if stop_mode.startswith("trail:") else None
    hhmm = sess["time"].dt.strftime("%H:%M")
    peak = sess["high"].iloc[i]
    for j in range(i + 1, len(sess)):
        b = sess.iloc[j]
        peak = max(peak, b["high"])
        if stop_mode == "bar_low" and b["low"] <= entry_low:
            return hhmm.iloc[j], entry_low, "stop"
        if stop_mode == "vwap" and b["close"] < b["vwap"]:
            return hhmm.iloc[j], b["close"], "vwap"
        if stop_mode == "ema9" and b["close"] < b["ema9"]:
            return hhmm.iloc[j], b["close"], "ema9"
        if pct is not None and b["low"] <= entry * (1 - pct):
            return hhmm.iloc[j], entry * (1 - pct), "stop"
        if trail is not None and b["low"] <= peak * (1 - trail):
            return hhmm.iloc[j], peak * (1 - trail), "trail"
    return hhmm.iloc[-1], sess["close"].iloc[-1], "close"


def evaluate(sym: str, df: pd.DataFrame, stop_mode: str = "bar_low") -> dict:
    day = df["time"].dt.date.iloc[-1]
    sess = add_indicators(df[df["time"].dt.date == day].reset_index(drop=True))
    dlo, dhi = sess["low"].min(), sess["high"].max()
    last = sess["close"].iloc[-1]
    close_pos = (last - dlo) / (dhi - dlo) * 100 if dhi > dlo else 0
    outcome = "WIN" if close_pos >= WIN_THRESH else ("FADE" if close_pos <= FADE_THRESH else "mid")

    res = {"symbol": sym, "close_pos": round(close_pos), "outcome": outcome,
           "fired": False, "time": None, "trade": None, "reason": None}
    trig = find_trigger(sess)
    if trig:
        i, px = trig["i"], trig["px"]
        xt, xpx, reason = simulate_exit(sess, i, stop_mode)
        res.update({
            "fired": True, "time": trig["time"], "entry": round(px, 2),
            "exit_t": xt, "exit": round(xpx, 2), "reason": reason,
            "trade": round((xpx / px - 1) * 100, 2),
        })
    return res


def _load_targets(argv: list[str]) -> list[tuple[str, pd.DataFrame]]:
    if argv:
        syms = [s.upper().rstrip(",") for s in argv]
        out = []
        for s in syms:
            hits = sorted(glob.glob(os.path.join(DATA_DIR, f"{s}_*_1min.csv")))
            if hits:
                out.append((s, pd.read_csv(hits[-1], parse_dates=["time"])))
            else:
                print(f"  (no cached CSV for {s})")
        return out
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*_1min.csv")))
    latest_date = max(os.path.basename(f).split("_")[1] for f in files)
    out = []
    for f in files:
        if f"_{latest_date}_" in os.path.basename(f):
            sym = os.path.basename(f).split("_")[0]
            out.append((sym, pd.read_csv(f, parse_dates=["time"])))
    return out


def main() -> int:
    global SCAN_START, SCAN_END, MIN_VWAP_DIST
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*")
    ap.add_argument("--scan-start", default=SCAN_START)
    ap.add_argument("--scan-end", default="15:30", help="intraday-flat: stop taking entries here")
    ap.add_argument("--stop", default="bar_low", help="bar_low | vwap | pct:X")
    ap.add_argument("--min-vwap-dist", type=float, default=MIN_VWAP_DIST,
                    help="require close >= this %% above VWAP at the trigger (precision filter)")
    a = ap.parse_args()
    SCAN_START, SCAN_END = a.scan_start, a.scan_end
    MIN_VWAP_DIST = a.min_vwap_dist

    targets = _load_targets(a.symbols)
    if not targets:
        print("no cached CSVs found -- run scan_phb.py / fetch_intraday.py first")
        return 1

    rows = [evaluate(sym, df, a.stop) for sym, df in targets]
    rank = {"WIN": 0, "mid": 1, "FADE": 2}
    rows.sort(key=lambda r: (rank[r["outcome"]], -r["close_pos"]))

    hdr = f"{'sym':<6}{'outcome':>8}{'clo%rng':>8}{'entry':>7}{'exit':>7}{'reason':>8}{'trade':>9}"
    print(f"\nINTRADAY-FLAT  trigger: >VWAP & 9>20EMA & close>9EMA & new-aft-high & RSI≥{RSI_MIN}↑ & vol>{VOL_MULT}×")
    print(f"scan {SCAN_START}-{SCAN_END} (flat by close)   stop={a.stop}")
    print(hdr); print("-" * len(hdr))
    for r in rows:
        if not r["fired"]:
            print(f"{r['symbol']:<6}{r['outcome']:>8}{r['close_pos']:>8}{'·':>7}")
            continue
        print(f"{r['symbol']:<6}{r['outcome']:>8}{r['close_pos']:>8}{r['entry']:>7.2f}{r['exit']:>7.2f}"
              f"{r['reason']:>8}{r['trade']:>+8.2f}%")

    fires = [r for r in rows if r["fired"]]
    if fires:
        pnl = [r["trade"] for r in fires]
        wins = [p for p in pnl if p > 0]
        gross_w = sum(wins); gross_l = -sum(p for p in pnl if p <= 0)
        pf = gross_w / gross_l if gross_l else float("inf")
        print(f"\nALL FIRES: {len(fires)} trades, win-rate {len(wins)/len(fires)*100:.0f}%, "
              f"avg {sum(pnl)/len(pnl):+.2f}%, total {sum(pnl):+.2f}%, profit-factor {pf:.2f}")
    for label in ("WIN", "FADE"):
        grp = [r for r in fires if r["outcome"] == label]
        n = sum(1 for r in rows if r["outcome"] == label)
        if grp:
            avg = sum(r["trade"] for r in grp) / len(grp)
            print(f"  {label}-day fires: {len(grp)}/{n}  avg {avg:+.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

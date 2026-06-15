#!/usr/bin/env python3
"""Dump every MFR fire over the cached multi-day files WITH the features that
might separate winners from losers, so we can tighten the gate empirically.

Per fire we record the flush/reclaim characteristics measurable AT entry (no
look-ahead) plus the realized trade. Faithful to the live detect_mfr finder.
"""
from __future__ import annotations

import glob, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators          # noqa: E402
import signal_monitor as sm                       # noqa: E402


def mfr_fire(sess: pd.DataFrame):
    hhmm = sess["time"].dt.strftime("%H:%M")
    o = sess["open"].iloc[0]
    low = sess["low"].values; close = sess["close"].values
    vwap = sess["vwap"].values; rsi = sess["rsi"].values
    vol = sess["volume"].values; volma = sess["vol_ma20"].values
    cur_min, cmi = float("inf"), 0
    for i in range(len(sess)):
        if low[i] < cur_min:
            cur_min, cmi = low[i], i
        if i < 2 or i <= cmi:
            continue
        if hhmm.iloc[cmi] > sm.MFR_MORNING_END:
            continue
        drop = (low[cmi] / o - 1) * 100
        if not (drop <= sm.MFR_MIN_DROP and rsi[cmi] <= sm.MFR_MAX_RSI):
            continue
        if close[i - 1] <= vwap[i - 1] and close[i] > vwap[i]:
            flush_low = low[cmi]; entry = close[i]
            exit_px, reason = close[-1], "close"
            for j in range(i + 1, len(sess)):
                if close[j] < flush_low:
                    exit_px, reason = close[j], "stop"; break
            return {
                "low_t": hhmm.iloc[cmi], "reclaim_t": hhmm.iloc[i],
                "drop": round(drop, 1),
                "rsi_low": round(float(rsi[cmi])),
                "vwap_dist": round((low[cmi] / vwap[cmi] - 1) * 100, 1),
                "bars_lo_to_entry": i - cmi,
                "off_low_entry": round((entry / flush_low - 1) * 100, 2),
                "vol_climax": round(vol[cmi] / volma[cmi], 2) if volma[cmi] > 0 else None,
                "reason": reason,
                "pnl": round((exit_px / entry - 1) * 100, 2),
            }
    return None


def main() -> int:
    g = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "*_2026-06-01_1min.csv")
    rows = []
    for f in sorted(glob.glob(g)):
        sym = os.path.basename(f).split("_")[0]
        df = pd.read_csv(f, parse_dates=["time"])
        for day, gg in df.groupby(df["time"].dt.date):
            if len(gg) < 30:
                continue
            sess = add_indicators(gg.sort_values("time").reset_index(drop=True))
            r = mfr_fire(sess)
            if r:
                rows.append({"sym": sym, "date": str(day), **r})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(HERE, "data", "_mfr_trades.csv"), index=False)
    pd.set_option("display.width", 200, "display.max_rows", 100)
    print(t.to_string(index=False))

    win = t[t.pnl > 0]; los = t[t.pnl <= 0]
    print(f"\nN={len(t)}  win {len(win)/len(t)*100:.0f}%  avg {t.pnl.mean():+.2f}%  total {t.pnl.sum():+.1f}%")
    feats = ["drop", "rsi_low", "vwap_dist", "bars_lo_to_entry", "off_low_entry", "vol_climax"]
    print("\nfeature        winners   losers")
    for c in feats:
        print(f"  {c:<14}{win[c].mean():>7.2f}{los[c].mean():>9.2f}")
    print(f"\nstop-out rate (close<flush low): {(t.reason=='stop').mean()*100:.0f}%  "
          f"avg pnl on stops {t[t.reason=='stop'].pnl.mean():+.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

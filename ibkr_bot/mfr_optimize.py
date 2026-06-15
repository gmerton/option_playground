#!/usr/bin/env python3
"""Find a tighter MFR gate that lifts EV, with a split-half robustness check.

Re-derives each fire's features (robust vol-spike via expanding mean, so it's
defined even for first-hour flushes), then evaluates economically-motivated
filters on the full sample AND on the first-half vs second-half of the dates.
A filter only counts as real if it helps in BOTH halves -- guards against
overfitting 50 trades.
"""
from __future__ import annotations

import glob, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators        # noqa: E402
import signal_monitor as sm                     # noqa: E402


def fire(sess):
    hhmm = sess["time"].dt.strftime("%H:%M")
    o = sess["open"].iloc[0]
    low = sess["low"].values; close = sess["close"].values
    vwap = sess["vwap"].values; rsi = sess["rsi"].values; vol = sess["volume"].values
    cur_min, cmi = float("inf"), 0
    for i in range(len(sess)):
        if low[i] < cur_min:
            cur_min, cmi = low[i], i
        if i < 2 or i <= cmi or hhmm.iloc[cmi] > sm.MFR_MORNING_END:
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
            vol_spike = vol[cmi] / vol[:cmi + 1].mean() if vol[:cmi + 1].mean() > 0 else 1.0
            return {
                "rsi_low": float(rsi[cmi]), "drop": drop,
                "vwap_dist": (low[cmi] / vwap[cmi] - 1) * 100,
                "off_low_entry": (entry / flush_low - 1) * 100,
                "reclaim_str": (close[i] / vwap[i] - 1) * 100,
                "vol_spike": vol_spike, "reason": reason,
                "pnl": (exit_px / entry - 1) * 100,
            }
    return None


def load(glob_pat):
    rows = []
    for f in sorted(glob.glob(glob_pat)):
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < 30:
                continue
            r = fire(add_indicators(g.sort_values("time").reset_index(drop=True)))
            if r:
                rows.append({"date": str(day), **r})
    return pd.DataFrame(rows)


def ev(t):
    if len(t) == 0:
        return (0, 0.0, 0.0, 0.0)
    w = (t.pnl > 0).mean() * 100
    pf_l = -t.pnl[t.pnl <= 0].sum()
    pf = (t.pnl[t.pnl > 0].sum() / pf_l) if pf_l else float("inf")
    return (len(t), w, t.pnl.mean(), pf)


FILTERS = {
    "baseline (current gate)":      lambda t: t.index == t.index,
    "vol_spike >= 1.3":             lambda t: t.vol_spike >= 1.3,
    "rsi_low >= 8 (no falling knife)": lambda t: t.rsi_low >= 8,
    "vwap_dist <= -3.5 (deep)":     lambda t: t.vwap_dist <= -3.5,
    "drop <= -6":                   lambda t: t["drop"] <= -6,
    "vol_spike>=1.3 & rsi>=8":      lambda t: (t.vol_spike >= 1.3) & (t.rsi_low >= 8),
    "vol_spike>=1.3 & vwap<=-3.5":  lambda t: (t.vol_spike >= 1.3) & (t.vwap_dist <= -3.5),
    "rsi>=8 & vwap<=-3.5":          lambda t: (t.rsi_low >= 8) & (t.vwap_dist <= -3.5),
    "vol>=1.3 & rsi>=8 & vwap<=-3.5": lambda t: (t.vol_spike >= 1.3) & (t.rsi_low >= 8) & (t.vwap_dist <= -3.5),
}


def main():
    t = load(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "*_2026-06-01_1min.csv"))
    dates = sorted(t.date.unique())
    mid = dates[len(dates) // 2]
    A = t[t.date < mid]; B = t[t.date >= mid]   # first half / second half
    print(f"{len(t)} trades over {len(dates)} sessions; split at {mid} "
          f"(A={A.date.nunique()}d/{len(A)}tr, B={B.date.nunique()}d/{len(B)}tr)\n")
    print(f"{'filter':<34}{'N':>4}{'win%':>6}{'avg%':>7}{'PF':>6}   {'A:avg(N)':>11}{'B:avg(N)':>12}")
    print("-" * 92)
    for name, fn in FILTERS.items():
        sub = t[fn(t)]
        n, w, a, pf = ev(sub)
        sa = ev(A[fn(A)]); sb = ev(B[fn(B)])
        robust = " ROBUST" if (sa[2] > 0 and sb[2] > 0 and n >= 12) else ""
        print(f"{name:<34}{n:>4}{w:>6.0f}{a:>+7.2f}{pf:>6.2f}   "
              f"{sa[2]:>+7.2f}({sa[0]:>2}){sb[2]:>+8.2f}({sb[0]:>2}){robust}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Naive intraday 9/20-EMA crossover backtest on a single symbol's 1-min bars.

Strategy (long-only, intraday-flat):
  - BUY  when ema9 crosses ABOVE ema20
  - SELL when ema9 crosses BELOW ema20
  - force-flat at the last bar of the session

Fills are taken at the CLOSE of the bar that confirms the cross (the signal is
only known once that bar closes -- causal, no look-ahead). EMAs reuse the same
definitions as the rest of the bot (characterize.add_indicators).

Usage:
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_backtest.py \
      ibkr_bot/data/AAOI_2026-06-12_1min.csv
"""

from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characterize import add_indicators  # noqa: E402


def backtest(
    df: pd.DataFrame,
    trend_vwap: bool = False,
    min_sep: float = 0.0,
    slope_bars: int = 0,
    entry_before: str | None = None,
    confirm_bars: int = 0,
    idx_by_hhmm: dict | None = None,
    rs_min: float | None = None,
    fast_span: int | None = None,
    slow_span: int | None = None,
    vol_mult: float | None = None,
    rvol_min: float | None = None,
    session_rvol: float | None = None,
    enter_th: float = 0.0,
    exit_th: float = 0.0,
) -> tuple[list[dict], dict]:
    """Long-only 9/20 crossover with optional chop filters.

    On a cross-up, optionally wait `confirm_bars` bars, then enter at that bar's
    close ONLY if the conditions below still hold there (a confirmation delay --
    this is what makes min_sep meaningful, since the EMAs need time to separate):
      confirm_bars -- bars to wait after the cross before entering
      trend_vwap   -- require close > vwap at the entry bar
      min_sep      -- require (ema9-ema20)/close*100 >= min_sep at the entry bar
      slope_bars   -- require ema20 rising over the last `slope_bars` bars
      entry_before -- "HH:MM": no NEW entries at/after this time
    A cross-down during the wait cancels the pending entry. Exits (cross-down or
    EOD flat) are never filtered."""
    df = add_indicators(df.copy()).reset_index(drop=True)
    if fast_span:                                              # override default 9/20 pair
        df["ema9"] = df["close"].ewm(span=fast_span, adjust=False).mean()
    if slow_span:
        df["ema20"] = df["close"].ewm(span=slow_span, adjust=False).mean()
    fast, slow = df["ema9"], df["ema20"]
    diff = fast - slow
    # normalized spread in pct points of price -> band thresholds are scale-free.
    # ANTICIPATION band: enter_th<=0 buys BEFORE the real 0-cross; exit_th>=0 sells
    # BEFORE the real down-cross. enter_th=exit_th=0 reproduces the plain crossover.
    s = diff / df["close"] * 100
    cross_up = (s > enter_th) & (s.shift(1) <= enter_th)         # up-cross of enter_th
    # exit while long: early down-cross of exit_th, OR spread fell back below enter_th
    # (the anticipated move failed) -- whichever comes first.
    exit_now = ((s < exit_th) & (s.shift(1) >= exit_th)) | (s < enter_th)
    cross_dn = exit_now                                          # reused for pending-cancel

    trades: list[dict] = []
    in_pos = False
    entry_px = entry_t = None
    pending = None           # bar index of a cross-up awaiting confirmation
    last_i = len(df) - 1
    cutoff = (pd.to_datetime(entry_before).time() if entry_before else None)
    open0 = df["open"].iloc[0]

    def entry_ok(i, px, t) -> bool:
        if s.iloc[i] <= enter_th:                              # spread fell back below the band
            return False
        if trend_vwap and not (px > df["vwap"].iloc[i]):
            return False
        if min_sep and (diff.iloc[i] / px * 100) < min_sep:
            return False
        if slope_bars and not (slow.iloc[i] > slow.iloc[i - slope_bars]):
            return False
        if cutoff and t.time() >= cutoff:
            return False
        if rs_min is not None:                                  # relative strength vs index
            idx = (idx_by_hhmm or {}).get(t.strftime("%H:%M"))
            if idx is None:
                return False
            rs = (px / open0 - 1 - idx) * 100                   # pct-point outperformance
            if rs < rs_min:
                return False
        if vol_mult is not None:                                # TRIGGER: cross-bar volume surge
            vma = df["vol_ma20"].iloc[i]
            if not (vma > 0) or df["volume"].iloc[i] < vol_mult * vma:
                return False
        if rvol_min is not None:                                # SELECTION: this name active today
            # session-so-far volume vs the name's typical full-day volume
            if session_rvol is None or session_rvol < rvol_min:
                return False
        return True

    for i in range(1, len(df)):
        px = df["close"].iloc[i]
        t = df["time"].iloc[i]
        if not in_pos:
            if cross_up.iloc[i]:
                pending = i
            if pending is not None and s.iloc[i] < enter_th and i > pending:
                pending = None                                 # spread reversed mid-wait
            elif pending is not None and i >= pending + confirm_bars:
                if entry_ok(i, px, t):
                    in_pos, entry_px, entry_t = True, px, t
                pending = None                                 # consumed either way
        elif in_pos and (cross_dn.iloc[i] or i == last_i):
            reason = "cross_dn" if cross_dn.iloc[i] else "eod_flat"
            trades.append({
                "entry_t": entry_t.strftime("%H:%M"),
                "exit_t": t.strftime("%H:%M"),
                "entry": round(entry_px, 2),
                "exit": round(px, 2),
                "ret_pct": round((px / entry_px - 1) * 100, 2),
                "bars_held": i - df.index[df["time"] == entry_t][0],
                "exit_reason": reason,
            })
            in_pos = False

    rets = [t["ret_pct"] for t in trades]
    wins = [r for r in rets if r > 0]
    total = sum(rets)
    gross_w = sum(r for r in rets if r > 0)
    gross_l = -sum(r for r in rets if r < 0)
    summary = {
        "n": len(trades),
        "win_rate": round(100 * len(wins) / len(trades), 1) if trades else 0.0,
        "total_ret_pct": round(total, 2),
        "avg_ret_pct": round(total / len(trades), 2) if trades else 0.0,
        "best": round(max(rets), 2) if rets else 0.0,
        "worst": round(min(rets), 2) if rets else 0.0,
        "profit_factor": round(gross_w / gross_l, 2) if gross_l else float("inf"),
    }
    return trades, summary


PRESETS = [
    ("baseline (no filter)", {}),
    ("trend: close>VWAP", {"trend_vwap": True}),
    ("ema20 slope up (5b)", {"slope_bars": 5}),
    ("confirm 2b + sep0.05%", {"confirm_bars": 2, "min_sep": 0.05}),
    ("entry before 11:30", {"entry_before": "11:30"}),
    ("VWAP + confirm2 + sep0.05", {"trend_vwap": True, "confirm_bars": 2, "min_sep": 0.05}),
    ("VWAP + before 11:30", {"trend_vwap": True, "entry_before": "11:30"}),
    ("VWAP + confirm2 + before11:30", {"trend_vwap": True, "confirm_bars": 2,
                                       "min_sep": 0.05, "entry_before": "11:30"}),
]


def compare(df: pd.DataFrame, sym, day) -> None:
    print(f"\n9/20 EMA crossover -- filter comparison  {sym} {day}\n")
    print(f"  {'config':<26} {'n':>3} {'win%':>5} {'total%':>7} "
          f"{'avg%':>6} {'best%':>6} {'worst%':>6} {'PF':>5}")
    for name, kw in PRESETS:
        _, s = backtest(df, **kw)
        pf = s["profit_factor"]
        pf_s = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"  {name:<26} {s['n']:>3} {s['win_rate']:>5} "
              f"{s['total_ret_pct']:>7} {s['avg_ret_pct']:>6} "
              f"{s['best']:>6} {s['worst']:>6} {pf_s:>5}")
    print("\n  gross of costs; % on underlying. Single in-sample day -- "
          "validate across the cache before trusting.\n")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    sym = os.path.basename(path).split("_")[0]
    day = df["time"].dt.date.iloc[-1]

    if "--compare" in sys.argv:
        compare(df, sym, day)
        return 0

    trades, s = backtest(df)
    print(f"\n9/20 EMA crossover -- {sym} {day}  (long-only, intraday-flat, "
          f"fills at signal-bar close)\n")
    if not trades:
        print("  no crossover trades")
        return 0
    print(f"  {'#':>2}  {'entry':>5} {'exit':>5}   {'in':>5} {'out':>7}  "
          f"{'ret%':>6}  {'bars':>4}  reason")
    for i, t in enumerate(trades, 1):
        print(f"  {i:>2}  {t['entry_t']:>5} {t['exit_t']:>5}   "
              f"{t['entry']:>6.2f} {t['exit']:>7.2f}  {t['ret_pct']:>6.2f}  "
              f"{t['bars_held']:>4}  {t['exit_reason']}")
    print(f"\n  trades {s['n']}  win% {s['win_rate']}  total {s['total_ret_pct']}%  "
          f"avg {s['avg_ret_pct']}%  best {s['best']}%  worst {s['worst']}%  "
          f"PF {s['profit_factor']}")
    print("\n  NOTE: gross of commissions/slippage; % is on the underlying, "
          "not an option.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

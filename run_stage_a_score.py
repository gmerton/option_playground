#!/usr/bin/env python3
"""
Stage A, step 2: score every long alert against a pre-registered exit grid, with controls.

Spec (fixed before the run; see the 2026-09-18 discussion):
  Signals   every UR / ORB9 / LVL fire from the uniform replay (run_stage_a_replay.py, tag "stagea"),
            SHOWN and OUT-OF-PLAY alike -- the gate itself is one of the things being tested.
  Entry     the next 1-min bar's open after the alert, + 10 bps.
  Stop      the level the alert published. risk = entry - stop; R = (exit - entry) / risk.
            A stop fill is stop - 10 bps (gap-through). Targets fill at the level.
            Within one bar, a stop that could also have been a target is scored as the STOP.
  Arms      stop_close   stop, else the 16:00 close
            t1R / t2R    first touch of entry + 1R / 2R, else stop, else close
            vwap_loss    first 1-min close back under the session VWAP, else stop, else close
            time30       exit 30 minutes after entry, else stop
            next_close   day-1 stop applies; otherwise hold to the NEXT session's close
            swing_trail  day-1 stop applies; otherwise stop = alert stop on a daily close, then the
                         first daily close under the 20 EMA, capped at 60 sessions
  Controls  random entry: 5 draws per alert, same symbol/session, a random bar 09:45-15:30, same
            dollar risk and the same arms -> does the TRIGGER carry information, or just the name-day?
  Splits    Feb-May (look) vs Jun-Sep (confirm); t clustered by session date.
  Bar       positive in both halves, beats the random control, |t| >= 3.

Usage: PYTHONPATH=src .venv/bin/python3 run_stage_a_score.py > data/studies/stage_a_intraday_2026-09-18.log
"""
from __future__ import annotations

import json
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

LOGS = Path("data/watchlist/logs")
BARS = Path("data/cache/intraday_1min")
SLIP = 0.0010
RNG = np.random.default_rng(20260918)
ARMS = ["stop_close", "t1R", "t2R", "vwap_loss", "time30", "next_close", "swing_trail"]
import sys as _sys
CONTROL = _sys.argv[_sys.argv.index("--control") + 1] if "--control" in _sys.argv else "month"
assert CONTROL in ("month", "post", "xname"), CONTROL
from collections import defaultdict as _dd
DAY_SYMS: dict[str, list[str]] = _dd(list)
for _q in BARS.glob("*.parquet"):
    _sym, _day = _q.name.rsplit("_", 1)[0], _q.name.rsplit("_", 1)[1][:-8]
    DAY_SYMS[_day].append(_sym)


@lru_cache(maxsize=4096)
def bars(sym: str, day: str) -> pd.DataFrame | None:
    p = BARS / f"{sym}_{day}.parquet"
    if not p.exists():
        return None
    b = pd.read_parquet(p)
    if "vwap" not in b.columns or "volume" not in b.columns:
        return None
    b = b[~b.index.duplicated(keep="first")].sort_index()
    cv = (b.vwap * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)
    b = b.assign(cum_vwap=cv)
    return b


def daily() -> pd.DataFrame:
    p = Path("data/cache/stage_a_daily.parquet")
    if p.exists():
        return pd.read_parquet(p)
    import yfinance as yf
    syms = sorted({q.name.rsplit("_", 1)[0] for q in BARS.glob("*.parquet")})
    d = yf.download(syms, start="2025-08-01", end="2026-09-19", auto_adjust=False, progress=False)
    out = d[["Close", "High", "Low"]].stack(level=1, future_stack=True).reset_index()
    out.columns = ["date", "ticker", "close", "high", "low"]
    out = out.dropna(subset=["close"])
    out.to_parquet(p, index=False)
    return out


D = daily()
D["date"] = pd.to_datetime(D.date)
DCL = D.pivot(index="date", columns="ticker", values="close").sort_index()
DEMA20 = DCL.ewm(span=20, adjust=False).mean()


def intraday_exit(b: pd.DataFrame, i0: int, entry: float, stop: float, arm: str) -> tuple[float, bool]:
    """(R-numerator exit price, stopped) walking bars from i0. Returns the final close if nothing triggers."""
    risk = entry - stop
    tgt = {"t1R": entry + risk, "t2R": entry + 2 * risk}.get(arm)
    end = len(b)
    if arm == "time30":
        end = min(len(b), i0 + 30)
    sub = b.iloc[i0:end]
    for j, (_, r) in enumerate(sub.iterrows()):
        if r.low <= stop:
            return stop * (1 - SLIP), True
        if tgt is not None and r.high >= tgt:
            return tgt, False
        if arm == "vwap_loss" and j > 0 and r.close < r.cum_vwap:
            return r.close, False
    return sub.iloc[-1].close, False


def swing_exit(sym: str, day: pd.Timestamp, entry: float, stop: float, cap: int = 60) -> float | None:
    if sym not in DCL.columns:
        return None
    idx = DCL.index
    pos = idx.searchsorted(day)
    for k in range(pos + 1, min(pos + 1 + cap, len(idx))):
        c, e = DCL[sym].iloc[k], DEMA20[sym].iloc[k]
        if not np.isfinite(c):
            continue
        if c < stop:
            return c
        if np.isfinite(e) and c < e:
            return c
    k = min(pos + cap, len(idx) - 1)
    return DCL[sym].iloc[k]


def next_close(sym: str, day: pd.Timestamp) -> float | None:
    if sym not in DCL.columns:
        return None
    pos = DCL.index.searchsorted(day)
    return DCL[sym].iloc[pos + 1] if pos + 1 < len(DCL) else None


def score_one(sym: str, day: str, stop: float, i0: int, b: pd.DataFrame) -> dict | None:
    entry = float(b.iloc[i0].open) * (1 + SLIP)
    risk = entry - stop
    if not np.isfinite(risk) or risk <= 0 or risk / entry > 0.25:
        return None
    out = {}
    for arm in ("stop_close", "t1R", "t2R", "vwap_loss", "time30"):
        px, _ = intraday_exit(b, i0, entry, stop, arm)
        out[arm] = (px - entry) / risk
    d1_px, d1_stopped = intraday_exit(b, i0, entry, stop, "stop_close")
    ts = pd.Timestamp(day)
    for arm, fn in (("next_close", next_close), ("swing_trail", swing_exit)):
        if d1_stopped:
            out[arm] = (d1_px - entry) / risk
        else:
            px = fn(sym, ts) if arm == "next_close" else swing_exit(sym, ts, entry, stop)
            out[arm] = np.nan if px is None else (float(px) - entry) / risk
    out["risk_pct"] = 100 * risk / entry
    return out


def main() -> None:
    # The engine writes JSONL only for OUT-OF-PLAY alerts; the SHOWN ones live in the text logs, so read both.
    from lib.alerts.study import parse_logs
    shown = parse_logs(sorted(LOGS.glob("universe_alerts_*_replay_stagea.log")))
    shown = shown.rename(columns={"sym": "symbol", "px": "price", "day_state_logged": "day_state"})
    shown["grade"] = np.where(shown.gated, "C", "A/B")
    oop_rows = []
    for p in sorted(LOGS.glob("alerts_oop_*_replay_stagea.jsonl")):
        for line in p.read_text().splitlines():
            if line.strip():
                oop_rows.append(json.loads(line))
    oop = pd.DataFrame(oop_rows)
    oop = oop[oop.side == "long"] if "side" in oop else oop
    keep = ["date", "t", "symbol", "kind", "price", "stop", "grade", "day_state"]
    A = pd.concat([shown.assign(out_of_play=False)[keep + ["out_of_play"]],
                   oop.assign(out_of_play=True)[keep + ["out_of_play"]]], ignore_index=True)
    A = A[A.kind.isin(["UR", "ORB9", "LVL"])].drop_duplicates(subset=["date", "t", "symbol", "kind"])
    print(f"alerts: {len(A):,} ({A.date.nunique()} sessions, {A.symbol.nunique()} symbols) | "
          f"by kind {A.kind.value_counts().to_dict()} | shown {int((~A.out_of_play).sum())} / out of play {int(A.out_of_play.sum())}")

    recs, ctrl, dropped = [], [], 0
    for r in A.itertuples(index=False):
        b = bars(r.symbol, r.date)
        if b is None or not np.isfinite(r.stop):
            dropped += 1
            continue
        t = pd.Timestamp(f"{r.date} {r.t}")
        i0 = int(b.index.searchsorted(t, side="right"))
        if i0 >= len(b) - 2:
            dropped += 1
            continue
        s = score_one(r.symbol, r.date, float(r.stop), i0, b)
        if s is None:
            dropped += 1
            continue
        recs.append({**s, "date": r.date, "sym": r.symbol, "kind": r.kind, "grade": r.grade,
                     "oop": bool(r.out_of_play), "day_state": r.day_state, "hhmm": r.t})
        # random-entry control, same dollar/percent risk:
        #   month  (original) same name-day, random bar 09:45-15:30 -- includes PRE-trigger minutes = look-ahead
        #   post   same name-day, random bar AFTER the trigger (timing)
        #   xname  random OTHER symbol with bars that day, same minute, same risk % (selection)
        lo = int(b.index.searchsorted(pd.Timestamp(f"{r.date} 09:45")))
        hi = int(b.index.searchsorted(pd.Timestamp(f"{r.date} 15:30")))
        e0 = float(b.iloc[i0].open) * (1 + SLIP)
        risk_px = e0 - float(r.stop)
        if CONTROL == "xname":
            others = [s for s in DAY_SYMS.get(r.date, []) if s != r.symbol]
            for s2 in RNG.choice(others, size=min(5, len(others)), replace=False) if others else []:
                b2 = bars(str(s2), r.date)
                if b2 is None:
                    continue
                k = int(b2.index.searchsorted(t, side="right"))
                if k >= len(b2) - 2:
                    continue
                e = float(b2.iloc[k].open) * (1 + SLIP)
                cs = score_one(str(s2), r.date, e * (1 - risk_px / e0), k, b2)
                if cs:
                    ctrl.append({**cs, "date": r.date, "sym": str(s2), "kind": r.kind})
            continue
        if CONTROL == "post":
            lo = i0 + 1
        if hi - lo > 10:
            for k in RNG.choice(np.arange(lo, hi), size=min(5, hi - lo), replace=False):
                e = float(b.iloc[int(k)].open) * (1 + SLIP)
                cs = score_one(r.symbol, r.date, e - risk_px, int(k), b)
                if cs:
                    ctrl.append({**cs, "date": r.date, "sym": r.symbol, "kind": r.kind})
    T, C = pd.DataFrame(recs), pd.DataFrame(ctrl)
    sfx = "" if CONTROL == "month" else f"_{CONTROL}"
    T.to_parquet(f"data/cache/stage_a_trades{sfx}.parquet", index=False)
    C.to_parquet(f"data/cache/stage_a_control{sfx}.parquet", index=False)
    print(f"control = {CONTROL}")
    print(f"scored {len(T):,} alerts ({dropped} dropped: no bars / bad stop / late fire), "
          f"{len(C):,} control entries\n")

    def stats(x: pd.DataFrame, arm: str) -> dict:
        s = x[arm].dropna()
        if len(s) < 30:
            return dict(n=len(s))
        d = s.groupby(x.loc[s.index, "date"]).mean()
        return dict(n=len(s), meanR=s.mean(), medR=s.median(), win=100 * (s > 0).mean(),
                    t=d.mean() / d.std() * np.sqrt(len(d)))

    print("=== ALL LONG ALERTS, by exit arm (R per trade) ===")
    tab = pd.DataFrame({a: stats(T, a) for a in ARMS}).T
    tab["ctrl_meanR"] = [C[a].dropna().mean() for a in ARMS]
    tab["edge_vs_ctrl"] = tab.meanR - tab.ctrl_meanR
    print(tab.round(3).to_string())

    for kind in sorted(T.kind.unique()):
        x = T[T.kind == kind]
        c = C[C.kind == kind]
        t2 = pd.DataFrame({a: stats(x, a) for a in ARMS}).T
        t2["ctrl"] = [c[a].dropna().mean() for a in ARMS]
        t2["edge"] = t2.meanR - t2.ctrl
        print(f"\n=== {kind} (n={len(x):,}) ===")
        print(t2.round(3).to_string())

    print("\n=== split sample (meanR) ===")
    h1, h2 = T[T.date < "2026-06-01"], T[T.date >= "2026-06-01"]
    print(pd.DataFrame({"Feb-May": {a: h1[a].mean() for a in ARMS},
                        "Jun-Sep": {a: h2[a].mean() for a in ARMS},
                        "n1": {a: h1[a].notna().sum() for a in ARMS},
                        "n2": {a: h2[a].notna().sum() for a in ARMS}}).round(3).to_string())

    print("\n=== does the in-play gate earn its keep? SHOWN vs SUPPRESSED (meanR) ===")
    print(T.groupby("oop")[ARMS].mean().join(T.groupby("oop").size().rename("n")).round(3).to_string())
    print("\n  shown alerts only, by kind:")
    print(T[~T.oop].groupby("kind")[ARMS].mean().join(T[~T.oop].groupby("kind").size().rename("n")).round(3).to_string())
    print("\n  shown vs its own random control (meanR):")
    sh = T[~T.oop]
    cs = C[C.set_index(["date","sym"]).index.isin(sh.set_index(["date","sym"]).index)]
    print(pd.DataFrame({"shown": {a: sh[a].mean() for a in ARMS}, "control(same name-days)": {a: cs[a].mean() for a in ARMS}}).round(3).to_string())
    print("\n=== by day state ===")
    print(T.groupby("day_state")[ARMS].mean().join(T.groupby("day_state").size().rename("n")).round(3).to_string())
    print("\n=== by time of day (entry hour, ET) ===")
    T["hour"] = T.hhmm.str[:2]
    print(T.groupby("hour")[ARMS].mean().join(T.groupby("hour").size().rename("n")).round(3).to_string())
    print(f"\nsignals per session: {len(T) / T.date.nunique():.1f} | median risk {T.risk_pct.median():.2f}% of price")


if __name__ == "__main__":
    main()

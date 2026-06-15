#!/usr/bin/env python3
"""Volatility-Contraction Breakout (VCB) detector — the "AAOI base-and-rip".

A distinct intraday archetype from MFR (flush reversal) and PHB (power-hour):
after the opening range, the name coils on *contracting* volume while holding
above VWAP, then breaks the opening-range high on a *volume expansion* and
trends. Archetype: AAOI 2026-06-04 (coiled 10:00-12:10, broke 181.30 @ ~12:24
on 3-6x volume, ran +20%).

DESIGN — timeframe-agnostic, built to answer "is 1-min granularity optimal?"
without the indicator-warmup confound found in add_indicators (whose periods
are in *bars*, so they mean different things per timeframe):

  * STRUCTURE on N-min bars (the real granularity knob): opening-range high,
    the base, volume contraction/expansion, the breakout level. Coarser bars
    smooth out 1-min head-fakes.
  * MOMENTUM CONTEXT held constant: RSI / EMA / VWAP are read from the 1-min
    series AT each N-min decision bar's close, so their meaning is identical at
    every timeframe (VWAP is cumulative, so identical regardless). Volume
    baseline is a trailing *time* window, not "20 bars".

So the only thing varying across 1/3/5/15-min is how coarsely we define
structure and how often we act. gate -> trigger -> invalidation framing.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb.py                 # sweep all tfs over cache
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb.py --explain AAOI  # why it fires/doesn't, per tf
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb.py --minutes 5 --stop vwap
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import DATA_DIR, add_indicators  # noqa: E402

# ---- gate/trigger params (tunable; defaults grounded in the AAOI card) ----
OR_END = "10:00"        # opening range = session start .. here; its high is the breakout level
SCAN_START = "10:00"    # earliest a breakout entry is taken (after the OR)
SCAN_END = "15:00"      # intraday-flat: stop taking entries here (need runway)
CONTRACT = 0.70         # GATE: base avg vol/min <= this x opening-range vol/min (quiet coil)
VOL_BASELINE_MIN = 30   # "normal" volume = trailing this many minutes (time-anchored, exclusive)
VOL_MULT = 2.0          # TRIGGER: breakout bar vol/min >= this x the trailing baseline (expansion)
MIN_VWAP_DIST = 0.0     # TRIGGER: close >= this % above VWAP (>=0 means simply above VWAP)
RSI_MIN = 60            # TRIGGER: 1-min RSI at the decision bar
RS_MIN = None           # TRIGGER (optional): name must outperform the index by >= this many
                        # percentage points (ret-from-open) at the breakout bar. None = off.
BIG_MOVE = 6.0          # opportunity label: day ran >= this % above the OR-high
CLOSE_STRONG = 60       # opportunity label: closed in top (100-this)% ... i.e. close_pos >= this


def load_sessions(glob_pat: str) -> dict:
    """{(sym,date): 1-min session df} from the cache; later file wins on dupes."""
    by = {}
    for f in sorted(glob.glob(glob_pat)):
        sym = os.path.basename(f).split("_")[0]
        df = pd.read_csv(f)
        df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert("US/Eastern")
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < 60:
                continue
            by[(sym, str(day))] = g.sort_values("time").reset_index(drop=True)
    return by


def load_index(symbol: str = "SPY", glob_pat: str | None = None) -> dict:
    """{date: Series(timestamp -> index ret-from-open)} for relative-strength gating."""
    pat = glob_pat or os.path.join(DATA_DIR, f"{symbol}_*_1min.csv")
    files = sorted(glob.glob(pat))
    if not files:
        return {}
    df = pd.read_csv(files[-1])  # the index pull is one multi-day file
    df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert("US/Eastern")
    out = {}
    for day, g in df.groupby(df["time"].dt.date):
        g = g.sort_values("time")
        o = g["open"].iloc[0]
        out[str(day)] = pd.Series((g["close"] / o - 1).values, index=g["time"])
    return out


def adr_table(sessions: dict) -> dict:
    """{sym: {date: avg-daily-range%}} — leave-one-out so a day's own range never
    sets its own stop (mild look-ahead guard). ADR% = mean of (high-low)/open*100
    over the symbol's OTHER cached sessions."""
    rng = {}
    for (sym, date), df in sessions.items():
        o = df["open"].iloc[0]
        r = (df["high"].max() - df["low"].min()) / o * 100 if o else 0.0
        rng.setdefault(sym, {})[date] = r
    out = {}
    for sym, byday in rng.items():
        for date in byday:
            others = [v for d, v in byday.items() if d != date]
            out.setdefault(sym, {})[date] = (sum(others) / len(others)) if others else byday[date]
    return out


def decision_frame(sess1m: pd.DataFrame, minutes: int, idx_ret: pd.Series | None = None) -> pd.DataFrame:
    """N-min STRUCTURE bars with 1-min MOMENTUM context attached at each close.

    OHLCV is aggregated over the bucket; rsi/ema9/ema20/vwap are the 1-min
    values as-of the bucket's last 1-min bar (constant meaning across timeframes).
    If idx_ret is given, attach relative strength = (name ret-from-open) - (index
    ret-from-open) in percentage points at each decision bar.
    """
    s = add_indicators(sess1m)  # 1-min indicators: fully warmed, identical semantics per tf
    s["bucket"] = s["time"].dt.floor(f"{minutes}min")
    g = s.groupby("bucket", sort=True)
    d = g.agg(
        bstart=("bucket", "first"),
        time=("time", "last"),
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"), volume=("volume", "sum"),
        rsi=("rsi", "last"), ema9=("ema9", "last"),
        ema20=("ema20", "last"), vwap=("vwap", "last"),
    ).reset_index(drop=True)
    d["hhmm"] = d["bstart"].dt.strftime("%H:%M")
    d["minutes"] = minutes
    # trailing, EXCLUSIVE volume baseline over ~VOL_BASELINE_MIN of wall-clock
    k = max(1, round(VOL_BASELINE_MIN / minutes))
    d["vol_base"] = d["volume"].shift(1).rolling(k, min_periods=1).mean()
    if idx_ret is not None:
        name_open = d["open"].iloc[0]
        name_ret = d["close"] / name_open - 1
        ir = d["time"].map(idx_ret)            # index ret-from-open at each bar's close minute
        d["rs"] = (name_ret - ir) * 100        # percentage points; NaN if no index minute matched
    return d


def find_vcb(d: pd.DataFrame) -> dict | None:
    """First N-min bar that breaks the OR-high out of a quiet coil, on volume."""
    or_bars = d[d["hhmm"] < OR_END]
    if or_bars.empty:
        return None
    or_high = or_bars["high"].max()
    or_minutes = max(1, len(or_bars) * int(d["minutes"].iloc[0]))
    or_vol_per_min = or_bars["volume"].sum() / or_minutes

    scan = d[(d["hhmm"] >= SCAN_START) & (d["hhmm"] <= SCAN_END)]
    for i in scan.index:
        r = d.loc[i]
        # GATE: the post-open base (OR_END .. now) has been quiet vs the open
        base = d[(d["hhmm"] >= OR_END) & (d.index < i)]
        if len(base):
            base_min = len(base) * int(r["minutes"])
            base_vol_per_min = base["volume"].sum() / base_min
            if base_vol_per_min > CONTRACT * or_vol_per_min:
                continue
        # TRIGGER conjunction
        vexp = r["volume"] / r["vol_base"] if r["vol_base"] and r["vol_base"] > 0 else 0
        conds = {
            "breakout": r["close"] > or_high,
            "vol_expansion": vexp >= VOL_MULT,
            "above_vwap": r["close"] >= r["vwap"] * (1 + MIN_VWAP_DIST / 100),
            "ema_up": r["ema9"] > r["ema20"],
            "rsi": r["rsi"] >= RSI_MIN,
        }
        if RS_MIN is not None:
            rs = r.get("rs", np.nan)
            conds["rel_strength"] = pd.notna(rs) and rs >= RS_MIN
        if all(conds.values()):
            return {"i": i, "time": r["hhmm"], "px": float(r["close"]),
                    "or_high": float(or_high), "vexp": float(vexp), "rsi": float(r["rsi"]),
                    "rs": float(r.get("rs")) if pd.notna(r.get("rs", np.nan)) else None}
    return None


def simulate_exit(d: pd.DataFrame, i: int, level: float, stop_mode: str,
                  adr_pct: float | None = None) -> tuple:
    """Intraday-flat exit walking the N-min decision frame from bar i.

    Stop modes: none | vwap | ema9 | level | trail:X | adr:K | vwap+trail:X |
    vwap+adr:K. trail:X = X% off the running peak; adr:K = K x the symbol's
    average daily range (adr_pct, normalizing the stop to the stock's own
    volatility); the vwap+ combo cuts losers at VWAP until in profit, then
    trails.
    """
    entry = d["close"].iloc[i]
    peak = d["high"].iloc[i]
    combo = stop_mode.startswith("vwap+")
    base = stop_mode.split("+", 1)[1] if combo else stop_mode
    tdist = None                                   # trailing distance as a fraction of price
    if base.startswith("trail:"):
        tdist = float(base.split(":")[1]) / 100
    elif base.startswith("adr:") and adr_pct:
        tdist = float(base.split(":")[1]) * adr_pct / 100
    for j in range(i + 1, len(d)):
        b = d.iloc[j]
        if stop_mode == "none":
            pass
        elif stop_mode == "vwap" and b["close"] < b["vwap"]:
            return b["hhmm"], float(b["close"]), "vwap"
        elif stop_mode == "ema9" and b["close"] < b["ema9"]:
            return b["hhmm"], float(b["close"]), "ema9"
        elif stop_mode == "level" and b["close"] < level:
            return b["hhmm"], float(b["close"]), "level"
        elif tdist is not None:
            if combo:
                if peak > entry and b["low"] <= peak * (1 - tdist):   # in profit -> trail
                    return b["hhmm"], float(peak * (1 - tdist)), "trail"
                if b["close"] < b["vwap"]:                            # not yet -> VWAP cut
                    return b["hhmm"], float(b["close"]), "vwap"
            elif b["low"] <= peak * (1 - tdist):
                return b["hhmm"], float(peak * (1 - tdist)), "trail"
        peak = max(peak, b["high"])
    return d["hhmm"].iloc[-1], float(d["close"].iloc[-1]), "close"


def evaluate(sym: str, date: str, sess1m: pd.DataFrame, minutes: int, stop: str,
             idx_ret: pd.Series | None = None, adr_pct: float | None = None) -> dict:
    d = decision_frame(sess1m, minutes, idx_ret)
    or_bars = d[d["hhmm"] < OR_END]
    or_high = or_bars["high"].max() if len(or_bars) else float("nan")
    dlo, dhi, last = d["low"].min(), d["high"].max(), d["close"].iloc[-1]
    close_pos = (last - dlo) / (dhi - dlo) * 100 if dhi > dlo else 0
    ran = (dhi / or_high - 1) * 100 if or_high == or_high else 0  # day high vs OR-high
    opportunity = ran >= BIG_MOVE and close_pos >= CLOSE_STRONG

    res = {"sym": sym, "date": date, "minutes": minutes, "fired": False,
           "ran_pct": round(ran, 1), "close_pos": round(close_pos),
           "opportunity": opportunity, "trade": None, "captured": None}
    trig = find_vcb(d)
    if trig:
        i = trig["i"]
        xt, xpx, reason = simulate_exit(d, i, trig["or_high"], stop, adr_pct)
        entry = trig["px"]
        post_high = d["high"].iloc[i:].max()
        max_fav = post_high - entry
        res.update({
            "fired": True, "time": trig["time"], "entry": round(entry, 2),
            "exit_t": xt, "exit": round(xpx, 2), "reason": reason,
            "vexp": round(trig["vexp"], 1), "rsi": round(trig["rsi"]),
            "trade": round((xpx / entry - 1) * 100, 2),
            "captured": round((xpx - entry) / max_fav * 100) if max_fav > 0 else None,
            "rs": round(trig["rs"], 1) if trig.get("rs") is not None else None,
        })
    return res


def _stat_line(rows: list[dict]) -> str:
    fires = [r for r in rows if r["fired"]]
    if not fires:
        return "no fires"
    pnl = [r["trade"] for r in fires]
    wins = [p for p in pnl if p > 0]
    gw, gl = sum(wins), -sum(p for p in pnl if p <= 0)
    pf = gw / gl if gl else float("inf")
    opps = [r for r in rows if r["opportunity"]]
    hit = [r for r in opps if r["fired"] and r["trade"] > 0]
    fp = [r for r in fires if not r["opportunity"]]
    caps = [r["captured"] for r in fires if r["captured"] is not None]
    med_cap = sorted(caps)[len(caps) // 2] if caps else 0
    recall = f"{len(hit)}/{len(opps)}" if opps else "0/0"
    return (f"{len(fires):>3} fires  win {len(wins)/len(fires)*100:>3.0f}%  "
            f"avg {sum(pnl)/len(pnl):+5.2f}%  total {sum(pnl):+7.1f}%  PF {pf:>4.2f}  "
            f"medCap {med_cap:>3}%  recall {recall:>6}  falseFires {len(fp):>2}")


def main() -> int:
    global RS_MIN
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(DATA_DIR, "*_1min.csv"))
    ap.add_argument("--minutes", default="1,3,5,15", help="comma list to sweep")
    ap.add_argument("--stop", default="vwap",
                    help="none | vwap | ema9 | level | trail:X | adr:K | vwap+trail:X | vwap+adr:K")
    ap.add_argument("--explain", default=None, help="SYMBOL: trace fire/no-fire per tf")
    ap.add_argument("--index", default="SPY", help="relative-strength index symbol (cached)")
    ap.add_argument("--rs-min", type=float, default=None,
                    help="require name to outperform index by >= this many pts at breakout")
    a = ap.parse_args()
    tfs = [int(x) for x in a.minutes.split(",")]
    RS_MIN = a.rs_min

    sessions = load_sessions(a.glob)
    if not sessions:
        print("no cached sessions found"); return 1
    idx = load_index(a.index)
    adr = adr_table(sessions)  # per-symbol avg-daily-range% for adr:K stops
    if a.rs_min is not None and not idx:
        print(f"! --rs-min set but no cached {a.index} data; run fetch_intraday.py {a.index} --days N")
        return 1
    if "adr" in a.stop and len(sessions) < 60:
        print("! adr:K stop needs several cached days per symbol to estimate ADR")

    if a.explain:
        sym = a.explain.upper()
        keys = sorted([k for k in sessions if k[0] == sym], key=lambda k: k[1])
        if not keys:
            print(f"no cached sessions for {sym}"); return 1
        for key in keys[-1:]:  # most recent session
            print(f"\n=== {sym} {key[1]} — VCB trace (stop={a.stop}, index={a.index}) ===")
            for m in tfs:
                r = evaluate(sym, key[1], sessions[key], m, a.stop, idx.get(key[1]),
                             adr.get(sym, {}).get(key[1]))
                if r["fired"]:
                    rs = f"  RS {r['rs']:+.1f}pts" if r.get("rs") is not None else ""
                    print(f"  {m:>2}m  FIRE @ {r['time']}  entry {r['entry']}  "
                          f"vexp {r['vexp']}x  rsi {r['rsi']}{rs}  -> exit {r['exit']}@{r['exit_t']} "
                          f"({r['reason']})  trade {r['trade']:+.2f}%  captured {r['captured']}% "
                          f"| day ran {r['ran_pct']:+.1f}% closePos {r['close_pos']}%")
                else:
                    print(f"  {m:>2}m  no fire"
                          f"  | day ran {r['ran_pct']:+.1f}% closePos {r['close_pos']}% "
                          f"opp={r['opportunity']}")
        return 0

    print(f"\nVCB sweep over {len(sessions)} sessions  (stop={a.stop}, vol≥{VOL_MULT}x base, "
          f"contract≤{CONTRACT}, RSI≥{RSI_MIN})")
    print("NOTE: cache is selection-biased toward big movers -> treat as an UPPER bound.\n")
    if a.rs_min is not None:
        print(f"  (relative-strength gate: >= {a.rs_min:+.1f} pts vs {a.index})")
    print(f"{'tf':>4}  {'stats':<} ")
    print("-" * 110)
    for m in tfs:
        rows = [evaluate(s, dt, df, m, a.stop, idx.get(dt), adr.get(s, {}).get(dt))
                for (s, dt), df in sessions.items()]
        print(f"{str(m)+'m':>4}  {_stat_line(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

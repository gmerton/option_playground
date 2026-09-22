#!/usr/bin/env python3
"""Level-trigger test (2026-09-21). PRE-REGISTERED: data/studies/level_trigger_test_2026-09-21.md -- read that first;
this script implements it and must not be tuned against its own output.

12 arms = 6 levels (PDH, PDL, EMA21, SMA50, AVWAP from the 20-session swing low, 15-min ORH) x {BREAK, HOLD},
plus the PIVOT (15-session high) BREAK comparator. Long only, 09:45-15:30, one signal per name-day per arm,
stop = level - 0.5 ADR. Scored with lib.studies.pattern_test's own intraday arms + random-minute control, in ONE
pass over the minute files (identical scoring to run_intraday, just 13 patterns per file read).

Usage: PYTHONPATH=src .venv/bin/python3 run_level_trigger_test.py | tee data/studies/level_trigger_test_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
from lib.studies import pattern_test as pt

SPLIT = "2026-06-01"
STOP_ADR, ZONE_ADR, BREAK_BAND = 0.5, 0.1, 0.0005
W0, W1 = "09:45", "15:30"
LEVELS = ["PDH", "PDL", "EMA21", "SMA50", "AVWAP", "ORH"]
ARMS = [f"{l} {b}" for l in LEVELS for b in ("BREAK", "HOLD")] + ["PIVOT BREAK"]
TAG = "levels 2026-09-21"


# ---------------------------------------------------------------- daily levels (data through D-1 only)
def daily_levels(names: set[str]) -> dict:
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[raw.ticker.isin(names)].sort_values(["ticker", "date"])
    out = {}
    for sym, g in raw.groupby("ticker"):
        g = g.set_index("date")
        C, H, L, V = g.close, g.high, g.low, g.volume
        ema21 = C.ewm(span=21, adjust=False).mean()
        sma50 = C.rolling(50, min_periods=50).mean()
        piv15 = H.rolling(15).max()
        pv = ((H + L + C) / 3 * V).values
        vv = V.values
        lows = L.values
        idx = g.index
        for i in range(21, len(g) - 1):                 # levels for session i+1 from data through session i
            d = idx[i + 1]
            if d < pd.Timestamp("2026-01-15"):
                continue
            a = i - 19 + int(np.argmin(lows[i - 19:i + 1]))   # anchor = lowest low of the prior 20 sessions
            out[(sym, d.strftime("%Y-%m-%d"))] = dict(
                PDH=float(H.iloc[i]), PDL=float(L.iloc[i]), EMA21=float(ema21.iloc[i]),
                SMA50=float(sma50.iloc[i]) if np.isfinite(sma50.iloc[i]) else np.nan,
                PIVOT=float(piv15.iloc[i]), av_pv=float(pv[a:i + 1].sum()), av_v=float(vv[a:i + 1].sum()))
    return out


# ---------------------------------------------------------------- signal logic (per name-day)
def find_signals(b: pd.DataFrame, lv: dict, a_pct: float) -> dict[str, dict]:
    hm = b.index.strftime("%H:%M").values
    C, H, Lo = b.close.values, b.high.values, b.low.values
    tp = ((b.high + b.low + b.close) / 3 * b.volume).cumsum().values
    vc = b.volume.cumsum().values
    n = len(b)
    win = (hm >= W0) & (hm <= W1)
    orng = (hm >= "09:30") & (hm < "09:45")
    level_series = {}
    for k in ("PDH", "PDL", "EMA21", "SMA50", "PIVOT"):
        if np.isfinite(lv.get(k, np.nan)):
            level_series[k] = np.full(n, lv[k])
    if lv["av_v"] > 0:
        level_series["AVWAP"] = (lv["av_pv"] + tp) / (lv["av_v"] + vc)
    if orng.any():
        orh = H[orng].max()
        s = np.full(n, np.nan); s[~(hm < "09:45")] = orh
        level_series["ORH"] = s
    out = {}
    for fam, Lv in level_series.items():
        z = Lv * a_pct / 100.0                           # 1 ADR in dollars at the level
        # BREAK: first close > L*(1+band) whose prior close <= L, inside the window
        for k in range(1, n):
            if win[k] and np.isfinite(Lv[k]) and np.isfinite(Lv[k - 1]) and C[k] > Lv[k] * (1 + BREAK_BAND) and C[k - 1] <= Lv[k - 1]:
                out[f"{fam} BREAK"] = dict(k=k, stop=Lv[k] - STOP_ADR * z[k], level=Lv[k])
                break
        if fam == "PIVOT":
            continue
        # HOLD: above (close >= L + 0.1 ADR) -> touch (low <= L + 0.1 ADR) -> trigger (close >= L + 0.1 ADR),
        # failed if a close < L - 0.1 ADR during the touch
        state = 0
        for k in range(n):
            if not np.isfinite(Lv[k]):
                continue
            up, dn = Lv[k] + ZONE_ADR * z[k], Lv[k] - ZONE_ADR * z[k]
            if state == 0:
                if C[k] >= up:
                    state = 1
            elif state == 1:
                if Lo[k] <= up:
                    state = 2
                    if C[k] < dn:
                        break
            elif state == 2:
                if C[k] < dn:
                    break
                if C[k] >= up and win[k]:
                    out[f"{fam} HOLD"] = dict(k=k, stop=Lv[k] - STOP_ADR * z[k], level=Lv[k])
                    break
    return out


def main():
    daily = pd.read_parquet(pt.REPO / "data/cache/stage_a_daily.parquet")
    daily["date"] = pd.to_datetime(daily.date)
    dcl = daily.pivot(index="date", columns="ticker", values="close").sort_index()
    adr = ((daily.pivot(index="date", columns="ticker", values="high")
            / daily.pivot(index="date", columns="ticker", values="low") - 1) * 100).rolling(20).mean()
    ema21_d = dcl.ewm(span=21, adjust=False).mean()
    ctl = {l.split()[0] for l in open(pt.REPO / "data/watchlist/universe_study_extra.txt") if l.strip() and not l.startswith("#")}
    files = sorted(pt.BARS.glob("*.parquet"))
    import os
    if os.environ.get("LIMIT"):                     # smoke test only; the real run uses every file
        files = files[::max(1, len(files) // int(os.environ["LIMIT"]))]
    LV =daily_levels({p.name.rsplit("_", 1)[0] for p in files})
    print(f"{len(files):,} minute files; daily levels for {len(LV):,} name-days", flush=True)
    recs = {a: [] for a in ARMS}; ctrl = {a: [] for a in ARMS}
    miss = 0
    for fi, p in enumerate(files):
        sym, day = p.name.rsplit("_", 1)[0], p.name.rsplit("_", 1)[1][:-8]
        ts = pd.Timestamp(day)
        if sym not in adr.columns or ts not in adr.index or (sym, day) not in LV:
            miss += 1
            continue
        a_pct = adr[sym].iloc[max(adr.index.searchsorted(ts) - 1, 0)]
        b = pd.read_parquet(p)
        if not isinstance(b.index, pd.DatetimeIndex) or len(b) < 60 or not np.isfinite(a_pct):
            continue
        b = b[~b.index.duplicated(keep="first")].sort_index()
        hm = b.index.strftime("%H:%M")
        b = b[(hm >= "09:30") & (hm < "16:00")]
        if len(b) < 60:
            continue
        cv = (b.vwap * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)
        e21 = ema21_d[sym].iloc[max(ema21_d.index.searchsorted(ts) - 1, 0)] if sym in ema21_d.columns else np.nan
        sig = find_signals(b, LV[(sym, day)], a_pct)
        lo = int(b.index.searchsorted(pd.Timestamp(f"{day} {W0}")))
        hi = int(b.index.searchsorted(pd.Timestamp(f"{day} {W1}")))
        for arm_name, s in sig.items():
            i0 = s["k"] + 1                              # entry = next bar's open (as run_intraday)
            if i0 >= len(b) - 2:
                continue
            o = pt._intra_arms(b, cv, i0, float(s["stop"]), "long", sym, day, dcl)
            if not o:
                continue
            px = float(b.close.iloc[s["k"]]); z = px * a_pct / 100
            recs[arm_name].append({**o, "sym": sym, "date": day, "side": "long", "set": "control set" if sym in ctl else "curated",
                                   "t": b.index[s["k"]].strftime("%H:%M"),
                                   "ext21_adr": (px - e21) / z if np.isfinite(e21) else np.nan,
                                   "risk_adr": (px - s["stop"]) / z,
                                   "vs_pivot_adr": (px - LV[(sym, day)]["PIVOT"]) / z})
            if hi - lo <= 10:
                continue
            stop_pct = float(s["stop"]) / (float(b.iloc[i0].open) * (1 + pt.SLIP)) - 1
            for k in pt.RNG.choice(np.arange(lo, hi), size=min(3, hi - lo), replace=False):
                e = float(b.iloc[int(k)].open) * (1 + pt.SLIP)
                co = pt._intra_arms(b, cv, int(k), e * (1 + stop_pct), "long", sym, day, dcl)
                if co:
                    ctrl[arm_name].append({**co, "sym": sym, "date": day})
        if fi % 2000 == 0:
            print(f"  {fi:,}/{len(files):,} files, signals so far {sum(len(v) for v in recs.values()):,}", flush=True)
    print(f"skipped {miss:,} files without daily levels/ADR", flush=True)

    rows = []
    for arm_name in ARMS:
        T, K = pd.DataFrame(recs[arm_name]), pd.DataFrame(ctrl[arm_name])
        if T.empty:
            print(f"{arm_name}: no signals"); continue
        T.to_parquet(pt.REPO / f"data/cache/pattern_{TAG.replace(' ', '_')}_{arm_name.replace(' ', '_').lower()}.parquet", index=False)
        pt._report(f"{TAG}: {arm_name}", T, K, pt.INTRA_ARMS, SPLIT, "pre-registered level_trigger_test_2026-09-21.md",
                   "intraday", ledger=(arm_name != "PIVOT BREAK"))
        s = T.stop_close
        d = s.groupby(T.date).mean()
        rows.append(dict(arm=arm_name, n=len(T), per_session=len(T) / T.date.nunique(), meanR=s.mean(),
                         t=d.mean() / d.std() * np.sqrt(len(d)), ctrl=K.stop_close.mean() if len(K) else np.nan,
                         half1=s[T.date < SPLIT].mean(), half2=s[T.date >= SPLIT].mean(),
                         curated=s[T.set == "curated"].mean(), control_set=s[T.set == "control set"].mean(),
                         win=(s > 0).mean() * 100, ext21_med=T.ext21_adr.median(), risk_med=T.risk_adr.median(),
                         vs_pivot_med=T.vs_pivot_adr.median(), next_close=T.next_close.mean()))
    R = pd.DataFrame(rows)
    R["edge"] = R.meanR - R.ctrl
    piv = float(R.loc[R.arm == "PIVOT BREAK", "meanR"].iloc[0]) if (R.arm == "PIVOT BREAK").any() else np.nan
    R["beats_pivot"] = R.meanR > piv
    R["PASS"] = (R.edge > 0) & (R.t.abs() >= 3) & (R.t > 0) & (R.half1 > 0) & (R.half2 > 0) & (R.control_set > 0) & R.beats_pivot
    R.loc[R.arm == "PIVOT BREAK", "PASS"] = False
    print("\n\n== SUMMARY (primary exit = stop_close: hold to the close with the stop; R) ==")
    print(R.round(3).to_string(index=False))
    R.to_csv(pt.REPO / "data/studies/level_trigger_test_2026-09-21.csv", index=False)
    print(f"\npasses: {int(R.PASS.sum())} of 12")


if __name__ == "__main__":
    main()

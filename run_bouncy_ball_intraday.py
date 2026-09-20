#!/usr/bin/env python3
"""
The "bouncy ball" on Breitstein's own timeframe: 5-min structure over our 1-min cache (Feb-Sep 2026).

Spec (data/lance_breitstein/principles/setup-grading-chart-nuance.md 2e), pre-registered:
  down leg    session high -> a low at least LEG_ADR (0.5) ADR below it, inside the session
  bounces     >= 2 fractal highs (5-min) after that high, EACH lower than the previous
  fading      the last bounce is smaller than the one before it
  tight       range of the last 3 five-min bars <= TIGHT (0.6) x the prior 3
  support     lowest low since the session high
  trigger     a 5-min CLOSE below support, 09:45-15:30
  entry       next 1-min bar's open, short, 10 bps against; stop = the trigger bar's high
  R           (entry - exit) / (stop - entry)
  arms        stop_close (cover at 16:00), t1R, t2R, vwap_reclaim (1-min close back above session VWAP),
              time30, trail_5m_highs (cover on a 5-min close above the prior 5-min bar's high),
              next_close (hold to the next session's close unless stopped intraday)
  control     3 random 5-min entries in the same name-day, same stop distance in %, same arms
  bar         positive, beats the control, |t| >= 3 (t clustered by session date)

No borrow cost modelled. Universe caveat: our cache is 192 liquid names; his stated habitat is in-play
small caps and recent IPOs.

Usage: PYTHONPATH=src .venv/bin/python3 run_bouncy_ball_intraday.py > data/studies/bouncy_ball_intraday_2026-09-18.log
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

BARS = Path("data/cache/intraday_1min")
SLIP, LEG_ADR, TIGHT = 0.0010, 0.5, 0.6
RNG = np.random.default_rng(20260918)
import sys as _sys
CONTROL = _sys.argv[_sys.argv.index("--control") + 1] if "--control" in _sys.argv else "month"
assert CONTROL in ("month", "post", "xname"), CONTROL
from collections import defaultdict as _dd
DAY_SYMS: dict[str, list[str]] = _dd(list)
ARMS = ["stop_close", "t1R", "t2R", "vwap_reclaim", "time30", "trail_5m_highs", "next_close"]

DAILY = pd.read_parquet("data/cache/stage_a_daily.parquet")
DAILY["date"] = pd.to_datetime(DAILY.date)
DCL = DAILY.pivot(index="date", columns="ticker", values="close").sort_index()
DHI = DAILY.pivot(index="date", columns="ticker", values="high").sort_index()
DLO = DAILY.pivot(index="date", columns="ticker", values="low").sort_index()
ADR = ((DHI / DLO - 1) * 100).rolling(20).mean()


def five_min(b: pd.DataFrame) -> pd.DataFrame:
    g = b.resample("5min", label="left", closed="left")
    f = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                      "close": g.close.last(), "volume": g.volume.sum()}).dropna()
    return f


def signals(sym: str, day: str, b: pd.DataFrame, adr_pct: float) -> list[dict]:
    f = five_min(b)
    if len(f) < 12 or not np.isfinite(adr_pct) or adr_pct <= 0:
        return []
    hi, lo, cl = f.high.values, f.low.values, f.close.values
    out, fired = [], False
    for i in range(6, len(f) - 1):
        if fired:
            break
        t = f.index[i]
        if not (pd.Timestamp(f"{day} 09:45") <= t <= pd.Timestamp(f"{day} 15:30")):
            continue
        hi_i = int(np.argmax(hi[:i + 1]))                       # session high so far
        if i - hi_i < 4:
            continue
        support = float(np.min(lo[hi_i:i]))
        leg_adr = (hi[hi_i] - support) / (hi[hi_i] * adr_pct / 100)
        if leg_adr < LEG_ADR:
            continue
        # fractal highs (5-min) strictly between the session high and now
        fr = [k for k in range(hi_i + 1, i) if 0 < k < len(hi) - 1 and hi[k] > hi[k - 1] and hi[k] >= hi[k + 1]]
        if len(fr) < 2:
            continue
        bh = [hi[k] for k in fr]
        if not all(bh[k + 1] < bh[k] for k in range(len(bh) - 1)):
            continue
        if (bh[-1] - support) >= (bh[-2] - support):            # the last bounce must be the smallest
            continue
        r3 = hi[i - 3:i].max() - lo[i - 3:i].min()
        r3p = hi[i - 6:i - 3].max() - lo[i - 6:i - 3].min()
        if not (r3p > 0 and r3 / r3p <= TIGHT):
            continue
        if cl[i] < support:                                     # trigger
            out.append(dict(sym=sym, date=day, t=t, stop=float(hi[i]), support=support,
                            leg_adr=leg_adr, n_bounces=len(bh)))
            fired = True
    return out


def arms_from(b: pd.DataFrame, i0: int, entry: float, stop: float, sym: str, day: str) -> dict | None:
    risk = stop - entry
    if not np.isfinite(risk) or risk <= 0 or risk / entry > 0.10:
        return None
    sub = b.iloc[i0:]
    cv = (b.vwap * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)
    out, stopped_at = {}, None
    for arm in ARMS:
        if arm == "next_close":
            continue
        r, lim = np.nan, (30 if arm == "time30" else len(sub))
        prev5_high = None
        for j in range(min(lim, len(sub))):
            row = sub.iloc[j]
            if row.high >= stop:
                r = (entry - stop * (1 + SLIP)) / risk
                stopped_at = stopped_at or j
                break
            if arm == "t1R" and row.low <= entry - risk:
                r = 1.0
                break
            if arm == "t2R" and row.low <= entry - 2 * risk:
                r = 2.0
                break
            if arm == "vwap_reclaim" and j > 0 and row.close > cv.iloc[i0 + j]:
                r = (entry - row.close * (1 + SLIP)) / risk
                break
            if arm == "trail_5m_highs" and j >= 5:
                prev5_high = sub.iloc[j - 5:j].high.max()
                if row.close > prev5_high:
                    r = (entry - row.close * (1 + SLIP)) / risk
                    break
        if not np.isfinite(r):
            r = (entry - sub.iloc[min(lim, len(sub)) - 1].close * (1 + SLIP)) / risk
        out[arm] = r
    # overnight: stopped intraday -> that result; else next session's close
    if stopped_at is not None:
        out["next_close"] = out["stop_close"]
    else:
        col = DCL[sym] if sym in DCL.columns else None
        if col is None:
            out["next_close"] = np.nan
        else:
            pos = DCL.index.searchsorted(pd.Timestamp(day))
            out["next_close"] = ((entry - float(col.iloc[pos + 1]) * (1 + SLIP)) / risk
                                 if pos + 1 < len(col) and np.isfinite(col.iloc[pos + 1]) else np.nan)
    return out


def main() -> None:
    files = sorted(BARS.glob("*.parquet"))
    for _q in files:
        DAY_SYMS[_q.name.rsplit("_", 1)[1][:-8]].append(_q.name.rsplit("_", 1)[0])
    sig, recs, ctrl = [], [], []
    for p in files:
        sym, day = p.name.rsplit("_", 1)[0], p.name.rsplit("_", 1)[1][:-8]
        ts = pd.Timestamp(day)
        if sym not in ADR.columns or ts not in ADR.index:
            continue
        pos = ADR.index.searchsorted(ts)
        adr_pct = ADR[sym].iloc[pos - 1] if pos > 0 else np.nan
        b = pd.read_parquet(p)
        b = b[~b.index.duplicated(keep="first")].sort_index()
        if len(b) < 60:
            continue
        for s in signals(sym, day, b, adr_pct):
            sig.append(s)
            i0 = int(b.index.searchsorted(s["t"] + pd.Timedelta(minutes=5), side="left"))
            if i0 >= len(b) - 2:
                continue
            entry = float(b.iloc[i0].open) * (1 - SLIP)
            o = arms_from(b, i0, entry, s["stop"], sym, day)
            if o:
                recs.append({**o, **{k: s[k] for k in ("sym", "date", "leg_adr", "n_bounces")}, "hhmm": s["t"].strftime("%H:%M")})
                stop_pct = s["stop"] / entry - 1
                lo_i = int(b.index.searchsorted(pd.Timestamp(f"{day} 09:45")))
                hi_i = int(b.index.searchsorted(pd.Timestamp(f"{day} 15:30")))
                if CONTROL == "xname":              # random other name with bars that day, same minute, same stop %
                    others = [x for x in DAY_SYMS.get(day, []) if x != sym]
                    for s2 in RNG.choice(others, size=min(3, len(others)), replace=False) if others else []:
                        b2 = pd.read_parquet(BARS / f"{s2}_{day}.parquet")
                        if not {"open", "high", "low", "close"} <= set(b2.columns) or ("vwap" in b.columns and "vwap" not in b2.columns):
                            continue
                        b2 = b2[~b2.index.duplicated(keep="first")].sort_index()
                        k = int(b2.index.searchsorted(b.index[i0], side="left"))
                        if k >= len(b2) - 2:
                            continue
                        e = float(b2.iloc[k].open) * (1 - SLIP)
                        co = arms_from(b2, k, e, e * (1 + stop_pct), str(s2), day)
                        if co:
                            ctrl.append({**co, "sym": str(s2), "date": day})
                    continue
                if CONTROL == "post":               # random later bar the same name-day
                    lo_i = i0 + 1
                if hi_i - lo_i > 10:
                    for k in RNG.choice(np.arange(lo_i, hi_i), size=min(3, hi_i - lo_i), replace=False):
                        e = float(b.iloc[int(k)].open) * (1 - SLIP)
                        co = arms_from(b, int(k), e, e * (1 + stop_pct), sym, day)
                        if co:
                            ctrl.append({**co, "sym": sym, "date": day})
    T, K = pd.DataFrame(recs), pd.DataFrame(ctrl)
    if T.empty:
        print("no signals"); return
    sfx = "" if CONTROL == "month" else f"_{CONTROL}"
    T.to_parquet(f"data/cache/bouncy_ball_intraday{sfx}.parquet", index=False)
    K.to_parquet(f"data/cache/bouncy_ball_intraday_control{sfx}.parquet", index=False)
    print(f"control = {CONTROL}")
    print(f"signals: {len(T):,} on {T.sym.nunique()} names / {T.date.nunique()} sessions "
          f"({len(T) / T.date.nunique():.2f} per session) | median leg {T.leg_adr.median():.2f} ADR, "
          f"bounces {T.n_bounces.median():.0f} | control {len(K):,}")

    def stats(x, arm):
        s = x[arm].dropna()
        if len(s) < 20:
            return dict(n=len(s))
        d = s.groupby(x.loc[s.index, "date"]).mean()
        return dict(n=len(s), meanR=s.mean(), medR=s.median(), win=100 * (s > 0).mean(),
                    t=d.mean() / d.std() * np.sqrt(len(d)))

    tab = pd.DataFrame({a: stats(T, a) for a in ARMS}).T
    tab["ctrl"] = [K[a].dropna().mean() if a in K else np.nan for a in ARMS]
    tab["edge"] = tab.meanR - tab.ctrl
    print(f"\n=== BOUNCY BALL (5-min structure, 1-min fills) — R per trade ===")
    print(tab.round(3).to_string())
    print("\n=== by half ===")
    h1, h2 = T[T.date < "2026-06-01"], T[T.date >= "2026-06-01"]
    print(pd.DataFrame({"Feb-May": {a: h1[a].mean() for a in ARMS}, "n1": {a: len(h1) for a in ARMS},
                        "Jun-Sep": {a: h2[a].mean() for a in ARMS}, "n2": {a: len(h2) for a in ARMS}}).round(3).to_string())
    print("\n=== by depth of the down leg ===")
    cut = pd.cut(T.leg_adr, [0.5, 1, 2, 4, 100])
    print(T.groupby(cut, observed=True)[ARMS].mean().join(T.groupby(cut, observed=True).size().rename("n")).round(3).to_string())


if __name__ == "__main__":
    main()

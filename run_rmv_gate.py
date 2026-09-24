#!/usr/bin/env python3
"""
[WL-3a] RMV tightness gate on the house breakout (pre-registered 2026-09-23; spec copied from
data/deepvue/videos/2026-03-06_dDAoAjyYI2I/notes.md "Not tested, could be" BEFORE running).

RMV (Deepvue "relative measured volatility", reconstructed): v_t = 3-bar true range / close,
  TR3_t = max(H[t-2..t], C[t-3]) - min(L[t-2..t], C[t-3]);  RMV_L,t = 100 (v_t - min v[t-L+1..t]) / (max - min), L = 15.
Trigger: house breakout (close > prior 20d high, ADR20 >= 3%, eligible), entered at the CLOSE.
Gate (PRIMARY): min(RMV15[t-3 .. t-1]) <= 10 -- tight in at least one of the 3 sessions before the breakout; the
  breakout day is excluded (expansion by construction), so the gate uses no bar >= t.
Exit (both arms): stop = breakout day's low judged on the close, then first close < EMA20, max 60 sessions, 0.10%
  slippage a side. METRIC = % return per trade (R reported second: stop floor 2%, cap 20).
PRIMARY control: date-matched cross-name -- on each date with >= 1 gated and >= 1 ungated breakout,
  diff_d = mean(gated %) - mean(ungated %); t clustered by date. (NOT a same-name window: that retracted the VCP pass.)
Secondary: the same within ADR terciles (date x tercile cells); harness rows (paired rule) vs post and xname.
Must also show: higher held-the-level share (low never touches the breakout level within 20 sessions) than same-date
  ungated breakouts.
Confound check (pre-declared): gated-minus-ungated gap in ext_above_level (ADR) and stop/ADR; primary re-run within
  extension terciles. If the gate only picks less-extended entries, it's the entry-extension finding again.
Bar: |t| >= 3 on the primary diff, both halves (split 2023-01-01) the same sign, per-year shown.
Exploratory (Sidak k = 8, |t| ~ 2.9, no verdict of their own): RMV5 <= 10; RMV15 <= 5; RMV15 <= 15; inner = 1-bar TR;
  inner = ATR3/C; Brandt ADX(14) <= 12. (vol_compression.is_compressing was in the spec's list; dropped here because
  it needs a 252-day history per name and is a year-scale screen, a different object -- noted, not run.)

Run: PYTHONPATH=src .venv/bin/python3 run_rmv_gate.py   (log -> data/studies/logs/rmv_gate.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import daily_signals, load_panel, run_daily
import run_vcp_damped_sine as V

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/rmv_gate.log"
START, SPLIT = "2019-10-01", "2023-01-01"


def inner(P, kind: str) -> pd.DataFrame:
    C, H, L = P.close, P.high, P.low
    pc = C.shift(1)
    if kind == "tr3":
        hi = np.maximum(H.rolling(3).max(), C.shift(3))
        lo = np.minimum(L.rolling(3).min(), C.shift(3))
        return (hi - lo) / C
    tr1 = np.maximum(H, pc) - np.minimum(L, pc)
    if kind == "tr1":
        return tr1 / C
    if kind == "atr3":
        return tr1.rolling(3).mean() / C
    raise ValueError(kind)


def rmv(v: pd.DataFrame, L: int) -> pd.DataFrame:
    lo, hi = v.rolling(L).min(), v.rolling(L).max()
    return 100 * (v - lo) / (hi - lo).replace(0, np.nan)


def adx(P, n: int = 14) -> pd.DataFrame:
    H, L, C = P.high, P.low, P.close
    up, dn = H.diff(), -L.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0)
    ndm = dn.where((dn > up) & (dn > 0), 0.0)
    tr = np.maximum(H, C.shift(1)) - np.minimum(L, C.shift(1))
    a = 1 / n
    atr = tr.ewm(alpha=a, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=a, adjust=False).mean() / atr
    ndi = 100 * ndm.ewm(alpha=a, adjust=False).mean() / atr
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=a, adjust=False).mean()


def trades(P) -> pd.DataFrame:
    hb, lvl = V.house_breakout(P)
    C, L = P.close.values, P.low.values
    adrpx = (P.adr / 100 * P.close).values
    rows = []
    for i, j in zip(*np.where(hb.values)):
        r = V.pct_trade(P, j, i, L[i, j], lvl.values[i, j])
        if r is None:
            continue
        stop_pct = max((C[i, j] - L[i, j]) / C[i, j], 0.02) * 100
        rows.append(dict(i=i, j=j, date=hb.index[i], sym=hb.columns[j], ret=r[0], held=r[1],
                         R=float(np.clip(r[0] / stop_pct, -20, 20)),
                         ext=(C[i, j] - lvl.values[i, j]) / adrpx[i, j], stop_adr=(C[i, j] - L[i, j]) / adrpx[i, j],
                         adr=P.adr.values[i, j]))
    return pd.DataFrame(rows)


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def date_matched(T: pd.DataFrame, gate: pd.Series, col: str = "ret", by: list[str] | None = None) -> dict:
    keys = ["date"] + (by or [])
    g = T.assign(g=gate.values).groupby(keys + ["g"])[col].mean().unstack("g")
    if True not in g or False not in g:
        return dict(n=0)
    d = (g[True] - g[False]).dropna()
    dd = d.groupby(level=0).mean()                                  # one value per date
    return dict(n_dates=len(dd), gated=g[True].loc[d.index].mean(), ungated=g[False].loc[d.index].mean(),
                diff=dd.mean(), t=tstat(dd), h1=dd[dd.index < SPLIT].mean(), h2=dd[dd.index >= SPLIT].mean(), _dd=dd)


def fmt(r: dict) -> str:
    if not r.get("n_dates"):
        return "no paired dates"
    return (f"dates {r['n_dates']:4d} | gated {r['gated']:+.2f} vs ungated {r['ungated']:+.2f} | diff {r['diff']:+.2f} "
            f"t {r['t']:+.2f} | halves {r['h1']:+.2f}/{r['h2']:+.2f}")


def main():
    P = load_panel()
    T = trades(P)
    T = T[T.date >= START].reset_index(drop=True)
    ii, jj = T.i.values, T.j.values
    gates = {}
    for name, kind, Lb, thr in (("PRIMARY RMV15<=10 (tr3)", "tr3", 15, 10), ("RMV5<=10", "tr3", 5, 10),
                                ("RMV15<=5", "tr3", 15, 5), ("RMV15<=15", "tr3", 15, 15),
                                ("inner 1-bar TR, RMV15<=10", "tr1", 15, 10), ("inner ATR3, RMV15<=10", "atr3", 15, 10)):
        R = rmv(inner(P, kind), Lb).shift(1).rolling(3).min()        # sessions t-3 .. t-1 only
        gates[name] = pd.Series(R.values[ii, jj] <= thr)
    A = adx(P).shift(1).values[ii, jj]
    gates["Brandt ADX14<=12 (t-1)"] = pd.Series(A <= 12)
    print(f"# RMV gate [WL-3a] -- {len(T):,} house breakouts, {T.sym.nunique()} names, {T.date.min().date()} -> "
          f"{T.date.max().date()}; all-breakout mean {T.ret.mean():+.2f}%")
    g0 = gates["PRIMARY RMV15<=10 (tr3)"]
    print(f"gated share {g0.mean():.1%}")
    print("\n## PRIMARY: gated vs ungated, same date, other names, % per trade")
    P1 = date_matched(T, g0)
    print(fmt(P1))
    yr = P1["_dd"].groupby(P1["_dd"].index.year).agg(["size", "mean"]).round(2)
    print("per year:\n" + yr.T.to_string())
    H = date_matched(T, g0, "held")
    print(f"held-the-level share (date-matched): gated {100 * H['gated']:.1f}% vs ungated {100 * H['ungated']:.1f}% "
          f"| diff {100 * H['diff']:+.1f}pp t {H['t']:+.2f}")
    RR = date_matched(T, g0, "R")
    print(f"R (stop floor 2%, cap 20): gated {RR['gated']:+.3f} vs ungated {RR['ungated']:+.3f} | diff {RR['diff']:+.3f} "
          f"t {RR['t']:+.2f}")
    print("\n## confound check (pre-declared)")
    Tg = T.assign(g=g0.values)
    print(Tg.groupby("g")[["ext", "stop_adr", "adr"]].median().round(3).to_string())
    T["ext_terc"] = pd.qcut(T.ext, 3, labels=["low ext", "mid ext", "high ext"])
    T["adr_terc"] = T.groupby("date").adr.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)
                                                    if len(s) >= 3 else 0)
    print("primary within extension terciles:")
    for k in ("low ext", "mid ext", "high ext"):
        m = (T.ext_terc == k).values
        print(f"  {k:8s} " + fmt(date_matched(T[m], g0[m])))
    print("secondary, ADR-tercile-matched within date: " + fmt(date_matched(T, g0, by=["adr_terc"])))
    print("\n## exploratory (Sidak k = 8, |t| ~ 2.9; no verdict of their own)")
    for name, g in gates.items():
        if name.startswith("PRIMARY"):
            continue
        print(f"  {name:28s} share {g.mean():5.1%} | " + fmt(date_matched(T, g)))
    T.assign(gate=g0.values).to_csv(REPO / "data/studies/logs/rmv_gate_trades.csv", index=False)

    print("\n\n# harness rows (paired rule; gated breakouts; close entry, day-low stop, hold 60)")
    gmask = pd.DataFrame(False, index=P.close.index, columns=P.close.columns)
    gmask.values[ii[g0.values], jj[g0.values]] = True

    def pattern(_P):
        return daily_signals(gmask, stop=P.low, side="long", since=START)
    run_daily("rmv15 gate on house breakout", pattern, hold=60, entry_at="close", control="post", panel=P,
              note="WL-3a Deepvue RMV15<=10 in t-3..t-1, house breakout, day-low stop")
    run_daily("rmv15 gate on house breakout xname", pattern, hold=60, entry_at="close", control="xname", panel=P,
              ledger=False)
    return P1, H


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    txt = open(LOG).read()
    print(txt.split("# harness rows")[0])
    for ln in txt.splitlines():
        if "paired edge by half" in ln or "passes the bar" in ln:
            print(ln)

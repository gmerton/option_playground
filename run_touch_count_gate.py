#!/usr/bin/env python3
"""
Resistance TOUCH COUNT as a gate on the house breakout (pre-registered 2026-10-04, BEFORE any outcome was computed).

Origin: TEST_INDEX §10 "Breakout gates: resistance touch count + weekly squeeze" (SMB FdMcPKGtFgA, queued 2026-09-26),
re-raised by Breitstein UAlhNPmvB14 (2026-10-03): "clean levels that price has respected rather than traded through".
Only the touch-count half is run here (Gabe 2026-10-04); the weekly squeeze stays queued.

Universe / trigger: liquid_panel_2009 (⚠ survivors -- both arms share the bias; the comparison is within-date), house
  breakout = close > prior 20-session high (the LEVEL), ADR20 >= 3%, eligible (ADDV >= $50M, px >= $5), 2010-01-01 ->
  2026-06-30 (room for the 60-session hold). Entry at the breakout CLOSE.
Exit (all arms): stop = breakout day's low judged on the close, else first close < EMA20, max 60 sessions; 0.10% slippage
  a side (after-cost). METRIC = % return per trade; R (stop floor 2%, cap 20) second.

TOUCH (pre-declared): in sessions t-60 .. t-1, a session "touches" when |high - LEVEL| <= 0.25 ADR (ADR in $ at t). A
  touch = one EPISODE = a run of consecutive touching sessions (a 3-day stall at the level is one touch). The session that
  set the 20-day high is itself a touch, so every breakout has >= 1.
PRIMARY (as queued): MANY = >= 5 touches vs FEW = 2-4 touches (1-touch breakouts are outside the primary comparison).
  diff_d = mean(MANY %) - mean(FEW %) on each date with >= 1 of each; t clustered by date.
Bar: |t| >= 3 on the primary diff, both halves (split 2018-01-01) the same sign, per-year shown, AND a higher
  held-the-level share (low never trades back to the level within 20 sessions). Verdict scheme per TEST_INDEX.
Confound check (pre-declared): MANY-minus-FEW medians of extension above the level (ADR), stop/ADR, ADR; primary re-run
  within extension terciles and within same-date ADR terciles. Many touches = a longer base under the level, so if the
  edge lives only in the low-extension tercile it is the entry-extension finding again, not the touch count.
Exploratory (Sidak k = 6, no verdict of their own):
  E1 >= 3 vs 1-2 touches;  E2 touch DAYS (not episodes) >= 5 vs 2-4;  E3 band 0.5 ADR, >= 5 vs 2-4;
  E4 lookback 120 sessions, >= 5 vs 2-4;  E5 Breitstein "respected": >= 3 touches AND no close above LEVEL + 0.25 ADR in
  t-60..t-1, vs every other breakout;  E6 dose table: mean same-date excess by touch count 1/2/3/4/5+ (descriptive).
Prior: LOW -- RMV (tight breakouts hold LESS, t -2.83), VCP and Carter squeeze all NULL on daily bars.

Run: PYTHONPATH=src .venv/bin/python3 run_touch_count_gate.py   (log -> data/studies/logs/touch_count_gate.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import run_vcp_damped_sine as V
from lib.studies.pattern_test import daily_signals, load_panel, run_daily

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/touch_count_gate.log"
START, UNTIL, SPLIT = "2010-01-01", "2026-06-30", "2018-01-01"
K_EXPL = 6
V.START = START                                                    # house_breakout zeroes signals before V.START


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def touches(H: np.ndarray, Cl: np.ndarray, i: int, j: int, lvl: float, band: float, look: int) -> tuple[int, int, bool]:
    """(episodes, touch days, closed above LEVEL + band) over sessions i-look .. i-1."""
    h = H[max(0, i - look):i, j]
    c = Cl[max(0, i - look):i, j]
    t = np.isfinite(h) & (np.abs(h - lvl) <= band)
    ep = int(t[0]) + int(np.sum(t[1:] & ~t[:-1])) if len(t) else 0
    return ep, int(t.sum()), bool(np.any(c[np.isfinite(c)] > lvl + band))


def trades(P) -> pd.DataFrame:
    hb, lvl = V.house_breakout(P)
    hb[hb.index > UNTIL] = False
    C, L, H = P.close.values, P.low.values, P.high.values
    adrpx = (P.adr / 100 * P.close).values
    rows = []
    for i, j in zip(*np.where(hb.values)):
        r = V.pct_trade(P, j, i, L[i, j], lvl.values[i, j])
        if r is None:
            continue
        lv, a = lvl.values[i, j], adrpx[i, j]
        ep, days, above = touches(H, C, i, j, lv, 0.25 * a, 60)
        ep50, _, _ = touches(H, C, i, j, lv, 0.50 * a, 60)
        ep120, _, _ = touches(H, C, i, j, lv, 0.25 * a, 120)
        stop_pct = max((C[i, j] - L[i, j]) / C[i, j], 0.02) * 100
        rows.append(dict(date=hb.index[i], sym=hb.columns[j], ret=r[0], held=r[1],
                         R=float(np.clip(r[0] / stop_pct, -20, 20)), ext=(C[i, j] - lv) / a,
                         stop_adr=(C[i, j] - L[i, j]) / a, adr=P.adr.values[i, j], i=i, j=j,
                         tc=ep, tdays=days, above=above, tc50=ep50, tc120=ep120))
    return pd.DataFrame(rows)


def matched(T: pd.DataFrame, a: pd.Series, b: pd.Series, col: str = "ret", by: list[str] | None = None) -> dict:
    """Same-date mean(a) - mean(b), one value per date; rows in neither group are dropped."""
    keys = ["date"] + (by or [])
    S = T[(a | b).values].assign(g=a[(a | b).values].values)
    g = S.groupby(keys + ["g"])[col].mean().unstack("g")
    if True not in g or False not in g:
        return dict(n_dates=0)
    d = (g[True] - g[False]).dropna()
    dd = d.groupby(level=0).mean()
    return dict(n_dates=len(dd), n_a=int(a.sum()), n_b=int(b.sum()), a=g[True].loc[d.index].mean(),
                b=g[False].loc[d.index].mean(), diff=dd.mean(), t=tstat(dd),
                h1=dd[dd.index < SPLIT].mean(), h2=dd[dd.index >= SPLIT].mean(), _dd=dd)


def fmt(r: dict, unit: str = "") -> str:
    if not r.get("n_dates"):
        return "no paired dates"
    return (f"n {r['n_a']:,}/{r['n_b']:,} dates {r['n_dates']:4d} | {r['a']:+.2f}{unit} vs {r['b']:+.2f}{unit} | "
            f"diff {r['diff']:+.2f} t {r['t']:+.2f} | halves {r['h1']:+.2f}/{r['h2']:+.2f}")


def main():
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    T = trades(P)
    T = T[(T.date >= START) & (T.date <= UNTIL)].reset_index(drop=True)
    many, few = (T.tc >= 5), T.tc.between(2, 4)
    print(f"# Touch-count gate -- {len(T):,} house breakouts, {T.sym.nunique()} names, {T.date.min().date()} -> "
          f"{T.date.max().date()}; all-breakout mean {T.ret.mean():+.2f}% (after 0.10%/side slippage)")
    print("touch-count distribution (episodes, 60 sessions, 0.25 ADR):")
    print(T.tc.clip(upper=8).value_counts().sort_index().rename(lambda k: f"{k}{'+' if k == 8 else ''}").to_string())
    print(f"MANY (>=5) {many.mean():.1%} | FEW (2-4) {few.mean():.1%} | 1 touch {(T.tc == 1).mean():.1%}")

    print("\n## PRIMARY: MANY (>=5) vs FEW (2-4), same date, % per trade")
    P1 = matched(T, many, few)
    print(fmt(P1, "%"))
    yr = P1["_dd"].groupby(P1["_dd"].index.year).agg(["size", "mean"]).round(2)
    print("per year:\n" + yr.T.to_string())
    print(f"years positive: {(yr['mean'] > 0).sum()} of {len(yr)}")
    Hd = matched(T, many, few, "held")
    print(f"held-the-level share: MANY {100 * Hd['a']:.1f}% vs FEW {100 * Hd['b']:.1f}% | diff {100 * Hd['diff']:+.1f}pp "
          f"t {Hd['t']:+.2f}")
    RR = matched(T, many, few, "R")
    print(f"R (stop floor 2%, cap 20): MANY {RR['a']:+.3f} vs FEW {RR['b']:+.3f} | diff {RR['diff']:+.3f} t {RR['t']:+.2f}")
    print(f"gross (add back 0.20pp to both arms; the diff is unchanged): MANY {P1['a'] + 0.2:+.2f}% vs FEW {P1['b'] + 0.2:+.2f}%")

    print("\n## confound check (pre-declared)")
    print(T.assign(grp=np.select([many, few], ["MANY", "FEW"], "1 touch")).groupby("grp")[["ext", "stop_adr", "adr"]]
          .median().round(3).to_string())
    T["ext_terc"] = pd.qcut(T.ext, 3, labels=["low ext", "mid ext", "high ext"])
    T["adr_terc"] = T.groupby("date").adr.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)
                                                    if len(s) >= 3 else 0)
    print("primary within extension terciles:")
    for k in ("low ext", "mid ext", "high ext"):
        m = (T.ext_terc == k).values
        print(f"  {k:8s} " + fmt(matched(T[m].reset_index(drop=True), many[m].reset_index(drop=True),
                                          few[m].reset_index(drop=True)), "%"))
    print("within same-date ADR terciles: " + fmt(matched(T, many, few, by=["adr_terc"]), "%"))

    thr = norm.ppf(1 - (1 - 0.95 ** (1 / K_EXPL)) / 2)
    print(f"\n## exploratory (Sidak k = {K_EXPL}, |t| >= {thr:.2f}; no verdict of their own)")
    expl = {"E1 >=3 vs 1-2 touches": (T.tc >= 3, T.tc.between(1, 2)),
            "E2 touch DAYS >=5 vs 2-4": (T.tdays >= 5, T.tdays.between(2, 4)),
            "E3 band 0.5 ADR >=5 vs 2-4": (T.tc50 >= 5, T.tc50.between(2, 4)),
            "E4 lookback 120 >=5 vs 2-4": (T.tc120 >= 5, T.tc120.between(2, 4))}
    resp = (T.tc >= 3) & ~T.above
    expl["E5 respected (>=3, never closed through) vs rest"] = (resp, ~resp)
    for name, (a, b) in expl.items():
        print(f"  {name:48s} " + fmt(matched(T, a, b), "%"))
    print("  E6 dose: same-date excess of each touch-count bucket vs all other breakouts that date")
    for k in (1, 2, 3, 4, 5):
        a = (T.tc >= 5) if k == 5 else (T.tc == k)
        r = matched(T, a, ~a)
        print(f"     {k}{'+' if k == 5 else ' '} touches: n {int(a.sum()):6,d} | excess {r['diff']:+.2f}pp t {r['t']:+.2f}")
    T.drop(columns=["ext_terc"]).to_csv(REPO / "data/studies/logs/touch_count_gate_trades.csv", index=False)

    print("\n\n# harness rows (paired rule; MANY-touch breakouts; close entry, day-low stop, hold 60)")
    gmask = pd.DataFrame(False, index=P.close.index, columns=P.close.columns)
    gmask.values[T.i.values[many.values], T.j.values[many.values]] = True

    def pattern(_P):
        return daily_signals(gmask, stop=P.low, side="long", since=START)
    run_daily("touch>=5 gate on house breakout", pattern, hold=60, entry_at="close", control="post", panel=P,
              split=SPLIT, note="TEST_INDEX §10 touch count (SMB/Breitstein), >=5 touches t-60..t-1 within 0.25 ADR")
    run_daily("touch>=5 gate on house breakout xname", pattern, hold=60, entry_at="close", control="xname", panel=P,
              split=SPLIT, ledger=False)
    return P1, Hd


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

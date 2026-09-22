#!/usr/bin/env python3
"""Universe test (pre-registered 2026-09-21): Ariel Hernandez's momentum scan vs our Minervini Trend Template,
plus their intersection and two hybrids. Spec: data/ariel_hernandez/analysis/2026-09-21_universe_list_review.md.

Arms (daily membership masks, computed on the liquid panel, shifted ONE session = membership as of the prior close):
  TT     Trend Template c1-c8, RS pct >= 70, ADDV(50d) >= $200M                      (ours)
  AH     >= 70% above the 252d low, close > 50 SMA, >= 2M sh/day (50d), close > $7, ADDV >= $100M   (his)
  INT    TT & AH
  HYB-A  AH & close > 200 SMA & 200 SMA rising (vs 20 sessions ago) & ADR >= 4%
  HYB-B  TT at ADDV >= $100M & ADR >= 4%

Q1  does the universe select?  forward 5/20-session close-to-close return of a random member vs the whole eligible
    panel on the same date; non-overlapping dates (every 5th / 20th session); t on per-date differences.
Q2  does the house breakout work inside it?  house breakout (run_precision_tier_control.build brk) on members,
    CLOSE entry, stop = day low, hold 60, all harness arms (ema20 trail = the house exit); control "post" (same name,
    random later session) and "xname" drawn from the SAME mask.
Q3  is it walkable?  members/day, monthly turnover, median ADR / ADDV.

A hybrid is adopted only if it beats BOTH parents (TT and AH) in BOTH halves (split 2023-01-01) on Q1 (20d excess)
or on Q2 (ema20 edge vs post). Pass bar for any arm on Q2 = the harness bar.
⚠ Caveats: the panel is today's liquid names (survivorship) -> compare arms with each other; RS percentile is ranked
inside the 1,742-name liquid panel, not the ~5k Polygon universe production ranks against (stricter).

Usage: PYTHONPATH=src .venv/bin/python3 run_universe_test.py | tee data/studies/universe_test_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)

import run_precision_tier_control as pc
from lib.studies import pattern_test as pt
from lib.studies.pattern_test import DailyPanel, daily_signals, run_daily

SPLIT = "2023-01-01"
START = "2020-01-01"       # 252-session windows need a year of panel history (panel starts 2019-01)
ARMS = ["TT", "AH", "INT", "HYB-A", "HYB-B"]


def build_masks(P: DailyPanel, raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    C, H, L = P.close, P.high, P.low
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex(index=C.index, columns=C.columns)
    dolvol, vol = piv("dolvol"), piv("volume")
    sma50, sma150, sma200 = (C.rolling(n, min_periods=n).mean() for n in (50, 150, 200))
    hi252 = H.rolling(252, min_periods=200).max()
    lo252 = L.rolling(252, min_periods=200).min()
    addv = dolvol.rolling(50, min_periods=50).mean()
    shares = vol.rolling(50, min_periods=50).mean()
    rs = 2 * C / C.shift(63) + C / C.shift(126) + C / C.shift(189) + C / C.shift(252)
    rs_pct = rs.where(P.elig).rank(axis=1, pct=True) * 100
    rising200 = sma200 > sma200.shift(20)
    adr = (H / L - 1).rolling(20).mean() * 100            # through today (membership is shifted a session below)
    tt_core = ((C > sma150) & (C > sma200) & (sma150 > sma200) & rising200 & (sma50 > sma150) & (C > sma50)
               & (C >= 1.30 * lo252) & (C >= 0.75 * hi252) & (rs_pct >= 70))
    tt = tt_core & (addv >= 200e6)
    ah = (C >= 1.70 * lo252) & (C > sma50) & (shares >= 2e6) & (C > 7) & (addv >= 100e6)
    m = {"TT": tt, "AH": ah, "INT": tt & ah,
         "HYB-A": ah & (C > sma200) & rising200 & (adr >= 4),
         "HYB-B": tt_core & (addv >= 100e6) & (adr >= 4)}
    out = {}
    for k, v in m.items():
        v = (v & P.elig).shift(1).fillna(False).astype(bool)     # membership as of the PRIOR close
        v[v.index < START] = False
        out[k] = v
    out["_adr"], out["_addv"] = adr.shift(1), addv.shift(1)
    return out


def q1(P: DailyPanel, masks: dict) -> pd.DataFrame:
    C = P.close
    base = P.elig.shift(1).fillna(False).astype(bool)
    rows = []
    for h in (5, 20):
        fr = C.shift(-h) / C - 1
        dates = C.index[(C.index >= START)][::h]
        dates = dates[dates <= C.index[-1 - h]]
        b = fr.where(base).loc[dates].mean(axis=1)
        for a in ARMS:
            mm = fr.where(masks[a]).loc[dates]
            d = (mm.mean(axis=1) - b).dropna()
            d = d[mm.count(axis=1).reindex(d.index) >= 5]           # need a few members on the date
            def t(x):
                return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
            h1, h2 = d[d.index < SPLIT], d[d.index >= SPLIT]
            rows.append(dict(horizon=f"{h}d", arm=a, dates=len(d), member_ret=mm.mean(axis=1).mean() * 100,
                             panel_ret=b.loc[d.index].mean() * 100, excess=d.mean() * 100, t=t(d),
                             half1=h1.mean() * 100, half2=h2.mean() * 100, pos_dates=(d > 0).mean() * 100))
    return pd.DataFrame(rows)


def q3(masks: dict) -> pd.DataFrame:
    rows = []
    for a in ARMS:
        m = masks[a]
        m = m[m.index >= START]
        n = m.sum(axis=1)
        ms = m.groupby(m.index.to_period("M")).head(1)            # first session of each month
        prev = ms.shift(1)
        stay = (ms & prev).sum(axis=1) / prev.sum(axis=1).replace(0, np.nan)
        rows.append(dict(arm=a, names_med=n.median(), names_p10=n.quantile(0.1), names_p90=n.quantile(0.9),
                         monthly_turnover=(1 - stay).mean() * 100,
                         adr_med=masks["_adr"].where(m).stack().median(),
                         addv_med_m=masks["_addv"].where(m).stack().median() / 1e6))
    return pd.DataFrame(rows)


def q2(P: DailyPanel, brk: pd.DataFrame, masks: dict) -> pd.DataFrame:
    rows = []
    for a in ["ALL"] + ARMS:
        m = brk if a == "ALL" else (brk & masks[a])
        m = m.copy(); m[m.index < START] = False
        sig = lambda _P, mm=m: daily_signals(mm, stop=P.low, side="long")
        name = f"universe test 2026-09-21: house breakout in {a}"
        print(f"\n\n{'=' * 100}\n{name}: {int(m.values.sum()):,} breakouts\n{'=' * 100}")
        tab_p = run_daily(name, sig, hold=60, panel=P, entry_at="close", control="post",
                          ledger=(a != "ALL"), note="pre-registered universe test; house = close entry, day-low stop, hold 60")
        T = pd.read_parquet(pt.REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet")
        Px = P if a == "ALL" else DailyPanel(open=P.open, high=P.high, low=P.low, close=P.close, adr=P.adr,
                                             elig=masks[a], ema20=P.ema20)
        tab_x = run_daily(name + " [xname in-mask]", sig, hold=60, panel=Px, entry_at="close", control="xname", ledger=False)
        for arm in ("ema20", "stop_hold", "t2R"):
            h1, h2 = T[T.date < SPLIT][arm].mean(), T[T.date >= SPLIT][arm].mean()
            rows.append(dict(universe=a, exit=arm, n=int(tab_p.loc[arm, "n"]), names=T.sym.nunique(),
                             dates=T.date.nunique(), meanR=tab_p.loc[arm, "meanR"], t=tab_p.loc[arm, "t"],
                             ctrl_post=tab_p.loc[arm, "ctrl"], edge_post=tab_p.loc[arm, "edge"],
                             ctrl_xname=tab_x.loc[arm, "ctrl"], edge_xname=tab_x.loc[arm, "edge"],
                             half1=h1, half2=h2))
    return pd.DataFrame(rows)


def verdict(Q1: pd.DataFrame, Q2: pd.DataFrame) -> None:
    print("\n\n== HYBRID RULE: beats BOTH parents (TT, AH) in BOTH halves ==")
    q1 = Q1[Q1.horizon == "20d"].set_index("arm")
    q2 = Q2[Q2.exit == "ema20"].set_index("universe")
    # Q2 by half: edge vs post isn't split by the harness; use meanR by half minus the full-sample post control
    for h in ("HYB-A", "HYB-B"):
        ok1 = all(q1.loc[h, c] > max(q1.loc["TT", c], q1.loc["AH", c]) for c in ("half1", "half2"))
        ok2 = all(q2.loc[h, c] > max(q2.loc["TT", c], q2.loc["AH", c]) for c in ("half1", "half2"))
        print(f"  {h}: Q1 20d excess beats both parents in both halves: {ok1} | "
              f"Q2 ema20 meanR beats both parents in both halves: {ok2}  -> {'ADOPT-candidate' if (ok1 or ok2) else 'no'}")


def main():
    P, brk, _prec = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    masks = build_masks(P, raw)
    print(f"panel {P.close.shape}, {P.close.index.min().date()} -> {P.close.index.max().date()}; test window {START} ->")
    print("\n== Q3. Walkability ==")
    print(q3(masks).round(1).to_string(index=False))
    print("\n== Q1. Does the universe select? member forward return vs the eligible panel, same dates (%) ==")
    Q1 = q1(P, masks)
    print(Q1.round(2).to_string(index=False))
    Q2 = q2(P, brk, masks)
    print("\n\n== Q2. House breakout inside each universe (R; hold 60, close entry, day-low stop) ==")
    print(Q2.round(3).to_string(index=False))
    verdict(Q1, Q2)
    Q1.to_csv(pt.REPO / "data/studies/universe_test_q1_2026-09-21.csv", index=False)
    Q2.to_csv(pt.REPO / "data/studies/universe_test_q2_2026-09-21.csv", index=False)


if __name__ == "__main__":
    main()

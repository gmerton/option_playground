#!/usr/bin/env python3
"""
Breitstein capitulation scorecard (SMB talk P4Ijq-IJhE8, principles/capitulation-ten-variables.md): does forward R
rise MONOTONICALLY with the number of his variables that align, and does the top bucket beat honest controls?

Candidates (both sides, liquid panel 2019->, ADDV >= $50M):
  extreme day e (= t-1): close >= 2 ADR beyond its 20 SMA (above = fade short, below = fade long)
  trigger day t ("right side of the V"): short = close < low[e]; long = close > high[e]
  entry next open (+10 bps, harness), stop = the extreme (short: max(high[e], high[t]); long: min(low[e], low[t])),
  risk >= 2% of the close (the honest floor), hold 10. Harness arms: stop_hold, t1R, t2R, trail_bar (his prior-bar
  trail), ema20 (meaningless for fades: it exits at once -- ignored).

Score = count of 7 mechanical variables, measured at e, mirrored for the long side:
  v1 accel    3-day move >= 2 ADR and >= 1.5x the 3 days before it
  v2 days     >= 3 consecutive closes in the move's direction
  v3 bb       >= 2.5 sigma beyond the 20 SMA (outside the 2-sigma band by >= 0.5 sigma)
  v5 volume   volume >= 3x its 50-day average
  v6 legs     >= 2 completed legs in the last 40 sessions (a 20d extreme followed within 3 sessions by a >= 1 ADR
              pullback), so the current push is leg 3+
  v7 no-cons  none of the last 5 bars moved < 0.3 ADR (no acceptance)
  v9 boring   top tercile of 50d dollar volume that day (proxy for large cap; his examples: Berkshire, Nikkei)
v4 (no fresh news) is tested separately on the names with MySQL earnings coverage: earnings within 3 sessions
before e = "fresh news" (he says don't fade it). v8 sentiment / v10 forced flows: not measurable.

Pass = mean R monotone in the score (Spearman across buckets > 0 AND top bucket > bottom), top bucket beats BOTH the
`post` and `xname` controls, both halves positive, |t| >= 3.

Usage: PYTHONPATH=src MYSQL_PASSWORD=... .venv/bin/python3 run_capitulation_scorecard.py > data/studies/breitstein_tests/logs/capitulation_scorecard_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import load_panel, run_daily

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
TODAY = date.today().isoformat()
HOLD = 10
ARMS = ["stop_hold", "t1R", "t2R", "trail_bar"]
OUT = pt.REPO / "data/studies/breitstein_tests"


def features(P, vol, dolvol):
    C, H, L = P.close, P.high, P.low
    adrp = P.adr / 100.0
    unit = C * adrp                                    # one ADR in price
    sma = C.rolling(20).mean(); sd = C.rolling(20).std()
    ext = (C - sma) / unit                             # signed distance to the 20 SMA, ADR units
    z = (C - sma) / sd
    r3 = (C / C.shift(3) - 1) / adrp
    r3p = (C.shift(3) / C.shift(6) - 1) / adrp
    up, dn = C > C.shift(1), C < C.shift(1)
    run_up = up.rolling(3).sum() == 3
    run_dn = dn.rolling(3).sum() == 3
    vmul = vol / vol.shift(1).rolling(50).mean()
    small = ((C / C.shift(1) - 1).abs() / adrp < 0.3).astype(float).rolling(5).sum() == 0
    boring = dolvol.rolling(50).mean().rank(axis=1, pct=True) >= 2 / 3
    # legs: a 20d extreme followed within 3 sessions by a >= 1 ADR pullback; only count ones complete by today
    hi20, lo20 = C >= C.rolling(20).max(), C <= C.rolling(20).min()
    fut_min = pd.concat([C.shift(-k) for k in (1, 2, 3)]).groupby(level=0).min()
    fut_max = pd.concat([C.shift(-k) for k in (1, 2, 3)]).groupby(level=0).max()
    leg_up = (hi20 & (fut_min <= C - unit)).astype(float).shift(3)
    leg_dn = (lo20 & (fut_max >= C + unit)).astype(float).shift(3)
    legs_up = leg_up.rolling(40).sum() >= 2
    legs_dn = leg_dn.rolling(40).sum() >= 2
    S = {}
    for side, sg in (("short", 1), ("long", -1)):
        v = {
            "v1_accel": (sg * r3 >= 2) & (sg * r3 >= 1.5 * np.maximum(sg * r3p, 0)),
            "v2_days": run_up if sg == 1 else run_dn,
            "v3_bb": sg * z >= 2.5,
            "v5_vol": vmul >= 3,
            "v6_legs": legs_up if sg == 1 else legs_dn,
            "v7_nocons": small,
            "v9_boring": boring,
        }
        S[side] = v
    return ext, S


def main():
    P = load_panel()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    vol = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(P.close.index)
    dolvol = raw.pivot(index="date", columns="ticker", values="dolvol").sort_index().reindex(P.close.index)
    ext, S = features(P, vol, dolvol)
    C, H, L = P.close, P.high, P.low

    try:
        from lib.mysql_lib import _get_engine
        E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
        E["raw_date"] = pd.to_datetime(E.raw_date)
    except Exception as e:                              # noqa: BLE001
        print(f"(earnings unavailable: {e})"); E = None

    all_rows, sig_tables = [], {}
    for side, sg in (("short", 1), ("long", -1)):
        cand = (sg * ext >= 2) & P.elig                                        # extreme day e
        trig = (C < L.shift(1)) if side == "short" else (C > H.shift(1))
        hit = cand.shift(1).fillna(False) & trig & P.elig
        stop = np.maximum(H, H.shift(1)) if side == "short" else np.minimum(L, L.shift(1))
        risk = sg * (stop - C) / C
        hit = hit & (risk >= 0.02) & (risk <= 0.25)
        score = sum(S[side][k].shift(1).fillna(False).astype(int) for k in S[side])
        m = hit[hit.index >= "2019-10-01"]
        ii, jj = np.where(m.values); off = len(hit) - len(m)
        ii = ii + off
        T = pd.DataFrame(dict(i=ii, j=jj, date=hit.index[ii], sym=hit.columns[jj], stop=stop.values[ii, jj], side=side,
                              score=score.values[ii, jj]))
        for k in S[side]:
            T[k] = S[side][k].shift(1).values[ii, jj].astype(bool)
        sig_tables[side] = T
        print(f"\n######## {side.upper()} fades: {len(T):,} signals, {T.date.nunique()} dates, {T.sym.nunique()} names")
        print("variable hit rates %:", {k: round(100 * T[k].mean(), 1) for k in S[side]})
        print("score distribution:", T.score.value_counts().sort_index().to_dict())

        buckets = [("0-1", T.score <= 1), ("2", T.score == 2), ("3", T.score == 3), ("4", T.score == 4),
                   ("5+", T.score >= 5)]
        for bname, bm in buckets:
            sub = T[bm]
            for ctrl in ("post", "xname"):
                name = f"capitulation scorecard {side} score {bname} ({ctrl})"
                print(f"\n=== {name}: {len(sub):,} signals, {sub.date.nunique()} dates ===")
                if len(sub) < 20:
                    continue
                tab = run_daily(name, lambda _P, s=sub: s[["i", "j", "date", "sym", "stop", "side"]], hold=HOLD, panel=P,
                                ledger=False, control=ctrl)
                if tab is None or len(tab) == 0:
                    continue
                Tt = pd.read_parquet(pt.REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet")
                h1, h2 = Tt[Tt.date < "2023-01-01"], Tt[Tt.date >= "2023-01-01"]
                for arm in ARMS:
                    all_rows.append(dict(side=side, bucket=bname, ctrl_kind=ctrl, arm=arm, n=int(tab.loc[arm, "n"]),
                                         dates=sub.date.nunique(), meanR=tab.loc[arm, "meanR"], win=tab.loc[arm, "win"],
                                         t=tab.loc[arm, "t"], ctrl=tab.loc[arm, "ctrl"], edge=tab.loc[arm, "edge"],
                                         h1=h1[arm].mean(), h2=h2[arm].mean()))

    R = pd.DataFrame(all_rows)
    R.to_csv(OUT / f"capitulation_scorecard_summary_{TODAY}.csv", index=False)
    print("\n\n################ SUMMARY: mean R by score bucket (post control) ################")
    for side in ("short", "long"):
        for arm in ARMS:
            x = R[(R.side == side) & (R.arm == arm) & (R.ctrl_kind == "post")]
            y = R[(R.side == side) & (R.arm == arm) & (R.ctrl_kind == "xname")].set_index("bucket")
            x = x.assign(ctrl_xname=x.bucket.map(y.ctrl), edge_xname=x.bucket.map(y.edge))
            rho = x.reset_index(drop=True).meanR.corr(pd.Series(range(len(x))), method="spearman")
            print(f"\n{side} / {arm}  (Spearman meanR vs bucket order = {rho:+.2f})")
            print(x[["bucket", "n", "dates", "meanR", "win", "t", "ctrl", "edge", "ctrl_xname", "edge_xname", "h1", "h2"]]
                  .round(3).to_string(index=False))

    # per-variable lift (does each variable, alone, add R?) on the trail_bar arm -- uses the post runs' trades
    print("\n\n################ per-variable split (trail_bar, all buckets pooled, post runs) ################")
    for side in ("short", "long"):
        T = sig_tables[side]
        parts = []
        for bname in ["0-1", "2", "3", "4", "5+"]:
            f = pt.REPO / f"data/cache/pattern_capitulation_scorecard_{side}_score_{bname}_(post)_daily.parquet"
            if f.exists():
                parts.append(pd.read_parquet(f))
        if not parts:
            continue
        TT = pd.concat(parts)
        TT["date"] = pd.to_datetime(TT.date)
        M = TT.merge(T.assign(date=pd.to_datetime(T.date)), on=["sym", "date"], how="left")
        rows = []
        for k in S[side]:
            a, b = M[M[k] == True], M[M[k] == False]            # noqa: E712
            rows.append(dict(var=k, n_yes=len(a), R_yes=a.trail_bar.mean(), R_no=b.trail_bar.mean(),
                             diff=a.trail_bar.mean() - b.trail_bar.mean(),
                             t1R_yes=a.t1R.mean(), t1R_no=b.t1R.mean()))
        print(f"\n{side}:"); print(pd.DataFrame(rows).round(3).to_string(index=False))
        if E is not None:
            cov = set(E.ticker)
            Mc = M[M.sym.isin(cov)].copy()
            ed = E.groupby("ticker").raw_date.apply(lambda s: np.sort(s.values)).to_dict()

            def fresh(r):
                d = ed.get(r.sym)
                if d is None:
                    return np.nan
                e_day = np.datetime64(r.date) - np.timedelta64(1, "D")
                k = np.searchsorted(d, e_day, side="right")
                return bool(k > 0 and (e_day - d[k - 1]) <= np.timedelta64(5, "D"))   # report within ~3 sessions
            Mc["fresh_news"] = Mc.apply(fresh, axis=1)
            print(f"  v4 (earnings-covered names only: {Mc.sym.nunique()} names, {len(Mc)} trades):")
            print(Mc.groupby("fresh_news")[ARMS].agg(["size", "mean"]).round(3).to_string())


if __name__ == "__main__":
    main()

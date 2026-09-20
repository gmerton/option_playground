#!/usr/bin/env python3
"""
Re-run every pre-2026-09-19 DAILY pattern-ledger row with the honest controls.

Why: the harness's original control (control="month": random session, same name, same calendar month) draws
sessions from BEFORE the signal in a name known to be about to fire -- look-ahead. On the house breakout it
"earned" +1.70R, three times the signal (breitstein_tests/precision_tier_control_2026-09-19.md). Every ledger
row dated 2026-09-18/19 used it, so "0 for 25, random beats the pattern" may be the control, not the patterns.

What this does: rebuilds each daily pattern's signals exactly as before and scores them against
  post   same name, random session in the 20 AFTER the signal (timing: is the signal day better than a later one?)
  xname  random eligible OTHER name, same date, same stop % (selection: does the name matter?)
Same arms, same R cap (10), same split (2023-01-01), same |t| >= 3 bar. One ledger row per pattern (ctrl = post;
the xname numbers go in the note), plus a side-by-side summary against the old month-control row.

Bar (honest): beats BOTH controls, positive in both halves, |t| >= 3.

Reconstructed patterns (the 2026-09-18 runs were inline, no script survived -- assumptions stated in the summary):
  in-play movers      close-to-close >= +4% (<= -4%) on volume >= 2x the trailing-50 mean, eligible; stop = bar low (high)
  earnings-proximity  the generic breakout pool (run_precision_tier_control.build) on the 241 names with earnings
                      dates, split by an earnings date in the prior 0-3 sessions vs none within +/-10

Usage: AWS_PROFILE=... MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_ledger_rerun.py [--only NAME_SUBSTR]
Output: data/studies/ledger_rerun/rerun_<date>.{csv,md}; stdout is verbose -> redirect to a log.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import lib.studies.pattern_test as pt
from lib.studies.pattern_test import DAILY_ARMS, append_ledger, daily_signals, load_panel, run_daily

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
sys.path.insert(0, str(pt.REPO))
TODAY = date.today().isoformat()
OUT = pt.REPO / "data/studies/ledger_rerun"
OUT.mkdir(parents=True, exist_ok=True)
SPLIT = "2023-01-01"


# ----------------------------------------------------------------------------------------------- patterns
def in_play(P, raw, side: str):
    V = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(P.close.index)
    ret = P.close.pct_change(fill_method=None)
    vrel = V / V.shift(1).rolling(50).mean()
    hit = ((ret >= 0.04) if side == "long" else (ret <= -0.04)) & (vrel >= 2) & P.elig
    stop = P.low if side == "long" else P.high
    return lambda _P: daily_signals(hit, stop=stop, side=side)


def bouncy_ball(P):
    """Port of run_bouncy_ball_daily.py's signal loop: fading lower bounces after a >= 3 ADR leg down, then a close
    below the leg's support on a tight 5-day range; short, stop = trigger-bar high."""
    from run_bouncy_ball_daily import LEG_ADR, LEG_MAX, TIGHT, fractal_highs
    C, H, L = P.close, P.high, P.low
    rng5 = H.rolling(5).max() - L.rolling(5).min()
    tight = rng5 / rng5.shift(5)
    Cv, Hv, Lv, ADRv, TIGHTv, ELIGv = C.values, H.values, L.values, P.adr.values, tight.values, P.elig.values
    hit = np.zeros(C.shape, bool)
    for j in range(C.shape[1]):
        h = Hv[:, j]
        fr_idx = np.flatnonzero(fractal_highs(h))
        if len(fr_idx) < 3:
            continue
        for a in range(len(fr_idx) - 2):
            hi_i = fr_idx[a]
            bounces = [fr_idx[b] for b in range(a + 1, len(fr_idx)) if fr_idx[b] <= hi_i + LEG_MAX]
            if len(bounces) < 2:
                continue
            bh = [h[x] for x in bounces]
            if not all(bh[k + 1] < bh[k] for k in range(len(bh) - 1)):
                continue
            last = bounces[-1]
            seg_lo_i = int(np.nanargmin(Lv[hi_i:last + 1, j])) + hi_i
            support = Lv[seg_lo_i, j]
            a_pct = ADRv[last, j]
            if not np.isfinite(a_pct) or a_pct <= 0:
                continue
            if (h[hi_i] - support) / (h[hi_i] * a_pct / 100) < LEG_ADR:
                continue
            if (bh[-1] - Lv[seg_lo_i, j]) / max(bh[-2] - Lv[seg_lo_i, j], 1e-9) >= 1.0:
                continue
            for i in range(last + 1, min(last + 1 + LEG_MAX, len(Cv) - 7)):
                if not np.isfinite(Cv[i, j]):
                    continue
                if Cv[i, j] > bh[-1]:
                    break
                if Cv[i, j] < support:
                    if ELIGv[i, j] and np.isfinite(TIGHTv[i, j]) and TIGHTv[i, j] <= TIGHT:
                        hit[i, j] = True
                    break
    m = pd.DataFrame(hit, index=C.index, columns=C.columns)
    return lambda _P: daily_signals(m, stop=P.high, side="short")


def earnings_patterns(P, raw):
    """run_delayed_earnings_study.py's five cells, verbatim, as (name, pattern, hold) tuples."""
    from lib.mysql_lib import _get_engine
    V = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(P.close.index)
    C, H, L = P.close, P.high, P.low
    ret = C.pct_change(fill_method=None)
    vrel = V / V.shift(1).rolling(50).mean()
    uphalf = (C - L) / (H - L).replace(0, np.nan) >= 0.5
    idx, cols = C.index, list(C.columns)
    colpos = {c: k for k, c in enumerate(cols)}
    E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
    E["raw_date"] = pd.to_datetime(E.raw_date)
    E = E[(E.raw_date >= idx[0]) & (E.raw_date <= idx[-1]) & E.ticker.isin(colpos)]
    react = []
    for r in E.itertuples(index=False):
        j = colpos[r.ticker]
        i0 = idx.searchsorted(r.raw_date)
        if i0 + 2 >= len(idx):
            continue
        cand = [i0, i0 + 1]
        rr = [ret.values[i, j] for i in cand]
        if not np.isfinite(rr).any():
            continue
        i = cand[int(np.nanargmax(np.abs(rr)))]
        rv = ret.values[i, j]
        good = (rv > 0) and (vrel.values[i, j] >= 1.5) and bool(uphalf.values[i, j])
        react.append((i, j, bool(good), bool(rv <= 0.04), float(rv)))
    R = pd.DataFrame(react, columns=["i", "j", "good", "muted", "rx"])
    print(f"{len(R):,} earnings reactions on {R.j.nunique()} names | good {R.good.mean():.0%}")

    def mask_from(rows):
        m = pd.DataFrame(False, index=idx, columns=cols)
        for i, j in rows:
            m.iat[i, j] = True
        return m

    out = []
    stop3 = L.shift(1).rolling(3).min()
    for lab, sub in (("good+MUTED", R[R.good & R.muted]), ("good+BIG", R[R.good & ~R.muted]), ("bad reaction", R[~R.good])):
        hit = mask_from([(int(x.i) + 1, int(x.j)) for x in sub.itertuples() if int(x.i) + 1 < len(idx)])
        out.append((f"earnings drift, {lab}", lambda _P, h=hit: daily_signals(h, stop=stop3, side="long"), 10))
    for lab, sub in (("good+MUTED", R[R.good & R.muted]), ("good+BIG", R[R.good & ~R.muted])):
        rows = []
        for x in sub.itertuples():
            i, j = int(x.i), int(x.j)
            hi = H.values[i, j]
            for k in range(i + 3, min(i + 21, len(idx) - 1)):
                c = C.values[k, j]
                if np.isfinite(c) and c > hi:
                    rows.append((k, j)); break
        hit = mask_from(rows)
        out.append((f"delayed bump after {lab} earnings", lambda _P, h=hit: daily_signals(h, stop=L, side="long"), 10))
    return out, E


def earnings_breakouts(Pb, brk, E):
    """Generic breakouts on the names with earnings dates, split by earnings in the prior 0-3 sessions vs none nearby."""
    idx = Pb.close.index
    names = [c for c in Pb.close.columns if c in set(E.ticker)]
    near = pd.DataFrame(False, index=idx, columns=Pb.close.columns)
    within10 = pd.DataFrame(False, index=idx, columns=Pb.close.columns)
    for r in E.itertuples(index=False):
        if r.ticker not in near.columns:
            continue
        i0 = idx.searchsorted(r.raw_date)
        near.iloc[i0:i0 + 4, near.columns.get_loc(r.ticker)] = True
        within10.iloc[max(i0 - 10, 0):i0 + 11, within10.columns.get_loc(r.ticker)] = True
    sub = brk[names].reindex(columns=Pb.close.columns).fillna(False)
    a = sub & near
    b = sub & ~within10
    return [("breakout 0-3d after earnings", lambda _P, m=a: daily_signals(m, stop=Pb.low, side="long"), 5),
            ("breakout, no earnings nearby (same names)", lambda _P, m=b: daily_signals(m, stop=Pb.low, side="long"), 5)]


# ----------------------------------------------------------------------------------------------- runner
def halves(name: str, arm: str) -> tuple[float, float]:
    T = pd.read_parquet(pt.REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet")
    return float(T[T.date < SPLIT][arm].mean()), float(T[T.date >= SPLIT][arm].mean())


def rerun(name: str, fn, hold: int, P, entry_at: str = "next_open", ledger_name: str | None = None) -> dict:
    print(f"\n\n################ {name} | hold {hold} | entry {entry_at} ################")
    tabs = {}
    for ctrl in ("post", "xname"):
        tabs[ctrl] = run_daily(name, fn, hold=hold, panel=P, ledger=False, entry_at=entry_at, control=ctrl)
    tp, tx = tabs["post"], tabs["xname"]
    if tp is None or len(tp) == 0 or "edge" not in tp:
        return dict(name=name, n=0)
    best = tp.edge.idxmax()
    h1, h2 = halves(name, best)
    row = tp.loc[best]
    beats_both = row.edge > 0 and tx.loc[best, "edge"] > 0
    passed = bool(beats_both and abs(row.t) >= 3 and h1 > 0 and h2 > 0)
    note = (f"RERUN {TODAY} of the 2026-09-18/19 row with honest controls; ctrl=post (timing); "
            f"xname ctrl {tx.loc[best, 'ctrl']:+.3f} edge {tx.loc[best, 'edge']:+.3f}; "
            f"bar = beats BOTH controls + halves + |t|>=3")
    append_ledger(name=ledger_name or name, timeframe="daily", n=int(row.n), best_arm=best, meanR=row.meanR,
                  ctrl=row.ctrl, edge=row.edge, t=row.t, half1=h1, half2=h2, passed=passed, note=note)
    out = dict(name=name, n=int(row.n), best_arm=best, meanR=row.meanR, win=row.win, t=row.t,
               post_ctrl=row.ctrl, post_edge=row.edge, xname_ctrl=tx.loc[best, "ctrl"], xname_edge=tx.loc[best, "edge"],
               half1=h1, half2=h2, passed=passed,
               # the best arm by raw meanR as well, so a reader can see if the "edge" arm is a losing arm
               top_arm=tp.meanR.idxmax(), top_meanR=tp.meanR.max(),
               top_post_edge=tp.loc[tp.meanR.idxmax(), "edge"], top_xname_edge=tx.loc[tp.meanR.idxmax(), "edge"])
    for a in DAILY_ARMS:
        out[f"{a}_meanR"] = tp.loc[a, "meanR"]; out[f"{a}_post"] = tp.loc[a, "ctrl"]; out[f"{a}_xname"] = tx.loc[a, "ctrl"]
    return out


def old_rows() -> pd.DataFrame:
    L = pd.read_csv(pt.LEDGER)
    L = L[(L.timeframe == "daily") & (L.tested <= "2026-09-19") & ~L.note.fillna("").str.contains("ctrl=post")]
    return L.drop_duplicates("name", keep="first").set_index("name")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="substring filter on the pattern name")
    ap.add_argument("--skip-earnings", action="store_true")
    args = ap.parse_args()

    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    P = load_panel()
    jobs: list[tuple[str, object, int, object, str]] = []      # name, fn, hold, panel, entry_at

    jobs.append(("in-play up mover (+4% on 2x vol)", in_play(P, raw, "long"), 5, P, "next_open"))
    jobs.append(("in-play down mover (-4% on 2x vol)", in_play(P, raw, "short"), 5, P, "next_open"))
    jobs.append(("Bouncy ball (Breitstein short)", bouncy_ball(P), 5, P, "next_open"))

    import run_hivol_gate_split as hv
    hi = hv.hivol_series(P, 0.80)
    for reg, want in (("HIGH", True), ("LOW", False)):
        jobs.append((f"20d breakout ADR>=3, {reg}-vol regime (panel p80, 1 ADR stop, hold 5)",
                     hv.arm_factory(P, hi, want, 1.0), 5, P, "next_open"))

    import run_boring_violent as bv
    jobs.append(("boring stock, violent move (drop >= 4x own ADR, ADR bottom tercile)", bv.pattern(P, "A", 4.0), 5, P, "next_open"))
    jobs.append(("violent move, any ADR (drop >= 4x own ADR)", bv.pattern(P, "B", 4.0), 5, P, "next_open"))

    import run_counter_trend_long as ct
    dolvol = raw.pivot(index="date", columns="ticker", values="dolvol").sort_index().reindex(P.close.index)
    ext, down, trig, vol2x = ct.masks(P, dolvol)
    for kind, label in (("A", "counter-trend long: >=3 ADR below 20 EMA + prior-bar-high break"),
                        ("B", "prior-bar-high break in a down leg, <3 ADR below 20 EMA (no extension gate)")):
        hit, st = ct.build(P, ext, down, trig, vol2x, kind, 3.0, "signal")
        jobs.append((label, lambda _P, h=hit, s=st: daily_signals(h, stop=s, side="long"), 5, P, "next_open"))

    import run_precision_tier_control as pc
    Pb, brk, prec = pc.build()
    jobs.append(("precision-tier breakout (house), next-open entry", lambda _P, m=prec: daily_signals(m, stop=Pb.low, side="long"), 5, Pb, "next_open"))
    jobs.append(("precision-tier breakout (house), next-open entry, hold 60", lambda _P, m=prec: daily_signals(m, stop=Pb.low, side="long"), 60, Pb, "next_open"))
    jobs.append(("precision-tier breakout (house), CLOSE entry, hold 60", lambda _P, m=prec: daily_signals(m, stop=Pb.low, side="long"), 60, Pb, "close"))

    if not args.skip_earnings:
        cells, E = earnings_patterns(P, raw)
        jobs += [(n, f, h, P, "next_open") for n, f, h in cells]
        jobs += [(n, f, h, Pb, "next_open") for n, f, h in earnings_breakouts(Pb, brk, E)]

    if args.only:
        jobs = [j for j in jobs if args.only.lower() in j[0].lower()]
    print(f"{len(jobs)} patterns to re-run")

    rows = []
    for name, fn, hold, panel, entry_at in jobs:
        try:
            rows.append(rerun(name, fn, hold, panel, entry_at))
        except Exception as e:                                   # keep going; report the failure in the summary
            print(f"!! {name}: {type(e).__name__}: {e}")
            rows.append(dict(name=name, n=0, error=f"{type(e).__name__}: {e}"))
    S = pd.DataFrame(rows).set_index("name")
    O = old_rows().reindex(S.index)
    S.insert(0, "old_meanR", O.meanR); S.insert(1, "old_month_ctrl", O.ctrl); S.insert(2, "old_edge", O.edge)
    S.insert(3, "old_best_arm", O.best_arm); S.insert(4, "old_n", O.n)
    S.to_csv(OUT / f"rerun_{TODAY}.csv")
    cols = ["old_n", "n", "old_best_arm", "old_meanR", "old_month_ctrl", "old_edge", "best_arm", "meanR", "post_ctrl",
            "post_edge", "xname_ctrl", "xname_edge", "t", "half1", "half2", "passed", "top_arm", "top_meanR",
            "top_post_edge", "top_xname_edge"]
    print("\n\n################ SUMMARY: old (month control) vs honest (post / xname) ################")
    print(S.reindex(columns=cols).round(3).to_string())
    print(f"\nwritten: {OUT / f'rerun_{TODAY}.csv'}")


if __name__ == "__main__":
    main()

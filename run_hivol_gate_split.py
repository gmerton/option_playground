#!/usr/bin/env python3
"""
Breitstein test 4: the high-volatility regime gate, as a SPLIT of the house breakout, not a new entry.

Spec: data/lance_breitstein/principles/high-volatility-playbook.md ("Harness spec"), pre-registered.

  signal      close > max(high of the prior 20 sessions)  AND  ADR >= 3  AND  elig      (long)
  stop        1 x ADR below the signal close (sweep: 2 x ADR) -- scale-free, so both arms carry the same
              number of ADRs of risk and any difference is the regime, not the stop width
  regime      cross-sectional median of per-name 20d realised vol (panel itself, no VIX needed);
              HIGH = above its own expanding trailing-252 pct-ile (0.80; sweep 0.70/0.90), point-in-time
  robustness  the same rule on the VIX close (data/cache/vix_daily.parquet)
  arms        the harness's five: stop_hold / t1R / t2R / trail_bar / ema20; hold 5 (sweep 20)
  control     harness: same name, random session, same month -> the control shares the regime
  ledger      ONLY the primary config (pct .80, 1 ADR, hold 5), one row per regime arm; sweeps report only

His claim: HIGH-vol half prefers the fast exit (t1R), LOW-vol half the slow ones (ema20 / trail_bar).
Our exit-timing result predicts the slow exit wins in both halves.

Usage:
  PYTHONPATH=src .venv/bin/python3 run_hivol_gate_split.py > data/studies/breitstein_tests/logs/hivol_gate_split_<date>.log
"""
from __future__ import annotations

import sys
import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals, load_panel, run_daily, DAILY_ARMS

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

TODAY = date.today().isoformat()
PRIMARY = dict(pct=0.80, k=1.0, hold=5)


def mkt_rv(P, win: int = 20) -> pd.Series:
    rv = P.close.pct_change(fill_method=None).rolling(win).std() * np.sqrt(252) * 100
    return rv.where(P.elig).median(axis=1)


def hivol_series(P, pct: float, src: str = "panel") -> pd.Series:
    """True/False per date; NaN where the trailing window is not yet defined (excluded from BOTH arms)."""
    if src == "panel":
        m = mkt_rv(P)
    else:
        v = pd.read_parquet(pt.REPO / "data/cache/vix_daily.parquet")
        m = v.set_index(pd.to_datetime(v.trade_date)).vix_close.reindex(P.close.index).ffill()
    thr = m.expanding(252).quantile(pct)
    hi = (m > thr).astype(float)
    hi[thr.isna() | m.isna()] = np.nan
    return hi


def breakout_mask(P):
    return (P.close > P.high.shift(1).rolling(20).max()) & (P.adr >= 3) & P.elig


def arm_factory(P, hi: pd.Series, want_high: bool, k: float):
    brk = breakout_mask(P)
    reg = hi.eq(1.0) if want_high else hi.eq(0.0)          # NaN regime -> in neither arm
    mask = brk & pd.DataFrame(np.repeat(reg.values[:, None], brk.shape[1], axis=1),
                              index=brk.index, columns=brk.columns)
    stop = P.close * (1 - k * P.adr / 100.0)
    return lambda _P: daily_signals(mask, stop=stop, side="long")


def compare(tabs: dict[str, pd.DataFrame], label: str) -> pd.DataFrame:
    """Side-by-side per-arm table: meanR / ctrl / edge / t for HIGH and LOW, plus the difference."""
    cols = {}
    for reg, tab in tabs.items():
        for c in ["meanR", "ctrl", "edge", "t", "win", "n"]:
            cols[f"{reg}_{c}"] = tab[c]
    out = pd.DataFrame(cols)
    out["diff_meanR(H-L)"] = out["HIGH_meanR"] - out["LOW_meanR"]
    out["diff_edge(H-L)"] = out["HIGH_edge"] - out["LOW_edge"]
    print(f"\n##### {label}: per-arm HIGH vs LOW #####")
    print(out.round(3).to_string())
    for reg, tab in tabs.items():
        print(f"  {reg}: best by meanR = {tab.meanR.idxmax()} ({tab.meanR.max():.3f}) | "
              f"best by edge = {tab.edge.idxmax()} ({tab.edge.max():+.3f})")
    return out


def run_config(P, pct: float, k: float, hold: int, src: str = "panel", ledger: bool = False) -> dict:
    hi = hivol_series(P, pct, src)
    share = hi.dropna().mean()
    print(f"\n\n================ {src} pct={pct} stop={k}ADR hold={hold} | regime defined "
          f"{hi.dropna().index.min().date()} -> {hi.dropna().index.max().date()}, HIGH share {100*share:.1f}% "
          f"of sessions ================")
    tabs = {}
    for reg, want in [("HIGH", True), ("LOW", False)]:
        name = f"20d breakout ADR>=3, {reg}-vol regime ({src} p{int(pct*100)}, {k:g} ADR stop, hold {hold})"
        note = (f"Breitstein test 4 (high-vol gate SPLIT, not a new entry); regime = cross-sectional median 20d RV "
                f"vs expanding-252 p{int(pct*100)}" if src == "panel" else
                f"Breitstein test 4 robustness; regime = VIX close vs expanding-252 p{int(pct*100)}")
        tabs[reg] = run_daily(name, arm_factory(P, hi, want, k), hold=hold, note=note, panel=P, ledger=ledger)
    return dict(pct=pct, k=k, hold=hold, src=src, share=share,
                cmp=compare(tabs, f"{src} p{int(pct*100)} / {k:g} ADR / hold {hold}"))


def main():
    P = load_panel()
    m = mkt_rv(P)
    print(f"panel {P.close.shape[0]} sessions x {P.close.shape[1]} names; market RV (ann. %, cross-sectional median) "
          f"p50 {m.median():.1f} p80 {m.quantile(.8):.1f} p90 {m.quantile(.9):.1f} max {m.max():.1f} on {m.idxmax().date()}")
    hi80 = hivol_series(P, 0.80)
    runs = hi80.dropna().astype(int)
    blocks = (runs != runs.shift()).cumsum()
    hb = runs[runs == 1].groupby(blocks).agg(["size"])
    spans = [(g.index.min().date(), g.index.max().date(), len(g)) for _, g in hi80[hi80 == 1].groupby(blocks[hi80 == 1])]
    print(f"HIGH-vol (p80) episodes: {len(spans)}; the {min(8, len(spans))} longest:")
    for s in sorted(spans, key=lambda x: -x[2])[:8]:
        print(f"   {s[0]} -> {s[1]}  ({s[2]} sessions)")

    results = []
    # primary: the only config that writes ledger rows
    results.append(run_config(P, **PRIMARY, ledger=True))
    # sweeps: pct, stop width, hold, VIX-based regime
    for pct in (0.70, 0.90):
        results.append(run_config(P, pct, 1.0, 5))
    results.append(run_config(P, 0.80, 2.0, 5))
    results.append(run_config(P, 0.80, 1.0, 20))
    results.append(run_config(P, 0.80, 1.0, 5, src="vix"))

    print("\n\n################ SUMMARY: best exit arm per half, every config ################")
    rows = []
    for r in results:
        c = r["cmp"]
        rows.append(dict(src=r["src"], pct=r["pct"], stop=f'{r["k"]:g} ADR', hold=r["hold"],
                         HIGH_best=c["HIGH_meanR"].idxmax(), HIGH_meanR=c["HIGH_meanR"].max(),
                         HIGH_ema20=c.loc["ema20", "HIGH_meanR"], HIGH_t1R=c.loc["t1R", "HIGH_meanR"],
                         HIGH_edge_best=c["HIGH_edge"].idxmax(), HIGH_n=int(c["HIGH_n"].max()),
                         LOW_best=c["LOW_meanR"].idxmax(), LOW_meanR=c["LOW_meanR"].max(),
                         LOW_ema20=c.loc["ema20", "LOW_meanR"], LOW_t1R=c.loc["t1R", "LOW_meanR"],
                         LOW_edge_best=c["LOW_edge"].idxmax(), LOW_n=int(c["LOW_n"].max())))
    S = pd.DataFrame(rows)
    print(S.round(3).to_string(index=False))
    S.to_csv(pt.REPO / f"data/studies/breitstein_tests/hivol_gate_split_summary_{TODAY}.csv", index=False)
    print(f"\nsummary csv: data/studies/breitstein_tests/hivol_gate_split_summary_{TODAY}.csv")


if __name__ == "__main__":
    main()

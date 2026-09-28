#!/usr/bin/env python3
"""
t-TEST OF THE LONG-SIDE VETOES: below the 200 SMA / 6-month return < -10% (pre-registered 2026-09-28, before the run;
queued 2026-09-24; Gabe: "Let's do 1 and 2").

WHY. The desk's long vetoes rest on a cohort table without t-stats (industry_rotation_detection_study.md section 8)
and an overlap-inflated RS-decile check (lowest decile -4.0pp at 60d, t -3.39). On 2026-09-28 we also found the
Trend Template ablation does NOT support "close > 150/200 SMA carries the weight" (c1/c2 retracted as redundant),
which the routine had cited. Before these vetoes block live trades, they need a real test.

VETOES (as of the breakout close, no look-ahead)
  V1  close below its 200-day SMA
  V2  6-month return (close / close 126 sessions earlier - 1) below -10%
POOL   house breakouts, the generic definition (ADR >= 3, 52-week range >= 17%, eligible, close >= the prior 15-session
       high on RVOL >= 1.1, upper-half close, MA stack >= 5 sessions, gap < 5%, day < 8%, prior close below the pivot)
       -- the trades the vetoes would actually block.
PRIMARY SAMPLE  the out-of-time 2010-01 -> 2019-09 period on liquid_panel_2009 (the vetoes were read off 2019-26
       data, so that period is not independent). SECONDARY: 2019-10 -> 2026-09 on the same panel.
OUTCOME  20-session forward % return from the breakout close, minus an ADR-MATCHED same-date benchmark (the eligible
       panel reweighted to the event's ADR decile), 10 bp per side. Secondary: 60 sessions; and the house trade itself
       (breakout-day-low stop on the close, 20-EMA close trail, 60-session cap) in %.
STATISTIC  per veto: excess of VETOED breakouts minus ALLOWED breakouts, OLS of excess on a veto dummy with standard
       errors clustered by entry date.
BAR   a veto is CERTIFIED only if, on the PRIMARY sample, vetoed - allowed <= 0 with t <= -3, both halves (split
      2015-01-01) negative, negative in a majority of years with >= 5 vetoed events, AND the 2019-26 sign agrees.
      2 vetoes -> Sidak |t| 2.24, but the house 3 governs. If vetoed breakouts do NOT underperform, the veto is
      costing trades: report how many breakouts it removes.
DESCRIPTIVE  panel-wide (all eligible name-days, non-overlapping 20-session dates): vetoed vs allowed ADR-matched
      excess -- does the veto describe weak stocks generally, even if it doesn't sort breakouts?
⚠ Survivor-biased panel (liquid as of 2026): vetoed names that later died are missing, which FLATTERS the vetoed
  group; a certified veto is therefore conservative, a null slightly optimistic for the vetoed side.
Local.

Run: PYTHONPATH=src .venv/bin/python3 run_veto_ttest.py   (log -> data/studies/logs/veto_ttest.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/veto_ttest.log"
COST = 0.0010
SAMPLES = {"PRIMARY 2010-01 -> 2019-09": ("2010-01-01", "2019-09-30", "2015-01-01"),
           "SECONDARY 2019-10 -> 2026-09": ("2019-10-01", "2026-09-30", "2023-01-01")}


def build():
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stack = stack_run(C, adr=adr)
    brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)).fillna(False)
    v1 = C < C.rolling(200, min_periods=200).mean()
    v2 = (C / C.shift(126) - 1) < -0.10
    e20 = C.ewm(span=20, adjust=False).mean()
    return C, L, e20, adr, elig, brk, {"V1 below 200 SMA": v1, "V2 6-month < -10%": v2}


def house_pct(Cv, Lv, E, i, j):
    entry, stop = Cv[i, j] * (1 + COST), Lv[i, j]
    end = min(i + 60, len(Cv) - 1); k = i
    for k in range(i + 1, end + 1):
        c = Cv[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or (np.isfinite(E[k, j]) and c < E[k, j]):
            break
    return 100 * (Cv[k, j] * (1 - COST) / entry - 1)


def adr_bench(fr_row, adr_row, elig_row):
    """Mean forward return of eligible names, by ADR decile (for matching)."""
    ok = elig_row & np.isfinite(fr_row) & np.isfinite(adr_row)
    if ok.sum() < 50:
        return None, None
    a = adr_row[ok]; cuts = np.nanpercentile(a, np.arange(10, 100, 10))
    dec = np.digitize(a, cuts)
    means = pd.Series(fr_row[ok]).groupby(dec).mean()
    return cuts, means


def clustered(y, x, groups):
    fit = sm.OLS(y, sm.add_constant(x.astype(float))).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return float(fit.params[1]), float(fit.tvalues[1])


def main():
    C, L, E, ADR, ELIG, BRK, VETO = build()
    Cv, Lv, Ev = C.values, L.values, E.values
    idx = C.index
    out = ["# Long-side veto t-test (pre-registration in the docstring)"]
    verdict = {}
    for lab, (a, b, split) in SAMPLES.items():
        rows = []
        for h in (20, 60):
            fr = (C.shift(-h) / C - 1).values
            m = BRK[(BRK.index >= a) & (BRK.index <= b)]
            off = idx.get_loc(m.index[0])
            ii, jj = np.where(m.values); ii = ii + off
            cache = {}
            for i, j in zip(ii, jj):
                if i + h >= len(idx) or not np.isfinite(fr[i, j]):
                    continue
                if i not in cache:
                    cache[i] = adr_bench(fr[i], ADR.values[i], ELIG.values[i])
                cuts, means = cache[i]
                if cuts is None or not np.isfinite(ADR.values[i, j]):
                    continue
                bm = means.get(int(np.digitize([ADR.values[i, j]], cuts)[0]), np.nan)
                rec = dict(h=h, date=idx[i], sym=C.columns[j], ex=100 * (fr[i, j] - bm) - 200 * COST,
                           **{k: bool(v.values[i, j]) for k, v in VETO.items()})
                if h == 20:
                    rec["house"] = house_pct(Cv, Lv, Ev, i, j)
                rows.append(rec)
        T = pd.DataFrame(rows)
        out.append(f"\n## {lab}: {T[T.h == 20].shape[0]:,} breakouts on {T[T.h == 20].date.nunique()} dates")
        for vk in VETO:
            for h in (20, 60):
                S = T[T.h == h].dropna(subset=["ex"])
                g = S.date.astype(str).factorize()[0]
                d, t = clustered(S.ex.values, S[vk].values, g)
                hs = S.date < split
                h1 = S[hs & S[vk]].ex.mean() - S[hs & ~S[vk]].ex.mean()
                h2 = S[~hs & S[vk]].ex.mean() - S[~hs & ~S[vk]].ex.mean()
                yr = S.groupby(S.date.dt.year).apply(lambda z: z[z[vk]].ex.mean() - z[~z[vk]].ex.mean() if z[vk].sum() >= 5 else np.nan).dropna()
                tag = "  *PRIMARY*" if (h == 20 and lab.startswith("PRIMARY")) else ""
                out.append(f"  {vk:18s} {h}d: vetoed n {int(S[vk].sum()):5d} ({100 * S[vk].mean():.0f}% of breakouts) excess "
                           f"{S[S[vk]].ex.mean():+.2f}% vs allowed {S[~S[vk]].ex.mean():+.2f}% -> diff {d:+.2f}pp t {t:+.2f} "
                           f"halves {h1:+.2f}/{h2:+.2f} yrs- {(yr < 0).sum()}/{len(yr)}{tag}")
                if h == 20:
                    verdict.setdefault(vk, {})[lab] = (d, t, h1, h2, (yr < 0).sum(), len(yr))
            S = T[T.h == 20]
            d, t = clustered(S.house.values, S[vk].values, S.date.astype(str).factorize()[0])
            out.append(f"  {vk:18s} house trade %: vetoed {S[S[vk]].house.mean():+.2f}% vs allowed {S[~S[vk]].house.mean():+.2f}% -> {d:+.2f}pp t {t:+.2f}")
        T.to_csv(REPO / f"data/studies/logs/veto_ttest_{'primary' if lab.startswith('PRIMARY') else 'secondary'}.csv", index=False)
    # descriptive: panel-wide
    out.append("\n## DESCRIPTIVE panel-wide (all eligible name-days, non-overlapping 20-session dates, ADR-matched)")
    fr = (C.shift(-20) / C - 1).values
    for lab, (a, b, split) in SAMPLES.items():
        ds = [k for k in range(len(idx)) if a <= str(idx[k].date()) <= b][::20]
        for vk, v in VETO.items():
            diffs = []
            for i in ds:
                if i + 20 >= len(idx):
                    continue
                cuts, means = adr_bench(fr[i], ADR.values[i], ELIG.values[i])
                if cuts is None:
                    continue
                ok = ELIG.values[i] & np.isfinite(fr[i]) & np.isfinite(ADR.values[i])
                dec = np.digitize(ADR.values[i][ok], cuts)
                ex = fr[i][ok] - means.reindex(dec).values
                vv = v.values[i][ok]
                if vv.sum() >= 5 and (~vv).sum() >= 5:
                    diffs.append(100 * (ex[vv].mean() - ex[~vv].mean()))
            dd = np.array(diffs)
            out.append(f"  {lab[:9]} {vk:18s}: vetoed - allowed {dd.mean():+.2f}pp t {dd.mean() / dd.std(ddof=1) * np.sqrt(len(dd)):+.2f} ({len(dd)} dates)")
    out.append("\nBAR (per veto): PRIMARY diff <= 0 with t <= -3, both halves < 0, majority of years < 0, 2019-26 sign agrees")
    for vk, r in verdict.items():
        d, t, h1, h2, yn, ny = r["PRIMARY 2010-01 -> 2019-09"]; d2 = r["SECONDARY 2019-10 -> 2026-09"][0]
        ok = d <= 0 and t <= -3 and h1 < 0 and h2 < 0 and yn > ny / 2 and d2 <= 0
        out.append(f"  {vk}: {'CERTIFIED' if ok else 'NOT CERTIFIED'} (primary {d:+.2f}pp t {t:+.2f}; 2019-26 {d2:+.2f}pp)")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

#!/usr/bin/env python3
"""
HYB-B parameter neighbourhood + optimisation-aware null ([WL-2], method-queue #2; pre-registered 2026-09-23).

HYB-B (universe test 2026-09-21, PARKED): Trend Template core at ADDV >= $100M and ADR >= 4% -> 20-day forward
return of members vs the whole eligible panel on the same (non-overlapping, every 20th session) dates: +1.79%,
t 2.6, beat both parents in both halves. Question: is that a PLATEAU or a SPIKE, and what is it worth once the choice
of thresholds is charged?

Grid (pre-registered, from memory project_method_upgrades_queue #2): ADR >= {3.5, 4.0, 4.5} x ADDV >= {$75M, $100M,
$150M} = 9 cells. Statistic per cell = t of the per-date ADR-MATCHED excess (members' mean 20d return minus the eligible
panel reweighted to the members' ADR-decile mix, as run_trend_template_ablation.per_date_returns; this is the column the
PARKED +1.79 / t 2.60 came from), dates with >= 5 members. Raw excess is reported alongside.
Null = on each date, random names drawn WITHIN each ADR decile in the members' decile counts (selection beyond ADR = 0).
Keys are shared across cells (one uniform per date x name per permutation), so overlapping cells stay correlated.
p_opt = share of 2,000 permutations whose max-over-9-cells t >= the observed max.
Plateau = share of cells with t >= 2 and both halves (split 2023-01-01) positive; plus median/best t.
Bar: the best cell must clear p_opt < 0.003 to move HYB-B off PARKED. A plateau with p_opt >= 0.003 stays PARKED;
a spike is downgraded.

Run: PYTHONPATH=src .venv/bin/python3 run_hybb_neighbourhood.py   (log -> data/studies/logs/hybb_neighbourhood.log)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import run_precision_tier_control as pc
from lib.studies import pattern_test as pt

START, SPLIT, H, PERMS, P_BAR = "2020-01-01", "2023-01-01", 20, 2000, 0.003
LOG = pt.REPO / "data/studies/logs/hybb_neighbourhood.log"
GRID = [(a, v) for a in (3.5, 4.0, 4.5) for v in (75e6, 100e6, 150e6)]


def components(P, raw):
    """Verbatim from run_universe_test.build_masks (tt_core, addv, adr), shifted one session."""
    C, Hh, L = P.close, P.high, P.low
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex(index=C.index, columns=C.columns)
    dolvol = piv("dolvol")
    sma50, sma150, sma200 = (C.rolling(n, min_periods=n).mean() for n in (50, 150, 200))
    hi252 = Hh.rolling(252, min_periods=200).max()
    lo252 = L.rolling(252, min_periods=200).min()
    addv = dolvol.rolling(50, min_periods=50).mean()
    rs = 2 * C / C.shift(63) + C / C.shift(126) + C / C.shift(189) + C / C.shift(252)
    rs_pct = rs.where(P.elig).rank(axis=1, pct=True) * 100
    rising200 = sma200 > sma200.shift(20)
    adr = (Hh / L - 1).rolling(20).mean() * 100
    tt_core = ((C > sma150) & (C > sma200) & (sma150 > sma200) & rising200 & (sma50 > sma150) & (C > sma50)
               & (C >= 1.30 * lo252) & (C >= 0.75 * hi252) & (rs_pct >= 70))
    sh = lambda x: x.shift(1)
    return (sh(tt_core & P.elig).fillna(False).astype(bool), sh(addv), sh(adr))


def main():
    P, _brk, _prec = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    core, addv, adr = components(P, raw)
    C = P.close
    base = P.elig.shift(1).fillna(False).astype(bool)
    fr = C.shift(-H) / C - 1
    dates = C.index[C.index >= START][::H]
    dates = dates[dates <= C.index[-1 - H]]
    F = fr.loc[dates].values
    B = base.loc[dates].values & np.isfinite(F)
    panel = np.nanmean(np.where(B, F, np.nan), axis=1)
    first = np.asarray(dates < pd.Timestamp(SPLIT))
    M = {}
    for a, v in GRID:
        m = (core & (addv >= v) & (adr >= a)).loc[dates].values & B
        M[(a, v)] = m

    def tstat(x):
        x = x[np.isfinite(x)]
        return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan

    # ADR deciles on each date (ranked across all names, as the ablation does); benchmark = decile means reweighted
    dec = adr.loc[dates].rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int).values
    dec = np.where(B, dec, -1)
    decmean = np.full((len(dates), 10), np.nan)
    for d in range(10):
        decmean[:, d] = np.nanmean(np.where(dec == d, F, np.nan), axis=1)

    def matched(m):
        cnt = m.sum(axis=1)
        cd = np.stack([(m & (dec == d)).sum(axis=1) for d in range(10)], axis=1)
        w = cd / np.maximum(cnt, 1)[:, None]
        bench = np.nansum(w * np.nan_to_num(decmean), axis=1) / np.maximum(np.sum(w * np.isfinite(decmean), axis=1), 1e-12)
        mem = np.nanmean(np.where(m, F, np.nan), axis=1)
        return np.where(cnt >= 5, mem - bench, np.nan), np.where(cnt >= 5, mem - panel, np.nan), cd

    rows, CD = [], {}
    for (a, v), m in M.items():
        ex, raw_ex, cd = matched(m)
        CD[(a, v)] = cd
        rows.append(dict(adr=a, addv_m=v / 1e6, dates=int(np.isfinite(ex).sum()), members_med=float(np.median(m.sum(axis=1))),
                         excess=np.nanmean(ex) * 100, t=tstat(ex), h1=np.nanmean(ex[first]) * 100,
                         h2=np.nanmean(ex[~first]) * 100, raw_excess=np.nanmean(raw_ex) * 100, raw_t=tstat(raw_ex)))
    S = pd.DataFrame(rows)
    obs = S.t.max()
    # permutation: within each (date, ADR decile), the c lowest keys stand in for that decile's c members
    di, ni = np.meshgrid(np.arange(len(dates)), np.arange(F.shape[1]), indexing="ij")
    null = np.empty(PERMS)
    for p in range(PERMS):
        u = pt._mix64((di.astype(np.int64) * 1_000_003 + ni) * 7_919 + (p + 1) * 0x5851F42D)
        key = np.where(dec >= 0, dec + u, np.inf)                  # sorts by decile, then by u inside it
        order = np.argsort(key, axis=1)
        sdec = np.take_along_axis(dec, order, axis=1)
        rank = np.empty_like(order)
        for r in range(len(dates)):
            starts = np.searchsorted(sdec[r], np.arange(-1, 10))       # sdec has -1 at the end (inf keys) -> ignore
            pos = np.arange(order.shape[1])
            grp_start = np.zeros(order.shape[1], dtype=np.int64)
            for d in range(10):
                lo = np.searchsorted(sdec[r], d, side="left"); hi = np.searchsorted(sdec[r], d, side="right")
                grp_start[lo:hi] = lo
            rank[r, order[r]] = pos - grp_start
        best = -np.inf
        for k, cd in CD.items():
            need = np.take_along_axis(cd, np.clip(dec, 0, 9), axis=1)
            m = (dec >= 0) & (rank < need)
            ex, _, _ = matched(m)
            best = max(best, tstat(ex))
        null[p] = best
    p_opt = (np.sum(null >= obs) + 1) / (PERMS + 1)
    good = (S.t >= 2) & (S.h1 > 0) & (S.h2 > 0)
    print(S.round(3).to_string(index=False))
    print(f"\nobserved max t {obs:.2f} | p_opt {p_opt:.4f} (null max-t p50 {np.median(null):.2f}, p95 "
          f"{np.quantile(null, .95):.2f}, p99 {np.quantile(null, .99):.2f})")
    print(f"plateau share (t >= 2 & both halves > 0): {good.mean():.0%} | median/best t {S.t.median() / obs:.2f}")
    S.to_csv(pt.REPO / "data/studies/hybb_neighbourhood_2026-09-23.csv", index=False)
    return S, p_opt, good.mean(), null


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read()[-2500:])

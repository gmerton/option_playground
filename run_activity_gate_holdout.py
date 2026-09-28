#!/usr/bin/env python3
"""
BREAKOUT-ACTIVITY GATE on the UNUSED 2010-2019 HOLDOUT: "press when the market is producing working breakouts"
(pre-registered 2026-09-27, before any run; Gabe: "yes, pre-register both"; this is item (2) of AUDIT STEP 3 in
TEST_INDEX section 10, list A of audit_top_down_2026-09-25.md. Run 2026-09-27 on Gabe's "go ahead and run those tests".)

WHY. The top traders' years are made in a few hot months at heavy size, and our book has the same shape: +0.45R
trade-weighted but ~0 month-weighted; the top 10% of months give 68% of positive R. Pressing on one's OWN results
fails (adaptive-trader sim 2026-09-27 NULL; WL-2b rho -0.01). The MARKET-level version was PARKED on 2019-26:
run_breakout_activity_gate.py (2026-09-22) found the 5-session precision-tier breakout count, as a percentile of its
own trailing 252 sessions, sorted outcomes Q1 +0.06R -> Q5 +0.86R, top - bottom +0.81R, t 2.59, both halves positive;
but raw counts were flat-to-inverted and the 10/20-session neighbours weak (no plateau). The 2010-01 -> 2019-09
period of liquid_panel_2009 has never been used for it: an out-of-time holdout.

FROZEN from the original, not re-fit: the precision-tier signal and trade exactly as run_breakout_activity_gate.py
(close entry; stop = min(day low, close x 0.98); exit on a close under the stop or the 20 EMA; 60-session cap;
5 bp/side; R capped at +/-20); the signal cnt5_pct = the count of precision-tier breakouts across the eligible
universe in the 5 sessions BEFORE entry, as a percentile of its trailing 252 sessions; quintile cuts computed on
the holdout itself (the gate is a percentile, so no level is carried over).
HOLDOUT  entries 2010-01-01 -> 2019-09-30 on data/cache/liquid_panel_2009.parquet (the 2019-10+ data is the
         original sample and is NOT re-scored here).
PRIMARY  top-minus-bottom quintile of cnt5_pct, mean R, t on entry-date cluster means.
         BAR: t >= 3 (a second look at a parked result is charged: the house bar, not the original 2), both halves
         (split 2015-01-01) positive, AND positive in a majority of years; AND the plateau check the original failed:
         cnt10_pct and cnt20_pct top-minus-bottom must have the same sign with t >= 1.5.
ALSO (declared) the audit's two controls: vs same-date other-name random entries (xname) and vs the same name on a
         later random session (post); % return next to R; per year; share of total R in the top quintile.
PRESS VERSION (descriptive, only if the primary passes): a book that runs 1.5x size in the top quintile and 0.5x in
         the bottom vs flat size -- terminal wealth, max drawdown, using the adaptive-trader event simulator.
⚠ Survivor-biased panel (liquid as of 2026): flatters breakouts in every quintile alike; the gate is a relative sort.
PRIOR  low-moderate: the original had no plateau, and the market-state gates tried since (index filter, breadth
       deferral, distribution days) were all NULL.
Local.

Run (when approved): PYTHONPATH=src .venv/bin/python3 run_activity_gate_holdout.py
"""
import sys
import warnings
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/activity_gate_holdout.log"
COST, CAP, FLOOR = 0.0005, 20.0, 0.02
HO_START, HO_END, SPLIT, SEED = "2010-01-01", "2019-09-30", "2015-01-01", 20260927


def trade_R(Cv, Lv, E, i, j):
    N_ = len(Cv)
    entry = Cv[i, j]; stop = min(Lv[i, j], entry * (1 - FLOOR)); risk = entry - stop
    if not (np.isfinite(entry) and np.isfinite(stop)) or risk <= 0 or i + 12 >= N_:
        return np.nan, np.nan
    for k in range(i + 1, min(i + 61, N_)):
        c = Cv[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or c < E[k, j]:
            break
    else:
        k = min(i + 60, N_ - 1)
    c = Cv[k, j]
    return float(np.clip((c * (1 - COST) - entry * (1 + COST)) / risk, -CAP, CAP)), 100 * (c * (1 - COST) / (entry * (1 + COST)) - 1)


def main():
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
    prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)).fillna(False)
    daily_cnt = prec.sum(axis=1)
    sig = pd.DataFrame(index=C.index)
    for N in (5, 10, 20):
        sig[f"cnt{N}"] = daily_cnt.rolling(N).sum().shift(1)
        sig[f"cnt{N}_pct"] = sig[f"cnt{N}"].rolling(252, min_periods=150).apply(lambda w: (w[-1] > w[:-1]).mean() * 100, raw=True)
    Cv, Lv, E = C.values, L.values, e20.values
    EL = elig.fillna(False).values; PR = prec.values
    rng = np.random.default_rng(SEED)
    m = prec[(prec.index >= HO_START) & (prec.index <= HO_END)]
    off = C.index.get_loc(m.index[0])
    ii, jj = np.where(m.values); ii = ii + off
    rows = []
    for i, j in zip(ii, jj):
        R, pc = trade_R(Cv, Lv, E, i, j)
        if not np.isfinite(R):
            continue
        cand = np.flatnonzero(EL[i] & ~PR[i]); cand = cand[cand != j]
        xs = [trade_R(Cv, Lv, E, i, c)[0] for c in rng.choice(cand, size=min(3, len(cand)), replace=False)] if len(cand) else []
        xs = [x for x in xs if np.isfinite(x)]
        ps = []
        for _ in range(3):
            k = i + int(rng.integers(20, 121))
            if k + 12 < len(Cv):
                r2 = trade_R(Cv, Lv, E, k, j)[0]
                if np.isfinite(r2):
                    ps.append(r2)
        d = C.index[i]
        rows.append(dict(date=d, sym=C.columns[j], R=R, pct=pc, xname=np.mean(xs) if xs else np.nan,
                         post=np.mean(ps) if ps else np.nan, **sig.loc[d].to_dict()))
    T = pd.DataFrame(rows).dropna(subset=["cnt20_pct"])
    out = [f"# Breakout-activity gate, 2010-19 HOLDOUT (pre-registration in the docstring)",
           f"{len(T):,} precision-tier trades {T.date.min().date()} -> {T.date.max().date()} on {T.date.nunique()} dates; "
           f"pooled mean R {T.R.mean():+.3f}, % {T.pct.mean():+.2f}"]

    def by_q(col, y="R"):
        q = pd.qcut(T[col].rank(method="first"), 5, labels=False)
        g = T.assign(q=q).groupby("q")[y]
        j2 = T.assign(q=q); j2 = j2[j2.q.isin([0, 4])].dropna(subset=[y])
        fit = sm.OLS(j2[y].values, sm.add_constant((j2.q == 4).astype(float).values)).fit(
            cov_type="cluster", cov_kwds={"groups": j2.date.astype(str).factorize()[0]})
        h = T.date < SPLIT
        h1 = T[(q == 4) & h][y].mean() - T[(q == 0) & h][y].mean()
        h2 = T[(q == 4) & ~h][y].mean() - T[(q == 0) & ~h][y].mean()
        yr = T.assign(q=q).groupby(T.date.dt.year).apply(lambda g2: g2[g2.q == 4][y].mean() - g2[g2.q == 0][y].mean())
        return g.mean(), float(fit.params[1]), float(fit.tvalues[1]), h1, h2, yr

    res = {}
    for col in ("cnt5_pct", "cnt10_pct", "cnt20_pct"):
        means, dd, t, h1, h2, yr = by_q(col)
        res[col] = (dd, t, h1, h2, yr)
        out.append(f"\n{col}{' *PRIMARY*' if col == 'cnt5_pct' else ''}: " + "  ".join(f"Q{k + 1} {v:+.2f}" for k, v in means.items())
                   + f"\n   top-bottom {dd:+.3f}R  t {t:+.2f}  halves {h1:+.2f} / {h2:+.2f}  years + {(yr > 0).sum()}/{yr.notna().sum()}")
    T["ex_x"], T["ex_p"] = T.R - T.xname, T.R - T.post
    for lab, y in (("excess vs xname", "ex_x"), ("excess vs post", "ex_p"), ("% return", "pct")):
        means, dd, t, h1, h2, yr = by_q("cnt5_pct", y)
        out.append(f"   cnt5_pct on {lab}: top-bottom {dd:+.3f}  t {t:+.2f}  halves {h1:+.2f} / {h2:+.2f}")
    dd, t, h1, h2, yr = res["cnt5_pct"]
    plateau = all(np.sign(res[c][0]) == np.sign(dd) and res[c][1] * np.sign(dd) >= 1.5 for c in ("cnt10_pct", "cnt20_pct"))
    ok = t >= 3 and h1 > 0 and h2 > 0 and (yr > 0).sum() > yr.notna().sum() / 2 and plateau
    out.append("   per year (cnt5_pct top-bottom R): " + " ".join(f"{y}:{v:+.2f}" for y, v in yr.items()))
    out.append(f"\nBAR: {'PASS' if ok else 'NOT MET'} (t >= 3, both halves > 0, majority of years, plateau {plateau})")
    T.to_csv(REPO / "data/studies/activity_gate_holdout_2026-09-27.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

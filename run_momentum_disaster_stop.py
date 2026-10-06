#!/usr/bin/env python3
"""
1-ADR DISASTER STOP on the certified 12-1 momentum sleeve (pre-registered 2026-10-05, BEFORE any outcome was computed;
Gabe: "I think we need at least a disaster stop for the momentum sleeve as well").

WHY NEW. The certified sleeve (run_momentum_portfolio.py, run_momentum_buffer.py T20-B = the live book) has NO stop.
The ledger varied lookback, skip, bucket, book size, buffer, vol scaling, residual, trend filter, entry timing, PTH and
vehicle -- never a per-name stop. The house disaster stop (stop_definitions.md: 1.0 ADR below the latest close, resting,
executed intraday, recomputed daily) went live on the sleeve names 2026-10-05, so its cost/benefit on THIS book is owed.

BOOK     T20-B exactly as run_momentum_buffer.simulate: month-end formation, 12-1 score close(t-21)/close(t-252)-1, keep a
         held name while eligible and in the top QUINTILE, refill to 20 from the top; equal weight; 10 bp per side on
         turnover. Membership is identical in both arms -- a stopped name sits in CASH (0) until the next month-end and is
         re-bought then if still in the book (that re-buy and the stop's own sale are charged 10 bp each).
ARMS     NONE  hold to the month-end (the certified rule).
         STOP  each session k inside the holding month: level = close(k-1) x (1 - ADR(k-1)), ADR = mean(high/low - 1) over
               the 20 sessions before k-1 (the exact live formula, verified to the cent vs the 2026-10-04 orders).
               open(k) <= level -> exit at the OPEN (gap); else low(k) <= level -> exit AT the level. 10 bp slippage.
DATA
  PRIMARY  liquid_panel_2009 (adjusted OHLCV; harness eligibility ADDV >= $50M, px >= $5). ⚠ SURVIVORS: the names a stop
           would save most (delisted crashers) are missing, so the panel UNDERSTATES any stop benefit -- declared.
  CHECK    survivorship-free chain_spot closes (the certification data; CLOSES ONLY): close-judged proxy -- exit at close(k)
           when close(k) < close(k-1) x (1 - c x ADRp(k-1)), ADRp = 20-session mean |close-to-close return|, c = the
           panel's median ratio mean(H/L-1) / mean|c2c| (calibrated on the panel, printed). Direction check only.
PRIMARY  d = STOP - NONE monthly book return (pp), Newey-West t (lag 3), formations 2011-01 -> 2026-01 (as certified).
         HELPS if t >= 3, both halves (2018-01) > 0, majority of years > 0; COSTS if t <= -3 with halves/years < 0;
         otherwise NULL (no measurable return effect). Co-reported RISK (descriptive, no bar): maxDD, worst 5 months,
         CAGR, Sharpe of each arm; stop-fire rate per name-day; share of months with >= 1 fire; gap-fill share.
         The pre-declared reading: a NULL with a lower maxDD = keep the stop as insurance; COSTS = the stop is paid for in
         return and the drawdown change must justify it.
Exploratory (Sidak k = 3, no verdict): 1.5 ADR, 2.0 ADR stops; D1 (top decile, plain) with the 1-ADR stop.
Prior: momentum's worst months are rebounds of last year's LOSERS (2009-04, 2020-04), which a long-only stop cannot help;
       per-name crashes inside the winner book are what it can catch. Lean: NULL to mildly COSTS, lower drawdown.

Run: PYTHONPATH=src:. .venv/bin/python3 run_momentum_disaster_stop.py   (log -> data/studies/logs/momentum_disaster_stop.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_momentum_portfolio as M
from lib.studies.pattern_test import load_panel

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_disaster_stop.log"
LOOKBACK, SKIP, SLIP = 252, 21, 0.001


def books(C: pd.DataFrame, elig: pd.DataFrame, plain_decile: bool = False):
    """Yield (a, b, names held over (a, b], turnover) for T20-B (or plain D1), as in run_momentum_buffer.simulate."""
    idx, Cv, E = C.index, C.values, elig.values
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    hold: set = set()
    for a, b in zip(me[:-1], me[1:]):
        if a - LOOKBACK < 0:
            continue
        score = Cv[a - SKIP] / Cv[a - LOOKBACK] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        names = np.flatnonzero(ok)
        if len(names) < 50:
            continue
        order = names[np.argsort(-score[names])]
        if plain_decile:
            new = set(order[:int(np.ceil(len(names) * 0.10))])
        else:
            q20 = set(order[:int(np.ceil(len(names) * 0.20))])
            keep = {j for j in hold if j in q20}
            new = keep | set([j for j in order if j not in keep][:max(20 - len(keep), 0)])
        to = 1 - len(new & hold) / max(len(new), 1)
        hold = new
        yield a, b, sorted(new), to


def name_month(j, a, b, Cv, Ov, Lv, Av, last, mult, close_only):
    """(NONE return, STOP return, fired, gap) for name j held close(a) -> close(b)."""
    end = min(b, last[j])
    if end <= a or not np.isfinite(Cv[a, j]):
        return np.nan, np.nan, False, False
    base = Cv[end, j] / Cv[a, j] - 1
    for k in range(a + 1, end + 1):
        lvl = Cv[k - 1, j] * (1 - mult * Av[k - 1, j])
        if not np.isfinite(lvl):
            continue
        if close_only:
            if Cv[k, j] < lvl:
                return base, Cv[k, j] * (1 - SLIP) / Cv[a, j] - 1, True, False
        elif np.isfinite(Ov[k, j]) and Ov[k, j] <= lvl:
            return base, Ov[k, j] * (1 - SLIP) / Cv[a, j] - 1, True, True
        elif np.isfinite(Lv[k, j]) and Lv[k, j] <= lvl:
            return base, lvl * (1 - SLIP) / Cv[a, j] - 1, True, False
    return base, base, False, False


def run(C, O, L, A, elig, mult=1.0, close_only=False, plain_decile=False) -> pd.DataFrame:
    Cv, Ov, Lv, Av = C.values, (O.values if O is not None else None), (L.values if L is not None else None), A.values
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                     for j in range(Cv.shape[1])])
    rows, stopped_prev = [], set()
    for a, b, names, to in books(C, elig, plain_decile):
        res = [name_month(j, a, b, Cv, Ov, Lv, Av, last, mult, close_only) for j in names]
        R = pd.DataFrame(res, index=names, columns=["none", "stop", "fired", "gap"]).dropna(subset=["none"])
        n = max(len(R), 1)
        rebuy = len([j for j in names if j in stopped_prev]) / n
        fired = set(R.index[R.fired])
        rows.append(dict(month=C.index[b].to_period("M"),
                         NONE=R.none.mean() - 2 * M.COST * to,
                         STOP=R.stop.mean() - 2 * M.COST * to - M.COST * (len(fired) / n + rebuy),
                         fires=len(fired), gaps=int(R.gap.sum()), names=len(R), days=len(R) * (b - a)))
        stopped_prev = fired
    return pd.DataFrame(rows).set_index("month")


def stats(r: pd.Series) -> dict:
    cum = (1 + r).cumprod()
    yrs = len(r) / 12
    return dict(mo=100 * r.mean(), cagr=100 * (cum.iloc[-1] ** (1 / yrs) - 1), sharpe=r.mean() / r.std() * np.sqrt(12),
                maxdd=100 * (1 - cum / cum.cummax()).max(), worst=", ".join(f"{p}:{100 * v:+.1f}" for p, v in r.nsmallest(5).items()))


def report(P: pd.DataFrame, label: str, primary: bool = False) -> None:
    d = (P.STOP - P.NONE) * 100
    h = P.index < pd.Period(M.SPLIT, "M")
    yd = d.groupby(d.index.year).sum()
    t = M.nw_t(d)
    verdict = ("HELPS" if t >= 3 and d[h].mean() > 0 and d[~h].mean() > 0 and (yd > 0).sum() > len(yd) / 2 else
               "COSTS" if t <= -3 and d[h].mean() < 0 and d[~h].mean() < 0 and (yd < 0).sum() > len(yd) / 2 else "NULL")
    print(f"\n## {label}{'  <- PRIMARY' if primary else ''}")
    print(f"STOP - NONE {d.mean():+.3f}pp/mo  t_NW {t:+.2f}  halves {d[h].mean():+.3f}/{d[~h].mean():+.3f}  "
          f"years + {(yd > 0).sum()}/{len(yd)}  -> {verdict if primary else '(exploratory)'}")
    for k in ("NONE", "STOP"):
        s = stats(P[k])
        print(f"  {k:4s} {s['mo']:+.2f}%/mo  CAGR {s['cagr']:+.1f}%  Sharpe {s['sharpe']:.2f}  maxDD {s['maxdd']:.1f}%  worst5 {s['worst']}")
    print(f"  fires: {P.fires.sum():,} of {P.names.sum():,} name-months ({100 * P.fires.sum() / P.names.sum():.1f}%), "
          f"{100 * P.fires.sum() / P.days.sum():.2f}% of name-days; months with >= 1 fire {100 * (P.fires > 0).mean():.0f}%; "
          f"gap fills {100 * P.gaps.sum() / max(P.fires.sum(), 1):.0f}% of fires")
    print("  per year (pp): " + " ".join(f"{y}:{v:+.1f}" for y, v in yd.items()))


def main():
    Pn = load_panel("data/cache/liquid_panel_2009.parquet")
    print(f"# 1-ADR disaster stop on the 12-1 momentum sleeve (T20-B); formations {M.START} -> {M.END}")
    P1 = run(Pn.close, Pn.open, Pn.low, Pn.adr / 100, Pn.elig)
    report(P1, "T20-B, 1.0 ADR, liquid_panel_2009 OHLC (intraday, gap at open)", primary=True)
    P1.to_csv(REPO / "data/studies/logs/momentum_disaster_stop_monthly.csv")

    print("\n# exploratory (Sidak k = 3, |t| >= 2.39; no verdict)")
    for m in (1.5, 2.0):
        report(run(Pn.close, Pn.open, Pn.low, Pn.adr / 100, Pn.elig, mult=m), f"T20-B, {m} ADR, panel")
    report(run(Pn.close, Pn.open, Pn.low, Pn.adr / 100, Pn.elig, plain_decile=True), "D1 plain, 1.0 ADR, panel")

    import run_dip_survivorship as DS
    C, V = DS.adjust_and_clean(DS.pull())
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    rng = (Pn.high / Pn.low - 1).rolling(250).mean()
    c2c = Pn.close.pct_change().abs().rolling(250).mean()
    cal = float((rng / c2c).median().median())
    Ap = C.pct_change().abs().rolling(20).mean() * cal
    print(f"\n# CHECK on survivorship-free chain_spot closes (close-judged proxy; calibration c = {cal:.2f})")
    report(run(C, None, None, Ap, liq, close_only=True), "T20-B, 1.0 ADR proxy, chain_spot incl. delisted")


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

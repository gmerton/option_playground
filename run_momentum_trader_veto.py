#!/usr/bin/env python3
"""
"TRADER VETO" on the 12-1 momentum sleeve: keep the 12-1 rank, but don't hold a name a trader would reject
(pre-registered 2026-10-06, BEFORE any outcome was computed).

Origin: Gabe 2026-10-05/06 -- NESR (-26% in 6 sessions, no news) and WDC (-45% off its June high, -25% over 3 months,
-11% under its 50-day, yet 12-1 +256%): "WDC is just not healthy ... there must be a middle ground" between pure 12-1 and
insisting on closeness to the 52-week high.
WHY NEW. The ledger RANKED on 52-week-high proximity (H1 vs 12-1 -0.83pp t -3.24; composite 12-1+PTH -0.48 t -2.55) and
tested skip length, entry-timing waits, vol scaling, a market trend filter, buffers and vehicles. It never applied a
binary per-name HEALTH VETO with refill from the next ranks. A veto touches only the tail of broken names; a rank
composite reshuffles the whole book -- different rules.

DATA     PRIMARY survivorship-free chain_spot closes (run_dip_survivorship.pull/adjust_and_clean), the certification data;
         eligibility = 50-session mean option volume >= 1,000 and px >= $5 (as certified). Every veto uses closes only.
         SECONDARY liquid_panel_2009 (survivors; harness eligibility), same rules -- direction check, no verdict.
BOOK     T20-B as in run_momentum_buffer.simulate (keep a held name while in the top quintile, refill to 20 from the top),
         month-end formations 2011-01 -> 2026-01, equal weight, hold to the next month-end, 10 bp per side on turnover,
         delisted names exit at their last close.
VETO (evaluated at each formation close t, on every candidate -- held or new; a vetoed held name is SOLD; refill skips
         vetoed names and continues down the ranks):
   DT  "3-month downtrend": close(t) < SMA50(t) AND close(t) / close(t-63) - 1 < 0   (both -- a pullback alone is not it)
   CR  "recent crash":      close(t) / max(close t-10 .. t) - 1 <= -20%
   PRIMARY  VETO = DT or CR, vs BASE (the certified T20-B).
STATISTIC monthly d = VETO - BASE (pp), Newey-West t (lag 3); halves split 2018-01; years with d > 0.
BAR      discovery track: ONE primary cell -> house |t| >= 3, both halves the same sign as the mean, a majority of years.
         BETTER -> adopt the veto on the live sleeve; INVERTED (t <= -3 under the same conditions) -> the veto costs.
         Also reported: each book's excess over the EW universe, CAGR, maxDD, vetoed names per formation, and the
         forward return of the VETOED names themselves (what the veto avoided).
Exploratory (Sidak k = 4, |t| >= 2.50; no verdict): X1 DT alone; X2 CR alone; X3 DT-or (close < SMA50 OR 63d < 0,
         the strict version); X4 VETO applied to NEW buys only (held names keep the buffer rule).
Prior: LOW-to-moderate -- PTH said far-from-high names carry part of the premium; NESR-type no-news crashes tend to
       reverse (short-term reversal). A veto that only drops the clearly broken tail is the variant most likely to survive.

Run: PYTHONPATH=src:. .venv/bin/python3 run_momentum_trader_veto.py   (log -> data/studies/logs/momentum_trader_veto.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_trader_veto.log"
LOOKBACK, SKIP = 252, 21


def vetoes(C: pd.DataFrame) -> dict[str, np.ndarray]:
    sma50 = C.rolling(50, min_periods=50).mean()
    r63 = C / C.shift(63) - 1
    dd10 = C / C.rolling(11, min_periods=11).max() - 1
    below, down = (C < sma50).values, (r63 < 0).values
    dt = below & down
    cr = (dd10 <= -0.20).values
    return {"VETO": dt | cr, "DT": dt, "CR": cr, "DT-or": below | down}


def simulate(C: pd.DataFrame, elig: pd.DataFrame, veto: np.ndarray | None, new_only: bool = False):
    idx, Cv, E = C.index, C.values, elig.values
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                     for j in range(Cv.shape[1])])
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    hold: set = set()
    rows, avoided = [], []
    for a, b in zip(me[:-1], me[1:]):
        if a - LOOKBACK < 0:
            continue
        score = Cv[a - SKIP] / Cv[a - LOOKBACK] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        names = np.flatnonzero(ok)
        if len(names) < 50:
            continue
        order = names[np.argsort(-score[names])]
        q20 = set(order[:int(np.ceil(len(names) * 0.20))])
        bad = (lambda j: bool(veto[a, j])) if veto is not None else (lambda j: False)
        keep = {j for j in hold if j in q20 and (new_only or not bad(j))}
        fill = [j for j in order if j not in keep and not bad(j)][:max(20 - len(keep), 0)]
        new = keep | set(fill)
        exit_i = np.minimum(b, last[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        to = 1 - len(new & hold) / max(len(new), 1)
        if veto is not None:      # what the veto avoided: vetoed names that plain T20-B logic would have held
            plain_keep = {j for j in hold if j in q20}
            plain = plain_keep | set([j for j in order if j not in plain_keep][:max(20 - len(plain_keep), 0)])
            av = [j for j in plain - new]
            avoided += [dict(month=idx[b].to_period("M"), x=r.get(j, np.nan) - r.mean()) for j in av]
        hold = new
        rows.append(dict(month=idx[b].to_period("M"), BOOK=r.reindex(list(new)).mean() - 2 * M.COST * to, EW=r.mean(),
                         n_veto=0 if veto is None else int(sum(bad(j) for j in order[:40]))))
    return pd.DataFrame(rows).set_index("month"), pd.DataFrame(avoided)


def stats(r: pd.Series) -> str:
    cum = (1 + r).cumprod()
    cagr = 100 * (cum.iloc[-1] ** (12 / len(r)) - 1)
    return f"{100 * r.mean():+.2f}%/mo CAGR {cagr:+.1f}% maxDD {100 * (1 - cum / cum.cummax()).max():.1f}%"


def compare(base: pd.DataFrame, cell: pd.DataFrame, avoided: pd.DataFrame, label: str, primary: bool = False) -> None:
    d = (cell.BOOK - base.BOOK).dropna() * 100
    h = d.index < pd.Period(M.SPLIT, "M")
    yd = d.groupby(d.index.year).sum()
    t = M.nw_t(d)
    up = t >= 3 and d[h].mean() > 0 and d[~h].mean() > 0 and (yd > 0).sum() > len(yd) / 2
    dn = t <= -3 and d[h].mean() < 0 and d[~h].mean() < 0 and (yd < 0).sum() > len(yd) / 2
    print(f"\n## {label}{'  <- PRIMARY' if primary else ''}")
    print(f"cell - BASE {d.mean():+.3f}pp/mo  t_NW {t:+.2f}  halves {d[h].mean():+.3f}/{d[~h].mean():+.3f}  "
          f"years + {(yd > 0).sum()}/{len(yd)}  -> {('BETTER' if up else 'INVERTED' if dn else 'NULL') if primary else '(exploratory)'}")
    print(f"  BASE {stats(base.BOOK)} | excess vs EW {100 * (base.BOOK - base.EW).mean():+.2f}pp")
    print(f"  CELL {stats(cell.BOOK)} | excess vs EW {100 * (cell.BOOK - cell.EW).mean():+.2f}pp")
    if len(avoided):
        x = avoided.x.dropna() * 100
        print(f"  avoided name-months {len(x):,} (~{len(x) / len(cell):.1f}/formation) | their excess vs EW "
              f"{x.mean():+.2f}pp/mo (median {x.median():+.2f}) | veto rate in ranks 1-40 {cell.n_veto.mean():.1f}")
    print("  per year (pp): " + " ".join(f"{y}:{v:+.1f}" for y, v in yd.items()))


def run_all(C: pd.DataFrame, elig: pd.DataFrame, title: str, explore: bool) -> None:
    print(f"\n# {title}")
    V = vetoes(C)
    base, _ = simulate(C, elig, None)
    cell, av = simulate(C, elig, V["VETO"])
    compare(base, cell, av, "VETO = DT or CR", primary=explore)
    if explore:
        print("\n# exploratory (Sidak k = 4, |t| >= 2.50; no verdict)")
        for k, lab in (("DT", "X1 DT alone"), ("CR", "X2 CR alone"), ("DT-or", "X3 DT-or (strict)")):
            c, a = simulate(C, elig, V[k])
            compare(base, c, a, lab)
        c, a = simulate(C, elig, V["VETO"], new_only=True)
        compare(base, c, a, "X4 VETO on new buys only")


def main():
    import run_dip_survivorship as DS
    from lib.studies.pattern_test import load_panel
    C, Vol = DS.adjust_and_clean(DS.pull())
    liq = ((Vol.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    run_all(C, liq, "PRIMARY: chain_spot incl. delisted (certification data)", explore=True)
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    run_all(P.close, P.elig, "SECONDARY: liquid_panel_2009 (survivors) -- direction check, no verdict", explore=False)


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

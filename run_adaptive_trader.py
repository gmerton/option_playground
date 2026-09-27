#!/usr/bin/env python3
"""
SIMULATED ADAPTIVE TRADER -- does reacting to your own results (sizing and knob-tuning) beat trading the rule flat?
(pre-registered 2026-09-27, before the run; spec = TEST_INDEX section 10 row incl. both 2026-09-26 amendments;
Gabe: "run the adaptive trader sim". Dependency met: the self-regime holdout ran 2026-09-25, NULL.)

THEORY. Feedback can only add expectancy if outcomes are serially dependent. Otherwise it only reshapes risk. So
every rule is compared with ITSELF run on the same trades with the outcomes shuffled (which destroys the dependence).

PART 0 -- runs test (neurotrader amendment (a)). Wald-Wolfowitz on the win/loss signs of the house breakout trades
       ordered by EXIT date (the order information arrives in). z ~ 0 predicts every feedback rule ties its shuffle.

PART 1 -- SIZING FEEDBACK on the real trade sequence
  trades   data/studies/logs/self_regime_trades.csv (2,226 house breakouts 2009-06 -> 2026-09: close entry, stop = the
           breakout-day low on the close, 20-EMA trail, 60-session cap; % return net of slippage).
  sizing   notional = 10% of current equity x the rule's multiplier (R is unusable for sizing here: stops as tight as
           0.1% make R run -10..+66). Positions open at entry and settle at exit, in event order, so concurrency is
           real. A rule may use ONLY trades closed before the entry date (no look-ahead).
  rules    FIXED 1.0 · AM_STREAK: last 3 closed all winners 1.5 / all losers 0.5 / else 1.0 · AM_20: sum of the last
           20 closed trades' % > 0 -> 1.5 else 0.5 · DD_CUT: equity > 15% below its peak -> 0.5 · QUIT: after 6
           closed losers in a row, no new trades for 28 calendar days · TURTLE_SKIP: last closed trade a winner ->
           skip (neurotrader amendment (b)) · TURTLE_SIZE: last closed winner 0.5 / loser 1.5.
  measures log terminal wealth, CAGR, max drawdown, share of trade-days under water, min equity (ruin = < 0.5).
  CONTROL  1,000 shuffles of the OUTCOMES among trades entered in the same calendar year (dates, concurrency and
           each year's opportunity set kept; serial dependence destroyed). Value of feedback = (rule - FIXED) on the
           real order minus the mean (rule - FIXED) on the shuffles; p = share of shuffles >= real.
  BAR      a rule ADDS VALUE only if p <= 0.05/6 (Bonferroni, 6 rules) on log terminal wealth AND its real-order gain
           over FIXED is positive in both halves (split 2018-01). Otherwise its effect is risk reshaping (report DD).

PART 2 -- KNOB ADAPTATION (Gabe's amendment) on the precision pool (run_precision_tier_control.build(), 2019-10 ->
  2026-09, close entry, 60-session cap)
  knobs    stop = entry - w x ADR% x entry, w in {0.5, 0.75, 1.0}, judged on the close  x  exit in {20-EMA close trail,
           10-session time exit, stop-only}: 9 cells; plus HOUSE (breakout-day-low stop + 20-EMA trail).
  adaptive each month, the knob with the best mean % return over trades that EXITED in the trailing 3 (primary) or 6
           months (min 20 trades, else HOUSE); applied to that month's entries. First evaluated month 2020-07.
  PRIMARY  ADAPT3 - HOUSE, % per trade (not R), paired by trade, t on entry-month cluster means.
  CONTROL  1,000 permutations of the MONTH ORDER of the knob-performance history used for selection (evaluation stays
           on the real months). p = share of permutations whose adaptive mean >= real.
  BAR      t >= 3 AND permutation p <= 0.05 AND both halves (split 2023-01) positive. Also reported: every fixed cell
           (the best one is hindsight, not a rule) and ADAPT6.
PRIOR     against: trailing-30d own-result / stop-out-share rules FAILED 2019-26; month persistence rho -0.01 (WL-2b);
          self-regime holdout NULL.
Local vs cloud: local (cached panels; minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_adaptive_trader.py   (log -> data/studies/logs/adaptive_trader.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/adaptive_trader.log"
BASE, NSHUF, SEED = 0.10, 1000, 20260927
RULES = ["FIXED", "AM_STREAK", "AM_20", "DD_CUT", "QUIT", "TURTLE_SKIP", "TURTLE_SIZE"]


def runs_z(signs: np.ndarray) -> float:
    s = signs[signs != 0]; n1, n2 = (s > 0).sum(), (s < 0).sum(); n = n1 + n2
    mu = 2 * n1 * n2 / n + 1; var = (mu - 1) * (mu - 2) / (n - 1)
    runs = 1 + (s[1:] != s[:-1]).sum()
    return float((runs - mu) / np.sqrt(var))


# ------------------------------------------------------------------ part 1
def simulate(entry, exit_, pct, rule):
    """Event simulation. entry/exit_ are int day numbers, pct % returns. Returns (log wealth, maxDD, underwater, min eq)."""
    n = len(pct); eq, peak, mn = 1.0, 1.0, 1.0
    order = np.argsort(entry, kind="stable")
    ex_order = np.argsort(exit_, kind="stable")
    closed, open_pos, pause_until, streak_loss = [], {}, -1, 0
    ei = 0; dd_max = 0.0; under = 0; checks = 0
    for k in order:
        t = entry[k]
        while ei < n and exit_[ex_order[ei]] < t:                  # settle everything that exited before t
            j = ex_order[ei]; ei += 1
            if j in open_pos:
                eq += open_pos.pop(j) * pct[j] / 100
                closed.append(pct[j]); streak_loss = streak_loss + 1 if pct[j] < 0 else 0
                if rule == "QUIT" and streak_loss >= 6:
                    pause_until = exit_[j] + 28; streak_loss = 0
                peak = max(peak, eq); mn = min(mn, eq)
                dd_max = max(dd_max, 1 - eq / peak); under += eq < peak; checks += 1
        m = 1.0
        if rule == "AM_STREAK" and len(closed) >= 3:
            last = closed[-3:]; m = 1.5 if all(x > 0 for x in last) else (0.5 if all(x < 0 for x in last) else 1.0)
        elif rule == "AM_20" and len(closed) >= 20:
            m = 1.5 if sum(closed[-20:]) > 0 else 0.5
        elif rule == "DD_CUT":
            m = 0.5 if eq < 0.85 * peak else 1.0
        elif rule == "QUIT":
            m = 0.0 if t <= pause_until else 1.0
        elif rule == "TURTLE_SKIP" and closed:
            m = 0.0 if closed[-1] > 0 else 1.0
        elif rule == "TURTLE_SIZE" and closed:
            m = 0.5 if closed[-1] > 0 else 1.5
        if m > 0:
            open_pos[k] = BASE * m * eq
    for j, v in list(open_pos.items()):
        eq += v * pct[j] / 100
    peak = max(peak, eq); dd_max = max(dd_max, 1 - eq / peak); mn = min(mn, eq)
    return np.log(max(eq, 1e-9)), dd_max, under / max(checks, 1), mn


def part1(out):
    T = pd.read_csv(REPO / "data/studies/logs/self_regime_trades.csv", parse_dates=["entry", "exit"]).sort_values("entry")
    d0 = T.entry.min()
    en = (T.entry - d0).dt.days.values; ex = (T.exit - d0).dt.days.values; pc = T.pct.values
    z = runs_z(np.sign(pc[np.argsort(ex, kind="stable")]))
    out.append(f"## PART 0 runs test: {len(pc):,} house breakouts ordered by exit, z {z:+.2f} "
               f"({'more alternation' if z > 0 else 'more streaking'} than chance; |z| < 2 = no serial dependence)")
    yrs = (T.entry.dt.year).values
    years = T.entry.dt.year.max() - T.entry.dt.year.min() + 1
    real = {r: simulate(en, ex, pc, r) for r in RULES}
    rng = np.random.default_rng(SEED); shuf = {r: [] for r in RULES}
    groups = [np.flatnonzero(yrs == y) for y in np.unique(yrs)]
    for _ in range(NSHUF):
        p2 = pc.copy()
        for g in groups:
            p2[g] = pc[rng.permutation(g)]
        for r in RULES:
            shuf[r].append(simulate(en, ex, p2, r)[0])
    base_real = real["FIXED"][0]; base_sh = np.array(shuf["FIXED"])
    h = T.entry < "2018-01-01"
    halves = {}
    for part, msk in (("h1", h.values), ("h2", ~h.values)):
        e1, x1, p1 = en[msk], ex[msk], pc[msk]
        f = simulate(e1, x1, p1, "FIXED")[0]
        halves[part] = {r: simulate(e1, x1, p1, r)[0] - f for r in RULES}
    out.append(f"\n## PART 1 sizing feedback on the real sequence ({len(pc):,} trades, {years} calendar years; notional 10% x multiplier)")
    out.append(f"  {'rule':12s} {'logW':>7s} {'CAGR':>7s} {'maxDD':>6s} {'under':>6s} {'minEq':>6s} | vs FIXED real  shuffled-mean  value  p   | halves (logW vs FIXED)")
    res = {}
    for r in RULES:
        lw, dd, uw, mn = real[r]
        d_real = lw - base_real; d_sh = np.array(shuf[r]) - base_sh
        val = d_real - d_sh.mean(); p = (d_sh >= d_real).mean()
        ok = r != "FIXED" and p <= 0.05 / 6 and halves["h1"][r] > 0 and halves["h2"][r] > 0
        res[r] = ok
        out.append(f"  {r:12s} {lw:+7.3f} {100 * (np.exp(lw / years) - 1):+6.1f}% {100 * dd:5.1f}% {100 * uw:5.0f}% {mn:6.2f} | "
                   f"{d_real:+.3f}   {d_sh.mean():+.3f}   {val:+.3f}  {p:.3f} | {halves['h1'][r]:+.3f} / {halves['h2'][r]:+.3f}"
                   + ("  ADDS VALUE" if ok else ""))
    return res


# ------------------------------------------------------------------ part 2
def knob_trades():
    P, brk, prec = build()
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    m = prec[prec.index >= "2019-10-01"]; off = len(prec) - len(m)
    ii, jj = np.where(m.values)
    cells = [(w, e) for w in (0.5, 0.75, 1.0) for e in ("EMA20", "TIME10", "STOPONLY")]
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + pt.SLIP)
        if i + 1 >= len(C) or not np.isfinite(ADR[i, j]) or not np.isfinite(L[i, j]) or entry <= L[i, j]:
            continue
        rec = dict(date=P.close.index[i], sym=P.close.columns[j])
        for name, stop, ex in [("HOUSE", L[i, j], "EMA20")] + [(f"w{w}_{e}", C[i, j] * (1 - w * ADR[i, j] / 100), e) for w, e in cells]:
            end = min(i + 60, len(C) - 1); k = i
            for k in range(i + 1, end + 1):
                c = C[k, j]
                if not np.isfinite(c):
                    continue
                if c < stop:
                    break
                if ex == "EMA20" and np.isfinite(E20[k, j]) and c < E20[k, j]:
                    break
                if ex == "TIME10" and k - i >= 10:
                    break
            rec[name] = 100 * (C[k, j] * (1 - pt.SLIP) / entry - 1); rec[name + "_x"] = P.close.index[k]
        rows.append(rec)
    return pd.DataFrame(rows), ["HOUSE"] + [f"w{w}_{e}" for w, e in cells]


def adaptive(T, knobs, look, month_perf_order=None):
    """Mean % per trade of the adaptive picker over the evaluation months."""
    T = T.copy(); T["m"] = T.date.dt.to_period("M")
    months = sorted(T.m.unique()); ev = [mm for mm in months if mm >= pd.Period("2020-07", "M")]
    # knob performance by EXIT month (information date)
    perf = {}
    for kb in knobs:
        xm = pd.to_datetime(T[kb + "_x"]).dt.to_period("M")
        perf[kb] = T.groupby(xm)[kb].agg(["sum", "count"])
    allm = sorted(set().union(*[set(v.index) for v in perf.values()]))
    if month_perf_order is not None:                     # permute which month's performance sits where
        mp = dict(zip(allm, month_perf_order))
        perf = {kb: v.rename(index=lambda x: mp.get(x, x)).groupby(level=0).sum() for kb, v in perf.items()}
    picks, rets = {}, []
    for mm in ev:
        win = [mm - q for q in range(1, look + 1)]
        best, bv = "HOUSE", -np.inf
        for kb in knobs:
            s = perf[kb].reindex(win).fillna(0)
            if s["count"].sum() >= 20 and s["sum"].sum() / s["count"].sum() > bv:
                best, bv = kb, s["sum"].sum() / s["count"].sum()
        picks[mm] = best
        sub = T[T.m == mm]
        rets.append(sub[best].rename("ret").to_frame().assign(house=sub.HOUSE.values, m=mm, date=sub.date.values))
    R = pd.concat(rets, ignore_index=True)
    return R, picks


def part2(out):
    T, knobs = knob_trades()
    out.append(f"\n## PART 2 knob adaptation, precision pool {T.date.min().date()} -> {T.date.max().date()} ({len(T):,} trades)")
    ev = T[T.date >= "2020-07-01"]
    out.append("  fixed cells, mean % per trade over the evaluation months (best = hindsight, not a rule):")
    out.append("   " + " | ".join(f"{k} {ev[k].mean():+.2f}" for k in knobs))
    res = {}
    for look in (3, 6):
        R, picks = adaptive(T, knobs, look)
        d = R.ret - R.house
        g = d.groupby(R.m).mean(); t = g.mean() / g.std(ddof=1) * np.sqrt(len(g))
        h = pd.to_datetime(R.date) < "2023-01-01"
        allm = sorted(set().union(*[set(pd.to_datetime(T[k + "_x"]).dt.to_period("M").unique()) for k in knobs]))
        rng = np.random.default_rng(SEED + look); null = []
        for _ in range(NSHUF):
            Rp, _ = adaptive(T, knobs, look, list(rng.permutation(allm)))
            null.append(Rp.ret.mean())
        p = (np.array(null) >= R.ret.mean()).mean()
        tag = "  *PRIMARY*" if look == 3 else ""
        pk = pd.Series(picks).value_counts()
        out.append(f"  ADAPT{look}: mean {R.ret.mean():+.2f}% vs HOUSE {R.house.mean():+.2f}% -> {d.mean():+.2f}pp t {t:+.2f} "
                   f"halves {d[h].mean():+.2f} / {d[~h].mean():+.2f} | month-permutation p {p:.3f} (null mean {np.mean(null):+.2f}%)"
                   f" | picks: {', '.join(f'{k} {v}' for k, v in pk.items())}{tag}")
        res[look] = (t, p, d[h].mean(), d[~h].mean())
    return res


def main():
    out = ["# Simulated adaptive trader (pre-registration in the docstring)"]
    r1 = part1(out)
    r2 = part2(out)
    t, p, h1, h2 = r2[3]
    ok2 = t >= 3 and p <= 0.05 and h1 > 0 and h2 > 0
    out.append(f"\nVERDICT: sizing rules that ADD VALUE: {[r for r, v in r1.items() if v] or 'none'} | "
               f"knob adaptation (ADAPT3 primary): {'PASS' if ok2 else 'NOT MET'}")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

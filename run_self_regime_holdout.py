#!/usr/bin/env python3
"""
Does the breakout strategy's OWN recent results tell you when to press and when to sit out? -- 2010-19 HOLDOUT
(pre-registered 2026-09-25, before any run; Gabe: "how did successful traders become successful?" -> the pros press
when their setups are working and shrink when they are not).

NOT A NEW AXIS, AND SAID SO. The 2019-26 ledger already answered the monthly version NULL:
  * breakout_regime_and_stop_distance_2026-09-17 (run_regime_feedback.py): last month's breakouts' 10-day return ->
    next month's new breakouts, rank corr +0.01. The ONE lean: the month after the FEWEST 10-day stop-outs
    (bottom quartile) -> +0.79R, 61% positive, t 2.0; the other quartiles +0.05-0.17; the reverse does not hold.
  * strategy_localisation (WL-2b, 2026-09-23): 26 strategies, trailing -> next month rho -0.011.
What IS new: (a) years those tests never saw -- liquid_panel_2009 gives 2010-01 -> 2019-09 out of time; (b) the
TRADE-level version (the last N closed trades, which a trader actually feels) instead of calendar months.

TRADES  the 9/17 pool definition exactly (run_regime_feedback.py): ADDV >= $50M & px >= $5 (harness mask), ADR 4-7,
        within 15% of the 252d high, 10>20>50 stacked (house 0.25-ADR slack) held >= 1 session, close clears the
        15-session pivot, RVOL >= 1.1, close in the upper half, gap < 5%, day < 8%. Entry = the close. Exit = first
        close under the entry-day low (the stop) or under the 20 EMA, cap 60 sessions; 10 bp per side. % return AND R.
        One trade per name at a time (a name re-enters only after its previous trade exits).
SIGNALS (everything strictly knowable before the decision)
  S1 PRIMARY -- the surviving lean, re-tested out of time: at each month start, breakouts entered 15-45 days before
        (so their first 10 sessions are complete); their 10-day stop-out share. FEWEST quartile uses the cut FIXED
        from 2019-10 -> 2026-09 (the lean's own window) -- no refit on the holdout. Outcome = mean % of the NEW
        breakouts entered in that month. Non-overlapping months; t on the Q1-vs-rest monthly difference.
  S2 (new, trade-level) -- at each entry, the last 20 trades CLOSED before that date: HOT if their mean % > 0, else
        COLD. Outcome = HOT-entry minus COLD-entry mean %, month-clustered.
WINDOW  PRIMARY = 2010-01 -> 2019-09 (holdout; split 2015-01). 2019-10 -> 2026-08 reported as the in-sample replay.
BAR     (declared now) ADOPT as an exposure rule only with t >= 3 on the holdout, both halves positive, majority of
        years. t ~2 with both halves positive = SUPPORTED (a nudge, as the 9/17 note already says), not a switch.
CONTROL (declared now) the market's own state: S2 is also reported inside SPY > / < its 50-day, so a "self-regime"
        that is only the market trend shows up as zero within strata.
DESCRIPTIVE the book view: monthly P&L of ALWAYS (take every trade, 1 unit) vs HOT-only vs 2x-HOT/0.5x-COLD, with
        mean, Sharpe and max drawdown, holdout and replay separately.
PRIOR   low: two NULLs already on the monthly version.
Survivorship: the panel is today's liquid names; both arms share it, so the within-strategy contrast is what counts.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_self_regime_holdout.py   (log -> data/studies/logs/self_regime_holdout.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/self_regime_holdout.log"
PANEL = REPO / "data/cache/liquid_panel_2009.parquet"
HO_START, HO_END, HO_SPLIT = "2010-01-01", "2019-09-30", "2015-01-01"
IS_START, IS_END = "2019-10-01", "2026-08-31"
SLIP, CAP, N_TRAIL = 0.0010, 60, 20


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def build_trades() -> tuple[pd.DataFrame, pd.Series]:
    raw = pd.read_parquet(PANEL); raw["date"] = pd.to_datetime(raw.date)
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); piv = H.shift(1).rolling(15).max()
    rvol = V / V.shift(1).rolling(50).mean(); pos = (C - L) / (H - L).replace(0, np.nan)
    gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None); run = stack_run(C, adr=adr)
    sig = (elig & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (run >= 1) & (C > piv) & (rvol >= 1.1)
           & (pos >= 0.5) & (gap < 0.05) & (chg < 0.08)).fillna(False)
    idx, cols = C.index, C.columns
    Cv, Lv, Ev, Sv = C.values, L.values, e20.values, sig.values
    rows = []
    for j in range(len(cols)):
        i, n = 0, len(idx)
        hits = np.flatnonzero(Sv[:, j])
        busy_until = -1
        for i in hits:
            if i <= busy_until or i + 1 >= n:
                continue
            entry, stop = Cv[i, j], Lv[i, j]
            if not (np.isfinite(entry) and np.isfinite(stop)) or entry <= stop:
                continue
            ex, how = None, "cap"
            for k in range(i + 1, min(i + CAP, n - 1) + 1):
                c = Cv[k, j]
                if not np.isfinite(c):
                    continue
                if c < stop:
                    ex, how = k, "stop"; break
                if c < Ev[k, j]:
                    ex, how = k, "ema"; break
                ex = k
            if ex is None:
                continue
            pct = 100 * (Cv[ex, j] * (1 - SLIP) / (entry * (1 + SLIP)) - 1)
            rows.append(dict(sym=cols[j], entry=idx[i], exit=idx[ex], how=how, pct=pct,
                             R=(Cv[ex, j] - entry) / (entry - stop),
                             stop10=(how == "stop" and ex - i <= 10)))
            busy_until = ex
    T = pd.DataFrame(rows).sort_values("entry").reset_index(drop=True)
    return T, spy


def s1_monthly(T: pd.DataFrame) -> pd.DataFrame:
    """Month m: signal = 10-day stop-out share of breakouts entered 15-45 days before m's first day;
    outcome = mean % of breakouts entered in m."""
    months = pd.period_range(T.entry.min().to_period("M") + 2, T.entry.max().to_period("M"), freq="M")
    out = []
    for m in months:
        d0 = m.start_time
        prior = T[(T.entry >= d0 - pd.Timedelta(days=45)) & (T.entry <= d0 - pd.Timedelta(days=15))]
        now = T[T.entry.dt.to_period("M") == m]
        if len(prior) >= 5 and len(now) >= 3:
            out.append(dict(month=m, stop_share=prior.stop10.mean(), n_prior=len(prior),
                            outcome=now.pct.mean(), outcome_R=now.R.clip(upper=20).mean(), n=len(now)))
    return pd.DataFrame(out)


def s2_trade(T: pd.DataFrame) -> pd.DataFrame:
    """For each trade: mean % of the last N trades that CLOSED strictly before its entry date."""
    closed = T.sort_values("exit")
    ex_dates, pcts = closed.exit.values, closed.pct.values
    trail = []
    for e in T.entry.values:
        k = np.searchsorted(ex_dates, e, side="left")       # exits strictly before the entry day
        trail.append(pcts[max(0, k - N_TRAIL):k].mean() if k >= N_TRAIL else np.nan)
    T = T.copy(); T["trail"] = trail; T["hot"] = T.trail > 0
    return T


def report_s1(M, q1_cut, lo, hi, split, out, label):
    W = M[(M.month.dt.start_time >= lo) & (M.month.dt.start_time <= hi)].copy()
    W["q1"] = W.stop_share <= q1_cut
    a, b = W[W.q1].outcome, W[~W.q1].outcome
    diff = a.mean() - b.mean()
    # t for a difference of two groups of non-overlapping months (Welch)
    se = np.sqrt(a.var(ddof=1) / max(len(a), 1) + b.var(ddof=1) / max(len(b), 1))
    h = W.month.dt.start_time < pd.Timestamp(split)
    d1 = W[h & W.q1].outcome.mean() - W[h & ~W.q1].outcome.mean()
    d2 = W[~h & W.q1].outcome.mean() - W[~h & ~W.q1].outcome.mean()
    out.append(f"  S1 {label}: FEWEST-stop-out months n {len(a)} mean {a.mean():+.2f}% vs rest n {len(b)} {b.mean():+.2f}% "
               f"| diff {diff:+.2f}pp Welch t {diff / se:+.2f} | halves {d1:+.2f} / {d2:+.2f} "
               f"| Q1 months positive {(a > 0).mean():.0%}")
    return diff, diff / se, d1, d2


def report_s2(T, lo, hi, split, out, label, spy_up=None):
    W = T[(T.entry >= lo) & (T.entry <= hi) & T.trail.notna()]
    mo = W.groupby([W.entry.dt.to_period("M"), W.hot]).pct.mean().unstack()
    dm = (mo.get(True) - mo.get(False)).dropna()
    hh = dm.index < pd.Period(split, "M")
    yr = dm.groupby(dm.index.year).mean(); same = int((np.sign(yr) == np.sign(dm.mean())).sum())
    out.append(f"  S2 {label}: HOT n {int(W.hot.sum())} {W[W.hot].pct.mean():+.2f}% vs COLD n {int((~W.hot).sum())} "
               f"{W[~W.hot].pct.mean():+.2f}% | month-clustered diff {dm.mean():+.2f}pp t {tstat(dm):+.2f} "
               f"| halves {dm[hh].mean():+.2f} / {dm[~hh].mean():+.2f} | years same sign {same}/{len(yr)}")
    if spy_up is not None:
        up = spy_up.reindex(W.entry).values
        for lab, m in (("SPY > 50d", up == True), ("SPY < 50d", up == False)):   # noqa: E712
            X = W[m]
            mo2 = X.groupby([X.entry.dt.to_period("M"), X.hot]).pct.mean().unstack()
            d2 = (mo2.get(True) - mo2.get(False)).dropna() if mo2.shape[1] == 2 else pd.Series(dtype=float)
            out.append(f"     control within {lab}: n {len(X)} diff {d2.mean():+.2f}pp t {tstat(d2):+.2f}")
    return dm


def book(T, lo, hi, out, label):
    W = T[(T.entry >= lo) & (T.entry <= hi) & T.trail.notna()].copy()
    rows = {}
    for name, w in (("ALWAYS", np.ones(len(W))), ("HOT only", W.hot.astype(float).values),
                    ("2x HOT / 0.5x COLD", np.where(W.hot, 2.0, 0.5))):
        m = (W.pct * w).groupby(W.exit.dt.to_period("M")).sum() / 100
        cum = m.cumsum()
        rows[name] = dict(mean_mo=100 * m.mean(), sharpe=m.mean() / m.std() * np.sqrt(12) if m.std() > 0 else np.nan,
                          maxDD=100 * (cum.cummax() - cum).max(), units=w.sum())
    out.append(f"  book {label} (sum of trade % per exit month, 1 unit = 1% of book per trade):")
    for k, v in rows.items():
        out.append(f"     {k:20s} mean {v['mean_mo']:+.2f}%/mo  Sharpe {v['sharpe']:+.2f}  maxDD {v['maxDD']:.1f}%  units {v['units']:.0f}")


def main():
    T, spy = build_trades()
    spy_up = (spy > spy.rolling(50).mean())
    T = s2_trade(T)
    out = ["# Self-regime (own recent results) -> next breakouts: 2010-19 HOLDOUT (pre-registration in the docstring)",
           f"# trades {len(T):,} on {T.sym.nunique()} names, {T.entry.min().date()} -> {T.entry.max().date()}; "
           f"holdout {((T.entry >= HO_START) & (T.entry <= HO_END)).sum():,}, replay {(T.entry >= IS_START).sum():,}; "
           f"stop exits {T.how.eq('stop').mean():.0%}, mean {T.pct.mean():+.2f}%/trade"]
    M = s1_monthly(T)
    fit = M[M.month.dt.start_time >= pd.Timestamp(IS_START)]
    q1_cut = fit.stop_share.quantile(0.25)
    out.append(f"\n## S1 PRIMARY -- fewest-stop-out months (cut fixed on 2019-10+: stop share <= {q1_cut:.2f})")
    s1 = report_s1(M, q1_cut, pd.Timestamp(HO_START), pd.Timestamp(HO_END), HO_SPLIT, out, "HOLDOUT 2010-19")
    report_s1(M, q1_cut, pd.Timestamp(IS_START), pd.Timestamp(IS_END), "2023-01-01", out, "replay 2019-26 (in-sample)")
    out.append(f"\n## S2 -- last {N_TRAIL} closed trades' mean % > 0 (HOT) vs not (COLD)")
    report_s2(T, HO_START, HO_END, HO_SPLIT, out, "HOLDOUT 2010-19", spy_up)
    report_s2(T, IS_START, IS_END, "2023-01-01", out, "replay 2019-26")
    out.append("\n## Book view (descriptive)")
    book(T, HO_START, HO_END, out, "HOLDOUT 2010-19")
    book(T, IS_START, IS_END, out, "replay 2019-26")
    ok = s1[1] >= 3 and s1[2] > 0 and s1[3] > 0
    sup = (not ok) and s1[1] >= 2 and s1[2] > 0 and s1[3] > 0
    out.append(f"\nVERDICT S1 (primary): {'ADOPT as an exposure rule' if ok else 'SUPPORTED (nudge only)' if sup else 'NULL on the holdout'}")
    T.to_csv(REPO / "data/studies/logs/self_regime_trades.csv", index=False)
    M.to_csv(REPO / "data/studies/logs/self_regime_months.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

#!/usr/bin/env python3
"""
Brandt's FRIDAY LOSING-CLOSE RULE as a time stop on the house breakout (pre-registered 2026-09-29, committed before any
run). Source: TraderLion interview _G8QyHkvQ2Q (his firm's rule: any trade entered during the week that is not in profit
at Friday's close is exited).

WHY. The house breakout's winners are the ~24% that never come back to the level (+1.27R); the ~76% that retest average
-0.37R (retrace_entry_2026-09-20). Every tightening rule tested so far cut WINNERS (profit-lock: 'extended -> tighten'
INVERTED; 10-EMA trail -0.47R). A rule conditioned on being UNDER WATER at the first Friday cuts losers instead. Untested.

PRE-REGISTRATION
  Panel     liquid_panel_2009, 2010-01 -> 2026-09 (the precision tier is thin before 2020 on this panel; stated).
  Pool      PRIMARY = the precision tier (run_oneil_pyramid_8wk.py definition). Secondary = the broad house breakout pool
            (close > prior 20-session high, ADR >= 3, eligible) for power.
  House     buy the close; stop = min(entry-day low, close x 0.98) judged on the close; exit on the first close < stop or
            < 20 EMA; 60-session cap; 5 bp per side. Outcome in % of entry (and R).
  Rule F    identical, plus: at the close of the FIRST FRIDAY strictly after the entry session, if the close <= the entry
            price and the house exit has not already fired, exit at that close.
  Secondary D3 / D5: the same test at the close of session 3 / 5 after entry instead of the first Friday.
  PRIMARY   paired F - House per trade (same trades), SE clustered by calendar month of entry. ADOPT iff t >= 3 AND both
            halves (split 2023-01-01) positive AND the top-1% of house trades is not reduced (the rule must not cut the
            Pareto tail: report the share of house P&L from the top 1% / 5% under both). INVERTED iff t <= -3 with both
            halves negative. Otherwise NULL.
  Report    trades touched by the rule (share exited early), their house outcome vs rule outcome, per-year, win rate,
            mean R.

Usage: PYTHONPATH=src .venv/bin/python3 run_friday_loser_timestop.py > data/studies/logs/friday_loser_timestop.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
COST, FLOOR, HOLD = 0.0005, 0.02, 60
SPLIT = pd.Timestamp("2023-01-01")


def main():
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100; piv = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stk = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv) & (rvol >= 1.1) & (pos >= 0.5) & (stk >= 5) & (gap < 0.05)
           & (chg < 0.08) & (C.shift(1) < piv))
    prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stk <= 40)).fillna(False)
    house = ((C > H.shift(1).rolling(20).max()) & (adr >= 3) & elig).fillna(False)
    Cv, Lv, Ev = C.values, L.values, e20.values; N = len(Cv); dates = C.index
    wd = dates.dayofweek.values

    def walk(i, j, rule):
        entry = Cv[i, j]; stop = min(Lv[i, j], entry * (1 - FLOOR))
        risk = entry - stop
        check = None
        if rule == "F":
            ks = [k for k in range(i + 1, min(i + 8, N)) if wd[k] == 4]
            check = ks[0] if ks else None
        elif rule == "D3":
            check = i + 3
        elif rule == "D5":
            check = i + 5
        for k in range(i + 1, min(i + HOLD + 1, N)):
            c = Cv[k, j]
            if not np.isfinite(c):
                continue
            if c < stop or c < Ev[k, j]:
                return (c * (1 - COST) - entry * (1 + COST)) / entry * 100, (c - entry) / risk, False
            if check is not None and k == check and c <= entry:
                return (c * (1 - COST) - entry * (1 + COST)) / entry * 100, (c - entry) / risk, True
        k = min(i + HOLD, N - 1)
        if k <= i:
            return np.nan, np.nan, False
        return (Cv[k, j] * (1 - COST) - entry * (1 + COST)) / entry * 100, (Cv[k, j] - entry) / risk, False

    def run(mask, label):
        ii, jj = np.where(mask.values)
        ok = (dates[ii] >= "2010-01-01") & (ii < N - 2)
        rows = []
        for i, j in zip(ii[ok], jj[ok]):
            r = dict(date=dates[i], sym=C.columns[j])
            for rule in ("H", "F", "D3", "D5"):
                pct, R, early = walk(i, j, rule)
                r[f"{rule}_pct"], r[f"{rule}_R"] = pct, R
                if rule != "H":
                    r[f"{rule}_early"] = early
            rows.append(r)
        T = pd.DataFrame(rows).dropna(subset=["H_pct"])
        print(f"\n== {label}: {len(T):,} trades, {T.date.min().date()} -> {T.date.max().date()} ==")
        out = []
        for rule in ("F", "D3", "D5"):
            d = T[f"{rule}_pct"] - T.H_pct
            m = pd.DataFrame(dict(d=d, mo=T.date.dt.to_period("M")))
            mu = d.mean(); s = m.groupby("mo").d.sum(); n = m.groupby("mo").size()
            se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum(); t = mu / se
            h1, h2 = d[T.date < SPLIT].mean(), d[T.date >= SPLIT].mean()
            e = T[T[f"{rule}_early"]]
            srt = np.sort(T.H_pct.values)[::-1]; srtr = np.sort(T[f"{rule}_pct"].values)[::-1]
            k1, k5 = max(1, len(T) // 100), max(1, len(T) // 20)
            out.append(dict(rule=rule, house_pct=T.H_pct.mean(), rule_pct=T[f"{rule}_pct"].mean(), diff_pp=mu, t=t, h1=h1, h2=h2,
                            share_exited_early=100 * len(e) / len(T), early_house_pct=e.H_pct.mean(), early_rule_pct=e[f"{rule}_pct"].mean(),
                            house_R=T.H_R.mean(), rule_R=T[f"{rule}_R"].mean(), win_house=100 * (T.H_pct > 0).mean(),
                            win_rule=100 * (T[f"{rule}_pct"] > 0).mean(), top1_house=srt[:k1].sum() / T.H_pct.sum(),
                            top1_rule=srtr[:k1].sum() / T[f"{rule}_pct"].sum(), top5_house=srt[:k5].mean(), top5_rule=srtr[:k5].mean()))
        R = pd.DataFrame(out); print(R.round(3).to_string(index=False))
        yr = T.assign(d=T.F_pct - T.H_pct).groupby(T.date.dt.year).d.agg(["mean", "size"])
        print("per year, F - House (pp):"); print(yr.round(2).T.to_string())
        return R, T

    RP, TP = run(prec, "PRIMARY: precision tier")
    RH, TH = run(house, "SECONDARY: broad house breakout pool")
    f = RP.iloc[0]
    tail_ok = f.top5_rule >= f.top5_house - 1e-9
    if f.t >= 3 and f.h1 > 0 and f.h2 > 0 and tail_ok:
        v = "ADOPT"
    elif f.t <= -3 and f.h1 < 0 and f.h2 < 0:
        v = "INVERTED"
    else:
        v = "NULL"
    print(f"\nPRIMARY (precision tier, Friday rule): {f.diff_pp:+.3f} pp/trade, t {f.t:+.2f}, halves {f.h1:+.3f}/{f.h2:+.3f}, "
          f"top-5% mean house {f.top5_house:+.2f} vs rule {f.top5_rule:+.2f} -> {v}")
    TP.to_csv("data/studies/logs/friday_loser_timestop_precision.csv", index=False)


if __name__ == "__main__":
    main()

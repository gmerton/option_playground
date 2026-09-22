#!/usr/bin/env python3
"""
Two O'Neil management rules on the house breakout book (2026-09-22).

Pool = the precision tier exactly as run_exit_timing_study.py builds it (the population behind the honest +0.4R):
ADR 4-7, within 15% of the 52wk high, stacked 5-40 sessions, close clears the 15-day pivot on RVOL >= 1.1,
upper-half close, gap < 5%, day < 8%, first close above the pivot; ADDV >= $50M; 2019-10 onward.
Base trade = buy the breakout close; stop = min(day low, close x 0.98) (the 2% risk floor) judged on the close;
exit = first close under the stop or the 20 EMA; 60-session cap; 5 bp per side. R capped at +/-20.

TEST 1 -- PYRAMID (O'Neil follow-on buy). At the close of session k after entry (k = 3, 5, 10), if the base trade
is still open, a second unit may be bought at that close. The add's stop = the base entry price (breakeven),
judged on the close; exit = same 20-EMA rule, same session-60 end date as the base. Add R is in units of the
add's own risk (close_k - base entry), cap +/-20. Add conditions:
  U  unconditional: any still-open trade (the control -- tells us what "being alive at k" alone is worth)
  A  up >= 1R on the base at the close of k
  B  never closed below the pivot (the breakout level) through k
  AB both
PRE-REGISTERED PASS: for some k, a conditioned add (A, B or AB) beats U at the same k by t >= 2 (month-clustered,
paired on the calendar) with the same sign in both halves (split 2023-01-01), AND its own mean R > 0.
Adds with risk < 2% of price are skipped (same floor as the base).

TEST 2 -- 8-WEEK HOLD. If the base trade closes >= +20% above entry within its first 15 sessions (3 weeks) while
still open, suspend the 20-EMA exit until session 40 (8 weeks); during the hold exit only on a close below the
entry price (O'Neil: never let a 20% gainer turn into a loss). After session 40 the 20-EMA rule resumes.
Same 60-session cap for both arms (and an 80-session variant for both).
PRE-REGISTERED PASS: paired (rule - base) improvement over ALL trades, month-clustered t >= 2, positive in both
halves.

Usage: PYTHONPATH=src .venv/bin/python3 run_oneil_pyramid_8wk.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
COST, CAP, FLOOR = 0.0005, 20.0, 0.02

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
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
gate = (adr >= 3) & (range52 >= 17) & elig
brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)).fillna(False).astype(bool)
prec = prec[prec.index >= "2019-10-01"]
ii, jj = np.where(prec.values); ii = ii + (len(C) - len(prec))
Cv, Lv, E, PV = C.values, L.values, e20.values, piv15.values
N = len(Cv)


def net(e, x): return x * (1 - COST) - e * (1 + COST)
def cap(r): return float(np.clip(r, -CAP, CAP))


def base_path(i, j, entry, stop, hold8=False, horizon=60):
    """returns (R, exit index)."""
    risk = entry - stop; t20 = False
    for k in range(i + 1, min(i + horizon + 1, N)):
        c = Cv[k, j]
        if not np.isfinite(c): continue
        if hold8 and not t20 and k - i <= 15 and c >= entry * 1.20: t20 = True
        in_hold = hold8 and t20 and k - i <= 40
        if in_hold:
            if c < entry: return net(entry, c) / risk, k, t20
            continue
        if c < stop or c < E[k, j]: return net(entry, c) / risk, k, t20
    k = min(i + horizon, N - 1); return net(entry, Cv[k, j]) / risk, k, t20


rows, adds = [], []
for i, j in zip(ii, jj):
    if i + 12 >= N: continue
    entry = Cv[i, j]; stop = min(Lv[i, j], entry * (1 - FLOOR)); risk = entry - stop
    if not (np.isfinite(entry) and np.isfinite(stop)) or risk <= 0: continue
    R, kx, _ = base_path(i, j, entry, stop)
    R8, _, trig = base_path(i, j, entry, stop, hold8=True)
    R80, _, _ = base_path(i, j, entry, stop, horizon=80)
    R880, _, _ = base_path(i, j, entry, stop, hold8=True, horizon=80)
    rows.append(dict(date=C.index[i], sym=C.columns[j], R=cap(R), R8=cap(R8), R80=cap(R80), R880=cap(R880), trig=trig))
    piv = PV[i, j]
    for k in (3, 5, 10):
        ka = i + k
        if ka >= kx or ka >= N: continue          # base already out (exit at or before k)
        ca = Cv[ka, j]
        if not np.isfinite(ca): continue
        arisk = ca - entry
        up1 = (ca - entry) >= risk
        held = bool(np.all(Cv[i + 1:ka + 1, j] >= piv))
        r_add = np.nan
        if arisk >= FLOOR * ca:
            for m in range(ka + 1, min(i + 61, N)):
                c = Cv[m, j]
                if not np.isfinite(c): continue
                if c < entry or c < E[m, j]: r_add = net(ca, c) / arisk; break
            else:
                m = min(i + 60, N - 1); r_add = net(ca, Cv[m, j]) / arisk
        # base R from k onward in BASE units (what the unit already on earns after k): for "which trades to add to"
        adds.append(dict(date=C.index[i], sym=C.columns[j], k=k, U=True, A=up1, B=held, AB=up1 and held,
                         addR=cap(r_add) if np.isfinite(r_add) else np.nan, baseR=cap(R)))
T = pd.DataFrame(rows); A = pd.DataFrame(adds)
T["month"] = T.date.dt.to_period("M"); A["month"] = A.date.dt.to_period("M")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def mclust(s, months):
    m = pd.Series(s.values, index=months.values).groupby(level=0).mean(); return m.mean(), mt(m)


print(f"base book: {len(T):,} trades, {T.date.min().date()}..{T.date.max().date()}, {T.month.nunique()} months, {T.date.nunique()} dates")
mu, t = mclust(T.R, T.month)
print(f"  base R (cap 20, 2% floor) mean {T.R.mean():+.3f}  month-weighted mean {mu:+.3f} t {t:+.2f} | date-clustered t {mclust(T.R, T.date.dt.to_period("D"))[1]:+.2f}  median {T.R.median():+.2f}  win {100*(T.R>0).mean():.0f}%")

print("\n== TEST 1: PYRAMID -- the add's own R (units of its own risk, stop = base entry) ==")
print(f"{'k':>3} {'cond':>4} {'n live':>7} {'n add':>6} {'share':>6} {'add R':>7} {'t':>6} | {'base R of these trades':>22} | {'add - U (same k)':>16} {'t':>6} {'H1':>7} {'H2':>7}")
passed = []
for k in (3, 5, 10):
    a = A[A.k == k]; u = a[a.U].dropna(subset=["addR"])
    um = u.groupby("month").addR.mean()
    for cond in ("U", "A", "B", "AB"):
        x = a[a[cond]]; xa = x.dropna(subset=["addR"])
        mu, t = mclust(xa.addR, xa.month)
        xm = xa.groupby("month").addR.mean(); d = (xm - um).dropna()
        h1 = d[d.index < pd.Period("2023-01", "M")]; h2 = d[d.index >= pd.Period("2023-01", "M")]
        dt = mt(d) if cond != "U" else np.nan
        print(f"{k:>3} {cond:>4} {len(x):>7} {len(xa):>6} {len(x)/len(T):>6.0%} {xa.addR.mean():>+7.3f} {t:>+6.2f} | {x.baseR.mean():>+22.3f} | "
              f"{(d.mean() if cond!='U' else 0):>+16.3f} {dt:>+6.2f} {(h1.mean() if cond!='U' else 0):>+7.3f} {(h2.mean() if cond!='U' else 0):>+7.3f}")
        if cond != "U" and xa.addR.mean() > 0 and dt >= 2 and np.sign(h1.mean()) == np.sign(h2.mean()) == 1: passed.append(f"k={k} {cond}")
print("PRE-REGISTERED PASS (pyramid):", passed or "NONE")

print("\n== does the condition at k call the base trade's outcome? (the bimodality question, post-entry) ==")
for k in (3, 5, 10):
    a = A[A.k == k]
    for cond in ("A", "B", "AB"):
        y, n = a[a[cond]].baseR, a[~a[cond]].baseR
        print(f"  k={k:<2} {cond:<2}: base R if true {y.mean():+.3f} (n {len(y)}, win {100*(y>0).mean():.0f}%)  vs false {n.mean():+.3f} (n {len(n)})  "
              f"| dead before k: {len(T)-len(a)} trades")

print("\n== TEST 2: 8-WEEK HOLD (>= +20% within 15 sessions -> hold to session 40 unless it closes below entry) ==")
for lab, b, r in (("60-session cap", "R", "R8"), ("80-session cap", "R80", "R880")):
    d = T[r] - T[b]; mu, t = mclust(d, T.month)
    h1 = d[T.date < "2023-01-01"]; h2 = d[T.date >= "2023-01-01"]
    trg = T[T.trig]
    print(f"  {lab}: triggered {len(trg)} ({100*len(trg)/len(T):.1f}%) | base {T[b].mean():+.3f} -> rule {T[r].mean():+.3f} | paired {d.mean():+.3f}  t {t:+.2f}  "
          f"H1 {h1.mean():+.3f} H2 {h2.mean():+.3f} | on triggered: {trg[b].mean():+.2f} -> {trg[r].mean():+.2f}, rule better on {100*(trg[r]>trg[b]).mean():.0f}%")
d = T.R8 - T.R; _, t = mclust(d, T.month)
print("PRE-REGISTERED PASS (8-week):", "YES" if (t >= 2 and d[T.date < "2023-01-01"].mean() > 0 and d[T.date >= "2023-01-01"].mean() > 0) else "NO")
T.to_csv("data/studies/oneil_8wk_trades.csv", index=False); A.to_csv("data/studies/oneil_pyramid_adds.csv", index=False)

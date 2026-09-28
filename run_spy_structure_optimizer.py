#!/usr/bin/env python3
"""
STEP 2 of the SPY vol-selling structure search: a CVaR-constrained linear program over put legs, walk-forward
(pre-registered 2026-09-28, before any run).

INPUTS  step 1 (spy_leg_surface_2026-09-28.md): v3 actual legs 2010-01 -> 2026-02 (data/cache/spy_leg_surface_entries.parquet)
        stress scenario (spy_synthetic_stress_2026-09-28.md): synthetic puts 1993-02 -> 2009-12
        (data/cache/spy_synthetic_puts_1993_2009.parquet, CENTRAL skew, 1x spread, credits scaled 0.888).

PRE-REGISTRATION (frozen before the first run)
  Universe   PUTS ONLY (calls carry no premium on the surface and there is no synthetic GFC for them -- v2 if this
             pays), tenors 30 and 45 DTE (the only tenors the synthetic prices within 6-9%), 8 |delta| centres,
             each leg SHORT or LONG -> 32 non-negative variables. Structures this spans: naked puts, put verticals,
             ratio spreads, put flies / broken wings, 30/45 put calendars and diagonals.
  Legs       one contract per week, entered at Friday's close, held to expiry. Short net = mid - 25% ba - comm - payoff;
             long net = payoff - mid - 25% ba - comm (synthetic: mid x 0.888, ba backed out of the stored net).
             Units bp of SPY notional. A leg missing on a Friday contributes 0 that week.
  Scenarios  calendar MONTHS (sum of that month's weekly entries per leg) -- monthly aggregation keeps the tail
             clustering of overlapping positions inside one scenario. Split by the state on the entry Friday:
             STRESS (SPY < 50 SMA & VIX >= 20) and CALM.
  LP         maximise the SHRUNK mean monthly P&L subject to CVaR_5% (monthly) <= 100 bp (Rockafellar-Uryasev),
             weights >= 0. Shrinkage: each leg-side mean -> 0.5 x own + 0.5 x the mean of all 16 legs of its side.
             Leg cap 4: solve, keep the 4 largest weights, re-solve on those 4.
  Walk-fwd   test year Y = 2000 .. 2026 (2026 = Jan-Feb). Fit on all months before Y (1993 -> Y-1), per state;
             apply to Y. Every strategy is scaled so its IN-SAMPLE CVaR_5% = 100 bp, then judged on OOS P&L.
  Strategies OPT-STATE   optimised weights per state (stress set in stress months, calm set in calm months)
             OPT-STRESS  optimised stress weights, flat in calm
             NAKED       short 45d 10-delta put every week (the surface's cleanest stress leg, run all-weather)
             NAKED-S     the same, stress months only
             CERT        stress months only, short 30d 25-delta / long 30d 16-delta put vertical (closest grid cell to
                         the certified 0.25/0.15 bull put; that one is ~20 DTE, not on this grid)
  PRIMARY    OPT-STATE minus NAKED, OOS monthly P&L at equal in-sample CVaR, 2000-2026: t on months; both halves
             (2000-2012 / 2013-2026) the same sign. Bar |t| >= 3 to ADOPT; 2 <= |t| < 3 = lead (PARKED).
             Also reported: OOS mean, OOS CVaR_5%, mean / CVaR, worst month, max drawdown, GFC 2007-09 sum.
  Caveats    2000-2009 OOS outcomes are SYNTHETIC; the structures cannot use calls or other tenors; an LP with a
             CVaR budget is scale-free, so this ranks return per unit tail, not capital efficiency (margin is v2).

AMENDMENT v1.1 (2026-09-28, AFTER the v1 run -- a declared second look, charged as such). v1 FAILED on design:
  (a) the LP was unbounded in 2000-2011 (combos with no losing month in sample -> the CVaR budget never binds ->
  solver failure -> zero weights); (b) where it solved it chose a 2:1 put ratio spread with almost no in-sample tail,
  scaled it to 60-70 contracts/week, and Feb 2020 (a CALM-state entry) cost -24,397 bp. Fix, applied to TRAINING
  scenarios only: three deterministic CRASH MONTHS per state -- SPY finishes 10% / 20% / 30% below entry at expiry,
  all 4 weekly entries of the month at each leg's median premium and median strike/spot -- plus a gross cap of
  100 contracts/week. Everything else unchanged. v1 log kept: logs/spy_structure_optimizer_v1.log.

AMENDMENT v1.2 (third and FINAL look, 2026-09-28): v1.1 put the crash months into the MEAN as well as the tail;
  three synthetic crashes in 50-150 months imply a 2-6%/month crash rate, so long far-OTM puts looked profitable and
  the LP bought crash insurance by the dozen (2001: -52,105 bp). The crash rows now enter the CVaR constraint only.
  No further changes will be made to this design; v1.1 log kept: logs/spy_structure_optimizer_v1_1.log.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_structure_optimizer.py > data/studies/logs/spy_structure_optimizer.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linprog

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
SLIP, COMM, SCALE = 0.25, 0.0065, 0.888
DELTAS = [0.05, 0.10, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50]
TENORS = [30, 45]
ALPHA, BUDGET, CAP, SHRINK = 0.05, 100.0, 4, 0.5
LEGS = [(s, t, d) for s in ("S", "L") for t in TENORS for d in DELTAS]
LEGNAME = [f"{s}{t}p{int(d * 100):02d}" for s, t, d in LEGS]


def weekly_matrix() -> pd.DataFrame:
    """rows = Fridays 1993-2026, cols = 32 leg-sides (bp of notional, net), plus 'stress'."""
    A = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    A = A[(A.cp == "P") & A.dtgt.isin(TENORS) & (A.trade_date.dt.dayofweek == 4)].copy()
    A["short"] = A.bp_n
    A["long"] = (A.pay - A.mid - SLIP * A.ba - COMM) / A.S_0 * 1e4
    Y = pd.read_parquet("data/cache/spy_synthetic_puts_1993_2009.parquet")
    Y = Y[(Y["skew"] == "q50") & (Y.spread_mult == 1.0) & Y.dtgt.isin(TENORS) & (Y.trade_date.dt.dayofweek == 4)].copy()
    pay = np.maximum(Y.K - Y.S_T, 0)
    ba = (SCALE * Y.mid - COMM - pay - Y.bp_n * Y.S_0 / 1e4) / SLIP
    Y["short"] = Y.bp_n
    Y["long"] = (pay - SCALE * Y.mid - SLIP * ba - COMM) / Y.S_0 * 1e4
    cols = {}
    for src in (Y, A):
        for s, t, d in LEGS:
            g = src[(src.dtgt == t) & (src.dcen == d)].set_index("trade_date")["short" if s == "S" else "long"]
            name = f"{s}{t}p{int(d * 100):02d}"
            cols[name] = pd.concat([cols[name], g]) if name in cols else g
    global CRASH
    prem, mny = {}, {}
    for t in TENORS:
        for d in DELTAS:
            a = A[(A.dtgt == t) & (A.dcen == d)]; y = Y[(Y.dtgt == t) & (Y.dcen == d)]
            pr = pd.concat([a.mid / a.S_0, SCALE * y.mid / y.S_0]) * 1e4
            cst = pd.concat([(SLIP * a.ba + COMM) / a.S_0, (SLIP * ((SCALE * y.mid - COMM - np.maximum(y.K - y.S_T, 0) - y.bp_n * y.S_0 / 1e4) / SLIP) + COMM) / y.S_0]) * 1e4
            prem[(t, d)] = (pr.median(), cst.median())
            mny[(t, d)] = pd.concat([a.strike / a.S_0, y.K / y.S_0]).median()
    rows = []
    for x in (0.10, 0.20, 0.30):
        r = []
        for s_, t, d in LEGS:
            p, c = prem[(t, d)]
            pay = max(mny[(t, d)] - (1 - x), 0) * 1e4
            r.append(4 * ((p - c - pay) if s_ == "S" else (pay - p - c)))
        rows.append(r)
    CRASH = np.array(rows)
    print("crash months (bp, 4 entries): S45p05 %s | L45p10 %s" % (CRASH[:, LEGNAME.index("S45p05")].round(0), CRASH[:, LEGNAME.index("L45p10")].round(0)))
    W = pd.DataFrame(cols).sort_index()
    W = W[~W.index.duplicated()]
    st = pd.concat([Y.drop_duplicates("trade_date").set_index("trade_date").stress,
                    A.drop_duplicates("trade_date").set_index("trade_date").stress])
    st = st[~st.index.duplicated()]
    W["stress"] = st.reindex(W.index).fillna(False).astype(bool)
    return W


def monthly(W: pd.DataFrame, state: bool) -> pd.DataFrame:
    X = W[W.stress == state].drop(columns="stress").fillna(0.0)
    return X.groupby(X.index.to_period("M")).sum()


def cvar(p: np.ndarray, a=ALPHA) -> float:
    k = max(1, int(np.ceil(a * len(p))))
    return float(-np.sort(p)[:k].mean())


def solve(M: np.ndarray, allowed=None, n_crash: int = 3) -> np.ndarray:
    """max shrunk mean s.t. CVaR_a(M @ w) <= BUDGET, w >= 0. Variables: w (n), z (T), eta (free).
    v1.2: the last n_crash rows (deterministic crash months) enter the CVaR constraint ONLY, not the mean."""
    T, n = M.shape
    mu = M[:T - n_crash].mean(axis=0)
    half = n // 2
    mu_s = mu.copy()
    for sl in (slice(0, half), slice(half, n)):
        mu_s[sl] = (1 - SHRINK) * mu[sl] + SHRINK * mu[sl].mean()
    c = np.concatenate([-mu_s, np.zeros(T), [0.0]])
    # z_t >= -(M_t w) - eta  ->  -M_t w - eta - z_t <= 0
    A1 = np.hstack([-M, -np.eye(T), -np.ones((T, 1))])
    # eta + 1/(a T) sum z <= BUDGET
    A2 = np.concatenate([np.zeros(n), np.full(T, 1 / (ALPHA * T)), [1.0]])[None, :]
    A3 = np.concatenate([np.ones(n), np.zeros(T), [0.0]])[None, :]          # gross cap (v1.1)
    A = np.vstack([A1, A2, A3]); b = np.concatenate([np.zeros(T), [BUDGET], [100.0]])
    bounds = [(0, None if (allowed is None or allowed[i]) else 0) for i in range(n)] + [(0, None)] * T + [(None, None)]
    r = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    if not r.success:
        return np.zeros(n)
    w = r.x[:n]
    if allowed is None and (w > 1e-9).sum() > CAP:
        keep = np.zeros(n, bool); keep[np.argsort(-w)[:CAP]] = True
        return solve(M, keep, n_crash)
    return w


def scale_to_budget(w, M):
    c = cvar(M @ w)
    return w * (BUDGET / c) if c > 0 else w * 0


def fixed(names_w: dict) -> np.ndarray:
    w = np.zeros(len(LEGNAME))
    for k, v in names_w.items():
        w[LEGNAME.index(k)] = v
    return w


def main():
    W = weekly_matrix()
    print(f"weekly scenarios {W.index.min().date()} -> {W.index.max().date()}: {len(W):,} Fridays, stress share {W.stress.mean():.1%}")
    MS, MC = monthly(W, True), monthly(W, False)
    print(f"monthly scenarios: stress {len(MS)}, calm {len(MC)}")
    naked = fixed({"S45p10": 1.0})
    cert = fixed({"S30p25": 1.0, "L30p16": 1.0})
    oos = []           # rows: month, strategy, pnl
    picks = []
    for Y in range(2000, 2027):
        ins_s = MS[MS.index.year < Y]; ins_c = MC[MC.index.year < Y]
        out_s = MS[MS.index.year == Y]; out_c = MC[MC.index.year == Y]
        Ts = np.vstack([ins_s[LEGNAME].values, CRASH]); Tc = np.vstack([ins_c[LEGNAME].values, CRASH])   # v1.1
        ws = solve(Ts); wc = solve(Tc)
        ws = scale_to_budget(ws, Ts); wc = scale_to_budget(wc, Tc)
        # all-weather naked scaled on all in-sample months; stress-only versions scaled on stress months
        ins_all = pd.concat([ins_s, ins_c])
        Ta = np.vstack([ins_all[LEGNAME].values, CRASH])
        wn = scale_to_budget(naked, Ta)          # benchmarks scaled on the SAME crash-augmented sets (v1.1)
        wns = scale_to_budget(naked, Ts)
        wce = scale_to_budget(cert, Ts)
        picks.append(dict(year=Y, stress_legs={LEGNAME[i]: round(ws[i], 2) for i in np.flatnonzero(ws > 1e-6)},
                          calm_legs={LEGNAME[i]: round(wc[i], 2) for i in np.flatnonzero(wc > 1e-6)},
                          naked_w=round(wn[LEGNAME.index("S45p10")], 2), cert_w=round(wce[LEGNAME.index("S30p25")], 2)))
        for per, row in out_s[LEGNAME].iterrows():
            v = row.values
            oos += [(per, "OPT-STATE", v @ ws), (per, "OPT-STRESS", v @ ws), (per, "NAKED", v @ wn),
                    (per, "NAKED-S", v @ wns), (per, "CERT", v @ wce)]
        for per, row in out_c[LEGNAME].iterrows():
            v = row.values
            oos += [(per, "OPT-STATE", v @ wc), (per, "OPT-STRESS", 0.0), (per, "NAKED", v @ wn),
                    (per, "NAKED-S", 0.0), (per, "CERT", 0.0)]
    O = pd.DataFrame(oos, columns=["month", "strategy", "pnl"]).groupby(["month", "strategy"]).pnl.sum().unstack()
    O = O.fillna(0.0)
    print("\n== walk-forward picks (in-sample fit through Y-1; weights = contracts/week at CVaR_5% = 100 bp) ==")
    for p in picks:
        print(f"  {p['year']}: STRESS {{{', '.join(f'{k}:{float(v):.2f}' for k, v in p['stress_legs'].items())}}}  |  CALM {{{', '.join(f'{k}:{float(v):.2f}' for k, v in p['calm_legs'].items())}}}  | naked {p['naked_w']} cert {p['cert_w']}")
    rows = []
    for s in O.columns:
        x = O[s]; cum = x.cumsum()
        rows.append(dict(strategy=s, months=len(x), mean_bp=x.mean(), cvar5=cvar(x.values), mean_over_cvar=x.mean() / max(cvar(x.values), 1e-9),
                         worst_month=x.min(), max_dd=(cum - cum.cummax()).min(),
                         gfc_07_09=x[(x.index.year >= 2007) & (x.index.year <= 2009)].sum(),
                         h1=x[x.index.year <= 2012].mean(), h2=x[x.index.year >= 2013].mean()))
    R = pd.DataFrame(rows).set_index("strategy")
    print("\n== OUT-OF-SAMPLE 2000-2026 (monthly bp of notional, each scaled to in-sample CVaR_5% = 100 bp) ==")
    print(R.round(2).to_string())
    d = O["OPT-STATE"] - O["NAKED"]
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    h1, h2 = d[d.index.year <= 2012].mean(), d[d.index.year >= 2013].mean()
    verdict = "ADOPT" if abs(t) >= 3 and np.sign(h1) == np.sign(h2) == np.sign(t) and t > 0 else \
        ("LEAD (PARKED)" if t >= 2 and np.sign(h1) == np.sign(h2) else "NULL/FAIL")
    print(f"\nPRIMARY OPT-STATE - NAKED: {d.mean():+.2f} bp/month, t {t:+.2f}, halves {h1:+.2f} / {h2:+.2f} -> {verdict}")
    for other in ("OPT-STRESS", "CERT", "NAKED-S"):
        dd = O["OPT-STATE"] - O[other]
        print(f"  OPT-STATE - {other}: {dd.mean():+.2f} bp/month, t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f}")
    dd = O["OPT-STRESS"] - O["CERT"]
    print(f"  OPT-STRESS - CERT: {dd.mean():+.2f} bp/month, t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f}")
    yr = O.groupby(O.index.year).sum()
    print("\nper-year OOS sums (bp):"); print(yr.round(0).astype(int).to_string())
    O.to_csv("data/studies/logs/spy_structure_optimizer_oos.csv")


if __name__ == "__main__":
    main()

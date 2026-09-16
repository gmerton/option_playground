#!/usr/bin/env python3
"""
Rolling-short campaign study (2026-09-16, ETFs, chains to 85 DTE in data/cache/calendar_path_long):
buy the long legs ONCE at ~L DTE (long put / long call, same-strike or --widen % wider than the FIRST shorts), sell 0.35-delta
shorts on the weekly nearest 12 DTE, and at each short expiry settle the shorts at intrinsic and sell the next weekly's
shorts against the same longs (re-struck at 0.35 delta of the new expiry, capped at the long strike; or --fixed strikes),
until the next short would expire within 5 days of the longs. Then sell the longs at mid - slippage on the last short expiry.
Costs: every fill mid +/- 25% BA + $0.0065/sh. Max risk (for ROC) = initial net debit + wider wing (the campaign's initial
capital at risk); later credits reduce the risk but the denominator stays.
Baseline for each campaign: the sum of independent 12/19d 2%-diagonals (results_ddiag_wide.parquet, widen 2.0) entered on
the same Friday and every following Friday whose short expiry falls on or before the campaign's end -- i.e. "re-enter fresh"
over the same window with roughly the same weekly capital.
Usage: PYTHONPATH=src:. python run_dcal_roll_sim.py [--long-dte 27 40 55] [--widen 0 2] [--tickers IWM QQQ SPY]
"""
from __future__ import annotations
import argparse, os, sys
from datetime import timedelta
from pathlib import Path
import numpy as np, pandas as pd
os.environ.setdefault("CALPATH_CACHE", "data/cache/calendar_path_long")
from run_dcal_path_sim import load, leg, CACHE, SLIP, COMM

DP = 0.35; S_TARGET = 12; S_TOL = 4; MIN_TAIL = 5


def simulate(t, closes, vix, spy_up, long_dtes, widens, fixed):
    P, C = load(t, "P"), load(t, "C")
    if P.empty or C.empty: return []
    cl = closes[closes.ticker == t].set_index("date").close.sort_index()
    Pd = {d: g for d, g in P.groupby("trade_date")}; Cd = {d: g for d, g in C.groupby("trade_date")}
    days = sorted(set(Pd) & set(Cd)); out = []

    def short_strikes(d, se, cap_p=None, cap_c=None):
        gp, gc = Pd[d], Cd[d]; sp = gp[(gp.expiry == se) & gp.delta.notna()]; sc = gc[(gc.expiry == se) & gc.delta.notna()]
        if sp.empty or sc.empty: return None, None
        Kp = float(sp.iloc[(sp.delta + DP).abs().argsort()[:1]].strike.iloc[0]); Kc = float(sc.iloc[(sc.delta - DP).abs().argsort()[:1]].strike.iloc[0])
        if cap_p is not None: Kp = max(Kp, cap_p)          # never a short put below the long put
        if cap_c is not None: Kc = min(Kc, cap_c)
        return Kp, Kc

    def sell(row): return row.mid - SLIP * row.ba - COMM      # credit received
    def buy(row): return row.mid + SLIP * row.ba + COMM        # debit paid

    for L in long_dtes:
        for d in days:
            if pd.Timestamp(d).weekday() != 4 or d not in cl.index: continue
            spot = float(cl[d]); exps = sorted(Pd[d].expiry.unique())
            lo = [e for e in exps if L - 7 <= (e - d).days <= L + 7]
            if not lo: continue
            le = min(lo, key=lambda e: abs((e - d).days - L))
            sh = [e for e in exps if S_TARGET - S_TOL <= (e - d).days <= S_TARGET + S_TOL and (le - e).days >= MIN_TAIL]
            if not sh: continue
            se = min(sh, key=lambda e: abs((e - d).days - S_TARGET))
            Kp0, Kc0 = short_strikes(d, se)
            if Kp0 is None or Kp0 >= spot or Kc0 <= spot: continue
            for w in widens:
                ks_p = np.array(sorted(Pd[d][Pd[d].expiry == le].strike.unique())); ks_c = np.array(sorted(Cd[d][Cd[d].expiry == le].strike.unique()))
                lpk = ks_p[ks_p <= Kp0 * (1 - w / 100)] if w > 0 else ks_p[ks_p == Kp0]; lck = ks_c[ks_c >= Kc0 * (1 + w / 100)] if w > 0 else ks_c[ks_c == Kc0]
                if not len(lpk) or not len(lck): continue
                Kpl, Kcl = float(lpk.max()), float(lck.min())
                lp, lc = leg(Pd[d], le, Kpl), leg(Cd[d], le, Kcl); sp, sc = leg(Pd[d], se, Kp0), leg(Cd[d], se, Kc0)
                if any(v is None for v in (lp, lc, sp, sc)): continue
                long_cost = buy(lp) + buy(lc); credit0 = sell(sp) + sell(sc)
                net0 = long_cost - credit0; width = max(Kp0 - Kpl, Kcl - Kc0); maxrisk = net0 + width
                if maxrisk <= 0.01: continue
                pnl = -long_cost + credit0; rolls = 0; Kp, Kc = Kp0, Kc0; cur_se = se; ok = True; roll_log = []
                # walk the short expiries
                while True:
                    ST = float(cl.get(cur_se, np.nan))
                    if np.isnan(ST) or cur_se not in Pd: ok = False; break
                    pnl -= max(Kp - ST, 0) + max(ST - Kc, 0)            # settle the shorts at intrinsic
                    nxt = [e for e in sorted(Pd[cur_se].expiry.unique()) if 5 <= (e - cur_se).days <= 9 and (le - e).days >= MIN_TAIL]
                    if not nxt: break
                    ne = min(nxt, key=lambda e: abs((e - cur_se).days - 7))
                    if fixed: nKp, nKc = Kp0, Kc0
                    else:
                        nKp, nKc = short_strikes(cur_se, ne, cap_p=Kpl, cap_c=Kcl)
                        if nKp is None: break
                    nsp, nsc = leg(Pd[cur_se], ne, nKp), leg(Cd[cur_se], ne, nKc)
                    if nsp is None or nsc is None: break
                    cr = sell(nsp) + sell(nsc); pnl += cr; rolls += 1; roll_log.append(cr); Kp, Kc, cur_se = nKp, nKc, ne
                if not ok: continue
                # sell the longs on the last short expiry
                lp_e, lc_e = leg(Pd[cur_se], le, Kpl), leg(Cd[cur_se], le, Kcl)
                if lp_e is None or lc_e is None: continue
                pnl += sell(lp_e) + sell(lc_e)
                out.append(dict(ticker=t, long_dte=L, widen=w, fixed=fixed, entry=d, spot=spot, long_exp=le, first_short=se, end=cur_se, days=(cur_se - d).days,
                                Kp0=Kp0, Kc0=Kc0, Kpl=Kpl, Kcl=Kcl, long_cost=long_cost, credit0=credit0, net0=net0, width=width, maxrisk=maxrisk,
                                rolls=rolls, roll_credit=sum(roll_log), pnl=pnl, vix=vix.get(d, np.nan), spy_up=spy_up.get(d, np.nan)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", nargs="*", default=["IWM", "QQQ", "SPY"]); ap.add_argument("--long-dte", nargs="*", type=int, default=[27, 40, 55])
    ap.add_argument("--widen", nargs="*", type=float, default=[0, 2.0]); ap.add_argument("--fixed", action="store_true"); ap.add_argument("--out", default=str(CACHE / "results_roll.parquet")); a = ap.parse_args()
    closes = pd.read_parquet(CACHE / "closes.parquet"); closes["date"] = pd.to_datetime(closes.date).dt.date
    vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix = pd.Series(vix.vix_close.values, index=pd.to_datetime(vix.trade_date).dt.date)
    spy = closes[closes.ticker == "SPY"].set_index("date").close.sort_index(); spy_up = (spy > spy.rolling(50).mean()).astype(float)
    rows = []
    for t in a.tickers:
        r = simulate(t, closes, vix, spy_up, a.long_dte, a.widen, a.fixed); rows += r; print(f"{t}: {len(r)} campaigns", flush=True)
    R = pd.DataFrame(rows); R.to_parquet(a.out, index=False); print(f"wrote {a.out}: {len(R)} rows"); return 0


if __name__ == "__main__":
    sys.exit(main())

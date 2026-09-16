#!/usr/bin/env python3
"""
Step 4 of the calendar path study (2026-09-15): DOUBLE calendars on real daily bid/ask (put calendar below + call calendar
above, same two expiries), IWM / SPY / QQQ. Needs chain_<T>_<yr>.parquet (puts) and chainC_<T>_<yr>.parquet (calls)
from run_calendar_path_pull.py.

Entries every Friday; structures DCAL (short ~12 / long ~19 DTE) and ETF (~20 / ~27); strike sets by the SHORT leg's
delta on the entry day: sym25 (0.25P / 0.25C), sym35 (0.35P / 0.35C, the SPY playbook's Bullish_LowIV cell),
asym35_10 (0.35P / 0.10C, the Bearish_HighIV cell). Long legs at the same strikes. Costs: mid +/- 25% BA per leg +
$0.0065/sh/leg. Short legs settle at intrinsic at the short expiry; longs sold at mid - slippage.
Variants (daily closes): hold | pt25/50/75 | stop40/60 | recenter2s (2-sigma move: close all, re-open the same strike
set ATM-relative, once) | inversion (put short IV > put long IV x 1.05) | drop_far (when the close crosses a short
strike with >= 2 days left, close the OTHER side's calendar at its marks, hold the tested side) | close_far50 (close a
side when its mark <= 50% of its own entry debit).
Usage: PYTHONPATH=src python run_dcal_path_sim.py [--tickers IWM SPY QQQ] [--out data/cache/calendar_path/results_dcal.parquet]
"""
from __future__ import annotations
import argparse, glob, sys
from datetime import timedelta
from pathlib import Path
import numpy as np, pandas as pd

import os
CACHE = Path(os.environ.get("CALPATH_CACHE", "data/cache/calendar_path")); SLIP, COMM = 0.25, 0.0065
# CALPATH_STRUCTS="M30g7:30:5:37,M30g14:30:5:44,L49g7:49:7:56,L49g27:49:7:76" -> name:short_dte:short_tol:long_dte
STRUCTS = ({k: (int(a), int(b), int(c)) for k, a, b, c in (x.split(":") for x in os.environ["CALPATH_STRUCTS"].split(","))}
           if os.environ.get("CALPATH_STRUCTS") else {"DCAL": (12, 3, 19), "ETF": (20, 5, 27)}); GAP_LO, GAP_HI = 5, 35
SETS = {"sym25": (0.25, 0.25), "sym35": (0.35, 0.35), "asym35_10": (0.35, 0.10)}
PT = (0.25, 0.50, 0.75); STOPS = (0.40, 0.60); INV = 1.05; MIN_LEFT = 2; RECENTER_SIG = 2.0


def load(t: str, cp: str) -> pd.DataFrame:
    fs = sorted(glob.glob(str(CACHE / (f"chain_{t}_*.parquet" if cp == "P" else f"chainC_{t}_*.parquet"))))
    if not fs: return pd.DataFrame()
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d = d[(d.ask > 0) & (d.bid >= 0) & (d.ask >= d.bid) & (d.ask < 9999)].copy()
    d["mid"] = (d.bid + d.ask) / 2; d["ba"] = d.ask - d.bid
    d["iv"] = np.where((d.bid_iv > 0) & (d.ask_iv > 0), (d.bid_iv + d.ask_iv) / 2, np.nan)
    d["trade_date"] = pd.to_datetime(d.trade_date).dt.date; d["expiry"] = pd.to_datetime(d.expiry).dt.date
    return d.sort_values("ba").drop_duplicates(["trade_date", "expiry", "strike"], keep="first")


def leg(g, exp, k):
    r = g[(g.expiry == exp) & (g.strike == k)]
    return r.iloc[0] if len(r) else None


def simulate(t: str, closes, vix, spy_up):
    P, C = load(t, "P"), load(t, "C")
    if P.empty or C.empty: return []
    cl = closes[closes.ticker == t].set_index("date").close.sort_index(); sd = cl.pct_change().rolling(20).std()
    Pd = {d: g for d, g in P.groupby("trade_date")}; Cd = {d: g for d, g in C.groupby("trade_date")}
    days = sorted(set(Pd) & set(Cd)); out = []

    def open_pos(d, se, le, dp, dc, spot):
        gp, gc = Pd[d], Cd[d]
        sp = gp[(gp.expiry == se) & gp.delta.notna()]; sc = gc[(gc.expiry == se) & gc.delta.notna()]
        if sp.empty or sc.empty: return None
        Kp = float(sp.iloc[(sp.delta + dp).abs().argsort()[:1]].strike.iloc[0]); Kc = float(sc.iloc[(sc.delta - dc).abs().argsort()[:1]].strike.iloc[0])
        if Kp >= spot or Kc <= spot: return None
        legs = dict(sp=leg(gp, se, Kp), lp=leg(gp, le, Kp), sc=leg(gc, se, Kc), lc=leg(gc, le, Kc))
        if any(v is None for v in legs.values()): return None
        dbp = legs["lp"].mid - legs["sp"].mid; dbc = legs["lc"].mid - legs["sc"].mid
        if dbp <= 0.01 or dbc <= 0.0: return None
        cost = dbp + dbc + SLIP * sum(v.ba for v in legs.values()) + 4 * COMM
        return dict(Kp=Kp, Kc=Kc, dbp=dbp, dbc=dbc, debit=dbp + dbc, cost=cost, ba=sum(v.ba for v in legs.values()), iv_sp=legs["sp"].iv, iv_lp=legs["lp"].iv)

    def path(d0, se, le, Kp, Kc):
        rows = []
        for dd in days:
            if dd <= d0 or dd > se: continue
            gp, gc = Pd[dd], Cd[dd]; a, b, c, e = leg(gp, se, Kp), leg(gp, le, Kp), leg(gc, se, Kc), leg(gc, le, Kc)
            if any(v is None for v in (a, b, c, e)): continue
            rows.append(dict(d=dd, S=float(cl.get(dd, np.nan)), sp=a.mid, spb=a.ba, lp=b.mid, lpb=b.ba, sc=c.mid, scb=c.ba, lc=e.mid, lcb=e.ba, ivs=a.iv, ivl=b.iv))
        return pd.DataFrame(rows)

    def close_all(r):   # exit both calendars at that day's marks
        return (r.lp - SLIP * r.lpb - COMM) - (r.sp + SLIP * r.spb + COMM) + (r.lc - SLIP * r.lcb - COMM) - (r.sc + SLIP * r.scb + COMM)
    def close_put(r): return (r.lp - SLIP * r.lpb - COMM) - (r.sp + SLIP * r.spb + COMM)
    def close_call(r): return (r.lc - SLIP * r.lcb - COMM) - (r.sc + SLIP * r.scb + COMM)
    def settle(last, Kp, Kc, ST, se):
        if pd.notna(ST) and last.d == se:
            return (last.lp - SLIP * last.lpb - COMM) - max(Kp - ST, 0) + (last.lc - SLIP * last.lcb - COMM) - max(ST - Kc, 0)
        return close_all(last)
    def settle_put(last, Kp, ST, se): return ((last.lp - SLIP * last.lpb - COMM) - max(Kp - ST, 0)) if (pd.notna(ST) and last.d == se) else close_put(last)
    def settle_call(last, Kc, ST, se): return ((last.lc - SLIP * last.lcb - COMM) - max(ST - Kc, 0)) if (pd.notna(ST) and last.d == se) else close_call(last)

    for sname, (sdte, stol, ldte) in STRUCTS.items():
        for d in days:
            if pd.Timestamp(d).weekday() != 4 or d not in cl.index: continue
            spot = float(cl[d]); exps = sorted(Pd[d].expiry.unique())
            sh = [e for e in exps if sdte - stol <= (e - d).days <= sdte + stol]
            if not sh: continue
            se = min(sh, key=lambda e: abs((e - d).days - sdte)); lo = [e for e in exps if GAP_LO <= (e - se).days <= GAP_HI]
            if not lo: continue
            le = min(lo, key=lambda e: abs((e - se).days - (ldte - sdte))); ST = float(cl.get(se, np.nan)); sig = sd.get(d, np.nan)
            for setn, (dp, dc) in SETS.items():
                o = open_pos(d, se, le, dp, dc, spot)
                if o is None: continue
                Pth = path(d, se, le, o["Kp"], o["Kc"])
                if Pth.empty: continue
                last = Pth.iloc[-1]; left = pd.Series([(se - x).days for x in Pth.d]); marks = (Pth.lp - Pth.sp) + (Pth.lc - Pth.sc)
                res = dict(ticker=t, struct=sname, dset=setn, entry=d, spot=spot, Kp=o["Kp"], Kc=o["Kc"], short_exp=se, long_exp=le, sdte=(se - d).days, gap=(le - se).days,
                           debit=o["debit"], cost=o["cost"], ba_pct=100 * o["ba"] / o["debit"], iv_sp=o["iv_sp"], vix=vix.get(d, np.nan), spy_up=spy_up.get(d, np.nan),
                           width_pct=100 * (o["Kc"] - o["Kp"]) / spot)
                res["hold"] = settle(last, o["Kp"], o["Kc"], ST, se) - o["cost"]; res["days"] = len(Pth)
                for x in PT:
                    hit = Pth[(marks >= o["debit"] * (1 + x)) & (left > 0)]; res[f"pt{int(100*x)}"] = (close_all(hit.iloc[0]) - o["cost"]) if len(hit) else res["hold"]
                for x in STOPS:
                    hit = Pth[(marks <= o["debit"] * (1 - x)) & (left > 0)]; res[f"stop{int(100*x)}"] = (close_all(hit.iloc[0]) - o["cost"]) if len(hit) else res["hold"]
                inv = Pth[(Pth.ivs > Pth.ivl * INV) & (left > 0)]; res["inversion"] = (close_all(inv.iloc[0]) - o["cost"]) if len(inv) else res["hold"]
                # drop_far: first close beyond a short strike with >= MIN_LEFT days left -> close the other side, hold the tested side
                res["drop_far"] = res["hold"]
                x = Pth[((Pth.S <= o["Kp"]) | (Pth.S >= o["Kc"])) & (left >= MIN_LEFT)]
                if len(x):
                    r0 = x.iloc[0]
                    if r0.S <= o["Kp"]:   # put side tested: close the call calendar now, settle the put calendar
                        res["drop_far"] = close_call(r0) + settle_put(last, o["Kp"], ST, se) - o["cost"]
                    else:
                        res["drop_far"] = close_put(r0) + settle_call(last, o["Kc"], ST, se) - o["cost"]
                # close_far50: a side whose mark <= 50% of its entry debit is closed; the other settles
                res["close_far50"] = res["hold"]
                pm, cm = (Pth.lp - Pth.sp), (Pth.lc - Pth.sc)
                xp = Pth[(pm <= 0.5 * o["dbp"]) & (left > 0)]; xc = Pth[(cm <= 0.5 * o["dbc"]) & (left > 0)]
                if len(xp) and (not len(xc) or xp.index[0] <= xc.index[0]):
                    res["close_far50"] = close_put(xp.iloc[0]) + settle_call(last, o["Kc"], ST, se) - o["cost"]
                elif len(xc):
                    res["close_far50"] = close_call(xc.iloc[0]) + settle_put(last, o["Kp"], ST, se) - o["cost"]
                # recenter once on a 2-sigma move: close all, re-open the same delta set, same expiries
                res["recenter2s"] = res["hold"]
                if pd.notna(sig) and sig > 0:
                    tr = Pth[((Pth.S / spot - 1).abs() >= RECENTER_SIG * sig) & (left >= MIN_LEFT)]
                    if len(tr):
                        r0 = tr.iloc[0]; o2 = open_pos(r0.d, se, le, dp, dc, float(r0.S))
                        if o2 is not None:
                            P2 = path(r0.d, se, le, o2["Kp"], o2["Kc"])
                            if not P2.empty:
                                res["recenter2s"] = (close_all(r0) - o["cost"]) + (settle(P2.iloc[-1], o2["Kp"], o2["Kc"], ST, se) - o2["cost"])
                out.append(res)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", nargs="*", default=["IWM", "SPY", "QQQ"]); ap.add_argument("--out", default=str(CACHE / "results_dcal.parquet"))
    ap.add_argument("--universe-file", default=None); a = ap.parse_args()
    if a.universe_file: a.tickers = [l.strip().upper() for l in open(a.universe_file) if l.strip()]
    closes = pd.read_parquet(CACHE / "closes.parquet"); closes["date"] = pd.to_datetime(closes.date).dt.date
    sc = CACHE / "spot_chain.parquet"
    if sc.exists():   # single names: the option table's strikes are unadjusted, so levels come from the chain's parity spot
        S_ = pd.read_parquet(sc); S_["date"] = pd.to_datetime(S_.date).dt.date
        closes = pd.concat([closes[~closes.ticker.isin(S_.ticker.unique())], S_[["date", "close", "ticker"]]], ignore_index=True)
    vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix = pd.Series(vix.vix_close.values, index=pd.to_datetime(vix.trade_date).dt.date)
    spy = closes[closes.ticker == "SPY"].set_index("date").close.sort_index(); spy_up = (spy > spy.rolling(50).mean()).astype(float)
    rows = []
    for t in a.tickers:
        r = simulate(t, closes, vix, spy_up); rows += r; print(f"{t}: {len(r)} double calendars", flush=True)
    R = pd.DataFrame(rows)
    if R.empty:
        print("no calendars built -- check that both chain_ (puts) and chainC_ (calls) files exist for these tickers"); return 1
    ep = CACHE / "earnings.parquet"
    if ep.exists() and len(R):        # earnings inside the trade window (entry, long expiry] -- single names
        E = pd.read_parquet(ep); E["edate"] = pd.to_datetime(E.edate).dt.date; by = {t: sorted(g.edate) for t, g in E.groupby("ticker")}
        R["earn_in_win"] = [any(r.entry < e <= r.long_exp for e in by.get(r.ticker, [])) for r in R.itertuples()]
    R.to_parquet(a.out, index=False); print(f"wrote {a.out}: {len(R)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())

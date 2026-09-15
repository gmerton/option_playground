#!/usr/bin/env python3
"""
Double DIAGONAL test (2026-09-15): same Friday entries, expiries and SHORT strikes as the sym35 double calendar in
run_dcal_path_sim.py, but the LONG legs sit wider: long put at the largest long-expiry strike <= Kp*(1-w), long call at the
smallest strike >= Kc*(1+w), w in --widen (percent of spot; 0 = the double calendar itself, the paired control).
Costs as the calendar sim (mid +/- 25% BA per leg + $0.0065/sh/leg). Shorts settle at intrinsic at the short expiry,
longs sold at mid - slippage. Max risk = cost + max(put width, call width) (only one wing can be breached at expiry);
ROC is reported on BOTH cost (the calendar convention) and max risk (the fair diagonal convention).
Variants: hold | pt25/50/75 (of max risk) | stop40/60 (of max risk).
Usage: PYTHONPATH=src python run_ddiag_path_sim.py [--tickers IWM SPY QQQ] [--widen 0 0.5 1.0]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
from run_dcal_path_sim import load, leg, CACHE, SLIP, COMM, STRUCTS, GAP_LO, GAP_HI

DP, DC = 0.35, 0.35; PT = (0.25, 0.50, 0.75); STOPS = (0.40, 0.60)


def simulate(t, closes, vix, spy_up, widens):
    P, C = load(t, "P"), load(t, "C")
    if P.empty or C.empty: return []
    cl = closes[closes.ticker == t].set_index("date").close.sort_index()
    Pd = {d: g for d, g in P.groupby("trade_date")}; Cd = {d: g for d, g in C.groupby("trade_date")}
    days = sorted(set(Pd) & set(Cd)); out = []

    def long_strikes(d, le, Kp, Kc, w):
        if w == 0: return Kp, Kc
        ks_p = np.array(sorted(Pd[d][Pd[d].expiry == le].strike.unique())); ks_c = np.array(sorted(Cd[d][Cd[d].expiry == le].strike.unique()))
        lp = ks_p[ks_p <= Kp * (1 - w / 100)]; lc = ks_c[ks_c >= Kc * (1 + w / 100)]
        if not len(lp) or not len(lc): return None, None
        return float(lp.max()), float(lc.min())

    def close_all(r): return (r.lp - SLIP * r.lpb - COMM) - (r.sp + SLIP * r.spb + COMM) + (r.lc - SLIP * r.lcb - COMM) - (r.sc + SLIP * r.scb + COMM)

    for sname, (sdte, stol, ldte) in STRUCTS.items():
        for d in days:
            if pd.Timestamp(d).weekday() != 4 or d not in cl.index: continue
            spot = float(cl[d]); exps = sorted(Pd[d].expiry.unique())
            sh = [e for e in exps if sdte - stol <= (e - d).days <= sdte + stol]
            if not sh: continue
            se = min(sh, key=lambda e: abs((e - d).days - sdte)); lo = [e for e in exps if GAP_LO <= (e - se).days <= GAP_HI]
            if not lo: continue
            le = min(lo, key=lambda e: abs((e - se).days - (ldte - sdte))); ST = float(cl.get(se, np.nan))
            gp, gc = Pd[d], Cd[d]
            sp = gp[(gp.expiry == se) & gp.delta.notna()]; sc = gc[(gc.expiry == se) & gc.delta.notna()]
            if sp.empty or sc.empty: continue
            Kp = float(sp.iloc[(sp.delta + DP).abs().argsort()[:1]].strike.iloc[0]); Kc = float(sc.iloc[(sc.delta - DC).abs().argsort()[:1]].strike.iloc[0])
            if Kp >= spot or Kc <= spot: continue
            for w in widens:
                Kpl, Kcl = long_strikes(d, le, Kp, Kc, w)
                if Kpl is None: continue
                legs = dict(sp=leg(gp, se, Kp), lp=leg(gp, le, Kpl), sc=leg(gc, se, Kc), lc=leg(gc, le, Kcl))
                if any(v is None for v in legs.values()): continue
                dbp = legs["lp"].mid - legs["sp"].mid; dbc = legs["lc"].mid - legs["sc"].mid
                if w == 0 and (dbp <= 0.01 or dbc <= 0.0): continue
                ba = sum(v.ba for v in legs.values()); cost = dbp + dbc + SLIP * ba + 4 * COMM
                wp, wc = Kp - Kpl, Kcl - Kc; maxrisk = cost + max(wp, wc)
                if maxrisk <= 0.01: continue
                rows = []
                for dd in days:
                    if dd <= d or dd > se: continue
                    g1, g2 = Pd[dd], Cd[dd]; a, b, c, e = leg(g1, se, Kp), leg(g1, le, Kpl), leg(g2, se, Kc), leg(g2, le, Kcl)
                    if any(v is None for v in (a, b, c, e)): continue
                    rows.append(dict(d=dd, S=float(cl.get(dd, np.nan)), sp=a.mid, spb=a.ba, lp=b.mid, lpb=b.ba, sc=c.mid, scb=c.ba, lc=e.mid, lcb=e.ba))
                Pth = pd.DataFrame(rows)
                if Pth.empty: continue
                last = Pth.iloc[-1]; left = pd.Series([(se - x).days for x in Pth.d]); marks = (Pth.lp - Pth.sp) + (Pth.lc - Pth.sc)
                if pd.notna(ST) and last.d == se:
                    fin = (last.lp - SLIP * last.lpb - COMM) - max(Kp - ST, 0) + (last.lc - SLIP * last.lcb - COMM) - max(ST - Kc, 0)
                else:
                    fin = close_all(last)
                res = dict(ticker=t, struct=sname, widen=w, entry=d, spot=spot, Kp=Kp, Kc=Kc, Kpl=Kpl, Kcl=Kcl, short_exp=se, long_exp=le,
                           debit=dbp + dbc, cost=cost, maxrisk=maxrisk, ba_pct=100 * ba / max(dbp + dbc, 0.01), vix=vix.get(d, np.nan), spy_up=spy_up.get(d, np.nan),
                           width_pct=100 * (Kc - Kp) / spot, ST=ST)
                res["hold"] = fin - cost; res["days"] = len(Pth)
                pnl = marks - cost   # mark-to-mid P&L path (no exit slippage until closed)
                for x in PT:
                    hit = Pth[(pnl >= maxrisk * x) & (left > 0)]; res[f"pt{int(100*x)}"] = (close_all(hit.iloc[0]) - cost) if len(hit) else res["hold"]
                for x in STOPS:
                    hit = Pth[(pnl <= -maxrisk * x) & (left > 0)]; res[f"stop{int(100*x)}"] = (close_all(hit.iloc[0]) - cost) if len(hit) else res["hold"]
                out.append(res)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", nargs="*", default=["IWM", "SPY", "QQQ"]); ap.add_argument("--widen", nargs="*", type=float, default=[0, 0.5, 1.0])
    ap.add_argument("--out", default=str(CACHE / "results_ddiag.parquet")); ap.add_argument("--universe-file", default=None); a = ap.parse_args()
    if a.universe_file: a.tickers = [l.strip().upper() for l in open(a.universe_file) if l.strip()]
    closes = pd.read_parquet(CACHE / "closes.parquet"); closes["date"] = pd.to_datetime(closes.date).dt.date
    sc = CACHE / "spot_chain.parquet"
    if sc.exists():   # single names: strikes are unadjusted, levels come from the chain's parity spot
        S_ = pd.read_parquet(sc); S_["date"] = pd.to_datetime(S_.date).dt.date
        closes = pd.concat([closes[~closes.ticker.isin(S_.ticker.unique())], S_[["date", "close", "ticker"]]], ignore_index=True)
    vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix = pd.Series(vix.vix_close.values, index=pd.to_datetime(vix.trade_date).dt.date)
    spy = closes[closes.ticker == "SPY"].set_index("date").close.sort_index(); spy_up = (spy > spy.rolling(50).mean()).astype(float)
    rows = []
    for t in a.tickers:
        r = simulate(t, closes, vix, spy_up, a.widen); rows += r; print(f"{t}: {len(r)} rows", flush=True)
    R = pd.DataFrame(rows)
    if R.empty: print("no rows"); return 1
    ep = CACHE / "earnings.parquet"
    if ep.exists():
        E = pd.read_parquet(ep); E["edate"] = pd.to_datetime(E.edate).dt.date; by = {t: sorted(g.edate) for t, g in E.groupby("ticker")}
        R["earn_in_win"] = [any(r.entry < e <= r.long_exp for e in by.get(r.ticker, [])) for r in R.itertuples()]
    R.to_parquet(a.out, index=False); print(f"wrote {a.out}: {len(R)} rows"); return 0


if __name__ == "__main__":
    sys.exit(main())

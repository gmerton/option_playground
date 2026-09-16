#!/usr/bin/env python3
"""
Paired iron condor vs double diagonal (2026-09-16, ETFs, main 40-DTE cache). Same Friday entries, same 0.35-delta
shorts on the same short expiry as the sym35 doubles (run_dcal_path_sim structure selection replicated so the entry set
matches). Two condors, all four legs in the SHORT expiry:
  IC_w2  : wings at the diagonal's long strikes (largest strike <= Kp x 0.98 / smallest >= Kc x 1.02)
  IC_d10 : wings at 0.10 delta
Credit = shorts sold at mid - 25% BA - comm, wings bought at mid + 25% BA + comm. Max risk = wider wing width - credit.
Hold: settle at intrinsic on the short expiry. Variants on daily marks: pt50 (close when mark <= 50% of credit), stop2x
(close when mark >= 2x credit), exit_m1 (close the day before expiry).
Usage: PYTHONPATH=src:. python run_ic_vs_dcal_sim.py [--tickers IWM QQQ SPY]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
from run_dcal_path_sim import load, leg, CACHE, SLIP, COMM, STRUCTS, GAP_LO, GAP_HI

DP = 0.35; WING_D = 0.10; W2 = 0.02


def simulate(t, closes, vix, spy_up):
    P, C = load(t, "P"), load(t, "C")
    if P.empty or C.empty: return []
    cl = closes[closes.ticker == t].set_index("date").close.sort_index()
    Pd = {d: g for d, g in P.groupby("trade_date")}; Cd = {d: g for d, g in C.groupby("trade_date")}
    days = sorted(set(Pd) & set(Cd)); out = []
    def sell(r): return r.mid - SLIP * r.ba - COMM
    def buy(r): return r.mid + SLIP * r.ba + COMM
    for sname, (sdte, stol, ldte) in STRUCTS.items():
        for d in days:
            if pd.Timestamp(d).weekday() != 4 or d not in cl.index: continue
            spot = float(cl[d]); exps = sorted(Pd[d].expiry.unique())
            sh = [e for e in exps if sdte - stol <= (e - d).days <= sdte + stol]
            if not sh: continue
            se = min(sh, key=lambda e: abs((e - d).days - sdte)); lo = [e for e in exps if GAP_LO <= (e - se).days <= GAP_HI]
            if not lo: continue
            ST = float(cl.get(se, np.nan))
            gp, gc = Pd[d], Cd[d]; sp = gp[(gp.expiry == se) & gp.delta.notna()]; sc = gc[(gc.expiry == se) & gc.delta.notna()]
            if sp.empty or sc.empty: continue
            Kp = float(sp.iloc[(sp.delta + DP).abs().argsort()[:1]].strike.iloc[0]); Kc = float(sc.iloc[(sc.delta - DP).abs().argsort()[:1]].strike.iloc[0])
            if Kp >= spot or Kc <= spot: continue
            ks_p = np.array(sorted(sp.strike.unique())); ks_c = np.array(sorted(sc.strike.unique()))
            wings = {}
            lp2 = ks_p[ks_p <= Kp * (1 - W2)]; lc2 = ks_c[ks_c >= Kc * (1 + W2)]
            if len(lp2) and len(lc2): wings["IC_w2"] = (float(lp2.max()), float(lc2.min()))
            wp = sp[sp.strike < Kp]; wc = sc[sc.strike > Kc]
            if len(wp) and len(wc):
                wings["IC_d10"] = (float(wp.iloc[(wp.delta + WING_D).abs().argsort()[:1]].strike.iloc[0]), float(wc.iloc[(wc.delta - WING_D).abs().argsort()[:1]].strike.iloc[0]))
            for ic, (Kpl, Kcl) in wings.items():
                if Kpl >= Kp or Kcl <= Kc: continue
                legs = dict(sp=leg(gp, se, Kp), sc=leg(gc, se, Kc), lp=leg(gp, se, Kpl), lc=leg(gc, se, Kcl))
                if any(v is None for v in legs.values()): continue
                credit = sell(legs["sp"]) + sell(legs["sc"]) - buy(legs["lp"]) - buy(legs["lc"])
                width = max(Kp - Kpl, Kcl - Kc); maxrisk = width - credit
                if credit <= 0.01 or maxrisk <= 0.01: continue
                rows = []
                for dd in days:
                    if dd <= d or dd > se: continue
                    g1, g2 = Pd[dd], Cd[dd]; a, b, c, e = leg(g1, se, Kp), leg(g2, se, Kc), leg(g1, se, Kpl), leg(g2, se, Kcl)
                    if any(v is None for v in (a, b, c, e)): continue
                    rows.append(dict(d=dd, mark=a.mid + b.mid - c.mid - e.mid, close_cost=buy(a) + buy(b) - sell(c) - sell(e)))
                Pth = pd.DataFrame(rows)
                if pd.isna(ST) and Pth.empty: continue
                # settlement is pure intrinsic at expiry -- never depends on chain rows (the pull's price/delta window drops
                # deep-ITM legs after big moves, which truncated the path and hid the losses before this fix, 2026-09-16)
                if pd.notna(ST):
                    hold = credit - (max(Kp - ST, 0) - max(Kpl - ST, 0)) - (max(ST - Kc, 0) - max(ST - Kcl, 0))
                else:
                    hold = credit - Pth.iloc[-1].close_cost
                if Pth.empty: Pth = pd.DataFrame([dict(d=d, mark=credit, close_cost=credit)])
                last = Pth.iloc[-1]; left = pd.Series([(se - x).days for x in Pth.d]); truncated = int(last.d != se)
                res = dict(ticker=t, struct=sname, ic=ic, entry=d, spot=spot, short_exp=se, Kp=Kp, Kc=Kc, Kpl=Kpl, Kcl=Kcl, credit=credit, width=width, maxrisk=maxrisk,
                           vix=vix.get(d, np.nan), spy_up=spy_up.get(d, np.nan), ST=ST, hold=hold, truncated=truncated)
                hit = Pth[(Pth.mark <= 0.5 * credit) & (left > 0)]; res["pt50"] = (credit - hit.iloc[0].close_cost) if len(hit) else hold
                hit = Pth[(Pth.mark >= 2.0 * credit) & (left > 0)]; res["stop2x"] = (credit - hit.iloc[0].close_cost) if len(hit) else hold
                early = Pth[left >= 1]; res["exit_m1"] = (credit - early.iloc[-1].close_cost) if len(early) else hold
                out.append(res)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", nargs="*", default=["IWM", "QQQ", "SPY"]); ap.add_argument("--out", default=str(CACHE / "results_ic.parquet"))
    ap.add_argument("--universe-file", default=None); a = ap.parse_args()
    if a.universe_file: a.tickers = [l.strip().upper() for l in open(a.universe_file) if l.strip()]
    closes = pd.read_parquet(CACHE / "closes.parquet"); closes["date"] = pd.to_datetime(closes.date).dt.date
    sc = CACHE / "spot_chain.parquet"
    if sc.exists():   # single names: unadjusted strikes -> parity spot from the chain (as in run_dcal_path_sim)
        S_ = pd.read_parquet(sc); S_["date"] = pd.to_datetime(S_.date).dt.date
        closes = pd.concat([closes[~closes.ticker.isin(S_.ticker.unique())], S_[["date", "close", "ticker"]]], ignore_index=True)
    vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix = pd.Series(vix.vix_close.values, index=pd.to_datetime(vix.trade_date).dt.date)
    spy = closes[closes.ticker == "SPY"].set_index("date").close.sort_index(); spy_up = (spy > spy.rolling(50).mean()).astype(float)
    rows = []
    for t in a.tickers:
        r = simulate(t, closes, vix, spy_up); rows += r; print(f"{t}: {len(r)} condors", flush=True)
    R = pd.DataFrame(rows); R.to_parquet(a.out, index=False); print(f"wrote {a.out}: {len(R)} rows"); return 0


if __name__ == "__main__":
    sys.exit(main())

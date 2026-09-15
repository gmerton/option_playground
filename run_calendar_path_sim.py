#!/usr/bin/env python3
"""
Step 2/3 of the CALENDAR path study (2026-09-15). Path-dependent single PUT-CALENDAR simulator on real daily bid/ask.

Entries: every Friday per ticker, two structures -- ETF (short ~20 DTE / long ~27, the XLU/XLV/XLP playbooks) and DCAL
(short ~12 / long ~19, the SPY double-calendar legs) -- ATM strike (nearest the close), same strike both legs, long leg =
next expiry 5..35 days past the short (monthlies-only names get the monthly gap; it is recorded).
Marks = daily close mids; executions = mid +/- 25% of that day's bid-ask + $0.0065/sh/leg (house cost model).
At the short expiry the short settles at intrinsic (no cost), the long is sold at mid - slippage.
Variants (each decided on the daily close, acted at that close):
  hold          to the short expiry (the playbook baseline)
  pt25/50/75    close when the spread mid >= debit x (1 + x)
  stop40/60     close when the spread mid <= debit x (1 - x)
  recenter1s/2s when |S/K - 1| >= 1 or 2 sigma (20d daily-return sd), close and re-open ATM with the SAME expiries, once
  inversion     close when the short leg's IV > long leg's IV x 1.05 (term structure inverted -- oquants' exit)
Gates recorded on every entry (never filtered here): FVF = sigma_fwd / sigma_short, iv_ratio = sigma_short / sigma_long,
IV percentile (1y of the entry structure's short-leg ATM IV), SPY-vs-50sma x VIX>=20 regime, entry BA% of debit.
Usage: PYTHONPATH=src python run_calendar_path_sim.py [--tickers SPY QQQ] [--out data/cache/calendar_path/results.parquet]
"""
from __future__ import annotations
import argparse, glob, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np, pandas as pd

CACHE = Path("data/cache/calendar_path"); SLIP, COMM = 0.25, 0.0065
STRUCTS = {"ETF": (20, 5, 27), "DCAL": (12, 3, 19)}       # short target, tol, long target
GAP_LO, GAP_HI = 5, 35
PT = (0.25, 0.50, 0.75); STOPS = (0.40, 0.60); RECENTER_SIGS = (1.0, 2.0); INV_RATIO = 1.05; MIN_LEFT = 2


def load_chain(t: str) -> pd.DataFrame:
    fs = sorted(glob.glob(str(CACHE / f"chain_{t}_*.parquet")))
    if not fs: return pd.DataFrame()
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d = d[(d.ask > 0) & (d.bid >= 0) & (d.ask >= d.bid) & (d.ask < 9999)].copy()
    d["mid"] = (d.bid + d.ask) / 2; d["ba"] = d.ask - d.bid
    d["iv"] = np.where((d.bid_iv > 0) & (d.ask_iv > 0), (d.bid_iv + d.ask_iv) / 2, np.nan)
    d["trade_date"] = pd.to_datetime(d.trade_date).dt.date; d["expiry"] = pd.to_datetime(d.expiry).dt.date
    d = d.sort_values("ba").drop_duplicates(["trade_date", "expiry", "strike"], keep="first")
    return d


def fwd_vol(iv1, t1, iv2, t2):
    if not (iv1 > 0 and iv2 > 0 and t2 > t1 > 0): return np.nan
    v = (iv2 ** 2 * t2 - iv1 ** 2 * t1) / (t2 - t1)
    return np.sqrt(v) if v > 0 else np.nan


def simulate_ticker(t: str, closes: pd.DataFrame, vix: pd.Series, spy_regime: pd.Series) -> list[dict]:
    ch = load_chain(t)
    if ch.empty: return []
    cl = closes[closes.ticker == t].set_index("date").close.sort_index()
    ret_sd = cl.pct_change().rolling(20).std()
    by_day = {d: g for d, g in ch.groupby("trade_date")}
    days = sorted(by_day)
    # 1y percentile reference: daily ATM ~short-target-DTE IV per structure
    out = []
    for sname, (sdte, stol, ldte) in STRUCTS.items():
        atm_iv = {}
        for d in days:
            g = by_day[d]; s0 = cl.get(d)
            if s0 is None: continue
            gg = g[(g.expiry >= d + timedelta(days=sdte - stol)) & (g.expiry <= d + timedelta(days=sdte + stol))]
            if gg.empty: continue
            k = gg.iloc[(gg.strike - s0).abs().argsort()[:1]]
            atm_iv[d] = float(k.iv.iloc[0]) if pd.notna(k.iv.iloc[0]) else np.nan
        ivs = pd.Series(atm_iv).sort_index()
        for d in days:
            if pd.Timestamp(d).weekday() != 4 or d not in cl.index: continue
            s0 = float(cl[d]); g = by_day[d]
            exps = sorted(g.expiry.unique())
            sh = [e for e in exps if sdte - stol <= (e - d).days <= sdte + stol]
            if not sh: continue
            se = min(sh, key=lambda e: abs((e - d).days - sdte))
            lo = [e for e in exps if GAP_LO <= (e - se).days <= GAP_HI]
            if not lo: continue
            le = min(lo, key=lambda e: abs((e - se).days - (ldte - sdte)))
            gs, gl = g[g.expiry == se], g[g.expiry == le]
            ks = set(gs.strike) & set(gl.strike)
            if not ks: continue
            K = min(ks, key=lambda k: abs(k - s0))
            rs, rl = gs[gs.strike == K].iloc[0], gl[gl.strike == K].iloc[0]
            debit = rl.mid - rs.mid
            if debit <= 0.02: continue
            cost = debit + SLIP * (rl.ba + rs.ba) + 2 * COMM
            t1, t2 = (se - d).days / 365, (le - d).days / 365
            fv = fwd_vol(rs.iv, t1, rl.iv, t2)
            hist = ivs[(ivs.index < d) & (ivs.index >= d - timedelta(days=365))].dropna()
            ivp = 100 * (hist < ivs.get(d, np.nan)).mean() if len(hist) > 120 and pd.notna(ivs.get(d, np.nan)) else np.nan
            sig = ret_sd.get(d, np.nan)
            base = dict(ticker=t, struct=sname, entry=d, K=K, short_exp=se, long_exp=le, sdte=(se - d).days, gap=(le - se).days, spot=s0,
                        debit=debit, cost=cost, ba_pct=100 * (rl.ba + rs.ba) / max(debit, 0.01), iv_s=rs.iv, iv_l=rl.iv,
                        fvf=fv / rs.iv if (pd.notna(fv) and rs.iv > 0) else np.nan, iv_ratio=rs.iv / rl.iv if (rs.iv > 0 and rl.iv > 0) else np.nan,
                        ivp=ivp, vix=vix.get(d, np.nan), spy_up=spy_regime.get(d, np.nan))
            # the path: every day entry < day <= short expiry with both legs quoted
            path = []
            for dd in days:
                if dd <= d or dd > se: continue
                gd = by_day[dd]; a = gd[(gd.expiry == se) & (gd.strike == K)]; b = gd[(gd.expiry == le) & (gd.strike == K)]
                if a.empty or b.empty: continue
                a, b = a.iloc[0], b.iloc[0]
                path.append(dict(d=dd, S=float(cl.get(dd, np.nan)), s_mid=a.mid, s_ba=a.ba, l_mid=b.mid, l_ba=b.ba, s_iv=a.iv, l_iv=b.iv))
            if not path: continue
            P = pd.DataFrame(path)
            # settlement at the short expiry: short at intrinsic, long sold at mid - slip
            ST = float(cl.get(se, np.nan))
            last = P.iloc[-1]
            if pd.notna(ST) and last.d == se:
                settle = (last.l_mid - SLIP * last.l_ba - COMM) - max(K - ST, 0.0)
            else:   # no quote on the expiry date: close both at the last available marks
                settle = (last.l_mid - SLIP * last.l_ba - COMM) - (last.s_mid + SLIP * last.s_ba + COMM)
            def close_at(row):  # exit both legs at that day's marks
                return (row.l_mid - SLIP * row.l_ba - COMM) - (row.s_mid + SLIP * row.s_ba + COMM)
            marks = P.l_mid - P.s_mid
            res = dict(base); res["hold"] = settle - cost; res["hold_days"] = len(P)
            left = [(se - x).days for x in P.d]
            for x in PT:
                hit = P[(marks >= debit * (1 + x)) & (pd.Series(left) > 0)]
                res[f"pt{int(100*x)}"] = (close_at(hit.iloc[0]) - cost) if len(hit) else res["hold"]
            for x in STOPS:
                hit = P[(marks <= debit * (1 - x)) & (pd.Series(left) > 0)]
                res[f"stop{int(100*x)}"] = (close_at(hit.iloc[0]) - cost) if len(hit) else res["hold"]
            inv = P[(P.s_iv > P.l_iv * INV_RATIO) & (pd.Series(left) > 0)]
            res["inversion"] = (close_at(inv.iloc[0]) - cost) if len(inv) else res["hold"]
            # re-center once: on the first day |S/K-1| >= n sigma with >= MIN_LEFT days to the short expiry, close and re-open ATM
            for nsig in RECENTER_SIGS:
                key = f"recenter{int(nsig)}s"; res[key] = res["hold"]; res[key + "_hit"] = False
                if not (pd.notna(sig) and sig > 0): continue
                trig = P[((P.S / K - 1).abs() >= nsig * sig) & (pd.Series(left) >= MIN_LEFT)]
                if not len(trig): continue
                r0 = trig.iloc[0]; dd = r0.d; gd = by_day[dd]
                K2 = min(set(gd[gd.expiry == se].strike) & set(gd[gd.expiry == le].strike), key=lambda k: abs(k - r0.S), default=None)
                if K2 is None or K2 == K: continue
                a2, b2 = gd[(gd.expiry == se) & (gd.strike == K2)].iloc[0], gd[(gd.expiry == le) & (gd.strike == K2)].iloc[0]
                debit2 = b2.mid - a2.mid; cost2 = debit2 + SLIP * (b2.ba + a2.ba) + 2 * COMM
                p2 = []
                for d3 in days:
                    if d3 <= dd or d3 > se: continue
                    g3 = by_day[d3]; a3 = g3[(g3.expiry == se) & (g3.strike == K2)]; b3 = g3[(g3.expiry == le) & (g3.strike == K2)]
                    if a3.empty or b3.empty: continue
                    p2.append((d3, a3.iloc[0], b3.iloc[0]))
                if p2 and debit2 > 0.02:
                    d3, a3, b3 = p2[-1]
                    settle2 = ((b3.mid - SLIP * b3.ba - COMM) - max(K2 - ST, 0.0)) if (pd.notna(ST) and d3 == se) else ((b3.mid - SLIP * b3.ba - COMM) - (a3.mid + SLIP * a3.ba + COMM))
                    res[key] = (close_at(r0) - cost) + (settle2 - cost2); res[key + "_hit"] = True
            out.append(res)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", nargs="*", default=None); ap.add_argument("--out", default=str(CACHE / "results.parquet")); a = ap.parse_args()
    closes = pd.read_parquet(CACHE / "closes.parquet"); closes["date"] = pd.to_datetime(closes.date).dt.date
    sc = CACHE / "spot_chain.parquet"
    if sc.exists():   # single names: the option table's strikes are unadjusted, so levels come from the chain's parity spot
        S_ = pd.read_parquet(sc); S_["date"] = pd.to_datetime(S_.date).dt.date
        closes = pd.concat([closes[~closes.ticker.isin(S_.ticker.unique())], S_[["date", "close", "ticker"]]], ignore_index=True)
    vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix = pd.Series(vix.vix_close.values, index=pd.to_datetime(vix.trade_date).dt.date)
    spy = closes[closes.ticker == "SPY"].set_index("date").close.sort_index(); spy_regime = (spy > spy.rolling(50).mean()).astype(float)
    tickers = a.tickers or sorted({Path(f).stem.split("_")[1] for f in glob.glob(str(CACHE / "chain_*.parquet"))})
    rows = []
    for t in tickers:
        r = simulate_ticker(t, closes, vix, spy_regime); rows += r; print(f"{t}: {len(r)} calendars", flush=True)
    R = pd.DataFrame(rows); R.to_parquet(a.out, index=False); print(f"wrote {a.out}: {len(R)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())

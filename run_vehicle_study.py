#!/usr/bin/env python3
"""
Reprice a window of closed long-stock trades as option structures at the same entry/exit
(ATM ~30-DTE call, 30-delta short put, 30/15-delta put credit spread) using ATM IV backed out of
options_daily_v3 prints. Reproduces data/studies/august_2026_vehicle_study.md for any window.

Inputs:
  --lens-csv   per-trade table from `run_trade_lens.py --out <csv>` (needs asset_category, dir, entry_date,
               exit_date, entry_px, exit_px, underlying_symbol, extended, max_abs_qty)
  --chains     parquet of v3 rows for the window's tickers/dates (see the SQL in the study doc); or pass
               --pull to query Athena for the tickers/dates in the lens CSV (slow: ~1M rows/month)
Usage: AWS_PROFILE=... PYTHONPATH=src python run_vehicle_study.py --lens-csv data/studies/august_2026_luk_tito_lens_trades.csv --pull
"""
import argparse, warnings
import numpy as np, pandas as pd, yfinance as yf
from math import log, sqrt, exp
from scipy.stats import norm
from scipy.optimize import brentq
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
ap = argparse.ArgumentParser(); ap.add_argument("--lens-csv", required=True); ap.add_argument("--chains", default=None); ap.add_argument("--pull", action="store_true"); a = ap.parse_args()
d = pd.read_csv(a.lens_csv); d = d[(d["dir"] == "BULL") & (d.asset_category == "STK") & d.exit_date.notna()].copy()
tk = sorted(d.underlying_symbol.unique()); d0, d1 = pd.Timestamp(d.entry_date.min()), pd.Timestamp(d.exit_date.max())
if a.pull:
    from lib.athena_lib import athena
    ch = athena(f"""SELECT ticker, trade_date, expiry, strike, cp, last, volume FROM silver.options_daily_v3
      WHERE ticker IN ({",".join(f"'{t}'" for t in tk)}) AND trade_date BETWEEN DATE '{d0.date()}' AND DATE '{d1.date()}'
      AND date_diff('day', trade_date, expiry) BETWEEN 14 AND 60 AND last>0 AND last<9999 AND volume>0""")
    ch.to_parquet("data/cache/vehicle_chains.parquet", index=False)
else:
    ch = pd.read_parquet(a.chains)
ch["trade_date"] = pd.to_datetime(ch.trade_date); ch["expiry"] = pd.to_datetime(ch.expiry)
raw = yf.download(tk, start=(d0 - pd.Timedelta(days=10)).date().isoformat(), end=(d1 + pd.Timedelta(days=3)).date().isoformat(), auto_adjust=True, threads=True, progress=False, group_by="ticker")
spot = pd.concat([raw[t]["Close"].rename(t) for t in tk if t in raw.columns.get_level_values(0)], axis=1).stack().rename("spot"); spot.index.names = ["trade_date", "ticker"]
r = 0.04
def bs(S, K, T, s, cp):
    if T <= 1e-6 or s <= 0: return max(0.0, (S - K) if cp == "C" else (K - S))
    d1 = (log(S / K) + (r + s * s / 2) * T) / (s * sqrt(T)); d2 = d1 - s * sqrt(T)
    return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2) if cp == "C" else K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
def delta(S, K, T, s, cp):
    d1 = (log(S / K) + (r + s * s / 2) * T) / (s * sqrt(T)); return norm.cdf(d1) if cp == "C" else norm.cdf(d1) - 1
def iv(p, S, K, T, cp):
    try: return brentq(lambda s: bs(S, K, T, s, cp) - p, 0.03, 6.0, xtol=1e-4)
    except Exception: return np.nan
ch = ch.join(spot, on=["trade_date", "ticker"]).dropna(subset=["spot"]); ch = ch[(ch.strike / ch.spot).between(0.90, 1.10)]; ch["T"] = (ch.expiry - ch.trade_date).dt.days / 365
ch["iv"] = [iv(p, s, k, t, c) for p, s, k, t, c in zip(ch["last"], ch.spot, ch.strike, ch["T"], ch.cp)]
ivt = ch.dropna(subset=["iv"]).groupby(["ticker", "trade_date", "expiry"]).agg(iv=("iv", "median"), n=("iv", "size")); ivt = ivt[ivt.n >= 3]
strikes = ch.groupby(["ticker", "expiry"]).strike.unique()
rows = []
for t in d.itertuples():
    tk_ = t.underlying_symbol; E, X = pd.Timestamp(t.entry_date), pd.Timestamp(t.exit_date); S0, S1 = t.entry_px, t.exit_px
    if tk_ not in ivt.index.get_level_values(0): continue
    cand = ivt.loc[tk_]
    if E not in cand.index.get_level_values(0) or X not in cand.index.get_level_values(0): continue
    eE, eX = cand.loc[E], cand.loc[X]; common = [x for x in eE.index if x in eX.index and 14 <= (x - E).days <= 60]
    if not common: continue
    xp = min(common, key=lambda x: abs((x - E).days - 30)); ivE, ivX = eE.loc[xp].iv, eX.loc[xp].iv; TE, TX = (xp - E).days / 365, max((xp - X).days, 0) / 365
    ks = np.array(sorted(strikes.loc[(tk_, xp)])); Kc = ks[np.argmin(abs(ks - S0))]
    dl = np.array([delta(S0, k, TE, ivE, "P") for k in ks]); Kp = ks[np.argmin(abs(dl + 0.30))]; Kq = ks[np.argmin(abs(dl + 0.15))]
    if Kq >= Kp: continue
    dc = np.array([delta(S0, k, TE, ivE, "C") for k in ks]); Kl = ks[np.argmin(abs(dc - 0.30))]; Ks = ks[np.argmin(abs(dc - 0.15))]
    cs_ok = Ks > Kl                            # 30/15-delta debit CALL spread (the Ravish geometry)
    if cs_ok:
        l0, l1 = bs(S0, Kl, TE, ivE, "C"), bs(S1, Kl, TX, ivX, "C"); s0_, s1_ = bs(S0, Ks, TE, ivE, "C"), bs(S1, Ks, TX, ivX, "C")
        cs_deb, cs_val = l0 - s0_, l1 - s1_   # debit in, value out
        cs_ok = cs_deb > 0.01
    if not cs_ok:
        cs_deb = cs_val = np.nan              # unconstructible: NaN this ARM, never drop the trade
    c0, c1 = bs(S0, Kc, TE, ivE, "C"), bs(S1, Kc, TX, ivX, "C"); p0, p1 = bs(S0, Kp, TE, ivE, "P"), bs(S1, Kp, TX, ivX, "P"); q0, q1 = bs(S0, Kq, TE, ivE, "P"), bs(S1, Kq, TX, ivX, "P")
    rows.append(dict(tkr=tk_, entry=t.entry_date, held=(X - E).days, move=S1 / S0 - 1, ivE=ivE, stock=(S1 - S0) * 100, call=(c1 - c0) * 100 - 0.03 * (c0 + c1) * 50, call_cost=c0 * 100,
                     put=(p0 - p1) * 100 - 0.05 * (p0 + p1) * 50, put_credit=p0 * 100, spread=((p0 - q0) - (p1 - q1)) * 100 - 0.05 * ((p0 - q0) + (p1 - q1)) * 50, spread_risk=(Kp - Kq) * 100 - (p0 - q0) * 100,
                     call_spread=(cs_val - cs_deb) * 100 - 0.05 * (cs_deb + cs_val) * 50, call_spread_risk=cs_deb * 100,
                     cs_width=(Ks - Kl), cs_debit=cs_deb, extended=bool(t.extended)))
v = pd.DataFrame(rows); notional = (v.stock / v.move.replace(0, np.nan)).abs(); notional = notional.fillna(notional.median()); risk = 0.02 * notional
print(f"call spread constructible on {v.call_spread.notna().sum()} of {len(v)} repriced trades")
print(f"call spread: median width ${v.cs_width.median():.1f}, median debit ${v.cs_debit.median():.2f} ({100*(v.cs_debit/v.cs_width).median():.0f}% of width, max {100*(v.cs_width/v.cs_debit-1).median():.0f}%)")
print(f"repriced {len(v)} of {len(d)} closed stock longs | median ATM IV {100 * v.ivE.median():.0f}% | hold med {v.held.median():.0f}d | move med {100 * v.move.median():+.2f}%")
print("\nPER CONTRACT vs 100 SHARES:")
for name, pnl in (("stock", v.stock), ("ATM call", v.call), ("short 30d put", v.put), ("put spread 30/15", v.spread), ("CALL spread 30/15 (debit)", v.call_spread)):
    q = pnl.dropna()
    print(f"  {name:26s} n {len(q):3d}  total {q.sum():+8.0f}  win {100 * (q > 0).mean():3.0f}%  mean {q.mean():+6.0f}  worst {q.min():+.0f}  best {q.max():+.0f}")
print("\nRISK-EQUALIZED to the stock's 2% stop risk:")
for name, pnl in (("stock", v.stock), ("call", v.call * risk / v.call_cost), ("short put stopped 2x", np.maximum(v.put, -2 * v.put_credit) * risk / (2 * v.put_credit)), ("put spread", v.spread * risk / v.spread_risk), ("CALL spread (debit)", v.call_spread * risk / v.call_spread_risk)):
    q = pnl.dropna()
    print(f"  {name:22s} n {len(q):3d}  total {q.sum():+8.0f}  win {100 * (q > 0).mean():3.0f}%  mean {q.mean():+6.0f}")
for lab, m in (("same-day", v.held == 0), ("1-3 days", (v.held > 0) & (v.held <= 3)), ("4+ days", v.held > 3), ("extended", v.extended), ("not extended", ~v.extended)):
    g = v[m]; print(f"  {lab:12s} n={len(g):3d} | stock {g.stock.sum():+7.0f} | call {g.call.sum():+7.0f} | short put {g.put.sum():+7.0f} | spread {g.spread.sum():+7.0f} | call spread {g.call_spread.sum():+7.0f}")

v.to_parquet("data/cache/vehicle_repriced.parquet", index=False)
m = v[v.call_spread.notna()]
print(f"\n\n=== MATCHED SAMPLE: the {len(m)} trades where ALL FIVE vehicles exist ===")
print("(the table above compares the call spread's 93 rows against the other arms' 158 -- composition, not vehicle)")
nm = (m.stock / m.move.replace(0, np.nan)).abs(); nm = nm.fillna(nm.median()); rm = 0.02 * nm
print("\nPER CONTRACT:")
for name, pnl in (("stock", m.stock), ("ATM call", m.call), ("short 30d put", m.put),
                  ("put spread 30/15", m.spread), ("CALL spread 30/15", m.call_spread)):
    print(f"  {name:20s} total {pnl.sum():+8.0f}  win {100*(pnl>0).mean():3.0f}%  mean {pnl.mean():+6.0f}  worst {pnl.min():+.0f}  best {pnl.max():+.0f}")
print("\nRISK-EQUALIZED to the stock's 2% stop risk:")
for name, pnl in (("stock", m.stock), ("call", m.call * rm / m.call_cost),
                  ("short put stopped 2x", np.maximum(m.put, -2*m.put_credit) * rm / (2*m.put_credit)),
                  ("put spread", m.spread * rm / m.spread_risk),
                  ("CALL spread (debit)", m.call_spread * rm / m.call_spread_risk)):
    print(f"  {name:22s} total {pnl.sum():+8.0f}  win {100*(pnl>0).mean():3.0f}%  mean {pnl.mean():+6.0f}")
print("\nBY BUCKET (matched):")
for lab, mask in (("same-day", m.held==0), ("1-3 days", (m.held>0)&(m.held<=3)), ("4+ days", m.held>3),
                  ("extended", m.extended), ("not extended", ~m.extended)):
    g = m[mask]
    if not len(g): continue
    print(f"  {lab:12s} n={len(g):3d} | stock {g.stock.sum():+7.0f} | call {g.call.sum():+7.0f} | "
          f"short put {g.put.sum():+7.0f} | put spr {g.spread.sum():+7.0f} | CALL spr {g.call_spread.sum():+7.0f}")

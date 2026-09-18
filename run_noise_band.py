#!/usr/bin/env python3
"""
Noise-band intraday momentum (Zarattini, Aziz, Barbon 2024, "Beat the Market", SSRN 4824172) on 1-min bars
from run_intraday_pull.py. QQQ intraday project, idea 1 (2026-09-17).

RULES (as recalled from the paper -- the SPY calibration run is the check on this recollection; published
SPY result 2007-2024: 19.6%/yr, Sharpe 1.33, net, WITH vol-target sizing up to 4x):
  sigma[m]  = mean over the prior LOOKBACK sessions of |close at minute m / that day's open - 1|     (LOOKBACK = 14, FIXED)
  upper[m]  = max(open_today, close_yesterday) * (1 + sigma[m])
  lower[m]  = min(open_today, close_yesterday) * (1 - sigma[m])
  Decisions only at HH:00 and HH:30 (10:00 ... 15:30). Flat -> long if price > upper, short if price < lower.
  Long exits when price < max(upper, VWAP); short exits when price > min(lower, VWAP). Flat at the close, always.

DEPARTURES, all conservative: a signal at a decision bar's close fills at the NEXT 1-min bar's open (the paper
fills at the signal price); the close-out fills at the last bar's close.

MODES
  --mode game   Gabe's game: fixed $10,000 every session, 1x, no compounding. Costs = IBKR fixed ($0.005/sh,
                $1.00 minimum per order) + $0.005/sh slippage (half of QQQ's 1-cent spread).
  --mode paper  the paper's setup for calibration: compounding from $100k, shares = equity * min(4, 2% / 14d daily
                vol) / open, $0.0035/sh commission + $0.001/sh slippage.

Usage: .venv/bin/python3 run_noise_band.py QQQ [--mode game] [--long-only] [--lookback 14] [--start 2007-01-01]
"""
from __future__ import annotations
import argparse
from math import sqrt
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("symbol"); ap.add_argument("--mode", choices=["game", "paper"], default="game")
ap.add_argument("--long-only", action="store_true"); ap.add_argument("--lookback", type=int, default=14)
ap.add_argument("--start", default=None); ap.add_argument("--end", default=None)
ap.add_argument("--capital", type=float, default=10_000.0); ap.add_argument("--no-vwap-stop", action="store_true")
ap.add_argument("--out", default=None)
a = ap.parse_args()

df = pd.read_parquet(f"data/cache/intraday_hist/{a.symbol}_1min.parquet")
df["day"] = df["ts"].dt.normalize(); df["m"] = (df["ts"].dt.hour * 60 + df["ts"].dt.minute) - 570   # 0 = the 09:30 bar
df = df[(df["m"] >= 0) & (df["m"] < 390)]
if a.start: df = df[df["day"] >= a.start]
if a.end: df = df[df["day"] <= a.end]
days = np.array(sorted(df["day"].unique())); D = len(days); didx = {d: i for i, d in enumerate(days)}
di = df["day"].map(didx).values; mi = df["m"].values


def grid(col, fill=np.nan):
    g = np.full((D, 390), fill); g[di, mi] = df[col].values; return g


C, O, V, W = grid("close"), grid("open"), grid("volume", 0.0), grid("average")
last = np.array([np.where(~np.isnan(C[i]))[0].max() for i in range(D)])          # last traded minute (early closes)
for i in range(D):                                                               # forward-fill gaps inside the session
    row = C[i, :last[i] + 1]; idx = np.where(~np.isnan(row), np.arange(len(row)), 0); np.maximum.accumulate(idx, out=idx); C[i, :last[i] + 1] = row[idx]
    O[i, :last[i] + 1] = np.where(np.isnan(O[i, :last[i] + 1]), C[i, :last[i] + 1], O[i, :last[i] + 1])
W = np.where(np.isnan(W) | (W <= 0), C, W)
first = np.array([np.where(~np.isnan(O[i]))[0].min() if (~np.isnan(O[i])).any() else 0 for i in range(D)])
day_open = O[np.arange(D), first]; day_close = C[np.arange(D), last]
ok_day = np.isfinite(day_open) & np.isfinite(day_close) & (last - first >= 300)      # skip sessions with a broken tape
with np.errstate(invalid="ignore", divide="ignore"):
    vwap = np.cumsum(W * V, axis=1) / np.cumsum(V, axis=1)
move = np.abs(C / day_open[:, None] - 1)
dret = pd.Series(day_close).pct_change().values
DEC = list(range(29, 360, 30))                                                   # bar 09:59 closes at 10:00 ... 15:29 -> 15:30

if a.mode == "game":
    comm_ps, comm_min, slip = 0.005, 1.00, 0.005
else:
    comm_ps, comm_min, slip = 0.0035, 0.0, 0.001

equity = 100_000.0 if a.mode == "paper" else a.capital
rows = []
for t in range(a.lookback + 1, D):
    if not ok_day[t] or not np.isfinite(day_close[t - 1]):
        continue
    sig = np.nanmean(move[t - a.lookback:t], axis=0)
    hi, lo = max(day_open[t], day_close[t - 1]), min(day_open[t], day_close[t - 1])
    ub, lb = hi * (1 + sig), lo * (1 - sig)
    if a.mode == "paper":
        vol = np.nanstd(dret[t - a.lookback:t], ddof=1); lev = min(4.0, 0.02 / vol) if vol > 0 else 1.0
        shares = int(equity * lev / day_open[t])
    else:
        shares = int(a.capital / day_open[t])
    pos, pnl, cost, ntr, entry_px = 0, 0.0, 0.0, 0, 0.0

    def trade(new_pos, m_fill, at_close=False):
        """Move to new_pos (-1/0/1) at minute m_fill's open (or the session's last close)."""
        global pos, pnl, cost, ntr, entry_px
        px = C[t, m_fill] if at_close else O[t, m_fill]
        if pos != 0:                                        # close the open leg
            fill = px - slip * pos; pnl += pos * shares * (fill - entry_px); cost += max(comm_min, comm_ps * shares); ntr += 1
        if new_pos != 0:
            entry_px = px + slip * new_pos; cost += max(comm_min, comm_ps * shares)
        pos = new_pos

    for m in DEC:
        if m + 1 > last[t]:
            break
        p = C[t, m]; want = pos
        if pos == 1 and p < (ub[m] if a.no_vwap_stop else max(ub[m], vwap[t, m])):
            want = 0
        if pos == -1 and p > (lb[m] if a.no_vwap_stop else min(lb[m], vwap[t, m])):
            want = 0
        if want == 0 or pos == 0:
            if p > ub[m]: want = 1
            elif p < lb[m] and not a.long_only: want = -1
        if want != pos:
            trade(want, m + 1)
    if pos != 0:
        trade(0, last[t], at_close=True)
    net = pnl - cost
    base = equity if a.mode == "paper" else a.capital
    rows.append(dict(day=days[t], gross=pnl / base, cost=cost / base, net=net / base, trades=ntr,
                     oc=day_close[t] / day_open[t] - 1, cc=day_close[t] / day_close[t - 1] - 1))
    if a.mode == "paper": equity += net

r = pd.DataFrame(rows).set_index("day")


def stats(x, label):
    x = x.dropna(); ann = x.mean() * 252; sd = x.std(ddof=1) * sqrt(252); eq = (1 + x).cumprod() if a.mode == "paper" else 1 + x.cumsum()
    dd = (eq / eq.cummax() - 1).min() if a.mode == "paper" else (eq - eq.cummax()).min()
    print(f"  {label:<28} ann {ann*100:6.1f}%  vol {sd*100:5.1f}%  Sharpe {ann/sd if sd else 0:5.2f}  t {x.mean()/(x.std(ddof=1)/sqrt(len(x))):5.2f}  maxDD {dd*100:6.1f}%")


print(f"\n{a.symbol}  {a.mode} mode  lookback {a.lookback}  {'long-only' if a.long_only else 'long/short'}  {r.index[0].date()} -> {r.index[-1].date()}  {len(r):,} sessions")
stats(r["net"], "strategy NET"); stats(r["gross"], "strategy gross")
stats(r["oc"], "benchmark: open->close 1x"); stats(r["cc"], "benchmark: buy & hold")
act = r[r["trades"] > 0]
print(f"  days traded {len(act)/len(r)*100:.0f}%   round trips/day {r['trades'].mean():.2f}   win days {100*(act['net']>0).mean():.0f}%   avg win {act.loc[act['net']>0,'net'].mean()*100:.2f}% / avg loss {act.loc[act['net']<=0,'net'].mean()*100:.2f}%   cost drag {r['cost'].mean()*252*100:.1f}%/yr")
print("  year    net%   gross%  Sharpe  trades   | open->close%  buy&hold%")
for y, s in r.groupby(r.index.year):
    sh = s["net"].mean() / s["net"].std(ddof=1) * sqrt(252) if s["net"].std() > 0 else 0
    print(f"  {y}  {s['net'].sum()*100:6.1f}  {s['gross'].sum()*100:7.1f}  {sh:6.2f}  {int(s['trades'].sum()):6d}   | {s['oc'].sum()*100:10.1f}  {((1+s['cc']).prod()-1)*100:9.1f}")
if a.out: r.to_csv(a.out)

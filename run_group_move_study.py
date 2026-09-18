#!/usr/bin/env python3
"""
Catching multi-month industry moves early (2026-09-17, Gabe: "semis Apr-Jun, oil recently -- catch them as early as possible").

The July rotation study asked whether a rotation can be PREDICTED and found no (fixed-horizon mean excess ~ 0).
This asks the different question: a multi-month move can be joined a month late and still pay -- so
  A. anatomy   how big/long/frequent are the moves, in hindsight (zigzag on the ETF/SPY ratio)
  B. recall    how early does a simple confirmation signal fire inside them, and how much is left
  C. precision every firing of that signal with no hindsight: what follows (the false-start problem)
  D. managed   enter on the signal, exit on a relative-strength trail: does cutting false starts and riding
               the real ones leave positive expectancy even though the fixed-horizon mean is ~0
  E. what separates real from false AT the signal (leader vs laggard base, commodity groups, SPY regime)

Signal S  = 21d return minus SPY's >= +5pp AND the ETF above its own 50-day. First firing after 21 quiet sessions.
Exit      = ETF/SPY ratio closes below its own 50-day average (RS trail), checked daily, max 252 sessions.
Excess    = ETF return minus SPY return over the hold. SEs cluster by entry month.

Usage: .venv/bin/python3 run_group_move_study.py [--refresh]
"""
import argparse, os
from math import sqrt
import numpy as np, pandas as pd
from market_conditions import SECTORS, INDUSTRIES

ap = argparse.ArgumentParser(); ap.add_argument("--refresh", action="store_true"); ap.add_argument("--rs", type=float, default=5.0)
ap.add_argument("--big", type=float, default=0.20); ap.add_argument("--rev", type=float, default=0.10); a = ap.parse_args()
CACHE = "data/cache/group_etf_closes.parquet"
NAMES = dict(SECTORS + INDUSTRIES); COMMOD = {"XLE", "XOP", "OIH", "XME", "GDX", "URA"}
if a.refresh or not os.path.exists(CACHE):
    import yfinance as yf
    px = yf.download(list(NAMES) + ["SPY"], start="2006-01-01", auto_adjust=True, progress=False)["Close"]; px.to_parquet(CACHE)
px = pd.read_parquet(CACHE).dropna(subset=["SPY"]); spy = px["SPY"]
print(f"{len(NAMES)} group ETFs  {px.index[0].date()} -> {px.index[-1].date()}")


def zigzag_up_legs(r: pd.Series, rev: float):
    """Up-legs of the ratio: trough -> peak, a leg ends when the ratio falls `rev` from its running peak."""
    legs, lo_i, hi_i, up = [], 0, 0, True; v = r.values
    for i in range(1, len(v)):
        if up:
            if v[i] > v[hi_i]: hi_i = i
            elif v[i] < v[hi_i] * (1 - rev): legs.append((lo_i, hi_i)); lo_i = i; up = False
        else:
            if v[i] < v[lo_i]: lo_i = i
            elif v[i] > v[lo_i] * (1 + rev): hi_i = i; up = True
    if up and hi_i > lo_i: legs.append((lo_i, hi_i))
    return legs


big, sigs = [], []
for t in NAMES:
    s = px[t].dropna()
    if len(s) < 400: continue
    sp = spy.reindex(s.index); ratio = s / sp
    rs21 = (s.pct_change(21) - sp.pct_change(21)) * 100
    S = (rs21 >= a.rs) & (s > s.rolling(50).mean())
    r50 = ratio.rolling(50).mean(); hi252, lo252 = ratio.rolling(252).max(), ratio.rolling(252).min()
    legs = [(i, j) for i, j in zigzag_up_legs(ratio.dropna(), a.rev) if ratio.iloc[j] / ratio.iloc[i] - 1 >= a.big and j - i >= 40]
    for i, j in legs:
        f = np.where(S.iloc[i:j].values)[0]
        tot = ratio.iloc[j] / ratio.iloc[i] - 1
        big.append(dict(t=t, start=s.index[i], end=s.index[j], days=j - i, excess=tot * 100,
                        sig_day=(f[0] if len(f) else np.nan), left=((ratio.iloc[j] / ratio.iloc[i + f[0]] - 1) / tot * 100 if len(f) else np.nan)))
    idx = np.where(S.values)[0]; last = -999
    for k in idx:
        if k - last > 21 and k + 1 < len(s) and k >= 252:
            e = k + 1; x = e + 1
            while x < len(s) - 1 and x - e < 252 and ratio.iloc[x] >= r50.iloc[x]: x += 1
            fw = lambda h: (s.iloc[min(e + h, len(s) - 1)] / s.iloc[e] - sp.iloc[min(e + h, len(s) - 1)] / sp.iloc[e]) * 100 if e + h < len(s) else np.nan
            inleg = any(i <= k <= i + (j - i) // 2 for i, j in legs)
            pos = (ratio.iloc[k] - lo252.iloc[k]) / (hi252.iloc[k] - lo252.iloc[k]) if hi252.iloc[k] > lo252.iloc[k] else np.nan
            sigs.append(dict(t=t, date=s.index[e], hold=x - e, mex=(s.iloc[x] / s.iloc[e] - sp.iloc[x] / sp.iloc[e]) * 100,
                             mabs=(s.iloc[x] / s.iloc[e] - 1) * 100, f63=fw(63), f126=fw(126), true=inleg, pos252=pos,
                             commod=t in COMMOD, spy_up=bool(sp.iloc[k] > sp.rolling(200).mean().iloc[k]), open=x >= len(s) - 1))
        if S.iloc[k]: last = k
B, G = pd.DataFrame(big), pd.DataFrame(sigs)

yrs = (px.index[-1] - px.index[0]).days / 365.25
print(f"\n== A. anatomy: relative up-legs >= +{a.big*100:.0f}% vs SPY lasting >= 40 sessions (hindsight) ==")
print(f"  {len(B)} moves = {len(B)/yrs:.1f} per year across the {len(NAMES)} groups   median {B['days'].median():.0f} sessions, median excess {B['excess'].median():+.0f}pp   (p25 {B['excess'].quantile(.25):+.0f} / p75 {B['excess'].quantile(.75):+.0f})")
print(f"\n== B. recall: signal S (rs21 >= +{a.rs:.0f}pp and above the 50-day) inside those moves ==")
h = B.dropna(subset=["sig_day"])
print(f"  fired inside {len(h)}/{len(B)} moves ({len(h)/len(B)*100:.0f}%)   median day {h['sig_day'].median():.0f} of {h['days'].median():.0f}   median share of the move still ahead {h['left'].median():.0f}%  (p25 {h['left'].quantile(.25):.0f}% / p75 {h['left'].quantile(.75):.0f}%)")
for t in ("SMH", "XLE", "XOP"):
    r = B[(B["t"] == t) & (B["end"] >= "2026-01-01")]
    for _, x in r.iterrows(): print(f"    {t} {x['start'].date()} -> {x['end'].date()}  {x['excess']:+.0f}pp  signal day {x['sig_day']:.0f}, {x['left']:.0f}% ahead")

Gc = G[~G["open"]]


def line(d, col, label):
    x = d[col].dropna(); m = x.groupby(d.loc[x.index, "date"].dt.to_period("M")).mean()
    print(f"  {label:<34} n={len(x):4d}  mean {x.mean():+6.2f}  median {x.median():+6.2f}  t(month-clustered) {m.mean()/(m.std(ddof=1)/sqrt(len(m))):+5.2f}  win {100*(x>0).mean():3.0f}%  p10 {x.quantile(.1):+6.1f}  p90 {x.quantile(.9):+6.1f}  >=+15pp {100*(x>=15).mean():3.0f}%")


print(f"\n== C. precision: every firing of S, no hindsight ({len(G)} signals, {len(G)/yrs:.0f} per year) ==")
print(f"  landed in the first half of a real big move: {100*G['true'].mean():.0f}%")
line(G, "f63", "fixed 63d excess (pp)"); line(G, "f126", "fixed 126d excess (pp)")
print("\n== D. managed: enter on S, exit when the ETF/SPY ratio closes under its 50-day average ==")
line(Gc, "mex", "excess vs SPY (pp)"); line(Gc, "mabs", "absolute return (%)")
w, l = Gc[Gc["mex"] > 0], Gc[Gc["mex"] <= 0]
print(f"  avg hold {Gc['hold'].mean():.0f} sessions (winners {w['hold'].mean():.0f} / losers {l['hold'].mean():.0f})   avg win {w['mex'].mean():+.1f}pp / avg loss {l['mex'].mean():+.1f}pp   payoff {w['mex'].mean()/-l['mex'].mean():.2f}")
top = Gc["mex"].sort_values(ascending=False); print(f"  top 5% of trades supply {top.head(max(1,len(top)//20)).sum()/top.sum()*100:.0f}% of the total excess")
half = Gc["date"] < Gc["date"].sort_values().iloc[len(Gc) // 2]
line(Gc[half], "mex", "  first half"); line(Gc[~half], "mex", "  second half")
print("  by era:"); [print(f"    {y}  n={len(d):3d}  mean excess {d['mex'].mean():+6.2f}pp  win {100*(d['mex']>0).mean():3.0f}%") for y, d in Gc.groupby((Gc["date"].dt.year // 4) * 4)]
print("\n== E. what separates real from false, measured AT the signal ==")
for lab, m in (("ratio in TOP third of its 252d range (leader)", Gc["pos252"] >= 2 / 3), ("ratio in MIDDLE third", Gc["pos252"].between(1 / 3, 2 / 3, inclusive="left")),
               ("ratio in BOTTOM third (laggard turn)", Gc["pos252"] < 1 / 3), ("commodity-linked group", Gc["commod"]), ("other groups", ~Gc["commod"]),
               ("SPY above its 200-day", Gc["spy_up"]), ("SPY below its 200-day", ~Gc["spy_up"])):
    line(Gc[m], "mex", lab)
G.to_csv("data/studies/group_move_signals.csv", index=False); B.to_csv("data/studies/group_move_legs.csv", index=False)

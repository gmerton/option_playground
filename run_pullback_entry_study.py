#!/usr/bin/env python3
"""
Pullback entries on leaders, daily bars (2026-09-17). Luk + Ariel Hernandez both prefer buying the pullback into a
rising EMA over chasing the breakout: "tightest definable stop, not extended; first pullback is best; skip if > ~3%
above the low; no gap-ups" (Luk, 20 mentions / 16 videos); "pullback into the 5/10/20-day with a reclaim trigger so
there is a low to risk off" (Ariel). Neither is tested on our data. Intraday triggers belong to the parked entry
study; this is the DAILY version, on the same panel and hold as the breakout pool so the two are comparable.

Leader (prior close): ADDV >= $50M, price >= $5, within 15% of the 52-week high, 10>20>50 stacked (house slack),
        rising 21 EMA (above its value 5 sessions ago). ADR gate is a variant (all / 3+ / 4-7).
Pullback: within the last --window sessions the LOW touched the EMA (low <= EMA x 1.005) after the close had been
        >= 1 ADR above the 21 EMA in the prior 10 sessions (so it is a pullback from extension, not a base grind).
Trigger: today's close > yesterday's high, close > the EMA, gap < 2%. Entry = that close. Stop = the pullback low
        (lowest low in the window). "Not extended": entry <= 1.03 x pullback low (Luk's ~3%), a variant.
First pullback: the first qualifying touch within 40 sessions of the stacked run starting.
Exit variants: A) house -- first close under the 20 EMA (or under the stop), 60 cap;  B) Luk 9-EMA buys "sell into
        strength": exit at the first close > entry + 2 x (entry - stop) or the trail, whichever first;  C) stop only.
Control: the same leaders on the same dates WITHOUT a pullback signal, bought at the close, stop = day's low, house exit.
Benchmark: the breakout pool (run_stack_slack_walkforward.py): mean R +0.55, ~+2.6% per trade.
SEs: month-clustered. Halves + 2022 reported. Usage: PYTHONPATH=src .venv/bin/python3 run_pullback_entry_study.py
"""
from __future__ import annotations
import argparse, warnings
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser(); ap.add_argument("--window", type=int, default=3); a = ap.parse_args()
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
ema = {n: C.ewm(span=n, adjust=False).mean() for n in (9, 21, 50)}; e20 = C.ewm(span=20, adjust=False).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); run = stack_run(C, adr=adr)
leader = (elig & (C / hi52 - 1 > -0.15) & (run > 0) & (ema[21] > ema[21].shift(5))).shift(1).fillna(False).astype(bool)
ext_recent = ((C / ema[21] - 1) * 100 / adr >= 1.0).shift(1).rolling(10).max().fillna(0).astype(bool)
gap = O / C.shift(1) - 1; reclaim = (C > H.shift(1)) & (gap < 0.02)
pb_low = L.rolling(a.window).min()
hi10 = H.shift(a.window).rolling(10).max()                     # the swing high before the pullback window
pb_low5 = L.rolling(5).min(); mid = pb_low5 + 0.5 * (hi10 - pb_low5)   # Gabe's "confirmed": price back above the midpoint of the pullback
confirmed = (C >= mid) & (C.shift(1) < mid) & (gap < 0.02)
first = (run <= 40) & (run > 0)
idx = C.index; Cv, Lv, E20v, E9v = C.values, L.values, e20.values, ema[9].values
W = len(C) - len(C[C.index >= "2019-10-01"])


def hold(i, j, entry, stop, mode):
    if not (np.isfinite(entry) and np.isfinite(stop)) or entry <= stop: return np.nan, np.nan, np.nan
    tgt = entry + 2 * (entry - stop)
    for k in range(i + 1, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if not np.isfinite(c): continue
        if c < stop: return (c - entry) / (entry - stop), c / entry - 1, 1
        if mode == "A" and c < E20v[k, j]: return (c - entry) / (entry - stop), c / entry - 1, 0
        if mode == "B" and (c >= tgt or c < E20v[k, j]): return (c - entry) / (entry - stop), c / entry - 1, 0
    k = min(i + 60, len(Cv) - 1); return (Cv[k, j] - entry) / (entry - stop), Cv[k, j] / entry - 1, 0


def events(mask, stop_df):
    m = mask.fillna(False).astype(bool); m = m[m.index >= "2019-10-01"]; ii, jj = np.where(m.values); ii = ii + W
    rows = []
    for i, j in zip(ii, jj):
        e, s = Cv[i, j], stop_df.values[i, j]
        rA = hold(i, j, e, s, "A"); rB = hold(i, j, e, s, "B"); rC = hold(i, j, e, s, "C")
        rows.append(dict(date=idx[i], j=j, adr=adr.values[i, j], risk=100 * (e / s - 1), first=bool(first.values[i, j]),
                         RA=rA[0], pA=100 * rA[1], stopA=rA[2], RB=rB[0], pB=100 * rB[1], RC=rC[0], pC=100 * rC[1]))
    d = pd.DataFrame(rows).dropna(subset=["RA"]); d["month"] = d["date"].dt.to_period("M"); return d


def line(d, lab, col="RA", pcol="pA"):
    if len(d) < 20: print(f"  {lab:<46} n={len(d):5d}  (too few)"); return
    m = d.groupby("month")[col].mean(); t = m.mean() / (m.std(ddof=1) / np.sqrt(len(m)))
    h = d["date"] < d["date"].sort_values().iloc[len(d) // 2]; y22 = d[d["date"].dt.year == 2022][col]
    print(f"  {lab:<46} n={len(d):5d}  R {d[col].mean():+5.2f} (t_m {t:+4.1f})  win {100*(d[col]>0).mean():3.0f}%  ret {d[pcol].mean():+5.2f}%  stop {d['risk'].median():4.1f}% away  | halves {d.loc[h,col].mean():+.2f} / {d.loc[~h,col].mean():+.2f}  2022 {y22.mean() if len(y22) > 10 else float('nan'):+.2f} (n{len(y22)})")


print("== PULLBACK ENTRIES on leaders, daily bars 2019-10 .. 2026-09 | R = (exit - entry) / (entry - pullback low) | exit A = first close under the 20 EMA ==")
res = {}
for n in (9, 21, 50):
    touched = (L <= ema[n] * 1.005).rolling(a.window).max().fillna(0).astype(bool)
    sig = leader & ext_recent & touched & reclaim & (C > ema[n])
    d = events(sig, pb_low); res[n] = d
    touched5 = (L <= ema[n] * 1.005).rolling(5).max().fillna(0).astype(bool)
    dconf = events(leader & ext_recent & touched5 & confirmed & (C > ema[n]), pb_low5)
    print(f"\n-- pullback into the {n} EMA --")
    line(dconf[dconf["adr"].between(4, 7)], "CONFIRMED (Gabe): back above the pullback midpoint, ADR 4-7")
    line(dconf[dconf["adr"].between(4, 7) & dconf["first"]], "CONFIRMED, first pullback")
    line(d, "all leaders (any ADR)")
    line(d[d["adr"] >= 3], "ADR >= 3")
    line(d[d["adr"].between(4, 7)], "ADR 4-7 (the breakout pool's band)")
    line(d[d["risk"] <= 3], "Luk: entry <= 3% above the pullback low")
    line(d[d["first"]], "first pullback (run <= 40 sessions)")
    line(d[~d["first"]], "later pullback (run > 40)")
    line(d[d["adr"].between(4, 7) & d["first"] & (d["risk"] <= 3)], "ADR 4-7 & first & <= 3% above low")
    print("  exit variants, ADR 4-7:"); dd = d[d["adr"].between(4, 7)]
    line(dd, "    A house 20 EMA trail"); line(dd, "    B sell into strength at +2R (or trail)", "RB", "pB"); line(dd, "    C stop only, 60 sessions", "RC", "pC")

print("\n== CONTROL: leaders (ADR 4-7) on days with NO pullback signal, bought at the close, stop = day's low, exit A ==")
anysig = pd.concat([((L <= ema[n] * 1.005).rolling(a.window).max().fillna(0).astype(bool) & reclaim) for n in (9, 21, 50)]).groupby(level=0).max()
ctl_mask = leader & (adr >= 4) & (adr <= 7) & ~anysig & (gap < 0.02)
rng = np.random.default_rng(1); cm = ctl_mask.fillna(False).astype(bool); cm = cm & (pd.DataFrame(rng.random(cm.shape), index=cm.index, columns=cm.columns) < 0.05)   # 5% sample
dc = events(cm, L); line(dc, "random 5% of leader-days, no signal")
print("\n== year by year: pullback into the 21 EMA, ADR 4-7 (R, n) ==")
d = res[21]; d = d[d["adr"].between(4, 7)]
print("  " + "  ".join(f"{y}: {g['RA'].mean():+.2f} (n{len(g)})" for y, g in d.groupby(d["date"].dt.year)))
pd.concat([res[n].assign(ema=n) for n in res]).to_csv("data/studies/pullback_entry_events.csv", index=False)

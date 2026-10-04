#!/usr/bin/env python3
"""
BEATEN-DOWN SINGLE-DRIVER GROUPS, BOUGHT WHEN THE DRIVER ASSET RECLAIMS ITS 21 EMA (pre-registered 2026-10-03, before
any data pull)

WHY. Gabe 2026-10-03: Ariel and Luk watched the beaten-down crypto group closely and struck as it turned. Our group-
washout test (2026-09-24) was NULL across 23 beaten groups (t -0.10) but its two crypto episodes were the best (+26.8%
2024-09, +8.4% 2025-04) -- 'crypto/BTC-specific, not a general rule'. Their trigger was the DRIVER, not breadth: Luk
7/20/2026 went long MSTR / COIN / BMNR on BTC and ETH reclaiming their rising 9/21 EMAs. Groups that are a levered bet on
one asset have a clean trigger (one price series) and a convex payoff (2-4x the driver). Breadth-timed washout rules
(three NULLs today) never looked at the driver.

GROUPS (basket <- driver), daily adjusted closes from yfinance:
  GOLD MINERS    GDX (2006-)                                <- GLD
  JUNIOR GOLD    GDXJ (2009-)                               <- GLD
  SILVER MINERS  SIL (2010-)                                <- SLV
  OIL E&P        XOP (2006-)                                <- USO
  CRYPTO EQUITY  equal-weight basket of MSTR, COIN, MARA, RIOT, CLSK, HUT, BITF, CIFR, IREN, WULF, rebalanced daily
                 over the names trading that day (2018-) <- BTC-USD.  ⚠ the member list is TODAY'S survivors (picked
                 in hindsight); WGMI (2022-) is reported as an ETF check.
  The ETF baskets are survivorship-free (the ETFs hold whatever existed).
EPISODE (per group, all at the close of day t):
  SETUP     basket close <= 0.70 x its prior 252-session high (beaten down >= 30%)
  TRIGGER   driver close > driver EMA21, after >= 20 consecutive closes below its EMA21 (the first reclaim)
  COOLDOWN  at most one episode per group per 60 sessions
  ENTRY     the basket's close on day t
OUTCOMES (h = 20 and 40 sessions; basket return from the entry close):
  PRIMARY   TIMING: basket h-session return minus the mean of the same basket's h-session return from 20 random later
            entry dates within the next 60 sessions (seed 20261003) -- does the driver reclaim time the group?
  SECONDARY LEVERAGE: basket return minus the driver's return over the same window (does the group beat simply holding
            the driver?), and minus beta x driver (beta = 252-session daily beta of basket on driver at entry).
STATISTIC: per episode; PRIMARY = 40-session timing excess pooled over all groups' episodes, t across episodes (episodes in
  different groups on nearby dates are treated as separate -- stated limitation). BAR (discovery): t >= 3 and both halves
  (split 2018-01-01) > 0. Expected n ~30-60 episodes in all; UNDERPOWERED is the likely verdict and is acceptable.
REPORTED: per group (n, mean 20/40d raw, timing and leverage excess); a 9-EMA + 21-EMA double reclaim variant (Luk's
  wording); setup threshold 0.60; the absolute 40d return distribution (median, share > +20%) -- the convexity the goal
  cares about; the live state per group (setup met? driver below / above its EMA21?).
PRIOR ~25% for timing; the 2-crypto-episode anecdote is the reason to look, not evidence.

  PYTHONPATH=src:. .venv/bin/python3 run_driver_reclaim_groups.py
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
import yfinance as yf

OUT = "data/studies/driver_reclaim_groups_2026-10-03"
GROUPS = {"GOLD MINERS": ("GDX", "GLD"), "JUNIOR GOLD": ("GDXJ", "GLD"), "SILVER MINERS": ("SIL", "SLV"),
          "OIL E&P": ("XOP", "USO"), "CRYPTO EQUITY": ("CRYPTO_EW", "BTC-USD")}
CRYPTO = ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "HUT", "BITF", "CIFR", "IREN", "WULF"]
SPLIT = pd.Timestamp("2018-01-01")
RNG = np.random.default_rng(20261003)


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def load() -> pd.DataFrame:
    tks = sorted({b for b, _ in GROUPS.values() if b != "CRYPTO_EW"} | {d for _, d in GROUPS.values()} | set(CRYPTO) | {"WGMI"})
    px = yf.download(tks, start="2005-01-01", auto_adjust=True, progress=False)["Close"]
    px.index = pd.to_datetime(px.index).tz_localize(None)
    r = px[CRYPTO].pct_change(fill_method=None)
    px["CRYPTO_EW"] = (1 + r.mean(axis=1, skipna=True).fillna(0)).cumprod().where(px[CRYPTO].notna().sum(axis=1) >= 3)
    return px


def episodes(px, basket, driver, double=False, setup=0.70):
    b = px[basket].dropna(); d = px[driver].reindex(b.index).ffill()
    e21 = d.ewm(span=21, adjust=False).mean(); e9 = d.ewm(span=9, adjust=False).mean()
    below = (d < e21).astype(int)
    run = below.groupby((below == 0).cumsum()).cumsum().shift(1)
    trig = (d > e21) & (run >= 20)
    if double:
        trig &= d > e9
    hi = b.shift(1).rolling(252, min_periods=200).max()
    sig = trig & (b <= setup * hi)
    out, last = [], -10 ** 9
    for i, (t, s) in enumerate(sig.items()):
        if s and i - last >= 60:
            out.append(i); last = i
    return b, d, out


def score(px, name, basket, driver, double=False, setup=0.70):
    b, d, eps = episodes(px, basket, driver, double, setup)
    lr = np.log(b).diff(); ld = np.log(d).diff()
    rows = []
    for i in eps:
        rec = dict(group=name, date=b.index[i])
        for h in (20, 40):
            if i + h >= len(b):
                continue
            rb = b.iloc[i + h] / b.iloc[i] - 1; rd = d.iloc[i + h] / d.iloc[i] - 1
            later = [j for j in RNG.choice(np.arange(i + 1, min(i + 61, len(b) - h)), size=20, replace=True)] if i + 1 < min(i + 61, len(b) - h) else []
            ctl = np.mean([b.iloc[j + h] / b.iloc[j] - 1 for j in later]) if later else np.nan
            w = slice(max(0, i - 252), i)
            beta = np.cov(lr.iloc[w].fillna(0), ld.iloc[w].fillna(0))[0, 1] / ld.iloc[w].fillna(0).var()
            rec.update({f"raw{h}": rb * 100, f"timing{h}": (rb - ctl) * 100, f"lev{h}": (rb - rd) * 100, f"betaex{h}": (rb - beta * rd) * 100})
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    px = load()
    E = pd.concat([score(px, n, b, d) for n, (b, d) in GROUPS.items()], ignore_index=True)
    E.to_csv(f"{OUT}_episodes.csv", index=False)
    x = E.timing40.dropna(); dd = E.loc[x.index, "date"]
    t = tstat(x); h1, h2 = x[dd < SPLIT].mean(), x[dd >= SPLIT].mean()
    v = "PASS" if (t >= 3 and h1 > 0 and h2 > 0) else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")
    L = [f"# Beaten single-driver groups at the driver's 21-EMA reclaim ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(E)} episodes across {E.group.nunique()} groups.", "",
         f"**PRIMARY timing excess, 40 sessions (vs the same basket from random later dates): {v}** — {x.mean():+.2f}pp, t {t:.2f}, "
         f"n {len(x)}, halves {h1:+.2f} / {h2:+.2f}", "", "## Reported, not a pass", ""]
    for col in ("timing20", "lev40", "lev20", "betaex40", "raw40", "raw20"):
        y = E[col].dropna(); L.append(f"- {col}: {y.mean():+.2f} (t {tstat(y):.2f}, n {len(y)}), median {y.median():+.2f}")
    r = E.raw40.dropna()
    L.append(f"- 40d raw: share > +20% {(r > 20).mean():.0%}, share < −20% {(r < -20).mean():.0%}")
    for lab, kw in (("9+21 EMA double reclaim", dict(double=True)), ("setup <= 0.60 x high", dict(setup=0.60))):
        V = pd.concat([score(px, n, b, d, **kw) for n, (b, d) in GROUPS.items()], ignore_index=True)
        y = V.timing40.dropna(); L.append(f"- {lab}: timing40 {y.mean():+.2f} t {tstat(y):.2f} n {len(y)}; raw40 {V.raw40.mean():+.2f}")
    W = score(px, "WGMI (ETF check)", "WGMI", "BTC-USD")
    L.append(f"- WGMI ETF check: n {len(W)}, raw40 {W.raw40.mean() if len(W) else float('nan'):+.2f}, timing40 {W.timing40.mean() if len(W) else float('nan'):+.2f}")
    L += ["", "Per group:", "", E.groupby("group")[["raw20", "raw40", "timing40", "lev40", "betaex40"]].agg(["mean", "count"]).round(2).to_string(),
          "", "## Live state", ""]
    for n, (b, d) in GROUPS.items():
        bb = px[b].dropna(); dd_ = px[d].reindex(bb.index).ffill(); e21 = dd_.ewm(span=21, adjust=False).mean()
        hi = bb.shift(1).rolling(252, min_periods=200).max()
        L.append(f"- {n}: basket {bb.iloc[-1] / hi.iloc[-1] - 1:+.0%} vs 52-wk high (setup {'MET' if bb.iloc[-1] <= 0.7 * hi.iloc[-1] else 'not met'}); "
                 f"driver {'ABOVE' if dd_.iloc[-1] > e21.iloc[-1] else 'below'} its EMA21 ({dd_.index[-1].date()})")
    L += ["", "## Episodes", "", E.round(2).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:24]))


if __name__ == "__main__":
    main()

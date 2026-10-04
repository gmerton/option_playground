#!/usr/bin/env python3
"""
FIRST BREAKOUT OF A BEATEN-DOWN NAME DURING A BREADTH RECOVERY (pre-registered 2026-10-03, before the run)

WHY. Gabe 2026-10-03: far more names sit at lows than highs; can we buy beaten-down names once they start rising? Three
washout rules are NULL (names that held up t -1.50; strongest bounce t -0.84; index bounce t 0.37). The long-base
breakout in beaten-down names (2026-09-24, run_beaten_down_rules test 1) was NULL (t 1.02) but ignored the market;
this keeps the stock-level "first breakout" and adds the timing the others lacked: the breadth RECOVERY after a
washout, when rebounds are led by what fell (weak-tape test mechanism).

UNIVERSE: liquid_panel_2009 (⚠ 2026 survivors -- beaten names that failed are missing, which flatters every arm here),
  eligible = ADDV50 >= $50M, price >= $5, not suspect, ADR(20) >= 3%. Signals 2010-03 -> 2026-07 (room for 40 sessions).
SIGNAL FB (first breakout), all at the close of day t:
  close_t > the highest close of the prior 50 sessions        (a 50-day closing high)
  no 50-day closing high in the prior 120 sessions             (the first one in ~6 months)
  close_t <= 0.75 x the prior 252-session high                 (still >= 25% below its 52-week high: beaten down)
BREADTH RECOVERY WINDOW (from run_weak_tape_leaders.py episodes: breadth = % of eligible names above their 50 SMA;
  episode = first close < 35% after >= 45%): the window opens on the first close back >= 45% after an episode (the
  re-arm close) and stays open 40 sessions. Everything is known at the close it is evaluated.
ARMS: IN = FB signals inside a recovery window; OUT = FB signals elsewhere.
OUTCOME: 40-session return from the signal close minus the mean return of the same-date ADR-matched field (all other
  eligible names in the same ADR band: 3-4 / 4-6 / 6+%), per signal; t clustered by signal date.
PRIMARY: IN excess. BAR (discovery): t >= 3, both halves (split 2018-01-01) > 0, a majority of years with IN signals > 0.
KEY SECONDARY: IN - OUT (does the recovery timing matter?), two-sample with date clustering.
REPORTED, not a pass: 20 / 60 sessions; house-managed version (buy the close, stop = the signal day's low judged on the
  close, exit on the first close below the 20 EMA, cap 60; % per trade) for IN and OUT; a stricter 'beaten' (<= 0.60 x
  high); signals per year; per-year IN excess; the live state (is a recovery window open, today's FB names).
PRIOR ~25%: the base version was NULL; the timing hypothesis is the new part.

  PYTHONPATH=src:. .venv/bin/python3 run_recovery_first_breakout.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/studies/recovery_first_breakout_2026-10-03"
SPLIT = pd.Timestamp("2018-01-01")
BANDS = [(3, 4), (4, 6), (6, 999)]
WIN, CAP = 40, 60


def ct(x: pd.Series, d: pd.Series):
    x = x.dropna(); d = d.loc[x.index]; n = len(x)
    if n < 20:
        return np.nan, np.nan, n
    mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
    return mu, mu / (np.sqrt((g ** 2).sum()) / n * np.sqrt(G / (G - 1))), n


def main() -> None:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    p = Panel.from_long(raw)
    C, H, L = p.close, p.high, p.low
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    el = elig & (adr >= 3)
    sma50 = C.rolling(50).mean()
    denom = (elig & sma50.notna()).sum(axis=1)
    breadth = 100 * ((C > sma50) & elig & sma50.notna()).sum(axis=1) / denom
    breadth = breadth[denom >= 0.5 * denom.rolling(20, min_periods=5).median().shift(1).fillna(denom)]
    breadth = breadth[breadth.index >= "2010-01-01"]
    # recovery windows
    idx = C.index; inwin = pd.Series(False, index=idx); armed, in_ep = True, False
    opens = []
    for d, b in breadth.items():
        if armed and b < 35:
            armed = False; in_ep = True
        elif not armed and b >= 45:
            armed = True
            if in_ep:
                opens.append(d); in_ep = False
    for d in opens:
        i = idx.get_loc(d); inwin.iloc[i:i + WIN] = True
    # signals
    hc50 = C.shift(1).rolling(50).max()
    new50 = C > hc50
    prior_new = new50.shift(1).rolling(120, min_periods=100).max().fillna(1).astype(bool)
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    beaten = C <= 0.75 * hi252
    FB = new50 & ~prior_new & beaten & el
    band = pd.DataFrame(np.select([(adr >= lo) & (adr < hi) for lo, hi in BANDS], range(len(BANDS)), -1), index=adr.index, columns=adr.columns)
    E20 = C.ewm(span=20, adjust=False).mean()

    def run(mask, h):
        Cv = C.values; rows = []
        fwd = (C.shift(-h) / C - 1)
        for i, j in zip(*np.where(mask.values)):
            d = idx[i]
            if not (pd.Timestamp("2010-03-01") <= d <= pd.Timestamp("2026-07-31")) or i + h >= len(idx):
                continue
            f = fwd.iloc[i]; ok = el.iloc[i] & f.notna(); bd = band.iloc[i]
            k = bd.iloc[j]
            if k < 0 or not np.isfinite(f.iloc[j]):
                continue
            fld = f[ok & (bd == k)].drop(C.columns[j], errors="ignore")
            if len(fld) < 10:
                continue
            # house-managed
            hm = np.nan
            for kk in range(i + 1, min(i + CAP, len(idx) - 1) + 1):
                c = Cv[kk, j]
                if np.isfinite(c) and (c < L.values[i, j] or c < E20.values[kk, j] or kk == i + CAP):
                    hm = (c / Cv[i, j] - 1 - 0.002) * 100; break
            rows.append(dict(date=d, sym=C.columns[j], ex=(f.iloc[j] - fld.mean()) * 100, raw=f.iloc[j] * 100, house=hm, inw=bool(inwin.iloc[i])))
        return pd.DataFrame(rows)

    R = run(FB, 40)
    R.to_csv(f"{OUT}_signals.csv", index=False)
    I, O = R[R.inw], R[~R.inw]
    m, t, n = ct(I.ex, I.date)
    h1, h2 = I[I.date < SPLIT].ex.mean(), I[I.date >= SPLIT].ex.mean()
    yr = I.groupby(I.date.dt.year).ex.mean()
    v = "PASS" if (t >= 3 and h1 > 0 and h2 > 0 and (yr > 0).mean() > 0.5) else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")
    mo, to, no = ct(O.ex, O.date)
    se = np.sqrt((m / t) ** 2 + (mo / to) ** 2)
    Lg = [f"# First breakout of a beaten-down name during a breadth recovery ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
          f"{len(opens)} recovery windows; FB signals {len(R)} (IN {len(I)}, OUT {len(O)}); window sessions {inwin.mean():.0%} of all.", "",
          f"**PRIMARY IN, 40-session ADR-matched excess: {v}** — {m:+.2f}pp, t {t:.2f}, n {n}; halves {h1:+.2f} / {h2:+.2f}; "
          f"years + {(yr > 0).sum()}/{len(yr)}", "",
          f"- KEY SECONDARY IN − OUT: {m - mo:+.2f}pp, t {(m - mo) / se:.2f} (OUT {mo:+.2f}pp, t {to:.2f}, n {no})", "", "## Reported, not a pass", ""]
    for h in (20, 60):
        X = run(FB, h); a = ct(X[X.inw].ex, X[X.inw].date); b = ct(X[~X.inw].ex, X[~X.inw].date)
        Lg.append(f"- {h} sessions: IN {a[0]:+.2f}pp t {a[1]:.2f} n {a[2]} · OUT {b[0]:+.2f}pp t {b[1]:.2f}")
    a, b = ct(I.house, I.date), ct(O.house, O.date)
    Lg.append(f"- house-managed % per trade: IN {a[0]:+.2f}% t {a[1]:.2f} n {a[2]} · OUT {b[0]:+.2f}% t {b[1]:.2f} n {b[2]}")
    S = run(FB & (C <= 0.60 * hi252), 40); a = ct(S[S.inw].ex, S[S.inw].date)
    Lg.append(f"- stricter beaten (<= 60% of the high), IN 40d: {a[0]:+.2f}pp t {a[1]:.2f} n {a[2]}")
    Lg += ["", "Per year, IN (mean excess pp, n):", "", I.groupby(I.date.dt.year).ex.agg(["mean", "count"]).round(2).to_string(), "",
           "## Live", ""]
    last = idx[-1]
    Lg.append(f"breadth {breadth.iloc[-1]:.1f}% on {breadth.index[-1].date()}; recovery window open: {bool(inwin.iloc[-1])}; "
              f"last window opened {opens[-1].date() if opens else '-'}; FB names on {last.date()}: "
              + " ".join(C.columns[FB.loc[last].fillna(False).values]))
    open(f"{OUT}_results.md", "w").write("\n".join(Lg) + "\n")
    print("\n".join(Lg[:20]))


if __name__ == "__main__":
    main()

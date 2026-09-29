#!/usr/bin/env python3
"""
Is the precision-tier breakout DECIDABLE before the close? Re-score the RVOL gate on volume through 15:50 ET
(pre-registered 2026-09-28, before any run).

WHY. NTAP 2026-09-28 met every precision condition only after the closing auction: at 15:50 it was above its 15-day
pivot on 0.83x a normal day's volume; the auction (22% of the day) lifted RVOL to 1.23. A market-on-close order must
be placed by ~15:50, so the full-day RVOL gate the tier has always been measured with uses volume that does not yet
exist when the order is sent -- a look-ahead in every precision-tier backtest.

PRE-REGISTRATION (frozen before the first run)
  Signals   the precision tier exactly as run_oneil_pyramid_8wk.py builds it (liquid_panel_2019, full-day bars) =
            the "BACKTEST" signal set (A).
  Window    names and sessions in data/cache/intraday_1min/ (192 alert-universe names, 2026-02-02 -> 2026-09-21);
            the 50-session average needs prior panel history, which the panel supplies.
  15:50 set (B) the same conditions evaluated on what is knowable at 15:50: last price at 15:49 (the 15:49 bar close)
            vs the 15-day pivot, day high/low through 15:49 for the upper-half-close condition, change vs the prior
            close < 8%, gap < 5%, the ADR / 52w / stack gates (prior-day values, unchanged). RVOL_1550 =
            volume through 15:49 / (50-session average full-day volume x f), where f = the name's median share of
            full-day volume traded by 15:49 over its PRIOR 20 cached sessions (a pro-rating known in advance; names
            with < 10 prior cached sessions use the cross-sectional median). Gate RVOL_1550 >= 1.1.
  Trade     both sets enter at the CLOSE (MOC) with the house rule: stop = min(entry-day low, close x 0.98) judged on the
            close; exit on the first close < stop or < 20 EMA; 60-session cap; outcome in % (and R).
  Report    counts: A, B, A&B, A-only (needs the auction: NOT tradeable live), B-only (fires at 15:50, fails at the
            close: traded live anyway). Mean % and R for each. PRIMARY = mean %(B) - mean %(A): the cost of the
            look-ahead to a live trader, with a date-clustered t. Descriptive: the effective sample is ~7 months of
            one regime; nothing here certifies anything.
  Check     the auction share: full-day panel volume vs the 1-min sum, per name-day (median reported).

Usage: PYTHONPATH=src .venv/bin/python3 run_precision_rvol_1550.py > data/studies/logs/precision_rvol_1550.log
"""
from __future__ import annotations

import glob
import os
import warnings

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
CACHE = "data/cache/intraday_1min"
CUT = "15:49"


def main():
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    Vsh = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex_like(p.close)
    C, H, L = p.close, p.high, p.low
    V = p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv = H.shift(1).rolling(15).max(); v50 = V.shift(1).rolling(50).mean()
    rvol = V / v50
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stk = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    # gates known before the session (prior-day values) -- identical for A and B
    pre = (adr >= 3) & (range52 >= 17) & elig & (adr >= 4) & (adr <= 7) & (stk.shift(1) >= 5) & (stk.shift(1) <= 40)
    A = (pre & (C >= piv) & (rvol >= 1.1) & (pos >= 0.5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv)
         & (off52 > -15) & (stk >= 5) & (stk <= 40)).fillna(False)

    files = sorted(glob.glob(f"{CACHE}/*.parquet"))
    idx = {}
    for f in files:
        b = os.path.basename(f)[:-8]; t, d = b.rsplit("_", 1)
        idx.setdefault(t, []).append(pd.Timestamp(d))
    names = [t for t in idx if t in C.columns]
    print(f"1-min cache: {len(files):,} name-days, {len(names)} names in the panel; window {min(min(v) for v in idx.values()).date()} -> {max(max(v) for v in idx.values()).date()}")

    rows, shares = [], []
    for t in names:
        j = C.columns.get_loc(t)
        days = sorted(d for d in idx[t] if d in C.index)
        hist = []
        for d in days:
            m = pd.read_parquet(f"{CACHE}/{t}_{d.date()}.parquet")
            if m.empty or not isinstance(m.index, pd.DatetimeIndex):
                continue                                  # ~5% of cache files are empty
            hm = m.index.strftime("%H:%M")
            pre_m = m[hm <= CUT]
            if pre_m.empty:
                continue
            v_cut = pre_m.volume.sum(); v_min = m.volume.sum()
            v_day = Vsh.loc[d, t]
            if np.isfinite(v_day) and v_day > 0:
                shares.append(dict(t=t, d=d, share_1550=v_cut / v_day, share_1min=v_min / v_day))
            f = np.median(hist[-20:]) if len(hist) >= 10 else np.nan
            if np.isfinite(v_day) and v_day > 0:
                hist.append(v_cut / v_day)
            i = C.index.get_loc(d)
            px = pre_m.close.iloc[-1]; hi, lo = pre_m.high.max(), pre_m.low.min()
            rows.append(dict(t=t, d=d, i=i, j=j, px1550=px, hi1550=hi, lo1550=lo, v1550=v_cut, f=f))
    X = pd.DataFrame(rows)
    Sh = pd.DataFrame(shares)
    fmed = Sh.share_1550.median()
    X["f"] = X.f.fillna(fmed)
    print(f"volume share traded by 15:49: median {fmed:.2%}; 1-min sum / panel daily volume: median {Sh.share_1min.median():.2%} "
          f"(the gap is the closing auction + late prints)")
    ii, jj = X.i.values, X.j.values
    g = lambda F: F.values[ii, jj]
    X["prev_close"] = g(C.shift(1)); X["piv"] = g(piv); X["v50"] = g(v50) / 1.0
    X["rvol1550"] = X.v1550 / (g(Vsh.shift(1).rolling(50).mean()) * X.f)
    X["pos1550"] = (X.px1550 - X.lo1550) / (X.hi1550 - X.lo1550).replace(0, np.nan)
    X["B"] = (g(pre).astype(bool) & (X.px1550 >= X.piv) & (X.rvol1550 >= 1.1) & (X.pos1550 >= 0.5) & (g(gap) < 0.05)
              & ((X.px1550 / X.prev_close - 1) < 0.08) & (X.prev_close < X.piv) & (g(off52) > -15)).fillna(False)
    X["A"] = g(A).astype(bool)
    X["rvol_full"] = g(rvol)

    Cv, Lv, E = C.values, L.values, e20.values; N = len(Cv)

    def trade(i, j):
        entry = Cv[i, j]; stop = min(Lv[i, j], entry * 0.98)
        for k in range(i + 1, min(i + 61, N)):
            c = Cv[k, j]
            if not np.isfinite(c):
                continue
            if c < stop or c < E[k, j]:
                return (c / entry - 1) * 100, (c - entry) / (entry - stop), False
        k = min(i + 60, N - 1)
        return (Cv[k, j] / entry - 1) * 100, (Cv[k, j] - entry) / (entry - stop), k == N - 1
    S = X[X.A | X.B].copy()
    tr = [trade(i, j) for i, j in zip(S.i, S.j)]
    S["ret"], S["R"], S["open"] = zip(*tr)
    grp = {"A (backtest, full-day RVOL)": S.A, "B (decidable at 15:50)": S.B, "A & B": S.A & S.B,
           "A only (needs the auction)": S.A & ~S.B, "B only (fires 15:50, fails at close)": S.B & ~S.A}
    out = []
    for k, m in grp.items():
        z = S[m]
        out.append(dict(set=k, n=len(z), dates=z.d.nunique(), mean_pct=z.ret.mean(), median_pct=z.ret.median(),
                        win=100 * (z.ret > 0).mean(), mean_R=z.R.mean(), still_open=int(z.open.sum()),
                        rvol_full_med=z.rvol_full.median(), rvol1550_med=z.rvol1550.median()))
    print("\n" + pd.DataFrame(out).round(2).to_string(index=False))
    a = S[S.A].groupby("d").ret.mean(); b = S[S.B].groupby("d").ret.mean()
    D = pd.concat([a.rename("A"), b.rename("B")], axis=1)
    both = D.dropna()
    diff = S[S.B].ret.mean() - S[S.A].ret.mean()
    dd = (both.B - both.A)
    t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 2 else np.nan
    print(f"\nPRIMARY mean %(B) - mean %(A): {diff:+.2f}pp | on dates with both: {dd.mean():+.2f}pp, date-clustered t {t:+.2f} ({len(dd)} dates)")
    print("\nA-only signals (the auction made them):")
    print(S[S.A & ~S.B][["t", "d", "px1550", "piv", "rvol1550", "rvol_full", "ret", "R"]].sort_values("d").round(2).to_string(index=False))
    S.to_csv("data/studies/logs/precision_rvol_1550_signals.csv", index=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
IPO lockup expiry event study, survivorship-free (pre-registered 2026-09-30, committed BEFORE any return is computed).

WHY. Structural blind spot: every panel's SMA200 / 400-bar minimums exclude recent IPOs (DATA_CATALOG section 7;
TEST_INDEX section 10 parked "IPO lockup expiry (90-180d) event study"). Timely: CBRS unlocks 19.4M shares 9/30, and more on
10/14 and 10/28. Gabe 2026-09-30: test 3 of 3. Literature prior (Field & Hanka 2001): about -1 to -2% abnormal return
around expiry. Is it there, and is it tradeable as a short after borrow?

EVENTS (counted before this pre-registration -- a power check only, no returns touched: 633)
  IPO date   the FIRST 424B4 (final prospectus) per CIK in the EDGAR quarterly full index 2010Q1 -> 2025Q4
             (run_sec_424b4_index.py), excluding SPAC names (acquisition / blank check / merger corp), mapped to a ticker
             through the Polygon ticker master incl. delisted (data/cache/pit/tickers.parquet).
  IPO filter chain_spot options series starts on/after the 424B4 date and within 120 days of it (drops pre-2010 IPOs whose
             first 424B4 in the window was a follow-on); IPO date >= 2010-07-01.
  expiry E   the first trading day >= IPO date + 180 calendar days (the standard lockup; staged/early releases such as
             CBRS's are NOT captured -- a 180-day proxy dilutes, it does not bias the sign).
  prices     chain_spot parity closes (run_dip_survivorship.pull + adjust_and_clean: split-adjusted, bad-print cuts),
             which include delisted names. A series ending inside a window exits at its last close.
PRIMARY    return close(E-5) -> close(E+5), minus the same-window mean of the CONTROL; t over events clustered by the
           ISO week of E. HYPOTHESIS: excess < 0.
CONTROL    other IPOs from the same event set that are 60-400 calendar days past their IPO date on E-5 and NOT within
           +/-20 trading days of their own E (holds "recent IPO" fixed; varies only the lockup). Needs >= 3; otherwise the
           event is dropped (count reported).
BAR        t <= -3, both halves (E < 2018-01-01 / >= 2018) negative, a majority of years negative -> the effect is REAL.
TRADEABLE  additionally: the absolute SHORT return over the window, net of 10 bp a side AND borrow at 30%/yr pro-rated
           (recent IPOs are hard to borrow; 10 sessions ~ 1.2%), must be > 0 on average.
SECONDARY  (Sidak k = 4, |t| >= 2.8; 3 governs): windows [E-1, E+1], [E, E+10], [E+1, E+20]; later-delisted vs survivors.
Also reported: the event count lost at each filter, and the CBRS-relevant read (effect size per unlock).
Local: cached chain_spot, one EDGAR pull (done).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_ipo_lockup.py   (log -> data/studies/logs/ipo_lockup.log)
"""
from __future__ import annotations

import sys
from math import sqrt

import numpy as np
import pandas as pd

import run_dip_survivorship as ds

REPO = ds.REPO
LOG = REPO / "data/studies/logs/ipo_lockup.log"
SPLIT, COST, BORROW = "2018-01-01", 0.0010, 0.30


def events(Cidx: pd.DatetimeIndex, have: set) -> pd.DataFrame:
    f = pd.read_parquet(REPO / "data/cache/sec_424b4_index.parquet")
    t = pd.read_parquet(REPO / "data/cache/pit/tickers.parquet").dropna(subset=["cik"])
    t["cik"] = t.cik.str.zfill(10)
    first = f.sort_values("date").groupby("cik").first().reset_index()
    n0 = len(first)
    first = first[~first.company.str.contains(r"acquisition|blank check|merger corp", case=False)]
    m = first.merge(t[["cik", "ticker", "delisted_utc"]], on="cik")
    cs = pd.read_parquet(ds.CACHE / "chain_spot_daily.parquet", columns=["ticker", "trade_date"])
    fd = cs.groupby("ticker").trade_date.agg(["min", "max"]).reset_index()
    m = m.merge(fd, on="ticker", how="left")
    ok = (m["min"].notna() & (m["min"] >= m.date) & (m["min"] <= m.date + pd.Timedelta(days=120))
          & (m.date >= "2010-07-01"))
    ev = m[ok & m.ticker.isin(have)].copy()
    ev["E"] = [Cidx[Cidx.searchsorted(d + pd.Timedelta(days=180))] if d + pd.Timedelta(days=180) <= Cidx[-1] else pd.NaT
               for d in ev.date]
    ev = ev.dropna(subset=["E"])
    print(f"filters: 424B4 CIKs {n0:,} -> non-SPAC matched {m.cik.nunique():,} -> IPO filter {int(ok.sum()):,} "
          f"-> with prices & E in range {len(ev):,}")
    return ev.rename(columns={"date": "ipo"}).reset_index(drop=True)


def wret(Cv, idx_pos, j, a, b, n, last):
    i0, i1 = idx_pos + a, min(idx_pos + b, n - 1, last[j])
    if i0 < 0 or i1 <= i0:
        return np.nan
    s0 = Cv[i0, j]
    seg = Cv[i0:i1 + 1, j]
    seg = seg[np.isfinite(seg)]
    if not np.isfinite(s0) or len(seg) < 2:
        return np.nan
    return 100 * (seg[-1] / s0 - 1)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def main():
    C, _ = ds.adjust_and_clean(ds.pull())
    ev = events(C.index, set(C.columns))
    Cv, cols = C.values, {c: k for k, c in enumerate(C.columns)}
    n = len(Cv)
    last = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                     for j in range(Cv.shape[1])])
    pos = {d: k for k, d in enumerate(C.index)}
    ev["ePos"] = ev.E.map(pos)
    windows = {"PRIMARY [E-5,E+5]": (-5, 5), "[E-1,E+1]": (-1, 1), "[E,E+10]": (0, 10), "[E+1,E+20]": (1, 20)}
    rows, dropped = [], 0
    for r in ev.itertuples():
        j = cols[r.ticker]
        d0 = C.index[max(r.ePos - 5, 0)]
        age = (d0 - ev.ipo).dt.days
        far = (ev.ePos - r.ePos).abs() > 20
        pool = ev[(age >= 60) & (age <= 400) & far & (ev.ticker != r.ticker)]
        if len(pool) < 3:
            dropped += 1
            continue
        rec = dict(ticker=r.ticker, ipo=r.ipo, E=r.E, delisted=pd.notna(r.delisted_utc), n_ctrl=len(pool))
        for lab, (a, b) in windows.items():
            x = wret(Cv, r.ePos, j, a, b, n, last)
            c = [wret(Cv, r.ePos, cols[t], a, b, n, last) for t in pool.ticker]
            rec[f"r|{lab}"], rec[f"c|{lab}"] = x, np.nanmean(c) if np.isfinite(c).any() else np.nan
        rows.append(rec)
    D = pd.DataFrame(rows)
    print(f"events with >= 3 recent-IPO controls: {len(D):,} (dropped {dropped}); median controls "
          f"{D.n_ctrl.median():.0f}; later delisted {int(D.delisted.sum())}")

    def cell(X, lab):
        X = X.dropna(subset=[f"r|{lab}", f"c|{lab}"])
        x = X[f"r|{lab}"] - X[f"c|{lab}"]
        wk = x.groupby(X.E.dt.to_period("W")).mean()
        h1, h2 = x[X.E < SPLIT].mean(), x[X.E >= SPLIT].mean()
        yr = x.groupby(X.E.dt.year).mean()
        return dict(n=len(X), raw=X[f"r|{lab}"].mean(), ctrl=X[f"c|{lab}"].mean(), excess=x.mean(), median=x.median(),
                    t=tstat(wk), h1=h1, h2=h2, yrs_neg=f"{int((yr < 0).sum())}/{len(yr)}", share_neg=(yr < 0).mean(),
                    _yr=yr.round(2))

    lab = "PRIMARY [E-5,E+5]"
    P = cell(D, lab)
    print(f"\n## PRIMARY {lab}: IPO at lockup vs other recent IPOs, same window (hypothesis < 0)")
    print(f"n {P['n']} | raw {P['raw']:+.2f}% vs control {P['ctrl']:+.2f}% | excess {P['excess']:+.2f}pp "
          f"(median {P['median']:+.2f}) t {P['t']:+.2f} | halves {P['h1']:+.2f}/{P['h2']:+.2f} | yrs neg {P['yrs_neg']}")
    real = P["excess"] < 0 and P["t"] <= -3 and P["h1"] < 0 and P["h2"] < 0 and P["share_neg"] > .5
    print(f"BAR: {'PASS - effect REAL' if real else 'FAIL'}")
    print("per year excess:\n" + P["_yr"].to_frame().T.to_string())
    X = D.dropna(subset=[f"r|{lab}"])
    short_net = -X[f"r|{lab}"] - 2 * 100 * COST - 100 * BORROW * 10 / 252
    print(f"TRADEABLE check: absolute short net of costs + 30%/yr borrow {short_net.mean():+.2f}% "
          f"(median {short_net.median():+.2f}, win {100 * (short_net > 0).mean():.0f}%)")
    print("\n## secondary (Sidak k = 4, |t| >= 2.8; 3 governs)")
    for lab2 in list(windows)[1:]:
        S = cell(D, lab2)
        print(f"  {lab2:12s} n {S['n']} | raw {S['raw']:+.2f} vs ctrl {S['ctrl']:+.2f} | excess {S['excess']:+.2f} "
              f"t {S['t']:+.2f} | halves {S['h1']:+.2f}/{S['h2']:+.2f}")
    for nm, m in (("later delisted", D.delisted), ("survivors", ~D.delisted)):
        S = cell(D[m.values], lab)
        print(f"  {nm:14s} n {S['n']} | excess {S['excess']:+.2f} t {S['t']:+.2f}")
    D.to_csv(REPO / "data/studies/logs/ipo_lockup_events.csv", index=False)


if __name__ == "__main__":
    real_out = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real_out
    print(open(LOG).read())

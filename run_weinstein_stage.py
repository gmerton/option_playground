#!/usr/bin/env python3
"""
WEINSTEIN STAGE ANALYSIS: THE STAGE 1 -> 2 BREAKOUT (replication) AND ARIEL'S "4B-MINUS" RECLAIM (discovery)
(pre-registered 2026-10-04, before any run)

WHY. Gabe 2026-10-04: Luk, Ariel and Gabe converged on crypto proxies in Aug 2026 after a long base -- "we wouldn't do
this trade if it were a falling knife". Ariel named the setup: a Stan Weinstein stage "4B" / "4B-minus" (IBIT 8/17:
reclaiming the 50-day after months of decline). Our variables are daily-scale (15-day pivots, 20/50-day EMAs, 252-day
highs); Weinstein's are WEEKLY (the 30-week MA, its slope, a stage-1 base). Two hypotheses, two tracks:

  H1 REPLICATION (Weinstein, *Secrets for Profiting in Bull and Bear Markets*, 1988 -- all our data is post-publication):
     the Stage 1 -> 2 breakout ("2A") beats comparable stocks over the following 6 months.
  H2 DISCOVERY (the 4B-minus label is a later practitioner refinement, not in the 1988 book): after a long stage-4
     decline, the first weekly close back above a still-falling 30-week MA, but only out of a compressed base (not a
     falling knife), beats comparable stocks.

DATA (survivorship-free, as the replication track requires): silver.chain_spot_daily via run_dip_survivorship.pull() /
  adjust_and_clean() -- closes for ~10.8k optionable tickers INCLUDING DELISTED, split-adjusted, 2010 -> 2026-02. Closes
  only: weekly "highs" are weekly closes, and Weinstein's volume rule cannot be applied here (see SECONDARY V).
  Eligible at the signal: 50-session mean option volume >= 1,000 contracts and price >= $5 (the momentum study's gate).
  Weekly bars = the last close of each W-FRI week. A name whose series ends inside the hold exits at its last close.
  SPY weekly (for Mansfield RS) from liquid_panel_2009.
DEFINITIONS (weekly, all known at the signal week's close):
  MA30   30-week SMA of weekly closes; SLOPE = MA30 / MA30 four weeks earlier - 1
  STAGE4 close < MA30 and SLOPE < 0
  RS     Mansfield relative strength = (close / SPY) / its 52-week SMA - 1
  H1 2A BREAKOUT: close > the highest weekly close of the prior 20 weeks (and the prior week was not above it: fresh);
         close > MA30; SLOPE >= -0.5%; a STAGE4 week within the prior 52 weeks; a stage-1 BASE = at least 16 of the prior
         20 weekly closes within +/-15% of MA30; RS > 0.
  H2 4B-MINUS: >= 20 consecutive STAGE4 weeks ending within the prior 4 weeks; this week close > MA30 while SLOPE < 0
         (first such week); NOT A FALLING KNIFE = the prior 12 weekly closes span <= 40% (max / min - 1).
  One signal per name per 26 weeks for each hypothesis.
OUTCOME: return from the signal-week close over 13 and 26 weeks, minus the mean of the same-week field = eligible
  names in the same volatility tercile (20-session st. dev. of daily returns at the signal date), excluding the name.
PRIMARY H1: 26-week excess, mean over signals, t clustered by signal week.
  BAR (replication): t >= 2 and >= its Sidak threshold over the 2 primary cells (2.24), both halves (split 2018-01-01)
  > 0, a majority of years positive. -> CERTIFIED (replication) / NULL / UNDERPOWERED.
PRIMARY H2: same metric. BAR (discovery): t >= 3, both halves > 0, majority of years.
PAYOFF SHAPE (Gabe: low downside after a long base), reported for both: STOP = the lowest weekly close of the prior 20
  weeks (the base low). Walk the weekly closes for 26 weeks: exit at the first weekly close below the stop, else at
  week 26. R = return / ((entry - stop) / entry). Report mean R, median R, win rate, stop-out share, and the share of
  signals with R >= 3.
SECONDARY (reported, not a pass): 13 weeks; H1 without the RS condition; H1 on liquid_panel_2009 (survivor-biased) WITH
  Weinstein's volume rule (breakout-week volume >= 2x the prior 4-week average) [V]; signals per year; per-year excess;
  driver assets descriptive (GLD, SLV, USO, BTC-USD, IBIT: every H1 / H2 signal with its 13/26-week return); the live
  list of names whose latest week fires H1 or H2 (from the survivor panel, which is current).
PRIOR: H1 ~35% (a famous, widely taught rule; most published technical rules decay); H2 ~25%.

  PYTHONPATH=src:. .venv/bin/python3 run_weinstein_stage.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OUT = "data/studies/weinstein_stage_2026-10-04"
OPTVOL_MIN, PX_MIN = 1000, 5.0
SPLIT = pd.Timestamp("2018-01-01")
SIDAK = 2.24


def weekly(C: pd.DataFrame) -> pd.DataFrame:
    return C.resample("W-FRI").last()


def signals(W: pd.DataFrame, spyw: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ma = W.rolling(30, min_periods=30).mean()
    slope = ma / ma.shift(4) - 1
    st4 = (W < ma) & (slope < 0)
    rs = (W.div(spyw.reindex(W.index), axis=0))
    rs = rs / rs.rolling(52, min_periods=40).mean() - 1
    res = W.shift(1).rolling(20, min_periods=20).max()
    base = ((W / ma - 1).abs() <= 0.15).astype(float).shift(1).rolling(20, min_periods=20).sum() >= 16
    had4 = st4.astype(float).shift(1).rolling(52, min_periods=30).max() >= 1
    h1 = (W > res) & ~(W.shift(1) > res.shift(1)) & (W > ma) & (slope >= -0.005) & had4 & base & (rs > 0)
    h1_nors = (W > res) & ~(W.shift(1) > res.shift(1)) & (W > ma) & (slope >= -0.005) & had4 & base
    # consecutive stage-4 weeks, per column
    s4 = st4.astype(int)
    runlen = s4.copy()
    for c in s4.columns:
        x = s4[c].values; r = np.zeros(len(x), dtype=int); k = 0
        for i, v in enumerate(x):
            k = k + 1 if v else 0; r[i] = k
        runlen[c] = r
    long4 = runlen.shift(1).rolling(4, min_periods=1).max() >= 20
    span12 = W.shift(1).rolling(12, min_periods=12).max() / W.shift(1).rolling(12, min_periods=12).min() - 1
    h2 = long4 & (W > ma) & (slope < 0) & ~((W.shift(1) > ma.shift(1)) & (slope.shift(1) < 0)) & (span12 <= 0.40)
    return h1, h2, h1_nors, W, ma


def thin(mask: pd.DataFrame, gap: int = 26) -> pd.DataFrame:
    out = mask.copy() * False
    for c in mask.columns:
        last = -10 ** 9
        for i in np.flatnonzero(mask[c].fillna(False).values):
            if i - last >= gap:
                out.iat[i, out.columns.get_loc(c)] = True; last = i
    return out.astype(bool)


def score(mask, W, elig_w, vol_w, horizon):
    rows = []
    fwd = W.shift(-horizon) / W - 1
    # delisted inside the hold: exit at the last available weekly close
    lastc = W.ffill()
    fwd = fwd.where(fwd.notna(), lastc.shift(-horizon) / W - 1)
    tert = vol_w.rank(axis=1, pct=True)
    tb = (tert > 1 / 3).astype(int) + (tert > 2 / 3).astype(int)
    for i, j in zip(*np.where(mask.values)):
        if i + horizon >= len(W) or not elig_w.iat[i, j] or not np.isfinite(fwd.iat[i, j]):
            continue
        k = tb.iat[i, j]
        f = fwd.iloc[i]; m = elig_w.iloc[i] & f.notna() & (tb.iloc[i] == k)
        m.iloc[j] = False
        if m.sum() < 20:
            continue
        rows.append(dict(week=W.index[i], sym=W.columns[j], ret=f.iat[j] * 100, ex=(f.iat[j] - f[m].mean()) * 100))
    return pd.DataFrame(rows)


def payoff(mask, W, horizon=26):
    out = []
    for i, j in zip(*np.where(mask.values)):
        if i + horizon >= len(W):
            continue
        e = W.iat[i, j]; stop = W.iloc[max(0, i - 20):i, j].min()
        if not (np.isfinite(e) and np.isfinite(stop) and e > stop):
            continue
        risk = (e - stop) / e; x = None
        for k in range(i + 1, i + horizon + 1):
            c = W.iat[k, j]
            if not np.isfinite(c):
                continue
            x = c
            if c < stop:
                out.append(((c / e - 1) / risk, True)); break
        else:
            if x is not None:
                out.append(((x / e - 1) / risk, False))
    R = pd.DataFrame(out, columns=["R", "stopped"])
    return R


def ct(x: pd.Series, d: pd.Series):
    x = x.dropna(); d = d.loc[x.index]; n = len(x)
    if n < 10:
        return np.nan, np.nan, n
    mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
    return mu, mu / (np.sqrt((g ** 2).sum()) / n * np.sqrt(G / (G - 1))), n


def verdict(S, bar):
    m, t, n = ct(S.ex, S.week)
    h1, h2 = S[S.week < SPLIT].ex.mean(), S[S.week >= SPLIT].ex.mean()
    yr = S.groupby(S.week.dt.year).ex.mean()
    ok = t >= bar and h1 > 0 and h2 > 0 and (yr > 0).mean() > 0.5
    return ok, m, t, n, h1, h2, yr


def main() -> None:
    import run_dip_survivorship as DS
    d = DS.pull()
    C, V = DS.adjust_and_clean(d)
    liq = ((V.rolling(50, min_periods=30).mean() >= OPTVOL_MIN) & (C >= PX_MIN)).fillna(False)
    vol = C.pct_change(fill_method=None).rolling(20, min_periods=15).std()
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet"); raw["date"] = pd.to_datetime(raw.date)
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    W = weekly(C); spyw = spy.resample("W-FRI").last()
    elig_w = liq.resample("W-FRI").last().reindex(W.index).fillna(False).astype(bool)
    vol_w = vol.resample("W-FRI").last().reindex(W.index)
    h1, h2, h1n, W, ma = signals(W, spyw)
    H1, H2, H1N = thin(h1), thin(h2), thin(h1n)
    L = [f"# Weinstein stage analysis ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"chain_spot weekly, {W.index[0].date()} -> {W.index[-1].date()}, {W.shape[1]} tickers (incl. delisted).", ""]
    for lab, M, bar, track in (("H1 Stage 1->2 breakout (2A)", H1, SIDAK, "replication"), ("H2 4B-minus reclaim, not a falling knife", H2, 3.0, "discovery")):
        S = score(M, W, elig_w, vol_w, 26); S.to_csv(f"{OUT}_{lab.split()[0]}_signals.csv", index=False)
        ok, m, t, n, a, b, yr = verdict(S, bar)
        v = ("CERTIFIED (replication)" if track == "replication" else "PASS") if ok else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")
        R = payoff(M & elig_w, W)
        S13 = score(M, W, elig_w, vol_w, 13); m13, t13, _ = ct(S13.ex, S13.week)
        L += [f"## {lab} [{track} bar t >= {bar}]", "",
              f"**{v}** — 26-week excess {m:+.2f}pp, t {t:.2f}, n {n}; halves {a:+.2f} / {b:+.2f}; years + {(yr > 0).sum()}/{len(yr)}; "
              f"raw 26-week return {S.ret.mean():+.2f}%", f"- 13 weeks: {m13:+.2f}pp t {t13:.2f}",
              f"- payoff with the base-low stop (weekly closes): mean R {R.R.mean():+.2f}, median R {R.R.median():+.2f}, win {(R.R > 0).mean():.0%}, "
              f"stopped {R.stopped.mean():.0%}, R >= 3 {(R.R >= 3).mean():.0%} (n {len(R)})",
              f"- signals per year: " + " ".join(f"{y}:{c}" for y, c in S.groupby(S.week.dt.year).size().items()), ""]
    S = score(H1N, W, elig_w, vol_w, 26); m, t, n = ct(S.ex, S.week)
    L.append(f"- H1 without the RS condition: {m:+.2f}pp t {t:.2f} n {n}")
    # [V] volume-confirmed H1 on the survivor panel
    pv = lambda c: raw.pivot(index="date", columns="ticker", values=c).sort_index()
    Cs, Vs = pv("close"), pv("volume")
    Ws = Cs.resample("W-FRI").last(); Vw = Vs.resample("W-FRI").sum()
    h1s = signals(Ws, spyw)[0] & (Vw >= 2 * Vw.shift(1).rolling(4).mean())
    eligs = ((pv("dolvol").rolling(50, min_periods=30).mean() >= 50e6) & (Cs >= 5)).resample("W-FRI").last().reindex(Ws.index).fillna(False).astype(bool)
    vols = Cs.pct_change(fill_method=None).rolling(20, min_periods=15).std().resample("W-FRI").last().reindex(Ws.index)
    SV = score(thin(h1s), Ws, eligs, vols, 26); m, t, n = ct(SV.ex, SV.week)
    L.append(f"- [V] H1 + Weinstein volume rule, survivor panel: {m:+.2f}pp t {t:.2f} n {n}")
    # driver assets, descriptive
    import yfinance as yf
    dr = yf.download(["GLD", "SLV", "USO", "BTC-USD", "IBIT"], start="2009-01-01", auto_adjust=True, progress=False)["Close"]
    dr.index = pd.to_datetime(dr.index).tz_localize(None)
    Dw = dr.resample("W-FRI").last()
    d1, d2, _, Dw, _ = signals(Dw, spyw)
    L += ["", "## Driver assets (descriptive): every signal, 13 / 26-week return %", ""]
    for lab, M in (("H1", thin(d1)), ("H2", thin(d2))):
        for i, j in zip(*np.where(M.values)):
            r13 = Dw.iat[i + 13, j] / Dw.iat[i, j] - 1 if i + 13 < len(Dw) else np.nan
            r26 = Dw.iat[i + 26, j] / Dw.iat[i, j] - 1 if i + 26 < len(Dw) else np.nan
            L.append(f"- {lab} {Dw.columns[j]} {Dw.index[i].date()}: {r13 * 100:+.1f} / {r26 * 100:+.1f}")
    # live list from the survivor panel
    last = Ws.index[-1]
    L += ["", f"## Live (survivor panel, week of {last.date()})", "",
          "H1: " + " ".join(Ws.columns[signals(Ws, spyw)[0].loc[last].fillna(False).values]),
          "H2: " + " ".join(Ws.columns[signals(Ws, spyw)[1].loc[last].fillna(False).values])]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:30]))


if __name__ == "__main__":
    main()

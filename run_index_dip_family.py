#!/usr/bin/env python3
"""
Index dip family (Quantified Strategies channel) settled with ONE rule -- TEST_INDEX section 10 row "Daily ETF mean
reversion benchmarked against buy-and-hold" (parked 2026-09-22), promoted by Gabe 2026-09-30.
Pre-registered 2026-09-30, before the first run. Creator claim -> DISCOVERY track (|t| >= 3).

WHY ONE RULE. About a third of the channel is "oversold SPY/QQQ + QS exit" with dozens of oscillators and settings; any
of them tested on the full sample is scored on the data it was fitted to. The author published the rule below in
October 2012 (Wayback capture 2013-06-05 of his post dated 2012-10-24: "a possible strategy to buy SPY when it closed
below the previous day's 5 day low ... suggest to buy on the close"), so 2013 -> 2026 is out of sample for it and it
has no free parameter. Exit as stated in video UkoTdKV65yk ("sell when the close is higher than yesterday's high or
after five trading days"); the 2012 post's own exit was not recoverable, so the exit is the channel's standard one.

RULES
  D5 entry  close_t < lowest LOW of the previous 5 trading days (t-5 .. t-1) -> buy the close of t
  TT entry  (second rule, also "2012" per video SjAVW7jgwuQ) t is a Monday and close_t < previous close -> buy the close
  exit      first s in t+1 .. t+5 with close_s > high_(s-1) -> sell the close of s; else sell the close of t+5
  book      a signal while long is ignored; re-entry allowed on the exit close.

DESIGN
  data      data/cache/index_daily_ftd.parquet (yfinance OHLCV + Adj Close, SPY 1993 ->, QQQ 1999 ->, to 2026-09-18).
            Signals on RAW OHLC; returns on Adj Close (total return).
  costs     1 bp + $0.005/share per side. Gross and net side by side.
  window    PRIMARY 2013-01-01 -> 2026-09-18 (post-publication). 1993 -> 2012 is reported as in-sample, descriptive.

  PRIMARY   SPY, D5, 2013 ->. Same instrument, same exit, vary only the entry day:
              r_d = total return from the close of d to the exit close under the rule above, for EVERY day d;
              cell = mean r_d on signal days minus mean r_d on all other days, OLS with HAC (10 lags).
            Bar: |t| >= 3, halves 2013-2019 / 2020-2026 both positive, majority of years positive, net mean trade > 0.
  SECONDARY (3 more cells, same test: QQQ D5, SPY TT, QQQ TT; 4 cells in all, Sidak 5% two-sided |t| >= 2.49; the
            discovery bar of 3 governs).
  ROBUSTNESS (pre-registered; a primary pass that fails R1 is PARKED as a volatility premium, not adopted)
    R1  volatility control: r_d on signal + lagged 20-day realised vol (z-scored, expanding); signal t with the control,
        and the signal-minus-other gap inside each RV20 tercile. Dips cluster in volatile tape, where every entry day
        earns more under a sell-into-strength exit.
    R2  random-entry null (as in run_darvas_spy.py): the same number of signal days drawn at random, same book, same
        exit, 2,000 draws; place the book's mean trade and return per long day in that distribution.
    R3  exposure-matched: close-to-close return on the book's long days vs its flat days, HAC (10); book CAGR, max
        drawdown and exposure vs buy-and-hold over the same window, net.
  EXPLORATORY (labelled, no claim): in-sample 1993-2012; next-open entry and exit; per-year table.

ADDED AFTER THE FIRST RUN (2026-09-30, labelled post hoc): the primary passed (t 3.72), and a clean pass is a bug until
proven otherwise. The rule decides and fills on the same closing print, which cannot be traded: a market-on-close order
must be in by 15:50. P1 REAL-FILL CHECK: take the signal from the last 1-min price before 10 minutes to the close
(IBKR 1-min, data/cache/intraday_hist, 2007 ->) against the same prior 5-day low, fill at the official close, same exit,
same any-day control, 2013 ->. Report how many signal days change and the cell. D5 only (TT is the same construction).

Also post hoc and EXPLORATORY (no claim): the primary cell split by trend (close above / below the 200-day average at
the signal) so today's regime row can be marked, the book's net return by year, and its five worst trades.

Local run (one cached parquet, seconds of CPU).
Usage: PYTHONPATH=src .venv/bin/python3 run_index_dip_family.py   (log -> data/studies/logs/index_dip_family.log)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/index_daily_ftd.parquet"
LOG = REPO / "data/studies/logs/index_dip_family.log"
BP, PER_SHARE, MAXHOLD, OOS = 0.0001, 0.005, 5, "2013-01-01"
HALVES = (("2013-2019", "2013", "2019"), ("2020-2026", "2020", "2026"))


def load(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(CACHE)
    d = d[d.ticker == sym].sort_index()
    d = d.rename(columns=str.lower).rename(columns={"adj close": "adj"})
    d["aopen"] = d.open * d.adj / d.close
    d["ret"] = d.adj.pct_change()
    rv = d.ret.rolling(20).std()
    d["rv_z"] = (rv - rv.expanding(250).mean()) / rv.expanding(250).std()   # known at the close of d
    d["rv"] = rv
    return d.dropna(subset=["open", "high", "low", "close", "adj"])


def sig_d5(d: pd.DataFrame) -> pd.Series:
    return (d.close < d.low.shift(1).rolling(5).min()).fillna(False)


def sig_tt(d: pd.DataFrame) -> pd.Series:
    return ((d.index.dayofweek == 0) & (d.close < d.close.shift(1))).fillna(False)


def exit_frame(d: pd.DataFrame, at_open: bool = False) -> pd.DataFrame:
    """For every day d: enter the close of d (or the next open), exit per the rule. Columns: gross, net, e, x (bar idx)."""
    n = len(d)
    strong = (d.close > d.high.shift(1)).values
    px, raw = (d.aopen.values, d.open.values) if at_open else (d.adj.values, d.close.values)
    rows = []
    for i in range(n):
        s = next((j for j in range(i + 1, min(i + MAXHOLD, n - 1) + 1) if strong[j]), i + MAXHOLD)
        e, x = (i + 1, s + 1) if at_open else (i, s)
        if x >= n:
            rows.append((np.nan, np.nan, -1, -1))
            continue
        gross = px[x] / px[e] - 1
        rows.append((gross, gross - 2 * BP - PER_SHARE / raw[e] - PER_SHARE / raw[x], e, x))
    return pd.DataFrame(rows, index=d.index, columns=["gross", "net", "e", "x"])


def book(ex: pd.DataFrame, sig: pd.Series) -> pd.DataFrame:
    g, nt, es, xs, idx = ex.gross.values, ex.net.values, ex.e.values, ex.x.values, ex.index
    out, free = [], -1
    for i in np.flatnonzero(sig.values):
        if np.isnan(g[i]) or es[i] < free:                 # still long at this signal (re-entry on the exit bar is allowed)
            continue
        out.append((idx[i], g[i], nt[i], int(es[i]), int(xs[i]), int(xs[i] - es[i])))
        free = int(xs[i])
    return pd.DataFrame(out, columns=["signal", "gross", "net", "e", "x", "bars"])


def stats(r: pd.Series) -> str:
    if r.empty:
        return "n 0"
    pf = r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else float("inf")
    return f"n {len(r):4d} | win {100 * (r > 0).mean():5.1f}% | mean {100 * r.mean():+.3f}% | PF {pf:5.2f}"


def hac(y: pd.Series, X: pd.DataFrame | pd.Series, lags: int = 10):
    X = X.to_frame() if isinstance(X, pd.Series) else X
    ok = y.notna() & X.notna().all(axis=1)
    fit = sm.OLS(y[ok] * 100, sm.add_constant(X[ok].astype(float))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return fit.params.iloc[1], fit.tvalues.iloc[1]


def cell(ex: pd.DataFrame, sig: pd.Series, a: str, b: str = "2026-12-31") -> tuple[str, float, float]:
    y, s = ex.gross.loc[a:b], sig.loc[a:b]
    ok = y.notna()
    diff, t = hac(y, s.rename("sig"))
    txt = (f"signal days {100 * y[ok & s].mean():+.3f}% (n {int((ok & s).sum())}, win {100 * (y[ok & s] > 0).mean():.1f}%) "
           f"vs other days {100 * y[ok & ~s].mean():+.3f}% (n {int((ok & ~s).sum())}, win "
           f"{100 * (y[ok & ~s] > 0).mean():.1f}%) | diff {diff:+.3f}pp, t {t:+.2f}")
    return txt, diff, t


def years(ex: pd.DataFrame, sig: pd.Series, a: str) -> pd.Series:
    yr = pd.DataFrame({"y": ex.gross.loc[a:], "s": sig.loc[a:]}).dropna()
    return yr.groupby(yr.index.year).apply(lambda g: 100 * (g.y[g.s].mean() - g.y[~g.s].mean()) if g.s.any() else np.nan)


def report(sym: str, rule: str, d: pd.DataFrame, sig: pd.Series, out: list[str], primary: bool) -> None:
    ex = exit_frame(d)
    tag = "PRIMARY" if primary else "secondary"
    out.append(f"\n## {sym} {rule} ({tag}) -- {int(sig.loc[OOS:].sum())} signal days 2013->, "
               f"{100 * sig.loc[OOS:].mean():.1f}% of days")
    txt, diff, t = cell(ex, sig, OOS)
    out.append(f"  2013->      {txt}")
    hs = []
    for lab, a, b in HALVES:
        th, dh, tt_ = cell(ex, sig, a, b)
        hs.append(dh)
        out.append(f"    {lab}  diff {dh:+.3f}pp, t {tt_:+.2f}")
    by = years(ex, sig, OOS).dropna()
    out.append(f"    years positive {int((by > 0).sum())}/{len(by)}: " + " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in by.items()))
    tr = book(ex, sig)
    tro = tr[tr.signal >= OOS]
    out.append(f"  book 2013-> gross {stats(tro.gross)} | avg bars {tro.bars.mean():.1f}")
    out.append(f"              net   {stats(tro.net)}")
    if primary:
        ok = abs(t) >= 3 and min(hs) > 0 and (by > 0).mean() > 0.5 and tro.net.mean() > 0
        out.append(f"  PRIMARY bar (t >= 3, both halves +, majority of years +, net mean > 0): {'PASS' if ok and t > 0 else 'FAIL'}")
    txt_is, _, _ = cell(ex, sig, "1993-01-01", "2012-12-31")
    out.append(f"  (in-sample 1993-2012, descriptive) {txt_is}")
    out.append(f"  (in-sample book) gross {stats(tr[tr.signal < OOS].gross)}")

    # R1 volatility control
    w = d.loc[OOS:]
    y = ex.gross.loc[OOS:]
    X = pd.DataFrame({"sig": sig.loc[OOS:].astype(float), "rv_z": w.rv_z})
    b1, t1 = hac(y, X)
    out.append(f"  R1 vol control: signal coefficient with lagged RV20 z-score in the regression {b1:+.3f}pp, t {t1:+.2f}")
    terc = pd.qcut(w.rv, 3, labels=["low", "mid", "high"])
    for lab in ("low", "mid", "high"):
        m = (terc == lab).values
        yy, ss = y[m], sig.loc[OOS:][m]
        if ss.sum() >= 10:
            dd_, tt_ = hac(yy, ss.rename("sig"))
            out.append(f"      RV20 {lab:4s} tercile: signal {100 * yy[ss].mean():+.3f}% (n {int(ss.sum())}) vs other "
                       f"{100 * yy[~ss].mean():+.3f}% | diff {dd_:+.3f}pp, t {tt_:+.2f}")

    # R2 random-entry null, R3 exposure-matched
    rets = d.ret.fillna(0).values
    i0 = d.index.get_indexer([d.loc[OOS:].index[0]])[0]
    days = lambda t_: np.concatenate([np.arange(a + 1, b + 1) for a, b in zip(t_.e, t_.x)]) if len(t_) else np.array([], int)
    mine_days = days(tro)
    mine = dict(bp_day=1e4 * rets[mine_days].mean(), mean_trade=100 * tro.gross.mean(), win=100 * (tro.gross > 0).mean())
    rng = np.random.default_rng(20260930)
    valid = np.flatnonzero(ex.gross.notna().values)
    valid = valid[valid >= i0]
    sims = []
    for _ in range(2000):
        rs = pd.Series(False, index=d.index)
        rs.iloc[rng.choice(valid, int(sig.loc[OOS:].sum()), replace=False)] = True
        rt = book(ex, rs)
        sims.append((1e4 * rets[days(rt)].mean(), 100 * rt.gross.mean(), 100 * (rt.gross > 0).mean()))
    sims = pd.DataFrame(sims, columns=["bp_day", "mean_trade", "win"])
    for c, unit in (("mean_trade", "% mean trade"), ("bp_day", "bp per long day"), ("win", "% winners")):
        q = sims[c]
        out.append(f"  R2 random-entry null, {unit:15s}: book {mine[c]:6.2f} | random median {q.median():6.2f} "
                   f"(5-95%: {q.quantile(.05):.2f} .. {q.quantile(.95):.2f}) | draws >= book {100 * (q >= mine[c]).mean():.2f}%")
    long = pd.Series(False, index=d.index)
    long.iloc[mine_days] = True
    lw, rw = long.loc[OOS:], d.ret.loc[OOS:]
    dl, tl = hac(rw, lw.rename("long"))
    cost = pd.Series(0.0, index=d.index)
    for r in tro.itertuples():
        cost.iloc[r.x] += r.gross - r.net
    eq = (1 + rw.where(lw, 0.0) - cost.loc[OOS:]).cumprod()
    bh = (1 + rw).cumprod()
    yrs = len(rw) / 252
    f = lambda e: f"CAGR {100 * (e.iloc[-1] ** (1 / yrs) - 1):.2f}%, maxDD {100 * (e / e.cummax() - 1).min():.1f}%"
    out.append(f"  R3 long days {1e4 * rw[lw].mean():+.2f} bp (n {int(lw.sum())}, {100 * lw.mean():.1f}% of days) vs flat days "
               f"{1e4 * rw[~lw].mean():+.2f} bp | diff {100 * dl:+.2f} bp, t {tl:+.2f}")
    out.append(f"     book net: {f(eq)} | buy-and-hold: {f(bh)}")

    exo = exit_frame(d, at_open=True)
    txt_o, _, _ = cell(exo, sig, OOS)
    out.append(f"  (exploratory, next-open entry and exit) {txt_o}")
    out.append(f"  (exploratory, next-open book net) {stats(book(exo, sig).query('signal >= @OOS').net)}")


def posthoc_1550(sym: str, d: pd.DataFrame, out: list[str]) -> None:
    m = pd.read_parquet(REPO / f"data/cache/intraday_hist/{sym}_1min.parquet", columns=["ts", "close"])
    m["day"] = m.ts.dt.normalize()
    last = m.groupby("day").ts.transform("max")
    pre = m[m.ts <= last - pd.Timedelta(minutes=10)].groupby("day").close.last()   # last print before T-10 min
    off = m.groupby("day").close.last()
    j = d.join(pre.rename("p1550")).join(off.rename("c1min")).loc[OOS:]
    j = j.dropna(subset=["p1550"])
    out.append(f"\n## POST HOC P1 -- {sym} D5 decided 10 minutes before the close, filled at the close "
               f"({len(j)} of {len(d.loc[OOS:])} days have 1-min data; median |1-min last / daily close - 1| "
               f"{1e4 * (j.c1min / j.close - 1).abs().median():.1f} bp)")
    low5 = d.low.shift(1).rolling(5).min().reindex(j.index)
    early, final = (j.p1550 < low5), sig_d5(d).reindex(j.index)
    out.append(f"  signal days: at the close {int(final.sum())}, at T-10 {int(early.sum())}, both {int((early & final).sum())}, "
               f"T-10 only {int((early & ~final).sum())}, close only {int((final & ~early).sum())}")
    ex = exit_frame(d)
    full = early.reindex(d.index).fillna(False).astype(bool)
    full.loc[:j.index[0]] = False
    exj, sj = ex.loc[j.index], full.loc[j.index]
    txt, _, _ = cell(exj, sj, OOS)
    out.append(f"  T-10 signal, close fill: {txt}")
    txt, _, _ = cell(exj, final.astype(bool), OOS)
    out.append(f"  close signal, same days: {txt}")
    tr = book(ex, full)
    out.append(f"  T-10 book net: {stats(tr.net)}")


def posthoc_regime(sym: str, d: pd.DataFrame, out: list[str]) -> None:
    ex, sig = exit_frame(d), sig_d5(d)
    up = (d.close > d.close.rolling(200).mean())
    out.append(f"\n## POST HOC, exploratory -- {sym} D5 by regime, 2013->")
    for lab, m in (("above 200d", up), ("below 200d", ~up)):
        mm = m.loc[OOS:].values
        y, ss = ex.gross.loc[OOS:][mm], sig.loc[OOS:][mm]
        dd_, tt_ = hac(y, ss.rename("sig"))
        out.append(f"  {lab}: signal {100 * y[ss].mean():+.3f}% (n {int(ss.sum())}, win {100 * (y[ss] > 0).mean():.1f}%) vs other "
                   f"{100 * y[~ss].mean():+.3f}% | diff {dd_:+.3f}pp, t {tt_:+.2f}")
    tr = book(ex, sig).query("signal >= @OOS")
    by = tr.groupby(tr.signal.dt.year).net.agg(lambda r: 100 * ((1 + r).prod() - 1))
    out.append("  book net return by year: " + " ".join(f"{y % 100:02d}:{v:+.1f}%" for y, v in by.items()))
    w = tr.nsmallest(5, "net")
    out.append("  five worst trades (net): " + ", ".join(f"{r.signal.date()} {100 * r.net:+.1f}%" for r in w.itertuples()))
    last = d.iloc[-1]
    rv_t = pd.qcut(d.rv.loc[OOS:], 3, labels=["low", "mid", "high"]).iloc[-1]
    out.append(f"  state at the last cached bar ({d.index[-1].date()}): {'above' if up.iloc[-1] else 'below'} the 200d, RV20 tercile {rv_t}, "
               f"signal {'ON' if sig.iloc[-1] else 'off'}")


def main() -> None:
    out = ["# Index dip family, one 2012-published rule on 2013-2026 -- pre-registration in the docstring"]
    for sym in ("SPY", "QQQ"):
        d = load(sym)
        out.append(f"\n# {sym} {d.index.min().date()} -> {d.index.max().date()}, {len(d)} days")
        ex = exit_frame(d)
        al = ex.gross.loc[OOS:].dropna()
        out.append(f"any-day entry with this exit, 2013->: {stats(al)} (overlapping, one per day)")
        report(sym, "D5 (close below the prior 5-day low)", d, sig_d5(d), out, primary=(sym == "SPY"))
        report(sym, "TT (down Monday)", d, sig_tt(d), out, primary=False)
        posthoc_1550(sym, d, out)
        posthoc_regime(sym, d, out)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

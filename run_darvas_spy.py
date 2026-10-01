#!/usr/bin/env python3
"""
Quantified Strategies "I Fixed the Darvas Box" (video b8Usenu2QIY, 2026-09-28) -- replication + control on SPY.
Pre-registered 2026-09-30, before the first run. Creator claim -> DISCOVERY track (|t| >= 3).

CLAIM (SPY 1993 -> 2026, TradeStation, no costs stated): 279 trades, 74.2% winners, +0.34% average trade, profit
factor 3.08; PF by era 2.70 / 2.78 / 3.94 (1993-2004, 2005-15, 2016-26); lookbacks 11/13/16/18/20 give PF 2.71-2.97.

RULES (as stated)
  box top   highest HIGH of the previous 12 trading days (t-12 .. t-1)
  entry     close_t > box top AND close_t <= box top * 1.0075 AND volume_t > 15-day average volume
            (TradeStation Average(Volume, 15) includes today; "excluding today" is a labelled sensitivity)
            -> buy the open of t+1
  exit      first day s >= t+1 with close_s > high_(s-1) -> sell the open of s+1   (the "QS exit")
  overlap   A (replication) = a signal while long is ignored, TradeStation default; B = re-enter at the same open.

DESIGN
  data      data/cache/index_daily_ftd.parquet (yfinance OHLCV + Adj Close; SPY 1993-01-29 -> 2026-09-18).
            Signals on RAW OHLC; returns on dividend-adjusted opens (open * AdjClose/Close), i.e. total return.
  costs     1 bp + $0.005/share per side (the index-ORB study's SPY cost). Gross and net side by side.
  REPLICATE trades, win rate, mean trade, PF, by era, lookback neighbourhood 11/12/13/16/18/20.

  PRIMARY   What does the ENTRY SIGNAL add? The exit sells only after strength and has no stop, so a high win rate is
            built in for ANY entry day. Hold SPY and the exit fixed and vary only the entry day:
              r_d = total return from the open of d+1 to the exit open under the same QS exit, for EVERY day d;
              primary cell = mean r_d on signal days minus mean r_d on all other days, OLS with HAC (10 lags).
            Bar: |t| >= 3, both halves the same sign (1993-2009 / 2010-2026), majority of years positive.
            The control varies the entry DAY only (same instrument, same exit, same fills) -- that is the question.
  SECONDARY (pre-registered, 2 cells; charged with the primary = 3 cells, Sidak 5% two-sided |t| >= 2.39; the
            discovery bar of 3 still governs)
    S1  exposure-matched: SPY open-to-open return on days the strategy is long vs days it is flat, HAC (10) t.
    S2  same test as the primary on QQQ (1999 ->) and IWM (2000 ->): he tested SPY only, so these are out of
        sample for the parameter choice. Reported per index, not pooled.
  EXPLORATORY (labelled, no claim): ablation of the three entry conditions (breakout only / + 0.75% cap / + volume),
            volume average excluding today, strategy CAGR / exposure / max drawdown vs buy-and-hold.
  The creator's own search is uncharged here: 12 is the best of the 6 lookbacks he shows, and the 0.75% cap and the
  15-day volume window come with no neighbourhood at all.

ADDED AFTER THE FIRST RUN (2026-09-30, labelled post hoc): the primary came back null per TRADE (t 0.09) while S1 came
back +7.3 bp per DAY (t 2.98). The two differ only in holding time, and S1's control (flat days) does not hold the
exit fixed. RANDOM-ENTRY NULL: draw the same number of signal days uniformly at random 2,000 times, run the identical
ignore-while-long book with the same exit, and place the strategy's per-long-day return, mean trade and mean bars in
that distribution. If random entries also earn ~11 bp per long day, S1 is the exit's arithmetic, not the entry.

Local run (one cached parquet, seconds of CPU).
Usage: PYTHONPATH=src .venv/bin/python3 run_darvas_spy.py   (log -> data/studies/logs/darvas_spy.log)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/index_daily_ftd.parquet"
LOG = REPO / "data/studies/logs/darvas_spy.log"
BP, PER_SHARE = 0.0001, 0.005
ERAS = (("1993-2004", "1993", "2004"), ("2005-2015", "2005", "2015"), ("2016-2026", "2016", "2026"))


def load(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(CACHE)
    d = d[d.ticker == sym].sort_index()
    d = d.rename(columns=str.lower).rename(columns={"adj close": "adj"})
    d["aopen"] = d.open * d.adj / d.close
    return d[["open", "high", "low", "close", "volume", "aopen"]].dropna()


def signals(d: pd.DataFrame, look: int = 12, cap: float | None = 0.0075, vol: int | None = 15,
            vol_incl_today: bool = True) -> pd.Series:
    top = d.high.shift(1).rolling(look).max()
    s = d.close > top
    if cap is not None:
        s &= d.close <= top * (1 + cap)
    if vol is not None:
        avg = d.volume.rolling(vol).mean() if vol_incl_today else d.volume.shift(1).rolling(vol).mean()
        s &= d.volume > avg
    return s.fillna(False)


def exit_frame(d: pd.DataFrame) -> pd.DataFrame:
    """For every day d: enter the open of d+1, exit the open after the first close above the prior day's high."""
    n = len(d)
    strong = (d.close > d.high.shift(1)).values
    nxt = np.full(n + 1, -1)                              # nxt[i] = first s >= i with strong[s]
    for i in range(n - 1, -1, -1):
        nxt[i] = i if strong[i] else nxt[i + 1]
    ao, ro = d.aopen.values, d.open.values
    rows = []
    for i in range(n - 1):
        e = i + 1
        s = nxt[e]
        if s < 0 or s + 1 >= n:
            rows.append((np.nan, np.nan, -1, -1))
            continue
        x = s + 1
        gross = ao[x] / ao[e] - 1
        cost = 2 * BP + PER_SHARE / ro[e] + PER_SHARE / ro[x]
        rows.append((gross, gross - cost, e, x))
    rows.append((np.nan, np.nan, -1, -1))
    return pd.DataFrame(rows, index=d.index, columns=["gross", "net", "e", "x"])


def trades(ex: pd.DataFrame, sig: pd.Series, reenter: bool = False) -> pd.DataFrame:
    out, free = [], 0                                     # free = first bar index at which we are flat
    for i in np.flatnonzero(sig.values):
        r = ex.iloc[i]
        if np.isnan(r.gross):
            continue
        if r.e < free or (r.e == free and not reenter):   # still long at the signal close (e == free: exiting next open)
            continue
        out.append(dict(signal=ex.index[i], gross=r.gross, net=r.net, e=int(r.e), x=int(r.x), bars=int(r.x - r.e)))
        free = int(r.x)
    return pd.DataFrame(out)


def stats(r: pd.Series) -> str:
    if r.empty:
        return "n 0"
    pf = r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else float("inf")
    return f"n {len(r):4d} | win {100 * (r > 0).mean():5.1f}% | mean {100 * r.mean():+.3f}% | PF {pf:5.2f}"


def hac(y: pd.Series, x: pd.Series, lags: int = 10):
    ok = y.notna()
    fit = sm.OLS(y[ok] * 100, sm.add_constant(x[ok].astype(float))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return fit.params.iloc[1], fit.tvalues.iloc[1]


def primary(ex: pd.DataFrame, sig: pd.Series, out: list[str], label: str) -> None:
    y = ex.gross
    ok = y.notna()
    diff, t = hac(y, sig)
    out.append(f"  {label}: signal days {100 * y[ok & sig].mean():+.3f}% (n {int((ok & sig).sum())}, win "
               f"{100 * (y[ok & sig] > 0).mean():.1f}%) vs other days {100 * y[ok & ~sig].mean():+.3f}% "
               f"(n {int((ok & ~sig).sum())}, win {100 * (y[ok & ~sig] > 0).mean():.1f}%) | diff {diff:+.3f}pp, t {t:+.2f}")
    for lab, a, b in (("1993-2009", "1993", "2009"), ("2010-2026", "2010", "2026")):
        if y.loc[a:b].notna().sum() > 250 and sig.loc[a:b].sum() > 5:
            dh, th = hac(y.loc[a:b], sig.loc[a:b])
            out.append(f"      half {lab}: diff {dh:+.3f}pp, t {th:+.2f}")
    yr = pd.DataFrame({"y": y[ok], "s": sig[ok]})
    by = yr.groupby(yr.index.year).apply(lambda g: g.y[g.s].mean() - g.y[~g.s].mean() if g.s.any() else np.nan).dropna()
    out.append(f"      years positive: {int((by > 0).sum())}/{len(by)}")


def main() -> None:
    out = ["# Darvas box on SPY (Quantified Strategies b8Usenu2QIY) -- pre-registration in the docstring"]
    d = load("SPY")
    ex = exit_frame(d)
    sig = signals(d)
    out.append(f"SPY {d.index.min().date()} -> {d.index.max().date()}, {len(d)} days, {int(sig.sum())} signal days")

    out.append("\n## REPLICATION (claim: n 279, win 74.2%, mean +0.34%, PF 3.08; eras 2.70 / 2.78 / 3.94)")
    for lab, re in (("A ignore-while-long", False), ("B re-enter", True)):
        tr = trades(ex, sig, re)
        out.append(f"  {lab:20s} gross {stats(tr.gross)} | avg bars {tr.bars.mean():.1f}")
        out.append(f"  {'':20s} net   {stats(tr.net)}")
        for era, a, b in ERAS:
            out.append(f"      {era}: {stats(tr.set_index('signal').loc[a:b].gross)}")
    out.append("  lookback neighbourhood (A, gross; claim 11: 2.75, 13: 2.97, 16: 2.84, 18: 2.71, 20: 2.80):")
    for look in (11, 12, 13, 16, 18, 20):
        out.append(f"      {look:2d}d: {stats(trades(ex, signals(d, look)).gross)}")

    out.append("\n## PRIMARY -- same exit, every entry day: does the signal day beat any other day?")
    primary(ex, sig, out, "SPY")
    al = ex.gross.dropna()
    out.append(f"  any-day entry with the QS exit: {stats(al)} (overlapping, one per day)")

    out.append("\n## S1 -- exposure-matched: open-to-open return on long days vs flat days")
    tr = trades(ex, sig)
    oo = d.aopen.shift(-1) / d.aopen - 1                  # return from open i to open i+1
    long = pd.Series(False, index=d.index)
    for r in tr.itertuples():
        long.iloc[r.e:r.x] = True
    diff, t = hac(oo, long)
    ok = oo.notna()
    out.append(f"  long days {1e4 * oo[ok & long].mean():+.2f} bp (n {int((ok & long).sum())}, {100 * long.mean():.1f}% of days) "
               f"vs flat days {1e4 * oo[ok & ~long].mean():+.2f} bp | diff {100 * diff:+.2f} bp, t {t:+.2f}")
    strat = np.where(long, oo.fillna(0), 0.0)
    cost = pd.Series(0.0, index=d.index)
    for r in tr.itertuples():
        cost.iloc[r.e] += r.gross - r.net
    eq, bh = (1 + pd.Series(strat, index=d.index) - cost).cumprod(), (1 + oo.fillna(0)).cumprod()
    yrs = len(d) / 252
    f = lambda e: f"CAGR {100 * (e.iloc[-1] ** (1 / yrs) - 1):.2f}%, maxDD {100 * (e / e.cummax() - 1).min():.1f}%"
    out.append(f"  (exploratory) strategy net: {f(eq)} | buy-and-hold: {f(bh)}")

    out.append("\n## POST HOC -- random-entry null for S1 (same count of signal days, same book, same exit; 2,000 draws)")
    rng = np.random.default_rng(20260930)
    valid = np.flatnonzero(ex.gross.notna().values)
    oov = oo.fillna(0).values
    sims = []
    for _ in range(2000):
        rs = pd.Series(False, index=d.index)
        rs.iloc[rng.choice(valid, int(sig.sum()), replace=False)] = True
        rt = trades(ex, rs)
        days = np.concatenate([np.arange(a, b) for a, b in zip(rt.e, rt.x)])
        sims.append((1e4 * oov[days].mean(), 100 * rt.gross.mean(), rt.bars.mean(), 100 * (rt.gross > 0).mean()))
    sims = pd.DataFrame(sims, columns=["bp_day", "mean_trade", "bars", "win"])
    mine = dict(bp_day=1e4 * oo[ok & long].mean(), mean_trade=100 * tr.gross.mean(), bars=tr.bars.mean(),
                win=100 * (tr.gross > 0).mean())
    for c, unit in (("bp_day", "bp per long day"), ("mean_trade", "% mean trade"), ("bars", "bars held"), ("win", "% winners")):
        q = sims[c]
        out.append(f"  {unit:16s} strategy {mine[c]:6.2f} | random median {q.median():6.2f} (5-95%: {q.quantile(.05):.2f} .. "
                   f"{q.quantile(.95):.2f}) | share of random draws >= strategy {100 * (q >= mine[c]).mean():.1f}%")

    out.append("\n## S2 -- other indexes (out of sample for the parameters)")
    for sym in ("QQQ", "IWM"):
        dd = load(sym)
        exx, sg = exit_frame(dd), signals(dd)
        out.append(f"  {sym} {dd.index.min().date()} -> : strategy A gross {stats(trades(exx, sg).gross)}")
        primary(exx, sg, out, sym)

    out.append("\n## EXPLORATORY -- ablation (SPY, all signal days vs other days, same exit)")
    for lab, kw in (("breakout only", dict(cap=None, vol=None)), ("+ 0.75% cap", dict(vol=None)),
                    ("+ volume (full rule)", {}), ("full, vol avg excl. today", dict(vol_incl_today=False)),
                    ("breakout + volume, no cap", dict(cap=None))):
        primary(ex, signals(d, **kw), out, f"{lab:26s}")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

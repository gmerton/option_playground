#!/usr/bin/env python3
"""
Cheap-convexity overlay: does a gated index-put hedge cut the BOOK's drawdown by more than it costs?

Queued 2026-09-20 (TEST_INDEX §10). The book is net long (breakouts, bull puts); only the straddle is
direction-neutral, and single-name shorts / ETF bear calls both failed. Idea (the Burry lesson): buy protection
when it is cheap, sell premium when it is rich -- the SPY VIX<20 selling cell is negative, so that is when the
hedge costs least.

Hedge: on the first trading day of each month, if the gate is open, spend a fixed premium budget (B%/yr of the
account, B/12 per month) on SPY or QQQ puts at the expiry nearest 75 DTE (55-100), strike nearest spot*(1-m).
Hold one month, sell on the next month's first trading day, re-evaluate the gate. Entry at the ASK, exit at the
BID (real fills; `--mid` variant for reference). Spot from put-call parity (v3 strikes are raw).
Variants: 5% OTM put, 10% OTM put, 5%/15% put debit spread (buy at ask, sell at bid; reverse on exit).
Gates: always, VIX < 20, VIX < 16, VIX below its trailing-252d median.

Book: three sleeves, monthly (entry month), 2018-04 -> 2026-02:
  straddle   data/cache/rsi_straddle.parquet (5,886 gated 7-DTE trades = the audited arm), mean roc/month
  bull put   data/cache/rsi_putspread.parquet (20-ETF roster, 45 DTE 0.35/0.25, 50% take, ceiling-filtered:
             +5.68%/trade reproduces the +5.70% post-erratum figure), mean roc/month
  breakout   data/studies/profit_lock/profit_lock_trades_2026-09-20.parquet BASE R (house process), mean R/month
Each sleeve scaled to equal monthly vol, summed, book scaled to BOOK_VOL per month. These are sleeve-level
per-trade averages turned into a risk-parity account -- an assumption, stated. The hedge's P&L in account % is
(B/12) * (exit value / premium paid - 1).

Usage: AWS_PROFILE=... PYTHONPATH=src .venv/bin/python3 run_put_overlay_study.py > data/studies/put_overlay/put_overlay_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
REPO = Path(__file__).resolve().parent
OUT = REPO / "data/studies/put_overlay"
CACHE = REPO / "data/cache/put_overlay_chain.parquet"
TODAY = date.today().isoformat()
BOOK_VOL = 4.0            # % per month (~14%/yr)
BUDGETS = [1.0, 2.0, 3.0, 5.0]   # % of account per year spent on premium
LAST_QUOTE = "2026-02-20"


def month_starts() -> list[pd.Timestamp]:
    from lib.athena_lib import athena
    d = athena("""SELECT DISTINCT trade_date FROM silver.options_daily_v3
                  WHERE ticker = 'SPY' AND trade_date BETWEEN DATE '2011-01-01' AND DATE '2026-02-28'""")
    d = pd.to_datetime(d.trade_date).sort_values()
    return list(d.groupby(d.dt.to_period("M")).min())


def pull_chain() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    from lib.athena_lib import athena
    ds = month_starts()
    frames = []
    for y in sorted({x.year for x in ds}):
        lst = ",".join(f"DATE '{x.date()}'" for x in ds if x.year == y)
        frames.append(athena(f"""
            SELECT ticker, trade_date, expiry, cp, strike, bid, ask
            FROM silver.options_daily_v3
            WHERE ticker IN ('SPY','QQQ') AND trade_date IN ({lst})
              AND date_diff('day', trade_date, expiry) BETWEEN 20 AND 110"""))
        print(f"  pulled {y}: {len(frames[-1]):,} rows", flush=True)
    ch = pd.concat(frames, ignore_index=True)
    ch["trade_date"], ch["expiry"] = pd.to_datetime(ch.trade_date), pd.to_datetime(ch.expiry)
    ch.to_parquet(CACHE, index=False)
    return ch


def parity_spot(g: pd.DataFrame) -> float:
    """Spot from put-call parity at the expiry nearest 30 DTE, near-ATM strikes (rates ignored: < 0.5% error)."""
    g = g[(g.bid > 0) & (g.ask > 0)].copy()
    g["mid"] = (g.bid + g.ask) / 2
    g["dte"] = (g.expiry - g.trade_date).dt.days
    e = g.loc[(g.dte - 30).abs().idxmin(), "expiry"]
    x = g[g.expiry == e].pivot_table(index="strike", columns="cp", values="mid").dropna()
    x["diff"] = (x["C"] - x["P"]).abs()
    near = x.nsmallest(4, "diff")
    return float((near.index + near["C"] - near["P"]).median())


def hedge_legs(ch: pd.DataFrame) -> pd.DataFrame:
    """For each (ticker, month start): chosen contracts, entry cost, and next-month exit value, per structure."""
    rows = []
    dates = sorted(ch.trade_date.unique())
    for tk in ["SPY", "QQQ"]:
        c = ch[ch.ticker == tk]
        by_day = {d: g for d, g in c.groupby("trade_date")}
        for d0, d1 in zip(dates[:-1], dates[1:]):
            if d0 not in by_day or d1 not in by_day:
                continue
            g0, g1 = by_day[d0], by_day[d1]
            try:
                S0, S1 = parity_spot(g0), parity_spot(g1)
            except (ValueError, KeyError):
                continue
            p0 = g0[(g0.cp == "P") & (g0.ask > 0)].copy()
            p0["dte"] = (p0.expiry - p0.trade_date).dt.days
            p0 = p0[p0.dte.between(55, 100)]
            if p0.empty:
                continue
            e = p0.loc[(p0.dte - 75).abs().idxmin(), "expiry"]
            p0 = p0[p0.expiry == e].set_index("strike")
            p1 = g1[(g1.cp == "P") & (g1.expiry == e)].set_index("strike")

            def leg(m):
                k = p0.index[np.abs(p0.index - S0 * (1 - m)).argmin()]
                a0, b0 = p0.loc[k, "ask"], p0.loc[k, "bid"]
                if k in p1.index and p1.loc[k, "bid"] > 0:
                    b1, a1 = p1.loc[k, "bid"], p1.loc[k, "ask"]
                else:                                     # no quote at exit: intrinsic
                    b1 = a1 = max(k - S1, 0.0)
                return k, float(a0), float(b0), float(b1), float(a1)

            k5, a5, b5, x5, y5 = leg(0.05)
            k10, a10, b10, x10, y10 = leg(0.10)
            k15, a15, b15, x15, y15 = leg(0.15)
            rec = dict(ticker=tk, date=d0, exit=d1, S0=S0, S1=S1, expiry=e, k5=k5, k10=k10, k15=k15)
            # real fills: buy at ask, sell at bid (spread short leg: sell at bid, buy back at ask)
            rec["put5"] = x5 / a5 - 1
            rec["put10"] = x10 / a10 - 1
            debit = a5 - b15
            rec["spr5_15"] = ((x5 - y15) / debit - 1) if debit > 0 and k15 < k5 else np.nan
            m5, m10, m15 = (a5 + b5) / 2, (a10 + b10) / 2, (a15 + b15) / 2
            rec["put5_mid"] = ((x5 + y5) / 2) / m5 - 1
            rec["put10_mid"] = ((x10 + y10) / 2) / m10 - 1
            rec["spr5_15_mid"] = ((x5 + y5) / 2 - (x15 + y15) / 2) / (m5 - m15) - 1 if m5 > m15 else np.nan
            rec["ba5"] = (a5 - b5) / m5
            rec["spx_ret"] = S1 / S0 - 1
            rows.append(rec)
    return pd.DataFrame(rows)


def vix_series() -> pd.Series:
    import yfinance as yf
    v = yf.download("^VIX", start="2010-01-01", end="2026-03-01", progress=False, auto_adjust=False)["Close"]
    v = v.iloc[:, 0] if isinstance(v, pd.DataFrame) else v
    v.index = pd.to_datetime(v.index)
    return v


def book_series() -> pd.DataFrame:
    s = pd.read_parquet(REPO / "data/cache/rsi_straddle.parquet")
    p = pd.read_parquet(REPO / "data/cache/rsi_putspread.parquet")
    b = pd.read_parquet(REPO / "data/studies/profit_lock/profit_lock_trades_2026-09-20.parquet")
    m = lambda d, col, v: d.groupby(pd.to_datetime(d[col]).dt.to_period("M"))[v].mean()
    B = pd.DataFrame({"straddle": m(s, "entry_date", "roc"), "bullput": m(p, "entry_date", "roc"),
                      "breakout": m(b, "date", "BASE")})
    B = B[(B.index >= pd.Period("2018-04", "M")) & (B.index <= pd.Period("2026-02", "M"))].fillna(0.0)
    Z = B / B.std()
    book = Z.sum(axis=1)
    B["book"] = book / book.std() * BOOK_VOL
    return B


def stats(r: pd.Series) -> dict:
    cum = r.cumsum()
    return dict(mean=r.mean(), t=r.mean() / r.std() * np.sqrt(len(r)), sharpe=r.mean() / r.std() * np.sqrt(12),
                maxDD=(cum.cummax() - cum).max(), worst=r.min(), worst3=r.nsmallest(3).mean(),
                y2020=r[r.index.year == 2020].sum(), y2022=r[r.index.year == 2022].sum())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ch = pull_chain()
    # v3 carries duplicate rows for some contracts: keep the one with the widest-valid quote (live bid first)
    ch = (ch.assign(_ok=(ch.bid > 0) & (ch.ask > 0)).sort_values("_ok", ascending=False)
            .drop_duplicates(["ticker", "trade_date", "expiry", "cp", "strike"]).drop(columns="_ok"))
    H = hedge_legs(ch)
    v = vix_series()
    vix_at = lambda d: float(v[:d].iloc[-1])
    H["vix"] = H.date.map(vix_at)
    med = v.rolling(252).median()
    H["vix_med"] = H.date.map(lambda d: float(med[:d].iloc[-1]))
    H["month"] = H.date.dt.to_period("M")
    H.to_parquet(OUT / f"put_overlay_legs_{TODAY}.parquet", index=False)
    gates = {"always": H.vix > 0, "vix<20": H.vix < 20, "vix<16": H.vix < 16, "vix<median": H.vix < H.vix_med}
    structs = ["put5", "put10", "spr5_15"]

    print(f"hedge months: {H.month.nunique()} ({H.date.min().date()} -> {H.date.max().date()}), "
          f"median 5% put bid/ask = {100 * H.ba5.median():.1f}% of mid")
    print("\n=== 1. the hedge ALONE: mean monthly return on premium (real fills / mid), share of months it pays, "
          "best month; 2011-2026 ===")
    rows = []
    for tk in ["SPY", "QQQ"]:
        for gname, gm in gates.items():
            X = H[(H.ticker == tk) & gm]
            for s in structs:
                r = X[s].dropna()
                rows.append(dict(ticker=tk, gate=gname, struct=s, months=len(r), open_pct=100 * gm[H.ticker == tk].mean(),
                                 mean=100 * r.mean(), mean_mid=100 * X[s + "_mid"].mean(), paid=100 * (r > 0).mean(),
                                 best=100 * r.max(), carry_yr=100 * r.mean() * 12 * gm[H.ticker == tk].mean()))
    A = pd.DataFrame(rows)
    print(A.round(1).to_string(index=False))

    B = book_series()
    print(f"\n=== 2. the book: {len(B)} months, sleeves scaled to equal vol, book {BOOK_VOL}%/month ===")
    print("sleeve correlations:"); print(B[["straddle", "bullput", "breakout"]].corr().round(2).to_string())
    base = stats(B.book)
    Hm = H.set_index(["ticker", "month"])
    print("\n=== 3. book + overlay (account %): budget = % of account/yr spent on premium; 'dDD' = maxDD change ===")
    out = [dict(ticker="-", gate="none", struct="-", budget=0, **base)]
    for tk in ["SPY", "QQQ"]:
        for gname in gates:
            for s in structs:
                h = Hm.loc[tk]
                on = gates[gname][H.ticker == tk].values
                hr = pd.Series(np.where(on, h[s].values, 0.0), index=h.index).reindex(B.index).fillna(0.0)
                for bud in BUDGETS:
                    r = B.book + (bud / 12) * 100 * hr / 100
                    out.append(dict(ticker=tk, gate=gname, struct=s, budget=bud, **stats(r)))
    R = pd.DataFrame(out)
    R["dSharpe"] = R.sharpe - base["sharpe"]
    R["dDD"] = R.maxDD - base["maxDD"]
    R["dMean"] = R["mean"] - base["mean"]
    cols = ["ticker", "gate", "struct", "budget", "mean", "dMean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "worst3",
            "y2020", "y2022"]
    print(R[R.budget.isin([0, 2.0])][cols].round(2).to_string(index=False))
    print("\n--- budget sweep, SPY 5% put (every gate) ---")
    print(R[(R.ticker.isin(["-", "SPY"])) & (R.struct.isin(["-", "put5"]))][cols].round(2).to_string(index=False))

    # the book's worst months: what did each hedge pay?
    print("\n=== 4. the book's 10 worst months: SPY 5% put return on premium, gated or not ===")
    w = B.book.nsmallest(10).index
    h = Hm.loc["SPY"]
    W = pd.DataFrame({"book%": B.book.loc[w], "put5_ret%": 100 * h.reindex(w)["put5"], "vix": h.reindex(w)["vix"],
                      "spy_mo%": 100 * h.reindex(w)["spx_ret"]})
    W["gate_vix<20"] = W.vix < 20
    print(W.round(1).to_string())
    print(f"\ncorrelation book vs SPY 5% put (ungated): {B.book.corr(h['put5'].reindex(B.index)):.2f}; "
          f"book vs SPY month: {B.book.corr(h['spx_ret'].reindex(B.index)):.2f}")
    # sensitivity: a book WITHOUT the straddle sleeve (the live book runs heavier in stock + bull puts)
    print("\n=== 5. sensitivity: book = bull put + breakout only (no straddle), same vol target ===")
    z = B[["bullput", "breakout"]] / B[["bullput", "breakout"]].std()
    nb = z.sum(axis=1); nb = nb / nb.std() * BOOK_VOL
    print(f"corr with SPY month: {nb.corr(h['spx_ret'].reindex(B.index)):.2f}")
    rows5 = [dict(gate="none", struct="-", budget=0, **stats(nb))]
    for gname in ["always", "vix<20"]:
        on = gates[gname][H.ticker == "SPY"].values
        for s in structs:
            hr = pd.Series(np.where(on, h[s].values, 0.0), index=h.index).reindex(B.index).fillna(0.0)
            for bud in [2.0, 5.0]:
                rows5.append(dict(gate=gname, struct=s, budget=bud, **stats(nb + (bud / 12) * hr)))
    R5 = pd.DataFrame(rows5); b0 = R5.iloc[0]
    R5["dSharpe"], R5["dDD"] = R5.sharpe - b0.sharpe, R5.maxDD - b0.maxDD
    print(R5[["gate", "struct", "budget", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "y2020", "y2022"]]
          .round(2).to_string(index=False))
    print("\n=== 6. the hedge in the market's worst months (SPY 5% put, return on premium) ===")
    sm = h.sort_values("spx_ret").head(8)
    print(pd.DataFrame({"spy_mo%": 100 * sm.spx_ret, "vix_at_entry": sm.vix, "put5%": 100 * sm.put5,
                        "gate_vix<20": sm.vix < 20}).round(1).to_string())
    R.to_csv(OUT / f"put_overlay_summary_{TODAY}.csv", index=False)
    A.to_csv(OUT / f"put_overlay_alone_{TODAY}.csv", index=False)


if __name__ == "__main__":
    main()

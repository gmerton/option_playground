#!/usr/bin/env python3
"""
SINCLAIR: FUNDAMENTAL-FACTOR STRADDLE PORTFOLIOS on the S&P 100 ex-financials (pre-registered 2026-09-28, before any
option pull; Gabe typed the rule from Euan Sinclair, "Positional Option Trading" (2020), and chose the defaults for
what the book leaves open: "he doesn't say. Go with the default.")

THE BOOK (as typed): universe = S&P 100 excluding financials. "On the Friday of each week, I ranked all the stocks
according to the valuation metrics and then formed an option portfolio based on this ranking by selling straddles on
the top quartile of stocks and buying straddles on the bottom quartile. Specifically, we traded ATM straddles in the
second monthly expiry. Each trade is done in a notional size of $10,000. As an example, he would long options on low
P/E stocks and short options on high P/E stocks." Factors: P/E, P/B, market cap, P/CF, D/E, RoE, RoA. The book's own
results were not provided.

WHY NEW. No fundamental factor has ever been tested in this ledger, on stocks or options. Siblings on the option side:
Goyal-Saretto and Vasquez (single-stock straddle sorts on vol signals) both died on costs, on a broader, less liquid
universe; this one is 86 mega-caps, where the spreads are the tightest in the market.

UNIVERSE  today's S&P 100 (Wikipedia, 2026-09-28) minus GICS Financials = 86 names, GOOG dropped as a duplicate of
          GOOGL -> 85. ⚠ SURVIVOR / LOOK-AHEAD BIAS, declared: today's members, not point-in-time membership. The sort
          is relative inside the universe, so both legs carry it; the absolute level is not interpretable. Historic
          v3 symbols mapped (FB -> META, UTX -> RTX).
FUNDAMENTALS  SEC XBRL company facts (pulled per name incl. predecessor CIKs -- XOM, AVGO, Alphabet; equity / net
          income / op. cash flow fall back to the incl.-NCI / ProfitLoss / continuing-ops tags where missing), POINT-IN-
          TIME: only facts FILED before the ranking Friday. Flows (net income, operating cash flow) are trailing-12-month
          = latest annual, or YTD + prior annual - prior-year YTD. Stocks (equity, assets, liabilities) = latest filed.
          Shares = cover-page count (fallbacks: balance-sheet count, weighted basic), split-adjusted to the Friday.
          Market cap = shares x raw close (chain_spot_daily).
METRICS and SIDES (short straddles = TOP quartile of the metric, long = BOTTOM, per the book)
          P/E   ranked on E/P reversed; negative earnings = highest P/E (short side)
          P/B   ranked on B/P reversed; negative equity = highest P/B
          P/CF  ranked on CF/P reversed; negative cash flow = highest P/CF
          MCAP  largest quartile short, smallest long
          D/E   total liabilities / equity (liabilities missing -> assets - equity); negative equity = highest D/E
          RoE   net income TTM / equity; negative equity excluded from this sort
          RoA   net income TTM / assets
TRADE     each Friday (last session of the week) 2010-01 -> 2026-02 (v3 bid/ask coverage): the ATM straddle (call delta
          nearest 0.50, both legs quoted) in the SECOND standard monthly expiry after the Friday (an expiry falling on
          the Friday itself does not count; pre-2015 Saturday expiries mapped). Size = $10,000 of stock notional
          (10,000 / spot shares-equivalent). HELD ONE WEEK, exit at the next Friday's quotes; DELTA-HEDGED at each
          close with v3 deltas (stock hedge 2 bp of traded notional). House costs on every option trade: 25% of each
          leg's quoted spread + $0.0065/share/leg, entry AND exit. A straddle with no exit quote is dropped and counted.
PRIMARY   per factor, the weekly portfolio return = mean $ P&L of the long-quartile straddles + mean $ P&L of the
          short-quartile straddles, per $10,000 notional (in bp of notional). Newey-West t (lag 4) over ~800 weeks.
          Positive = the book's direction works. BAR (7 factors; house |t| >= 3 is stricter than Sidak-7 2.69): a factor
          PASSES with t >= 3, both halves (split 2018-01) > 0, positive in a majority of years.
SECONDARY gross (mid-to-mid, no costs); each leg alone; UNHEDGED; HELD TO EXPIRY (daily hedge, settled at intrinsic
          on raw spot, entry costs only; overlapping cohorts, NW lag 9); per year; names per quartile; share of
          straddles dropped for a missing exit quote.
PRIOR     weekly round trips pay the spread twice a week; on mega-caps a ~45-DTE ATM straddle's quoted spread is ~1-3%
          of mid, so ~0.5-1.5% of premium per week in friction. A factor needs a gross vol-pricing error of that order
          every week. Expect NULL net on most; the likeliest gross signal is MCAP (small caps carry richer vol premia).
Local: ~34 Athena queries (formation + paths, one per year each) cached to data/cache/sinclair_fund/; CPU minutes.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_sinclair_fundamental_straddles.py
     (log -> data/studies/logs/sinclair_fundamental_straddles.log)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from lib.athena_lib import athena

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/sinclair_fund"
LOG = REPO / "data/studies/logs/sinclair_fundamental_straddles.log"
START, END, SPLIT = "2010-01-01", "2026-02-20", "2018-01-01"
SLIP, COMM, HEDGE_BP, NOTIONAL = 0.25, 0.0065, 0.0002, 10_000.0
ALIAS = {"FB": "META", "UTX": "RTX"}
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai", "Accept-Encoding": "gzip, deflate"}
FACT_TAGS = ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic",
             "NetIncomeLoss", "Assets", "Liabilities", "StockholdersEquity", "NetCashProvidedByUsedInOperatingActivities"]


def log(m):
    print(m, file=sys.stderr, flush=True)


def nw_t(x, lag=4):
    x = pd.Series(x).dropna().values; n = len(x)
    if n < 10:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n
    s = g0 + 2 * sum((1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, lag + 1))
    return float(x.mean() / np.sqrt(s / n))


# ------------------------------------------------------------------ universe + fundamentals
def universe() -> list[str]:
    t = pd.read_csv(REPO / "data/cache/sp100_wikipedia_2026-09-28.csv")
    u = t[t.Sector != "Financials"].Symbol.str.replace(".", "-", regex=False).tolist()
    return sorted(set(u) - {"GOOG"})


EXTRA_CIKS = {"XOM": ["0000034088"], "AVGO": ["0001441634", "0001649338"], "GOOGL": ["0001288776"]}
FALLBACK = {"StockholdersEquity": "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "NetIncomeLoss": "ProfitLoss",
            "NetCashProvidedByUsedInOperatingActivities": "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"}


def load_facts(U) -> pd.DataFrame:
    """SEC company facts pulled fresh for the universe (current CIK + predecessor CIKs); a fallback tag fills a
    primary tag only where the primary has no fact for that period end."""
    f = CACHE / "facts.parquet"
    if not f.exists():
        ct = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=60).json()
        m = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in ct.values()}
        want = set(FACT_TAGS) | set(FALLBACK.values())
        rows = []
        for t in U:
            for cik in [m.get(t)] + EXTRA_CIKS.get(t, []):
                if not cik:
                    continue
                r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=UA, timeout=120)
                time.sleep(0.15)
                if r.status_code != 200:
                    log(f"  facts {t} {cik}: HTTP {r.status_code}"); continue
                for ns, tags in r.json()["facts"].items():
                    for tag, body in tags.items():
                        if tag not in want:
                            continue
                        for unit, vals in body["units"].items():
                            for v in vals:
                                rows.append(dict(cik=cik, ticker=t, tag=tag, unit=unit, val=v["val"], start=v.get("start"),
                                                 end=v["end"], form=v.get("form"), filed=v["filed"]))
            log(f"  facts {t}")
        d = pd.DataFrame(rows)
        for c in ("start", "end", "filed"):
            d[c] = pd.to_datetime(d[c])
        d.to_parquet(f, index=False)
    d = pd.read_parquet(f).dropna(subset=["val", "end", "filed"])
    d = d[d.unit.isin(["USD", "shares"])]
    for prim, fb in FALLBACK.items():
        have = set(zip(d[d.tag == prim].ticker, d[d.tag == prim].end))
        x = d[d.tag == fb]
        x = x[[(t, e) not in have for t, e in zip(x.ticker, x.end)]].assign(tag=prim)
        d = pd.concat([d[d.tag != fb], x], ignore_index=True)
    return d


def ttm(f: pd.DataFrame, D) -> float:
    """Trailing-12-month flow from duration facts filed before D."""
    f = f[(f.filed < D) & f.start.notna()]
    if f.empty:
        return np.nan
    f = f.assign(dur=(f.end - f.start).dt.days).sort_values("filed").drop_duplicates(["start", "end"], keep="last")
    E = f.end.max()
    cur = f[f.end == E]
    ann = cur[(cur.dur >= 350) & (cur.dur <= 380)]
    if len(ann):
        return float(ann.val.iloc[-1])
    ytd = cur[(cur.dur >= 80) & (cur.dur <= 290)].sort_values("dur")
    if ytd.empty:
        return np.nan
    y = ytd.iloc[-1]
    prevA = f[(f.dur >= 350) & (f.dur <= 380) & ((f.end - (y.start - pd.Timedelta(days=1))).dt.days.abs() <= 10)]
    prevY = f[((f.end - (E - pd.DateOffset(years=1))).dt.days.abs() <= 10) & ((f.dur - y.dur).abs() <= 15)]
    if prevA.empty or prevY.empty:
        return np.nan
    return float(y.val + prevA.val.iloc[-1] - prevY.val.iloc[-1])


def latest(f: pd.DataFrame, D):
    f = f[f.filed < D]
    if f.empty:
        return np.nan, pd.NaT
    f = f.sort_values(["end", "filed"])
    return float(f.val.iloc[-1]), f.end.iloc[-1]


def fundamentals(F: pd.DataFrame, fridays, raw: pd.DataFrame, U) -> pd.DataFrame:
    f = CACHE / "fundamentals.parquet"
    if f.exists():
        return pd.read_parquet(f)
    sp = pd.read_parquet(REPO / "data/cache/pit/splits.parquet")
    sp["execution_date"] = pd.to_datetime(sp.execution_date)
    sp = sp[(sp.split_from > 0) & (sp.split_to > 0)]
    rows = []
    G = {k: g for k, g in F.groupby(["ticker", "tag"])}
    for t in U:
        spl = sp[sp.ticker == t]
        g = lambda tag: G.get((t, tag), pd.DataFrame(columns=F.columns))
        for D in fridays:
            if t not in raw.columns or not np.isfinite(raw.at[D, t]):
                continue
            sh, se = np.nan, pd.NaT
            for tag in ("EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"):
                sh, se = latest(g(tag), D)
                if np.isfinite(sh):
                    break
            if not np.isfinite(sh):
                w = g("WeightedAverageNumberOfSharesOutstandingBasic")
                sh, se = latest(w, D)
            if not np.isfinite(sh):
                continue
            for r in spl[(spl.execution_date > se) & (spl.execution_date <= D)].itertuples():
                sh *= r.split_to / r.split_from
            px = raw.at[D, t]
            ni, ocf = ttm(g("NetIncomeLoss"), D), ttm(g("NetCashProvidedByUsedInOperatingActivities"), D)
            eq, _ = latest(g("StockholdersEquity"), D)
            at, _ = latest(g("Assets"), D)
            li, _ = latest(g("Liabilities"), D)
            if not np.isfinite(li) and np.isfinite(at) and np.isfinite(eq):
                li = at - eq
            rows.append(dict(ticker=t, trade_date=D, mcap=sh * px, ni=ni, ocf=ocf, eq=eq, assets=at, liab=li))
        log(f"  fundamentals {t}")
    d = pd.DataFrame(rows)
    d.to_parquet(f, index=False)
    return d


def metrics(X: pd.DataFrame) -> dict[str, pd.Series]:
    """Each returns a SCORE where HIGH = the book's TOP quartile (short straddles)."""
    s = {}
    s["P/E"] = -(X.ni / X.mcap)                  # low E/P (incl. negative E) = high P/E
    s["P/B"] = -(X.eq / X.mcap)
    s["P/CF"] = -(X.ocf / X.mcap)
    s["MCAP"] = X.mcap
    de = X.liab / X.eq
    s["D/E"] = de.where(X.eq > 0, np.inf)
    s["RoE"] = (X.ni / X.eq).where(X.eq > 0)
    s["RoA"] = X.ni / X.assets
    return {k: v.replace([np.inf], 1e18) for k, v in s.items()}


# ------------------------------------------------------------------ options
def third_friday(y, m):
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)


def second_monthly(D):
    out = []
    y, m = D.year, D.month
    while len(out) < 2:
        tf = third_friday(y, m)
        if tf > D:
            out.append(tf)
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out[1]


def pull_formation(fridays, U) -> pd.DataFrame:
    vt = sorted(set(U) | {k for k, v in ALIAS.items() if v in U})
    out = []
    for y in sorted({d.year for d in fridays}):
        f = CACHE / f"formation_{y}.parquet"
        if not f.exists():
            ds = [d for d in fridays if d.year == y]
            ex = sorted({second_monthly(d) + pd.Timedelta(days=k) for d in ds for k in (-1, 0, 1)})
            log(f"  formation pull {y}")
            athena(f"""SELECT ticker, trade_date, expiry, strike, cp, bid, ask, delta FROM options_daily_v3
                       WHERE ticker IN ({",".join(f"'{t}'" for t in vt)})
                         AND trade_date IN ({",".join(f"DATE '{d.date()}'" for d in ds)})
                         AND expiry IN ({",".join(f"DATE '{e.date()}'" for e in ex)})
                         AND bid > 0 AND ask > 0 AND abs(delta) BETWEEN 0.30 AND 0.70""").to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"):
        d[c] = pd.to_datetime(d[c])
    d["ticker"] = d.ticker.replace(ALIAS)
    d["cp"] = d.cp.str.upper().str[0]
    d["want"] = d.trade_date.map(lambda x: second_monthly(x))
    d = d[(d.expiry - d.want).dt.days.abs() <= 1]
    c = d[d.cp == "C"].drop_duplicates(["ticker", "trade_date", "expiry", "strike"])
    p = d[d.cp == "P"].drop_duplicates(["ticker", "trade_date", "expiry", "strike"])
    m = c.merge(p, on=["ticker", "trade_date", "expiry", "strike"], suffixes=("_c", "_p"))
    m["dd"] = (m.delta_c - 0.5).abs()
    m = m.sort_values("dd").drop_duplicates(["ticker", "trade_date"])
    return m[["ticker", "trade_date", "expiry", "strike", "bid_c", "ask_c", "bid_p", "ask_p"]]


def pull_paths(S: pd.DataFrame) -> pd.DataFrame:
    inv = {v: k for k, v in ALIAS.items()}
    out = []
    for y, g in S.groupby(S.trade_date.dt.year):
        f = CACHE / f"paths_{y}.parquet"
        if not f.exists():
            tl = sorted(set(g.ticker) | {inv[t] for t in g.ticker if t in inv})
            log(f"  path pull {y} ({len(g)} straddles)")
            q = athena(f"""SELECT ticker, trade_date, expiry, strike, cp, bid, ask, delta FROM options_daily_v3
                           WHERE ticker IN ({",".join(f"'{t}'" for t in tl)})
                             AND expiry IN ({",".join(f"DATE '{e.date()}'" for e in sorted(g.expiry.unique()))})
                             AND strike IN ({",".join(f"{k:g}" for k in sorted(g.strike.unique()))})
                             AND trade_date BETWEEN DATE '{g.trade_date.min().date()}' AND DATE '{g.expiry.max().date()}'""")
            q["ticker"] = q.ticker.replace(ALIAS)
            for c in ("trade_date", "expiry"):
                q[c] = pd.to_datetime(q[c])
            q = q.merge(g[["ticker", "expiry", "strike"]].drop_duplicates(), on=["ticker", "expiry", "strike"])
            q.to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    d["cp"] = d.cp.str.upper().str[0]
    return d.drop_duplicates(["ticker", "expiry", "strike", "cp", "trade_date"])


def pnl(S, P, raw, fridays) -> pd.DataFrame:
    nxt = dict(zip(fridays[:-1], fridays[1:]))
    W = P.pivot_table(index=["ticker", "expiry", "strike", "trade_date"], columns="cp", values=["bid", "ask", "delta"], aggfunc="mean")
    days = raw.index
    rows = []
    for r in S.itertuples():
        D1 = nxt.get(r.trade_date)
        if D1 is None or r.ticker not in raw.columns:
            continue
        try:
            w = W.loc[(r.ticker, r.expiry, r.strike)]
        except KeyError:
            continue
        sp = raw[r.ticker]
        s0 = sp.get(r.trade_date, np.nan)
        if not np.isfinite(s0) or s0 <= 0:
            continue
        n = NOTIONAL / s0
        mid0 = (r.bid_c + r.ask_c + r.bid_p + r.ask_p) / 2
        c0 = SLIP * ((r.ask_c - r.bid_c) + (r.ask_p - r.bid_p)) + 2 * COMM

        def leg(end):
            i0, i1 = days.get_loc(r.trade_date), days.searchsorted(end, side="right") - 1
            path = sp.iloc[i0:i1 + 1].ffill()
            dl = (w[("delta", "C")] + w[("delta", "P")]).reindex(path.index).ffill().fillna(0.0)
            h = -dl.values[:-1]
            s = path.values
            hedge = float(np.nansum(h * np.diff(s)))
            tr = np.abs(np.diff(np.concatenate([[0.0], h, [0.0]])))
            hc = float(HEDGE_BP * np.nansum(tr * np.concatenate([s[:-1], [s[-1]]])))
            return hedge, hc, s[-1]

        rec = dict(ticker=r.ticker, trade_date=r.trade_date, prem_pct=100 * mid0 / s0, spr_pct=100 * c0 / mid0)
        # one-week hold
        q1 = w.loc[D1] if D1 in w.index else None
        if q1 is not None and np.isfinite(q1[("bid", "C")]) and np.isfinite(q1[("bid", "P")]) and q1[("ask", "C")] > 0 and q1[("ask", "P")] > 0:
            mid1 = (q1[("bid", "C")] + q1[("ask", "C")] + q1[("bid", "P")] + q1[("ask", "P")]) / 2
            c1 = SLIP * ((q1[("ask", "C")] - q1[("bid", "C")]) + (q1[("ask", "P")] - q1[("bid", "P")])) + 2 * COMM
            hedge, hc, _ = leg(D1)
            rec.update(L_gross=n * (mid1 - mid0 + hedge), L_net=n * (mid1 - c1 - mid0 - c0 + hedge - hc),
                       S_gross=n * (mid0 - mid1 - hedge), S_net=n * (mid0 - c0 - mid1 - c1 - hedge - hc),
                       L_unh=n * (mid1 - c1 - mid0 - c0), S_unh=n * (mid0 - c0 - mid1 - c1))
        # hold to expiry
        iT = days.searchsorted(r.expiry, side="right") - 1
        if iT > days.get_loc(r.trade_date) and days[iT] >= r.expiry - pd.Timedelta(days=4):
            hedge, hc, sT = leg(days[iT])
            pay = abs(sT - r.strike)
            rec.update(LX_net=n * (pay - mid0 - c0 + hedge - hc), SX_net=n * (mid0 - c0 - pay - hedge - hc))
        rows.append(rec)
    return pd.DataFrame(rows)


def evaluate(E, fac, score, out, res):
    E = E.assign(score=score.values).dropna(subset=["score"])
    E["q"] = E.groupby("trade_date").score.transform(lambda s: pd.qcut(s.rank(method="first"), 4, labels=False))
    lo, hi = E[E.q == 0], E[E.q == 3]

    def port(lc, sc, lag=4, lab=""):
        a, b = lo.groupby("trade_date")[lc].mean(), hi.groupby("trade_date")[sc].mean()
        x = (a + b).dropna() / NOTIONAL * 1e4          # bp of notional
        return x, nw_t(x, lag)
    x, t = port("L_net", "S_net")
    h = x.index < pd.Timestamp(SPLIT); yr = x.groupby(x.index.year).mean()
    g, tg = port("L_gross", "S_gross")
    u, tu = port("L_unh", "S_unh")
    xe, te = port("LX_net", "SX_net", lag=9)
    la = lo.groupby("trade_date").L_net.mean().dropna() / NOTIONAL * 1e4
    sa = hi.groupby("trade_date").S_net.mean().dropna() / NOTIONAL * 1e4
    ok = t >= 3 and x[h].mean() > 0 and x[~h].mean() > 0 and (yr > 0).sum() > len(yr) / 2
    out.append(f"  {fac:5s} NET {x.mean():+6.2f}bp/wk t {t:+5.2f} halves {x[h].mean():+6.2f}/{x[~h].mean():+6.2f} yrs+ {(yr > 0).sum():2d}/{len(yr)} "
               f"| gross {g.mean():+6.2f} (t {tg:+5.2f}) | long leg {la.mean():+6.2f} short leg {sa.mean():+6.2f} | unhedged {u.mean():+6.2f} (t {tu:+5.2f}) "
               f"| to-expiry {xe.mean():+7.2f} (t {te:+5.2f}) | ~{len(lo) / max(lo.trade_date.nunique(), 1):.0f}/quartile {'PASS' if ok else ''}")
    res[fac] = x.groupby(x.index.year).mean()


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    import run_dip_survivorship as DS
    d = DS.pull()
    d["ticker"] = d.ticker.replace(ALIAS)
    raw = d.pivot_table(index="trade_date", columns="ticker", values="spot").sort_index()
    raw.index = pd.to_datetime(raw.index)
    U = [t for t in universe() if t in raw.columns]
    idx = raw.index[(raw.index >= START) & (raw.index <= END)]
    s = pd.Series(idx, index=idx)
    fridays = list(s.groupby(idx.to_period("W")).max())
    F = load_facts(U)
    X = fundamentals(F, fridays, raw, U)
    S = pull_formation(fridays, U)
    log(f"  straddles: {len(S):,}")
    P = pull_paths(S)
    R = pnl(S, P, raw, fridays)
    E = R.merge(X, on=["ticker", "trade_date"], how="inner")
    out = ["# Sinclair fundamental-factor straddle portfolios, S&P 100 ex-financials (pre-registration in the docstring)",
           f"universe {len(U)} names; straddles with fundamentals {len(E):,} over {E.trade_date.nunique()} Fridays "
           f"({E.trade_date.min().date()} -> {E.trade_date.max().date()}); median premium {E.prem_pct.median():.1f}% of spot; "
           f"median entry cost {E.spr_pct.median():.1f}% of premium; dropped for no exit quote {100 * E.L_net.isna().mean():.1f}%",
           "units: weekly portfolio P&L in bp of $10,000 notional per straddle (long-quartile mean + short-quartile mean); "
           "to-expiry = same cohorts held to expiry (entry cost only, NW lag 9)\n"]
    res = {}
    for fac, sc in metrics(E).items():
        evaluate(E, fac, sc, out, res)
    out.append("\nNET by year (bp/wk):\n" + pd.DataFrame(res).round(1).T.to_string())
    E.to_parquet(REPO / "data/studies/logs/sinclair_fundamental_straddles.parquet", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

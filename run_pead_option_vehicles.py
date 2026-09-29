#!/usr/bin/env python3
"""
SINCLAIR'S PEAD VEHICLES: call spread after a beat, put spread after a miss, covered call / covered put
(pre-registered 2026-09-28, before any option pull; Gabe typed the claim from Euan Sinclair, "Positional Option
Trading" (2020); "yes, pre-register it and run it").

CLAIM (as typed). "For stocks with positive earnings surprises, being long a short-dated 40 delta / 10 delta call
spread is usually a cheap way to leverage PEAD. For bearish positions a 50 delta / 20 delta put spread achieves the
same effect while also selling one of the most expensive parts of the implied vol curve. An alternative approach is to
sell a covered call or put. Although the variance premium being collected won't be significant, this method is
guaranteed to profit if any drift occurs at all."

WHY NEW. PEAD on the STOCK is NULL here (pead_2026-09-20.md: 12,232 events, no surprise bucket passes; DR-EP buying
the catalyst day -0.17R t -4.70). A vehicle cannot create a drift, so the call-spread arm has a low prior. The new axis
is the vol half: the 50/20 put spread SELLS the rich downside wing and may pay with no drift at all. The control below
separates "the surprise helps" from "the structure pays anyway".

EVENTS   data/cache/earnings_yf.parquet (yfinance actual vs estimate EPS, AMC/BMO timing), sessions 2010-01 -> 2026-01.
         REACTION DAY = the session date for BMO, the next session for AMC or unknown timing. ENTRY at the reaction-day
         close (raw spot, chain_spot_daily), i.e. once the surprise and the first reaction are public.
         BEAT = surprise >= +10%; MISS = surprise <= -10% (the buckets of the stock PEAD test). EXPLORATORY: any sign.
UNIVERSE at entry: 50-session mean option volume >= 1,000 contracts, spot >= $10, no split before expiry.
EXPIRY   nearest 30 DTE within 20-45 ("short-dated").
ARMS (all held to expiry, settled at intrinsic on the raw spot; no management)
   A  BEAT: long ~0.40-delta call / short ~0.10-delta call above it. Return per $ debit.
   B  MISS: long ~0.50-delta put / short ~0.20-delta put below it. Return per $ debit.
   C  BEAT: covered call = long stock + short ~0.30-delta call (strike unstated in the book; declared). Return on
      the net cost (spot - call credit).
   D  MISS: covered put = short stock + short ~0.30-delta put. Return per $ of spot shorted. (No borrow fee, no
      dividends: declared omissions, both small over ~30 days on liquid names.)
FILLS    house model: each option leg at mid +/- 25% of its quoted spread + $0.0065/share; stock 10 bp per side.
CONTROL  the SAME name and the SAME structure entered at the first session >= 25 sessions after the reaction day
         (the event trade has expired; the name is held fixed; no fresh surprise), dropped if an earnings session falls
         before the control's expiry. The event minus its own control isolates the surprise; the control's own mean
         shows what the structure earns with no event.
PRIMARY  A and B: event - control, % of debit per trade, t on entry-month cluster means. BAR (4 arms; house |t| >= 3
         governs Sidak-4 2.50): an arm's surprise effect is certified with t >= 3, both halves (split 2018-01) > 0,
         positive in a majority of years. ALSO reported, NOT gating: each arm's absolute net return (month-clustered t,
         halves, per year) and its gross (mid) version -- the book's claim is that the arm is profitable, not only that
         it beats a control.
SECONDARY C and D, the same event - control and absolute; "guaranteed to profit if any drift occurs": share of C trades
         with S_T > S_0 that profit (definitional, reported only to show what the guarantee costs when drift is absent).
EXPLORATORY any-sign surprise (> 0 / < 0); 20% thresholds.
PRIOR    A NULL-to-negative (no drift to lever; debit spreads lose their spread costs). B positive in absolute (the
         skew/variance premium), event - control ~0. C/D ~ the stock drift (~0) plus a small premium.
Local: one Athena query per year for the entry chains, joined to the exact (ticker, date) pairs; no path pull (held to
expiry at intrinsic). Cached to data/cache/pead_options/.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_pead_option_vehicles.py
     (log -> data/studies/logs/pead_option_vehicles.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/pead_options"
LOG = REPO / "data/studies/logs/pead_option_vehicles.log"
START, END, SPLIT = "2010-01-01", "2026-01-31", "2018-01-01"
SLIP, COMM, STK = 0.25, 0.0065, 0.0010
OPTVOL_MIN, PX_MIN, CTRL_GAP = 1000, 10.0, 25


def log(m):
    print(m, file=sys.stderr, flush=True)


def spot():
    import run_dip_survivorship as DS
    d = DS.pull()
    d["trade_date"] = pd.to_datetime(d.trade_date)
    raw = d.pivot_table(index="trade_date", columns="ticker", values="spot").sort_index()
    ov = d.pivot_table(index="trade_date", columns="ticker", values="opt_vol").reindex_like(raw).rolling(50, min_periods=30).mean()
    return raw, ov


def events(raw, ov) -> pd.DataFrame:
    e = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet")
    e["session"] = pd.to_datetime(e.session)
    e = e[(e.session >= START) & (e.session <= END) & e.ticker.isin(raw.columns)].dropna(subset=["surprise_pct"])
    idx = raw.index
    earn = e.groupby("ticker").session.apply(lambda s: np.sort(s.values)).to_dict()
    sp = pd.read_parquet(REPO / "data/cache/pit/splits.parquet"); sp["execution_date"] = pd.to_datetime(sp.execution_date)
    spl = sp.groupby("ticker").execution_date.apply(list).to_dict()
    rows = []
    for r in e.itertuples():
        k = idx.searchsorted(r.session)
        if k >= len(idx):
            continue
        same = idx[k] == r.session
        i = k if (str(r.timing).upper() == "BMO" and same) else (k + 1 if same else k)
        if i + CTRL_GAP + 40 >= len(idx):
            continue
        for kind, j in (("event", i), ("control", i + CTRL_GAP)):
            d = idx[j]
            px, v = raw.at[d, r.ticker], ov.at[d, r.ticker]
            if not (np.isfinite(px) and px >= PX_MIN and np.isfinite(v) and v >= OPTVOL_MIN):
                continue
            rows.append(dict(eid=f"{r.ticker}|{r.session.date()}", ticker=r.ticker, trade_date=d, kind=kind,
                             surprise=r.surprise_pct, s0=px, earn=earn[r.ticker], spl=spl.get(r.ticker, [])))
    return pd.DataFrame(rows)


def pull_chains(E: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y, g in E.groupby(E.trade_date.dt.year):
        f = CACHE / f"chains_{y}.parquet"
        if not f.exists():
            pairs = g[["ticker", "trade_date"]].drop_duplicates()
            parts = []
            for k0 in range(0, len(pairs), 2500):
                ch = pairs.iloc[k0:k0 + 2500]
                vals = ",".join(f"('{t}', DATE '{d.date()}')" for t, d in zip(ch.ticker, ch.trade_date))
                log(f"  chain pull {y} [{k0}:{k0 + len(ch)}] of {len(pairs)} ticker-days")
                parts.append(athena(f"""WITH k(tk, d) AS (VALUES {vals})
                       SELECT o.ticker, o.trade_date, o.expiry, o.strike, o.cp, o.bid, o.ask, o.delta
                       FROM options_daily_v3 o JOIN k ON o.ticker = k.tk AND o.trade_date = k.d
                       WHERE o.trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
                         AND date_diff('day', o.trade_date, o.expiry) BETWEEN 20 AND 45
                         AND o.bid > 0 AND o.ask > 0 AND abs(o.delta) BETWEEN 0.05 AND 0.65"""))
            pd.concat(parts, ignore_index=True).to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"):
        d[c] = pd.to_datetime(d[c])
    d["cp"] = d.cp.str.upper().str[0]
    return d.drop_duplicates(["ticker", "trade_date", "expiry", "strike", "cp"])


def pick(g, cp, target, below=None, above=None):
    g = g[g.cp == cp]
    if below is not None:
        g = g[g.strike < below]
    if above is not None:
        g = g[g.strike > above]
    if g.empty:
        return None
    return g.iloc[(g.delta.abs() - target).abs().argsort()[:1]].iloc[0]


def buy(o):
    return (o.bid + o.ask) / 2 + SLIP * (o.ask - o.bid) + COMM


def sell(o):
    return (o.bid + o.ask) / 2 - SLIP * (o.ask - o.bid) - COMM


def mid(o):
    return (o.bid + o.ask) / 2


def trades(E, C, raw) -> pd.DataFrame:
    G = {k: g for k, g in C.groupby(["ticker", "trade_date"])}
    idx = raw.index
    rows = []
    for r in E.itertuples():
        g = G.get((r.ticker, r.trade_date))
        if g is None:
            continue
        g = g.assign(gap=((g.expiry - g.trade_date).dt.days - 30).abs())
        g = g[g.gap == g.gap.min()]; g = g[g.expiry == g.expiry.min()]
        T = g.expiry.iloc[0]
        if any(r.trade_date < x <= T for x in r.spl):
            continue
        if r.kind == "control" and any(r.trade_date < x <= T for x in r.earn):
            continue
        iT = idx.searchsorted(T, side="right") - 1
        if idx[iT] < T - pd.Timedelta(days=4):
            continue
        sT, s0 = raw[r.ticker].iloc[:iT + 1].ffill().iloc[-1], r.s0
        if not np.isfinite(sT):
            continue
        rec = dict(eid=r.eid, ticker=r.ticker, trade_date=r.trade_date, kind=r.kind, surprise=r.surprise, s0=s0, sT=sT)
        c40 = pick(g, "C", 0.40); c10 = pick(g, "C", 0.10, above=c40.strike) if c40 is not None else None
        if c40 is not None and c10 is not None:
            deb, debm = buy(c40) - sell(c10), mid(c40) - mid(c10)
            pay = max(sT - c40.strike, 0) - max(sT - c10.strike, 0)
            if deb > 0 and debm > 0:
                rec.update(A=100 * (pay / deb - 1), A_g=100 * (pay / debm - 1))
        p50 = pick(g, "P", 0.50); p20 = pick(g, "P", 0.20, below=p50.strike) if p50 is not None else None
        if p50 is not None and p20 is not None:
            deb, debm = buy(p50) - sell(p20), mid(p50) - mid(p20)
            pay = max(p50.strike - sT, 0) - max(p20.strike - sT, 0)
            if deb > 0 and debm > 0:
                rec.update(B=100 * (pay / deb - 1), B_g=100 * (pay / debm - 1))
        c30 = pick(g, "C", 0.30)
        if c30 is not None:
            cost = s0 * (1 + STK) - sell(c30)
            rec.update(C=100 * ((min(sT, c30.strike) - STK * min(sT, c30.strike)) / cost - 1),
                       C_g=100 * (min(sT, c30.strike) / (s0 - mid(c30)) - 1))
        p30 = pick(g, "P", 0.30)
        if p30 is not None:
            rec.update(D=100 * (s0 * (1 - STK) + sell(p30) - max(sT, p30.strike) * (1 + STK)) / s0,
                       D_g=100 * (s0 + mid(p30) - max(sT, p30.strike)) / s0)
        rows.append(rec)
    return pd.DataFrame(rows)


def mclu(x, d):
    g = x.groupby(d.dt.to_period("M")).mean()
    return g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g)), len(g)


def report(T, arm, side, thr, out, primary):
    ev = T[(T.kind == "event") & (T.surprise >= thr if side == "beat" else T.surprise <= -thr)].dropna(subset=[arm])
    ct = T[T.kind == "control"].dropna(subset=[arm]).set_index("eid")[arm]
    P = ev.assign(ctrl=ev.eid.map(ct)).dropna(subset=["ctrl"])
    P["d"] = P[arm] - P.ctrl
    m, t, nm = mclu(P.d, P.trade_date)
    h = P.trade_date < SPLIT
    yr = P.groupby(P.trade_date.dt.year).d.mean()
    a, ta, _ = mclu(ev[arm], ev.trade_date)
    ag, tg, _ = mclu(ev[f"{arm}_g"], ev.trade_date)
    c, tc, _ = mclu(P.ctrl, P.trade_date)
    ha = ev.trade_date < SPLIT
    out.append(f"  {arm} {side:4s} >= {thr:>2}%: n {len(ev):5d} (paired {len(P)}) | ABS net {a:+6.2f}% t {ta:+5.2f} halves {ev[ha][arm].mean():+6.2f}/{ev[~ha][arm].mean():+6.2f} "
               f"| gross {ag:+6.2f}% t {tg:+5.2f} | control {c:+6.2f}% t {tc:+5.2f} | EVENT - CONTROL {m:+6.2f}pp t {t:+5.2f} "
               f"halves {P[h].d.mean():+6.2f}/{P[~h].d.mean():+6.2f} yrs+ {(yr > 0).sum()}/{len(yr)}" + ("  *PRIMARY*" if primary else ""))
    return dict(m=m, t=t, h1=P[h].d.mean(), h2=P[~h].d.mean(), yp=(yr > 0).sum(), ny=len(yr), abs=a, tabs=ta,
                yr_abs=ev.groupby(ev.trade_date.dt.year)[arm].mean())


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    raw, ov = spot()
    E = events(raw, ov)
    log(f"  entries: {len(E):,} ({(E.kind == 'event').sum():,} events)")
    C = pull_chains(E)
    T = trades(E, C, raw)
    out = ["# Sinclair PEAD option vehicles (pre-registration in the docstring)",
           f"trades priced: {len(T):,} ({(T.kind == 'event').sum():,} event, {(T.kind == 'control').sum():,} control), "
           f"{T.ticker.nunique()} names, {T.trade_date.min().date()} -> {T.trade_date.max().date()}",
           "A = 40/10 call spread (beats), B = 50/20 put spread (misses): % of debit. C = covered call (beats): % of net cost. "
           "D = covered put (misses): % of spot.\n"]
    res = {}
    out.append("## PRIMARY / SECONDARY (surprise >= 10%)")
    for arm, side, prim in (("A", "beat", True), ("B", "miss", True), ("C", "beat", False), ("D", "miss", False)):
        res[arm] = report(T, arm, side, 10, out, prim)
    out.append("\n## EXPLORATORY thresholds")
    for thr in (0.001, 20):
        for arm, side in (("A", "beat"), ("B", "miss"), ("C", "beat"), ("D", "miss")):
            report(T, arm, side, thr, out, False)
    evC = T[(T.kind == "event") & (T.surprise >= 10)].dropna(subset=["C"])
    up = evC[evC.sT > evC.s0]
    out.append(f"\n'guaranteed if any drift': covered-call beats with S_T > S_0: {len(up)} of {len(evC)} "
               f"({100 * len(up) / max(len(evC), 1):.0f}%), profitable {100 * (up.C > 0).mean():.0f}%; with S_T <= S_0: "
               f"mean {evC[evC.sT <= evC.s0].C.mean():+.2f}%")
    out.append("\nabsolute net by year (%): \n" + pd.DataFrame({k: v["yr_abs"] for k, v in res.items()}).round(1).T.to_string())
    out.append("\nBAR (event - control, t >= 3, both halves > 0, majority of years):")
    for k in ("A", "B"):
        r = res[k]
        ok = r["t"] >= 3 and r["h1"] > 0 and r["h2"] > 0 and r["yp"] > r["ny"] / 2
        out.append(f"  {k}: {'PASS' if ok else 'NOT MET'} ({r['m']:+.2f}pp t {r['t']:+.2f}); absolute {r['abs']:+.2f}% t {r['tabs']:+.2f}")
    T.drop(columns=[], errors="ignore").to_parquet(REPO / "data/studies/logs/pead_option_vehicles.parquet", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

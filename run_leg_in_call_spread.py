#!/usr/bin/env python3
"""
LEG INTO A CONDOR: bull put spread -> stock rallies, put spread is winning -> SELL a bear call spread above it
(pre-registered 2026-09-25, before any run; Sosnoff, More Tom clip FZfndYs_nXc, "sell a call spread above your put
spread and reduce your basis"; Gabe asked for the test).

WHY NEW. The ledger has the call side only UNCONDITIONALLY: the ETF put-spread exit rule on bear calls / condors FAILED
(+0.36%/trade, t 0.6, 2026-09-16), and single-name short premium dies at costs. The CONDITIONAL entry (sell the call
spread only after a rally, while an open bull put is winning) has never been run. The claim is about timing, so the
control holds everything but the timing fixed.

UNIVERSE  SPY, QQQ, IWM + 10 liquid mega-caps (AAPL MSFT NVDA AMZN META GOOGL TSLA AMD NFLX AVGO).
          2012-01 -> 2026-03 (v3 bid/ask coverage ends ~2026-03). Pulled direct from silver.options_daily_v3 (NOT the
          MySQL cache, which drops zero-bid quotes and breaks exit scans on winners). Friday expiries only. Raw strikes
          are matched to RAW chain-parity spot (silver.chain_spot_daily, unadjusted) for settlement.
BASE      every Friday: bull put spread, short put nearest -0.25 delta, long nearest -0.15, expiry = the Friday with DTE
          closest to 20 (14-28 allowed). 50% take at the real closing cost, else held to expiry (the certified shape,
          no regime gate so there's enough power).
TRIGGER   the first session after entry, while the put spread is still open and DTE >= 5, on which (a) spot > entry spot
          and (b) the put spread shows >= 25% of its credit as profit at the MID (what the trader sees).
TREATED   on the trigger day: SELL a bear call spread on the SAME expiry, short call nearest +0.25 delta, long nearest
          +0.15. 50% take at the real closing cost, else settle at intrinsic on the expiry-date spot.
CONTROL   the same call spread (same ticker, same 0.25/0.15 deltas, same DTE at entry) sold in cycles where the
          trigger did NOT fire, entered on the session with that same DTE -- matched per treated trade on (ticker, DTE),
          controls within +-730 days of the treated entry. Only the timing (after a rally while the put side wins) varies.
FILLS     house cost model: each leg fills at mid -+ 25% of its quoted spread plus $0.0065/share per leg per side;
          legs settling at expiry pay no exit cost. Gross (mid) reported alongside. Return = P&L / max risk
          (width - credit), per trade.
CELLS     PRIMARY: pooled, after-cost return of the TREATED call spread (the decision: is adding it worth money?).
          Month-clustered t >= 3, both halves (2019-01) > 0, majority of years > 0.
          CO-REQUIREMENT for adoption: treated minus matched control >= 0 (the timing mustn't be worse than
          selling the call spread any day).
          Reported cells: {pooled, ETFs, single names} x {treated absolute, treated - control} x {50% take, hold}
          = 12, Sidak(12) |t| >= 2.87; the house 3 governs.
PRIOR     low. The call side has been null everywhere, and stocks that just rose tend to keep going (12-1 momentum
          t 2.93), which works against a fresh short call.

Local vs cloud: 15 chunked Athena pulls (one per year, ~13 tickers), cached to data/cache/leg_in/; then local CPU.
Usage: PYTHONPATH=src:. .venv/bin/python3 run_leg_in_call_spread.py   (log -> data/studies/logs/leg_in_call_spread.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/leg_in_call_spread.log"
CACHE = REPO / "data/cache/leg_in"
ETFS = ["SPY", "QQQ", "IWM"]
NAMES = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD", "NFLX", "AVGO"]
TICKERS = ETFS + NAMES
Y0, Y1, END = 2012, 2026, pd.Timestamp("2026-03-31")
SPLIT = pd.Period("2019-01", "M")
SLIP, COMM = 0.25, 0.0065


def pull_year(y: int) -> pd.DataFrame:
    f = CACHE / f"v3_{y}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    from lib.athena_lib import athena
    CACHE.mkdir(parents=True, exist_ok=True)
    tl = ",".join(f"'{t}'" for t in TICKERS)
    d = athena(f"""
        SELECT ticker, trade_date, expiry, strike, cp, bid, ask, delta
        FROM silver.options_daily_v3
        WHERE ticker IN ({tl}) AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
          AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 35 AND day_of_week(expiry) = 5
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ((cp = 'P' AND (delta IS NULL OR delta BETWEEN -0.60 AND 0.0))
            OR (cp = 'C' AND (delta IS NULL OR delta BETWEEN 0.0 AND 0.60)))""")
    d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
    d = d.drop_duplicates(["ticker", "trade_date", "expiry", "strike", "cp"])
    d.to_parquet(f)
    print(f"  v3 {y}: {len(d):,} rows", flush=True)
    return d


def fill(bid, ask, sell: bool, cost: bool) -> float:
    mid = (bid + ask) / 2
    if not cost:
        return mid
    return mid - SLIP * (ask - bid) - COMM if sell else mid + SLIP * (ask - bid) + COMM


class Chain:
    """Per-ticker quote lookup: (date, expiry, cp) -> frame indexed by strike."""
    def __init__(self, d: pd.DataFrame):
        self.g = {k: v.set_index("strike").sort_index() for k, v in d.groupby(["trade_date", "expiry", "cp"])}
        self.dates = np.array(sorted(d.trade_date.unique()))

    def get(self, day, exp, cp):
        return self.g.get((day, exp, cp))

    def pick(self, day, exp, cp, target):
        q = self.get(day, exp, cp)
        if q is None:
            return None
        q = q[q.delta.notna() & (q.bid > 0)]
        if q.empty:
            return None
        return q.index[np.argmin(np.abs(q.delta.values - target))]

    def quote(self, day, exp, cp, k):
        q = self.get(day, exp, cp)
        if q is None or k not in q.index:
            return None
        r = q.loc[k]
        return float(r.bid), float(r.ask)


def spread_trade(ch: Chain, spot: pd.Series, t0, exp, cp: str, d_short: float, d_long: float, take: bool, cost: bool):
    """Sell a vertical at t0; return (ret on risk, exit_day) or None. cp 'P' = bull put, 'C' = bear call."""
    ks, kl = ch.pick(t0, exp, cp, d_short), ch.pick(t0, exp, cp, d_long)
    if ks is None or kl is None or ks == kl:
        return None
    if (cp == "P" and not kl < ks) or (cp == "C" and not kl > ks):
        return None
    qs, ql = ch.quote(t0, exp, cp, ks), ch.quote(t0, exp, cp, kl)
    credit = fill(*qs, True, cost) - fill(*ql, False, cost)
    width = abs(ks - kl)
    if credit <= 0 or credit >= width:
        return None
    risk = width - credit
    if take:
        for day in ch.dates[(ch.dates > t0) & (ch.dates < exp)]:
            a, b = ch.quote(day, exp, cp, ks), ch.quote(day, exp, cp, kl)
            if a is None or b is None:
                continue
            close = fill(*a, False, cost) - fill(*b, True, cost)      # buy back short, sell long
            if close <= 0.5 * credit:
                return (credit - close) / risk, day
    s = spot.loc[:exp]
    if s.empty or (exp - s.index[-1]).days > 4:
        return None
    S = float(s.iloc[-1])
    intr = (max(ks - S, 0) - max(kl - S, 0)) if cp == "P" else (max(S - ks, 0) - max(S - kl, 0))
    return (credit - intr) / risk, exp


def put_mid_profit(ch, day, exp, ks, kl, credit_mid):
    a, b = ch.quote(day, exp, "P", ks), ch.quote(day, exp, "P", kl)
    if a is None or b is None:
        return None
    return (credit_mid - ((a[0] + a[1]) / 2 - (b[0] + b[1]) / 2)) / credit_mid


def run_ticker(tk: str, d: pd.DataFrame, spot: pd.Series) -> tuple[list, list]:
    ch = Chain(d)
    exps = np.array(sorted(d.expiry.unique()))
    fridays = [x for x in ch.dates if pd.Timestamp(x).dayofweek == 4]
    treated, cycles = [], []
    for f in fridays:
        f = pd.Timestamp(f)
        dte = np.array([(pd.Timestamp(e) - f).days for e in exps])
        ok = np.flatnonzero((dte >= 14) & (dte <= 28))
        if not len(ok) or f not in spot.index:
            continue
        exp = pd.Timestamp(exps[ok[np.argmin(np.abs(dte[ok] - 20))]])
        ks, kl = ch.pick(f, exp, "P", -0.25), ch.pick(f, exp, "P", -0.15)
        if ks is None or kl is None or not kl < ks:
            continue
        qs, ql = ch.quote(f, exp, "P", ks), ch.quote(f, exp, "P", kl)
        cm = (qs[0] + qs[1]) / 2 - (ql[0] + ql[1]) / 2
        base = spread_trade(ch, spot, f, exp, "P", -0.25, -0.15, True, True)
        if base is None or cm <= 0:
            continue
        put_close = base[1]
        s0 = float(spot.loc[f])
        trig = None
        for day in ch.dates[(ch.dates > f) & (ch.dates < exp)]:
            day = pd.Timestamp(day)
            if day >= put_close or (exp - day).days < 5:
                break
            if day not in spot.index or spot.loc[day] <= s0:
                continue
            p = put_mid_profit(ch, day, exp, ks, kl, cm)
            if p is not None and p >= 0.25:
                trig = day; break
        cycles.append(dict(ticker=tk, entry=f, expiry=exp, trig=trig))
        if trig is not None:
            row = dict(ticker=tk, entry=trig, expiry=exp, dte=(exp - trig).days, put_ret=base[0])
            for take in (True, False):
                for cost in (True, False):
                    r = spread_trade(ch, spot, trig, exp, "C", 0.25, 0.15, take, cost)
                    row[f"r_{'take' if take else 'hold'}_{'net' if cost else 'gross'}"] = r[0] if r else np.nan
            treated.append(row)
    # controls: untriggered cycles, the call spread sold at each DTE a treated trade used
    need = {r["dte"] for r in treated}
    dset = set(pd.to_datetime(ch.dates))
    controls = []
    for c in cycles:
        if c["trig"] is not None:
            continue
        for k in need:
            day = c["expiry"] - pd.Timedelta(days=k)
            if day <= c["entry"] or day not in dset:
                continue
            row = dict(ticker=tk, entry=day, expiry=c["expiry"], dte=k)
            for take in (True, False):
                for cost in (True, False):
                    r = spread_trade(ch, spot, day, c["expiry"], "C", 0.25, 0.15, take, cost)
                    row[f"r_{'take' if take else 'hold'}_{'net' if cost else 'gross'}"] = r[0] if r else np.nan
            controls.append(row)
    return treated, controls


def clustered_t(x: pd.Series, months: pd.Series) -> float:
    m = x.groupby(months).mean().dropna()
    return float(m.mean() / m.std(ddof=1) * np.sqrt(len(m))) if len(m) > 2 else np.nan


def main():
    out = ["# Leg into a condor: sell a call spread after the bull put is winning (pre-registration in the docstring)"]
    import run_dip_survivorship as DS
    cs = DS.pull()
    cs = cs[cs.ticker.isin(TICKERS)].copy(); cs["trade_date"] = pd.to_datetime(cs.trade_date)
    V3 = pd.concat([pull_year(y) for y in range(Y0, Y1 + 1)])
    V3 = V3[V3.trade_date <= END]
    TR, CO = [], []
    for tk in TICKERS:
        spot = cs[cs.ticker == tk].set_index("trade_date").spot.sort_index()
        t, c = run_ticker(tk, V3[V3.ticker == tk], spot)
        TR += t; CO += c
        out.append(f"  {tk}: treated {len(t)}, control trades {len(c)}")
    T, C = pd.DataFrame(TR), pd.DataFrame(CO)
    T.to_csv(REPO / "data/studies/logs/leg_in_call_spread_treated.csv", index=False)
    cols = ["r_take_net", "r_take_gross", "r_hold_net", "r_hold_gross"]
    # matched control mean per treated trade: same ticker & DTE, within +-730 days
    for col in cols:
        mc = []
        for r in T.itertuples():
            m = C[(C.ticker == r.ticker) & (C.dte == r.dte) & ((C.entry - r.entry).abs() <= pd.Timedelta(days=730))][col]
            mc.append(m.mean() if m.notna().sum() >= 3 else np.nan)
        T[f"ctl_{col}"] = mc
    T["month"] = T.entry.dt.to_period("M")
    R = []
    for grp, G in (("pooled", T), ("ETFs", T[T.ticker.isin(ETFS)]), ("names", T[T.ticker.isin(NAMES)])):
        for exit_ in ("take", "hold"):
            for kind in ("abs", "diff"):
                x = G[f"r_{exit_}_net"] * 100
                if kind == "diff":
                    x = x - G[f"ctl_r_{exit_}_net"] * 100
                x = x.dropna(); mo = G.loc[x.index, "month"]
                h = mo < SPLIT; yr = x.groupby(G.loc[x.index, "entry"].dt.year).mean()
                t = clustered_t(x, mo)
                ok = abs(t) >= 3 and np.sign(x[h].mean()) == np.sign(x[~h].mean()) and (np.sign(yr) == np.sign(x.mean())).sum() > len(yr) / 2
                prim = grp == "pooled" and exit_ == "take" and kind == "abs"
                gross = G[f"r_{exit_}_gross"].mean() * 100 if kind == "abs" else np.nan
                R.append(dict(group=grp, exit=exit_, measure=kind, n=len(x), mean=x.mean(), gross=gross, t=t,
                              h1=x[h].mean(), h2=x[~h].mean(), yrs=f"{(np.sign(yr) == np.sign(x.mean())).sum()}/{len(yr)}",
                              win=(x > 0).mean() if kind == "abs" else np.nan, PASS=ok, primary=prim))
    D = pd.DataFrame(R)
    out.append(f"\nTreated call spreads: {len(T)} (trigger fired in {len(T)} of the base cycles); median DTE {T.dte.median():.0f}; "
               f"control trades {len(C)}")
    ctl_all = C.r_take_net.mean() * 100
    out.append(f"Unconditional control call spread (all DTEs, take, net): {ctl_all:+.2f}%/trade on risk, n {C.r_take_net.notna().sum()}")
    out.append("\n" + D.round(2).to_string(index=False))
    p = D[D.primary].iloc[0]
    dd = D[(D.group == "pooled") & (D.exit == "take") & (D.measure == "diff")].iloc[0]
    out.append(f"\nVERDICT (PRIMARY pooled/take/abs): {p['mean']:+.2f}%/trade on risk after costs (gross {p.gross:+.2f}), "
               f"t {p.t:+.2f}, halves {p.h1:+.2f}/{p.h2:+.2f}, yrs {p.yrs} -> {'PASS' if p.PASS else 'fail'}; "
               f"timing vs matched control {dd['mean']:+.2f}pp t {dd.t:+.2f} -> "
               + ("ADOPT" if p.PASS and dd["mean"] >= 0 else "do not adopt"))
    D.to_csv(REPO / "data/studies/leg_in_call_spread_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

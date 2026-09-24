#!/usr/bin/env python3
"""
Put credit spread vs the HOUSE stock trade on the same precision-tier breakout, at equal risk, each vehicle under
its own management (2026-09-24, Gabe: "put spread vs hold stock is apples and oranges -- our stock strategy gets
stopped out quite often whereas with put spreads we hold to expiration").

PRE-REGISTRATION (written before any option data was pulled)
------------------------------------------------------------
Why this is new (TEST_INDEX checked 2026-09-24):
  * `csp_vs_stopped_stock_2026-09-23` compared a naked 0.30-delta put with delta-matched stock under a GENERIC 0.5-ADR
    stop on BCI-cache entries (NULL, +0.235%/trade t 0.84). Not a spread, not the house signal, not the house exit.
  * `vehicle_benchmark_2026-09-22` / `cw_play` compared the spread with stock held unstopped at the spread's delta.
  * `august_2026_vehicle_study` repriced Gabe's own fills (inadmissible for selection) with BS marks.
  Nothing has put the in-book breakout signal through a spread vs through the house stock process.

Signal: the precision-tier house breakout (`run_precision_tier_control.build()`), liquid panel, 2019-10 -> entries
whose option expiry is <= 2026-03-20 (v3 bid/ask coverage ends ~Mar 2026).

ARM S (stock, the house process, `run_qullamaggie_exit.simulate(..., "BASE")`): buy the breakout close +10 bps, stop =
  breakout-day low judged on the CLOSE, exit on the first close under the 20 EMA, cap 60 sessions, risk floor 2%,
  -10 bps out. Unit = R (return per $ of planned risk).
ARM P (put spread, the live scan's legs): on the same breakout close sell the ~0.30-delta put and buy the ~0.15-delta
  put at the expiry nearest 30 DTE (21-45), HOLD TO EXPIRY (the house rule for spreads), settle at intrinsic vs the
  raw spot recovered from the chain. House fills: 25% of each leg's quoted bid-ask + $0.0065/share/leg; no exit cost
  at expiry. Unit = ROC on max loss (return per $ of max risk) -- the same unit as R: a dollar of risk budget.
  Tradeability gate (the live scan's): both legs quoted, short-leg bid-ask <= 25% of mid, credit > 0.
  Signals with no tradeable spread are excluded from BOTH arms (paired); the excluded share is reported.

PRIMARY (one cell): mean(ROC_P - R_S) per signal, t clustered by entry date. Bar |t| >= 3, both chronological halves
  the same sign, per-year shown. Prior: NULL (the short put tied the stopped stock; the spread tracks its own delta;
  the long wing adds a leg of friction) -- but the precision tier is the one signal here with measured selection edge.
SECONDARY (exploratory, Sidak-charged for 3 cells -> |t| >= ~2.7):
  P2  a more directional spread (~0.45 / ~0.30 delta), same rules      vs S
  CTL the 0.30/0.15 spread on a random NON-signal session of the same name and month (does the signal help the
      spread at all? -- the spread's own selection control)         P - CTL
DESCRIPTIVE: gross (mid) vs net, win rate, days held, worst trade, per-year, and return per CAPITAL-day (stock sized to
  the risk unit needs entry/risk dollars of capital; the spread needs its max loss) -- the ROC framing from earlier.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_breakout_putspread_vs_stock.py
       (log -> data/studies/logs/breakout_putspread_vs_stock.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.chain_spot import implied_spot
from run_precision_tier_control import build
from run_qullamaggie_exit import simulate, FLOOR

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/breakout_putspread_vs_stock.log"
CACHE = REPO / "data/cache/breakout_putspread_v3"
OUT = REPO / "data/studies/logs/breakout_putspread_vs_stock_trades.parquet"
START, LAST_EXPIRY = pd.Timestamp("2019-10-01"), pd.Timestamp("2026-03-20")
LAST_ENTRY = pd.Timestamp("2026-02-13")
COMM, SLIP = 0.0065, 0.25
DTE_LO, DTE_HI, DTE_T = 21, 45, 30
STRUCTS = {"P": (-0.30, -0.15), "P2": (-0.45, -0.30)}
RNG = np.random.default_rng(20260924)

SQL = """
SELECT ticker, trade_date, expiry, strike,
       CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask, CAST(delta AS DOUBLE) AS delta,
       (CAST(bid_iv AS DOUBLE) + CAST(ask_iv AS DOUBLE)) / 2 AS iv
FROM silver.options_daily_v3
WHERE ticker IN ({tickers})
  AND trade_date BETWEEN DATE '{a}' AND DATE '{b}'
  AND upper(substr(cp, 1, 1)) = 'P'
  AND date_diff('day', trade_date, expiry) BETWEEN {dlo} AND {dhi}
  AND delta BETWEEN -0.80 AND -0.05
  AND concat(ticker, '|', cast(trade_date AS varchar)) IN ({keys})
"""


def pull(name: str, pairs: pd.DataFrame, dlo: int, dhi: int) -> pd.DataFrame:
    """Rows for exact (ticker, trade_date) pairs, one Athena query per year; cached."""
    f = CACHE / f"{name}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    from lib.athena_lib import athena
    frames = []
    for y, g in pairs.groupby(pairs.trade_date.dt.year):
        tickers = ",".join(f"'{t}'" for t in sorted(g.ticker.unique()))
        keys = ",".join(f"'{t}|{d.date()}'" for t, d in zip(g.ticker, g.trade_date))
        df = athena(SQL.format(tickers=tickers, keys=keys, a=g.trade_date.min().date(), b=g.trade_date.max().date(),
                               dlo=dlo, dhi=dhi))
        print(f"  [{name} {y}] {len(g):,} name-days -> {len(df):,} rows", flush=True)
        frames.append(df)
    q = pd.concat(frames, ignore_index=True)
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    q["_ba"] = q.ask - q.bid
    q = (q.sort_values("_ba", ascending=False).drop_duplicates(["ticker", "trade_date", "expiry", "strike"])
          .drop(columns="_ba").reset_index(drop=True))
    CACHE.mkdir(parents=True, exist_ok=True)
    q.to_parquet(f, index=False)
    return q


def chain_spot(q: pd.DataFrame) -> pd.Series:
    dte = (q.expiry - q.trade_date).dt.days
    m = q.delta.between(-0.75, -0.25) & q.iv.between(0.02, 4.0) & dte.between(5, 60)
    s = implied_spot(q.strike[m], q.delta[m], q.iv[m], dte[m], np.array(["P"] * int(m.sum())))
    return pd.Series(s, index=q.index[m]).groupby([q.ticker[m], q.trade_date[m]]).median()


def pick(q: pd.DataFrame, sd: float, ld: float) -> pd.DataFrame:
    """One spread per (ticker, trade_date): expiry nearest 30 DTE, legs nearest the target deltas."""
    q = q.assign(dte=(q.expiry - q.trade_date).dt.days)
    q = q[(q.bid > 0) & (q.ask >= q.bid) & q.dte.between(DTE_LO, DTE_HI) & (q.expiry <= LAST_EXPIRY)]
    out = []
    for (t, d), g in q.groupby(["ticker", "trade_date"]):
        g = g[g.dte == g.dte.iloc[(g.dte - DTE_T).abs().argmin()]]
        s = g.iloc[(g.delta - sd).abs().argmin()]
        lg = g[g.strike < s.strike]
        if lg.empty or abs(s.delta - sd) > 0.10:
            continue
        l = lg.iloc[(lg.delta - ld).abs().argmin()]
        out.append((t, d, s.expiry, s.strike, l.strike, s.bid, s.ask, l.bid, l.ask))
    e = pd.DataFrame(out, columns=["ticker", "trade_date", "expiry", "ks", "kl", "sb", "sa", "lb", "la"])
    e["width"] = e.ks - e.kl
    e["credit_mid"] = (e.sb + e.sa) / 2 - (e.lb + e.la) / 2
    e["credit"] = ((e.sb + e.sa) / 2 - SLIP * (e.sa - e.sb)) - ((e.lb + e.la) / 2 + SLIP * (e.la - e.lb)) - 2 * COMM
    e["tradeable"] = ((e.sa - e.sb) <= 0.25 * (e.sb + e.sa) / 2) & (e.credit > 0) & (e.width > e.credit)
    return e


def settle(e: pd.DataFrame, spot_exp: pd.Series) -> pd.DataFrame:
    S = np.array([spot_exp.get((t, x), np.nan) for t, x in zip(e.ticker, e.expiry)])
    pay = np.maximum(e.ks - S, 0) - np.maximum(e.kl - S, 0)
    e = e.assign(S_T=S)
    e["roc"] = (e.credit - pay) / (e.width - e.credit)
    e["roc_gross"] = (e.credit_mid - pay) / (e.width - e.credit_mid)
    e["days"] = (e.expiry - e.trade_date).dt.days
    return e


def dtstat(x: pd.Series, d: pd.Series) -> tuple[float, float]:
    g = x.groupby(d).mean()
    return g.mean(), (g.mean() / g.std(ddof=1) * np.sqrt(len(g)) if len(g) > 2 else np.nan)


def main() -> None:
    P, brk, prec = build()
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    S10 = P.close.rolling(10).mean().values; S20 = P.close.rolling(20).mean().values
    idx = P.close.index

    # ── ARM S on every precision signal ──────────────────────────────────────
    m = prec[(prec.index >= START) & (prec.index <= LAST_ENTRY)]
    rows = []
    for i, j in zip(*np.where(m.values)):
        i += prec.index.get_loc(m.index[0])
        entry = C[i, j] * 1.001
        risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C):
            continue
        r, pct, _ = simulate(C, E20, S10, S20, ADR, L, i, j, "BASE")
        # holding period of the stock arm: re-walk the BASE exit to get the exit session
        k = i
        for k in range(i + 1, min(i + 60, len(C) - 1) + 1):
            c = C[k, j]
            if np.isfinite(c) and (c < L[i, j] or (np.isfinite(E20[k, j]) and c < E20[k, j])):
                break
        rows.append(dict(ticker=P.close.columns[j], trade_date=idx[i], R=r, pct=pct, risk_pct=100 * risk / entry,
                         s_days=(idx[k] - idx[i]).days))
    S = pd.DataFrame(rows)
    print(f"precision signals with a valid stock trade: {len(S):,} ({S.ticker.nunique()} names), "
          f"{S.trade_date.min().date()} -> {S.trade_date.max().date()}", flush=True)

    # control sessions: a random NON-signal session, same name, same month
    sig = set(zip(S.ticker, S.trade_date))
    ctl = []
    for r in S.itertuples(index=False):
        month = idx[(idx.year == r.trade_date.year) & (idx.month == r.trade_date.month) & (idx <= LAST_ENTRY)]
        cand = [d for d in month if (r.ticker, d) not in sig]
        if cand:
            ctl.append((r.ticker, pd.Timestamp(RNG.choice(cand)), r.trade_date))
    CT = pd.DataFrame(ctl, columns=["ticker", "trade_date", "signal_date"])

    # ── option pulls: entry name-days, then expiry name-days for settlement ─
    ent_pairs = pd.concat([S[["ticker", "trade_date"]], CT[["ticker", "trade_date"]]]).drop_duplicates()
    q = pull("entry", ent_pairs, DTE_LO, DTE_HI + 5)
    picks = {k: pick(q, *v) for k, v in STRUCTS.items()}
    exps = pd.concat([p[["ticker", "expiry"]] for p in picks.values()]).drop_duplicates()
    # the expiry session and the 3 before it (holiday Thursdays), for the chain spot
    sp_pairs = pd.concat([exps.assign(trade_date=exps.expiry - pd.Timedelta(days=k)) for k in range(0, 4)])
    sp_pairs = sp_pairs[sp_pairs.trade_date.dt.weekday < 5][["ticker", "trade_date"]].drop_duplicates()
    qe = pull("expiry", sp_pairs, 1, 70)
    spot = chain_spot(qe)
    last = spot.rename("S").reset_index().sort_values("trade_date")
    by_t = {t: g for t, g in last.groupby("ticker")}
    spot_exp = {}
    for (t, x) in zip(exps.ticker, exps.expiry):
        z = by_t.get(t)
        if z is None:
            continue
        z = z[(z.trade_date <= x) & (z.trade_date >= x - pd.Timedelta(days=4))]
        if len(z):
            spot_exp[(t, x)] = float(z.S.iloc[-1])
    for k in picks:
        picks[k] = settle(picks[k], pd.Series(spot_exp))

    # split guard: drop trades whose entry chain spot and expiry spot differ by > 45% (a split inside the trade)
    sp0 = chain_spot(q)
    for k in picks:
        e = picks[k]
        s0 = np.array([sp0.get((t, d), np.nan) for t, d in zip(e.ticker, e.trade_date)])
        bad = ~np.isfinite(s0) | (np.abs(e.S_T / s0 - 1) > 0.45)
        picks[k] = e[~bad & e.S_T.notna()]

    # ── assemble paired frames ───────────────────────────────────────────────
    def join(k, frame):
        p = picks[k][picks[k].tradeable]
        return frame.merge(p[["ticker", "trade_date", "roc", "roc_gross", "days", "credit", "width"]],
                           on=["ticker", "trade_date"], how="inner")
    J = join("P", S)
    J2 = join("P2", S)
    PC = picks["P"][picks["P"].tradeable].merge(CT, on=["ticker", "trade_date"])
    PC = PC.merge(J[["ticker", "trade_date", "roc"]].rename(columns={"trade_date": "signal_date", "roc": "roc_sig"}),
                  on=["ticker", "signal_date"])
    J.to_parquet(OUT, index=False)

    L_ = []
    pr = lambda s: L_.append(s)
    pr(f"# Put spread vs the house stock trade on precision-tier breakouts (pre-registration in the docstring)\n")
    pr(f"signals with a stock trade {len(S):,}; with a tradeable 0.30/0.15 spread {len(J):,} "
       f"({100 * len(J) / len(S):.0f}%), {J.ticker.nunique()} names, {J.trade_date.nunique()} dates")
    sub = S.merge(J[["ticker", "trade_date"]], on=["ticker", "trade_date"], how="left", indicator=True)
    pr(f"stock R on the excluded (no tradeable spread) signals: {sub[sub._merge == 'left_only'].R.mean():+.3f} "
       f"vs included {sub[sub._merge == 'both'].R.mean():+.3f}  (is the spread subset a different population?)\n")

    pr(f"{'arm':34s} {'n':>6s} {'mean':>8s} {'t':>6s} {'median':>8s} {'win%':>6s} {'days':>6s} {'worst':>8s}")
    for lab, x, d, days in [("S  stock, house process (R)", J.R, J.trade_date, J.s_days),
                            ("P  0.30/0.15 spread, net (ROC)", J.roc, J.trade_date, J.days),
                            ("P  0.30/0.15 spread, GROSS mid", J.roc_gross, J.trade_date, J.days),
                            ("P2 0.45/0.30 spread, net (ROC)", J2.roc, J2.trade_date, J2.days),
                            ("CTL 0.30/0.15, random same-name-month", PC.roc, PC.signal_date, PC.days)]:
        mu, t = dtstat(x, d)
        pr(f"{lab:34s} {len(x):>6,} {mu:>+8.3f} {t:>6.2f} {x.median():>+8.3f} {100 * (x > 0).mean():>6.1f} "
           f"{days.mean():>6.1f} {x.min():>+8.2f}")

    # PRIMARY
    J["d"] = J.roc - J.R
    mu, t = dtstat(J.d, J.trade_date)
    cut = J.trade_date.sort_values().iloc[len(J) // 2]
    h1 = dtstat(J.d[J.trade_date < cut], J.trade_date[J.trade_date < cut])
    h2 = dtstat(J.d[J.trade_date >= cut], J.trade_date[J.trade_date >= cut])
    pr(f"\n## PRIMARY: ROC(P) - R(S), paired per signal, per $ of risk")
    pr(f"  diff {mu:+.3f}  t {t:+.2f}  (n {len(J):,}, {J.trade_date.nunique()} dates)   halves {h1[0]:+.3f} "
       f"(t {h1[1]:+.2f}) / {h2[0]:+.3f} (t {h2[1]:+.2f})  split {cut.date()}")
    yr = J.groupby(J.trade_date.dt.year).agg(n=("d", "size"), S=("R", "mean"), P=("roc", "mean"), d=("d", "mean"))
    pr("  per year:\n" + yr.round(3).to_string())
    ok = abs(t) >= 3 and np.sign(h1[0]) == np.sign(h2[0])
    pr(f"  bar |t| >= 3 and halves same sign: {'PASS' if ok else 'FAIL'}"
       + (f" -> {'SPREAD' if mu > 0 else 'STOCK'} better" if ok else ""))

    pr("\n## SECONDARY (Sidak |t| >= ~2.7 for 3 cells)")
    J2["d"] = J2.roc - J2.R
    mu2, t2 = dtstat(J2.d, J2.trade_date)
    pr(f"  P2 - S : {mu2:+.3f}  t {t2:+.2f}  (n {len(J2):,})")
    PC["d"] = PC.roc_sig - PC.roc
    mu3, t3 = dtstat(PC.d, PC.signal_date)
    pr(f"  P - CTL: {mu3:+.3f}  t {t3:+.2f}  (n {len(PC):,})  -- does the breakout signal help the spread?")

    # tails and stop behaviour
    pr("\n## shape")
    for lab, x in [("S", J.R), ("P", J.roc)]:
        pr(f"  {lab}: p5 {x.quantile(.05):+.2f}  p25 {x.quantile(.25):+.2f}  p75 {x.quantile(.75):+.2f}  "
           f"p95 {x.quantile(.95):+.2f}  share <= -0.9 {100 * (x <= -0.9).mean():.1f}%")
    pr(f"  stock exits within 5 sessions: {100 * (J.s_days <= 7).mean():.0f}%  (the 'stopped out often' point)")
    for lab, msk in [("stock R <= -0.5 (stopped/lost)", J.R <= -0.5), ("stock R > -0.5", J.R > -0.5)]:
        z = J[msk]
        pr(f"  when {lab:30s} n {len(z):>5,}  S {z.R.mean():+.3f}  P {z.roc.mean():+.3f}")

    # capital-time (descriptive)
    J["s_cap"] = 1 / (J.risk_pct / 100)           # $ capital per $ of risk for the stock
    s_cd = (J.R / J.s_cap).sum() / (J.s_days.clip(lower=1)).sum() * 365
    p_cd = J.roc.sum() / J.days.sum() * 365
    pr(f"\n## capital-time (descriptive): per $ of CAPITAL per year while deployed")
    pr(f"  stock {100 * s_cd:+.1f}%/yr (median capital {J.s_cap.median():.0f}x the risk unit)   "
       f"spread {100 * p_cd:+.1f}%/yr (capital = max loss)")
    print("\n".join(L_))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())

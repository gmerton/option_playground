#!/usr/bin/env python3
"""
ETF bull put spreads: take-profit vs hold, and Friday-only vs any-day entry, on RETURN PER CAPITAL-DAY
(2026-09-24, Gabe: "should we optimise for return on capital rather than dollar return?" and "why do we limit
entries to Thursday and Friday?").

PRE-REGISTRATION (written before any v3 path was pulled)
---------------------------------------------------------
Why this is new (TEST_INDEX checked 2026-09-24):
  * `etf_put_spread_exit_rule_2026-09-16.md` compared a 50% take against a hold arm from a DIFFERENT structure
    (30 DTE 0.30/0.15 vs 45 DTE 0.35/0.25) on `options_cache`, which drops every zero-bid quote except at expiry --
    exactly the long-leg quote a winning spread shows near the take. Not a paired test, and biased toward hold.
  * `ann_target` (annualised-ROC exit) was only run in the TMF/TLT/ASHR playbooks, at mid, pre-cost; retired.
  * No put-spread study ever varied the entry weekday (engine default `entry_weekday=4`). The only weekday test
    (7-DTE straddle) confounded weekday with tenor; at 45 DTE it does not.
  * No study measured capital-TIME: what matters for "high annualised ROC" is whether freed capital is redeployed.

Universe: the 20-ETF in-book roster (`run_etf_putspread_roster.py`), puts from `silver.options_daily_v3`
(unfiltered: zero bids kept), trade dates 2018-01-02 -> 2026-03-31, entries with expiry <= 2026-03-20 (bid/ask
coverage ends ~Mar 2026).

Structure (roster spec): expiry nearest 45 DTE within 40-50; short put nearest -0.35 delta, long put nearest -0.25
delta at a lower strike. Filters as the roster: credit/width <= 0.50, capital >= 0.10/share, both legs quoted
(bid > 0, ask >= bid) at entry.

Fills (house cost model, `lib.studies.costs`): every traded leg pays 25% of ITS OWN QUOTED bid-ask that day plus
$0.0065/share. Entry credit C = (mid_s - .25 BA_s) - (mid_l + .25 BA_l) - 2 x .0065. Close debit on day d
X_d = (mid_s + .25 BA_s) - (mid_l - .25 BA_l) + 2 x .0065 (the exit-day spread, not the entry proxy). Held
spreads settle at intrinsic vs the RAW spot recovered from the chain (`chain_spot`), no exit cost.
Capital = width - C. ROC = P&L / capital. Gross (mid, no costs) reported alongside.

Exit arms (every entry is run through every arm -> paired):
  HOLD    to expiry
  T50     close at EOD the first day X_d <= 0.50 C      (the roster's live rule)
  T25/T75 same at 25% / 75% of credit captured
  FAST50  T50 only if hit within 5 trading days, else hold  (Gabe's "50% after one day" case)
  ANN100  close when (C - X_d)/capital x 365/days >= 1.0  (the annualised-ROC exit he proposed)
EOD marks only: a resting GTC limit would fill some takes intraday that EOD misses -> take arms are, if anything,
understated. Days with a missing/crossed leg are skipped (cannot trigger); coverage reported per arm.

PRIMARY (one cell, stated in advance): Friday entries, per-entry ROC(T50) - ROC(HOLD), after costs,
  month-clustered t. Bar: |t| >= 3, both chronological halves same sign, per-year shown.
SECONDARY, the capital-time question (exploratory, Sidak-charged): one slot per ticker, always re-deployed at
  the next eligible entry day after an exit (next session, never same-day). Policies = {Fri-only, any-day} x
  {HOLD, T50, T25, T75, FAST50, ANN100} = 12 cells, 11 compared with the incumbent (Fri, T50) -> Sidak per-cell
  alpha 0.0027/11 -> |t| >= ~3.6. Metric: slot return per year = sum of trade ROCs / years (every trade uses the
  full slot), idle share, worst month; inference on the equal-weight monthly slot series, paired by month.
TERTIARY (descriptive): entry weekday Mon..Fri paired within ticker-week, HOLD and T50.

Cost: ~180 Athena chunks (ticker-year), cached per ticker under data/cache/etf_puts_v3/; compute is local.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_putspread_exit_capital_time.py [--pull-only]
      > data/studies/logs/putspread_exit_capital_time.log 2>&1
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/etf_puts_v3"
OUT_TRADES = REPO / "data/studies/logs/putspread_exit_capital_time_trades.parquet"

ROSTER = ["ASHR", "EEM", "FXI", "GDX", "GLD", "INDA", "IWM", "QQQ", "SOXX", "SPY",
          "TLT", "USO", "XBI", "XLE", "XLF", "XLK", "XLP", "XLU", "XLV", "XOP"]
SHORT_D, LONG_D = -0.35, -0.25
DTE_LO, DTE_HI, DTE_T = 40, 50, 45
LAST_EXPIRY = pd.Timestamp("2026-03-20")
COMM, SLIP = 0.0065, 0.25
ARMS = ["HOLD", "T25", "T50", "T75", "FAST50", "ANN100"]

SQL = """
SELECT trade_date, expiry, strike,
       CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
       CAST(delta AS DOUBLE) AS delta, (CAST(bid_iv AS DOUBLE) + CAST(ask_iv AS DOUBLE)) / 2 AS iv
FROM silver.options_daily_v3
WHERE ticker = '{t}'
  AND trade_date BETWEEN DATE '{a}' AND DATE '{b}'
  AND upper(substr(cp, 1, 1)) = 'P'
  AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 55
  AND (delta IS NULL OR delta >= -0.85)
"""


# ── data ──────────────────────────────────────────────────────────────────────
def pull(t: str) -> pd.DataFrame:
    f = CACHE / f"{t}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    from lib.athena_lib import athena
    frames = []
    for y in range(2018, 2027):
        a, b = f"{y}-01-01", (f"{y}-12-31" if y < 2026 else "2026-03-31")
        df = athena(SQL.format(t=t, a=a, b=b))
        print(f"  [{t} {y}] {len(df):,} rows", flush=True)
        frames.append(df)
    q = pd.concat(frames, ignore_index=True)
    q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
    # cheap insurance (v3 is verified unique since 2026-09-23): keep the widest-spread row per contract-day
    q["_ba"] = q.ask - q.bid
    q = (q.sort_values("_ba", ascending=False)
          .drop_duplicates(["trade_date", "expiry", "strike"]).drop(columns="_ba")
          .sort_values(["trade_date", "expiry", "strike"]).reset_index(drop=True))
    CACHE.mkdir(parents=True, exist_ok=True)
    q.to_parquet(f, index=False)
    return q


def raw_spot(q: pd.DataFrame) -> pd.Series:
    """Median chain-implied spot per trade_date from liquid mid-delta legs (strikes are RAW)."""
    from lib.studies.chain_spot import implied_spot
    dte = (q.expiry - q.trade_date).dt.days
    m = q.delta.between(-0.75, -0.25) & q.iv.between(0.02, 3.0) & dte.between(7, 55)
    s = implied_spot(q.strike[m], q.delta[m], q.iv[m], dte[m], np.array(["P"] * int(m.sum())))
    return pd.Series(s, index=q.index[m]).groupby(q.trade_date[m]).median()


# ── trades ────────────────────────────────────────────────────────────────────
def build_entries(t: str, q: pd.DataFrame) -> pd.DataFrame:
    q = q.assign(dte=(q.expiry - q.trade_date).dt.days)
    ok = (q.bid > 0) & (q.ask >= q.bid) & q.delta.notna()
    c = q[ok & q.dte.between(DTE_LO, DTE_HI) & (q.expiry <= LAST_EXPIRY)]
    # expiry nearest 45 DTE per entry day
    ex = c.groupby("trade_date").dte.apply(lambda s: s.iloc[(s - DTE_T).abs().argmin()])
    c = c[c.dte == c.trade_date.map(ex)]
    out = []
    for d, g in c.groupby("trade_date"):
        s = g.iloc[(g.delta - SHORT_D).abs().argmin()]
        lg = g[g.strike < s.strike]
        if lg.empty:
            continue
        l = lg.iloc[(lg.delta - LONG_D).abs().argmin()]
        out.append((d, s.expiry, s.strike, l.strike, s.bid, s.ask, l.bid, l.ask, s.delta, l.delta))
    e = pd.DataFrame(out, columns=["entry_date", "expiry", "ks", "kl", "sb", "sa", "lb", "la", "sd", "ld"])
    if e.empty:
        return e
    e.insert(0, "ticker", t)
    e["width"] = e.ks - e.kl
    e["credit_mid"] = (e.sb + e.sa) / 2 - (e.lb + e.la) / 2
    e["credit"] = ((e.sb + e.sa) / 2 - SLIP * (e.sa - e.sb)) - ((e.lb + e.la) / 2 + SLIP * (e.la - e.lb)) - 2 * COMM
    e["capital"] = e.width - e.credit
    e["capital_mid"] = e.width - e.credit_mid
    keep = (e.credit_mid / e.width <= 0.50) & (e.capital >= 0.10) & (e.credit > 0)
    return e[keep].reset_index(drop=True)


def run_arms(e: pd.DataFrame, q: pd.DataFrame, spot: pd.Series) -> pd.DataFrame:
    """Every entry through every exit arm, on the daily path of both legs."""
    sessions = pd.DatetimeIndex(sorted(q.trade_date.unique()))
    key = q.set_index(["trade_date", "expiry", "strike"])[["bid", "ask"]]
    # split guard: a raw-strike contract does not survive a split under the same key, so drop any trade
    # whose life spans a day-over-day chain-spot jump outside [0.7, 1.4] (SOXX 3:1, USO 1:8, XLU 2:1 ...)
    jr = spot / spot.shift(1)
    jumps = jr.index[(jr > 1.4) | (jr < 0.7)]
    if len(jumps):
        span = np.zeros(len(e), dtype=bool)
        for j in jumps:
            span |= (e.entry_date < j).to_numpy() & (e.expiry >= j).to_numpy()
        print(f"    split guard: {len(jumps)} jump day(s) {[str(j.date()) for j in jumps]}, "
              f"dropped {int(span.sum())} entries", flush=True)
        e = e[~span]
    rows = []
    for r in e.itertuples(index=False):
        days = sessions[(sessions > r.entry_date) & (sessions < r.expiry)]
        idx_s = pd.MultiIndex.from_arrays([days, [r.expiry] * len(days), [r.ks] * len(days)])
        idx_l = pd.MultiIndex.from_arrays([days, [r.expiry] * len(days), [r.kl] * len(days)])
        S = key.reindex(idx_s).to_numpy(); L = key.reindex(idx_l).to_numpy()
        valid = (S[:, 0] >= 0) & (S[:, 1] >= S[:, 0]) & (S[:, 1] > 0) & (L[:, 0] >= 0) & (L[:, 1] >= L[:, 0])
        smid, sba = (S[:, 0] + S[:, 1]) / 2, S[:, 1] - S[:, 0]
        lmid, lba = (L[:, 0] + L[:, 1]) / 2, L[:, 1] - L[:, 0]
        X = (smid + SLIP * sba) - (lmid - SLIP * lba) + 2 * COMM       # executable close debit
        Xm = smid - lmid                                                # mid close debit (gross)
        cal = np.array([(d - r.entry_date).days for d in days], dtype=float)
        # settlement at expiry: raw spot on expiry day, else the last session before it
        sp = spot.loc[:r.expiry]
        S_T = float(sp.iloc[-1]) if len(sp) and (r.expiry - sp.index[-1]).days <= 4 else np.nan
        settle = max(r.ks - S_T, 0) - max(r.kl - S_T, 0) if np.isfinite(S_T) else np.nan
        hold_days = (r.expiry - r.entry_date).days
        exit_sess = {}  # arm -> (index into days or None for hold)
        v = np.where(valid)[0]
        prof = r.credit - X
        for arm, frac in (("T25", .25), ("T50", .50), ("T75", .75)):
            hit = v[X[v] <= (1 - frac) * r.credit]
            exit_sess[arm] = int(hit[0]) if len(hit) else None
        hit = v[X[v] <= 0.5 * r.credit]
        exit_sess["FAST50"] = int(hit[0]) if len(hit) and hit[0] < 5 else None
        hit = v[(prof[v] / r.capital) * 365 / np.clip(cal[v], 1, None) >= 1.0]
        exit_sess["ANN100"] = int(hit[0]) if len(hit) else None
        exit_sess["HOLD"] = None
        base = dict(ticker=r.ticker, entry_date=r.entry_date, expiry=r.expiry, width=r.width, credit=r.credit,
                    credit_mid=r.credit_mid, capital=r.capital, capital_mid=r.capital_mid,
                    coverage=float(valid.mean()) if len(valid) else np.nan, settle=settle)
        for arm in ARMS:
            i = exit_sess[arm]
            if i is None:
                pnl, pnl_g, dh, how = r.credit - settle, r.credit_mid - settle, hold_days, "expiry"
                exit_date = r.expiry
            else:
                pnl, pnl_g, dh, how = r.credit - X[i], r.credit_mid - Xm[i], cal[i], "take"
                exit_date = days[i]
            rows.append({**base, "arm": arm, "exit": how, "exit_date": exit_date, "days": dh,
                         "pnl": pnl, "roc": pnl / r.capital, "roc_gross": pnl_g / r.capital_mid})
    return pd.DataFrame(rows)


# ── stats ─────────────────────────────────────────────────────────────────────
def ctstat(x: pd.Series, d: pd.Series) -> tuple[float, float, int]:
    g = x.groupby(pd.to_datetime(d).dt.to_period("M")).mean()
    return g.mean(), (g.mean() / g.std() * np.sqrt(len(g)) if len(g) > 2 else np.nan), len(g)


def slot_sim(tr: pd.DataFrame, arm: str, fri_only: bool) -> pd.DataFrame:
    """One slot per ticker: enter the first eligible session after the previous exit."""
    out = []
    for t, g in tr[tr.arm == arm].sort_values("entry_date").groupby("ticker"):
        if fri_only:
            g = g[g.entry_date.dt.weekday == 4]
        free = pd.Timestamp.min
        for r in g.itertuples(index=False):
            if np.isfinite(r.roc) and r.entry_date > free:
                out.append(r)
                free = r.exit_date
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--pull-only", action="store_true"); a = ap.parse_args()
    trs = []
    for t in ROSTER:
        q = pull(t)
        if a.pull_only:
            continue
        e = build_entries(t, q)
        tr = run_arms(e, q, raw_spot(q))
        print(f"  {t}: {len(e):,} entries, settle known {tr.settle.notna().mean():.1%}, "
              f"median path coverage {tr.coverage.median():.0%}", flush=True)
        trs.append(tr)
    if a.pull_only:
        return
    tr = pd.concat(trs, ignore_index=True)
    tr = tr[tr.settle.notna()].reset_index(drop=True)
    tr.to_parquet(OUT_TRADES, index=False)
    tr["month"] = tr.entry_date.dt.to_period("M")
    fri = tr[tr.entry_date.dt.weekday == 4]

    # ── reproduction check vs the committed roster rebuild ────────────────────
    print("\n=== sanity: Friday T50 vs the 2026-09-22 roster rebuild (options_cache, +4.35% gross / -6.78% net) ===")
    x = fri[fri.arm == "T50"]
    print(f"  n {len(x):,}  gross {100 * x.roc_gross.mean():+.2f}%  net {100 * x.roc.mean():+.2f}%  "
          f"take rate {(x.exit == 'take').mean():.0%}  median days {x.days.median():.0f}")

    # ── per-entry arms, Friday entries ────────────────────────────────────────
    print("\n=== per-entry, FRIDAY entries (ROC on capital; net = house fills; t month-clustered) ===")
    print(f"{'arm':8s} {'n':>6s} {'gross%':>8s} {'net%':>8s} {'t':>6s} {'win%':>6s} {'take%':>6s} {'days':>5s} "
          f"{'net%/cap-day':>13s} {'worst%':>8s}")
    for arm in ARMS:
        x = fri[fri.arm == arm]
        m, t, _ = ctstat(x.roc, x.entry_date)
        print(f"{arm:8s} {len(x):>6,} {100 * x.roc_gross.mean():>8.2f} {100 * m:>8.2f} {t:>6.2f} "
              f"{100 * (x.roc > 0).mean():>6.1f} {100 * (x.exit == 'take').mean():>6.1f} {x.days.mean():>5.1f} "
              f"{100 * x.roc.sum() / x.days.sum():>13.4f} {100 * x.roc.min():>8.1f}")

    # ── PRIMARY ───────────────────────────────────────────────────────────────
    p = fri.pivot_table(index=["ticker", "entry_date"], columns="arm", values="roc").dropna()
    d = (p["T50"] - p["HOLD"]).rename("d").reset_index()
    m, t, nm = ctstat(d.d, d.entry_date)
    mid = d.entry_date.sort_values().iloc[len(d) // 2]
    h1 = ctstat(d.d[d.entry_date < mid], d.entry_date[d.entry_date < mid])
    h2 = ctstat(d.d[d.entry_date >= mid], d.entry_date[d.entry_date >= mid])
    print(f"\n=== PRIMARY: Friday, ROC(T50) - ROC(HOLD), net, paired ===")
    print(f"  diff {100 * m:+.2f}pp  t {t:+.2f}  ({nm} months, n {len(d):,})   "
          f"halves {100 * h1[0]:+.2f} (t {h1[1]:+.2f}) / {100 * h2[0]:+.2f} (t {h2[1]:+.2f})")
    yr = d.groupby(d.entry_date.dt.year).d.agg(["mean", "size"])
    print("  per year (pp):", "  ".join(f"{y} {100 * r['mean']:+.2f}" for y, r in yr.iterrows()))
    verdict = abs(t) >= 3 and np.sign(h1[0]) == np.sign(h2[0])
    print(f"  bar |t|>=3 and both halves same sign: {'PASS' if verdict else 'FAIL'}")
    for other in ["T25", "T75", "FAST50", "ANN100"]:
        dd = (p[other] - p["HOLD"]).rename("d").reset_index()
        mm, tt, _ = ctstat(dd.d, dd.entry_date)
        print(f"  (exploratory) {other} - HOLD: {100 * mm:+.2f}pp t {tt:+.2f}")

    # ── path coverage guard ───────────────────────────────────────────────────
    x = fri[fri.arm == "HOLD"]
    print(f"\n  path coverage (valid both-leg marks / sessions): median {x.coverage.median():.0%}, "
          f"<50% on {(x.coverage < .5).mean():.1%} of entries")
    lo = p.reset_index().merge(x[["ticker", "entry_date", "coverage"]], on=["ticker", "entry_date"])
    for lab, msk in [("coverage >= 90%", lo.coverage >= .9), ("coverage < 90%", lo.coverage < .9)]:
        z = lo[msk]
        print(f"    {lab:16s} n {len(z):>5,}  T50-HOLD {100 * (z.T50 - z.HOLD).mean():+.2f}pp")

    # ── SECONDARY: capital-time slot simulation ───────────────────────────────
    years = (tr.expiry.max() - tr.entry_date.min()).days / 365.25
    print(f"\n=== SECONDARY: one slot per ticker, re-deployed next eligible session ({years:.1f} yrs, 20 slots) ===")
    print(f"{'entry':6s} {'exit':7s} {'trades/yr':>9s} {'idle%':>6s} {'net ROC/yr %':>12s} {'gross/yr %':>10s} "
          f"{'worst mo %':>10s} {'t vs Fri-T50':>12s}")
    series = {}
    for fri_only in (True, False):
        for arm in ARMS:
            s = slot_sim(tr, arm, fri_only)
            s["em"] = pd.to_datetime(s.exit_date).dt.to_period("M")
            busy = (pd.to_datetime(s.exit_date) - s.entry_date).dt.days.groupby(s.ticker).sum()
            span = s.groupby("ticker").apply(lambda g: (pd.to_datetime(g.exit_date).max() - g.entry_date.min()).days)
            idle = 1 - (busy / span).mean()
            # equal-weight monthly slot return: sum ROC realised that month per ticker, mean across tickers
            mo = s.groupby(["em", "ticker"]).roc.sum().unstack().reindex(columns=ROSTER).fillna(0).mean(axis=1)
            series[(fri_only, arm)] = mo
            per_yr = s.groupby("ticker").roc.sum().mean() / years
            per_yr_g = s.groupby("ticker").roc_gross.sum().mean() / years
            lab = "Fri" if fri_only else "any"
            print(f"{lab:6s} {arm:7s} {len(s) / 20 / years:>9.1f} {100 * idle:>6.1f} {100 * per_yr:>12.2f} "
                  f"{100 * per_yr_g:>10.2f} {100 * mo.min():>10.2f}", end="")
            if (fri_only, arm) != (True, "T50"):
                base = series.get((True, "T50"))
                if base is not None:
                    j = pd.concat([mo, base], axis=1).fillna(0)
                    dd = j.iloc[:, 0] - j.iloc[:, 1]
                    print(f" {dd.mean() / dd.std() * np.sqrt(len(dd)):>12.2f}", end="")
            print()
    print("  Sidak bar for the 11 comparisons: |t| >= ~3.6")

    # ── TERTIARY: weekday ─────────────────────────────────────────────────────
    print("\n=== TERTIARY (descriptive): entry weekday, paired vs Friday of the same ticker-week ===")
    tr["wk"] = tr.entry_date.dt.to_period("W-FRI")
    for arm in ("HOLD", "T50"):
        x = tr[tr.arm == arm]
        fr = x[x.entry_date.dt.weekday == 4].set_index(["ticker", "wk"]).roc
        line = []
        for wd, nm in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
            y = x[x.entry_date.dt.weekday == wd]
            if wd == 4:
                line.append(f"{nm} {100 * y.roc.mean():+.2f}%")
                continue
            j = y.set_index(["ticker", "wk"]).roc.to_frame("r").join(fr.rename("f"), how="inner").reset_index()
            dd = j.r - j.f
            g = dd.groupby(j.wk).mean()
            line.append(f"{nm} {100 * y.roc.mean():+.2f}% (vs Fri {100 * dd.mean():+.2f}pp t "
                        f"{g.mean() / g.std() * np.sqrt(len(g)):+.2f})")
        print(f"  {arm:5s} " + " | ".join(line))

    # ── per ticker, Friday HOLD vs T50 ────────────────────────────────────────
    print("\n=== per ticker, Friday entries, net ROC % ===")
    pt = fri.pivot_table(index="ticker", columns="arm", values="roc", aggfunc="mean")[ARMS] * 100
    pt["n"] = fri[fri.arm == "HOLD"].groupby("ticker").size()
    print(pt.round(2).to_string())
    print(f"\ntrades -> {OUT_TRADES}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
OptionsPlay's OWN credit-spread spec, tested against delta-matched stock (2026-09-24, pre-registered here before the pull).

Source: Tony Zhang, "Finding the Optimal Credit Spreads" (bk9Co7V6AI4, 2020-10-08; notes in
data/optionsplay/videos/2020-10-08_bk9Co7V6AI4/notes.md): sell the ~50-delta, buy the ~25-delta, ~45 DTE, and
take only spreads whose credit is >= 33% of the width. What makes it NEW: our premium-to-width test
(`run_premium_to_width.py`) used 30d/20d at ~30 DTE, where only 0.07% of spreads reach 0.33, and it scored ROC, not
excess over the stock. `csp_yield_rank_2026-09-24` then showed the yield sort on puts is beta. So the open question:
is his near-the-money floor a PREMIUM filter, or a way of buying delta?

DATA: options_daily_v3 (Athena, pulled once to data/cache/optionsplay_spec_chains.parquet): the 20 names of the
ivrank/premium-to-width panel, Friday entries 2018-01 -> 2026-02, puts, DTE 38-55, |delta| 0.15-0.60, bid > 0.
Spot recovered from the chain (RAW strikes, lib.studies.chain_spot).
STRUCTURE: expiry nearest 45 DTE; short put nearest 0.50 delta, long put nearest 0.25 delta (each within 0.07).
FILL: credit = short bid - long ask - 2 x $0.0065 (cross both spreads: harsher than the 0.13-0.20 of spread measured
  on real fills in fill_slippage_2026-09-24, so the result is conservative). Held to expiry, settled at intrinsic
  against the chain-implied spot on the expiry Friday. (His exits -- 50% take, 2x stop, 21 DTE -- are not modelled:
  the stop is already CONTRADICTED on credit spreads, etf_put_spread_study section 2.)
RETURN on max-loss capital: roc = (credit - max(Ks - ST, 0) + max(Kl - ST, 0)) / (width - credit).
BENCHMARK: the stock held at the spread's entry net delta on the same capital:
  stock_d = (|d_short| - |d_long|) x (ST - S0) / (width - credit);  excess = roc - stock_d.
ARMS: ALL spreads of his structure; FLOOR = credit/width >= 0.33 (his filter); quintiles of credit/width within date.

PRIMARY (declared): FLOOR arm, mean EXCESS over delta-matched stock, month-clustered t.
  PASS: t >= 3 and positive in both halves (split 2022-07-01), no single year carrying it (per-year table).
SECONDARY (exploratory): FLOOR roc; ALL roc and excess; within-date Q5 - Q1 of roc and of excess; the share of spreads
  that reach 0.33; a re-price at 20% of each leg's spread (the arrival-price slippage measured on real fills).
One primary -> no multiple-testing charge.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_optionsplay_spec.py
"""
from __future__ import annotations
import os, warnings
from pathlib import Path
import numpy as np, pandas as pd
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
CACHE = "data/cache/optionsplay_spec_chains.parquet"
OUT = Path("data/studies/optionsplay_spec_2026-09-24.csv")
LOG = Path("data/studies/logs/optionsplay_spec_2026-09-24.log")
NAMES = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMD", "META", "AMZN", "GOOGL",
         "TSLA", "NFLX", "JPM", "XOM", "GLD", "SMH", "COST", "AVGO", "CRM", "WMT"]
COMM, FLOOR, SPLIT = 0.0065, 0.33, pd.Timestamp("2022-07-01")
lines = []


def P(s=""):
    print(s); lines.append(str(s))


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    from lib.athena_lib import athena
    lst = ", ".join(f"'{t}'" for t in NAMES)
    sql = f"""
    SELECT ticker, trade_date, expiry, cp, strike,
           CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask, CAST(delta AS DOUBLE) d,
           CAST((bid_iv + ask_iv)/2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({lst})
      AND trade_date >= TIMESTAMP '2018-01-01 00:00:00' AND trade_date <= TIMESTAMP '2026-04-30 23:59:59'
      AND day_of_week(trade_date) = 5 AND cp = 'P'
      AND bid > 0 AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) BETWEEN 38 AND 55
      AND ABS(delta) BETWEEN 0.15 AND 0.60
    """
    df = athena(sql); df.to_parquet(CACHE, index=False); return df


def pick(g, target):
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.07 else None


def tstat(s):
    s = s.dropna(); return s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan


raw = pull()
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize(); raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
raw = raw.drop_duplicates(["ticker", "trade_date", "expiry", "strike"])
SPOT = spot_from_chain(raw, delta="d")
rows = []
for (tk, d), g in raw[raw.trade_date <= "2026-02-27"].groupby(["ticker", "trade_date"]):
    g = g.assign(gap=(g.dte - 45).abs()); exp = g.sort_values("gap").expiry.iloc[0]; g = g[g.expiry == exp]
    s, l = pick(g, 0.50), pick(g, 0.25)
    if s is None or l is None or l.strike >= s.strike:
        continue
    S0, ST = SPOT.get((tk, d), np.nan), SPOT.get((tk, exp), np.nan)
    if not (np.isfinite(S0) and np.isfinite(ST)):
        continue
    width = s.strike - l.strike
    for arm, cr in (("cross", (s.bid - l.ask) - 2 * COMM),
                    ("slip20", (s.bid + s.ask) / 2 - (l.bid + l.ask) / 2 - 0.20 * ((s.ask - s.bid) + (l.ask - l.bid)) - 2 * COMM)):
        cap = width - cr
        if cr <= 0 or cap <= 0:
            continue
        pay = cr - max(s.strike - ST, 0) + max(l.strike - ST, 0)
        nd = abs(s.d) - abs(l.d)
        rows.append(dict(sym=tk, date=d, expiry=exp, arm=arm, width=width, credit=cr, cw=cr / width, iv=s.iv,
                         netdelta=nd, roc=100 * pay / cap, stock_d=100 * nd * (ST - S0) / cap))
T = pd.DataFrame(rows)
T["excess"] = T.roc - T.stock_d; T["month"] = T.date.dt.to_period("M")
T.to_csv(OUT, index=False)
missing_exp = raw.expiry.max()
for arm in ("cross", "slip20"):
    A = T[T.arm == arm].copy()
    tag = "real fill: cross both spreads" if arm == "cross" else "re-price at 20% of each leg's spread (measured arrival slippage)"
    P(f"\n{'#' * 90}\n# {tag}: {len(A):,} spreads, {A.sym.nunique()} names, {A.date.nunique()} Fridays, "
      f"{A.date.min().date()} -> {A.date.max().date()}\n{'#' * 90}")
    P(f"credit/width: median {A.cw.median():.3f}, p90 {A.cw.quantile(.9):.3f}; share >= {FLOOR}: {100 * (A.cw >= FLOOR).mean():.1f}%  "
      f"(mean net delta {A.netdelta.mean():.2f})")
    F = A[A.cw >= FLOOR]
    for name, x in (("ALL", A), ("FLOOR cw>=0.33", F)):
        m = x.groupby("month")
        P(f"  {name:<15} n {len(x):>5}  roc {x.roc.mean():+6.2f}% (t {tstat(m.roc.mean()):+.2f})  stock_d {x.stock_d.mean():+6.2f}%  "
          f"excess {x.excess.mean():+6.2f}pp (t {tstat(m.excess.mean()):+.2f})  win {100 * (x.roc > 0).mean():.0f}%  "
          f"worst1 {x.roc[x.roc <= x.roc.quantile(.01)].mean():+.0f}%")
    if arm == "cross":
        me = F.groupby("month").excess.mean(); first = F.groupby("month").date.min()
        h1, h2 = me[first < SPLIT], me[first >= SPLIT]
        P(f"\n[PRIMARY] FLOOR excess over delta-matched stock: {me.mean():+.2f}pp  t {tstat(me):+.2f} ({len(me)} months)  "
          f"halves {h1.mean():+.2f} (t {tstat(h1):+.2f}) / {h2.mean():+.2f} (t {tstat(h2):+.2f})")
        P("  by year (excess, n): " + "  ".join(f"{y} {v.excess.mean():+.1f} ({len(v)})" for y, v in F.groupby(F.date.dt.year)))
        ok = tstat(me) >= 3 and h1.mean() > 0 and h2.mean() > 0
        P(f"  PRE-REGISTERED PASS: {'YES' if ok else 'NO'}")
        P("  FLOOR names: " + ", ".join(f"{k} {v}" for k, v in F.sym.value_counts().head(8).items()))
    A["q"] = A.groupby("date").cw.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False) + 1 if len(s) >= 10 else np.nan)
    tab = A.dropna(subset=["q"]).groupby("q").agg(n=("roc", "size"), cw=("cw", "mean"), iv=("iv", "mean"), roc=("roc", "mean"),
                                                 stock_d=("stock_d", "mean"), excess=("excess", "mean"))
    P("\nwithin-date quintiles of credit/width (secondary):\n" + tab.round(2).to_string())
    for y in ("roc", "excess"):
        g = A.dropna(subset=["q"]).groupby(["month", "q"])[y].mean().unstack(); dd = (g[5] - g[1]).dropna()
        P(f"  Q5 - Q1 {y}: {dd.mean():+.2f}pp  t {tstat(dd):+.2f}")
LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(lines) + "\n")
print(f"\n-> {LOG}\n-> {OUT}")

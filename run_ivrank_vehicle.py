#!/usr/bin/env python3
"""
Does IV RANK choose the vehicle? (2026-09-22, pre-registered here before the first run.)

OptionsPlay's cheat sheet (2026-09-11 webinar @32:11): bullish + LOW IV rank -> buy a debit CALL spread;
bullish + HIGH IV rank -> sell a bull PUT spread (and the mirror on the bear side). We have never tested IV rank
as a vehicle chooser. Related priors: our August vehicle study ranked the 30d/15d debit call spread WORST
risk-equalised (n 93, mid prices); the bull put spread is only certified in the bearish-high-IV index cell.

UNIVERSE: 20 liquid names with deep chains (mega-caps + ETFs), 2018-01 .. 2026-02 (v3 has bid/ask/greeks to
2026-02; after Jul-2026 it is prints only).
ENTRIES: every Friday, the expiry closest to 30 DTE (25-40 DTE accepted).
VEHICLES, both opened the same day on the same name, held to expiry, settled on the underlying close:
  CALL DEBIT  long ~0.30d call / short ~0.15d call   -- paid at the ASK, sold at the BID (real fills)
  PUT CREDIT  short ~0.30d put  / long ~0.20d put    -- sold at the BID, bought at the ASK
Return is on capital at risk: debit / (width - credit). Costs: the crossing above + $0.0065/share/leg one way
(both structures settle at expiry, so no exit crossing).
IV RANK: per name, percentile of that day's ~30d 0.30-delta call mid-IV within the trailing 52 weekly entries
(strictly prior). Tercile cut per name: LOW <= 33, MID, HIGH >= 67 (his 33 line, made a rank within the name).
SETTLEMENT (fixed 2026-09-22 after a first run read -38% on bull puts): the liquid panel's closes are
split-ADJUSTED while v3 strikes are RAW, so any name with a split in the sample settles against the wrong price.
Spot is therefore recovered from the CHAIN itself, on both the entry and the expiry Friday, by inverting
Black-Scholes on every leg: d1 = Phi^-1(|delta|) for calls and Phi^-1(1+delta) for puts, then
S = K * exp(d1*iv*sqrt(T) - iv^2*T/2), taking the median across legs. The panel is used only for the 50-SMA flag.
DIRECTION: his rules are conditional on a bullish view, so each vehicle is also reported on the subset where the
name closed above its 50-day SMA at entry ("bullish"), which is the only direction filter we hold fixed.

PRE-REGISTERED PASS (his claim): the SPREAD between vehicles flips with IV rank in the direction he states --
(call debit - put credit) higher in the LOW tercile than in the HIGH tercile, month-clustered t >= 2 on the
difference-in-differences, same sign in both halves (split 2022-01-01). Anything else = NULL.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_ivrank_vehicle.py
"""
from __future__ import annotations
import os, warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.athena_lib import athena
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
CACHE = "data/cache/ivrank_vehicle_chains.parquet"
NAMES = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMD", "META", "AMZN", "GOOGL",
         "TSLA", "NFLX", "JPM", "XOM", "GLD", "SMH", "COST", "AVGO", "CRM", "WMT"]
COMM = 0.0065


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    lst = ", ".join(f"'{t}'" for t in NAMES)
    sql = f"""
    SELECT ticker, trade_date, expiry, cp, strike,
           CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask, CAST(delta AS DOUBLE) d,
           CAST((bid_iv + ask_iv)/2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({lst})
      AND trade_date >= TIMESTAMP '2018-01-01 00:00:00' AND trade_date <= TIMESTAMP '2026-02-27 23:59:59'
      AND day_of_week(trade_date) = 5
      AND bid > 0 AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) BETWEEN 25 AND 40
      AND ABS(delta) BETWEEN 0.10 AND 0.40
    """
    df = athena(sql); df.to_parquet(CACHE, index=False); return df


def pick(g: pd.DataFrame, target: float) -> pd.Series | None:
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.07 else None


raw = pull()
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize()
raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")   # RAW spot from the chain; see lib/studies/chain_spot.py
panel = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); panel["date"] = pd.to_datetime(panel.date)
C = panel.pivot(index="date", columns="ticker", values="close").sort_index()
s50 = C.rolling(50).mean()

rows = []
for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
    g = g.copy(); g["gap"] = (g.dte - 30).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[g.expiry == exp]
    calls, puts = g[g.cp == "C"], g[g.cp == "P"]
    c30, c15 = pick(calls, 0.30), pick(calls, 0.15)
    p30, p20 = pick(puts, 0.30), pick(puts, 0.20)
    if c30 is None or c15 is None or p30 is None or p20 is None: continue
    if tk not in C.columns or d not in C.index: continue
    spot = SPOT.get((tk, d), np.nan); ST = SPOT.get((tk, exp), np.nan)   # raw, from the chain on both dates
    if not (np.isfinite(ST) and np.isfinite(spot)): continue
    # call debit spread: pay ask on the long, receive bid on the short
    debit = (c30.ask - c15.bid) + 2 * COMM
    wc = c15.strike - c30.strike
    if debit <= 0 or wc <= 0: continue
    payc = min(max(ST - c30.strike, 0.0), wc)
    r_call = (payc - debit) / debit
    # put credit spread: receive bid on the short, pay ask on the long
    credit = (p30.bid - p20.ask) - 2 * COMM
    wp = p30.strike - p20.strike
    if credit <= 0 or wp <= 0 or credit >= wp: continue
    lossp = min(max(p30.strike - ST, 0.0), wp)
    r_put = (credit - lossp) / (wp - credit)
    rows.append(dict(sym=tk, date=d, expiry=exp, iv=c30.iv, spot=spot,
                     bull=bool(np.isfinite(s50.at[d, tk]) and C.at[d, tk] > s50.at[d, tk]),   # trend flag: adjusted series is fine
                     r_call=r_call, r_put=r_put, debit=debit, credit=credit, wc=wc, wp=wp))
T = pd.DataFrame(rows).sort_values(["sym", "date"])
T["ivrank"] = T.groupby("sym").iv.transform(lambda s: s.rolling(52, min_periods=40).apply(lambda w: (w[-1] > w[:-1]).mean(), raw=True) * 100)
T = T.dropna(subset=["ivrank"])
T["terc"] = np.where(T.ivrank <= 33, "LOW", np.where(T.ivrank >= 67, "HIGH", "MID"))
T["month"] = T.date.dt.to_period("M"); T["diff"] = T.r_call - T.r_put
print(f"spot check: median |chain-implied / panel close - 1| = {(T.spot / C.values[[C.index.get_loc(x) for x in T.date], [C.columns.get_loc(x) for x in T.sym]] - 1).abs().median():.3f}")
print(f"{len(T):,} paired entries, {T.sym.nunique()} names, {T.date.min().date()}..{T.date.max().date()}, {T.month.nunique()} months")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def table(df, lab):
    g = df.groupby("terc")[["r_call", "r_put", "diff"]].mean() * 100
    g["n"] = df.groupby("terc").size()
    g["t_diff"] = [mt(df[df.terc == k].groupby("month")["diff"].mean()) for k in g.index]
    print(f"\n{lab}\n{g.round(2).to_string()}")
    return g


for lab, sub in (("ALL entries", T), ("BULLISH only (spot > 50 SMA)", T[T.bull])):
    g = table(sub, lab)
    if {"LOW", "HIGH"} <= set(g.index):
        did = sub[sub.terc == "LOW"].groupby("month")["diff"].mean() - sub[sub.terc == "HIGH"].groupby("month")["diff"].mean()
        did = did.dropna()
        h1 = did[did.index < pd.Period("2022-01", "M")]; h2 = did[did.index >= pd.Period("2022-01", "M")]
        print(f"  his claim (call-debit favoured at LOW vs HIGH IV rank): DiD {100*did.mean():+.2f}pp  t {mt(did):+.2f}"
              f"  halves {100*h1.mean():+.2f} / {100*h2.mean():+.2f}  months {len(did)}")
        if lab.startswith("BULLISH"):
            ok = did.mean() > 0 and mt(did) >= 2 and np.sign(h1.mean()) == np.sign(h2.mean()) == 1
            print("  PRE-REGISTERED PASS:", "YES" if ok else "NO")
T.to_csv("data/studies/ivrank_vehicle_2026-09-22.csv", index=False)

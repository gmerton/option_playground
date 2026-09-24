#!/usr/bin/env python3
"""
Calibrate the house slippage charge against Gabe's REAL option fills (2026-09-24, pre-registered here before the pull).

WHY: `src/lib/studies/costs.py` charges 25% of each leg's quoted bid-ask per side traded. The 25% was copied from one
calendar study (dc_time_machine) and never measured. Every after-cost number in TEST_INDEX runs through it, so if the
true figure is 10% the ledger is too harsh, and if it is 50% every surviving strategy is overstated. The journal is
admissible for exactly this (cost realism), never for setup selection.

DATA
- Fills: MySQL `journal_trades`, asset_category OPT, transaction_type ExchTrade (BookTrade = expiry/assignment,
  dropped). `trade_datetime` is ET; one row per partial fill; `trade_price` is the raw fill (commission separate).
- Quotes: IBKR `reqHistoricalData(whatToShow="BID_ASK", barSize 1 min, useRTH)`. Per IB's convention a BID_ASK bar's
  OPEN is the time-averaged bid and CLOSE the time-averaged ask over the minute. Quote = the bar of the fill minute.
- ⚠ IBKR serves no history for EXPIRED options (tested: no security definition, by symbol or by conId with
  includeExpired). The sample is therefore only fills in contracts that expire on or after the pull date: 403 of
  1,224 fills, median DTE at fill 31 vs 16 for all fills. Longer-dated contracts have wider absolute spreads but it is
  the FRACTION of the spread that we measure. Report this selection explicitly; do not generalise to 0-7 DTE.
- ⚠ Survivorship of limit orders: only FILLED orders are visible. A resting limit at mid that fills is adversely
  selected (price moved through it), and unfilled orders cost opportunity, not slippage. This measure is therefore a
  LOWER bound on the cost of trading at a patient limit, and a fair measure for marketable orders.

MEASURE (per fill leg): s = side * (fill - mid) / (ask - bid), side = +1 buy / -1 sell, mid = (bid + ask) / 2.
  s = 0 fills at mid; s = 0.5 fills at the far touch (bid for a sale, ask for a purchase); s < 0 is price improvement
  beyond mid. The model assumes s = 0.25 on every leg.
UNIT: the ORDER = (underlying, fill minute). For multi-leg orders IB allocates the combo price across legs
  arbitrarily, so a combo is scored at the order level: s_order = sum(side * qty * (fill - mid)) /
  sum(|qty| * (ask - bid)). Single-leg orders reduce to the per-leg formula. Orders are weighted equally.
QUALITY FILTERS (declared): bid > 0, ask > bid, fill inside [bid - spread, ask + spread] (else a quote/fill mismatch,
  counted and reported, not silently dropped).

PRIMARY (declared in advance): the mean of s_order over all orders, with a bootstrap 95% CI resampled by trading day.
  Verdict: if the CI contains 0.25 -> the model is CALIBRATED; CI entirely below 0.25 -> the model is CONSERVATIVE
  (the ledger's after-cost numbers are too harsh by the gap); entirely above -> the model is OPTIMISTIC (every
  after-cost result is overstated). One primary, no multiple-testing charge.
SECONDARY (exploratory, labelled so): single-leg vs combo; opening vs closing; spread width as a % of mid (terciles);
  median alongside the mean; $ per contract; per-half (Aug vs Sep) for stability.

Usage (live TWS on 7496, read-only, a fresh clientId):
  source ~/.trading_env; PYTHONPATH=src .venv/bin/python3 run_fill_slippage.py            # pull (resumable) + score
  PYTHONPATH=src .venv/bin/python3 run_fill_slippage.py --score-only
"""
from __future__ import annotations
import argparse, time, warnings
from pathlib import Path
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
CACHE = Path("data/cache/fill_quotes_ibkr_1min.parquet")
OUT = Path("data/studies/fill_slippage_2026-09-24.csv")
LOG = Path("data/studies/logs/fill_slippage_2026-09-24.log")
MODEL_S = 0.25


def load_fills(asof: str) -> pd.DataFrame:
    from lib.mysql_lib import _get_conn
    t = pd.read_sql("SELECT conid, trade_date, trade_datetime, underlying_symbol, put_call, strike, expiry, buy_sell, "
                    "open_close, quantity, trade_price FROM journal_trades "
                    "WHERE asset_category='OPT' AND transaction_type='ExchTrade'", _get_conn())
    t["ts"] = pd.to_datetime(t.trade_datetime)
    t["expiry"] = pd.to_datetime(t.expiry)
    t["n_all"] = len(t)
    return t[t.expiry >= pd.Timestamp(asof)].copy()


def pull(fills: pd.DataFrame, client_id: int) -> None:
    from ib_async import IB, Contract
    have = pd.read_parquet(CACHE) if CACHE.exists() else pd.DataFrame(columns=["conid", "day"])
    done = set(zip(have.conid.astype(int), have.day.astype(str)))
    todo = sorted({(int(c), pd.Timestamp(d).strftime("%Y-%m-%d")) for c, d in zip(fills.conid, fills.trade_date)} - done)
    print(f"{len(todo)} contract-days to pull ({len(done)} cached)")
    if not todo:
        return
    ib = IB(); ib.connect("127.0.0.1", 7496, clientId=client_id, readonly=True, timeout=20)
    rows, t0 = [], time.time()
    for i, (cid, day) in enumerate(todo, 1):
        c = Contract(conId=cid, exchange="SMART")
        try:
            if not ib.qualifyContracts(c) or not c.conId:
                raise ValueError("unqualified")
            bars = ib.reqHistoricalData(c, endDateTime=day.replace("-", "") + " 16:00:00 US/Eastern", durationStr="1 D",
                                        barSizeSetting="1 min", whatToShow="BID_ASK", useRTH=True, timeout=60)
            for b in bars:
                rows.append(dict(conid=cid, day=day, minute=pd.Timestamp(b.date).tz_localize(None), bid=b.open, ask=b.close,
                                 ask_max=b.high, bid_min=b.low))
            if not bars:
                rows.append(dict(conid=cid, day=day, minute=pd.NaT, bid=np.nan, ask=np.nan, ask_max=np.nan, bid_min=np.nan))
        except Exception as e:  # noqa: BLE001 -- record and move on; reported in the score step
            rows.append(dict(conid=cid, day=day, minute=pd.NaT, bid=np.nan, ask=np.nan, ask_max=np.nan, bid_min=np.nan))
            print(f"  {cid} {day}: {e}")
        if i % 25 == 0 or i == len(todo):
            new = pd.DataFrame(rows)
            have = pd.concat([have, new], ignore_index=True) if len(have) else new
            have.to_parquet(CACHE, index=False); rows = []
            print(f"  {i}/{len(todo)}  {time.time() - t0:.0f}s")
    ib.disconnect()


def boot_ci(df: pd.DataFrame, col: str, n=4000, seed=7) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    days = df.day.unique(); g = {d: df.loc[df.day == d, col].values for d in days}
    stats = []
    for _ in range(n):
        pick = rng.choice(days, len(days))
        stats.append(np.concatenate([g[d] for d in pick]).mean())
    return tuple(np.percentile(stats, [2.5, 97.5]))


def score(fills: pd.DataFrame) -> None:
    q = pd.read_parquet(CACHE).dropna(subset=["minute"])
    f = fills.copy()
    f["minute"] = f.ts.dt.floor("min"); f["day"] = f.ts.dt.strftime("%Y-%m-%d")
    f = f.merge(q[["conid", "minute", "bid", "ask"]], on=["conid", "minute"], how="left")
    lines = []
    P = lambda s="": (print(s), lines.append(s))
    n0 = len(f)
    f["spread"] = f.ask - f.bid
    no_q = f.bid.isna(); bad_q = ~no_q & ((f.bid <= 0) | (f.spread <= 0))
    f["mid"] = (f.bid + f.ask) / 2; f["side"] = np.where(f.buy_sell.str.upper() == "BUY", 1, -1)
    px = f.trade_price.astype(float)
    outside = ~no_q & ~bad_q & ((px < f.bid - f.spread) | (px > f.ask + f.spread))
    P(f"fills in unexpired contracts: {n0} of {int(fills.n_all.iloc[0])} option fills")
    P(f"  no quote bar at the fill minute: {no_q.sum()} · zero/crossed quote: {bad_q.sum()} · fill far outside quote: {outside.sum()}")
    f = f[~no_q & ~bad_q & ~outside].copy()
    f["qty"] = f.quantity.astype(float).abs()
    f["s_leg"] = f.side * (px[f.index] - f.mid) / f.spread
    f["num"] = f.side * f.qty * (px[f.index] - f.mid); f["den"] = f.qty * f.spread
    f["usd_per_ct"] = f.side * (px[f.index] - f.mid) * 100
    o = (f.groupby(["underlying_symbol", "minute"])
          .agg(day=("day", "first"), num=("num", "sum"), den=("den", "sum"), legs=("conid", "nunique"),
               oc=("open_close", lambda s: "".join(sorted(set(s)))), spr_pct=("spread", lambda s: np.nan),
               usd=("usd_per_ct", "mean"))
          .reset_index())
    sp = f.assign(sp=f.spread / f.mid).groupby(["underlying_symbol", "minute"]).sp.mean()
    o["spr_pct"] = o.set_index(["underlying_symbol", "minute"]).index.map(sp)
    o["s"] = o.num / o.den
    o["kind"] = np.where(o.legs >= 2, "combo", "single")
    o.to_csv(OUT, index=False)
    lo, hi = boot_ci(o, "s")
    m = o.s.mean()
    verdict = "CALIBRATED" if lo <= MODEL_S <= hi else ("CONSERVATIVE (model too harsh)" if hi < MODEL_S else "OPTIMISTIC (model too kind)")
    P(f"scored fills {len(f)} · orders {len(o)} · trading days {o.day.nunique()}")
    P("")
    P("PRIMARY: mean fraction of the quoted spread paid vs mid, per order (model assumes 0.25)")
    P(f"  mean {m:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}] (day-block bootstrap)  median {o.s.median():+.3f}  -> {verdict}")
    P("")
    P("SECONDARY (exploratory)")
    def row(name, d):
        if len(d) < 5: P(f"  {name:<28} n {len(d):>4}  (too few)"); return
        a, b = boot_ci(d, "s") if d.day.nunique() > 3 else (np.nan, np.nan)
        P(f"  {name:<28} n {len(d):>4}  mean {d.s.mean():+.3f} [{a:+.3f}, {b:+.3f}]  median {d.s.median():+.3f}  $/ct vs mid {d.usd.mean():+.2f}")
    for k in ("single", "combo"): row(k, o[o.kind == k])
    for k, lab in (("O", "opening"), ("C", "closing")): row(lab, o[o.oc == k])
    o["spr_t"] = pd.qcut(o.spr_pct, 3, labels=["tight", "mid", "wide"])
    for k in ("tight", "mid", "wide"): row(f"spread {k} ({o[o.spr_t == k].spr_pct.median():.1%} of mid)", o[o.spr_t == k])
    row("August", o[o.day < "2026-09-01"]); row("September", o[o.day >= "2026-09-01"])
    P(f"  legs at or better than mid: {(f.s_leg <= 0).mean():.0%} · at/through far touch (s >= 0.5): {(f.s_leg >= 0.5).mean():.0%}")
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(lines) + "\n")
    print(f"\n-> {OUT}\n-> {LOG}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--score-only", action="store_true"); ap.add_argument("--asof", default="2026-09-24"); ap.add_argument("--client-id", type=int, default=173)
    a = ap.parse_args()
    fills = load_fills(a.asof)
    if not a.score_only:
        pull(fills, a.client_id)
    score(fills)

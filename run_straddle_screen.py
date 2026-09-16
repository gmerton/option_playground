#!/usr/bin/env python3
"""
Long-straddle live screen — CURRENT playbook spec (long_straddle_playbook.md, 2026-08-08).

Supersedes run_straddle_fvr_scan.py, which still screens the retired 140-name list,
targets ~10 DTE, and has no IV-percentile gate.

Gates checked, in playbook order:
  1. ticker in data/watchlist/straddle_pool_323.txt   (weekly-optionable pool)
  2. FVR >= 1.20        — 30->90d ATM-put forward vol ratio, computed LIVE from Tradier
  3. IV pct <= 30       — today's ~7 DTE ATM put IV ranked against that ticker's OWN
                          trailing history
  4. liquidity          — bid-ask <= 25% of mid on both straddle legs, OI > 0

EARNINGS ARE FLAGGED, NOT GATED. Tested 2026-08-11 on 38,768 trades: an earnings
event inside the holding window cuts hold-to-expiry return from +4.79% to +0.13%
(CI [-3.66,+4.14] — indistinguishable from zero). But the IV-percentile gate already
removes 98% of them as a byproduct — pre-earnings IV sits at the 90th percentile of a
name's own range, and earnings trades fall from 9.6% of all trades to 0.3% of arm C.
An explicit gate would remove ~16 trades in 5,265, so this reports proximity instead.

IV-PERCENTILE SOURCE (rev 2026-09-16). Two references are computed and both are printed:

  ib      today's IV30 ranked against the SAME name's trailing 1y IV30 history, pulled
          live from IBKR (reqHistoricalData OPTION_IMPLIED_VOLATILITY). CURRENT.
  athena  ~7 DTE ATM put IV ranked against silver.fwd_vol_daily -- the study's original
          metric, but that table ENDS 2026-02-20 (v3 lost bid/ask in Mar 2026, so the
          builder cannot be extended; Jun 2026+ is prints-only). ~7 months stale.

The gate uses `ib` when IBKR is reachable and falls back to `athena` otherwise, marking
which was used per row. IBKR is queried ONLY for names that already clear the FVR and
liquidity gates, so a full-pool run costs a handful of historical-data requests.

⚠ The two are not the same metric: IBKR publishes a 30-day composite IV, the study gated
on ~10-DTE ATM put IV. Both answer "is this name's vol cheap against its own year", and
the printed columns let you see where they disagree; treat a large gap as a reason to
look at the name rather than to trust either number.

Requires TWS/Gateway for the `ib` source. The live-port guard in ibkr_bot/conn.py is
respected, not bypassed -- run with IB_PORT=7496 IB_ALLOW_LIVE=1 for live TWS (this
script only ever calls reqHistoricalData; it places no orders).

Usage:
  TRADIER_API_KEY=... AWS_PROFILE=clarinut-gmerton IB_PORT=7496 IB_ALLOW_LIVE=1 \\
      PYTHONPATH=src:. .venv/bin/python3 run_straddle_screen.py
  ... --tickers AAPL MU        # screen a subset
  ... --min-fvr 1.10           # widen the report (gate unchanged at 1.20)
  ... --iv-source athena       # skip IBKR, gate on the stale table (old behaviour)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from datetime import date

import numpy as np
import pandas as pd
import awswrangler as wr

from run_straddle_fvr_scan import scan_one, quote_straddle
from lib.mysql_lib import _get_engine
from lib.tradier.tradier_client_wrapper import TradierClient

POOL = "data/watchlist/straddle_pool_323.txt"
FVR_GATE, IVPCT_GATE, BA_MAX = 1.20, 30.0, 25.0


def next_earnings(tickers: list[str]) -> dict:
    """{ticker: date of next earnings on/after today} from stocks.earnings_report."""
    try:
        q = ("SELECT ticker, MIN(raw_date) d FROM earnings_report "
             "WHERE raw_date >= CURDATE() AND ticker IN (%s) GROUP BY ticker"
             % ",".join(f"'{t}'" for t in tickers))
        e = pd.read_sql(q, _get_engine())
        return {r.ticker: pd.Timestamp(r.d).date() for r in e.itertuples(index=False)}
    except Exception as exc:
        print(f"  (earnings lookup unavailable: {type(exc).__name__}) — flag will show n/a")
        return {}


def trailing_iv(tickers: list[str]) -> pd.DataFrame:
    """Per-ticker trailing iv_put_10 distribution (ends 2026-02-20 — see header)."""
    frames, CH = [], 200
    for i in range(0, len(tickers), CH):
        b = tickers[i:i + CH]
        frames.append(wr.athena.read_sql_query(
            sql=f"""SELECT ticker, iv_put_10 FROM silver.fwd_vol_daily
                    WHERE ticker IN ({",".join(f"'{t}'" for t in b)})
                      AND iv_put_10 > 0 AND trade_date >= DATE '2025-02-20'""",
            database="silver", workgroup="dev-v3", s3_output="s3://athena-919061006621/"))
    return pd.concat(frames, ignore_index=True)


IB_PACE_S = 0.35          # reqHistoricalData pacing
IB_MAX_CALLS = 50         # IB allows ~60 historical requests per 10 min; stay under it in one burst


def ibkr_iv_pctile(tickers: list[str], client_id: int = 47) -> pd.DataFrame:
    """Today's IV30 and its trailing-1y percentile per ticker, straight from IBKR.

    Returns columns ticker / ib_iv30 / ib_pctile / ib_asof / ib_days, empty on any
    connection failure (the caller then falls back to the stale Athena reference).
    Read-only: reqHistoricalData(OPTION_IMPLIED_VOLATILITY) only, no orders.
    """
    if not tickers:
        return pd.DataFrame(columns=["ticker", "ib_iv30", "ib_pctile", "ib_asof", "ib_days"])
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot"))
    try:
        from ib_async import Stock, util
        from conn import connect_ib
        ib = connect_ib(client_id=client_id, timeout=15)
    except SystemExit as exc:                      # live-port guard, or gateway absent
        print(f"  (IBKR unavailable: {exc}) — falling back to the stale Athena reference")
        return pd.DataFrame()
    except Exception as exc:                       # noqa: BLE001
        print(f"  (IBKR unavailable: {type(exc).__name__}: {exc}) — falling back to Athena")
        return pd.DataFrame()

    rows = []
    for t in tickers:
        try:
            c = Stock(t, "SMART", "USD"); ib.qualifyContracts(c)
            bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y", barSizeSetting="1 day",
                                        whatToShow="OPTION_IMPLIED_VOLATILITY", useRTH=True, formatDate=1)
            time.sleep(IB_PACE_S)
            if not bars:
                continue
            df = util.df(bars)
            iv = pd.Series(df["close"].values, index=pd.to_datetime(df["date"]))
            iv = iv[iv > 0]
            if len(iv) < 60:
                continue
            today, hist = float(iv.iloc[-1]), iv.iloc[:-1]
            rows.append(dict(ticker=t, ib_iv30=100 * today, ib_pctile=100 * (hist < today).mean(),
                             ib_asof=iv.index[-1].date(), ib_days=len(iv)))
        except Exception:                          # noqa: BLE001 — one bad name must not kill the screen
            continue
    ib.disconnect()
    return pd.DataFrame(rows)


async def gather(tickers: list[str], conc: int):
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        sem = asyncio.Semaphore(conc)
        res = await asyncio.gather(*[scan_one(c, t, sem) for t in tickers])
        quotes = {}
        for r in res:
            if not r.get("err") and r.get("fvr", 0) >= 1.0:      # quote the plausible ones
                quotes[r["tkr"]] = await quote_straddle(c, r["tkr"], r["spot"])
    return res, quotes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=None)
    ap.add_argument("--min-fvr", type=float, default=1.10)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--iv-source", choices=["ibkr", "athena"], default="ibkr",
                    help="reference for the IV percentile gate (default ibkr, falls back to athena)")
    ap.add_argument("--ib-client-id", type=int, default=47)
    a = ap.parse_args()

    tickers = a.tickers or [l.strip() for l in open(POOL) if l.strip()]
    print(f"screening {len(tickers)} names — gates: FVR>={FVR_GATE}, "
          f"IVpct<={IVPCT_GATE:.0f}, BA<={BA_MAX:.0f}%")
    print(f"today: {date.today():%A %Y-%m-%d}\n")

    res, quotes = asyncio.run(gather(tickers, a.concurrency))
    ok = sorted({r["tkr"] for r in res if not r.get("err")})
    hist = trailing_iv(ok)
    earn = next_earnings(ok)

    rows, errs = [], 0
    for r in res:
        if r.get("err"):
            errs += 1; continue
        t, fvr, iv30 = r["tkr"], r.get("fvr"), r.get("iv30")
        h = hist[hist.ticker == t].iv_put_10
        ath = (h < iv30).mean() * 100 if (len(h) >= 60 and iv30) else np.nan
        q = quotes.get(t) or {}
        ed = earn.get(t)
        edays = (ed - date.today()).days if ed else None
        rows.append(dict(tkr=t, spot=r["spot"], fvr=fvr, iv30=iv30, ath_pctile=ath,
                         dte=q.get("dte"), cost=q.get("cost"), ba=q.get("ba"), oi=q.get("oi"),
                         earn_days=edays,
                         earn_in_win=(edays is not None and q.get("dte") is not None
                                      and 0 <= edays <= q.get("dte"))))
    d = pd.DataFrame(rows)
    d["g_fvr"] = d.fvr >= FVR_GATE
    d["g_liq"] = ((d.ba <= BA_MAX) & (d.oi > 0)).fillna(False)

    # IBKR is asked only about names that already clear FVR + liquidity: those are the only
    # rows whose verdict the IV percentile can still change.
    d["ib_pctile"] = np.nan
    cand = list(d.loc[d.g_fvr & d.g_liq].sort_values("fvr", ascending=False).tkr)
    if len(cand) > IB_MAX_CALLS:
        print(f"  {len(cand)} FVR+liquidity survivors exceeds the IB pacing budget; "
              f"querying the top {IB_MAX_CALLS} by FVR, the rest fall back to athena")
        cand = cand[:IB_MAX_CALLS]
    if a.iv_source == "ibkr" and cand:
        print(f"  IBKR IV percentile for {len(cand)} FVR+liquidity survivors: {' '.join(cand)}")
        ibd = ibkr_iv_pctile(cand, client_id=a.ib_client_id)
        if not ibd.empty:
            d = d.drop(columns=["ib_pctile"]).merge(
                ibd.rename(columns={"ticker": "tkr"}), on="tkr", how="left")
            print(f"  IBKR returned {int(ibd.ib_pctile.notna().sum())} of {len(cand)} "
                  f"(as of {ibd.ib_asof.max()})")
    for c in ("ib_iv30", "ib_asof", "ib_days"):
        if c not in d.columns:
            d[c] = np.nan

    d["iv_src"] = np.where(d.ib_pctile.notna(), "ib", np.where(d.ath_pctile.notna(), "athena", "none"))
    d["ivpct"] = d.ib_pctile.fillna(d.ath_pctile)
    d["g_iv"] = d.ivpct <= IVPCT_GATE
    d["pass_all"] = d.g_fvr & d.g_iv.fillna(False) & d.g_liq

    print(f"scanned {len(d)} ok, {errs} errors")
    print(f"  FVR>={FVR_GATE}: {d.g_fvr.sum()}   liquidity: {int(d.g_liq.sum())}"
          f"   both: {int((d.g_fvr & d.g_liq).sum())}   +IVpct<={IVPCT_GATE:.0f}: {int(d.pass_all.sum())}")
    nib = int((d.iv_src == "ib").sum())
    if nib:
        cmp_ = d[(d.iv_src == "ib") & d.ath_pctile.notna()]
        if len(cmp_):
            gap = (cmp_.ib_pctile - cmp_.ath_pctile).abs()
            flip = int(((cmp_.ib_pctile <= IVPCT_GATE) != (cmp_.ath_pctile <= IVPCT_GATE)).sum())
            print(f"  IV source: ib for {nib} name(s), athena for {int((d.iv_src=='athena').sum())}"
                  f"   |ib-athena| median {gap.median():.0f}pp, max {gap.max():.0f}pp,"
                  f" verdict differs on {flip}/{len(cmp_)}")

    q = d[d.pass_all].sort_values("fvr", ascending=False)
    print(f"\n{'='*84}\n  QUALIFIERS ({len(q)})\n{'='*84}")
    if q.empty:
        print("  none")
    else:
        print(f"  {'tkr':<7}{'spot':>9}{'FVR':>8}{'IV%ib':>7}{'IV%ath':>8}{'src':>7}{'DTE':>5}"
              f"{'strad$':>9}{'BA%':>7}{'OI':>7}{'size':>7}   earnings")
        for x in q.itertuples(index=False):
            if x.earn_days is None:
                eflag = "n/a"
            elif x.earn_in_win:
                eflag = f"⚠ IN WINDOW (T+{x.earn_days})"
            else:
                eflag = f"T+{x.earn_days}"
            ib = f"{x.ib_pctile:.0f}%" if pd.notna(x.ib_pctile) else "-"
            at = f"{x.ath_pctile:.0f}%" if pd.notna(x.ath_pctile) else "-"
            print(f"  {x.tkr:<7}{x.spot:>9.2f}{x.fvr:>8.3f}{ib:>7}{at:>8}{x.iv_src:>7}{x.dte:>5.0f}"
                  f"{x.cost:>9.2f}{x.ba:>7.1f}{int(x.oi):>7}"
                  f"{'FULL' if x.fvr>=1.40 else 'half':>7}   {eflag}")
        nwin = int(q.earn_in_win.sum())
        if nwin:
            print(f"\n  ⚠ {nwin} qualifier(s) report earnings inside the holding window.")
            print(f"    Not a disqualifier — the IV gate already screens out 98% of earnings")
            print(f"    trades, so these are the ~2% exception. But earnings straddles earned")
            print(f"    +0.13% hold-to-expiry vs +4.79% clean. Size accordingly.")

    near = d[(~d.pass_all) & (d.fvr >= a.min_fvr)].sort_values("fvr", ascending=False).head(12)
    if len(near):
        print(f"\n  --- near misses (FVR >= {a.min_fvr}) ---")
        print(f"  {'tkr':<7}{'FVR':>8}{'IVpct':>8}{'src':>7}{'BA%':>7}   blocked by")
        for x in near.itertuples(index=False):
            why = ", ".join(w for w, ok in
                            [("FVR", x.g_fvr), ("IVpct", bool(x.g_iv)), ("liquidity", bool(x.g_liq))] if not ok)
            iv = f"{x.ivpct:.0f}%" if pd.notna(x.ivpct) else "n/a"
            ba = f"{x.ba:.1f}" if pd.notna(x.ba) else "n/a"
            print(f"  {x.tkr:<7}{x.fvr:>8.3f}{iv:>8}{x.iv_src:>7}{ba:>7}   {why}")
    d.to_csv("straddle_screen_latest.csv", index=False)
    print(f"\n  full results -> straddle_screen_latest.csv")


if __name__ == "__main__":
    main()

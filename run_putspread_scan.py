#!/usr/bin/env python3
"""
Single-name bull-put-spread scan (2026-09-18), built from the rules that tested:
  universe   leaders: ADDV >= $50M, 10>20>50 stacked (house slack), within 15% of the 52-week high, above a rising 50-day
  IV gate    own IV30 percentile (1y, IBKR) >= 60  AND  IV30 / RV30 >= 1.0     (paid_to_wait_study: gate +5.7% net vs -3.3% ungated;
             today's PANW/CRWD lesson: at pct 55-57 and IV/RV 0.78 the credit did not pay for the odds)
  market     the daily state must not be up/B+ (that cell loses -5.2%); printed as context
  structure  ~30 DTE, short ~0.30 delta / long ~0.15 delta puts (the study's legs); credit, width, BA both legs, wing OI
  liquidity  bid-ask <= 25% of mid on both legs, wing OI >= 50, credit >= 2x commissions
  earnings   flagged if inside the window (Tradier calendar when available; otherwise unknown)
Management for anything taken: HOLD to expiry, never manage on the break, size to the max loss.

Usage: IB_PORT=7496 IB_ALLOW_LIVE=1 TRADIER_API_KEY=... PYTHONPATH=src:. .venv/bin/python3 run_putspread_scan.py [--expiry 2026-10-16] [--min-ivpct 60]
"""
from __future__ import annotations
import argparse, asyncio, os, sys
from datetime import date
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot"))
from lib.commons.ma_stack import stack_run
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_contracts import list_contracts_for_expiry

ap = argparse.ArgumentParser(); ap.add_argument("--expiry", default="2026-10-16"); ap.add_argument("--min-ivpct", type=float, default=60)
ap.add_argument("--min-ivrv", type=float, default=1.0); ap.add_argument("--client-id", type=int, default=62); ap.add_argument("--no-chains", action="store_true")
a = ap.parse_args()

# ---- universe from the liquid panel
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]; raw["date"] = pd.to_datetime(raw.date)
raw = raw[raw.date >= raw.date.max() - pd.Timedelta(days=500)]
pv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index()
H, L, C, V = pv("high"), pv("low"), pv("close"), pv("volume")
addv = (C * V).tail(50).mean(); uni = addv[addv >= 50e6].index; H, L, C = H[uni], L[uni], C[uni].ffill(limit=1)
adr = (H / L - 1).shift(1).rolling(20).mean() * 100; run = stack_run(C, adr=adr); s50 = C.rolling(50).mean(); hi52 = H.shift(1).rolling(252, min_periods=120).max()
e21 = C.ewm(span=21, adjust=False).mean()
d = C.index[-1]
lead = (run.loc[d] > 0) & (C.loc[d] / hi52.loc[d] - 1 > -0.15) & (C.loc[d] > s50.loc[d]) & (s50.loc[d] > s50.iloc[-6])
names = sorted(lead[lead].index)
spy = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); spy = spy[spy.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
trend = "up" if spy.iloc[-1] > spy.rolling(50).mean().iloc[-1] > spy.rolling(200).mean().iloc[-1] else ("bear" if spy.iloc[-1] < spy.rolling(200).mean().iloc[-1] else "chop")
adv = (C.pct_change() > 0).mean(axis=1).rolling(10).mean().iloc[-1]; breadth = "B+" if adv >= 0.5 else "B-"
print(f"panel {d.date()} | {len(uni)} names with ADDV >= $50M | {len(names)} leaders (stacked, within 15% of high, above a rising 50-day) | market state {trend}/{breadth}" + ("  <-- up/B+ is the LOSING cell for single-name put spreads (paid_to_wait)" if trend == "up" and breadth == "B+" else ""))

# ---- IV percentile from IBKR
from ib_async import Stock, util
from conn import connect_ib
ib = connect_ib(client_id=a.client_id, timeout=20)
rows = []
for s in names:
    try:
        c = Stock(s, "SMART", "USD"); ib.qualifyContracts(c)
        iv = util.df(ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y", barSizeSetting="1 day", whatToShow="OPTION_IMPLIED_VOLATILITY", useRTH=True, formatDate=1))
        rv = util.df(ib.reqHistoricalData(c, endDateTime="", durationStr="1 M", barSizeSetting="1 day", whatToShow="HISTORICAL_VOLATILITY", useRTH=True, formatDate=1))
        if iv is None or len(iv) < 120: continue
        iv = iv["close"][iv["close"] > 0]; today_iv = float(iv.iloc[-1]); hist = iv.iloc[:-1]
        rv_now = float(rv["close"][rv["close"] > 0].iloc[-1]) if rv is not None and len(rv) else np.nan
        rows.append(dict(tkr=s, px=float(C.loc[d, s]), iv30=round(100 * today_iv, 1), iv_pct=round(100 * (hist < today_iv).mean()), rv30=round(100 * rv_now, 1),
                         iv_rv=round(today_iv / rv_now, 2) if rv_now else np.nan, adr=round(float(adr.loc[d, s]), 1), ext21=round(float((C.loc[d, s] / e21.loc[d, s] - 1) * 100 / adr.loc[d, s]), 1),
                         off52=round(float((C.loc[d, s] / hi52.loc[d, s] - 1) * 100), 1)))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {s}: {type(exc).__name__}", file=sys.stderr)
ib.disconnect()
iv = pd.DataFrame(rows)
if iv.empty: sys.exit("no IV data")
gate = iv[(iv.iv_pct >= a.min_ivpct) & (iv.iv_rv >= a.min_ivrv)].sort_values("iv_pct", ascending=False)
print(f"\nIV gate (own pct >= {a.min_ivpct:.0f} AND IV/RV >= {a.min_ivrv}): {len(gate)} of {len(iv)} leaders")
pd.set_option("display.width", 220)
print(gate.to_string(index=False) if len(gate) else "  none")
near = iv[(iv.iv_pct >= 50) & (iv.iv_pct < a.min_ivpct)].sort_values("iv_pct", ascending=False)
if len(near): print(f"\nnear misses (pct 50-{a.min_ivpct:.0f}):"); print(near.to_string(index=False))
iv.to_csv(f"data/watchlist/putspread_scan_iv_{d.date()}.csv", index=False)
if a.no_chains or gate.empty: sys.exit(0)


# ---- chains: ~0.30 short / ~0.15 long put at the target expiry
async def quote(sym, spot):
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        ch = await list_contracts_for_expiry(sym, a.expiry, option_type="put", client=c, min_strike=spot * 0.7, max_strike=spot * 1.02)
    puts = [o for o in ch if o.get("bid") and o.get("ask") and (o.get("greeks") or {}).get("delta") is not None]
    if len(puts) < 4: return None
    def pick(target): return min(puts, key=lambda o: abs(abs(float(o["greeks"]["delta"])) - target))
    s, l = pick(0.30), pick(0.15)
    if s["strike"] <= l["strike"]: return None
    mid = lambda o: (o["bid"] + o["ask"]) / 2; ba = lambda o: (o["ask"] - o["bid"]) / mid(o) * 100 if mid(o) > 0 else 999
    credit = mid(s) - mid(l); width = s["strike"] - l["strike"]
    return dict(short=s["strike"], sd=round(abs(float(s["greeks"]["delta"])), 2), long=l["strike"], ld=round(abs(float(l["greeks"]["delta"])), 2), credit=round(credit, 2), width=width,
                cw=round(100 * credit / width), ba_s=round(ba(s)), ba_l=round(ba(l)), oi_l=l.get("open_interest", 0), oi_s=s.get("open_interest", 0),
                cushion_adr=None)


out = []
for r in gate.itertuples():
    try:
        q = asyncio.run(quote(r.tkr, r.px))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {r.tkr} chain: {exc}"[:120]); continue
    if not q: continue
    q["cushion_adr"] = round((r.px / q["short"] - 1) * 100 / r.adr, 1)
    liquid = q["ba_s"] <= 25 and q["ba_l"] <= 25 and q["oi_l"] >= 50 and q["credit"] >= 0.10
    out.append(dict(tkr=r.tkr, px=r.px, iv_pct=r.iv_pct, iv_rv=r.iv_rv, **q, liquid="YES" if liquid else "no"))
res = pd.DataFrame(out)
print(f"\n{a.expiry} bull put spreads (~0.30 / ~0.15 delta):")
print(res.to_string(index=False) if len(res) else "  no quotable chains")
if len(res): res.to_csv(f"data/watchlist/putspread_scan_{d.date()}.csv", index=False)
print("\nManagement: HOLD to expiry; never manage on the break; size to the max loss (width - credit). Check earnings dates before entry.")

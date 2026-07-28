#!/usr/bin/env python3
"""
Live FVR scan for the long-straddle strategy (long_straddle_playbook.md).

Computes today's forward-vol ratio (30->90d, ATM puts) for the walk-forward
approved universe straight from Tradier chains — replaces the stale
fvr_daily.parquet path for live entry decisions.

Signal:  FVR >= 1.40 -> full size (1.5% premium)
         FVR 1.20-1.39 -> half size (0.75% premium)
Entry day per playbook: Friday morning, ~10 DTE ATM straddle, stop -50% premium.
For qualifiers this also quotes the ~10 DTE ATM straddle (cost, BA%, OI) so the
playbook's liquidity gate can be checked in one pass. Earnings dates are NOT a
strategy gate (the study had none) — check them separately if you care.

Run:
    PYTHONPATH=src .venv/bin/python3 run_straddle_fvr_scan.py            # core 82
    ... --extended        # also the 58-name 3-4-fold list (0.5x sizing)
    ... --min-fvr 1.10    # widen the report (signal thresholds unchanged)

Requires: TRADIER_API_KEY.
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys
from datetime import date

from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.list_expirations import list_expirations
from lib.commons.get_underlying_price import get_underlying_price
from lib.tradier.tradier_client_wrapper import TradierClient

CORE = """AAL AAOI AAPL AFL AG AMC ANET AVGO BAC BK BKNG BSX CAT CMG COF COP COTY CSCO
CVNA CVS CYBR EOG ERX ET ETN EW FCX FDX FEZ GM GS HAL HCA HD IBM INTU IYR JNJ JPM KKR
LB LLY LOW LRCX MCK MET MRK MRVL MT MU NOV NTAP NTES NVDA OIH PAA PBR PSX RCL RIG RRC
SCHW SLB STX SU SYY TECK TEVA TPR TQQQ TSM UAL ULTA UPRO URI VLO VOD WFC WMB XLK XRT
YUM""".split()

EXTENDED = """ABBV AGNC AMAT AMRN ASML AXP BP BURL C CF CLF COST CVX DAL DB DE ED EPD
FAS FSLR FUTU GD HPE INTC JETS KLAC KR LEN LVS MAR MARA MDB NET NOK NTR NUE NUGT OXY
PLTR PM PNC REGN ROST RVLV SIG SLV SMH STEM TAP TJX TNA TXN UNP WDC WPM XHB XOM ZIM""".split()


def _atm_put_iv(puts):
    """(iv, strike) of the put nearest 0.50 delta with a usable IV."""
    best = None
    for p in puts:
        g = p.get("greeks") or {}
        d, iv = g.get("delta"), g.get("mid_iv") or g.get("smv_vol")
        if d is None or not iv or iv <= 0:
            continue
        score = abs(abs(d) - 0.50)
        if best is None or score < best[0]:
            best = (score, float(iv), p["strike"])
    return (best[1], best[2]) if best else (None, None)


async def scan_one(client, tkr, sem):
    async with sem:
        try:
            spot = await get_underlying_price(tkr, client=client)
            exps = await list_expirations(tkr, client=client)
            today = date.today()
            dted = [(e, (date.fromisoformat(e) - today).days) for e in exps]
            # Far window is wide (50-160) because chains often jump e.g. 57d -> 148d
            # before the interim monthlies list; nearest-to-90 is still preferred.
            near = [x for x in dted if 20 <= x[1] <= 45]
            if not near:
                return {"tkr": tkr, "err": "no near expiry"}
            e30, t30 = min(near, key=lambda x: abs(x[1] - 30))
            far = [x for x in dted if 50 <= x[1] <= 160 and x[1] > t30 + 15]
            if not far:
                return {"tkr": tkr, "err": "no far expiry"}
            e90, t90 = min(far, key=lambda x: abs(x[1] - 90))
            p30 = await list_contracts_for_expiry(tkr, e30, option_type="put", client=client,
                                                  min_strike=spot * 0.8, max_strike=spot * 1.2)
            p90 = await list_contracts_for_expiry(tkr, e90, option_type="put", client=client,
                                                  min_strike=spot * 0.8, max_strike=spot * 1.2)
            iv30, _ = _atm_put_iv(p30)
            iv90, _ = _atm_put_iv(p90)
            if not iv30 or not iv90:
                return {"tkr": tkr, "err": "no ATM IV"}
            var_fwd = (iv90 ** 2 * t90 - iv30 ** 2 * t30) / (t90 - t30)
            if var_fwd <= 0:
                return {"tkr": tkr, "err": "negative fwd var"}
            fvr = math.sqrt(var_fwd) / iv30
            return {"tkr": tkr, "spot": spot, "iv30": iv30, "iv90": iv90,
                    "t30": t30, "t90": t90, "fvr": fvr}
        except Exception as e:
            return {"tkr": tkr, "err": f"{type(e).__name__}"[:30]}


async def quote_straddle(client, tkr, spot):
    """~10 DTE ATM straddle quote for a qualifier: (dte, cost, worst BA%, min OI)."""
    try:
        exps = await list_expirations(tkr, client=client)
        today = date.today()
        cands = [(e, (date.fromisoformat(e) - today).days) for e in exps if 6 <= (date.fromisoformat(e) - today).days <= 17]
        if not cands:
            return None
        exp, dte = min(cands, key=lambda x: abs(x[1] - 10))
        chain = await list_contracts_for_expiry(tkr, exp, client=client,
                                                min_strike=spot * 0.9, max_strike=spot * 1.1)
        legs = {}
        for cp in ("call", "put"):
            side = [c for c in chain if c.get("option_type") == cp]
            best = None
            for p in side:
                g = p.get("greeks") or {}
                d = g.get("delta")
                if d is None:
                    continue
                score = abs(abs(d) - 0.50)
                if best is None or score < best[1]:
                    best = (p, score)
            if not best:
                return None
            legs[cp] = best[0]
        cost = ba = oi = 0
        vals = []
        for p in legs.values():
            bid, ask = p.get("bid") or 0, p.get("ask") or 0
            if bid <= 0 or ask <= 0:
                return {"dte": dte, "bad": True}
            mid = (bid + ask) / 2
            cost += mid
            vals.append(((ask - bid) / mid * 100, p.get("open_interest") or 0))
        return {"dte": dte, "cost": cost, "ba": max(v[0] for v in vals),
                "oi": min(v[1] for v in vals),
                "strikes": f"{legs['call']['strike']:g}C/{legs['put']['strike']:g}P"}
    except Exception:
        return None


async def main() -> None:
    ap = argparse.ArgumentParser(description="Live FVR scan for the long-straddle universe")
    ap.add_argument("--extended", action="store_true", help="include the 3-4-fold list (0.5x size)")
    ap.add_argument("--min-fvr", type=float, default=1.20, help="report floor (signal tiers unchanged)")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    key = os.environ.get("TRADIER_API_KEY")
    if not key:
        sys.exit("TRADIER_API_KEY not set")

    universe = [(t, "core") for t in CORE]
    if args.extended:
        universe += [(t, "ext") for t in EXTENDED]

    sem = asyncio.Semaphore(args.concurrency)
    async with TradierClient(api_key=key) as client:
        res = await asyncio.gather(*[scan_one(client, t, sem) for t, _ in universe])
        tier = dict(universe)
        ok = [r for r in res if "err" not in r]
        errs = [r for r in res if "err" in r]
        ok.sort(key=lambda r: -r["fvr"])

        print(f"\n=== LIVE FVR SCAN — {date.today()} ({len(ok)} quoted, {len(errs)} skipped) ===")
        print("signal: >=1.40 full (1.5% premium) | 1.20-1.39 half (0.75%) | cap 3% open premium")
        print(f"{'tkr':<6}{'list':<5}{'spot':>9}{'iv30':>7}{'iv90':>7}{'FVR':>6}  size")
        hits = []
        for r in ok:
            if r["fvr"] < args.min_fvr:
                continue
            sz = "FULL" if r["fvr"] >= 1.40 else "half"
            if tier[r["tkr"]] == "ext":
                sz += " x0.5(ext)"
            print(f"{r['tkr']:<6}{tier[r['tkr']]:<5}{r['spot']:>9.2f}{r['iv30']*100:>6.1f}%{r['iv90']*100:>6.1f}%{r['fvr']:>6.2f}  {sz}")
            hits.append(r)

        if not hits:
            print("  (no signals at the report floor)")
        else:
            print(f"\n--- ~10 DTE ATM straddle quotes for qualifiers (playbook liquidity gate) ---")
            for r in hits:
                q = await quote_straddle(client, r["tkr"], r["spot"])
                if q is None:
                    print(f"{r['tkr']:<6} no 6-17 DTE expiry / no quote")
                elif q.get("bad"):
                    print(f"{r['tkr']:<6} {q['dte']}DTE — zero bid on a leg: FAIL liquidity gate")
                else:
                    n_half = int(750 // (q['cost'] * 100)) if q['cost'] > 0 else 0
                    n_full = int(1500 // (q['cost'] * 100)) if q['cost'] > 0 else 0
                    print(f"{r['tkr']:<6} {q['dte']}DTE {q['strikes']:<14} cost ${q['cost']:.2f}  "
                          f"worstBA {q['ba']:.0f}%  minOI {q['oi']}  -> {n_full} cts full / {n_half} half")
        if errs:
            print(f"\nskipped: {', '.join(r['tkr'] + '(' + r['err'] + ')' for r in errs)}")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Stock double-calendar / double-diagonal screener (playbook: data/studies/double_calendar_playbook.md, rule 3).

For each mega-cap on the roster, on a Friday:
  1. shorts at 0.35 delta each side on the ~20 DTE expiry, next weekly (5-9d later) for the longs
  2. LIQUIDITY GATE on the SAME-STRIKE calendar: four-leg bid-ask <= 25% of the calendar debit and debit >= $1.50
     (the diagonal's own debit is ~0, so the calendar quote is the test -- study step 7b)
  3. EARNINGS POSITION (next earnings date vs the two expiries) decides the structure:
       none in the window            -> double DIAGONAL, longs --widen % of spot wider (2%: +10.9% vs calendar +6.8%, step 7e)
       between short and long expiry -> same-strike double CALENDAR (+11 / +17%; the long-leg vega is the edge there)
       before the short expiry       -> MARGINAL, not an entry (12/19d +7% diag / +2% cal; 20/27d +17% diag) -- printed, not ENTER
  4. size on MAX RISK = net debit + wider wing (= debit for the calendar); hold to the short expiry.
Earnings dates: MySQL stocks.earnings_report (run_straddle_screen.next_earnings), yfinance fallback.
Usage: PYTHONPATH=src python run_stock_dcal_screener.py [--date YYYY-MM-DD] [--tickers ...] [--widen 1.0] [--dte 20] [--concurrency 3]
"""
from __future__ import annotations
import argparse, asyncio, csv, os, sys
from datetime import date
from pathlib import Path
from typing import Optional

from lib.tradier.tradier_client_wrapper import TradierClient
from run_friday_screener import (find_target_expiry, find_long_expiry, find_by_delta, ba_pct, mid_price,
                                 _safe_spot, _safe_expirations, _safe_chain, _dte)

# Roster = names that cleared the tight cut often enough to matter and scored >= ~+8% ROC on max risk with both halves
# positive in the 90-name study (results_ddiag_stocks*.parquet, tight cut, 1% diagonal); NFLX from the calendar table.
ROSTER = ["AVGO", "TSLA", "META", "V", "GOOGL", "GOOG", "NVDA", "MA", "MSFT", "GS", "ADBE", "CRM", "MRVL", "CVX", "AAPL",
          "AMD", "AMAT", "HD", "UNH", "JPM", "QCOM", "C", "MU", "COST", "TSM", "NFLX"]
SHORT_DELTA = 0.35; GAP_MIN, GAP_MAX = 5, 9; BA_MAX_PCT = 25.0; DEBIT_MIN = 1.50


def next_earnings_map(tickers: list[str]) -> dict[str, date]:
    out: dict[str, date] = {}
    try:
        from run_straddle_screen import next_earnings
        out = next_earnings(tickers)
    except Exception as e:
        print(f"  (MySQL earnings lookup failed: {type(e).__name__})", file=sys.stderr)
    missing = [t for t in tickers if t not in out]
    if missing:
        try:
            import yfinance as yf, pandas as pd
            for t in missing:
                try:
                    cal = yf.Ticker(t).calendar
                    ds = cal.get("Earnings Date") if isinstance(cal, dict) else None
                    if ds:
                        d = min(pd.Timestamp(x).date() for x in (ds if isinstance(ds, (list, tuple)) else [ds]))
                        if d >= date.today(): out[t] = d
                except Exception:
                    pass
        except Exception:
            pass
    return out


def _leg_at(chain: list[dict], cp: str, strike: float) -> Optional[dict]:
    return next((c for c in chain if c.get("option_type") == cp and abs(c["strike"] - strike) < 1e-6 and (c.get("bid") or 0) > 0), None)


def _wider(chain: list[dict], cp: str, k: float, w: float) -> Optional[dict]:
    cands = [c for c in chain if c.get("option_type") == cp and (c.get("bid") or 0) > 0
             and (c["strike"] <= k * (1 - w) if cp == "put" else c["strike"] >= k * (1 + w))]
    if not cands: return None
    return max(cands, key=lambda c: c["strike"]) if cp == "put" else min(cands, key=lambda c: c["strike"])


async def screen_one(t: str, client: TradierClient, today: date, dte: int, widen: float, earn: Optional[date], sem: asyncio.Semaphore) -> dict:
    r: dict = {"ticker": t, "verdict": "SKIP", "why": "", "earnings": earn.isoformat() if earn else ""}
    async with sem:
        spot = await _safe_spot(t, client); exps = await _safe_expirations(t, client)
    if not spot or not exps:
        r["why"] = "no spot / expirations"; return r
    se = find_target_expiry(exps, today, dte_target=dte, dte_tol=5)
    le = find_long_expiry(exps, se, GAP_MIN, GAP_MAX) if se else None
    if not se or not le:
        r["why"] = f"no expiry pair (~{dte} DTE + {GAP_MIN}-{GAP_MAX}d)"; return r
    async with sem:
        sc = await _safe_chain(t, se, client); lc = await _safe_chain(t, le, client)
    if not sc or not lc:
        r["why"] = "no chain"; return r
    # the near weekly often has $2.50 strikes where the next weekly has only $5 ones: pick the shorts by delta among
    # strikes that also exist (with a bid) on the long expiry, so a same-strike calendar is always constructible
    long_puts = {c["strike"] for c in lc if c.get("option_type") == "put" and (c.get("bid") or 0) > 0}
    long_calls = {c["strike"] for c in lc if c.get("option_type") == "call" and (c.get("bid") or 0) > 0}
    sc_common = [c for c in sc if (c.get("option_type") == "put" and c["strike"] in long_puts) or (c.get("option_type") == "call" and c["strike"] in long_calls)]
    sp = find_by_delta(sc_common, SHORT_DELTA, "put"); scall = find_by_delta(sc_common, SHORT_DELTA, "call")
    if sp is None or scall is None:
        r["why"] = "no 0.35d short strikes shared by both expiries"; return r
    Kp, Kc = sp["strike"], scall["strike"]
    lp, lcall = _leg_at(lc, "put", Kp), _leg_at(lc, "call", Kc)
    if lp is None or lcall is None:
        r["why"] = "no same-strike longs on the next weekly"; return r
    cal_debit = (mid_price(lp) - mid_price(sp)) + (mid_price(lcall) - mid_price(scall))
    ba4 = sum((c["ask"] - c["bid"]) for c in (sp, scall, lp, lcall))
    cal_ba_pct = 100 * ba4 / cal_debit if cal_debit > 0.01 else float("inf")
    r.update(spot=spot, short_exp=se, long_exp=le, sdte=_dte(se, today), gap=_dte(le, today) - _dte(se, today), Kp=Kp, Kc=Kc,
             cal_debit=round(cal_debit, 3), cal_ba_pct=round(cal_ba_pct, 1))
    # earnings position
    sed, led = date.fromisoformat(se), date.fromisoformat(le)
    epos = "none" if (earn is None or earn > led) else ("between" if earn > sed else "before short exp")
    r["epos"] = epos
    if cal_debit < DEBIT_MIN:
        r["why"] = f"calendar debit ${cal_debit:.2f} < ${DEBIT_MIN:.2f}"; return r
    if cal_ba_pct > BA_MAX_PCT:
        r["why"] = f"calendar 4-leg bid-ask {cal_ba_pct:.0f}% of debit > {BA_MAX_PCT:.0f}%"; return r
    # structure by earnings position
    if epos == "between":
        struct, longs = "CALENDAR", (lp, lcall)
    else:
        wp, wc = _wider(lc, "put", Kp, widen / 100), _wider(lc, "call", Kc, widen / 100)
        if wp is None or wc is None:
            r["why"] = f"no long strikes {widen}% wider on {le}"; return r
        struct, longs = f"DIAGONAL {widen:g}%", (wp, wc)
    lpx, lcx = longs
    net = (mid_price(lpx) - mid_price(sp)) + (mid_price(lcx) - mid_price(scall))
    width = max(Kp - lpx["strike"], lcx["strike"] - Kc)
    maxrisk = net + width
    leg_ba = max(ba_pct(c) or 9 for c in (sp, scall, lpx, lcx))
    r.update(structure=struct, Kpl=lpx["strike"], Kcl=lcx["strike"], net=round(net, 3), width=width, max_risk=round(maxrisk, 3),
             worst_leg_ba_pct=round(100 * leg_ba, 1))
    if epos == "before short exp":
        r["verdict"] = "MARGINAL"; r["why"] = f"earnings {earn} before the short expiry (weakest cell; +7% diag on 12/19d, +17% on 20/27d)"
    else:
        r["verdict"] = "ENTER"; r["why"] = ("earnings between the expiries -> same-strike calendar (+11/+17%)" if epos == "between"
                                          else f"no earnings in window -> {struct} (+10% vs +6.6% calendar)")
    return r


async def run(a) -> list[dict]:
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("ERROR: TRADIER_API_KEY not set", file=sys.stderr); sys.exit(1)
    earn = next_earnings_map(a.tickers)
    sem = asyncio.Semaphore(a.concurrency)
    async with TradierClient(api_key=api_key) as client:
        return await asyncio.gather(*[screen_one(t, client, a.date, a.dte, a.widen, earn.get(t), sem) for t in a.tickers])


def main() -> int:
    print("\n  ⚠ ON HOLD (2026-09-16): the calendar path study behind these rules truncated its daily path after ~2% moves; corrected ETF edge ≈ 0 and the stock re-run is pending. Output is for reference only -- not entries. See calendar_path_study.md erratum.\n")
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=date.today()); ap.add_argument("--tickers", nargs="*", default=ROSTER)
    ap.add_argument("--widen", type=float, default=2.0)   # step 7e: stocks plateau from 1% (+10.1) to 2% (+10.9); 2% = the ETF rule; ap.add_argument("--dte", type=int, default=20); ap.add_argument("--concurrency", type=int, default=3)
    a = ap.parse_args()
    rows = asyncio.run(run(a))
    order = {"ENTER": 0, "MARGINAL": 1, "SKIP": 2}
    rows.sort(key=lambda r: (order[r["verdict"]], r.get("cal_ba_pct", 999)))
    print(f"\n  STOCK DOUBLE CALENDAR / DIAGONAL SCREEN  ·  {a.date}  ·  shorts 0.35d ~{a.dte} DTE, longs next weekly, diagonal {a.widen:g}% wide")
    print("  gate = same-strike calendar: 4-leg bid-ask <= 25% of debit, debit >= $1.50 | structure by earnings position | size on MAX RISK | hold to short expiry\n")
    hdr = f"  {'':8s} {'tkr':6s} {'spot':>8s} {'short/long exp':22s} {'shorts P/C':>16s} {'cal debit':>9s} {'cal BA%':>7s} {'earn':10s} {'pos':8s} {'structure':13s} {'longs P/C':>16s} {'net':>8s} {'max risk':>8s}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        mark = {"ENTER": "🟢 ENTER", "MARGINAL": "🟡 MARG.", "SKIP": "🔴 SKIP "}[r["verdict"]]
        if "Kp" not in r:
            print(f"  {mark} {r['ticker']:6s} {'':>8s} {r['why']}"); continue
        net = r.get("net"); nets = ("" if net is None else (f"cr {abs(net):.2f}" if net < 0 else f"db {net:.2f}"))
        print(f"  {mark} {r['ticker']:6s} {r['spot']:8.2f} {r['short_exp']}/{r['long_exp'][5:]:5s} {r['Kp']:7.1f}/{r['Kc']:<7.1f} {r['cal_debit']:9.2f} {r['cal_ba_pct']:7.1f} {r['earnings'] or '-':10s} {r.get('epos',''):8s} {r.get('structure','') :13s} "
              + (f"{r['Kpl']:7.1f}/{r['Kcl']:<7.1f} {nets:>8s} {r['max_risk']:8.2f}" if "Kpl" in r else "") + ("" if r["verdict"] == "ENTER" else f"   {r['why']}"))
    out = Path("data/watchlist") / f"stock_dcal_{a.date.isoformat()}.csv"
    keys = ["ticker", "verdict", "why", "spot", "short_exp", "long_exp", "sdte", "gap", "Kp", "Kc", "cal_debit", "cal_ba_pct", "earnings", "epos", "structure", "Kpl", "Kcl", "net", "width", "max_risk", "worst_leg_ba_pct"]
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    n_e = sum(r["verdict"] == "ENTER" for r in rows); print(f"\n  {n_e} ENTER / {sum(r['verdict']=='MARGINAL' for r in rows)} MARGINAL / {len(rows) - n_e} other  ->  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Forward paper trade: the calm-regime SPY weekly put sale (CERTIFIED-CANDIDATE, spy_calm_weekly_put_2026-09-28.md).

Rule (as tested): on FRIDAY at ~15:50 ET, if the regime is CALM (NOT [SPY < 50-session SMA AND VIX >= 20]) and SPY net
dealer GEX > 0, sell the 7-DTE put (expiry nearest 7 calendar days in [5, 9]) at |delta| nearest 0.10 (primary) and
0.05 (variant); hold to expiry; settle on SPY's close. House fill: mid - 25% of the bid-ask - $0.0065/share.
Mid-week entries were tested and are NOT part of the rule (spy_calm_weekly_put_weekday: Mon-Thu weaker, bigger tails).

The script is idempotent and runs every evening from daily_desk.sh:
  --settle   settle every trade whose expiry has passed (or is today after 16:05 ET) and print the running tally
  --entry    settle, then on a Friday at/after 15:30 ET log the signal and, if it qualifies, the paper trades
  add --dry to print without writing.
GEX: reuses today's row in data/paper/gex_fly_signals.csv (written by the GEX fly step a moment earlier); computes it
live via run_gex_fly_paper.compute_gex only if that row is missing.
Logs: data/paper/calm_put_signals.csv, data/paper/calm_put_trades.csv
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import run_gex_fly_paper as gf

ET = ZoneInfo("America/New_York")
OUT = gf.OUT
SIG, TRD = OUT / "calm_put_signals.csv", OUT / "calm_put_trades.csv"
SLIP, COMM = 0.25, 0.0065
TARGETS = {"n10": (0.10, 0.025), "n05": (0.05, 0.015)}
LIVE_LEG = "n05"          # Gabe 2026-09-28: live = the 5-delta put, ONE contract (worst tested week ~-86 bp = ~0.8% of NAV)


def daily_closes(n_days: int = 120) -> pd.Series:
    start = (pd.Timestamp.now(tz=ET).normalize() - pd.Timedelta(days=int(n_days * 1.6))).strftime("%Y-%m-%d")
    h = gf.get("/markets/history", symbol="SPY", interval="daily", start=start).get("history") or {}
    days = h.get("day") or []
    days = [days] if isinstance(days, dict) else days
    return pd.Series({pd.Timestamp(d["date"]): float(d["close"]) for d in days}).sort_index()


def vix_last() -> float:
    try:
        q = gf.get("/markets/quotes", symbols="VIX")["quotes"]["quote"]
        v = float(q.get("last") or 0)
        if v > 0:
            return v
    except Exception:
        pass
    import yfinance as yf
    return float(yf.download("^VIX", period="5d", progress=False, auto_adjust=False)["Close"].squeeze().iloc[-1])


def today_gex(today: str, S: float) -> tuple[float, str]:
    if gf.SIG.exists():
        s = pd.read_csv(gf.SIG)
        row = s[s.date == today]
        if len(row):
            return float(row.iloc[-1].gex_usd_per_1pct), "gex_fly_signals.csv"
    g, _ = gf.compute_gex(S)
    return g, "computed live"


def log_row(path, row: dict, dry: bool) -> None:
    print(("[dry] " if dry else "") + f"{path.name}: {row}")
    if dry:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row])
    if path.exists():
        df = df.reindex(columns=pd.read_csv(path, nrows=0).columns)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def settle(dry: bool) -> None:
    if not TRD.exists():
        print("no calm-put paper trades yet"); return
    t = pd.read_csv(TRD)
    now = datetime.now(ET); today = now.strftime("%Y-%m-%d")
    due = t[t.settled.isna() & ((t.expiry < today) | ((t.expiry == today) & (now.hour * 60 + now.minute >= 16 * 60 + 5)))]
    if len(due):
        closes = daily_closes(30)
    for i, r in due.iterrows():
        ex = pd.Timestamp(r.expiry)
        c = closes[closes.index <= ex]
        if c.empty or c.index[-1] < ex - pd.Timedelta(days=3):
            continue
        S_T = float(c.iloc[-1])
        pnl = r.credit - max(r.strike - S_T, 0.0)
        beta = abs(r.delta) * (S_T - r.S_entry)
        t.loc[i, ["S_settle", "pnl_share", "pnl_bp", "excess_bp", "settled"]] = [
            S_T, round(pnl, 4), round(pnl / r.S_entry * 1e4, 2), round((pnl - beta) / r.S_entry * 1e4, 2), today]
        print(f"settled {r.leg} {r.expiry} K {r.strike}: SPY {S_T:.2f} -> {pnl * 100:+.2f} $/contract ({pnl / r.S_entry * 1e4:+.2f} bp)")
    if not dry:
        t.to_csv(TRD, index=False)
    s = t[t.settled.notna()]
    for leg, g in s.groupby("leg"):
        print(f"running tally {leg}: {len(g)} trades, {g.pnl_share.sum() * 100:+,.0f} $/contract total, mean {g.pnl_bp.mean():+.2f} bp "
              f"(excess {g.excess_bp.mean():+.2f}), win {100 * (g.pnl_share > 0).mean():.0f}%, worst {g.pnl_bp.min():+.1f} bp")


def entry(dry: bool) -> None:
    now = datetime.now(ET); today = now.strftime("%Y-%m-%d")
    if now.weekday() != 4:
        print(f"{today} is not a Friday -- the rule enters on Fridays only"); return
    if now.hour * 60 + now.minute < 15 * 60 + 30:
        sys.exit("too early: the entry step runs from 15:30 ET (the backtest priced at the close)")
    if SIG.exists() and (pd.read_csv(SIG).date == today).any():
        print("calm-put signal already logged today -- not logging twice"); return
    S = gf.spot()
    closes = daily_closes()
    closes = closes[closes.index < pd.Timestamp(today)]
    sma50 = float(pd.concat([closes, pd.Series({pd.Timestamp(today): S})]).tail(50).mean())
    vix = vix_last()
    stress = (S < sma50) and (vix >= 20)
    gex, src = today_gex(today, S)
    qualifies = (not stress) and gex > 0
    print(f"SPY {S:.2f} vs 50SMA {sma50:.2f} | VIX {vix:.2f} -> {'STRESS' if stress else 'CALM'} | GEX {gex / 1e9:+.2f} $bn/1% ({src}) "
          f"-> {'ENTER' if qualifies else 'no trade'}")
    log_row(SIG, dict(date=today, time=now.strftime("%H:%M"), spot=S, sma50=round(sma50, 2), vix=vix, regime="STRESS" if stress else "CALM",
                      gex=round(gex), qualifies=qualifies), dry)
    if not qualifies:
        return
    exps = [e for e in gf.expirations() if 5 <= (pd.Timestamp(e) - pd.Timestamp(today)).days <= 9]
    if not exps:
        print("no expiry 5-9 days out -- skipped"); return
    ex = min(exps, key=lambda e: abs((pd.Timestamp(e) - pd.Timestamp(today)).days - 7))
    c = gf.chain(ex)
    p = c[(c.cp == "P") & c.delta.notna() & (c.bid > 0) & (c.ask >= c.bid)].copy()
    p["ad"] = p.delta.abs()
    for leg, (tgt, tol) in TARGETS.items():
        x = p[(p.ad - tgt).abs() <= tol]
        if x.empty:
            print(f"{leg}: no strike within {tol} of {tgt} delta -- skipped"); continue
        r = x.loc[(x.ad - tgt).abs().idxmin()]
        mid = (r.bid + r.ask) / 2
        credit = mid - SLIP * (r.ask - r.bid) - COMM
        if leg == LIVE_LEG:
            print(f"\n  >>> LIVE ACTION (Gabe 2026-09-28: 5-delta, 1 contract): SELL TO OPEN 1 SPY {ex} {r.strike:g} PUT "
                  f"(delta {r.delta:+.3f}) -- limit at mid {mid:.2f} or better, not below {credit:.2f}; hold to expiry, "
                  f"no stop, no adjustment. <<<\n")
        log_row(TRD, dict(entered=today, time=now.strftime("%H:%M"), leg=leg, expiry=ex, strike=r.strike, delta=round(r.delta, 4),
                          bid=r.bid, ask=r.ask, credit=round(credit, 4), S_entry=S, vix=vix, gex=round(gex),
                          S_settle=None, pnl_share=None, pnl_bp=None, excess_bp=None, settled=None), dry)


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--entry", action="store_true"); g.add_argument("--settle", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    settle(a.dry)
    if a.entry:
        entry(a.dry)


if __name__ == "__main__":
    main()

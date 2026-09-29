#!/usr/bin/env python3
"""Forward paper trade: SPY (from 2026-09-22) and QQQ (from 2026-09-29) 1-day iron butterfly on positive dealer-gamma days.

2026-09-29: QQQ added (close_1d only), gated on QQQ's OWN gamma, after the 2016+ re-cut made the QQQ fly SUPPORTED
(t 3.64; data/studies/gex_fly_2016_recut_2026-09-29.md). Paper only, no size. Every log row carries a `ticker`;
rows written before 2026-09-29 are SPY. open_0dte stays SPY-only.

The trade under test (data/studies/gex_spy_ironfly_2026-09-21.md, PASS at 2x wings): at ~15:50 ET compute SPY net
gamma exposure (GEX) from the live Tradier chain; if it is POSITIVE, sell the ATM straddle in the expiry that settles
on the NEXT trading day and buy wings at K +/- 2 x (straddle mid), nearest listed strike. House fills: shorts at
mid - 25% of the bid-ask, longs at mid + 25%, $0.0065/share/leg. Held to expiry, settled at SPY's close.

Secondary variant (logged for evidence only, never backtested with real quotes): the same fly in the 0DTE expiry
entered at ~09:45 ET on the day after a positive-gamma close ("open_0dte"). See gex_overnight_split_2026-09-21.log:
the overnight gap is ~half the day's variance and half the edge, so expectations are modest.

GEX = sum over every listed expiry and strikes within +/-20% of spot of (call OI x call gamma - put OI x put gamma)
x 100 x S^2 x 0.01 (the naive sign used in the backtest). ⚠ The backtest's GEX came from options_daily_v3 vendor
gamma; this uses Tradier (ORATS) gamma. Same definition, different vendor, and there are no overlapping dates to
compare, so the first weeks double as a sanity check of the sign's behaviour (it should be positive ~40-50% of days).

Modes (from repo root, TRADIER_API_KEY set):
  run_gex_fly_paper.py --close    ~15:50 ET: settle due trades, compute GEX per ticker (--tickers, default SPY,QQQ),
                                  log the signal, paper-enter close_1d
  run_gex_fly_paper.py --open     ~09:45 ET: settle due trades, paper-enter open_0dte if the last close signal was positive
  run_gex_fly_paper.py --settle   settle any expired trades and print the running tally
  add --dry to print without writing the logs.
Logs: data/paper/gex_fly_signals.csv, data/paper/gex_fly_trades.csv
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

ET = ZoneInfo("America/New_York")
API = "https://api.tradier.com/v1"
OUT = Path(__file__).resolve().parent / "data" / "paper"
SIG, TRD = OUT / "gex_fly_signals.csv", OUT / "gex_fly_trades.csv"
SLIP, COMM, WING = 0.25, 0.0065, 2.0
TICKERS = ("SPY", "QQQ")


def get(path: str, **params):
    h = {"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"}
    for attempt in range(4):
        r = requests.get(API + path, params=params, headers=h, timeout=20)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def spot(tk: str = "SPY") -> float:
    q = get("/markets/quotes", symbols=tk)["quotes"]["quote"]
    return float(q["last"])


def chain(tk: str, expiry: str) -> pd.DataFrame:
    o = (get("/markets/options/chains", symbol=tk, expiration=expiry, greeks="true").get("options") or {}).get("option") or []
    rows = [dict(strike=x["strike"], cp=x["option_type"][0].upper(), bid=x.get("bid") or 0.0, ask=x.get("ask") or 0.0,
                 oi=x.get("open_interest") or 0, delta=(x.get("greeks") or {}).get("delta"),
                 gamma=(x.get("greeks") or {}).get("gamma")) for x in o]
    return pd.DataFrame(rows)


def expirations(tk: str = "SPY") -> list[str]:
    return get("/markets/options/expirations", symbol=tk, includeAllRoots="true")["expirations"]["date"]


def compute_gex(tk: str, S: float) -> tuple[float, int]:
    tot, n = 0.0, 0
    for e in expirations(tk):
        c = chain(tk, e)
        if c.empty:
            continue
        c = c[(c.strike >= 0.8 * S) & (c.strike <= 1.2 * S) & c.gamma.notna()]
        sgn = c.cp.map({"C": 1.0, "P": -1.0})
        tot += float((sgn * c.oi * c.gamma).sum()) * 100 * S * S * 0.01
        n += 1
        time.sleep(0.3)
    return tot, n


def price_fly(tk: str, expiry: str, S: float) -> dict | None:
    c = chain(tk, expiry)
    if c.empty:
        return None
    c["mid"] = (c.bid + c.ask) / 2; c["ba"] = c.ask - c.bid
    calls = c[c.cp == "C"].set_index("strike").sort_index(); puts = c[c.cp == "P"].set_index("strike").sort_index()
    ks = calls.index.intersection(puts.index)
    cd = calls.loc[ks].dropna(subset=["delta"])
    if cd.empty:
        return None
    K = (cd.delta - 0.5).abs().idxmin()
    smid = calls.loc[K, "mid"] + puts.loc[K, "mid"]
    cw = calls[(calls.index > K) & (calls.ask > 0)]; pw = puts[(puts.index < K) & (puts.ask > 0)]
    if cw.empty or pw.empty or smid <= 0:
        return None
    kc = cw.index[abs(cw.index - (K + WING * smid)).argmin()]; kp = pw.index[abs(pw.index - (K - WING * smid)).argmin()]
    sell = lambda r: r.mid - SLIP * r.ba; buy = lambda r: r.mid + SLIP * r.ba
    credit = sell(calls.loc[K]) + sell(puts.loc[K]) - buy(calls.loc[kc]) - buy(puts.loc[kp]) - 4 * COMM
    width = max(kc - K, K - kp)
    return dict(expiry=expiry, S_entry=S, K=K, k_call_wing=kc, k_put_wing=kp, straddle_mid=round(smid, 3),
                credit=round(credit, 4), max_risk=round(width - credit, 4))


def prev_session(today: str) -> str:
    """The last completed SPY trading day before today (from Tradier daily history; handles weekends and holidays)."""
    start = (pd.Timestamp(today) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    h = get("/markets/history", symbol="SPY", interval="daily", start=start, end=today).get("history") or {}
    days = h.get("day") or []
    days = [days] if isinstance(days, dict) else days
    past = sorted(d["date"] for d in days if d["date"] < today)
    if not past:
        sys.exit("could not determine the previous session from Tradier history")
    return past[-1]


def settle(dry: bool) -> None:
    if not TRD.exists():
        return
    t = pd.read_csv(TRD)
    t["ticker"] = t.get("ticker", pd.Series("SPY", index=t.index)).fillna("SPY")
    now = datetime.now(ET); today = now.strftime("%Y-%m-%d")
    due = t[t.settled.isna() & ((t.expiry < today) | ((t.expiry == today) & (now.hour * 60 + now.minute >= 16 * 60 + 5)))]
    for i, r in due.iterrows():
        h = get("/markets/history", symbol=r.ticker, interval="daily", start=r.expiry, end=r.expiry).get("history")
        day = (h or {}).get("day")
        if isinstance(day, list):
            day = day[0] if day else None
        if not day:
            if r.expiry == today:
                q = get("/markets/quotes", symbols=r.ticker)["quotes"]["quote"]; S_t = float(q["last"])
            else:
                continue
        else:
            S_t = float(day["close"])
        pay = min(max(S_t - r.K, 0), r.k_call_wing - r.K) + min(max(r.K - S_t, 0), r.K - r.k_put_wing)
        pnl = r.credit - pay
        t.loc[i, ["S_settle", "pnl_usd", "ret_risk_pct", "settled"]] = [S_t, round(pnl * 100, 2), round(pnl / r.max_risk * 100, 2), today]
        print(f"settled {r.ticker} {r.variant} {r.expiry}: {r.ticker} {S_t:.2f} vs K {r.K} -> {pnl * 100:+.2f} $/fly ({pnl / r.max_risk * 100:+.1f}% on risk)")
    if not dry:
        t.to_csv(TRD, index=False)
    s = t[t.settled.notna()]
    if "valid" in t.columns:                            # rows marked valid=False (e.g. a stale signal) stay out of the tally
        bad = s[s.valid.astype(str).str.lower() == "false"]
        if len(bad):
            print(f"excluded from the tally (valid=False): {len(bad)} -- " + "; ".join(f"{r.entered} {r.variant}: {r.note}" for r in bad.itertuples()))
        s = s[s.valid.astype(str).str.lower() != "false"]
    if len(s):
        for (tk, v), g in s.groupby(["ticker", "variant"]):
            print(f"running tally {tk} {v}: {len(g)} flies, {g.pnl_usd.sum():+,.0f} $, mean {g.ret_risk_pct.mean():+.2f}% on risk, win {100 * (g.pnl_usd > 0).mean():.0f}%")


def log_row(path: Path, row: dict, dry: bool) -> None:
    print(("[dry] " if dry else "") + f"{path.name}: {row}")
    if dry:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row])
    if path.exists():                                   # align to the file's header (columns were added 2026-09-28)
        head = pd.read_csv(path, nrows=0).columns
        if set(df.columns) - set(head):                 # a new column (e.g. ticker, 2026-09-29): rewrite with it
            old = pd.read_csv(path)
            pd.concat([old, df], ignore_index=True).to_csv(path, index=False)
            return
        df = df.reindex(columns=head)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def close_step(tk: str, today: str, now: datetime, dry: bool) -> None:
    """Log tk's close GEX signal and, on positive gamma, paper-enter the 1-day 2x fly. Idempotent per (date, ticker)."""
    if SIG.exists():
        s = pd.read_csv(SIG)
        s_tk = s.get("ticker", pd.Series("SPY", index=s.index)).fillna("SPY")
        if ((s.date == today) & (s_tk == tk)).any():
            print(f"{tk}: close signal already logged today -- not logging twice"); return
    S = spot(tk)
    gex, n = compute_gex(tk, S)
    sign = "POSITIVE" if gex > 0 else "negative"
    log_row(SIG, dict(date=today, time=now.strftime("%H:%M"), ticker=tk, spot=S, gex_usd_per_1pct=round(gex), expiries=n, sign=sign), dry)
    print(f"{tk} {S:.2f} | net GEX {gex / 1e9:+.2f} $bn per 1% | {sign}")
    nxt = [e for e in expirations(tk) if e > today]
    if gex > 0 and nxt:
        f = price_fly(tk, nxt[0], S)
        if f and f["credit"] > 0:
            log_row(TRD, dict(entered=today, time=now.strftime("%H:%M"), ticker=tk, variant="close_1d", gex=round(gex), **f,
                              S_settle=None, pnl_usd=None, ret_risk_pct=None, settled=None), dry)
        else:
            print(f"{tk}: positive gamma but no valid fly quote -- skipped")
    elif gex <= 0:
        print(f"{tk}: negative gamma: no trade (the short fly lost on these days in the backtest)")


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--close", action="store_true"); g.add_argument("--open", action="store_true"); g.add_argument("--settle", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--tickers", default=",".join(TICKERS), help="close_1d tickers (default SPY,QQQ)")
    a = ap.parse_args()
    now = datetime.now(ET); today = now.strftime("%Y-%m-%d")
    settle(a.dry)
    if a.settle:
        return
    if now.weekday() >= 5:
        sys.exit("weekend: nothing to enter")
    mins = now.hour * 60 + now.minute
    if a.close:
        if mins < 15 * 60 + 30:
            sys.exit("too early: the close step runs from 15:30 ET (the backtest priced at the close)")
        for tk in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
            close_step(tk, today, now, a.dry)
    if a.open:
        if not (9 * 60 + 40 <= mins <= 10 * 60 + 30):
            sys.exit("the open step runs 09:40-10:30 ET")
        if TRD.exists() and ((pd.read_csv(TRD).entered == today) & (pd.read_csv(TRD).variant == "open_0dte")).any():
            print("0DTE already logged today"); return
        if not SIG.exists():
            sys.exit("no close signal logged yet")
        s = pd.read_csv(SIG)
        s = s[s.get("ticker", pd.Series("SPY", index=s.index)).fillna("SPY") == "SPY"]   # open_0dte is SPY-only
        prev = s[s.date < today].tail(1)
        last = prev_session(today)
        if not prev.empty and prev.iloc[0].date != last:
            # 2026-09-28: a missed close run (no desk on 9/25) let Monday's open trade key off Thursday's signal
            print(f"last close signal is from {prev.iloc[0].date}, not the previous session {last} -> stale, no 0DTE entry")
            return
        if prev.empty or prev.iloc[0].sign != "POSITIVE":
            print(f"last close signal: {'none' if prev.empty else prev.iloc[0].sign} -> no 0DTE entry")
            return
        if today not in expirations():
            print("no SPY expiry today -> no 0DTE entry"); return
        S = spot(); f = price_fly("SPY", today, S)
        if f and f["credit"] > 0:
            log_row(TRD, dict(entered=today, time=now.strftime("%H:%M"), ticker="SPY", variant="open_0dte", gex=prev.iloc[0].gex_usd_per_1pct, **f,
                              S_settle=None, pnl_usd=None, ret_risk_pct=None, settled=None), a.dry)


if __name__ == "__main__":
    main()

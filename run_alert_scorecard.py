#!/usr/bin/env python3
"""Score a day's alerts: alert price -> stop hit (loss to the stop) or close, with every tag
and the index state, so the sample accumulates before any gate is tuned.

  PYTHONPATH=src .venv/bin/python3 run_alert_scorecard.py            # today's session
  PYTHONPATH=src .venv/bin/python3 run_alert_scorecard.py 2026-09-09
  PYTHONPATH=src .venv/bin/python3 run_alert_scorecard.py 2026-09-09 --oop   # the hidden out-of-play alerts
                                                                   (add --replay to score a replay's file)

Reads data/journal/alerts/<date>.json (what the monitor published), writes
data/watchlist/logs/alert_scorecard_<date>.csv and appends to alert_scorecard_all.csv
(deduped on date+time+symbol+kind). Prints the splits that matter.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from lib.tradier.get_daily_history import get_intraday_bars
from lib.tradier.tradier_client_wrapper import TradierClient

LOGS = Path("data/watchlist/logs")
KEEP = ["date", "t", "symbol", "kind", "side", "price", "stop", "stop_pct", "stop_adr", "tag", "level", "below_ema9", "adr_vs_21", "vol_pace",
        "gap_adr", "light_vol", "spy_vs_vwap", "qqq_vs_vwap", "index_above", "gated", "rs_spy", "rs_group", "group", "rs_leader", "level_type", "day_state", "out_of_play"]


async def main() -> int:
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    oop, replay = "--oop" in sys.argv, "--replay" in sys.argv
    d = args[0] if args else date.today().isoformat()
    if oop:   # the out-of-play alerts the monitor saved but never showed
        src = LOGS / f"alerts_oop_{d}{'_replay' if replay else ''}.jsonl"
        if not src.exists():
            print(f"no out-of-play file {src}"); return 1
        alerts = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    else:
        src = Path(f"data/journal/alerts/{d}.json")
        if not src.exists():
            print(f"no alerts file for {d}"); return 1
        doc = json.loads(src.read_text()); alerts = doc.get("alerts", [])
    if not alerts:
        print(f"{d}: no alerts"); return 0
    sem = asyncio.Semaphore(2); rows = []
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        async def one(a):
            async with sem:
                try:
                    m = await get_intraday_bars(a["symbol"], date.fromisoformat(d), interval="1min", client=c)
                except Exception:  # noqa: BLE001
                    m = None
            if m is None:
                return
            t = pd.Timestamp(f"{d} {a['t']}"); after = m.loc[m.index > t]
            close = float(m["close"].iloc[-1]); lo = float(after["low"].min()) if len(after) else close
            hi = float(after["high"].max()) if len(after) else close
            short = a.get("side") == "short"
            stopped = (hi >= a["stop"]) if short else (lo <= a["stop"])
            raw = (a["stop"] / a["price"] - 1) * 100 if stopped else (close / a["price"] - 1) * 100
            res = -raw if short else raw
            rows.append({**{k: a.get(k) for k in KEEP if k != "date"}, "date": d, "close": round(close, 2),
                         "max_up_pct": round((hi / a["price"] - 1) * 100, 2), "stopped": stopped, "result_pct": round(res, 2)})
        await asyncio.gather(*(one(a) for a in alerts))
    df = pd.DataFrame(rows)[["date"] + [k for k in KEEP if k != "date"] + ["close", "max_up_pct", "stopped", "result_pct"]]
    df = df.sort_values("t")
    LOGS.mkdir(parents=True, exist_ok=True)
    tag = "_oop" if oop else ""
    df.to_csv(LOGS / f"alert_scorecard{tag}_{d}.csv", index=False)
    allp = LOGS / f"alert_scorecard{tag}_all.csv"
    full = pd.concat([pd.read_csv(allp), df]) if allp.exists() else df
    full = full.drop_duplicates(subset=["date", "t", "symbol", "kind"], keep="last").sort_values(["date", "t"])
    full.to_csv(allp, index=False)
    pd.set_option("display.width", 220)
    print(df[["t", "symbol", "kind", "side", "price", "stop", "stop_adr", "tag", "level", "adr_vs_21", "vol_pace", "spy_vs_vwap", "gated", "stopped", "result_pct"]].to_string(index=False))
    n_win = int((df.result_pct > 0).sum())
    print(f"\n{d}{' OUT-OF-PLAY' if oop else ''}: {len(df)} alerts | winners {n_win} | stopped {int(df.stopped.sum())} | avg {df.result_pct.mean():+.2f}%")
    for name, mask in [("SPY above VWAP", df.index_above == True), ("UR", df.kind == "UR"), ("ORB9", df.kind == "ORB9"),  # noqa: E712
                       ("BIR", df.kind == "BIR"), ("FBO", df.kind == "FBO"),
                       ("not gated", df.gated != True)]:  # noqa: E712
        a = df[mask]
        if len(a):
            print(f"  {name:16s} n={len(a):2d} avg {a.result_pct.mean():+.2f}% win {int((a.result_pct > 0).sum())}")
    print(f"cumulative: {len(full)} alerts across {full.date.nunique()} days | avg {full.result_pct.mean():+.2f}% | "
          f"SPY-above avg {full[full.index_above == True].result_pct.mean():+.2f}% (n={int((full.index_above == True).sum())}) "  # noqa: E712
          f"vs below {full[full.index_above == False].result_pct.mean():+.2f}% (n={int((full.index_above == False).sum())})")  # noqa: E712
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

#!/usr/bin/env python3
"""Account give-back alarm (designed 2026-09-11, built 2026-09-21).

Watches the account's live day P&L from IBKR (read-only: reqPnL, no orders possible) and chimes when the day's
gain is being given back:

  GIVE-BACK     day P&L has fallen >= $GIVEBACK (default $500) below the day's high, once the high is > $0
  40% OFF HIGH  the high is > $BIG_HIGH (default $1,000) and day P&L is <= (1 - PCT) x high (default 40% off)

Each stage fires once, then re-arms only after a NEW high at least $GIVEBACK above the high it fired from (so a
chopping P&L doesn't chime every minute). This is information, not an exit rule: our studies say trims, locks and
tightening cost money on the swing book (profit_lock study 2026-09-20), so the alarm is for noticing a reversal and
checking positions against their plans, not for selling automatically.

⚠ The high only counts while this runs: IBKR does not give an intraday history of day P&L. The high and fired stages
are saved to data/watchlist/logs/pnl_alarm_state_<date>.json, so a restart the same day keeps them. Start it at the
open for a true session high.

Delivery: terminal line + bell + chime (Glass), log data/watchlist/logs/pnl_alarm_<date>.log, heartbeat every 5 min.
No phone push, no macOS dialogs (Gabe, 2026-09-08 / 09-10).

Usage (from repo root; TWS/Gateway running with the API enabled):
  .venv/bin/python3 run_pnl_alarm.py                     # live TWS 7496, defaults
  .venv/bin/python3 run_pnl_alarm.py --giveback 400 --big-high 1500 --pct 0.35
  IB_PORT=4002 .venv/bin/python3 run_pnl_alarm.py        # paper Gateway
  .venv/bin/python3 run_pnl_alarm.py --simulate          # replay a synthetic P&L path through the logic, no IBKR
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent
LOGS = REPO / "data" / "watchlist" / "logs"
ET = ZoneInfo("America/New_York")
CHIME = "/System/Library/Sounds/Glass.aiff"


@dataclass
class State:
    date: str
    high: float = -math.inf
    high_t: str = ""
    fired: dict = field(default_factory=dict)      # stage -> the high it fired from
    last: float = math.nan


class Alarm:
    def __init__(self, giveback: float, big_high: float, pct: float, sound: bool, day: str, persist: bool = True):
        self.giveback, self.big_high, self.pct, self.sound, self.persist = giveback, big_high, pct, sound, persist
        LOGS.mkdir(parents=True, exist_ok=True)
        self.state_path = LOGS / f"pnl_alarm_state_{day}.json"
        self.log_path = LOGS / f"pnl_alarm_{day}.log"
        self.st = State(date=day)
        if persist and self.state_path.exists():
            d = json.loads(self.state_path.read_text())
            self.st = State(**{**asdict(self.st), **d, "high": float(d["high"]) if d.get("high") is not None else -math.inf,
                                "last": float(d["last"]) if d.get("last") is not None else math.nan})
            self.say(f"resumed today's state: high {self._m(self.st.high)} at {self.st.high_t}, fired {self.st.fired or 'none'}")

    @staticmethod
    def _m(x: float) -> str:
        return "n/a" if not math.isfinite(x) else f"{x:+,.0f}"

    def say(self, msg: str, alarm: bool = False) -> None:
        line = f"[{datetime.now(ET):%H:%M:%S}] {msg}"
        print(("\a" if alarm else "") + line, flush=True)
        with open(self.log_path, "a") as f:
            f.write(line + "\n")
        if alarm and self.sound:
            subprocess.Popen(["afplay", CHIME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _save(self) -> None:
        if self.persist:
            self.state_path.write_text(json.dumps({**asdict(self.st), "high": self.st.high if math.isfinite(self.st.high) else None,
                                                   "last": self.st.last if math.isfinite(self.st.last) else None}))

    def update(self, pnl: float, t: str | None = None) -> list[str]:
        """Feed one day-P&L reading; returns the stages that fired (for tests)."""
        if pnl is None or not math.isfinite(pnl):
            return []
        t = t or f"{datetime.now(ET):%H:%M:%S}"
        st, fired = self.st, []
        st.last = pnl
        if pnl > st.high:
            st.high, st.high_t = pnl, t
            for stage, from_high in list(st.fired.items()):      # re-arm after a meaningfully new high
                if st.high >= from_high + self.giveback:
                    del st.fired[stage]
                    self.say(f"re-armed {stage}: new high {self._m(st.high)} is >= ${self.giveback:,.0f} above the {self._m(from_high)} it fired from")
            self._save()
        dd = st.high - pnl
        if "GIVE-BACK" not in st.fired and st.high > 0 and dd >= self.giveback:
            st.fired["GIVE-BACK"] = st.high; fired.append("GIVE-BACK")
            self.say(f"⚠ GIVE-BACK: day P&L {self._m(pnl)} is ${dd:,.0f} below today's high {self._m(st.high)} ({st.high_t}). "
                     f"Check each position against its plan; don't sell just to lock the day (profit-lock study).", alarm=True)
        if "40% OFF HIGH" not in st.fired and st.high > self.big_high and pnl <= (1 - self.pct) * st.high:
            st.fired["40% OFF HIGH"] = st.high; fired.append("40% OFF HIGH")
            self.say(f"⚠⚠ 40% OFF HIGH: day P&L {self._m(pnl)} has given back {dd / st.high * 100:.0f}% of today's high "
                     f"{self._m(st.high)} ({st.high_t}).", alarm=True)
        if fired:
            self._save()
        return fired

    def heartbeat(self) -> None:
        st = self.st
        self.say(f"day P&L {self._m(st.last)} | high {self._m(st.high)} ({st.high_t}) | off high "
                 f"{'n/a' if not (math.isfinite(st.high) and math.isfinite(st.last)) else f'${st.high - st.last:,.0f}'} | "
                 f"armed: {', '.join(s for s in ('GIVE-BACK', '40% OFF HIGH') if s not in st.fired) or 'none'}")


def simulate(args) -> None:
    """Synthetic path through the logic: rise to +1,800, fall, re-high, fall again."""
    a = Alarm(args.giveback, args.big_high, args.pct, sound=False, day="SIMULATION", persist=False)
    path = [0, 300, 900, 1500, 1800, 1700, 1400, 1250, 1100, 1000, 900, 1300, 1900, 2400, 2350, 1800, 1300, 900]
    for i, p in enumerate(path):
        f = a.update(p, t=f"step{i:02d}")
        print(f"   step {i:02d} pnl {p:+6,}  high {a.st.high:+6,.0f}  fired {f or '-'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--giveback", type=float, default=500.0, help="$ below the day's high that fires GIVE-BACK (default 500)")
    ap.add_argument("--big-high", type=float, default=1000.0, help="the 40%%-off stage needs a high above this (default 1000)")
    ap.add_argument("--pct", type=float, default=0.40, help="fraction of the high given back for the second stage (default 0.40)")
    ap.add_argument("--heartbeat", type=int, default=5, help="minutes between status lines (default 5)")
    ap.add_argument("--until", default="16:00", help="ET time to stop (default 16:00)")
    ap.add_argument("--no-sound", action="store_true", help="terminal bell only, no chime")
    ap.add_argument("--client-id", type=int, default=int(os.environ.get("IB_CLIENT_ID", 61)))
    ap.add_argument("--simulate", action="store_true", help="run the logic on a synthetic path, no IBKR")
    args = ap.parse_args()
    if args.simulate:
        return simulate(args)

    from ib_async import IB
    port = int(os.environ.get("IB_PORT", 7496))
    day = datetime.now(ET).strftime("%Y-%m-%d")
    alarm = Alarm(args.giveback, args.big_high, args.pct, sound=not args.no_sound, day=day)
    ib = IB()
    try:
        ib.connect(os.environ.get("IB_HOST", "127.0.0.1"), port, clientId=args.client_id, readonly=True, timeout=15)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"could not connect to TWS/Gateway on port {port} (clientId {args.client_id}): {e!r}. "
                 f"Is TWS open with the API enabled? Another app on clientId {args.client_id}? Try --client-id.")
    acct = ib.managedAccounts()[0]
    pnl = ib.reqPnL(acct)
    alarm.say(f"watching account {acct} day P&L (read-only, port {port}) | GIVE-BACK at ${args.giveback:,.0f} off the high, "
              f"40%-OFF stage once the high > ${args.big_high:,.0f} | until {args.until} ET")
    ib.pnlEvent += lambda p: alarm.update(p.dailyPnL)
    last_hb = datetime.now(ET)
    stop_hm = args.until
    try:
        while True:
            ib.sleep(1)
            now = datetime.now(ET)
            if (now - last_hb).total_seconds() >= args.heartbeat * 60:
                alarm.heartbeat(); last_hb = now
            if now.strftime("%H:%M") >= stop_hm:
                alarm.say(f"{stop_hm} ET reached, stopping"); break
            if not ib.isConnected():
                alarm.say("⚠ lost the TWS connection -- the alarm is NOT watching. Restart it.", alarm=True); break
    except KeyboardInterrupt:
        pass
    finally:
        alarm.heartbeat()
        alarm.say(f"session summary: high {alarm._m(alarm.st.high)} at {alarm.st.high_t}, last {alarm._m(alarm.st.last)}, "
                  f"fired {alarm.st.fired or 'none'}")
        if ib.isConnected():
            ib.cancelPnL(acct, "")
            ib.disconnect()


if __name__ == "__main__":
    main()

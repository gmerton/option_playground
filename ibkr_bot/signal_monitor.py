#!/usr/bin/env python3
"""
Combined live signal monitor (alert-only) for three intraday patterns.

Watches one or more symbols on live 1-minute bars and notifies you the moment
any of these fire. NO orders are placed -- this is a heads-up tool.

  1. EMA cross  -- 9 EMA crosses the 20 EMA (the original v1 signal).
  2. MFR        -- Morning Flush Reversal: a sharp morning gap/flush deep below
                   VWAP into oversold, then a reclaim. Buy-the-reclaim alert.
  3. PHB        -- Power Hour Breakout: the validated directional-ignition
                   conjunction in the afternoon window. Long heads-up.

The detection logic is shared with the backtests on purpose:
  - indicators come from characterize.add_indicators (same EMAs/VWAP/RSI), and
  - PHB reuses power_hour_trigger.find_trigger with the precision filter on,
so a live alert means the same thing a backtest "fire" meant.

Each signal fires at most once per symbol per session (EMA crosses can recur,
since a cross is inherently a repeating event). Both MFR and PHB are one-shot.

Usage:
  .venv/bin/python3 ibkr_bot/signal_monitor.py PL CIEN SPY
  .venv/bin/python3 ibkr_bot/signal_monitor.py --signals mfr,phb PL CIEN
  .venv/bin/python3 ibkr_bot/signal_monitor.py --mfr-trigger rsi40 PL

Env (via conn.py): IB_HOST, IB_PORT (default 4002 paper), IB_CLIENT_ID,
IB_ALLOW_LIVE. Connects to the paper account. Ctrl-C stops.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime

import pandas as pd
from ib_async import Stock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators  # noqa: E402
from conn import connect_ib, connect_ib_with_retry  # noqa: E402
import power_hour_trigger as pht  # noqa: E402
import vcb  # noqa: E402
import signal_store  # noqa: E402

LOG_PATH = os.path.join(HERE, "alerts.log")

# --- MFR (Morning Flush Reversal) gate, from patterns/morning_flush_reversal.md.
# Thresholds are PROVISIONAL (the pattern doc is N=1, PL 2026-05-29). Kept tight
# on the GATE per the "precision over recall" preference -- we only ever consider
# a real flush; the human judges the reclaim.
#
# Gate anchor: % DOWN FROM OPEN + oversold RSI are the REQUIRED conditions; being
# deep below VWAP is reported as context but NOT required. Rationale: on an
# open-gap flush the selloff can happen so fast that session-VWAP is dragged down
# with price, leaving the low only modestly below VWAP even on a violent drop --
# anchoring on the open keeps the gate honest for that case. (PL's low at 10:26
# was -8.8% from open, -4.3% vs VWAP, RSI 25 -- it satisfies both anyway.)
# ⚠️ Still N=1 and not out-of-sample validated; treat MFR alerts as experimental.
MFR_MORNING_END = "11:00"   # the flush low must occur this early
MFR_MIN_DROP = -5.0         # REQUIRED: open -> session low, percent (PL was -8.8%)
MFR_MAX_RSI = 30            # REQUIRED: RSI at the low at/below this (PL was 25)
MFR_NOTE_VWAP_DIST = -3.0   # context only: flag "deep below VWAP" if low <= this


class _HistCancelFilter(logging.Filter):
    """Drop the benign 'Error 162 ... query cancelled' that ib_async logs every
    time we cancelHistoricalData on a symbol dropped from the watchlist. Real
    162 errors (anything not a cancellation) still pass through."""
    def filter(self, record: logging.LogRecord) -> bool:
        m = record.getMessage()
        return not (m.startswith("Error 162,") and "cancelled" in m.lower())


def _quiet_hist_cancel() -> None:
    logging.getLogger("ib_async.wrapper").addFilter(_HistCancelFilter())


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _mac_alert(title: str, msg: str) -> None:
    """Non-blocking macOS dialog + sound (same plumbing as ema_monitor).

    macOS-only: on Linux/headless (e.g. the AWS deployment) there is no
    desktop to draw on -- the signal still reaches you via the store/web UI
    and alerts.log, so we just no-op here instead of crashing on missing
    osascript/afplay.
    """
    if sys.platform != "darwin":
        return
    safe_msg = msg.replace("\\", "").replace('"', "'")
    safe_title = title.replace("\\", "").replace('"', "'")
    script = (
        'tell application "System Events" to display dialog '
        f'"{safe_msg}" with title "{safe_title}" '
        'buttons {"Dismiss"} default button "Dismiss" with icon caution'
    )
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _alert(symbol: str, tag: str, msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}]  [{tag}] {symbol}: {msg}"
    bar = "=" * 72
    print(f"\a\n{bar}\n  {line}\n{bar}\n", flush=True)
    _log(line)
    try:
        signal_store.add_signal(symbol, tag, msg)
    except Exception as e:                       # never let the UI sink kill a signal
        print(f"  ! signal_store write failed: {e}", flush=True)
    _mac_alert(f"{symbol} {tag}", f"{symbol}: {msg}")


def _hhmm(sess: pd.DataFrame) -> pd.Series:
    return sess["time"].dt.strftime("%H:%M")


# --------------------------------------------------------------------------
# Detectors. Each takes the indicator-enriched closed-bar session and returns
# an alert message (str) if the signal fires on the just-closed (last) bar,
# else None. They are pure reads of `sess`; one-shot dedup is handled by caller.
# --------------------------------------------------------------------------

def detect_ema(sess: pd.DataFrame) -> str | None:
    """9/20 EMA cross on the just-closed bar (matches characterize's EMAs)."""
    if len(sess) < 2:
        return None
    spread = sess["ema9"] - sess["ema20"]
    prev, cur = spread.iloc[-2], spread.iloc[-1]
    last = sess.iloc[-1]
    vw = last["vwap"]
    side = "above" if last["close"] > vw else "below"
    ctx = f"price {last['close']:.2f}, VWAP {vw:.2f} (px {side})"
    if prev <= 0 < cur:
        return f"9 EMA crossed ABOVE 20 EMA  |  {ctx}  (bar {_hhmm(sess).iloc[-1]})"
    if prev >= 0 > cur:
        return f"9 EMA crossed BELOW 20 EMA  |  {ctx}  (bar {_hhmm(sess).iloc[-1]})"
    return None


def detect_mfr(sess: pd.DataFrame, trigger: str) -> str | None:
    """Morning Flush Reversal: valid morning flush gate + reclaim on the last bar.

    Gate (required): session low is in the morning, >= MFR_MIN_DROP below the
    OPEN, and oversold (RSI <= MFR_MAX_RSI at the low). Being deep below VWAP is
    reported as context but not required. Trigger ('vwap' = close reclaims VWAP,
    the cleaner confirmation; 'rsi40' = RSI crosses back up through 40, earlier)
    must occur on the just-closed bar and after the flush low.
    """
    if len(sess) < 3:
        return None
    hhmm = _hhmm(sess)
    lo_i = sess["low"].idxmin()
    if hhmm.iloc[lo_i] > MFR_MORNING_END:      # flush must be a morning event
        return None
    last_i = sess.index[-1]
    if last_i <= lo_i:                          # reclaim must come after the low
        return None

    o = sess["open"].iloc[0]
    lo = sess["low"].iloc[lo_i]
    vwap_at_low = sess["vwap"].iloc[lo_i]
    rsi_at_low = sess["rsi"].iloc[lo_i]
    drop = (lo / o - 1) * 100
    vwap_dist = (lo / vwap_at_low - 1) * 100 if vwap_at_low else 0
    if not (drop <= MFR_MIN_DROP and rsi_at_low <= MFR_MAX_RSI):
        return None
    deep = " deep-below-VWAP" if vwap_dist <= MFR_NOTE_VWAP_DIST else ""

    cur, prev = sess.iloc[-1], sess.iloc[-2]
    if trigger == "rsi40":
        fired = prev["rsi"] <= 40 < cur["rsi"]
        what = "RSI reclaimed 40"
    else:  # "vwap"
        fired = prev["close"] <= prev["vwap"] and cur["close"] > cur["vwap"]
        what = "close reclaimed VWAP"
    if not fired:
        return None

    off_low = (cur["close"] / lo - 1) * 100
    return (f"MORNING FLUSH RECLAIM -- {what} @ {hhmm.iloc[-1]}  |  "
            f"flush low {lo:.2f}@{hhmm.iloc[lo_i]} ({drop:+.1f}% from open, "
            f"{vwap_dist:+.1f}% vs VWAP{deep}, RSI {rsi_at_low:.0f}); "
            f"now {cur['close']:.2f} (+{off_low:.1f}% off low)")


def detect_phb(sess: pd.DataFrame) -> str | None:
    """Power Hour Breakout: the validated ignition conjunction, fresh this bar.

    Delegates to power_hour_trigger.find_trigger (precision filter on) so the
    live criteria are identical to the backtest. Only alerts when the trigger
    bar IS the just-closed bar.
    """
    trig = pht.find_trigger(sess)
    if not trig:
        return None
    if trig["i"] != sess.index[-1]:            # not fresh -- fired earlier
        return None
    r = sess.iloc[-1]
    vwap_dist = (r["close"] / r["vwap"] - 1) * 100
    return (f"POWER-HOUR IGNITION @ {trig['time']}  |  entry {trig['px']:.2f}  "
            f"(+{vwap_dist:.1f}% vs VWAP, RSI {r['rsi']:.0f}); "
            f"intraday-flat -- exit by close, VWAP stop")


def _index_ret_series(df: pd.DataFrame) -> pd.Series:
    """Index ret-from-open per bar (for VCB relative strength), indexed by time."""
    o = df["open"].iloc[0]
    return pd.Series((df["close"] / o - 1).values, index=pd.to_datetime(df["time"]))


def detect_vcb(df_raw: pd.DataFrame, idx_ret: pd.Series | None) -> str | None:
    """Volatility-Contraction Breakout, fresh this bar (mirrors vcb.find_vcb).

    Builds the 1-min decision frame with relative strength vs the index and
    delegates to vcb.find_vcb so the live gate/trigger are identical to the
    backtest. The RS gate needs the index feed; without it we don't fire (a VCB
    without the selection gate is just a noisy breakout). Alerts only when the
    trigger bar IS the just-closed bar. ADR/no-stop is an execution choice (see
    patterns/volatility_contraction_breakout.md) -- not part of the alert.
    """
    if idx_ret is None or idx_ret.empty:
        return None
    d = vcb.decision_frame(df_raw, 1, idx_ret)
    trig = vcb.find_vcb(d)
    if not trig or trig["i"] != d.index[-1]:       # not fresh -- fired earlier / never
        return None
    rs = trig.get("rs")
    rss = f", RS {rs:+.1f}pts vs idx" if rs is not None else ""
    return (f"VCB BREAKOUT @ {trig['time']}  |  entry {trig['px']:.2f}  "
            f"(OR-high {trig['or_high']:.2f}, vol {trig['vexp']:.1f}x, "
            f"RSI {trig['rsi']:.0f}{rss}); intraday-flat -- exit by close, wide/ADR stop")


# --------------------------------------------------------------------------

class SymbolState:
    """Per-symbol one-shot dedup. EMA crosses recur (dedup per bar); MFR/PHB/VCB
    fire once per session."""
    def __init__(self) -> None:
        self.last_bar = None       # last processed closed-bar timestamp
        self.fired = set()         # {"mfr", "phb", "vcb"}
        self.last_ema_bar = None   # bar time of the last EMA alert


def _bars_to_df(closed) -> pd.DataFrame:
    df = pd.DataFrame([{
        "time": b.date, "open": b.open, "high": b.high, "low": b.low,
        "close": b.close, "volume": b.volume, "wap": b.average,
    } for b in closed])
    df["time"] = pd.to_datetime(df["time"])
    return df


def make_handler(state: dict, signals: set, mfr_trigger: str,
                 index_state: dict, index_symbol: str):
    def on_bar_update(bars, has_new_bar: bool) -> None:
        if not has_new_bar or len(bars) < 2:
            return
        sym = bars.contract.symbol
        closed = bars[:-1]                       # last element is the forming bar
        if not closed:
            return

        # The index feed updates the shared relative-strength series every bar
        # (even when the index isn't itself a watched symbol).
        if sym == index_symbol:
            index_state["ret"] = _index_ret_series(_bars_to_df(closed))

        st = state.get(sym)
        if st is None:                           # index-only / removed symbol
            return
        if len(closed) < 22:                     # need >=20 for vol_ma20/RSI
            return
        bar_time = closed[-1].date
        if bar_time == st.last_bar:              # already processed this bar
            return
        st.last_bar = bar_time

        df = _bars_to_df(closed)
        sess = add_indicators(df).reset_index(drop=True)

        if "ema" in signals:
            msg = detect_ema(sess)
            if msg and _hhmm(sess).iloc[-1] != st.last_ema_bar:
                st.last_ema_bar = _hhmm(sess).iloc[-1]
                _alert(sym, "EMA", msg)
        if "mfr" in signals and "mfr" not in st.fired:
            msg = detect_mfr(sess, mfr_trigger)
            if msg:
                st.fired.add("mfr")
                _alert(sym, "MFR", msg)
        if "phb" in signals and "phb" not in st.fired:
            msg = detect_phb(sess)
            if msg:
                st.fired.add("phb")
                _alert(sym, "PHB", msg)
        if "vcb" in signals and "vcb" not in st.fired:
            msg = detect_vcb(df, index_state.get("ret"))
            if msg:
                st.fired.add("vcb")
                _alert(sym, "VCB", msg)

    return on_bar_update


WATCHLIST_POLL = 5          # seconds between active-list change checks
_HIST_KW = dict(endDateTime="", durationStr="1 D", barSizeSetting="1 min",
                whatToShow="TRADES", useRTH=True, keepUpToDate=True)


def _attach(sym: str, bars, handler, state: dict, subs: dict, announce: bool) -> None:
    """Wire a live bar feed into state + the handler (shared by sync/async paths)."""
    state[sym] = SymbolState()
    subs[sym] = bars
    bars.updateEvent += handler
    if announce:
        if not bars or len(bars) < 22:
            print(f"  ! {sym}: thin/no bars yet -- will alert when live")
        else:
            df = pd.DataFrame([{
                "time": b.date, "open": b.open, "high": b.high, "low": b.low,
                "close": b.close, "volume": b.volume, "wap": b.average,
            } for b in bars])
            df["time"] = pd.to_datetime(df["time"])
            sess = add_indicators(df).reset_index(drop=True)
            ema9, ema20 = sess["ema9"].iloc[-1], sess["ema20"].iloc[-1]
            rel = "ABOVE (bullish)" if ema9 > ema20 else "BELOW (bearish)"
            print(f"  {sym}: 9EMA={ema9:.3f} 20EMA={ema20:.3f} -> 9 is {rel}")


def subscribe(ib, sym: str, handler, state: dict, subs: dict, announce: bool = True) -> bool:
    """Synchronous subscribe -- used during startup (before the run loop)."""
    contract = Stock(sym, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        print(f"  x {sym}: could not qualify -- skipping")
        return False
    _attach(sym, ib.reqHistoricalData(contract, **_HIST_KW), handler, state, subs, announce)
    return True


async def subscribe_async(ib, sym: str, handler, state: dict, subs: dict) -> bool:
    """Async subscribe -- used by the live poller from inside the run loop,
    where the blocking sync wrappers can't be called."""
    contract = Stock(sym, "SMART", "USD")
    if not await ib.qualifyContractsAsync(contract):
        return False
    bars = await ib.reqHistoricalDataAsync(contract, **_HIST_KW)
    _attach(sym, bars, handler, state, subs, announce=False)
    return True


def unsubscribe(ib, sym: str, state: dict, subs: dict) -> None:
    bars = subs.pop(sym, None)
    if bars is not None:
        ib.cancelHistoricalData(bars)
    state.pop(sym, None)


async def watchlist_poller(ib, handler, state: dict, subs: dict,
                           protected: set | None = None) -> None:
    """Apply UI watchlist changes live: diff the active set against current
    subscriptions whenever the stored revision changes. Unchanged symbols keep
    their session state (dedup/indicators) untouched. `protected` symbols (e.g.
    the VCB index feed) are never auto-removed even though they aren't watched."""
    protected = protected or set()
    last_rev = signal_store.watchlist_rev()
    while True:
        await asyncio.sleep(WATCHLIST_POLL)
        try:
            rev = signal_store.watchlist_rev()
            if rev == last_rev:
                continue
            last_rev = rev
            active = set(signal_store.get_watchlist()["active"])
        except Exception as e:
            print(f"  ! watchlist poll failed: {e}", flush=True)
            continue
        current = set(subs) - protected
        for sym in sorted(active - current):
            ok = await subscribe_async(ib, sym, handler, state, subs)
            print(f"  + watchlist: added {sym}" if ok
                  else f"  x watchlist: could not add {sym}", flush=True)
        for sym in sorted(current - active):
            unsubscribe(ib, sym, state, subs)
            print(f"  - watchlist: removed {sym}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*",
                    help="tickers to watch (or use --watchlist)")
    ap.add_argument("--watchlist", help="file of tickers, one per line "
                    "(blank lines and # comments ignored)")
    ap.add_argument("--signals", default="ema,mfr,vcb",
                    help="comma list of: ema, mfr, phb, vcb (default ema,mfr,vcb)")
    ap.add_argument("--mfr-trigger", default="vwap", choices=["vwap", "rsi40"],
                    help="MFR reclaim trigger: vwap (cleaner) or rsi40 (earlier)")
    ap.add_argument("--phb-scan-start", default="14:30")
    ap.add_argument("--phb-scan-end", default="15:30",
                    help="intraday-flat window end (stop taking PHB entries)")
    ap.add_argument("--index", default="SPY",
                    help="relative-strength benchmark for VCB (auto-subscribed)")
    ap.add_argument("--vcb-rs-min", type=float, default=3.0,
                    help="VCB: require name to outperform the index by >= this many pts")
    a = ap.parse_args()

    wl_symbols = []
    if a.watchlist:
        with open(a.watchlist) as fh:
            wl_symbols = [ln.strip() for ln in fh
                          if ln.strip() and not ln.lstrip().startswith("#")]
    a.symbols = list(a.symbols) + wl_symbols
    if not a.symbols:
        print("no symbols: pass tickers as args or --watchlist FILE")
        return 1

    signals = {s.strip().lower() for s in a.signals.split(",") if s.strip()}
    bad = signals - {"ema", "mfr", "phb", "vcb"}
    if bad:
        print(f"unknown signal(s): {', '.join(sorted(bad))}")
        return 1

    # Align PHB live criteria with the chosen/validated backtest config:
    # intraday-flat window + the 1.0% above-VWAP precision filter.
    pht.SCAN_START, pht.SCAN_END = a.phb_scan_start, a.phb_scan_end
    pht.MIN_VWAP_DIST = 1.0
    # VCB live config = the recommended recipe (RS-gated; vcb.py defaults for the
    # rest: 1-min, OR<10:00, scan 10:00-15:00, vol>=2x, contract<=0.7, RSI>=60).
    index_symbol = a.index.upper()
    vcb.RS_MIN = a.vcb_rs_min if "vcb" in signals else None

    _quiet_hist_cancel()
    seed_symbols = [s.upper().rstrip(",") for s in a.symbols]
    signal_store.init_db()
    # Seed the default + active lists from the file/CLI on first run only; after
    # that the stored lists (editable in the UI) are authoritative.
    signal_store.init_settings(seed_symbols)
    # Supervised (container) mode: wait for the gateway through the daily reset,
    # and exit non-zero on disconnect so the restart policy gives us a fresh
    # process that re-subscribes. Interactive mode keeps the old run-til-Ctrl-C.
    supervised = os.environ.get("IB_SUPERVISED") == "1"
    cid = int(os.environ.get("IB_CLIENT_ID", "13"))
    ib = connect_ib_with_retry(client_id=cid) if supervised else connect_ib(client_id=cid)

    active = signal_store.get_watchlist()["active"]
    print(f"OK Connected (paper {ib.managedAccounts()}).")
    vcb_note = f"   VCB: RS>=+{a.vcb_rs_min:g} vs {index_symbol}" if "vcb" in signals else ""
    print(f"Signals: {', '.join(sorted(signals))}   "
          f"MFR trigger: {a.mfr_trigger}   PHB window: {a.phb_scan_start}-{a.phb_scan_end}{vcb_note}")
    print(f"Monitoring {len(active)} ticker(s) (editable live in the UI): "
          f"{', '.join(active)}\n")
    _log(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] --- signal_monitor start: "
         f"{','.join(sorted(signals))} on {', '.join(active)} ---")

    state: dict[str, SymbolState] = {}
    subs: dict = {}
    index_state: dict = {}                # shared {"ret": Series} updated by the index feed
    handler = make_handler(state, signals, a.mfr_trigger, index_state, index_symbol)
    for sym in active:
        subscribe(ib, sym, handler, state, subs)

    # VCB needs a live relative-strength benchmark. Subscribe the index feed if
    # it isn't already a watched symbol -- wire the handler (to update the shared
    # RS series) but NOT into `state`, so the index itself runs no detectors.
    index_feed_added = False
    if "vcb" in signals and index_symbol not in subs:
        ic = Stock(index_symbol, "SMART", "USD")
        if ib.qualifyContracts(ic):
            ibars = ib.reqHistoricalData(ic, **_HIST_KW)
            subs[index_symbol] = ibars
            ibars.updateEvent += handler
            index_feed_added = True
            print(f"  + index feed: {index_symbol} (relative-strength benchmark for VCB)")
        else:
            print(f"  ! could not subscribe index {index_symbol} -- VCB will not fire without it")

    # Apply UI watchlist edits live (subscribe/drop without a restart).
    try:
        import ib_async.util as util
        protected = {index_symbol} if index_feed_added else set()
        util.getLoop().create_task(watchlist_poller(ib, handler, state, subs, protected))
    except Exception as e:
        print(f"  ! watchlist poller not started: {e}", flush=True)

    # In supervised mode, a dropped gateway (daily reset) ends the run loop so
    # the process exits non-zero and the container is restarted to reconnect.
    dropped = {"flag": False}
    if supervised:
        def _on_disconnect() -> None:
            dropped["flag"] = True
            print("! gateway disconnected -- exiting for supervised restart", flush=True)
            try:
                import ib_async.util as util
                util.getLoop().stop()
            except Exception:
                pass
        ib.disconnectedEvent += _on_disconnect

    print("\nWatching live (market hours). Ctrl-C to stop.\n")
    try:
        ib.run()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        if ib.isConnected():
            ib.disconnect()
    return 1 if dropped["flag"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared, paper-safe IBKR connection helper.

Reads connection settings from the environment so every ibkr_bot script
behaves the same way:

  IB_HOST        (default 127.0.0.1)
  IB_PORT        (default 4002  -- paper IB Gateway; 7497 for paper TWS)
  IB_CLIENT_ID   (default 11)
  IB_ALLOW_LIVE  (set to 1 to permit live ports 7496/4001; off by default)
  IB_SKIP_PREFLIGHT (set to 1 to skip the raw API-handshake preflight)
"""

from __future__ import annotations

import os
import socket
import struct
import time
from datetime import datetime

from ib_async import IB

PAPER_PORTS = {7497, 4002}
LIVE_PORTS = {7496, 4001}


def _preflight_api(host: str, port: int, timeout: float = 4.0) -> None:
    """Fail fast if the gateway is up but its API server is wedged.

    A restarted-but-stuck IB Gateway keeps the port bound and accepts the
    TCP connection, yet never answers the API handshake -- so a normal
    ib_async connect just hangs for the full timeout. This sends the raw
    "API\\0" version handshake and expects the server version reply within
    a few seconds; silence means the API thread is dead and the gateway
    needs a restart. Raises SystemExit with an actionable message.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        try:
            sock.connect((host, port))
        except OSError as e:
            raise SystemExit(
                f"x Nothing accepting connections on {host}:{port} ({e}).\n"
                "  Is IB Gateway / TWS running and logged in?"
            )
        payload = b"v100..187"
        sock.sendall(b"API\0" + struct.pack(">I", len(payload)) + payload)
        try:
            data = sock.recv(64)
        except socket.timeout:
            data = b""
        if not data:
            raise SystemExit(
                f"x {host}:{port} is listening but the IB API server is not "
                "responding to the handshake.\n"
                "  The gateway's API thread is wedged -- fully quit and relaunch "
                "IB Gateway, then retry.\n"
                "  (Set IB_SKIP_PREFLIGHT=1 to bypass this check.)"
            )
    finally:
        sock.close()


def connect_ib(client_id: int | None = None, timeout: float = 10.0) -> IB:
    """Connect to TWS / IB Gateway and return a live IB instance.

    Refuses live trading ports unless IB_ALLOW_LIVE=1, so a stray IB_PORT
    can never silently point a paper tool at the real account.
    """
    host = os.environ.get("IB_HOST", "127.0.0.1")
    port = int(os.environ.get("IB_PORT", "4002"))
    cid = client_id if client_id is not None else int(os.environ.get("IB_CLIENT_ID", "11"))

    if port in LIVE_PORTS and os.environ.get("IB_ALLOW_LIVE") != "1":
        raise SystemExit(
            f"x Port {port} is a LIVE trading port. Refusing to connect.\n"
            "  Use a paper port (7497 TWS / 4002 Gateway), or set IB_ALLOW_LIVE=1."
        )
    if port not in PAPER_PORTS and port not in LIVE_PORTS:
        print(f"! Port {port} is non-standard -- double-check it is a PAPER account.")

    if os.environ.get("IB_SKIP_PREFLIGHT") != "1":
        _preflight_api(host, port)

    ib = IB()
    ib.connect(host, port, clientId=cid, timeout=timeout)
    return ib


def connect_ib_with_retry(client_id: int | None = None, timeout: float = 10.0,
                          attempts: int = 60, backoff: float = 5.0) -> IB:
    """connect_ib, but wait for the gateway instead of dying.

    On a server the daily IB reset (and container start ordering) means the
    gateway is routinely absent or still wedged for a minute or two. The
    preflight raises SystemExit in those cases; here we treat that as
    retryable and keep trying with a capped backoff, so the bot rides through
    the reset window. A LIVE-port refusal is NOT retryable -- it re-raises.
    """
    last = None
    for i in range(1, attempts + 1):
        try:
            return connect_ib(client_id=client_id, timeout=timeout)
        except SystemExit as e:
            # The live-port guard is a config error, not a transient outage.
            if "LIVE trading port" in str(e):
                raise
            last = e
        except (ConnectionError, OSError, TimeoutError) as e:
            # TimeoutError covers asyncio.TimeoutError too (aliased on 3.11+).
            last = e
        wait = min(backoff * i, 30.0)
        print(f"! gateway not ready (attempt {i}/{attempts}): {last}; "
              f"retrying in {wait:.0f}s", flush=True)
        time.sleep(wait)
    raise SystemExit(f"x gave up connecting after {attempts} attempts: {last}")


def daily_bars_completed(ib, contract, duration_str: str = "60 D",
                         what_to_show: str = "TRADES", use_rth: bool = True) -> list:
    """Daily bars with today's IN-PROGRESS session stripped.

    During market hours IB returns a partial bar for the current session as the
    LAST element, whose close is the live price. Using that as the prior close
    (so prevclose == last) or inside a 20-day-high pivot (so the pivot tracks
    today's own move) is a bug -- it made every day-change read +0.0%. This drops
    any trailing bar dated today, so callers get only COMPLETED sessions:
        prior_close = daily_bars_completed(...)[-1].close
    Pre-open there is no today bar, so nothing is dropped; never returns empty.
    """
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr=duration_str,
        barSizeSetting="1 day", whatToShow=what_to_show, useRTH=use_rth,
    )
    if not bars:
        return bars
    today = datetime.now().date()

    def _bar_date(b):
        d = b.date
        return d.date() if hasattr(d, "date") else d  # datetime -> .date(); date stays

    trimmed = [b for b in bars if _bar_date(b) != today]
    return trimmed if trimmed else bars  # safety: never empty

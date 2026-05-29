"""Shared, paper-safe IBKR connection helper.

Reads connection settings from the environment so every ibkr_bot script
behaves the same way:

  IB_HOST        (default 127.0.0.1)
  IB_PORT        (default 4002  -- paper IB Gateway; 7497 for paper TWS)
  IB_CLIENT_ID   (default 11)
  IB_ALLOW_LIVE  (set to 1 to permit live ports 7496/4001; off by default)
"""

from __future__ import annotations

import os

from ib_async import IB

PAPER_PORTS = {7497, 4002}
LIVE_PORTS = {7496, 4001}


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

    ib = IB()
    ib.connect(host, port, clientId=cid, timeout=timeout)
    return ib

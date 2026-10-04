"""
The book gate: Luk-style tape check for NEW house longs (run_luk_regime_book_switch.py, 2026-10-03).

ON  = QQQ close > QQQ SMA50  AND  QQQ EMA9 > QQQ EMA21  AND  the 5-session mean of (names at a 20-day closing high
      minus names at a 20-day closing low) > 0, over the eligible universe (50-day ADDV >= $50M, price >= $5).
OFF = anything else. Evaluated at a session's close; it governs NEW longs from the next session on.

What the test found (TEST_INDEX §7): on the house breakout book, taking no new longs while OFF trimmed max drawdown
(-41% -> -29%) with no measurable cost (+0.06pp/mo, t 0.50) -- a risk tool, NOT an edge. Flattening the whole book
cost return; timing the 12-1 momentum sleeve with it HURT (t -2.67). So: show it, tag long setups with it, never use
it on the momentum sleeve.

Data: data/cache/liquid_panel_2019.parquet (refreshed by the morning journal, the evening desk and start_alerts.sh).
The study ran on liquid_panel_2009; this panel's universe differs slightly (2026 list), so counts can differ a little.

    PYTHONPATH=src .venv/bin/python3 -m lib.regime.book_gate          # print the last 5 sessions + record them
    PYTHONPATH=src .venv/bin/python3 -m lib.regime.book_gate --line   # one line (used by the desk / alerts)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
PANEL = REPO / "data" / "cache" / "liquid_panel_2019.parquet"


def compute(panel: Path = PANEL) -> pd.DataFrame:
    raw = pd.read_parquet(panel, columns=["date", "ticker", "close", "dolvol"])
    C = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    C.index = pd.to_datetime(C.index)
    D = raw.pivot(index="date", columns="ticker", values="dolvol").reindex_like(C)
    q = C["QQQ"]
    elig = (D.rolling(50, min_periods=30).mean() >= 50e6) & (C >= 5)
    elig = elig.drop(columns=[c for c in ("SPY", "QQQ", "IWM", "RSP") if c in elig.columns])
    Ce = C[elig.columns]
    net = ((Ce >= Ce.rolling(20).max()) & elig).sum(1) - ((Ce <= Ce.rolling(20).min()) & elig).sum(1)
    out = pd.DataFrame({"qqq": q, "sma50": q.rolling(50).mean(), "ema9": q.ewm(span=9, adjust=False).mean(),
                        "ema21": q.ewm(span=21, adjust=False).mean(), "net": net, "net5": net.rolling(5).mean()})
    out["c1"] = out.qqq > out.sma50
    out["c2"] = out.ema9 > out.ema21
    out["c3"] = out.net5 > 0
    out["gate"] = np.where(out.c1 & out.c2 & out.c3, "ON", "OFF")
    return out.dropna(subset=["sma50", "net5"])


def line(row: pd.Series, date) -> str:
    ok = lambda b: "✓" if b else "✗"
    return (f"BOOK GATE {row.gate} as of {pd.Timestamp(date):%Y-%m-%d} close: QQQ>SMA50 {ok(row.c1)} ({row.qqq:.2f} vs {row.sma50:.2f}), "
            f"EMA9>EMA21 {ok(row.c2)}, net 20d highs-lows 5d {row.net5:+.0f} {ok(row.c3)} (today {row.net:+.0f})"
            + ("" if row.gate == "ON" else " -> no-new-longs rule"))


def latest(panel: Path = PANEL) -> tuple[str, str, pd.Timestamp]:
    g = compute(panel)
    d = g.index[-1]
    return g.gate.iloc[-1], line(g.iloc[-1], d), d


def record(g: pd.DataFrame) -> int:
    """Upsert every computed session into MySQL journal_book_gate (idempotent; the history self-heals)."""
    from lib.mysql_lib import _get_conn
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS journal_book_gate (
            trade_date DATE PRIMARY KEY, gate VARCHAR(3) NOT NULL, qqq DECIMAL(12,4), sma50 DECIMAL(12,4),
            ema9 DECIMAL(12,4), ema21 DECIMAL(12,4), net INT, net5 DECIMAL(10,2), c1 TINYINT, c2 TINYINT, c3 TINYINT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)""")
        rows = [(d.date(), r.gate, float(r.qqq), float(r.sma50), float(r.ema9), float(r.ema21), int(r.net), float(r.net5),
                 int(r.c1), int(r.c2), int(r.c3)) for d, r in g.iterrows()]
        cur.executemany("""INSERT INTO journal_book_gate (trade_date, gate, qqq, sma50, ema9, ema21, net, net5, c1, c2, c3)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE gate=VALUES(gate), qqq=VALUES(qqq), sma50=VALUES(sma50), ema9=VALUES(ema9),
                             ema21=VALUES(ema21), net=VALUES(net), net5=VALUES(net5), c1=VALUES(c1), c2=VALUES(c2), c3=VALUES(c3)""", rows)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", action="store_true", help="print one line only, do not record")
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args()
    g = compute()
    if a.line:
        print(line(g.iloc[-1], g.index[-1])); return 0
    print(line(g.iloc[-1], g.index[-1]))
    print(g.tail(5)[["gate", "qqq", "sma50", "ema9", "ema21", "net", "net5"]].round(2).to_string())
    if not a.no_record:
        try:
            print(f"recorded {record(g)} sessions in journal_book_gate")
        except Exception as e:                                     # the desk must not stop on a DB hiccup
            print(f"(journal_book_gate not updated: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

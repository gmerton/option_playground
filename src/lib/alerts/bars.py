"""Per-symbol intraday book: 1-minute bars built from trade prints (live) or fed
directly (replay), session VWAP from cumulative price*size, 5-minute aggregation
aligned to 09:30 ET."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass
class Bar:
    t: datetime          # bar start (ET, naive)
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float          # session VWAP at bar close


@dataclass
class SymbolBook:
    symbol: str
    bars: list[Bar] = field(default_factory=list)
    cur: Bar | None = None
    pv: float = 0.0
    v: float = 0.0
    session_open: float | None = None
    session_high: float = 0.0
    session_low: float = float("inf")
    low_time: datetime | None = None

    # ---- live path: trade prints -------------------------------------------------
    def on_trade(self, t: datetime, price: float, size: float) -> Bar | None:
        """Ingest one print. Returns the just-CLOSED 1-min bar when a new minute starts."""
        closed = None
        minute = t.replace(second=0, microsecond=0)
        if self.cur is not None and minute > self.cur.t:
            closed = self._close_cur()
        if self.cur is None or self.cur.t != minute:
            self.cur = Bar(minute, price, price, price, price, 0.0, price)
        b = self.cur
        b.high = max(b.high, price)
        b.low = min(b.low, price)
        b.close = price
        b.volume += size
        self.pv += price * size
        self.v += size
        b.vwap = self.pv / self.v if self.v else price
        self._track(b)
        return closed

    def flush_if_stale(self, now: datetime) -> Bar | None:
        """Close the open bar if the wall clock has moved past its minute (idle names)."""
        if self.cur is not None and now.replace(second=0, microsecond=0) > self.cur.t:
            return self._close_cur()
        return None

    def _close_cur(self) -> Bar:
        b = self.cur
        self.bars.append(b)
        self.cur = None
        return b

    # ---- replay path: finished 1-min bars ----------------------------------------
    def on_bar(self, b: Bar, bar_vwap: float | None = None) -> Bar:
        px = bar_vwap if bar_vwap else b.close
        self.pv += px * b.volume
        self.v += b.volume
        b.vwap = self.pv / self.v if self.v else b.close
        self._track(b)
        self.bars.append(b)
        return b

    def _track(self, b: Bar) -> None:
        if self.session_open is None:
            self.session_open = b.open
        self.session_high = max(self.session_high, b.high)
        if b.low < self.session_low:
            self.session_low = b.low
            self.low_time = b.t

    # ---- views ------------------------------------------------------------------
    @property
    def cum_volume(self) -> float:
        return self.v

    def last_close(self) -> float | None:
        return self.bars[-1].close if self.bars else None

    def five_min_bars(self) -> list[Bar]:
        """Aggregate closed 1-min bars into 5-min bars aligned to 09:30."""
        out: list[Bar] = []
        for b in self.bars:
            slot = b.t.replace(minute=(b.t.minute // 5) * 5, second=0, microsecond=0)
            if out and out[-1].t == slot:
                a = out[-1]
                a.high = max(a.high, b.high)
                a.low = min(a.low, b.low)
                a.close = b.close
                a.volume += b.volume
                a.vwap = b.vwap
            else:
                out.append(Bar(slot, b.open, b.high, b.low, b.close, b.volume, b.vwap))
        return out

    def opening_range(self, minutes: int = 15) -> tuple[float, float] | None:
        end = time(9, 30 + minutes)
        ob = [b for b in self.bars if b.t.time() < end]
        if not ob or self.bars[-1].t.time() < end:
            return None            # opening range not complete yet
        return max(b.high for b in ob), min(b.low for b in ob)

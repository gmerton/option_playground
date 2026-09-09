"""Intraday condition detectors, parameterized in ADR units.

Every detector = gate (context worth acting on) -> trigger (the bar that times the
entry) -> one-shot per session. Both were specified from the 2026-09-08 tape:

  UR   undercut & reclaim   SPCX: open +0.7%, flushed -2.6% (0.5 ADR) in 12 min,
                            undercut the prior-day low, 1-min close back above VWAP
                            at 09:46, closed +3.7%.
                            TXG: gapped -2.1% BELOW the daily 9 EMA (open = session
                            low), dipped 0.6% under VWAP at 09:45, reclaimed at
                            09:55, closed +4.7%. So the flush is measured from
                            max(open, prev close) and the arming band is fixed.
  ORB9 opening-range break  LITE: gap +1.9%, first-minute low held the daily 9 EMA
       above the 9 EMA      (0.4% above) and VWAP, 09:45 5-min close above the
                            15-min opening-range high, closed +11%.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time

from .bars import Bar, SymbolBook
from .context import DailyCtx
from .volprofile import vol_frac

# --- UR parameters -----------------------------------------------------------------
UR_LOW_BY = time(11, 0)        # the session low must be printed before this
UR_MIN_FLUSH_ADR = 0.25        # open -> low, in ADR units, always required
UR_BIG_FLUSH_ADR = 0.50        # ...or a flush this deep qualifies on its own
UR_EMA_TAG_PCT = 0.30          # low within this % of the daily 9/21 EMA counts as a tag
UR_MAX_FIRES = 2               # second fire only after a NEW session low...
UR_REFIRE_ADR = 0.25           # ...that is at least this many ADR below the first fire's low
UR_ARM_BAND = 0.0010           # a 1-min close this far under VWAP arms the reclaim
UR_TRIG_BAND = 0.0010          # reclaim trigger: close must clear VWAP by this fraction
                               # (dance protection = UR_MAX_FIRES + new-low requirement, not a wide band)
# --- ORB9 parameters ---------------------------------------------------------------
ORB_MINUTES = 15
ORB_BY = time(12, 0)
ORB_MIN_PACE = 1.0             # cumulative volume vs. profile-projected, x avg20 (below 1.2 is tagged "light vol")
GAP_WARN_ADR = 1.0             # tag alerts whose open gapped >= this many ADR (lens rule: no gap-up buys in hour one)
ORB_HOLD_ADR = 0.15            # session low may undercut the 9 EMA by this many ADR (floor 0.3%)


@dataclass
class Alert:
    symbol: str
    kind: str
    t: datetime
    price: float
    stop: float
    msg: str
    fields: dict = field(default_factory=dict)   # structured copy of the tags for the website/JSON


def vwap_band(adr_pct: float) -> float:
    """Schmitt-trigger deadband around VWAP, as a fraction (same rule as fade_watch)."""
    return max(0.0010, 0.20 * adr_pct / 100.0)


def vol_pace(book: SymbolBook, ctx: DailyCtx, t: datetime) -> float:
    elapsed = (t.hour - 9) * 60 + t.minute - 30 + 1
    proj = ctx.avg_vol20 * vol_frac(elapsed)
    return book.cum_volume / proj if proj > 0 else 0.0


def adr_from_21(price: float, ctx: DailyCtx) -> float:
    return (price / ctx.ema21 - 1) * 100 / ctx.adr_pct if ctx.adr_pct else 0.0


def gap_tag(book: SymbolBook, ctx: DailyCtx) -> str:
    gap_adr = (book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct if ctx.adr_pct else 0.0
    return f" | GAP {gap_adr:+.1f} ADR (no hour-one gap buys)" if gap_adr >= GAP_WARN_ADR else ""


class SymbolState:
    def __init__(self) -> None:
        self.below_vwap_seen = False
        self.ur_fires: list[float] = []      # session lows at each UR fire
        self.orb_fired = False
        self.orb_disqualified = False


def detect_ur(book: SymbolBook, ctx: DailyCtx, st: SymbolState, b: Bar) -> Alert | None:
    """Runs on every CLOSED 1-min bar."""
    if b.close < b.vwap * (1 - UR_ARM_BAND):
        st.below_vwap_seen = True
        return None
    if not st.below_vwap_seen or book.low_time is None or book.session_open is None:
        return None
    if len(st.ur_fires) >= UR_MAX_FIRES:
        return None
    if st.ur_fires and book.session_low > st.ur_fires[-1] * (1 - UR_REFIRE_ADR * ctx.adr_pct / 100):
        return None
    if book.low_time.time() > UR_LOW_BY or b.t <= book.low_time:
        return None
    lo = book.session_low
    ref = max(book.session_open, ctx.prev_close)          # gap-down opens count as the flush
    flush_adr = (ref - lo) / ref * 100 / ctx.adr_pct
    if flush_adr < UR_MIN_FLUSH_ADR:
        return None
    tag = None
    if lo <= ctx.prev_low:
        tag = f"undercut PDL {ctx.prev_low:.2f}"
    elif abs(lo / ctx.ema9 - 1) * 100 <= UR_EMA_TAG_PCT or lo < ctx.ema9 <= ref:
        tag = ("opened below" if book.session_open < ctx.ema9 else "tagged") + f" 9 EMA {ctx.ema9:.2f}"
    elif abs(lo / ctx.ema21 - 1) * 100 <= UR_EMA_TAG_PCT or lo < ctx.ema21 <= ref:
        tag = ("opened below" if book.session_open < ctx.ema21 else "tagged") + f" 21 EMA {ctx.ema21:.2f}"
    elif flush_adr >= UR_BIG_FLUSH_ADR:
        tag = "deep flush"
    if tag is None:
        return None
    # trigger: this bar closed back above VWAP (small fixed band; the wide ADR band only arms)
    if b.close <= b.vwap * (1 + UR_TRIG_BAND):
        return None
    st.ur_fires.append(lo)
    st.below_vwap_seen = False
    pace = vol_pace(book, ctx, b.t)
    ema_note = "" if b.close >= ctx.ema9 else f" | still below 9 EMA {ctx.ema9:.2f}"
    msg = (f"UR reclaim {b.close:.2f} > VWAP {b.vwap:.2f} | low {lo:.2f}@{book.low_time:%H:%M} "
           f"({-flush_adr:.2f} ADR, {tag}) | stop {lo:.2f} ({(b.close / lo - 1) * 100:.1f}%){ema_note} | "
           f"{adr_from_21(b.close, ctx):+.1f} ADR vs 21 EMA | vol pace {pace:.1f}x{gap_tag(book, ctx)}")
    return Alert(book.symbol, "UR", b.t, b.close, lo, msg, {
        "low": round(lo, 2), "low_time": book.low_time.strftime("%H:%M"), "flush_adr": round(-flush_adr, 2),
        "tag": tag, "stop_pct": round((b.close / lo - 1) * 100, 2), "below_ema9": b.close < ctx.ema9,
        "adr_vs_21": round(adr_from_21(b.close, ctx), 1), "vol_pace": round(pace, 1),
        "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})


def detect_orb9(book: SymbolBook, ctx: DailyCtx, st: SymbolState, b: Bar) -> Alert | None:
    """Runs on every CLOSED 1-min bar; acts only when a 5-min bar has just completed."""
    if st.orb_fired or st.orb_disqualified or book.session_open is None:
        return None
    hold = ctx.ema9 * (1 - max(0.003, ORB_HOLD_ADR * ctx.adr_pct / 100))
    if book.session_open < hold or book.session_low < hold:
        st.orb_disqualified = True
        return None
    if b.t.time() > ORB_BY:
        st.orb_disqualified = True
        return None
    orng = book.opening_range(ORB_MINUTES)
    if orng is None or (b.t.minute + 1) % 5 != 0:      # need a completed 5-min bar
        return None
    or_high, or_low = orng
    f5 = book.five_min_bars()
    if not f5 or f5[-1].t.time() < time(9, 30 + ORB_MINUTES):
        return None
    last5 = f5[-1]
    if last5.close <= or_high or last5.close <= last5.vwap:
        return None
    pace = vol_pace(book, ctx, b.t)
    if pace < ORB_MIN_PACE:
        return None
    st.orb_fired = True
    stop = max(or_low, last5.low)
    msg = (f"ORB9 5-min close {last5.close:.2f} > OR high {or_high:.2f} | open {book.session_open:.2f} "
           f"({(book.session_open / ctx.prev_close - 1) * 100:+.1f}%) held 9 EMA {ctx.ema9:.2f} | "
           f"stop {stop:.2f} ({(last5.close / stop - 1) * 100:.1f}%) | {adr_from_21(last5.close, ctx):+.1f} ADR vs 21 EMA | "
           f"vol pace {pace:.1f}x{' (light vol)' if pace < 1.2 else ''} | 15d high {ctx.high15:.2f}{gap_tag(book, ctx)}")
    return Alert(book.symbol, "ORB9", b.t, last5.close, stop, msg, {
        "or_high": round(or_high, 2), "open_pct": round((book.session_open / ctx.prev_close - 1) * 100, 2),
        "ema9": round(ctx.ema9, 2), "stop_pct": round((last5.close / stop - 1) * 100, 2), "below_ema9": False,
        "adr_vs_21": round(adr_from_21(last5.close, ctx), 1), "vol_pace": round(pace, 1), "light_vol": pace < 1.2,
        "high15": round(ctx.high15, 2),
        "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})


DETECTORS = {"ur": detect_ur, "orb9": detect_orb9}
